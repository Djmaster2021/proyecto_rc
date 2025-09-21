// Inicializa toda la UI del dashboard cuando el DOM está listo
document.addEventListener('DOMContentLoaded', () => {
    initUI();
});

function initUI() {
    setLiveClock();
    setLastUpdate();
    initBurger();
    initTabs();
    initModals();
    initToast();
    initCounters();
    renderCharts();
    renderAllData();
    initAgenda();
    initPaymentsPage();
    initServicesPage();
    initPatientsPage();
    initReportsPage();
    initPatientHistoryPage();
    initAccordion();
}

/* --- Funciones de Layout y UI --- */
// Reloj en tiempo real
function setLiveClock() {
    const clockElement = document.getElementById('liveClock');
    if (clockElement) {
        setInterval(() => {
            const now = new Date();
            const dateStr = now.toLocaleDateString('es-MX', { day: '2-digit', month: '2-digit', year: 'numeric' });
            const timeStr = now.toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit' });
            clockElement.textContent = `${dateStr} ${timeStr}`;
        }, 1000);
    }
}

// Estampa de hora para la última actualización
function setLastUpdate() {
    const lastUpdateElement = document.getElementById('lastUpdate');
    if (lastUpdateElement) {
        lastUpdateElement.textContent = new Date().toLocaleString('es-MX', {
            dateStyle: 'short',
            timeStyle: 'short'
        });
    }
}

// Sidebar hamburger
function initBurger() {
    const burger = document.getElementById('burger');
    const side = document.getElementById('sidebar');
    const shell = document.querySelector('.shell');
    if (burger && side && shell) {
        burger.addEventListener('click', () => {
            shell.classList.toggle('collapsed');
        });
    }
}

// Tabs
function initTabs() {
    const tabsContainer = document.querySelector('.tabs');
    if (!tabsContainer) return;
    tabsContainer.addEventListener('click', (e) => {
        const tab = e.target.closest('.tab');
        if (!tab) return;

        const activeTab = tabsContainer.querySelector('.tab.active');
        if (activeTab) {
            activeTab.classList.remove('active');
            const activePanel = document.getElementById(activeTab.dataset.tab);
            if (activePanel) {
                activePanel.classList.remove('active');
            }
        }

        tab.classList.add('active');
        const targetPanel = document.getElementById(tab.dataset.tab);
        if (targetPanel) {
            targetPanel.classList.add('active');
        }
    });
}

// Modal open/close
function initModals() {
    document.body.addEventListener('click', e => {
        const openBtn = e.target.closest('[data-modal]');
        if (openBtn) {
            const modalId = openBtn.dataset.modal;
            const modal = document.querySelector(modalId);
            if (modal) {
                modal.classList.add('show');
            }
        }

        const closeBtn = e.target.closest('[data-close]');
        if (closeBtn) {
            const modal = closeBtn.closest('.modal');
            if (modal) {
                modal.classList.remove('show');
            }
        }
    });
}

// Toast simple
function initToast() {
    const toastNode = document.getElementById('toast');
    if (!toastNode) return;

    document.body.addEventListener('click', e => {
        const btn = e.target.closest('[data-toast]');
        if (btn) {
            showToast(btn.dataset.toast);
        }
    });
}

function showToast(message) {
    const toastNode = document.getElementById('toast');
    if (!toastNode) return;

    toastNode.textContent = message;
    toastNode.classList.add('show');
    clearTimeout(toastNode._timeoutId);
    toastNode._timeoutId = setTimeout(() => {
        toastNode.classList.remove('show');
    }, 2400);
}

// Animación de contadores
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
            el.textContent = cur;
        }, 10);
    });
}

