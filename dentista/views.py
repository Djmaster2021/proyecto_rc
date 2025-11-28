import json
import base64
import qrcode
from io import BytesIO
from collections import defaultdict
from datetime import datetime, time, timedelta
import re
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.utils.timezone import localtime
from django.db.models import Sum, Q
from django.db.models.functions import TruncMonth, TruncDay
from django.http import HttpResponse, JsonResponse
from django.template.loader import get_template
from django.db import transaction
from .models import Cita, Paciente, Servicio, Horario, Dentista, Pago

# --- HELPER: Obtener ID Dentista Seguro ---
def get_dentista_id(user):
    try:
        return user.dentista.id
    except:
        first = Dentista.objects.first()
        return first.id if first else None

# ==============================================================================
# VISTAS PRINCIPALES
# ==============================================================================

@login_required
def dashboard(request):
    dentista_id = get_dentista_id(request.user)
    if not dentista_id: return redirect("home")

    hoy = timezone.localdate()
    ahora = timezone.now()
    hora_actual = ahora.time()

    # 1. Filtros Base
    estados_validos = ['CONFIRMADA', 'PENDIENTE', 'COMPLETADA', 'EN_CURSO']

    # 2. Consultas (CORREGIDAS: Usando 'fecha' y 'hora_inicio')
    
    # Citas de Hoy
    citas_hoy = Cita.objects.filter(
        dentista_id=dentista_id, 
        fecha=hoy,  # <--- CAMBIO: Usar 'fecha' directo
        estado__in=estados_validos
    ).order_by('hora_inicio') # <--- CAMBIO: Ordenar por hora_inicio

    # Pacientes Vistos Hoy (Ya terminaron)
    # Lógica: Fecha es hoy Y (hora_fin < hora_actual O estado es completada)
    pacientes_vistos = Cita.objects.filter(
        dentista_id=dentista_id,
        fecha=hoy,
        estado__in=estados_validos
    ).filter(
        Q(hora_fin__lt=hora_actual) | Q(estado='COMPLETADA') # <--- CAMBIO: Comparar solo hora
    ).order_by('-hora_fin')

    # Próxima Cita (La que sigue o está en curso)
    # Lógica: Fecha >= hoy. Si es hoy, hora_fin >= hora_actual.
    # Simplificación: Buscamos la primera futura
    proxima_cita = Cita.objects.filter(
        dentista_id=dentista_id,
        fecha__gte=hoy,
        estado__in=['CONFIRMADA', 'PENDIENTE', 'EN_CURSO']
    ).filter(
        # Si es hoy, que no haya terminado. Si es futuro, cualquiera sirve.
        Q(fecha__gt=hoy) | (Q(fecha=hoy) & Q(hora_fin__gte=hora_actual))
    ).select_related('paciente', 'servicio').order_by('fecha', 'hora_inicio').first()

    # 3. KPIs
    kpi_pacientes = Paciente.objects.count() 
    kpi_pendientes = Cita.objects.filter(dentista_id=dentista_id, estado='PENDIENTE').count()
    
    ingresos_mes = Pago.objects.filter(
        cita__dentista_id=dentista_id,
        estado='COMPLETADO',
        created_at__month=ahora.month
    ).aggregate(Sum("monto"))["monto__sum"] or 0

    # Radar 90 Días
    inicio_rango = hoy
    fin_rango = inicio_rango + timedelta(days=90)
    
    # Consulta optimizada para el radar
    citas_proximas = Cita.objects.filter(
        dentista_id=dentista_id, 
        fecha__range=[inicio_rango, fin_rango], # <--- CAMBIO: Usar rango de fecha
        estado__in=estados_validos
    )
    
    mapa_citas = defaultdict(list)
    for c in citas_proximas: 
        mapa_citas[c.fecha].append(c) # <--- Agrupar por c.fecha
    
    calendario_dias = []
    DIAS_ES = {0: 'LUN', 1: 'MAR', 2: 'MIÉ', 3: 'JUE', 4: 'VIE', 5: 'SÁB', 6: 'DOM'}
    
    for i in range(90):
        fecha_iter = inicio_rango + timedelta(days=i)
        citas_dia_list = []
        for c in mapa_citas.get(fecha_iter, []):
            # Formatear hora manualmente ya que es objeto time
            hora_str = c.hora_inicio.strftime("%H:%M")
            citas_dia_list.append({ 
                "hora": hora_str, 
                "paciente": c.paciente.nombre, 
                "servicio": c.servicio.nombre, 
                "clase_estado": "estado-confirmada" if c.estado == 'CONFIRMADA' else "estado-pendiente" 
            })
        
        calendario_dias.append({ 
            "dia": fecha_iter, 
            "label_dia": DIAS_ES[fecha_iter.weekday()], 
            "clases": "hoy" if fecha_iter == hoy else "", 
            "citas": citas_dia_list, 
            "es_domingo": fecha_iter.weekday() == 6 
        })

    # Dentista obj para el nombre
    try:
        dentista_obj = Dentista.objects.get(id=dentista_id)
    except:
        dentista_obj = None

    context = {
        "dentista": dentista_obj,
        "citas_hoy": citas_hoy,
        "proxima_cita": proxima_cita,
        "pacientes_vistos": pacientes_vistos,
        "kpi_pacientes": kpi_pacientes,
        "kpi_pendientes": kpi_pendientes,
        "ingresos_mes": ingresos_mes,
        "calendario_dias": calendario_dias,
    }
    return render(request, "dentista/dashboard.html", context)
