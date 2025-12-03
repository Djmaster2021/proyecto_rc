/* ==========================================================================
   DENTIST DASHBOARD PRO | MAIN APPLICATION LOGIC vFINAL
   ========================================================================== 
   INDICE:
   1. INICIALIZACIÓN (DOM Content Loaded)
      - Sidebar & Navegación
      - Relojes
      - Configuración de Gráficas (Chart.js adaptado a Tema Claro)
   2. FUNCIONES GLOBALES (Window Exports)
      - Agenda & Filtros
      - Modals (Apertura/Cierre)
      - Lógica del Ticket (Visualización en tiempo real)
      - Alertas (SweetAlert)
   ========================================================================== */

   document.addEventListener("DOMContentLoaded", function () {
    
    /* ---------------------------------------------------------
       1. SIDEBAR & NAVEGACIÓN
       --------------------------------------------------------- */
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("sidebar-overlay");
    const toggleBtn = document.getElementById("mobile-toggle"); // Botón flotante móvil
    const sidebarToggleBtn = document.getElementById("sidebar-toggle"); // Botón interno (si existe)

    function toggleSidebar() {
        if (!sidebar) return;
        sidebar.classList.toggle("sidebar-open");
        
        // Manejo del overlay para oscurecer el fondo en móvil
        if (overlay) {
            if (sidebar.classList.contains("sidebar-open")) {
                overlay.style.display = "block";
                setTimeout(() => overlay.classList.add("visible"), 10);
            } else {
                overlay.classList.remove("visible");
                setTimeout(() => overlay.style.display = "none", 300);
            }
        }
    }

    if (toggleBtn) toggleBtn.addEventListener("click", toggleSidebar);
    if (sidebarToggleBtn) sidebarToggleBtn.addEventListener("click", toggleSidebar);
    if (overlay) overlay.addEventListener("click", toggleSidebar);

    // Cerrar sidebar al hacer clic en un enlace (Solo en móvil)
    document.querySelectorAll(".sidebar a").forEach(link => {
        link.addEventListener("click", () => {
            if (window.innerWidth < 1024) toggleSidebar();
        });
    });

    // Indicador "Lava Lamp" (Barra lateral animada)
    const navLists = document.querySelectorAll('.nav-list');
    function moveIndicator(list) {
        const activeLink = list.querySelector('.nav-item.active');
        const indicator = list.querySelector('.nav-indicator');
        if (activeLink && indicator) {
            indicator.style.top = `${activeLink.offsetTop}px`;
            indicator.style.height = `${activeLink.offsetHeight}px`;
            indicator.style.opacity = '1';
        } else if (indicator) {
            indicator.style.opacity = '0';
        }
    }
    navLists.forEach(list => moveIndicator(list));


    /* ---------------------------------------------------------
       2. RELOJES & NOTIFICACIONES
       --------------------------------------------------------- */
    function updateClocks() {
        const now = new Date();
        const timeString = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        const sidebarClock = document.getElementById('sidebar-clock');
        const dashClock = document.getElementById('live-clock'); // Reloj grande en Dashboard
        
        if (sidebarClock) sidebarClock.innerText = timeString;
        if (dashClock) dashClock.innerText = timeString;
    }
    setInterval(updateClocks, 1000);
    updateClocks();

    // Desaparecer mensajes flash (Toasts) automáticamente
    const msgArea = document.getElementById('messages-area');
    if (msgArea) {
        setTimeout(() => {
            msgArea.style.transition = "opacity 0.5s ease";
            msgArea.style.opacity = '0';
            setTimeout(() => msgArea.remove(), 500);
        }, 4000);
    }


    /* ---------------------------------------------------------
       3. GRÁFICAS (Chart.js) - ADAPTADO A TEMA CLARO
       --------------------------------------------------------- */
    if (typeof Chart !== 'undefined') {
        // Configuración Global para Tema Claro
        Chart.defaults.color = '#64748b'; // Texto Gris Oscuro
        Chart.defaults.font.family = "'Inter', sans-serif";
        Chart.defaults.font.weight = '600';
        
        const commonScales = {
            y: { 
                beginAtZero: true, 
                grid: { color: '#e2e8f0', drawBorder: false }, // Rejilla gris suave
                ticks: { callback: v => '$' + v, font: { weight: 'bold' } } 
            },
            x: { 
                grid: { display: false } 
            }
        };

        // A. Gráfica de Tendencia (Reportes)
        const ctxTrend = document.getElementById('ingresosTrendChart');
        if (ctxTrend) {
            const grad = ctxTrend.getContext('2d').createLinearGradient(0,0,0,400);
            grad.addColorStop(0, 'rgba(0, 173, 193, 0.2)'); // Cyan suave
            grad.addColorStop(1, 'rgba(0, 173, 193, 0)');

            new Chart(ctxTrend, {
                type: 'line',
                data: {
                    labels: ['Sem 1', 'Sem 2', 'Sem 3', 'Sem 4'],
                    datasets: [{
                        label: 'Ingresos Netos', 
                        data: [12000, 19000, 15000, 25000],
                        borderColor: '#00adc1', // Tu color Cyan de Marca
                        backgroundColor: grad, 
                        borderWidth: 3, 
                        fill: true, 
                        tension: 0.4,
                        pointBackgroundColor: '#fff', 
                        pointBorderColor: '#00adc1', 
                        pointBorderWidth: 2,
                        pointRadius: 6,
                        pointHoverRadius: 8
                    }]
                },
                options: { 
                    responsive: true, 
                    maintainAspectRatio: false, 
                    plugins: { legend: { display: false }, tooltip: { backgroundColor: '#1e293b', titleColor: '#fff', bodyColor: '#fff', padding: 10, cornerRadius: 8 } }, 
                    scales: commonScales 
                }
            });
        }

        // B. Gráfica de Dona (Tratamientos)
        const ctxDonut = document.getElementById('treatmentsChart');
        if (ctxDonut) {
            new Chart(ctxDonut, {
                type: 'doughnut',
                data: {
                    labels: ['Limpiezas', 'Ortodoncia', 'Cirugía'],
                    datasets: [{
                        data: [45, 30, 25],
                        backgroundColor: ['#00adc1', '#2d7282', '#94a3b8'], // Paleta Noguchi (Cyan, Petróleo, Gris)
                        borderWidth: 2,
                        borderColor: '#ffffff', // Borde blanco para separar segmentos
                        hoverOffset: 10
                    }]
                },
                options: { 
                    responsive: true, 
                    maintainAspectRatio: false, 
                    cutout: '70%', 
                    plugins: { legend: { position: 'bottom', labels: { usePointStyle: true, padding: 20 } } } 
                }
            });
        }
    }
    
    // Inicializar Vista de Agenda (Por defecto Lista)
    if (document.getElementById('agendaGrid')) {
        filterAgenda('list');
    }

    // Cerrar modales al hacer clic fuera (Listener Global)
    window.onclick = function(event) {
        if (event.target.classList.contains('modal-overlay')) {
            closeModals();
            closeEditModal(); 
        }
    };

}); // --- FIN DOMContentLoaded ---


