document.addEventListener('DOMContentLoaded', function () {
  const ctx = document.getElementById('weeklyActivityChart');
  // Salimos de la función si el elemento canvas no existe en la página actual
  if (!ctx) {
      return;
  }

  const chartCtx = ctx.getContext('2d');

  // --- GRADIENTE PARA LA GRÁFICA ---
  const gradient = chartCtx.createLinearGradient(0, 0, 0, 400);
  gradient.addColorStop(0, 'rgba(48, 162, 255, 0.6)');
  gradient.addColorStop(1, 'rgba(0, 224, 199, 0.1)');

  // --- DATOS (A REEMPLAZAR CON DATOS REALES DEL BACKEND) ---
  const labels = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'];
  const data = {
      labels: labels,
      datasets: [{
          label: 'Número de Citas',
          data: [12, 19, 10, 15, 22, 18, 8], // Datos de ejemplo
          borderColor: '#30A2FF',
          backgroundColor: gradient,
          fill: true,
          tension: 0.4, // Curvas más suaves
          pointBackgroundColor: '#F9FAFB',
          pointBorderColor: '#30A2FF',
          pointRadius: 5,
          pointHoverRadius: 8
      }]
  };

  // --- CONFIGURACIÓN DE LA GRÁFICA ---
  const config = {
      type: 'line',
      data: data,
      options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
              legend: {
                  display: false
              },
              tooltip: {
                  backgroundColor: '#121826',
                  titleFont: { size: 16, weight: 'bold' },
                  bodyFont: { size: 14 },
                  padding: 12,
                  cornerRadius: 8,
                  displayColors: false
              }
          },
          scales: {
              y: {
                  beginAtZero: true,
                  grid: {
                      color: 'rgba(57, 67, 89, 0.5)'
                  },
                  ticks: {
                      color: '#A0AEC0'
                  }
              },
              x: {
                  grid: {
                      display: false
                  },
                  ticks: {
                      color: '#A0AEC0'
                  }
              }
          }
      }
  };

  new Chart(chartCtx, config);
});
