import csv
import json
import codecs
import base64
import qrcode
from io import BytesIO
from collections import defaultdict
from datetime import datetime, time, timedelta
from .models import Horario, Dentista
import json
from django.utils import timezone
from datetime import timedelta
from collections import defaultdict
import weasyprint
from xhtml2pdf import pisa
from django.core.exceptions import ObjectDoesNotExist

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash, get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q, Count, Avg
from django.db.models.functions import TruncMonth, TruncDay
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string, get_template
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import localtime
from django.utils.html import strip_tags
from django.conf import settings
from django.core.mail import send_mail
from django.core.serializers.json import DjangoJSONEncoder
# Importaciones de dominio
from domain.models import Cita, Paciente, Servicio, Pago, Disponibilidad, Notificacion
from domain.ai_services import (
    procesar_inasistencia, sugerir_horario_cita,
    es_horario_laboral_dentista
)
from domain.notifications import (
    enviar_correo_confirmacion_cita, enviar_correo_penalizacion,
)

User = get_user_model()

# ==============================================================================
# CONSTANTES GLOBALES
# ==============================================================================

FESTIVOS_MX = {
    (1, 1): "Año Nuevo",
    (2, 5): "Día de la Constitución",
    (3, 21): "Natalicio de Benito Juárez",
    (5, 1): "Día del Trabajo",
    (9, 16): "Día de la Independencia",
    (11, 20): "Día de la Revolución",
    (12, 25): "Navidad",
}

# ==============================================================================
# VISTAS PRINCIPALES (DASHBOARD & AGENDA)
# ==============================================================================

# Constantes
FESTIVOS_MX = {(1, 1): "Año Nuevo", (5, 1): "Día del Trabajo", (9, 16): "Independencia", (11, 20): "Revolución", (12, 25): "Navidad"}

@login_required
def dashboard(request):
    if not hasattr(request.user, "perfil_dentista"):
        return redirect("home")

    dentista = request.user.perfil_dentista
    hoy = timezone.localdate()
    ahora = timezone.now() # Hora exacta actual con zona horaria

    # --- 1. FILTRO DE ESTADOS ACTIVOS ---
    # Ignoramos canceladas para todo el dashboard
    estados_validos = [Cita.EstadoCita.CONFIRMADA, Cita.EstadoCita.PENDIENTE, Cita.EstadoCita.COMPLETADA]

    # --- 2. LOGICA INTELIGENTE: ¿QUIÉN YA PASÓ? ---
    
    # A. Pacientes Vistos Hoy (Historial del Día)
    # Criterio: Citas de hoy donde (Hora Fin < Ahora) O (Estado = Completada)
    pacientes_vistos = Cita.objects.filter(
        dentista=dentista,
        fecha_hora_inicio__date=hoy,
        estado__in=estados_validos
    ).filter(
        Q(fecha_hora_fin__lt=ahora) | Q(estado=Cita.EstadoCita.COMPLETADA)
    ).order_by('-fecha_hora_fin') # Los más recientes arriba

    # B. Próxima Cita / En Curso (El "Hero")
    # Criterio: Citas de hoy/futuro donde (Hora Fin >= Ahora)
    # Es decir, que todavía no terminan.
    proxima_cita = Cita.objects.filter(
        dentista=dentista,
        fecha_hora_fin__gte=ahora, 
        estado__in=[Cita.EstadoCita.CONFIRMADA, Cita.EstadoCita.PENDIENTE]
    ).select_related('paciente', 'servicio').order_by('fecha_hora_inicio').first()

    # --- 3. RESTO DE DATOS (KPIs, Agenda, etc) ---
    citas_hoy = Cita.objects.filter(dentista=dentista, fecha_hora_inicio__date=hoy, estado__in=estados_validos).order_by("fecha_hora_inicio")
    kpi_pacientes = Paciente.objects.count()
    kpi_pendientes = Cita.objects.filter(dentista=dentista, estado=Cita.EstadoCita.PENDIENTE).exclude(estado=Cita.EstadoCita.CANCELADA).count()
    notificaciones = Notificacion.objects.filter(usuario=request.user, leida=False).order_by('-enviada_el')[:10]
    
    # Radar 90 Días
    inicio_rango = hoy
    fin_rango = inicio_rango + timedelta(days=90)
    citas_proximas = Cita.objects.filter(dentista=dentista, fecha_hora_inicio__date__range=[inicio_rango, fin_rango], estado__in=estados_validos).select_related("paciente", "servicio")
    
    mapa_citas = defaultdict(list)
    for c in citas_proximas: mapa_citas[c.fecha_hora_inicio.date()].append(c)
    
    calendario_dias = []
    DIAS_ES = {0: 'LUN', 1: 'MAR', 2: 'MIÉ', 3: 'JUE', 4: 'VIE', 5: 'SÁB', 6: 'DOM'}
    
    for i in range(90):
        fecha = inicio_rango + timedelta(days=i)
        citas_dia_list = []
        for c in mapa_citas.get(fecha, []):
            dt_local = localtime(c.fecha_hora_inicio)
            # Filtro visual: Si es hoy y ya pasó, no la mostramos en el radar (opcional, para limpiar)
            citas_dia_list.append({ 
                "hora": dt_local.strftime("%H:%M"), 
                "paciente": c.paciente.nombre, 
                "servicio": c.servicio.nombre, 
                "clase_estado": "estado-confirmada" if c.estado == Cita.EstadoCita.CONFIRMADA else "estado-pendiente" 
            })
        calendario_dias.append({ "dia": fecha, "label_dia": DIAS_ES[fecha.weekday()], "clases": "hoy" if fecha == hoy else "", "tiene_citas": bool(citas_dia_list), "citas": citas_dia_list, "es_festivo": (fecha.month, fecha.day) in FESTIVOS_MX, "es_domingo": fecha.weekday() == 6 })

    # Finanzas
    ingresos_mes = Pago.objects.filter(estado=Pago.EstadoPago.COMPLETADO, created_at__year=ahora.year, created_at__month=ahora.month).aggregate(Sum("monto"))["monto__sum"] or 0
    
    # Datos Gráfica Mini (Dummy para ejemplo)
    labels_diarios = ["Lun", "Mar", "Mié", "Jue", "Vie"]
    data_diarios = [0, 0, 0, 0, 0]

    context = {
        "dentista": dentista,
        "citas_hoy": citas_hoy,
        "proxima_cita": proxima_cita,       # La tarjeta grande
        "pacientes_vistos": pacientes_vistos, # La lista nueva
        "notificaciones": notificaciones,
        "kpi_pacientes": kpi_pacientes,
        "kpi_pendientes": kpi_pendientes,
        "ingresos_mes": ingresos_mes,
        "calendario_dias": calendario_dias,
        "labels_diarios": json.dumps(labels_diarios),
        "data_diarios": json.dumps(data_diarios),
    }

    return render(request, "dentista/dashboard.html", context)

