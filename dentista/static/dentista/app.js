// dentista/static/dentista/app.js

// Inicializa toda la UI del dashboard cuando el DOM está listo
document.addEventListener('DOMContentLoaded', () => {
    const Style = getComputedStyle(document.body);
    const COLOR_PRIMARY = Style.getPropertyValue('--color-primary-cyber').trim() || '#00e0ff';
    const COLOR_SECONDARY = Style.getPropertyValue('--color-secondary-cyber').trim() || '#764ba2';
    const COLOR_ACCENT = Style.getPropertyValue('--color-accent-cyber').trim() || '#39ff14';
    const COLOR_WARNING = Style.getPropertyValue('--color-warning-cyber').trim() || '#ffc107';
    const COLOR_TEXT_MUTED = Style.getPropertyValue('--color-text-muted').trim() || '#9bb0c6';
    const COLOR_BORDER_SUBTLE = 'rgba(255, 255, 255, 0.1)';

    initUI(COLOR_PRIMARY, COLOR_SECONDARY, COLOR_ACCENT, COLOR_WARNING, COLOR_TEXT_MUTED, COLOR_BORDER_SUBTLE);
});

function initUI(p, s, a, w, tm, bs) {
    setLiveDateTime('live-datetime-dentist'); // Para dashboard de dentista
    setLiveDateTime('live-datetime-patient'); // Para dashboard de paciente
    setLiveDateTime('liveClock'); // Para la agenda
    initBurger();
    initTabs();
    initToast();
    initCounters();
    initModals();
    renderCharts(p, s, a, w, tm, bs);
    renderAllData();
    initAgenda();
    initPaymentsPage();
    initServicesPage(); // <-- Esta es la función que hemos actualizado
    initPatientsPage();
    initReportsPage(p, s, a, w, tm, bs);
    initConfiguracionPage();
    initSoportePage();
    initPenaltiesPage();
}

// --- FUNCIÓN MEJORADA PARA FECHA Y HORA ---
function setLiveDateTime(elementId) {
    const clockElement = document.getElementById(elementId);
    if (clockElement) {
        const updateClock = () => {
            const now = new Date();
            const dateOptions = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
            const timeOptions = { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true };
            
            const dateStr = now.toLocaleDateString('es-MX', dateOptions);
            const timeStr = now.toLocaleTimeString('es-MX', timeOptions);

            const formattedDate = dateStr.charAt(0).toUpperCase() + dateStr.slice(1);

            clockElement.innerHTML = `${formattedDate} &nbsp; | &nbsp; ${timeStr}`;
        };
        updateClock();
        setInterval(updateClock, 1000);
    }
}

function initBurger() {
    const burger = document.getElementById('burger');
    const shell = document.querySelector('.shell');
    if (burger && shell) {
        burger.addEventListener('click', () => {
            shell.classList.toggle('collapsed');
        });
    }
}

function initTabs() {
    const tabsContainer = document.querySelector('.tabs');
    if (!tabsContainer) return;
    tabsContainer.addEventListener('click', (e) => {
        const tab = e.target.closest('.tab');
        if (!tab) return;
        tabsContainer.querySelector('.tab.active')?.classList.remove('active');
        document.querySelector('.panel.active')?.classList.remove('active');
        tab.classList.add('active');
        document.getElementById(tab.dataset.tab)?.classList.add('active');
    });
}

function showToast(message) {
    const toastNode = document.getElementById('toast');
    if (!toastNode) return;
    toastNode.textContent = message;
    toastNode.classList.add('show');
    clearTimeout(toastNode._timeoutId);
    toastNode._timeoutId = setTimeout(() => toastNode.classList.remove('show'), 2400);
}

function initToast() {
    document.body.addEventListener('click', e => {
        const btn = e.target.closest('[data-toast]');
        if (btn) showToast(btn.dataset.toast);
    });
    const saveAllBtn = document.getElementById('save-all-settings');
    if (saveAllBtn) {
        saveAllBtn.addEventListener('click', () => showToast('Configuración guardada con éxito'));
    }
}

