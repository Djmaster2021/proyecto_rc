/* ============================================================================
   app.js — PANEL DEL PACIENTE
   - Tema claro/oscuro, menú lateral móvil
   - Confirmaciones (SweetAlert2), contacto con el consultorio
   - Selector de horarios (agendar / reprogramar) usando /paciente/api/slots/
============================================================================ */
(function () {
  "use strict";

  var CFG = window.RC_PACIENTE || {};
  var lang = (window.location.pathname.indexOf("/en/") === 0 ? "en" : (document.body.dataset.lang || "es")).slice(0, 2);
  var EN = lang === "en";

  var STR = {
    loading: EN ? "Looking for available times…" : "Buscando horarios disponibles…",
    pickService: EN ? "Choose a treatment first." : "Primero elige un tratamiento.",
    pickDate: EN ? "Choose a date to see available times." : "Elige una fecha para ver los horarios.",
    noSlots: EN ? "No available times that day. Try another date." : "No hay horarios libres ese día. Prueba otra fecha.",
    noSundays: EN ? "We don't work on Sundays. Choose another date." : "No atendemos domingos. Elige otra fecha.",
    error: EN ? "Couldn't load times. Try again." : "No se pudieron cargar los horarios. Intenta de nuevo.",
    suggested: EN ? "Suggested" : "Sugerido",
    cancel: EN ? "Cancel" : "Cancelar",
    ok: EN ? "OK" : "Aceptar",
    confirm: EN ? "Confirm?" : "¿Confirmar?",
    done: EN ? "Done!" : "¡Listo!",
    errTitle: EN ? "Error" : "Error",
    // Cancelar cita
    cancelTitle: EN ? "Cancel this appointment?" : "¿Cancelar esta cita?",
    cancelText: EN
      ? "You can cancel <b>once per month</b>. Please do it at least <b>1 day in advance</b>.<br><br><b>You will lose your spot.</b>"
      : "Solo puedes cancelar <b>una vez al mes</b>. Hazlo con al menos <b>1 día de anticipación</b>.<br><br><b>Perderás tu lugar en la agenda.</b>",
    cancelConfirm: EN ? "Yes, cancel" : "Sí, cancelar",
    keep: EN ? "Keep appointment" : "Conservar cita",
    // Reprogramar
    reprogLimitTitle: EN ? "Reschedule limit reached" : "Límite de reprogramación",
    reprogLimitText: EN
      ? "This appointment was already rescheduled. Contact the clinic for more changes."
      : "Esta cita ya fue reprogramada. Contacta al consultorio para más cambios.",
    reprogTitle: EN ? "Reschedule appointment?" : "¿Reprogramar la cita?",
    reprogText: EN
      ? "You can reschedule <b>only once</b> per appointment and once per month."
      : "Solo puedes reprogramar <b>una vez</b> por cita y una vez al mes.",
    reprogConfirm: EN ? "Continue" : "Continuar",
    // Contacto
    contactTitle: EN ? "Contact the clinic?" : "¿Contactar al consultorio?",
    contactText: EN
      ? "We'll send your name, email and phone so the clinic can get in touch with you."
      : "Enviaremos tu nombre, correo y teléfono para que el consultorio se comunique contigo.",
    contactConfirm: EN ? "Send request" : "Enviar solicitud",
    contactOk: EN ? "Request sent. The clinic will contact you soon." : "Solicitud enviada. El consultorio te contactará pronto.",
    contactFail: EN ? "Couldn't send the request. Try later." : "No se pudo enviar la solicitud. Intenta más tarde.",
  };

  var BRAND = "#00adc1";
  var DANGER = "#ef4444";
  var MUTED = "#64748b";

  /* ------------------------------------------------------------
     Utilidades
  ------------------------------------------------------------ */
  function getCookie(name) {
    var match = document.cookie.match(new RegExp("(?:^|; )" + name + "=([^;]*)"));
    return match ? decodeURIComponent(match[1]) : null;
  }

  function swal(opts) {
    if (typeof Swal === "undefined") {
      return Promise.resolve({ isConfirmed: window.confirm((opts.title || "") + "\n" + (opts.text || "")) });
    }
    return Swal.fire(Object.assign({ confirmButtonColor: BRAND, cancelButtonColor: MUTED, reverseButtons: true }, opts));
  }

  window.rcConfirmar = function (opts) {
    opts = opts || {};
    return swal({
      icon: opts.icon || "question",
      title: opts.title || STR.confirm,
      html: opts.text || "",
      showCancelButton: true,
      confirmButtonText: opts.confirmButton || STR.ok,
      cancelButtonText: opts.cancelButton || STR.cancel,
      confirmButtonColor: opts.confirmColor || BRAND,
    }).then(function (r) { return r.isConfirmed; });
  };

  /* ------------------------------------------------------------
     Tema claro / oscuro
  ------------------------------------------------------------ */
  var root = document.documentElement;
  var themeBtn = document.getElementById("theme-toggle");
  if (themeBtn) {
    themeBtn.addEventListener("click", function () {
      var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try { localStorage.setItem("paciente-theme", next); } catch (e) {}
    });
  }

  /* ------------------------------------------------------------
     Menú lateral (móvil)
  ------------------------------------------------------------ */
  var sidebar = document.getElementById("sidebar");
  var overlay = document.getElementById("sidebar-overlay");
  function setMenu(open) {
    if (!sidebar) return;
    sidebar.classList.toggle("open", open);
    if (overlay) overlay.classList.toggle("open", open);
  }
  var menuBtn = document.getElementById("menu-btn");
  var closeBtn = document.getElementById("sidebar-close");
  if (menuBtn) menuBtn.addEventListener("click", function () { setMenu(true); });
  if (closeBtn) closeBtn.addEventListener("click", function () { setMenu(false); });
  if (overlay) overlay.addEventListener("click", function () { setMenu(false); });

  /* ------------------------------------------------------------
     Formularios con confirmación: <form data-confirm-title="...">
  ------------------------------------------------------------ */
  document.querySelectorAll("form[data-confirm-title]").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      if (form.dataset.confirmed === "1") return;
      e.preventDefault();
      window.rcConfirmar({
        title: form.dataset.confirmTitle,
        text: form.dataset.confirmText,
        icon: form.dataset.confirmIcon,
        confirmButton: form.dataset.confirmButton,
        confirmColor: form.dataset.confirmColor,
      }).then(function (ok) {
        if (ok) { form.dataset.confirmed = "1"; form.submit(); }
      });
    });
  });

  /* ------------------------------------------------------------
     Contactar al consultorio
  ------------------------------------------------------------ */
  window.contactarDentista = function () {
    setMenu(false);
    window.rcConfirmar({
      icon: "question",
      title: STR.contactTitle,
      text: STR.contactText,
      confirmButton: STR.contactConfirm,
    }).then(function (ok) {
      if (!ok) return;
      fetch(CFG.contactUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": getCookie("csrftoken") },
        body: "{}",
        credentials: "same-origin",
      })
        .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, data: d }; }); })
        .then(function (res) {
          if (res.ok && res.data.status === "ok") {
            swal({ icon: "success", title: STR.done, text: STR.contactOk });
          } else {
            swal({ icon: "error", title: STR.errTitle, text: (res.data && res.data.msg) || STR.contactFail, confirmButtonColor: DANGER });
          }
        })
        .catch(function () {
          swal({ icon: "error", title: STR.errTitle, text: STR.contactFail, confirmButtonColor: DANGER });
        });
    });
  };

  /* ------------------------------------------------------------
     Pestañas: [data-tabs] con botones [data-tab="id"]
  ------------------------------------------------------------ */
  document.querySelectorAll("[data-tabs]").forEach(function (wrap) {
    var buttons = wrap.querySelectorAll("[data-tab]");
    buttons.forEach(function (btn) {
      btn.addEventListener("click", function () {
        buttons.forEach(function (b) {
          var active = b === btn;
          b.classList.toggle("active", active);
          b.setAttribute("aria-selected", active ? "true" : "false");
          var panel = document.getElementById(b.dataset.tab);
          if (panel) panel.hidden = !active;
        });
      });
    });
  });

  /* ------------------------------------------------------------
     Vista previa de foto de perfil
  ------------------------------------------------------------ */
  var fotoInput = document.getElementById("foto-input");
  if (fotoInput) {
    fotoInput.addEventListener("change", function () {
      var file = fotoInput.files && fotoInput.files[0];
      var preview = document.getElementById("foto-preview");
      if (!file || !preview) return;
      var reader = new FileReader();
      reader.onload = function (ev) {
        preview.innerHTML = "";
        var img = document.createElement("img");
        img.src = ev.target.result;
        img.alt = "";
        preview.appendChild(img);
      };
      reader.readAsDataURL(file);
      var quitar = document.getElementById("quitar-imagen");
      if (quitar) quitar.value = "0";
    });
  }

  /* ------------------------------------------------------------
     Selector de horarios
     <form data-slot-picker>
       servicio: input[name=servicio] (radio o hidden)
       fecha:    input[data-fecha]
       horas:    [data-slots]   (contenedor de botones)
       hora:     input[name=hora] (hidden)
       enviar:   [data-submit]
       resumen opcional: [data-sum="servicio|precio|duracion|doctor|fecha|hora"]
  ------------------------------------------------------------ */
  function SlotPicker(form) {
    this.form = form;
    this.fecha = form.querySelector("[data-fecha]");
    this.slots = form.querySelector("[data-slots]");
    this.hora = form.querySelector("input[name=hora]");
    this.submit = form.querySelector("[data-submit]");
    this.url = form.dataset.slotsUrl || CFG.slotsUrl;
    this.reqId = 0;

    var self = this;
    var today = new Date();
    var max = new Date();
    max.setDate(max.getDate() + 60);
    if (this.fecha) {
      this.fecha.min = toISO(today);
      this.fecha.max = toISO(max);
      this.fecha.addEventListener("change", function () { self.load(); });
    }
    form.querySelectorAll("input[name=servicio]").forEach(function (inp) {
      inp.addEventListener("change", function () { self.updateSummary(); self.load(); });
    });
    form.addEventListener("submit", function (e) {
      if (!self.hora || !self.hora.value) { e.preventDefault(); }
    });
    this.updateSummary();
    this.load();
  }

  function toISO(d) {
    return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");
  }

  SlotPicker.prototype.servicio = function () {
    var checked = this.form.querySelector("input[name=servicio]:checked");
    if (checked) return checked;
    var hidden = this.form.querySelector("input[type=hidden][name=servicio]");
    return hidden && hidden.value ? hidden : null;
  };

  SlotPicker.prototype.message = function (txt) {
    this.slots.innerHTML = "";
    var div = document.createElement("div");
    div.className = "slots-msg";
    div.textContent = txt;
    this.slots.appendChild(div);
  };

  SlotPicker.prototype.setHora = function (value) {
    if (this.hora) this.hora.value = value || "";
    if (this.submit) this.submit.disabled = !value;
    this.setSum("hora", value || "—");
  };

  SlotPicker.prototype.setSum = function (key, value) {
    var el = this.form.querySelector('[data-sum="' + key + '"]');
    if (el) el.textContent = value;
  };

  SlotPicker.prototype.updateSummary = function () {
    var s = this.servicio();
    var ds = (s && s.dataset) || {};
    this.setSum("servicio", ds.nombre || "—");
    this.setSum("doctor", ds.doctor ? "Dr. " + ds.doctor : "—");
    this.setSum("duracion", ds.duracion ? ds.duracion + " min" : "—");
    this.setSum("precio", ds.precio ? "$" + ds.precio + " MXN" : "—");
    var f = this.fecha && this.fecha.value;
    if (f) {
      var d = new Date(f + "T00:00:00");
      this.setSum("fecha", d.toLocaleDateString(EN ? "en-US" : "es-MX", { weekday: "long", day: "numeric", month: "long" }));
    } else {
      this.setSum("fecha", "—");
    }
  };

  SlotPicker.prototype.reset = function () {
    if (this.fecha) this.fecha.value = "";
    this.setHora("");
    this.updateSummary();
    this.message(this.servicio() ? STR.pickDate : STR.pickService);
  };

  SlotPicker.prototype.load = function () {
    var self = this;
    this.setHora("");
    this.updateSummary();
    var s = this.servicio();
    var f = this.fecha && this.fecha.value;
    if (!s) return this.message(STR.pickService);
    if (!f) return this.message(STR.pickDate);
    if (new Date(f + "T00:00:00").getDay() === 0) return this.message(STR.noSundays);

    var id = ++this.reqId;
    this.message(STR.loading);
    fetch(this.url + "?fecha=" + encodeURIComponent(f) + "&servicio_id=" + encodeURIComponent(s.value), { credentials: "same-origin" })
      .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, data: d }; }); })
      .then(function (res) {
        if (id !== self.reqId) return;
        if (!res.ok) return self.message(res.data.msg || STR.error);
        var list = (res.data.slots || []);
        if (!list.some(function (x) { return x.estado === "libre"; })) return self.message(res.data.msg || STR.noSlots);
        self.render(list);
      })
      .catch(function () { if (id === self.reqId) self.message(STR.error); });
  };

  SlotPicker.prototype.render = function (list) {
    var self = this;
    this.slots.innerHTML = "";
    var grid = document.createElement("div");
    grid.className = "slots";
    list.forEach(function (s) {
      var b = document.createElement("button");
      b.type = "button";
      b.className = "slot";
      b.textContent = s.hora;
      if (s.estado !== "libre") {
        b.disabled = true;
      } else {
        if (s.recomendado) b.title = STR.suggested;
        b.addEventListener("click", function () {
          grid.querySelectorAll(".slot.selected").forEach(function (x) { x.classList.remove("selected"); });
          b.classList.add("selected");
          self.setHora(s.hora);
        });
      }
      grid.appendChild(b);
    });
    this.slots.appendChild(grid);
  };

  var pickers = {};
  document.querySelectorAll("form[data-slot-picker]").forEach(function (form) {
    pickers[form.id || "default"] = new SlotPicker(form);
  });

  /* ------------------------------------------------------------
     Modal genérico
  ------------------------------------------------------------ */
  function openModal(id) {
    var m = document.getElementById(id);
    if (m) m.classList.add("is-visible");
  }
  function closeModal(m) {
    if (typeof m === "string") m = document.getElementById(m);
    if (m) m.classList.remove("is-visible");
  }
  window.cerrarModal = closeModal;
  document.addEventListener("click", function (e) {
    if (e.target.classList && e.target.classList.contains("modal")) closeModal(e.target);
    var closer = e.target.closest && e.target.closest("[data-close-modal]");
    if (closer) closeModal(closer.closest(".modal"));
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") document.querySelectorAll(".modal.is-visible").forEach(closeModal);
  });

  /* ------------------------------------------------------------
     Reprogramar / cancelar cita
  ------------------------------------------------------------ */
  window.reprogramarCita = function (btn) {
    var d = btn.dataset;
    if (Number(d.veces || 0) >= 1) {
      swal({ icon: "info", title: STR.reprogLimitTitle, text: STR.reprogLimitText });
      return;
    }
    window.rcConfirmar({
      icon: "question",
      title: STR.reprogTitle,
      text: STR.reprogText,
      confirmButton: STR.reprogConfirm,
    }).then(function (ok) {
      if (!ok) return;
      var form = document.getElementById("form-reprogramar");
      if (!form) return;
      form.action = d.url;
      var srv = form.querySelector("input[name=servicio]");
      srv.value = d.servicioId;
      srv.dataset.nombre = d.servicio || "";
      srv.dataset.doctor = d.doctor || "";
      srv.dataset.duracion = d.duracion || "";
      srv.dataset.precio = d.precio || "";
      var actual = document.getElementById("reprog-actual");
      if (actual) actual.textContent = d.actual || "";
      if (pickers["form-reprogramar"]) pickers["form-reprogramar"].reset();
      openModal("modal-reprogramar");
    });
  };

  window.cancelarCita = function (btn) {
    window.rcConfirmar({
      icon: "warning",
      title: STR.cancelTitle,
      text: STR.cancelText,
      confirmButton: STR.cancelConfirm,
      cancelButton: STR.keep,
      confirmColor: DANGER,
    }).then(function (ok) {
      if (!ok) return;
      var form = document.getElementById("form-cancelar");
      if (!form) return;
      form.action = btn.dataset.url;
      form.submit();
    });
  };
})();
