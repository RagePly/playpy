#!/bin/env python3
import re, sys

if sys.argv[1:]:
  inp = " ".join(sys.argv[1:])
else:
  inp = sys.stdin.read()

var = r"[_a-zA-Z]\w*"
num = r"\d+(?:\.\d+)?"
string1 = r"\"(?:\\\"|[^\"])*\""
string2 = r"'(?:\\'|[^'])*'"
op = r"[*+^:!|#@$%&/=\\\-`~]+"
contr = r"[\[\]{}(),.]"
r = "|".join([var, num, string1, string2, op, contr])

print("\n".join(re.findall(r, inp)))