function initModals() {
    document.querySelectorAll('.modal-close').forEach(btn => {
        btn.addEventListener('click', () => {
            btn.closest('.modal-overlay').classList.remove('is-visible');
        });
    });
    document.querySelectorAll('.modal-overlay').forEach(modal => {
        modal.addEventListener('click', e => {
            if (e.target === modal) {
                modal.classList.remove('is-visible');
            }
        });
    });
}

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('is-visible');
    }
}

function initCounters() {
    document.querySelectorAll('[data-counter]').forEach(el => {
        const end = Number(el.dataset.counter || 0);
        let cur = 0;
        const step = Math.max(1, Math.ceil(end / 80));
        const id = setInterval(() => {
            cur += step;
            if (cur >= end) {
                cur = end;
                clearInterval(id);
            }
            el.textContent = cur.toLocaleString('es-MX');
        }, 10);
    });
}

// --- Configuración de Gráficas con Estilo Neón --- //
function renderCharts(primary, secondary, accent, warning, textMuted, borderSubtle) {
    if (typeof Chart === 'undefined') return;

    const balanceChartEl = document.getElementById('balanceChart');
    if (balanceChartEl) {
        new Chart(balanceChartEl.getContext('2d'), {
            type: 'bar',
            data: {
                labels: ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep'],
                datasets: [{
                    label: 'Ingresos',
                    data: [120, 150, 130, 170, 160, 190, 185, 200, 220],
                    backgroundColor: primary,
                    borderRadius: 5
                }, {
                    label: 'Gastos',
                    data: [40, 35, 50, 45, 60, 55, 62, 58, 70],
                    backgroundColor: secondary,
                    borderRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: textMuted, font: { family: "'Poppins', sans-serif" } } }
                },
                scales: {
                    x: {
                        grid: { color: borderSubtle },
                        ticks: { color: textMuted, font: { family: "'Poppins', sans-serif" } }
                    },
                    y: {
                        grid: { color: borderSubtle },
                        ticks: { color: textMuted, font: { family: "'Poppins', sans-serif" } }
                    }
                }
            }
        });
    }
}

