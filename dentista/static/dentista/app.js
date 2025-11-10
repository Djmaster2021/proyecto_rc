// static/dentista/app.js
// Versión Profesional Limpia - Solo lógica de UI interactiva y Gráficas reales

document.addEventListener('DOMContentLoaded', () => {
    initUI();
});

function initUI() {
    // Iniciar componentes interactivos
    initClock('live-datetime-dentist');
    initBurger();
    initTabs();
    initModals();
    initCounters();
    
    // Iniciar gráficas con datos reales
    initRealFinanceChart();
}

// --- 1. RELOJ EN TIEMPO REAL ---
function initClock(elementId) {
    const clockElement = document.getElementById(elementId);
    if (clockElement) {
        const updateClock = () => {
            const now = new Date();
            // Formato amigable: "Sábado, 9 de noviembre de 2025 | 10:30:15 a. m."
            const dateStr = now.toLocaleDateString('es-MX', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
            const timeStr = now.toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit' });
            clockElement.innerHTML = `${dateStr.charAt(0).toUpperCase() + dateStr.slice(1)} | ${timeStr}`;
        };
        updateClock();
        setInterval(updateClock, 1000); // Actualiza cada segundo
    }
}

// --- 2. MENÚ HAMBURGUESA (Móvil) ---
function initBurger() {
    const burger = document.getElementById('burger');
    const sidebar = document.getElementById('sidebar');
    if (burger && sidebar) {
        burger.addEventListener('click', () => {
            sidebar.classList.toggle('active'); // Asegúrate que tu CSS use esta clase para mostrar/ocultar
        });
    }
}

// --- 3. SISTEMA DE PESTAÑAS (Tabs) ---
function initTabs() {
    const tabsContainer = document.querySelector('.tabs');
    if (!tabsContainer) return;
    tabsContainer.addEventListener('click', (e) => {
        const tab = e.target.closest('.tab');
        if (!tab) return;
        
        // Quitar activo anterior
        tabsContainer.querySelector('.tab.active')?.classList.remove('active');
        document.querySelector('.panel.active')?.classList.remove('active');
        
        // Activar nuevo
        tab.classList.add('active');
        const targetPanel = document.getElementById(tab.dataset.tab);
        if (targetPanel) targetPanel.classList.add('active');
    });
}

// --- 4. SISTEMA DE MODALES ---
function initModals() {
    // Cerrar al dar clic en la X o fuera del modal
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal-overlay') || e.target.classList.contains('modal-close')) {
            const modal = e.target.closest('.modal-overlay');
            if (modal) modal.style.display = 'none';
        }
    });
}

// --- 5. ANIMACIÓN DE CONTADORES (KPIs) ---
function initCounters() {
    document.querySelectorAll('[data-counter]').forEach(el => {
        const target = parseInt(el.innerText, 10); // Lee el valor real que puso Django
        if (isNaN(target)) return;
        
        let current = 0;
        const increment = Math.ceil(target / 20); // Velocidad de animación
        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                el.innerText = target; // Asegura el valor final exacto
                clearInterval(timer);
            } else {
                el.innerText = current;
            }
        }, 30);
    });
}

// --- 6. GRÁFICA FINANCIERA REAL (Chart.js + API Django) ---
function initRealFinanceChart() {
    const chartCanvas = document.getElementById('balanceChart');
    if (!chartCanvas) return; // Si no estamos en el dashboard, no hacemos nada

    fetch('/dentista/api/grafica/ingresos/')
        .then(response => {
            if (!response.ok) throw new Error("Error de red al obtener datos gráficos");
            return response.json();
        })
        .then(data => {
            // Si no hay datos, mostramos un placeholder elegante
            const labels = data.labels.length ? data.labels : ['Sin datos'];
            const ingresos = data.labels.length ? data.ingresos : [0];

            new Chart(chartCanvas, {
                type: 'line', // Línea se ve mejor para tendencias de tiempo
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Ingresos Reales ($)',
                        data: ingresos,
                        borderColor: '#2ee6a6',      // Verde neón
                        backgroundColor: 'rgba(46, 230, 166, 0.1)', // Relleno transparente
                        borderWidth: 3,
                        tension: 0.4, // Curvatura suave de la línea
                        fill: true,
                        pointBackgroundColor: '#2ee6a6',
                        pointBorderColor: '#0b1220',
                        pointBorderWidth: 2,
                        pointRadius: 5,
                        pointHoverRadius: 7
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }, // Minimalista, sin leyenda si solo hay 1 dato
                        tooltip: {
                            backgroundColor: '#1e293b',
                            titleColor: '#e8eef7',
                            bodyColor: '#2ee6a6',
                            bodyFont: { weight: 'bold', size: 14 },
                            padding: 12,
                            cornerRadius: 8,
                            callbacks: {
                                label: (c) => ` Ingresos: $${c.raw.toLocaleString('es-MX', {minimumFractionDigits: 2})}`
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: { color: 'rgba(255, 255, 255, 0.05)' },
                            ticks: { 
                                color: '#93a1b3',
                                font: { family: "'Poppins', sans-serif" },
                                callback: value => '$' + value.toLocaleString('es-MX') // Formato moneda eje Y
                            }
                        },
                        x: {
                            grid: { display: false },
                            ticks: { color: '#e8eef7', font: { family: "'Poppins', sans-serif" } }
                        }
                    }
                }
            });
        })
        .catch(err => console.warn("⚠️ No se pudo cargar la gráfica financiera:", err));
}