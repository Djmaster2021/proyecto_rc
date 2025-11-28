// ======================================================================
// 1) Tema claro/oscuro del LOGIN (radios #t-light / #t-dark)
// ======================================================================
(() => {
  const LIGHT = "light";
  const DARK = "dark";
  const $light = document.getElementById("t-light");
  const $dark = document.getElementById("t-dark");

  const saved = localStorage.getItem("rc:theme");
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  const initial = saved || (prefersDark ? DARK : LIGHT);

  if (initial === DARK && $dark) $dark.checked = true;
  if (initial === LIGHT && $light) $light.checked = true;

  function applyTheme() {
    const theme = $dark?.checked ? DARK : LIGHT;
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("rc:theme", theme);
  }

  $light?.addEventListener("change", applyTheme);
  $dark?.addEventListener("change", applyTheme);
  applyTheme();
})();

// ======================================================================
// 2) Accesibilidad: Enter/Espacio en selector de rol (.role-toggle)
// ======================================================================
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".role-toggle label").forEach((label) => {
    label.setAttribute("tabindex", "0");
    label.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        const id = label.getAttribute("for");
        const input = document.getElementById(id);
        if (input) {
          input.checked = true;
          input.dispatchEvent(new Event("change", { bubbles: true }));
        }
      }
    });
  });
});

// ======================================================================
// 3) Ojo para mostrar/ocultar contraseña en el LOGIN
// ======================================================================
document.addEventListener("DOMContentLoaded", () => {
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
});

// ======================================================================
// 4) Pantallas de RECUPERACIÓN (rc-auth-body)
//    - Tema Oscuro/Claro con botón #authThemeToggle
//    - Botón "Enviando..." al mandar el formulario
// ======================================================================
document.addEventListener("DOMContentLoaded", () => {
  const body = document.body;
  if (!body.classList.contains("rc-auth-body")) return; // solo en reset / flows auth nuevos

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
});

// ===============================
// RC Auth / Password Reset helpers
// ===============================

document.addEventListener("DOMContentLoaded", () => {
  const page = document.querySelector(".rc-auth-page");

  if (!page) return;

  // Log simple para debug
  console.log("RC Auth page:", page.className);

  // Autofocus en el primer input si existe
  const firstInput = page.querySelector("input[type='email'], input[type='password']");
  if (firstInput) {
      try {
          firstInput.focus();
      } catch (e) {
          console.warn("No se pudo hacer focus en el input:", e);
      }
  }
});
