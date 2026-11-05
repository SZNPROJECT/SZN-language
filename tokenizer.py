import lexer

class Token():
    def __init__(self, token, raw = None):
        self.token = token
        self.raw = TokenCatalog.ReverseTable[token] if raw is None and token in TokenCatalog.ReverseTable else raw

    def __str__(self):
        return self.token

class TokenCatalog():

    TranslationTable = {
        "var": "Var",

        "int": "Integer",
        "float": "Float",
        "string": "String",
        "bool": "Boolean",
        "list": "List",
        "set": "Set",

        "=": "Assignment",
        ".": "Dot",
        ",": "Comma",

        "of": "Of",
        "from" : "From",
        "<<" : "Attribute",
        "remove" : "Remove",

        ";": "EOL",
        "(": "OpenB1",
        ")": "ClosedB1",
        "{": "BlockOpen",
        "}": "BlockClosed",
        "[": "OpenB3",
        "]": "ClosedB3",
        '"': "Quote",
        "'": "Quote",

        "+": "Plus",
        "-": "Minus",
        "*": "Times",
        "/": "Divide",
        "^": "Power",

        "?": "Optional",

        "sin": "Sine",
        "cos": "Cosine",

        "--": "ConsMinus",
        "++": "ConsPlus",
        "+=": "Increment",
        "-=": "Decrement",
            
        "and": "And",
        "or": "Or",
        "not": "Not",
        "xor": "Xor",

        "==": "Equals",
        "!=": "NotEquals",
        ">=": "GreaterOE",
        "<=": "LessOE",
        ">": "Greater",
        "<": "Less",

        "if": "If",
        "else": "Else",
        "while": "While",
        "for": "For",
        "foreach": "Foreach",
        "return": "Return",
        "fn": "Function",
        "print": "Print",

        "null": "Null",
        "true": "True",
        "false": "False",

        "extern": "External",
        "direct": "Direct",

        "class": "Class"
    }

    ReverseTable = {v: k for k, v in TranslationTable.items()}

    BooleanOperators = [
        "And", "Or", "Xor", "Equals", 
        "GreaterOE", "LessOE", "Greater", "Less"      
    ]

    BinaryOperators = [
        "Plus", "Minus", "Times", "Divide", "Power",
        "And", "Or", "Xor", "Equals", 
        "GreaterOE", "LessOE", "Greater", "Less", 
        "ConsMinus", "ConsPlus", "Increment", "Decrement" 
    ]
    
    
    numeric = ["Integer", "Real", "Float", "Double"]

    OperatorsConfig = {
        "Plus":      [-1,  1, False],
        "Minus":     [-1,  1, True],
        "Times":     [-1,  2, False],
        "Divide":    [-1,  2, False],
        "Power":     [1, 3, False],

        "Sine":      [-1, 5,  True ],
        "Cosine":    [-1, 5,  True ],
            
        "And":       [-1, -2, False],
        "Or":        [-1, -3, False],
        "Not":       [-1, -1, True ],
        "Xor":       [-1, -3, False],

        "Equals":    [-1,  0, False], 
        "GreaterOE": [-1,  0, False], 
        "LessOE":    [-1,  0, False], 
        "Greater":   [-1,  0, False], 
        "Less":      [-1,  0, False], 
            
        "Increment": [1, 0, False], 
        "Decrement": [1, 0, False]
    }
    
    def GetOperators():
        return TokenCatalog.OperatorsConfig.keys()
    
    GenericTypeTokens = [
        "Integer", "Float", "Double", "Real", "String", "Boolean"
    ]
    
    GenericTypesRaw = [
        "int", "float", "string", "bool"
    ]

    AllTypeTokens = GenericTypeTokens
    AllTypesRaw = GenericTypesRaw

    SeparationPair = ["Comma", ","]
    
class UnknownOperator(Exception):
    def __init__(symbol : str):
        super().__init__(f"Cannot resolve following symbol: '{symbol}'")
            

class Tokenizer():
    def Compare(token : str, target : list[str]):
        if target == ["Anything"]: return True
        if target in TokenCatalog.AllKeywords: return True

        return token in target

    def Translate(raw : list) -> list:
        raw = list(map(lambda x: TokenCatalog.TranslationTable[x] if x in TokenCatalog.TranslationTable else x, raw))
        for i, string in enumerate(raw):
            if not (string in TokenCatalog.TranslationTable.values()):
                type = lexer.Lexer.GetCharacterType(string)
                if len(string) > 1 and string[0] == string[-1] and string[0] in ['"', "'"]:
                    raw[i] = "String"
                elif type == 0:
                    raw[i] = "Name"
                elif type == 1:
                    raw[i] = "Number"
                elif string[0] == "-" and string[0:-1]:
                    raw[i] = "Number"
                else:
                    raw[i] = "ERR"
        return raw

    def Merge(tokens : list, raw : list):
        r = []
        for i, t in enumerate(tokens):
            r += [Token(t, raw[i])]
        return r
                

    