/* =========================================================
   FUNCIONES GLOBALES (Exportadas a Window)
   ========================================================= */

// --- 1. GESTIÓN DE AGENDA (Filtros Visuales) ---
window.filterAgenda = function(viewType) {
    const allDays = document.querySelectorAll('.day-card');
    const btns = document.querySelectorAll('.tool-btn');
    
    if (!allDays.length) return;

    // Actualizar botones
    btns.forEach(btn => btn.classList.remove('active'));
    const activeBtn = document.getElementById('btn-' + viewType);
    if (activeBtn) activeBtn.classList.add('active');

    // Lógica simple de mostrar/ocultar
    let limit = allDays.length; 
    if (viewType === 'week') limit = 7;   // Mostrar 7 días
    if (viewType === 'month') limit = 30; // Mostrar todo

    allDays.forEach((card, index) => {
        if (index < limit) {
            card.style.display = 'flex';
            // Pequeña animación de entrada
            card.style.opacity = '0';
            setTimeout(() => card.style.opacity = '1', 50 * index);
        } else {
            card.style.display = 'none';
        }
    });
};

// --- 2. ALERTAS (SweetAlert Tema Claro) ---
window.confirmarEliminacion = function(btnElement, nombrePaciente) {
    Swal.fire({
        title: '¿Eliminar Cita?',
        html: `Estás a punto de borrar la cita de <strong>${nombrePaciente}</strong>.<br>Esta acción no se puede deshacer.`,
        icon: 'warning',
        background: '#ffffff',       // Fondo Blanco
        color: '#0f172a',            // Texto Oscuro
        showCancelButton: true,
        confirmButtonColor: '#ef4444', // Rojo Peligro
        cancelButtonColor: '#cbd5e1',  // Gris Suave
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar',
        cancelButtonColor: '#64748b',
        reverseButtons: true,
        customClass: {
            popup: 'swal-clean-popup' // Clase hook por si quieres CSS extra
        }
    }).then((result) => {
        if (result.isConfirmed) {
            const form = btnElement.closest('form');
            form.submit();
        }
    });
};


// --- 3. GESTIÓN DE MODALES ---
window.openProfileModal = function() {
    const m = document.getElementById('profileModal');
    if(m) { m.style.display = 'flex'; setTimeout(() => m.classList.add('active'), 10); }
};

window.openPasswordModal = function() {
    const m = document.getElementById('passwordModal');
    if(m) { m.style.display = 'flex'; setTimeout(() => m.classList.add('active'), 10); }
};

window.closeModals = function() {
    document.querySelectorAll('.modal-overlay').forEach(m => {
        m.classList.remove('active');
        setTimeout(() => m.style.display = 'none', 300);
    });
};

window.openEditModal = function(citaId, currentNotes) {
    const modal = document.getElementById('editModal');
    const form = document.getElementById('editForm');
    const notesArea = document.getElementById('modalNotes');
    
    // Limpiar inputs de archivo previos
    const fileInput = document.getElementById('modalFileInput');
    const fileText = document.getElementById('modalFileText');

    if (!modal || !form || !notesArea) return;

    form.action = `/dentista/citas/${citaId}/actualizar-nota/`;
    notesArea.value = currentNotes;
    
    if(fileInput) fileInput.value = "";
    if(fileText) fileText.innerText = "";

    modal.style.display = 'flex';
    setTimeout(() => modal.classList.add('active'), 10);
};

window.closeEditModal = function() {
    const modal = document.getElementById('editModal');
    if (!modal) return;
    modal.classList.remove('active');
    setTimeout(() => modal.style.display = 'none', 300);
};


// --- 4. VISUALIZACIÓN DE ARCHIVOS (Inputs) ---
// Sirve para el modal de perfil y el de historial
window.updateProfileFileText = function() {
    const input = document.getElementById('profileFileInput');
    const textDisplay = document.getElementById('profileFileText');
    updateFileDisplay(input, textDisplay);
};

window.updateModalFileText = function() {
    const input = document.getElementById('modalFileInput');
    const textDisplay = document.getElementById('modalFileText');
    updateFileDisplay(input, textDisplay);
};

// Función auxiliar para no repetir código
function updateFileDisplay(input, textDisplay) {
    if (input && input.files && input.files.length > 0) {
        textDisplay.innerHTML = `<i class="ph-fill ph-check-circle"></i> ${input.files[0].name}`;
        textDisplay.style.color = '#00adc1'; // Color Cyan Brand
        textDisplay.style.fontWeight = 'bold';
    } else if(textDisplay) {
        textDisplay.innerText = "";
    }
}


// --- 5. BÚSQUEDA EN TABLAS (Pagos/Pacientes) ---
window.filterPaymentTable = function() {
    const input = document.getElementById("searchInput");
    if (!input) return;

    const filter = input.value.toUpperCase();
    const table = document.getElementById("pagosTable"); // Asegúrate que tu tabla tenga este ID
    if (!table) return;

    const tr = table.getElementsByTagName("tr");

    for (let i = 1; i < tr.length; i++) {
        let found = false;
        const tds = tr[i].getElementsByTagName("td");
        for (let j = 0; j < tds.length; j++) {
            if (tds[j]) {
                if (tds[j].innerText.toUpperCase().indexOf(filter) > -1) {
                    found = true;
                    break;
                }
            }
        }
        tr[i].style.display = found ? "" : "none";
    }
};


// --- 6. TICKET VISUAL (Nueva Cita) ---
// Esta función actualiza la tarjeta de vista previa al crear cita
window.updateTicket = function() {
    const sSelect = document.getElementById('servicio');
    const fInput = document.getElementById('fecha');
    const hSelect = document.getElementById('hora');
    
    const tPaciente = document.getElementById('t-paciente');
    const tServicio = document.getElementById('t-servicio');
    const tDuracion = document.getElementById('t-duracion');
    const tFecha = document.getElementById('t-fecha');
    const tHora = document.getElementById('t-hora');
    const tPrecio = document.getElementById('t-precio');

    // 1. Actualizar Paciente (Compatibilidad Select2)
    if (typeof $ !== 'undefined' && $('#paciente').length) {
        const selectedData = $('#paciente').select2('data')[0];
        if (selectedData && selectedData.element) {
            tPaciente.textContent = selectedData.element.getAttribute('data-nombre');
            // FIX IMPORTANTE: Color oscuro para fondo blanco
            tPaciente.style.color = "#2d7282"; 
            tPaciente.style.fontWeight = "800";
        }
    }

    // 2. Actualizar Servicio y Precio
    if (sSelect && sSelect.selectedIndex > 0) {
        const opt = sSelect.options[sSelect.selectedIndex];
        tServicio.textContent = opt.getAttribute('data-nombre');
        tDuracion.textContent = opt.getAttribute('data-duracion') + " min";
        
        const precioRaw = parseFloat(opt.getAttribute('data-precio'));
        tPrecio.textContent = "$" + precioRaw.toFixed(2);
        
        // Animación de precio
        tPrecio.classList.remove('animate-update');
        void tPrecio.offsetWidth; // Trigger reflow
        tPrecio.classList.add('animate-update');
    }

    // 3. Actualizar Fecha
    if (fInput && fInput.value) {
        const [y, m, d] = fInput.value.split('-');
        const dateObj = new Date(y, m-1, d);
        const options = { weekday: 'long', day: 'numeric', month: 'short' };
        let fStr = dateObj.toLocaleDateString('es-MX', options);
        tFecha.textContent = fStr.charAt(0).toUpperCase() + fStr.slice(1);
    }

    // 4. Actualizar Hora
    if (hSelect && hSelect.value) {
        let cleanText = hSelect.options[hSelect.selectedIndex].text.replace(' (Ocupado)', '');
        tHora.textContent = cleanText;
    } else if (tHora) {
        tHora.textContent = "--:--";
    }
};

