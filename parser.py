from tokens import BasicID as Bt
from nodes import *

#rgb_to_ansi = lambda r, g, b : f"\033[38;2;{r};{g};{b}m"
# : COLON is a the line seperator

class Parser:
    def __init__(self) -> None:
        pass

    def parse(self, tokens):
        self.pos = 0
        self.__tokens = tokens
        self.token = tokens[self.pos]
        self.lineno = 0

        #color = rgb_to_ansi(13, 145, 33)

        stmts = []
        while self.pos < len(self.__tokens):
            self.parse_linenum()
            # print('\033[41m', s, '\033[0m')
            stmts.append(LineRoot(self.lineno, self.statements()))
            self.advance()  # pass newline
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
        raise Exception(f"Expected type(s) {expected}. Got {self.token.type}\nLine: {self.lineno}")

    def parse_linenum(self):
        if self.token.type == Bt.INTEGER:
            self.lineno = int(self.token.value)
            self.advance()       
        else:
            # print(self.token.type)
            raise Exception(f"INVALID LINE NUMBER: {self.token}, {self.lineno}")




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
        elif self.token.type == Bt.VARID:
            return self.assignment()
        elif self.token.type == Bt.IF:
             return self.ifstmt()
        elif self.token.type == Bt.FOR:
            return self.forstmt()
        elif self.token.type == Bt.PRINT:
            return self.printstmt()
        elif self.token.type == Bt.REM:
            self.consume(Bt.REM)
        elif self.token.type == Bt.NEXT:
            return self.nextstmt()
        elif self.token.type == Bt.GOSUB:
            return self.gosubstmt()
        elif self.token.type == Bt.GOTO:
            return self.gotostmt()
        elif self.token.type == Bt.RETURN:
            return self.returnstmt()
        elif self.token.type == Bt.STOP:
            return self.stopstmt()
        elif self.token.type == Bt.DATA:
            return self.datastmt()
        elif self.token.type == Bt.READ:
            return self.readstmt()
        elif self.token.type == Bt.DIM:
            return self.dimstmt()


    
    def readstmt(self):
        self.consume(Bt.READ)
        v = []
        while self.token.type == Bt.VARID:
            v.append(self.token.value)
            self.consume(Bt.VARID)
            self.consume(Bt.COMMA)
        return Read(v)

    def datastmt(self):
        self.consume(Bt.DATA)
        v = [self.token.value]
        self.advance()

        while self.token.type == Bt.COMMA:
            self.consume(Bt.COMMA)
            v.append(self.token.value)
            self.advance()
        
        return Data(v)
        
    def dimstmt(self):
        """ dim_stmt ::= DIM [VARIABLE(INT (, INT)*) ','?]* """
        self.consume(Bt.DIM)
        arrays = [self.__dim_definition()]

        # MSBASIC allows dims of multiple arrays delimited by commas
        while self.token.type == Bt.COMMA:
            self.consume(Bt.COMMA)
            arrays.append(self.__dim_definition())

        return Holder(arrays)
        
    def __dim_definition(self):
        """ dim_def ::= VARIABLE '(' expression [',' expression]* ')' """
        name = self.token.value
        self.consume(Bt.VARID)
        self.consume(Bt.LPAREN)

        dims = []
        if self.pos <= len(self.__tokens):
            dims.append(self.expression())

            while self.token.type == Bt.COMMA:
                self.consume(Bt.COMMA)
                dims.append(self.expression())
        self.consume(Bt.RPAREN)

        # current token type should be COMMA
        return Dim(name, dims)
        
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

    def nextstmt(self):
        self.consume(Bt.NEXT)
        if self.token.type != Bt.VARID:
            raise SyntaxError(f"Loop vairable should follow NEXT statement on line {self.lineno}")
        s = self.token.value
        self.consume(Bt.VARID)
        return Next(s)

    def gotostmt(self):
        """ goto_stmt ::= GOTO line_number """
        self.consume(Bt.GOTO)
        return ControlFlow("GOTO", self.expression())

    def gosubstmt(self):
        """ gosub_stmt ::= GOSUB expression """
        self.consume(Bt.GOSUB)
        return ControlFlow("GOSUB", self.expression())

    def returnstmt(self):
        self.consume(Bt.RETURN)
        return ControlFlow("RETURN", None)
    
    def inputstmt(self):
        """ input_stmt ::= INPUT (#filenum|STRING;) [VARIABLE,]*
                        |  INPUT STRING; (VARIABLE,)*"""
        self.consume(Bt.INPUT)

        # parse optional input prompt
        if self.token.type == Bt.STRING:
            prompt = self.token.value
            self.consume(Bt.STRING)
            self.consume(Bt.SEMI)
        # aquire prompt variables
        var_list = []
        
        var_list.append(self.token.type)
        self.consume(Bt.VARID)

        while self.token.type == Bt.COMMA:
            self.consume(Bt.COMMA)
            var_list.append(self.factor())
            continue

        return Input(prompt, var_list)

    def stopstmt(self):
        self.consume(Bt.STOP)
        return ControlFlow("STOP", expr=None)

    def datastmt(self):
        pass
