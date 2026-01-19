import datetime

from django.db import transaction
from django.shortcuts import render
from django.utils import timezone
from django.views import View

from ..models import Cendis, Planificacion, PlanificacionNormalizada, PlanningEntry, Product, Sucursal, MapeoCedis, MapeoSucursal


class PlanificacionNormalizeView(View):
    template_name = "planificacion_normalizar.html"

    def get(self, request, *args, **kwargs):
        self._sync_from_legacy()
        selected_month = self._selected_month(request)
        months = self._months()
        summary = self._summary(selected_month)
        errors = (
            Planificacion.objects.filter(normalize_status="error")
            .filter(plan_month=selected_month)
            .order_by("-created_at")[:50]
            if selected_month
            else []
        )
        pending = (
            Planificacion.objects.filter(normalize_status="pending")
            .filter(plan_month=selected_month)
            .order_by("-created_at")[:50]
            if selected_month
            else []
        )
        return render(
            request,
            self.template_name,
            {
                "summary": summary,
                "errors": errors,
                "pending": pending,
                "ran": False,
                "months": months,
                "selected_month": selected_month,
            },
        )

    def post(self, request, *args, **kwargs):
        self._sync_from_legacy()
        selected_month = self._selected_month(request)
        months = self._months()
        
        # Verificar si es una acción de limpieza
        action = request.POST.get('action')
        reset_message = None
        
        # Si es solo limpieza (sin normalización), hacerlo y retornar
        if action == 'reset_all':
            # Limpiar TODAS las normalizaciones de planificación
            
            # Resetear estado de TODAS las Planificaciones
            reset_count = Planificacion.objects.all().update(
                normalize_status='pending',
                normalize_notes='',
                normalized_at=None
            )
            
            # Eliminar TODOS los registros normalizados
            deleted_count = PlanificacionNormalizada.objects.all().delete()[0]
            
            print(f"🗑️ Limpiadas TODAS las normalizaciones: {reset_count} registros reseteados, {deleted_count} normalizados eliminados")
            
            # Retornar inmediatamente después de limpiar (no normalizar automáticamente)
            summary = self._summary(selected_month)
            errors = []
            pending = []
            
            return render(request, self.template_name, {
                "summary": summary,
                "errors": errors,
                "pending": pending,
                "ran": False,
                "months": months,
                "selected_month": selected_month,
                "reset_message": f"✅ Todas las normalizaciones limpiadas: {reset_count} registros reseteados, {deleted_count} eliminados. Presiona 'Normalizar pendientes' para procesar."
            })
            
        elif action == 'reset_month' and selected_month:
            # Limpiar normalizaciones de este mes específico
            
            # Resetear estado de Planificacion de este mes
            reset_count = Planificacion.objects.filter(plan_month=selected_month).update(
                normalize_status='pending',
                normalize_notes='',
                normalized_at=None
            )
            
            # Eliminar registros normalizados de este mes
            deleted_count = PlanificacionNormalizada.objects.filter(plan_month=selected_month).delete()[0]
            
            print(f"🗑️ Limpiado mes {selected_month}: {reset_count} registros reseteados, {deleted_count} normalizados eliminados")
            reset_message = f"✅ Mes {selected_month.strftime('%Y-%m')} limpiado: {reset_count} registros listos para re-normalizar"
            # Continuar con la normalización automáticamente...

        # Normalizar TODOS los meses - no filtrar por mes seleccionado
        to_process = Planificacion.objects.filter(normalize_status__in=["pending", "error"])
        
        # Pre-cargar datos en memoria para evitar N+1 queries
        print(f"\n🔄 INICIANDO NORMALIZACIÓN")
        print(f"📊 Total de registros a procesar: {to_process.count()}")
        
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
        
        # Mapear por NOMBRE y por CÓDIGO/ID
        sucursales_map = {}
        for s in sucursales:
            sucursales_map[s.name.lower()] = s  # Por nombre
            sucursales_map[str(s.bpl_id).lower()] = s  # Por BPL_ID
        
        cendis_map = {}
        for c in cendis_list:
            cendis_map[c.origin.lower()] = c  # Por nombre (origin)
            cendis_map[str(c.id).lower()] = c  # Por ID
            if c.code:
                cendis_map[c.code.lower()] = c  # Por código
        
        products_map = {p.code.lower(): p for p in products}
        
        # Mapeos: nombre_crudo -> entidad_oficial (ahora también por ID)
        mapeos_cedis_dict = {}
        for m in mapeos_cedis:
            # Por nombre crudo
            mapeos_cedis_dict[m.nombre_crudo.lower()] = m.cedis_oficial
            # También mapear por ID del CEDIS oficial para buscar por ID
            mapeos_cedis_dict[str(m.cedis_oficial.id).lower()] = m.cedis_oficial
            # Y por código si existe
            if m.cedis_oficial.code:
                mapeos_cedis_dict[m.cedis_oficial.code.lower()] = m.cedis_oficial
        
        mapeos_sucursales_dict = {}
        for m in mapeos_sucursales:
            # Por nombre crudo
            mapeos_sucursales_dict[m.nombre_crudo.lower()] = m.sucursal_oficial
            # También mapear por BPL_ID de la sucursal oficial
            mapeos_sucursales_dict[str(m.sucursal_oficial.bpl_id).lower()] = m.sucursal_oficial
        
        print(f"\n📋 CENDIS disponibles: {list(cendis_map.keys())}")
        print(f"📋 Sucursales disponibles (primeras 10): {list(sucursales_map.keys())[:10]}")
        print(f"🔗 Mapeos CEDIS (incluye nombres e IDs): {len(mapeos_cedis_dict)} entradas")
        print(f"🔗 Mapeos Sucursales (incluye nombres e IDs): {len(mapeos_sucursales_dict)} entradas")
        
        # Obtener registros normalizados existentes de una vez
        existing_normalized = {
            n.raw_id: n 
            for n in PlanificacionNormalizada.objects.filter(
                raw__in=to_process
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
            for raw in to_process:
                record_count += 1
                if record_count <= 5:  # Log primeros 5 registros
                    print(f"\n🔍 Registro #{record_count}:")
                    print(f"   ID: {raw.id}")
                    print(f"   Sucursal raw: '{raw.sucursal}'")
                    print(f"   CENDIS raw: '{raw.cendis}'")
                    print(f"   Item code: '{raw.item_code}'")
                
                issues = []

                # Normalizar SUCURSAL DESTINO (tienda)
                sucursal = None
                if raw.sucursal:
                    sucursal_key = raw.sucursal.strip().lower()
                    # 1. Buscar directamente (por nombre o BPL_ID)
                    sucursal = sucursales_map.get(sucursal_key)
                    # 2. Si no existe, buscar en mapeos (ahora incluye IDs)
                    if not sucursal:
                        sucursal = mapeos_sucursales_dict.get(sucursal_key)
                    
                    if record_count <= 5:
                        status = '✅ Encontrada' if sucursal else '❌ NO encontrada'
                        print(f"   🏢 Buscando sucursal (tienda): '{sucursal_key}' -> {status}")
                    if not sucursal:
                        issues.append(f"Sucursal (tienda) destino no encontrada: {raw.sucursal}")
                else:
                    issues.append("Sin sucursal (tienda) destino")
                    if record_count <= 5:
                        print(f"   🏢 Sucursal (tienda): ❌ Sin valor")

                # Normalizar CEDIS ORIGEN (almacén/centro de distribución)
                cedis_origen = None
                if raw.cendis:
                    cendis_key = raw.cendis.strip().lower()
                    # 1. Buscar directamente (por nombre, ID o código)
                    cedis_origen = cendis_map.get(cendis_key)
                    # 2. Si no existe, buscar en mapeos (ahora incluye IDs)
                    if not cedis_origen:
                        cedis_origen = mapeos_cedis_dict.get(cendis_key)
                    
                    if record_count <= 5:
                        status = '✅ Encontrado' if cedis_origen else '❌ NO encontrado'
                        print(f"   🏭 Buscando CEDIS (almacén): '{cendis_key}' -> {status}")
                    if not cedis_origen:
                        issues.append(f"CEDIS (almacén) origen no encontrado: {raw.cendis}")
                else:
                    if record_count <= 5:
                        print(f"   🏭 CEDIS (almacén): ⚠️ Sin valor (opcional)")

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

                # Verificar si ya existe normalizado para este raw
                existing = existing_normalized.get(raw.id)
                
                if existing:
                    # Actualizar existente
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
                    # Crear nuevo
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
            
            # Bulk operations - CRÍTICO: Asegurar que se ejecuten
            print(f"\n💾 Ejecutando operaciones bulk...")
            
            if to_create:
                print(f"   ➕ Creando {len(to_create)} registros normalizados...")
                PlanificacionNormalizada.objects.bulk_create(to_create, batch_size=500)
                print(f"   ✅ Creados")
            
            if to_update:
                print(f"   ♻️ Actualizando {len(to_update)} registros normalizados...")
                PlanificacionNormalizada.objects.bulk_update(
                    to_update,
                    ['tipo_carga', 'item_name', 'product', 'cendis', 'cedis_origen',
                     'a_despachar_total', 'plan_month', 'item_code', 'sucursal'],
                    batch_size=500
                )
                print(f"   ✅ Actualizados")
            
            if to_update_raw:
                print(f"   📝 Actualizando {len(to_update_raw)} registros raw...")
                Planificacion.objects.bulk_update(
                    to_update_raw,
                    ['normalize_status', 'normalize_notes', 'normalized_at'],
                    batch_size=500
                )
                print(f"   ✅ Actualizados")
        
        print(f"\n✅ NORMALIZACIÓN COMPLETADA")
        print(f"   📊 Procesados: {to_process.count()}")
        print(f"   ➕ Creados: {created}")
        print(f"   ♻️ Actualizados: {updated}")
        print(f"   ❌ Errores: {errors_count}")

        summary = self._summary(selected_month)
        errors = (
            Planificacion.objects.filter(normalize_status="error")
            .filter(plan_month=selected_month)
            .order_by("-created_at")[:50]
            if selected_month
            else []
        )
        pending = (
            Planificacion.objects.filter(normalize_status="pending")
            .filter(plan_month=selected_month)
            .order_by("-created_at")[:50]
            if selected_month
            else []
        )

        run_result = {
            "processed": to_process.count(),
            "created": created,
            "updated": updated,
            "errors": errors_count,
        }

        context = {
            "summary": summary,
            "errors": errors,
            "pending": pending,
            "ran": True,
            "run_result": run_result,
            "months": months,
            "selected_month": selected_month,
        }
        
        # Agregar mensaje de reset si existe
        if reset_message:
            context["message"] = reset_message

        return render(
            request,
            self.template_name,
            context,
        )

    @staticmethod
    def _summary(selected_month):
        base = Planificacion.objects.all()
        if selected_month:
            base = base.filter(plan_month=selected_month)
        return {
            "pending": base.filter(normalize_status="pending").count(),
            "ok": base.filter(normalize_status="ok").count(),
            "error": base.filter(normalize_status="error").count(),
            "total": base.count(),
        }

    @staticmethod
    def _months():
        return list(Planificacion.objects.dates("plan_month", "day", order="DESC"))

    def _selected_month(self, request):
        month_raw = request.POST.get("plan_month") or request.GET.get("plan_month")
        if month_raw:
            try:
                return datetime.date.fromisoformat(month_raw)
            except ValueError:
                return None
        months = self._months()
        return months[0] if months else None

    @staticmethod
    def _sync_from_legacy():
        """
        Sincroniza registros de PlanningEntry (legacy) hacia Planificacion.
        Solo se ejecuta si hay registros legacy sin sincronizar.
        """
        # Verificar si hay trabajo por hacer
        legacy_count = PlanningEntry.objects.count()
        if legacy_count == 0:
            return
        
        # Verificar si ya se sincronizó (heurística: si hay planificaciones, probablemente ya se hizo)
        existing_count = Planificacion.objects.count()
        if existing_count >= legacy_count * 0.8:  # Si ya hay 80% o más, skip
            return
        
        # Sincronizar
        legacy = (
            PlanningEntry.objects.select_related("batch")
            .values("batch__plan_date", "item_code", "item_name", "sucursal", "tipo_carga", "cendis", "a_despachar_total")
        )
        
        to_create = []
        for row in legacy:
            plan_date = row.get("batch__plan_date")
            if not plan_date:
                continue
            
            exists = Planificacion.objects.filter(
                plan_month=plan_date,
                item_code=row.get("item_code") or "",
                sucursal=row.get("sucursal") or "",
            ).exists()
            
            if exists:
                continue
            
            to_create.append(
                Planificacion(
                    plan_month=plan_date,
                    tipo_carga=row.get("tipo_carga") or "",
                    item_code=row.get("item_code") or "",
                    item_name=row.get("item_name") or "",
                    sucursal=row.get("sucursal") or "",
                    cendis=row.get("cendis") or "",
                    a_despachar_total=row.get("a_despachar_total"),
                    normalize_status="pending",
                )
            )
        
        if to_create:
            Planificacion.objects.bulk_create(to_create, ignore_conflicts=True)
