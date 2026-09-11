# -*- coding: utf-8 -*-
"""Сборка статического сайта из data/*.json. Запуск: python3 build.py"""
import json, os, shutil, sys, datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "build"))
import comp
from comp import (e, money, img, gallery, in_stock, discount, fmt_size, icon,
                  head, page, header, footer, breadcrumbs, product_grid, product_card,
                  trust_block, size_chart, empty_state, title_of, product_url,
                  CATEGORIES, GENDERS, COLORS, COLOR_HEX, plural,
                  org_schema, website_schema, breadcrumb_schema, product_schema)

ROOT = os.path.dirname(os.path.abspath(__file__))
D = lambda n: json.load(open(os.path.join(ROOT, "data", n), encoding="utf-8"))

CFG = D("config.json")
BRANDS = {b["slug"]: b for b in D("brands.json")}
BRAND_LIST = D("brands.json")
PRODUCTS = D("products.json")
CONTENT = D("content.json")

WRITTEN = []


def mk(path, html):
    """path: '' → index.html, 'about/' → about/index.html, '404.html' → как есть."""
    if path.endswith(".html") or path.endswith(".xml") or path.endswith(".txt"):
        full = os.path.join(ROOT, path)
    else:
        full = os.path.join(ROOT, path, "index.html")
    os.makedirs(os.path.dirname(full), exist_ok=True)
    open(full, "w", encoding="utf-8").write(html)
    WRITTEN.append(path or "/")


def urlfor(depth):
    prefix = "../" * depth
    return (lambda p="": (prefix + p) if p else (prefix or "./")), prefix


# ─────────────────────────────────────────────────── фильтры и сортировка

SORTS = [("popular", "Популярное"), ("price-asc", "Цена по возрастанию"),
         ("price-desc", "Цена по убыванию"), ("new", "Новинки"), ("discount", "Максимальная скидка")]


def filters_panel(items, u):
    def opts(key, title, pairs, kind="check"):
        if len(pairs) < 2:
            return ""
        rows = ""
        for val, label, count in pairs:
            if kind == "color":
                bg = COLOR_HEX.get(val, "#555")
                style = ("background:%s" % bg) if bg.startswith("linear") is False else ("background-image:%s" % bg)
                rows += (f'<label class="fopt fopt--color"><input type="checkbox" data-f="{key}" value="{e(val)}">'
                         f'<span class="swatch" style="{style}"></span><span class="fopt__t">{e(label)}</span>'
                         f'<span class="fopt__n">{count}</span></label>')
            else:
                rows += (f'<label class="fopt"><input type="checkbox" data-f="{key}" value="{e(val)}">'
                         f'<span class="fopt__box">{icon("check", 12)}</span>'
                         f'<span class="fopt__t">{e(label)}</span><span class="fopt__n">{count}</span></label>')
        return (f'<details class="fgroup" open><summary>{e(title)}{icon("chev", 15)}</summary>'
                f'<div class="fgroup__body">{rows}</div></details>')

    def tally(fn):
        d = {}
        for p in items:
            for v in fn(p):
                d[v] = d.get(v, 0) + 1
        return d

    br = tally(lambda p: [p["brand"]])
    brand_opts = sorted(((s, BRANDS[s]["name"], n) for s, n in br.items()), key=lambda x: -x[2])
    gn = tally(lambda p: [p["gender"]])
    gender_opts = [(k, GENDERS[k], gn[k]) for k in ("men", "women", "unisex") if k in gn]
    ct = tally(lambda p: [p["category"]])
    cat_opts = [(k, CATEGORIES[k]["title"], ct[k]) for k in CATEGORIES if k in ct]
    cl = tally(lambda p: [p["color"]])
    color_opts = sorted(((k, COLORS.get(k, k), n) for k, n in cl.items()), key=lambda x: -x[2])
    pu = tally(lambda p: [p["purpose"]])
    purpose_opts = sorted(((k, k, n) for k, n in pu.items()), key=lambda x: -x[2])

    all_sizes = sorted({s["size"] for p in items for s in p["sizes"] if s["stock"] > 0})
    size_rows = "".join(
        f'<label class="fsize"><input type="checkbox" data-f="size" value="{fmt_size(s)}">'
        f'<span>{fmt_size(s)}</span></label>' for s in all_sizes)
    sizes_html = (f'<details class="fgroup" open><summary>Размер{icon("chev", 15)}</summary>'
                  f'<div class="fgroup__body fgroup__body--sizes">{size_rows}</div></details>') if all_sizes else ""

    prices = [p["price"] for p in items] or [0]
    lo, hi = min(prices), max(prices)
    price_html = (f'<details class="fgroup" open><summary>Цена{icon("chev", 15)}</summary>'
                  f'<div class="fgroup__body"><div class="fprice">'
                  f'<label><span>от</span><input type="number" id="price-min" inputmode="numeric" '
                  f'value="{lo}" min="{lo}" max="{hi}" step="100" aria-label="Цена от"></label>'
                  f'<label><span>до</span><input type="number" id="price-max" inputmode="numeric" '
                  f'value="{hi}" min="{lo}" max="{hi}" step="100" aria-label="Цена до"></label>'
                  f'</div></div></details>') if hi > lo else ""

    stock_html = (f'<div class="fgroup fgroup--flat"><label class="fopt">'
                  f'<input type="checkbox" data-f="instock" value="1">'
                  f'<span class="fopt__box">{icon("check", 12)}</span>'
                  f'<span class="fopt__t">Только в наличии</span></label></div>')

    return f"""<aside class="filters" id="filters" aria-label="Фильтры">
  <div class="filters__head">
    <span class="filters__title">Фильтры</span>
    <button class="filters__reset" type="button" id="reset-filters">Сбросить</button>
    <button class="hdr-btn filters__close" type="button" data-close-filters aria-label="Закрыть фильтры">{icon('close')}</button>
  </div>
  <div class="filters__body">
    {stock_html}
    {opts('brand', 'Бренд', brand_opts)}
    {sizes_html}
    {opts('gender', 'Пол', gender_opts)}
    {opts('cat', 'Категория', cat_opts)}
    {opts('color', 'Цвет', color_opts, 'color')}
    {price_html}
    {opts('purpose', 'Назначение', purpose_opts)}
  </div>
  <div class="filters__apply"><button class="btn btn--grad btn--wide" type="button" data-close-filters>Показать результаты</button></div>
</aside>"""


def toolbar(total, u):
    o = "".join('<option value="%s">%s</option>' % (v, e(t)) for v, t in SORTS)
    return f"""<div class="toolbar">
  <button class="btn btn--ghost toolbar__filters" type="button" data-open-filters>Фильтры</button>
  <span class="toolbar__count">Найдено: <b id="results-count">{total}</b></span>
  <label class="toolbar__sort"><span>Сортировка</span>
    <select id="sort-select" aria-label="Сортировка">{o}</select>
  </label>
</div>"""


