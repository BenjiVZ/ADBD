"""
Vista para normalizar TODO (Planificaciones + Salidas) de un solo golpe.
"""
import datetime
from django.db import transaction
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views import View
from django.http import JsonResponse

from ..models import (
    Cendis, Planificacion, PlanificacionNormalizada, PlanningEntry, 
    Product, Salida, SalidaNormalizada, Sucursal, MapeoCedis, MapeoSucursal,
    IgnorarCedis, IgnorarSucursal
)


class NormalizarTodoView(View):
    template_name = "normalizar_todo.html"

    def get(self, request, *args, **kwargs):
        """Muestra el estado actual y botón para normalizar."""
        summary = self._get_summary()
        return render(request, self.template_name, {"summary": summary, "ran": False})

    def post(self, request, *args, **kwargs):
        """Ejecuta la normalización de planificaciones y salidas."""
        results = {}
        
        # 1. Normalizar Planificaciones
        results["planificacion"] = self._normalize_planificaciones()
        
        # 2. Normalizar Salidas
        results["salidas"] = self._normalize_salidas()
        
        summary = self._get_summary()
        return render(request, self.template_name, {
            "summary": summary, 
            "ran": True,
            "results": results
        })

    def _get_summary(self):
        """Obtiene resumen del estado actual."""
        return {
            "planificacion": {
                "pending": Planificacion.objects.filter(normalize_status="pending").count(),
                "ok": Planificacion.objects.filter(normalize_status="ok").count(),
                "error": Planificacion.objects.filter(normalize_status="error").count(),
                "ignored": Planificacion.objects.filter(normalize_status="ignored").count(),
                "total": Planificacion.objects.count(),
            },
            "salidas": {
                "pending": Salida.objects.filter(normalize_status="pending").count(),
                "ok": Salida.objects.filter(normalize_status="ok").count(),
                "error": Salida.objects.filter(normalize_status="error").count(),
                "ignored": Salida.objects.filter(normalize_status="ignored").count(),
                "total": Salida.objects.count(),
            }
        }

    def _normalize_planificaciones(self):
        """Normaliza todas las planificaciones pendientes."""
        to_process = Planificacion.objects.filter(normalize_status__in=["pending", "error"])
        
        if not to_process.exists():
            return {"processed": 0, "created": 0, "updated": 0, "errors": 0, "ignored": 0}
        
        # Pre-cargar datos
        sucursales = Sucursal.objects.all()
        cendis_list = Cendis.objects.all()
        products = Product.objects.all()
        mapeos_cedis = MapeoCedis.objects.select_related('cedis_oficial').all()
        mapeos_sucursales = MapeoSucursal.objects.select_related('sucursal_oficial').all()
        
        # Cargar nombres ignorados
        ignorados_cedis = set(i.lower() for i in IgnorarCedis.objects.values_list("nombre_crudo", flat=True))
        ignorados_sucursales = set(i.lower() for i in IgnorarSucursal.objects.values_list("nombre_crudo", flat=True))
        
        # Mapear
        sucursales_map = {}
        for s in sucursales:
            sucursales_map[s.name.lower()] = s
            sucursales_map[str(s.bpl_id).lower()] = s
        
        cendis_map = {}
        for c in cendis_list:
            cendis_map[c.origin.lower()] = c
            cendis_map[str(c.id).lower()] = c
            if c.code:
                cendis_map[c.code.lower()] = c
        
        products_map = {p.code.lower(): p for p in products}
        
        mapeos_cedis_dict = {}
        for m in mapeos_cedis:
            mapeos_cedis_dict[m.nombre_crudo.lower()] = m.cedis_oficial
        
        mapeos_sucursales_dict = {}
        for m in mapeos_sucursales:
            mapeos_sucursales_dict[m.nombre_crudo.lower()] = m.sucursal_oficial
        
        # Obtener existentes
        existing_normalized = {
            n.raw_id: n 
            for n in PlanificacionNormalizada.objects.filter(raw__in=to_process).select_related('raw')
        }
        
        created = 0
        updated = 0
        errors_count = 0
        ignored_count = 0
        to_create = []
        to_update = []
        to_update_raw = []
        now = timezone.now()

        with transaction.atomic():
            for raw in to_process:
                # Verificar si debe ser ignorado
                sucursal_key = raw.sucursal.strip().lower() if raw.sucursal else ""
                cedis_key = raw.cendis.strip().lower() if raw.cendis else ""
                
                if sucursal_key in ignorados_sucursales or cedis_key in ignorados_cedis:
                    raw.normalize_status = "ignored"
                    raw.normalize_notes = "Ignorado por configuración"
                    raw.normalized_at = None
                    to_update_raw.append(raw)
                    ignored_count += 1
                    continue
                
                issues = []

                # Normalizar SUCURSAL
                sucursal = None
                if raw.sucursal:
                    sucursal = sucursales_map.get(sucursal_key) or mapeos_sucursales_dict.get(sucursal_key)
                    if not sucursal:
                        issues.append(f"Sucursal no encontrada: {raw.sucursal}")
                else:
                    issues.append("Sin sucursal")

                # Normalizar CEDIS
                cedis_origen = None
                if raw.cendis:
                    cedis_origen = cendis_map.get(cedis_key) or mapeos_cedis_dict.get(cedis_key)
                    if not cedis_origen:
                        issues.append(f"CEDIS no encontrado: {raw.cendis}")

                # Normalizar PRODUCTO
                product = None
                if raw.item_code:
                    product = products_map.get(raw.item_code.strip().lower())
                    if not product:
                        issues.append(f"Producto no encontrado: {raw.item_code}")

                if issues:
                    raw.normalize_status = "error"
                    raw.normalize_notes = "; ".join(issues)
                    raw.normalized_at = None
                    to_update_raw.append(raw)
                    errors_count += 1
                    continue

                existing = existing_normalized.get(raw.id)
                
                if existing:
                    existing.tipo_carga = raw.tipo_carga
                    existing.item_name = raw.item_name
                    existing.product = product
                    existing.cendis = raw.cendis
                    existing.cedis_origen = cedis_origen
                    existing.a_despachar_total = raw.a_despachar_total
                    existing.plan_month = raw.plan_month
                    existing.item_code = raw.item_code
                    existing.sucursal = sucursal
                    to_update.append(existing)
                    updated += 1
                else:
                    to_create.append(
                        PlanificacionNormalizada(
                            raw=raw,
                            plan_month=raw.plan_month,
                            tipo_carga=raw.tipo_carga,
                            item_code=raw.item_code,
                            item_name=raw.item_name,
                            sucursal=sucursal,
                            cedis_origen=cedis_origen,
                            product=product,
                            cendis=raw.cendis,
                            a_despachar_total=raw.a_despachar_total,
                        )
                    )
                    created += 1

                raw.normalize_status = "ok"
                raw.normalize_notes = ""
                raw.normalized_at = now
                to_update_raw.append(raw)
            
            # Bulk operations
            if to_create:
                PlanificacionNormalizada.objects.bulk_create(to_create, batch_size=500)
            if to_update:
                PlanificacionNormalizada.objects.bulk_update(
                    to_update,
                    ['tipo_carga', 'item_name', 'product', 'cendis', 'cedis_origen',
                     'a_despachar_total', 'plan_month', 'item_code', 'sucursal'],
                    batch_size=500
                )
            if to_update_raw:
                Planificacion.objects.bulk_update(
                    to_update_raw,
                    ['normalize_status', 'normalize_notes', 'normalized_at'],
                    batch_size=500
                )

        return {"processed": to_process.count(), "created": created, "updated": updated, "errors": errors_count, "ignored": ignored_count}

    def _normalize_salidas(self):
        """Normaliza todas las salidas pendientes."""
        to_process = Salida.objects.filter(normalize_status__in=["pending", "error"])
        
        if not to_process.exists():
            return {"processed": 0, "created": 0, "updated": 0, "errors": 0, "ignored": 0}
        
        # Pre-cargar datos
        sucursales = Sucursal.objects.all()
        cendis_list = Cendis.objects.all()
        products = Product.objects.all()
        mapeos_cedis = MapeoCedis.objects.select_related('cedis_oficial').all()
        mapeos_sucursales = MapeoSucursal.objects.select_related('sucursal_oficial').all()
        
        # Cargar nombres ignorados
        ignorados_cedis = set(i.lower() for i in IgnorarCedis.objects.values_list("nombre_crudo", flat=True))
        ignorados_sucursales = set(i.lower() for i in IgnorarSucursal.objects.values_list("nombre_crudo", flat=True))
        
        # Mapear
        sucursales_map = {}
        for s in sucursales:
            sucursales_map[s.name.lower()] = s
            sucursales_map[str(s.bpl_id).lower()] = s
        
        cendis_map = {}
        for c in cendis_list:
            cendis_map[c.origin.lower()] = c
            cendis_map[str(c.id).lower()] = c
            if c.code:
                cendis_map[c.code.lower()] = c
        
        products_map = {p.code.lower(): p for p in products}
        
        mapeos_cedis_dict = {}
        for m in mapeos_cedis:
            mapeos_cedis_dict[m.nombre_crudo.lower()] = m.cedis_oficial
        
        mapeos_sucursales_dict = {}
        for m in mapeos_sucursales:
            mapeos_sucursales_dict[m.nombre_crudo.lower()] = m.sucursal_oficial
        
        # Obtener existentes
        existing_normalized = {
            n.raw_id: n 
            for n in SalidaNormalizada.objects.filter(raw__in=to_process).select_related('raw')
        }
        
        created = 0
        updated = 0
        errors_count = 0
        ignored_count = 0
        to_create = []
        to_update = []
        to_update_raw = []
        now = timezone.now()

        with transaction.atomic():
            for raw in to_process:
                # Obtener el campo de sucursal destino (intentar varios campos)
                sucursal_raw = (
                    raw.sucursal_destino_propuesto or 
                    raw.nombre_sucursal_destino or 
                    raw.nombre_almacen_destino or 
                    ""
                ).strip()
                
                cedis_raw = (
                    raw.nombre_sucursal_origen or 
                    raw.nombre_almacen_origen or 
                    ""
                ).strip()
                
                sucursal_key = sucursal_raw.lower() if sucursal_raw else ""
                cedis_key = cedis_raw.lower() if cedis_raw else ""
                
                # Ignorar registros sin sucursal destino (vacíos)
                if not sucursal_raw:
                    raw.normalize_status = "ignored"
                    raw.normalize_notes = "Sin sucursal destino - ignorado automáticamente"
                    raw.normalized_at = None
                    to_update_raw.append(raw)
                    ignored_count += 1
                    continue
                
                # Verificar si debe ser ignorado por configuración
                if sucursal_key in ignorados_sucursales or cedis_key in ignorados_cedis:
                    raw.normalize_status = "ignored"
                    raw.normalize_notes = "Ignorado por configuración"
                    raw.normalized_at = None
                    to_update_raw.append(raw)
                    ignored_count += 1
                    continue
                
                issues = []

                # Normalizar SUCURSAL DESTINO
                sucursal_destino = None
                if sucursal_raw:
                    # Buscar por nombre, ID, o mapeo
                    sucursal_destino = (
                        sucursales_map.get(sucursal_key) or 
                        mapeos_sucursales_dict.get(sucursal_key)
                    )
                    if not sucursal_destino:
                        issues.append(f"Sucursal destino no encontrada: {sucursal_raw}")

                # Normalizar CEDIS ORIGEN
                cedis_origen = None
                if cedis_raw:
                    cedis_origen = cendis_map.get(cedis_key) or mapeos_cedis_dict.get(cedis_key)
                    if not cedis_origen:
                        issues.append(f"CEDIS origen no encontrado: {cedis_raw}")

                # Normalizar PRODUCTO (usando sku del modelo Salida)
                product = None
                if raw.sku:
                    product = products_map.get(raw.sku.strip().lower())
                    if not product:
                        issues.append(f"Producto no encontrado: {raw.sku}")

                if issues:
                    raw.normalize_status = "error"
                    raw.normalize_notes = "; ".join(issues)
                    raw.normalized_at = None
                    to_update_raw.append(raw)
                    errors_count += 1
                    continue

                existing = existing_normalized.get(raw.id)
                
                if existing:
                    existing.fecha_salida = raw.fecha_salida
                    existing.sku = raw.sku
                    existing.descripcion = raw.descripcion
                    existing.product = product
                    existing.sucursal_destino = sucursal_destino
                    existing.cedis_origen = cedis_origen
                    existing.cantidad = raw.cantidad
                    existing.origen_nombre = raw.nombre_sucursal_origen
                    existing.destino_nombre = raw.nombre_sucursal_destino
                    to_update.append(existing)
                    updated += 1
                else:
                    to_create.append(
                        SalidaNormalizada(
                            raw=raw,
                            salida=raw.salida,
                            fecha_salida=raw.fecha_salida,
                            sku=raw.sku,
                            descripcion=raw.descripcion,
                            product=product,
                            sucursal_destino=sucursal_destino,
                            cedis_origen=cedis_origen,
                            cantidad=raw.cantidad,
                            origen_nombre=raw.nombre_sucursal_origen,
                            destino_nombre=raw.nombre_sucursal_destino,
                            entrada=raw.entrada,
                            fecha_entrada=raw.fecha_entrada,
                            comments=raw.comments,
                        )
                    )
                    created += 1

                raw.normalize_status = "ok"
                raw.normalize_notes = ""
                raw.normalized_at = now
                to_update_raw.append(raw)
            
            # Bulk operations
            if to_create:
                SalidaNormalizada.objects.bulk_create(to_create, batch_size=500)
            if to_update:
                SalidaNormalizada.objects.bulk_update(
                    to_update,
                    ['fecha_salida', 'sku', 'descripcion', 'product', 
                     'sucursal_destino', 'cedis_origen', 'cantidad',
                     'origen_nombre', 'destino_nombre'],
                    batch_size=500
                )
            if to_update_raw:
                Salida.objects.bulk_update(
                    to_update_raw,
                    ['normalize_status', 'normalize_notes', 'normalized_at'],
                    batch_size=500
                )

        return {"processed": to_process.count(), "created": created, "updated": updated, "errors": errors_count, "ignored": ignored_count}

