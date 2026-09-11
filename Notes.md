- an opportunity for improvement is the have the exponentiation be like a function call to reduce the number of repetitions.
- not actually sure there is an explicit logical AND, OR, NOT in basic
- the register allocator could be refactored in a number of ways.
    1. use bisect.insort() or sort lists such that the element in question is located at the last index
    2. changing the location of variables based on its current use time
- `Generator.get_variable_location()` will need to be eliminated once the semantic analyzer is re-added to the compiler
- The semantic analysis for valid variable names should probably be thrown during Lexer()

Task List
- [ ] The parsing function table should be separated into two dicts because most of the entries only have one parsing function. It also makes the parse_expression() function more readable.
- [ ] This entire project needs some refactoring
- [ ] update the lexer to match the grammatical constructs of Dartmouth BASIC