// --- Mock Data (Simulación de Backend) --- //
const MOCK_DATA = {
    dentistProfile: {
        name: 'Dr. Rodolfo Castellón',
        specialty: 'Cirujano Dentista',
        email: 'r.castellon@consultorio.com',
        phone: '+52 322 123 4567',
        photoUrl: '/static/img/dr-castellon.png'
    },
    // La lista de 'services' fue eliminada de aquí. Ahora se obtiene de la API.
    audit: [
        { t: '26 Sep 2025, 20:05', user: 'Sistema', action: 'Cuenta suspendida', details: 'Paciente David R. (ID: P-005) suspendido por 3 penalizaciones.' },
        { t: '26 Sep 2025, 20:05', user: 'Sistema', action: 'Penalización automática', details: 'Generada para David R. (ID: P-005) por inasistencia.' },
        { t: '25 Sep 2025, 20:01', user: 'Sistema', action: 'Penalización automática', details: 'Generada para Sofía S. (ID: P-004) por inasistencia.' },
        { t: '20 Sep 2025, 14:35', user: 'Dr. Castellón', action: 'Cita creada', details: 'Agendó a Ana García.' },
        { t: '19 Sep 2025, 18:00', user: 'Ana García', action: 'Pago recibido', details: 'Recibió pago en línea de $850.' },
    ],
    treatmentPlans: [
        { patient: 'Juan Pérez', patientId: 'P-003', treatment: 'Ortodoncia (Fase 1)', progress: '25%', lastUpdate: '18 Sep 2025' },
        { patient: 'Laura García', patientId: 'P-002', treatment: 'Limpieza y Resina', progress: '100%', lastUpdate: '20 Sep 2025' }
    ],
    inventory: [{ product: 'Resina Composita', category: 'Materiales', stock: '12 unidades', expiryDate: '10/2026' }, { product: 'Guantes Nitrilo', category: 'Consumibles', stock: 'Bajo', expiryDate: 'N/A' }],
    agendaAppointments: { '2025-09-22': [{ time: '10:00 AM', patient: 'Ana García', service: 'Limpieza', status: 'Confirmada', id: 'A-223' }, { time: '04:00 PM', patient: 'Emilio Segura', service: 'Ortodoncia', status: 'Pendiente', id: 'A-224' }], '2025-09-23': [{ time: '11:30 AM', patient: 'Carlos López', service: 'Blanqueamiento', status: 'Confirmada', id: 'A-225' }], '2025-09-24': [], '2025-09-25': [{ time: '03:00 PM', patient: 'María Ruiz', service: 'Resina', status: 'Pendiente', id: 'A-226' }], '2025-09-26': [{ time: '09:00 AM', patient: 'Juan Rodríguez', service: 'Extracción', status: 'Confirmada', id: 'A-227' }, { time: '10:30 AM', patient: 'Daniela Aceves', service: 'Revisión', status: 'Confirmada', id: 'A-228' }], '2025-09-27': [], '2025-09-28': [] },
    payments: [
        { id: 'PAY-001', date: '2025-09-20', patient: 'Ana García', patientId: 'P-001', service: 'Ortodoncia', amount: 2500, status: 'Pagado', action: 'Recibo' },
        { id: 'PAY-002', date: '2025-09-18', patient: 'Laura M.', patientId: 'P-002', service: 'Limpieza', amount: 850, status: 'Pendiente', action: 'Recordar' },
        { id: 'PAY-003', date: '2025-09-15', patient: 'Juan D.', patientId: 'P-003', service: 'Resina', amount: 1500, status: 'Pagado', action: 'Recibo' },
        { id: 'PAY-004', date: '2025-09-12', patient: 'Sofía S.', patientId: 'P-004', service: 'Blanqueamiento', amount: 1200, status: 'Pendiente', action: 'Recordar' }
    ],
    patients: [
        { id: 'P-001', name: 'Ana García', email: 'ana.g@ejemplo.com', phone: '+52 55 1234 5678', lastVisit: '2025-09-20', status: 'Activo' },
        { id: 'P-002', name: 'Laura M.', email: 'laura.m@ej.com', phone: '+52 55 8765 4321', lastVisit: '2025-09-18', status: 'En tratamiento' },
        { id: 'P-003', name: 'Juan D.', email: 'juan.d@ej.com', phone: '+52 55 1122 3344', lastVisit: '2025-01-05', status: 'Inactivo' },
        { id: 'P-004', name: 'Sofía S.', email: 'sofia.s@ej.com', phone: '+52 55 9988 7766', lastVisit: '2025-09-12', status: 'Con deuda' },
        { id: 'P-005', name: 'David R.', email: 'david.r@ej.com', phone: '+52 55 4433 2211', lastVisit: '2025-08-10', status: 'Inactivo (Penalizado)' }
    ],
    penalties: [
        { id: 'PEN-001', patient: 'Sofía S.', patientId: 'P-004', date: '2025-09-25, 10:00 AM', reason: 'Inasistencia (No-Show)', status: 'Pendiente', amount: 500.00 },
        { id: 'PEN-002', patient: 'David R.', patientId: 'P-005', date: '2025-09-26, 04:30 PM', reason: 'Inasistencia (No-Show)', status: 'Pendiente', amount: 500.00 },
        { id: 'PEN-003', patient: 'David R.', patientId: 'P-005', date: '2025-08-10, 11:00 AM', reason: 'Cancelación Tardía', status: 'Pagada', amount: 500.00 },
        { id: 'PEN-004', patient: 'David R.', patientId: 'P-005', date: '2025-07-01, 01:00 PM', reason: 'Inasistencia (No-Show)', status: 'Pagada', amount: 500.00 }
    ]
};

