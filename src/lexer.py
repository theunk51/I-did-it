from __future__ import annotations
from typing import Iterator
from .tokens import TokenType, Token

class Lexer:
    """
    A lexical analyzer that operates as an iterator (generator class), yielding one `Token` object at a time as it
    processes the input string. Once the end of the input is reached, it yields a final EOF token before raising 
    StopIteration for subsequent iterations.
    """
    def __init__(self, text: str = ""):
        self.text = text
        self.pos = 0
        self.lineno = 1
        self.col = 0

        if self.text:
            self.c = self.text[self.pos]
        else:
            self.c = '\0'

        self.has_eof_yielded = False

    def __iter__(self) -> Iterator[Token]:
        return self
    
    def __next__(self) -> Token:
        if self.c.isspace() and self.c != '\n':
            self.whitespace()   # skip whitespace

        if self.c == '\0':
            if self.has_eof_yielded == True:
                raise StopIteration()
            else:
                self.has_eof_yielded = True
                return Token(TokenType.EOF, "\0")            
        elif self.c == '\n':
            self.advance()
            return Token(TokenType.NEWLINE, '\\n')
        elif self.c.isdigit() or self.c == '.':
            return self.number()
        elif self.c.isalpha():
            return self.keywords()
        elif self.c in '+-*/=:;%()<>!,^':
            return self.operators()
        elif self.c == '"':
            return self.string()
        else:
            raise SyntaxError(f"Unrecognized character '{self.c}' at line {self.lineno} column {self.col}")
    
        
    def advance(self) -> None:
        """ Advances the text pointer and updates line/column trackers."""
        if self.c == "\n":
            self.col = 0
            self.lineno += 1
        
        self.col += 1
        self.pos += 1
        if self.pos < len(self.text):
            self.c = self.text[self.pos]
        else:
            self.c = '\0'

    def number(self) -> Token:
        _type = TokenType.INTEGER
        found_decimal = False
        v = ''
        while self.c.isdigit() or self.c == '.':
            # check for decimal or 2nd decimal
            if self.c == '.':
                if found_decimal:
                    raise SyntaxError(f"Expected one decimal point but received two at line {self.lineno} column {self.col}")
                found_decimal = True
                _type = TokenType.FLOAT

            v += self.c
            self.advance()
            
        return Token(_type, v)

    def string(self) -> Token:
        # pass opeining quote
        self.advance()
        v = ''
        while self.c != '"' and self.c != '\0':
            v += self.c
            self.advance()
        if self.c == '\0':
            raise SyntaxError(f"Unmatched quotes at line {self.lineno}")
        self.advance()
        return Token(TokenType.STRING, v)
    
    def keywords(self) -> Token:
        """Tokenizes keywords, comments, and variables."""
        v = ''
        while True:
            v += self.c
            self.advance()

            if not self.c.isalnum() or self.c in ("$", "_"):
                break
        
        if v.upper() == 'REM':
            while self.c != '\0' and self.c != '\n':
                v += self.c
                self.advance()
            return Token(TokenType.REM, v)
        
        up = TokenType.find_type(v.upper())
        if up == None:
            return Token(TokenType.IDENTIFIER, v)
        return Token(up, v.upper())

    def operators(self) -> Token:
        one_char = self.c
        self.advance()

        two_char = one_char + self.c
        match_two = TokenType.find_type(two_char)
        if match_two is not None:
            self.advance()  # consume second char
            return Token(match_two, two_char)

        match_one = TokenType.find_type(one_char)
        if match_one is not None:
            return Token(match_one, one_char)
        
        raise Exception(f"Unknown character {one_char} as pos {self.pos}")

    def whitespace(self) -> None:
        while self.c.isspace() and self.c not in ('\0', '\n'):
            self.advance()