// --- 7. ELIMINAR PACIENTE (SweetAlert) ---
window.confirmarEliminarPaciente = function(btnElement, nombrePaciente) {
    Swal.fire({
        title: '¿Eliminar Expediente?',
        html: `Estás a punto de eliminar a <strong>${nombrePaciente}</strong> y TODO su historial clínico.<br><br><span style="color:#ef4444; font-weight:bold;">⚠️ Esta acción es irreversible.</span>`,
        icon: 'warning',
        background: '#fff',
        color: '#0f172a',
        showCancelButton: true,
        confirmButtonColor: '#ef4444',
        cancelButtonColor: '#cbd5e1',
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar',
        reverseButtons: true,
        customClass: { popup: 'swal-clean-popup' }
    }).then((result) => {
        if (result.isConfirmed) {
            const form = btnElement.closest('form');
            form.submit();
        }
    });
};

// --- 8. SISTEMA DE PESTAÑAS (PERFIL PACIENTE) ---
document.addEventListener("DOMContentLoaded", function () {
    const tabs = document.querySelectorAll('.tab-btn');
    const panes = document.querySelectorAll('.tab-pane');

    if (tabs.length > 0) {
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                // 1. Desactivar todos
                tabs.forEach(t => t.classList.remove('active'));
                panes.forEach(p => p.classList.remove('active'));

                // 2. Activar el actual
                tab.classList.add('active');
                
                // 3. Buscar y mostrar el contenido correspondiente
                const targetId = tab.getAttribute('data-tab');
                const targetPane = document.getElementById(targetId);
                if (targetPane) targetPane.classList.add('active');
            });
        });
    }
});

// --- 9. GESTIÓN DE SERVICIOS (MODAL Y BÚSQUEDA) ---

// Variables globales para el modal de servicios
let modalServicio; 

document.addEventListener("DOMContentLoaded", function() {
    // Inicializar referencias si estamos en la página de servicios
    modalServicio = document.getElementById('modalServicio');
    const buscador = document.getElementById('buscadorServicios');

    if (buscador) {
        buscador.addEventListener('keyup', function() {
            let filter = this.value.toLowerCase();
            let rows = document.querySelectorAll('#tablaServicios tbody tr');

            rows.forEach(row => {
                let text = row.innerText.toLowerCase();
                row.style.display = text.includes(filter) ? '' : 'none';
            });
        });
    }
});

// Funciones Exportadas a Window (para usar onclick en HTML)
window.abrirModalServicio = function() {
    if(!modalServicio) return;
    
    // Limpiar formulario para crear nuevo
    document.getElementById('modalTitle').innerText = "Nuevo Servicio";
    document.getElementById('servicio_id').value = "";
    document.getElementById('nombre').value = "";
    document.getElementById('precio').value = "";
    document.getElementById('duracion').value = "30"; // Default
    document.getElementById('activo').checked = true;
    
    modalServicio.classList.add('active');
    modalServicio.style.display = 'flex';
};

window.editarServicio = function(id, nombre, precio, duracion, activo) {
    if(!modalServicio) return;

    // Llenar formulario con datos existentes
    document.getElementById('modalTitle').innerText = "Editar Servicio";
    document.getElementById('servicio_id').value = id;
    document.getElementById('nombre').value = nombre;
    // Asegurar formato decimal con punto para el input number
    document.getElementById('precio').value = precio.replace(',', '.'); 
    document.getElementById('duracion').value = duracion;
    // Convertir string 'True'/'False' o 'true'/'false' a booleano
    document.getElementById('activo').checked = (activo.toLowerCase() === 'true');
    
    modalServicio.classList.add('active');
    modalServicio.style.display = 'flex';
};

window.cerrarModalServicio = function() {
    if(!modalServicio) return;
    modalServicio.classList.remove('active');
    setTimeout(() => modalServicio.style.display = 'none', 300);
};

// Función SweetAlert para eliminar servicio (Consistente con Pacientes)
window.confirmarEliminarServicio = function(btnElement, nombreServicio) {
    Swal.fire({
        title: '¿Eliminar Servicio?',
        text: `Se eliminará "${nombreServicio}" del catálogo.`,
        icon: 'warning',
        background: '#fff', color: '#0f172a',
        showCancelButton: true,
        confirmButtonColor: '#ef4444', cancelButtonColor: '#cbd5e1',
        confirmButtonText: 'Sí, eliminar', cancelButtonText: 'Cancelar',
        reverseButtons: true,
        customClass: { popup: 'swal-clean-popup' }
    }).then((result) => {
        if (result.isConfirmed) {
            btnElement.closest('form').submit();
        }
    });
};

// --- 10. BUSCADOR DE RIESGOS ---
document.addEventListener("DOMContentLoaded", function() {
    const searchRisk = document.getElementById('searchRisk');
    if (searchRisk) {
        searchRisk.addEventListener('keyup', function() {
            let filter = this.value.toLowerCase();
            let rows = document.querySelectorAll('#riskTable tbody tr');

            rows.forEach(row => {
                let text = row.innerText.toLowerCase();
                row.style.display = text.includes(filter) ? '' : 'none';
            });
        });
    }
});

// --- 11. GESTIÓN DE CONFIGURACIÓN (ARCHIVOS) ---

// Actualizar nombre de archivo al subir foto de perfil
window.updateProfileFileText = function() {
    const input = document.getElementById('profileFileInput');
    const textDisplay = document.getElementById('profileFileText');
    
    if (input && input.files && input.files.length > 0) {
        textDisplay.innerHTML = `<i class="ph-fill ph-check-circle"></i> ${input.files[0].name}`;
        textDisplay.classList.add('active');
    } else if (textDisplay) {
        textDisplay.innerText = "";
    }
};