// Charts con Chart.js
function renderCharts() {
    if (typeof Chart === 'undefined') return;

    const balanceChartEl = document.getElementById('balanceChart');
    if (balanceChartEl) {
        new Chart(balanceChartEl.getContext('2d'), {
            type: 'bar',
            data: {
                labels: ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep'],
                datasets: [{
                    label: 'Ingresos',
                    data: [12000, 15000, 13000, 17000, 16000, 19000, 18500, 20000, 22000],
                    backgroundColor: 'rgba(0,240,255,0.7)',
                    borderRadius: 5
                }, {
                    label: 'Gastos',
                    data: [4000, 3500, 5000, 4500, 6000, 5500, 6200, 5800, 7000],
                    backgroundColor: 'rgba(138,99,255,0.7)',
                    borderRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: '#9bb0c6'
                        }
                    }
                },
                scales: {
                    x: {
                        stacked: true,
                        grid: {
                            color: 'rgba(255,255,255,0.1)'
                        },
                        ticks: {
                            color: '#9bb0c6'
                        }
                    },
                    y: {
                        stacked: true,
                        grid: {
                            color: 'rgba(255,255,255,0.1)'
                        },
                        ticks: {
                            color: '#9bb0c6'
                        }
                    }
                }
            }
        });
    }
}

/* --- Mock Data (Simulación de Backend) --- */

