Take two of I-did-parser from 4 years ago

```python
python -m pytest --cov=src --cov-report=term-missing tst/
```


# References

### BASIC Language & History
- [Dartmouth BASIC Commands - Overview](https://www.dartmouth.edu/basicfifty/commands.html)
- [Dartmouth BASIC v1 Manual: First Draft](https://www.dartmouth.edu/basicfifty/basicmanual_1964.pdf)
- [Dartmouth BASIC Manual - 4th Edition (Jan 1968)](https://archive.org/details/bitsavers_dartmouthB_3679804/page/n37/mode/2up)
- [Dartmouth BASIC v4 Emulator Discussion: Matrices and Vectors](https://retrocomputingforum.com/t/dartmouth-basic-v4-emulator/4426/6)
- [Beginner's Guide to BASIC](https://programming.muthu.co/posts/beginners-guide-to-basic/#google_vignette)
- [NetWare BASIC Language Guide](https://www.zx.net.nz/netware/server/411-kvm-2/webdoc/online/wpguide/07ch02t1.html)

### Parsing & Compiler Theory
- [Stanford CS143: Compilers Course](https://web.stanford.edu/class/cs143/)
- [Precedence Climbing Algorithm (Parsing Expressions)](https://pdubroy.github.io/200andchange/precedence-climbing/)
- [Writing a C Compiler from Scratch with Python](https://medium.com/@pasi_pyrro/how-to-write-your-own-c-compiler-from-scratch-with-python-90ab84ffe071)
    - https://github.com/Hyper5phere/simple-c-compiler/blob/master/modules/code_gen.py
- [TypeScript C Compiler Reference (Rajeev-K/c-compiler)](https://github.com/Rajeev-K/c-compiler/blob/main/compiler.ts#L1036)

### Register Allocation
- [Linear Scan Register Allocation (Overview)](https://bernsteinbear.com/blog/linear-scan/)
- [Linear Scan Register Allocation (Original Poletto/Sarkar ACM Paper)](https://dl.acm.org/doi/epdf/10.1145/330249.330250)

### Assembly, x86-64 ABI & Calling Conventions
- [x86-64 Brief Summary](https://researcher111.github.io/uva-cso1-F23-DG/readings/x86.html#fnref:ms2)
- [x86 and amd64 instruction reference (Felix)](https://www.felixcloutier.com/x86/)
- [Calling conventions for different C++ compilers and operating systems](http://www.agner.org/optimize/calling_conventions.pdf)
- [System V ABI x86-64 Architecture Supplement](https://www.sra.uni-hannover.de/Lehre/SS25/V_BSB/doc/x86-abi.html)
- [Cornell CS4120: System V Calling Convention Guide](http://cs.cornell.edu/courses/cs4120/2022sp/project/abi.pdf)
- [Windows x64 Assembly & Calling Convention Guide](https://github.com/simon-whitehead/assembly-fun/blob/master/windows-x64/README.md)

# Notes
- Strings must be stored in the .data section since it is easier to load from a permanant address than registers. Spilled variables only need empty RAM slots when the CPU runs out of registers to store values, so use .bss.
- RAX is the accumulator variable, so all expression values will be stored there
- if possible, look into how gaps in variable lifespans can be handled
- The way the label counter works is by storing a dict mapping of (label_type: count).
- the stack really only has to be aligned whenever a C function call is made. It is just easier to keep the stack aligned at all times.
- From the 1968 Basic Manual: "that spaces have no significance in BASIC, except in messages which are to be printed out, as in line number 65 above. Thus, spaces may be used, or not used, at will to "pretty up" a program and make it more readable. Statement 10 could have been typed as 10READA,B,D,E and statement 15 as 15LETG=A\*E-B\*D."

# To-Do
### 📦 1. Program Structure & Statements
- [x] `program` – Manages sequential program execution with line splits.
- [x] `line` – Binds a line number to its statement block.
- [x] `statement` – Routing hub for all statement actions.
- [x] `let_stmt` – Classic variable assignment (`LET X = ...`).
- [ ] `array_assignment` – Assigning data to an array index (`LET A(1) = ...`).
- [ ] `dim_stmt` – Array memory sizing definition (`DIM A(10,10)`).
- [x] `func_decl` – Custom user function declaration (`DEF FN...`).
- [ ] `input_stmt` – Halts execution for console runtime input (`INPUT X`).
- [/] `print_stmt` – Main text and expression printer.
- [/] `print_item` – Elements valid for printing (strings/math calculations).
- [/] `print_separator` – Layout spacers (`,` or `;`).
- [ ] `if_stmt` – Logical branching engine with optional `ELSE`.
- [ ] `goto_stmt` – Unconditional branching jump.
- [ ] `gosub_stmt` – Jumps to a subroutine line code.
- [x] `return_stmt` – Breaks out of subroutines back to `GOSUB`.
- [ ] `for_stmt` – Loop initialization controller with optional `STEP`.
- [ ] `next_stmt` – Increments and terminates the respective loop index.
- [ ] `data_stmt` – Safe list holding hardcoded sequential arrays.
- [ ] `read_stmt` – Variable text loader from `DATA` registers.
- [ ] `stop_stmt` / `end_stmt` – Process termination triggers.
- [ ] `rem_stmt` – System code text remarks and comments parser.

### 🧮 2. Precedence Rules & Expressions
- [x] `expression` – Top level entry point for mathematical queries.
- [x] `logical_or` – Evaluates conditional `OR` gates.
- [x] `logical_and` – Evaluates conditional `AND` gates.
- [x] `equality` – Handles equal/not-equal comparisons (`==`, `!=`).
- [x] `comparison` – Solves scalar limits (`<`, `<=`, `>`, `=>`).
- [x] `term` – Base layer for additive calculations (`+`, `-`).
- [x] `factor` – Base layer for multiplicative calculations (`*`, `/`).
- [x] `power` – Exponent evaluation node (`^`).
- [x] `unary` – Negation toggles and logical inversion (`NOT`, `-`).
- [x] `primary` – Evaluates atomic math nodes (literals/brackets/brackets).
- [x] `func_call` – Resolves native and custom user function runs.
- [ ] `array_access` – Look up values at array indices (`A(X,Y)`).

### 🔍 3. Utilities & Lexer Tokens
- [ ] `builtin_funcs` – Math calculations keyword matching (`SIN`, `COS`, etc.).
- [ ] `relation_op` – Relational validation comparisons operators.
- [x] `line_number` – Validates script structural markers.
- [x] `literal` – Base classification structure for variables and data.
- [x] `string` – Processes double-quoted text blocks (`"..."`).
- [x] `boolean` – Matches boolean state declarations (`TRUE`, `FALSE`).
- [x] `variable` – Identifies names matching a single letter and optional digit.
- [x] `number` – Catch-all for routing decimal types.
- [x] `float` – Decodes decimal notation styles (`3.14`, `.5`).
- [x] `integer` – Decodes traditional basic integer notation values.
- [x] `letter` – Resolves standard single alphabetical characters.
- [x] `digit` – Resolves base standard numeric components (`0-9`).