@login_required

@login_required
def agenda(request):
    dentista_id = get_dentista_id(request.user)
    if not dentista_id: return redirect("home")
    
    hoy = timezone.localdate()
    ahora = timezone.now()
    inicio_rango = hoy
    fin_rango = inicio_rango + timedelta(days=90)

    # 1. CORRECCIÓN: Usar 'fecha__range' en lugar de 'fecha_hora_inicio__date__range'
    citas_qs = Cita.objects.filter(
        dentista_id=dentista_id,
        fecha__range=[inicio_rango, fin_rango] # <--- CAMBIO AQUÍ
    ).exclude(estado__in=['CANCELADA', 'INASISTENCIA']).select_related("paciente", "servicio").order_by("fecha", "hora_inicio") # <--- CAMBIO AQUÍ
    
    mapa_citas = defaultdict(list)
    for c in citas_qs: 
        mapa_citas[c.fecha].append(c) # <--- CAMBIO: Agrupar por c.fecha

    dias_rango = [inicio_rango + timedelta(days=i) for i in range(90)]
    semanas = []

    for i in range(0, len(dias_rango), 7):
        dias_semana = []
        for fecha in dias_rango[i : i + 7]:
            tipo_dia = "no_laboral" if fecha.weekday() == 6 else "laboral"
            
            citas_dia = []
            for c in mapa_citas.get(fecha, []):
                # Como los objetos ahora tienen fecha/hora separados,
                # agregamos una propiedad 'fecha_hora_inicio' al vuelo para que el template no falle
                c.fecha_hora_inicio = datetime.combine(c.fecha, c.hora_inicio)
                citas_dia.append({"obj": c, "fuera_horario": False})
            
            dias_semana.append({"fecha": fecha, "citas": citas_dia, "tipo_dia": tipo_dia})
        semanas.append(dias_semana)

    # Sidebar Data (Correcciones de fecha)
    proxima = Cita.objects.filter(
        dentista_id=dentista_id, 
        fecha__gte=hoy 
    ).filter(
        Q(fecha__gt=hoy) | (Q(fecha=hoy) & Q(hora_fin__gte=ahora.time()))
    ).order_by('fecha', 'hora_inicio').first()

    vistos = Cita.objects.filter(
        dentista_id=dentista_id, 
        fecha=hoy, 
        hora_fin__lt=ahora.time()
    )

    context = {
        "semanas": semanas, 
        "fecha_actual": hoy, 
        "inicio_rango": inicio_rango, 
        "fin_rango": fin_rango, 
        "total_futuras": citas_qs.count(),
        "proxima_cita": proxima,
        "pacientes_vistos": vistos
    }
    return render(request, "dentista/agenda.html", context)
# ==============================================================================
# GESTIÓN DE CITAS (CREAR, ELIMINAR, CONFIRMAR)
# ==============================================================================

