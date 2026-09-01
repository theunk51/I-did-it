from pathlib import Path
from typing import Literal

from src.register_allocation import RegisterAllocator
from src.abi_specification import ABISpecification as ABI
from src.debug import print_ast
from src.ast_nodes import *
from src.parser import Parser

class CodeGenerator:
    """
    Converts the parsed AST program into x86-64 assembly that can be
    compiled and executed with GCC.
    """
    def __init__(self, ast: Program):
        self.ast = ast
        self.current_line_number: int = 0

        # assembly program section state
        self.data_section: list[str] = []
        self.bss_section: list[str] = []
        self.text_section: list[str] = []

        # program state
        self.variable_allocation = RegisterAllocator.allocate(ast)
        self.label_counter = {}
        self.global_variables = {}
        self.stack_offset = 0
        self.temporary_registers = ABI.compiler_scratch_regs

    def generate_assembly_str(self) -> str:
        """
        Walks the AST program dictionary, compiles each statement, 
        and joins sections into a final assembly string.
        """
        self.emit(".bss", section="bss")
        for variable, location in self.variable_allocation.items():
            if location.endswith("_bss(%rip)"):
                # Syntax: .lcomm symbol_name, size_in_bytes
                # local common means that this variable will only be accessible in this program
                self.emit(f"    .lcomm {variable}_bss, 8", section="bss")

        self.emit(".data", section="data")
        self.emit("    format_int: .string \"%d\\n\"", section="data")
        self.emit("\n")

        self.emit(".global main")
        self.emit(".text")
        self.emit("main:")
        self.emit("    pushq %rbp") # save the previous stack frame pointer
        self.emit("    movq %rsp, %rbp") # load the current frame pointer
        
        # save callee-saved registers if need be
        for reg in ABI.pushable_callee_saved_regs:
            self.emit(f"    pushq {reg}")
            self.stack_offset -= 8
        # padding = self._calculate_stack_padding(0)
        # if padding > 0:
        #     self.emit(f"    subq ${padding}, %rsp")

        self._compile_Program(self.ast)

        self.emit(".main_exit:")
        self.emit_C_call("printf", [
            ("leaq", "format_int(%rip)"), # 1st Argument: The string format
            ("movq", "%rax")              # 2nd Argument: The number to print
        ])

        # restore callee-saved registers
        # if padding > 0:
        #     self.emit(f"    addq ${padding}, %rsp")
        for reg in reversed(ABI.pushable_callee_saved_regs):
            self.emit(f"    popq {reg}")
            self.stack_offset += 8

        # exit program, returning 0 from main
        self.emit("    movq $0, %rax")
        self.emit("    movq %rbp, %rsp")
        self.emit("    popq %rbp")
        self.emit("    ret")
        self.emit("\n")

        output = "\n".join(self.data_section) + "\n"
        output += "\n".join(self.bss_section) + "\n"
        output += "\n".join(self.text_section) + "\n"
        return output

    def generate_assembly_file(self, filename: str | Path = "output.s") -> None:
        """Writes the assembly instructions to the file with given name or path."""

        path = Path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        asm = self.generate_assembly_str()
        path.write_text(asm, encoding="utf-8")

    
    # === Helper methods ===

    def get_new_label(self, _type: str):
        """Creates a new label for the given situtation using an interal counter."""
        if _type not in self.label_counter:
            self.label_counter[_type] = 0
    
        self.label_counter[_type] += 1
        i = self.label_counter[_type]
        return f".label_{_type}_{i}:"

    def emit(self, instruction: str, section: Literal["text", "data", "bss"]="text"):
        """
        Appends the given instructions to the assembly program's specified section.
        """
        if section == "data":
            self.data_section.append(instruction)
        elif section == "bss":
            self.bss_section.append(instruction)
        else:
            self.text_section.append(instruction)

    def emit_C_call(self, func_name: str, inst_args: list[tuple[str, str]] = []):
        """
        Safely calls a C function across any OS.
        inst_args is an optional list of (instruction, source_operand).
        Example: emit_C_call("printf", [("leaq", "hello_world_str(%rip)"), ("movq", "%rax")])
        """
        self.emit(f"    # --- CALL C FUNCTION: {func_name} ---")
        # only backup caller-saved regs that RegisterAllocator is actually allowed to use.
        regs_to_save = [reg for reg in ABI.caller_saved_regs 
                        if reg in ABI.allocatable_registers]
        for reg in regs_to_save:
            self.emit(f"    pushq {reg}")
            self.stack_offset -= 8
        

        if inst_args:
            # what about variables assigned to registers?
            num_abi_args = len(ABI.argument_regs)
            num_spilled_args = max(0, len(inst_args) - num_abi_args)
            stack_allocation = ABI.shadow_space_size + num_spilled_args * 8
            stack_allocation += self._calculate_stack_padding(stack_allocation)

            if stack_allocation > 0:
                self.emit(f"    subq ${stack_allocation}, %rsp")
                self.stack_offset -= stack_allocation

            if num_spilled_args > 0:
                offset = ABI.shadow_space_size
                for i, (inst, src) in enumerate(inst_args[num_abi_args:]):
                    # prevent illegal memory-to-memory moves for stack arguments
                    if "bss" in src or "(%rip)" in src:
                        self.emit(f"    {inst} {src}, %r15")  # move to scratch
                        self.emit(f"    movq %r15, {offset}(%rsp)") # move to stack
                    else:
                        self.emit(f"    {inst} {src}, {offset}(%rsp)")
                    offset += 8
            
            for i, (inst, src) in enumerate(inst_args[:num_abi_args]):
                self.emit(f"    {inst} {src}, {ABI.argument_regs[i]}")

            self.emit(f"    movq $0, %rax") # for variadic functions
            self.emit(f"    call {func_name}")

            if stack_allocation > 0:
                self.emit(f"    addq ${stack_allocation}, %rsp")
                self.stack_offset += stack_allocation

            for reg in reversed(regs_to_save):
                self.emit(f"    popq {reg}")
                self.stack_offset += 8

            self.emit(f"    # --- End Call {func_name} ---\n")

    def emit_trace_variable(self, variable_name: str, location: str):
        """Prints a message every time a specific variable's value changes."""
        fmt_label = f"trace_fmt_{variable_name}"
        self.emit(f'{fmt_label}: .string "[TRACE] {variable_name} updated to %d\\n"', section="data")
        
        self.emit_C_call("printf", [
            ("leaq", f"{fmt_label}(%rip)"), # Arg 1: The format string
            ("movq", location)              # Arg 2: The variable's location
        ])
    
    def error(self, message: str):
        raise Exception(f"Compiler Error at '{self.current_line_number}': {message}")

    def _calculate_stack_padding(self, upcoming_allocation: int) -> int:
        """
        Calculates how many bytes of padding are needed to ensure the stack 
        pointer (%rsp) is aligned to the ABI's required alignment boundary
        AFTER the upcoming allocation is subtracted.
        """
        total_pending_offset = abs(self.stack_offset) + upcoming_allocation
        misalignment = total_pending_offset % ABI.stack_alignment
        if misalignment == 0:
            return 0
        return ABI.stack_alignment - misalignment

    def compile_node(self, node: ASTNode):
        """
        Dynamically dispatch to the correct compilation method for an ASTNode
        subclass. If one is not found, a dummy method will be returned.
        """  
        method_name = f"_compile_{type(node).__name__}"
        method = getattr(self, method_name, self._missing_compile_node)
        return method(node)

    def _missing_compile_node(self, node, *args, **kwargs):
        raise NotImplementedError(f"No compile method defined for {type(node).__name__}")

    def _compile_Program(self, node: Program):
        for line_number, statement in sorted(node.statements.items()):
            self.current_line_number = line_number
            self.emit(f".L_line_{line_number}:")
            self.compile_node(statement)

    def _compile_IntegerLiteral(self, node: IntegerLiteral):
        # an integer moves its value into the accumulator
        self.emit(f"    movq ${node.value}, %rax")

    def _compile_FloatLiteral(self, node: FloatLiteral):
        # an integer moves its value into the accumulator
        self.emit(f"    movq ${node.value}, %xmm1")

    def _compile_Identifier(self, node: Identifier):
        # variable moves its stored value into the accumulator
        loc = self.variable_allocation[node.value]
        self.emit(f"    movq {loc}, %rax")

    def _compile_LetStatement(self, node: LetStatement):
        self.compile_node(node.value)
        destination = self.variable_allocation[node.name.value]
        self.emit(f"    movq %rax, {destination}")
        # self.emit_trace_variable(node.name.value, destination)

    def _compile_InfixExpression(self, node: InfixExpression):
        self.compile_node(node.left)
        self.emit("    pushq %rax")
        self.stack_offset -= 8
        self.compile_node(node.right)
        self.emit("    movq %rax, %rdx")
        self.emit("    popq %rax")
        self.stack_offset += 8

        # left = %rax;  right = %rdx
        # instruction source, destination
        if node.operator == "+":
            self.emit("    addq %rdx, %rax")
        elif node.operator == "-":
            self.emit("    subq %rdx, %rax")
        elif node.operator == "*":
            self.emit("    imulq %rdx, %rax")
        elif node.operator == "/":
            # The divisor is currently in %rdx. 
            # idivq requires the dividend to be in %rdx:%rax
            self.emit("    movq %rdx, %r15")
            self.emit("    cqto")           # Sign-extend %rax into %rdx:%rax
            self.emit("    idivq %r15")     # Divides %rdx:%rax by %r15. Quotient goes to %rax

    def _compile_PrintStatement(self, node: PrintStatement):
        if len(node.items) == 0:
            self.emit_C_call("print_newline", [])
            return

        for item in node.items:
            if item == ',':
                self.emit_C_call("print_basic_comma")
            elif item == ';':
                self.emit_C_call("print_basic_semicolon")
            elif isinstance(item, CallExpression) and item.name.value == "TAB":
                self.compile_node(item.arguments[0]) # Put X in %rax
                self.emit_C_call("basic_tab", [("movq", "%rax")])
            elif isinstance(item, StringLiteral):
                self.compile_node(item) 
                self.emit_C_call("print_basic_string", [("movq", "%rax")])
            elif isinstance(item, IntegerLiteral):
                self.compile_node(item) 
                self.emit_C_call("print_basic_number", [("movq", "%rax")])
            elif isinstance(item, FloatLiteral):
                self.compile_node(item) 
                self.emit_C_call("print_basic_number", [("movq", "%rax")])
            else:
                raise NotImplementedError(f"IDK what {item} is")

        last_item = node.items[-1]
        if node.items[-1] not in (',', ';'):
            self.emit_C_call("print_newline")
