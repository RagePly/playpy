def foldl(f, xs):
    assert xs
    match xs:
        case [x]: return x
        case [*xs, x]: return f(foldl(f, xs), x)

def fmap(f,p):
    def np(s):
        match p(s):
            case None: return None
            case x,rs: return f(x), rs
    return np

def pure(x):
    return lambda s: (x, s)

def sec(pf, p):
    def np(s):
        match pf(s):
            case None: return None
            case f,rs: return fmap(f,p)(rs)
    return np

def liftA2(f, p1, p2):
    return sec(fmap(lambda x: lambda y: f(x,y), p1), p2)

def seqA(ps):
    return foldl((lambda p1,p2: liftA2(lambda x,y: x+[y], p1, p2)), [pure([])] + ps)

def oneof(*ps):
    def np(s):
        match ps[0](s):
            case None: return oneof(*ps[1:])(s) if len(ps) > 1 else None
            case r: return r
    return np

def left(pl,pr):
    return liftA2(lambda x,y: x, pl, pr)

def right(pl,pr):
    return liftA2(lambda x,y: y, pl, pr)

def many(p): 
    def np(s):
        match p(s):
            case x,rs:
                l, rrs = np(rs)
                return [x] + l, rrs
        return ([], s)
    return np

def join(p):
    return fmap(lambda l: "".join(l), p)

def more(p):
    def np(s):
        match many(p)(s):
            case [],_: return None
            case r: return r
    return np

                        
def pc(c):
    return lambda s: (c,s[1:]) if s and c == s[0] else None

def pt(f):
    return lambda s: (s[0], s[1:]) if s and f(s[0]) else None

pd = pt(str.isdigit)
pn = fmap(int, join(more(pd)))

def ps(s):
    return join(seqA(list(map(pc,s))))

ws = many(pt(str.isspace))
def sepby(sep, p):
    return oneof(liftA2(lambda f,rs: [f] + rs, p, many(right(ws, right(sep, right(ws, p))))), pure([]))

pJson = lambda s: oneof(pNull, pBool, pDigit, pLit, pArray, pObject)(s)
pNull = fmap(lambda x: None, ps("null"))
pBool = fmap(lambda r: r == "true", oneof(ps("true"), ps("false")))
pDigit = pn
pLit = left(right(pc("\""), join(many(oneof(ps("\\\""), pt(lambda c: c != "\""))))), pc("\""))
pArray = left(right(pc("["), right(ws, sepby(pc(","), pJson))), right(ws, pc("]")))
pObject = left(right(pc("{"), right(ws, fmap(dict, sepby(pc(","), liftA2(lambda k, v: (k, v), left(pLit, right(ws, pc(":"))), right(ws, pJson)))))), right(ws, pc("}")))

def parse_json(s):
    match pJson(s):
        case x, "": return x
        case _: return None

