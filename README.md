# proyecto_rc
# 🦷 Sistema de Gestión Dental RC (Rodolfo Castellón)

![Status](https://img.shields.io/badge/Estado-Finalizado-success)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Django](https://img.shields.io/badge/Django-5.0-green)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED)

Un **Sistema Integral de Gestión de Citas** automatizado, diseñado para optimizar el flujo de trabajo del Consultorio Dental Rodolfo Castellón. Este sistema elimina la necesidad de una secretaria para la gestión básica, permitiendo al dentista enfocarse en la atención al cliente y a los pacientes gestionar sus propias citas.

## 🚀 Características Principales

### 👨‍⚕️ Para el Dentista
* **Gestión de Agenda:** Visualización y administración total de citas.
* **Automatización:** Sistema capaz de operar sin asistencia administrativa constante.
* **Reportes y Métricas:** Panel de control (Dashboard) con estadísticas del consultorio.
* **Gestión de Pacientes:** Historial clínico y seguimiento digital.

### 🧑‍🦱 Para el Paciente
* **Autogestión de Citas:** Agendar, reprogramar o cancelar citas en línea.
* **Interfaz Accesible:** Diseño intuitivo con **Modo Oscuro/Claro** persistente.
* **Notificaciones:** Recordatorios automáticos vía Email.

### 🤖 Tecnología e Innovación
* **Chatbot Integrado:** Asistente virtual para resolver dudas básicas y guiar al usuario.
* **Integración Google Calendar:** Sincronización de citas con calendarios externos (Google OAuth).
* **Dockerizado:** Configuración lista para despliegue con Docker Compose.

## 🛠️ Tecnologías Utilizadas

* **Backend:** Python, Django Framework.
* **Frontend:** HTML5, CSS3 (Diseño Responsivo), JavaScript (Vanilla).
* **Base de Datos:** SQLite (Entorno local) / PostgreSQL (Producción).
* **Integraciones:** Google Calendar API, SMTP para correos.
* **DevOps:** Docker & Docker Compose.

## 📸 Capturas de Pantalla

*(Aquí puedes subir imágenes de tu proyecto en funcionamiento. Ej: El Login, el Calendario, el Chatbot)*
## 🔧 Instalación y Despliegue Local

### Opción A: Con Docker (Recomendado)
Si tienes Docker instalado, solo ejecuta:
```bash
docker-compose up --build