@login_required
def crear_cita_manual(request):
    # 1. SEGURIDAD: Obtener ID Dentista
    dentista_id = get_dentista_id(request.user)
    if not dentista_id:
        messages.error(request, "No hay perfil de dentista.")
        return redirect('dentista:dashboard')

    hoy = timezone.localdate()
    limite_mes = hoy + timedelta(days=30)

    # 2. Pacientes Ocupados (CORREGIDO: Usar 'fecha')
    pacientes_ocupados = Cita.objects.filter(
        dentista_id=dentista_id,
        fecha__gte=hoy,  # <--- CAMBIO: Usamos 'fecha' directo
        estado__in=['PENDIENTE', 'CONFIRMADA']
    ).values_list('paciente_id', flat=True)

    # 3. Lista de Pacientes
    all_pacientes = Paciente.objects.all().order_by('nombre')
    
    pacientes_visual = []
    for p in all_pacientes:
        tiene_cita = p.id in pacientes_ocupados
        pacientes_visual.append({'paciente': p, 'disabled': tiene_cita, 'razon': '(Cita activa)' if tiene_cita else ''})

    # 4. Horarios
    horarios = Horario.objects.filter(dentista_id=dentista_id)
    horarios_dict = {}
    for h in horarios:
        horarios_dict[h.dia_semana] = {'inicio': h.hora_inicio.strftime("%H:%M"), 'fin': h.hora_fin.strftime("%H:%M")}

    # 5. Ocupadas JSON (CORREGIDO: Usar 'fecha' y 'hora_inicio')
    citas_futuras = Cita.objects.filter(
        dentista_id=dentista_id,
        fecha__gte=hoy  # <--- CAMBIO
    ).exclude(estado='CANCELADA')
    
    ocupadas_dict = defaultdict(list)
    for c in citas_futuras:
        # Usamos c.fecha directo porque ya es un objeto fecha
        str_fecha = c.fecha.strftime("%Y-%m-%d")
        
        ocupadas_dict[str_fecha].append({
            'inicio': c.hora_inicio.strftime("%H:%M"), 
            'fin': c.hora_fin.strftime("%H:%M")
        })

    # POST
    if request.method == 'POST':
        try:
            fecha_str = request.POST.get('fecha')
            hora_inicio_str = request.POST.get('hora_inicio')
            hora_fin_str = request.POST.get('hora_fin')
            
            servicio = Servicio.objects.get(id=request.POST.get('servicio'))

            Cita.objects.create(
                dentista_id=dentista_id,
                paciente_id=request.POST.get('paciente'),
                servicio=servicio,
                fecha=fecha_str,             # <--- CAMBIO: Campo separado
                hora_inicio=hora_inicio_str, # <--- CAMBIO: Campo separado
                hora_fin=hora_fin_str,       # <--- CAMBIO: Campo separado
                notas=request.POST.get('notas'),
                estado='CONFIRMADA'
            )
            messages.success(request, "Cita creada.")
            return redirect('dentista:agenda')
        except Exception as e:
            messages.error(request, f"Error: {e}")

    context = {
        'pacientes_visual': pacientes_visual,
        'servicios': Servicio.objects.filter(dentista_id=dentista_id, activo=True),
        'fecha_minima': hoy.strftime("%Y-%m-%d"),
        'fecha_maxima': limite_mes.strftime("%Y-%m-%d"),
        'horarios_json': json.dumps(horarios_dict), 
        'ocupadas_json': json.dumps(ocupadas_dict),
    }
    return render(request, 'dentista/crear_cita_manual.html', context)
@login_required
def eliminar_cita(request, cita_id):
    dentista_id = get_dentista_id(request.user)
    # Buscamos la cita asegurando que sea del dentista actual
    cita = get_object_or_404(Cita, id=cita_id, dentista_id=dentista_id)
    
    if request.method == "POST":
        cita.delete()
        messages.success(request, "Cita eliminada correctamente.")
    
    return redirect("dentista:agenda")

@login_required
def confirmar_cita(request, cita_id):
    dentista_id = get_dentista_id(request.user)
    cita = get_object_or_404(Cita, id=cita_id, dentista_id=dentista_id)
    cita.estado = 'CONFIRMADA'
    cita.save()
    messages.success(request, "Cita confirmada.")
    return redirect("dentista:agenda")

