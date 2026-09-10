/* ФОРМА — поведение витрины.
   Состояние корзины хранится локально в браузере. Оплата и отправка заказа не выполняются. */
(function () {
  'use strict';

  var P = window.FORMA_PRODUCTS || [];
  var CAT = window.FORMA_CATEGORIES || {};
  var img = window.formaImg;
  var KEY = 'forma.cart.v1';
  var calm = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var byId = function (id) { return P.filter(function (p) { return p.id === id; })[0]; };
  var rub = function (n) { return n.toLocaleString('ru-RU') + ' ₽'; };

  /* ── Корзина ─────────────────────────────────────── */
  function read() {
    try { return JSON.parse(localStorage.getItem(KEY)) || []; }
    catch (e) { return []; }
  }
  function write(c) {
    try { localStorage.setItem(KEY, JSON.stringify(c)); } catch (e) {}
    paint();
  }
  function count() { return read().reduce(function (n, l) { return n + l.qty; }, 0); }
  function total() {
    return read().reduce(function (n, l) {
      var p = byId(l.id);
      return n + (p ? p.price * l.qty : 0);
    }, 0);
  }

  function add(id, size) {
    var c = read();
    var hit = c.filter(function (l) { return l.id === id && l.size === size; })[0];
    if (hit) { hit.qty += 1; } else { c.push({ id: id, size: size, qty: 1 }); }
    write(c);
    $$('.cart-count').forEach(function (el) {
      el.classList.remove('is-bumped');
      void el.offsetWidth;
      el.classList.add('is-bumped');
    });
  }
  function setQty(i, d) {
    var c = read();
    if (!c[i]) return;
    c[i].qty += d;
    if (c[i].qty < 1) c.splice(i, 1);
    write(c);
  }
  function drop(i) { var c = read(); c.splice(i, 1); write(c); }

  /* ── Отрисовка корзины ───────────────────────────── */
  function paint() {
    var n = count();
    $$('.cart-count').forEach(function (el) { el.textContent = n; });

    var boxes = $$('[data-cart-lines]');
    if (!boxes.length) return;
    var c = read();

    boxes.forEach(function (box) {
      if (!c.length) {
        box.innerHTML =
          '<div class="empty">' +
          '<svg aria-hidden="true"><use href="#i-tread"></use></svg>' +
          '<p class="h-sm">Здесь пока пусто</p>' +
          '<p>Выберите размер на карточке товара, чтобы добавить пару.</p>' +
          '<a class="btn btn--ghost" href="catalog.html">В каталог</a>' +
          '</div>';
        return;
      }
      box.innerHTML = c.map(function (l, i) {
        var p = byId(l.id);
        if (!p) return '';
        return '<article class="line">' +
          '<img src="' + img(p.img, 200, 200) + '" alt="" loading="lazy" width="74" height="74">' +
          '<div>' +
            '<h3 class="line__t">' + p.name + '</h3>' +
            '<span class="line__m">Размер ' + l.size + ' · ' + CAT[p.category] + '</span>' +
            '<span class="line__p">' + rub(p.price * l.qty) + '</span>' +
            '<div class="qty">' +
              '<button type="button" data-q="-1" data-i="' + i + '" aria-label="Убрать одну пару ' + p.name + '">−</button>' +
              '<span>' + l.qty + '</span>' +
              '<button type="button" data-q="1" data-i="' + i + '" aria-label="Добавить одну пару ' + p.name + '">+</button>' +
            '</div>' +
          '</div>' +
          '<button class="line__x" type="button" data-x="' + i + '" aria-label="Удалить ' + p.name + ' размер ' + l.size + ' из корзины">' +
            '<svg aria-hidden="true"><use href="#i-x"></use></svg>' +
          '</button>' +
        '</article>';
      }).join('');
    });

    $$('[data-cart-total]').forEach(function (el) { el.textContent = rub(total()); });
    $$('[data-cart-n]').forEach(function (el) { el.textContent = n; });
    $$('[data-cart-empty-hide]').forEach(function (el) { el.hidden = !c.length ? true : false; });
  }

  document.addEventListener('click', function (e) {
    var q = e.target.closest('[data-q]');
    if (q) { setQty(+q.dataset.i, +q.dataset.q); return; }
    var x = e.target.closest('[data-x]');
    if (x) { drop(+x.dataset.x); return; }
  });

  /* ── Выдвижная корзина ───────────────────────────── */
  var scrim = $('#cart');
  var lastFocus = null;
  function focusable() {
    if (!scrim) return [];
    return $$('a[href],button:not([disabled]),input,[tabindex]:not([tabindex="-1"])', scrim)
      .filter(function (el) { return el.offsetParent !== null; });
  }
  function openCart() {
    if (!scrim) return;
    lastFocus = document.activeElement;
    scrim.classList.add('is-open');
    scrim.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
    // элемент становится фокусируемым только после того, как снялся visibility:hidden
    requestAnimationFrame(function () {
      requestAnimationFrame(function () {
        var c = $('#cart-close');
        if (c) c.focus();
      });
    });
  }
  function closeCart() {
    if (!scrim) return;
    scrim.classList.remove('is-open');
    scrim.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }
  $$('[data-open-cart]').forEach(function (b) {
    b.addEventListener('click', function (e) { e.preventDefault(); openCart(); });
  });
  if (scrim) {
    scrim.addEventListener('click', function (e) { if (e.target === scrim) closeCart(); });
    var cl = $('#cart-close');
    if (cl) cl.addEventListener('click', closeCart);
  }
  document.addEventListener('keydown', function (e) {
    if (!scrim || !scrim.classList.contains('is-open')) return;
    if (e.key === 'Escape') { closeCart(); return; }
    if (e.key !== 'Tab') return;
    var f = focusable();
    if (!f.length) return;
    var first = f[0], last = f[f.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  });

  /* ── Карточка товара ─────────────────────────────── */
  function card(p) {
    var sizes = p.sizes.map(function (s) {
      var off = p.out.indexOf(s) > -1;
      return '<button class="size" type="button" role="button" aria-pressed="false" data-size="' + s + '"' +
        (off ? ' disabled aria-label="Размер ' + s + ' — нет в наличии"' : ' aria-label="Размер ' + s + '"') +
        '>' + s + '</button>';
    }).join('');

    return '<article class="card rise" data-product="' + p.id + '">' +
      '<div class="card__media">' +
        '<span class="card__cat">' + CAT[p.category] + '</span>' +
        '<img src="' + img(p.img, 700) + '" alt="Кроссовки ' + p.name + '" loading="lazy" width="700" height="700">' +
        '<svg class="card__print" viewBox="0 0 100 110" aria-hidden="true"><use href="#i-tread"></use></svg>' +
      '</div>' +
      '<div class="card__body">' +
        '<div class="card__row">' +
          '<h3 class="h-sm"><a href="product.html?id=' + p.id + '">' + p.name + '</a></h3>' +
          '<span class="price">' + rub(p.price) + '</span>' +
        '</div>' +
        '<p class="card__tag">' + p.tagline + '</p>' +
        '<dl class="spec">' +
          '<div><dt>Вес</dt><dd>' + p.spec.ves + '</dd></div>' +
          '<div><dt>Перепад</dt><dd>' + p.spec.perepad + '</dd></div>' +
        '</dl>' +
        '<div class="card__foot">' +
          '<div class="sizes" role="group" aria-label="Размер ' + p.name + '">' +
            '<span class="sizes__lbl">Размер</span>' + sizes +
          '</div>' +
          '<button class="btn btn--solid btn--wide" type="button" data-add="' + p.id + '">В корзину</button>' +
          '<span class="hint" role="status"></span>' +
        '</div>' +
      '</div>' +
    '</article>';
  }

  function wire(root) {
    $$('.card', root).forEach(function (c) {
      var hint = $('.hint', c);
      $$('.size', c).forEach(function (b) {
        b.addEventListener('click', function () {
          $$('.size', c).forEach(function (o) { o.setAttribute('aria-pressed', 'false'); });
          b.setAttribute('aria-pressed', 'true');
          if (hint) hint.textContent = '';
        });
      });
      var addBtn = $('[data-add]', c);
      if (!addBtn) return;
      addBtn.addEventListener('click', function () {
        var sel = $('.size[aria-pressed="true"]', c);
        if (!sel) {
          if (hint) hint.textContent = 'Сначала выберите размер';
          var first = $('.size:not([disabled])', c);
          if (first) first.focus();
          return;
        }
        add(addBtn.dataset.add, sel.dataset.size);
        if (hint) hint.textContent = 'Добавлено · размер ' + sel.dataset.size;
      });
    });
  }

  /* ── Сетки товаров ───────────────────────────────── */
  var grid = $('#grid');
  if (grid) {
    var limit = +(grid.dataset.limit || 0);
    var render = function (cat) {
      var list = cat === 'all' ? P : P.filter(function (p) { return p.category === cat; });
      if (limit) list = list.slice(0, limit);
      if (!list.length) {
        grid.innerHTML = '';
        grid.classList.remove('grid-products');
        grid.innerHTML = '<div class="empty"><svg aria-hidden="true"><use href="#i-tread"></use></svg>' +
          '<p class="h-sm">В этой подборке пока нет пар</p>' +
          '<p>Выберите другую категорию.</p></div>';
        return;
      }
      grid.classList.add('grid-products');
      grid.innerHTML = list.map(card).join('');
      wire(grid);
      observe(grid);
      var n = $('#found');
      if (n) n.textContent = list.length;
    };
    render(new URLSearchParams(location.search).get('cat') || 'all');

    $$('.chip[data-cat]').forEach(function (b) {
      var active = new URLSearchParams(location.search).get('cat') || 'all';
      b.setAttribute('aria-pressed', String(b.dataset.cat === active));
      b.addEventListener('click', function () {
        $$('.chip[data-cat]').forEach(function (o) { o.setAttribute('aria-pressed', 'false'); });
        b.setAttribute('aria-pressed', 'true');
        render(b.dataset.cat);
      });
    });
  }

  /* ── Подбор по бюджету ───────────────────────────── */
  var range = $('#budget-range');
  if (range) {
    var val = $('#budget-val');
    var cnt = $('#budget-n');
    var hits = $('#budget-hits');
    var tick = function () {
      var v = +range.value;
      var pct = ((v - range.min) / (range.max - range.min)) * 100;
      range.style.setProperty('--fill', pct + '%');
      if (val) val.textContent = rub(v);
      var list = P.filter(function (p) { return p.price <= v; })
                  .sort(function (a, b) { return b.price - a.price; });
      if (cnt) cnt.textContent = list.length;
      if (hits) {
        hits.innerHTML = list.length
          ? list.map(function (p) {
              return '<a class="hit" href="product.html?id=' + p.id + '">' + p.name + ' <b>' + rub(p.price) + '</b></a>';
            }).join('')
          : '<span class="line__m">В этот бюджет пока не попадает ни одна пара. Поднимите сумму.</span>';
      }
    };
    range.addEventListener('input', tick);
    tick();
  }

  /* ── Страница товара ─────────────────────────────── */
  var pdp = $('#pdp');
  if (pdp) {
    var id = new URLSearchParams(location.search).get('id');
    var p = byId(id) || P[0];

    document.title = p.name + ' — ФОРМА';
    $$('[data-f="name"]').forEach(function (e) { e.textContent = p.name; });
    $$('[data-f="price"]').forEach(function (e) { e.textContent = rub(p.price); });
    $$('[data-f="cat"]').forEach(function (e) { e.textContent = CAT[p.category]; });
    $$('[data-f="tagline"]').forEach(function (e) { e.textContent = p.tagline; });

    var hero = $('#pdp-img');
    if (hero) { hero.src = img(p.img, 1200); hero.alt = 'Кроссовки ' + p.name; }

    var spec = $('#pdp-spec');
    if (spec) {
      spec.innerHTML =
        '<div><dt>Вес пары</dt><dd>' + p.spec.ves + '</dd></div>' +
        '<div><dt>Высота стека</dt><dd>' + p.spec.stek + '</dd></div>' +
        '<div><dt>Перепад</dt><dd>' + p.spec.perepad + '</dd></div>' +
        '<div><dt>Верх</dt><dd>' + p.spec.verh + '</dd></div>';
    }

    var box = $('#pdp-sizes');
    if (box) {
      box.innerHTML = '<span class="sizes__lbl">Размер</span>' + p.sizes.map(function (s) {
        var off = p.out.indexOf(s) > -1;
        return '<button class="size" type="button" aria-pressed="false" data-size="' + s + '"' +
          (off ? ' disabled aria-label="Размер ' + s + ' — нет в наличии"' : ' aria-label="Размер ' + s + '"') +
          '>' + s + '</button>';
      }).join('');
      var hint2 = $('#pdp-hint');
      $$('.size', box).forEach(function (b) {
        b.addEventListener('click', function () {
          $$('.size', box).forEach(function (o) { o.setAttribute('aria-pressed', 'false'); });
          b.setAttribute('aria-pressed', 'true');
          if (hint2) hint2.textContent = '';
        });
      });
      var pb = $('#pdp-add');
      if (pb) pb.addEventListener('click', function () {
        var sel = $('.size[aria-pressed="true"]', box);
        if (!sel) {
          if (hint2) hint2.textContent = 'Сначала выберите размер';
          return;
        }
        add(p.id, sel.dataset.size);
        if (hint2) hint2.textContent = 'Добавлено · размер ' + sel.dataset.size;
        openCart();
      });
    }

    var also = $('#pdp-also');
    if (also) {
      var rest = P.filter(function (x) { return x.id !== p.id; }).slice(0, 4);
      also.innerHTML = rest.map(card).join('');
      wire(also);
      observe(also);
    }
  }

  /* ── Оформление ──────────────────────────────────── */
  var form = $('#order');
  if (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var out = $('#order-result');
      if (!out) return;
      out.hidden = false;
      out.textContent = 'Это дизайн-концепт: заказ не отправляется и оплата не проводится. Данные формы никуда не передаются.';
      out.focus();
    });
  }

  /* ── Появление при прокрутке ─────────────────────── */
  var io = null;
  function observe(root) {
    if (calm) { $$('.rise', root).forEach(function (el) { el.classList.add('is-in'); }); return; }
    if (!('IntersectionObserver' in window)) {
      $$('.rise', root).forEach(function (el) { el.classList.add('is-in'); });
      return;
    }
    if (!io) {
      io = new IntersectionObserver(function (entries) {
        entries.forEach(function (en, i) {
          if (!en.isIntersecting) return;
          var el = en.target;
          var sibs = Array.prototype.slice.call(el.parentNode.children).indexOf(el);
          el.style.transitionDelay = Math.min(sibs, 6) * 65 + 'ms';
          el.classList.add('is-in');
          io.unobserve(el);
        });
      }, { rootMargin: '0px 0px -8% 0px', threshold: .08 });
    }
    $$('.rise', root).forEach(function (el) {
      if (!el.classList.contains('is-in')) io.observe(el);
    });
  }
  observe(document);

  /* ── Липкая шапка ────────────────────────────────── */
  var nav = $('.nav');
  if (nav) {
    var stick = function () { nav.classList.toggle('is-stuck', window.scrollY > 24); };
    window.addEventListener('scroll', stick, { passive: true });
    stick();
  }

  /* ── Первый экран: след протектора ───────────────── */
  var trail = document.getElementById('trail');
  if (trail) {
    var N = 8;
    var html = '';
    for (var i = 0; i < N; i++) {
      var t = i / (N - 1);                       // 0 — ближний след, 1 — дальний
      var size = 22 - t * 17;                    // % ширины контейнера — уходит вглубь кадра
      var left = 6 + t * 56;                     // и вправо
      var bottom = 1 + t * 74;                   // и вверх
      var lean = (i % 2 ? 10 : -8) + t * 5;      // шаг то левой, то правой
      var op = (0.62 - t * 0.5).toFixed(3);
      html += '<svg class="step" viewBox="0 0 100 110" style="' +
        'width:' + size.toFixed(2) + '%;left:' + left.toFixed(1) + '%;bottom:' + bottom.toFixed(1) + '%;' +
        'transform:rotate(' + lean.toFixed(1) + 'deg)">' +
        '<use href="#i-tread"></use></svg>';
    }
    trail.innerHTML = html;
    var steps = $$('.step', trail);
    steps.forEach(function (s, i) {
      var op = (0.62 - (i / (N - 1)) * 0.5);
      if (calm) { s.style.opacity = op; return; }
      // шаги отпечатываются издалека к зрителю
      s.animate(
        [
          { opacity: 0, transform: s.style.transform + ' scale(.7)' },
          { opacity: op, transform: s.style.transform + ' scale(1)' }
        ],
        { duration: 540, delay: 340 + (N - 1 - i) * 125, fill: 'forwards', easing: 'cubic-bezier(.2,.8,.3,1)' }
      );
    });
  }

  /* ── Первый экран: подъём строк ──────────────────── */
  if (!calm) {
    $$('#hero-title .ln > span').forEach(function (s, i) {
      s.animate(
        [{ transform: 'translateY(105%)' }, { transform: 'translateY(0)' }],
        { duration: 760, delay: 90 + i * 110, fill: 'both', easing: 'cubic-bezier(.22,.61,.36,1)' }
      );
    });
    $$('[data-fade]').forEach(function (el, i) {
      el.animate(
        [{ opacity: 0, transform: 'translateY(14px)' }, { opacity: 1, transform: 'none' }],
        { duration: 620, delay: 420 + i * 110, fill: 'both', easing: 'cubic-bezier(.22,.61,.36,1)' }
      );
    });
  }

  paint();
})();
