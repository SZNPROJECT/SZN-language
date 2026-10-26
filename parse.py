# 5th version of that script
from node import *
from functools import reduce
from collections.abc import Iterable
from tokenizer import Token, TokenCatalog
from difflib import SequenceMatcher

class ParseException (Exception):
    def __init__(self, info : str, fix : str = None, expected = "something..."):
        self.info = info
        self.exp = expected 
        self.fix = fix if fix != None else f"Add \"{expected}\"" 

        super().__init__(f'\033[1;41mSyntaxError: {self.info}\033[0m\n\033[14;44mFix: {self.fix}\033[0m')

class Result:
    def __init__(self, value, end : int):
        self.value = value
        self.end = end

    def __bool__(self):
        return not isinstance(self.value, ParseException)

    def __str__(self):
        s = lambda obj: [s(x) for x in obj] if isinstance(obj, list) else str(obj)
        return f"{s(self.value)} ending at {self.end}"

class c:

    def match(expected : Token):
        def run(p, tokens : list[Token]):
            if p >= len(tokens): return Result(ParseException("Insufficient length."), p)
            if tokens[p].token == expected.token:
                return Result(tokens[p], p + 1)
            else:
                return Result(ParseException(f"Expected \"{expected.raw}\", got \"{tokens[p].raw}\".", f"Replace \"{tokens[p].raw}\" with \"{expected.raw}\"."), p)
        return run

    def unfold(parser):
        def run(p, tokens : list[Token]):
            def subf(s):
                if not isinstance(item, list): return s
                for item in s:
                    if isinstance(item, (list, tuple)):
                        yield from subf(item)
                    else:
                        yield item
            r = parser(p, tokens)
            if isinstance(r, list): r.value = list(subf(r.value))
            return r.value

        return run

    def map(parser, f):
        def run(p, tokens):
            r = parser(p, tokens)
            if r: return Result(f(r.value), r.end)
            return r
        return run
    
    def may(parser):
        def run(p, tokens : list[Token]):
            r = parser(p, tokens)
            if r : return r
            else : return Result([], p)
        return run
    
    def many(parser):
        def run(p, tokens : list[Token]):
            acc = []
            while True:
                r = parser(p,tokens)
                if r.end == p: return Result(acc, p)
                if r:
                    p = r.end
                    acc.append(r.value)
                else: return Result(acc, p)
        return run

    def until(parser, stop):
        def run(p, tokens : list[Token]):
            acc = []
            while True:
                r = parser(p,tokens)
                #if r.end == p: return Result(acc, p)
                if r:
                    p = r.end
                    acc.append(r.value)
                elif stop(p,tokens): return Result(acc, p)
                else : return r
        return run

    def seq(*parsers):
        def run(p, tokens : list[Token]):
            acc = []
            cur = p
            for parser in parsers:
                r = parser(cur, tokens)
                if not r:
                    return r                
                acc.append(r.value)
                cur = r.end
            return Result(acc, cur)
        return run
    
    def any(*parsers):
        def run(p, tokens : list[Token]):
            rs = []
            rf = []
            for par in parsers:
                res = par(p, tokens)
                if res: rs.append(res)
                else: rf.append(res)

            if len(rs) == 0:
                best = rf[0]
                for res in rf:
                    if res.end > best.end: best = res
                return best
            else : return rs[0] 
        return run
    
    def sep(content_parser, separator_parser):
        return c.map(c.seq(c.many(c.seq(content_parser, separator_parser)), content_parser), lambda x: [s for p in x[0] for s in p] + [x[1]])

            

