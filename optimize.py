from node import Expression

class Optimizer:

    def SerializeExpressions():
        owned = []

        toSerialize = ["Plus", "Times"]

        for expr in Expression.all:
            for op in expr.operands:
                if isinstance(op, Expression): owned += [op]

        for expr in Expression.all:
            if not expr in owned and expr.operation in toSerialize:
                expr.Serialize()