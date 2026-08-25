# -*- coding: utf-8 -*-
"""
SSR-заглушка для главной ПодборVPS.

Главная рендерится из <template> в #root на клиенте, поэтому в сыром HTML
контента нет — краулеры без JS (в первую очередь Яндекс) видят пустую страницу.
Этот скрипт кладёт в #root СТАТИЧНЫЙ SEO-блок (H1, лид, список провайдеров,
как выбрать, FAQ, ссылки на подборки/страницы). Приложение при загрузке делает
root.innerHTML='' и рендерит интерактив поверх — пользователь блок не видит,
краулер без JS видит полноценный контент. Идемпотентно (маркеры SSR).

Запуск: python3 ssrgen/ssr_home.py [КОРЕНЬ]
"""
import os, re, sys, json, html, glob

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
PUB = os.path.join(ROOT, "public")
IDX = os.path.join(PUB, "index.html")

def rd(p):
    with open(p, encoding="utf-8") as f: return f.read()

s = rd(IDX)

# ---- 1. провайдеры из массива PROVIDERS ----
m = re.search(r'var PROVIDERS\s*=\s*\[(.*?)\n\]', s, re.S)
prov_src = m.group(1) if m else ""
def field(obj, key):
    mm = re.search(key + r":'((?:[^'\\]|\\.)*)'", obj)
    return mm.group(1).replace("\\'", "'") if mm else ""
providers = []
for line in prov_src.split("\n"):
    line = line.strip()
    if not line.startswith("{id:'"): continue
    providers.append(dict(
        id=field(line, "id"), name=field(line, "name"),
        geoLabel=field(line, "geoLabel"), desc=field(line, "desc"),
        price=field(line, "price"), url=field(line, "url"),
    ))

# ---- 2. FAQ из JSON-LD ----
faq = []
for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
    try: d = json.loads(b)
    except Exception: continue
    if isinstance(d, dict) and d.get("@type") == "FAQPage":
        for q in d.get("mainEntity", []):
            faq.append((q.get("name", ""), q.get("acceptedAnswer", {}).get("text", "")))

# ---- 3. подборки: slug + <h1> из сгенерированных страниц ----
entities = []
idxp = os.path.join(ROOT, "entitygen", "entities_index.json")
if os.path.exists(idxp):
    for e in json.load(open(idxp, encoding="utf-8")):
        p = os.path.join(PUB, e["slug"], "index.html")
        if os.path.exists(p):
            h = re.search(r"<h1[^>]*>(.*?)</h1>", rd(p), re.S)
            title = re.sub(r"<[^>]+>", "", h.group(1)).strip() if h else e["slug"]
            entities.append((e["slug"], title, e.get("kind", "")))

# ---- сборка блока ----
esc = html.escape
def prov_li(p):
    parts = [f'<strong>{esc(p["name"])}</strong>']
    if p["geoLabel"]: parts.append(esc(p["geoLabel"]))
    if p["price"]: parts.append(esc(p["price"]))
    head = " — ".join(parts)
    link = f' <a href="{esc(p["url"])}" rel="nofollow sponsored noopener" target="_blank">Перейти</a>' if p["url"] else ""
    return f'<li>{head}. {esc(p["desc"])}{link}</li>'

geo = [e for e in entities if e[2] == "geo"]
uc  = [e for e in entities if e[2] == "uc"]
def ent_links(items):
    return " · ".join(f'<a href="/{esc(sl)}/">{esc(t)}</a>' for sl, t, _ in items)

parts = []
parts.append('<div style="max-width:820px;margin:0 auto;padding:24px 18px;font-family:sans-serif;line-height:1.6;color:#0F1B33">')
parts.append('<h1>Подберём VPS под вашу задачу</h1>')
parts.append('<p>ПодборVPS — независимый калькулятор и справочный каталог VPS. Укажите задачу, нужные ресурсы, географию и бюджет — и получите отсортированный под вашу задачу список виртуальных серверов российских и зарубежных провайдеров. Партнёрские ссылки не влияют на порядок подбора.</p>')
parts.append('<p><a href="/#calc">Открыть калькулятор подбора VPS</a></p>')

parts.append('<h2>Как это работает</h2>')
parts.append('<p>Пять параметров — задача (сайт, интернет-магазин, 1С и Битрикс, Telegram-бот, база данных, AI и ML, игровой сервер, разработка, выделенный сервер), объём оперативной памяти, число ядер CPU, география дата-центра и способ оплаты. По ним калькулятор ранжирует провайдеров по соответствию.</p>')

parts.append('<h2>Провайдеры VPS в каталоге</h2>')
parts.append("<ul>" + "".join(prov_li(p) for p in providers) + "</ul>")

if geo:
    parts.append('<h2>Подборки по географии</h2>')
    parts.append("<p>" + ent_links(geo) + "</p>")
if uc:
    parts.append('<h2>Подборки по задачам</h2>')
    parts.append("<p>" + ent_links(uc) + "</p>")

parts.append('<h2>О проекте</h2>')
parts.append('<p><a href="/o-proekte/">О проекте</a> · <a href="/metodologiya/">Методология подбора</a> · <a href="/redakciya/">Редакция</a> · <a href="/news/">Новости рынка VPS</a> · <a href="/akcii-promokody-vps/">Акции и промокоды</a></p>')

if faq:
    parts.append('<h2>Частые вопросы</h2>')
    for q, a in faq:
        parts.append(f'<h3>{esc(q)}</h3><p>{esc(a)}</p>')

parts.append('</div>')
block = "<!--SSR-->" + "".join(parts) + "<!--/SSR-->"

# ---- инъекция в #root (идемпотентно) ----
if "<!--SSR-->" in s:
    new = re.sub(r'<!--SSR-->.*?<!--/SSR-->', block, s, flags=re.S)
else:
    new = re.sub(r'(<div id="root">)(\s*)(</div>)', r'\1' + block + r'\3', s, count=1)

with open(IDX, "w", encoding="utf-8") as f:
    f.write(new)

print(f"SSR-блок в #root: провайдеров {len(providers)}, FAQ {len(faq)}, подборок {len(entities)} (гео {len(geo)}, задач {len(uc)})")
print("размер блока:", len(block), "байт")
