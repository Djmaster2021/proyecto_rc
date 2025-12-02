from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta

# Importamos modelos
from domain.models import Paciente, Dentista, Cita, Pago, Servicio, Horario

# Servicios auxiliares con fallback
try:
    from .services import obtener_horarios_disponibles, crear_aviso_por_cita
except ImportError:
    def obtener_horarios_disponibles(*args): return []
    def crear_aviso_por_cita(*args): pass

# ========================================================
# 1. COMPLETAR PERFIL
# ========================================================
@login_required
def completar_perfil_paciente(request):
    user = request.user
    if hasattr(user, 'dentista'): return redirect('dentista:dashboard')
    if hasattr(user, 'paciente_perfil'): return redirect('paciente:dashboard')

    dentista_asignado = Dentista.objects.first()
    if not dentista_asignado:
        messages.error(request, "Error crítico: No hay dentistas registrados.")
        return redirect('home')

    if request.method == 'POST':
        try:
            nombre = request.POST.get('nombre', '').strip() or f"{user.first_name} {user.last_name}"
            telefono = request.POST.get('telefono', '').strip()
            
            if not telefono:
                messages.error(request, "El teléfono es obligatorio.")
                return render(request, 'paciente/completar_perfil.html', {'nombre_google': nombre})

            Paciente.objects.create(
                user=user,
                dentista=dentista_asignado, 
                nombre=nombre,
                telefono=telefono,
                fecha_nacimiento=request.POST.get('fecha_nacimiento') or None,
                direccion=request.POST.get('direccion', '').strip()
            )
            messages.success(request, "¡Perfil creado con éxito!")
            return redirect('paciente:dashboard')
        except Exception as e:
            print(f"Error: {e}")
            messages.error(request, "Error al guardar datos.")

    nombre_pre = f"{user.first_name} {user.last_name}".strip() or user.username
    return render(request, 'paciente/completar_perfil.html', {'nombre_google': nombre_pre})


# ========================================================
# 2. DASHBOARD
# ========================================================
@login_required
def dashboard(request):
    try:
        paciente = request.user.paciente_perfil
    except:
        return redirect('paciente:completar_perfil')

    hoy = timezone.localdate()
    
    proxima_cita = Cita.objects.filter(
        paciente=paciente,
        fecha__gte=hoy,
        estado__in=['PENDIENTE', 'CONFIRMADA']
    ).order_by('fecha', 'hora_inicio').first()

    historial = Cita.objects.filter(
        paciente=paciente
    ).exclude(
        id=proxima_cita.id if proxima_cita else None
    ).order_by('-fecha', '-hora_inicio')[:5]

    # --- NUEVO: Cargamos los servicios para el Modal ---
    servicios = Servicio.objects.filter(activo=True).order_by('nombre')

    context = {
        'paciente': paciente,
        'proxima_cita': proxima_cita,
        'historial': historial,
        'servicios': servicios, # <--- Agregamos esto al contexto
    }
    return render(request, 'paciente/dashboard.html', context)

# ========================================================
# 3. EDITAR PERFIL
# ========================================================
@login_required
def editar_perfil(request):
    try:
        paciente = request.user.paciente_perfil
    except:
        return redirect('paciente:completar_perfil')

    if request.method == 'POST':
        paciente.nombre = request.POST.get('nombre')
        paciente.telefono = request.POST.get('telefono')
        paciente.direccion = request.POST.get('direccion')
        fecha = request.POST.get('fecha_nacimiento')
        if fecha: paciente.fecha_nacimiento = fecha
        paciente.save()
        messages.success(request, "Datos actualizados.")
        return redirect('paciente:dashboard')

    return render(request, 'paciente/completar_perfil.html', {
        'nombre_google': paciente.nombre,
        'telefono_actual': paciente.telefono,
        'paciente': paciente,
        'es_edicion': True
    })


# ========================================================
# 4. AGENDAR CITA (Lógica Híbrida Inteligente)
# ========================================================
@login_required
def agendar_cita(request):
    try:
        paciente = request.user.paciente_perfil
    except:
        return redirect('paciente:completar_perfil')

    if request.method == 'POST':
        servicio_id = request.POST.get('servicio')
        fecha_str = request.POST.get('fecha')
        hora_str = request.POST.get('hora') 

        if servicio_id and fecha_str and hora_str:
            # 1. Obtenemos el servicio seleccionado
            servicio = get_object_or_404(Servicio, id=servicio_id)
            
            # 2. LÓGICA HÍBRIDA:
            # La cita se asigna al dentista QUE REALIZA el servicio,
            # no necesariamente al dentista de cabecera del paciente.
            dentista_especialista = servicio.dentista

            try:
                hora_inicio = datetime.strptime(hora_str, "%H:%M").time()
                fecha_obj = datetime.strptime(fecha_str, "%Y-%m-%d").date()
                inicio_dt = datetime.combine(fecha_obj, hora_inicio)
                fin_dt = inicio_dt + timedelta(minutes=servicio.duracion_estimada or 30)
                
                # Creamos la cita con el especialista correcto
                nueva_cita = Cita.objects.create(
                    dentista=dentista_especialista, # <--- AQUÍ ESTÁ EL CAMBIO
                    paciente=paciente,
                    servicio=servicio,
                    fecha=fecha_str,
                    hora_inicio=hora_inicio,
                    hora_fin=fin_dt.time(),
                    estado='PENDIENTE'
                )
                
                crear_aviso_por_cita(nueva_cita, "NUEVA_CITA", f"Cita agendada: {servicio.nombre}")
                
                # Mensaje personalizado
                if dentista_especialista != paciente.dentista:
                    msg = f"Cita agendada con el especialista Dr. {dentista_especialista.nombre}."
                else:
                    msg = "Cita agendada con tu dentista correctamente."
                
                messages.success(request, msg)
                return redirect('paciente:dashboard')

            except ValueError:
                messages.error(request, "Error en los datos seleccionados.")

    # GET: Mostrar TODOS los servicios activos de la clínica
    # Ordenamos primero por el dentista del paciente (para sugerirlos primero) y luego por nombre
    servicios = Servicio.objects.filter(activo=True).order_by('dentista__id', 'nombre')
    
    return render(request, 'paciente/agendar_cita.html', {
        'servicios': servicios,
        'dentista_cabecera': paciente.dentista
    })


# ========================================================
# 5. PAGOS & EXTRAS
# ========================================================
@login_required
def mis_pagos(request):
    try:
        paciente = request.user.paciente_perfil
    except:
        return redirect('paciente:completar_perfil')
    pagos = Pago.objects.filter(cita__paciente=paciente).order_by('-created_at')
    return render(request, 'paciente/pagos.html', {'pagos': pagos})

@login_required
def cancelar_registro_paciente(request):
    logout(request)
    return redirect('home')