import pytest
from src.lexer import Lexer
from src.parser import Parser
from src.ast_nodes import *

def parse_expr(source_code: str):
    """Helper to initialize the parser, prime it, and parse a single expression."""
    parser = Parser(source_code)
    return parser.parse_expression(0)



def test_unary_minus():
    # "- 5"
    ast = parse_expr("- 5")
    assert isinstance(ast, PrefixExpression)
    assert ast.operator == "-"
    assert isinstance(ast.right, IntegerLiteral)
    assert ast.right.value == 5

def test_unary_not():
    # "NOT TRUE"
    ast = parse_expr("NOT TRUE")
    assert isinstance(ast, PrefixExpression)
    assert ast.operator == "NOT"
    assert isinstance(ast.right, BooleanLiteral)
    assert ast.right.value == True


# === Binary Associativity Tests ===

def test_binary_left_associative():
    # "1 - 2 - 3" should group as "(1 - 2) - 3"
    ast = parse_expr("1 - 2 - 3")
    assert isinstance(ast, InfixExpression)
    assert ast.operator == "-"
    assert isinstance(ast.right, IntegerLiteral)
    assert ast.right.value == 3
    
    # Left side should be "1 - 2"
    left_node = ast.left
    assert isinstance(left_node, InfixExpression)
    assert left_node.operator == "-"
    assert isinstance(left_node.left, IntegerLiteral)
    assert left_node.left.value == 1
    assert isinstance(left_node.right, IntegerLiteral)
    assert left_node.right.value == 2

def test_binary_right_associative():
    # "2 ^ 3 ^ 4" should group as "2 ^ (3 ^ 4)"
    ast = parse_expr("2 ^ 3 ^ 4")
    assert isinstance(ast, InfixExpression)
    assert ast.operator == "^"
    assert isinstance(ast.left, IntegerLiteral)
    assert ast.left.value == 2
    
    # Right side should be "3 ^ 4"
    right_node = ast.right
    assert isinstance(right_node, InfixExpression)
    assert right_node.operator == "^"
    assert isinstance(right_node.left, IntegerLiteral)
    assert right_node.left.value == 3
    assert isinstance(right_node.right, IntegerLiteral)
    assert right_node.right.value == 4


# === Precedence Tests ===

def test_precedence_addition_multiplication():
    # "1 + 2 * 3" should group as "1 + (2 * 3)"
    ast = parse_expr("1 + 2 * 3")
    assert isinstance(ast, InfixExpression)
    assert ast.operator == "+"
    assert isinstance(ast.left, IntegerLiteral)
    assert ast.left.value == 1
    
    assert isinstance(ast.right, InfixExpression)
    assert ast.right.operator == "*"
    assert ast.right.left.value == 2
    assert ast.right.right.value == 3

def test_precedence_division_subtraction():
    # "1 / 2 - 3" should group as "(1 / 2) - 3"
    ast = parse_expr("1 / 2 - 3")
    assert isinstance(ast, InfixExpression)
    assert ast.operator == "-"
    assert ast.right.value == 3
    
    assert isinstance(ast.left, InfixExpression)
    assert ast.left.operator == "/"
    assert ast.left.left.value == 1
    assert ast.left.right.value == 2

def test_precedence_comparisons():
    # "A * B > C + D" should group as "(A * B) > (C + D)"
    ast = parse_expr("A * B > C + D")
    assert isinstance(ast, InfixExpression)
    assert ast.operator == ">"
    
    assert isinstance(ast.left, InfixExpression)
    assert ast.left.operator == "*"
    assert ast.left.left.value == "A"
    assert ast.left.right.value == "B"
    
    assert isinstance(ast.right, InfixExpression)
    assert ast.right.operator == "+"
    assert ast.right.left.value == "C"
    assert ast.right.right.value == "D"

def test_grouping_parentheses():
    # "(1 + 2) * 3" should group as "(1 + 2) * 3"
    ast = parse_expr("(1 + 2) * 3")
    assert isinstance(ast, InfixExpression)
    assert ast.operator == "*"
    assert isinstance(ast.right, IntegerLiteral)
    assert ast.right.value == 3
    
    assert isinstance(ast.left, InfixExpression)
    assert ast.left.operator == "+"
    assert ast.left.left.value == 1
    assert ast.left.right.value == 2


def test_print_statement():
    parser = Parser('PRINT A, B; "HELLO"')
    ast = parser.parse_statement()
    
    assert isinstance(ast, PrintStatement)
    assert len(ast.items) == 5
    
    assert isinstance(ast.items[0], Identifier)
    assert ast.items[0].value == "A"
    assert ast.items[1] == ","
    assert isinstance(ast.items[2], Identifier)
    assert ast.items[2].value == "B"
    assert ast.items[3] == ";"
    assert isinstance(ast.items[4], StringLiteral)
    assert ast.items[4].value == "HELLO"


def test_function_call_no_args():
    ast = parse_expr("RND()")
    assert isinstance(ast, CallExpression)
    assert isinstance(ast.name, Identifier)
    assert ast.name.value == "RND"
    assert len(ast.arguments) == 0

def test_function_call_one_arg():
    ast = parse_expr("TAB(5)")
    assert isinstance(ast, CallExpression)
    assert isinstance(ast.name, Identifier)
    assert ast.name.value == "TAB"
    assert len(ast.arguments) == 1
    assert isinstance(ast.arguments[0], IntegerLiteral)
    assert ast.arguments[0].value == 5

def test_function_call_multiple_args():
    ast = parse_expr("MYFUNC(A, 2 + 3)")
    assert isinstance(ast, CallExpression)
    assert isinstance(ast.name, Identifier)
    assert ast.name.value == "MYFUNC"
    assert len(ast.arguments) == 2
    
    assert isinstance(ast.arguments[0], Identifier)
    assert ast.arguments[0].value == "A"
    
    assert isinstance(ast.arguments[1], InfixExpression)
    assert ast.arguments[1].operator == "+"
    assert ast.arguments[1].left.value == 2
    assert ast.arguments[1].right.value == 3
