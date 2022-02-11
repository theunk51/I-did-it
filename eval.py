from tokens import BasicID as Bt
from nodes import *
from collections import namedtuple

def debug(*s, code='\033[40m'): 
    print("DEBUG: ", code, *s, '\033[0m')


# get rid of namedTuple and just make it a tuple and index it
# LoopFrame = namedtuple('LFrame', 'var end step line_idx')


class Interpreter:
    def __init__(self):
        # store the entire program in <line num> = AST
        self.program = {}
        self.vars = {}
        # current executed line number
        self.lineno = None
        # records line numbers that need to be returned
        self.return_stack = []
        # pointer to line index in sorted linenums
        self.index = 0
        # keeps track for ForLoop frames
        self.loop_stack = []

    def visit(self, node):
        """ Gets the correct node visitor function and visitr """
        method_name = f"visit{type(node).__name__}"
        method = getattr(self, method_name, self.__error)
        return method(node)

    def __error(self, node):
        """rasises and error is method attribute is not found"""
        raise AttributeError(f"Interpreter has no method visit{type(node).__name__}")

    def interpret(self, program: list):

        # NOTE: change index and line_numbers to local variables
        for line in program:
            self.program[line.lineno] = line.body

        self.line_numbers = list(self.program.keys())
        self.line_numbers.sort()

        self.set_next_lineno(self.line_numbers[self.index])

        """   
        # print(f"LNS: {line_numbers}")
        while self.index < len(program):
           ast = self.program[self.lineno]
           debug(self.lineno, ast, self.index)
           # returns the next line num
           line = self.visit(ast)
           if line 
        """
        while True:
            if self.lineno not in self.line_numbers:
                raise RuntimeError(f"{self.lineno} not found")
            stmt = self.program[self.lineno]
            debug(self.lineno, stmt, self.index)
            line = self.visit(stmt)

            # process line numbers
            if line == None:        # execute next line
                try:
                    self.index += 1
                    self.set_next_lineno(self.line_numbers[self.index])
                except:
                    break # program complete
            elif line:
                debug(f"Going to line {line} from line {self.lineno}", code="\033[32;1m")
                self.index = self.line_numbers.index(line)
                self.set_next_lineno(line)
            elif line < 0:  # return
                self.index = -line
                self.set_next_lineno(self.line_numbers[self.index])



 
    def visitControlFlow(self, node: ControlFlow):
        if node.flow_type == "RETURN":
            idx = self.return_stack.pop()
            return -idx

        elif node.flow_type == "GOTO":
            # returns to the line to jump to
            return self.visit(node.expr)

        elif node.flow_type == "GOSUB":
            self.return_stack.append(self.index+1)
            return self.visit(node.expr)

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
        self.assign(node.name, self.visit(node.value))
        print('\033[33m', self.vars, '\033[0m')

    def visitPrint(self, node: Print):
        s = ''
        for i in node.exprs:
            if type(i) == str:
                s += i
            else:
                s += str(self.visit(i))

        print('\033[33m',s, '\033[0m')

    def visitUnary(self, node: Unary):
        if node.op.type == Bt.NOT:
            return not self.visit(node.right)
        elif node.op.type == Bt.PLUS:
            return self.visit(node.right)
        elif node.op.type == Bt.MINUS:
            return -self.visit(node.right)

    def visitConditional(self, node):
        # returns None if initial conditonal 
        # is fasle and there it note a defined elese branch
        cond = self.visit(node.if_branch)
        # check if initial conditon is true
        if cond:
            return self.visit(node.then_branch)
        else:
            if node.else_branch:
                return self.visit(node.else_branch)
    
    def visitForLoop(self, node: ForLoop) -> None:
        """
        creates a ForLoop 'frame' that consists of:
            line number - which line the loop is one
            loop_var - the variable referenced in loop
            stop, and step variables
        :return: None
        """
        # ForLoop(lvar, start, stop, step)
        start = self.visit(node.start)
        step  = node.step if type(node.step) == int else self.visit(node.step)
        stop  = self.visit(node.stop)   #self.visit(node.stop)
        # assign loop variable to variables
        self.assign(node.lvar, start)

        # change goto next line bc self.lineo reinitializes the loop
        
        # frame = tuple(loop_var, stop, step, line_after)
        frame = (node.lvar, stop, step, self.line_numbers[self.index+1])
        self.loop_stack.append(frame)
        debug(f"{self.lineno} assigned {frame} to stack")

    def visitNext(self, node: Next):
        if self.loop_stack == []:
            raise RuntimeError(f"No loops have been defined before {self.lineno}")
        # find matching loop var
    
        for frame in self.loop_stack:
            if frame[0] == node.var:
                
                self.vars[frame[0]] += frame[2]
                #self.index = self.line_numbers.index(frame.line)
                # self.set_next_lineno(frame.line)
                # debug(f"LINE: {self.lineno}  IDX:{self.index}")
                
                if ((frame[2] > 0 and self.vars[frame[0]] <= frame[1])
                    or frame[2] < 0 and self.vars[frame[0]] >= frame[1]):
                    return frame[3]

    def set_next_lineno(self, ln) :
        self.lineno = ln

    def assign(self, name, value) -> None:
        """ assigns variables to Enviroment """
        self.vars[name] = value

    