const MOCK_DATA = {
    audit: [{
        t: '20 Sep 2025, 14:35',
        user: 'Dr. Castellón',
        action: 'Cita creada',
        details: 'Agendó a Ana García.'
    }, {
        t: '20 Sep 2025, 14:00',
        user: 'Sistema',
        action: 'Recordatorio enviado',
        details: 'Recordatorio a Juan Perez.'
    }, {
        t: '19 Sep 2025, 18:00',
        user: 'Ana García',
        action: 'Pago recibido',
        details: 'Recibió pago en línea de $850.'
    }, {
        t: '19 Sep 2025, 17:00',
        user: 'Dr. Castellón',
        action: 'Servicio actualizado',
        details: 'Actualizó el precio de Blanqueamiento.'
    }],
    treatmentPlans: [{
        patient: 'Juan Pérez',
        treatment: 'Ortodoncia (Fase 1)',
        progress: '25%',
        lastUpdate: '18 Sep 2025'
    }, {
        patient: 'Laura García',
        treatment: 'Limpieza y Resina',
        progress: '100%',
        lastUpdate: '20 Sep 2025'
    }],
    inventory: [{
        product: 'Resina Composita',
        category: 'Materiales',
        stock: '12 unidades',
        expiryDate: '10/2026'
    }, {
        product: 'Guantes Nitrilo',
        category: 'Consumibles',
        stock: 'Bajo',
        expiryDate: 'N/A'
    }],
    budgets: [{
        title: 'Implante dental',
        patient: 'Carlos Ruiz',
        date: '20 Sep 2025',
        amount: '$9,800.00'
    }, {
        title: 'Extracción de muela',
        patient: 'Sofía López',
        date: '19 Sep 2025',
        amount: '$1,200.00'
    }],
    agendaAppointments: {
        '2025-09-22': [{
            time: '10:00 AM',
            patient: 'Ana García',
            service: 'Limpieza',
            status: 'Confirmada',
            id: 'A-223'
        }, {
            time: '04:00 PM',
            patient: 'Emilio Segura',
            service: 'Ortodoncia',
            status: 'Pendiente',
            id: 'A-224'
        }],
        '2025-09-23': [{
            time: '11:30 AM',
            patient: 'Carlos López',
            service: 'Blanqueamiento',
            status: 'Confirmada',
            id: 'A-225'
        }],
        '2025-09-24': [],
        '2025-09-25': [{
            time: '03:00 PM',
            patient: 'María Ruiz',
            service: 'Resina',
            status: 'Pendiente',
            id: 'A-226'
        }],
        '2025-09-26': [{
            time: '09:00 AM',
            patient: 'Juan Rodríguez',
            service: 'Extracción',
            status: 'Confirmada',
            id: 'A-227'
        }, {
            time: '10:30 AM',
            patient: 'Daniela Aceves',
            service: 'Revisión',
            status: 'Confirmada',
            id: 'A-228'
        }],
        '2025-09-27': [],
        '2025-09-28': []
    },
    payments: [{
        id: 'P-001',
        date: '2025-09-20',
        patient: 'Ana García',
        service: 'Ortodoncia',
        amount: 2500,
        status: 'Pagado',
        action: 'Recibo'
    }, {
        id: 'P-002',
        date: '2025-09-18',
        patient: 'Laura M.',
        service: 'Limpieza',
        amount: 850,
        status: 'Pendiente',
        action: 'Recordar'
    }, {
        id: 'P-003',
        date: '2025-09-15',
        patient: 'Juan D.',
        service: 'Resina',
        amount: 1500,
        status: 'Pagado',
        action: 'Recibo'
    }, {
        id: 'P-004',
        date: '2025-09-12',
        patient: 'Sofía S.',
        service: 'Blanqueamiento',
        amount: 1200,
        status: 'Pendiente',
        action: 'Recordar'
    }],
    services: {
        general: [{
            procedure: 'Limpieza profunda',
            duration: '45–60 min',
            price: '$600',
            notes: 'Incluye instrucción de higiene',
        }, {
            procedure: 'Radiografías',
            duration: '10–20 min',
            price: '$200',
            notes: 'Periapical / aleta de mordida',
        }, {
            procedure: 'Resinas',
            duration: '40–60 min',
            price: '$800',
            notes: 'Material compósito',
        }, {
            procedure: 'Extracciones',
            duration: '30–50 min',
            price: 'desde $500',
            notes: 'Considerar remisión si quirúrgica',
        }],
        aesthetic: [{
            procedure: 'Blanqueamiento',
            duration: '60 min',
            price: '$1,200',
            notes: 'Requiere evaluación previa',
        }, {
            procedure: 'Carillas',
            duration: '90–120 min',
            price: 'desde $3,500',
            notes: 'Plan digital recomendado',
        }, {
            procedure: 'Resinas estéticas',
            duration: '45 min',
            price: 'desde $900',
            notes: '',
        }, {
            procedure: 'Contorneado dental',
            duration: '30 min',
            price: '$700',
            notes: '',
        }],
        orthodontics: [{
            procedure: 'Brackets',
            duration: '30-45 min',
            price: 'desde $18,000',
            notes: 'Planes fijos',
        }, {
            procedure: 'Alineadores',
            duration: '20-30 min',
            price: 'desde $22,000',
            notes: 'Planes removibles',
        }, {
            procedure: 'Retenedores',
            duration: '15 min',
            price: '$1,200',
            notes: 'Retenedores fijos o removibles',
        }]
    },
    patients: [{
        id: 'P-001',
        name: 'Ana García',
        email: 'ana.g@ejemplo.com',
        phone: '+52 55 1234 5678',
        lastVisit: '2025-09-20',
        status: 'Activo'
    }, {
        id: 'P-002',
        name: 'Carlos López',
        email: 'carlos@ej.com',
        phone: '+52 55 8765 4321',
        lastVisit: '2025-09-18',
        status: 'En tratamiento'
    }, {
        id: 'P-003',
        name: 'Juan Rodríguez',
        email: 'juan.r@ej.com',
        phone: '+52 55 1122 3344',
        lastVisit: '2025-01-05',
        status: 'Inactivo'
    }, {
        id: 'P-004',
        name: 'María Ruíz',
        email: 'maria.r@ej.com',
        phone: '+52 55 9988 7766',
        lastVisit: '2025-09-25',
        status: 'Con deuda'
    }],
    patientHistory: [{
        date: '2025-09-20',
        service: 'Ortodoncia (ajuste)',
        amount: 2500,
        status: 'Pagado',
    },{
        date: '2025-08-15',
        service: 'Limpieza profunda',
        amount: 850,
        status: 'Pendiente',
    },{
        date: '2025-07-28',
        service: 'Revisión',
        amount: 0,
        status: 'Pagado',
    }, {
        date: '2025-05-10',
        service: 'Blanqueamiento',
        amount: 1200,
        status: 'Pagado',
    }]
};

function renderAllData() {
    renderAuditList();
    renderTreatmentPlansTable();
    renderInventoryTable();
    renderBudgetsTable();
}

/* --- Funciones de Renderizado --- */

