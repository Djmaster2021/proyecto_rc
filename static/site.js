// ===== site.js mínimo/seguro =====
(() => {
  'use strict';
  const ready = (fn) => (document.readyState === 'loading')
    ? document.addEventListener('DOMContentLoaded', fn, { once:true })
    : fn();

  ready(() => {
    // Parallax simple (sin dependencias)
    const layers = Array.from(document.querySelectorAll('[data-plx-speed]'));
    function update(){
      const y = window.scrollY || 0;
      for (const el of layers){
        const speed = parseFloat(el.getAttribute('data-plx-speed'))||0.2;
        el.style.transform = `translate3d(0, ${-(y*speed)}px, 0)`;
      }
    }
    window.addEventListener('scroll', () => requestAnimationFrame(update), {passive:true});
    window.addEventListener('resize', () => requestAnimationFrame(update));
    update();
  });
})();
