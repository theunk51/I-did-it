from lexer import Lexer
from parser import Parser
from eval import Interpreter


white = '\033[0m'
yellow = '\033[33m'
teal = '\033[36m'
magenta = '\033[35m'

if __name__ == "__main__":
    l = Lexer()
    d = Parser()
    i = Interpreter()

    prog = []
    # for _ in range(5):
    #     s = input("> ")
    #     if s.lower() == "stop":
    #         break
    #     else:
    #         tokens = l.tokenize(s)
    #         tree = d.parse(tokens)
    #         print(teal, tree, white)
           # prog.append(s)
    
    # #prog = '\n'.join(prog)
    # # print(prog)
    prog = "10 LET x = 9\n30 LET c = 8\n20 "
    tokens = l.tokenize(prog)
    print(yellow, tokens, white)
    tree = d.parse(tokens)
    print(teal, tree, white)
    final = i.interpret(tree)
    print(magenta, final, white)




# rgb_to_ansi = lambda r, g, b : f"\033[38;5;{r};{g};{b}m"


"""
if __name__ == "__main__":
    l = Lexer()
    d = Parser()

    with open('example.bas', 'r') as f:
        lines = "".join(f.readlines())
        f.close()
    
    tokens = l.tokenize(lines)
    print(yellow, tokens, white)
    tree = d.parse(tokens)
    print(tree)
    
"""