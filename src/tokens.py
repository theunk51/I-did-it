from enum import Enum, auto, unique

class Token:
    def __init__(self, type, value):
        self.type = type
        self.value = value

    def __repr__(self):
        return f"Token({self.value}, {self.type})"

@unique
class TokenType(Enum):
    # Miscellaneous
    EOF = -1
    IDENTIFIER = auto()
    INTEGER = auto()
    FLOAT = auto()
    STRING = auto()
    BOOLEAN = auto()
    NEWLINE = auto()

    # Keywords
    IF = auto()
    THEN = auto()
    ELSE = auto()
    FOR = auto()
    TO = auto()
    STEP = auto()
    NEXT = auto()
    INPUT = auto()
    PRINT = auto()
    LET = auto()
    RETURN = auto()
    GOTO = auto()
    GOSUB = auto()
    STOP = auto()
    READ = auto()
    DATA = auto()
    DIM = auto()
    REM = auto()
    
    # Logical Operators
    AND = auto()
    OR = auto()
    NOT = auto()

    # Arithmetic Operators
    PLUS = auto()
    MINUS = auto()
    MUL = auto()
    DIV = auto()
    MOD = auto()
    EXPONENT = auto()

    # Relational Operators
    EQ = auto()
    NEQ = auto()
    LT = auto()
    GT = auto()
    LTEQ = auto()
    GTEQ = auto()

    # Punctuation / Delimiters
    LPAREN = auto()
    RPAREN = auto()
    COLON = auto()
    SEMICOLON = auto()
    COMMA = auto()

    # Built-in Math Functions
    SIN = auto()
    COS = auto()
    TAN = auto()
    ATN = auto()
    EXP = auto()
    LOG = auto()
    ABS = auto()
    SQR = auto()
    INT = auto()
    RND = auto()


    @classmethod
    def find_type(cls, name: str):
        """Matches string value with token type."""
        symbols = {
            "^": cls.EXPONENT, "*": cls.MUL, "/": cls.DIV, "+": cls.PLUS, "-": cls.MINUS,
            "%": cls.MOD, "<": cls.LT, "<=": cls.LTEQ, ">": cls.GT,
            ">=": cls.GTEQ, "=": cls.EQ, "<>": cls.NEQ, ":": cls.COLON,
            ";": cls.SEMICOLON, ",": cls.COMMA, "(": cls.LPAREN, ")": cls.RPAREN
        }
        
        if name in symbols:
            return symbols[name]

        # For keywords like "IF", "THEN", look them up directly via the Enum class
        try:
            name = name.upper()
            if name in ("TRUE", "FALSE"):
                return cls.BOOLEAN
            else:
                return cls[name]
        except Exception:
            return None


KEYWORDS = frozenset([
    TokenType.IF, TokenType.THEN, TokenType.ELSE, TokenType.FOR, 
    TokenType.TO, TokenType.STEP, TokenType.NEXT, TokenType.INPUT, 
    TokenType.PRINT, TokenType.LET, TokenType.RETURN, TokenType.GOTO, 
    TokenType.GOSUB, TokenType.STOP, TokenType.READ, TokenType.DATA, 
    TokenType.DIM, TokenType.REM
])

ARITHMETIC_OPERATORS = frozenset([
    TokenType.MUL, TokenType.DIV, TokenType.PLUS, TokenType.MINUS, TokenType.MOD, TokenType.EXPONENT
])

RELATIONAL_OPERATORS = frozenset([
    TokenType.EQ, TokenType.NEQ, TokenType.LT, TokenType.GT, TokenType.LTEQ, TokenType.GTEQ
])

LOGICAL_OPERATORS = frozenset([
    TokenType.AND, TokenType.OR, TokenType.NOT
])

OPERATORS = ARITHMETIC_OPERATORS | RELATIONAL_OPERATORS | LOGICAL_OPERATORS

LITERAL_TYPES = frozenset([ TokenType.INTEGER, TokenType.FLOAT, TokenType.STRING, TokenType.IDENTIFIER, TokenType.BOOLEAN ])

BUILTIN_FUNCTIONS = frozenset([
    TokenType.SIN, TokenType.COS, TokenType.TAN, TokenType.ATN, 
    TokenType.EXP, TokenType.LOG, TokenType.ABS, TokenType.SQR, 
    TokenType.INT, TokenType.RND
])

