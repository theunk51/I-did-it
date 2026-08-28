import subprocess
from pathlib import Path
from src.parser import Parser
from src.code_generator import CodeGenerator

def run_basic_program(source_code: str) -> str:
    """Helper to compile a BASIC string, run it via GCC, and return its stdout."""
    ast = Parser(source_code).parse_program()
    cg = CodeGenerator(ast)
    
    asm_path = Path("test_output.s")
    exe_path = Path("test_output.exe")
    cg.generate_assembly_file(asm_path)
    
    try:
        subprocess.run(["gcc", str(asm_path), "-o", str(exe_path)], check=True, capture_output=True)
        result = subprocess.run([str(exe_path.resolve())], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    finally:
        # cleanup
        if asm_path.exists(): 
            asm_path.unlink()
        if exe_path.exists():
            try:
                exe_path.unlink()
            except PermissionError:
                pass # sometimes Windows holds onto the exe a bit longer

def test_compiler_addition():
    source = "10 LET X = 5 + 10"
    assert run_basic_program(source) == "15"

def test_compiler_subtraction():
    source = "10 LET X = 5 - 10"
    assert run_basic_program(source) == "-5"

def test_compiler_order_of_operations():
    source = "10 LET X = 5 + 10 * 2"
    assert run_basic_program(source) == "25"

def test_compiler_division():
    source = "10 LET X = 20 / 4 * 2"
    assert run_basic_program(source) == "10"

def test_compiler_multiple_variables():
    source = """
    10 LET X = 10
    20 LET Y = 20
    30 LET Z = X + Y
    """
    assert run_basic_program(source) == "30"

def test_compiler_register_spill():
    # TODO: not true
    source = """
    10 LET V1 = 1
    11 LET V2 = 2
    12 LET V3 = 3
    13 LET V4 = 4
    14 LET V5 = 5
    15 LET V6 = 6
    16 LET V7 = 7
    20 LET RESULT = V1 + V2 + V3 + V4 + V5 + V6 + V7
    """
    assert run_basic_program(source) == "28"
