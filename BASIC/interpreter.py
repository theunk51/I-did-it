from tokens import BasicID as Bt

def debug(statement): 
    print('\033[41m', statement, '\033[0m')

class Interpreter:
    

    def __init__(self) -> None:
        self.vars = {}
        # stores the entire program as <line num> = AST
        self.program = {}

        # records linenumbers of reteun statements
        self.returns = []

        self.next_line = 0

    def interpret(self, trees: list):
        for tree in trees:
            self.program[tree.lineno] = tree.body

        debug(self.program)


        
    # HACK: give vevery node type a self._name var to refer to

    def visit(self, node):
        """ Gets the correct node visitor function and visitor """
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
        elif node.op.type == Bt.MODULO:
            return self.visit(node.left) % self.visit(node.right)

        elif node.op.type == Bt.EQUAL:
            return self.visit(node.left) == self.visit(node.right)
        elif node.op.type == Bt.NOTEQUAL:
            return self.visit(node.left) != self.visit(node.right)
        elif node.op.type == Bt.GREATER:
            return self.visit(node.left) > self.visit(node.right)
        elif node.op.type == Bt.LESSER:
            return self.visit(node.left) < self.visit(node.right)
        elif node.op.type == Bt.LESSTHAN:
            return self.visit(node.left) <= self.visit(node.right)
        elif node.op.type == Bt.GREATTHAN:
            return self.visit(node.left) >= self.visit(node.right)

        elif node.op.type == Bt.AND:
            return self.visit(node.left) and self.visit(node.right)
        elif node.op.type == Bt.OR:
            return self.visit(node.left) or self.visit(node.right)

    def visitLiteral(self, node):
        if node.token.type == Bt.INT:    
            return int(node.token.value)
        elif node.token.type == Bt.FLOAT: 
            return float(node.token.value)
        elif node.token.type == Bt.VARIABLE:
            x = self.GLOBALS.get(node.value, None)
            if not x: raise NameError(f"\'{node.name}\' not defined")
            return x
        else:
            return node.token.value
    
    def visitAssignment(self, node):
        self.vars[node.name] = self.visit(node.value)
        print(self.vars)


    def __execute(self):
        line_numbers = list(self.program.keys()).sort()

        if 0 < len(line_numbers):
            # pointer to each line in sorted line numbers
            # increments by 1 unless modifed by jump (GOTO, FOR, GOSUB, RETURN)
            index = 0
            self.next_line = line_numbers[index]

            self.visit(self.program[self.next_line])

        else:
            raise RuntimeError("No statements to execute")


        