@login_required
def agenda(request):
    if not hasattr(request.user, "perfil_dentista"):
        return redirect("home")
    
    dentista = request.user.perfil_dentista
    hoy = timezone.localdate()
    ahora = timezone.now()
    inicio_rango = hoy
    fin_rango = inicio_rango + timedelta(days=90)

    # --- 1. OBTENER CITAS ACTIVAS (FILTRO DE LIMPIEZA) ---
    # Excluimos 'CANCELADA' e 'INASISTENCIA' para que no ocupen espacio visual
    citas_qs = Cita.objects.filter(
        dentista=dentista,
        fecha_hora_inicio__date__range=[inicio_rango, fin_rango],
    ).exclude(
        estado__in=[Cita.EstadoCita.CANCELADA, Cita.EstadoCita.INASISTENCIA]
    ).select_related("paciente", "servicio").order_by("fecha_hora_inicio")
    
    # Agrupar por fecha
    mapa_citas = defaultdict(list)
    for c in citas_qs:
        mapa_citas[c.fecha_hora_inicio.date()].append(c)

    # Helper para saber si es horario laboral
    def es_fuera_horario(dt):
        wd = dt.weekday()
        h = dt.time()
        # Lunes a Viernes (0-4): 7am - 8pm
        if wd <= 4: return not (time(7, 0) <= h <= time(20, 0))
        # Sábado (5): 9am - 2pm
        elif wd == 5: return not (time(9, 0) <= h <= time(14, 0))
        # Domingo (6): Cerrado
        else: return True

    # Generar calendario
    dias_rango = [inicio_rango + timedelta(days=i) for i in range(90)]
    semanas = []

    for i in range(0, len(dias_rango), 7):
        dias_semana = []
        for fecha in dias_rango[i : i + 7]:
            festivo_label = FESTIVOS_MX.get((fecha.month, fecha.day))
            tipo_dia = "festivo" if festivo_label else ("no_laboral" if fecha.weekday() == 6 else "laboral")
            
            citas_dia = []
            for c in mapa_citas.get(fecha, []):
                # Opcional: Ocultar citas pasadas del día de hoy (si ya pasaron)
                # Si quieres ver todas las de hoy aunque ya pasaron, quita el "if"
                if c.fecha_hora_inicio >= ahora or c.fecha_hora_inicio.date() > hoy:
                    citas_dia.append({
                        "obj": c, 
                        "fuera_horario": es_fuera_horario(c.fecha_hora_inicio)
                    })
            
            dias_semana.append({
                "fecha": fecha, 
                "citas": citas_dia, 
                "tipo_dia": tipo_dia, 
                "festivo_label": festivo_label
            })
        semanas.append(dias_semana)

    context = {
        "dentista": dentista, 
        "semanas": semanas, 
        "fecha_actual": hoy, 
        "inicio_rango": inicio_rango, 
        "fin_rango": fin_rango, 
        "total_futuras": citas_qs.count()
    }
    return render(request, "dentista/agenda.html", context)

