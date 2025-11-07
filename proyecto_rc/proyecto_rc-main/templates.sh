#!/usr/bin/env bash
set -euo pipefail

# === Carpetas ===
mkdir -p templates/landing
mkdir -p templates/_components

mkdir -p paciente/templates/paciente
mkdir -p dentista/templates/dentista
mkdir -p accounts/templates/accounts

# === Componentes compartidos ===
cat >templates/_components/base_site.html <<'EOF'
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>{% block title %}Consultorio RC{% endblock %}</title>
  {% load static %}
  <link rel="stylesheet" href="{% static 'site.css' %}">
  {% block head_extra %}{% endblock %}
</head>
<body>
  {% include "_components/navbar.html" %}
  <main class="container">
    {% include "_components/messages.html" %}
    {% block content %}{% endblock %}
  </main>
  {% include "_components/footer.html" %}
  <script src="{% static 'site.js' %}"></script>
  {% block scripts %}{% endblock %}
</body>
</html>
EOF

cat >templates/_components/navbar.html <<'EOF'
<nav class="navbar">
  <a href="{% url 'home' %}" class="brand">RC</a>
  <ul class="nav">
    <li><a href="{% url 'paciente:dashboard' %}">Paciente</a></li>
    <li><a href="{% url 'dentista:dashboard' %}">Dentista</a></li>
    <li><a href="{% url 'accounts:login' %}">Ingresar</a></li>
  </ul>
</nav>
EOF

cat >templates/_components/footer.html <<'EOF'
<footer class="site-footer">
  <small>&copy; {% now "Y" %} Consultorio “Rodolfo Castellón”. Todos los derechos reservados.</small>
</footer>
EOF

cat >templates/_components/messages.html <<'EOF'
{% if messages %}
  <div class="messages">
    {% for m in messages %}
      <div class="msg {{ m.tags }}">{{ m }}</div>
    {% endfor %}
  </div>
{% endif %}
EOF

cat >templates/_components/breadcrumb.html <<'EOF'
<nav aria-label="breadcrumb" class="breadcrumb">
  <ol>
    <li><a href="{% url 'home' %}">Inicio</a></li>
    {% block crumbs %}{% endblock %}
  </ol>
</nav>
EOF

cat >templates/_components/modal.html <<'EOF'
<div class="modal" id="{{ id|default:'modal' }}" hidden>
  <div class="modal-dialog">
    <header class="modal-header">
      <h3>{{ title|default:"Título" }}</h3>
      <button type="button" class="modal-close" aria-label="Cerrar">&times;</button>
    </header>
    <div class="modal-body">
      {{ body|default:"Contenido del modal..." }}
    </div>
    <footer class="modal-footer">
      {{ footer|default:"" }}
    </footer>
  </div>
</div>
EOF

cat >templates/_components/card.html <<'EOF'
<article class="card">
  {% if title %}<header class="card-head"><h3>{{ title }}</h3></header>{% endif %}
  <div class="card-body">
    {% if body %}{{ body }}{% else %}{% block card_body %}{% endblock %}{% endif %}
  </div>
  {% if footer %}<footer class="card-foot">{{ footer }}</footer>{% endif %}
</article>
EOF

# === Landing (root /) ===
cat >templates/landing/index.html <<'EOF'
{% extends "_components/base_site.html" %}
{% block title %}Bienvenido — Consultorio RC{% endblock %}
{% block content %}
  {% include "_components/breadcrumb.html" with title="Inicio" %}
  <section class="hero">
    <h1>Consultorio “Rodolfo Castellón”</h1>
    <p>Sistema base para gestión de pacientes, citas y pagos.</p>
    <p>
      <a href="{% url 'paciente:dashboard' %}">Área Paciente</a> ·
      <a href="{% url 'dentista:dashboard' %}">Área Dentista</a> ·
      <a href="{% url 'accounts:login' %}">Ingresar</a>
    </p>
  </section>
{% endblock %}
EOF

# === PACIENTE ===
cat >paciente/templates/paciente/base.html <<'EOF'
{% extends "_components/base_site.html" %}
{% block title %}Área Paciente — {% block ptitle %}{% endblock %}{% endblock %}
{% block content %}
  <header class="section-head"><h2>Paciente</h2></header>
  {% block pcontent %}{% endblock %}
{% endblock %}
EOF

