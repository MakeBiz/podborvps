# -*- coding: utf-8 -*-
"""
Генератор новостной части ПодборVPS. Один источник правды — newsgen/news.json.
Обновляет: public/index.html (блок var NEWS), public/news.html (каталог), public/sitemap.xml.

Правила:
- pinned: закреплённые новости, ВСЕГДА сверху и на главной, и в каталоге.
- feed: обычная лента, показывается ниже закреплённых, новее — выше.
- Главная показывает закреплённые + до HOME_FEED свежих из ленты и ссылку «Все новости».
- Каталог /news показывает все новости: закреплённые сверху, затем вся лента.

Запуск:  python3 newsgen/build_site.py [КОРЕНЬ_РЕПО]   (по умолчанию текущая папка)
"""
import os, sys, re, json, html

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
PUB = os.path.join(ROOT, "public")
HOME_FEED = 3  # сколько свежих новостей из ленты показывать на главной под закреплёнными

def esc(t):
    return html.escape(t, quote=True)

def jsstr(s):
    return s.replace("\\", "\\\\").replace("'", "\\'")

data = json.load(open(os.path.join(ROOT, "newsgen", "news.json"), encoding="utf-8"))
pinned = data["pinned"]
feed = sorted(data["feed"], key=lambda x: x["iso"], reverse=True)  # новее выше

home_items = pinned + feed[:HOME_FEED]
catalog_items = pinned + feed
all_items = pinned + feed

# ---------- 1. блок var NEWS на главной ----------
def news_row(n):
    return "{id:'%s',date:'%s',tag:'%s',title:'%s',text:'%s',url:'/news/%s/'}" % (
        jsstr(n["id"]), jsstr(n["date"]), jsstr(n["tag"]),
        jsstr(n["title"]), jsstr(n["teaser"]), jsstr(n["slug"]))

block = "var NEWS = [\n" + ",\n".join(news_row(n) for n in home_items) + "\n];"
idx_path = os.path.join(PUB, "index.html")
idx = open(idx_path, encoding="utf-8").read()
idx, cnt = re.subn(r"var NEWS = \[.*?\];", block, idx, count=1, flags=re.S)
assert cnt == 1, "блок var NEWS на главной не найден"
open(idx_path, "w", encoding="utf-8").write(idx)

# ---------- 2. каталог public/news.html ----------
CARD = """<a href="/news/{slug}/" target="_blank" rel="noopener" onclick="try{{ym(111248718,'reachGoal','news_click',{{news:'{id}'}})}}catch(e){{}}" style="display:flex;flex-direction:column;padding:24px;border-radius:24px;color:inherit;text-decoration:none;background:linear-gradient(180deg,#FFFFFF,#FBFCFE);border:1px solid #E4EAF2;box-shadow:inset 0 1px 0 #fff,0 18px 36px -22px rgba(3,35,95,.4);transition:.2s;cursor:pointer"><div style="display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:14px"><span style="font-size:11.5px;font-weight:700;letter-spacing:.3px;color:#fff;padding:5px 11px;border-radius:9px;background:linear-gradient(180deg,#3D85FF,#0A47CC);box-shadow:inset 0 1px 0 rgba(255,255,255,.4),0 5px 12px -4px rgba(7,78,232,.55)">{tag}</span><span style="font-size:12px;color:#8290A8">{date}</span></div><h3 style="font-family:'Onest',sans-serif;font-size:17px;font-weight:700;letter-spacing:-.3px;line-height:1.3;margin:0 0 9px;text-wrap:pretty">{title}</h3><p style="font-size:14px;color:#5E6F8E;margin:0;flex-grow:1;text-wrap:pretty">{teaser}</p><div style="display:inline-flex;align-items:center;gap:7px;font-family:'Onest',sans-serif;font-size:13.5px;font-weight:700;color:#013CA4;margin-top:16px">Читать <span style="display:inline-flex;align-items:center;justify-content:center;width:20px;height:20px;border-radius:7px;background:#E9F0FD;border:1px solid #D8E3F6;font-size:11px">→</span></div></a>"""

def cards_html(items):
    return "\n".join(CARD.format(slug=n["slug"], id=esc(n["id"]), tag=esc(n["tag"]),
                                 date=esc(n["date"]), title=esc(n["title"]),
                                 teaser=esc(n["teaser"])) for n in items)

# шасси (шапка/стиль/подвал) берём из готовой страницы статьи, чтобы оформление совпадало 1:1
sample_path = os.path.join(PUB, "news", pinned[0]["slug"], "index.html")
sample = open(sample_path, encoding="utf-8").read()
m_open = sample.find("<main")
m_close = sample.find("</main>") + len("</main>")
head_hdr = sample[:m_open]
head_hdr = head_hdr.replace(', ecommerce:"dataLayer"', '')  # чистим рудимент ecommerce
tail = sample[m_close:]

