import datetime

from django.db import transaction
from django.shortcuts import render
from django.utils import timezone
from django.views import View

from ..models import Cendis, Product, Salida, SalidaNormalizada, Sucursal, MapeoCedis, MapeoSucursal


class SalidaNormalizeView(View):
    template_name = "salida_normalizar.html"

    def get(self, request, *args, **kwargs):
        selected_date = self._selected_date(request)
        dates = self._dates()
        summary = self._summary(selected_date)
        errors = self._errors(selected_date)
        pending = self._pending(selected_date)
        return render(
            request,
            self.template_name,
            {
                "summary": summary,
                "errors": errors,
                "pending": pending,
                "selected_date": selected_date,
                "dates": dates,
                "ran": False,
            },
        )

    def post(self, request, *args, **kwargs):
        selected_date = self._selected_date(request)
        dates = self._dates()
        
        # Verificar si es una acción de limpieza
        action = request.POST.get('action')
        reset_message = None
        if action == 'reset_date' and selected_date:
            # Limpiar normalizaciones de esta fecha específica
            # selected_date ya es un objeto date, no necesita parsear
            fecha_obj = selected_date if isinstance(selected_date, datetime.date) else datetime.datetime.strptime(selected_date, "%Y-%m-%d").date()
            
            # Resetear estado de Salidas de esta fecha
            reset_count = Salida.objects.filter(fecha_salida=fecha_obj).update(
                normalize_status='pending',
                normalize_notes='',
                normalized_at=None
            )
            
            # Eliminar registros normalizados de esta fecha
            deleted_count = SalidaNormalizada.objects.filter(fecha_salida=fecha_obj).delete()[0]
            
            print(f"🗑️ Limpiada fecha {selected_date}: {reset_count} registros reseteados, {deleted_count} normalizados eliminados")
            reset_message = f"✅ Fecha {selected_date} limpiada: {reset_count} registros listos para re-normalizar"
            # Continuar con la normalización automáticamente...

        # Normalizar TODAS las fechas - no filtrar por fecha seleccionada
        queryset = Salida.objects.filter(normalize_status__in=["pending", "error"])
        
        print(f"\n🔄 INICIANDO NORMALIZACIÓN DE SALIDAS")
        print(f"📊 Total de registros a procesar: {queryset.count()}")

        # Pre-cargar datos en memoria para evitar N+1 queries
        sucursales = Sucursal.objects.all()
        cendis_list = Cendis.objects.all()
        products = Product.objects.all()
        
        # Cargar mapeos
        mapeos_cedis = MapeoCedis.objects.select_related('cedis_oficial').all()
        mapeos_sucursales = MapeoSucursal.objects.select_related('sucursal_oficial').all()
        
        print(f"✅ Cargadas {len(sucursales)} sucursales")
        print(f"✅ Cargados {len(cendis_list)} CENDIS")
        print(f"✅ Cargados {len(products)} productos")
        print(f"✅ Cargados {len(mapeos_cedis)} mapeos de CEDIS")
        print(f"✅ Cargados {len(mapeos_sucursales)} mapeos de Sucursales")
        
        sucursales_map = {s.name.lower(): s for s in sucursales}
        cendis_map = {c.origin.lower(): c for c in cendis_list}
        products_map = {p.code.lower(): p for p in products}
        
        # Mapeos: nombre_crudo -> entidad_oficial
        mapeos_cedis_dict = {m.nombre_crudo.lower(): m.cedis_oficial for m in mapeos_cedis}
        mapeos_sucursales_dict = {m.nombre_crudo.lower(): m.sucursal_oficial for m in mapeos_sucursales}
        
        print(f"\n📋 CENDIS disponibles: {list(cendis_map.keys())}")
        print(f"📋 Sucursales disponibles (primeras 10): {list(sucursales_map.keys())[:10]}")
        print(f"🔗 Mapeos CEDIS: {list(mapeos_cedis_dict.keys())}")
        print(f"🔗 Mapeos Sucursales (primeras 10): {list(mapeos_sucursales_dict.keys())[:10]}")
        
        # Obtener registros normalizados existentes de una vez
        existing_normalized = {
            n.raw_id: n 
            for n in SalidaNormalizada.objects.filter(
                raw__in=queryset
            ).select_related('raw')
        }
        
        created = 0
        updated = 0
        errors_count = 0
        
        to_create = []
        to_update = []
        to_update_raw = []
        now = timezone.now()

        with transaction.atomic():
            record_count = 0
            for raw in queryset:
                record_count += 1
                if record_count <= 5:  # Log primeros 5 registros
                    print(f"\n🔍 Registro #{record_count}:")
                    print(f"   ID: {raw.id}")
                    print(f"   Origen raw (almacen): '{raw.nombre_almacen_origen}'")
                    print(f"   Destino raw: '{raw.nombre_sucursal_destino}'")
                    print(f"   SKU: '{raw.sku}'")
                
                issues = []

                # ORIGEN: DEBE estar en CEDIS (almacenes) - SI NO → ERROR
                cedis_origen = None
                if raw.nombre_almacen_origen:
                    origen_key = raw.nombre_almacen_origen.strip().lower()
                    # 1. Buscar nombre exacto en CEDIS
                    cedis_origen = cendis_map.get(origen_key)
                    # 2. Si no existe, buscar en mapeos de CEDIS
                    if not cedis_origen:
                        cedis_origen = mapeos_cedis_dict.get(origen_key)
                    
                    if not cedis_origen:
                        # NO está en CEDIS → ERROR (aunque esté en Sucursales)
                        if record_count <= 5:
                            en_sucursal = origen_key in sucursales_map
                            if en_sucursal:
                                print(f"   ❌ Origen '{origen_key}' NO es un CEDIS (está en Sucursales) → ERROR")
                            else:
                                print(f"   ❌ Origen '{origen_key}' NO encontrado en CEDIS → ERROR")
                        issues.append(f"Origen NO es un almacén CEDIS: {raw.nombre_almacen_origen}")
                    else:
                        if record_count <= 5:
                            print(f"   ✅ Origen: '{origen_key}' → CEDIS (almacén) encontrado")
                else:
                    if record_count <= 5:
                        print(f"   ⚠️ Origen: Sin valor (nombre_almacen_origen vacío)")
                    issues.append("Sin origen especificado")

                # DESTINO debe ser Sucursal/Tienda (tabla Sucursal)
                # Usar nombre_sucursal_destino, o sucursal_destino_propuesto como fallback
                sucursal_destino = None
                destino_nombre = raw.nombre_sucursal_destino or raw.sucursal_destino_propuesto
                if destino_nombre:
                    destino_key = destino_nombre.strip().lower()
                    # 1. Buscar nombre exacto en Sucursales
                    sucursal_destino = sucursales_map.get(destino_key)
                    # 2. Si no existe, buscar en mapeos de Sucursales
                    if not sucursal_destino:
                        sucursal_destino = mapeos_sucursales_dict.get(destino_key)
                    
                    if record_count <= 5:
                        status = '✅ Encontrada' if sucursal_destino else '❌ NO encontrada'
                        print(f"   🏢 Buscando sucursal/tienda destino: '{destino_key}' -> {status}")
                    if not sucursal_destino:
                        issues.append(f"Sucursal/tienda destino no encontrada: {destino_nombre}")
                else:
                    if record_count <= 5:
                        print(f"   🏢 Sucursal/tienda destino: ⚠️ Sin valor")

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

                payload = {
                    "salida": raw.salida or "",
                    "fecha_salida": raw.fecha_salida,
                    "sku": raw.sku or "",
                    "descripcion": raw.descripcion or "",
                    "cantidad": raw.cantidad,
                    "cedis_origen": cedis_origen,
                    "sucursal_destino": sucursal_destino,
                    "product": product,
                    "origen_nombre": raw.nombre_almacen_origen or "",
                    "destino_nombre": destino_nombre or "",  # Usar el nombre resuelto (puede venir de sucursal_destino_propuesto)
                    "entrada": raw.entrada or "",
                    "fecha_entrada": raw.fecha_entrada,
                    "comments": raw.comments or "",
                }

                existing = existing_normalized.get(raw.id)
                
                if existing:
                    # Actualizar existente
                    for field, value in payload.items():
                        setattr(existing, field, value)
                    to_update.append(existing)
                    updated += 1
                else:
                    # Crear nuevo
                    to_create.append(
                        SalidaNormalizada(raw=raw, **payload)
                    )
                    created += 1

                raw.normalize_status = "ok"
                raw.normalize_notes = ""
                raw.normalized_at = now
                to_update_raw.append(raw)
            
            # Bulk operations - CRÍTICO: Asegurar que se ejecuten
            print(f"\n💾 Ejecutando operaciones bulk...")
            
            if to_create:
                print(f"   ➕ Creando {len(to_create)} registros normalizados...")
                SalidaNormalizada.objects.bulk_create(to_create, batch_size=500)
                print(f"   ✅ Creados")
            
            if to_update:
                print(f"   ♻️ Actualizando {len(to_update)} registros normalizados...")
                SalidaNormalizada.objects.bulk_update(
                    to_update,
                    ['salida', 'fecha_salida', 'sku', 'descripcion', 'cantidad',
                     'cedis_origen', 'sucursal_destino', 'product', 
                     'origen_nombre', 'destino_nombre', 'entrada', 
                     'fecha_entrada', 'comments'],
                    batch_size=500
                )
                print(f"   ✅ Actualizados")
            
            if to_update_raw:
                print(f"   📝 Actualizando {len(to_update_raw)} registros raw...")
                Salida.objects.bulk_update(
                    to_update_raw,
                    ['normalize_status', 'normalize_notes', 'normalized_at'],
                    batch_size=500
                )
                print(f"   ✅ Actualizados")
        
        print(f"\n✅ NORMALIZACIÓN DE SALIDAS COMPLETADA")
        print(f"   📊 Procesados: {queryset.count()}")
        print(f"   ➕ Creados: {created}")
        print(f"   ♻️ Actualizados: {updated}")
        print(f"   ❌ Errores: {errors_count}")

        summary = self._summary(selected_date)
        errors = self._errors(selected_date)
        pending = self._pending(selected_date)

        context = {
            "summary": summary,
            "errors": errors,
            "pending": pending,
            "selected_date": selected_date,
            "dates": dates,
            "ran": True,
            "run_result": {
                "processed": queryset.count(),
                "created": created,
                "updated": updated,
                "errors": errors_count,
            },
        }
        
        # Agregar mensaje de reset si existe
        if reset_message:
            context["message"] = reset_message

        return render(
            request,
            self.template_name,
            context,
        )

    def _dates(self):
        return list(
            Salida.objects.filter(fecha_salida__isnull=False)
            .order_by("-fecha_salida")
            .values_list("fecha_salida", flat=True)
            .distinct()
        )

    def _selected_date(self, request):
        raw_date = request.GET.get("fecha_salida") or request.POST.get("fecha_salida")
        if raw_date:
            try:
                # Intentar formato estándar YYYY-MM-DD primero
                return datetime.datetime.strptime(raw_date, "%Y-%m-%d").date()
            except ValueError:
                try:
                    # Intentar formato de Django "Jan. 14, 2026"
                    return datetime.datetime.strptime(raw_date, "%b. %d, %Y").date()
                except ValueError:
                    return None
        dates = self._dates()
        return dates[0] if dates else None

    def _summary(self, selected_date):
        qs = Salida.objects.all()
        if selected_date:
            qs = qs.filter(fecha_salida=selected_date)
        return {
            "pending": qs.filter(normalize_status="pending").count(),
            "ok": qs.filter(normalize_status="ok").count(),
            "error": qs.filter(normalize_status="error").count(),
            "total": qs.count(),
        }

    def _errors(self, selected_date):
        qs = Salida.objects.filter(normalize_status="error")
        if selected_date:
            qs = qs.filter(fecha_salida=selected_date)
        return qs.order_by("-created_at")[:50]

    def _pending(self, selected_date):
        qs = Salida.objects.filter(normalize_status="pending")
        if selected_date:
            qs = qs.filter(fecha_salida=selected_date)
        return qs.order_by("-created_at")[:50]
