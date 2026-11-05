from node import *
import math
from functools import reduce

class Optimizer:

    def UnfoldExpressions():
        owned = []

        toSerialize = ["Plus", "Times", "Concat"]

        for expr in Expression.all:
            for op in expr.operands:
                if isinstance(op, Expression): owned += [op]

        for expr in Expression.all:
            if not expr in owned and expr.operation in toSerialize:
                expr.Serialize()

    def Bake():
        scheme = {
            "Concat":   [True,  lambda x,y: x+y      ],
            "Plus":     [True,  lambda x,y: x+y      ],
            "Minus":    [False, lambda x,y: x-y      ],
            "Times":    [True,  lambda x,y: x*y      ],
            "Divide":   [False, lambda x,y: x/y      ],
            "Negative": [False, lambda x: -x         ],
            "Power":    [True,  lambda x,y: y**x     ],
            "Sine":     [False, lambda x: math.sin(x)],
            "Cosine":   [False, lambda x: math.cos(x)]
        } #T/F stands for serial and not serial

        typemap = {
            "Integer": int,
            "Float": float,
            "String": str
        }

        isConstant = lambda node: node.baked is not None if isinstance(node, Expression) else isinstance(node, Content)
        getConstantValue = lambda node: node.baked if isinstance(node, Expression) else node.value
        isBakeable = lambda expr : all(isConstant(op) for op in expr.operands) and expr.baked is None and expr.operation in scheme


        while any(isBakeable(expr) for expr in Expression.all):
            for expr in Expression.all:
                if isBakeable(expr):
                    s = scheme[expr.operation]
                    operands = [getConstantValue(op) for op in expr.operands]

                    if expr.operation == "Power": operands.reverse()

                    if s[0]:
                        expr.baked = reduce(s[1], operands)
                    else:
                        expr.baked = s[1](*operands)

                    expr.baked = typemap[expr.finalType](expr.baked)
