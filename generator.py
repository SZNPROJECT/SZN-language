from node import *
from debug import CInfo
import random
import os


class Component:
    pass

class Project:
    name = "SZN"
    funcs = []
    def GetAllComponents(): return Project.funcs

    def QMake(path : str):
        try : os.makedirs(path) 
        except FileExistsError: CInfo(f"[FINAL] {path} is already set. Ignoring.")        


    def Build(path : str):
        funcpath = path+f"\\{Project.name}\\data\\{Project.name.lower()}\\function\\"
        minecraftpath = path+f"\\{Project.name}\\data\\minecraft\\tags\\function\\"
        Project.QMake(funcpath)
        Project.QMake(minecraftpath)
        tick = open(f"{minecraftpath}tick.json", "w")
        tick.write('{"values": ["szn:tick"]}')
        tick.close()
        meta = open(path+f"\\{Project.name}\\pack.mcmeta", "w")
        meta.write('{"pack": {"description": "SZN auto-generated","min_format": 119,"max_format": 119}}')
        meta.close()

        for func in Project.funcs:
            CInfo(f"[FINAL] Created function file for {func.name}")
            f = open(f"{funcpath}{func.name}.mcfunction", "w")
            f.write("\n".join(func.content))
            f.close()


class MFunction(Component):
    def __init__(self, name : str, content : list[str] = None):
        self.name = name
        self.content = content if content != None else []

        Project.funcs += [self]

class Generator:

    nametable = {

    }

    storagetable = {

    }

    argumenttable = {

    }

    generalContext = None

    unique = -1 # dont touch it please

    def Unique() -> int:
        unique += 1
        return Generator.unique

    def TranslateStatementSet(AST : list[Node], context : MFunction = None, argmode = False):
        args = 0
        def add(s:str): context.content += [str(s)]

        def Recursive(expr : Returnable) -> dict:
            if isinstance(expr, Call):
                for i, argexpr in enumerate(expr.arg.args):
                    name = Generator.argumenttable[expr.name][i]
                    storage = Generator.storagetable[name]
                    add(f'data modify storage {storage}:{name} set {Recursive(argexpr)["access"]}')
                add(f"function {expr.name}")
                return {
                    "type": "CALL",
                    "content": expr.name,
                    "access": f"from storage szn:returnspace {expr.name}",
                    "serialized": f'{{"type": "storage", "storage": "szn:returnspace", "path": "{expr.name}"}}',
                    "additional": None
                }
            if isinstance(expr, Content):
                if expr.type == "Integer" or expr.type == "Float":
                    return {
                        "type": "CONTENT",
                        "content": expr.value,
                        "access": f"value {expr.value}",
                        "serialized": f'{{"type": "constant", "value": {expr.value}}}',
                        "additional": {"type":expr.type}
                    }
            if isinstance(expr, Reference):
                return {
                    "type": "REFERENCE",
                    "content": Generator.storagetable[expr.name] + ":" + Generator.nametable[expr.name],
                    "access": f"from storage {Generator.storagetable[expr.name] + ":" + Generator.nametable[expr.name]}",
                    "serialized": f'{{"type": "storage", "storage": "szn:{Generator.storagetable[expr.name]}", "path": "{Generator.nametable[expr.name]}"}}',
                    "additional": {"name": expr.name}
                }
            if isinstance(expr, Expression):
                serial = '{"type": "OPERATION", "inputs": [NONE, NONE]}'
                binary = '{"type": "OPERATION", "left": NONE, "right": NONE}'
                unary  = '{"type": "OPERATION", "input": NONE}'

                operands = [Recursive(op) for op in expr.operands]

                operandsSerialized = [op["serialized"] for op in operands]

                convert = {
                    "Plus": "add",
                    "Minus": "sub",
                    "Times": "mul",
                    "Divide": "div",
                    "Power": "pow",
                    "Sine": "sin",
                    "Cosine" : "cos",
                    "Negative": "negate"
                }

                polarC = ["Divide", "Minus"]
                unaryC = ["Sine", "Cosine", "Negative"]
                    
                copmparison_convert = {
                    "Equals",
                    "NotEquals",
                    "GreaterOE",
                    "LessOE",
                    "Greater",
                    "Less"
                }

                serialized = ""

                template = binary if expr.operation in polarC else serial if len(operandsSerialized) > 1 else unary

                template = template.replace("OPERATION",convert[expr.operation])

                for operand in operandsSerialized:
                    template = template.replace("NONE", operand, 1)

                return {
                    "type": "OPERATION",
                    "content": expr.operation,
                    "access": f"compute default float {template}",
                    "serialized": template,
                    "additional": {"type":"BINARY" if expr.operation in polarC else "SERIAL" if len(operandsSerialized) > 1 else "UNARY", "operands": operandsSerialized}
                }


        CInfo(f"[GEN] Parsing new set.")

        for node in AST:
            CInfo(f"[GEN] Translating {node.__class__.__name__}." + (" [ARGUMENT MODE]" if argmode else ''), nt = True)
            print(" "+node.introduce())

            if isinstance(node, Wrapper):
                Recursive(node.expression)
            elif isinstance(node, FunctionDeclaration):
                mfnc = MFunction(node.name)
                Generator.generalContext = mfnc
                Generator.argumenttable[node.name] = []
                Generator.TranslateStatementSet(node.dec.members,mfnc, argmode=True)
                Generator.TranslateStatementSet(node.main.members,mfnc)

            elif isinstance(node, Assignment):
                if node.external != None:
                    add(f"data modify storage szn:{Generator.storagetable[node.target.name]} {Generator.nametable[node.target.name]} set from {node.external.value}")
                else:
                    resolved = Recursive(node.value)
                    if resolved == None : continue
                    print("storage",Generator.storagetable)
                    add(f"data modify storage szn:{Generator.storagetable[node.target.name]} {Generator.nametable[node.target.name]} set {resolved["access"]}")
            
            elif isinstance(node, Declaration):
                convert = {
                    "Integer": ["int", "value", "0"],
                    "Float": ["float", "value", "0f"]
                }                
                storage = f"szn_{convert[node.type][0]}"
                Generator.storagetable.update({node.name: storage})
                if argmode:
                    print(f"Stored argument {node.name}")
                    Generator.nametable.update({node.name: node.name})
                    Generator.argumenttable[Generator.generalContext.name] += [node.name]
                else:
                    Generator.nametable.update({node.name: node.name})
                    #VVV temp solution VVV or nah?
                    artfREF = Reference(node.name)
                    Reference.AddAppearance(node.name, -1) #avoiding duplication of a single instance ap. amount
                    Generator.TranslateStatementSet([Assignment(artfREF, node.value)], context)

            elif isinstance(node, Return):
                resolved = Recursive(node.toReturn)
                add(f"data modify storage szn:returnspace {context.name.lower()} set {resolved['access']}")
                add("return 1")

            elif isinstance(node, Direct):
                add(node.data.value)

            elif isinstance(node, If):
                name = ''.join(random.choice(str.ascii_lowercase) for i in range(8))
                context2 = MFunction(name, [])
                Generator.TranslateStatementSet(node.statement, context2)
                n,s = Recursive(node.condition)
                if s:
                    add(f"execute if data storage {s}:{n} run function szn:{name}")

        CInfo(f"[GEN] Latest set finished successfuly.")

        