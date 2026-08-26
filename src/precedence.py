from src.tokens import TokenType, BUILTIN_FUNCTIONS

RIGHT_ASSOCIATIVE = frozenset([TokenType.EXPONENT])

class Precedence:
    NONE = 0
    ASSIGNMENT = 10  # =
    OR = 20          # or
    AND = 30         # and
    EQUALITY = 40    # == !=
    COMPARISON = 50  # < > <= >=
    TERM = 60        # + -
    FACTOR = 70      # * /
    POWER = 75       # ^
    UNARY = 80       # ! - +
    CALL = 90        # . () []
    PRIMARY = 100

    RULES = {
        TokenType.EQ: EQUALITY,
        TokenType.NEQ: EQUALITY,
        TokenType.LT: COMPARISON,
        TokenType.GT: COMPARISON,
        TokenType.LTEQ: COMPARISON,
        TokenType.GTEQ: COMPARISON,
        TokenType.PLUS: TERM,
        TokenType.MINUS: TERM,
        TokenType.MUL: FACTOR,
        TokenType.DIV: FACTOR,
        TokenType.MOD: FACTOR,
        TokenType.EXPONENT: POWER,
        TokenType.LPAREN: CALL,          # Function calls / grouping bind the tightest
    }

    @classmethod
    def is_right_associative(cls, token_type: TokenType) -> bool:
        """Returns True if the token type is right-associative."""
        return token_type in RIGHT_ASSOCIATIVE

    @classmethod
    def get_prec(cls, token_type: TokenType) -> int:
        """Returns the precedence of a given token type."""
        return cls.RULES.get(token_type, cls.NONE)

for func in BUILTIN_FUNCTIONS:
    Precedence.RULES[func] = Precedence.CALL

__all__ = ['Precedence']