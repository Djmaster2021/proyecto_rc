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

    // Leer datos del Backend (JSON)
    const horariosData = JSON.parse(document.getElementById('horarios-data').textContent || '{}');
    const ocupadasData = JSON.parse(document.getElementById('ocupadas-data').textContent || '{}');

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