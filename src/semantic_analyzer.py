from dataclasses import dataclass
from typing import List, Tuple
from src.ast_nodes import *
from src.tokens import ARITHMETIC_OPERATORS, RELATIONAL_OPERATORS, LOGICAL_OPERATORS, TokenType
from enum import Enum, auto

class SemanticError(Exception):
    pass

class ValueType(Enum):
    INT = auto()
    FLOAT = auto()
    STRING = auto()
    BOOL = auto()
    ANY = auto()    # for built-ins or user functions
    VOID = auto()   # for functions/statements that return nothing

    @property
    def is_numeric(self) -> bool:
        return self in (ValueType.INT, ValueType.FLOAT)

def _build_primitive_rules():
    rules = {}
    for op in ARITHMETIC_OPERATORS:
        rules[(ValueType.INT, op, ValueType.INT)] = ValueType.INT
        rules[(ValueType.FLOAT, op, ValueType.FLOAT)] = ValueType.FLOAT
        rules[(ValueType.INT, op, ValueType.FLOAT)] = ValueType.FLOAT
        rules[(ValueType.FLOAT, op, ValueType.INT)] = ValueType.FLOAT
    
    for op in RELATIONAL_OPERATORS:
        rules[(ValueType.INT, op, ValueType.INT)] = ValueType.BOOL
        rules[(ValueType.FLOAT, op, ValueType.FLOAT)] = ValueType.BOOL
        rules[(ValueType.STRING, op, ValueType.STRING)] = ValueType.BOOL
        rules[(ValueType.BOOL, op, ValueType.BOOL)] = ValueType.BOOL
        rules[(ValueType.INT, op, ValueType.FLOAT)] = ValueType.BOOL
        rules[(ValueType.FLOAT, op, ValueType.INT)] = ValueType.BOOL

    for op in LOGICAL_OPERATORS:
        rules[(ValueType.BOOL, op, ValueType.BOOL)] = ValueType.BOOL

    rules[(ValueType.STRING, TokenType.PLUS, ValueType.STRING)] = ValueType.STRING
    
    return rules

@dataclass
class FunctionSignature:
    return_type: ValueType
    param_types: List[Tuple[ValueType, ...]]

class SemanticAnalyzer:
    PRIMITIVE_RULES = _build_primitive_rules()
    BUILT_IN_FUNCTIONS = {
        "TAB": FunctionSignature(ValueType.VOID, [(ValueType.INT, ValueType.FLOAT)]),
        "SIN": FunctionSignature(ValueType.FLOAT, [(ValueType.INT, ValueType.FLOAT)]),
        "COS": FunctionSignature(ValueType.FLOAT, [(ValueType.INT, ValueType.FLOAT)]),
        "TAN": FunctionSignature(ValueType.FLOAT, [(ValueType.INT, ValueType.FLOAT)]),
    }

    def __init__(self):
        # maps variable names to their types (e.g., {"x": ValueType.INT})
        self.symbol_table = {}

    def analyze(self, ast: ASTNode):
        self.symbol_table.clear()
        self.validate(ast)

    def validate(self, node: ASTNode):
        method_name = f'validate_{type(node).__name__}'
        validator = getattr(self, method_name, self.generic_validate)
        
        result_type = validator(node)
        node.expr_type = result_type
        return result_type

    def generic_validate(self, node: ASTNode):
        pass

    def validate_Program(self, node: Program):
        for stmt in node.statements.values():
            self.validate(stmt)

    def validate_BlockStatement(self, node: BlockStatement):
        for stmt in node.statements:
            self.validate(stmt)

    def validate_LetStatement(self, node: LetStatement):
        value_type = self.validate(node.value)
        self.symbol_table[node.name.value] = value_type

    def validate_PrintStatement(self, node: PrintStatement):
        for item in node.items:
            if isinstance(item, ASTNode):
                self.validate(item)

    def validate_IntegerLiteral(self, node: IntegerLiteral):
        return ValueType.INT

    def validate_FloatLiteral(self, node: FloatLiteral):
        return ValueType.FLOAT

    def validate_StringLiteral(self, node: StringLiteral):
        return ValueType.STRING

    def validate_BooleanLiteral(self, node: BooleanLiteral):
        return ValueType.BOOL

    def validate_Identifier(self, node: Identifier):
        if node.value not in self.symbol_table:
            raise SemanticError(f"Undefined variable used: '{node.value}'")
        return self.symbol_table[node.value]

    def validate_PrefixExpression(self, node: PrefixExpression):
        right_type = self.validate(node.right)
        
        if node.operator == TokenType.MINUS:
            if not right_type.is_numeric:
                raise SemanticError(f"Unary minus requires a number, got '{right_type.name}'")
            return right_type
        elif node.operator == TokenType.NOT:
            if right_type != ValueType.BOOL:
                raise SemanticError(f"Logical NOT requires a boolean, got '{right_type.name}'")
            return ValueType.BOOL
            
        return right_type

    def validate_InfixExpression(self, node: InfixExpression):
        left_type = self.validate(node.left)
        right_type = self.validate(node.right)
        
        key = (left_type, node.operator, right_type)
        if key in self.PRIMITIVE_RULES:
            return self.PRIMITIVE_RULES[key]
            
        raise SemanticError(
            f"Semantic Error: Cannot apply '{node.operator.name}' to '{left_type.name}' and '{right_type.name}'"
        )

    def validate_FunctionDeclaration(self, node: FunctionDeclaration):
        for param in node.parameters:
            self.symbol_table[param.value] = ValueType.ANY
        self.validate(node.body)

    def validate_CallExpression(self, node: CallExpression):
        func_name = node.name.value
        
        # check if it's a known built-in function
        if func_name in self.BUILT_IN_FUNCTIONS:
            sig = self.BUILT_IN_FUNCTIONS[func_name]
            
            expected_args = len(sig.param_types)
            if len(node.arguments) != expected_args: 
                raise SemanticError(f"Function {func_name} expects {expected_args} argument(s), got {len(node.arguments)}")

            for i, arg in enumerate(node.arguments):
                arg_type = self.validate(arg)
                expected_types = sig.param_types[i]
                if arg_type not in expected_types:
                    raise SemanticError(f"Function {func_name} argument {i+1} expects {[t.name for t in expected_types]}, got {arg_type.name}")
                
            return sig.return_type
        else:
            # fallback for user-defined or unverified functions
            for arg in node.arguments:
                self.validate(arg)
            return ValueType.ANY

    def validate_ReturnStatement(self, node: ReturnStatement):
        self.validate(node.value)
