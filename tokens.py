from enum import Enum

class Token:
    def __init__(self, type, value):
        self.type = type
        self.value = value

    def __repr__(self):
        return f"Token({self.value}, {self.type})"


class BasicID(Enum):
    EOF = -1 
    VARID = 0
    INTEGER = 1
    FLOAT = 2
    STRING = 3
    NEWLINE = 4

    IF = 5; THEN = 6; ELSE = 7

    MUL = 8
    DIV = 9
    MINUS = 10
    MOD = 11
    PLUS = 12
    RETURN = 13
    FOR = 14
    INPUT = 15
    AND = 16
    OR = 17
    NOT = 18
    EQ = 19
    NEQ = 20
    LT = 21
    GT = 22
    LTEQ = 23
    GTEQ = 24
    LET = 25
    TO = 26
    LPAREN = 27
    RPAREN = 28
    PRINT = 29
    LOAD = 30
    SAVE = 31
    COLON = 32
    SEMI = 33
    COMMA = 34
    REM = 35

    GOTO = 36
    GOSUB = 37
    STEP = 38
    NEXT = 39
    STOP = 40

    READ = 41
    OPEN = 42
    DATA = 43
    DIM = 44
    LIST = 45
    ON = 46


    PI = 55




    # NOTE: Find better waye of matching. this is too long and memory consuming 
    @classmethod
    def match(cls, name: str):
        """Matches string value with token token type."""
        if name == "IF": return cls.IF
        elif name == "THEN": return cls.THEN
        elif name == "ELSE": return cls.ELSE
        elif name == "FOR": return cls.FOR
        elif name == "TO": return cls.TO
        elif name == "AND": return cls.AND
        elif name == "NOT": return cls.NOT
        elif name == "OR": return cls.OR
        elif name == "INPUT": return cls.INPUT
        elif name == "REM": return cls.REM
        elif name == "LOAD": return cls.LOAD
        elif name == "SAVE": return cls.SAVE
        elif name == "PRINT": return cls.PRINT
        elif name == "LET": return cls.LET
        elif name == "RETURN": return cls.RETURN
        elif name == "GOTO": return cls.GOTO
        elif name == "GOSUB": return cls.GOSUB
        elif name == "STEP": return cls.STEP
        elif name == "NEXT": return cls.NEXT
        elif name == "STOP": return cls.STOP
        elif name == "READ": return cls.READ
        elif name == "OPEN": return cls.OPEN
        elif name == "DATA": return cls.DATA
        elif name == "DIM": return cls.DIM
        elif name == "LIST": return cls.LIST
        elif name == "ON": return cls.ON
        
        elif name == "*" : return cls.MUL
        elif name == "/" : return cls.DIV
        elif name == "+" : return cls.PLUS
        elif name == "-" : return cls.MINUS
        elif name == "%" : return cls.MOD
        elif name == "<" : return cls.LT
        elif name == "<=": return cls.LTEQ
        elif name == ">" : return cls.GT
        elif name == ">=": return cls.GTEQ
        elif name == "=" : return cls.EQ
        elif name == "!=": return cls.NEQ
        elif name == ":" : return cls.COLON
        elif name == ';' : return cls.SEMI
        elif name == ',' : return cls.COMMA
        elif name == '(' : return cls.LPAREN
        elif name == ')' : return cls.RPAREN

        elif name == "PI": return cls.PI
 
        else: return None

