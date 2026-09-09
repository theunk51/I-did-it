from pathlib import Path
from typing import Literal

from src.register_allocation import RegisterAllocator
from src.abi_specification import ABISpecification as ABI
from src.debug import print_ast
from src.ast_nodes import *
from src.parser import Parser
from src.semantic_analyzer import ValueType
from src.tokens import TokenType

class Generator:
    def __init__(self, ast: Program):
        self.ast = ast
        self.current_line_number: int = 0

        # assembly program section state
        self.data_section: list[str] = []
        self.bss_section: list[str] = []
        self.text_section: list[str] = []

        # program state
        self.label_counter = {}
        self.stack_offset = 0

    def walk_ast(self):
        self.emit_noindent(".global main")
        self.emit_noindent(".text")
        self.emit_noindent("main:")
        self.push("%rbp") # save the previous stack frame pointer
        self.emit("movq %rsp, %rbp") # load the current frame pointer

        self.compile_node(self.ast)
        
        # exit program, returning 0 from main
        # self.emit("movq $0, %rax")
        self.emit("movq %rbp, %rsp")
        self.pop("%rbp")
        self.emit("ret")
        self.emit_noindent('\n')

        # ensure that everything has been returned
        assert self.stack_offset == 0

    def generate_assembly_as_string(self) -> str:
        output = ""
        sections = [self.data_section, self.bss_section, self.text_section]
        for section in sections:
            if section != []:
                output += "\n".join(section) + "\n"
        return output

    def generate_assembly_file(self, filename: str | Path = "output.s") -> None:
        """
        Writes the assembly instructions to the given file or path. Defaults 
        to output.s.
        """

        path = Path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        asm = self.generate_assembly_as_string()
        path.write_text(asm, encoding="utf-8")

    ##################################
    # Helper Methods
    ##################################

    def error(self, message: str):
        raise Exception(f"Compiler Error at '{self.current_line_number}': {message}")
    
    def align_stack(self, upcoming_allocation: int) -> int:
        """
        Calculates how many bytes of padding are needed to ensure the stack 
        pointer (%rsp) is aligned to the ABI's required alignment boundary
        AFTER the upcoming allocation is subtracted. Use 0 to align the stack with 
        its allocation.
        """
        total_pending_offset = abs(self.stack_offset) + upcoming_allocation
        misalignment = total_pending_offset % ABI.stack_alignment
        if misalignment == 0:
            return 0
        return ABI.stack_alignment - misalignment
    
    def emit(self, instruction: str, section: Literal["text", "data", "bss"] = "text", indent: bool = True):
        """
        Appends the given instructions to the assembly program's specified section.
        """
        formatted_instruction = f"\t{instruction}" if indent else instruction
        if section == "data":
            self.data_section.append(formatted_instruction)
        elif section == "bss":
            self.bss_section.append(formatted_instruction)
        else:
            self.text_section.append(formatted_instruction)
    
    def emit_noindent(self, instruction: str, section: Literal["text", "data", "bss"] = "text"):
        """
        Convenience method to emit an instruction (like a label) without indentation.
        """
        self.emit(instruction, section=section, indent=False)

    def push(self, register: str):
        self.emit(f"pushq {register}")
        self.stack_offset -= 8

    def pop(self, register: str):
        self.emit(f"popq {register}")
        self.stack_offset += 8
    

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
            self.emit_noindent(f".L_line_{line_number}:")
            self.compile_node(statement)

    def _compile_IntegerLiteral(self, node: IntegerLiteral):
        # an integer moves its value into the accumulator
        self.emit(f"movq ${node.value}, %rax")

    def _compile_InfixExpression(self, node: InfixExpression):
        self.compile_node(node.left)
        self.push("%rax")
        self.compile_node(node.right)
        self.emit("movq %rax, %rdx")
        self.pop("%rax")

        # left = %rax;  right = %rdx
        # instruction source, destination ---> D = Src OP Dest
        if node.operator == TokenType.PLUS:
            self.emit("addq %rdx, %rax")
        elif node.operator == TokenType.MINUS:
            self.emit("subq %rdx, %rax")
        elif node.operator == TokenType.MUL:
            self.emit("imulq %rdx, %rax")
        elif node.operator == TokenType.DIV:
            # The divisor is currently in %rdx. 
            # idivq requires the dividend to be in %rdx:%rax
            self.emit("movq %rdx, %r15")
            self.emit("cqto")           # Sign-extend %rax into %rdx:%rax
            self.emit("idivq %r15")     # Divides %rdx:%rax by %r15. Quotient goes to %rax


##################################
# Test Cases 
##################################



if __name__ == "__main__":
    import subprocess
    import sys
    from src.parser import Parser

    num_tests = 0
    num_passed = 0

    def assert_compilation(expected: int, source_code: str):
        global num_tests, num_passed
        num_tests += 1

        ast = Parser("1 " + source_code).parse_program()
        gen = Generator(ast)
        gen.walk_ast()
        gen.generate_assembly_file("temp.s")

        process = subprocess.run(["gcc", "-static", "-o", "temp.exe", "temp.s"])
        if process.returncode != 0:
            sys.exit(process.returncode)
        
        process = subprocess.run(['./temp.exe'])
        if process.returncode != expected:
            print(f"{source_code} => {expected} expected, but got {process.returncode}")
        else:
            print("OK")
            num_passed += 1

    assert_compilation(0, "0")
    assert_compilation(42, "42")
    assert_compilation(21, "5+20-4")
    assert_compilation(41, " 12 + 34 - 5 ")
    assert_compilation(47, "5+6*7")
    assert_compilation(15, "5*(9-6)")
    assert_compilation(4, "(3+5)/2")
    assert_compilation(28, "8 / 2 * 7")

    print(f"Passed {num_passed}/{num_tests}. (passing rate: {num_passed/num_tests:.3%})")

        