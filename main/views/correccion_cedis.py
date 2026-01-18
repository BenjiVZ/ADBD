"""
Vista para corrección masiva de nombres de CEDIS en datos crudos.
Muestra cada nombre único y permite reasignar al código oficial.
"""
import logging

from django.contrib import messages
from django.db import transaction
from django.db.models import Count
from django.shortcuts import render
from django.views import View

from ..models import Cendis, Planificacion, Salida

logger = logging.getLogger(__name__)


class CorreccionCedisView(View):
    """
    Vista para corregir nombres de CEDIS en datos crudos (Planificacion y Salida).
    Muestra agrupaciones por similitud y permite asignar códigos oficiales.
    """
    template_name = "correccion_cedis.html"

    def get(self, request):
        # 1. Obtener todos los CEDIS oficiales
        cedis_oficiales = list(Cendis.objects.all().order_by("code"))
        
        # 2. Obtener valores únicos de datos crudos
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
        
        # 3. Consolidar todos los nombres únicos (sin agrupar)
        nombres_unicos = []
        procesados = set()
        
        for item in cedis_planificacion:
            nombre = item["cendis"].strip()
            if nombre and nombre not in procesados:
                nombres_unicos.append({
                    "nombre": nombre,
                    "planificacion": item["count"],
                    "salida": 0,
                })
                procesados.add(nombre)
        
        for item in nombres_almacen_salida:
            nombre = item["nombre_almacen_origen"].strip()
            if nombre:
                if nombre not in procesados:
                    nombres_unicos.append({
                        "nombre": nombre,
                        "planificacion": 0,
                        "salida": item["count"],
                    })
                    procesados.add(nombre)
                else:
                    # Actualizar conteo de salida si ya existe
                    for entry in nombres_unicos:
                        if entry["nombre"] == nombre:
                            entry["salida"] += item["count"]
                            break
        
        # Ordenar por total de registros
        nombres_unicos.sort(key=lambda x: x["planificacion"] + x["salida"], reverse=True)
        
        context = {
            "cedis_oficiales": cedis_oficiales,
            "nombres_unicos": nombres_unicos,
            "total_registros_planificacion": sum(n["planificacion"] for n in nombres_unicos),
            "total_registros_salida": sum(n["salida"] for n in nombres_unicos),
            "total_nombres": len(nombres_unicos),
        }
        
        return render(request, self.template_name, context)

    def post(self, request):
        """
        Aplica las correcciones seleccionadas.
        Espera: correcciones = {nombre_crudo: codigo_cedis_oficial}
        """
        logger.info("=" * 80)
        logger.info("INICIANDO CORRECCIÓN DE CEDIS")
        logger.info(f"Datos POST recibidos: {dict(request.POST)}")
        
        correcciones = {}
        
        # Parsear datos del formulario
        idx = 1
        while True:
            nombre_crudo = request.POST.get(f"nombre_original_{idx}")
            codigo_oficial = request.POST.get(f"codigo_{idx}", "").strip()
            
            if not nombre_crudo:
                break
                
            logger.info(f"Procesando índice {idx}: nombre_crudo='{nombre_crudo}', codigo_oficial='{codigo_oficial}'")
            
            if codigo_oficial:
                correcciones[nombre_crudo] = codigo_oficial
                logger.info(f"✓ Agregado a correcciones: '{nombre_crudo}' → '{codigo_oficial}'")
            
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
        logger.info("CORRECCIÓN DE CEDIS COMPLETADA")
        logger.info("=" * 80)
        
        messages.success(
            request,
            f"✅ Correcciones aplicadas: {registros_actualizados['planificacion']} "
            f"en Planificación, {registros_actualizados['salida']} en Salidas."
        )
        
        return self.get(request)

    @transaction.atomic
    def _aplicar_correcciones(self, correcciones):
        """
        Aplica las correcciones en los datos crudos.
        correcciones: {nombre_crudo: codigo_oficial}
        """
        count_planificacion = 0
        count_salida = 0
        
        logger.info("Aplicando correcciones a la base de datos...")
        
        for nombre_crudo, codigo_oficial in correcciones.items():
            logger.info(f"Corrigiendo '{nombre_crudo}' → '{codigo_oficial}'")
            # Actualizar en Planificacion
            updated = Planificacion.objects.filter(cendis=nombre_crudo).update(
                cendis=codigo_oficial
            )
            logger.info(f"  - Planificación: {updated} registros actualizados")
            count_planificacion += updated
            
            # Actualizar en Salida
            updated = Salida.objects.filter(nombre_almacen_origen=nombre_crudo).update(
                nombre_almacen_origen=codigo_oficial
            )
            logger.info(f"  - Salidas: {updated} registros actualizados")
            count_salida += updated
        
        logger.info(f"Total actualizado: Planificación={count_planificacion}, Salidas={count_salida}")
        
        return {
            "planificacion": count_planificacion,
            "salida": count_salida,
        }
