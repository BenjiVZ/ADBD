import datetime
from collections import defaultdict
from decimal import Decimal

from django.shortcuts import render
from django.views import View
from django.http import HttpResponse
import csv

from ..models import PlanificacionNormalizada, SalidaNormalizada, Pvp, GerenteRegional


class TableroNormalizadoView(View):
    template_name = "tablero_normalizado.html"

    def get(self, request, *args, **kwargs):
        # Obtener fechas seleccionadas
        plan_date = self._selected_plan_date(request)
        salida_date = self._selected_salida_date(request)
        active_tab = request.GET.get("tab", "cumplimiento")
        
        # Obtener filtro de gerente
        gerente_id = request.GET.get("gerente")
        selected_gerente = None
        if gerente_id:
            try:
                selected_gerente = GerenteRegional.objects.get(id=gerente_id)
            except GerenteRegional.DoesNotExist:
                pass
        
        # Obtener fechas disponibles para los selectores
        plan_dates = self._available_plan_dates()
        salida_dates = self._available_salida_dates()
        
        # Si no hay fechas seleccionadas, usar las más recientes
        if not plan_date and plan_dates:
            plan_date = plan_dates[0]
        if not salida_date and salida_dates:
            salida_date = salida_dates[0]
        
        # Pre-cargar precios PVP
        pvp_map = {p.sku.lower(): p.price for p in Pvp.objects.all()}
        
        # Generar datos para cada pestaña
        resumen_cumplimiento = self._build_resumen_cumplimiento(plan_date, salida_date, pvp_map)
        resumen_cedis = self._build_resumen_cedis(plan_date, salida_date, pvp_map)
        resumen_tiendas = self._build_resumen_tiendas(plan_date, salida_date, pvp_map, selected_gerente)
        
        # Lista de gerentes para el filtro
        gerentes = GerenteRegional.objects.all().order_by("name")
        
        # Totales nacionales con conteo de registros
        nacional = self._calculate_nacional(resumen_tiendas, plan_date, salida_date)
        
        # Export CSV
        export = request.GET.get("export")
        if export == "cumplimiento":
            return self._export_cumplimiento_csv(resumen_cumplimiento, plan_date, salida_date)
        elif export == "cedis":
            return self._export_cedis_csv(resumen_cedis, plan_date, salida_date)
        elif export == "tiendas":
            return self._export_tiendas_csv(resumen_tiendas, plan_date, salida_date)

        return render(
            request,
            self.template_name,
            {
                "plan_date": plan_date,
                "salida_date": salida_date,
                "plan_dates": plan_dates,
                "salida_dates": salida_dates,
                "active_tab": active_tab,
                "resumen_cumplimiento": resumen_cumplimiento,
                "resumen_cedis": resumen_cedis,
                "resumen_tiendas": resumen_tiendas,
                "nacional": nacional,
                "gerentes": gerentes,
                "selected_gerente": selected_gerente,
            },
        )

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def _selected_plan_date(self, request):
        raw_date = request.GET.get("plan_date") or request.POST.get("plan_date")
        if raw_date:
            try:
                return datetime.datetime.strptime(raw_date, "%Y-%m-%d").date()
            except ValueError:
                return None
        return None

    def _selected_salida_date(self, request):
        raw_date = request.GET.get("salida_date") or request.POST.get("salida_date")
        if raw_date:
            try:
                return datetime.datetime.strptime(raw_date, "%Y-%m-%d").date()
            except ValueError:
                return None
        return None
    
    def _available_plan_dates(self):
        return list(
            PlanificacionNormalizada.objects
            .values_list("plan_month", flat=True)
            .distinct()
            .order_by("-plan_month")
        )
    
    def _available_salida_dates(self):
        return list(
            SalidaNormalizada.objects
            .values_list("fecha_salida", flat=True)
            .distinct()
            .order_by("-fecha_salida")
        )

    def _get_price(self, item_code, pvp_map):
        """Obtener precio de un producto"""
        if not item_code:
            return Decimal("0")
        return pvp_map.get(item_code.lower(), Decimal("0"))

    def _build_resumen_cumplimiento(self, plan_date, salida_date, pvp_map):
        """
        Construye resumen jerárquico: CEDIS → Tipo Carga → Categoría → Productos
        """
        if not plan_date:
            return []
        
        # Obtener planificaciones
        plan_qs = (
            PlanificacionNormalizada.objects
            .filter(plan_month=plan_date)
            .select_related("cedis_origen", "product")
        )
        
        # Obtener salidas
        salida_qs = (
            SalidaNormalizada.objects
            .filter(fecha_salida=salida_date)
            .select_related("cedis_origen", "product")
        ) if salida_date else SalidaNormalizada.objects.none()
        
        # Agrupar planificaciones: cedis -> tipo_carga -> grupo -> categoria -> producto_code -> {qty, info}
        # NOTA: Excluimos registros vacíos y "SIN TIPO" del análisis
        plan_data = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(dict))))
        for p in plan_qs:
            tipo_raw = p.tipo_carga.strip() if p.tipo_carga else ""
            # Excluir registros vacíos o con "SIN TIPO"
            if not tipo_raw or tipo_raw.upper() == "SIN TIPO":
                continue
            # Normalizar: quitar prefijos numéricos "1. ", "2. ", etc.
            tipo = tipo_raw.split('. ', 1)[-1] if '. ' in tipo_raw else tipo_raw
            cedis_name = p.cedis_origen.origin if p.cedis_origen else "SIN CEDIS"
            grupo = p.product.group.strip() if p.product and p.product.group else "SIN GRUPO"
            categoria = p.product.category.strip() if p.product and p.product.category else "SIN CATEGORÍA"
            producto_code = p.item_code if p.item_code else "SIN CÓDIGO"
            qty = Decimal(p.a_despachar_total or 0)
            
            # Inicializar o actualizar
            if producto_code not in plan_data[cedis_name][tipo][grupo][categoria]:
                plan_data[cedis_name][tipo][grupo][categoria][producto_code] = {
                    'qty': Decimal('0'),
                    'code': p.item_code or "",
                    'name': p.item_name or "",
                    'group': p.product.group if p.product else "",
                    'manufacturer': p.product.manufacturer if p.product else "",
                    'category': p.product.category if p.product else "",
                    'subcategory': p.product.subcategory if p.product else "",
                    'size': p.product.size if p.product else "",
                }
            plan_data[cedis_name][tipo][grupo][categoria][producto_code]['qty'] += qty
        
        # Mapear salidas a planificaciones para obtener tipo_carga
        # Solo incluir registros con tipo válido (no vacíos ni "SIN TIPO")
        plan_lookup = {}
        for p in plan_qs:
            tipo_raw = p.tipo_carga.strip() if p.tipo_carga else ""
            # Solo guardar si tiene contenido y no es "SIN TIPO"
            if not tipo_raw or tipo_raw.upper() == "SIN TIPO":
                continue
            # Normalizar
            tipo = tipo_raw.split('. ', 1)[-1] if '. ' in tipo_raw else tipo_raw
            key = (
                p.cedis_origen.id if p.cedis_origen else None,
                p.item_code.lower() if p.item_code else "",
                p.sucursal_id
            )
            plan_lookup[key] = tipo
        
        # Agrupar salidas: cedis -> tipo_carga -> grupo -> categoria -> producto_code -> {qty, info}
        salida_data = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(dict))))
        for s in salida_qs:
            cedis_name = s.cedis_origen.origin if s.cedis_origen else "SIN CEDIS"
            grupo = s.product.group.strip() if s.product and s.product.group else "SIN GRUPO"
            categoria = s.product.category.strip() if s.product and s.product.category else "SIN CATEGORÍA"
            producto_code = s.sku if s.sku else "SIN CÓDIGO"
            qty = Decimal(s.cantidad or 0)
            
            # Buscar tipo_carga de la planificación correspondiente
            key = (
                s.cedis_origen_id,
                s.sku.lower() if s.sku else "",
                s.sucursal_destino_id
            )
            tipo = plan_lookup.get(key, "NO PLANIFICADO")
            
            # Inicializar o actualizar
            if producto_code not in salida_data[cedis_name][tipo][grupo][categoria]:
                salida_data[cedis_name][tipo][grupo][categoria][producto_code] = {
                    'qty': Decimal('0'),
                    'code': s.sku or "",
                    'name': s.descripcion or "",
                    'group': s.product.group if s.product else "",
                    'manufacturer': s.product.manufacturer if s.product else "",
                    'category': s.product.category if s.product else "",
                    'subcategory': s.product.subcategory if s.product else "",
                    'size': s.product.size if s.product else "",
                }
            salida_data[cedis_name][tipo][grupo][categoria][producto_code]['qty'] += qty
        
        # Construir estructura de resultado
        result = []
        all_cedis = sorted(set(plan_data.keys()) | set(salida_data.keys()))
        
        for cedis_name in all_cedis:
            cedis_plan = plan_data.get(cedis_name, {})
            cedis_salida = salida_data.get(cedis_name, {})
            
            # Ordenar tipos en orden específico: PRIORIDAD, LANZAMIENTO, NO PLANIFICADO
            tipo_order = {"PRIORIDAD": 0, "LANZAMIENTO": 1, "NO PLANIFICADO": 2}
            all_tipos = sorted(set(cedis_plan.keys()) | set(cedis_salida.keys()), 
                             key=lambda x: tipo_order.get(x.upper(), 99))
            
            tipos_list = []
            cedis_total_plan = Decimal("0")
            cedis_total_salida = Decimal("0")
            
            for tipo in all_tipos:
                tipo_plan = cedis_plan.get(tipo, {})
                tipo_salida = cedis_salida.get(tipo, {})
                
                all_grupos = sorted(set(tipo_plan.keys()) | set(tipo_salida.keys()))
                
                grupos_list = []
                tipo_total_plan = Decimal("0")
                tipo_total_salida = Decimal("0")
                
                for grupo in all_grupos:
                    grupo_plan = tipo_plan.get(grupo, {})
                    grupo_salida = tipo_salida.get(grupo, {})
                    
                    all_categorias = sorted(set(grupo_plan.keys()) | set(grupo_salida.keys()))
                    
                    categorias_list = []
                    grupo_total_plan = Decimal("0")
                    grupo_total_salida = Decimal("0")
                    
                    for categoria in all_categorias:
                        categoria_plan = grupo_plan.get(categoria, {})
                        categoria_salida = grupo_salida.get(categoria, {})
                        
                        all_productos = sorted(set(categoria_plan.keys()) | set(categoria_salida.keys()))
                        
                        productos_list = []
                        categoria_total_plan = Decimal("0")
                        categoria_total_salida = Decimal("0")
                        
                        for producto_code in all_productos:
                            plan_info = categoria_plan.get(producto_code, {})
                            salida_info = categoria_salida.get(producto_code, {})
                            
                            plan_qty = plan_info.get('qty', Decimal("0")) if plan_info else Decimal("0")
                            salida_qty = salida_info.get('qty', Decimal("0")) if salida_info else Decimal("0")
                            
                            # Tomar info del producto de planificación, si no existe de salida
                            info = plan_info if plan_info else salida_info
                            
                            percent = self._calc_percent(salida_qty, plan_qty)
                            
                            productos_list.append({
                                "code": info.get('code', ''),
                                "name": info.get('name', ''),
                                "group": info.get('group', ''),
                                "manufacturer": info.get('manufacturer', ''),
                                "category": info.get('category', ''),
                                "subcategory": info.get('subcategory', ''),
                                "size": info.get('size', ''),
                                "plan": plan_qty,
                                "salida": salida_qty,
                                "percent": percent,
                            })
                            
                            categoria_total_plan += plan_qty
                            categoria_total_salida += salida_qty
                        
                        # Ordenar productos de mayor a menor por porcentaje de cumplimiento
                        productos_list.sort(key=lambda x: x["percent"], reverse=True)
                        
                        categoria_percent = self._calc_percent(categoria_total_salida, categoria_total_plan)
                        
                        categorias_list.append({
                            "name": categoria,
                            "plan": categoria_total_plan,
                            "salida": categoria_total_salida,
                            "percent": categoria_percent,
                            "productos": productos_list,
                        })
                        
                        grupo_total_plan += categoria_total_plan
                        grupo_total_salida += categoria_total_salida
                    
                    # Ordenar categorías de mayor a menor por porcentaje de cumplimiento
                    categorias_list.sort(key=lambda x: x["percent"], reverse=True)
                    
                    grupo_percent = self._calc_percent(grupo_total_salida, grupo_total_plan)
                    
                    grupos_list.append({
                        "name": grupo,
                        "plan": grupo_total_plan,
                        "salida": grupo_total_salida,
                        "percent": grupo_percent,
                        "categorias": categorias_list,
                    })
                    
                    tipo_total_plan += grupo_total_plan
                    tipo_total_salida += grupo_total_salida
                
                
                # Ordenar grupos de mayor a menor por porcentaje de cumplimiento
                grupos_list.sort(key=lambda x: x["percent"], reverse=True)
                
                tipo_percent = self._calc_percent(tipo_total_salida, tipo_total_plan)
                
                tipos_list.append({
                    "name": tipo,
                    "plan": tipo_total_plan,
                    "salida": tipo_total_salida,
                    "percent": tipo_percent,
                    "grupos": grupos_list,
                })
                
                cedis_total_plan += tipo_total_plan
                cedis_total_salida += tipo_total_salida
            
            # Ordenar tipos en orden específico: PRIORIDAD, LANZAMIENTO, NO PLANIFICADO
            tipo_order = {"PRIORIDAD": 0, "LANZAMIENTO": 1, "NO PLANIFICADO": 2}
            tipos_list.sort(key=lambda x: tipo_order.get(x["name"].upper(), 99))
            
            cedis_percent = self._calc_percent(cedis_total_salida, cedis_total_plan)
            
            result.append({
                "name": cedis_name,
                "plan": cedis_total_plan,
                "salida": cedis_total_salida,
                "percent": cedis_percent,
                "tipos": tipos_list,
            })
        
        # Ordenar CEDIS de mayor a menor por porcentaje de cumplimiento
        result.sort(key=lambda x: x["percent"], reverse=True)
        
        return result

    def _build_resumen_cedis(self, plan_date, salida_date, pvp_map):
        """
        Construye resumen por CEDIS con unidades y USD
        """
        if not plan_date:
            return []
        
        # Obtener planificaciones
        plan_qs = (
            PlanificacionNormalizada.objects
            .filter(plan_month=plan_date)
            .select_related("cedis_origen", "product")
        )
        
        # Obtener salidas
        salida_qs = (
            SalidaNormalizada.objects
            .filter(fecha_salida=salida_date)
            .select_related("cedis_origen", "product")
        ) if salida_date else SalidaNormalizada.objects.none()
        
        # Crear lookup de planificaciones por (cedis, sku, sucursal)
        plan_lookup = set()
        for p in plan_qs:
            key = (
                p.cedis_origen_id,
                p.item_code.lower() if p.item_code else "",
                p.sucursal_id
            )
            plan_lookup.add(key)
        
        # Agrupar planificaciones por CEDIS
        plan_by_cedis = defaultdict(lambda: {"qty": Decimal("0"), "usd": Decimal("0")})
        for p in plan_qs:
            cedis_name = p.cedis_origen.origin if p.cedis_origen else "SIN CEDIS"
            qty = Decimal(p.a_despachar_total or 0)
            price = self._get_price(p.item_code, pvp_map)
            plan_by_cedis[cedis_name]["qty"] += qty
            plan_by_cedis[cedis_name]["usd"] += qty * price
        
        # Agrupar salidas por CEDIS (separando planificadas vs no planificadas)
        salida_plan_by_cedis = defaultdict(lambda: {"qty": Decimal("0"), "usd": Decimal("0")})
        salida_noplan_by_cedis = defaultdict(lambda: {"qty": Decimal("0"), "usd": Decimal("0")})
        
        for s in salida_qs:
            cedis_name = s.cedis_origen.origin if s.cedis_origen else "SIN CEDIS"
            qty = Decimal(s.cantidad or 0)
            price = self._get_price(s.sku, pvp_map)
            
            # Verificar si estaba planificada
            key = (
                s.cedis_origen_id,
                s.sku.lower() if s.sku else "",
                s.sucursal_destino_id
            )
            
            if key in plan_lookup:
                salida_plan_by_cedis[cedis_name]["qty"] += qty
                salida_plan_by_cedis[cedis_name]["usd"] += qty * price
            else:
                salida_noplan_by_cedis[cedis_name]["qty"] += qty
                salida_noplan_by_cedis[cedis_name]["usd"] += qty * price
        
        # Construir resultado
        result = []
        all_cedis = sorted(set(plan_by_cedis.keys()) | set(salida_plan_by_cedis.keys()) | set(salida_noplan_by_cedis.keys()))
        
        for cedis_name in all_cedis:
            plan = plan_by_cedis.get(cedis_name, {"qty": Decimal("0"), "usd": Decimal("0")})
            salida_plan = salida_plan_by_cedis.get(cedis_name, {"qty": Decimal("0"), "usd": Decimal("0")})
            salida_noplan = salida_noplan_by_cedis.get(cedis_name, {"qty": Decimal("0"), "usd": Decimal("0")})
            
            total_salida_qty = salida_plan["qty"] + salida_noplan["qty"]
            total_salida_usd = salida_plan["usd"] + salida_noplan["usd"]
            
            result.append({
                "name": cedis_name,
                "plan_qty": plan["qty"],
                "plan_usd": plan["usd"],
                "salida_plan_qty": salida_plan["qty"],
                "salida_plan_usd": salida_plan["usd"],
                "percent_qty": self._calc_percent(salida_plan["qty"], plan["qty"]),
                "percent_usd": self._calc_percent(salida_plan["usd"], plan["usd"]),
                "salida_noplan_qty": salida_noplan["qty"],
                "salida_noplan_usd": salida_noplan["usd"],
                "total_salida_qty": total_salida_qty,
                "total_salida_usd": total_salida_usd,
            })
        
        # Ordenar CEDIS de mayor a menor por porcentaje de cumplimiento
        result.sort(key=lambda x: x["percent_qty"], reverse=True)
        
        return result

    def _build_resumen_tiendas(self, plan_date, salida_date, pvp_map, gerente_filter=None):
        """
        Construye resumen por Tienda con jerarquía: Tienda → Tipo Carga → Grupo → Categoría → Producto
        Mantiene los totales correctos incluyendo TODAS las planificaciones y separando salidas planificadas vs no planificadas
        Si gerente_filter está definido, solo muestra tiendas de ese gerente.
        """
        if not plan_date:
            return []
        
        # Obtener planificaciones
        plan_qs = (
            PlanificacionNormalizada.objects
            .filter(plan_month=plan_date)
            .select_related("sucursal", "sucursal__gerente", "product")
        )
        
        # Filtrar por gerente si está definido
        if gerente_filter:
            plan_qs = plan_qs.filter(sucursal__gerente=gerente_filter)
        
        # Obtener salidas
        salida_qs = (
            SalidaNormalizada.objects
            .filter(fecha_salida=salida_date)
            .select_related("sucursal_destino", "sucursal_destino__gerente", "product")
        ) if salida_date else SalidaNormalizada.objects.none()
        
        # Filtrar salidas por gerente si está definido
        if gerente_filter and salida_date:
            salida_qs = salida_qs.filter(sucursal_destino__gerente=gerente_filter)
        
        # Crear lookup de planificaciones por (sucursal, sku) - incluye TODOS los registros
        plan_lookup_set = set()
        for p in plan_qs:
            key = (p.sucursal_id, p.item_code.lower() if p.item_code else "")
            plan_lookup_set.add(key)
        
        # Totales por tienda - incluye TODAS las planificaciones
        tienda_totals = defaultdict(lambda: {
            "plan_qty": Decimal("0"),
            "plan_usd": Decimal("0"),
            "salida_plan_qty": Decimal("0"),
            "salida_plan_usd": Decimal("0"),
            "salida_noplan_qty": Decimal("0"),
            "salida_noplan_usd": Decimal("0"),
        })
        
        # Sumar TODAS las planificaciones (incluyendo SIN TIPO)
        for p in plan_qs:
            tienda_name = p.sucursal.name if p.sucursal else "SIN TIENDA"
            qty = Decimal(p.a_despachar_total or 0)
            price = self._get_price(p.item_code, pvp_map)
            tienda_totals[tienda_name]["plan_qty"] += qty
            tienda_totals[tienda_name]["plan_usd"] += qty * price
        
        # Sumar salidas y clasificarlas como planificadas o no planificadas
        for s in salida_qs:
            tienda_name = s.sucursal_destino.name if s.sucursal_destino else "SIN TIENDA"
            qty = Decimal(s.cantidad or 0)
            price = self._get_price(s.sku, pvp_map)
            
            key = (s.sucursal_destino_id, s.sku.lower() if s.sku else "")
            if key in plan_lookup_set:
                tienda_totals[tienda_name]["salida_plan_qty"] += qty
                tienda_totals[tienda_name]["salida_plan_usd"] += qty * price
            else:
                tienda_totals[tienda_name]["salida_noplan_qty"] += qty
                tienda_totals[tienda_name]["salida_noplan_usd"] += qty * price
        
        # Agrupar planificaciones para jerarquía: tienda -> tipo_carga -> grupo -> categoria -> producto_code
        # Excluimos SIN TIPO solo de la JERARQUÍA visual, no de los totales
        plan_data = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(dict))))
        plan_lookup_tipo = {}
        
        for p in plan_qs:
            tipo_raw = p.tipo_carga.strip() if p.tipo_carga else ""
            # Para la jerarquía visual, excluir SIN TIPO
            if not tipo_raw or tipo_raw.upper() == "SIN TIPO":
                continue
            tipo = tipo_raw.split('. ', 1)[-1] if '. ' in tipo_raw else tipo_raw
            tienda_name = p.sucursal.name if p.sucursal else "SIN TIENDA"
            grupo = p.product.group.strip() if p.product and p.product.group else "SIN GRUPO"
            categoria = p.product.category.strip() if p.product and p.product.category else "SIN CATEGORÍA"
            producto_code = p.item_code if p.item_code else "SIN CÓDIGO"
            qty = Decimal(p.a_despachar_total or 0)
            price = self._get_price(p.item_code, pvp_map)
            
            # Guardar tipo para el lookup de salidas
            key = (p.sucursal_id, p.item_code.lower() if p.item_code else "")
            plan_lookup_tipo[key] = tipo
            
            if producto_code not in plan_data[tienda_name][tipo][grupo][categoria]:
                plan_data[tienda_name][tipo][grupo][categoria][producto_code] = {
                    'qty': Decimal('0'),
                    'usd': Decimal('0'),
                    'code': p.item_code or "",
                    'name': p.item_name or "",
                    'group': p.product.group if p.product else "",
                    'manufacturer': p.product.manufacturer if p.product else "",
                    'category': p.product.category if p.product else "",
                    'subcategory': p.product.subcategory if p.product else "",
                    'size': p.product.size if p.product else "",
                }
            plan_data[tienda_name][tipo][grupo][categoria][producto_code]['qty'] += qty
            plan_data[tienda_name][tipo][grupo][categoria][producto_code]['usd'] += qty * price
        
        # Agrupar salidas para jerarquía
        salida_data = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(dict))))
        for s in salida_qs:
            tienda_name = s.sucursal_destino.name if s.sucursal_destino else "SIN TIENDA"
            grupo = s.product.group.strip() if s.product and s.product.group else "SIN GRUPO"
            categoria = s.product.category.strip() if s.product and s.product.category else "SIN CATEGORÍA"
            producto_code = s.sku if s.sku else "SIN CÓDIGO"
            qty = Decimal(s.cantidad or 0)
            price = self._get_price(s.sku, pvp_map)
            
            key = (s.sucursal_destino_id, s.sku.lower() if s.sku else "")
            tipo = plan_lookup_tipo.get(key, "NO PLANIFICADO")
            
            if producto_code not in salida_data[tienda_name][tipo][grupo][categoria]:
                salida_data[tienda_name][tipo][grupo][categoria][producto_code] = {
                    'qty': Decimal('0'),
                    'usd': Decimal('0'),
                    'code': s.sku or "",
                    'name': s.descripcion or "",
                    'group': s.product.group if s.product else "",
                    'manufacturer': s.product.manufacturer if s.product else "",
                    'category': s.product.category if s.product else "",
                    'subcategory': s.product.subcategory if s.product else "",
                    'size': s.product.size if s.product else "",
                }
            salida_data[tienda_name][tipo][grupo][categoria][producto_code]['qty'] += qty
            salida_data[tienda_name][tipo][grupo][categoria][producto_code]['usd'] += qty * price
        
        # Construir estructura de resultado
        result = []
        all_tiendas = sorted(set(tienda_totals.keys()) | set(plan_data.keys()) | set(salida_data.keys()))
        
        for tienda_name in all_tiendas:
            tienda_plan = plan_data.get(tienda_name, {})
            tienda_salida = salida_data.get(tienda_name, {})
            totals = tienda_totals.get(tienda_name, {
                "plan_qty": Decimal("0"), "plan_usd": Decimal("0"),
                "salida_plan_qty": Decimal("0"), "salida_plan_usd": Decimal("0"),
                "salida_noplan_qty": Decimal("0"), "salida_noplan_usd": Decimal("0"),
            })
            
            tipo_order = {"PRIORIDAD": 0, "LANZAMIENTO": 1, "NO PLANIFICADO": 2}
            all_tipos = sorted(set(tienda_plan.keys()) | set(tienda_salida.keys()), 
                             key=lambda x: tipo_order.get(x.upper(), 99))
            
            tipos_list = []
            
            for tipo in all_tipos:
                tipo_plan = tienda_plan.get(tipo, {})
                tipo_salida = tienda_salida.get(tipo, {})
                
                all_grupos = sorted(set(tipo_plan.keys()) | set(tipo_salida.keys()))
                
                grupos_list = []
                tipo_total_plan_qty = Decimal("0")
                tipo_total_plan_usd = Decimal("0")
                tipo_total_salida_qty = Decimal("0")
                tipo_total_salida_usd = Decimal("0")
                
                for grupo in all_grupos:
                    grupo_plan = tipo_plan.get(grupo, {})
                    grupo_salida = tipo_salida.get(grupo, {})
                    
                    all_categorias = sorted(set(grupo_plan.keys()) | set(grupo_salida.keys()))
                    
                    categorias_list = []
                    grupo_total_plan_qty = Decimal("0")
                    grupo_total_plan_usd = Decimal("0")
                    grupo_total_salida_qty = Decimal("0")
                    grupo_total_salida_usd = Decimal("0")
                    
                    for categoria in all_categorias:
                        categoria_plan = grupo_plan.get(categoria, {})
                        categoria_salida = grupo_salida.get(categoria, {})
                        
                        all_productos = sorted(set(categoria_plan.keys()) | set(categoria_salida.keys()))
                        
                        productos_list = []
                        categoria_total_plan_qty = Decimal("0")
                        categoria_total_plan_usd = Decimal("0")
                        categoria_total_salida_qty = Decimal("0")
                        categoria_total_salida_usd = Decimal("0")
                        
                        for producto_code in all_productos:
                            plan_info = categoria_plan.get(producto_code, {})
                            salida_info = categoria_salida.get(producto_code, {})
                            
                            plan_qty = plan_info.get('qty', Decimal("0")) if plan_info else Decimal("0")
                            plan_usd = plan_info.get('usd', Decimal("0")) if plan_info else Decimal("0")
                            salida_qty = salida_info.get('qty', Decimal("0")) if salida_info else Decimal("0")
                            salida_usd = salida_info.get('usd', Decimal("0")) if salida_info else Decimal("0")
                            
                            info = plan_info if plan_info else salida_info
                            
                            percent_qty = self._calc_percent(salida_qty, plan_qty)
                            percent_usd = self._calc_percent(salida_usd, plan_usd)
                            
                            productos_list.append({
                                "code": info.get('code', ''),
                                "name": info.get('name', ''),
                                "group": info.get('group', ''),
                                "manufacturer": info.get('manufacturer', ''),
                                "category": info.get('category', ''),
                                "subcategory": info.get('subcategory', ''),
                                "size": info.get('size', ''),
                                "plan_qty": plan_qty,
                                "plan_usd": plan_usd,
                                "salida_plan_qty": salida_qty,
                                "salida_plan_usd": salida_usd,
                                "percent_qty": percent_qty,
                                "percent_usd": percent_usd,
                            })
                            
                            categoria_total_plan_qty += plan_qty
                            categoria_total_plan_usd += plan_usd
                            categoria_total_salida_qty += salida_qty
                            categoria_total_salida_usd += salida_usd
                        
                        productos_list.sort(key=lambda x: x["percent_qty"], reverse=True)
                        
                        categorias_list.append({
                            "name": categoria,
                            "plan_qty": categoria_total_plan_qty,
                            "plan_usd": categoria_total_plan_usd,
                            "salida_plan_qty": categoria_total_salida_qty,
                            "salida_plan_usd": categoria_total_salida_usd,
                            "percent_qty": self._calc_percent(categoria_total_salida_qty, categoria_total_plan_qty),
                            "percent_usd": self._calc_percent(categoria_total_salida_usd, categoria_total_plan_usd),
                            "productos": productos_list,
                        })
                        
                        grupo_total_plan_qty += categoria_total_plan_qty
                        grupo_total_plan_usd += categoria_total_plan_usd
                        grupo_total_salida_qty += categoria_total_salida_qty
                        grupo_total_salida_usd += categoria_total_salida_usd
                    
                    categorias_list.sort(key=lambda x: x["percent_qty"], reverse=True)
                    
                    grupos_list.append({
                        "name": grupo,
                        "plan_qty": grupo_total_plan_qty,
                        "plan_usd": grupo_total_plan_usd,
                        "salida_plan_qty": grupo_total_salida_qty,
                        "salida_plan_usd": grupo_total_salida_usd,
                        "percent_qty": self._calc_percent(grupo_total_salida_qty, grupo_total_plan_qty),
                        "percent_usd": self._calc_percent(grupo_total_salida_usd, grupo_total_plan_usd),
                        "categorias": categorias_list,
                    })
                    
                    tipo_total_plan_qty += grupo_total_plan_qty
                    tipo_total_plan_usd += grupo_total_plan_usd
                    tipo_total_salida_qty += grupo_total_salida_qty
                    tipo_total_salida_usd += grupo_total_salida_usd
                
                grupos_list.sort(key=lambda x: x["percent_qty"], reverse=True)
                
                tipos_list.append({
                    "name": tipo,
                    "plan_qty": tipo_total_plan_qty,
                    "plan_usd": tipo_total_plan_usd,
                    "salida_plan_qty": tipo_total_salida_qty,
                    "salida_plan_usd": tipo_total_salida_usd,
                    "percent_qty": self._calc_percent(tipo_total_salida_qty, tipo_total_plan_qty),
                    "percent_usd": self._calc_percent(tipo_total_salida_usd, tipo_total_plan_usd),
                    "grupos": grupos_list,
                })
            
            tipo_order = {"PRIORIDAD": 0, "LANZAMIENTO": 1, "NO PLANIFICADO": 2}
            tipos_list.sort(key=lambda x: tipo_order.get(x["name"].upper(), 99))
            
            # Usar totales REALES (incluyendo SIN TIPO) para la tienda
            total_salida_qty = totals["salida_plan_qty"] + totals["salida_noplan_qty"]
            total_salida_usd = totals["salida_plan_usd"] + totals["salida_noplan_usd"]
            
            result.append({
                "name": tienda_name,
                "plan_qty": totals["plan_qty"],
                "plan_usd": totals["plan_usd"],
                "salida_plan_qty": totals["salida_plan_qty"],
                "salida_plan_usd": totals["salida_plan_usd"],
                "salida_noplan_qty": totals["salida_noplan_qty"],
                "salida_noplan_usd": totals["salida_noplan_usd"],
                "total_salida_qty": total_salida_qty,
                "total_salida_usd": total_salida_usd,
                "percent_qty": self._calc_percent(totals["salida_plan_qty"], totals["plan_qty"]),
                "percent_usd": self._calc_percent(totals["salida_plan_usd"], totals["plan_usd"]),
                "tipos": tipos_list,
            })
        
        result.sort(key=lambda x: x["percent_qty"], reverse=True)
        
        return result

    def _calculate_nacional(self, resumen_tiendas, plan_date, salida_date):
        """Calcula totales nacionales incluyendo conteo de registros y tiendas"""
        total = {
            "plan_qty": Decimal("0"),
            "plan_usd": Decimal("0"),
            "salida_plan_qty": Decimal("0"),
            "salida_plan_usd": Decimal("0"),
            "salida_noplan_qty": Decimal("0"),
            "salida_noplan_usd": Decimal("0"),
            "total_salida_qty": Decimal("0"),
            "total_salida_usd": Decimal("0"),
            "total_plan_registros": 0,
            "total_salida_registros": 0,
            "tiendas_planificadas": 0,
            "tiendas_despachadas": 0,
            "tiendas_noplan_despachadas": 0,
            "total_tiendas_despachadas": 0,
            "percent_tiendas": Decimal("0"),
        }
        
        for tienda in resumen_tiendas:
            total["plan_qty"] += tienda["plan_qty"]
            total["plan_usd"] += tienda["plan_usd"]
            total["salida_plan_qty"] += tienda["salida_plan_qty"]
            total["salida_plan_usd"] += tienda["salida_plan_usd"]
            total["salida_noplan_qty"] += tienda["salida_noplan_qty"]
            total["salida_noplan_usd"] += tienda["salida_noplan_usd"]
            total["total_salida_qty"] += tienda["total_salida_qty"]
            total["total_salida_usd"] += tienda["total_salida_usd"]
            
            # Contar tiendas con planificación y con despachos de planificadas
            if tienda["plan_qty"] > 0:
                total["tiendas_planificadas"] += 1
                # Solo contar como despachada si tenía plan Y recibió despachos planificados
                if tienda["salida_plan_qty"] > 0:
                    total["tiendas_despachadas"] += 1
            else:
                # Tienda NO planificada pero que recibió despachos
                if tienda["salida_noplan_qty"] > 0 or tienda["salida_plan_qty"] > 0:
                    total["tiendas_noplan_despachadas"] += 1
        
        # Total de tiendas despachadas = planificadas despachadas + no planificadas despachadas
        total["total_tiendas_despachadas"] = total["tiendas_despachadas"] + total["tiendas_noplan_despachadas"]
        
        total["percent_qty"] = self._calc_percent(total["salida_plan_qty"], total["plan_qty"])
        total["percent_usd"] = self._calc_percent(total["salida_plan_usd"], total["plan_usd"])
        total["percent_tiendas"] = self._calc_percent(Decimal(total["tiendas_despachadas"]), Decimal(total["tiendas_planificadas"]))
        
        # Contar registros totales de planificación y salida
        if plan_date:
            total["total_plan_registros"] = PlanificacionNormalizada.objects.filter(plan_month=plan_date).count()
        if salida_date:
            total["total_salida_registros"] = SalidaNormalizada.objects.filter(fecha_salida=salida_date).count()
        
        return total

    def _calc_percent(self, actual, planned):
        """Calcular porcentaje de cumplimiento"""
        if planned and planned > 0:
            return ((actual / planned) * Decimal("100")).quantize(Decimal("0.01"))
        return Decimal("0")

    def _export_cumplimiento_csv(self, data, plan_date, salida_date):
        response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
        response["Content-Disposition"] = f'attachment; filename="cumplimiento_{plan_date}_{salida_date}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(["CEDIS", "Tipo Carga", "Categoría", "Producto", "Planificado", "Despachado", "% Cumplimiento"])
        
        for cedis in data:
            for tipo in cedis["tipos"]:
                for categoria in tipo["categorias"]:
                    for producto in categoria["productos"]:
                        writer.writerow([
                            cedis["name"],
                            tipo["name"],
                            categoria["name"],
                            producto["name"],
                            str(producto["plan"]),
                            str(producto["salida"]),
                            f'{producto["percent"]}%'
                        ])
        
        return response

    def _export_cedis_csv(self, data, plan_date, salida_date):
        response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
        response["Content-Disposition"] = f'attachment; filename="resumen_cedis_{plan_date}_{salida_date}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            "CEDIS", "Unid. Plan.", "USD Plan.", "Unid. Plan. Despachadas", "USD Plan. Despachados",
            "% Unid. Plan.", "% USD Plan.", "Unid. NO Plan.", "USD NO Plan.",
            "Total Unid. Despachadas", "Total USD Despachados"
        ])
        
        for row in data:
            writer.writerow([
                row["name"],
                str(row["plan_qty"]),
                str(row["plan_usd"]),
                str(row["salida_plan_qty"]),
                str(row["salida_plan_usd"]),
                f'{row["percent_qty"]}%',
                f'{row["percent_usd"]}%',
                str(row["salida_noplan_qty"]),
                str(row["salida_noplan_usd"]),
                str(row["total_salida_qty"]),
                str(row["total_salida_usd"]),
            ])
        
        return response

    def _export_tiendas_csv(self, data, plan_date, salida_date):
        response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
        response["Content-Disposition"] = f'attachment; filename="resumen_tiendas_{plan_date}_{salida_date}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            "Tienda", "Unid. Plan.", "USD Plan.", "Unid. Plan. Despachadas", "USD Plan. Despachados",
            "% Unid. Plan.", "% USD Plan.", "Unid. NO Plan.", "USD NO Plan.",
            "Total Unid. Despachadas", "Total USD Despachados"
        ])
        
        for row in data:
            writer.writerow([
                row["name"],
                str(row["plan_qty"]),
                str(row["plan_usd"]),
                str(row["salida_plan_qty"]),
                str(row["salida_plan_usd"]),
                f'{row["percent_qty"]}%',
                f'{row["percent_usd"]}%',
                str(row["salida_noplan_qty"]),
                str(row["salida_noplan_usd"]),
                str(row["total_salida_qty"]),
                str(row["total_salida_usd"]),
            ])
        
        return response
