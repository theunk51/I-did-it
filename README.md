Take two of I-did-parser from 4 years ago

```python
python -m pytest --cov=src --cov-report=term-missing tst/
```


# References
1. https://www.dartmouth.edu/basicfifty/commands.html
1. https://www.zx.net.nz/netware/server/411-kvm-2/webdoc/online/wpguide/07ch02t1.html
1. [Darmouth BASIC v1 Manual: First Draft](https://www.dartmouth.edu/basicfifty/basicmanual_1964.pdf)
1. https://retrocomputingforum.com/t/dartmouth-basic-v4-emulator/4426/6
1. https://archive.org/details/bitsavers_dartmouthB_3679804/page/n37/mode/2up
1. [Beginner's Guide to BASIC](https://programming.muthu.co/posts/beginners-guide-to-basic/#google_vignette)
1. https://pdubroy.github.io/200andchange/precedence-climbing/
1. https://bernsteinbear.com/blog/linear-scan/
    - https://dl.acm.org/doi/epdf/10.1145/330249.330250
1. https://web.stanford.edu/class/cs143/
    - https://medium.com/@pasi_pyrro/how-to-write-your-own-c-compiler-from-scratch-with-python-90ab84ffe071
    - https://github.com/Hyper5phere/simple-c-compiler/blob/master/modules/code_gen.py
1. https://www.sra.uni-hannover.de/Lehre/SS25/V_BSB/doc/x86-abi.html
1. http://cs.cornell.edu/courses/cs4120/2022sp/project/abi.pdf
1. http://www.agner.org/optimize/calling_conventions.pdf
1. https://github.com/simon-whitehead/assembly-fun/blob/master/windows-x64/README.md

# Notes
Summary for your Compiler
.data: Use it if you ever add Strings to your language (e.g., let msg = "Error!"), because the text "Error!" must be saved in the file.

.bss: Use it for all spilled variables, because they just need empty RAM slots reserved for when the CPU runs out of registers during math operations.

- RAX is the accumulator variable, so all expression values will be stored there
- if possible, look into how gaps in variable lifespans can be handled
- The way the label counter works is by storing a dict mapping of (label_type: count).

# To-Do
### 📦 1. Program Structure & Statements
- [ ] `program` – Manages sequential program execution with line splits.
- [ ] `line` – Binds a line number to its statement block.
- [ ] `statement` – Routing hub for all statement actions.
- [ ] `let_stmt` – Classic variable assignment (`LET X = ...`).
- [ ] `array_assignment` – Assigning data to an array index (`LET A(1) = ...`).
- [ ] `dim_stmt` – Array memory sizing definition (`DIM A(10,10)`).
- [ ] `func_decl` – Custom user function declaration (`DEF FN...`).
- [ ] `input_stmt` – Halts execution for console runtime input (`INPUT X`).
- [ ] `print_stmt` – Main text and expression printer.
- [ ] `print_item` – Elements valid for printing (strings/math calculations).
- [ ] `print_separator` – Layout spacers (`,` or `;`).
- [ ] `if_stmt` – Logical branching engine with optional `ELSE`.
- [ ] `goto_stmt` – Unconditional branching jump.
- [ ] `gosub_stmt` – Jumps to a subroutine line code.
- [ ] `return_stmt` – Breaks out of subroutines back to `GOSUB`.
- [ ] `for_stmt` – Loop initialization controller with optional `STEP`.
- [ ] `next_stmt` – Increments and terminates the respective loop index.
- [ ] `data_stmt` – Safe list holding hardcoded sequential arrays.
- [ ] `read_stmt` – Variable text loader from `DATA` registers.
- [ ] `stop_stmt` / `end_stmt` – Process termination triggers.
- [ ] `rem_stmt` – System code text remarks and comments parser.

### 🧮 2. Precedence Rules & Expressions
- [ ] `expression` – Top level entry point for mathematical queries.
- [ ] `logical_or` – Evaluates conditional `OR` gates.
- [ ] `logical_and` – Evaluates conditional `AND` gates.
- [ ] `equality` – Handles equal/not-equal comparisons (`==`, `!=`).
- [ ] `comparison` – Solves scalar limits (`<`, `<=`, `>`, `=>`).
- [ ] `term` – Base layer for additive calculations (`+`, `-`).
- [ ] `factor` – Base layer for multiplicative calculations (`*`, `/`).
- [ ] `power` – Exponent evaluation node (`^`).
- [ ] `unary` – Negation toggles and logical inversion (`NOT`, `-`).
- [ ] `primary` – Evaluates atomic math nodes (literals/brackets/brackets).
- [ ] `func_call` – Resolves native and custom user function runs.
- [ ] `array_access` – Look up values at array indices (`A(X,Y)`).

### 🔍 3. Utilities & Lexer Tokens
- [ ] `builtin_funcs` – Math calculations keyword matching (`SIN`, `COS`, etc.).
- [ ] `relation_op` – Relational validation comparisons operators.
- [ ] `line_number` – Validates script structural markers.
- [ ] `literal` – Base classification structure for variables and data.
- [ ] `string` – Processes double-quoted text blocks (`"..."`).
- [ ] `boolean` – Matches boolean state declarations (`TRUE`, `FALSE`).
- [ ] `variable` – Identifies names matching a single letter and optional digit.
- [ ] `number` – Catch-all for routing decimal types.
- [ ] `float` – Decodes decimal notation styles (`3.14`, `.5`).
- [ ] `integer` – Decodes traditional basic integer notation values.
- [ ] `letter` – Resolves standard single alphabetical characters.
- [ ] `digit` – Resolves base standard numeric components (`0-9`).