# ─────────────────────────────────────────────────── каталог

CATALOG_PAGES = [
    ("catalog/",           "Каталог",   "Все кроссовки",              lambda p: True,
     "Кроссовки Nike, New Balance, Puma и Vans для бега, тренировок и города."),
    ("catalog/mens/",      "Мужское",   "Мужские кроссовки",          lambda p: p["gender"] in ("men", "unisex"),
     "Мужские кроссовки для бега, зала и повседневной носки."),
    ("catalog/womens/",    "Женское",   "Женские кроссовки",          lambda p: p["gender"] in ("women", "unisex"),
     "Женские кроссовки для бега, тренировок и города."),
    ("catalog/running/",   "Бег",       "Беговые кроссовки",          lambda p: p["category"] == "running",
     "Беговые кроссовки для асфальта и стадиона."),
    ("catalog/lifestyle/", "Lifestyle", "Lifestyle-кроссовки",        lambda p: p["category"] == "lifestyle",
     "Lifestyle-кроссовки для повседневной носки."),
    ("catalog/training/",  "Training",  "Кроссовки для тренировок",   lambda p: p["category"] == "training",
     "Кроссовки для зала и функционального тренинга."),
    ("catalog/new/",       "Новинки",   "Новинки",                    lambda p: p.get("isNew"),
     "Новые поступления в каталоге."),
    ("catalog/sale/",      "Sale",      "Sale",                       lambda p: bool(p.get("oldPrice")),
     "Кроссовки со сниженной ценой."),
]


def build_catalog():
    for path, nav, h1, pred, desc in CATALOG_PAGES:
        depth = path.count("/")
        u, prefix = urlfor(depth)
        items = [p for p in PRODUCTS if pred(p)]
        crumbs = [("Главная", "")]
        if path != "catalog/":
            crumbs.append(("Каталог", "catalog/"))
        crumbs.append((nav, path))
        h = head(CFG, u, title="%s — купить в интернет-магазине %s" % (h1, CFG["siteName"]),
                 desc=desc, path=path,
                 og_image=img(items[0]["image"], 1200, 630) if items else None,
                 schema=[breadcrumb_schema(CFG, crumbs), org_schema(CFG, u)])
        body = f"""<section class="pagehead">
  <div class="wrap">{breadcrumbs(crumbs, u)}
    <h1 class="ttl">{e(h1)}</h1>
    <p class="lede">{e(desc)}</p>
  </div>
</section>
<section class="wrap catalog">
  {toolbar(len(items), u)}
  <div class="catalog__grid">
    {filters_panel(items, u)}
    <div class="catalog__main">
      {product_grid(items, BRANDS, u, eager_first=4)}
      {empty_state('Ничего не найдено', 'Попробуйте изменить или сбросить фильтры.', u)}
    </div>
  </div>
</section>"""
        mk(path, page(CFG, u, head_html=h, body=body, active=path,
                      body_class="page-catalog", base_prefix=prefix))


# ─────────────────────────────────────────────────── карточка товара

def build_products():
    for p in PRODUCTS:
        path = "product/%s/" % p["id"]
        u, prefix = urlfor(2)
        b = BRANDS[p["brand"]]
        name = title_of(p, BRANDS)
        stock = in_stock(p)
        imgs = gallery(p, 1100)
        thumbs = "".join(
            f'<button class="pdp-thumb" type="button" data-i="{i}" aria-label="Изображение {i+1}"'
            f'{" aria-pressed=\"true\"" if i == 0 else " aria-pressed=\"false\""}>'
            f'<img src="{img(p["image"], 160, 160, i)}" alt="" width="160" height="160" loading="lazy"></button>'
            for i in range(len(imgs)))
        slides = "".join(
            f'<div class="pdp-slide"><img src="{src}" alt="{e(name)} — изображение {i+1}"'
            f' width="1100" height="1100" loading="{"eager" if i == 0 else "lazy"}" data-i="{i}"></div>'
            for i, src in enumerate(imgs))
        sizes = "".join(
            f'<button class="size" type="button" data-size="{fmt_size(s["size"])}" aria-pressed="false"'
            f'{"" if s["stock"] else " disabled"} '
            f'aria-label="Размер {fmt_size(s["size"])}{"" if s["stock"] else " — нет в наличии"}">'
            f'{fmt_size(s["size"])}</button>' for s in p["sizes"])
        price = (f'<span class="pdp-price">{money(p["price"])}</span>'
                 f'<span class="pdp-old">{money(p["oldPrice"])}</span>'
                 f'<span class="pdp-disc">−{discount(p)}%</span>') if p.get("oldPrice") \
            else f'<span class="pdp-price">{money(p["price"])}</span>'

        spec = [("Артикул", p["sku"]), ("Бренд", b["name"]), ("Модель", p["model"]),
                ("Цвет", p["colorName"]), ("Пол", GENDERS[p["gender"]]),
                ("Категория", CATEGORIES[p["category"]]["title"]), ("Назначение", p["purpose"]),
                ("Материал верха", p["materials"]["upper"]),
                ("Материал подошвы", p["materials"]["sole"]), ("Страна производства", p["country"])]
        spec_rows = "".join("<div><dt>%s</dt><dd>%s</dd></div>" % (e(k), e(v)) for k, v in spec if v)

        rel = [x for x in PRODUCTS if x["id"] != p["id"] and
               (x["brand"] == p["brand"] or x["category"] == p["category"])][:4]

        crumbs = [("Главная", ""), ("Каталог", "catalog/"),
                  (CATEGORIES[p["category"]]["title"], "catalog/%s/" % p["category"]), (name, path)]
        h = head(CFG, u,
                 title="%s %s — %s, артикул %s" % (b["name"], p["model"], p["colorName"], p["sku"]),
                 desc="%s %s, %s. %s Размеры %s. Доставка по России, возврат 14 дней." % (
                     b["name"], p["model"], p["colorName"], p["description"][:90],
                     ", ".join(fmt_size(s["size"]) for s in p["sizes"] if s["stock"])[:60]),
                 path=path, og_image=img(p["image"], 1200, 630),
                 schema=[product_schema(CFG, p, BRANDS), breadcrumb_schema(CFG, crumbs)])

        stock_line = ('<span class="pdp-stock is-in">В наличии</span>' if stock
                      else '<span class="pdp-stock is-out">Нет в наличии</span>')

        body = f"""<section class="wrap pdp-top">{breadcrumbs(crumbs, u)}</section>
<section class="wrap pdp">
  <div class="pdp-media">
    <div class="pdp-frame">
      <div class="pdp-stage" id="pdp-stage">{slides}</div>
      <button class="pdp-zoom" type="button" id="pdp-zoom" aria-label="Открыть изображение крупнее">Увеличить</button>
    </div>
    <div class="pdp-thumbs" id="pdp-thumbs">{thumbs}</div>
  </div>
  <div class="pdp-info">
    <a class="pdp-brand" href="{u('brands/%s/' % b['slug'])}">{e(b['name'])}</a>
    <h1 class="pdp-name">{e(p['model'])}</h1>
    <p class="pdp-color">{e(p['colorName'])}</p>
    <p class="pdp-sku">Артикул: {e(p['sku'])}</p>
    <div class="pdp-prices">{price}</div>
    {stock_line}
    <div class="pdp-sizes">
      <div class="pdp-sizes__head">
        <span>Размер (EU)</span>
        <button class="linkish" type="button" id="open-sizechart">Размерная сетка</button>
      </div>
      <div class="sizes" role="group" aria-label="Выберите размер">{sizes}</div>
      <p class="hint" id="pdp-hint" role="status"></p>
    </div>
    <div class="pdp-buy">
      <button class="btn btn--grad btn--wide" type="button" id="pdp-add"
              data-product="{e(p['id'])}"{'' if stock else ' disabled'}>В корзину</button>
      <button class="btn btn--ghost pdp-wish" type="button" data-wish="{e(p['id'])}"
              aria-pressed="false" aria-label="В избранное">{icon('heart', 18)}<span>В избранное</span></button>
    </div>
    {trust_block()}
    <div class="acc" id="pdp-acc">
      <details class="acc__item" open><summary>Описание{icon('chev', 16)}</summary>
        <div class="acc__body"><p>{e(p['description'])}</p></div></details>
      <details class="acc__item"><summary>Характеристики{icon('chev', 16)}</summary>
        <div class="acc__body"><dl class="spec">{spec_rows}</dl></div></details>
      <details class="acc__item"><summary>Доставка{icon('chev', 16)}</summary>
        <div class="acc__body"><p>Курьером, в пункты выдачи и постаматы по всей России. Москва и Санкт-Петербург — 1–3 рабочих дня, другие регионы — 3–10 дней.</p>
        <p><a class="linkish" href="{u('delivery/')}">Условия доставки</a></p></div></details>
      <details class="acc__item"><summary>Возврат{icon('chev', 16)}</summary>
        <div class="acc__body"><p>14 дней на возврат при сохранении товарного вида, фабричных бирок и коробки. Обмен размера оформляем после получения возврата.</p>
        <p><a class="linkish" href="{u('returns/')}">Условия возврата</a></p></div></details>
    </div>
  </div>
</section>

<dialog class="lightbox" id="lightbox" aria-label="Просмотр изображения">
  <button class="lightbox__close" type="button" data-close-lightbox aria-label="Закрыть">{icon('close', 22)}</button>
  <img id="lightbox-img" src="" alt="">
</dialog>

<dialog class="modal" id="sizechart" aria-label="Размерная сетка">
  <button class="modal__close" type="button" data-close-modal aria-label="Закрыть">{icon('close', 22)}</button>
  {size_chart(p)}
</dialog>

<section class="wrap sect">
  <h2 class="sect__ttl">Похожие модели</h2>
  {product_grid(rel, BRANDS, u)}
</section>"""
        mk(path, page(CFG, u, head_html=h, body=body, active="",
                      body_class="page-product", base_prefix=prefix))