// --- 12. FILTRO FAQ (SOPORTE) ---
document.addEventListener("DOMContentLoaded", function() {
    const searchInput = document.getElementById('faqSearch');
    
    if (searchInput) {
        searchInput.addEventListener('keyup', function() {
            const filter = this.value.toLowerCase();
            const details = document.querySelectorAll('details.faq-item');

            details.forEach(detail => {
                const question = detail.querySelector('summary').innerText.toLowerCase();
                const answer = detail.querySelector('.faq-answer').innerText.toLowerCase();
                
                // Si el texto coincide con la pregunta o la respuesta
                if (question.includes(filter) || answer.includes(filter)) {
                    detail.style.display = '';
                    // Opcional: Abrir automáticamente si hay texto escrito
                    if(filter.length > 2) detail.setAttribute('open', ''); 
                } else {
                    detail.style.display = 'none';
                    detail.removeAttribute('open');
                }
            });
        });
    }
});

// --- 13. GESTIÓN DE CONSULTA ---
window.cancelarCitaDesdeConsulta = function() {
    Swal.fire({
        title: '¿Cancelar esta consulta?',
        text: "La cita se marcará como cancelada y volverás al inicio.",
        icon: 'warning',
        background: '#fff', color: '#0f172a',
        showCancelButton: true,
        confirmButtonColor: '#ef4444',
        cancelButtonColor: '#cbd5e1',
        confirmButtonText: 'Sí, cancelar',
        cancelButtonText: 'Continuar editando',
        reverseButtons: true,
        customClass: { popup: 'swal-clean-popup' }
    }).then((result) => {
        if (result.isConfirmed) {
            document.getElementById('formCancelar').submit();
        }
    });
};

// --- 14. TPV (TERMINAL DE PAGO) ---
window.selectCita = function(cardElement, id, precio, paciente, servicio) {
    // 1. Estilos visuales (Quitar 'selected' de todos, poner al clickeado)
    document.querySelectorAll('.pay-card').forEach(c => c.classList.remove('selected'));
    cardElement.classList.add('selected');

    // 2. Llenar datos del formulario (Inputs Ocultos)
    document.getElementById('selectedCitaId').value = id;
    // Asegurar formato decimal con punto para JS
    const precioFormat = parseFloat(precio.replace(',', '.')).toFixed(2);
    document.getElementById('inputMonto').value = precioFormat;
    
    // 3. Actualizar Resumen Visual (Ticket)
    document.getElementById('displayTotal').innerText = "$" + precioFormat;
    document.getElementById('summaryPatient').innerText = paciente;
    document.getElementById('summaryService').innerText = servicio;
    
    // 4. Habilitar botón de cobro
    document.getElementById('btnCobrar').disabled = false;
};

// --- 15. NUEVA CITA (LÓGICA DE TIEMPO) ---
document.addEventListener("DOMContentLoaded", function() {
    
    // 1. Inicializar Select2 para Pacientes (Búsqueda avanzada)
    // Requiere jQuery cargado antes
    if (typeof $ !== 'undefined' && $('.select2-patient').length) {
        $('.select2-patient').select2({
            placeholder: "Buscar paciente por nombre...",
            width: '100%',
            language: { noResults: () => "No encontrado" }
        });
    }

    // 2. Cálculo Automático de Hora Fin
    const inputInicio = document.querySelector('input[name="hora_inicio"]');
    const inputFin = document.querySelector('input[name="hora_fin"]');
    const selectServicio = document.querySelector('select[name="servicio"]');

    function calcularHoraFin() {
        if (!inputInicio || !inputFin || !selectServicio) return;
        
        // Obtener duración del servicio seleccionado (atributo data-duration)
        const option = selectServicio.options[selectServicio.selectedIndex];
        // Si no hay data-duration, asumimos 30 min por defecto
        const duracionMin = parseInt(option.getAttribute('data-duration')) || 30; 
        
        // Obtener hora inicio
        const horaInicioVal = inputInicio.value; // Formato "HH:MM"
        if (!horaInicioVal) return;

        // Crear objeto fecha para sumar minutos
        let [hours, minutes] = horaInicioVal.split(':').map(Number);
        let date = new Date();
        date.setHours(hours);
        date.setMinutes(minutes + duracionMin); 

        // Formatear nueva hora a HH:MM
        let newHours = String(date.getHours()).padStart(2, '0');
        let newMinutes = String(date.getMinutes()).padStart(2, '0');
        
        inputFin.value = `${newHours}:${newMinutes}`;
    }

    // Escuchar cambios para recalcular
    if (selectServicio) selectServicio.addEventListener('change', calcularHoraFin);
    if (inputInicio) inputInicio.addEventListener('change', calcularHoraFin);
});