@login_required
def detalle_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    
    # --- CORRECCIÓN AQUÍ: SOLO MOSTRAR HISTORIAL REAL ---
    historial = Cita.objects.filter(
        paciente=paciente
    ).exclude( # <--- SI SE CANCELÓ, NO ES PARTE DEL HISTORIAL CLÍNICO
        estado=Cita.EstadoCita.CANCELADA
    ).order_by("-fecha_hora_inicio")
    # ----------------------------------------------------
    
    # Recalcular contadores basados en el historial limpio
    return render(request, "dentista/detalle_paciente.html", {
        "paciente": paciente,
        "historial": historial,
        "total_citas": historial.count(),
        "citas_completadas": historial.filter(estado=Cita.EstadoCita.COMPLETADA).count()
    })
#)=========================================================================
# GESTIÓN DE CITAS (CRUD & CONSULTA)
# ==============================================================================

# En dentista/views.py

@login_required
def crear_cita_manual(request):
    # 1. SEGURIDAD: Obtener ID Dentista
    try:
        dentista_obj = request.user.dentista
        dentista_id = dentista_obj.id
    except:
        dentista_id = Dentista.objects.first().id if Dentista.objects.exists() else None
    
    if not dentista_id:
        messages.error(request, "No hay perfil de dentista disponible.")
        return redirect('dentista:dashboard')

    # 2. Datos Base
    hoy = timezone.localdate()
    limite_mes = hoy + timedelta(days=30)

    # 3. Lógica de Pacientes (FIX: A prueba de campos faltantes)
    # Intentamos filtrar por dentista, si falla (porque no existe el campo), traemos todos
    try:
        pacientes_ocupados_ids = Cita.objects.filter(
            dentista_id=dentista_id,
            fecha_hora_inicio__date__gte=hoy,
            estado__in=['PENDIENTE', 'CONFIRMADA', 'EN_CURSO']
        ).values_list('paciente_id', flat=True)
        
        all_pacientes = Paciente.objects.filter(dentista_id=dentista_id)
    except Exception:
        # Fallback: Si el modelo Paciente no tiene 'dentista', traemos todos
        # y asumimos ocupados globalmente
        pacientes_ocupados_ids = Cita.objects.filter(
            fecha_hora_inicio__date__gte=hoy,
            estado__in=['PENDIENTE', 'CONFIRMADA', 'EN_CURSO']
        ).values_list('paciente_id', flat=True)
        all_pacientes = Paciente.objects.all()
    
    pacientes_visual = []
    for p in all_pacientes:
        tiene_cita = p.id in pacientes_ocupados_ids
        pacientes_visual.append({
            'paciente': p,
            'disabled': tiene_cita,
            'razon': '(Ya tiene cita)' if tiene_cita else ''
        })

    # 4. Horarios y Servicios (También a prueba de fallos)
    try:
        horarios = Horario.objects.filter(dentista_id=dentista_id)
        servicios = Servicio.objects.filter(dentista_id=dentista_id, activo=True)
    except Exception:
        # Si falla, intentamos sin filtro de dentista
        horarios = Horario.objects.all()
        servicios = Servicio.objects.filter(activo=True)

    horarios_dict = {}
    for h in horarios:
        horarios_dict[h.dia_semana] = {
            'inicio': h.hora_inicio.strftime("%H:%M"),
            'fin': h.hora_fin.strftime("%H:%M")
        }

    # 5. Citas Ocupadas
    citas_futuras = Cita.objects.filter(
        dentista_id=dentista_id,
        fecha_hora_inicio__date__gte=hoy,
        fecha_hora_inicio__date__lte=limite_mes
    ).exclude(estado='CANCELADA')
    
    ocupadas_dict = {}
    for c in citas_futuras:
        fecha_local = timezone.localtime(c.fecha_hora_inicio)
        str_fecha = fecha_local.strftime("%Y-%m-%d")
        str_hora = fecha_local.strftime("%H:%M")
        
        if str_fecha not in ocupadas_dict:
            ocupadas_dict[str_fecha] = []
        ocupadas_dict[str_fecha].append(str_hora)

    # POST
    if request.method == 'POST':
        try:
            fecha_str = request.POST.get('fecha')
            hora_ini_str = request.POST.get('hora_inicio')
            hora_fin_str = request.POST.get('hora_fin')
            
            dt_inicio = f"{fecha_str} {hora_ini_str}"
            dt_fin = f"{fecha_str} {hora_fin_str}"

            Cita.objects.create(
                dentista_id=dentista_id,
                paciente_id=request.POST.get('paciente'),
                servicio_id=request.POST.get('servicio'),
                fecha_hora_inicio=dt_inicio,
                fecha_hora_fin=dt_fin,
                notas=request.POST.get('notas'),
                estado='CONFIRMADA'
            )
            messages.success(request, "Cita creada exitosamente.")
            return redirect('dentista:agenda')
        except Exception as e:
            messages.error(request, f"Error al guardar: {e}")

    context = {
        'pacientes_visual': pacientes_visual,
        'servicios': servicios,
        'fecha_minima': hoy.strftime("%Y-%m-%d"),
        'fecha_maxima': limite_mes.strftime("%Y-%m-%d"),
        'horarios_json': json.dumps(horarios_dict), 
        'ocupadas_json': json.dumps(ocupadas_dict),
    }
    return render(request, 'dentista/crear_cita_manual.html', context)


