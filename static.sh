#!/usr/bin/env bash
set -euo pipefail

# === Carpetas ===
mkdir -p static
mkdir -p paciente/static/paciente
mkdir -p dentista/static/dentista
mkdir -p accounts/static/accounts

# === Global: CSS/JS del sitio (landing + compartidos) ===
cat >static/site.css <<'EOF'
/* ====== Global styles (site.css) ====== */
:root {
  --bg: #0f1115;
  --fg: #e7e9ee;
  --muted: #a0a6b1;
  --primary: #62a0ff;
  --card: #161a22;
  --border: #232836;
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body {
  font-family: system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, "Helvetica Neue", Arial, "Noto Sans", "Apple Color Emoji", "Segoe UI Emoji";
  background: var(--bg);
  color: var(--fg);
  line-height: 1.5;
}
.container { width: min(1100px, 92%); margin: 2rem auto; }
a { color: var(--primary); text-decoration: none; }
a:hover { text-decoration: underline; }

.navbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: .9rem 1.2rem; border-bottom: 1px solid var(--border); background: #0d1016cc; backdrop-filter: blur(8px);
}
.navbar .brand { font-weight: 700; letter-spacing: .5px; color: var(--fg); }
.navbar .nav { list-style: none; display: flex; gap: 1rem; margin: 0; padding: 0; }
.navbar .nav a { padding: .4rem .6rem; border-radius: .6rem; }
.navbar .nav a:hover { background: var(--card); text-decoration: none; }

.site-footer { border-top: 1px solid var(--border); padding: 1rem; text-align: center; color: var(--muted); }

.section-head { margin-bottom: 1rem; border-bottom: 1px dashed var(--border); }
.section-head h2 { margin: 0 0 .6rem 0; }

.messages { display: grid; gap: .6rem; margin: 1rem 0; }
.msg { padding: .8rem 1rem; border-radius: .6rem; background: #1b2130; border: 1px solid var(--border); }
.msg.success { border-color: #2f9e44; }
.msg.error { border-color: #e03131; }
.msg.warning { border-color: #f08c00; }

.card {
  background: var(--card); border: 1px solid var(--border);
  border-radius: .8rem; overflow: hidden; margin: 1rem 0;
}
.card-head { padding: .9rem 1rem; border-bottom: 1px solid var(--border); font-weight: 600; }
.card-body { padding: 1rem; color: var(--fg); }
.card-foot { padding: .8rem 1rem; border-top: 1px solid var(--border); color: var(--muted); }

.breadcrumb { font-size: .95rem; color: var(--muted); margin-bottom: 1rem; }
.breadcrumb ol { margin: 0; padding: 0; list-style: none; display: flex; gap: .5rem; flex-wrap: wrap; }
.breadcrumb a { color: var(--muted); }
.hero { padding: 2.5rem 0; }
.hero h1 { margin: 0 0 .5rem 0; font-size: clamp(1.6rem, 3vw, 2.2rem); }
.hero p { margin: .3rem 0; color: var(--muted); }
button, .btn {
  background: var(--primary); color: #0b1020; border: none; padding: .6rem .9rem;
  border-radius: .6rem; font-weight: 600; cursor: pointer;
}
button:hover, .btn:hover { filter: brightness(1.05); }
EOF

cat >static/site.js <<'EOF'
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
EOF

# === Estáticos por app (placeholders) ===
cat >paciente/static/paciente/styles.css <<'EOF'
/* Styles específicos de la sección Paciente */
.table { width: 100%; border-collapse: collapse; }
.table th, .table td { padding: .6rem .8rem; border-bottom: 1px solid #232836; }
EOF

cat >paciente/static/paciente/app.js <<'EOF'
// JS específico de Paciente
console.log("Paciente UI listo");
EOF

cat >dentista/static/dentista/styles.css <<'EOF'
/* Styles específicos de la sección Dentista */
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 1rem; }
EOF

cat >dentista/static/dentista/app.js <<'EOF'
// JS específico de Dentista
console.log("Dentista UI listo");
EOF

cat >accounts/static/accounts/styles.css <<'EOF'
/* Styles específicos de Accounts (login/registro) */
.form { display: grid; gap: .8rem; max-width: 420px; }
.form label { font-size: .95rem; color: #a0a6b1; }
.form input { padding: .6rem .7rem; border-radius: .5rem; border: 1px solid #232836; background: #0f131b; color: #e7e9ee; }
EOF

cat >accounts/static/accounts/app.js <<'EOF'
// JS específico de Accounts
console.log("Accounts UI listo");
EOF

echo "✔ Estructura de estáticos creada."
echo "Asegúrate en settings.py de tener:"
echo "  STATIC_URL = 'static/'"
echo "  TEMPLATES[0]['DIRS'] = [BASE_DIR / 'templates']"
echo "Si quieres que Django sirva 'static/' global en dev:"
echo "  from pathlib import Path; BASE_DIR = Path(__file__).resolve().parent.parent"
echo "  STATICFILES_DIRS = [BASE_DIR / 'static']"
