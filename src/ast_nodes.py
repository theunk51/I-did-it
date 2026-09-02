from dataclasses import dataclass, field
from typing import List, Any, Optional, Dict
from src.tokens import TokenType

class ASTNode:
    pass

class Expression(ASTNode):
    pass

class Statement(ASTNode):
    pass

class Declaration(ASTNode):
    pass

@dataclass
class Program(ASTNode):
    statements: Dict[int, Statement] = field(default_factory=dict) # Keyed by line number

@dataclass
class Identifier(Expression):
    value: str

@dataclass
class IntegerLiteral(Expression):
    value: int

@dataclass
class FloatLiteral(Expression):
    value: float

@dataclass
class StringLiteral(Expression):
    value: str

@dataclass
class BooleanLiteral(Expression):
    value: bool

@dataclass
class PrefixExpression(Expression):
    operator: TokenType
    right: Expression

@dataclass
class InfixExpression(Expression):
    left: Expression
    operator: TokenType
    right: Expression

@dataclass
class CallExpression(Expression):
    name: Identifier
    arguments: List[Expression]

@dataclass
class FunctionDeclaration(Declaration):
    name: str
    parameters: List[Identifier]
    body: Statement


@dataclass
class LetStatement(Statement):
    name: Identifier
    value: Expression

@dataclass
class ReturnStatement(Statement):
    value: Expression

@dataclass
class PrintStatement(Statement):
    items: List[Expression | str]

@dataclass
class BlockStatement(Statement):
    statements: List[Statement]

