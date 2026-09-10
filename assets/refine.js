/* Лёгкий параллакс витрины: точка схода следует за курсором.
   При prefers-reduced-motion не подключается. */
(function () {
  'use strict';
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  var scene = document.querySelector('.scene');
  if (!scene) return;
  var pending = false, mx = 0, my = 0;

  function apply() {
    pending = false;
    scene.style.setProperty('--px', mx.toFixed(1) + 'px');
    scene.style.setProperty('--py', my.toFixed(1) + 'px');
  }
  window.addEventListener('pointermove', function (e) {
    if (e.pointerType === 'touch') return;
    mx = (e.clientX / window.innerWidth - 0.5) * -80;
    my = (e.clientY / window.innerHeight - 0.5) * -50;
    if (!pending) { pending = true; requestAnimationFrame(apply); }
  }, { passive: true });
  window.addEventListener('pointerleave', function () { mx = 0; my = 0; apply(); }, { passive: true });
})();