# ─────────────────────────────────────────────────── главная

def build_home():
    u, prefix = urlfor(0)
    c = CONTENT["home"]
    hero_imgs = [p for p in PRODUCTS if p["id"] in (
        "nike-air-jordan-1-mid-black-red", "nike-free-rn-flyknit-red",
        "nike-air-force-1-shadow-pastel", "new-balance-247-olive")]
    faces = ["face-front", "face-back", "face-top", "face-bottom"]
    cube = "".join(
        f'<div class="cube-face {faces[i]}"><img src="{img(p["image"], 700, 700)}" '
        f'alt="{e(title_of(p, BRANDS))}" width="700" height="700"'
        f'{" fetchpriority=\"high\"" if i == 0 else " loading=\"lazy\""}></div>'
        for i, p in enumerate(hero_imgs))

    newest = sorted([p for p in PRODUCTS if p.get("isNew")],
                    key=lambda p: p["releasedAt"], reverse=True)[:4]
    popular = [p for p in PRODUCTS if p["id"] in (
        "puma-court-classic-white", "nike-air-force-1-07-lv8-wheat",
        "new-balance-x90-pink-grey", "nike-free-rn-5-black-volt")]
    sale = sorted([p for p in PRODUCTS if p.get("oldPrice")], key=lambda p: -discount(p))[:3]

    def count_for(pred):
        return sum(1 for p in PRODUCTS if pred(p))

    # Баннер на всю ширину и две плитки под ним — ссылки на разделы каталога
    bento = [
        ("Мужское", "catalog/mens/", "photo-1514989940723-e8e51635b782",
         "Город, зал и бег", count_for(lambda p: p["gender"] in ("men", "unisex")), True),
        ("Женское", "catalog/womens/", "photo-1551107696-a4b0c5a0d9a2",
         "Силуэты на каждый день", count_for(lambda p: p["gender"] in ("women", "unisex")), False),
        ("Бег", "catalog/running/", "photo-1542291026-7eec264c27ff",
         "Асфальт и стадион", count_for(lambda p: p["category"] == "running"), False),
    ]
    tiles_html = "".join(
        f'<a class="tile{" tile--wide" if wide else ""}" href="{u(path)}">'
        f'<img src="{img(pid, 1400, 790) if wide else img(pid, 700, 530)}" alt=""'
        f' width="{1400 if wide else 700}" height="{790 if wide else 530}" loading="lazy">'
        f'<span class="tile__body">'
        f'<span class="tile__t">{e(t)}</span>'
        f'<span class="tile__s">{e(sub)}</span>'
        f'</span>'
        f'<span class="tile__go">{plural(n, "модель", "модели", "моделей")}{icon("chev", 16)}</span></a>'
        for t, path, pid, sub, n, wide in bento)


    lo = int(min(p["price"] for p in PRODUCTS) // 1000 * 1000)
    hi = int(-(-max(p["price"] for p in PRODUCTS) // 1000) * 1000)
    start = int((lo + hi) // 2 // 500 * 500)
    rhythms = [
        ("На каждый день", "catalog/lifestyle/", "Плоская подошва и спокойная форма",
         count_for(lambda p: p["category"] == "lifestyle")),
        ("Для зала", "catalog/training/", "Устойчивая пятка и гибкий мысок",
         count_for(lambda p: p["category"] == "training")),
        ("Для движения", "catalog/running/", "Высокий стек и возврат энергии",
         count_for(lambda p: p["category"] == "running")),
    ]
    rhythm_html = "".join(
        f'<a class="rhythm" href="{u(path)}">'
        f'<span class="rhythm__n">{plural(n, "модель", "модели", "моделей")}</span>'
        f'<span class="rhythm__t">{e(t)}</span>'
        f'<span class="rhythm__s">{e(s)}</span>'
        f'<span class="rhythm__go">Смотреть{icon("chev", 15)}</span></a>'
        for t, path, s, n in rhythms)

    adv = "".join(f'<li><h3>{e(a["title"])}</h3><p>{e(a["text"])}</p></li>' for a in c["advantages"])

    h = head(CFG, u,
             title="%s — мультибрендовый магазин кроссовок Nike, New Balance, Puma, Vans" % CFG["siteName"],
             desc="Кроссовки для бега, тренировок и города. Доставка по России, возврат 14 дней, проверка каждой пары перед отправкой.",
             path="", og_image=img(hero_imgs[0]["image"], 1200, 630),
             schema=[org_schema(CFG, u), website_schema(CFG)])

    body = f"""<section class="relative h-screen w-full flex items-center overflow-hidden pt-20">
  <div class="hero-mark" aria-hidden="true">
    <div class="container mx-auto px-6"><span>Твой<br>ход</span></div>
  </div>
  <div class="container mx-auto px-6 relative z-10 grid grid-cols-1 md:grid-cols-2 gap-12 items-center h-full">
    <div class="flex flex-col gap-6 order-2 md:order-1">
      <div class="uppercase text-sm font-bold tracking-[0.2em] text-[#999999]">{e(c['heroEyebrow'])}</div>
      <h1 class="hero-title font-heavy uppercase">{c['heroTitle']}</h1>
      <p class="text-lg font-light text-[#999999] max-w-md">{e(c['heroText'])}</p>
      <div class="pt-4 hero-cta">
        <a class="btn btn--grad" href="{u('catalog/')}">{e(c['heroCta'])}</a>
        <a class="btn btn--ghost" href="{u('catalog/new/')}">Новинки</a>
      </div>
    </div>
    <div class="order-1 md:order-2 h-[50vh] flex items-center justify-center">
      <div class="scene"><div class="cube">{cube}</div></div>
    </div>
  </div>
</section>

<div class="border-y border-white/10 py-4 bg-[#111111] overflow-hidden flex items-center" aria-hidden="true">
  <div class="marquee-container w-full"><div class="marquee-content text-2xl md:text-4xl font-heavy uppercase tracking-widest text-[#999999]">
    NIKE • NEW BALANCE • PUMA • VANS • NIKE • NEW BALANCE • PUMA • VANS • NIKE • NEW BALANCE • PUMA • VANS •
  </div></div>
</div>

<section class="wrap sect">
  <div class="sect__head"><h2 class="sect__ttl">Новинки</h2><a class="linkish" href="{u('catalog/new/')}">Все новинки</a></div>
  {product_grid(newest, BRANDS, u)}
</section>

<section class="wrap sect">
  <div class="sect__head"><h2 class="sect__ttl">Категории</h2></div>
  <div class="tiles">{tiles_html}</div>
</section>

<section class="wrap sect">
  <div class="sect__head"><h2 class="sect__ttl">Популярное</h2><a class="linkish" href="{u('catalog/')}">Весь каталог</a></div>
  {product_grid(popular, BRANDS, u)}
</section>

<section class="wrap sect">
  <div class="sect__head"><h2 class="sect__ttl">Sale</h2><a class="linkish" href="{u('catalog/sale/')}">Все скидки</a></div>
  {product_grid(sale, BRANDS, u)}
</section>

<section class="glow-section rhythms-sect">
  <div class="wrap">
    <div class="sect__head"><h2 class="sect__ttl">Три ритма</h2></div>
    <div class="rhythms">{rhythm_html}</div>

    <div class="budget">
      <h3 class="budget__ttl">Подбор по бюджету</h3>
      <div class="budget__read">
        <span class="budget__label">До</span>
        <span class="budget__val" id="budget-val">{money(start)}</span>
        <span class="budget__cnt">Подходит пар: <b id="budget-n">0</b></span>
      </div>
      <input class="budget__range" type="range" id="budget-range"
             min="{lo}" max="{hi}" step="500" value="{start}"
             aria-label="Максимальная цена в рублях">
      <div class="budget__scale"><span>{money(lo)}</span><span>{money(hi)}</span></div>
      <div class="budget__hits" id="budget-hits"></div>
      <a class="btn btn--white" id="budget-go" href="{u('catalog/')}">Показать варианты</a>
    </div>
  </div>
</section>

<section class="adv">
  <div class="wrap">
    <h2 class="sect__ttl">{e(c['advantagesTitle'])}</h2>
    <ul class="adv__list">{adv}</ul>
  </div>
</section>

<section class="wrap sect">
  <div class="news">
    <div class="news__copy">
      <h2 class="sect__ttl">{e(c['newsletterTitle'])}</h2>
      <p class="lede">{e(c['newsletterText'])}</p>
    </div>
    <form class="news__form" data-form="newsletter">
      <label class="sr-only" for="nl-email">Электронная почта</label>
      <input id="nl-email" type="email" name="email" required placeholder="Ваш e-mail" autocomplete="email">
      <button class="btn btn--grad" type="submit">Подписаться</button>
      <p class="news__note">{e(c['newsletterNote'])}</p>
      <p class="formmsg" role="status" hidden></p>
    </form>
  </div>
</section>"""
    mk("", page(CFG, u, head_html=h, body=body, active="", body_class="page-home", base_prefix=prefix))


# ─────────────────────────────────────────────────── бренды

def build_brands():
    u, prefix = urlfor(1)
    cards = ""
    for b in BRAND_LIST:
        items = [p for p in PRODUCTS if p["brand"] == b["slug"]]
        cards += f"""<a class="brandcard" href="{u('brands/%s/' % b['slug'])}">
      <span class="brandcard__name">{e(b['name'])}</span>
      <span class="brandcard__meta">{e(b['country'])} · с {b['founded']}</span>
      <p class="brandcard__sum">{e(b['summary'])}</p>
      <span class="brandcard__n">{plural(len(items), "модель", "модели", "моделей")}</span>
    </a>"""
    crumbs = [("Главная", ""), ("Бренды", "brands/")]
    h = head(CFG, u, title="Бренды — %s" % CFG["siteName"],
             desc="Бренды в каталоге: Nike, New Balance, Puma, Vans. Кроссовки для бега, тренировок и города.",
             path="brands/", schema=[breadcrumb_schema(CFG, crumbs), org_schema(CFG, u)])
    body = f"""<section class="pagehead"><div class="wrap">{breadcrumbs(crumbs, u)}
  <h1 class="ttl">Бренды</h1>
  <p class="lede">Мы независимый магазин и собираем ассортимент по качеству моделей. Портфель брендов расширяется —
  условия сотрудничества описаны на странице <a class="linkish" href="{u('brand-partnerships/')}">Brand Partnerships</a>.</p>
</div></section>
<section class="wrap sect"><div class="brandgrid">{cards}</div></section>"""
    mk("brands/", page(CFG, u, head_html=h, body=body, active="brands/",
                       body_class="page-brands", base_prefix=prefix))

    for b in BRAND_LIST:
        u2, prefix2 = urlfor(2)
        items = [p for p in PRODUCTS if p["brand"] == b["slug"]]
        path = "brands/%s/" % b["slug"]
        crumbs = [("Главная", ""), ("Бренды", "brands/"), (b["name"], path)]
        cats = sorted({p["category"] for p in items})
        chips = "".join(
            f'<a class="chip" href="{u2("catalog/%s/" % c)}">{e(CATEGORIES[c]["title"])}</a>' for c in cats)
        h2 = head(CFG, u2, title="%s — кроссовки в интернет-магазине %s" % (b["name"], CFG["siteName"]),
                  desc="%s Модели %s в наличии, доставка по России." % (b["summary"], b["name"]),
                  path=path, og_image=img(items[0]["image"], 1200, 630) if items else None,
                  schema=[breadcrumb_schema(CFG, crumbs)])
        body2 = f"""<section class="pagehead"><div class="wrap">{breadcrumbs(crumbs, u2)}
  <h1 class="ttl">{e(b['name'])}</h1>
  <p class="brandmeta">{e(b['country'])} · основан в {b['founded']}</p>
  <p class="lede">{e(b['description'])}</p>
  <div class="chips">{chips}</div>
</div></section>
<section class="wrap catalog">
  {toolbar(len(items), u2)}
  <div class="catalog__grid">
    {filters_panel(items, u2)}
    <div class="catalog__main">
      {product_grid(items, BRANDS, u2, eager_first=4)}
      {empty_state('Ничего не найдено', 'Попробуйте изменить или сбросить фильтры.', u2)}
    </div>
  </div>
</section>"""
        mk(path, page(CFG, u2, head_html=h2, body=body2, active="brands/",
                      body_class="page-catalog", base_prefix=prefix2))


# ─────────────────────────────────────────────────── контентные страницы

def info_page(path, nav, title, desc, h1, inner, *, lede="", active="", schema=None):
    depth = path.count("/")
    u, prefix = urlfor(depth)
    crumbs = [("Главная", ""), (nav, path)]
    h = head(CFG, u, title="%s — %s" % (title, CFG["siteName"]), desc=desc, path=path,
             schema=(schema or []) + [breadcrumb_schema(CFG, crumbs)])
    body = f"""<section class="pagehead"><div class="wrap">{breadcrumbs(crumbs, u)}
  <h1 class="ttl">{e(h1)}</h1>
  {'<p class="lede">%s</p>' % e(lede) if lede else ''}
</div></section>
{inner(u)}"""
    mk(path, page(CFG, u, head_html=h, body=body, active=active,
                  body_class="page-info", base_prefix=prefix))


def prose_sections(sections):
    return "".join('<section class="prose__sect"><h2>%s</h2><p>%s</p></section>'
                   % (e(s["title"]), e(s["body"])) for s in sections)


def build_about():
    c = CONTENT["about"]
    info_page("about/", "О нас", "О нас", c["lead"], c["title"],
              lambda u: f"""<section class="wrap sect"><div class="prose">{prose_sections(c['sections'])}
  <section class="prose__sect"><h2>Контакты</h2>{contacts_inline(u)}</section>
</div></section>
<section class="adv"><div class="wrap">{trust_block(False)}</div></section>""",
              lede=c["lead"], active="about/")


def contacts_inline(u, show_form_link=True):
    k, c = CFG["contacts"], CFG["company"]
    rows = []
    if k.get("phone"):
        rows.append(('Телефон', '<a href="tel:%s">%s</a>' % (e(k["phone"].replace(" ", "")), e(k["phone"]))))
    if k.get("email"):
        rows.append(('Электронная почта', '<a href="mailto:%s">%s</a>' % (e(k["email"]), e(k["email"]))))
    if k.get("wholesaleEmail"):
        rows.append(('Оптовые закупки', '<a href="mailto:%s">%s</a>'
                     % (e(k["wholesaleEmail"]), e(k["wholesaleEmail"]))))
    if k.get("telegram"):
        rows.append(('Telegram', '<a href="%s" rel="noopener">%s</a>' % (e(k["telegram"]), e(k["telegram"]))))
    if k.get("workHours"):
        rows.append(('Часы работы', e(k["workHours"])))
    if c.get("actualAddress"):
        rows.append(('Адрес', e(c["actualAddress"])))
    if not rows:
        return ('<p class="lede">Напишите нам через форму — ответим в течение рабочего дня.</p>'
                + (('<p><a class="btn btn--ghost" href="%s">Связаться</a></p>' % u("contacts/"))
                   if show_form_link else ""))
    return '<dl class="contacts">%s</dl>' % "".join(
        "<div><dt>%s</dt><dd>%s</dd></div>" % (k_, v) for k_, v in rows)


def contact_form(kind, title, note, fields):
    fi = ""
    for f in fields:
        fid = "%s-%s" % (kind, f["name"])
        if f.get("type") == "textarea":
            ctl = ('<textarea id="%s" name="%s" rows="4"%s></textarea>'
                   % (fid, f["name"], " required" if f.get("required") else ""))
        else:
            ctl = ('<input id="%s" name="%s" type="%s"%s%s>'
                   % (fid, f["name"], f.get("type", "text"),
                      ' required' if f.get("required") else '',
                      ' autocomplete="%s"' % f["autocomplete"] if f.get("autocomplete") else ''))
        fi += '<div class="field%s"><label for="%s">%s</label>%s</div>' % (
            " field--wide" if f.get("wide") else "", fid, e(f["label"]), ctl)
    return f"""<form class="cform" data-form="{e(kind)}">
  <h2 class="sect__ttl">{e(title)}</h2>
  <div class="cform__grid">{fi}</div>
  <button class="btn btn--grad" type="submit">Отправить</button>
  <p class="cform__note">{e(note)}</p>
  <p class="formmsg" role="status" hidden></p>
</form>"""


LEAD_FIELDS = [
    {"name": "name", "label": "Имя", "required": True, "autocomplete": "name"},
    {"name": "company", "label": "Компания"},
    {"name": "email", "label": "Электронная почта", "type": "email", "required": True, "autocomplete": "email"},
    {"name": "phone", "label": "Телефон", "type": "tel", "autocomplete": "tel"},
    {"name": "brands", "label": "Бренды / категории", "wide": True},
    {"name": "message", "label": "Сообщение", "type": "textarea", "wide": True, "required": True},
]


def build_partnerships():
    c = CONTENT["partnerships"]
    def inner(u):
        cats = "".join("<li>%s</li>" % e(x) for x in c["categories"])
        ch = "".join('<li><h3>%s</h3><p>%s</p></li>' % (e(x["title"]), e(x["text"])) for x in c["channels"])
        terms = "".join("<li>%s</li>" % e(x) for x in c["terms"])
        return f"""<section class="wrap sect">
  <div class="bp-lead">
    <p class="bp-lead__en">{e(c['lead'])}</p>
    <p class="bp-lead__ru">{e(c['leadRu'])}</p>
  </div>
</section>
<section class="wrap sect bp-cols">
  <div><h2 class="sect__ttl">{e(c['categoriesTitle'])}</h2><ul class="ticks">{cats}</ul></div>
  <div><h2 class="sect__ttl">{e(c['termsTitle'])}</h2><ul class="ticks">{terms}</ul></div>
</section>
<section class="adv"><div class="wrap">
  <h2 class="sect__ttl">{e(c['channelsTitle'])}</h2>
  <ul class="adv__list">{ch}</ul>
</div></section>
<section class="wrap sect bp-contact">
  <div>
    <h2 class="sect__ttl">{e(c['contactTitle'])}</h2>
    <p class="lede">{e(c['contactText'])}</p>
    {contacts_inline(u, show_form_link=False)}
  </div>
  {contact_form('wholesale', c['formTitle'], c['formNote'], LEAD_FIELDS)}
</section>"""
    info_page("brand-partnerships/", "Brand Partnerships", "Brand Partnerships",
              "Открыты к прямому оптовому сотрудничеству с производителями спортивной обуви и одежды, дистрибьюторами и региональными партнёрами.",
              c["title"], inner, lede="")


def build_contacts():
    def inner(u):
        return f"""<section class="wrap sect bp-contact">
  <div><h2 class="sect__ttl">Как с нами связаться</h2>{contacts_inline(u, False)}
    <p class="lede">По вопросам оптового сотрудничества — страница
    <a class="linkish" href="{u('brand-partnerships/')}">Brand Partnerships</a>.</p>
  </div>
  {contact_form('contact', 'Написать нам', 'Отправляя форму, вы соглашаетесь с политикой обработки персональных данных.', [
      {"name": "name", "label": "Имя", "required": True, "autocomplete": "name"},
      {"name": "email", "label": "Электронная почта", "type": "email", "required": True, "autocomplete": "email"},
      {"name": "order", "label": "Номер заказа"},
      {"name": "message", "label": "Сообщение", "type": "textarea", "wide": True, "required": True}])}
</section>"""
    info_page("contacts/", "Контакты", "Контакты", "Свяжитесь с нами по вопросам заказа, доставки и возврата.",
              "Контакты", inner)


def build_delivery():
    c = CONTENT["delivery"]
    def inner(u):
        rows = "".join("<tr><td>%s</td><td>%s</td><td>%s</td></tr>"
                       % (e(r["name"]), e(r["term"]), e(r["price"])) for r in c["regions"])
        svc = "".join('<li><h3>%s</h3><p>%s</p></li>' % (e(s["title"]), e(s["text"])) for s in c["services"])
        rec = "".join("<li>%s</li>" % e(x) for x in c["receiving"])
        return f"""<section class="wrap sect">
  <div class="tablewrap"><table class="dtable">
    <caption>Сроки и стоимость по регионам</caption>
    <thead><tr><th scope="col">Регион</th><th scope="col">Срок</th><th scope="col">Стоимость</th></tr></thead>
    <tbody>{rows}</tbody></table></div>
</section>
<section class="adv"><div class="wrap"><h2 class="sect__ttl">{e(c['servicesTitle'])}</h2>
  <ul class="adv__list">{svc}</ul></div></section>
<section class="wrap sect"><div class="prose">
  <section class="prose__sect"><h2>{e(c['receivingTitle'])}</h2><ul class="ticks">{rec}</ul></section>
  <section class="prose__sect"><h2>{e(c['cancelTitle'])}</h2><p>{e(c['cancelText'])}</p></section>
</div></section>"""
    info_page("delivery/", "Доставка", "Доставка", c["lead"], c["title"], inner, lede=c["lead"])


def build_returns():
    c = CONTENT["returns"]
    def inner(u):
        cond = "".join("<li>%s</li>" % e(x) for x in c["condition"])
        docs = "".join("<li>%s</li>" % e(x) for x in c["docs"])
        proc = "".join("<li>%s</li>" % e(x) for x in c["process"])
        return f"""<section class="wrap sect"><div class="prose">
  <section class="prose__sect"><h2>{e(c['termTitle'])}</h2><p>{e(c['termText'])}</p></section>
  <section class="prose__sect"><h2>{e(c['conditionTitle'])}</h2><ul class="ticks">{cond}</ul></section>
  <section class="prose__sect"><h2>{e(c['docsTitle'])}</h2><ul class="ticks">{docs}</ul></section>
  <section class="prose__sect"><h2>{e(c['processTitle'])}</h2><ol class="steps">{proc}</ol></section>
  <section class="prose__sect"><h2>{e(c['moneyTitle'])}</h2><p>{e(c['moneyText'])}</p></section>
  <section class="prose__sect"><h2>{e(c['exchangeTitle'])}</h2><p>{e(c['exchangeText'])}</p></section>
</div></section>"""
    info_page("returns/", "Возврат", "Возврат и обмен", c["lead"], c["title"], inner, lede=c["lead"])


def build_payment():
    c = CONTENT["payment"]
    def inner(u):
        pm = "".join(
            f'<li class="pay"><span class="pay__t">{e(m["title"])}</span>'
            f'<span class="pay__n">{e(m["note"])}</span></li>'
            for m in CFG["payments"] if m.get("enabled"))
        return f"""<section class="wrap sect">
  <ul class="paylist">{pm}</ul>
</section>
<section class="wrap sect"><div class="prose">
  <section class="prose__sect"><h2>{e(c['securityTitle'])}</h2><p>{e(c['securityText'])}</p></section>
  <section class="prose__sect"><h2>{e(c['invoiceTitle'])}</h2><p>{e(c['invoiceText'])}</p>
    <p><a class="linkish" href="{u('contacts/')}">Написать нам</a></p></section>
</div></section>"""
    info_page("payment/", "Оплата", "Оплата", c["lead"], c["title"], inner, lede=c["lead"])


def build_faq():
    c = CONTENT["faq"]
    schema = {"@context": "https://schema.org", "@type": "FAQPage",
              "mainEntity": [{"@type": "Question", "name": i["q"],
                              "acceptedAnswer": {"@type": "Answer", "text": i["a"]}} for i in c["items"]]}
    def inner(u):
        items = "".join(
            f'<details class="acc__item"><summary>{e(i["q"])}{icon("chev", 16)}</summary>'
            f'<div class="acc__body"><p>{e(i["a"])}</p></div></details>' for i in c["items"])
        return '<section class="wrap sect"><div class="acc acc--wide">%s</div></section>' % items
    info_page("faq/", "Вопросы и ответы", "Вопросы и ответы",
              "Ответы на частые вопросы о размерах, доставке, возврате и оплате.",
              c["title"], inner, schema=[schema])


def build_legal():
    for key, path, nav in (("offer", "offer/", "Оферта"),
                           ("privacy", "privacy/", "Политика конфиденциальности"),
                           ("personalData", "personal-data/", "Персональные данные")):
        c = CONTENT["legal"][key]
        def inner(u, c=c):
            return ('<section class="wrap sect"><div class="prose"><p class="lede">%s</p>%s</div></section>'
                    % (e(c["intro"]), prose_sections(c["sections"])))
        info_page(path, nav, c["title"], c["intro"][:150], c["title"], inner)

    # Реквизиты: показываем только заполненные поля
    def inner(u):
        c = CFG["company"]
        rows = [(t, c.get(k)) for t, k in (
            ("Наименование", "companyName"), ("Юридическое лицо", "legalName"),
            ("ИНН", "inn"), ("КПП", "kpp"), ("ОГРН/ОГРНИП", "ogrn"),
            ("Юридический адрес", "legalAddress"), ("Фактический адрес", "actualAddress"))]
        rows = [(t, v) for t, v in rows if v]
        table = ('<dl class="contacts">%s</dl>' % "".join(
            "<div><dt>%s</dt><dd>%s</dd></div>" % (e(t), e(v)) for t, v in rows)) if rows else ""
        docs = "".join('<li><a href="%s">%s</a></li>' % (u(p), e(t)) for t, p in (
            ("Публичная оферта", "offer/"), ("Политика конфиденциальности", "privacy/"),
            ("Согласие на обработку персональных данных", "personal-data/"),
            ("Условия доставки", "delivery/"), ("Условия возврата", "returns/"),
            ("Условия оплаты", "payment/")))
        return f"""<section class="wrap sect"><div class="prose">
  {'<section class="prose__sect"><h2>Реквизиты</h2>%s</section>' % table if table else ''}
  <section class="prose__sect"><h2>Документы</h2><ul class="linklist">{docs}</ul></section>
  <section class="prose__sect"><h2>Контакты</h2>{contacts_inline(u)}</section>
</div></section>"""
    info_page("legal/", "Правовая информация", "Правовая информация",
              "Реквизиты, оферта, политика конфиденциальности и условия работы магазина.",
              "Правовая информация", inner)


# ─────────────────────────────────────────────────── корзина / оформление / прочее

def build_cart():
    def inner(u):
        return f"""<section class="wrap sect">
  <div class="cartlayout">
    <div class="cartlines" id="cart-lines" data-empty-title="Корзина пуста"
         data-empty-text="Выберите модель в каталоге и добавьте нужный размер."></div>
    <aside class="summary" id="cart-summary" hidden>
      <h2 class="summary__ttl">Итого</h2>
      <div class="summary__row"><span>Товары</span><b data-sum-goods>0 ₽</b></div>
      <div class="summary__row summary__row--muted"><span>Доставка</span><span>рассчитывается при оформлении</span></div>
      <div class="summary__row summary__row--total"><span>К оплате</span><b data-sum-total>0 ₽</b></div>
      <a class="btn btn--grad btn--wide" href="{u('checkout/')}">Перейти к оформлению</a>
      <a class="btn btn--ghost btn--wide" href="{u('catalog/')}">Продолжить покупки</a>
      {trust_block()}
    </aside>
  </div>
</section>"""
    info_page("cart/", "Корзина", "Корзина", "Товары, выбранные к покупке.", "Корзина", inner)


def build_checkout():
    def inner(u):
        pm = "".join(
            f'<label class="radio"><input type="radio" name="payment" value="{e(m["id"])}"'
            f'{" checked" if i == 0 else ""}><span class="radio__mark"></span>'
            f'<span class="radio__body"><b>{e(m["title"])}</b><i>{e(m["note"])}</i></span></label>'
            for i, m in enumerate([x for x in CFG["payments"] if x.get("enabled")]))
        dl = "".join(
            f'<label class="radio"><input type="radio" name="delivery" value="{v}"'
            f'{" checked" if i == 0 else ""}><span class="radio__mark"></span>'
            f'<span class="radio__body"><b>{e(t)}</b><i>{e(n)}</i></span></label>'
            for i, (v, t, n) in enumerate([
                ("courier", "Курьером до двери", "Дату и интервал согласуем по телефону"),
                ("pickup", "Пункт выдачи", "Заберите заказ в удобное время"),
                ("postamat", "Постамат", "Код для получения придёт в СМС")]))
        return f"""<section class="wrap sect">
  <div class="cartlayout">
    <form class="checkout" id="checkout-form" novalidate>
      <fieldset class="fs"><legend class="fs__ttl">Получатель</legend>
        <div class="cform__grid">
          <div class="field"><label for="co-name">Имя и фамилия</label><input id="co-name" name="name" required autocomplete="name"></div>
          <div class="field"><label for="co-phone">Телефон</label><input id="co-phone" name="phone" type="tel" required autocomplete="tel"></div>
          <div class="field field--wide"><label for="co-email">Электронная почта</label><input id="co-email" name="email" type="email" required autocomplete="email"></div>
        </div>
      </fieldset>
      <fieldset class="fs"><legend class="fs__ttl">Доставка</legend>
        <div class="radios">{dl}</div>
        <div class="cform__grid" id="addr-block">
          <div class="field"><label for="co-city">Город</label><input id="co-city" name="city" required autocomplete="address-level2"></div>
          <div class="field"><label for="co-zip">Индекс</label><input id="co-zip" name="zip" inputmode="numeric" autocomplete="postal-code"></div>
          <div class="field field--wide"><label for="co-addr">Адрес</label><input id="co-addr" name="address" required autocomplete="street-address"></div>
        </div>
      </fieldset>
      <fieldset class="fs"><legend class="fs__ttl">Оплата</legend>
        <div class="radios">{pm}</div>
      </fieldset>
      <fieldset class="fs"><legend class="fs__ttl">Комментарий</legend>
        <div class="field field--wide"><label for="co-note">Пожелания к заказу</label><textarea id="co-note" name="note" rows="3"></textarea></div>
      </fieldset>
      <label class="agree"><input type="checkbox" id="co-agree" required>
        <span>Я согласен с <a href="{u('offer/')}">офертой</a> и <a href="{u('personal-data/')}">обработкой персональных данных</a></span></label>
      <button class="btn btn--grad btn--wide" type="submit">Оформить заказ</button>
      <p class="formmsg" role="status" hidden></p>
    </form>
    <aside class="summary" id="checkout-summary">
      <h2 class="summary__ttl">Ваш заказ</h2>
      <div id="checkout-lines"></div>
      <div class="summary__row"><span>Товары</span><b data-sum-goods>0 ₽</b></div>
      <div class="summary__row summary__row--total"><span>К оплате</span><b data-sum-total>0 ₽</b></div>
      {trust_block()}
    </aside>
  </div>
</section>"""
    info_page("checkout/", "Оформление", "Оформление заказа",
              "Оформление заказа: доставка по России, оплата картой, СБП или при получении.",
              "Оформление заказа", inner)


def build_wishlist():
    def inner(u):
        return """<section class="wrap sect">
  <div id="wish-grid" data-empty-title="В избранном пусто"
       data-empty-text="Нажмите на сердце в карточке товара, чтобы сохранить модель."></div>
</section>"""
    info_page("wishlist/", "Избранное", "Избранное", "Сохранённые модели.", "Избранное", inner)


def build_search():
    def inner(u):
        return """<section class="wrap sect">
  <form class="searchpage__form" role="search" method="get">
    <label class="sr-only" for="q">Поисковый запрос</label>
    <input id="q" name="q" type="search" placeholder="Бренд, модель или артикул" autocomplete="off">
    <button class="btn btn--grad" type="submit">Найти</button>
  </form>
  <p class="searchpage__meta" id="search-meta"></p>
  <div id="search-results"></div>
</section>"""
    info_page("search/", "Поиск", "Поиск по каталогу",
              "Поиск кроссовок по бренду, модели, артикулу и категории.", "Поиск", inner)


def build_account():
    def inner(u):
        return f"""<section class="wrap sect bp-contact">
  <div>
    <h2 class="sect__ttl">Статус заказа</h2>
    <p class="lede">Укажите номер заказа и телефон — покажем, на каком этапе он находится.</p>
    {contact_form('order-status', 'Проверить заказ', 'Номер заказа указан в письме о подтверждении.', [
        {"name": "order", "label": "Номер заказа", "required": True},
        {"name": "phone", "label": "Телефон", "type": "tel", "required": True, "autocomplete": "tel"}])}
  </div>
  <div>
    <h2 class="sect__ttl">Быстрые ссылки</h2>
    <ul class="linklist">
      <li><a href="{u('wishlist/')}">Избранное</a></li>
      <li><a href="{u('cart/')}">Корзина</a></li>
      <li><a href="{u('returns/')}">Оформить возврат</a></li>
      <li><a href="{u('contacts/')}">Связаться с нами</a></li>
    </ul>
    {contacts_inline(u)}
  </div>
</section>"""
    info_page("account/", "Аккаунт", "Аккаунт", "Проверка статуса заказа и быстрые ссылки.",
              "Аккаунт", inner)


def build_404():
    # 404 отдаётся по произвольному пути, поэтому ссылки — абсолютные от корня проекта
    from urllib.parse import urlparse
    base_path = urlparse(CFG["baseUrl"]).path.rstrip("/") + "/"
    u = lambda p="": base_path + p
    h = head(CFG, u, title="Страница не найдена — %s" % CFG["siteName"],
             desc="Страница не найдена.", path="404.html", robots="noindex")
    body = f"""<section class="pagehead"><div class="wrap">
  <h1 class="ttl">404</h1>
  <p class="lede">Такой страницы нет. Возможно, товар снят с продажи или адрес введён с ошибкой.</p>
  <div class="hero-cta">
    <a class="btn btn--grad" href="{u('catalog/')}">В каталог</a>
    <a class="btn btn--ghost" href="{u('')}">На главную</a>
  </div>
</div></section>"""
    mk("404.html", page(CFG, u, head_html=h, body=body, active="",
                        body_class="page-info", base_prefix=base_path))


# ─────────────────────────────────────────────────── данные для клиента, sitemap, robots

def build_data_js():
    items = []
    for p in PRODUCTS:
        items.append({
            "id": p["id"], "brand": p["brand"], "brandName": BRANDS[p["brand"]]["name"],
            "model": p["model"], "name": title_of(p, BRANDS), "sku": p["sku"],
            "gender": p["gender"], "category": p["category"], "purpose": p["purpose"],
            "color": p["color"], "colorName": p["colorName"],
            "price": p["price"], "oldPrice": p.get("oldPrice"),
            "isNew": bool(p.get("isNew")), "releasedAt": p["releasedAt"],
            "sizes": [{"size": s["size"], "stock": s["stock"]} for s in p["sizes"]],
            "img": img(p["image"], 560, 560),
            "thumb": img(p["image"], 200, 200),
            "url": "product/%s/" % p["id"],
        })
    js = ("window.SHOP=%s;\n" % json.dumps(
        {"products": items,
         "brands": [{"slug": b["slug"], "name": b["name"]} for b in BRAND_LIST],
         "categories": {k: v["title"] for k, v in CATEGORIES.items()},
         "genders": GENDERS,
         "config": {"formEndpoint": CFG["forms"]["endpoint"],
                    "email": CFG["contacts"].get("email", ""),
                    "phone": CFG["contacts"].get("phone", "")}},
        ensure_ascii=False, separators=(",", ":")))
    open(os.path.join(ROOT, "assets", "data.js"), "w", encoding="utf-8").write(js)


def build_sitemap():
    base = CFG["baseUrl"].rstrip("/")
    today = datetime.date.today().isoformat()
    prio = {"/": "1.0", "catalog/": "0.9", "brands/": "0.8", "brand-partnerships/": "0.8"}
    urls = []
    for p in WRITTEN:
        if p.endswith((".html", ".xml", ".txt")):
            continue
        loc = base + "/" + ("" if p == "/" else p)
        pr = prio.get(p, "0.7" if p.startswith(("product/", "catalog/", "brands/")) else "0.5")
        urls.append("  <url><loc>%s</loc><lastmod>%s</lastmod><priority>%s</priority></url>"
                    % (loc, today, pr))
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemap.org/schemas/sitemap/0.9">\n%s\n</urlset>\n'
           % "\n".join(sorted(set(urls))))
    xml = xml.replace("http://www.sitemap.org", "http://www.sitemaps.org")
    mk("sitemap.xml", xml)
    mk("robots.txt", "User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % base)


def main():
    build_home()
    build_catalog()
    build_products()
    build_brands()
    build_about()
    build_partnerships()
    build_contacts()
    build_delivery()
    build_returns()
    build_payment()
    build_faq()
    build_legal()
    build_cart()
    build_checkout()
    build_wishlist()
    build_search()
    build_account()
    build_404()
    build_data_js()
    build_sitemap()
    warn = []
    if not CFG["contacts"].get("phone"):
        warn.append("contacts.phone — телефон не показывается в шапке, подвале и контактах")
    if not CFG["contacts"].get("email") and not CFG["forms"]["endpoint"]:
        warn.append("contacts.email или forms.endpoint — формы и оформление заказа не смогут отправить заявку")
    if not CFG["company"].get("legalName"):
        warn.append("company.legalName / inn / ogrn — блок реквизитов на /legal/ скрыт")
    if not CFG.get("domain"):
        warn.append("domain — не подставляется в адреса вида wholesale@…")
    if warn:
        print("\nНЕ ЗАПОЛНЕНО в data/config.json (страницы собраны, поля просто скрыты):")
        for w in warn:
            print("  • " + w)
    print("\nСобрано страниц: %d" % len(WRITTEN))
    for p in sorted(WRITTEN):
        print("  /" + (p if p != "/" else ""))


if __name__ == "__main__":
    main()
