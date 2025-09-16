// Drawer / Hamburguesa y pequeñas ayudas responsive
(function (){
    const sidebar  = document.getElementById('sidebar');
    const burger   = document.getElementById('burgerBtn');
    const backdrop = document.getElementById('backdrop');
    if (!sidebar || !burger || !backdrop) return;
  
    function toggleDrawer(open){
      const willOpen = (typeof open === 'boolean') ? open : !sidebar.classList.contains('open');
      sidebar.classList.toggle('open', willOpen);
      backdrop.hidden = !willOpen;
      burger.setAttribute('aria-expanded', String(willOpen));
      document.documentElement.classList.toggle('no-scroll', willOpen);
    }
  
    burger.addEventListener('click', () => toggleDrawer());
    backdrop.addEventListener('click', () => toggleDrawer(false));
    window.addEventListener('keydown', (e)=>{ if(e.key==='Escape') toggleDrawer(false); });
    window.matchMedia('(min-width:1024px)').addEventListener('change', e => { if (e.matches) toggleDrawer(false); });
  
    // Cierra al navegar en móvil
    sidebar.addEventListener('click', (e)=>{
      if (window.matchMedia('(max-width:1023px)').matches && e.target.closest('a')) toggleDrawer(false);
    });
  
    // Marca link activo
    const here = window.location.pathname.replace(/\/$/, '');
    document.querySelectorAll('.sidebar-nav a').forEach(a=>{
      const href = a.getAttribute('href')?.replace(/\/$/, '');
      if (href && (here === href || (here.startsWith(href) && href !== '/'))) a.classList.add('is-active');
    });
  })();
  