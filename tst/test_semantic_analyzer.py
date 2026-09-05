import pytest
from src.ast_nodes import *
from src.tokens import TokenType
from src.semantic_analyzer import SemanticAnalyzer, SemanticError, ValueType

@pytest.fixture
def analyzer():
    return SemanticAnalyzer()

def test_literals(analyzer):
    # Test that literals return the correct ValueType and decorate the node
    node_int = IntegerLiteral(42)
    assert analyzer.validate(node_int) == ValueType.INT
    assert node_int.expr_type == ValueType.INT

    node_float = FloatLiteral(3.14)
    assert analyzer.validate(node_float) == ValueType.FLOAT
    assert node_float.expr_type == ValueType.FLOAT

    node_str = StringLiteral("hello")
    assert analyzer.validate(node_str) == ValueType.STRING
    assert node_str.expr_type == ValueType.STRING

    node_bool = BooleanLiteral(True)
    assert analyzer.validate(node_bool) == ValueType.BOOL
    assert node_bool.expr_type == ValueType.BOOL

def test_variable_declaration_and_lookup(analyzer):
    # Let X = 100
    let_node = LetStatement(name=Identifier("X"), value=IntegerLiteral(100))
    analyzer.validate(let_node)
    
    assert analyzer.symbol_table["X"] == ValueType.INT

    # Lookup X
    id_node = Identifier("X")
    assert analyzer.validate(id_node) == ValueType.INT
    assert id_node.expr_type == ValueType.INT

def test_undefined_variable(analyzer):
    id_node = Identifier("Y")
    with pytest.raises(SemanticError, match="Undefined variable used: 'Y'"):
        analyzer.validate(id_node)

def test_prefix_expressions(analyzer):
    # Valid: -5
    valid_minus = PrefixExpression(operator=TokenType.MINUS, right=IntegerLiteral(5))
    assert analyzer.validate(valid_minus) == ValueType.INT

    # Valid: NOT True
    valid_not = PrefixExpression(operator=TokenType.NOT, right=BooleanLiteral(True))
    assert analyzer.validate(valid_not) == ValueType.BOOL

    # Invalid: -"string"
    invalid_minus = PrefixExpression(operator=TokenType.MINUS, right=StringLiteral("test"))
    with pytest.raises(SemanticError, match="Unary minus requires a number"):
        analyzer.validate(invalid_minus)

    # Invalid: NOT 5
    invalid_not = PrefixExpression(operator=TokenType.NOT, right=IntegerLiteral(5))
    with pytest.raises(SemanticError, match="Logical NOT requires a boolean"):
        analyzer.validate(invalid_not)

def test_infix_arithmetic(analyzer):
    # Valid: int + int -> int
    add_ints = InfixExpression(left=IntegerLiteral(10), operator=TokenType.PLUS, right=IntegerLiteral(20))
    assert analyzer.validate(add_ints) == ValueType.INT

    # Valid: float * int -> float
    mul_mix = InfixExpression(left=FloatLiteral(2.5), operator=TokenType.MUL, right=IntegerLiteral(2))
    assert analyzer.validate(mul_mix) == ValueType.FLOAT

    # Valid: string + string -> string
    add_strs = InfixExpression(left=StringLiteral("a"), operator=TokenType.PLUS, right=StringLiteral("b"))
    assert analyzer.validate(add_strs) == ValueType.STRING

    # Invalid: int + string
    invalid_add = InfixExpression(left=IntegerLiteral(5), operator=TokenType.PLUS, right=StringLiteral("a"))
    with pytest.raises(SemanticError, match="Cannot apply 'PLUS' to 'INT' and 'STRING'"):
        analyzer.validate(invalid_add)

def test_infix_relational(analyzer):
    # Valid: int < float -> bool
    lt_mix = InfixExpression(left=IntegerLiteral(5), operator=TokenType.LT, right=FloatLiteral(10.0))
    assert analyzer.validate(lt_mix) == ValueType.BOOL

    # Valid: string == string -> bool
    eq_strs = InfixExpression(left=StringLiteral("a"), operator=TokenType.EQ, right=StringLiteral("b"))
    assert analyzer.validate(eq_strs) == ValueType.BOOL

    # Invalid: string > int
    invalid_gt = InfixExpression(left=StringLiteral("a"), operator=TokenType.GT, right=IntegerLiteral(5))
    with pytest.raises(SemanticError, match="Cannot apply 'GT' to 'STRING' and 'INT'"):
        analyzer.validate(invalid_gt)

