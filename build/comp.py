# -*- coding: utf-8 -*-
"""Переиспользуемые компоненты разметки. Ни один из них не дублируется по страницам."""
import html, json, os, re, hashlib

IMG = "https://images.unsplash.com/{id}?auto=format&fit=crop&w={w}&h={h}&q={q}{extra}"
VIEWS = ["", "&crop=top", "&crop=bottom", "&crop=left", "&crop=right"]

CATEGORIES = {
    "running":   {"title": "Бег",       "slug": "running",   "h1": "Беговые кроссовки"},
    "lifestyle": {"title": "Lifestyle", "slug": "lifestyle", "h1": "Lifestyle-кроссовки"},
    "training":  {"title": "Training",  "slug": "training",  "h1": "Кроссовки для тренировок"},
}
GENDERS = {"men": "Мужское", "women": "Женское", "unisex": "Унисекс"}
COLORS = {
    "black": "Чёрный", "white": "Белый", "grey": "Серый", "red": "Красный",
    "green": "Зелёный", "pink": "Розовый", "brown": "Коричневый", "multi": "Разноцветный",
}
COLOR_HEX = {
    "black": "#1a1a1a", "white": "#f2f2f2", "grey": "#8d8d8d", "red": "#b3242c",
    "green": "#5f7d3a", "pink": "#d9a2b0", "brown": "#8a6440", "multi": "linear-gradient(135deg,#d9a2b0,#8fc4d8,#e8d9a0)",
}
# Европейский размер → длина стопы, UK, US
SIZE_TABLE = {
    35.5: (22.5, "3", "5"), 36: (22.5, "3.5", "5.5"), 36.5: (23, "4", "6"),
    37: (23.5, "4.5", "6.5"), 37.5: (23.5, "4.5", "6.5"), 38: (24, "5", "7"),
    38.5: (24.5, "5.5", "7.5"), 39: (25, "6", "8"), 40: (25.5, "6.5", "8.5"),
    40.5: (26, "7", "9"), 41: (26.5, "7.5", "9.5"), 42: (27, "8", "10"),
    42.5: (27.5, "8.5", "10.5"), 43: (28, "9", "11"), 44: (28.5, "9.5", "11.5"),
    44.5: (29, "10", "12"), 45: (29.5, "10.5", "12.5"), 46: (30, "11", "13"),
}

e = lambda s: html.escape(str(s), quote=True)

_ASSET_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
_VER = {}


def ver(name):
    """assets/<name> + короткий хеш содержимого — чтобы кэш не отдавал старую версию."""
    if name not in _VER:
        p = os.path.join(_ASSET_DIR, name)
        try:
            h = hashlib.sha1(open(p, "rb").read()).hexdigest()[:8]
        except OSError:
            h = "0"
        _VER[name] = h
    return "assets/%s?v=%s" % (name, _VER[name])


def money(n):
    return "{:,}".format(int(n)).replace(",", " ") + " ₽"


def fmt_size(s):
    return str(int(s)) if float(s) == int(s) else str(s)


def img(pid, w=800, h=800, view=0, q=80):
    return IMG.format(id=pid, w=w, h=h, q=q, extra=VIEWS[view % len(VIEWS)])


def gallery(p, w=1000):
    return [img(p["image"], w, w, i) for i in range(len(VIEWS))]


def in_stock(p):
    return sum(s["stock"] for s in p["sizes"])


def discount(p):
    if not p.get("oldPrice"):
        return 0
    return round((p["oldPrice"] - p["price"]) / p["oldPrice"] * 100)


def product_url(p, u):
    return u("product/%s/" % p["id"])


def title_of(p, brands):
    return "%s %s" % (brands[p["brand"]]["name"], p["model"])


# ─────────────────────────────────────────────────────────── head / seo

