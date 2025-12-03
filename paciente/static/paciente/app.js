/* ============================================================================
   app.js — PACIENTE
============================================================================ */


/* ============================================================
   1. SISTEMA DE ALERTAS TIPO TOAST
=============================================================== */

/**
 * Muestra un toast de éxito o error.
 * @param {string} message
 * @param {"success"|"danger"} type
 */
function showToast(message, type = "success") {
    const container = document.getElementById("toast-container");
    if (!container) return;
  
    const toast = document.createElement("div");
    toast.classList.add("toast-card");
    toast.classList.add(type === "success" ? "toast-success" : "toast-danger");
    toast.textContent = message;
  
    container.appendChild(toast);
  
    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateX(40px)";
        setTimeout(() => toast.remove(), 300);
    }, 4000);
  }
  
  
  
  /* ============================================================
   2. INICIALIZACIÓN GENERAL (esperar al DOM)
  =============================================================== */
  
document.addEventListener("DOMContentLoaded", () => {
  // ------------------------------
  // Tema claro/oscuro con persistencia
  // ------------------------------
  const body = document.body;
  const themeToggle = document.getElementById("theme-toggle");
  const pathLang = window.location.pathname.startsWith("/en/") ? "en" : null;
  const lang = (pathLang || body.dataset.lang || document.documentElement.lang || "es").slice(0, 2);
  const THEME_KEY = "paciente-theme";
  const STR = {
    selectDate: lang === "en" ? "Select a date to see times." : "Selecciona fecha para ver horarios.",
    selectOtherDate: lang === "en" ? "Select another date." : "Selecciona otra fecha.",
    selectServiceDate: lang === "en" ? "Select service and date to see times." : "Selecciona servicio y fecha para ver horarios.",
    noSundays: lang === "en" ? "We don't work on Sundays. Please choose another date." : "No atendemos domingos. Elige otra fecha.",
    titleNew: lang === "en" ? "Book Appointment" : "Agendar Cita",
    titleReschedule: lang === "en" ? "Reschedule Appointment" : "Reprogramar Cita",
    swalLimitTitle: lang === "en" ? "Reschedule limit reached" : "Límite de reprogramación alcanzado",
    swalLimitText: lang === "en"
      ? "You can only reschedule once. For more changes, contact the clinic."
      : "Solo puedes reprogramar una vez. Para más cambios, contacta al consultorio.",
    swalReprogTitle: lang === "en" ? "Do you want to reschedule?" : "¿Deseas reprogramar?",
    swalReprogText1: lang === "en"
      ? "You can reschedule only <b>1 time</b>."
      : "Solamente se puede reprogramar <b>1 sola vez</b>.",
    swalReprogText2: lang === "en"
      ? "For further changes, ask your dentist to do it."
      : "Para volver a cancelar o reprogramar, avisa a tu dentista para que él lo haga.",
    swalReprogConfirm: lang === "en" ? "Continue and reschedule" : "Continuar y reprogramar",
    swalReprogCancel: lang === "en" ? "Cancel" : "Cancelar",
    swalCancelTitle: lang === "en" ? "Are you sure you want to cancel?" : "¿Seguro que deseas cancelar?",
    swalCancelText1: lang === "en"
      ? "You can cancel only <b>1 time</b>."
      : "Solamente se puede cancelar <b>1 sola vez</b>.",
    swalCancelText2: lang === "en"
      ? "Please do it with <b>1 day in advance</b>."
      : "Recuerda hacerlo con <b>1 día de anticipación</b>.",
    swalCancelWarning: lang === "en"
      ? "<strong>If you cancel now, you will lose your spot.</strong>"
      : "<strong>Si cancelas ahora, perderás tu lugar.</strong>",
    swalCancelConfirm: lang === "en" ? "Yes, cancel" : "Sí, cancelar",
    swalCancelCancel: lang === "en" ? "Cancel" : "Cancelar",
    noSlots: lang === "en" ? "No available times. Try another day." : "Sin horarios libres. Intenta otro día.",
  };

  function applyTheme(theme) {
    body.classList.remove("dark-mode", "light-mode");
    body.classList.add(theme === "light" ? "light-mode" : "dark-mode");
    body.setAttribute("data-theme", theme);
    if (themeToggle) {
      themeToggle.querySelector(".chip-icon").textContent = theme === "light" ? "☀️" : "🌙";
      themeToggle.querySelector(".chip-label").textContent = theme === "light" ? "Claro" : "Oscuro";
    }
  }

  const savedTheme = localStorage.getItem(THEME_KEY);
  if (savedTheme === "light" || savedTheme === "dark") {
    applyTheme(savedTheme);
  } else {
    applyTheme("dark");
  }

  if (themeToggle) {
    themeToggle.addEventListener("click", () => {
      const next = body.classList.contains("light-mode") ? "dark" : "light";
      localStorage.setItem(THEME_KEY, next);
      applyTheme(next);
    });
  }

  // Referencias principales (solo existen en dashboard de paciente)
  const modalCita    = document.getElementById("modal-cita");
  const modalPerfil  = document.getElementById("modal-perfil");
  
    const formCita     = document.getElementById("form-cita");
    const servicio     = document.getElementById("servicio_modal") || document.getElementById("cita-servicio");
    const fecha        = document.getElementById("cita-fecha");
    const horaSelect   = document.getElementById("cita-hora");
    const horaHelp     = document.getElementById("hora-help");
    const proximaCita  = document.getElementById("proxima-cita-card");
    const btnSubmit    = document.getElementById("btn-submit-cita");
    const formCancelar = document.getElementById("form-cancelar");
    const slotsUrl     = formCita ? formCita.dataset.slotsUrl || "/paciente/api/slots/" : "/paciente/api/slots/";
  
    // Si no estamos en el dashboard paciente, no hacemos nada más
    if (!formCita || !modalCita) {
        return;
    }
  
  
    /* ------------------------------------------
       2.1 Flatpickr para fechas de cita
    ------------------------------------------- */
    if (typeof flatpickr !== "undefined" && fecha) {
        window.citaCalendar = flatpickr("#cita-fecha", {
            locale: lang === "en" ? "en" : "es",
            minDate: "today",
            maxDate: new Date().fp_incr(60),
            dateFormat: "Y-m-d",
            inline: true,
            disable: [
                function (date) {
                    // Bloquea domingos (0)
                    return date.getDay() === 0;
                }
            ],
            onChange: function (selectedDates, dateStr) {
                if (servicio && servicio.value) {
                    consultarHorarios(dateStr);
                }
            }
        });
    }
  
  
    /* ------------------------------------------
       2.2 Cambiar servicio → habilitar fecha
    ------------------------------------------- */
    if (servicio && fecha) {

        // límites: hoy y hasta 60 días
        const today = new Date();
        const todayStr = today.toISOString().split("T")[0];
        const maxDate = new Date();
        maxDate.setDate(maxDate.getDate() + 60);
        const maxStr = maxDate.toISOString().split("T")[0];
        fecha.min = todayStr;
        fecha.max = maxStr;

        servicio.addEventListener("change", () => {
            fecha.value = "";
            resetHoras(STR.selectDate);
            btnSubmit.disabled = true;
            if (window.citaCalendar) {
                window.citaCalendar.clear();
            }
        });

        fecha.addEventListener("change", () => {
            if (!fecha.value || !servicio.value) return;
            const f = new Date(fecha.value + "T00:00:00");
            if (f.getDay() === 0) {
                showToast(STR.noSundays, "danger");
                fecha.value = "";
                resetHoras(STR.selectOtherDate);
                btnSubmit.disabled = true;
                return;
            }
            consultarHorarios(fecha.value);
        });
    }
  
  
    /* ------------------------------------------
       2.3 Envío de formulario de cita
       (nos aseguramos de que servicio no esté disabled)
    ------------------------------------------- */
    formCita.addEventListener("submit", () => {
        if (servicio) servicio.disabled = false;
    });
  
  
    /* ------------------------------------------
       2.4 Cerrar modal al hacer click fuera
    ------------------------------------------- */
    document.addEventListener("click", (e) => {
        if (e.target.classList.contains("modal-overlay")) {
            e.target.classList.remove("is-visible");
        }
    });
  
  
    /* ------------------------------------------
       2.5 Mensajes de Django → Toasts bonitos
    ------------------------------------------- */
    const djangoMessages = document.querySelectorAll(".cyber-alert");
    djangoMessages.forEach(msg => {
        const type =
            msg.classList.contains("cyber-alert-danger") ? "danger" : "success";
  
        showToast(msg.textContent.trim(), type);
        msg.style.display = "none";
    });
  
  
    /* ======================================================
       3. FUNCIONES LIGADAS A window.* PARA USO DESDE HTML
       (onclick="...") → aseguran que SIEMPRE existen
    ======================================================= */
  
    /**
     * Abre el modal para agendar una nueva cita.
     */
    window.abrirModalAgendar = function () {
        if (!modalCita) return;
  
        // Título del modal
        const title = modalCita.querySelector(".modal-header h3");
        if (title) {
            title.innerHTML = `<i class="ph-duotone ph-calendar-plus"></i> ${STR.titleNew}`;
        }
  
        // Reset de formulario
        formCita.action = formCita.getAttribute("action"); // URL original de agendar
        formCita.reset();
  
        if (servicio) {
            servicio.disabled = false;
            servicio.value = "";
        }
        if (fecha) {
            fecha.value = "";
        }
        resetHoras(STR.selectServiceDate);
        if (horaSelect) {
            horaSelect.value = "";
        }
        if (btnSubmit) {
            btnSubmit.disabled = true;
        }
  
        modalCita.classList.add("is-visible");
    };
  
  
    /**
     * Cierra el modal de cita (agendar/reprogramar).
     */
    window.cerrarModal = function () {
        if (!modalCita) return;
        modalCita.classList.remove("is-visible");
  
        // Limpieza ligera
        if (window.citaCalendar) {
            window.citaCalendar.clear();
        }
    };
  
  
    /**
     * Verifica si puede reprogramar la cita y en caso afirmativo
     * abre el modal configurado para reprogramación.
     * - veces = proxima_cita.veces_reprogramada (desde el template)
     */
    window.verificarReprogramacion = function (citaId, servicioId, veces) {
        if (typeof Swal === "undefined") {
            // Si no está SweetAlert, abrimos el modal directo
            return abrirModalReprogramarDirecto(citaId, servicioId);
        }

        if (veces >= 1) {
            Swal.fire({
                title: STR.swalLimitTitle,
                text: STR.swalLimitText,
                icon: "info",
                confirmButtonColor: "#00d4ff",
                background: "#18212f",
                color: "#e8eef7"
            });
            return;
        }

        Swal.fire({
            title: STR.swalReprogTitle,
            html: `
                <div class="alert-icon">
                    <span>!</span>
                </div>
                <p>${STR.swalReprogText1}</p>
                <p>${STR.swalReprogText2}</p>
            `,
            icon: null,
            showCancelButton: true,
            confirmButtonText: STR.swalReprogConfirm,
            confirmButtonColor: "#00d4ff",
            cancelButtonText: STR.swalReprogCancel,
            cancelButtonColor: "#94a3b8",
            background: "rgba(8,13,23,0.95)",
            color: "#e8eef7",
            customClass: { popup: "swal-rc" }
        }).then(result => {
            if (result.isConfirmed) {
                abrirModalReprogramarDirecto(citaId, servicioId);
            }
        });
    };
  
  
    /**
     * Lógica común para abrir el modal en modo reprogramación.
     * Cambia la acción del formulario a /paciente/citas/reprogramar/<id>/
     */
    function abrirModalReprogramarDirecto(citaId, servicioId) {
        if (!modalCita) return;
  
        const title = modalCita.querySelector(".modal-header h3");
        if (title) {
            title.innerHTML = `<i class="ph-duotone ph-calendar-plus"></i> ${STR.titleReschedule}`;
        }
  
        // Se usa la URL CORRECTA: /paciente/citas/reprogramar/<id>/
        formCita.action = `/paciente/citas/reprogramar/${citaId}/`;
  
        // Servicio fijo (no editable)
        if (servicio) {
            servicio.value = servicioId;
            servicio.disabled = true;
        }
  
        // Habilitar fecha para que el usuario elija
        if (fecha) {
            fecha.disabled = false;
            if (window.citaCalendar) {
                window.citaCalendar.clear();
            }
        }
  
        // Limpiar horarios y deshabilitar botón hasta elegir fecha
        resetHoras(STR.selectDate);
        if (horaSelect) {
            horaSelect.value = "";
        }
        if (btnSubmit) {
            btnSubmit.disabled = true;
        }
  
        modalCita.classList.add("is-visible");
    }
  
  
    /**
     * Confirma la cancelación de la cita.
     */
    window.confirmarCancelacion = function (citaId) {
        if (!formCancelar) return;
  
        if (typeof Swal === "undefined") {
            formCancelar.action = `/paciente/citas/${citaId}/cancelar/`;
            return formCancelar.submit();
        }

        Swal.fire({
            title: STR.swalCancelTitle,
            html: `
                <div class="alert-icon">
                    <span>!</span>
                </div>
                <p>${STR.swalCancelText1}</p>
                <p>${STR.swalCancelText2}</p>
                <p style="color:#f87171;">${STR.swalCancelWarning}</p>
            `,
            icon: null,
            showCancelButton: true,
            confirmButtonText: STR.swalCancelConfirm,
            confirmButtonColor: "#ef4444",
            cancelButtonText: STR.swalCancelCancel,
            cancelButtonColor: "#94a3b8",
            background: "rgba(8,13,23,0.95)",
            color: "#e8eef7",
            customClass: { popup: "swal-rc" }
        }).then(result => {
            if (result.isConfirmed) {
                formCancelar.action = `/paciente/citas/${citaId}/cancelar/`;
                formCancelar.submit();
            }
        });
    };
  
  
    /**
     * Abre el modal de editar perfil.
     */
    window.abrirModalPerfil = function () {
        if (!modalPerfil) return;
  
        modalPerfil.classList.add("is-visible");
  
        // Calendario para fecha de nacimiento
        if (typeof flatpickr !== "undefined") {
            flatpickr("#perfil-fecha", {
                locale: "es",
                dateFormat: "Y-m-d",
                maxDate: "today"
            });
        }
    };
  
  
    /**
     * Cierra el modal de perfil.
     */
    window.cerrarModalPerfil = function () {
        if (!modalPerfil) return;
        modalPerfil.classList.remove("is-visible");
    };
  
  
    /* ============================================================
       4. FUNCIÓN AUXILIAR: CONSULTAR HORARIOS (API)
       Se deja dentro del DOMContentLoaded para tener acceso a refs.
    ============================================================ */
    async function consultarHorarios(fechaStr) {
        if (!servicio || !horaSelect || !btnSubmit) return;
  
        const servicioId = servicio.value;
        if (!servicioId) return;
  
        btnSubmit.disabled = true;
        horaSelect.innerHTML = "<option>Cargando...</option>";
        horaSelect.disabled = true;
        if (horaHelp) {
            horaHelp.style.display = "block";
            horaHelp.textContent = "Buscando horarios...";
        }
  
        try {
            const res = await fetch(
                `${slotsUrl}?fecha=${fechaStr}&servicio_id=${servicioId}`
            );
            const data = await res.json();
            if (!res.ok) {
                throw new Error(data.msg || "No disponible");
            }
  
            if (data.slots && data.slots.length > 0) {
                setHorasDesdeSlots(data.slots);
            } else {
                resetHoras("Lleno / No disponible. Intenta otro día.");
            }
        } catch (err) {
            resetHoras(err.message || "Error de conexión.");
            showToast("No se pudieron obtener los horarios.", "danger");
        }
    }

    function setHorasDesdeSlots(slots) {
        horaSelect.innerHTML = '<option value="" selected disabled>-- Elige hora --</option>';
        let candidato = null;
        slots.forEach((s) => {
            const opt = document.createElement("option");
            opt.value = s.hora;
            opt.textContent = s.hora + (s.recomendado ? " • sugerido" : "");
            if (s.estado === "ocupado") {
                opt.disabled = true;
                opt.textContent = `${s.hora} (ocupado)`;
            } else if (!candidato || s.recomendado) {
                candidato = s.hora;
            }
            horaSelect.appendChild(opt);
        });

        if (candidato) {
            horaSelect.value = candidato;
            btnSubmit.disabled = false;
            horaSelect.disabled = false;
            if (horaHelp) {
                horaHelp.style.display = "none";
            }
        } else {
            resetHoras(STR.noSlots);
        }
    }

    function resetHoras(mensaje) {
        if (horaSelect) {
            horaSelect.innerHTML = `<option value="">${mensaje}</option>`;
            horaSelect.disabled = true;
        }
        if (horaHelp) {
            horaHelp.style.display = "block";
            horaHelp.textContent = mensaje;
        }
        if (btnSubmit) btnSubmit.disabled = true;
    }
  
  }); // FIN DOMContentLoaded
  
  /* ============================================================
   FIN DE app.js — PACIENTE
  =============================================================== */
  
