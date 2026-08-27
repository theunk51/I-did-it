

from pathlib import Path
from typing import Literal

from src.ast_nodes import *
from src.parser import Parser


"""
Before allocating anything, the compiler must figure out the lifespan of every variable.
A variable is considered "live" from the moment it is defined (e.g., x = 5) until the exact moment it is used for the very last time (e.g., return x + y).

If Variable A dies on line 10, and Variable B is born on line 11, they can safely share the exact same register (RAX, for instance). The compiler maps out these overlapping lifespans to see which variables are "interfering" (alive at the exact same time)
How compilers choose what to spill:
A smart compiler doesn't just spill randomly; it uses heuristics:

Spill the least used: If Variable A is used 50 times in a loop, and Variable B is used twice, spill B.

Spill the longest-living: If a variable sits dormant for 100 lines of code between uses, it's a great candidate for the stack.

Never spill loop counters: Variables actively controlling while or for loops should almost always stay in fast registers.

4. Linear Scan (The Faster Alternative)
Graph coloring produces incredibly optimized code, but solving the graph takes a lot of time. If you are writing a JIT (Just-In-Time) compiler (like the V8 engine in Chrome or the Java JVM), you cannot afford to wait for a graph to solve.

Instead, they use Linear Scan Allocation.
The compiler reads the code top-to-bottom in a single pass. When a variable is born, it grabs a free register. When the variable dies, it gives the register back. If it needs a register and they are all full, it instantly spills the variable that won't be needed until the furthest point in the future. It is not perfectly optimal, but it is lightning fast to compile
This is the beauty of Linear Scan Allocation. It guarantees that the CPU registers are always holding the variables that are needed soonest, while variables that are just "waiting around" are shuffled into RAM (the .bss section) until they are actually needed!
"""
from dataclasses import dataclass
from collections import deque
from bisect import insort


"""
Rather than allocating all variables to stack, and assigning them registers as needed, this compiler can use something
call Linear Scan allocation. It traverses the program AST node, to determine the lifespan of all variables in the program.
A variable is considered "live" from the moment it is defined (e.g., x = 5) until the exact moment it is used for the very 
last time (e.g., return x + y). Register allocation happens during the second pass. When a variable is born, it grabs a 
free register. When the variable dies, it gives the register back. If there are no more register, it instantly spills 
the variable that won't be needed until the furthest point in the future. It is not perfectly optimal, but it is lightning
fast to compile. BASIC defines all variables as globals, but that does not mean a single program will contain 286 variables, 
thus this optimizes potential over allocation by allocating only what is needed. Linear Scan Allocation guarantees 
that the CPU registers are always holding the variables that are needed soonest, while variables that are just 
"waiting around" are shuffled into RAM (the .bss section) until they are actually needed.
"""
"""
Rather than allocating all variables to the stack and moving them into registers as needed, 
this compiler uses Linear Scan Allocation.

The allocator operates in two passes:
1. Lifespan Analysis: It traverses the program's AST to determine the lifespan (live range) 
   of all variables. A variable is considered "live" from the moment it is defined 
   (e.g., x = 5) until the exact moment it is used for the very last time (e.g., return x + y).

2. Register Allocation: As the program executes top-to-bottom, a variable grabs a free 
   register when it is born. When the variable dies, it gives the register back. If all 
   registers are full when a new variable is born, the allocator instantly spills the variable 
   that won't be needed until the furthest point in the future. 

While not mathematically optimal (like Graph Coloring), Linear Scan allocation is fast to implement
and compile. Because BASIC defines all variables as globals all register spills go to .BSS. Additionally,
while BASIC only allows 286 unqiue variables, a single program rarely uses all 286, and allocating all of
these variables premptively though a single program rarely uses all 286 
possible variables—this strategy prevents massive overallocation of memory. It guarantees 
that the fast CPU registers always hold the variables needed soonest, while dormant variables 
are shuffled into RAM (the .bss section) until they are actually needed again.
"""

"""

"""
# look up Stack slot coloring