function renderAuditList() {
    const list = document.getElementById('auditList');
    if (!list) return;
    list.innerHTML = '';
    MOCK_DATA.audit.forEach(item => {
        const li = document.createElement('li');
        li.innerHTML = `
            <div>
                <strong>${item.action}</strong>
                <span class="muted tiny">${item.details}</span>
            </div>
            <span class="muted tiny">${item.t}</span>
        `;
        list.appendChild(li);
    });
}

function renderTreatmentPlansTable() {
    const tableBody = document.querySelector('#treatmentTable tbody');
    if (!tableBody) return;
    tableBody.innerHTML = '';
    MOCK_DATA.treatmentPlans.forEach(item => {
        const row = tableBody.insertRow();
        row.innerHTML = `
            <td>${item.patient}</td>
            <td>${item.treatment}</td>
            <td>${item.progress}</td>
            <td>${item.lastUpdate}</td>
        `;
    });
}

function renderInventoryTable() {
    const tableBody = document.querySelector('#inventoryTable tbody');
    if (!tableBody) return;
    tableBody.innerHTML = '';
    MOCK_DATA.inventory.forEach(item => {
        const row = tableBody.insertRow();
        row.innerHTML = `
            <td>${item.product}</td>
            <td>${item.category}</td>
            <td>${item.stock}</td>
            <td>${item.expiryDate}</td>
        `;
    });
}

function renderBudgetsTable() {
    const tableBody = document.querySelector('#budgetTable tbody');
    if (!tableBody) return;
    tableBody.innerHTML = '';
    MOCK_DATA.budgets.forEach(item => {
        const row = tableBody.insertRow();
        row.innerHTML = `
            <td>${item.title}</td>
            <td>${item.patient}</td>
            <td>${item.date}</td>
            <td>${item.amount}</td>
        `;
    });
}

// Lógica de Pagos
function initPaymentsPage() {
    const paymentsTableBody = document.getElementById('paymentsTableBody');
    if (!paymentsTableBody) return;

    renderPaymentsTable(MOCK_DATA.payments);

    const searchInput = document.getElementById('paymentsSearchInput');
    searchInput?.addEventListener('input', () => {
        const searchTerm = searchInput.value.toLowerCase();
        const filteredPayments = MOCK_DATA.payments.filter(p =>
            p.patient.toLowerCase().includes(searchTerm) ||
            p.service.toLowerCase().includes(searchTerm)
        );
        renderPaymentsTable(filteredPayments);
    });
}

function renderPaymentsTable(payments) {
    const paymentsTableBody = document.getElementById('paymentsTableBody');
    if (!paymentsTableBody) return;
    paymentsTableBody.innerHTML = '';
    payments.forEach(p => {
        const row = paymentsTableBody.insertRow();
        const statusClass = p.status === 'Pagado' ? 'badge-green' : 'badge-yellow';
        const actionText = p.action === 'Recibo' ? 'Recibo' : 'Recordar';
        row.innerHTML = `
            <td>${p.id}</td>
            <td>${p.patient}</td>
            <td>${p.date}</td>
            <td>${p.service}</td>
            <td>$${p.amount.toFixed(2)}</td>
            <td><span class="badge ${statusClass}">${p.status}</span></td>
            <td><a class="action-link" href="#">${actionText}</a></td>
        `;
    });
}

// Lógica de Agenda
function initAgenda() {
    renderAgenda();
    renderUpcomingApptsTable();
}

