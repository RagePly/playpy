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
- [svt\_fetch\_rss.py](./svt_fetch/svt_fetch_rss.py): I got annoyed that I can't see edits on news articles, especially when I want to point out journalists' grammar mistakes. This script is part of a small project to monitor the history of SVT's headlines. This script's sole purpose is to output the text of all headline-articles into a folder.
- [nda.py](./nda.py): A simple N-dimensional array library. Not complete, but some *numpy*-inspired dispatching works.
- [koket.py](./recept-fetch/koket.py): A script for fetching all ingredients in a [köket](https://www.koket.se/)-recipy and generating a report of them.
- [courses.py](./university-fetch/courses.py): A script for fetching all master-level courses (name, period, examination) for the university I attend. The University's site is annoying to navigate so I wish to scrape it to gain better insight. Very much WiP.