def confirmar_cita(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id, dentista__user=request.user)
    if cita.estado == Cita.EstadoCita.PENDIENTE:
        cita.estado = Cita.EstadoCita.CONFIRMADA; cita.save()
        messages.success(request, "Cita confirmada.")
    return redirect("dentista:dashboard")

@login_required
def eliminar_cita(request, cita_id):
    if not hasattr(request.user, "perfil_dentista"): return redirect("home")
    cita = get_object_or_404(Cita, id=cita_id, dentista=request.user.perfil_dentista)
    if request.method == "POST":
        cita.delete()
        messages.success(request, "Cita eliminada.")
    return redirect("dentista:agenda")

@login_required
def marcar_no_show(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id, dentista__user=request.user)
    procesar_inasistencia(cita) # Lógica de dominio/AI
    messages.warning(request, "Cita marcada como inasistencia.")
    return redirect("dentista:dashboard")

@login_required
def completar_cita(request, cita_id): 
    return redirect("dentista:vista_consulta", cita_id=cita_id)

@login_required
def vista_consulta(request, cita_id):
    # Vista principal para la "Estación Clínica"
    cita = get_object_or_404(Cita.objects.select_related('servicio', 'paciente'), id=cita_id, dentista__user=request.user)
    pago = getattr(cita, "pago_relacionado", None)

    if request.method == "POST":
        # 1. Guardar Notas
        cita.notas = request.POST.get("notas_clinicas", "")
        
        # 2. Guardar Archivo (SI SE SUBIÓ UNO)
        if request.FILES.get('archivo_adjunto'):
            cita.archivo_adjunto = request.FILES['archivo_adjunto']

        cita.estado = Cita.EstadoCita.COMPLETADA
        cita.save()
        
        # 3. Procesar Pago
        try:
            monto = float(request.POST.get("monto") or 0)
        except ValueError:
            monto = 0.0
            
        pagado = request.POST.get("pagado") == "on"
        
        if not pago: 
            pago = Pago(cita=cita, monto=monto)
        else: 
            pago.monto = monto
            
        pago.estado = Pago.EstadoPago.COMPLETADO if pagado else Pago.EstadoPago.PENDIENTE
        pago.save()
        
        messages.success(request, "Consulta finalizada y expediente actualizado.")
        return redirect("dentista:dashboard")
    
    # Precio Sugerido
    precio_sugerido = pago.monto if pago else cita.servicio.precio

    return render(request, "dentista/consulta.html", {
        "cita": cita,
        "monto_default": precio_sugerido,
        "pagado_default": pago.estado == Pago.EstadoPago.COMPLETADO if pago else True
    })

@login_required
def actualizar_nota_cita(request, cita_id):
    # Vista para el Modal de Edición en el Historial
    if request.method == "POST":
        cita = get_object_or_404(Cita, id=cita_id, dentista__user=request.user)
        
        # 1. Actualizar Texto
        nuevas_notas = request.POST.get("notas_clinicas")
        if nuevas_notas is not None:
            cita.notas = nuevas_notas
        
        # 2. Actualizar Archivo
        if request.FILES.get("archivo_adjunto"):
            cita.archivo_adjunto = request.FILES["archivo_adjunto"]
            
        cita.save()
        messages.success(request, "Expediente actualizado correctamente.")
        return redirect("dentista:detalle_paciente", paciente_id=cita.paciente.id)
    
    return redirect("dentista:dashboard")