def head(cfg, u, *, title, desc, path, h1=None, og_image=None, schema=None, robots=None):
    base = cfg["baseUrl"].rstrip("/")
    canonical = base + "/" + path if path else base + "/"
    og = og_image or (base + "/assets/og-default.png")
    out = [
        '<!DOCTYPE html>', '<html lang="ru">', '<head>',
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width,initial-scale=1">',
        '<title>%s</title>' % e(title),
        '<meta name="description" content="%s">' % e(desc),
        '<link rel="canonical" href="%s">' % e(canonical),
        '<meta name="theme-color" content="#050505">',
        '<meta property="og:type" content="website">',
        '<meta property="og:site_name" content="%s">' % e(cfg["siteName"]),
        '<meta property="og:title" content="%s">' % e(title),
        '<meta property="og:description" content="%s">' % e(desc),
        '<meta property="og:url" content="%s">' % e(canonical),
        '<meta property="og:image" content="%s">' % e(og),
        '<meta property="og:locale" content="ru_RU">',
        '<meta name="twitter:card" content="summary_large_image">',
    ]
    if robots:
        out.append('<meta name="robots" content="%s">' % e(robots))
    out += [
        '<link rel="icon" href="%s" type="image/svg+xml">' % u("assets/favicon.svg"),
        '<link rel="preconnect" href="https://images.unsplash.com" crossorigin>',
        '<link rel="preload" as="style" href="%s">' % u(ver("styles.css")),
        '<link rel="stylesheet" href="%s">' % u(ver("styles.css")),
        '<link rel="stylesheet" href="%s">' % u(ver("refine.css")),
        '<link rel="stylesheet" href="%s">' % u(ver("shop.css")),
    ]
    for s in (schema or []):
        out.append('<script type="application/ld+json">%s</script>'
                   % json.dumps(s, ensure_ascii=False, separators=(",", ":")))
    out.append('</head>')
    return "\n".join(out)


def org_schema(cfg, u):
    base = cfg["baseUrl"].rstrip("/")
    org = {"@context": "https://schema.org", "@type": "Organization",
           "name": cfg["company"]["companyName"], "url": base + "/",
           "logo": base + "/assets/favicon.svg"}
    if cfg["company"].get("legalName"):
        org["legalName"] = cfg["company"]["legalName"]
    cp = {}
    if cfg["contacts"].get("phone"):
        cp["telephone"] = cfg["contacts"]["phone"]
    if cfg["contacts"].get("email"):
        cp["email"] = cfg["contacts"]["email"]
    if cp:
        cp.update({"@type": "ContactPoint", "contactType": "customer support", "areaServed": "RU"})
        org["contactPoint"] = [cp]
    if cfg["company"].get("legalAddress"):
        org["address"] = {"@type": "PostalAddress", "streetAddress": cfg["company"]["legalAddress"],
                          "addressCountry": "RU"}
    if cfg.get("social"):
        org["sameAs"] = cfg["social"]
    return org


def website_schema(cfg):
    base = cfg["baseUrl"].rstrip("/")
    return {"@context": "https://schema.org", "@type": "WebSite", "name": cfg["siteName"],
            "url": base + "/", "inLanguage": "ru-RU",
            "potentialAction": {"@type": "SearchAction",
                                "target": {"@type": "EntryPoint",
                                           "urlTemplate": base + "/search/?q={search_term_string}"},
                                "query-input": "required name=search_term_string"}}


def breadcrumb_schema(cfg, items):
    base = cfg["baseUrl"].rstrip("/")
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": i + 1, "name": name,
                 "item": base + "/" + path if path else base + "/"}
                for i, (name, path) in enumerate(items)]}


def product_schema(cfg, p, brands):
    base = cfg["baseUrl"].rstrip("/")
    stock = in_stock(p)
    d = {"@context": "https://schema.org", "@type": "Product",
         "name": title_of(p, brands),
         "sku": p["sku"],
         "brand": {"@type": "Brand", "name": brands[p["brand"]]["name"]},
         "color": p["colorName"],
         "description": p["description"],
         "image": gallery(p),
         "category": CATEGORIES[p["category"]]["title"],
         "offers": {"@type": "Offer",
                    "price": p["price"], "priceCurrency": "RUB",
                    "url": base + "/product/%s/" % p["id"],
                    "availability": "https://schema.org/InStock" if stock else "https://schema.org/OutOfStock",
                    "itemCondition": "https://schema.org/NewCondition"}}
    if p.get("country"):
        d["countryOfOrigin"] = p["country"]
    if p["materials"].get("upper"):
        d["material"] = p["materials"]["upper"]
    return d


# ─────────────────────────────────────────────────────────── header

NAV = [
    ("Мужское",  "catalog/mens/"),
    ("Женское",  "catalog/womens/"),
    ("Бренды",   "brands/"),
    ("Бег",      "catalog/running/"),
    ("Lifestyle", "catalog/lifestyle/"),
    ("Training", "catalog/training/"),
    ("Новинки",  "catalog/new/"),
    ("Sale",     "catalog/sale/"),
    ("О нас",    "about/"),
]

