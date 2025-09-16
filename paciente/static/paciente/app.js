// static/paciente/app.js — versión alineada a dashboard.html (btnCrear/btnReprogram/btnCancel + Perfil)
(function () {
    "use strict";
  
    // ===== Helpers =====
    const $ = (s, r = document) => r.querySelector(s);
  
    // ===== Estado (demo en localStorage) =====
    const LS_APPT = "pc-next-appointment"; // cita activa
    const LS_REPROG_AT = "pc-reprog-at";   // última reprogramación (ms)
    const LS_REPROG_COUNT = "pc-reprog-count";
    const LS_CANCEL_COUNT = "pc-cancel-count"; // cancelaciones hechas (por cita)
  
    const getAppt = () => { try { return JSON.parse(localStorage.getItem(LS_APPT) || "null"); } catch { return null; } };
    const setAppt = (a) => localStorage.setItem(LS_APPT, JSON.stringify(a));
    const resetCancelCt = () => localStorage.removeItem(LS_CANCEL_COUNT);
    const getCancelCt = () => Number(localStorage.getItem(LS_CANCEL_COUNT) || "0");
    const incCancelCt = () => localStorage.setItem(LS_CANCEL_COUNT, String(getCancelCt() + 1));
    const setReprogAt = (ts) => localStorage.setItem(LS_REPROG_AT, String(ts));
    const getReprogAt = () => Number(localStorage.getItem(LS_REPROG_AT) || "0");
    const setReprogCount = (n) => localStorage.setItem(LS_REPROG_COUNT, String(n));
    const getReprogCount = () => Number(localStorage.getItem(LS_REPROG_COUNT) || "0");
  
    // ===== Fechas útiles =====
    const today = new Date(); today.setHours(0, 0, 0, 0);
    const isoToday = today.toISOString().slice(0, 10);
    const isoTomorrow = new Date(today.getTime() + 24 * 3600 * 1000).toISOString().slice(0, 10);
  
    const prettyDate = (iso) => {
      if (!iso) return "—";
      const [y, m, d] = iso.split("-").map(Number);
      return new Date(y, m - 1, d).toLocaleDateString("es-MX", { day: "2-digit", month: "short", year: "numeric" });
    };
  
    // ===== Referencias UI (dashboard.html) =====
    const elBtnCrear = $("#btnCrear");
    const elBtnReprog = $("#btnReprogram");
    const elBtnCancel = $("#btnCancel");
    const elBtnICS = $("#btnICS");
  
    const elFecha = $("#apFecha");
    const elHora = $("#apHora");
    const elMotivo = $("#apMotivo");
    const elChip = $("#apEstadoChip");
    const elCons = $("#apConsultorio");
  
    // ===== Render =====
    function render() {
      const a = getAppt();
  
      if (a) {
        if (elFecha) elFecha.textContent = prettyDate(a.fechaISO);
        if (elHora) elHora.textContent = a.hora || "—";
        if (elMotivo) elMotivo.textContent = a.motivo || a.servicio || "—";
  
        if (elChip) {
          if (a.estado === "Reprogramada") { elChip.hidden = false; elChip.textContent = "Reprogramada"; }
          else { elChip.hidden = true; }
        }
  
        if (elBtnCrear) elBtnCrear.style.display = "none";
        if (elBtnReprog) elBtnReprog.style.display = "";
        if (elBtnCancel) elBtnCancel.style.display = "";
  
        // Prepara mailto para cancelar (se abrirá tras confirmación)
        if (elBtnCancel) {
          const nombre = ($("#pfNombre")?.textContent || $("#pc-nombre")?.textContent || "Paciente").trim();
          const correo = "dentista.choyo@gmail.com";
          const subject = encodeURIComponent("Solicitud de cancelación de cita");
          const body = encodeURIComponent(
  `Hola Dr. Castellón,
  
  Deseo solicitar la cancelación de mi cita.
  
  Datos de la cita:
  - Paciente: ${nombre}
  - Servicio: ${a.servicio || a.motivo || "—"}
  - Motivo: ${a.motivo || "—"}
  - Fecha: ${a.fechaISO || "—"}
  - Hora: ${a.hora || "—"}
  
  Estoy enterad@ de que la cancelación se gestiona directamente con usted y que no puedo cancelar más de una vez. Asimismo, comprendo la penalización de $150 MXN por cancelación.
  
  Gracias.`
          );
          elBtnCancel.dataset.mailto = `mailto:${correo}?subject=${subject}&body=${body}`;
          elBtnCancel.href = "#";
        }
      } else {
        if (elBtnCrear) elBtnCrear.style.display = "";
        if (elBtnReprog) elBtnReprog.style.display = "none";
        if (elBtnCancel) elBtnCancel.style.display = "none";
        if (elChip) elChip.hidden = true;
      }
    }
  
    // ===== Crear cita (dialog #dlgCrear del dashboard) =====
    (function setupCrear() {
      const dlg = $("#dlgCrear");
      const form = $("#formCrear");
      const f = $("#crFecha");
      if (f) f.min = isoToday; // si quieres forzar 24h antes, usa isoTomorrow
  
      if (elBtnCrear && dlg) elBtnCrear.addEventListener("click", () => dlg.showModal());
  
      if (!form) return;
      form.addEventListener("submit", (e) => {
        e.preventDefault();
  
        if (getAppt()) {
          alert("Ya tienes una cita. Usa Reprogramar.");
          dlg?.close(); return;
        }
  
        const servicio = $("#crServicio")?.value || "";
        const fechaISO = $("#crFecha")?.value || "";
        const hora = $("#crHora")?.value || "";
        const motivo = ($("#crMotivo")?.value || servicio || "").trim();
  
        if (!servicio || !fechaISO || !hora) { alert("Completa servicio, fecha y hora."); return; }
  
        setAppt({ servicio, fechaISO, hora, motivo, estado: "Confirmada" });
        resetCancelCt();                 // nueva cita -> resetea límite de cancelación
        dlg?.close();
        alert("Cita creada");
        render();
      });
    })();
  
    // ===== Reprogramar (placeholder: marca estado y respeta ventana 24h) =====
    function canReprogram(newISO) {
      if (newISO < isoTomorrow) { alert("No puedes reprogramar para hoy. Desde mañana en adelante."); return false; }
      const last = getReprogAt();
      if (last && (Date.now() - last) < 24 * 3600 * 1000) {
        const hrs = Math.ceil((24 * 3600 * 1000 - (Date.now() - last)) / 3600000);
        alert(`Ya reprogramaste recientemente. Intenta en ${hrs} h.`);
        return false;
      }
      return true;
    }
  
    if (elBtnReprog) {
      elBtnReprog.addEventListener("click", () => {
        const a = getAppt();
        if (!a) { alert("No tienes cita para reprogramar."); return; }
  
        // DEMO rápida: pedir nueva fecha/hora con prompt (tu modal real puede reemplazar esto)
        const nf = prompt("Nueva fecha (YYYY-MM-DD):", a.fechaISO || isoTomorrow);
        if (!nf) return;
        const nh = prompt("Nueva hora (HH:MM):", a.hora || "10:00");
        if (!nh) return;
        if (!/^\d{4}-\d{2}-\d{2}$/.test(nf) || !/^\d{2}:\d{2}$/.test(nh)) { alert("Formato inválido."); return; }
        if (!canReprogram(nf)) return;
  
        a.fechaISO = nf;
        a.hora = nh;
        a.estado = "Reprogramada";
        setAppt(a);
        setReprogAt(Date.now());
        setReprogCount(getReprogCount() + 1);
        alert("Cita reprogramada");
        render();
      });
    }
  
    // ===== Cancelar (advertencia + límite 1) =====
    if (elBtnCancel) {
      elBtnCancel.addEventListener("click", (e) => {
        e.preventDefault();
        const a = getAppt();
        if (!a) { alert("No tienes cita para cancelar."); return; }
  
        if (getCancelCt() >= 1) {
          alert("No puedes cancelar más de una vez esta cita. Contacta al consultorio.");
          return;
        }
  
        const ok = confirm(
          "Importante:\n" +
          "• La cancelación solo puede realizarse con el dentista (políticas de la clínica).\n" +
          "• No se permite cancelar más de 1 vez. Cancelaciones adicionales tienen penalización de $150 MXN.\n\n" +
          "¿Deseas solicitar la cancelación por correo?"
        );
        if (!ok) return;
  
        incCancelCt(); // registra la primera cancelación
        const href = elBtnCancel.dataset.mailto;
        if (href) window.location.href = href;
        else alert("No fue posible preparar el correo.");
      });
    }
  
    // ===== .ICS (Agregar a calendario) =====
    function toICS(appt) {
      const dtStr = (appt.fechaISO || isoTomorrow) + "T" + (appt.hora || "10:00") + ":00";
      const dt = new Date(dtStr);
      const dtEnd = new Date(dt.getTime() + 30 * 60000);
      const pad = (n) => String(n).padStart(2, "0");
      const fmt = (d) => d.getUTCFullYear()
        + pad(d.getUTCMonth() + 1) + pad(d.getUTCDate()) + "T"
        + pad(d.getUTCHours()) + pad(d.getUTCMinutes()) + "00Z";
  
      return [
        "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//RC//Paciente//ES",
        "BEGIN:VEVENT",
        "UID:" + Date.now() + "@rcpaciente",
        "DTSTAMP:" + fmt(new Date()),
        "DTSTART:" + fmt(dt),
        "DTEND:" + fmt(dtEnd),
        "SUMMARY:" + (appt.motivo || "Cita dental"),
        "LOCATION:" + (elCons?.textContent || "Consultorio"),
        "DESCRIPTION:" + (appt.servicio ? ("Servicio: " + appt.servicio) : "Cita"),
        "END:VEVENT", "END:VCALENDAR"
      ].join("\r\n");
    }
  
    if (elBtnICS) {
      elBtnICS.addEventListener("click", () => {
        const a = getAppt();
        if (!a) { alert("Primero crea una cita."); return; }
        const blob = new Blob([toICS(a)], { type: "text/calendar;charset=utf-8" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url; link.download = "cita_rc.ics";
        document.body.appendChild(link); link.click();
        document.body.removeChild(link); URL.revokeObjectURL(url);
        alert(".ics generado");
      });
    }
  
    // ===== PERFIL: prefill + guardar (Nombre, Edad, Teléfono, Correo, Dirección) =====
    (function setupPerfil() {
      // Mapa tolerante a tus dos convenciones de IDs en la tarjeta (pf* y pc-*)
      const viewMap = {
        nombre: ["#pfNombre", "#pc-nombre"],
        edad: ["#pfEdad", "#pc-edad"],
        telefono: ["#pfTelefono", "#pc-telefono"],
        correo: ["#pfCorreo", "#pc-correo"],
        direccion: ["#pfDireccion", "#pc-direccion"],
      };
      const inputMap = {
        nombre: "#f-nombre",
        edad: "#f-edad",
        telefono: "#f-telefono",
        correo: "#f-correo",
        direccion: "#f-direccion",
      };
  
      const form = $("#pc-form-perfil");     // <form id="pc-form-perfil">
      const btnOK = $("#pc-save-perfil");    // <button id="pc-save-perfil" ...>
      const modal = $("#pc-m-perfil");       // <section id="pc-m-perfil">
      if (!modal) return; // si no existe el modal, no hacemos nada
  
      const getView = (sels) => {
        for (const s of sels) { const el = $(s); if (el) return el; }
        return null;
      };
  
      function prefill() {
        Object.entries(inputMap).forEach(([k, inSel]) => {
          const input = $(inSel);
          if (!input) return;
          const view = getView(viewMap[k] || []);
          const txt = (view?.textContent || "").trim();
          input.value = txt;
        });
      }
  
      function isValid(form) {
        // Aprovecha HTML5 validation
        if (!form) return true;
        if (!form.checkValidity()) { form.reportValidity(); return false; }
        return true;
      }
  
      function reflectToCard() {
        Object.entries(inputMap).forEach(([k, inSel]) => {
          const input = $(inSel); if (!input) return;
          let val = input.value.trim();
          if (k === "edad" && val !== "") val = String(parseInt(val, 10));
          if (k === "telefono") val = val.replace(/\s+/g, " ").trim();
          const view = getView(viewMap[k] || []);
          if (view) view.textContent = val || "—";
        });
      }
  
      // Prefill cuando el modal se abre por hash (#pc-m-perfil)
      window.addEventListener("hashchange", () => {
        if (location.hash === "#pc-m-perfil") prefill();
      });
      if (location.hash === "#pc-m-perfil") prefill();
  
      // Guardar
      if (btnOK) {
        btnOK.addEventListener("click", (e) => {
          const f = form || $("#pc-form-perfil");
          if (f && !isValid(f)) { e.preventDefault(); return; }
          reflectToCard();
          // cerrar modal navegando a hash neutro
          location.hash = "#_";
        });
      }
    })();
  
    // ===== Init =====
    render();
    console.log("Paciente UI (dashboard) listo");
  })();
  