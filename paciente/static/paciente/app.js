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
    // Referencias principales (solo existen en dashboard de paciente)
    const modalCita    = document.getElementById("modal-cita");
    const modalPerfil  = document.getElementById("modal-perfil");
  
    const formCita     = document.getElementById("form-cita");
    const servicio     = document.getElementById("cita-servicio");
    const fecha        = document.getElementById("cita-fecha");
    const hora         = document.getElementById("cita-hora");
    const btnSubmit    = document.getElementById("btn-submit-cita");
    const formCancelar = document.getElementById("form-cancelar");
  
    // Si no estamos en el dashboard paciente, no hacemos nada más
    if (!formCita || !modalCita) {
        return;
    }
  
  
    /* ------------------------------------------
       2.1 Flatpickr para fechas de cita
    ------------------------------------------- */
    if (typeof flatpickr !== "undefined" && fecha) {
        window.citaCalendar = flatpickr("#cita-fecha", {
            locale: "es",
            minDate: "today",
            maxDate: new Date().fp_incr(30),
            dateFormat: "Y-m-d",
            disable: [
                function (date) {
                    // Bloquea domingos (0)
                    return date.getDay() === 0;
                }
            ],
            onChange: function (selectedDates, dateStr) {
                consultarHorarios(dateStr);
            }
        });
    }
  
  
    /* ------------------------------------------
       2.2 Cambiar servicio → habilitar fecha
    ------------------------------------------- */
    if (servicio && fecha) {
        fecha.disabled = true;
  
        servicio.addEventListener("change", () => {
            if (servicio.value) {
                fecha.disabled = false;
                if (window.citaCalendar) {
                    window.citaCalendar.clear();
                }
            } else {
                fecha.disabled = true;
            }
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
            title.innerHTML = '<i class="ph-duotone ph-calendar-plus"></i> Agendar Cita';
        }
  
        // Reset de formulario
        formCita.action = formCita.getAttribute("action"); // URL original de agendar
        formCita.reset();
  
        if (servicio) {
            servicio.disabled = false;
            servicio.value = "";
        }
        if (fecha) {
            fecha.disabled = true;
            fecha.value = "";
        }
        if (hora) {
            hora.disabled = true;
            hora.innerHTML = '<option value="">-- Primero fecha --</option>';
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
                title: "Límite de reprogramación alcanzado",
                text: "Solo puedes reprogramar una vez. Para más cambios, contacta al consultorio.",
                icon: "info",
                confirmButtonColor: "#00d4ff",
                background: "#18212f",
                color: "#e8eef7"
            });
            return;
        }
  
        Swal.fire({
            title: "¿Deseas reprogramar tu cita?",
            html: "<p>Recuerda que solo tienes <b>1 oportunidad</b> para reprogramar.</p>",
            icon: "warning",
            showCancelButton: true,
            confirmButtonText: "Sí, reprogramar",
            confirmButtonColor: "#00d4ff",
            cancelButtonColor: "#64748b",
            background: "#18212f",
            color: "#e8eef7"
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
            title.innerHTML = '<i class="ph-duotone ph-calendar-plus"></i> Reprogramar Cita';
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
        if (hora) {
            hora.disabled = true;
            hora.innerHTML = '<option value="">-- Primero fecha --</option>';
        }
        if (btnSubmit) {
            btnSubmit.disabled = false; // se habilita al elegir horario, pero aquí lo dejamos listo
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
            title: "¿Seguro que deseas cancelar?",
            html: "<p>Solo puedes cancelar <b>1 vez</b> y con <b>24 horas de anticipación</b>.</p>",
            icon: "warning",
            showCancelButton: true,
            confirmButtonText: "Sí, cancelar",
            confirmButtonColor: "#ef4444",
            cancelButtonColor: "#64748b",
            background: "#18212f",
            color: "#e8eef7"
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
        if (!servicio || !hora || !btnSubmit) return;
  
        const servicioId = servicio.value;
        if (!servicioId) return;
  
        hora.innerHTML = "<option>Cargando...</option>";
        hora.disabled = true;
        btnSubmit.disabled = true;
  
        try {
            const res = await fetch(
                `/paciente/api/horarios/?fecha=${fechaStr}&servicio_id=${servicioId}`
            );
            const horarios = await res.json();
  
            hora.innerHTML = "";
  
            if (horarios.length > 0) {
                horarios.forEach(h => {
                    const opt = document.createElement("option");
                    opt.value = h;
                    opt.textContent = h;
                    hora.appendChild(opt);
                });
  
                hora.disabled = false;
                btnSubmit.disabled = false;
            } else {
                hora.innerHTML = "<option>Sin disponibilidad</option>";
            }
        } catch (err) {
            hora.innerHTML = "<option>Error</option>";
        }
    }
  
  }); // FIN DOMContentLoaded
  
  /* ============================================================
   FIN DE app.js — PACIENTE
  =============================================================== */
  