// --- 16. GESTOR INTELIGENTE DE CITAS ---
document.addEventListener("DOMContentLoaded", function() {
    
    // Referencias DOM
    const inputFecha = document.getElementById('inputFecha');
    const selectHora = document.getElementById('selectHora');
    const selectServicio = document.getElementById('selectServicio');
    const inputHoraFin = document.getElementById('inputHoraFin');

    // Leer datos del Backend (JSON) solo si existen los nodos
    const horariosEl = document.getElementById('horarios-data');
    const ocupadasEl = document.getElementById('ocupadas-data');
    const horariosData = horariosEl ? JSON.parse(horariosEl.textContent || '{}') : {};
    const ocupadasData = ocupadasEl ? JSON.parse(ocupadasEl.textContent || '{}') : {};

    // Si no estamos en una vista que use agenda, salimos
    if (!inputFecha && !selectHora && !selectServicio) {
        return;
    }

    // 1. Inicializar Select2
    if (typeof $ !== 'undefined' && $('.select2-patient').length) {
        $('.select2-patient').select2({
            placeholder: "Buscar paciente...",
            width: '100%'
        });
    }

    // 2. Evento Cambio de Fecha -> Generar Horas
    if (inputFecha) {
        inputFecha.addEventListener('change', function() {
            const fechaSeleccionada = this.value;
            if (!fechaSeleccionada) return;

            // Obtener día de la semana (JS: 0=Domingo, 1=Lunes... ¡OJO!)
            // Python suele ser 0=Lunes. Ajustamos según tu BD.
            // Asumiremos que tu BD usa 1=Lunes ... 7=Domingo para simplificar, o adaptamos.
            // Truco: Creamos la fecha y vemos qué día es.
            const dateObj = new Date(fechaSeleccionada + 'T00:00:00');
            let diaSemana = dateObj.getDay(); // 0 (Dom) a 6 (Sab)
            
            // Mapeo JS (0=Dom) a Django (Si usas 1=Lunes...6=Sábado, 7=Domingo)
            // Ajusta este mapa según cómo guardas en tu BD
            const jsToDjangoDay = { 1:1, 2:2, 3:3, 4:4, 5:5, 6:6, 0:7 }; 
            const diaDjango = jsToDjangoDay[diaSemana];

            selectHora.innerHTML = '<option value="">Cargando...</option>';
            selectHora.disabled = true;

            // Verificar si trabaja ese día
            const horarioDia = horariosData[diaDjango]; // Busca en el JSON
            
            if (!horarioDia) {
                selectHora.innerHTML = '<option value="">No laborable / Descanso</option>';
                return;
            }

            // Generar Slots
            const slots = generarSlots(horarioDia.inicio, horarioDia.fin, 30); // Cada 30 min
            const citasEseDia = ocupadasData[fechaSeleccionada] || [];

            // Filtrar ocupados
            selectHora.innerHTML = '<option value="" selected disabled>Selecciona hora inicio</option>';
            
            let slotsDisponibles = 0;
            slots.forEach(hora => {
                if (!citasEseDia.includes(hora)) {
                    const option = document.createElement('option');
                    option.value = hora;
                    option.text = hora;
                    selectHora.appendChild(option);
                    slotsDisponibles++;
                }
            });

            if (slotsDisponibles === 0) {
                selectHora.innerHTML = '<option value="">Agenda llena este día</option>';
            } else {
                selectHora.disabled = false;
            }
        });
    }

    // 3. Calcular Hora Fin al seleccionar Inicio
    if (selectHora && selectServicio) {
        selectHora.addEventListener('change', updateHoraFin);
        selectServicio.addEventListener('change', updateHoraFin);
    }

    function updateHoraFin() {
        const horaInicio = selectHora.value;
        if (!horaInicio) return;

        const optionServicio = selectServicio.options[selectServicio.selectedIndex];
        const duracion = parseInt(optionServicio.getAttribute('data-duration')) || 30;

        let [h, m] = horaInicio.split(':').map(Number);
        let date = new Date();
        date.setHours(h);
        date.setMinutes(m + duracion);

        let finH = String(date.getHours()).padStart(2, '0');
        let finM = String(date.getMinutes()).padStart(2, '0');
        
        inputHoraFin.value = `${finH}:${finM}`;
    }

    // Helper: Generador de intervalos de tiempo
    function generarSlots(start, end, interval) {
        const slots = [];
        let [startH, startM] = start.split(':').map(Number);
        let [endH, endM] = end.split(':').map(Number);
        
        let current = new Date();
        current.setHours(startH, startM, 0, 0);
        
        let endTime = new Date();
        endTime.setHours(endH, endM, 0, 0);

        while (current < endTime) {
            let h = String(current.getHours()).padStart(2, '0');
            let m = String(current.getMinutes()).padStart(2, '0');
            slots.push(`${h}:${m}`);
            current.setMinutes(current.getMinutes() + interval);
        }
        return slots;
    }
});
// ==========================================
// Lógica del Menú Móvil (Reparada)
// ==========================================
document.addEventListener("DOMContentLoaded", () => {
    const mobileBtn = document.getElementById("mobile-menu-btn");
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("sidebar-overlay");

    // Función para abrir/cerrar
    function toggleMenu() {
        console.log("Click en menú detectado"); // Para depurar
        sidebar.classList.toggle("active"); // Asegúrate de que tu CSS tenga la clase .active para el sidebar
        
        if (overlay) {
            overlay.classList.toggle("active");
        }
    }

    // Event Listener
    if (mobileBtn) {
        mobileBtn.addEventListener("click", (e) => {
            e.stopPropagation(); // Evita clics fantasmas
            toggleMenu();
        });
    }

    // Cerrar al tocar el fondo oscuro (overlay)
    if (overlay) {
        overlay.addEventListener("click", () => {
            sidebar.classList.remove("active");
            overlay.classList.remove("active");
        });
    }
});

/* ==========================================
   RC Dental - Lógica Principal v7.3
   ========================================== */

   document.addEventListener("DOMContentLoaded", () => {
    console.log("Sistema RC Dental iniciado.");

    // --- 1. REFERENCIAS A ELEMENTOS ---
    const mobileBtn = document.getElementById("mobile-menu-btn");
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("sidebar-overlay");

    // --- 2. FUNCIÓN PARA ABRIR/CERRAR ---
    function toggleSidebar(e) {
        if(e) e.stopPropagation(); // Evita clics dobles
        
        // Alternar clase 'active' en el menú y el fondo oscuro
        if(sidebar) sidebar.classList.toggle("active");
        if(overlay) overlay.classList.toggle("active");
        
        console.log("Botón menú presionado. Sidebar activo:", sidebar.classList.contains("active"));
    }

    // --- 3. EVENT LISTENERS (ESCUCHADORES) ---
    
    // A) Clic en el botón hamburguesa
    if (mobileBtn) {
        mobileBtn.addEventListener("click", toggleSidebar);
        console.log("Botón móvil detectado y listo.");
    } else {
        console.error("ERROR: No se encontró el botón con ID 'mobile-menu-btn'");
    }

    // B) Clic en el fondo oscuro (para cerrar al tocar afuera)
    if (overlay) {
        overlay.addEventListener("click", () => {
            sidebar.classList.remove("active");
            overlay.classList.remove("active");
        });
    }

    // C) Cerrar menú al hacer clic en un enlace (Mejora de UX)
    const navLinks = document.querySelectorAll('.nav-item');
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            // Solo cerrar si estamos en modo móvil (pantalla pequeña)
            if (window.innerWidth < 1024) { 
                sidebar.classList.remove("active");
                if(overlay) overlay.classList.remove("active");
            }
        });
    });
});

/* =========================================
   LÓGICA DE SERVICIOS (Modal y Menús)
   ========================================= */

// Abrir/Cerrar menú de opciones de cada tarjeta
function toggleServiceMenu(id) {
    const menu = document.getElementById(id);
    
    // Cierra cualquier otro menú abierto primero
    document.querySelectorAll('.mini-menu').forEach(el => {
        if (el.id !== id) el.classList.remove('show');
    });
    
    // Alternar el actual
    if (menu) menu.classList.toggle('show');
}

// Abrir Modal para CREAR nuevo
function abrirModalServicio() {
    const modal = document.getElementById('serviceModal');
    if (!modal) return;

    modal.style.display = 'flex';
    document.getElementById('modalTitle').textContent = 'Nuevo Servicio';
    
    // Limpiar formulario
    document.getElementById('formId').value = '';
    document.getElementById('formNombre').value = '';
    document.getElementById('formPrecio').value = '';
    document.getElementById('formDuracion').value = '30';
    document.getElementById('formActivo').checked = true;
}

// Abrir Modal para EDITAR existente
function editarServicio(id, nombre, precio, duracion, activo) {
    const modal = document.getElementById('serviceModal');
    if (!modal) return;

    modal.style.display = 'flex';
    document.getElementById('modalTitle').textContent = 'Editar Servicio';
    
    // Llenar formulario con datos
    document.getElementById('formId').value = id;
    document.getElementById('formNombre').value = nombre;
    // Limpiar precio (quitar comas si las hay)
    document.getElementById('formPrecio').value = parseFloat(precio.replace(',',''));
    document.getElementById('formDuracion').value = duracion;
    
    // Convertir string 'True'/'False' a booleano para el checkbox
    const esActivo = (activo === 'True' || activo === 'true' || activo === true);
    document.getElementById('formActivo').checked = esActivo;
    
    // Cerrar el menú flotante
    toggleServiceMenu('menu-' + id);
}

