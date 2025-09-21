// Este script controla la navegación y la interactividad de la aplicación.
(function () {
  // Elementos principales del layout y el modal
  const sidebar = document.getElementById('sidebar');
  const burger = document.getElementById('burgerBtn');
  const backdrop = document.getElementById('backdrop');
  const modal = document.getElementById('modal');
  const modalBody = document.getElementById('modal-body');
  const modalTitle = document.getElementById('modal-title');

  // Función para abrir y cerrar el menú lateral en dispositivos móviles
  function toggleDrawer(open) {
    const willOpen = (typeof open === 'boolean') ? open : !sidebar.classList.contains('open');
    sidebar.classList.toggle('open', willOpen);
    backdrop.hidden = !willOpen;
    burger.setAttribute('aria-expanded', String(willOpen));
    document.documentElement.classList.toggle('no-scroll', willOpen);
  }

  // Función para abrir un modal con un título y contenido
  function openModal(title, contentHTML) {
    if (modal) {
      modalTitle.textContent = title;
      modalBody.innerHTML = contentHTML;
      modal.hidden = false;
      document.documentElement.classList.add('no-scroll');
      modal.focus();
    }
  }

  // Función para cerrar el modal
  function closeModal() {
    if (modal) {
      modal.hidden = true;
      document.documentElement.classList.remove('no-scroll');
      modalTitle.textContent = '';
      modalBody.innerHTML = '';
    }
  }

  // Event Listeners para la navegación y el modal
  if (burger) {
    burger.addEventListener('click', () => toggleDrawer());
    backdrop.addEventListener('click', () => toggleDrawer(false));
    window.addEventListener('keydown', (e) => { if (e.key === 'Escape') toggleDrawer(false); });
    const mq = window.matchMedia('(min-width:1024px)');
    mq.addEventListener('change', e => { if (e.matches) toggleDrawer(false); });
    sidebar.addEventListener('click', (e) => {
      if (!mq.matches && e.target.closest('a')) toggleDrawer(false);
    });
  }

  if (modal) {
    document.getElementById('modalCloseBtn').addEventListener('click', closeModal);
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        closeModal();
      }
    });
  }

  // Lógica para marcar el enlace activo en la barra lateral
  const here = window.location.pathname.replace(/\/$/, '');
  document.querySelectorAll('.sidebar-nav a').forEach(a => {
    const href = a.getAttribute('href')?.replace(/\/$/, '');
    if (href && (here === href || (here.startsWith(href) && href !== '/'))) a.classList.add('is-active');
  });

  // Lógica para los formularios y la interactividad
  document.addEventListener('DOMContentLoaded', () => {
    const currentPage = window.location.pathname;

    // Lógica para la página de la Agenda
    if (currentPage.includes('agenda')) {
      const nuevaCitaBtn = document.querySelector('.page-toolbar .btn-primary');
      if (nuevaCitaBtn) {
        nuevaCitaBtn.addEventListener('click', (e) => {
          e.preventDefault();
          const formHTML = `
            <form class="form">
              <label class="form-field">
                <span>Paciente</span>
                <input type="text" class="form-input" placeholder="Nombre del paciente">
              </label>
              <label class="form-field">
                <span>Servicio</span>
                <select class="form-input">
                  <option>Limpieza bucal</option>
                  <option>Extracción</option>
                  <option>Ortodoncia</option>
                </select>
              </label>
              <label class="form-field">
                <span>Fecha y hora</span>
                <input type="datetime-local" class="form-input">
              </label>
              <div class="modal-actions">
                <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancelar</button>
                <button type="submit" class="btn btn-primary">Guardar cita</button>
              </div>
            </form>
          `;
          openModal('Crear nueva cita', formHTML);
        });
      }
    }

    // Lógica para la página de Pacientes
    if (currentPage.includes('pacientes')) {
      const nuevoPacienteBtn = document.querySelector('.page-toolbar .btn-primary');
      const searchInput = document.querySelector('input[type="search"]');
      const statusFilter = document.querySelector('select.form-input');
      const patientRows = document.querySelectorAll('.table--stack tbody tr');

      if (nuevoPacienteBtn) {
        nuevoPacienteBtn.addEventListener('click', (e) => {
          e.preventDefault();
          const formHTML = `
            <form class="form">
              <label class="form-field">
                <span>Nombre completo</span>
                <input type="text" class="form-input" placeholder="Ej. Ana López">
              </label>
              <label class="form-field">
                <span>Teléfono</span>
                <input type="tel" class="form-input" placeholder="Ej. 55 1234 5678">
              </label>
              <label class="form-field">
                <span>Correo electrónico</span>
                <input type="email" class="form-input" placeholder="Ej. ana@mail.com">
              </label>
              <div class="modal-actions">
                <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancelar</button>
                <button type="submit" class="btn btn-primary">Guardar paciente</button>
              </div>
            </form>
          `;
          openModal('Agregar nuevo paciente', formHTML);
        });
      }

      function filterPatients() {
        const searchTerm = searchInput.value.toLowerCase();
        const status = statusFilter.value.toLowerCase();

        patientRows.forEach(row => {
          const name = row.querySelector('[data-label="Nombre"]').textContent.toLowerCase();
          const phone = row.querySelector('[data-label="Teléfono"]').textContent.toLowerCase();
          const email = row.querySelector('[data-label="Correo electrónico"]').textContent.toLowerCase();
          const patientStatus = row.querySelector('.badge').textContent.toLowerCase();
          
          const matchesSearch = name.includes(searchTerm) || phone.includes(searchTerm) || email.includes(searchTerm);
          const matchesStatus = (status === 'todos') || (patientStatus.includes(status));
          
          row.style.display = (matchesSearch && matchesStatus) ? '' : 'none';
        });
      }

      if (searchInput && statusFilter) {
        searchInput.addEventListener('input', filterPatients);
        statusFilter.addEventListener('change', filterPatients);
      }
    }

    // Lógica para la página de Servicios
    if (currentPage.includes('servicios')) {
      const nuevoServicioBtn = document.querySelector('.page-toolbar .btn-primary');
      if (nuevoServicioBtn) {
        nuevoServicioBtn.addEventListener('click', (e) => {
          e.preventDefault();
          const formHTML = `
            <form class="form">
              <label class="form-field">
                <span>Nombre del servicio</span>
                <input type="text" class="form-input" placeholder="Ej. Limpieza bucal">
              </label>
              <label class="form-field">
                <span>Precio</span>
                <input type="number" class="form-input" placeholder="Ej. 500">
              </label>
              <label class="form-field">
                <span>Duración (minutos)</span>
                <input type="number" class="form-input" placeholder="Ej. 40">
              </label>
              <div class="modal-actions">
                <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancelar</button>
                <button type="submit" class="btn btn-primary">Guardar servicio</button>
              </div>
            </form>
          `;
          openModal('Agregar nuevo servicio', formHTML);
        });
      }
    }

    // Lógica para los gráficos
    const charts = {
      chartCitas: {
        type: 'line', data: { labels: ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'], datasets: [{ label: 'Citas', data: [3, 5, 4, 7, 6, 2, 1], borderColor: '#00bcd4', backgroundColor: 'rgba(0,188,212,.18)', fill: true, tension: .35, pointRadius: 0 }] }, options: { responsive: true, maintainAspectRatio: false, scales: { x: { grid: { display: false } }, y: { beginAtZero: true, grid: { color: 'rgba(127,127,127,.18)' } } }, plugins: { legend: { display: false }, tooltip: { mode: 'index', intersect: false } } }
      },
      paymentsChart: {
        type: 'line', data: { labels: Array.from({length:30}, (_,i)=>`D${i+1}`), datasets: [{ label: 'Ingresos', data: Array.from({length:30}, ()=> Math.round(300 + Math.random()*700)), borderColor: '#00bcd4', backgroundColor: 'rgba(0,188,212,.18)', fill: true, tension: .35, pointRadius: 0 }] }, options: { responsive: true, maintainAspectRatio: false, scales: { x: { grid: { display: false } }, y: { grid: { color: 'rgba(127,127,127,.18)' } } }, plugins: { legend: { display: false } } }
      },
      annualRevenueChart: {
        type: 'bar', data: { labels: ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'], datasets: [{ label: 'Ingresos', data: [4500, 5200, 6100, 5800, 7200, 7500, 8100, 7800, 8500, 9200, 8900, 9500], backgroundColor: '#00bcd4', borderColor: '#00bcd4', borderWidth: 1 }] }, options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true } }, plugins: { legend: { display: false } } }
      },
      servicesChart: {
        type: 'doughnut', data: { labels: ['Limpieza', 'Extracción', 'Ortodoncia', 'Blanqueamiento'], datasets: [{ label: 'Citas por servicio', data: [25, 15, 10, 20], backgroundColor: ['#00bcd4', '#33e08a', '#ffc107', '#ff4757'], hoverOffset: 4 }] }, options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom', labels: { usePointStyle: true } } } }
      },
      attendanceChart: {
        type: 'line', data: { labels: ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep'], datasets: [{ label: 'Tasa de asistencia (%)', data: [88, 90, 91, 95, 92, 94, 93, 96, 92], borderColor: '#33e08a', backgroundColor: 'rgba(51,224,138,.12)', fill: true, tension: 0.4 }] }, options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true, max: 100, title: { display: true, text: 'Porcentaje de Asistencia (%)' } } }, plugins: { legend: { display: false }, tooltip: { mode: 'index', intersect: false } } }
      }
    };
    
    for (const id in charts) {
      const el = document.getElementById(id);
      if (el) {
        new Chart(el, charts[id]);
      }
    }
  });
})();
