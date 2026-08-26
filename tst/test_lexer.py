import pytest
from src.lexer import Lexer
from src.tokens import TokenType

OPERATOR_CASES = [
    ("+", TokenType.PLUS),
    ("-", TokenType.MINUS),
    ("*", TokenType.MUL),
    ("/", TokenType.DIV),
    ("%", TokenType.MOD),
    ("^", TokenType.EXPONENT),
    ("=", TokenType.EQ),
    ("<", TokenType.LT),
    (">", TokenType.GT),
    ("<=", TokenType.LTEQ),
    (">=", TokenType.GTEQ),
    ("<>", TokenType.NEQ),
    ("(", TokenType.LPAREN),
    (")", TokenType.RPAREN),
    (";", TokenType.SEMICOLON),
    (",", TokenType.COMMA),
    (":", TokenType.COLON),
]

KEYWORD_CASES = [
    ("IF", TokenType.IF),
    ("then", TokenType.THEN), 
    ("Else", TokenType.ELSE),
    ("FOR", TokenType.FOR),
    ("TO", TokenType.TO),
    ("STEP", TokenType.STEP),
    ("NEXT", TokenType.NEXT),
    ("PRINT", TokenType.PRINT),
    ("LET", TokenType.LET),
    ("True", TokenType.BOOLEAN)
]

IDENTIFIER_CASES = [
    ("A", TokenType.IDENTIFIER),
    ("X", TokenType.IDENTIFIER),
    ("B1", TokenType.IDENTIFIER),
    ("Z9", TokenType.IDENTIFIER),
    ("c5", TokenType.IDENTIFIER),
    ("FnD", TokenType.IDENTIFIER),
    ("SQR", TokenType.SQR),
    ("TAN", TokenType.TAN)
]


NUMBER_CASES = [
    ("123", TokenType.INTEGER, "123"),
    ("0", TokenType.INTEGER, "0"),
    ("3.14", TokenType.FLOAT, "3.14"),
    ("0.99", TokenType.FLOAT, "0.99"),
    ("1.", TokenType.FLOAT, "1."),
    (".123456", TokenType.FLOAT, ".123456")
]


@pytest.mark.parametrize("source, expected_type", OPERATOR_CASES + KEYWORD_CASES + IDENTIFIER_CASES)
def test_single_tokens(source, expected_type):
    lexer = Lexer(source)
    tokens = list(lexer)
    
    assert tokens[0].type == expected_type
    assert tokens[1].type == TokenType.EOF

@pytest.mark.parametrize("source, expected_type, expected_value", NUMBER_CASES)
def test_numbers(source, expected_type, expected_value):
    lexer = Lexer(source)
    tokens = list(lexer)
    
    assert tokens[0].type == expected_type
    assert tokens[0].value == expected_value

def test_strings():
    lexer = Lexer('"hello world"')
    tokens = list(lexer)
    
    assert tokens[0].type == TokenType.STRING
    assert tokens[0].value == "hello world"  # Should strip the quotes
    assert tokens[1].type == TokenType.EOF

def test_comments():
    lexer = Lexer("REM This is a comment\nLeT A = 1")
    tokens = list(lexer)
    
    assert tokens[0].type == TokenType.REM
    assert tokens[0].value == "REM This is a comment"
    assert tokens[1].type == TokenType.NEWLINE
    assert tokens[1].value == "\\n"
    assert tokens[-1].type == TokenType.EOF

def test_multiple_tokens_in_statement():
    lexer = Lexer("LET A1 = 10")
    tokens = list(lexer)
    
    assert tokens[0].type == TokenType.LET
    assert tokens[0].value == "LET"
    assert tokens[1].type == TokenType.IDENTIFIER
    assert tokens[1].value == "A1"
    assert tokens[2].type == TokenType.EQ
    assert tokens[2].value == "="
    assert tokens[3].type == TokenType.INTEGER
    assert tokens[3].value == "10"
    assert tokens[4].type == TokenType.EOF

def test_unclosed_string():
    lexer = Lexer('"unclosed')
    with pytest.raises(SyntaxError, match="Unmatched quotes"):
        list(lexer)

def test_too_many_decimals():
    lexer = Lexer("1.2.3")
    with pytest.raises(SyntaxError, match="Expected one decimal point"):
        list(lexer)

def test_unrecognized_char():
    lexer = Lexer("@")
    with pytest.raises(SyntaxError, match="Unrecognized character"):
        list(lexer)

def test_stop_iteration():
    lexer = Lexer('123')
    token = next(lexer)  # Token(INTEGER, '123')
    assert token.value == '123'
    assert token.type == TokenType.INTEGER

    token = next(lexer)
    assert token.value == '\0'
    assert token.type == TokenType.EOF

    with pytest.raises(StopIteration):
        next(lexer)
