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

// Dashboard Paciente: agendar / reprogramar / cancelar / editar perfil
document.addEventListener('DOMContentLoaded', () => {
  const modal = document.getElementById('modal-cita');
  const formCita = document.getElementById('form-cita');
  const titleModal = document.getElementById('modal-title');
  const servicioInput = document.getElementById('cita-servicio');
  const fechaInput = document.getElementById('cita-fecha');
  const horaInput = document.getElementById('cita-hora');
  const btnSubmit = document.getElementById('btn-submit-cita');
  const modalPerfil = document.getElementById('modal-perfil');
  const formCancelar = document.getElementById('form-cancelar');

  // Si no estamos en el dashboard, salimos
  if (!modal || !formCita || !servicioInput || !fechaInput || !horaInput) {
    return;
  }

  // Flatpickr para fechas de cita
  let calendar = null;
  if (typeof flatpickr !== 'undefined') {
    calendar = flatpickr(fechaInput, {
      locale: 'es',
      minDate: 'today',
      maxDate: new Date().fp_incr(30),
      dateFormat: 'Y-m-d',
      disable: [
        function (date) {
          // 0 = domingo
          return date.getDay() === 0;
        }
      ],
      onChange: function (selectedDates, dateStr) {
        consultarHorarios(dateStr);
      }
    });
  }

  function cerrarModal() {
    modal.classList.remove('is-visible');
    formCita.reset();
    if (calendar) {
      calendar.clear();
    }
    horaInput.innerHTML = '<option value="">-- Primero fecha --</option>';
    horaInput.disabled = true;
    fechaInput.disabled = true;
    servicioInput.disabled = false;
    btnSubmit.disabled = true;
  }

  window.cerrarModal = cerrarModal;

  window.abrirModalAgendar = function () {
    titleModal.innerHTML = '<i class="ph-duotone ph-calendar-plus"></i> Agendar Cita';
    // El action ya viene con {% url 'paciente:agendar_crear' %}
    modal.classList.add('is-visible');
  };

  window.verificarReprogramacion = function (citaId, servicioId, vecesReprogramada) {
    if (typeof Swal === 'undefined') return;

    if (vecesReprogramada >= 1) {
      Swal.fire({
        title: 'Límite de reprogramación alcanzado',
        text: 'Ya reprogramaste esta cita una vez. Para volver a reprogramar, deberás avisarle al dentista directamente.',
        icon: 'info',
        confirmButtonText: 'Entendido',
        confirmButtonColor: '#0D8ABC',
        background: '#1e293b',
        color: '#fff'
      });
      return;
    }

    Swal.fire({
      title: '¿Deseas reprogramar?',
      html: "<p>Solamente se puede reprogramar <b>1 sola vez</b>.</p><p>Para volver a cancelar o reprogramar en el futuro, deberás avisarle al dentista para que él lo haga.</p>",
      icon: 'warning',
      showCancelButton: true,
      confirmButtonText: 'Continuar y reprogramar',
      confirmButtonColor: '#0D8ABC',
      cancelButtonColor: '#334155',
      background: '#1e293b',
      color: '#fff'
    }).then(result => {
      if (result.isConfirmed) {
        titleModal.innerHTML = '<i class="ph-duotone ph-calendar-plus"></i> Reprogramar Cita';
        formCita.action = `/paciente/reprogramar/${citaId}/`;
        servicioInput.value = servicioId;
        servicioInput.disabled = true;
        fechaInput.disabled = false;
        modal.classList.add('is-visible');
      }
    });
  };

  window.confirmarCancelacion = function (citaId) {
    if (typeof Swal === 'undefined') return;

    Swal.fire({
      title: '¿Seguro que deseas cancelar?',
      html: "<p>Solamente se puede cancelar <b>1 sola vez</b>.</p><p>Recuerda que debes hacerlo con <b>1 día de anticipación</b>.</p><p style='color:#ef4444; margin-top:10px;'>⚠️ Si cancelas ahora, perderás tu lugar.</p>",
      icon: 'warning',
      showCancelButton: true,
      confirmButtonText: 'Sí, cancelar',
      confirmButtonColor: '#ef4444',
      background: '#1e293b',
      color: '#fff'
    }).then(result => {
      if (result.isConfirmed && formCancelar) {
        formCancelar.action = `/paciente/cancelar/${citaId}/`;
        formCancelar.submit();
      }
    });
  };

  if (servicioInput) {
    servicioInput.addEventListener('change', function () {
      if (this.value) {
        fechaInput.disabled = false;
        if (calendar) {
          calendar.clear();
        }
      } else {
        fechaInput.disabled = true;
      }
    });
  }

  async function consultarHorarios(fechaStr) {
    const servicioId = servicioInput.value;
    if (!servicioId) return;

    horaInput.innerHTML = '<option>Cargando...</option>';
    horaInput.disabled = true;
    btnSubmit.disabled = true;

    try {
      const res = await fetch(`/paciente/api/horarios/?fecha=${fechaStr}&servicio_id=${servicioId}`);
      const horarios = await res.json();
      horaInput.innerHTML = '';
      if (horarios.length > 0) {
        horarios.forEach(h => {
          const opt = document.createElement('option');
          opt.value = h;
          opt.textContent = h;
          horaInput.appendChild(opt);
        });
        horaInput.disabled = false;
        btnSubmit.disabled = false;
      } else {
        horaInput.innerHTML = '<option>Sin disponibilidad</option>';
      }
    } catch (e) {
      horaInput.innerHTML = '<option>Error</option>';
    }
  }

  formCita.addEventListener('submit', () => {
    // Garantizar que servicio vaya habilitado al backend
    servicioInput.disabled = false;
  });

  // Perfil: fecha de nacimiento
  window.abrirModalPerfil = function () {
    if (modalPerfil) {
      modalPerfil.classList.add('is-visible');
      if (typeof flatpickr !== 'undefined') {
        flatpickr('#perfil-fecha', {
          locale: 'es',
          dateFormat: 'Y-m-d',
          maxDate: 'today'
        });
      }
    }
  };

  window.cerrarModalPerfil = function () {
    if (modalPerfil) {
      modalPerfil.classList.remove('is-visible');
    }
  };
});