function renderAgenda() {
    const agendaGrid = document.getElementById('agendaGrid');
    if (!agendaGrid) return;

    const days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];
    const startDate = new Date('2025-09-22T00:00:00');

    agendaGrid.innerHTML = '';
    for (let i = 0; i < 7; i++) {
        const currentDate = new Date(startDate);
        currentDate.setDate(startDate.getDate() + i);
        const dayDate = currentDate.toISOString().split('T')[0];
        const dayAppointments = MOCK_DATA.agendaAppointments[dayDate] || [];

        const dayCell = document.createElement('div');
        dayCell.className = 'day-cell';

        const dayName = days[currentDate.getDay() === 0 ? 6 : currentDate.getDay() - 1];
        dayCell.innerHTML = `
            <div class="day-header">
                <span class="day-name">${dayName}</span>
                <span class="day-date">${currentDate.getDate()}</span>
            </div>
            <div class="appointment-list"></div>
        `;

        const appointmentList = dayCell.querySelector('.appointment-list');
        if (dayAppointments.length === 0) {
            appointmentList.innerHTML = `<div class="no-appointments">Sin citas programadas</div>`;
        } else {
            dayAppointments.forEach(appt => {
                const apptCard = document.createElement('div');
                apptCard.className = 'appointment-card';
                apptCard.innerHTML = `
                    <div class="appt-time">${appt.time}</div>
                    <div class="appt-patient"><strong>${appt.patient}</strong></div>
                    <div class="appt-service muted">${appt.service}</div>
                    <div class="appt-status">
                        <span class="pill ${appt.status === 'Confirmada' ? 'ok' : 'warn'}">${appt.status}</span>
                    </div>
                `;
                appointmentList.appendChild(apptCard);
            });
        }
        agendaGrid.appendChild(dayCell);
    }
}

// Nueva función para renderizar la tabla detallada de citas
function renderUpcomingApptsTable() {
    const tableBody = document.getElementById('upcomingApptsTableBody');
    if (!tableBody) return;
    tableBody.innerHTML = '';

    const allAppointments = Object.values(MOCK_DATA.agendaAppointments).flat();

    allAppointments.forEach(appt => {
        const row = tableBody.insertRow();
        const statusClass = appt.status === 'Confirmada' ? 'badge-green' : 'badge-yellow';
        row.innerHTML = `
            <td>${appt.id}</td>
            <td>${appt.patient}</td>
            <td>${new Date('2025-09-22T00:00:00').toLocaleDateString()}</td>
            <td>${appt.time}</td>
            <td>${appt.service}</td>
            <td><span class="badge ${statusClass}">${appt.status}</span></td>
            <td>
                <button class="btn-chip" data-action="reprogramar">Reprogramar</button>
                <button class="btn-danger-chip" data-action="cancelar">Cancelar</button>
            </td>
        `;
    });
}


// Lógica para la página de servicios
function initServicesPage() {
    renderServicesTable('general', MOCK_DATA.services.general);
    renderServicesTable('aesthetic', MOCK_DATA.services.aesthetic);
    renderServicesTable('orthodontics', MOCK_DATA.services.orthodontics);
}

function renderServicesTable(category, data) {
    const tableBody = document.getElementById(`${category}ServicesTableBody`);
    if (!tableBody) return;
    tableBody.innerHTML = '';

    data.forEach(service => {
        const row = tableBody.insertRow();
        row.innerHTML = `
            <td>${service.procedure}</td>
            <td>${service.duration}</td>
            <td>${service.price}</td>
            <td>${service.notes}</td>
            <td>
                <button class="btn-chip" data-action="edit">Editar</button>
                <button class="btn-danger-chip" data-action="delete">Eliminar</button>
            </td>
        `;
    });
}
// Nueva lógica para la página de pacientes
function initPatientsPage() {
    const patientsTableBody = document.getElementById('patientsTableBody');
    if (!patientsTableBody) return;

    renderPatientsTable(MOCK_DATA.patients);

    const searchInput = document.getElementById('patientsSearchInput');
    searchInput?.addEventListener('input', () => {
        const searchTerm = searchInput.value.toLowerCase();
        const filteredPatients = MOCK_DATA.patients.filter(p =>
            p.name.toLowerCase().includes(searchTerm) ||
            p.email.toLowerCase().includes(searchTerm) ||
            p.phone.toLowerCase().includes(searchTerm)
        );
        renderPatientsTable(filteredPatients);
    });
}