class Constructor:
    def Construct(tokens : list[Token]):
        t = lambda x, y = None: c.match(Token(x, y)) 
        n = c.match(Token("Name", "Name"))

        def _returnable(allow_exp = True):
            # No sign of God past this comment.
            operation = c.any(*[t(token) for token in TokenCatalog.GetOperators()])
            unary = c.any(*[t(token) for token in TokenCatalog.GetOperators() if TokenCatalog.OperatorsConfig[token][2]])
            right = c.any(*[t(token) for token in TokenCatalog.GetOperators() if TokenCatalog.OperatorsConfig[token][0]])
            def fold(parser : "function") -> Expression: #expects the set to be valid, expamle: ret-able, opToken, ret-able...
                def run(p, tokens : list[Token | Returnable]):
                    out = parser(p, tokens)
                    if isinstance(out.value, ParseException): return out
                    seq = out.value
                    for i, token in enumerate(seq):
                        if i % 2:
                            seq[i] = Expression(token.token, [None, None])
                    seq[1].operands[0] = seq[0]
                    seq[-2].operands[1] = seq[-1]
                    seq.pop(0)
                    seq.pop()
                    getPriority = lambda n: TokenCatalog.OperatorsConfig[n.operation][1]
                    getAssociativity = lambda n: TokenCatalog.OperatorsConfig[n.operation][0]
                    for i,e in enumerate(seq):
                        if (i+1)%2 == 0:
                            l = getPriority(seq[i-1])
                            r = getPriority(seq[i+1])
                            if l>r: seq[i-1].operands[1] = e
                            elif r>l: seq[i+1].operands[0] = e
                            else: 
                                d = getAssociativity(seq[i-1])
                                seq[i+d].operands[int(d*-1/2 + 0.5)] = e

                    a = 0
                    for i in range(0, len(seq)-1, 2):
                        seq.pop(a+i+1)
                        a -= 1
                    while len(seq) > 1:
                        for i, e in enumerate(seq):
                            if not None in e.operands:
                                l = seq[i-1] if i != 0 else None
                                r = seq[i+1] if i < len(seq) - 1 else None
                                lia = (l != None) and (l.operands[1] == None)
                                ria = (r != None) and (r.operands[0] == None)
                                if lia and ria:
                                    lp, rp = getPriority(l), getPriority(r)
                                    if lp > rp:
                                        l.operands[1] = e
                                    elif rp > lp:
                                        r.operands[0] = e
                                    else:
                                        seq[i+getAssociativity(r)].operands[int(getAssociativity(r)*-1/2 + 0.5)] = e
                                elif lia:
                                    l.operands[1] = e
                                elif ria:
                                    r.operands[0] = e
                                else: continue
                                seq.pop(i)
                    seq[0].ComputeFinalType()
                    return Result(seq[0], out.end)

                        
                return run

            def run(p, tokens : list[Token]):
                execute = []
                if allow_exp : execute = [fold(c.any(c.sep(_returnable(allow_exp=False), operation)))]
                reference = c.map(n, lambda x: Reference(x.raw))
                number = c.any(c.map(c.seq(t("Number"), t("Dot"), t("Number")), lambda x: Content(float(''.join([y.raw for y in x])), "Float")), c.map(t("Number"), lambda x: Content(int(x.raw), "Integer")))
                call = c.map(c.seq(n, t("OpenB1"), c.may(c.sep(_returnable(), t("Comma"))), t("ClosedB1")), lambda x: Call(x[0].raw, [y[0] for i, y in enumerate(x[2]) if (i + 1) % 2 != 0]))
                execute += [number, call, reference]
                o = c.any(*execute)(p, tokens)
                return o

            return run

        def _return():
            return c.map(c.seq(t("Return"), _returnable()), lambda x: Return(x[1]))

        def _block():
            return c.map(c.seq(t("BlockOpen"), c.until(c.any(*statements), t("BlockClosed"))), lambda x: Block([s for s in x[1]]))

        def _argumentDeclaration():
            return c.map(c.seq(t("OpenB1"), c.may(c.sep(n, t("Comma"))), t("ClosedB1")), lambda x: ArgumentDeclatation([y.raw for i, y in enumerate(x[1]) if (i + 1) % 2 != 0]))
        def _functionDeclaration():
            return c.map(c.seq(t("Function"), n, _argumentDeclaration(), _block()), lambda x: FunctionDeclaration(x[1].raw, x[2], x[3]))

        statements = [
            _return()
        ]
        root_statements = [
            _functionDeclaration()
        ]
        AST = c.seq(*root_statements)(0,tokens)
        print(AST)
        return AST.value
        