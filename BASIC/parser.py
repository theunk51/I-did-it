from tokens import BasicID as Bt
from nodes import *
# : COLON is a the line seperator

class Parser:
    def __init__(self) -> None:
        pass

    def parse(self, tokens):
        self.pos = 0
        self.__tokens = tokens
        self.token = tokens[self.pos]
        self.lineno = 0

        stmts = []
        while self.pos < len(self.__tokens):
            self.parse_linenum()
            stmts.append(LineRoot(self.lineno, self.statements()))
            self.advance()
        #     s = []
        #     self.parse_linenum()
        #     while self.pos < len(self.__tokens) and self.token.type != Bt.NEWLINE:
        #         s.append(self.statements())
            
        #     # self.consume(Bt.NEWLINE)
        #     self.advance()
        #     stmts.append(LineRoot(self.lineno, s))
        return stmts

    def advance(self):
        self.pos += 1
        if self.pos < len(self.__tokens):
            self.token = self.__tokens[self.pos]
        
    def consume(self, *expected):
        for typ in expected:
            if self.token.type == typ:
                self.advance()
                return None
        raise Exception(f"Expected type(s) {expected}. Got {self.token.type}")

    def parse_linenum(self):
        if self.token.type == Bt.INTEGER:
            self.lineno = int(self.token.value)
            self.advance()
        else:
            print(self.token.type)
            raise Exception(f"INVALID LINE NUMBER: {self.token}, {self.pos}")

    def logical(self):
        """ logical : log_not ((AND|OR) log_not))* """
        left = self.log_not()
        while self.token.type in (Bt.NOT, Bt.AND):
            op = self.token
            self.consume(Bt.AND, Bt.NOT)
            right = self.log_not()
            left = Binary(left, op, right)

        return left

    def log_not(self):
        """ not : NOT relation | relation """
        if self.token.type == Bt.NOT:
            op = self.token
            self.consume(Bt.NOT)
            right = self.relation()
            return Unary(op, right)
        else:
            return self.relation()

    def relation(self):
        """ relation : term ((rel_op) term)* """
        left = self.expression()

        while self.token.type in (Bt.GTEQ, Bt.GT, Bt.LTEQ, Bt.LT, Bt.EQ, Bt.NEQ):
            op = self.token
            self.consume(Bt.GTEQ, Bt.GT, Bt.LTEQ, Bt.LT, Bt.EQ, Bt.NEQ)
            right = self.expression()
            left = Binary(left, op, right)
        return left

    def expression(self):
        left = self.term()

        while self.token.type in (Bt.MINUS, Bt.PLUS):
            op = self.token
            self.consume(Bt.MINUS, Bt.PLUS)
            right = self.term()
            left = Binary(left, op, right)
        return left

    def term(self):
        left = self.factor()

        while self.token.type in (Bt.MUL, Bt.MOD, Bt.DIV):
            op = self.token
            self.consume(Bt.MUL, Bt.DIV, Bt.MOD)
            right = self.factor()
            left = Binary(left, op, right)
        return left

    def factor(self):
        """
        factor : VARIABLE | INT | FLOAT | STRING | (expression)
        unary  : ((PLUS|MINS) factor)* | factor
        """
        token = self.token
        if token.type in (Bt.PLUS, Bt.MINUS):
            self.consume(Bt.PLUS, Bt.MINUS)
            right = self.factor()
            return Unary(token, right)
        elif token.type == Bt.LPAREN:
            self.consume(Bt.LPAREN)
            group = self.expression()
            self.consume(Bt.RPAREN)
            return Grouping(group)
        elif token.type in (Bt.INTEGER, Bt.FLOAT, Bt.STRING, Bt.VARID):
            self.consume(Bt.INTEGER, Bt.FLOAT, Bt.STRING, Bt.VARID)
            return Literal(token)

    def statements(self):
        if self.token.type == Bt.LET:
            self.consume(Bt.LET)
            return self.assignment()
        elif self.token.type == Bt.IF:
             return self.ifstmt()
        elif self.token.type == Bt.FOR:
            return self.forstmt()
        elif self.token.type == Bt.PRINT:
            return self.printstmt()
        elif self.token.type == Bt.REM:
            pass
        # impplement support for vars by themselves
        # elif self.token.type == Bt.NEWLINE:
        #     self.consume(Bt.NEWLINE)
        #     self.parse_linenum()
        else:
            
            return self.logical()
            
    def assignment(self):
        """ LET VARIABLE = expression """
        name = self.token.value
        self.consume(Bt.VARID)

        self.consume(Bt.EQ)
        value = self.expression()
        return Assignment(name, value)

    def functions(self):
        """ function : VARIABLE(parameters?) 
            parameters := VARIABLE(VARIABLE (, VARIABLE)?*)
        """
        name = self.token
        self.advance()

        # exceptions: PI,
        if name.type == Bt.PI:
            return Function(name, args=None)
        else:
            args = []
            self.consume(Bt.LPAREN)
            while self.token.type != Bt.RPAREN:
                a = self.expression()
                args.append(a)
                # move pass arg
                # self.advance()
                # pass comma
                self.consume(Bt.COMMA)
            self.consume(Bt.RPAREN)
            return Function(name, args)

    def ifstmt(self):
        """ if_stmt := IF expression THEN statement (ELSE statement)?"""
        self.consume(Bt.IF)
        ifcon = self.logical()
        self.consume(Bt.THEN)
        thencon = self.statements()
        elsecon = None
        # self.token should be ELSe
        if self.token.type == Bt.ELSE:
            self.consume(Bt.ELSE)
            elsecon = self.statements()
        
        return Conditional(ifcon, thencon, elsecon)

    def forstmt(self):
        """ for_stmt := FOR variable = <expression> TO <expression> [STEP <expression>] """
        self.consume(Bt.FOR)
        # should be variable
        var = self.token.value
        self.consume(Bt.VARID)

        self.consume(Bt.EQ)
        start = self.expression()

        self.consume(Bt.TO)
        end = self.expression()
        
        step = 1
        if self.token.type == Bt.STEP:
            self.consume(Bt.STEP)
            step = self.expression()
        
        return ForLoop(var, start, end, step)
    
    def printstmt(self):
        """print_stmt ::=  PRINT <print list> 
                        | expression <print list>
                        | ';' <print list> 
        """
        self.consume(Bt.PRINT)
        p = []
        while self.pos < len(self.__tokens) and self.token.type != Bt.NEWLINE:
            if self.token.type == Bt.STRING:
                p.append(self.token.value)
                self.consume(Bt.STRING)
            elif self.token.type == Bt.COMMA:
                p.append(" ")
                self.consume(Bt.COMMA)
            elif self.token.type == Bt.SEMI:
                self.consume(Bt.SEMI)
            else:
                p.append(self.logical())
        return Print(p)

            
