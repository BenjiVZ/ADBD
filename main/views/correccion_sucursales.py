"""
Vista para corrección masiva de nombres de Sucursales en datos crudos.
Muestra cada nombre único y permite reasignar al código oficial.
"""
import logging

from django.contrib import messages
from django.db import transaction
from django.db.models import Count
from django.shortcuts import render
from django.views import View

from ..models import Sucursal, Planificacion, Salida

logger = logging.getLogger(__name__)


class CorreccionSucursalesView(View):
    """
    Vista para corregir nombres de Sucursales en datos crudos (Planificacion y Salida).
    Muestra agrupaciones por similitud y permite asignar códigos oficiales.
    """
    template_name = "correccion_sucursales.html"

    def get(self, request):
        # 1. Obtener todas las Sucursales oficiales
        sucursales_oficiales = list(Sucursal.objects.all().order_by("bpl_id"))
        
        # 2. Obtener valores únicos de datos crudos
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
        
        # 3. Consolidar todos los nombres únicos (sin agrupar)
        nombres_unicos = []
        procesados = set()
        
        for item in sucursales_planificacion:
            nombre = item["sucursal"].strip()
            if nombre and nombre not in procesados:
                nombres_unicos.append({
                    "nombre": nombre,
                    "planificacion": item["count"],
                    "salida_almacen": 0,
                    "salida_sucursal": 0,
                })
                procesados.add(nombre)
        
        for item in almacen_destino_salida:
            nombre = item["nombre_almacen_destino"].strip()
            if nombre:
                if nombre not in procesados:
                    nombres_unicos.append({
                        "nombre": nombre,
                        "planificacion": 0,
                        "salida_almacen": item["count"],
                        "salida_sucursal": 0,
                    })
                    procesados.add(nombre)
                else:
                    for entry in nombres_unicos:
                        if entry["nombre"] == nombre:
                            entry["salida_almacen"] += item["count"]
                            break
        
        for item in sucursal_destino_salida:
            nombre = item["nombre_sucursal_destino"].strip()
            if nombre:
                if nombre not in procesados:
                    nombres_unicos.append({
                        "nombre": nombre,
                        "planificacion": 0,
                        "salida_almacen": 0,
                        "salida_sucursal": item["count"],
                    })
                    procesados.add(nombre)
                else:
                    for entry in nombres_unicos:
                        if entry["nombre"] == nombre:
                            entry["salida_sucursal"] += item["count"]
                            break
        
        # Ordenar por total de registros
        nombres_unicos.sort(key=lambda x: x["planificacion"] + x["salida_almacen"] + x["salida_sucursal"], reverse=True)
        
        context = {
            "sucursales_oficiales": sucursales_oficiales,
            "nombres_unicos": nombres_unicos,
            "total_registros_planificacion": sum(n["planificacion"] for n in nombres_unicos),
            "total_registros_salida": sum(n["salida_almacen"] + n["salida_sucursal"] for n in nombres_unicos),
            "total_nombres": len(nombres_unicos),
        }
        
        return render(request, self.template_name, context)

    def post(self, request):
        """
        Aplica las correcciones seleccionadas.
        Espera: correcciones = {nombre_crudo: bpl_id_oficial}
        """
        logger.info("=" * 80)
        logger.info("INICIANDO CORRECCIÓN DE SUCURSALES")
        logger.info(f"Datos POST recibidos: {dict(request.POST)}")
        
        correcciones = {}
        
        # Parsear datos del formulario
        idx = 1
        while True:
            nombre_crudo = request.POST.get(f"nombre_original_{idx}")
            bpl_id = request.POST.get(f"codigo_{idx}", "").strip()
            
            if not nombre_crudo:
                break
                
            logger.info(f"Procesando índice {idx}: nombre_crudo='{nombre_crudo}', bpl_id='{bpl_id}'")
            
            if bpl_id:
                correcciones[nombre_crudo] = bpl_id
                logger.info(f"✓ Agregado a correcciones: '{nombre_crudo}' → '{bpl_id}'")
            
            idx += 1
        
        logger.info(f"Total de correcciones parseadas: {len(correcciones)}")
        logger.info(f"Correcciones: {correcciones}")
        
        if not correcciones:
            logger.warning("No se encontraron correcciones en el formulario")
            messages.warning(request, "No se seleccionaron correcciones.")
            return self.get(request)
        
        # Aplicar correcciones
        registros_actualizados = self._aplicar_correcciones(correcciones)
        
        logger.info(f"Registros actualizados: {registros_actualizados}")
        logger.info("CORRECCIÓN DE SUCURSALES COMPLETADA")
        logger.info("=" * 80)
        
        messages.success(
            request,
            f"✅ Correcciones aplicadas: {registros_actualizados['planificacion']} en Planificación, "
            f"{registros_actualizados['salida_almacen']} en Salidas (almacén destino), "
            f"{registros_actualizados['salida_sucursal']} en Salidas (sucursal destino)."
        )
        
        return self.get(request)

    @transaction.atomic
    def _aplicar_correcciones(self, correcciones):
        """
        Aplica las correcciones en los datos crudos.
        correcciones: {nombre_crudo: bpl_id}
        """
        count_planificacion = 0
        count_salida_almacen = 0
        count_salida_sucursal = 0
        
        logger.info("Aplicando correcciones a la base de datos...")
        
        for nombre_crudo, bpl_id in correcciones.items():
            logger.info(f"Corrigiendo '{nombre_crudo}' → '{bpl_id}'")
            
            # Actualizar en Planificacion
            updated = Planificacion.objects.filter(sucursal=nombre_crudo).update(
                sucursal=bpl_id
            )
            logger.info(f"  - Planificación: {updated} registros actualizados")
            count_planificacion += updated
            
            # Actualizar en Salida (nombre_almacen_destino)
            updated = Salida.objects.filter(nombre_almacen_destino=nombre_crudo).update(
                nombre_almacen_destino=bpl_id
            )
            logger.info(f"  - Salidas (almacén destino): {updated} registros actualizados")
            count_salida_almacen += updated
            
            # Actualizar en Salida (nombre_sucursal_destino)
            updated = Salida.objects.filter(nombre_sucursal_destino=nombre_crudo).update(
                nombre_sucursal_destino=bpl_id
            )
            logger.info(f"  - Salidas (sucursal destino): {updated} registros actualizados")
            count_salida_sucursal += updated
        
        logger.info(f"Total actualizado: Planificación={count_planificacion}, Salidas(almacén)={count_salida_almacen}, Salidas(sucursal)={count_salida_sucursal}")
        
        return {
            "planificacion": count_planificacion,
            "salida_almacen": count_salida_almacen,
            "salida_sucursal": count_salida_sucursal,
        }