function renderPatientsTable(patients) {
    const patientsTableBody = document.getElementById('patientsTableBody');
    if (!patientsTableBody) return;
    patientsTableBody.innerHTML = '';

    patients.forEach(patient => {
        const statusClass = {
            'Activo': 'badge-green',
            'En tratamiento': 'badge-cyan',
            'Inactivo': 'badge-danger',
            'Con deuda': 'badge-yellow'
        }[patient.status] || 'badge-cyan';

        const row = patientsTableBody.insertRow();
        row.innerHTML = `
            <td>${patient.name}</td>
            <td>${patient.email}<br><span class="muted tiny">${patient.phone}</span></td>
            <td>${patient.lastVisit}</td>
            <td><span class="badge ${statusClass}">${patient.status}</span></td>
            <td>
                <a class="action-link" href="#">Historial</a> • 
                <a class="action-link" href="#">Portal</a>
            </td>
        `;
    });
}

function initReportsPage() {
    renderReportsServicesTable();
    renderReportsCharts();
}

function renderReportsServicesTable() {
    const tableBody = document.getElementById('servicesReportTableBody');
    if (!tableBody) return;
    tableBody.innerHTML = '';

    const reports = [{
        service: 'Ortodoncia',
        times: 245,
        totalRevenue: 245000,
        noShowRate: '8%'
    }, {
        service: 'Blanqueamiento',
        times: 160,
        totalRevenue: 192000,
        noShowRate: '5%'
    }, {
        service: 'Limpieza',
        times: 320,
        totalRevenue: 272000,
        noShowRate: '12%'
    }, {
        service: 'Extracciones',
        times: 95,
        totalRevenue: 47500,
        noShowRate: '4%'
    }];

    reports.forEach(report => {
        const row = tableBody.insertRow();
        row.innerHTML = `
            <td>${report.service}</td>
            <td>${report.times}</td>
            <td>$${report.totalRevenue.toLocaleString()}</td>
            <td>${report.noShowRate}</td>
        `;
    });
}

function renderReportsCharts() {
    if (typeof Chart === 'undefined') return;

    const monthlyRevenueChartEl = document.getElementById('monthlyRevenue');
    new Chart(monthlyRevenueChartEl.getContext('2d'), {
        type: 'bar',
        data: {
            labels: ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'],
            datasets: [{
                label: 'Ingresos Mensuales',
                data: [12000, 9000, 15000, 11000, 16000, 14000, 17000, 18000, 15000, 16000, 17500, 19000],
                backgroundColor: 'rgba(138,99,255,0.7)',
                borderRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { ticks: { color: '#93a4b6' } },
                y: { ticks: { color: '#93a4b6' } }
            }
        }
    });

    const doughnutServicesEl = document.getElementById('doughnutServices');
    new Chart(doughnutServicesEl.getContext('2d'), {
        type: 'doughnut',
        data: {
            labels: ['Ortodoncia (34%)', 'Estética (22%)', 'Limpieza (28%)', 'Implantes (16%)'],
            datasets: [{
                data: [34, 22, 28, 16],
                backgroundColor: ['var(--c1)', 'var(--c2)', 'var(--c3)', 'var(--c4)'],
                borderColor: 'var(--panel)',
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: 'var(--ink)' }
                }
            }
        }
    });
}

function initPatientHistoryPage() {
    const patientHistoryTableBody = document.getElementById('patientHistoryTableBody');
    if (!patientHistoryTableBody) return;

    renderPatientHistoryTable(MOCK_DATA.patientHistory);
}

function renderPatientHistoryTable(history) {
    const tableBody = document.getElementById('patientHistoryTableBody');
    if (!tableBody) return;
    tableBody.innerHTML = '';

    history.forEach(item => {
        const row = tableBody.insertRow();
        const statusClass = item.status === 'Pagado' ? 'badge-green' : 'badge-yellow';
        row.innerHTML = `
            <td>${item.date}</td>
            <td>${item.service}</td>
            <td>$${item.amount.toLocaleString()}</td>
            <td><span class="badge ${statusClass}">${item.status}</span></td>
            <td><a class="action-link" href="#">Ver recibo</a></td>
        `;
    });
}

function initAccordion() {
    document.querySelectorAll('.accordion-header').forEach(header => {
        header.addEventListener('click', () => {
            const item = header.closest('.accordion-item');
            if (item) {
                item.classList.toggle('active');
            }
        });
    });
}