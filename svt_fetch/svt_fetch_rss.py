#!/bin/env python3
from requests import Session
from bs4 import BeautifulSoup
from sys import stderr, argv
from re import compile as compile_re
from os import mkdir

assert len(argv) == 2, "usage: svt_fetch_rss OUTDIR"

_, outdir = argv
try: mkdir(outdir);
except FileExistsError: ...
html_parser = lambda d: BeautifulSoup(d, "lxml")
xml_parser = lambda d: BeautifulSoup(d, "xml")

with Session() as s: 
    rss_r = s.get("https://svt.se/rss.xml")
    
    assert rss_r.ok, f"failed to fetch rss.xml ({rss_rstatus_code})" 
    rss = xml_parser(rss_r.text)

    links = [item.link.string
             for item in rss.rss.channel.find_all("item")]

    for link in links:
        art_r = s.get(link)

        if not art_r.ok:
            print(f"failed to fetch {link}", file=stderr)
            continue

        html = html_parser(art_r.content.decode())
        article = html.find(itemprop="articleBody") 

        # remove "no-javascript" reminder
        if (msg := article.find(**{"class":compile_re("NoScriptMessage.*")})) is not None:
            msg.decompose()
        content = article.get_text()

        _, title = link.rsplit("/", 1)
        with open(f"{outdir}/{title}", "w") as f:
            f.write(content)

