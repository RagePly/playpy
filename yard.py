#!/bin/env python3
import sys

tokens = sys.stdin.readlines()
opstack = []
stack = []

def to_num(s):
    try: return int(s)
    except:
        try: return float(s)
        except: return None

ops = ["^", "*", "/", "+", "-"]
def higher(o1,o2):
    return ops.index(o1) < ops.index(o2)

def is_func(f):
    import math
    return hasattr(math, f)

for tk in filter(bool, map(str.strip, tokens)):
    if (n := to_num(tk)) is not None:
        stack.append(n)
    elif is_func(tk):
        opstack.append(tk)
    elif tk in ops:
        while opstack and opstack[-1] != "(" and higher(opstack[-1], tk):
            stack.append(opstack.pop())
        opstack.append(tk)
    elif tk == ",":
        while opstack[-1] != "(":
            stack.append(opstack.pop())
    elif tk == "(":
        opstack.append(tk)
    elif tk == ")":
        while opstack[-1] != "(":
            stack.append(opstack.pop())
        opstack.pop()
        if opstack and is_func(opstack[-1]):
            stack.append(opstack.pop())
    else:
        print("Unknown token", tk, file=sys.stderr)
        sys.exit(1)

while opstack:
    stack.append(opstack.pop())

print("\n".join(map(str, stack)))
    