cat >paciente/templates/paciente/dashboard.html <<'EOF'
{% extends "paciente/base.html" %}
{% block ptitle %}Dashboard{% endblock %}
{% block pcontent %}
  <h3>Bienvenido/a</h3>
  {% include "_components/card.html" with title="Tu próxima cita" body="Aquí irá información de la próxima cita…" %}
{% endblock %}
EOF

cat >paciente/templates/paciente/citas.html <<'EOF'
{% extends "paciente/base.html" %}
{% block ptitle %}Citas{% endblock %}
{% block pcontent %}
  <h3>Mis citas</h3>
  <p>Listado y detalle próximamente…</p>
{% endblock %}
EOF

cat >paciente/templates/paciente/pagos.html <<'EOF'
{% extends "paciente/base.html" %}
{% block ptitle %}Pagos{% endblock %}
{% block pcontent %}
  <h3>Pagos</h3>
  <p>Resumen de pagos y recibos próximamente…</p>
{% endblock %}
EOF

# === DENTISTA ===
cat >dentista/templates/dentista/base.html <<'EOF'
{% extends "_components/base_site.html" %}
{% block title %}Área Dentista — {% block dtitle %}{% endblock %}{% endblock %}
{% block content %}
  <header class="section-head"><h2>Dentista</h2></header>
  {% block dcontent %}{% endblock %}
{% endblock %}
EOF

cat >dentista/templates/dentista/dashboard.html <<'EOF'
{% extends "dentista/base.html" %}
{% block dtitle %}Dashboard{% endblock %}
{% block dcontent %}
  <h3>Panel del Dentista</h3>
  {% include "_components/card.html" with title="Agenda de hoy" body="Bloques de horario y pacientes programados…" %}
{% endblock %}
EOF

cat >dentista/templates/dentista/agenda.html <<'EOF'
{% extends "dentista/base.html" %}
{% block dtitle %}Agenda{% endblock %}
{% block dcontent %}
  <h3>Agenda</h3>
  <p>Calendario y disponibilidad próximamente…</p>
{% endblock %}
EOF

cat >dentista/templates/dentista/pacientes.html <<'EOF'
{% extends "dentista/base.html" %}
{% block dtitle %}Pacientes{% endblock %}
{% block dcontent %}
  <h3>Pacientes</h3>
  <p>Listado, búsqueda y fichas clínicas próximamente…</p>
{% endblock %}
EOF

# === ACCOUNTS ===
cat >accounts/templates/accounts/base.html <<'EOF'
{% extends "_components/base_site.html" %}
{% block title %}Cuentas — {% block atitle %}{% endblock %}{% endblock %}
{% block content %}
  <header class="section-head"><h2>Acceso</h2></header>
  {% block acontent %}{% endblock %}
{% endblock %}
EOF

cat >accounts/templates/accounts/login.html <<'EOF'
{% extends "accounts/base.html" %}
{% block atitle %}Ingresar{% endblock %}
{% block acontent %}
  <h3>Iniciar sesión</h3>
  <form method="post">
    {% csrf_token %}
    <!-- Tu equipo diseña los campos -->
    <label>Usuario</label><input type="text" name="username" />
    <label>Contraseña</label><input type="password" name="password" />
    <button type="submit">Entrar</button>
  </form>
{% endblock %}
EOF

cat >accounts/templates/accounts/register.html <<'EOF'
{% extends "accounts/base.html" %}
{% block atitle %}Registro{% endblock %}
{% block acontent %}
  <h3>Crear cuenta</h3>
  <form method="post">
    {% csrf_token %}
    <!-- Tu equipo diseña los campos -->
    <label>Usuario</label><input type="text" name="username" />
    <label>Email</label><input type="email" name="email" />
    <label>Contraseña</label><input type="password" name="password1" />
    <label>Confirmar contraseña</label><input type="password" name="password2" />
    <button type="submit">Registrarme</button>
  </form>
{% endblock %}
EOF

echo "✔ Estructura de templates creada (opción A)."
echo "Recuerda en settings.py:"
echo "  TEMPLATES[0]['DIRS'] = [BASE_DIR / 'templates']"
