def foldl(f, xs):
    assert xs
    match xs:
        case [x]: return x
        case [*xs, x]: return f(foldl(f, xs), x)

class P:
    def __init__(self, p):
        self.p = p

    def __call__(self, s): return self.p(s)

    def __rmatmul__(self, f):
        return P(lambda s:
            (f(r[0]), r[1]) if (r := self(s)) else None)

    def __and__(self, p):
        return P(lambda s:
            (r[0] @ p)(r[1]) if (r := self(s)) else None)

    def __or__(self, p): return P(lambda s: self(s) or p(s))

    def __lt__(self, p): return P.liftA2(lambda x,_: x)(self, p)

    def __gt__(self, p): return P.liftA2(lambda _,y: y)(self, p)

    @property
    def many(self):
        def r(s):
            match self(s):
                case x, rs:
                    l, rrs = r(rs)
                    return [x] + l, rrs
            return ([], s)
        return P(r)

    @property
    def some(self):
        return P(lambda s: r if (r := self.many(s))[0] else None)

    @property
    def join(self): return "".join @ self

    def parse(self, s):
        match self(s):
            case x,"": return x
            case _: return None
    
    @staticmethod
    def pure(x): return P(lambda s: (x,s))

    @staticmethod
    def liftA2(f):
        return lambda p1, p2: ((lambda x: lambda y: f(x,y)) @ p1) & p2

    @staticmethod
    def seqA(ps):
        return foldl(P.liftA2(lambda x,y: x+[y]), [P.pure([])] + ps)

pt = lambda f: P(lambda s: (s[0], s[1:]) if s and f(s[0]) else None)
pd = pt(str.isdigit)
pn = int @ pd.some.join
pc = lambda c: pt(c.__eq__)
ps = lambda s: P.seqA([pc(c) for c in s]).join
ws = pt(str.isspace).many
sepby = lambda sep, p: P.liftA2(lambda f,rs:[f]+rs)(p,(((ws>sep)>ws)>p).many) | P.pure([])

pJson = P(lambda s: (pNull | pBool | pDigit | pLit | pArray | pObject)(s)) # avoid forward declaration
pNull = (lambda _:None) @ ps("null")
pBool = (lambda r:r=="true") @ (ps("true") | ps("false"))
pDigit = pn
pLit = (pc("\"") > (ps("\\\"") | pt(lambda c: c!="\"")).many.join) < pc("\"")
pArray = (((pc("[") > ws) > sepby(pc(","), pJson)) < ws) < pc("]")
pObject = (((pc("{") > ws) > (dict @ sepby(pc(","), P.liftA2(lambda k,v:(k,v))((pLit<ws)<pc(":"),ws>pJson)))) < ws) < pc("}")


assert pc('a').parse("a") == "a"
assert pc('a').parse("b") == None
assert pd.parse("1") == "1"
assert pd.parse("2") == "2"
assert (int @ pd).parse("1") == 1
assert (P.pure(int) & pd).parse("1") == 1
assert (pc('a') | pc('b') | pc('c')).parse('c') == 'c'
assert (pc('a') < pc('b')).parse("ab") == "a"
assert (pc('a') > pc('b')).parse("ab") == "b"
assert ((pc('a') > pc('b')) > pc('c')).parse("abc") == "c"
assert pc('a').many.parse("aaa") == ["a", "a", "a"]
assert pc('a').some.parse("") == None
assert ps("abc").parse("abc") == "abc"
assert pn.parse("321") == 321
assert sepby(pc(","), pc("a")).parse("a,a,a") == ["a", "a", "a"]
assert pArray.parse("[1,2,3]") == [1,2,3]
assert pLit.parse('"hej"') == "hej"
assert pObject.parse('{"key": "value"}') == {"key": "value"}
assert pJson.parse('[1,2,3,"hello","world",[1,2,3,4, {"key": "value", "one": [1,2,3]}]]') == [1,2,3,"hello","world",[1,2,3,4,{"key": "value", "one": [1,2,3]}]]
