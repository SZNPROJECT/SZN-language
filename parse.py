# 5th version of that script
from exception import *
from node import *
from functools import reduce
from lexer import Lexer
from collections.abc import Iterable
from tokenizer import Token, TokenCatalog
from difflib import SequenceMatcher
import time


class Result:
    original = None
    def __init__(self, value, end : int):
        self.value = value
        self.end = end

    def __bool__(self):
        return not isinstance(self.value, SZNExpception)

    def __str__(self):
        s = lambda obj: [s(x) for x in obj] if isinstance(obj, list) else str(obj)
        return f"{s(self.value)} at line {Lexer.GetLineByTokenIndex(Result.original,self.end)}, token {self.end}"

class c:

    def match(expected : Token): #single matches 
        def run(p, tokens : list[Token]):
            if p >= len(tokens): return Result(SyntaxException("Insufficient length."), p)
            if tokens[p].token == expected.token:
                return Result(tokens[p], p + 1)
            else:
                return Result(SyntaxException(info=f"Expected \"{expected.raw}\", got \"{tokens[p].raw}\".", fix = f"Replace \"{tokens[p].raw}\" with \"{expected.raw}\".", got = tokens[p].raw, expected=expected.raw), p)
        return run

    def unfold(parser): # flattens the result?
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
            return r

        return run

    def map(parser, f): # maps result with provided function if success, does nothing the result otherwise
        def run(p, tokens):
            r = parser(p, tokens)
            if r: return Result(f(r.value), r.end)
            return r
        return run
    
    def may(parser): # ingnores the failure
        def run(p, tokens : list[Token]):
            r = parser(p, tokens)
            if r : return r
            else : return Result([], p)
        return run
    
    def many(parser): # advances until first failure, then returns the sequence, if none was captured, returns failure
        def run(p, tokens : list[Token]):
            acc = []
            while True:
                r = parser(p,tokens)
                if r.end <= p: return Result(acc, p)
                if r:
                    p = r.end
                    acc.append(r.value)
                else: return Result(acc, p)
        return run

    def until(parser, stop, capture = False): # acts like "many()" with custom terminator, if finds none, returns failure
        def run(p, tokens : list[Token]):
            acc = []
            while True:
                r = parser(p,tokens)
                #if r.end == p: return Result(acc, p)
                s = stop(p,tokens)
                if r:
                    p = r.end
                    acc.append(r.value)
                elif s: 
                    if capture:
                        acc.append([s.value]) 
                        return Result(acc, s.end)
                    else : return Result(acc, r.end)
                else : return r
        return run

    def seq(*parsers): # a regular sequence, returns failure if any of its parsers fails
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
    
    def any(*parsers, exp = "Anything"): # tries all given parsers returns the result of the frist successful one, if none succeeds, returns most advanced failure
        def run(p, tokens : list[Token]):
            rf = []
            for par in parsers:
                res = par(p, tokens)
                if res:return res
                else: rf.append(res)

            best = rf[0]
            for res in rf:
                if res.end > best.end: best = res
            best.value.expected = exp
            return best
        return run

    def anyB(*parsers, exp = None): # tries all parses, returns most advanced result
        def run(p, tokens):
            r = max([par(p, tokens) for par in parsers], key = lambda x: x.end + int(not isinstance(x.value, SZNExpception)))
            if isinstance(r.value, SZNExpception) and exp: 
                return Result(SyntaxException(f'Expected {exp}, got "{r.value.got}".', r.value.got, f'Add or replace "{r.value.got}" with {"an" if exp[0].lower() in 'aeiou' else "a"} {exp} of any kind.'), r.end)
            return r
        return run

    def sep(content_parser, separator_parser): # tries to parse by CONTENT, SEP, ... CONTENT. pattern
        return c.map(c.until(c.seq(content_parser, separator_parser), content_parser, capture=True), lambda x: [z for y in x for z in y])
        #return c.map(c.seq(c.many(c.seq(content_parser, separator_parser)), content_parser), lambda x: [s for p in x[0] for s in p] + [x[1]])

    def all(parser): # success if (one or more) and fully finished to the last token, failure otherwise   
        def run(p, tokens : list[Token]):
            acc = []
            while True:
                r = parser(p,tokens)
                if r.end <= p: return Result(acc, p)
                if r:
                    p = r.end + 1
                    acc.append(r.value)
                else: return r
        return run

    def fail(): #always returns InternalException that ends at -99
        def run(p, *anything):
            return Result(InternalException("Always false. (c.fail)"), -99)
        return run
            
def rec(x):
    if isinstance(x, Iterable):
        for y in x:
            rec(y)
    else:print(x)
