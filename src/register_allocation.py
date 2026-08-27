from dataclasses import dataclass
from collections import deque
from bisect import insort

from src.ast_nodes import *


__all__ = ['RegisterAllocator']

@dataclass(slots=True)
class Lifespan:
    name: str
    start: int
    end: int


class RegisterAllocator:
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

    While not mathematically optimal (like Graph Coloring), Linear Scan allocation is fast to 
    implement and compile. Because BASIC defines all variables as global in any scope, all register spills 
    go to the .bss section. Additionally, while BASIC allows up to 286 unique variables, a single 
    program rarely uses all of them. By allocating only what is actively used, this strategy 
    prevents the massive overallocation of memory that would occur if we preemptively reserved 
    space for all 286. It guarantees that the fast CPU registers always hold the variables 
    needed soonest, while dormant variables are shuffled into RAM until they are actually needed again.
    Variables will only have one location for its entire lifetime.
    """

    __SPILL_TEMPLATE = "%s_bss(%rip)"

    def __init__(self, program: Program):
        self.program = program

        # State for Pass 1 (Lifespans)
        self.variable_lifespans: dict[str, Lifespan] = {}
        self.current_line = 0
        
        # State for Pass 2 (Allocation)
        self.free_registers = deque([
            '%r8', '%r9', '%r10', '%r11', '%r12', '%r13', 
            '%r14', '%rbx', '%rcx', '%rsi', '%rdi'
        ])
        self.active_lifespans: list[Lifespan] = []
        self.allocation_map: dict[str, str] = {}

    @classmethod
    def allocate(cls, program: Program) -> dict[str, str]:
        """
        The static entry point. 
        Creates a short-lived instance to track state during the AST traversal,
        then returns the final allocation map and discards the instance.
        """
        allocator = cls(program)
        allocator.analyze_variable_lifespans()
        allocator.compute_register_allocation()
        return allocator.allocation_map


    def analyze_variable_lifespans(self):
        for line, statement in sorted(self.program.statements.items()):
            self.current_line = line
            self.analyze_variables_in_nodes(statement)

        # for lifespan in self.variable_lifespans.values():
        #     print(lifespan)

    def _mark_variable_lifespan(self, variable: str):
        if variable not in self.variable_lifespans:
            self.variable_lifespans[variable] = Lifespan(
                name=variable,
                start=self.current_line,
                end=self.current_line
            )
        else:
            self.variable_lifespans[variable].end = self.current_line

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
        sorted_lifespans = sorted(self.variable_lifespans.values(), key=lambda x: x.start)
        for current_lifespan in sorted_lifespans:
            # Expire old variables: if another allocated variable dies before the current variable starts,
            # return the register so that it can be used by the current variable
            for active_lifespan in self.active_lifespans[:]:
                if active_lifespan.end < current_lifespan.start:
                    self.active_lifespans.remove(active_lifespan)
                    register = self.allocation_map[active_lifespan.name]
                    self.free_registers.append(register)

            # allocate or spill registers
            if len(self.free_registers) > 0:
                register = self.free_registers.popleft()
                self.allocation_map[current_lifespan.name] = register
                insort(self.active_lifespans, current_lifespan, key=lambda x: x.end)
            else:
                longest_lifespan = self.active_lifespans[-1]
                if longest_lifespan.end > current_lifespan.end:
                    # the allocated variable lives longer, so we can steal its register. The kicked
                    # variable is stored in the .bss section.
                    register = self.allocation_map[longest_lifespan.name]
                    self.allocation_map[longest_lifespan.name] = self.__SPILL_TEMPLATE % longest_lifespan.name
                    self.allocation_map[current_lifespan.name] = register
                    self.active_lifespans.pop(-1)
                    insort(self.active_lifespans, current_lifespan, key=lambda x: x.end)
                else:
                    # the current variable lives the longest so far, so spill into BSS
                    self.allocation_map[current_lifespan.name] =  self.__SPILL_TEMPLATE % current_lifespan.name
        
        