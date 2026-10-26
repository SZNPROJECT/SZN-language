from debug import CInfo

import lexer
import tokenizer
import parse
import node
import time
import extract
import generator
import optimize

from sys import argv

def main(custom = ''):
    if len(argv) == 1 : raise Exception("Incorrect use. Use '\\ main.py <pathToFile>'")
    start_time = time.monotonic()
    

    originalfile = open(argv[1] if custom=='' else custom, "r")
    original = originalfile.read()
    originalfile.close()


    stringExtract, extracted = extract.Extractor.RawExtractSingular(original, "'", '"')

    extract.Extractor.storage.update({"string": stringExtract}) #???

    separated = lexer.Lexer.Separate(extracted)
    bonded = lexer.Lexer.Bond(separated)
    cleaned = lexer.Lexer.Clean(bonded)
    tokenized = tokenizer.Tokenizer.Merge(tokenizer.Tokenizer.Translate(cleaned), cleaned)
    print(cleaned, "\n")
    AST = parse.Constructor.Construct(tokenized)

    optimize.Optimizer.UnfoldExpressions()
    optimize.Optimizer.Bake()

    for s in AST : node.Visualize(s)

    generator.Generator.TranslateStatementSet(AST)
    generator.Project.Build(argv[2]) # code.work() life.success() fps = 999



    

if __name__ == "__main__":
    main()