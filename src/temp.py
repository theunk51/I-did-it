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
        self.push("%rbp")  # save the previous stack frame pointer
        self.emit("movq %rsp, %rbp")  # load the current frame pointer

        self.compile_node(self.ast)

        # exit program, returning 0 from main
        # self.emit("movq $0, %rax")
        self.emit_noindent(".main_exit:")
        self.emit("movq %rbp, %rsp")
        self.pop("%rbp")
        self.emit("ret")
        self.emit_noindent("\n")

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
        self.emit(instruction, section=section, indent=False)

    def emit_label(self, label: str):
        self.emit_noindent(f"{label}:")

    def push(self, register: str):
        self.emit(f"pushq {register}")
        self.stack_offset -= 8

    def pop(self, register: str):
        self.emit(f"popq {register}")
        self.stack_offset += 8

    def create_label(self, name: str):
        """Creates a new label for the given situtation using an internal counter."""
        count = self.label_counter.get(name, 0) + 1
        self.label_counter[name] = count
        return f".L_{name}_{count}"

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
        elif node.operator in (TokenType.DIV, TokenType.MOD):
            # The divisor is currently in %rdx.
            # idivq requires the dividend to be in %rdx:%rax
            self.emit("movq %rdx, %r15")
            self.emit("cqto")  # Sign-extend %rax into %rdx:%rax
            self.emit("idivq %r15")  # Divides %rdx:%rax by %r15. Quotient goes to %rax

            if node.operator == TokenType.MOD:
                self.emit("movq %rdx, %rax")

        elif node.operator == TokenType.EXPONENT:
            # def exponent(base, exponent):
            #   result = 1
            #   while exponent > 0:
            #       if exponent % 2 == 1:
            #           result *= base
            #       base *= base            # Square the base
            #       exponent //= 2          # Halve the exponent
            # Time complexity: O(log n)

            end_label = self.create_label("exponent_end")
            while_label = self.create_label("exponent_while")
            even_label = self.create_label("exponent_even")

            # %rax = base
            # %rdx = exponent
            # %r15 = result
            self.emit_label(self.create_label("exponent"))
            self.emit("movq $1, %r15")
            self.emit("testq %rdx, %rdx")
            self.emit(f"jle {end_label}")
            self.emit_label(while_label)
            self.emit("testq $1, %rdx")
            self.emit(f"jz {even_label}")
            self.emit("imulq %rax, %r15")
            self.emit_label(even_label)
            self.emit("imulq %rax, %rax")
            self.emit("shrq $1, %rdx")
            self.emit(f"jnz {while_label}")
            self.emit_label(end_label)
            self.emit("movq %r15, %rax")


##################################
# Test Cases
##################################

if __name__ == "__main__":
    import subprocess
    import sys
    from src.parser import Parser

    TEST_CASES = [
        (0, "0"),
        (42, "42"),
        (21, "5+20-4"),
        (41, " 12 + 34 - 5 "),
        (47, "5+6*7"),
        (15, "5*(9-6)"),
        (4, "(3+5)/2"),
        (8, "2^3"),
        (28, "8 / 2 * 7"),
        (32, "2 ^ 5"),
        (16, "2 ^ 2 ^ 2"),
        (512, "2 ^ (3 ^ 2)"),
        (56, "2 ^ 3 * 7"),
        (2, "2 ^ 7 / 2 ^ 6"),
        (64, "2 ^ 7 - 2 ^ 6"),
        (192, "2 ^ 7 + 2 ^ 6"),
        (8192, "2 ^ 7 * 2 ^ 6"),
        (1, "10 % 3"),
        (0, "10 % 2"),
        (5, "5 % 10"),
        (0, "42 % 1"),
        (0, "0 % 5"),
        (2, "10 % 3 + 1"),
        (2, "10 % (3 + 1)"),
        (0, "10 * 2 % 5"),
        (4, "20 % 6 * 2"),
        (12, "10 + 20 % 6"),
        (0, "10 % 4 % 2"),
    ]

    num_tests = len(TEST_CASES)
    num_ran = 0
    num_passed = 0
    failures = []

    def draw_progress_bar(current: int, total: int, bar_length: int = 40):
        progress = current / total
        filled = int(bar_length * progress)
        empty = bar_length - filled
        bar = "█" * filled + "-" * empty
        percent = int(progress * 100)
        print(f"\rTesting: [{bar}] {percent}% ({current}/{total})", end="", flush=True)

    def assert_compilation(expected: int, source_code: str):
        global num_ran, num_passed

        ast = Parser("1 " + source_code).parse_program()
        gen = Generator(ast)
        gen.walk_ast()
        gen.generate_assembly_file("temp.s")

        process = subprocess.run(["gcc", "-static", "-o", "temp.exe", "temp.s"])
        if process.returncode != 0:
            failures.append(
                f"GCC Compilation failed on: {source_code}\n\t\t{process.stderr.strip()}"
            )

        process = subprocess.run(["./temp.exe"])
        if process.returncode != expected:
            failures.append(
                f"{source_code} => {expected} expected, but got {process.returncode}"
            )
        else:
            num_passed += 1

        num_ran += 1
        draw_progress_bar(num_ran, num_tests)

    # main
    draw_progress_bar(0, num_tests)
    for case in TEST_CASES:
        assert_compilation(*case)

    print(f"\nPassed {num_passed}/{num_tests}. (passing rate: {num_passed/num_tests:.3%})")
    if failures:
        print("Failures:")
        for failure in failures:
            print(failure)
