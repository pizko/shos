/* ФОРМА — клиентская логика магазина: корзина, избранное, фильтры, поиск, галерея, формы. */
(function () {
  'use strict';

  var SHOP = window.SHOP || { products: [], brands: [], config: {} };
  var P = SHOP.products;
  var CFG = SHOP.config || {};
  var BASE = (document.body && document.body.dataset.base) || '';
  var CART_KEY = 'forma.cart.v2';
  var WISH_KEY = 'forma.wish.v2';
  var calm = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var byId = function (id) { for (var i = 0; i < P.length; i++) if (P[i].id === id) return P[i]; return null; };
  var money = function (n) { return Number(n).toLocaleString('ru-RU') + ' ₽'; };
  var url = function (p) { return BASE + p; };
  var fmtSize = function (s) { return (Number(s) % 1 === 0) ? String(Number(s)) : String(s); };
  var esc = function (s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  };

  /* ── хранилище ────────────────────────────────────── */
  function read(key) {
    try { var v = JSON.parse(localStorage.getItem(key)); return Array.isArray(v) ? v : []; }
    catch (e) { return []; }
  }
  function write(key, v) {
    try { localStorage.setItem(key, JSON.stringify(v)); } catch (e) {}
  }

  var cart = read(CART_KEY).filter(function (l) {
    var p = byId(l.id);
    return p && p.sizes.some(function (s) { return fmtSize(s.size) === fmtSize(l.size); })
      && l.qty > 0 && l.qty <= 99;
  });
  var wish = read(WISH_KEY).filter(byId);

  function saveCart() { write(CART_KEY, cart); paintBadges(); renderCart(); renderCheckout(); }
  function saveWish() { write(WISH_KEY, wish); paintBadges(); paintWishButtons(); renderWishlist(); }

  function cartCount() { return cart.reduce(function (n, l) { return n + l.qty; }, 0); }
  function cartTotal() {
    return cart.reduce(function (n, l) {
      var p = byId(l.id); return n + (p ? p.price * l.qty : 0);
    }, 0);
  }
  function stockFor(p, size) {
    for (var i = 0; i < p.sizes.length; i++)
      if (fmtSize(p.sizes[i].size) === fmtSize(size)) return p.sizes[i].stock;
    return 0;
  }

  function addToCart(id, size) {
    var p = byId(id);
    if (!p) return false;
    var max = stockFor(p, size);
    if (!max) return false;
    var line = null;
    for (var i = 0; i < cart.length; i++)
      if (cart[i].id === id && fmtSize(cart[i].size) === fmtSize(size)) { line = cart[i]; break; }
    if (line) { if (line.qty >= max) return 'max'; line.qty += 1; }
    else cart.push({ id: id, size: fmtSize(size), qty: 1 });
    saveCart();
    return true;
  }

  function paintBadges() {
    var n = cartCount();
    $$('[data-cart-count]').forEach(function (el) { el.textContent = n; el.hidden = !n; });
    $$('[data-wish-count]').forEach(function (el) { el.textContent = wish.length; el.hidden = !wish.length; });
  }

  /* ── избранное ────────────────────────────────────── */
  function paintWishButtons() {
    $$('[data-wish]').forEach(function (b) {
      b.setAttribute('aria-pressed', String(wish.indexOf(b.dataset.wish) > -1));
    });
  }
  document.addEventListener('click', function (ev) {
    var b = ev.target.closest('[data-wish]');
    if (!b) return;
    ev.preventDefault();
    var id = b.dataset.wish, i = wish.indexOf(id);
    if (i > -1) wish.splice(i, 1); else wish.push(id);
    saveWish();
  });

  /* ── мобильное меню ───────────────────────────────── */
  var menu = $('#menu-drawer');
  function closeOthers(keep) {
    if (keep !== 'menu' && menu && !menu.hidden) { menu.hidden = true; }
    if (keep !== 'search' && overlay && !overlay.hidden) { overlay.hidden = true; }
    var f = $('#filters');
    if (keep !== 'filters' && f) f.classList.remove('is-open');
  }

  function openMenu() {
    if (!menu) return;
    closeOthers('menu');
    menu.hidden = false;
    document.body.style.overflow = 'hidden';
    $$('[data-open-menu]').forEach(function (b) { b.setAttribute('aria-expanded', 'true'); });
    var c = $('[data-close-menu]', menu); if (c && c.focus) setTimeout(function () { c.focus(); }, 30);
  }
  function closeMenu() {
    if (!menu) return;
    menu.hidden = true;
    document.body.style.overflow = '';
    $$('[data-open-menu]').forEach(function (b) { b.setAttribute('aria-expanded', 'false'); });
  }
  $$('[data-open-menu]').forEach(function (b) { b.addEventListener('click', openMenu); });
  document.addEventListener('click', function (ev) {
    if (ev.target.closest('[data-close-menu]')) closeMenu();
  });

  /* ── поиск ────────────────────────────────────────── */
  var overlay = $('#search-overlay');
  var sInput = $('#site-search');
  var sOut = $('#search-suggest');

  function matches(q) {
    q = q.trim().toLowerCase();
    if (q.length < 2) return [];
    var terms = q.split(/\s+/);
    return P.filter(function (p) {
      var hay = (p.brandName + ' ' + p.model + ' ' + p.sku + ' ' + p.colorName + ' ' +
        (SHOP.categories[p.category] || '') + ' ' + p.purpose).toLowerCase();
      return terms.every(function (t) { return hay.indexOf(t) > -1; });
    });
  }

  function openSearch() {
    if (!overlay) return;
    closeOthers('search');
    overlay.hidden = false;
    document.body.style.overflow = 'hidden';
    if (sInput) setTimeout(function () { sInput.focus(); }, 30);
  }
  function closeSearch() {
    if (!overlay) return;
    overlay.hidden = true;
    document.body.style.overflow = '';
    if (sOut) sOut.innerHTML = '';
  }
  $$('[data-open-search]').forEach(function (b) { b.addEventListener('click', openSearch); });
  document.addEventListener('click', function (ev) {
    if (ev.target.closest('[data-close-search]')) closeSearch();
  });

  function suggestRow(p) {
    return '<a class="sugg" href="' + url(p.url) + '" role="option">' +
      '<img src="' + p.thumb + '" alt="" width="46" height="46" loading="lazy">' +
      '<span><span class="sugg__b">' + esc(p.brandName) + '</span>' +
      '<span class="sugg__n">' + esc(p.model) + '</span></span>' +
      '<span class="sugg__p">' + money(p.price) + '</span></a>';
  }

  if (sInput && sOut) {
    sInput.addEventListener('input', function () {
      var res = matches(sInput.value).slice(0, 6);
      if (!sInput.value.trim() || sInput.value.trim().length < 2) { sOut.innerHTML = ''; return; }
      sOut.innerHTML = res.length
        ? res.map(suggestRow).join('')
        : '<div class="srch__hint">Ничего не найдено. Попробуйте другой запрос.</div>';
    });
  }

  document.addEventListener('keydown', function (ev) {
    if (ev.key !== 'Escape') return;
    if (overlay && !overlay.hidden) closeSearch();
    if (menu && !menu.hidden) closeMenu();
    var f = $('#filters');
    if (f && f.classList.contains('is-open')) f.classList.remove('is-open');
  });

  /* страница поиска */
  var sResults = $('#search-results');
  if (sResults) {
    var q = new URLSearchParams(location.search).get('q') || '';
    var field = $('#q');
    if (field) field.value = q;
    var meta = $('#search-meta');
    var res = matches(q);
    if (!q.trim()) {
      if (meta) meta.textContent = 'Введите бренд, модель или артикул.';
      sResults.innerHTML = '';
    } else if (!res.length) {
      if (meta) meta.textContent = 'По запросу «' + q + '» ничего не найдено.';
      sResults.innerHTML = '<div class="empty"><h3>Ничего не найдено</h3>' +
        '<p>Проверьте написание или посмотрите каталог целиком.</p>' +
        '<a class="btn btn--ghost" href="' + url('catalog/') + '">Весь каталог</a></div>';
    } else {
      if (meta) meta.textContent = 'Найдено: ' + res.length + ' по запросу «' + q + '»';
      sResults.innerHTML = '<div class="pgrid">' + res.map(cardHTML).join('') + '</div>';
      paintWishButtons();
    }
  }

  function cardHTML(p) {
    var badges = '';
    if (p.oldPrice) badges += '<span class="badge badge--sale">−' +
      Math.round((p.oldPrice - p.price) / p.oldPrice * 100) + '%</span>';
    if (p.isNew) badges += '<span class="badge badge--new">Новинка</span>';
    var stock = p.sizes.reduce(function (n, s) { return n + s.stock; }, 0);
    var sizes = p.sizes.filter(function (s) { return s.stock > 0; })
      .map(function (s) { return fmtSize(s.size); }).join(' ');
    return '<article class="pcard' + (stock ? '' : ' is-out') + '">' +
      '<a class="pcard__media" href="' + url(p.url) + '" tabindex="-1" aria-hidden="true">' +
      (badges ? '<div class="pcard__badges">' + badges + '</div>' : '') +
      '<img src="' + p.img + '" alt="" width="560" height="560" loading="lazy"></a>' +
      '<button class="pcard__wish" type="button" data-wish="' + p.id + '" aria-pressed="false" ' +
      'aria-label="В избранное: ' + esc(p.name) + '">' + heartSVG() + '</button>' +
      '<div class="pcard__body">' +
      '<span class="pcard__brand">' + esc(p.brandName) + '</span>' +
      '<h3 class="pcard__name"><a href="' + url(p.url) + '">' + esc(p.model) + '</a></h3>' +
      '<span class="pcard__color">' + esc(p.colorName) + '</span>' +
      '<div class="pcard__prices"><span class="pcard__price">' + money(p.price) + '</span>' +
      (p.oldPrice ? '<span class="pcard__old">' + money(p.oldPrice) + '</span>' : '') + '</div>' +
      '<div class="pcard__sizes">' + (sizes ? 'Размеры: ' + sizes : 'Нет в наличии') + '</div>' +
      '</div></article>';
  }
  function heartSVG() {
    return '<svg class="ico" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
      'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
      '<path d="M12 20.3 4.7 13a4.6 4.6 0 0 1 6.5-6.5l.8.8.8-.8A4.6 4.6 0 1 1 19.3 13Z"/></svg>';
  }

  /* ── фильтры и сортировка ─────────────────────────── */
  var grid = $('#product-grid');
  if (grid) {
    var cards = $$('.pcard', grid);
    var panel = $('#filters');
    var countEl = $('#results-count');
    var emptyEl = $('#empty-state');
    var sortSel = $('#sort-select');
    var pMin = $('#price-min'), pMax = $('#price-max');

    $$('[data-open-filters]').forEach(function (b) {
      b.addEventListener('click', function () {
        closeOthers('filters');
        if (panel) { panel.classList.add('is-open'); document.body.style.overflow = 'hidden'; }
      });
    });
    document.addEventListener('click', function (ev) {
      if (!ev.target.closest('[data-close-filters]')) return;
      if (panel) panel.classList.remove('is-open');
      document.body.style.overflow = '';
    });

    var checked = function (key) {
      return $$('input[data-f="' + key + '"]:checked', panel).map(function (i) { return i.value; });
    };

    function apply() {
      var f = {
        brand: checked('brand'), size: checked('size'), gender: checked('gender'),
        cat: checked('cat'), color: checked('color'), purpose: checked('purpose'),
        instock: checked('instock').length > 0
      };
      var lo = pMin ? Number(pMin.value) || 0 : 0;
      var hi = pMax ? Number(pMax.value) || Infinity : Infinity;

      var shown = cards.filter(function (c) {
        var d = c.dataset;
        if (f.brand.length && f.brand.indexOf(d.brand) < 0) return false;
        if (f.gender.length && f.gender.indexOf(d.gender) < 0) return false;
        if (f.cat.length && f.cat.indexOf(d.cat) < 0) return false;
        if (f.color.length && f.color.indexOf(d.color) < 0) return false;
        if (f.purpose.length && f.purpose.indexOf(d.purpose) < 0) return false;
        if (f.instock && Number(d.stock) <= 0) return false;
        var pr = Number(d.price);
        if (pr < lo || pr > hi) return false;
        if (f.size.length) {
          var have = (d.sizes || '').split(',');
          if (!f.size.some(function (s) { return have.indexOf(s) > -1; })) return false;
        }
        return true;
      });

      var mode = sortSel ? sortSel.value : 'popular';
      var order = shown.slice();
      if (mode === 'price-asc') order.sort(function (a, b) { return a.dataset.price - b.dataset.price; });
      if (mode === 'price-desc') order.sort(function (a, b) { return b.dataset.price - a.dataset.price; });
      if (mode === 'new') order.sort(function (a, b) {
        return a.dataset.released < b.dataset.released ? 1 : -1;
      });
      if (mode === 'discount') order.sort(function (a, b) { return b.dataset.sale - a.dataset.sale; });

      cards.forEach(function (c) { c.hidden = shown.indexOf(c) < 0; });
      order.forEach(function (c) { grid.appendChild(c); });

      if (countEl) countEl.textContent = shown.length;
      grid.hidden = !shown.length;
      if (emptyEl) emptyEl.hidden = !!shown.length;
    }

    $$('input[data-f]', panel).forEach(function (i) { i.addEventListener('change', apply); });
    if (pMin) pMin.addEventListener('input', apply);
    if (pMax) pMax.addEventListener('input', apply);
    if (sortSel) sortSel.addEventListener('change', apply);
    var reset = $('#reset-filters');
    if (reset) reset.addEventListener('click', function () {
      $$('input[data-f]', panel).forEach(function (i) { i.checked = false; });
      if (pMin) pMin.value = pMin.min;
      if (pMax) pMax.value = pMax.max;
      if (sortSel) sortSel.value = 'popular';
      apply();
    });
    if (emptyEl) emptyEl.hidden = true;
    apply();
  }

  /* ── карточка товара ──────────────────────────────── */
  var stage = $('#pdp-stage');
  if (stage) {
    var thumbs = $$('.pdp-thumb');
    var slides = $$('.pdp-slide', stage);

    function activate(i) {
      thumbs.forEach(function (t, j) { t.setAttribute('aria-pressed', String(i === j)); });
    }
    thumbs.forEach(function (t) {
      t.addEventListener('click', function () {
        var i = Number(t.dataset.i);
        stage.scrollTo({ left: slides[i].offsetLeft - stage.offsetLeft, behavior: calm ? 'auto' : 'smooth' });
        activate(i);
      });
    });
    stage.addEventListener('scroll', function () {
      var i = Math.round(stage.scrollLeft / stage.clientWidth);
      activate(Math.max(0, Math.min(i, slides.length - 1)));
    }, { passive: true });

    var lb = $('#lightbox'), lbImg = $('#lightbox-img'), zoom = $('#pdp-zoom');
    function openLB() {
      var i = Math.round(stage.scrollLeft / stage.clientWidth);
      var im = $('img', slides[Math.max(0, Math.min(i, slides.length - 1))]);
      if (!lb || !im) return;
      lbImg.src = im.src; lbImg.alt = im.alt;
      if (lb.showModal) lb.showModal();
    }
    if (zoom) zoom.addEventListener('click', openLB);
    slides.forEach(function (s) { $('img', s).addEventListener('click', openLB); });
    document.addEventListener('click', function (ev) {
      if (ev.target.closest('[data-close-lightbox]') && lb) lb.close();
      if (ev.target.closest('[data-close-modal]')) {
        var m = ev.target.closest('dialog'); if (m) m.close();
      }
    });
    if (lb) lb.addEventListener('click', function (ev) { if (ev.target === lb) lb.close(); });

    var chart = $('#sizechart'), openChart = $('#open-sizechart');
    if (openChart && chart) {
      openChart.addEventListener('click', function () { if (chart.showModal) chart.showModal(); });
      chart.addEventListener('click', function (ev) { if (ev.target === chart) chart.close(); });
    }

    var picked = null;
    var hint = $('#pdp-hint');
    $$('.pdp-sizes .size').forEach(function (b) {
      b.addEventListener('click', function () {
        $$('.pdp-sizes .size').forEach(function (o) { o.setAttribute('aria-pressed', 'false'); });
        b.setAttribute('aria-pressed', 'true');
        picked = b.dataset.size;
        if (hint) hint.textContent = '';
      });
    });
    var addBtn = $('#pdp-add');
    if (addBtn) addBtn.addEventListener('click', function () {
      if (!picked) {
        if (hint) hint.textContent = 'Выберите размер';
        var first = $('.pdp-sizes .size:not([disabled])');
        if (first) first.focus();
        return;
      }
      var r = addToCart(addBtn.dataset.product, picked);
      if (hint) hint.textContent = r === 'max' ? 'Больше нет в наличии'
        : r ? 'Добавлено в корзину · размер ' + picked : 'Этого размера нет в наличии';
    });
  }

  /* ── корзина ──────────────────────────────────────── */
  function lineHTML(l, i) {
    var p = byId(l.id);
    if (!p) return '';
    return '<article class="cline">' +
      '<img src="' + p.thumb + '" alt="" width="104" height="104" loading="lazy">' +
      '<div><span class="cline__b">' + esc(p.brandName) + '</span>' +
      '<h3 class="cline__n"><a href="' + url(p.url) + '">' + esc(p.model) + '</a></h3>' +
      '<span class="cline__m">' + esc(p.colorName) + ' · размер ' + esc(l.size) + ' · арт. ' + esc(p.sku) + '</span>' +
      '<div class="qty"><button type="button" data-q="-1" data-i="' + i + '"' +
      (l.qty <= 1 ? ' disabled' : '') + ' aria-label="Уменьшить количество">−</button>' +
      '<span>' + l.qty + '</span>' +
      '<button type="button" data-q="1" data-i="' + i + '"' +
      (l.qty >= stockFor(p, l.size) ? ' disabled' : '') + ' aria-label="Увеличить количество">+</button></div>' +
      '<button class="cline__x" type="button" data-x="' + i + '">Удалить</button></div>' +
      '<div class="cline__p">' + money(p.price * l.qty) +
      (p.oldPrice ? '<span class="cline__old">' + money(p.oldPrice * l.qty) + '</span>' : '') +
      '</div></article>';
  }

  function renderCart() {
    var host = $('#cart-lines');
    if (!host) return;
    var summary = $('#cart-summary');
    if (!cart.length) {
      host.innerHTML = '<div class="empty"><h3>' + esc(host.dataset.emptyTitle) + '</h3>' +
        '<p>' + esc(host.dataset.emptyText) + '</p>' +
        '<a class="btn btn--ghost" href="' + url('catalog/') + '">В каталог</a></div>';
      if (summary) summary.hidden = true;
      return;
    }
    host.innerHTML = cart.map(lineHTML).join('');
    if (summary) summary.hidden = false;
    $$('[data-sum-goods]').forEach(function (el) { el.textContent = money(cartTotal()); });
    $$('[data-sum-total]').forEach(function (el) { el.textContent = money(cartTotal()); });
  }

  function renderCheckout() {
    var host = $('#checkout-lines');
    if (!host) return;
    if (!cart.length) {
      host.innerHTML = '<p class="summary__line">Корзина пуста</p>';
    } else {
      host.innerHTML = cart.map(function (l) {
        var p = byId(l.id);
        return '<div class="summary__line"><span>' + esc(p.brandName) + ' ' + esc(p.model) +
          ' · ' + esc(l.size) + ' · ' + l.qty + ' шт.</span><b>' + money(p.price * l.qty) + '</b></div>';
      }).join('');
    }
    $$('[data-sum-goods]').forEach(function (el) { el.textContent = money(cartTotal()); });
    $$('[data-sum-total]').forEach(function (el) { el.textContent = money(cartTotal()); });
  }

  document.addEventListener('click', function (ev) {
    var q = ev.target.closest('[data-q]');
    if (q) {
      var i = Number(q.dataset.i), d = Number(q.dataset.q), l = cart[i];
      if (!l) return;
      var p = byId(l.id);
      var next = l.qty + d;
      if (next < 1 || next > stockFor(p, l.size)) return;
      l.qty = next; saveCart(); return;
    }
    var x = ev.target.closest('[data-x]');
    if (x) { cart.splice(Number(x.dataset.i), 1); saveCart(); }
  });

  function renderWishlist() {
    var host = $('#wish-grid');
    if (!host) return;
    var items = wish.map(byId).filter(Boolean);
    if (!items.length) {
      host.innerHTML = '<div class="empty"><h3>' + esc(host.dataset.emptyTitle) + '</h3>' +
        '<p>' + esc(host.dataset.emptyText) + '</p>' +
        '<a class="btn btn--ghost" href="' + url('catalog/') + '">В каталог</a></div>';
      return;
    }
    host.innerHTML = '<div class="pgrid">' + items.map(cardHTML).join('') + '</div>';
    paintWishButtons();
  }

  /* ── формы ────────────────────────────────────────── */
  function say(form, text, ok) {
    var box = $('.formmsg', form);
    if (!box) return;
    box.hidden = false;
    box.textContent = text;
    box.className = 'formmsg ' + (ok ? 'is-ok' : 'is-err');
  }

  function collect(form) {
    var d = {};
    $$('input,textarea,select', form).forEach(function (el) {
      if (!el.name) return;
      if (el.type === 'radio' || el.type === 'checkbox') { if (el.checked) d[el.name] = el.value || 'да'; }
      else d[el.name] = el.value;
    });
    return d;
  }

  function send(form, subject, data) {
    if (CFG.formEndpoint) {
      fetch(CFG.formEndpoint, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ subject: subject, data: data })
      }).then(function (r) {
        if (r.ok) { say(form, 'Заявка отправлена. Ответим в течение рабочего дня.', true); form.reset(); }
        else say(form, 'Не удалось отправить. Попробуйте ещё раз или свяжитесь с нами напрямую.', false);
      }).catch(function () {
        say(form, 'Не удалось отправить. Проверьте соединение или свяжитесь с нами напрямую.', false);
      });
      return;
    }
    if (CFG.email) {
      var body = Object.keys(data).map(function (k) { return k + ': ' + data[k]; }).join('\n');
      location.href = 'mailto:' + CFG.email + '?subject=' + encodeURIComponent(subject) +
        '&body=' + encodeURIComponent(body);
      say(form, 'Открывается почтовая программа — отправьте письмо, чтобы мы получили заявку.', true);
      return;
    }
    say(form, 'Отправка заявок ещё не настроена. Свяжитесь с нами по контактам на сайте.', false);
  }

  $$('[data-form]').forEach(function (form) {
    form.addEventListener('submit', function (ev) {
      ev.preventDefault();
      if (!form.reportValidity()) return;
      var kind = form.dataset.form;
      var titles = {
        newsletter: 'Подписка на рассылку', wholesale: 'Заявка на оптовое сотрудничество',
        contact: 'Обращение с сайта', 'order-status': 'Запрос статуса заказа'
      };
      send(form, titles[kind] || 'Заявка с сайта', collect(form));
    });
  });

  var checkout = $('#checkout-form');
  if (checkout) {
    var addr = $('#addr-block');
    $$('input[name="delivery"]', checkout).forEach(function (r) {
      r.addEventListener('change', function () {
        var courier = r.value === 'courier';
        var street = $('#co-addr');
        if (street) street.required = courier;
        var lbl = addr ? $('label[for="co-addr"]', addr) : null;
        if (lbl) lbl.textContent = courier ? 'Адрес' : 'Адрес пункта выдачи';
      });
    });
    checkout.addEventListener('submit', function (ev) {
      ev.preventDefault();
      if (!cart.length) { say(checkout, 'Корзина пуста — добавьте товар перед оформлением.', false); return; }
      if (!checkout.reportValidity()) return;
      var d = collect(checkout);
      d.order = cart.map(function (l) {
        var p = byId(l.id);
        return p.brandName + ' ' + p.model + ' / ' + p.colorName + ' / размер ' + l.size +
          ' / ' + l.qty + ' шт. / арт. ' + p.sku;
      }).join('\n');
      d.total = money(cartTotal());
      send(checkout, 'Заказ с сайта на ' + money(cartTotal()), d);
    });
  }

  /* ── параллакс витрины на главной ─────────────────── */
  var scene = $('.scene');
  if (scene && !calm) {
    var pending = false, mx = 0, my = 0;
    var applyP = function () {
      pending = false;
      scene.style.setProperty('--px', mx.toFixed(1) + 'px');
      scene.style.setProperty('--py', my.toFixed(1) + 'px');
    };
    window.addEventListener('pointermove', function (ev) {
      if (ev.pointerType === 'touch') return;
      mx = (ev.clientX / window.innerWidth - 0.5) * -80;
      my = (ev.clientY / window.innerHeight - 0.5) * -50;
      if (!pending) { pending = true; requestAnimationFrame(applyP); }
    }, { passive: true });
  }

  paintBadges();
  paintWishButtons();
  renderCart();
  renderCheckout();
  renderWishlist();

  window.addEventListener('storage', function (ev) {
    if (ev.key === CART_KEY) { cart = read(CART_KEY); paintBadges(); renderCart(); renderCheckout(); }
    if (ev.key === WISH_KEY) { wish = read(WISH_KEY); paintBadges(); paintWishButtons(); renderWishlist(); }
  });
})();