# ==============================================================================
# FINANZAS Y PAGOS
# ==============================================================================

@login_required
def pagos(request):
    if not hasattr(request.user, "perfil_dentista"): return redirect("home")
    hoy = timezone.localdate()
    
    # Lista de pagos completados
    pagos_list = Pago.objects.filter(estado=Pago.EstadoPago.COMPLETADO).select_related('cita', 'cita__paciente').order_by("-created_at")
    
    # KPIs
    total_historico = pagos_list.aggregate(Sum("monto"))["monto__sum"] or 0
    total_hoy = pagos_list.filter(created_at__date=hoy).aggregate(Sum("monto"))["monto__sum"] or 0

    context = {
        "pagos": pagos_list,
        "total_historico": total_historico,
        "total_hoy": total_hoy,
    }
    return render(request, "dentista/pagos.html", context)

@login_required
def registrar_pago_efectivo(request):
    if not hasattr(request.user, "perfil_dentista"): return redirect("home")
    dentista = request.user.perfil_dentista
    ahora = timezone.now()
    
    citas_disponibles = Cita.objects.filter(dentista=dentista, fecha_hora_inicio__lte=ahora).filter(Q(pago_relacionado__isnull=True) | ~Q(pago_relacionado__estado=Pago.EstadoPago.COMPLETADO)).select_related('paciente', 'servicio').order_by("-fecha_hora_inicio")
    
    cita_preseleccionada = None
    if request.GET.get("paciente"):
        cita_preseleccionada = citas_disponibles.filter(paciente_id=request.GET.get("paciente")).first()

    if request.method == "POST":
        cita_id = request.POST.get("cita_id")
        monto_str = request.POST.get("monto", "").strip()
        notas = request.POST.get("notas", "").strip()

        if not cita_id:
            messages.error(request, "Selecciona la cita.")
            return redirect("dentista:registrar_pago_efectivo")
        try:
            monto = float(monto_str)
            if monto <= 0: raise ValueError
        except:
            messages.error(request, "Monto inválido.")
            return redirect("dentista:registrar_pago_efectivo")

        cita = get_object_or_404(Cita, id=cita_id, dentista=dentista)
        pago = getattr(cita, "pago_relacionado", None)
        if pago is None: pago = Pago(cita=cita, monto=monto)
        else: pago.monto = monto

        if hasattr(Pago, "MetodoPago") and hasattr(Pago.MetodoPago, "EFECTIVO"): pago.metodo = Pago.MetodoPago.EFECTIVO
        else: pago.metodo = "EFECTIVO"

        pago.estado = Pago.EstadoPago.COMPLETADO
        # Si tu modelo tiene notas en pago, descomenta:
        # if hasattr(pago, "notas"): pago.notas = notas
        pago.save()
        
        messages.success(request, f"Pago registrado para {cita.paciente.nombre}.")
        return redirect("dentista:pagos")

    context = {"dentista": dentista, "citas_disponibles": citas_disponibles, "cita_preseleccionada": cita_preseleccionada}
    return render(request, "dentista/registrar_pago_efectivo.html", context)

# ==============================================================================
# PACIENTES
# ==============================================================================

@login_required
def pacientes(request):
    query = request.GET.get("q", "")
    pacientes_list = Paciente.objects.all().order_by("nombre")
    if query:
        pacientes_list = pacientes_list.filter(Q(nombre__icontains=query) | Q(user__email__icontains=query) | Q(telefono__icontains=query))
    return render(request, "dentista/pacientes.html", {"pacientes": pacientes_list, "query": query})

@login_required
def detalle_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    historial = Cita.objects.filter(paciente=paciente).order_by("-fecha_hora_inicio")
    return render(request, "dentista/detalle_paciente.html", {
        "paciente": paciente,
        "historial": historial,
        "total_citas": historial.count(),
        "citas_completadas": historial.filter(estado=Cita.EstadoCita.COMPLETADA).count()
    })

@login_required
def editar_paciente(request, paciente_id):
    if not hasattr(request.user, "perfil_dentista"): return redirect("home")
    paciente = get_object_or_404(Paciente, id=paciente_id)
    if request.method == "POST":
        paciente.nombre = request.POST.get("nombre", "").strip()
        paciente.telefono = request.POST.get("telefono", "").strip()
        paciente.direccion = request.POST.get("direccion", "").strip()
        try: paciente.fecha_nacimiento = request.POST.get("fecha_nacimiento")
        except: pass
        if request.POST.get("email") and paciente.user:
            paciente.user.email = request.POST.get("email", "").strip()
            paciente.user.save()
        paciente.save()
        messages.success(request, "Paciente actualizado.")
        return redirect("dentista:detalle_paciente", paciente_id=paciente.id)
    return render(request, "dentista/editar_paciente.html", {"paciente": paciente})