@login_required
def vista_consulta(request, cita_id):
    dentista_id = get_dentista_id(request.user)
    cita = get_object_or_404(Cita, id=cita_id, dentista_id=dentista_id)
    
    try: pago = cita.pago_relacionado
    except: pago = None

    if request.method == "POST":
        cita.notas = request.POST.get("notas_clinicas", "")
        if request.FILES.get('archivo_adjunto'):
            cita.archivo_adjunto = request.FILES['archivo_adjunto']
        cita.estado = 'COMPLETADA'
        cita.save()
        
        # Pago
        monto = float(request.POST.get("monto") or 0)
        pagado_now = request.POST.get("pagado") == "on"
        
        if not pago: 
            pago = Pago(cita=cita, monto=monto)
        else: 
            pago.monto = monto
            
        pago.estado = 'COMPLETADO' if pagado_now else 'PENDIENTE'
        pago.save()
        
        messages.success(request, "Consulta finalizada.")
        return redirect("dentista:dashboard")
    
    monto_sug = pago.monto if pago else cita.servicio.precio
    return render(request, "dentista/consulta.html", {"cita": cita, "monto_default": monto_sug, "pagado_default": pago.estado == 'COMPLETADO' if pago else True})

# ==============================================================================
# OTRAS VISTAS (PACIENTES, SERVICIOS, ETC) - Versiones Simplificadas
# ==============================================================================

@login_required
def pacientes(request):
    pacientes_list = Paciente.objects.all().order_by("nombre")
    return render(request, "dentista/pacientes.html", {"pacientes": pacientes_list})

@login_required
def detalle_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    
    # CORRECCIÓN: Ordenar por fecha y hora por separado
    historial = Cita.objects.filter(paciente=paciente).exclude(estado='CANCELADA').order_by("-fecha", "-hora_inicio")
    
    # Añadimos la propiedad combinada al vuelo para que el template ({{ cita.fecha_hora_inicio }}) no falle
    for c in historial:
        c.fecha_hora_inicio = datetime.combine(c.fecha, c.hora_inicio)
    
    pagos_pendientes = Pago.objects.filter(cita__paciente=paciente, estado='PENDIENTE').aggregate(Sum('monto'))['monto__sum'] or 0
    
    return render(request, "dentista/detalle_paciente.html", {
        "paciente": paciente,
        "historial": historial,
        "total_citas": historial.count(),
        "total_pagado": Pago.objects.filter(cita__paciente=paciente, estado='COMPLETADO').aggregate(Sum('monto'))['monto__sum'] or 0,
        "deuda_total": pagos_pendientes
    })

@login_required
def editar_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    if request.method == "POST":
        paciente.nombre = request.POST.get("nombre")
        paciente.telefono = request.POST.get("telefono")
        paciente.direccion = request.POST.get("direccion")
        paciente.save()
        return redirect("dentista:detalle_paciente", paciente_id=paciente.id)
    return render(request, "dentista/editar_paciente.html", {"paciente": paciente})

@login_required
def registrar_paciente(request):
    dentista_id = get_dentista_id(request.user)
    if not dentista_id:
        messages.error(request, "No se encontró perfil de dentista.")
        return redirect("dentista:dashboard")

    if request.method == "POST":
        # 1. Obtener datos limpios
        nombre = request.POST.get("nombre", "").strip()
        telefono = request.POST.get("telefono", "").strip()
        email = request.POST.get("email", "").strip()
        direccion = request.POST.get("direccion", "").strip()
        fecha_nac = request.POST.get("fecha_nacimiento") or None
        
        errores = []

        # --- 2. VALIDACIONES (Lo que pediste) ---
        
        # A. Nombre (Solo letras y espacios, incluyendo acentos/ñ)
        if not re.match(r'^[a-zA-ZñÑáéíóúÁÉÍÓÚ\s]+$', nombre):
            errores.append("El nombre solo puede contener letras.")

        # B. Teléfono (Exactamente 10 dígitos numéricos)
        if not re.match(r'^\d{10}$', telefono):
            errores.append("El teléfono debe ser de 10 dígitos numéricos exactos.")
        
        # C. Email (Obligatorio y Único)
        if not email:
            errores.append("El correo es obligatorio para el acceso del paciente.")
        elif User.objects.filter(email=email).exists():
            errores.append("Ese correo ya está registrado en el sistema.")

        # Si hay errores, detenemos todo y mostramos alerta
        if errores:
            for err in errores:
                messages.error(request, err)
            # Devolvemos el formulario con los datos previos para no borrar todo
            return render(request, "dentista/editar_paciente.html", {
                "paciente": None, 
                "data_prev": request.POST # Para no perder lo escrito
            })

        # --- 3. CREACIÓN DE USUARIO Y PACIENTE ---
        try:
            with transaction.atomic():
                # Paso A: Crear el Usuario de Login
                # Usamos el email como username y el teléfono como password temporal
                nuevo_usuario = User.objects.create_user(
                    username=email, 
                    email=email, 
                    password=telefono, 
                    first_name=nombre
                )

                # Paso B: Crear la Ficha Médica vinculada
                Paciente.objects.create(
                    dentista_id=dentista_id,
                    user=nuevo_usuario, # Vinculamos el login
                    nombre=nombre,
                    telefono=telefono,
                    fecha_nacimiento=fecha_nac,
                    direccion=direccion
                )

            messages.success(request, f"Paciente registrado. Su contraseña temporal es: {telefono}")
            return redirect("dentista:pacientes")

        except Exception as e:
            messages.error(request, f"Error del sistema: {e}")

    return render(request, "dentista/editar_paciente.html", {
        "paciente": None,
        "data_prev": {}  
    })

