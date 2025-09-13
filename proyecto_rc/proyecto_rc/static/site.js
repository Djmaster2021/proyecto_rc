// ====== Global scripts (site.js) ======
// Cierra modales con [data-close] o con tecla ESC
document.addEventListener('click', (e) => {
  const btn = e.target.closest('[data-close]');
  if (!btn) return;
  const modal = btn.closest('.modal');
  if (modal) modal.setAttribute('hidden', '');
});
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') document.querySelectorAll('.modal:not([hidden])').forEach(m => m.setAttribute('hidden', ''));
});