@login_required
def eliminar_paciente(request, paciente_id):
    if not hasattr(request.user, "perfil_dentista"): return redirect("home")
    
    if request.method == "POST":
        paciente = get_object_or_404(Paciente, id=paciente_id)
        nombre = paciente.nombre
        # Borramos usuario y perfil
        user = paciente.user
        paciente.delete()
        if user: user.delete()
        
        messages.success(request, f"Expediente de {nombre} eliminado correctamente.")
        
    return redirect("dentista:pacientes")
# ==============================================================================
# SERVICIOS
# ==============================================================================

@login_required
def gestionar_servicios(request):
    if not hasattr(request.user, "perfil_dentista"): return redirect("home")
    
    if request.method == "POST":
        sid = request.POST.get("servicio_id")
        nom = request.POST.get("nombre")
        pre = request.POST.get("precio")
        dur = request.POST.get("duracion")
        act = request.POST.get("activo") == "on"

        if sid:
            s = get_object_or_404(Servicio, id=sid)
            s.nombre = nom; s.precio = pre; s.duracion_estimada = dur; s.activo = act; s.save()
            messages.success(request, f"Servicio '{nom}' actualizado.")
        else:
            Servicio.objects.create(nombre=nom, precio=pre, duracion_estimada=dur, activo=act)
            messages.success(request, f"Nuevo servicio '{nom}' creado.")
        return redirect("dentista:servicios")
    
    return render(request, "dentista/servicios.html", {"servicios": Servicio.objects.all().order_by("nombre")})

@login_required
def eliminar_servicio(request, servicio_id):
    if not hasattr(request.user, "perfil_dentista"): return redirect("home")
    if request.method == "POST":
        servicio = get_object_or_404(Servicio, id=servicio_id)
        nombre = servicio.nombre
        servicio.delete()
        messages.success(request, f"Servicio '{nombre}' eliminado.")
    return redirect("dentista:servicios")

# ==============================================================================
# REPORTES E INTELIGENCIA FINANCIERA
# ==============================================================================

@login_required
def reportes(request):
    # Vista para el Dashboard Financiero ($100k)
    if not hasattr(request.user, "perfil_dentista"):
        return redirect("home")
        
    hoy = timezone.now().date()
    
    fecha_inicio_str = request.GET.get('inicio', (hoy - timedelta(days=30)).strftime('%Y-%m-%d'))
    fecha_fin_str = request.GET.get('fin', hoy.strftime('%Y-%m-%d'))
    modo_grafica = request.GET.get('modo', 'dias')

    try:
        fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
        fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
    except ValueError:
        fecha_inicio = hoy - timedelta(days=30)
        fecha_fin = hoy

    # Filtrar Citas en rango
    citas_filtradas = Cita.objects.filter(
        fecha_hora_inicio__date__range=[fecha_inicio, fecha_fin]
    ).select_related('paciente', 'servicio').order_by('-fecha_hora_inicio')

    # KPIs
    total_ingresos = Pago.objects.filter(
        cita__in=citas_filtradas, estado=Pago.EstadoPago.COMPLETADO
    ).aggregate(Sum("monto"))["monto__sum"] or 0
    
    total_citas = citas_filtradas.count()
    pacientes_unicos = citas_filtradas.values('paciente').distinct().count()
    
    ticket_promedio = 0
    if total_citas > 0:
        ticket_promedio = total_ingresos / total_citas

    # Datos Gráfica
    labels = []
    data_points = []
    
    # Usamos los pagos para la gráfica de ingresos, no las citas
    pagos_rango = Pago.objects.filter(
        estado=Pago.EstadoPago.COMPLETADO,
        created_at__date__range=[fecha_inicio, fecha_fin]
    )

    if modo_grafica == 'meses':
        datos_grafica = pagos_rango.annotate(periodo=TruncMonth('created_at')).values('periodo').annotate(total=Sum('monto')).order_by('periodo')
        for d in datos_grafica:
            labels.append(d['periodo'].strftime('%b %Y'))
            data_points.append(float(d['total']))
    else:
        datos_grafica = pagos_rango.annotate(periodo=TruncDay('created_at')).values('periodo').annotate(total=Sum('monto')).order_by('periodo')
        for d in datos_grafica:
            labels.append(d['periodo'].strftime('%d %b'))
            data_points.append(float(d['total']))

    # Respuesta JSON (AJAX)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        lista_citas = []
        for c in citas_filtradas:
            monto_cita = 0
            if hasattr(c, 'pago_relacionado'):
                monto_cita = float(c.pago_relacionado.monto)
            elif hasattr(c.servicio, 'precio'):
                monto_cita = float(c.servicio.precio)

            lista_citas.append({
                'fecha': localtime(c.fecha_hora_inicio).strftime('%d %b, Y'),
                'hora': localtime(c.fecha_hora_inicio).strftime('%H:%M'),
                'paciente': c.paciente.nombre,
                'paciente_inicial': c.paciente.nombre[0].upper(),
                'servicio': c.servicio.nombre,
                'estado': c.estado,
                'monto': monto_cita
            })

        return JsonResponse({
            'kpi_ingresos': float(total_ingresos),
            'kpi_citas': total_citas,
            'kpi_ticket': float(round(ticket_promedio, 2)),
            'kpi_pacientes': pacientes_unicos,
            'chart_labels': labels,
            'chart_data': data_points,
            'tabla_citas': lista_citas
        })

    # Respuesta HTML Normal
    context = {
        'fecha_inicio': fecha_inicio_str,
        'fecha_fin': fecha_fin_str,
        'total_ingresos': total_ingresos,
        'total_citas': total_citas,
        'ticket_promedio': ticket_promedio,
        'total_pacientes': pacientes_unicos,
        'citas': citas_filtradas,
        'init_labels': labels, 
        'init_data': data_points,
    }
    return render(request, "dentista/reportes.html", context)

