
// ======================================================================
// 1) Tema claro/oscuro del LOGIN (radios #t-light / #t-dark)
//    * Aplica sobre <html data-theme="light|dark">
//    * Usa localStorage: "rc:theme"
// ======================================================================
(() => {
  const LIGHT = "light";
  const DARK = "dark";

  const $light = document.getElementById("t-light");
  const $dark = document.getElementById("t-dark");

  const saved = localStorage.getItem("rc:theme");
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  const initial = saved || (prefersDark ? DARK : LIGHT);

  // Estado inicial de los radios según preferencia
  if (initial === DARK && $dark) $dark.checked = true;
  if (initial === LIGHT && $light) $light.checked = true;

  function applyTheme() {
    const theme = $dark?.checked ? DARK : LIGHT;
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("rc:theme", theme);
  }

  // Listeners en los radios
  $light?.addEventListener("change", applyTheme);
  $dark?.addEventListener("change", applyTheme);

  // Aplicar al cargar
  applyTheme();
})();

// ======================================================================
// 2) Inicializaciones al cargar el DOM
// ======================================================================

document.addEventListener("DOMContentLoaded", () => {
  setupRoleToggleAccessibility();
  setupPasswordToggle();
  setupRecoveryScreens();
  setupAuthPageHelpers();
});

// ======================================================================
// 2.1) Accesibilidad: Enter/Espacio en selector de rol (.role-toggle)
// ======================================================================
function setupRoleToggleAccessibility() {
  const labels = document.querySelectorAll(".role-toggle label");
  if (!labels.length) return;

  labels.forEach((label) => {
    label.setAttribute("tabindex", "0");
    label.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        const id = label.getAttribute("for");
        const input = id ? document.getElementById(id) : null;
        if (input) {
          input.checked = true;
          // Disparamos el change por si hay lógica adicional
          input.dispatchEvent(new Event("change", { bubbles: true }));
        }
      }
    });
  });
}

// ======================================================================
// 2.2) Ojo para mostrar/ocultar contraseña en el LOGIN
//      - Usa:
//          #togglePassword (botón)
//          #id_password   (input password)
//          #eye-open      (icono mostrar)
//          #eye-closed    (icono ocultar)
// ======================================================================
function setupPasswordToggle() {
  const toggleBtn = document.getElementById("togglePassword");
  const passwordInput = document.getElementById("id_password");
  const eyeOpen = document.getElementById("eye-open");
  const eyeClosed = document.getElementById("eye-closed");

  if (!toggleBtn || !passwordInput) return;

  function setState(isVisible) {
    passwordInput.type = isVisible ? "text" : "password";

    if (eyeOpen && eyeClosed) {
      eyeOpen.style.display = isVisible ? "none" : "block";
      eyeClosed.style.display = isVisible ? "block" : "none";
    }

    toggleBtn.setAttribute(
      "aria-label",
      isVisible ? "Ocultar contraseña" : "Mostrar contraseña"
    );
  }

  toggleBtn.addEventListener("click", () => {
    const isHidden = passwordInput.type === "password";
    setState(isHidden);
  });
}

// ======================================================================
// 2.3) Pantallas de RECUPERACIÓN (rc-auth-body)
//      - Solo corre si <body> tiene la clase .rc-auth-body
//      - Tema Oscuro/Claro con #authThemeToggle
//      - Botón "Enviando..." al mandar el formulario
// ======================================================================
function setupRecoveryScreens() {
  const body = document.body;
  if (!body.classList.contains("rc-auth-body")) return;

  const STORAGE_KEY = "rc-auth-theme";
  const toggle = document.getElementById("authThemeToggle");
  const form = document.querySelector(".rc-auth-form");
  const submitBtn = document.getElementById("rc-submit-btn");

  // ---- Tema claro/oscuro para reset ----
  function applyAuthTheme(theme) {
    if (theme === "light") {
      body.classList.add("rc-theme--light");
    } else {
      body.classList.remove("rc-theme--light");
      theme = "dark";
    }

    if (toggle) {
      const label = toggle.querySelector("span") || toggle;
      label.textContent = theme === "light" ? "Claro" : "Oscuro";
    }
  }

  let currentTheme = localStorage.getItem(STORAGE_KEY) || "dark";
  applyAuthTheme(currentTheme);

  if (toggle) {
    toggle.addEventListener("click", () => {
      currentTheme = currentTheme === "dark" ? "light" : "dark";
      localStorage.setItem(STORAGE_KEY, currentTheme);
      applyAuthTheme(currentTheme);
    });
  }

  // ---- Estado "Enviando..." en el botón ----
  if (form && submitBtn) {
    form.addEventListener("submit", () => {
      submitBtn.classList.add("is-loading");
      submitBtn.textContent = "Enviando...";
    });
  }
}

// ======================================================================
// 2.4) RC Auth / Password Reset helpers
//      - Aplica a cualquier página que tenga .rc-auth-page
//      - Hace focus en el primer input (email o password)
// ======================================================================
function setupAuthPageHelpers() {
  const page = document.querySelector(".rc-auth-page");
  if (!page) return;

  const firstInput = page.querySelector(
    "input[type='email'], input[type='password']"
  );
  if (firstInput) {
    try {
      firstInput.focus();
    } catch (e) {
      console.warn("No se pudo hacer focus en el input:", e);
    }
  }
}