// --- Renderizado de Datos --- //
function renderAllData() {
    const auditList = document.getElementById('auditList');
    if (auditList) {
        const iconMap = {
            'Cita creada': 'ph-calendar-plus',
            'Recordatorio enviado': 'ph-bell-ringing',
            'Pago recibido': 'ph-currency-circle-dollar',
            'Servicio actualizado': 'ph-pencil-simple',
            'Penalización automática': 'ph-warning-octagon',
            'Cuenta suspendida': 'ph-user-circle-minus'
        };

        auditList.innerHTML = MOCK_DATA.audit.map(item => {
            const iconClass = iconMap[item.action] || 'ph-info';
            return `
                <li class="audit-item">
                    <i class="ph ${iconClass} audit-icon"></i>
                    <div>
                        <strong>${item.action}:</strong>
                        <span class="text-muted">${item.details}</span>
                    </div>
                    <div class="spacer"></div>
                    <small class="text-muted">${item.t}</small>
                </li>
            `;
        }).join('');
    }

    const treatmentTable = document.querySelector('#treatmentTable tbody');
    if (treatmentTable) treatmentTable.innerHTML = MOCK_DATA.treatmentPlans.map(item => `<tr><td>${item.patientId}</td><td>${item.patient}</td><td>${item.treatment}</td><td>${item.progress}</td><td>${item.lastUpdate}</td></tr>`).join('');
}


// --- Lógica de Páginas Específicas --- //

function initConfiguracionPage() {
    if (!document.getElementById('dentist-profile-grid')) return;

    const profile = MOCK_DATA.dentistProfile;

    function updateAllProfileImages(newUrl) {
        const imgView = document.getElementById('dentist-profile-img-view');
        const imgModal = document.getElementById('dentist-profile-img-modal');
        const sidebarAvatar = document.getElementById('sidebar-avatar-img');

        if (imgView) imgView.src = newUrl;
        if (imgModal) imgModal.src = newUrl;
        if (sidebarAvatar) sidebarAvatar.src = newUrl;
    }

    const nameView = document.getElementById('dentist-name-view');
    const specView = document.getElementById('dentist-spec-view');
    const emailView = document.getElementById('dentist-email-view');
    const phoneView = document.getElementById('dentist-phone-view');

    const nameInput = document.getElementById('dentist-name-input');
    const specInput = document.getElementById('dentist-spec-input');
    const emailInput = document.getElementById('dentist-email-input');
    const phoneInput = document.getElementById('dentist-phone-input');
    const photoInput = document.getElementById('dentist-photo-input');

    function renderProfile() {
        if (nameView) nameView.textContent = profile.name;
        if (specView) specView.textContent = profile.specialty;
        if (emailView) emailView.textContent = profile.email;
        if (phoneView) phoneView.textContent = profile.phone;
        updateAllProfileImages(profile.photoUrl);
    }

    document.getElementById('btn-edit-dentist-profile')?.addEventListener('click', () => {
        nameInput.value = profile.name;
        specInput.value = profile.specialty;
        emailInput.value = profile.email;
        phoneInput.value = profile.phone;
        openModal('modal-perfil-dentista');
    });

    document.getElementById('btn-change-dentist-password')?.addEventListener('click', () => {
        openModal('modal-password-dentista');
    });

    document.getElementById('form-perfil-dentista')?.addEventListener('submit', e => {
        e.preventDefault();
        profile.name = nameInput.value;
        profile.specialty = specInput.value;
        profile.email = emailInput.value;
        profile.phone = phoneInput.value;
        renderProfile();
        document.getElementById('modal-perfil-dentista').classList.remove('is-visible');
        showToast('Perfil actualizado con éxito');
    });

    document.getElementById('form-password-dentista')?.addEventListener('submit', e => {
        e.preventDefault();
        document.getElementById('modal-password-dentista').classList.remove('is-visible');
        showToast('Contraseña actualizada');
    });

    photoInput?.addEventListener('change', e => {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function (event) {
                const newPhotoUrl = event.target.result;
                profile.photoUrl = newPhotoUrl;
                updateAllProfileImages(newPhotoUrl);
            }
            reader.readAsDataURL(file);
        }
    });

    renderProfile();
}