ICONS = {
    "search": '<path d="M11 4a7 7 0 1 0 0 14 7 7 0 0 0 0-14Zm5.5 12.5L21 21"/>',
    "heart":  '<path d="M12 20.3 4.7 13a4.6 4.6 0 0 1 6.5-6.5l.8.8.8-.8A4.6 4.6 0 1 1 19.3 13Z"/>',
    "user":   '<circle cx="12" cy="8" r="3.6"/><path d="M4.8 20a7.2 7.2 0 0 1 14.4 0"/>',
    "bag":    '<path d="M6 8h12l-1.1 12.2A2 2 0 0 1 14.9 22H9.1a2 2 0 0 1-2-1.8L6 8Z"/><path d="M9 8V6.2a3 3 0 0 1 6 0V8"/>',
    "close":  '<path d="M6 6l12 12M18 6 6 18"/>',
    "burger": '<path d="M4 7h16M4 12h16M4 17h16"/>',
    "chev":   '<path d="m9 6 6 6-6 6"/>',
    "check":  '<path d="m5 12.5 4.5 4.5L19 7.5"/>',
}


def icon(name, size=20, cls=""):
    return ('<svg class="ico %s" width="%d" height="%d" viewBox="0 0 24 24" fill="none" '
            'stroke="currentColor" stroke-width="1.6" stroke-linecap="round" '
            'stroke-linejoin="round" aria-hidden="true">%s</svg>') % (cls, size, size, ICONS[name])


def header(cfg, u, active=""):
    links = "".join(
        '<a href="%s"%s>%s</a>' % (u(path), ' aria-current="page"' if path == active else "", e(name))
        for name, path in NAV)
    mob = "".join(
        '<a href="%s"%s>%s %s</a>' % (u(path), ' aria-current="page"' if path == active else "",
                                      e(name), icon("chev", 16))
        for name, path in NAV)

    phone = ""
    if cfg["contacts"].get("phone"):
        ph = cfg["contacts"]["phone"]
        phone = '<a class="hdr-top__phone" href="tel:%s">%s</a>' % (
            e(re.sub(r"[^\d+]", "", ph)), e(ph))

    return f"""<a class="skip" href="#main">Перейти к содержимому</a>
<header class="hdr" id="site-header">
  <div class="hdr-top">
    <div class="hdr-top__in">
      <span>Доставка по России · возврат 14 дней</span>
      {phone}
    </div>
  </div>
  <div class="hdr-main">
    <button class="hdr-burger" type="button" data-open-menu aria-label="Открыть меню" aria-expanded="false">{icon('burger', 22)}</button>
    <a class="hdr-logo" href="{u('')}"><span class="hdr-logo__dot" aria-hidden="true"></span>{e(cfg['siteName'])}</a>
    <nav class="hdr-nav" aria-label="Основное меню">{links}</nav>
    <div class="hdr-actions">
      <button class="hdr-btn" type="button" data-open-search aria-label="Поиск">{icon('search')}</button>
      <a class="hdr-btn" href="{u('wishlist/')}" aria-label="Избранное">{icon('heart')}<span class="hdr-badge" data-wish-count hidden>0</span></a>
      <a class="hdr-btn hdr-btn--acct" href="{u('account/')}" aria-label="Аккаунт">{icon('user')}</a>
      <a class="hdr-btn hdr-btn--cart" href="{u('cart/')}" aria-label="Корзина">{icon('bag')}<span class="hdr-badge" data-cart-count hidden>0</span></a>
    </div>
  </div>
</header>

<div class="drawer" id="menu-drawer" hidden>
  <div class="drawer__scrim" data-close-menu></div>
  <nav class="drawer__panel" aria-label="Мобильное меню">
    <div class="drawer__head">
      <span class="drawer__title">Меню</span>
      <button class="hdr-btn" type="button" data-close-menu aria-label="Закрыть меню">{icon('close')}</button>
    </div>
    <div class="drawer__links">{mob}</div>
    <div class="drawer__foot">
      <a href="{u('account/')}">Аккаунт</a>
      <a href="{u('delivery/')}">Доставка</a>
      <a href="{u('returns/')}">Возврат</a>
      <a href="{u('payment/')}">Оплата</a>
      <a href="{u('brand-partnerships/')}">Brand Partnerships</a>
    </div>
  </nav>
</div>

<div class="srch" id="search-overlay" hidden>
  <div class="srch__scrim" data-close-search></div>
  <div class="srch__panel" role="dialog" aria-modal="true" aria-label="Поиск по каталогу">
    <form class="srch__form" action="{u('search/')}" method="get" role="search">
      {icon('search', 22, 'srch__ico')}
      <input class="srch__input" type="search" name="q" id="site-search" autocomplete="off"
             placeholder="Бренд, модель или артикул" aria-label="Поисковый запрос">
      <button class="hdr-btn" type="button" data-close-search aria-label="Закрыть поиск">{icon('close')}</button>
    </form>
    <div class="srch__hint">Например: Air Force, New Balance, FRM-NK-1041</div>
    <div class="srch__out" id="search-suggest" role="listbox" aria-label="Подсказки"></div>
  </div>
</div>"""


