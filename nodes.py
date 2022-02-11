# from __future__ import annotations
from tokens import BasicID


class AST:
    def __init__(self):
        pass

    def visit(self):
        pass

    def __repr__(self):
        return str(self)
    
class Unary():
    def __init__(self, op, right):
        self.right = right
        self.op = op

    def __repr__(self):
        return f"Unary({self.op.value},{self.right})"
    
class Grouping():
    def __init__(self, expression):
        self.expression = expression

    def __str__(self):
        return f"({self.expression})"

    def visit(self):
        return self.expression.visit()

class Binary():
    _name = "Binary"
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

    def __repr__(self):
        return f"BinOp({self.left}, {self.op.value}, {self.right})"
    
class Literal():
    def __init__(self, token):
        self.token = token

    def __repr__(self):
       # return str(self.token.value)
       return f"Lit({self.token.value})"

class Function():
    def __init__(self, name, args):
        self.name = name.value
        self.type = name.type    # Token type
        self.args = args


    def __repr__(self):
        if not self.args:
            return self.name
        else:
            return f"{self.name}{*self.args,}"
    
    def visit(self):
        pass

class Assignment():
    def __init__(self, name: str, value):
        self.name = name
        self.value = value
    
    def __repr__(self):
        return f"Assignment({self.name}, {self.value})"
    
class Conditional():
    def __init__(self, ifbr, thenbr, elsebr):
        self.if_branch = ifbr
        self.then_branch = thenbr
        self.else_branch = elsebr

    def __repr__(self):
        # return f"IF {self.if_branch} THEN {self.then_branch} ELSE {self.else_branch}"
        return f"Condition({self.if_branch}, {self.then_branch}, {self.else_branch})"

class ControlFlow():
    """ 
    represents GOTO, GOSUB, and RETURN statments 
    """

    GOTO = 1
    GOSUB = 2
    RETURN = 0
    NEXT = 3
    STOP = -1
    def __init__(self, flow_type: str, expr):
        """ 
        flow_type  = "GOTO", "GOSUB", "RETURN" or "NEXT"
        """
        if flow_type.upper() in ("GOTO", "GOSUB", "RETURN", "NEXT", "STOP"):
            self.type = flow_type
        else: 
            raise ValueError(f"ControlFlow node recived invalid type {flow_type}")

        if flow_type in ("RETURN", "STOP") and expr != None:
            raise ValueError("Receive value for RETURN expr")

class ForLoop():
    def __init__(self, lvar:str, start:int, stop:int, step:int):
        self.start = start
        self.stop = stop
        self.step = step
        self.lvar = lvar

    def __repr__(self):
        return f"Loop({self.lvar}={self.start}, {self.stop}, {self.step})"

class Print():
    def __init__(self, exprs: list) -> None:
        self.exprs = exprs

    def __repr__(self) -> str:
        return f"Print({', '.join(str(x) for x in self.exprs)})"

class LineRoot():
    """ represents all the ASTs on a line """
    _name = "LineRoot"
    def __init__(self, lineno, asts) -> None:
        self.lineno = lineno
        self.body = asts

    def __repr__(self) -> str:
        return f"LINE: {self.lineno} CHILDREN: {self.body}"
        # return f"Line({self.lineno}, {self.body})"

class Next():
    def __init__(self, var):
        self.var = var

    def __repr__(self):
        return f"Next {self.var}"

class Input():
    def __init__(self, question: str, vars: list):
        self.vars = vars
        self.question = question
    
    def __repr__(self):
        return f"Input({self.question}, {self.vars})"


class Arrays:
    def ___init__(self, arrays: list):
        self.arrays = arrays

    def __repr__(self):
        return ", ".join([str(a) for a in self.arrays]) 


class Dim:
    """ Represents DIM assigment """
    def __init__(self, name, dimensions):
        self.dims = dimensions
        self.name = name

    def __repr__(self) -> None:
        self


class On:
    pass

class Data:
    def __init__(self, data):
        self.data = data

    def __repr__(self):
        return f"Data: {self.data}"

class Read:
    def __init__(self, varlist: list):
        self.vars = varlist
    
    def __repr__(self):
        return f"Read({self.vars})"
    

