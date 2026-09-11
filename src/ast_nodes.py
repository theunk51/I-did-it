from dataclasses import dataclass, field
from typing import Any, Optional
from src.tokens import TokenType

# ==========================================
# Abstract Categories & Root
# ==========================================
class ASTNode:
    expr_type = None

class Expression(ASTNode): pass   # returns a computed value 
class Statement(ASTNode): pass     
class Declaration(ASTNode): pass
class Literal(Expression): pass

@dataclass
class Program(ASTNode):
    statements: dict[int, 'Statement'] = field(default_factory=dict) # Keyed by line number

# ==========================================
# Literals (Expressions)
# ==========================================
@dataclass
class IntegerLiteral(Literal):
    value: int

@dataclass
class FloatLiteral(Literal):
    value: float

@dataclass
class StringLiteral(Literal):
    value: str

@dataclass
class BooleanLiteral(Literal):
    value: bool

@dataclass
class Identifier(Literal):
    value: str

# ==========================================
# Expressions
# ==========================================
@dataclass
class CastExpression(Expression):
    target_type: Any
    value: Expression

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
    arguments: list[Expression]

# ==========================================
# Statements
# ==========================================
@dataclass
class LetStatement(Statement):
    name: Identifier
    value: Expression

@dataclass
class ReturnStatement(Statement):
    value: Expression

@dataclass
class PrintStatement(Statement):
    items: list[Expression | str]

@dataclass
class BlockStatement(Statement):
    statements: list[Statement]

@dataclass
class ForStatement(Statement):
    iterator: Identifier
    start: Expression
    end: Expression
    step: Optional[Expression]
    body: BlockStatement

@dataclass
class GotoStatement(Statement):
    target: IntegerLiteral

class IfStatement(Statement):
    condition: Expression
    then: IntegerLiteral

@dataclass
class OnStatement(Statement):
    condition: Expression
    targets: list[IntegerLiteral]


# ==========================================
# Declarations
# ==========================================
@dataclass
class FunctionDeclaration(Declaration):
    name: str
    parameters: list[Identifier]
    body: Statement

