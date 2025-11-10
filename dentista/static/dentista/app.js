/* === DENTIST DASHBOARD APP.JS (CONECTADO A BD) === */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Reloj en tiempo real
    const clockElement = document.getElementById('live-datetime-dentist');
    if (clockElement) {
        const updateClock = () => {
            const now = new Date();
            const dateStr = now.toLocaleDateString('es-MX', { weekday: 'long', day: 'numeric', month: 'long' });
            const timeStr = now.toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit' });
            clockElement.textContent = `${dateStr.charAt(0).toUpperCase() + dateStr.slice(1)} | ${timeStr}`;
        };
        updateClock();
        setInterval(updateClock, 30000); // Actualiza cada 30 seg
    }

    // 2. Gráfica Financiera REAL (Conectada a la BD)
    initRealFinanceChart();
});

function initRealFinanceChart() {
    const canvas = document.getElementById('balanceChart');
    if (!canvas || typeof Chart === 'undefined') return;
    const ctx = canvas.getContext('2d');

    // Llamamos a la API que creamos en views.py
    fetch('/dentista/api/grafica/ingresos/')
        .then(response => response.json())
        .then(data => {
            
            // Si no hay datos, mostramos un placeholder
            const labels = data.labels.length ? data.labels : ['Sin Ingresos'];
            const ingresos = data.ingresos.length ? data.ingresos : [0];

            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Ingresos',
                        data: ingresos,
                        borderColor: '#00ffc3',
                        backgroundColor: 'rgba(0, 255, 195, 0.15)',
                        tension: 0.4,
                        fill: true,
                        borderWidth: 3,
                        pointBackgroundColor: '#00ffc3',
                        pointBorderColor: '#0b1220',
                        pointBorderWidth: 2,
                        pointRadius: 5
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: { label: (c) => ` $${c.raw.toLocaleString()}` }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: { color: 'rgba(255, 255, 255, 0.05)' },
                            ticks: { color: '#9ca3af', callback: value => '$' + value }
                        },
                        x: {
                            grid: { display: false },
                            ticks: { color: '#9ca3af' }
                        }
                    }
                }
            });
        })
        .catch(error => {
            console.error("Error al cargar la gráfica:", error);
            ctx.font = "16px Inter";
            ctx.fillStyle = "#9ca3af";
            ctx.textAlign = "center";
            ctx.fillText("Error al cargar datos", canvas.width / 2, canvas.height / 2);
        });
}