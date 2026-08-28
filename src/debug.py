from src.ast_nodes import *

def print_ast(node: ASTNode, prefix="", is_last=True, is_root=True, custom_label=None):
    if is_root:
        marker = ""
    else:
        marker = "└── " if is_last else "├── "
        
    # Determine the label for the current node
    if isinstance(node, Program):
        label = "Program"
    elif isinstance(node, LetStatement):
        label = f"Let ({node.name.value})"
    elif isinstance(node, ReturnStatement):
        label = "Return"
    elif isinstance(node, ExpressionStatement):
        label = "ExpressionStatement"
    elif isinstance(node, Identifier):
        label = f"Identifier({node.value})"
    elif isinstance(node, IntegerLiteral):
        label = f"Integer({node.value})"
    elif isinstance(node, FloatLiteral):
        label = f"Float({node.value})"
    elif isinstance(node, StringLiteral):
        label = f"String('{node.value}')"
    elif isinstance(node, BooleanLiteral):
        label = f"Boolean({node.value})"
    elif isinstance(node, PrefixExpression):
        label = f"Prefix({node.operator})"
    elif isinstance(node, InfixExpression):
        label = f"Infix({node.operator})"
    elif isinstance(node, FunctionLiteral):
        label = "Function"
    elif isinstance(node, CallExpression):
        label = "Call"
    elif isinstance(node, BlockStatement):
        label = "Block"
    else:
        label = f"Unknown({type(node).__name__})"

    # Prepend any custom prefix (like "Line 10: ") to the node label
    if custom_label:
        label = f"{custom_label} {label}"

    # Print the current node!
    print(f"{prefix}{marker}{label}")
    
    # Calculate the indentation prefix for children
    child_prefix = prefix + ("    " if is_last else "|   ") if not is_root else ""

    # Gather all children of this node in order
    children = []
    
    if isinstance(node, Program):
        for line_number, statement in node.statements.items():
            children.append((statement, f"Line {line_number}:"))
    elif isinstance(node, LetStatement):
        children.append((node.value, None))
    elif isinstance(node, ReturnStatement):
        children.append((node.value, None))
    elif isinstance(node, ExpressionStatement):
        children.append((node.expression, None))
    elif isinstance(node, PrefixExpression):
        children.append((node.right, None))
    elif isinstance(node, InfixExpression):
        children.append((node.left, None))
        children.append((node.right, None))
    elif isinstance(node, FunctionLiteral):
        for param in node.parameters:
            children.append((param, "Param:"))
        children.append((node.body, "Body:"))
    elif isinstance(node, CallExpression):
        children.append((node.function, "Function:"))
        for arg in node.arguments:
            children.append((arg, "Arg:"))
    elif isinstance(node, BlockStatement):
        for stmt in node.statements:
            children.append((stmt, None))

    # Recursively print all gathered children
    for i, (child, c_label) in enumerate(children):
        is_last_child = (i == len(children) - 1)
        print_ast(child, child_prefix, is_last_child, False, c_label)
