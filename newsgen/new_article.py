# -*- coding: utf-8 -*-
"""
Генератор одной новости ПодборVPS из черновика JSON.
  1) читает черновик (по умолчанию newsgen/_draft.json)
  2) создаёт public/news/<slug>/index.html (в дизайне сайта, папочный URL /news/<slug>/)
  3) добавляет запись в начало feed в newsgen/news.json
После запуска — прогнать newsgen/build_site.py, чтобы обновились каталог /news/, sitemap и блок новостей на главной.

Запуск:  python3 newsgen/new_article.py [путь_к_черновику.json] [КОРЕНЬ]

Черновик (см. newsgen/draft.example.json):
{
  "slug": "...", "id": "...", "tag": "Рынок", "date": "25 августа 2026", "iso": "2026-08-25",
  "title": "...", "description": "... (до ~160 симв., для сниппета)", "teaser": "... (1-2 предложения в каталог)",
  "lead": "... (вводный абзац)",
  "sections": [ {"h2": "Заголовок раздела", "paras": ["абзац", "абзац"]}, ... ],
  "source": {"name": "Название издания", "url": "https://..."},          // необязательно, но желательно
  "provider": {"id": "timeweb", "name": "Timeweb Cloud", "url": "https://ref-ссылка", "utm": "news_<id>"}  // необязательно
}
"""
import os, sys, re, json, html

DRAFT = sys.argv[1] if len(sys.argv) > 1 else "newsgen/_draft.json"
ROOT  = sys.argv[2] if len(sys.argv) > 2 else "."
PUB   = os.path.join(ROOT, "public")
COUNTER = "111248718"

d = json.load(open(DRAFT, encoding="utf-8"))
req = ["slug","id","tag","date","iso","title","description","teaser","lead","sections"]
miss = [k for k in req if not d.get(k)]
assert not miss, "в черновике нет полей: %s" % miss
slug = d["slug"]; url = "https://podborvps.ru/news/%s/" % slug

def rd(p):
    with open(p, encoding="utf-8") as f: return f.read()

# ---- шасси из свежей закреплённой статьи ----
news = json.load(open(os.path.join(ROOT, "newsgen", "news.json"), encoding="utf-8"))
sample_slug = news["pinned"][0]["slug"]
sample = rd(os.path.join(PUB, "news", sample_slug, "index.html"))
head = sample[:sample.find("</head>")]
header = sample[sample.find("<body>")+6 : sample.find('<main class="wrap">')]
footer = sample[sample.find("</main>")+len("</main>") :]  # <footer>...</html>

# ---- head со свапом мета/canonical/og/JSON-LD ----
h = head
h = re.sub(r"<title>.*?</title>", "<title>%s — ПодборVPS</title>" % html.escape(d["title"]), h, flags=re.S)
h = re.sub(r'<meta name="description" content=".*?">', '<meta name="description" content="%s">' % html.escape(d["description"]), h, flags=re.S)
h = re.sub(r'<link rel="canonical" href=".*?">', '<link rel="canonical" href="%s">' % url, h, flags=re.S)
h = re.sub(r'<meta property="og:title" content=".*?">', '<meta property="og:title" content="%s">' % html.escape(d["title"]), h, flags=re.S)
h = re.sub(r'<meta property="og:description" content=".*?">', '<meta property="og:description" content="%s">' % html.escape(d["description"]), h, flags=re.S)
h = re.sub(r'<meta property="og:url" content=".*?">', '<meta property="og:url" content="%s">' % url, h, flags=re.S)
h = re.sub(r'<meta property="og:type" content=".*?">', '<meta property="og:type" content="article">', h, flags=re.S)
if 'article:published_time' in h:
    h = re.sub(r'<meta property="article:published_time" content=".*?">', '<meta property="article:published_time" content="%s">' % d["iso"], h, flags=re.S)
else:
    h = h.replace('</head>' if '</head>' in h else h[-1:], '', 0)  # no-op safety
