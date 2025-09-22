(() => {
  'use strict';

  const ready = (fn) => (document.readyState === 'loading')
    ? document.addEventListener('DOMContentLoaded', fn, { once: true })
    : fn();

  ready(() => {
    const navbar = document.querySelector('.rc-navbar');
    const burger = document.getElementById('burger');
    const mobilePanel = document.getElementById('mobile-panel');

    // 1. Efecto de desenfoque en la Navbar al hacer scroll
    const handleScroll = () => {
      if (window.scrollY > 20) {
        navbar?.classList.add('is-scrolled');
      } else {
        navbar?.classList.remove('is-scrolled');
      }
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    handleScroll();

    // 2. Funcionalidad del Menú Hamburguesa
    if (burger && mobilePanel) {
      const toggleMenu = () => {
        const isOpen = mobilePanel.classList.toggle('is-open');
        burger.classList.toggle('is-active', isOpen);
        burger.setAttribute('aria-expanded', String(isOpen));
        burger.innerHTML = isOpen ? '<i class="ph ph-x"></i>' : '<i class="ph ph-list"></i>';
        document.body.style.overflow = isOpen ? 'hidden' : '';
      };
      
      burger.addEventListener('click', toggleMenu);

      mobilePanel.addEventListener('click', (e) => {
        if (e.target.tagName === 'A') {
          toggleMenu();
        }
      });
    }
    
    // 3. Animaciones de revelado de elementos al hacer scroll
    const revealElements = document.querySelectorAll('.reveal');
    if ("IntersectionObserver" in window) {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add('in');
          }
        });
      }, { threshold: 0.1 });

      revealElements.forEach(el => observer.observe(el));
    } else {
      // Si el navegador es muy antiguo, simplemente muestra los elementos
      revealElements.forEach(el => el.classList.add('in'));
    }
  });
})();