@login_required
def eliminar_paciente(request, paciente_id):
    if request.method == "POST":
        Paciente.objects.filter(id=paciente_id).delete()
    return redirect("dentista:pacientes")

@login_required
def gestionar_servicios(request): # <--- RENOMBRADO AQUÍ
    dentista_id = get_dentista_id(request.user)
    if request.method == "POST":
        sid = request.POST.get("servicio_id")
        act = request.POST.get("activo") == "on"
        if sid:
            s = get_object_or_404(Servicio, id=sid)
            s.nombre = request.POST.get("nombre")
            s.precio = request.POST.get("precio")
            s.duracion_estimada = request.POST.get("duracion")
            s.activo = act
            s.save()
        else:
            Servicio.objects.create(
                dentista_id=dentista_id,
                nombre=request.POST.get("nombre"),
                precio=request.POST.get("precio"),
                duracion_estimada=request.POST.get("duracion"),
                activo=act
            )
        return redirect("dentista:servicios")
    
    servicios = Servicio.objects.filter(dentista_id=dentista_id).order_by("nombre")
    return render(request, "dentista/servicios.html", {"servicios": servicios})
@login_required
def eliminar_servicio(request, servicio_id):
    if request.method == "POST":
        Servicio.objects.filter(id=servicio_id).delete()
    return redirect("dentista:servicios")

@login_required
def pagos(request):
    dentista_id = get_dentista_id(request.user)
    pagos_list = Pago.objects.filter(cita__dentista_id=dentista_id, estado='COMPLETADO').order_by("-created_at")
    return render(request, "dentista/pagos.html", {"pagos": pagos_list, "total_hoy": 0})

@login_required
def registrar_pago_efectivo(request):
    dentista_id = get_dentista_id(request.user)
    citas_pendientes = Cita.objects.filter(dentista_id=dentista_id, pago_relacionado__isnull=True)
    
    if request.method == "POST":
        cita = get_object_or_404(Cita, id=request.POST.get("cita_id"))
        Pago.objects.create(
            cita=cita,
            monto=request.POST.get("monto"),
            estado='COMPLETADO',
            metodo='EFECTIVO'
        )
        return redirect("dentista:pagos")

    return render(request, "dentista/registrar_pago_efectivo.html", {"citas_disponibles": citas_pendientes})

@login_required
def reportes(request):
    return render(request, "dentista/reportes.html", {'total_ingresos': 0, 'citas': []})

@login_required
def configuracion(request):
    dentista = Dentista.objects.get(id=get_dentista_id(request.user))
    horarios = Horario.objects.filter(dentista=dentista).order_by("dia_semana")
    
    if request.method == "POST" and request.POST.get("action") == "add_schedule":
        Horario.objects.create(
            dentista=dentista,
            dia_semana=request.POST.get("dia"),
            hora_inicio=request.POST.get("hora_inicio"),
            hora_fin=request.POST.get("hora_fin")
        )
        return redirect("dentista:configuracion")

    return render(request, "dentista/configuracion.html", {"dentista": dentista, "horarios": horarios, "dias_semana": Horario.DIAS})

@login_required
def eliminar_horario(request, horario_id):
    Horario.objects.filter(id=horario_id).delete()
    return redirect("dentista:configuracion")

@login_required
def soporte(request):
    return render(request, "dentista/soporte.html")

@login_required
def penalizaciones(request):
    return render(request, "dentista/penalizaciones.html", {'pacientes_riesgo': []})

@login_required
def exportar_citas_csv(request): return HttpResponse("CSV OK")
@login_required
def exportar_citas_pdf(request): return HttpResponse("PDF OK")