// ===== Tema claro/oscuro con persistencia ==================================
(() => {
  const LIGHT = 'light', DARK = 'dark';
  const $light = document.getElementById('t-light');
  const $dark  = document.getElementById('t-dark');

  const saved = localStorage.getItem('rc:theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  const initial = saved || (prefersDark ? DARK : LIGHT);

  if (initial === DARK && $dark) $dark.checked = true;
  if (initial === LIGHT && $light) $light.checked = true;

  function applyTheme() {
    const theme = $dark?.checked ? DARK : LIGHT;
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('rc:theme', theme);
  }
  $light?.addEventListener('change', applyTheme);
  $dark?.addEventListener('change', applyTheme);
  applyTheme();
})();

// ===== Mostrar/ocultar contraseña ==========================================
(() => {
  const box = document.querySelector('.password-box');
  if (!box) return;
  const input = box.querySelector('input');
  const btn = box.querySelector('.eye');
  btn?.addEventListener('click', () => {
    const reveal = input.type === 'password';
    input.type = reveal ? 'text' : 'password';
    box.classList.toggle('show', reveal);
    input.focus();
  });
})();

// ===== Accesibilidad: Enter en chips de rol =================================
(() => {
  document.querySelectorAll('.role-chip').forEach(label => {
    label.setAttribute('tabindex', '0');
    label.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        const id = label.getAttribute('for');
        const input = document.getElementById(id);
        input.checked = true;
        input.dispatchEvent(new Event('change', { bubbles:true }));
      }
    });
  });
})();
