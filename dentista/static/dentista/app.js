/* --- AGENDA.JS: Lógica del Calendario y Modal --- */

// Declaración de variables globales de forma simple (una sola vez)
let fpFecha, fpHora;

document.addEventListener('DOMContentLoaded', function() {
    
    // 1. Obtener el elemento del calendario
    var calendarEl = document.getElementById('calendar');
    
    // Ejecutamos la lógica del calendario solo si el elemento existe en el DOM
    if (calendarEl) {
        console.log("Inicializando Calendario...");

        // 2. Inicializar Flatpickr (Calendarios de los inputs del modal)
        fpFecha = flatpickr("#manual-fecha", {
            locale: "es",
            dateFormat: "Y-m-d",
            minDate: "today",
            disableMobile: "true",
            disable: [ function(date) { return (date.getDay() === 0); } ] // Bloquea domingos
        });

        fpHora = flatpickr("#manual-hora", {
            enableTime: true,
            noCalendar: true,
            dateFormat: "H:i",
            time_24hr: false,
            disableMobile: "true"
        });

        // 3. Obtener Citas de Django (JSON seguro)
        var eventos = [];
        try {
            var jsonScript = document.getElementById('eventos-data');
            if (jsonScript) {
                eventos = JSON.parse(jsonScript.textContent);
            }
        } catch (e) {
            console.error("Error cargando eventos:", e);
        }

        // 4. Configurar e Iniciar FullCalendar
        var calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: 'timeGridWeek',
            locale: 'es',
            firstDay: 1,
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek,timeGridDay'
            },
            slotMinTime: '07:00:00', // Inicio 7 AM
            slotMaxTime: '21:00:00', // Fin 9 PM
            allDaySlot: false,
            height: '100%', // Se adapta al contenedor CSS
            expandRows: true,
            nowIndicator: true,
            selectable: true, // Permite clic en huecos
            events: eventos,

            // --- CLIC EN HUECO VACÍO (Abrir Modal y rellenar) ---
            dateClick: function(info) {
                abrirModalManual();
                // Rellenar inputs automáticamente
                let fechaClic = info.dateStr.split('T')[0];
                let horaClic = info.date.toTimeString().split(' ')[0].substring(0,5);

                fpFecha.setDate(fechaClic);
                fpHora.setDate(horaClic);
            },

            // --- CLIC EN CITA EXISTENTE (Ver Detalles) ---
            eventClick: function(info) {
                var props = info.event.extendedProps;
                if (typeof Swal !== 'undefined') {
                    Swal.fire({
                        title: info.event.title,
                        html: `<div style="text-align:left">
                               <p><strong>Tratamiento:</strong> ${props.servicio}</p>
                               <p><strong>Teléfono:</strong> ${props.telefono}</p>
                               <p><strong>Estado:</strong> ${props.estado_texto}</p>
                               <p><strong>Notas:</strong> <i>${props.notas || '--'}</i></p></div>`,
                        icon: 'info',
                        confirmButtonText: 'Gestionar Consulta',
                        confirmButtonColor: '#2dd4bf',
                        showCancelButton: true,
                        cancelButtonText: 'Cerrar',
                        cancelButtonColor: '#334155',
                        background: '#1e293b',
                        color: '#fff'
                    }).then((r) => {
                        if(r.isConfirmed) window.location.href = "/dentista/citas/" + info.event.id + "/consulta/";
                    });
                }
            }
        });

        calendar.render();
    }
});

// --- FUNCIONES GLOBALES DEL MODAL (Llamadas desde el HTML) ---

window.abrirModalManual = function() {
    const modal = document.getElementById('modal-manual');
    if(modal) {
        modal.style.display = 'flex'; // Primero lo hacemos visible
        setTimeout(() => { modal.classList.add('is-visible'); }, 10);
    }
}

window.cerrarModalManual = function() {
    const modal = document.getElementById('modal-manual');
    if(modal) {
        modal.classList.remove('is-visible'); // Inicia animación de ocultar
        setTimeout(() => {
            modal.style.display = 'none'; // Oculta al finalizar la animación
            // Limpiar formulario y Flatpickr
            const form = document.querySelector('#form-manual');
            if(form) form.reset();
            if(fpFecha) fpFecha.clear();
            if(fpHora) fpHora.clear();
        }, 200);
    }
}