# ─────────────────────────────────────────────────────────── footer

def footer(cfg, u):
    c, k = cfg["company"], cfg["contacts"]

    def group(title, items):
        li = "".join('<li><a href="%s">%s</a></li>' % (u(p), e(t)) for t, p in items)
        return '<div class="ft-col"><h3>%s</h3><ul>%s</ul></div>' % (e(title), li)

    cols = (
        group("Магазин", [("Каталог", "catalog/"), ("Новинки", "catalog/new/"),
                          ("Sale", "catalog/sale/"), ("Бренды", "brands/")]) +
        group("Помощь", [("Доставка", "delivery/"), ("Оплата", "payment/"),
                         ("Возврат", "returns/"), ("Вопросы и ответы", "faq/")]) +
        group("Компания", [("О нас", "about/"), ("Контакты", "contacts/"),
                           ("Brand Partnerships", "brand-partnerships/")]) +
        group("Документы", [("Оферта", "offer/"), ("Конфиденциальность", "privacy/"),
                            ("Персональные данные", "personal-data/"), ("Реквизиты", "legal/")])
    )

    ct = []
    if k.get("phone"):
        ct.append('<a class="ft-contact" href="tel:%s">%s</a>'
                  % (e(re.sub(r"[^\d+]", "", k["phone"])), e(k["phone"])))
    if k.get("email"):
        ct.append('<a class="ft-contact" href="mailto:%s">%s</a>' % (e(k["email"]), e(k["email"])))
    if k.get("workHours"):
        ct.append('<span class="ft-hours">%s</span>' % e(k["workHours"]))
    social = "".join('<a href="%s" rel="noopener" target="_blank">%s</a>' % (e(s["url"]), e(s["title"]))
                     for s in cfg.get("social", []))
    if social:
        ct.append('<div class="ft-social">%s</div>' % social)
    contacts = ('<div class="ft-col ft-col--contacts"><h3>Контакты</h3>%s</div>' % "".join(ct)) if ct else ""

    legal_line = " · ".join(x for x in [
        c.get("legalName") or c.get("companyName"),
        ("ИНН " + c["inn"]) if c.get("inn") else "",
        ("ОГРН " + c["ogrn"]) if c.get("ogrn") else "",
    ] if x)

    return f"""<footer class="ft">
  <div class="ft__in">
    <div class="ft-brand">
      <span class="ft-brand__mark">{e(cfg['siteName'])}</span>
      <p>{e(cfg['tagline'])}</p>
    </div>
    <div class="ft-cols">{cols}{contacts}</div>
  </div>
  <div class="ft__bar">
    <span>© 2026 {e(legal_line)}</span>
    <span class="ft__bar-links">
      <a href="{u('offer/')}">Оферта</a>
      <a href="{u('privacy/')}">Конфиденциальность</a>
    </span>
  </div>
</footer>"""


# ─────────────────────────────────────────────────────────── товар

def badges(p):
    out = []
    d = discount(p)
    if d:
        out.append('<span class="badge badge--sale">−%d%%</span>' % d)
    if p.get("isNew"):
        out.append('<span class="badge badge--new">Новинка</span>')
    if 0 < in_stock(p) <= 3:
        out.append('<span class="badge badge--last">Мало</span>')
    return '<div class="pcard__badges">%s</div>' % "".join(out) if out else ""


