import lexer
import tokenizer
import parse
import node
import time
import generator
import moderngen
import optimize

from sys import argv

def main(custom = ''):
    if len(argv) == 1 : raise Exception("Incorrect use. Use '\\ main.py <pathToFile>'")
    start_time = time.monotonic()
    

    originalfile = open(argv[1] if custom=='' else custom, "r")
    original = originalfile.read()
    originalfile.close()


    separated = lexer.Lexer.Separate(original)
    bonded = lexer.Lexer.Bond(separated)
    parse.Result.original = bonded
    cleaned = lexer.Lexer.Clean(bonded)
    tokenized = tokenizer.Tokenizer.Merge(tokenizer.Tokenizer.Translate(cleaned), cleaned)
    [print(t) for t in tokenized]
    AST = parse.Constructor.Construct(tokenized)

    optimize.Optimizer.UnfoldExpressions()
    optimize.Optimizer.Bake()

    for s in AST : node.Visualize(s)

    moderngen.Generator.ParseAST(AST)
    moderngen.Central.Build("Test", argv[2]) # code.work() life.success() fps = 999

    print(time.monotonic()-start_time)



    

if __name__ == "__main__":
    main()