@login_required
def exportar_citas_pdf(request):
    # Generador de PDF robusto
    if not hasattr(request.user, "perfil_dentista"): return redirect("home")
    dentista = request.user.perfil_dentista
    
    fecha_inicio_str = request.GET.get('inicio')
    fecha_fin_str = request.GET.get('fin')

    try:
        fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
        fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        hoy = timezone.localdate()
        fecha_inicio = hoy.replace(day=1)
        fecha_fin = hoy

    citas = Cita.objects.filter(
        dentista=dentista,
        fecha_hora_inicio__date__range=[fecha_inicio, fecha_fin]
    ).select_related('paciente', 'servicio', 'pago_relacionado').order_by("fecha_hora_inicio")

    total_ingresos = 0
    for c in citas:
        if hasattr(c, 'pago_relacionado'):
            total_ingresos += c.pago_relacionado.monto

    # QR
    qr_base64 = None
    try:
        qr = qrcode.QRCode(box_size=4, border=2)
        qr.add_data(f"Reporte-{dentista.id}-{fecha_inicio}-{fecha_fin}")
        qr.make(fit=True)
        img = qr.make_image(fill_color="#111a2c", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()
    except Exception: pass

    context = {
        'dentista': dentista,
        'fecha_inicio': fecha_inicio.strftime('%d/%m/%Y'),
        'fecha_fin': fecha_fin.strftime('%d/%m/%Y'),
        'citas': citas,
        'total_citas': citas.count(),
        'total_ingresos': total_ingresos,
        'qr_code_base64': qr_base64,
    }

    template = get_template('dentista/reporte_pdf.html')
    html = template.render(context)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Reporte_{fecha_inicio}.pdf"'
    
    weasyprint.HTML(string=html, base_url=request.build_absolute_uri()).write_pdf(response)
    return response

@login_required
def exportar_citas_csv(request):
    if not hasattr(request.user, "perfil_dentista"): return redirect("home")
    
    inicio = request.GET.get("inicio")
    fin = request.GET.get("fin")
    
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="Reporte_{inicio}.csv"'
    response.write(codecs.BOM_UTF8)
    
    writer = csv.writer(response)
    writer.writerow(["REPORTE DE CITAS"])
    writer.writerow([f"Periodo: {inicio} al {fin}"])
    writer.writerow([])
    writer.writerow(["FECHA", "HORA", "PACIENTE", "SERVICIO", "ESTADO", "NOTAS", "MONTO"])
    
    citas = Cita.objects.filter(
        dentista=request.user.perfil_dentista,
        fecha_hora_inicio__date__range=[inicio, fin]
    ).select_related('paciente', 'servicio', 'pago_relacionado').order_by("fecha_hora_inicio")

    for c in citas:
        monto = c.pago_relacionado.monto if hasattr(c, "pago_relacionado") else 0.0
        notas = getattr(c, 'notas', '')
        writer.writerow([
            localtime(c.fecha_hora_inicio).strftime("%d/%m/%Y"),
            localtime(c.fecha_hora_inicio).strftime("%H:%M"),
            c.paciente.nombre,
            c.servicio.nombre,
            c.get_estado_display(),
            notas,
            monto
        ])
    return response

# ==============================================================================
# PENALIZACIONES, SOPORTE & CONFIGURACIÓN
# ==============================================================================

@login_required
def penalizaciones(request):
    if not hasattr(request.user, "perfil_dentista"): return redirect("home")
    dentista = request.user.perfil_dentista
    hoy = timezone.localdate()

    if request.method == "POST":
        paciente_id = request.POST.get("paciente_id")
        accion = request.POST.get("accion") 

        if paciente_id and accion == "perdonar":
            citas_sucias = Cita.objects.filter(dentista=dentista, paciente_id=paciente_id, estado=Cita.EstadoCita.INASISTENCIA)
            for c in citas_sucias:
                c.estado = Cita.EstadoCita.CANCELADA 
                c.notas = f"{c.notas or ''} [Penalización perdonada el {hoy}]"
                c.save()
            messages.success(request, "Penalización removida.")
            return redirect("dentista:penalizaciones")

    pacientes_qs = Paciente.objects.all().order_by("nombre")
    penalizados = []
    general = []
    total_deuda = 0

    for paciente in pacientes_qs:
        inasistencias_qs = Cita.objects.filter(
            dentista=dentista, paciente=paciente, estado=Cita.EstadoCita.INASISTENCIA
        ).order_by("-fecha_hora_inicio")
        
        count = inasistencias_qs.count()
        data = {
            "paciente": paciente,
            "inasistencias": count,
            "ultimo_incidente": inasistencias_qs.first() if count > 0 else None,
        }

        if count >= 3:
            total_deuda += 300
            data["monto_deuda"] = 300
            data["estado_label"] = "CRÍTICO"
            data["acciones"] = True
            penalizados.append(data)
        else:
            data["monto_deuda"] = 0
            data["estado_label"] = "Al día" if count == 0 else "Advertencia"
            data["acciones"] = False
            general.append(data)

    context = {"penalizados": penalizados, "general": general, "total_deuda": total_deuda, "total_casos": len(penalizados)}
    return render(request, "dentista/penalizaciones.html", context)

@login_required
def configuracion(request):
    if not hasattr(request.user, "perfil_dentista"): return redirect("home")
    dentista = request.user.perfil_dentista
    
    if request.method == "POST":
        action = request.POST.get("action")

        if action == "add_schedule":
            try:
                Disponibilidad.objects.create(
                    dentista=dentista,
                    dia_semana=int(request.POST.get("dia")),
                    hora_inicio=request.POST.get("hora_inicio"),
                    hora_fin=request.POST.get("hora_fin")
                )
                messages.success(request, "Horario agregado.")
            except Exception as e:
                messages.error(request, f"Error: {e}")

        elif action == "update_profile":
            try:
                dentista.nombre = request.POST.get("nombre", dentista.nombre)
                dentista.telefono = request.POST.get("telefono", dentista.telefono)
                dentista.especialidad = request.POST.get("especialidad", dentista.especialidad)
                if "foto_perfil" in request.FILES:
                    dentista.foto_perfil = request.FILES["foto_perfil"]
                dentista.save()
                messages.success(request, "Perfil actualizado.")
            except Exception as e:
                messages.error(request, f"Error: {e}")

        elif action == "change_password":
            p_act = request.POST.get("old_password")
            p_new = request.POST.get("new_password")
            p_conf = request.POST.get("confirm_password")
            if request.user.check_password(p_act) and p_new == p_conf:
                request.user.set_password(p_new)
                request.user.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, "Contraseña actualizada.")
            else:
                messages.error(request, "Error en contraseñas.")

        return redirect("dentista:configuracion")

    horarios = Disponibilidad.objects.filter(dentista=dentista).order_by("dia_semana", "hora_inicio")
    return render(request, "dentista/configuracion.html", {"dentista": dentista, "horarios": horarios, "dias_semana": Disponibilidad.DIAS_SEMANA})

@login_required
def eliminar_horario(request, horario_id):
    get_object_or_404(Disponibilidad, id=horario_id, dentista__user=request.user).delete()
    return redirect("dentista:configuracion")

@login_required
def soporte(request):
    if request.method == "POST":
        # Lógica de envío de correo
        messages.success(request, "Reporte enviado.")
        return redirect("dentista:soporte")
    return render(request, "dentista/soporte.html")

# Placeholders para evitar errores de URL si faltan
def pagos_placeholder(request): return redirect("dentista:pagos")
def servicios_placeholder(request): return redirect("dentista:servicios")
def penalizaciones_placeholder(request): return redirect("dentista:penalizaciones")
def reportes_placeholder(request): return redirect("dentista:reportes")