// ================= Asistente IA en página de Citas =================
document.addEventListener('DOMContentLoaded', () => {
  const fab = document.querySelector('#aiFab');
  const dock = document.querySelector('#aiDock');
  const closeBtn = document.querySelector('#aiClose');
  const body = document.querySelector('#aiBody');
  const form = document.querySelector('#aiForm');
  const input = document.querySelector('#aiInput');

  // Si no estamos en la página que tiene el dock, salimos silenciosamente
  if (!fab || !dock || !body || !form || !input) {
    return;
  }

  const urlPagos = dock.dataset.pagosUrl || '';

  function openDock() {
    dock.setAttribute('aria-hidden', 'false');
    input.focus();
  }

  function closeDock() {
    dock.setAttribute('aria-hidden', 'true');
  }

  function appendMsg(role, text) {
    const el = document.createElement('div');
    el.className = 'ai-msg ' + (role === 'user' ? 'user' : 'bot');
    el.textContent = text;
    body.appendChild(el);
    body.scrollTop = body.scrollHeight;
  }

  function answer(question) {
    const t = (question || '').toLowerCase();

    if (t.includes('pago')) {
      if (urlPagos) {
        window.location.href = urlPagos;
        return 'Abriendo “Pagos”…';
      }
      return 'No tengo configurada la ruta de pagos en este momento.';
    }

    if (t.includes('cuantas') || t.includes('cuántas')) {
      return 'Aún no hay listado real en esta pantalla de citas. Cuando exista, podré contar tus citas desde lo que se muestre aquí.';
    }

    return 'Puedo llevarte a “Pagos” o ayudarte con tus citas cuando el listado esté disponible en esta sección.';
  }

  fab.addEventListener('click', openDock);
  closeBtn.addEventListener('click', closeDock);

  window.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
      closeDock();
    }
  });

  body.addEventListener('click', e => {
    const chip = e.target.closest('.ai-chip');
    if (!chip) return;
    input.value = chip.dataset.q || '';
    input.focus();
  });

  form.addEventListener('submit', e => {
    e.preventDefault();
    const q = input.value.trim();
    if (!q) return;
    appendMsg('user', q);
    input.value = '';
    const resp = answer(q);
    appendMsg('bot', resp);
  });
});

