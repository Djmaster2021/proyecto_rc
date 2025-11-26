(() => {
  'use strict';
  const ready = (fn) => (document.readyState === 'loading')
    ? document.addEventListener('DOMContentLoaded', fn, { once:true })
    : fn();

  ready(() => {
    /* ===== Parallax simple (ya lo tenías) ===== */
    const layers = Array.from(document.querySelectorAll('[data-plx-speed]'));
    function updateParallax(){
      const y = window.scrollY || 0;
      for (const el of layers){
        const speed = parseFloat(el.getAttribute('data-plx-speed'))||0.2;
        el.style.transform = `translate3d(0, ${-(y*speed)}px, 0)`;
      }
    }
    window.addEventListener('scroll', () => requestAnimationFrame(updateParallax), {passive:true});
    window.addEventListener('resize', () => requestAnimationFrame(updateParallax));
    updateParallax();

    /* ===== Hamburguesa accesible (ya lo tenías) ===== */
    const burger = document.getElementById('burger');
    const panel  = document.getElementById('mobile-panel');
    if (burger && panel){
      burger.addEventListener('click', () => {
        const open = burger.getAttribute('aria-expanded') === 'true';
        burger.setAttribute('aria-expanded', String(!open));
        panel.style.display = open ? 'none' : 'block';
      });
    }

    /* ===== Header glass → solid al hacer scroll ===== */
    const header = document.querySelector('.header');
    const onScrollHeader = () => {
      const solid = window.scrollY > 24;
      header?.classList.toggle('header--solid', solid);
      header?.classList.toggle('header--glass', !solid);
    };
    window.addEventListener('scroll', onScrollHeader, {passive:true});
    onScrollHeader();

    /* ===== Highlighter de navegación por sección ===== */
    const links = Array.from(document.querySelectorAll('[data-section]'));
    const sections = ['inicio','servicios','pagos','contacto']
      .map(id => document.getElementById(id))
      .filter(Boolean);

    const activate = (id) => {
      for (const a of links){
        const match = a.getAttribute('data-section') === id;
        a.classList.toggle('active', match);
        if (match) a.setAttribute('aria-current','page'); else a.removeAttribute('aria-current');
      }
    };

    // IntersectionObserver para detectar sección visible
    const io = new IntersectionObserver((entries) => {
      entries.forEach(e => { if (e.isIntersecting) activate(e.target.id); });
    }, { rootMargin: '-40% 0px -55% 0px', threshold: 0.01 });

    sections.forEach(s => io.observe(s));

    // Enlace manual (hash) también activa
    window.addEventListener('hashchange', () => {
      const id = (location.hash || '#inicio').replace('#','');
      activate(id);
    });
  });
})();

// Scroll suave si no lo tienes
if ('scrollBehavior' in document.documentElement.style === false) {
  // polyfill simple
}
// Navbar shrink
const nav=document.querySelector('.navbar');
if(nav){
  const onScroll=()=> nav.classList.toggle('navbar-blur', window.scrollY>8);
  window.addEventListener('scroll', onScroll, {passive:true}); onScroll();
}
