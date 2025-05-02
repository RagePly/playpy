#!/bin/env python3
import operator

class _F:
    def __init__(self,f): self.f = f
    def __call__(self,x): return self.f(x)
    def __mul__(self,f): return _F (lambda x: self(f(x))) # (\f. \g. \x. f (g x))
    def __pow__(self,f): return _F (lambda x: self * f(x)) # (\f. \g. \x. \y. f (g x y))
    __and__ = __call__ # f & x <=> f(x)

F = _F (_F)

def _curry(n, f):
    def _w(x,l):
        l = l + [x]
        if len(l) == n:
            return f(*l)
        return F (lambda x: _w(x, l))
    return F (lambda x: _w(x,[]))

curry = _curry(2, _curry)

truthy = F (bool)
iff = F (lambda t: K if truthy (t) else flip (K))

K = curry (2) (lambda x,_: x) # K-combinator (\x. \y. x)
S = curry (3) (lambda f,g,x: (f(x) * g)(x)) # S-combinator (\f. \g. \x. (f x) (g x))
I = S (K) (K) # I-combinator (\x. x), (I x) == ((S K K) x)
apply = curry (2) (lambda f,g: f (g))
flip = curry (3) (lambda f,y,x: f (x) (y))

# Implementation of list functionality (with as few python builtins as possible)
_index = curry (2) (list.__getitem__)
_rng = curry (2) (slice)
cat = curry (2) (lambda x,l: l+[x])

head = flip (_index) & -1
tail = flip (_index) & _rng (None) (-1)

index = curry (2) (lambda i,l: iff (i==0) (head) (index (i-1) * tail) & l)

## S and K combinators here since python is not lazy and if-body is evaluated before the
## conditional is checked.
_rev = curry (2) (lambda l,a: iff (l) (S & _rev * tail & flip (cat) (a) * head) (K (a)) & l)
rev = F (lambda l: _rev (l) ([]))

foldr = curry (3) (lambda f,b,l: iff (l) (S & f * head & foldr (f) (b) * tail) (K & b) & l)
foldl = curry (2) (lambda f,b: foldr (flip (f)) (b) * rev)

_mapp = curry (3) (lambda f,l,a: iff (l) (S & _mapp (f) * tail & flip (cat) (a) * f * head) (K & a) & l)
mapp = curry (2) (lambda f,l: _mapp (f) (l) ([]))

# Curry and add some functions to the local scope from module "operator"
assign = curry (3) (operator.setitem) # a,i,x -> a[i]=x
get = curry (2) (getattr) # o,x -> o.x

add_binop = S & assign (locals()) & curry (2) * get (operator)
mapp (add_binop) (["add", "sub", "mul", "truediv", "eq"])

# More list-functions
summ = foldr (add) (0)
prod = foldr (mul) (1)
length = summ * mapp (K & 1)

# Aaaaand back again...
to_py = F (lambda f: lambda *xs: foldl (apply) (f) (list(xs)))

summ_py = to_py & summ
prod_py = to_py & prod
length_py = to_py & length

if __name__ == "__main__":
    l = list(range(1,81))
    print("Stats about numbers 1-80")
    print("Sum:", summ_py(l))
    print("Product:", prod_py(l))
    print("Count:", length_py(l))
    print("Fun fact, this library cannot handle bigger lists!")

