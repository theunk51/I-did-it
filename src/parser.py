
from typing import Literal
from src.tokens import ARITHMETIC_OPERATORS, LITERAL_TYPES, TokenType, Token, RELATIONAL_OPERATORS
from src.precedence import Precedence
from src.lexer import Lexer
from src.ast_nodes import *

DEFAULT_RULE = (None, None)

class Parser:
    __PARSING_RULES = {}

    def __init__(self, source_code: str) -> None:
        self.lexer = Lexer(source_code)
        if len(self.__PARSING_RULES) == 0:
            self.init_rules()

        self.previous_token = None
        self.current_token = None
        self.next_token = None

        self.__advance_token()
        self.__advance_token()


    def __advance_token(self):
        self.previous_token = self.current_token
        self.current_token = self.next_token

        try:
            self.next_token = next(self.lexer)
        except StopIteration:
            self.next_token = Token(TokenType.EOF, "\0")

    def consume(self, *expected):
        """Checks if the current token matches any of the given types. """
        for typ in expected:
            if self.current_token.type == typ:
                self.__advance_token()
                return self.previous_token

        raise Exception(f"Expected type(s) {expected}. Got {self.current_token.type}")

    def error(self, message: str):
        raise Exception(message)

    @property
    def is_at_end(self):
        return self.current_token.type == TokenType.EOF
    

    # === PARSING FUNCTIONS === #

    def parse_program(self):
        stmts = {}
        while self.current_token.type != TokenType.EOF:
            # skip over any blank lines
            if self.current_token.type == TokenType.NEWLINE:
                self.consume(TokenType.NEWLINE)
                continue

            line_number = int(self.consume(TokenType.INTEGER).value)
            statement = self.parse_statement()

            if not self.is_at_end:
                self.consume(TokenType.NEWLINE)
            
            stmts[line_number] = statement
        return stmts

    def parse_statement(self):
        if self.current_token.type == TokenType.LET:
            return self.parse_let_statement()
        elif self.current_token.type == TokenType.RETURN:
            return self.parse_return_statement()
        else:
            return self.parse_expression()

    def parse_let_statement(self):
        pass

    def parse_return_statement(self):
        pass
    
    def parse_expression(self, precedence):
        # parses any expression of a given precedence level or higher
        prefix_function = self.__PARSING_RULES.get(self.current_token.type, DEFAULT_RULE)[0]
        if prefix_function is None:
            self.error(f"Unexpected token '{self.current_token.value}' at start of expression")
        left = prefix_function(self)

        while self.current_token.type != TokenType.EOF:
            infix_function = self.__PARSING_RULES.get(self.current_token.type, DEFAULT_RULE)[1]
            if not infix_function:
                return left

            current_precedence = Precedence.get_prec(self.current_token.type)
            if precedence >= current_precedence:
                break

            left = infix_function(self, left)
        return left

    def parse_unary_expression(self):
        op_type = self.current_token.value
        self.consume(TokenType.NOT, TokenType.MINUS)
        right = self.parse_expression(Precedence.UNARY)
        return PrefixExpression(op_type, right)

    def parse_binary_expression(self, left: Expression) -> Expression:
        op_type = self.current_token.value
        precedence = Precedence.get_prec(self.current_token.type)
        if Precedence.is_right_associative(self.current_token.type):
            precedence -= 1
        
        self.consume(
            *ARITHMETIC_OPERATORS, 
            *RELATIONAL_OPERATORS, 
            TokenType.AND, 
            TokenType.OR
        )
        
        right = self.parse_expression(precedence)
        return InfixExpression(left, op_type, right)

    def parse_grouped_expression(self):
        self.consume(TokenType.LPAREN)
        expr = self.parse_expression(Precedence.NONE)
        self.consume(TokenType.RPAREN)
        return expr
        
    def parse_literal(self):
        token = self.current_token
        self.consume(TokenType.INTEGER, TokenType.FLOAT, TokenType.STRING, TokenType.BOOLEAN)
        
        if token.type == TokenType.INTEGER:
            return IntegerLiteral(int(token.value))
        elif token.type == TokenType.FLOAT:
            return FloatLiteral(float(token.value))
        elif token.type == TokenType.STRING:
            return StringLiteral(token.value)
        elif token.type == TokenType.BOOLEAN:
            return BooleanLiteral(token.value.upper() == 'TRUE')

    def parse_identifier(self):
        self.consume(TokenType.IDENTIFIER)
        return Identifier(self.previous_token.value)
    
    @classmethod
    def init_rules(cls):
        cls.__PARSING_RULES = {
            TokenType.NOT: (cls.parse_unary_expression, None),
            TokenType.MINUS: (cls.parse_unary_expression, cls.parse_binary_expression),
            TokenType.PLUS: (None, cls.parse_binary_expression),
            TokenType.MUL: (None, cls.parse_binary_expression),
            TokenType.DIV: (None, cls.parse_binary_expression),
            TokenType.MOD: (None, cls.parse_binary_expression),
            TokenType.EXPONENT: (None, cls.parse_binary_expression),
            TokenType.EQ: (None, cls.parse_binary_expression),
            TokenType.NEQ: (None, cls.parse_binary_expression),
            TokenType.LT: (None, cls.parse_binary_expression),
            TokenType.GT: (None, cls.parse_binary_expression),
            TokenType.LTEQ: (None, cls.parse_binary_expression),
            TokenType.GTEQ: (None, cls.parse_binary_expression),
            TokenType.AND: (None, cls.parse_binary_expression),
            TokenType.OR: (None, cls.parse_binary_expression),
            TokenType.INTEGER: (cls.parse_literal, None),
            TokenType.FLOAT: (cls.parse_literal, None),
            TokenType.STRING: (cls.parse_literal, None),
            TokenType.BOOLEAN: (cls.parse_literal, None),
            TokenType.IDENTIFIER: (cls.parse_identifier, None),
            TokenType.LPAREN: (cls.parse_grouped_expression, None),
        }
        