# правим шапку <head> под каталог
CAT_TITLE = "Новости и обзоры о VPS и хостинге"
CAT_DESC = "Новости рынка VPS, хостинга и дата-центров: цены, локации, регулирование и что это значит для выбора сервера. Разборы редакции ПодборVPS со ссылкой на первоисточник."
head_hdr = re.sub(r"<title>.*?</title>", "<title>%s — ПодборVPS</title>" % esc(CAT_TITLE), head_hdr, flags=re.S)
head_hdr = re.sub(r'<meta name="description" content=".*?">', '<meta name="description" content="%s">' % esc(CAT_DESC), head_hdr, flags=re.S)
head_hdr = re.sub(r'<link rel="canonical" href=".*?">', '<link rel="canonical" href="https://podborvps.ru/news/">', head_hdr, flags=re.S)
head_hdr = re.sub(r'<meta property="og:title" content=".*?">', '<meta property="og:title" content="%s">' % esc(CAT_TITLE), head_hdr, flags=re.S)
head_hdr = re.sub(r'<meta property="og:description" content=".*?">', '<meta property="og:description" content="%s">' % esc(CAT_DESC), head_hdr, flags=re.S)
head_hdr = re.sub(r'<meta property="og:url" content=".*?">', '<meta property="og:url" content="https://podborvps.ru/news/">', head_hdr, flags=re.S)
head_hdr = re.sub(r'<meta property="og:type" content=".*?">', '<meta property="og:type" content="website">', head_hdr, flags=re.S)
head_hdr = re.sub(r'\s*<meta property="article:published_time" content=".*?">', '', head_hdr, flags=re.S)

ld = json.dumps({
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    "name": CAT_TITLE,
    "description": CAT_DESC,
    "url": "https://podborvps.ru/news/",
    "inLanguage": "ru-RU",
    "isPartOf": {"@type": "WebSite", "name": "ПодборVPS", "url": "https://podborvps.ru/"},
    "hasPart": [{"@type": "NewsArticle", "headline": n["title"],
                 "url": "https://podborvps.ru/news/" + n["slug"] + "/",
                 "datePublished": n["iso"]} for n in all_items],
}, ensure_ascii=False)
head_hdr = re.sub(r'<script type="application/ld\+json">.*?</script>',
                  '<script type="application/ld+json">%s</script>' % ld, head_hdr, flags=re.S)

pinned_cards = cards_html(pinned)
feed_cards = cards_html(feed)
grid = 'style="display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:20px"'
main = (
    '<main class="wrap" style="max-width:1180px">\n'
    '<div class="crumbs"><a href="/">Главная</a> → Новости</div>\n'
    '<article style="padding:14px 0 10px">\n'
    '<div class="kicker"><span class="tag">Редакция</span></div>\n'
    '<h1>Новости и обзоры</h1>\n'
    '<p class="lead">Пишем только о том, что можем проверить по первоисточнику, и разбираем, что это значит для выбора сервера. Свежие материалы добавляются ниже закреплённых.</p>\n'
    '<h2 style="margin-top:30px">Главное</h2>\n'
    '<div ' + grid + '>\n' + pinned_cards + '\n</div>\n'
    + ('<h2 style="margin-top:38px">Лента</h2>\n<div ' + grid + '>\n' + feed_cards + '\n</div>\n' if feed else '')
    + '<div class="card alt" style="margin-top:34px">\n'
    '<h2>Подобрать сервер под задачу</h2>\n'
    '<p style="margin:0 0 18px">Пять параметров в калькуляторе — и провайдеры отсортированы под вашу задачу: ресурсы, география, бюджет.</p>\n'
    '<a class="btn ghost" href="/#calc">Открыть калькулятор →</a>\n'
    '</div>\n'
    '</article>\n'
    '</main>'
)

open(os.path.join(PUB, "news", "index.html"), "w", encoding="utf-8").write(head_hdr + main + tail)

# ---------- 3. sitemap ----------
rows = [("https://podborvps.ru/", "1.0"), ("https://podborvps.ru/news/", "0.9")]
DATES = {"https://podborvps.ru/": "2026-08-03", "https://podborvps.ru/news/": max(n["iso"] for n in all_items)}
xml = ['<?xml version="1.0" encoding="UTF-8"?>',
       '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
def row(loc, lm, pr):
    return '  <url><loc>%s</loc><lastmod>%s</lastmod><priority>%s</priority></url>' % (loc, lm, pr)
xml.append(row("https://podborvps.ru/", "2026-08-06", "1.0"))
xml.append(row("https://podborvps.ru/news/", max(n["iso"] for n in all_items), "0.9"))
xml.append(row("https://podborvps.ru/akcii-promokody-vps/", "2026-08-06", "0.8"))
xml.append(row("https://podborvps.ru/privacy/", "2026-08-06", "0.3"))
xml.append(row("https://podborvps.ru/cookie/", "2026-08-06", "0.3"))
xml.append(row("https://podborvps.ru/o-proekte/", "2026-08-24", "0.5"))
xml.append(row("https://podborvps.ru/metodologiya/", "2026-08-24", "0.5"))
xml.append(row("https://podborvps.ru/redakciya/", "2026-08-24", "0.4"))
for n in all_items:  # закреплённые + лента (новее выше внутри ленты уже отсортировано)
    xml.append(row("https://podborvps.ru/news/" + n["slug"] + "/", n["iso"], "0.8"))
xml.append("</urlset>")
open(os.path.join(PUB, "sitemap.xml"), "w", encoding="utf-8").write("\n".join(xml) + "\n")

print("Главная: закреплённых %d + лента %d (показано на главной %d)" % (len(pinned), len(feed), len(home_items)))
print("Каталог /news: всего %d карточек" % len(catalog_items))
print("Sitemap: %d URL" % (2 + len(all_items)))
