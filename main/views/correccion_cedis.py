"""
Vista para corrección masiva de nombres de CEDIS en datos crudos.
Muestra cada nombre único y permite reasignar al código oficial.
Soporta ignorar nombres de forma persistente.
"""
import logging

from django.contrib import messages
from django.db import transaction
from django.db.models import Count
from django.shortcuts import render
from django.views import View

from ..models import Cendis, Planificacion, Salida, IgnorarCedis

logger = logging.getLogger(__name__)


class CorreccionCedisView(View):
    """
    Vista para corregir nombres de CEDIS en datos crudos (Planificacion y Salida).
    Muestra agrupaciones por similitud y permite asignar códigos oficiales.
    Soporta ignorar nombres de forma persistente.
    """
    template_name = "correccion_cedis.html"

    def get(self, request):
        # 1. Obtener todos los CEDIS oficiales
        cedis_oficiales = list(Cendis.objects.all().order_by("code"))
        
        # 2. Obtener nombres ignorados
        ignorados = set(IgnorarCedis.objects.values_list("nombre_crudo", flat=True))
        
        # 3. Obtener valores únicos de datos crudos
        cedis_planificacion = (
            Planificacion.objects.exclude(cendis__isnull=True)
            .exclude(cendis="")
            .values("cendis")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        
        nombres_almacen_salida = (
            Salida.objects.exclude(nombre_almacen_origen__isnull=True)
            .exclude(nombre_almacen_origen="")
            .values("nombre_almacen_origen")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        
        # También obtener nombres de nombre_sucursal_origen (usado en normalización)
        nombres_sucursal_origen = (
            Salida.objects.exclude(nombre_sucursal_origen__isnull=True)
            .exclude(nombre_sucursal_origen="")
            .values("nombre_sucursal_origen")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        
        # 4. Consolidar todos los nombres únicos
        nombres_unicos = []
        nombres_ignorados = []
        procesados = set()
        
        for item in cedis_planificacion:
            nombre = item["cendis"].strip()
            if nombre and nombre not in procesados:
                entry = {
                    "nombre": nombre,
                    "planificacion": item["count"],
                    "salida": 0,
                    "ignorado": nombre in ignorados,
                }
                if nombre in ignorados:
                    nombres_ignorados.append(entry)
                else:
                    nombres_unicos.append(entry)
                procesados.add(nombre)
        
        for item in nombres_almacen_salida:
            nombre = item["nombre_almacen_origen"].strip()
            if nombre:
                if nombre not in procesados:
                    entry = {
                        "nombre": nombre,
                        "planificacion": 0,
                        "salida": item["count"],
                        "ignorado": nombre in ignorados,
                    }
                    if nombre in ignorados:
                        nombres_ignorados.append(entry)
                    else:
                        nombres_unicos.append(entry)
                    procesados.add(nombre)
                else:
                    # Actualizar conteo de salida si ya existe
                    for entry in nombres_unicos + nombres_ignorados:
                        if entry["nombre"] == nombre:
                            entry["salida"] += item["count"]
                            break
        
        # Agregar nombres de nombre_sucursal_origen (campo usado en normalización)
        for item in nombres_sucursal_origen:
            nombre = item["nombre_sucursal_origen"].strip()
            if nombre:
                if nombre not in procesados:
                    entry = {
                        "nombre": nombre,
                        "planificacion": 0,
                        "salida": item["count"],
                        "ignorado": nombre in ignorados,
                    }
                    if nombre in ignorados:
                        nombres_ignorados.append(entry)
                    else:
                        nombres_unicos.append(entry)
                    procesados.add(nombre)
                else:
                    # Actualizar conteo de salida si ya existe
                    for entry in nombres_unicos + nombres_ignorados:
                        if entry["nombre"] == nombre:
                            entry["salida"] += item["count"]
                            break
        
        # Ordenar por total de registros
        nombres_unicos.sort(key=lambda x: x["planificacion"] + x["salida"], reverse=True)
        nombres_ignorados.sort(key=lambda x: x["planificacion"] + x["salida"], reverse=True)
        
        # Combinar: primero los no ignorados, luego los ignorados
        todos_los_nombres = nombres_unicos + nombres_ignorados
        
        context = {
            "cedis_oficiales": cedis_oficiales,
            "nombres_unicos": todos_los_nombres,
            "total_registros_planificacion": sum(n["planificacion"] for n in todos_los_nombres),
            "total_registros_salida": sum(n["salida"] for n in todos_los_nombres),
            "total_nombres": len(todos_los_nombres),
            "total_ignorados": len(nombres_ignorados),
        }
        
        return render(request, self.template_name, context)

    def post(self, request):
        """
        Aplica las correcciones seleccionadas y guarda los ignorados.
        """
        logger.info("=" * 80)
        logger.info("INICIANDO CORRECCIÓN DE CEDIS")
        
        correcciones = {}
        ignorar_nuevos = []
        des_ignorar = []
        
        # Parsear datos del formulario
        idx = 1
        while True:
            nombre_crudo = request.POST.get(f"nombre_original_{idx}")
            codigo_oficial = request.POST.get(f"codigo_{idx}", "").strip()
            ignorar = request.POST.get(f"ignorar_{idx}") == "1"
            
            if not nombre_crudo:
                break
            
            # Verificar si estaba ignorado antes
            estaba_ignorado = IgnorarCedis.objects.filter(nombre_crudo=nombre_crudo).exists()
            
            if ignorar and not estaba_ignorado:
                ignorar_nuevos.append(nombre_crudo)
                logger.info(f"🚫 Marcando para ignorar: '{nombre_crudo}'")
            elif not ignorar and estaba_ignorado:
                des_ignorar.append(nombre_crudo)
                logger.info(f"✅ Des-ignorando: '{nombre_crudo}'")
            elif codigo_oficial and not ignorar:
                correcciones[nombre_crudo] = codigo_oficial
                logger.info(f"✓ Agregado a correcciones: '{nombre_crudo}' → '{codigo_oficial}'")
            
            idx += 1
        
        # Aplicar cambios en ignorados
        with transaction.atomic():
            # Guardar nuevos ignorados
            for nombre in ignorar_nuevos:
                IgnorarCedis.objects.get_or_create(
                    nombre_crudo=nombre,
                    defaults={"razon": "Ignorado desde corrección de CEDIS"}
                )
                # Marcar registros con error como ignorados
                Planificacion.objects.filter(
                    cendis=nombre,
                    normalize_status="error"
                ).update(
                    normalize_status="ignored",
                    normalize_notes="Ignorado por configuración"
                )
                Salida.objects.filter(
                    nombre_sucursal_origen=nombre,
                    normalize_status="error"
                ).update(
                    normalize_status="ignored",
                    normalize_notes="Ignorado por configuración"
                )
            
            # Eliminar des-ignorados y resetear a pending
            if des_ignorar:
                IgnorarCedis.objects.filter(nombre_crudo__in=des_ignorar).delete()
                # Resetear registros ignorados a pending para re-normalizarlos
                for nombre in des_ignorar:
                    Planificacion.objects.filter(
                        cendis=nombre,
                        normalize_status="ignored"
                    ).update(
                        normalize_status="pending",
                        normalize_notes=""
                    )
                    Salida.objects.filter(
                        nombre_sucursal_origen=nombre,
                        normalize_status="ignored"
                    ).update(
                        normalize_status="pending",
                        normalize_notes=""
                    )
        
        # Aplicar correcciones de nombres
        registros_actualizados = {"planificacion": 0, "salida": 0}
        if correcciones:
            registros_actualizados = self._aplicar_correcciones(correcciones)
        
        # Construir mensaje
        msg_parts = []
        if correcciones:
            msg_parts.append(
                f"✅ Correcciones: {registros_actualizados['planificacion']} en Planificación, "
                f"{registros_actualizados['salida']} en Salidas"
            )
        if ignorar_nuevos:
            msg_parts.append(f"🚫 {len(ignorar_nuevos)} nombres ignorados")
        if des_ignorar:
            msg_parts.append(f"✅ {len(des_ignorar)} nombres des-ignorados")
        
        if msg_parts:
            messages.success(request, " | ".join(msg_parts))
        else:
            messages.warning(request, "No se realizaron cambios.")
        
        return self.get(request)

    @transaction.atomic
    def _aplicar_correcciones(self, correcciones):
        """
        Aplica las correcciones en los datos crudos.
        correcciones: {nombre_crudo: codigo_oficial}
        También resetea registros con error a pending para re-normalizarlos.
        """
        count_planificacion = 0
        count_salida = 0
        
        for nombre_crudo, codigo_oficial in correcciones.items():
            # Actualizar en Planificacion y resetear a pending
            updated = Planificacion.objects.filter(cendis=nombre_crudo).update(
                cendis=codigo_oficial,
                normalize_status="pending",
                normalize_notes=""
            )
            count_planificacion += updated
            
            # Actualizar en Salida (nombre_almacen_origen) y resetear a pending
            updated = Salida.objects.filter(nombre_almacen_origen=nombre_crudo).update(
                nombre_almacen_origen=codigo_oficial,
                normalize_status="pending",
                normalize_notes=""
            )
            count_salida += updated
            
            # También actualizar en Salida (nombre_sucursal_origen) - campo usado en normalización
            updated = Salida.objects.filter(nombre_sucursal_origen=nombre_crudo).update(
                nombre_sucursal_origen=codigo_oficial,
                normalize_status="pending",
                normalize_notes=""
            )
            count_salida += updated
        
        return {
            "planificacion": count_planificacion,
            "salida": count_salida,
        }