// Cerrar Modal
function cerrarModalServicio() {
    const modal = document.getElementById('serviceModal');
    if (modal) modal.style.display = 'none';
}

// Cerrar menús si hago click fuera
window.addEventListener('click', function(event) {
    if (!event.target.matches('.icon-btn-ghost') && !event.target.closest('.icon-btn-ghost')) {
        document.querySelectorAll('.mini-menu').forEach(el => el.classList.remove('show'));
    }
    if (event.target == document.getElementById('serviceModal')) {
        cerrarModalServicio();
    }
});

// Tabs del expediente del paciente
document.addEventListener("DOMContentLoaded", function () {
    const tabButtons = document.querySelectorAll(".patient-tabs-nav .tab-btn");
    const panels = document.querySelectorAll(".patient-tabs-panels .tab-panel");

    tabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            if (btn.disabled) return;

            const target = btn.dataset.tab;

            // botones
            tabButtons.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");

            // panels
            panels.forEach(p => {
                p.classList.toggle("active", p.id === "tab-" + target);
            });
        });
    });
});

// =========================================================
// SISTEMA DE PESTAÑAS (TABS) - PERFIL PACIENTE
// =========================================================

document.addEventListener("DOMContentLoaded", function () {
    
    // 1. Seleccionamos todos los botones y todos los paneles de contenido
    const tabs = document.querySelectorAll('.tab-btn');
    const panes = document.querySelectorAll('.tab-pane');

    // Solo ejecutamos si encontramos pestañas en la página
    if (tabs.length > 0) {
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                
                // A. Quitar la clase 'active' de TODAS las pestañas y paneles
                // (Esto "apaga" o esconde todo lo anterior)
                tabs.forEach(t => t.classList.remove('active'));
                panes.forEach(p => p.classList.remove('active'));

                // B. Agregar la clase 'active' solo al botón que clickeaste
                tab.classList.add('active');
                
                // C. Buscar el panel de contenido que corresponde a este botón
                // El botón dice: data-tab="tab-odonto" -> Buscamos el div con id="tab-odonto"
                const targetId = tab.getAttribute('data-tab');
                const targetPane = document.getElementById(targetId);
                
                // D. Mostrar ese panel específico
                if (targetPane) {
                    targetPane.classList.add('active');
                }
            });
        });
    }
});

// =========================================================
//  CREAR CITA MANUAL – IA LIGERA Y UX
//  Se activa sólo en la pantalla de crear_cita_manual.html
// =========================================================
document.addEventListener("DOMContentLoaded", function () {
    const servicioSelect = document.getElementById("servicio");
    const fechaInput = document.getElementById("fecha");
    const horaInput = document.getElementById("hora");
    const iaBox = document.getElementById("iaBox");
    const iaMessage = document.getElementById("iaMessage");

    if (!servicioSelect || !fechaInput || !horaInput) {
        // No estamos en la pantalla de crear cita, salimos
        return;
    }

    function actualizarRecomendacionIA() {
        const servicioOption = servicioSelect.options[servicioSelect.selectedIndex];
        const fechaVal = fechaInput.value;
        const horaVal = horaInput.value;

        if (!servicioOption || !fechaVal) {
            iaBox.style.display = "none";
            return;
        }

        // Duración estimada desde atributo data-duracion
        const duracion = servicioOption.getAttribute("data-duracion") || "30";

        // Mensaje sencillo de IA por ahora (versión 1)
        let mensaje = `Para "${servicioOption.text}" se recomienda evitar
                       huecos largos entre citas.`;

        if (horaVal) {
            mensaje += ` Has elegido las ${horaVal}.`;
        } else {
            mensaje += ` Elige una hora dentro del horario laboral disponible.`;
        }

        mensaje += ` Duración estimada: ${duracion} minutos.`;

        iaMessage.textContent = mensaje;
        iaBox.style.display = "block";
    }

    servicioSelect.addEventListener("change", actualizarRecomendacionIA);
    fechaInput.addEventListener("change", actualizarRecomendacionIA);
    horaInput.addEventListener("change", actualizarRecomendacionIA);
});

document.addEventListener("DOMContentLoaded", function () {
    const servicioSelect = document.getElementById("servicio");
    const fechaInput = document.getElementById("fecha");
    const horaInput = document.getElementById("hora");
    const iaBox = document.getElementById("iaBox");
    const iaMessage = document.getElementById("iaMessage");

    if (!servicioSelect || !fechaInput || !horaInput) {
        return; // No estamos en crear_cita_manual
    }

    function actualizarRecomendacionIA() {
        const servicioOption = servicioSelect.options[servicioSelect.selectedIndex];
        const fechaVal = fechaInput.value;
        const horaVal = horaInput.value;

        if (!servicioOption || !fechaVal) {
            iaBox.style.display = "none";
            return;
        }

        const duracion = servicioOption.getAttribute("data-duracion") || "30";

        let mensaje = `Para "${servicioOption.text}" se recomienda evitar huecos largos entre citas.`;
        if (horaVal) {
            mensaje += ` Has elegido las ${horaVal}.`;
        } else {
            mensaje += ` Elige una hora dentro del horario laboral disponible.`;
        }
        mensaje += ` Duración estimada: ${duracion} minutos.`;

        iaMessage.textContent = mensaje;
        iaBox.style.display = "block";
    }

    servicioSelect.addEventListener("change", actualizarRecomendacionIA);
    fechaInput.addEventListener("change", actualizarRecomendacionIA);
    horaInput.addEventListener("change", actualizarRecomendacionIA);
});


