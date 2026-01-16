import datetime
from collections import defaultdict
from decimal import Decimal

from django.shortcuts import render
from django.views import View
from django.http import HttpResponse
import csv

from ..models import PlanificacionNormalizada, SalidaNormalizada, Pvp


class TableroNormalizadoView(View):
    template_name = "tablero_normalizado.html"

    def get(self, request, *args, **kwargs):
        # Obtener fechas seleccionadas
        plan_date = self._selected_plan_date(request)
        salida_date = self._selected_salida_date(request)
        active_tab = request.GET.get("tab", "cumplimiento")
        
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
        resumen_tiendas = self._build_resumen_tiendas(plan_date, salida_date, pvp_map)
        
        # Totales nacionales
        nacional = self._calculate_nacional(resumen_tiendas)
        
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
        
        # Agrupar planificaciones: cedis -> tipo_carga -> categoria -> producto -> qty
        plan_data = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(Decimal))))
        for p in plan_qs:
            cedis_name = p.cedis_origen.origin if p.cedis_origen else "SIN CEDIS"
            tipo = p.tipo_carga.strip() if p.tipo_carga else "SIN TIPO"
            categoria = p.product.category.strip() if p.product and p.product.category else "SIN CATEGORÍA"
            producto = f"{p.item_code} - {p.item_name}" if p.item_code and p.item_name else p.item_code or p.item_name or "SIN NOMBRE"
            qty = Decimal(p.a_despachar_total or 0)
            plan_data[cedis_name][tipo][categoria][producto] += qty
        
        # Mapear salidas a planificaciones para obtener tipo_carga
        plan_lookup = {}
        for p in plan_qs:
            key = (
                p.cedis_origen.id if p.cedis_origen else None,
                p.item_code.lower() if p.item_code else "",
                p.sucursal_id
            )
            plan_lookup[key] = p.tipo_carga.strip() if p.tipo_carga else "SIN TIPO"
        
        # Agrupar salidas: cedis -> tipo_carga -> categoria -> producto -> qty
        salida_data = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(Decimal))))
        for s in salida_qs:
            cedis_name = s.cedis_origen.origin if s.cedis_origen else "SIN CEDIS"
            categoria = s.product.category.strip() if s.product and s.product.category else "SIN CATEGORÍA"
            producto = f"{s.sku} - {s.descripcion}" if s.sku and s.descripcion else s.sku or s.descripcion or "SIN NOMBRE"
            qty = Decimal(s.cantidad or 0)
            
            # Buscar tipo_carga de la planificación correspondiente
            key = (
                s.cedis_origen_id,
                s.sku.lower() if s.sku else "",
                s.sucursal_destino_id
            )
            tipo = plan_lookup.get(key, "NO PLANIFICADO")
            
            salida_data[cedis_name][tipo][categoria][producto] += qty
        
        # Construir estructura de resultado
        result = []
        all_cedis = sorted(set(plan_data.keys()) | set(salida_data.keys()))
        
        for cedis_name in all_cedis:
            cedis_plan = plan_data.get(cedis_name, {})
            cedis_salida = salida_data.get(cedis_name, {})
            
            all_tipos = sorted(set(cedis_plan.keys()) | set(cedis_salida.keys()))
            
            tipos_list = []
            cedis_total_plan = Decimal("0")
            cedis_total_salida = Decimal("0")
            
            for tipo in all_tipos:
                tipo_plan = cedis_plan.get(tipo, {})
                tipo_salida = cedis_salida.get(tipo, {})
                
                all_categorias = sorted(set(tipo_plan.keys()) | set(tipo_salida.keys()))
                
                categorias_list = []
                tipo_total_plan = Decimal("0")
                tipo_total_salida = Decimal("0")
                
                for categoria in all_categorias:
                    categoria_plan = tipo_plan.get(categoria, {})
                    categoria_salida = tipo_salida.get(categoria, {})
                    
                    all_productos = sorted(set(categoria_plan.keys()) | set(categoria_salida.keys()))
                    
                    productos_list = []
                    categoria_total_plan = Decimal("0")
                    categoria_total_salida = Decimal("0")
                    
                    for producto in all_productos:
                        plan_qty = categoria_plan.get(producto, Decimal("0"))
                        salida_qty = categoria_salida.get(producto, Decimal("0"))
                        
                        percent = self._calc_percent(salida_qty, plan_qty)
                        
                        productos_list.append({
                            "name": producto,
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
                    
                    tipo_total_plan += categoria_total_plan
                    tipo_total_salida += categoria_total_salida
                
                # Ordenar categorías de mayor a menor por porcentaje de cumplimiento
                categorias_list.sort(key=lambda x: x["percent"], reverse=True)
                
                tipo_percent = self._calc_percent(tipo_total_salida, tipo_total_plan)
                
                tipos_list.append({
                    "name": tipo,
                    "plan": tipo_total_plan,
                    "salida": tipo_total_salida,
                    "percent": tipo_percent,
                    "categorias": categorias_list,
                })
                
                cedis_total_plan += tipo_total_plan
                cedis_total_salida += tipo_total_salida
            
            # Ordenar tipos de mayor a menor por porcentaje de cumplimiento
            tipos_list.sort(key=lambda x: x["percent"], reverse=True)
            
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

    def _build_resumen_tiendas(self, plan_date, salida_date, pvp_map):
        """
        Construye resumen por Tienda con jerarquía: Tienda → Prioridad → Tipo de carga → Producto
        """
        if not plan_date:
            return []
        
        # Obtener planificaciones
        plan_qs = (
            PlanificacionNormalizada.objects
            .filter(plan_month=plan_date)
            .select_related("sucursal", "product")
        )
        
        # Obtener salidas
        salida_qs = (
            SalidaNormalizada.objects
            .filter(fecha_salida=salida_date)
            .select_related("sucursal_destino", "product")
        ) if salida_date else SalidaNormalizada.objects.none()
        
        # Crear lookup de planificaciones por (sucursal, sku)
        plan_lookup = set()
        for p in plan_qs:
            key = (p.sucursal_id, p.item_code.lower() if p.item_code else "")
            plan_lookup.add(key)
        
        # Agrupar planificaciones por Tienda → Prioridad → Tipo → Producto
        plan_by_tienda = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {"qty": Decimal("0"), "usd": Decimal("0")}))))
        for p in plan_qs:
            tienda_name = p.sucursal.name if p.sucursal else "SIN TIENDA"
            prioridad = "PLANIFICADO"  # Las planificaciones son siempre planificadas
            tipo_carga = p.tipo_carga.strip() if p.tipo_carga else "SIN TIPO"
            producto = f"{p.item_code} - {p.item_name}" if p.item_code and p.item_name else p.item_code or p.item_name or "SIN NOMBRE"
            qty = Decimal(p.a_despachar_total or 0)
            price = self._get_price(p.item_code, pvp_map)
            plan_by_tienda[tienda_name][prioridad][tipo_carga][producto]["qty"] += qty
            plan_by_tienda[tienda_name][prioridad][tipo_carga][producto]["usd"] += qty * price
        
        # Agrupar salidas por Tienda → Prioridad → Tipo → Producto
        salida_plan_by_tienda = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {"qty": Decimal("0"), "usd": Decimal("0")}))))
        salida_noplan_by_tienda = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {"qty": Decimal("0"), "usd": Decimal("0")}))))
        
        for s in salida_qs:
            tienda_name = s.sucursal_destino.name if s.sucursal_destino else "SIN TIENDA"
            tipo_carga = "SIN TIPO"  # Las salidas no tienen tipo_carga
            producto = f"{s.sku} - {s.descripcion}" if s.sku and s.descripcion else s.sku or s.descripcion or "SIN NOMBRE"
            qty = Decimal(s.cantidad or 0)
            price = self._get_price(s.sku, pvp_map)
            
            # Verificar si estaba planificada
            key = (s.sucursal_destino_id, s.sku.lower() if s.sku else "")
            
            if key in plan_lookup:
                prioridad = "PLANIFICADO"
                salida_plan_by_tienda[tienda_name][prioridad][tipo_carga][producto]["qty"] += qty
                salida_plan_by_tienda[tienda_name][prioridad][tipo_carga][producto]["usd"] += qty * price
            else:
                prioridad = "NO PLANIFICADO"
                salida_noplan_by_tienda[tienda_name][prioridad][tipo_carga][producto]["qty"] += qty
                salida_noplan_by_tienda[tienda_name][prioridad][tipo_carga][producto]["usd"] += qty * price
        
        # Construir resultado jerárquico
        result = []
        all_tiendas = sorted(set(plan_by_tienda.keys()) | set(salida_plan_by_tienda.keys()) | set(salida_noplan_by_tienda.keys()))
        
        for tienda_name in all_tiendas:
            tienda_plan = plan_by_tienda.get(tienda_name, {})
            tienda_salida_plan = salida_plan_by_tienda.get(tienda_name, {})
            tienda_salida_noplan = salida_noplan_by_tienda.get(tienda_name, {})
            
            # Combinar todas las prioridades
            all_prioridades = sorted(set(tienda_plan.keys()) | set(tienda_salida_plan.keys()) | set(tienda_salida_noplan.keys()))
            
            prioridades_list = []
            tienda_total_plan_qty = Decimal("0")
            tienda_total_plan_usd = Decimal("0")
            tienda_total_salida_plan_qty = Decimal("0")
            tienda_total_salida_plan_usd = Decimal("0")
            tienda_total_salida_noplan_qty = Decimal("0")
            tienda_total_salida_noplan_usd = Decimal("0")
            
            for prioridad in all_prioridades:
                prio_plan = tienda_plan.get(prioridad, {})
                prio_salida_plan = tienda_salida_plan.get(prioridad, {})
                prio_salida_noplan = tienda_salida_noplan.get(prioridad, {})
                
                all_tipos = sorted(set(prio_plan.keys()) | set(prio_salida_plan.keys()) | set(prio_salida_noplan.keys()))
                
                tipos_list = []
                prio_total_plan_qty = Decimal("0")
                prio_total_plan_usd = Decimal("0")
                prio_total_salida_plan_qty = Decimal("0")
                prio_total_salida_plan_usd = Decimal("0")
                prio_total_salida_noplan_qty = Decimal("0")
                prio_total_salida_noplan_usd = Decimal("0")
                
                for tipo in all_tipos:
                    tipo_plan = prio_plan.get(tipo, {})
                    tipo_salida_plan = prio_salida_plan.get(tipo, {})
                    tipo_salida_noplan = prio_salida_noplan.get(tipo, {})
                    
                    all_productos = sorted(set(tipo_plan.keys()) | set(tipo_salida_plan.keys()) | set(tipo_salida_noplan.keys()))
                    
                    productos_list = []
                    tipo_total_plan_qty = Decimal("0")
                    tipo_total_plan_usd = Decimal("0")
                    tipo_total_salida_plan_qty = Decimal("0")
                    tipo_total_salida_plan_usd = Decimal("0")
                    tipo_total_salida_noplan_qty = Decimal("0")
                    tipo_total_salida_noplan_usd = Decimal("0")
                    
                    for producto in all_productos:
                        plan = tipo_plan.get(producto, {"qty": Decimal("0"), "usd": Decimal("0")})
                        salida_plan = tipo_salida_plan.get(producto, {"qty": Decimal("0"), "usd": Decimal("0")})
                        salida_noplan = tipo_salida_noplan.get(producto, {"qty": Decimal("0"), "usd": Decimal("0")})
                        
                        total_salida_qty = salida_plan["qty"] + salida_noplan["qty"]
                        total_salida_usd = salida_plan["usd"] + salida_noplan["usd"]
                        
                        productos_list.append({
                            "name": producto,
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
                        
                        tipo_total_plan_qty += plan["qty"]
                        tipo_total_plan_usd += plan["usd"]
                        tipo_total_salida_plan_qty += salida_plan["qty"]
                        tipo_total_salida_plan_usd += salida_plan["usd"]
                        tipo_total_salida_noplan_qty += salida_noplan["qty"]
                        tipo_total_salida_noplan_usd += salida_noplan["usd"]
                    
                    # Ordenar productos por porcentaje
                    productos_list.sort(key=lambda x: x["percent_qty"], reverse=True)
                    
                    tipo_total_salida_qty = tipo_total_salida_plan_qty + tipo_total_salida_noplan_qty
                    tipo_total_salida_usd = tipo_total_salida_plan_usd + tipo_total_salida_noplan_usd
                    
                    tipos_list.append({
                        "name": tipo,
                        "plan_qty": tipo_total_plan_qty,
                        "plan_usd": tipo_total_plan_usd,
                        "salida_plan_qty": tipo_total_salida_plan_qty,
                        "salida_plan_usd": tipo_total_salida_plan_usd,
                        "percent_qty": self._calc_percent(tipo_total_salida_plan_qty, tipo_total_plan_qty),
                        "percent_usd": self._calc_percent(tipo_total_salida_plan_usd, tipo_total_plan_usd),
                        "salida_noplan_qty": tipo_total_salida_noplan_qty,
                        "salida_noplan_usd": tipo_total_salida_noplan_usd,
                        "total_salida_qty": tipo_total_salida_qty,
                        "total_salida_usd": tipo_total_salida_usd,
                        "productos": productos_list,
                    })
                    
                    prio_total_plan_qty += tipo_total_plan_qty
                    prio_total_plan_usd += tipo_total_plan_usd
                    prio_total_salida_plan_qty += tipo_total_salida_plan_qty
                    prio_total_salida_plan_usd += tipo_total_salida_plan_usd
                    prio_total_salida_noplan_qty += tipo_total_salida_noplan_qty
                    prio_total_salida_noplan_usd += tipo_total_salida_noplan_usd
                
                # Ordenar tipos por porcentaje
                tipos_list.sort(key=lambda x: x["percent_qty"], reverse=True)
                
                prio_total_salida_qty = prio_total_salida_plan_qty + prio_total_salida_noplan_qty
                prio_total_salida_usd = prio_total_salida_plan_usd + prio_total_salida_noplan_usd
                
                prioridades_list.append({
                    "name": prioridad,
                    "plan_qty": prio_total_plan_qty,
                    "plan_usd": prio_total_plan_usd,
                    "salida_plan_qty": prio_total_salida_plan_qty,
                    "salida_plan_usd": prio_total_salida_plan_usd,
                    "percent_qty": self._calc_percent(prio_total_salida_plan_qty, prio_total_plan_qty),
                    "percent_usd": self._calc_percent(prio_total_salida_plan_usd, prio_total_plan_usd),
                    "salida_noplan_qty": prio_total_salida_noplan_qty,
                    "salida_noplan_usd": prio_total_salida_noplan_usd,
                    "total_salida_qty": prio_total_salida_qty,
                    "total_salida_usd": prio_total_salida_usd,
                    "tipos": tipos_list,
                })
                
                tienda_total_plan_qty += prio_total_plan_qty
                tienda_total_plan_usd += prio_total_plan_usd
                tienda_total_salida_plan_qty += prio_total_salida_plan_qty
                tienda_total_salida_plan_usd += prio_total_salida_plan_usd
                tienda_total_salida_noplan_qty += prio_total_salida_noplan_qty
                tienda_total_salida_noplan_usd += prio_total_salida_noplan_usd
            
            # Ordenar prioridades (PLANIFICADO primero)
            prioridades_list.sort(key=lambda x: (x["name"] != "PLANIFICADO", x["percent_qty"]), reverse=True)
            
            tienda_total_salida_qty = tienda_total_salida_plan_qty + tienda_total_salida_noplan_qty
            tienda_total_salida_usd = tienda_total_salida_plan_usd + tienda_total_salida_noplan_usd
            
            result.append({
                "name": tienda_name,
                "plan_qty": tienda_total_plan_qty,
                "plan_usd": tienda_total_plan_usd,
                "salida_plan_qty": tienda_total_salida_plan_qty,
                "salida_plan_usd": tienda_total_salida_plan_usd,
                "percent_qty": self._calc_percent(tienda_total_salida_plan_qty, tienda_total_plan_qty),
                "percent_usd": self._calc_percent(tienda_total_salida_plan_usd, tienda_total_plan_usd),
                "salida_noplan_qty": tienda_total_salida_noplan_qty,
                "salida_noplan_usd": tienda_total_salida_noplan_usd,
                "total_salida_qty": tienda_total_salida_qty,
                "total_salida_usd": tienda_total_salida_usd,
                "prioridades": prioridades_list,
            })
        
        # Ordenar tiendas de mayor a menor por porcentaje de cumplimiento
        result.sort(key=lambda x: x["percent_qty"], reverse=True)
        
        return result

    def _calculate_nacional(self, resumen_tiendas):
        """Calcula totales nacionales"""
        total = {
            "plan_qty": Decimal("0"),
            "plan_usd": Decimal("0"),
            "salida_plan_qty": Decimal("0"),
            "salida_plan_usd": Decimal("0"),
            "salida_noplan_qty": Decimal("0"),
            "salida_noplan_usd": Decimal("0"),
            "total_salida_qty": Decimal("0"),
            "total_salida_usd": Decimal("0"),
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
        
        total["percent_qty"] = self._calc_percent(total["salida_plan_qty"], total["plan_qty"])
        total["percent_usd"] = self._calc_percent(total["salida_plan_usd"], total["plan_usd"])
        
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
