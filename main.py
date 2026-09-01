import argparse
import subprocess
from pathlib import Path

from src.parser import Parser
from src.debug import print_ast
from src.code_generator import CodeGenerator


def assemble_and_run(asm_file: Path):
    """Uses GCC to assemble/link the file, then executes it."""
    # On Windows, executables end in .exe. (On Linux/WSL, we can just omit it)
    exe_file = asm_file.with_suffix(".exe")
    
    print(f"Assembling '{asm_file}' with GCC...")
    try:
        # Assemble & Link
        gcc_result = subprocess.run(
            ["gcc", "-g", str(asm_file), "src/runtime.c", "-o", str(exe_file)], 
            capture_output=True, text=True
        )
        if gcc_result.returncode != 0:
            print(f"GCC Error:\n{gcc_result.stderr}")
            return
    except FileNotFoundError:
        print("Error: 'gcc' is not installed or not available in your system PATH.")
        print("If you are on Windows, you must run this inside WSL (Windows Subsystem for Linux) or install MinGW.")
        return

    print(f"Running '{exe_file.name}'...\n{'-'*30}")
    
    # Run the compiled executable
    # Note: str(exe_file.resolve()) ensures it runs correctly regardless of OS
    run_result = subprocess.run([str(exe_file.resolve())], capture_output=True, text=True)
    
    # Print output
    if run_result.stdout:
        print(run_result.stdout, end="")
    if run_result.stderr:
        print(run_result.stderr, end="")
        
    print(f"\n{'-'*30}\nProgram exited with code {run_result.returncode}")


def main():
    parser = argparse.ArgumentParser(description="BASIC to x86-64 Compiler")
    parser.add_argument("file", help="Path to the BASIC (.bas) or Assembly (.s) file", type=str)
    parser.add_argument("-o", "--output", help="The name of the output assembly file (default: output.s)", type=str, default="output.s")
    parser.add_argument("-r", "--run", help="Compile the assembly with GCC and run it immediately", action="store_true")
    
    args = parser.parse_args()
    file_path = Path(args.file)

    if not file_path.exists():
        print(f"Error: Could not find file '{file_path}'")
        return

    # If the user passed an assembly file directly, skip BASIC parsing!
    if file_path.suffix == '.s':
        if args.run:
            assemble_and_run(file_path)
        else:
            print(f"File '{file_path}' is already assembly. Use the -r flag to run it!")
        return

    print(f"Parsing '{file_path}'...")
    source_code = file_path.read_text(encoding="utf-8")
    ast = Parser(source_code).parse_program()
    out_path = Path(args.output)
    print(f"Generating assembly to '{out_path}'...")
    cg = CodeGenerator(ast)
    cg.generate_assembly_file(out_path)

    print(cg.variable_allocation)
    print("Success!")

    # 4. Run it if requested
    if args.run:
        print("") # blank line for spacing
        assemble_and_run(out_path)

if __name__ == "__main__":
    main()