graph = {"@context":"https://schema.org","@graph":[
  {"@type":"NewsArticle","headline":d["title"],"description":d["description"],
   "datePublished":d["iso"],"dateModified":d["iso"],"inLanguage":"ru-RU",
   "mainEntityOfPage":url,"url":url,
   "image":"https://podborvps.ru/og-image.png",
   "author":{"@type":"Organization","name":"Редакция ПодборVPS","url":"https://podborvps.ru/redakciya/"},
   "publisher":{"@type":"Organization","name":"ПодборVPS","url":"https://podborvps.ru/",
     "logo":{"@type":"ImageObject","url":"https://podborvps.ru/icon-512.png","width":512,"height":512}}},
  {"@type":"BreadcrumbList","itemListElement":[
     {"@type":"ListItem","position":1,"name":"Главная","item":"https://podborvps.ru/"},
     {"@type":"ListItem","position":2,"name":"Новости","item":"https://podborvps.ru/news/"},
     {"@type":"ListItem","position":3,"name":d["title"],"item":url}]}
]}
ld = json.dumps(graph, ensure_ascii=False)
h = re.sub(r'<script type="application/ld\+json">.*?</script>', '<script type="application/ld+json">%s</script>' % ld, h, flags=re.S, count=1)

# ---- тело статьи ----
body = '<article><div class="kicker"><span class="tag">%s</span><span class="date">%s</span></div>' % (html.escape(d["tag"]), html.escape(d["date"]))
body += '<h1>%s</h1><p class="lead">%s</p>' % (html.escape(d["title"]), html.escape(d["lead"]))
for sec in d["sections"]:
    body += '<h2>%s</h2>' % html.escape(sec["h2"])
    for para in sec.get("paras", []):
        body += '<p>%s</p>' % para   # допускаем инлайн-разметку (<a>, <b>) в абзацах черновика
# источник (E-E-A-T)
if d.get("source", {}).get("url"):
    src = d["source"]
    body += ('<p style="font-size:14px;color:#8290A8;margin-top:22px">Источник: '
             '<a href="%s" target="_blank" rel="noopener" style="color:#0F58EC;font-weight:600">%s</a></p>'
             % (html.escape(src["url"]), html.escape(src.get("name","первоисточник"))))
# CTA провайдера (если новость про конкретного провайдера)
if d.get("provider", {}).get("url"):
    pr = d["provider"]; utm = pr.get("utm", "news_"+d["id"])
    link = pr["url"] + ("&" if "?" in pr["url"] else "?") + "utm_source=podborvps&utm_medium=referral&utm_campaign=%s&utm_content=%s" % (utm, pr["id"])
    body += ('<div class="cta"><h2>%s</h2><div class="ctabtns">'
             '<a class="btn" href="%s" target="_blank" rel="sponsored nofollow noopener" '
             'onclick="try{ym(%s,\'reachGoal\',\'provider_click\',{provider:\'%s\',place:\'news\'});ym(%s,\'reachGoal\',\'go_%s\')}catch(e){}">'
             'Перейти на сайт провайдера <span>→</span></a></div>'
             '<p class="ctanote">Переход по кнопке партнёрский: сервис может получить вознаграждение, для вас цена не меняется.</p></div>'
             % (html.escape(pr["name"]), html.escape(link), COUNTER, pr["id"], COUNTER, pr["id"]))
# CTA калькулятора
body += ('<div class="card alt"><h2>Не уверены, какой сервер нужен</h2>'
         '<p style="margin:0 0 18px">Пять параметров в калькуляторе — и провайдеры отсортированы под вашу задачу: ресурсы, география, бюджет.</p>'
         '<a class="btn ghost" href="/#calc">Открыть калькулятор →</a></div></article>')

crumbs = '<div class="crumbs"><a href="/">Главная</a> → <a href="/news/">Новости</a> → %s</div>' % html.escape(d["title"])
out = h + '</head>\n<body>' + header + '<main class="wrap">' + crumbs + body + '</main>\n' + footer
os.makedirs(os.path.join(PUB, "news", slug), exist_ok=True)
open(os.path.join(PUB, "news", slug, "index.html"), "w", encoding="utf-8").write(out)

# ---- добавить в news.json (feed, сверху) ----
item = {"slug":slug,"id":d["id"],"tag":d["tag"],"date":d["date"],"iso":d["iso"],"title":d["title"],"teaser":d["teaser"]}
news.setdefault("feed", [])
news["feed"] = [x for x in news["feed"] if x.get("slug") != slug]  # без дублей
news["feed"].insert(0, item)
json.dump(news, open(os.path.join(ROOT, "newsgen", "news.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)

print("Статья создана: public/news/%s/index.html" % slug)
print("Добавлено в news.json (feed).")
print("Теперь: python3 newsgen/build_site.py .   — обновит каталог /news/, sitemap и блок новостей на главной.")