class RegisterAllocator:
    @dataclass(slots=True)
    class Interval:
        name: str
        start: int
        end: int


    def __init__(self, program: Program):
        self.program = program

        # State for Pass 1 (Lifespans)
        self.variable_intervals: Dict[str, "RegisterAllocator.Interval"] = {}
        self.current_line = 0
        
        # State for Pass 2 (Allocation)
        self.free_registers = deque([
            '%r8', '%r9', '%r10', '%r11', '%r12', '%r13', 
            '%r14', '%rbx', '%rcx', '%rsi', '%rdi', '%rdx'
        ])
        self.active_intervals: list["RegisterAllocator.Interval"] = []
        self.allocation_map: Dict[str, str] = {}

    @classmethod
    def allocate(cls, program: Program) -> dict[str, str]:
        """
        The static entry point. 
        Creates a short-lived instance to track state during the AST traversal,
        then returns the final allocation map and discards the instance.
        """
        allocator = cls(program)
        allocator.analyze_variable_lifespans(program)
        allocator.compute_register_allocation()
        return allocator.allocation_map

    def analyze_variable_lifespans(self):
        self.variable_intervals: dict[str, "RegisterAllocator.Interval"] = {}
        for line, statement in sorted(self.program.statements.items()):
            self.current_line = line
            self.analyze_variables_in_nodes(statement)

        for interval in self.variable_intervals:
            print(f"Variable [interval.name]: Alive from line {interval.start} to {interval.end}")

    def _mark_variable_lifespan(self, variable: str):
        if variable not in self.variable_intervals:
            self.variable_intervals[variable] = self.Interval(
                name=variable,
                start=self.current_line,
                end=self.current_line
            )
        else:
            self.variable_intervals[variable].end = self.current_line

    def analyze_variables_in_nodes(self, node: ASTNode):
        if node is None: 
            return

        if isinstance(node, LetStatement):
            self._mark_variable_lifespan(node.name.value)
            self.analyze_variables_in_nodes(node.value)
        elif isinstance(node, ExpressionStatement):
            self.analyze_variables_in_nodes(node.expression)
        elif isinstance(node, Identifier):
            self._mark_variable_lifespan(node.value)
        elif isinstance(node, InfixExpression):
            self.analyze_variables_in_nodes(node.left)
            self.analyze_variables_in_nodes(node.right)
        elif isinstance(node, PrefixExpression):
            self.analyze_variables_in_nodes(node.right)
        elif isinstance(node, CallExpression):
            self.analyze_variables_in_nodes(node.function)
            for arg in node.arguments:
                self.analyze_variables_in_nodes(arg)

        # Note: Literals (Integer, Float, String, Boolean) don't contain variables, 
        # so we don't need to do anything when we hit them.


    def compute_register_allocation(self):
        sorted_intervals = sorted(self.variable_intervals.values(), key=lambda x: x.start)
        for current_interval in sorted_intervals:
            # Expire old variables: if another allocated variable dies before the current variable starts,
            # return the register so that it can be used by the current variable
            for active_interval in self.active_intervals[:]:
                if active_interval.end < current_interval.start:
                    self.active_intervals.remove(active_interval)
                    register = self.allocation_map[active_interval.name]
                    self.free_registers.append(register)

            # allocate or spill registers
            if len(self.free_registers) > 0:
                register = self.free_registers.popleft()
                self.allocation_map[current_interval.name] = register
                insort(self.active_intervals, current_interval, key=lambda x: x.end)
            else:
                longest_alive_interval = self.active_intervals[-1]
                if longest_alive_interval.end > current_interval.end:
                    # the allocated variable lives longer, so we can steal its register. The kicked
                    # variable then could be stored on the stack or in the BSS section. The BSS
                    # section works because there are at most 26 * 11 = 286 variables
                    register = self.allocation_map[longest_alive_interval.name]
                    self.allocation_map[longest_alive_interval.name] = f"{longest_alive_interval.name}_bss"
                    self.allocation_map[current_interval.name] = register
                    self.active_intervals.pop(-1)
                    insort(self.allocated_variables, current_interval, key=lambda x: x.end)
                else:
                    # the current variable lives the longest so far, so spill into BSS
                    self.allocation_map[current_interval.name] = f"{current_interval.name}_bss"




class CodeGenerator:
    """
    Converts the parsed AST program into x86-64 assembly that can be
    compiled and executed with GCC.
    """
    def __init__(self, ast: Program):
        self.ast = ast
        self.current_line_number: int = 0

        # assembly program section state
        self.data_section: list[str] = [".data"]
        self.text_section: list[str] = []

        # program state
        # - available registers
        # - current global scope
        # - the stack pointer offset for variables
        self.stack_offset = 0


    def generate_assembly(self) -> str:
        """
        Walks the AST program dictionary, compiles each statement, 
        and joins sections into a final assembly string.
        """

        self.emit(".global _start")
        self.emit(".text")
        self.emit("_start:")
        self.emit("    pushq %rbp") # save the previous stack frame pointer
        self.emit("    movq %rsp, %rbp") # load the current frame pointer
        # save callee-saved registers if need be

        self._compile_Program(self.ast)

        # exit program
        # restore resigster states if need be
        self.emit("    movq $60, %rax")  # syscall number for sys_exit
        self.emit("    xorq %rdi, %rdi") # exit code 0
        self.emit("    syscall")
        self.emit("")        

    def generate_assembly_file(self, filename: str | Path = "output.s") -> None:
        """Writes the assembly instruction to the file with given name or path."""

        path = Path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        asm = self.generate_assembly()
        path.write_text(asm, encoding="utf-8")

    
    # === Helper methods ===
    
    def emit(self, instruction: str, section: Literal["text", "data"]="text"):
        """
        Appends the given instructions to the assembly program's specified section.
        """
        if section == "data":
            self.data_section.append(instruction)
        else:
            self.text_section.append(instruction)

    def error(self, message: str):
        raise Exception(f"Compiler Error at '{self.current_line_number}': {message}")

    def compile_node(self, node: ASTNode):
        """
        Dynamically dispatch to the correct compilation method for an ASTNode
        subclass. If one is not found, a dummy method will be returned.
        """  
        method_name = f"_compile_{type(node).__name__}"
        method = getattr(self, method_name, self._missing_compile_node)
        return method(node)

    def _missing_compile_node(self, node, *args, **kwargs):
        raise NotImplementedError(f"No compile method defined for {type(node).__name__}")

    def _compile_Program(self, node: Program):
        for line_number, statement in sorted(node.statements.items()):
            self.current_line_number = line_number
            self.emit(f".L_line_{line_number}:")
            self.compile_node(statement)

    