// ===============================
// Menú lateral Dentista (móvil + escritorio)
// ===============================
document.addEventListener("DOMContentLoaded", function () {
    console.log("RC Dentista :: menú lateral listo");
  
    var openBtn = document.getElementById("mobile-menu-btn");
    var closeBtn = document.getElementById("sidebar-close-btn");
    var sidebar = document.getElementById("sidebar");
    var overlay = document.getElementById("sidebar-overlay");
    var toggleBtn = document.getElementById("sidebarToggle");
    var body = document.body;
    var STORAGE_KEY = "rc_sidebar_collapsed";
  
    // ----- Helpers móvil -----
    function closeMenu() {
      if (sidebar) sidebar.classList.remove("active");
      if (overlay) overlay.classList.remove("active");
    }
  
    function openMenu() {
      if (sidebar) sidebar.classList.add("active");
      if (overlay) overlay.classList.add("active");
    }
  
    if (openBtn) {
      openBtn.addEventListener("click", function (e) {
        e.stopPropagation();
        openMenu();
      });
    }
  
    if (closeBtn) {
      closeBtn.addEventListener("click", function (e) {
        e.stopPropagation();
        closeMenu();
      });
    }
  
    if (overlay) {
      overlay.addEventListener("click", function () {
        closeMenu();
      });
    }
  
    // ----- Toggle escritorio (colapsar sidebar) -----
    if (toggleBtn) {
      try {
        var saved = localStorage.getItem(STORAGE_KEY);
        if (saved === "1") {
          body.classList.add("sidebar-collapsed");
        }
      } catch (e) {
        console.warn("LocalStorage no disponible para sidebar:", e);
      }
  
      toggleBtn.addEventListener("click", function (e) {
        e.stopPropagation();
        body.classList.toggle("sidebar-collapsed");
        var isCollapsed = body.classList.contains("sidebar-collapsed");
        try {
          localStorage.setItem(STORAGE_KEY, isCollapsed ? "1" : "0");
        } catch (e) {
          console.warn("No se pudo guardar preferencia de sidebar:", e);
        }
      });
    }
  });

  // Confirmación al eliminar horario
  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".btn-delete-sch").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.preventDefault();
        const href = btn.getAttribute("href");
        const dia = btn.dataset.dia || "este día";
        const hora = btn.dataset.hora || "";
        const texto = `Vas a eliminar el bloque ${dia} ${hora}. No se podrá agendar en ese horario.`;

        if (typeof Swal !== "undefined") {
          Swal.fire({
            title: "¿Eliminar horario?",
            text: texto,
            icon: "warning",
            showCancelButton: true,
            confirmButtonText: "Sí, eliminar",
            cancelButtonText: "Cancelar",
            confirmButtonColor: "#ef4444",
            cancelButtonColor: "#94a3b8",
          }).then((result) => {
            if (result.isConfirmed && href) window.location.href = href;
          });
        } else {
          if (confirm(texto)) {
            if (href) window.location.href = href;
          }
        }
      });
    });
  });

  // Apertura de modales genéricos por data-target
  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".js-open-modal").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.preventDefault();
        const targetId = btn.dataset.target;
        if (!targetId) return;
        const modal = document.getElementById(targetId);
        if (!modal) return;
        modal.style.display = "flex";
        modal.classList.add("active");
      });
    });

    // Cerrar modales al click en fondo
    document.querySelectorAll(".modal-overlay").forEach((modal) => {
      modal.addEventListener("click", (e) => {
        if (e.target === modal) {
          modal.classList.remove("active");
          setTimeout(() => (modal.style.display = "none"), 200);
        }
      });
    });
  });

  // Forzar submit del formulario de horario aunque haya JS extra cargado
  document.querySelectorAll("form[action*='configuracion'][method='post']").forEach((form) => {
    const actionInput = form.querySelector("input[name='action'][value='add_schedule']");
    if (!actionInput) return;
    const submitBtn = form.querySelector("button[type='submit']");
    if (submitBtn) {
      submitBtn.addEventListener("click", () => {
        form.submit();
      });
    }
  });
  /* ============================================================
   LÓGICA DE CITAS MANUALES (AJAX)
   ============================================================ */

async function cargarSlots() {
    const servicioId = document.getElementById('servicioSelect').value;
    const fecha = document.getElementById('fechaInput').value;
    const container = document.getElementById('slots-container');
    const loader = document.getElementById('loading-badge');
    const btnSubmit = document.getElementById('btnSubmit');
    const inputHora = document.getElementById('horaSelected');

    // 1. Resetear estados previos
    inputHora.value = "";
    btnSubmit.disabled = true;

    // Si falta algún dato, no hacemos nada
    if (!servicioId || !fecha) return;

    // 2. Mostrar carga y limpiar contenedor
    loader.style.display = 'inline-block';
    container.innerHTML = ''; 

    try {
        // 3. Llamada a la API de Django
        const response = await fetch(`/dentista/api/slots/?fecha=${fecha}&servicio_id=${servicioId}`);
        const data = await response.json();

        loader.style.display = 'none';

        // 4. Manejo de respuesta vacía
        if (!data.slots || data.slots.length === 0) {
            container.innerHTML = `
                <div class="empty-slot-msg">
                    <i class="ph-bold ph-warning-circle"></i>
                    No hay horarios disponibles para esta fecha.
                    <br><small>Intenta otro día o verifica que sea laboral.</small>
                </div>`;
            return;
        }

        // 5. Generar botones dinámicamente
        data.slots.forEach((slot) => {
            const btn = document.createElement('div');
            btn.className = 'time-slot-btn';
            btn.innerHTML = `${slot.hora}`;
            
            // Si la IA lo marca como recomendado
            if (slot.recomendado) {
                btn.innerHTML += `<span class="slot-badge-ia">⚡ Sugerido</span>`;
            }

            // Evento click
            btn.onclick = () => seleccionarSlot(btn, slot.hora);
            container.appendChild(btn);
        });

    } catch (error) {
        console.error('Error cargando slots:', error);
        loader.style.display = 'none';
        container.innerHTML = `
            <div class="empty-slot-msg" style="color: #ef4444; border-color: #fca5a5; background:#fef2f2;">
                Error de conexión. Intenta de nuevo.
            </div>`;
    }
}

function seleccionarSlot(btnElement, hora) {
    // 1. Quitar clase 'selected' de todos los botones
    document.querySelectorAll('.time-slot-btn').forEach(b => b.classList.remove('selected'));
    
    // 2. Marcar el actual
    btnElement.classList.add('selected');
    
    // 3. Inyectar valor en el input oculto y habilitar submit
    document.getElementById('horaSelected').value = hora;
    document.getElementById('btnSubmit').disabled = false;
}
  

/* ============================================================
   LÓGICA DE AGENDA Y MODALES
   ============================================================ */

// Confirmación de eliminación (SweetAlert)
function confirmarEliminacion(btn, nombre) {
    Swal.fire({
        title: '¿Eliminar cita?',
        text: `Se eliminará la cita de ${nombre}`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#ef4444',
        cancelButtonColor: '#334155',
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            btn.closest('form').submit();
        }
    })
}

// Lógica para abrir modal de citas finalizadas
function abrirModalFinalizada(paciente, servicio, inicio, fin, urlExpediente) {
    // 1. Llenar datos visuales
    document.getElementById('modal-paciente').innerText = paciente;
    document.getElementById('modal-servicio').innerText = servicio;
    document.getElementById('modal-horario').innerText = inicio + ' - ' + fin;
    
    // 2. Configurar botón usando la URL que nos pasó el HTML
    document.getElementById('btn-expediente').href = urlExpediente;

    // 3. Mostrar modal
    document.getElementById('modal-cita-finalizada').style.display = 'flex';
}

function cerrarModalFinalizada() {
    document.getElementById('modal-cita-finalizada').style.display = 'none';
}

// Cerrar si clic afuera
window.onclick = function(event) {
    const modal = document.getElementById('modal-cita-finalizada');
    if (event.target == modal) {
        modal.style.display = "none";
    }
}