class Constructor:
    def Construct(tokens : list[Token]):
        t = lambda x, y = None: c.match(Token(x, y)) 
        n = c.match(Token("Name", "Name"))

        def _returnable(*excepted):
            # No sign of God past this comment.
            operation = c.any(*[t(token) for token in TokenCatalog.GetOperators()])
            unary = c.any(*[t(token) for token in TokenCatalog.GetOperators() if TokenCatalog.OperatorsConfig[token][2]])
            def fold(parser : "function") -> Expression: #expects the set to be valid, expamle: ret-able, opToken, ret-able...
                def run(p, tokens : list[Token | Returnable]):
                    out = parser(p, tokens)
                    if isinstance(out.value, SZNExpception): return out
                    seq = out.value
                    if len(seq) < 2: return Result(InternalException(),p+1)
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
                    seq[0].Finalize()
                    return Result(seq[0], out.end)

                        
                return run

            def run(p, tokens : list[Token]):
                expr =      fold(c.sep(_returnable("expr"), operation))
                reference = c.map(n, lambda x: Reference(x.raw))
                boolean =   c.map(c.any(t("True"), t("False")), lambda x: Content("0b" if x.token == "False" else "1b", "Boolean"))
                number =    c.any(c.map(c.seq(t("Number"), t("Dot"), t("Number")), lambda x: Content(float(''.join([y.raw for y in x])), "Float")), c.map(t("Number"), lambda x: Content(int(x.raw), "Integer")))
                call =      c.anyB(c.map(c.seq(n, t("OpenB1"), t("ClosedB1")), lambda x: Call(x[0].raw,[])), c.map(c.seq(n, t("OpenB1"), c.sep(_returnable(), t("Comma")), t("ClosedB1")), lambda x: Call(x[0].raw, [y for i, y in enumerate(x[2]) if (i + 1) % 2 != 0])))
                embeded =   c.map(c.seq(t("OpenB1"), _returnable(), t("ClosedB1")), lambda x: x[1])
                unaryOP =   c.map(c.seq(unary, _returnable("expr")), lambda x: Expression(x[0].raw if x[0].token != "Minus" else "Negative", [x[1]]))
                string =    c.map(t("String"), lambda x: Content(x.raw[1:-1], "String"))
                component = c.map(c.seq(_returnable("component", "expr"), c.any(t("Of"), t("From")), _returnable("component", "expr")), lambda x: External("entity" if x[1].token == "Of" else "storage", x[2], x[0]))
                execute = [e for e in [boolean, expr, call, reference, number, embeded, unaryOP, string, component] if e not in [locals()[n] for n in excepted]]
                o = c.anyB(*execute)(p, tokens)
                #Visualize(o.value)
                return o

            return run

        def _return():
            return c.anyB(c.map(c.seq(t("Return"), _returnable()), lambda x: Return(x[1])), c.map(t("Return"), lambda x: Return(None)))

        def _block():
            return c.map(c.seq(t("BlockOpen"), c.until(c.anyB(*statements), t("BlockClosed"))), lambda x: Block([s for s in x[1]]))

        def _argumentDeclaration():
            return c.map(
                c.unfold(c.seq(t("OpenB1"), c.may(c.any(c.sep(n, t("Comma")), n)), t("ClosedB1"))), 
                lambda x: ArgumentDeclatation([y.raw for i, y in enumerate(x[1]) if (i + 1) % 2 != 0])
                )
        
        def _functionDeclaration():
            return c.map(c.seq(t("Function"), n, _argumentDeclaration(), _block()), lambda x: FunctionDeclaration(x[1].raw, x[2], x[3]))

        def _assignment():
            return c.map(c.seq(_returnable(), t("Assignment"), _returnable()), lambda x: Assignment(x[0], x[2]))

        def _direct():
            return c.map(c.seq(t("Direct"), _returnable()), lambda x: Direct(x[1]))

        def _attributeModify():
            return c.anyB(
                c.map(
                    c.seq(n,n, t("Of"), _returnable(), t("Assignment"), _returnable()),
                    lambda x: AttributeModify(x[3], x[0].raw, x[1].raw, x[5])
                ),
                c.map(
                    c.seq(t("Remove"), n, n, t("Of"), _returnable()),
                    lambda x: AttributeModify(x[4], x[1].raw, x[2].raw, False)
                )
            )#air_drag_modifier of "@s" lifted total = 2 
             #remove air_drag_modifier lifted of "@s"
        
        statements = [
            _attributeModify(),
            _direct(),
            _return(),
            _assignment()
        ]
        root_statements = [
            _functionDeclaration()
        ]
        AST = c.all(c.anyB(*root_statements))(0,tokens)
        print(AST)
        return AST.value
        