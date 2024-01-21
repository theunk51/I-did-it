from lexer import Lexer
from parser import Parser
from eval import Interpreter


white = '\033[0m'
yellow = '\033[33m'
teal = '\033[36m'
magenta = '\033[35m'
#blue = '\033[93m'   # 96 = cyan  92 = green # 90 = gray
cyan = '\033[95m'   

""" 
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
    # prog = "10 LET x = -8\n20 c = 7\n30 y = x * c\n40 IF y < 0 THEN PRINT y ELSE LET x = 8"
    prog = "10 let x = 4\n15 IF x < 7 THEN PRINT x\n20 FOR v= TO 10"
    tokens = l.tokenize(prog)
    print(yellow, tokens, white)
    tree = d.parse(tokens)
    print(teal, tree, white)
    final = i.interpret(tree)
    print(magenta, final, white)

"""


rgb_to_ansi = lambda r, g, b : f"\033[38;2;{r};{g};{b}m"





if __name__ == "__main__":
    l = Lexer()
    d = Parser()
    i = Interpreter()

    with open('example.bas', 'r') as f:
       lines = "".join(f.readlines())
       f.close()
    
    # lines = """
    #         5 LET x = 8
    #         10 DIM ARRAY(1,2,3), A2(3, 4, 5)
    #         """.strip()
   
    tokens = l.tokenize(lines)
    color = rgb_to_ansi(31, 237, 23)
    print(color, tokens, white)
    tree = d.parse(tokens)
    for t in tree: 
        print(teal, t, white)
    i.interpret(tree)