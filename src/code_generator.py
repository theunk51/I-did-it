

from pathlib import Path
from typing import Literal

from src.register_allocation import RegisterAllocator
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
        self.global_variables = {}
        self.stack_offset = 0
        self.temporary_registers = ["%rax", "%rdx", "%r15"]


    def generate_assembly_str(self) -> str:
        """
        Walks the AST program dictionary, compiles each statement, 
        and joins sections into a final assembly string.
        """
        self.emit(".bss", section="bss")
        for variable, location in self.variable_allocation.items():
            if "bss" in location:
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
        self.emit("    pushq %rbx")
        self.emit("    pushq %r10")
        self.emit("    pushq %r12")
        self.emit("    pushq %r13")
        self.emit("    pushq %r14")
        self.emit("    pushq %r15")


        self._compile_Program(self.ast)

        self.emit(".main_exit:")
        # PRINT THE RESULT (Windows x64 Calling Convention)
        self.emit("    # Print the final result (Windows ABI)")
        self.emit("    movq %rax, %rdx")             # 2nd Argument: The number to print
        self.emit("    leaq format_int(%rip), %rcx") # 1st Argument: The string format
        
        # Windows REQUIRES 32 bytes of "shadow space" on the stack before calling C functions.
        self.emit("    subq $32, %rsp")
        self.emit("    call printf")

        # restore callee-saved registers (reverse order of pushes)
        self.emit("    addq $32, %rsp")
        self.emit("    popq %r15")
        self.emit("    popq %r14")
        self.emit("    popq %r13")
        self.emit("    popq %r12")
        self.emit("    popq %r10")
        self.emit("    popq %rbx")

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
        """Writes the assembly instruction to the file with given name or path."""

        path = Path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        asm = self.generate_assembly_str()
        path.write_text(asm, encoding="utf-8")

    
    # === Helper methods ===
    
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

    def error(self, message: str):
        raise Exception(f"Compiler Error at '{self.current_line_number}': {message}")

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
        # Base case: An integer simply moves its value into the accumulator
        self.emit(f"    movq ${node.value}, %rax")

    def _compile_Identifier(self, node: Identifier):
        # Base case: A variable moves its stored value into the accumulator
        loc = self.variable_allocation[node.value]
        self.emit(f"    movq {loc}, %rax")

    def _compile_LetStatement(self, node: LetStatement):
        self.compile_node(node.value)
        destination = self.variable_allocation[node.name.value]
        self.emit(f"    movq %rax, {destination}")

    def _compile_InfixExpression(self, node: InfixExpression):
        self.compile_node(node.left)
        self.emit("    pushq %rax")
        self.stack_offset -= 8
        self.compile_node(node.right)
        self.emit("    movq %rax, %rdx")
        self.emit("    popq %rax")
        self.stack_offset -= 8

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
