# Python Playground

Just some small and possibly obscure scripts I've written

## Scripts

- [fun.py](./fun.py): Higher order functions and playing around with combinators. Trying to make it read like Haskell.
- Calculator: Extremely simple calculator that isn't just `import math,sys; print(eval(sys.stdin.read()))`
  - [tok.py](./tok.py): Tokenizer, cheating with regular expressions. Somewhat useful.
  - [yard.py](./yard.py): Shunting-Yard algorithm implementation.
  - [pol.py](./pol.py): Stack machine, parsing reverse polish notation.
- Json Parser: Some attempts at writing json parsers using parser-combinators. Solutions in less than 100 loc.
  - [funjson.py](./funjson.py): Parser-combinators using only functions that doesnt look appealing.
  - [oojson.py](./oojson.py): Parser-combinators using Object Oriented constructs as an attempt at writing more visually pleasing combinators.

