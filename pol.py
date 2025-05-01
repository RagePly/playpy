#!/bin/env python3
import sys, operator, math
tokens = sys.stdin.readlines()
stack = []

def pop():
    global stack
    return stack.pop()

def push(x):
    global stack
    stack.append(x)

def op1(f):
    return f(pop())

def op2(f):
    y,x = pop(), pop()
    return f(x,y)

for tok in filter(bool, map(str.strip, tokens)):
    match tok:
        case "+":
            push(op2(operator.add))
        case "-":
            push(op2(operator.sub))
        case "*":
            push(op2(operator.mul))
        case "/":
            push(op2(operator.truediv))
        case "^":
            push(op2(operator.pow))
        case _:
            if hasattr(math, tok):
                push(op1(getattr(math, tok))) 
            else:
                push(float(tok))

print("\n".join(map(str, stack)))