function initSoportePage() {
    const accordion = document.getElementById('faq-accordion');
    if (accordion) {
        accordion.addEventListener('click', e => {
            const header = e.target.closest('.accordion-header');
            if (!header) return;

            const item = header.parentElement;
            const content = header.nextElementSibling;

            item.classList.toggle('active');
            if (item.classList.contains('active')) {
                content.style.maxHeight = content.scrollHeight + 'px';
            } else {
                content.style.maxHeight = 0;
            }
        });
    }

    const btnReport = document.getElementById('btn-report-problem');
    if (btnReport) {
        btnReport.addEventListener('click', () => {
            openModal('modal-report-problem');
        });
    }

    const formReport = document.getElementById('form-report-problem');
    if (formReport) {
        formReport.addEventListener('submit', e => {
            e.preventDefault();
            document.getElementById('modal-report-problem').classList.remove('is-visible');
            showToast('Reporte enviado con éxito. Gracias.');
        });
    }
}


function initAgenda() {
    const agendaGrid = document.getElementById('agendaGrid');
    if (!agendaGrid) return;

    const days = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'];
    const startDate = new Date('2025-09-22T00:00:00');
    agendaGrid.innerHTML = '';

    for (let i = 0; i < 7; i++) {
        const currentDate = new Date(startDate);
        currentDate.setDate(startDate.getDate() + i);
        const dayKey = currentDate.toISOString().split('T')[0];
        const appointments = MOCK_DATA.agendaAppointments[dayKey] || [];

        const dayCell = document.createElement('div');
        dayCell.className = 'day-cell';

        let appointmentsHTML = appointments.map(appt => `
            <div class="appointment-card">
                <div class="row">
                    <strong>${appt.patient}</strong>
                    <div class="spacer"></div>
                    <span class="pill ${appt.status === 'Confirmada' ? 'ok' : 'warn'}">${appt.status}</span>
                </div>
                <small>${appt.time} - ${appt.service}</small>
            </div>
        `).join('');

        dayCell.innerHTML = `
            <div class="day-header">${days[i]} <span class="highlight">${currentDate.getDate()}</span></div>
            ${appointmentsHTML || ''}
        `;
        agendaGrid.appendChild(dayCell);
    }
}

// ==================================================================
// ==                 FUNCIÓN MODIFICADA PARA USAR API             ==
// ==================================================================
async function initServicesPage() {
    const container = document.getElementById('allServicesGrid');
    if (!container) return;

    try {
        // 1. Hacemos la petición a nuestra API real en lugar de usar MOCK_DATA
        const response = await fetch('/api/servicios/');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const services = await response.json(); // 2. Convertimos la respuesta a JSON

        // 3. Renderizamos los datos que vienen de la base de datos
        if (services.length === 0) {
            container.innerHTML = "<p>No hay servicios registrados. Agrégalos en el panel de Admin.</p>";
            return;
        }

        container.innerHTML = services.map(service => {
            // Usamos una imagen por defecto ya que el modelo no tiene campo de imagen aún
            const image = 'odontologia general.png'; 

            return `
            <div class="glow-card-wrapper">
                <div class="service-card">
                    <img src="/static/img/${image}" alt="${service.nombre}" class="service-card-img">
                    <div class="service-card-body">
                        <h4>${service.nombre}</h4>
                        <p class="service-card-description">${service.descripcion}</p>
                        
                        <div class="service-card-details">
                            <span>Precio:</span>
                            <strong>$${parseFloat(service.precio).toFixed(2)}</strong>
                        </div>
                        <div class="service-card-actions">
                            <button class="cyber-btn" style="flex:1;">
                                <i class="ph ph-pencil-simple"></i> Editar
                            </button>
                            <button class="cyber-btn cyber-btn-danger">
                                <i class="ph ph-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            `;
        }).join('');

    } catch (error) {
        console.error("No se pudieron cargar los servicios:", error);
        container.innerHTML = "<p>Error al cargar los servicios. Revisa la consola para más detalles.</p>";
    }
}