def test_infix_logical(analyzer):
    # Valid: bool AND bool -> bool
    and_bools = InfixExpression(left=BooleanLiteral(True), operator=TokenType.AND, right=BooleanLiteral(False))
    assert analyzer.validate(and_bools) == ValueType.BOOL

    # Invalid: bool OR int
    invalid_or = InfixExpression(left=BooleanLiteral(True), operator=TokenType.OR, right=IntegerLiteral(0))
    with pytest.raises(SemanticError, match="Cannot apply 'OR' to 'BOOL' and 'INT'"):
        analyzer.validate(invalid_or)

def test_builtin_functions(analyzer):
    # Valid: TAB(5) -> VOID
    call_tab = CallExpression(name=Identifier("TAB"), arguments=[IntegerLiteral(5)])
    assert analyzer.validate(call_tab) == ValueType.VOID

    # Valid: SIN(3.14) -> FLOAT
    call_sin = CallExpression(name=Identifier("SIN"), arguments=[FloatLiteral(3.14)])
    assert analyzer.validate(call_sin) == ValueType.FLOAT

    # Invalid Argument Type: TAB("hello")
    call_tab_bad_arg = CallExpression(name=Identifier("TAB"), arguments=[StringLiteral("hello")])
    with pytest.raises(SemanticError, match="Function TAB argument 1 expects \\['INT', 'FLOAT'\\], got STRING"):
        analyzer.validate(call_tab_bad_arg)

    # Invalid Argument Count: SIN(1, 2)
    call_sin_bad_count = CallExpression(name=Identifier("SIN"), arguments=[IntegerLiteral(1), IntegerLiteral(2)])
    with pytest.raises(SemanticError, match="Function SIN expects 1 argument\\(s\\), got 2"):
        analyzer.validate(call_sin_bad_count)

def test_user_defined_functions(analyzer):
    # Function MYFUNC(X)
    func_decl = FunctionDeclaration(
        name=Identifier("MYFUNC"),
        parameters=[Identifier("X")],
        body=BlockStatement(statements=[
            ReturnStatement(value=Identifier("X"))
        ])
    )
    analyzer.validate(func_decl)
    
    # Check that parameters are added to symbol table
    assert analyzer.symbol_table["X"] == ValueType.ANY
    
    # Call MYFUNC(10)
    call_myfunc = CallExpression(name=Identifier("MYFUNC"), arguments=[IntegerLiteral(10)])
    assert analyzer.validate(call_myfunc) == ValueType.ANY # User functions currently return ANY

def test_program_analysis_resets_state(analyzer):
    # First analysis pass: Let X = 10
    prog1 = Program(statements={
        10: LetStatement(name=Identifier("X"), value=IntegerLiteral(10))
    })
    analyzer.analyze(prog1)
    
    assert "X" in analyzer.symbol_table
    
    # Second analysis pass: completely different program
    prog2 = Program(statements={
        10: LetStatement(name=Identifier("Y"), value=FloatLiteral(3.14))
    })
    analyzer.analyze(prog2)
    
    assert "Y" in analyzer.symbol_table
    # X should have been cleared because analyze() resets state
    assert "X" not in analyzer.symbol_table

def test_ast_node_decoration(analyzer):
    # 10 Let X = 5 + 5.5
    add_node = InfixExpression(left=IntegerLiteral(5), operator=TokenType.PLUS, right=FloatLiteral(5.5))
    let_node = LetStatement(name=Identifier("X"), value=add_node)
    
    analyzer.validate(let_node)
    
    # Check if nodes were correctly decorated with expr_type
    assert let_node.value.expr_type == ValueType.FLOAT
    assert let_node.value.left.expr_type == ValueType.INT
    assert let_node.value.right.expr_type == ValueType.FLOAT
