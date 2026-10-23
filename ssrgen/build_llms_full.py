#!/usr/bin/env python3
"""llms-full.txt: полный текст главных посадочных одним файлом для ИИ-поисковиков (метод ВИДНО, 23.10.2026).

Берёт адреса из public/llms.txt (его пишет entitygen/build_entities.py), читает собранные
страницы public/<путь>/index.html и складывает их текст (заголовки, абзацы, списки, таблицы)
в public/llms-full.txt. Ничего на страницах не меняет.

Запуск из корня репозитория последним шагом пересборки:  python3 ssrgen/build_llms_full.py .
"""
import os
import re
import sys
from html.parser import HTMLParser
from urllib.parse import urlparse

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
PUB = os.path.join(ROOT, "public")
MAX_PAGE = 7000  # символов на страницу: хватает на ответ, таблицу и FAQ

SKIP = {"script", "style", "noscript", "svg", "nav", "header", "footer", "form", "button", "iframe", "template"}
BLOCK = {"p", "div", "section", "article", "li", "tr", "h1", "h2", "h3", "h4", "table", "ul", "ol", "dd", "dt", "details", "summary", "br"}


class Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip = 0
        self.in_main = 0
        self.has_main = False
        self.lines_main, self.lines_all = [], []
        self.cur = []
        self.prefix = ""
        self.cells = None

    def _flush(self):
        t = re.sub(r"\s+", " ", "".join(self.cur)).strip()
        self.cur = []
        if t:
            line = self.prefix + t
            self.lines_all.append(line)
            if self.in_main:
                self.lines_main.append(line)
        self.prefix = ""

    def handle_starttag(self, tag, attrs):
        if tag in SKIP:
            self.skip += 1
            return
        if self.skip:
            return
        if tag == "main":
            self.in_main += 1
            self.has_main = True
        if tag in ("td", "th") and self.cells is not None:
            self.cur = []
            return
        if tag == "tr":
            self._flush()
            self.cells = []
            return
        if tag in BLOCK:
            self._flush()
            if tag in ("h1", "h2", "h3"):
                self.prefix = {"h1": "## ", "h2": "### ", "h3": "#### "}[tag]
            elif tag == "li":
                self.prefix = "- "

    def handle_endtag(self, tag):
        if tag in SKIP:
            self.skip = max(0, self.skip - 1)
            return
        if self.skip:
            return
        if tag in ("td", "th") and self.cells is not None:
            self.cells.append(re.sub(r"\s+", " ", "".join(self.cur)).strip())
            self.cur = []
            return
        if tag == "tr" and self.cells is not None:
            row = " | ".join(c for c in self.cells if c)
            self.cells = None
            if row:
                self.lines_all.append(row)
                if self.in_main:
                    self.lines_main.append(row)
            return
        if tag in BLOCK:
            self._flush()
        if tag == "main":
            self._flush()
            self.in_main = max(0, self.in_main - 1)

    def handle_data(self, data):
        if not self.skip:
            self.cur.append(data)


def page_text(path):
    p = Text()
    with open(path, encoding="utf-8") as f:
        p.feed(f.read())
    p._flush()
    lines = p.lines_main if p.has_main and p.lines_main else p.lines_all
    out, seen = [], set()
    for ln in lines:
        if ln in seen and not ln.startswith("#"):
            continue
        seen.add(ln)
        out.append(ln)
    txt = "\n".join(out)
    return txt[:MAX_PAGE].rsplit("\n", 1)[0] if len(txt) > MAX_PAGE else txt


def main():
    llms = os.path.join(PUB, "llms.txt")
    if not os.path.exists(llms):
        sys.exit("нет public/llms.txt, сначала entitygen/build_entities.py")
    src = open(llms, encoding="utf-8").read()
    head = src.split("\n## ", 1)[0].strip()
    site = None
    urls = []
    for u in re.findall(r"https?://[^\s)\]]+", src):
        pu = urlparse(u)
        site = site or pu.netloc
        if pu.netloc != site or pu.fragment or u in urls:
            continue
        urls.append(u)
    parts = [head, "", "Полный текст главных страниц. Краткая карта: https://%s/llms.txt" % site, ""]
    n = 0
    for u in urls:
        rel = urlparse(u).path.strip("/")
        f = os.path.join(PUB, rel, "index.html") if rel else os.path.join(PUB, "index.html")
        if not rel or not os.path.exists(f):
            continue
        body = page_text(f)
        if not body:
            continue
        parts += ["---", "URL: " + u, body, ""]
        n += 1
    with open(os.path.join(PUB, "llms-full.txt"), "w", encoding="utf-8") as fo:
        fo.write("\n".join(parts).rstrip() + "\n")
    print("llms-full.txt: %d страниц" % n)


if __name__ == "__main__":
    main()
