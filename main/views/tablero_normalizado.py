import datetime
from decimal import Decimal

from django.shortcuts import render
from django.views import View
from django.http import HttpResponse
import csv

from ..models import PlanificacionNormalizada, SalidaNormalizada


class TableroNormalizadoView(View):
    template_name = "tablero_normalizado.html"

    def get(self, request, *args, **kwargs):
        # Obtener fechas seleccionadas
        plan_date = self._selected_plan_date(request)
        salida_date = self._selected_salida_date(request)
        selected_origin = self._selected_origin(request)
        
        # Obtener fechas disponibles para los selectores
        plan_dates = self._available_plan_dates()
        salida_dates = self._available_salida_dates()
        origin_choices = self._origin_choices()
        
        # Si no hay fechas seleccionadas, usar las más recientes
        if not plan_date and plan_dates:
            plan_date = plan_dates[0]
        if not salida_date and salida_dates:
            salida_date = salida_dates[0]
        
        # Obtener datos de plan y salidas para las fechas específicas
        plan_data = self._plan_by_dest_group(plan_date) if plan_date else {}
        salida_data = self._salidas_by_origin_dest_group(salida_date, selected_origin) if salida_date else {}
        
        # Construir tabla de comparación
        table = self._build_comparison_table(plan_data, salida_data, plan_date, salida_date)
        
        # Calcular resumen general
        summary = self._calculate_summary(table)
        
        # Export CSV
        if request.GET.get("export") == "csv":
            return self._export_csv(table, plan_date, salida_date)

        return render(
            request,
            self.template_name,
            {
                "plan_date": plan_date,
                "salida_date": salida_date,
                "plan_dates": plan_dates,
                "salida_dates": salida_dates,
                "selected_origin": selected_origin,
                "origin_choices": origin_choices,
                "table": table,
                "summary": summary,
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

    def _selected_origin(self, request):
        raw = request.GET.get("origin") or request.POST.get("origin")
        try:
            return int(raw) if raw else None
        except (TypeError, ValueError):
            return None
    
    def _available_plan_dates(self):
        """Obtener fechas disponibles de planificación ordenadas descendente"""
        return list(
            PlanificacionNormalizada.objects
            .values_list("plan_month", flat=True)
            .distinct()
            .order_by("-plan_month")
        )
    
    def _available_salida_dates(self):
        """Obtener fechas disponibles de salidas ordenadas descendente"""
        return list(
            SalidaNormalizada.objects
            .values_list("fecha_salida", flat=True)
            .distinct()
            .order_by("-fecha_salida")
        )

    def _plan_by_dest_group(self, plan_date):
        """Retorna plan agrupado por origen -> destino -> grupo para una fecha específica"""
        if not plan_date:
            return {}
        
        result = {}
        qs = (
            PlanificacionNormalizada.objects
            .filter(plan_month=plan_date)
            .select_related("product", "sucursal", "cedis_origen")
        )
        
        for row in qs:
            # Origen (CEDIS) - si no tiene, usar "TODOS"
            if row.cedis_origen:
                key_origin = (row.cedis_origen.id, row.cedis_origen.origin)
            else:
                key_origin = (None, "TODOS LOS CEDIS")
            
            # Destino
            dest = row.sucursal
            if not dest:
                continue
            
            group = (row.product.group if row.product and row.product.group else "SIN GRUPO").strip() or "SIN GRUPO"
            qty = Decimal(row.a_despachar_total or 0)
            
            origin_bucket = result.setdefault(key_origin, {})
            dest_bucket = origin_bucket.setdefault(dest.id, {
                "name": dest.name,
                "groups": {}
            })
            dest_bucket["groups"].setdefault(group, Decimal("0"))
            dest_bucket["groups"][group] += qty
        
        return result

    def _salidas_by_origin_dest_group(self, salida_date, selected_origin_id=None):
        """Retorna salidas agrupadas por origen -> destino -> grupo para una fecha específica"""
        if not salida_date:
            return {}
        
        result = {}
        qs = (
            SalidaNormalizada.objects
            .filter(fecha_salida=salida_date)
            .select_related("product", "cedis_origen", "sucursal_destino")
        )
        
        if selected_origin_id:
            qs = qs.filter(cedis_origen_id=selected_origin_id)
        
        for row in qs:
            if not row.sucursal_destino:
                continue
            
            origin = row.cedis_origen
            dest = row.sucursal_destino
            group = (row.product.group if row.product and row.product.group else "SIN GRUPO").strip() or "SIN GRUPO"
            qty = Decimal(row.cantidad or 0)
            
            key_origin = (origin.id if origin else None, origin.origin if origin else "SIN ORIGEN")
            origin_bucket = result.setdefault(key_origin, {})
            dest_bucket = origin_bucket.setdefault(dest.id, {
                "name": dest.name,
                "groups": {}
            })
            dest_bucket["groups"].setdefault(group, Decimal("0"))
            dest_bucket["groups"][group] += qty
        
        return result
    
    def _build_comparison_table(self, plan_data, salida_data, plan_date, salida_date):
        """
        Construye tabla comparativa entre plan y salidas.
        Cuando la planificación no tiene CEDIS origen (TODOS), se agregan salidas de todos los orígenes.
        """
        table = []
        
        # Caso especial: Si hay planificación con origen None (TODOS), agregar salidas de todos los orígenes
        plan_todos_key = (None, "TODOS LOS CEDIS")
        if plan_todos_key in plan_data:
            # Agregar salidas de todos los orígenes a "TODOS LOS CEDIS"
            salidas_agregadas = {}
            for origin_key, origin_data in salida_data.items():
                for dest_id, dest_data in origin_data.items():
                    if dest_id not in salidas_agregadas:
                        salidas_agregadas[dest_id] = {
                            "name": dest_data["name"],
                            "groups": {}
                        }
                    # Sumar cantidades por grupo
                    for group, qty in dest_data["groups"].items():
                        current = salidas_agregadas[dest_id]["groups"].get(group, Decimal("0"))
                        salidas_agregadas[dest_id]["groups"][group] = current + qty
            
            # Crear entrada para "TODOS LOS CEDIS" combinando plan y salidas agregadas
            plan_origin = plan_data[plan_todos_key]
            all_dest_ids = set(plan_origin.keys()) | set(salidas_agregadas.keys())
            
            destinos = []
            for dest_id in all_dest_ids:
                plan_dest = plan_origin.get(dest_id, {"name": "", "groups": {}})
                salida_dest = salidas_agregadas.get(dest_id, {"name": "", "groups": {}})
                
                dest_name = plan_dest.get("name") or salida_dest.get("name", f"Destino {dest_id}")
                all_groups = set(plan_dest.get("groups", {}).keys()) | set(salida_dest.get("groups", {}).keys())
                
                grupos = []
                for group in all_groups:
                    plan_qty = plan_dest.get("groups", {}).get(group, Decimal("0"))
                    salida_qty = salida_dest.get("groups", {}).get(group, Decimal("0"))
                    
                    if plan_qty > 0:
                        percent = (salida_qty / plan_qty) * Decimal("100")
                        percent = percent.quantize(Decimal("0.01"))
                    else:
                        percent = Decimal("0") if salida_qty == 0 else Decimal("999")
                    
                    if plan_qty == 0 and salida_qty > 0:
                        status = "sin_plan"
                    elif plan_qty > 0 and salida_qty == 0:
                        status = "sin_entregas"
                    elif percent >= 100:
                        status = "completo"
                    elif percent >= 80:
                        status = "alto"
                    elif percent >= 50:
                        status = "medio"
                    elif percent > 0:
                        status = "bajo"
                    else:
                        status = "ninguno"
                    
                    grupos.append({
                        "name": group,
                        "plan": plan_qty,
                        "salida": salida_qty,
                        "percent": percent if percent < 999 else None,
                        "status": status
                    })
                
                if grupos:
                    destinos.append({
                        "id": dest_id,
                        "name": dest_name,
                        "grupos": sorted(grupos, key=lambda g: g["name"])
                    })
            
            if destinos:
                table.append({
                    "origin_id": None,
                    "origin_name": "TODOS LOS CEDIS",
                    "destinos": sorted(destinos, key=lambda d: d["name"])
                })
        
        # Procesar orígenes específicos (salidas sin plan correspondiente)
        for origin_key in salida_data.keys():
            origin_id, origin_name = origin_key
            
            # Solo mostrar orígenes específicos si tienen salidas sin plan
            if origin_key not in plan_data and plan_todos_key not in plan_data:
                salida_origin = salida_data[origin_key]
                destinos = []
                
                for dest_id, salida_dest in salida_origin.items():
                    dest_name = salida_dest.get("name", f"Destino {dest_id}")
                    all_groups = set(salida_dest.get("groups", {}).keys())
                    
                    grupos = []
                    for group in all_groups:
                        salida_qty = salida_dest["groups"][group]
                        grupos.append({
                            "name": group,
                            "plan": Decimal("0"),
                            "salida": salida_qty,
                            "percent": None,
                            "status": "sin_plan"
                        })
                    
                    if grupos:
                        destinos.append({
                            "id": dest_id,
                            "name": dest_name,
                            "grupos": sorted(grupos, key=lambda g: g["name"])
                        })
                
                if destinos:
                    table.append({
                        "origin_id": origin_id,
                        "origin_name": origin_name,
                        "destinos": sorted(destinos, key=lambda d: d["name"])
                    })
        
        return sorted(table, key=lambda o: o["origin_name"] if o["origin_name"] != "TODOS LOS CEDIS" else "")
    
    
    def _calculate_summary(self, table):
        """Calcula resumen general de cumplimiento"""
        total_plan = Decimal("0")
        total_salidas = Decimal("0")
        total_destinos = 0
        total_grupos = 0
        
        for origen in table:
            for destino in origen["destinos"]:
                total_destinos += 1
                for grupo in destino["grupos"]:
                    total_grupos += 1
                    total_plan += grupo["plan"]
                    total_salidas += grupo["salida"]
        
        percent_general = Decimal("0")
        if total_plan > 0:
            percent_general = (total_salidas / total_plan) * Decimal("100")
            percent_general = percent_general.quantize(Decimal("0.01"))
        
        return {
            "total_plan": total_plan,
            "total_salidas": total_salidas,
            "percent_general": percent_general,
            "total_destinos": total_destinos,
            "total_grupos": total_grupos,
        }
    
    def _origin_choices(self):
        """Lista de todos los CEDIS disponibles incluyendo opción 'TODOS'"""
        from ..models import Cendis
        
        # Agregar opción "Todos" al inicio
        origins = [(None, "TODOS LOS CEDIS")]
        
        # Obtener todos los CEDIS registrados
        cedis_list = Cendis.objects.values_list('id', 'origin').order_by('origin')
        origins.extend(list(cedis_list))
        
        return origins
    
    def _export_csv(self, table, plan_date, salida_date):
        """Exporta tabla a CSV"""
        response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
        response["Content-Disposition"] = f'attachment; filename="tablero_normalizado_{plan_date}_{salida_date}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            "CEDIS Origen",
            "Sucursal Destino",
            "Grupo",
            f"Plan ({plan_date})",
            f"Salidas ({salida_date})",
            "% Cumplimiento",
            "Estado"
        ])
        
        for origen in table:
            origin_name = origen["origin_name"]
            for destino in origen["destinos"]:
                dest_name = destino["name"]
                for grupo in destino["grupos"]:
                    writer.writerow([
                        origin_name,
                        dest_name,
                        grupo["name"],
                        str(grupo["plan"]),
                        str(grupo["salida"]),
                        f'{grupo["percent"]}%' if grupo["percent"] is not None else "N/A",
                        grupo["status"]
                    ])
        
        return response