function initPatientsPage() {
    const tableBody = document.getElementById('patientsTableBody');
    if (!tableBody) return;
    tableBody.innerHTML = MOCK_DATA.patients.map(p => {
        const statusMap = {
            'Activo': 'accent',
            'En tratamiento': 'primary',
            'Inactivo': 'warning',
            'Con deuda': 'warning',
            'Inactivo (Penalizado)': 'danger'
        };
        const statusColor = statusMap[p.status] || 'primary';
        return `<tr>
            <td>${p.id}</td>
            <td>${p.name}</td>
            <td>${p.email}<br><small class="text-muted">${p.phone}</small></td>
            <td>${p.lastVisit}</td>
            <td><span class="pill" style="background:rgba(var(--color-${statusColor}-cyber-rgb), 0.1); color:var(--color-${statusColor}-cyber);">${p.status}</span></td>
            <td><a href="#" class="action-link">Ver Historial</a></td>
        </tr>`;
    }).join('');
}

function initPaymentsPage() {
    const tableBody = document.getElementById('paymentsTableBody');
    if (!tableBody) return;
    
    tableBody.innerHTML = MOCK_DATA.payments.map(p => `
        <tr>
            <td>${p.id}</td>
            <td>${p.patient}</td>
            <td>${p.date}</td>
            <td>${p.service}</td>
            <td>$${p.amount.toFixed(2)}</td>
            <td><span class="pill ${p.status === 'Pagado' ? 'ok' : 'warn'}">${p.status}</span></td>
            <td><a href="#" class="action-link">${p.action}</a></td>
        </tr>
    `).join('');
}

function initPenaltiesPage() {
    const tableBody = document.getElementById('penaltiesTableBody');
    if (!tableBody) return;

    tableBody.innerHTML = MOCK_DATA.penalties.map(p => {
        const isPending = p.status === 'Pendiente';
        const statusPill = `<span class="pill ${isPending ? 'warn' : 'ok'}">${p.status}</span>`;
        const actionButton = isPending
            ? `<a href="#" class="action-link" data-toast="Estado cambiado a Pagada">Marcar como Pagada</a>`
            : `<a href="#" class="action-link text-muted" style="cursor:default;">-</a>`;

        return `<tr>
            <td>${p.id}</td>
            <td>${p.patientId}</td>
            <td>${p.patient}</td>
            <td>${p.date}</td>
            <td>${p.reason}</td>
            <td>${statusPill}</td>
            <td>$${p.amount.toFixed(2)}</td>
            <td>${actionButton}</td>
        </tr>`;
    }).join('');
}


function initReportsPage(primary, secondary, accent, warning, textMuted, borderSubtle) {
    if (typeof Chart === 'undefined') return;

    const monthlyRevenueEl = document.getElementById('monthlyRevenue');
    if (monthlyRevenueEl) {
        new Chart(monthlyRevenueEl, {
            type: 'line',
            data: {
                labels: ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct'],
                datasets: [{
                    label: 'Ingresos Mensuales',
                    data: [120, 150, 130, 170, 160, 190, 185, 200, 220, 240],
                    borderColor: primary,
                    backgroundColor: 'rgba(0, 224, 255, 0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { display: false }, ticks: { color: textMuted } },
                    y: { grid: { color: borderSubtle }, ticks: { color: textMuted } }
                }
            }
        });
    }

    const doughnutServicesEl = document.getElementById('doughnutServices');
    if (doughnutServicesEl) {
        new Chart(doughnutServicesEl, {
            type: 'doughnut',
            data: {
                labels: ['Ortodoncia', 'Estética', 'Limpieza', 'General'],
                datasets: [{
                    data: [34, 22, 28, 16],
                    backgroundColor: [primary, secondary, accent, warning],
                    borderColor: '#0a0f14',
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { color: textMuted, font: { family: "'Poppins', sans-serif" } }
                    }
                }
            }
        });
    }
}