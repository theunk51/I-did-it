from ast import MatchOr
from tokens import Token, BasicID as BID

class Lexer:

    def advance(self):
        if self.c == "\n":
            self.col = 0
            self.lineno += 1

        self.pos += 1
        if self.pos < len(self.text):
            self.c = self.text[self.pos]
        else:
            self.c = '\0'

    def number(self) -> Token:
        typ = BID.INTEGER
        point = False
        v = ''
        while self.c.isdigit() or self.c == '.':
            v += self.c
            self.advance()

            # check for decimal or 2nd decimal
            if self.c == '.' and not point:
                point = True
                typ = BID.FLOAT
            # else: raise SyntaxError(f"""Expected one decimal point but received two at line {self.lineno} column {self.col}""")
        return Token(typ, v)

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
        return Token(BID.STRING, v)
    
    def words(self) -> Token:
        """ tokenizes keywords and variables"""
        v = ''
        while self.c.isalnum() or self.c in ('$', '_'):
            v += self.c
            self.advance()
        
        if v.upper() == 'REM':
            while self.c != '\0' or self.c != '\n':
                v += self.c
                self.advance()
        
        up = BID.match(v.upper()) 
        return Token(BID.VARID, v) if up == None else Token(up, v.upper())

    def operators(self):
        f = self.c
        self.advance()
        
        m = BID.match(f)
        if m == None:
            f += self.c
            self.advance()
            m = BID.match(f)
            if m == None:
                raise Exception(f"Unknown character {f} as pos {self.pos}")
        return Token(m, f)

    def tokenize(self, text) -> list[Token]:
        self.reset()
        self.text = text
        self.c = text[self.pos]
        tokenList = []

        while self.c != '\0':
            while self.c.isspace() and self.c != '\n':
                self.advance()

            if self.c == '\n':
                self.advance()
                tokenList.append(Token(BID.NEWLINE, '\\n'))
            elif self.c.isdigit():
                t = self.number()
                tokenList.append(t)
            elif self.c.isalpha():
                t = self.words()
                tokenList.append(t)
            elif self.c in '+-*/=:;%()<>!,':
                t = self.operators()
                tokenList.append(t)
            elif self.c == '"':
                t = self.string()
                tokenList.append(t)
            elif self.c != '\0':
                raise SyntaxError(f"Unrecognized charater {self.c} as {self.pos}")
            
        return tokenList


    def __init__(self) -> None:
        self.pos = 0
        self.lineno = 1
        self.col = 0

    def reset(self):
        """ Reinitalizes/cleans the class without redefining """ 
        self.__init__()
    