// ===================== PAGOS PACIENTE =====================
document.addEventListener('DOMContentLoaded', () => {
  'use strict';

  const container = document.querySelector('.payment-experience-container');
  if (!container) {
    // No estamos en la vista de pagos
    return;
  }

  const $ = s => document.querySelector(s);
  const $$ = s => document.querySelectorAll(s);

  const cardFlipper = $('#card-flipper');
  const cardForm = $('#form-tarjeta');
  const numberInput = $('#card-number');
  const nameInput = $('#card-name');
  const expiryInput = $('#card-expiry');
  const cvcInput = $('#card-cvc');

  const numberIcon = $('#number-validation-icon');
  const nameIcon = $('#name-validation-icon');
  const expiryIcon = $('#expiry-validation-icon');
  const cvcIcon = $('#cvc-validation-icon');

  const modalFactura = $('#modal-factura');
  const modalCustomAlert = $('#modal-custom-alert');

  const pagosConfig = document.querySelector('#pagos-config');
  const dashboardUrl = pagosConfig?.dataset.dashboardUrl || '#';

  // ----- Modales -----
  const openModal = modal => modal.classList.add('is-visible');
  const closeModal = modal => modal.classList.remove('is-visible');

  $$('.modal-close').forEach(btn => {
    btn.addEventListener('click', e => {
      const overlay = e.target.closest('.modal-overlay');
      if (overlay) {
        closeModal(overlay);
      }
    });
  });

  // ----- LocalStorage: datos de próxima cita simulada -----
  const LS_PROXIMA_CITA = 'rc_proxima_cita';

  const getProx = () => {
    try {
      return JSON.parse(localStorage.getItem(LS_PROXIMA_CITA));
    } catch {
      return null;
    }
  };

  const setProx = cita => {
    localStorage.setItem(LS_PROXIMA_CITA, JSON.stringify(cita));
  };

  const prettyDate = iso => {
    return new Date(iso + 'T00:00:00').toLocaleDateString('es-MX', {
      day: '2-digit',
      month: 'long',
      year: 'numeric'
    });
  };

  // ----- Card.js (visualización de la tarjeta) -----
  if (typeof Card !== 'undefined') {
    // eslint-disable-next-line no-undef
    new Card({
      form: '#form-tarjeta',
      container: '.card-wrapper',
      formSelectors: {
        numberInput: '#card-number',
        expiryInput: '#card-expiry',
        cvcInput: '#card-cvc',
        nameInput: '#card-name'
      }
    });
  } else {
    console.error('Card.js no está cargado. Verifica el script en base.html');
  }

  // Flip cuando el usuario entra al CVC
  cvcInput.addEventListener('focus', () => {
    cardFlipper.classList.add('flipped');
  });

  cvcInput.addEventListener('blur', () => {
    cardFlipper.classList.remove('flipped');
  });

  // ----- Validación visual -----
  const getCSSVar = name =>
    getComputedStyle(document.documentElement).getPropertyValue(name).trim();

  const setValidationState = (input, icon, isValid) => {
    const accent = getCSSVar('--color-accent') || '#22c55e';
    const danger = getCSSVar('--color-danger') || '#ef4444';

    const checkSVG = `
      <svg viewBox="0 0 24 24" fill="none" stroke="${accent}" stroke-width="2">
        <path d="M20 6 9 17l-5-5"/>
      </svg>
    `;
    const errorSVG = `
      <svg viewBox="0 0 24 24" fill="none" stroke="${danger}" stroke-width="2">
        <path d="M18 6 6 18M6 6l12 12"/>
      </svg>
    `;

    icon.innerHTML = isValid ? checkSVG : errorSVG;
    icon.classList.add('visible');
    input.classList.remove('valid', 'invalid');

    if (input.value.length > 0) {
      input.classList.add(isValid ? 'valid' : 'invalid');
    } else {
      icon.classList.remove('visible');
    }
  };

  let isNumberValid = false;
  let isNameValid = false;
  let isExpiryValid = false;
  let isCvcValid = false;

  numberInput.addEventListener('input', () => {
    isNumberValid = /^\d{4}\s\d{4}\s\d{4}\s\d{4}$/.test(numberInput.value);
    setValidationState(numberInput, numberIcon, isNumberValid);
  });

  nameInput.addEventListener('input', () => {
    isNameValid = nameInput.value.trim().length > 3;
    setValidationState(nameInput, nameIcon, isNameValid);
  });

  expiryInput.addEventListener('input', () => {
    isExpiryValid = false;

    if (/^\d{2}\s\/\s\d{2}$/.test(expiryInput.value)) {
      const [monthStr, yearStr] = expiryInput.value.split(' / ');
      const month = parseInt(monthStr, 10);
      const year = parseInt(yearStr, 10);

      const now = new Date();
      const currentYear = now.getFullYear() % 100;

      if (year > currentYear || (year === currentYear && month >= now.getMonth() + 1)) {
        isExpiryValid = true;
      }
    }

    setValidationState(expiryInput, expiryIcon, isExpiryValid);
  });

  cvcInput.addEventListener('input', () => {
    isCvcValid = /^\d{3,4}$/.test(cvcInput.value);
    setValidationState(cvcInput, cvcIcon, isCvcValid);
  });

  // ----- Render y lógica de pago -----
  const renderPaymentDetails = () => {
    const proxCita = getProx();

    if (proxCita && proxCita.estado !== 'Pagada') {
      const monto = '500.00';
      const summaryEl = $('#payment-summary');

      if (summaryEl) {
        const fechaLegible = proxCita.fecha ? prettyDate(proxCita.fecha) : '';
        summaryEl.textContent = `Estás pagando una cita de ${proxCita.motivo}${
          fechaLegible ? ' para el ' + fechaLegible : ''
        }.`;
      }

      const amountBtn = $('#payment-amount-btn');
      if (amountBtn) {
        amountBtn.textContent = `$${monto} MXN`;
      }
    } else {
      const flow = document.querySelector('.payment-flow-card');
      if (flow) {
        flow.innerHTML =
          '<h2 style="text-align: center;">No tienes pagos pendientes.</h2>';
      }
    }
  };

  const showInvoice = cita => {
    const facturaBody = $('#factura-body');
    if (!facturaBody) return;

    const transactionId = `MP-SIM-${Date.now()}`;
    facturaBody.innerHTML = `
<p><strong>Consultorio Dental "Rodolfo Castellón"</strong></p>
<p>-----------------------------------</p>
<p><strong>ID Transacción:</strong> ${transactionId}</p>
<p><strong>Fecha:</strong> ${new Date().toLocaleDateString('es-MX')}</p>
<p><strong>Paciente:</strong> Ana López</p>
<p>-----------------------------------</p>
<p><strong>Concepto:</strong> Cita - ${cita.motivo}</p>
<p><strong>Monto Pagado:</strong> $${cita.pago} MXN</p>
<p><strong>Método:</strong> Tarjeta (Simulado)</p>
<p>-----------------------------------</p>
<p>Gracias por su pago.</p>
    `;

    openModal(modalFactura);
  };

  const processPayment = () => {
    const proxCita = getProx();
    const alertTitle = $('#custom-alert-title');
    const alertMessage = $('#custom-alert-message');

    if (!alertTitle || !alertMessage) {
      return;
    }

    alertTitle.textContent = 'Procesando Pago';
    alertMessage.innerHTML = `
<p>Conectando de forma segura con el servidor...</p>
    `;
    openModal(modalCustomAlert);

    setTimeout(() => {
      if (!proxCita) {
        alertTitle.textContent = 'Error';
        alertMessage.innerHTML = '<p>No se encontró la cita a pagar.</p>';
        return;
      }

      proxCita.estado = 'Pagada';
      proxCita.pago = '500.00';
      setProx(proxCita);

      alertTitle.textContent = '¡Pago Exitoso!';
      alertMessage.innerHTML = `
<p>Tu pago ha sido procesado correctamente.</p>
<p>Se ha enviado un correo de confirmación con tu factura al correo registrado.</p>
<div class="form-actions invoice-actions">
  <button id="btn-ver-factura" class="cyber-btn" type="button">Ver Factura</button>
  <a href="${dashboardUrl}" class="cyber-btn cyber-btn-glow" style="text-decoration: none;">Dashboard</a>
</div>
      `;

      const btnFactura = document.querySelector('#btn-ver-factura');
      if (btnFactura) {
        btnFactura.addEventListener('click', () => {
          showInvoice(proxCita);
          closeModal(modalCustomAlert);
        });
      }
    }, 2000);
  };

  // ----- Inicialización -----
  renderPaymentDetails();

  cardForm.addEventListener('submit', e => {
    e.preventDefault();

    if (isNumberValid && isNameValid && isExpiryValid && isCvcValid) {
      processPayment();
    } else {
      alert(
        'Por favor, revisa los datos de tu tarjeta. Hay campos con errores o incompletos.'
      );
    }
  });
});



