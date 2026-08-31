

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
        self.temporary_registers = ["%rax", "%rdx", "%r15"]
        self.abi = ABI.get_abi()


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
        self.stack_offset -= 8

        # save callee-saved registers if need be
        for reg in ABI.pushable_callee_saved_regs:
            self.emit(f"    pushq {reg}")
            self.stack_offset -= 8

        self._compile_Program(self.ast)
        self.emit_debug_dump()

        self.emit(".main_exit:")

        # PRINT THE RESULT
        self.emit_C_call("printf", [
            ("leaq", "format_int(%rip)"), # 1st Argument: The string format
            ("movq", "%rax")              # 2nd Argument: The number to print
        ])

        # restore callee-saved registers
        for reg in reversed(ABI.pushable_callee_saved_regs):
            self.emit(f"    popq {reg}")
            self.stack_offset += 8

        # exit program returning 0 from main
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

    def emit_C_call(self, func_name: str, inst_args: list[tuple[str, str]] = None):
        """
        Safely calls a C function across any OS.
        inst_args is an optional list of (instruction, source_operand).
        Example: emit_C_call("printf", [("leaq", "hello_world_str(%rip)"), ("movq", "%rax")])
        """
        self.emit(f"\n    # --- CALL C FUNCTION: {func_name} ---")
        # Only backup caller-saved regs that RegisterAllocator is actually allowed to use.
        regs_to_save = [reg for reg in self.abi.caller_saved_regs 
                        if reg in self.abi.allocatable_registers]
        for reg in regs_to_save:
            self.emit(f"  pushq {reg}")
            self.stack_offset -= 8
        

        if inst_args:
            # what about variables assigned to registers?
            num_abi_args = len(ABI.argument_regs)
            num_spilled_args = max(0, len(inst_args) - num_abi_args)
            stack_allocation = self.abi.shadow_space_size + num_spilled_args * 8
            stack_allocation += self._calculate_stack_padding(stack_allocation)

            if stack_allocation > 0:
                self.emit(f"    subq ${stack_allocation}, %rsp")
                self.stack_offset -= stack_allocation

            if num_spilled_args > 0:
                offset = ABI.shadow_space_size
                for i, (inst, src) in enumerate(inst_args[num_abi_args:]):
                    # prevent illegal Memory-to-Memory moves for stack arguments
                    if "bss" in src or "(%rip)" in src:
                        self.emit(f"    {inst} {src}, %r15")  # Move to scratch
                        self.emit(f"    movq %r15, {offset}(%rsp)") # Move to stack
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

    def emit_debug_dump(self):
        """Emits assembly to print all allocated variables and their current values at runtime."""
        
        self.emit("debug_fmt: .string \"DEBUG Variable %s (%s) = %d\\n\"", section="data")
    
        self.emit(".L_debug_state_dump:")
        all_used_registers = [
            '%r8', '%r9', '%r10', '%r11', '%r12', '%r13', '%r14', '%r15', 
            '%rax', '%rbx', '%rcx', '%rsi', '%rdi', '%rdx'
        ]
        should_align_stack = len(all_used_registers) % 2 != 0
        for reg in all_used_registers:
            self.emit(f"    pushq {reg}")
        if should_align_stack:
            self.emit(f"    subq $8, %rsp")


        for variable, location in self.variable_allocation.items():
            self.emit(f"var_name_{variable}: .string \"{variable}\"", section="data")
            self.emit(f"var_loc_{variable}: .string \"{location}\"", section="data")
            
            # Windows printf ABI: 
            # 1st arg (%rcx) = format string, 
            # 2nd arg (%rdx) = var name, 
            # 3rd arg (%r8) = var location
            # 4th arg (%r9) = value
            self.emit("    leaq debug_fmt(%rip), %rcx")
            self.emit(f"    leaq var_name_{variable}(%rip), %rdx")
            self.emit(f"    leaq var_loc_{variable}(%rip), %r8")
            
            
            if "bss" in location:
                self.emit(f"    movq {location}, %r9") # Load from memory
            else:
                # If it's a register (e.g. %r8), it was pushed to the stack.
                # Do not read the register directly because printf might have destryed it. 
                reg_index = all_used_registers.index(location)
                stack_offset = (len(all_used_registers) - 1 - reg_index) * 8
                self.emit(f"    movq {stack_offset}(%rsp), %r9")
        
            # Allocate 32 bytes shadow space, call printf, clean up shadow space
            self.emit("    subq $32, %rsp")
            self.emit("    call printf")
            self.emit("    addq $32, %rsp")

        if should_align_stack:
            self.emit(f"    subq $8, %rsp")
        for reg in reversed(all_used_registers):
            self.emit(f"    popq {reg}")
            
        self.emit("# --- END DEBUG DUMP ---\n")
    
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

    def _compile_Identifier(self, node: Identifier):
        # variable moves its stored value into the accumulator
        loc = self.variable_allocation[node.value]
        self.emit(f"    movq {loc}, %rax")

    def _compile_LetStatement(self, node: LetStatement):
        self.compile_node(node.value)
        destination = self.variable_allocation[node.name.value]
        self.emit(f"    movq %rax, {destination}")
        
        # Optionally trace the variable change!
        # self.emit_trace_variable(node.name.value, destination)

    def emit_trace_variable(self, variable_name: str, location: str):
        """Prints a message every time a specific variable's value changes."""
        self.emit(f"\n    # --- TRACE: {variable_name} ---")
        self.emit(f"trace_fmt_{variable_name}: .string \"[TRACE] {variable_name} updated to %d\\n\"", section="data")
        
        # Save volatile registers
        volatile_regs = ['%rax', '%rcx', '%rdx', '%r8', '%r9', '%r10', '%r11']
        for reg in volatile_regs:
            self.emit(f"    pushq {reg}")
            
        # Align stack to 16 bytes. We pushed 7 registers (56 bytes), so we need 8 more bytes.
        self.emit("    subq $8, %rsp")
        
        self.emit(f"    leaq trace_fmt_{variable_name}(%rip), %rcx")
        
        # Read the value from memory or stack
        if "bss" in location:
            self.emit(f"    movq {location}, %rdx")
        else:
            if location in volatile_regs:
                # Calculate where we pushed it on the stack (account for the 8 bytes we just subtracted)
                reg_index = volatile_regs.index(location)
                stack_offset = ((len(volatile_regs) - 1 - reg_index) * 8) + 8
                self.emit(f"    movq {stack_offset}(%rsp), %rdx")
            else:
                # It's a callee-saved register, so printf won't destroy it and we didn't push it
                self.emit(f"    movq {location}, %rdx")
                
        # 32 bytes shadow space
        self.emit("    subq $32, %rsp")
        self.emit("    call printf")
        self.emit("    addq $32, %rsp")
        
        self.emit("    addq $8, %rsp")
        for reg in reversed(volatile_regs):
            self.emit(f"    popq {reg}")
        self.emit("    # --- END TRACE ---\n")

    def emit_dump_all_registers(self):
        """Prints the raw integer value of every single physical CPU register."""
        self.emit("\n    # --- DUMP ALL PHYSICAL REGISTERS ---")
        
        # All standard general-purpose registers
        physical_regs = [
            '%rax', '%rbx', '%rcx', '%rdx', '%rsi', '%rdi',
            '%r8', '%r9', '%r10', '%r11', '%r12', '%r13', '%r14', '%r15'
        ]
        
        # Push them ALL to the stack to preserve them
        for reg in physical_regs:
            self.emit(f"    pushq {reg}")
            
        # 14 registers = 112 bytes. 112 is a multiple of 16, so the stack is perfectly aligned!
        self.emit("reg_dump_fmt: .string \"[CPU] %s = %d\\n\"", section="data")
        
        for i, reg in enumerate(physical_regs):
            reg_name = reg.strip('%')
            self.emit(f"reg_name_str_{reg_name}: .string \"{reg}\"", section="data")
            
            self.emit("    leaq reg_dump_fmt(%rip), %rcx")
            self.emit(f"    leaq reg_name_str_{reg_name}(%rip), %rdx")
            
            # Read from the stack backup!
            stack_offset = (len(physical_regs) - 1 - i) * 8
            self.emit(f"    movq {stack_offset}(%rsp), %r8")
            
            self.emit("    subq $32, %rsp")
            self.emit("    call printf")
            self.emit("    addq $32, %rsp")
            
        # Pop them all back
        for reg in reversed(physical_regs):
            self.emit(f"    popq {reg}")
            
        self.emit("    # --- END DUMP ---\n")

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
