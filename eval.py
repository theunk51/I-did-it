from tokens import BasicID as Bt

def debug(*s):
    print("DEBUG: ",'\033[40m', *s, '\033[0m')


class Interpreter:
    def __init__(self):
        # store the entire program in <line num> = AST
        self.program = {}
        self.vars = {}

        # current executed line number
        self.lineno = 0
        # records line number thath need to be returned
        self.returns = []
        # pointer to line index in sorted
        self.index = 0

    def interpret(self, program: list):
        for line in program:
            self.program[line.lineno] = line.body

        self.index = 0
        line_numbers = list(self.program.keys())
        line_numbers.sort()
        # debug(self.program)
        print(f"LNS: {line_numbers}")
        while self.index < len(program):
           self.set_next_lineno(line_numbers[self.index])
           ast = self.program[self.lineno]
           debug(self.lineno, ast)
           self.visit(ast)
           self.index += 1
        
    def visit(self, node):
        """ Gets the correct node visitor function and visitr """
        method_name = f"visit{type(node).__name__}"
        method = getattr(self, method_name, self.__error)
        return method(node)

    def __error(self, node):
        """rasises and error is method attribute is not found"""
        raise AttributeError(f"Interpreter has no method visit{type(node).__name__}")

    def visitBinary(self, node):
        if node.op.type == Bt.PLUS: 
            return self.visit(node.left) + self.visit(node.right)
        elif node.op.type == Bt.MINUS:
            return self.visit(node.left) - self.visit(node.right)
        elif node.op.type == Bt.MUL:
            return self.visit(node.left) * self.visit(node.right)
        elif node.op.type == Bt.DIV:
            return self.visit(node.left) / self.visit(node.right)
        elif node.op.type == Bt.MOD:
            return self.visit(node.left) % self.visit(node.right)

        elif node.op.type == Bt.EQ:
            return self.visit(node.left) == self.visit(node.right)
        elif node.op.type == Bt.NEQ:
            return self.visit(node.left) != self.visit(node.right)
        elif node.op.type == Bt.GT:
            return self.visit(node.left) > self.visit(node.right)
        elif node.op.type == Bt.LT:
            return self.visit(node.left) < self.visit(node.right)
        elif node.op.type == Bt.LTEQ:
            return self.visit(node.left) <= self.visit(node.right)
        elif node.op.type == Bt.GTEQ:
            return self.visit(node.left) >= self.visit(node.right)

        elif node.op.type == Bt.AND:
            return self.visit(node.left) and self.visit(node.right)
        elif node.op.type == Bt.OR:
            return self.visit(node.left) or self.visit(node.right)

    def visitLiteral(self, node):
        if node.token.type == Bt.INTEGER:    
            return int(node.token.value)
        elif node.token.type == Bt.FLOAT: 
            return float(node.token.value)
        elif node.token.type == Bt.VARID:
            x = self.vars.get(node.token.value, None)
            if not x: raise NameError(f"\'{node.token.value}\' not defined")
            return x
        else: return node.token.value
              
    def visitAssignment(self, node):
        self.vars[node.name] = self.visit(node.value)
        print(self.vars)


    def set_next_lineno(self, ln):
        self.lineno = ln


    