document.addEventListener('DOMContentLoaded', function() {
    
    // --- GRÁFICAS DE FINANZAS ---
    const ctxIncome = document.getElementById('incomeChart');
    const ctxMethod = document.getElementById('methodChart');

    if (ctxIncome && typeof Chart !== 'undefined') {
        // Gráfica de Barras (Ingresos vs Gastos simulado)
        new Chart(ctxIncome, {
            type: 'bar',
            data: {
                labels: ['Sem 1', 'Sem 2', 'Sem 3', 'Sem 4'],
                datasets: [{
                    label: 'Ingresos',
                    data: [1200, 1900, 3000, 2500], // Aquí podrías poner datos reales de Django
                    backgroundColor: '#00adc1',
                    borderRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true, grid: { display: false } }, x: { grid: { display: false } } }
            }
        });
    }

    if (ctxMethod && typeof Chart !== 'undefined' && typeof chartData !== 'undefined') {
        // Gráfica de Dona (Métodos de Pago)
        new Chart(ctxMethod, {
            type: 'doughnut',
            data: {
                labels: ['Efectivo', 'Digital'],
                datasets: [{
                    data: [chartData.efectivo, chartData.digital],
                    backgroundColor: ['#10b981', '#3b82f6'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '70%',
                plugins: { legend: { position: 'right' } }
            }
        });
    }

    // --- MODAL PAGO ---
    window.abrirModalPago = function() {
        const m = document.getElementById('modal-pago');
        if(m) m.style.display = 'flex';
    }
    window.cerrarModalPago = function() {
        const m = document.getElementById('modal-pago');
        if(m) m.style.display = 'none';
    }
});
/* ============================================================
   LÓGICA FINANZAS (GRÁFICAS)
   ============================================================ */
   document.addEventListener('DOMContentLoaded', function() {
    
    // 1. LEER DATOS DEL HTML
    const dataDiv = document.getElementById('finance-data');
    
    if (dataDiv && typeof Chart !== 'undefined') {
        // Convertimos texto a número flotante
        const efectivo = parseFloat(dataDiv.dataset.efectivo) || 0;
        const digital = parseFloat(dataDiv.dataset.digital) || 0;

        // 2. GRÁFICA DE DONA (MÉTODOS)
        const ctxMethod = document.getElementById('methodChart');
        if (ctxMethod) {
            new Chart(ctxMethod, {
                type: 'doughnut',
                data: {
                    labels: ['Efectivo', 'Digital'],
                    datasets: [{
                        data: [efectivo, digital],
                        backgroundColor: ['#10b981', '#3b82f6'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '75%',
                    plugins: {
                        legend: { position: 'right', labels: { boxWidth: 12, usePointStyle: true } }
                    }
                }
            });
        }

        // 3. GRÁFICA DE BARRAS (SIMULADA POR AHORA)
        const ctxIncome = document.getElementById('incomeChart');
        if (ctxIncome) {
            new Chart(ctxIncome, {
                type: 'bar',
                data: {
                    labels: ['Sem 1', 'Sem 2', 'Sem 3', 'Sem 4'],
                    datasets: [{
                        label: 'Ingresos',
                        data: [efectivo * 0.2, digital * 0.5, efectivo * 0.8, (efectivo + digital)],
                        backgroundColor: '#00adc1',
                        borderRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: { beginAtZero: true, grid: { display: false } },
                        x: { grid: { display: false } }
                    }
                }
            });
        }
    }

    // --- MODAL PAGO MANUAL ---
    window.abrirModalPago = function() {
        const m = document.getElementById('modal-pago');
        if(m) m.style.display = 'flex';
    }
    window.cerrarModalPago = function() {
        const m = document.getElementById('modal-pago');
        if(m) m.style.display = 'none';
    }
});

/* =========================================
   MODAL DE PAGO (FINANZAS)
   ========================================= */
   window.abrirModalPago = function() {
    const modal = document.getElementById('modal-pago');
    if (modal) {
        modal.style.display = 'flex';
        setTimeout(() => modal.classList.add('active'), 10); // Animación suave
    } else {
        console.error("Error: No se encontró el modal con ID 'modal-pago'");
    }
};

window.cerrarModalPago = function() {
    const modal = document.getElementById('modal-pago');
    if (modal) {
        modal.classList.remove('active');
        setTimeout(() => modal.style.display = 'none', 300);
    }
};

// Cerrar al dar clic fuera
window.addEventListener('click', function(event) {
    const modal = document.getElementById('modal-pago');
    if (event.target === modal) {
        cerrarModalPago();
    }
});

document.addEventListener("DOMContentLoaded", function () {
    // ELIMINAR SERVICIO
    document.querySelectorAll(".btn-servicio-delete").forEach((btn) => {
      btn.addEventListener("click", () => {
        const id = btn.dataset.id;
        const nombre = btn.dataset.nombre || "este servicio";
  
        if (typeof Swal === "undefined") {
          if (confirm(`¿Eliminar "${nombre}"? Esta acción no se puede deshacer.`)) {
            document
              .getElementById(`form-delete-servicio-${id}`)
              .submit();
          }
          return;
        }
  
        Swal.fire({
          title: "¿Eliminar servicio?",
          text: `Estás a punto de borrar el servicio "${nombre}". Esta acción no se puede deshacer.`,
          icon: "warning",
          showCancelButton: true,
          confirmButtonText: "Sí, eliminar",
          cancelButtonText: "Cancelar",
        }).then((result) => {
          if (result.isConfirmed) {
            document
              .getElementById(`form-delete-servicio-${id}`)
              .submit();
          }
        });
      });
    });
  
    // ACTIVAR / INHABILITAR SERVICIO
    document.querySelectorAll(".btn-servicio-toggle").forEach((btn) => {
      btn.addEventListener("click", () => {
        const id = btn.dataset.id;
        const nombre = btn.dataset.nombre || "este servicio";
        const activo = btn.dataset.activo === "true";
  
        const accion = activo ? "inhabilitar" : "activar";
        const descripcion = activo
          ? "ya no podrá ser agendado por los pacientes."
          : "volverá a estar disponible para agendar.";
  
        if (typeof Swal === "undefined") {
          if (
            confirm(
              `¿${accion.charAt(0).toUpperCase() + accion.slice(1)} "${nombre}"? ` +
                `El servicio ${descripcion}`
            )
          ) {
            document
              .getElementById(`form-toggle-servicio-${id}`)
              .submit();
          }
          return;
        }
  
        Swal.fire({
          title: `¿${accion.charAt(0).toUpperCase() + accion.slice(1)} servicio?`,
          text: `Estás a punto de ${accion} "${nombre}". El servicio ${descripcion}`,
          icon: "warning",
          showCancelButton: true,
          confirmButtonText: `Sí, ${accion}`,
          cancelButtonText: "Cancelar",
        }).then((result) => {
          if (result.isConfirmed) {
            document
              .getElementById(`form-toggle-servicio-${id}`)
              .submit();
          }
        });
      });
    });
  });
  
