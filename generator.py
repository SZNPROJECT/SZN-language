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
            CInfo(f"[FINAL] Created function file for {Generator.nametable[func.name]} ({func.name})")
            f = open(f"{funcpath}{Generator.nametable[func.name]}.mcfunction", "w")
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

    unique = 0

            

    def BuildProject(AST : list[Node], context : MFunction = None, argmode = False):
        args = 0
        def add(s:str): context.content += [str(s)]

        def Recursive(expr : Returnable, name : str = "alpha") -> tuple[str, str|bool]:
            if isinstance(expr, Content):
                if expr.type == "Integer":
                    return expr.value, False
            if isinstance(expr, Reference):
                return Generator.nametable[expr.name], Generator.storagetable[expr.name]
            if isinstance(expr, Expression):
                lo, lst = Recursive(expr.operands[0])
                ro, rst = (Recursive(expr.operands[1], "beta")) if len(expr.operands)==2 else (None, None)
                print(lo,lst,ro,rst)

                convert = {
                    "Plus": "add",
                    "Minus": "sub",
                    "Times": "mul",
                    "Divide": "div",
                    "Power": "pow",
                    "Sine": "sin",
                    "Cosine" : "cos"
                }

                copmparison_convert = {
                    "Equals",
                    "NotEquals",
                    "GreaterOE",
                    "LessOE",
                    "Greater",
                    "Less"
                }

                def GenerateOperand(op : str, storage):
                    return f'{{"type": "storage", "storage": "szn:{storage}", "path": "{op}"}}' if storage != False else f'{{"type": "constant", "value": {op}}}'

                if len(expr.operands)>1:
                    add(f'data modify storage szn:internal {name} set compute default float {{"type": "{convert[expr.operation]}", "inputs": [{GenerateOperand(lo, lst)}, {GenerateOperand(ro, rst)}]}}')
                else:
                    add(f'data modify storage szn:internal {name} set compute default float {{"type": "{convert[expr.operation]}", "input": {GenerateOperand(lo, lst)}}}')
                return name, "internal"

        CInfo(f"[GEN] Parsing new set.")

        for node in AST:
            CInfo(f"[GEN] Translating {node.__class__.__name__}.")
            if isinstance(node, FunctionDeclaration):
                Generator.nametable.update({node.name: node.name.lower()})
                Generator.BuildProject(node.main.members,MFunction(node.name), True)
                Generator.BuildProject(node.main.members,MFunction(node.name), False)

            elif isinstance(node, Assignment):
                if isinstance(node.value, Content) and node.value.value == None:
                    add(f"data modify storage szn:{Generator.storagetable[node.target.name]} {Generator.nametable[node.target.name]} set value 0")
                else:
                    n, s = Recursive(node.value)
                    if s:
                        add(f"data modify storage szn:{Generator.storagetable[node.target.name]} {Generator.nametable[node.target.name]} set from storage szn:{s} {n}")
                    else:
                        add(f"data modify storage szn:{Generator.storagetable[node.target.name]} {Generator.nametable[node.target.name]} set value {n}")
            
            elif isinstance(node, Declaration):
                convert = {
                    "Integer": ["int", "value", "0"]
                }                
                storage = f"szn_{convert[node.type][0]}"
                if argmode:
                    Generator.nametable.update({node.name: str(args)})
                    Generator.storagetable.update({node.name: storage})
                    args +=1
                else:
                    Generator.nametable.update({node.name: node.name})
                    #VVV temp solution VVV
                    artfREF = Reference(node.name)
                    Reference.AddAppearance(node.name, -1) #avoiding duplication of a single instance ap. amount
                    Generator.BuildProject([Assignment(artfREF, node.value)], context)
            elif isinstance(node, Return):
                Recursive(node.toReturn)
                add("data modify storage szn:internal return set from storage szn:internal alpha")
                add("return 1")

            elif isinstance(node, Direct):
                add(node.data.value)

            elif isinstance(node, If):
                name = ''.join(random.choice(str.ascii_lowercase) for i in range(8))
                context2 = MFunction(name, [])
                Generator.BuildProject(node.statement, context2)
                n,s = Recursive(node.condition)
                if s:
                    add(f"execute if data storage {s}:{n} run function szn:{name}")

        CInfo(f"[GEN] Latest set finished successfuly.")

        