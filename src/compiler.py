from src.parser import Parser
from src.ast_nodes import *

class Compiler:
    """
    Converts the generated AST into x86-64 Assembly with AT&T syntax.
    """
    def __init__(self, source_code: str = ""):
        self.current_lineno = 0
        self.ast = Parser(source_code).parse_program()

        self.asm_text = []
        self.data_section = []
        self.globals = {}
        self._float_counter = 0

    def emit(self, instruction: str):
        self.asm_text.append(instruction)

    def error(self, message: str):
        raise Exception(f"Compiler Error at '{self.current_lineno}': {message}")

    def compile(self, node: ASTNode):
        """Dynamically dispatch to the correct compilation method."""
        method_name = f'__compile_{type(node).__name__}'
        compiler_method = getattr(self, method_name, self.no_compile_method)
        return compiler_method(node)

    def no_compile_method(self, node: ASTNode):
        raise Exception(f"No compile method defined for {type(node).__name__}")
        
    def _infer_type(self, node):
        """Basic type inference to decide between int and float instructions."""
        if isinstance(node, IntegerLiteral):
            return int
        elif isinstance(node, FloatLiteral):
            return float
        elif isinstance(node, InfixExpression):
            left_type = self._infer_type(node.left)
            right_type = self._infer_type(node.right)
            if left_type == float or right_type == float:
                return float
            return int
        return int # fallback
    
    def generate_asm_str(self):
        self.emit(".global _start")
        self.emit(".text")
        self.emit("_start:")
        self.emit("    pushq %rbp") # save the previous stack frame pointer
        self.emit("    movq %rsp, %rbp") # load the current frame pointer

        self.compile(self.ast)

        # exit program
        self.emit("    movq $60, %rax")  # syscall number for sys_exit
        self.emit("    xorq %rdi, %rdi") # exit code 0
        self.emit("    syscall")
        self.emit("")

        out = ""
        if self.data_section:
            out += ".data\n"
            out += "\n".join(self.data_section) + "\n\n"

        out += "\n".join(self.asm_text)
        
        if self.globals:
            out += "\n\n.bss\n"
            for g in self.globals:
                # .lcomm allocates memory in the bss section (8 bytes for a 64-bit int)
                out += f"    .lcomm global_{g}, 8\n"
            
        return out
    
    def __compile_Program(self, node: Program):
        for line_number, statement in sorted(node.statements.items()):
            self.current_lineno = line_number
            self.emit(f".L_line_{line_number}:")
            self.compile(statement)

    def __compile_IntegerLiteral(self, node: IntegerLiteral):
        self.emit(f"    pushq ${node.value}")

    def __compile_FloatLiteral(self, node: FloatLiteral):
        self._float_counter += 1
        label = f".L_float_{self._float_counter}"
        self.data_section.append(f"{label}: .double {node.value}")
        
        self.emit(f"    movsd {label}(%rip), %xmm0")
        self.emit( "    subq $8, %rsp")
        self.emit( "    movsd %xmm0, (%rsp)")

    def __compile_InfixExpression(self, node: InfixExpression):
        node_type = self._infer_type(node)
        left_type = self._infer_type(node.left)
        right_type = self._infer_type(node.right)
        
        self.compile(node.left)
        
        # If left was int but operation is float, convert left
        if left_type == int and node_type == float:
            self.emit("    popq %rax")
            self.emit("    cvtsi2sdq %rax, %xmm0")
            self.emit("    subq $8, %rsp")
            self.emit("    movsd %xmm0, (%rsp)")

        self.compile(node.right)
        
        # If right was int but operation is float, convert right
        if right_type == int and node_type == float:
            self.emit("    popq %rax")
            self.emit("    cvtsi2sdq %rax, %xmm0")
            self.emit("    subq $8, %rsp")
            self.emit("    movsd %xmm0, (%rsp)")

        if node_type == int:
            self.emit("    popq %rbx")
            self.emit("    popq %rax")
            
            if node.operator == '+':
                self.emit("    addq %rbx, %rax")
            elif node.operator == '-':
                self.emit("    subq %rbx, %rax")
            elif node.operator == '*':
                self.emit("    imulq %rbx, %rax")
            elif node.operator == '/':
                self.emit("    cqto")
                self.emit("    idivq %rbx")
                
            self.emit("    pushq %rax")
            
        elif node_type == float:
            self.emit("    movsd (%rsp), %xmm1")
            self.emit("    addq $8, %rsp")
            self.emit("    movsd (%rsp), %xmm0")
            self.emit("    addq $8, %rsp")
            
            if node.operator == '+':
                self.emit("    addsd %xmm1, %xmm0")
            elif node.operator == '-':
                self.emit("    subsd %xmm1, %xmm0")
            elif node.operator == '*':
                self.emit("    mulsd %xmm1, %xmm0")
            elif node.operator == '/':
                self.emit("    divsd %xmm1, %xmm0")
                
            self.emit("    subq $8, %rsp")
            self.emit("    movsd %xmm0, (%rsp)")
