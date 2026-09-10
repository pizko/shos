/* Единственный источник данных о товарах.
   Все модели, цены и характеристики — демонстрационные. */
window.FORMA_PRODUCTS = [
  {
    id: 'gorod-01', name: 'ГОРОД 01', price: 12500, category: 'city',
    tagline: 'Низкий силуэт для длинных городских переходов',
    spec: { ves: '284 г', stek: '28/20 мм', perepad: '8 мм', verh: 'Сетка + замша' },
    sizes: [40, 41, 42, 43, 44, 45],
    out: [40],
    img: 'photo-1606107557195-0e29a4b5b4aa'
  },
  {
    id: 'impuls', name: 'ИМПУЛЬС', price: 14900, category: 'run',
    tagline: 'Отзывчивая пена для темповых тренировок',
    spec: { ves: '241 г', stek: '34/26 мм', perepad: '8 мм', verh: 'Инженерная сетка' },
    sizes: [39, 40, 41, 42, 43, 44],
    out: [39, 44],
    img: 'photo-1542291026-7eec264c27ff'
  },
  {
    id: 'ritm', name: 'РИТМ', price: 8900, category: 'every',
    tagline: 'База гардероба: белый верх, плоская подошва',
    spec: { ves: '312 г', stek: '22/16 мм', perepad: '6 мм', verh: 'Гладкая кожа' },
    sizes: [36, 37, 38, 39, 40, 41, 42],
    out: [],
    img: 'photo-1551107696-a4b0c5a0d9a2'
  },
  {
    id: 'marshrut', name: 'МАРШРУТ', price: 16200, category: 'city',
    tagline: 'Плотный протектор для мокрого асфальта',
    spec: { ves: '336 г', stek: '30/22 мм', perepad: '8 мм', verh: 'Нейлон + резина' },
    sizes: [41, 42, 43, 44, 45, 46],
    out: [46],
    img: 'photo-1595950653106-6c9ebd614d3a'
  },
  {
    id: 'noch', name: 'НОЧЬ', price: 19400, category: 'run',
    tagline: 'Светоотражающий верх для тёмного времени',
    spec: { ves: '256 г', stek: '36/28 мм', perepad: '8 мм', verh: 'Сетка со светоотражением' },
    sizes: [40, 41, 42, 43, 44],
    out: [],
    img: 'photo-1608231387042-66d1773070a5'
  },
  {
    id: 'kvartal', name: 'КВАРТАЛ', price: 11300, category: 'every',
    tagline: 'Замша, скрытые швы, спокойная форма',
    spec: { ves: '298 г', stek: '24/18 мм', perepad: '6 мм', verh: 'Замша' },
    sizes: [38, 39, 40, 41, 42, 43],
    out: [38],
    img: 'photo-1525966222134-fcfa99b8ae77'
  },
  {
    id: 'razgon', name: 'РАЗГОН', price: 22800, category: 'run',
    tagline: 'Жёсткая пластина, максимальный возврат энергии',
    spec: { ves: '218 г', stek: '39/31 мм', perepad: '8 мм', verh: 'Ультралёгкая сетка' },
    sizes: [41, 42, 43, 44, 45],
    out: [45],
    img: 'photo-1539185441755-769473a23570'
  },
  {
    id: 'seryi-den', name: 'СЕРЫЙ ДЕНЬ', price: 9700, category: 'every',
    tagline: 'Монохром, который переживёт любой сезон',
    spec: { ves: '305 г', stek: '23/17 мм', perepad: '6 мм', verh: 'Плотный канвас' },
    sizes: [37, 38, 39, 40, 41, 42, 43],
    out: [],
    img: 'photo-1600185365483-26d7a4cc7519'
  }
];

window.FORMA_CATEGORIES = {
  city:  'Город',
  run:   'Бег',
  every: 'Каждый день'
};

window.formaImg = function (id, w, h) {
  return 'https://images.unsplash.com/' + id + '?auto=format&fit=crop&w=' + (w || 900) +
         (h ? '&h=' + h : '') + '&q=80';
};
