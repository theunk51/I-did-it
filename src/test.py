from lexer import Lexer
from tokens import BasicID as Bt, Token

def debug(*s, code='\033[40m'): 
    print("DEBUG: ", code, *s, '\033[0m')



# THis time use tokens as asts sort of
class AST:
    def __init__(self, token):
        self.lineno = None
        self.token = token
        self.children = []

    def set_linenum(self, ln: int):
        self.lineno = ln

    def add_child(self, child):
        self.children.append(child)

    def add_children(self, children):
        for c in children:
            self.children.append(c)
    
    def _pass(self, _):
        """ Has no use in practicality. Only used for clean code purposes """
        return self

    def finalize(self): 
        return self

    def __repr__(self):
        return f"AST(Lineno: {self.lineno}, children: {*self.children,})"

def combine(x, y) -> AST:
    """
    combines a token with another to from an AST that could be used for unary purposes
    """
    a = AST(Token(x.type, None))
    a.add_child(y)
    return a

    
class Parser:
    def advance(self, inc=1):
        self.pos += inc
        if self.pos < len(self.tokens):
            self.token = self.tokens[self.pos]
        else:
            self.token = None
    
    def parse(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.token = self.tokens[self.pos]

    
        a = AST(Token(Bt.ROOT, None))
        self.advance()

        while self.token != None:
            ln = self.parse_linenum()
            self.parse_statements(n, a)
            self.advance() # pass newline

    def parse_linenum(self):
        if self.token.type == Bt.INTEGER:
            self.lineno = int(self.token.value)
            self.advance()       
        else:
            # print(self.token.type)
            raise Exception(f"INVALID LINE NUMBER: {self.token}, {self.lineno}")

    def match(self, *ttypes) -> AST:
        """ 
        Matches token to expected type; similar to `consume` in other versions

        :return: AST
        """

        if self.token.type != ttype:
            raise SyntaxError(f"Got {self.token.type}. Expeced {ttype} on line {self.lineno}")
        
        a = AST(self.token)
        self.advance()
        return a

    def parse_statements(ln, root: AST):
        a = self.expression()
        a.set_linenum(ln)
        root.add_child(a)

        while self.token == Bt.NEWLINE:
            self.advance()
            root.add_child(self.expression())
        

    def factor(self):
        token = self.token
        if token.type in (Bt.PLUS, Bt.MINUS):
            self.consume(Bt.PLUS, Bt.MINUS)
            right = self.factor()
            
        elif token.type in (Bt.INTEGER, Bt.FLOAT, Bt.STRING, Bt.VARID):
            self.advance()
            

    def endstmt(self):
        self.match(Bt.EN)




if __name__ == "__main__":
    l = Lexer()
    p = Parser()
    i = Interpreter()

