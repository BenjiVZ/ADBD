"""
Vista para corrección masiva de nombres de Sucursales en datos crudos.
Muestra cada nombre único y permite reasignar al código oficial.
Soporta ignorar nombres de forma persistente.
"""
import logging

from django.contrib import messages
from django.db import transaction
from django.db.models import Count
from django.shortcuts import render
from django.views import View

from ..models import Sucursal, Planificacion, Salida, IgnorarSucursal

logger = logging.getLogger(__name__)


class CorreccionSucursalesView(View):
    """
    Vista para corregir nombres de Sucursales en datos crudos (Planificacion y Salida).
    Muestra agrupaciones por similitud y permite asignar códigos oficiales.
    Soporta ignorar nombres de forma persistente.
    """
    template_name = "correccion_sucursales.html"

    def get(self, request):
        # 1. Obtener todas las Sucursales oficiales
        sucursales_oficiales = list(Sucursal.objects.all().order_by("bpl_id"))
        
        # 2. Obtener nombres ignorados
        ignorados = set(IgnorarSucursal.objects.values_list("nombre_crudo", flat=True))
        
        # 3. Obtener valores únicos de datos crudos
        sucursales_planificacion = (
            Planificacion.objects.exclude(sucursal__isnull=True)
            .exclude(sucursal="")
            .values("sucursal")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        
        almacen_destino_salida = (
            Salida.objects.exclude(nombre_almacen_destino__isnull=True)
            .exclude(nombre_almacen_destino="")
            .values("nombre_almacen_destino")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        
        sucursal_destino_salida = (
            Salida.objects.exclude(nombre_sucursal_destino__isnull=True)
            .exclude(nombre_sucursal_destino="")
            .values("nombre_sucursal_destino")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        
        # También obtener sucursal_destino_propuesto (usado en normalización)
        sucursal_propuesto_salida = (
            Salida.objects.exclude(sucursal_destino_propuesto__isnull=True)
            .exclude(sucursal_destino_propuesto="")
            .values("sucursal_destino_propuesto")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        
        # 4. Consolidar todos los nombres únicos
        nombres_unicos = []
        nombres_ignorados = []
        procesados = set()
        
        for item in sucursales_planificacion:
            nombre = item["sucursal"].strip()
            if nombre and nombre not in procesados:
                entry = {
                    "nombre": nombre,
                    "planificacion": item["count"],
                    "salida_almacen": 0,
                    "salida_sucursal": 0,
                    "ignorado": nombre in ignorados,
                }
                if nombre in ignorados:
                    nombres_ignorados.append(entry)
                else:
                    nombres_unicos.append(entry)
                procesados.add(nombre)
        
        for item in almacen_destino_salida:
            nombre = item["nombre_almacen_destino"].strip()
            if nombre:
                if nombre not in procesados:
                    entry = {
                        "nombre": nombre,
                        "planificacion": 0,
                        "salida_almacen": item["count"],
                        "salida_sucursal": 0,
                        "ignorado": nombre in ignorados,
                    }
                    if nombre in ignorados:
                        nombres_ignorados.append(entry)
                    else:
                        nombres_unicos.append(entry)
                    procesados.add(nombre)
                else:
                    for entry in nombres_unicos + nombres_ignorados:
                        if entry["nombre"] == nombre:
                            entry["salida_almacen"] += item["count"]
                            break
        
        for item in sucursal_destino_salida:
            nombre = item["nombre_sucursal_destino"].strip()
            if nombre:
                if nombre not in procesados:
                    entry = {
                        "nombre": nombre,
                        "planificacion": 0,
                        "salida_almacen": 0,
                        "salida_sucursal": item["count"],
                        "ignorado": nombre in ignorados,
                    }
                    if nombre in ignorados:
                        nombres_ignorados.append(entry)
                    else:
                        nombres_unicos.append(entry)
                    procesados.add(nombre)
                else:
                    for entry in nombres_unicos + nombres_ignorados:
                        if entry["nombre"] == nombre:
                            entry["salida_sucursal"] += item["count"]
                            break
        
        # Agregar nombres de sucursal_destino_propuesto (campo usado en normalización)
        for item in sucursal_propuesto_salida:
            nombre = item["sucursal_destino_propuesto"].strip()
            if nombre:
                if nombre not in procesados:
                    entry = {
                        "nombre": nombre,
                        "planificacion": 0,
                        "salida_almacen": 0,
                        "salida_sucursal": item["count"],
                        "ignorado": nombre in ignorados,
                    }
                    if nombre in ignorados:
                        nombres_ignorados.append(entry)
                    else:
                        nombres_unicos.append(entry)
                    procesados.add(nombre)
                else:
                    for entry in nombres_unicos + nombres_ignorados:
                        if entry["nombre"] == nombre:
                            entry["salida_sucursal"] += item["count"]
                            break
        
        # Ordenar por total de registros
        nombres_unicos.sort(key=lambda x: x["planificacion"] + x["salida_almacen"] + x["salida_sucursal"], reverse=True)
        nombres_ignorados.sort(key=lambda x: x["planificacion"] + x["salida_almacen"] + x["salida_sucursal"], reverse=True)
        
        # Combinar: primero los no ignorados, luego los ignorados
        todos_los_nombres = nombres_unicos + nombres_ignorados
        
        context = {
            "sucursales_oficiales": sucursales_oficiales,
            "nombres_unicos": todos_los_nombres,
            "total_registros_planificacion": sum(n["planificacion"] for n in todos_los_nombres),
            "total_registros_salida": sum(n["salida_almacen"] + n["salida_sucursal"] for n in todos_los_nombres),
            "total_nombres": len(todos_los_nombres),
            "total_ignorados": len(nombres_ignorados),
        }
        
        return render(request, self.template_name, context)

    def post(self, request):
        """
        Aplica las correcciones seleccionadas y guarda los ignorados.
        """
        logger.info("=" * 80)
        logger.info("INICIANDO CORRECCIÓN DE SUCURSALES")
        
        correcciones = {}
        ignorar_nuevos = []
        des_ignorar = []
        
        # Parsear datos del formulario
        idx = 1
        while True:
            nombre_crudo = request.POST.get(f"nombre_original_{idx}")
            bpl_id = request.POST.get(f"codigo_{idx}", "").strip()
            ignorar = request.POST.get(f"ignorar_{idx}") == "1"
            
            if not nombre_crudo:
                break
            
            # Verificar si estaba ignorado antes
            estaba_ignorado = IgnorarSucursal.objects.filter(nombre_crudo=nombre_crudo).exists()
            
            if ignorar and not estaba_ignorado:
                ignorar_nuevos.append(nombre_crudo)
                logger.info(f"🚫 Marcando para ignorar: '{nombre_crudo}'")
            elif not ignorar and estaba_ignorado:
                des_ignorar.append(nombre_crudo)
                logger.info(f"✅ Des-ignorando: '{nombre_crudo}'")
            elif bpl_id and not ignorar:
                correcciones[nombre_crudo] = bpl_id
                logger.info(f"✓ Agregado a correcciones: '{nombre_crudo}' → '{bpl_id}'")
            
            idx += 1
        
        # Aplicar cambios en ignorados
        with transaction.atomic():
            # Guardar nuevos ignorados
            for nombre in ignorar_nuevos:
                IgnorarSucursal.objects.get_or_create(
                    nombre_crudo=nombre,
                    defaults={"razon": "Ignorado desde corrección de Sucursales"}
                )
                # Marcar registros con error como ignorados
                Planificacion.objects.filter(
                    sucursal=nombre,
                    normalize_status="error"
                ).update(
                    normalize_status="ignored",
                    normalize_notes="Ignorado por configuración"
                )
                Salida.objects.filter(
                    nombre_sucursal_destino=nombre,
                    normalize_status="error"
                ).update(
                    normalize_status="ignored",
                    normalize_notes="Ignorado por configuración"
                )
                # También para sucursal_destino_propuesto
                Salida.objects.filter(
                    sucursal_destino_propuesto=nombre,
                    normalize_status="error"
                ).update(
                    normalize_status="ignored",
                    normalize_notes="Ignorado por configuración"
                )
            
            # Eliminar des-ignorados y resetear a pending
            if des_ignorar:
                IgnorarSucursal.objects.filter(nombre_crudo__in=des_ignorar).delete()
                # Resetear registros ignorados a pending para re-normalizarlos
                for nombre in des_ignorar:
                    Planificacion.objects.filter(
                        sucursal=nombre,
                        normalize_status="ignored"
                    ).update(
                        normalize_status="pending",
                        normalize_notes=""
                    )
                    Salida.objects.filter(
                        nombre_sucursal_destino=nombre,
                        normalize_status="ignored"
                    ).update(
                        normalize_status="pending",
                        normalize_notes=""
                    )
                    # También para sucursal_destino_propuesto
                    Salida.objects.filter(
                        sucursal_destino_propuesto=nombre,
                        normalize_status="ignored"
                    ).update(
                        normalize_status="pending",
                        normalize_notes=""
                    )
        
        # Aplicar correcciones de nombres
        registros_actualizados = {"planificacion": 0, "salida_almacen": 0, "salida_sucursal": 0}
        if correcciones:
            registros_actualizados = self._aplicar_correcciones(correcciones)
        
        # Construir mensaje
        msg_parts = []
        if correcciones:
            msg_parts.append(
                f"✅ Correcciones: {registros_actualizados['planificacion']} en Planificación, "
                f"{registros_actualizados['salida_almacen']} en Salidas (almacén), "
                f"{registros_actualizados['salida_sucursal']} en Salidas (sucursal)"
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
        correcciones: {nombre_crudo: bpl_id}
        También resetea registros con error a pending para re-normalizarlos.
        """
        count_planificacion = 0
        count_salida_almacen = 0
        count_salida_sucursal = 0
        
        for nombre_crudo, bpl_id in correcciones.items():
            # Actualizar en Planificacion y resetear a pending
            updated = Planificacion.objects.filter(sucursal=nombre_crudo).update(
                sucursal=bpl_id,
                normalize_status="pending",
                normalize_notes=""
            )
            count_planificacion += updated
            
            # Actualizar en Salida (nombre_almacen_destino) y resetear a pending
            updated = Salida.objects.filter(nombre_almacen_destino=nombre_crudo).update(
                nombre_almacen_destino=bpl_id,
                normalize_status="pending",
                normalize_notes=""
            )
            count_salida_almacen += updated
            
            # Actualizar en Salida (nombre_sucursal_destino) y resetear a pending
            updated = Salida.objects.filter(nombre_sucursal_destino=nombre_crudo).update(
                nombre_sucursal_destino=bpl_id,
                normalize_status="pending",
                normalize_notes=""
            )
            count_salida_sucursal += updated
            
            # También actualizar sucursal_destino_propuesto (campo usado en normalización)
            updated = Salida.objects.filter(sucursal_destino_propuesto=nombre_crudo).update(
                sucursal_destino_propuesto=bpl_id,
                normalize_status="pending",
                normalize_notes=""
            )
            count_salida_sucursal += updated
        
        return {
            "planificacion": count_planificacion,
            "salida_almacen": count_salida_almacen,
            "salida_sucursal": count_salida_sucursal,
        }
