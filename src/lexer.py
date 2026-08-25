from __future__ import annotations
from typing import Iterator
from tokens import TokenType, Token

class Lexer:
    def advance(self) -> None:
        """Advances the pointer and updates line/column trackers."""
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
        has_decimal = False
        v = ''
        while self.c.isdigit() or self.c == '.':
            v += self.c
            self.advance()

            # check for decimal or 2nd decimal
            if self.c == '.' and not has_decimal:
                has_decimal = True
                _type = TokenType.FLOAT
            else: 
                raise SyntaxError(f"Expected one decimal point but received two at line {self.lineno} column {self.col}")
        return Token(_type, v)

    def string(self) -> Token:
        # pass opeining quote
        self.advance()
        v = ''
        while self.c != '"' and self.c != '\0':
            v += self.c
            self.advance()
        if self.c == '\0':
            raise SyntaxError(f"Unmatched qoutes at line {self.lineno}")
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
        
        up = TokenType.match(v.upper()) 
        return Token(TokenType.VARID, v) if up == None else Token(up, v.upper())

    def operators(self) -> Token:
        f = self.c
        self.advance()
        
        m = TokenType.match(f)
        if m == None:
            f += self.c
            self.advance()
            m = TokenType.match(f)
            if m == None:
                raise Exception(f"Unknown character {f} as pos {self.pos}")
        return Token(m, f)

    def whitespace(self) -> None:
        while self.c.isspace() and self.c not in ('\0', '\n'):
            self.advance()

    def tokenize(self, text: str) -> Iterator[Token]:
        """Generates tokens one by one from the given source code"""
        self.__init__(text)
        while self.c != '\0':
            if self.c.isspace() and self.c != '\n':
                self.whitespace()
                continue
            
        if self.c == '\n':
            yield Token(TokenType.NEWLINE, '\\n')
            self.advance()
        elif self.c.isdigit():
            yield self.number()
        elif self.c.isalpha():
            yield self.keywords()
        elif self.c in '+-*/=:;%()<>!,':
            yield self.operators()
        elif self.c == '"':
            yield self.string()
        else:
            raise SyntaxError(f"Unrecognized character '{self.c}' at line {self.lineno} column {self.col}")
            
        # always yield an EOF token at the end so the parser knows to stop
        yield Token(TokenType.EOF, "EOF")
                    

    def __init__(self, text: str = ""):
        self.text = text
        self.pos = 0
        self.lineno = 1
        self.col = 0
        if self.text:
            self.c = self.text[self.pos]
        else:
            self.c = '\0'