def product_card(p, brands, u, *, eager=False):
    stock = in_stock(p)
    price = ('<span class="pcard__price">%s</span>'
             '<span class="pcard__old">%s</span>' % (money(p["price"]), money(p["oldPrice"]))) \
        if p.get("oldPrice") else '<span class="pcard__price">%s</span>' % money(p["price"])
    sizes = " ".join(fmt_size(s["size"]) for s in p["sizes"] if s["stock"] > 0)
    return f"""<article class="pcard{'' if stock else ' is-out'}"
  data-product="{e(p['id'])}" data-brand="{e(p['brand'])}" data-cat="{e(p['category'])}"
  data-gender="{e(p['gender'])}" data-color="{e(p['color'])}" data-price="{p['price']}"
  data-stock="{stock}" data-new="{1 if p.get('isNew') else 0}" data-sale="{discount(p)}"
  data-purpose="{e(p['purpose'])}" data-released="{e(p['releasedAt'])}"
  data-sizes="{e(','.join(fmt_size(s['size']) for s in p['sizes'] if s['stock'] > 0))}"
  data-name="{e(title_of(p, brands))}" data-sku="{e(p['sku'])}">
  <a class="pcard__media" href="{product_url(p, u)}" tabindex="-1" aria-hidden="true">
    {badges(p)}
    <img src="{img(p['image'], 560, 560)}" alt="" width="560" height="560"
         loading="{'eager' if eager else 'lazy'}" decoding="async">
  </a>
  <button class="pcard__wish" type="button" data-wish="{e(p['id'])}"
          aria-label="Добавить {e(title_of(p, brands))} в избранное" aria-pressed="false">{icon('heart', 18)}</button>
  <div class="pcard__body">
    <span class="pcard__brand">{e(brands[p['brand']]['name'])}</span>
    <h3 class="pcard__name"><a href="{product_url(p, u)}">{e(p['model'])}</a></h3>
    <span class="pcard__color">{e(p['colorName'])}</span>
    <div class="pcard__prices">{price}</div>
    <div class="pcard__sizes">{'Размеры: ' + e(sizes) if sizes else 'Нет в наличии'}</div>
  </div>
</article>"""


def product_grid(items, brands, u, *, eager_first=0):
    if not items:
        return empty_state("В этой подборке пока нет моделей",
                           "Посмотрите каталог целиком или измените фильтры.", u)
    cards = "".join(product_card(p, brands, u, eager=(i < eager_first))
                    for i, p in enumerate(items))
    return '<div class="pgrid" id="product-grid">%s</div>' % cards


def empty_state(title, text, u, action=("Весь каталог", "catalog/")):
    return f"""<div class="empty" id="empty-state">
  <h3>{e(title)}</h3><p>{e(text)}</p>
  <a class="btn btn--ghost" href="{u(action[1])}">{e(action[0])}</a>
</div>"""


def breadcrumbs(items, u):
    parts = []
    for i, (name, path) in enumerate(items):
        last = i == len(items) - 1
        parts.append('<span aria-current="page">%s</span>' % e(name) if last
                     else '<a href="%s">%s</a>' % (u(path), e(name)))
    return '<nav class="crumbs" aria-label="Хлебные крошки">%s</nav>' % \
           '<span class="crumbs__sep">/</span>'.join(parts)


TRUST = [
    ("Оригинальная продукция", "Принимаем товар по накладным от поставщиков"),
    ("Возврат в течение 14 дней", "Если размер не подошёл — вернём деньги"),
    ("Доставка по России", "Курьер, пункты выдачи и постаматы"),
    ("Безопасная оплата", "Карта, СБП или оплата при получении"),
    ("Проверка перед отправкой", "Осматриваем каждую пару на брак и комплектность"),
]


def trust_block(compact=True):
    items = "".join('<li>%s<span><b>%s</b>%s</span></li>' % (icon("check", 16), e(t), e(d))
                    for t, d in TRUST)
    return '<ul class="trust%s">%s</ul>' % (" trust--compact" if compact else "", items)


def size_chart(p):
    rows = ""
    for s in p["sizes"]:
        cm, uk, us = SIZE_TABLE.get(s["size"], ("—", "—", "—"))
        rows += "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            fmt_size(s["size"]), uk, us, cm)
    return f"""<div class="modal__box">
  <table class="sizetable">
    <caption>Размерная сетка · {e(p['model'])}</caption>
    <thead><tr><th scope="col">EU</th><th scope="col">UK</th><th scope="col">US</th><th scope="col">Длина стопы, см</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
  <p class="sizetable__note">Измерьте стопу вечером, стоя на листе бумаги. Если значение между размерами — выбирайте больший.</p>
</div>"""


def page(cfg, u, *, head_html, body, active="", body_class="", base_prefix=""):
    return "\n".join([
        head_html,
        '<body class="%s" data-base="%s">' % (e(body_class), e(base_prefix)),
        header(cfg, u, active),
        '<main id="main">', body, '</main>',
        footer(cfg, u),
        '<script src="%s" defer></script>' % u(ver("data.js")),
        '<script src="%s" defer></script>' % u(ver("shop.js")),
        '</body>', '</html>', ''
    ])
