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

// ===== Accesibilidad: Enter en botones de rol =================================
(() => {
  // Actualizado para que coincida con la clase .role-toggle
  document.querySelectorAll('.role-toggle label').forEach(label => {
    label.setAttribute('tabindex', '0'); // Permite enfocar con Tab
    label.addEventListener('keydown', e => {
      // Activa el 'radio' al presionar Enter o Espacio
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        const id = label.getAttribute('for');
        const input = document.getElementById(id);
        if (input) {
          input.checked = true;
          // Dispara el evento change por si otro script depende de él
          input.dispatchEvent(new Event('change', { bubbles:true }));
        }
      }
    });
  });
})();

// =========================================================
// RC · Tema claro/oscuro para pantallas de recuperación
// =========================================================

document.addEventListener("DOMContentLoaded", () => {
  const body = document.body;
  const toggle = document.getElementById("authThemeToggle");
  if (!toggle || !body.classList.contains("rc-auth-body")) return;

  const STORAGE_KEY = "rc-auth-theme";

  function applyTheme(theme) {
    if (theme === "light") {
      body.classList.add("rc-theme--light");
    } else {
      body.classList.remove("rc-theme--light");
      theme = "dark";
    }

    const label = toggle.querySelector("span");
    if (label) {
      label.textContent = theme === "light" ? "Claro" : "Oscuro";
    }
  }

  let current = localStorage.getItem(STORAGE_KEY) || "dark";
  applyTheme(current);

  toggle.addEventListener("click", () => {
    current = current === "dark" ? "light" : "dark";
    localStorage.setItem(STORAGE_KEY, current);
    applyTheme(current);
  });
});

// Script para alternar visibilidad de contraseña
document.addEventListener('DOMContentLoaded', function() {
  const toggleBtn = document.getElementById('togglePassword');
  const passwordInput = document.getElementById('id_password');
  const eyeOpen = document.getElementById('eye-open');
  const eyeClosed = document.getElementById('eye-closed');

  if (toggleBtn && passwordInput) {
    toggleBtn.addEventListener('click', function() {
      // Verificar el tipo actual
      const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
      passwordInput.setAttribute('type', type);
      
      // Alternar iconos
      if (type === 'text') {
        eyeOpen.style.display = 'none';
        eyeClosed.style.display = 'block';
        toggleBtn.setAttribute('aria-label', 'Ocultar contraseña');
      } else {
        eyeOpen.style.display = 'block';
        eyeClosed.style.display = 'none';
        toggleBtn.setAttribute('aria-label', 'Mostrar contraseña');
      }
    });
  }
});

document.addEventListener("DOMContentLoaded", () => {
  const pwdInput = document.getElementById("id_password");
  const toggle = document.getElementById("togglePassword");
  const eyeOpen = document.getElementById("eye-open");
  const eyeClosed = document.getElementById("eye-closed");

  if (pwdInput && toggle) {
    toggle.addEventListener("click", () => {
      const isHidden = pwdInput.type === "password";
      pwdInput.type = isHidden ? "text" : "password";
      eyeOpen.style.display = isHidden ? "none" : "block";
      eyeClosed.style.display = isHidden ? "block" : "none";
    });
  }

  // Tema claro/oscuro
  const tLight = document.getElementById("t-light");
  const tDark = document.getElementById("t-dark");
  const html = document.documentElement;

  function setTheme(theme) {
    html.setAttribute("data-theme", theme);
  }

  tLight?.addEventListener("change", () => setTheme("light"));
  tDark?.addEventListener("change", () => setTheme("dark"));
});

  
