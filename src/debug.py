from src.ast_nodes import *


def print_ast(node: ASTNode, indent=0):
    space = " " * indent

    if isinstance(node, Program):
        for statement in node.statements:
            print_ast(statement, indent)
    elif isinstance(node, LetStatement):
        print(
            space + f"Let {node.name.value}"
        )
        print_ast(node.value, indent + 2)
    elif isinstance(node, ReturnStatement):
        print(space + "Return")
        print_ast(node.value, indent + 2)
    elif isinstance(node, ExpressionStatement):
        print_ast(node.expression, indent)
    elif isinstance(node, Identifier):
        print(
            space + f"Identifier({node.value})"
        )
    elif isinstance(node, IntegerLiteral):
        print(
            space + f"Integer({node.value})"
        )
    elif isinstance(node, PrefixExpression):
        print(
            space + f"Prefix({node.operator})"
        )
        print_ast(node.right, indent + 2)
    elif isinstance(node, InfixExpression):
        print(
            space + f"Infix({node.operator})"
        )
        print_ast(node.left, indent + 2)
        print_ast(node.right, indent + 2)
    elif isinstance(node, FunctionLiteral):
        print(space + "Function")

        print(space + "  Parameters:")
        for parameter in node.parameters:
            print_ast(parameter, indent + 4)

        print(space + "  Body:")
        print_ast(node.body, indent + 4)
    elif isinstance(node, CallExpression):
        print(space + "Call")

        print(space + "  Function:")
        print_ast(node.function, indent + 4)

        print(space + "  Arguments:")
        for argument in node.arguments:
            print_ast(argument, indent + 4)
    elif isinstance(node, BlockStatement):
        print(space + "Block")
        for statement in node.statements:
            print_ast(statement, indent + 2)
