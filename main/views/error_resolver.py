import difflib
from collections import defaultdict
from decimal import Decimal

from django.db import transaction
from django.shortcuts import redirect, render
from django.views import View

from ..models import Cendis, Planificacion, Product, Salida, Sucursal


class PlanificacionErrorResolverView(View):
    template_name = "planificacion_error_resolver.html"

    def get(self, request, *args, **kwargs):
        # Obtener errores agrupados
        errors = Planificacion.objects.filter(normalize_status="error")
        
        # Agrupar por tipo de error
        cedis_origen_faltantes = defaultdict(list)
        sucursales_faltantes = defaultdict(list)
        productos_faltantes = defaultdict(list)
        
        for error in errors:
            notes = error.normalize_notes or ""
            if "CEDIS origen no encontrado" in notes:
                origen_name = error.cendis
                cedis_origen_faltantes[origen_name].append(error.id)
            elif "Sucursal no encontrada" in notes:
                sucursal_name = error.sucursal
                sucursales_faltantes[sucursal_name].append(error.id)
            elif "Producto no encontrado" in notes:
                product_code = error.item_code
                productos_faltantes[product_code].append(error.id)
        
        # Obtener sucursales, cendis y productos existentes para sugerencias
        existing_sucursales = list(Sucursal.objects.values_list('name', flat=True))
        existing_cendis = list(Cendis.objects.values_list('origin', flat=True))
        existing_products = list(Product.objects.values_list('code', 'name'))
        
        # Generar sugerencias con fuzzy matching para CEDIS origen (busca en Cendis)
        cedis_origen_suggestions = {}
        for origen_name in cedis_origen_faltantes.keys():
            if origen_name:
                matches = difflib.get_close_matches(
                    origen_name.lower(), 
                    [s.lower() for s in existing_cendis], 
                    n=3, 
                    cutoff=0.6
                )
                cedis_origen_suggestions[origen_name] = [
                    s for s in existing_cendis 
                    if s.lower() in matches
                ]
        
        # Generar sugerencias con fuzzy matching para sucursales destino
        sucursal_suggestions = {}
        for sucursal_name in sucursales_faltantes.keys():
            if sucursal_name:
                matches = difflib.get_close_matches(
                    sucursal_name.lower(), 
                    [s.lower() for s in existing_sucursales], 
                    n=3, 
                    cutoff=0.6
                )
                # Obtener nombres originales
                sucursal_suggestions[sucursal_name] = [
                    s for s in existing_sucursales 
                    if s.lower() in matches
                ]
        
        product_suggestions = {}
        for product_code in productos_faltantes.keys():
            if product_code:
                matches = difflib.get_close_matches(
                    product_code.lower(),
                    [p[0].lower() for p in existing_products],
                    n=3,
                    cutoff=0.6
                )
                product_suggestions[product_code] = [
                    {"code": p[0], "name": p[1]}
                    for p in existing_products
                    if p[0].lower() in matches
                ]
        
        return render(request, self.template_name, {
            "cedis_origen_faltantes": dict(cedis_origen_faltantes),
            "sucursales_faltantes": dict(sucursales_faltantes),
            "productos_faltantes": dict(productos_faltantes),
            "cedis_origen_suggestions": cedis_origen_suggestions,
            "sucursal_suggestions": sucursal_suggestions,
            "product_suggestions": product_suggestions,
            "total_errors": errors.count(),
        })
    
    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        
        if action == "create_cedis_origen":
            return self._create_cedis_origen(request)
        elif action == "map_cedis_origen":
            return self._map_cedis_origen(request)
        elif action == "create_sucursal":
            return self._create_sucursal(request)
        elif action == "map_sucursal":
            return self._map_sucursal(request)
        elif action == "create_product":
            return self._create_product(request)
        elif action == "map_product":
            return self._map_product(request)
        elif action == "ignore_errors":
            return self._ignore_errors(request)
        
        return redirect("planificacion_error_resolver")
    
    def _create_cedis_origen(self, request):
        cedis_name = request.POST.get("cedis_name")
        cedis_code = request.POST.get("cedis_code")
        
        if not cedis_name or not cedis_code:
            return render(request, self.template_name, {
                "error": "Nombre de CEDIS y Código son requeridos",
            })
        
        try:
            with transaction.atomic():
                # Crear CEDIS en tabla Cendis
                cedis = Cendis.objects.create(
                    origin=cedis_name.strip(),
                    code=cedis_code.strip()
                )
                
                # Actualizar registros con error relacionados
                Planificacion.objects.filter(
                    normalize_status="error",
                    cendis__iexact=cedis_name
                ).update(
                    normalize_status="pending",
                    normalize_notes="",
                    normalized_at=None
                )
                
                return redirect("planificacion_error_resolver")
        except Exception as e:
            return render(request, self.template_name, {
                "error": f"Error al crear CEDIS: {str(e)}",
            })
    
    def _map_cedis_origen(self, request):
        original_name = request.POST.get("original_name")
        target_name = request.POST.get("target_name")
        
        if not original_name or not target_name:
            return render(request, self.template_name, {
                "error": "Nombre original y objetivo son requeridos",
            })
        
        try:
            with transaction.atomic():
                # Actualizar todos los registros con el nombre original
                updated = Planificacion.objects.filter(
                    cendis__iexact=original_name
                ).update(
                    cendis=target_name,
                    normalize_status="pending",
                    normalize_notes="",
                    normalized_at=None
                )
                
                return redirect("planificacion_error_resolver")
        except Exception as e:
            return render(request, self.template_name, {
                "error": f"Error al mapear CEDIS origen: {str(e)}",
            })
    
    def _create_sucursal(self, request):
        sucursal_name = request.POST.get("sucursal_name")
        bpl_id = request.POST.get("bpl_id")
        
        if not sucursal_name or not bpl_id:
            return render(request, self.template_name, {
                "error": "Nombre y BPL ID son requeridos",
            })
        
        try:
            with transaction.atomic():
                # Crear sucursal
                sucursal = Sucursal.objects.create(
                    name=sucursal_name.strip(),
                    bpl_id=int(bpl_id)
                )
                
                # Actualizar registros con error relacionados
                Planificacion.objects.filter(
                    normalize_status="error",
                    sucursal__iexact=sucursal_name
                ).update(
                    normalize_status="pending",
                    normalize_notes="",
                    normalized_at=None
                )
                
                return redirect("planificacion_error_resolver")
        except Exception as e:
            return render(request, self.template_name, {
                "error": f"Error al crear sucursal: {str(e)}",
            })
    
    def _map_sucursal(self, request):
        original_name = request.POST.get("original_name")
        target_name = request.POST.get("target_name")
        
        if not original_name or not target_name:
            return render(request, self.template_name, {
                "error": "Nombre original y objetivo son requeridos",
            })
        
        try:
            with transaction.atomic():
                # Actualizar todos los registros con el nombre original
                updated = Planificacion.objects.filter(
                    sucursal__iexact=original_name
                ).update(
                    sucursal=target_name,
                    normalize_status="pending",
                    normalize_notes="",
                    normalized_at=None
                )
                
                return redirect("planificacion_error_resolver")
        except Exception as e:
            return render(request, self.template_name, {
                "error": f"Error al mapear sucursal: {str(e)}",
            })
    
    def _create_product(self, request):
        code = request.POST.get("product_code")
        name = request.POST.get("product_name")
        group = request.POST.get("product_group", "")
        
        if not code or not name:
            return render(request, self.template_name, {
                "error": "Código y nombre son requeridos",
            })
        
        try:
            with transaction.atomic():
                product = Product.objects.create(
                    code=code.strip(),
                    name=name.strip(),
                    group=group.strip()
                )
                
                # Actualizar registros con error relacionados
                Planificacion.objects.filter(
                    normalize_status="error",
                    item_code__iexact=code
                ).update(
                    normalize_status="pending",
                    normalize_notes="",
                    normalized_at=None
                )
                
                return redirect("planificacion_error_resolver")
        except Exception as e:
            return render(request, self.template_name, {
                "error": f"Error al crear producto: {str(e)}",
            })
    
    def _map_product(self, request):
        original_code = request.POST.get("original_code")
        target_code = request.POST.get("target_code")
        
        if not original_code or not target_code:
            return render(request, self.template_name, {
                "error": "Código original y objetivo son requeridos",
            })
        
        try:
            with transaction.atomic():
                # Actualizar todos los registros con el código original
                Planificacion.objects.filter(
                    item_code__iexact=original_code
                ).update(
                    item_code=target_code,
                    normalize_status="pending",
                    normalize_notes="",
                    normalized_at=None
                )
                
                return redirect("planificacion_error_resolver")
        except Exception as e:
            return render(request, self.template_name, {
                "error": f"Error al mapear producto: {str(e)}",
            })
    
    def _ignore_errors(self, request):
        error_type = request.POST.get("error_type")
        error_value = request.POST.get("error_value")
        
        try:
            with transaction.atomic():
                if error_type == "sucursal":
                    Planificacion.objects.filter(
                        normalize_status="error",
                        sucursal__iexact=error_value
                    ).update(
                        normalize_status="ignored",
                        normalize_notes="Ignorado manualmente"
                    )
                elif error_type == "product":
                    Planificacion.objects.filter(
                        normalize_status="error",
                        item_code__iexact=error_value
                    ).update(
                        normalize_status="ignored",
                        normalize_notes="Ignorado manualmente"
                    )
                
                return redirect("planificacion_error_resolver")
        except Exception as e:
            return render(request, self.template_name, {
                "error": f"Error al ignorar: {str(e)}",
            })


class SalidaErrorResolverView(View):
    template_name = "salida_error_resolver.html"

    def get(self, request, *args, **kwargs):
        errors = Salida.objects.filter(normalize_status="error")
        
        sucursales_origen_faltantes = defaultdict(list)
        sucursales_destino_faltantes = defaultdict(list)
        productos_faltantes = defaultdict(list)
        
        for error in errors:
            notes = error.normalize_notes or ""
            if "Sucursal origen no encontrada" in notes:
                sucursal_name = error.nombre_sucursal_origen
                sucursales_origen_faltantes[sucursal_name].append(error.id)
            if "Sucursal destino no encontrada" in notes:
                sucursal_name = error.nombre_sucursal_destino
                sucursales_destino_faltantes[sucursal_name].append(error.id)
            if "Producto no encontrado" in notes:
                product_code = error.sku
                productos_faltantes[product_code].append(error.id)
        
        existing_sucursales = list(Sucursal.objects.values_list('name', flat=True))
        existing_products = list(Product.objects.values_list('code', 'name'))
        
        sucursal_suggestions = {}
        for sucursal_name in set(list(sucursales_origen_faltantes.keys()) + list(sucursales_destino_faltantes.keys())):
            if sucursal_name:
                matches = difflib.get_close_matches(
                    sucursal_name.lower(),
                    [s.lower() for s in existing_sucursales],
                    n=3,
                    cutoff=0.6
                )
                sucursal_suggestions[sucursal_name] = [
                    s for s in existing_sucursales
                    if s.lower() in matches
                ]
        
        product_suggestions = {}
        for product_code in productos_faltantes.keys():
            if product_code:
                matches = difflib.get_close_matches(
                    product_code.lower(),
                    [p[0].lower() for p in existing_products],
                    n=3,
                    cutoff=0.6
                )
                product_suggestions[product_code] = [
                    {"code": p[0], "name": p[1]}
                    for p in existing_products
                    if p[0].lower() in matches
                ]
        
        return render(request, self.template_name, {
            "sucursales_origen_faltantes": dict(sucursales_origen_faltantes),
            "sucursales_destino_faltantes": dict(sucursales_destino_faltantes),
            "productos_faltantes": dict(productos_faltantes),
            "sucursal_suggestions": sucursal_suggestions,
            "product_suggestions": product_suggestions,
            "total_errors": errors.count(),
        })
    
    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        
        if action == "create_sucursal":
            return self._create_sucursal(request)
        elif action == "map_sucursal":
            return self._map_sucursal(request)
        elif action == "create_product":
            return self._create_product(request)
        elif action == "map_product":
            return self._map_product(request)
        
        return redirect("salida_error_resolver")
    
    def _create_sucursal(self, request):
        sucursal_name = request.POST.get("sucursal_name")
        bpl_id = request.POST.get("bpl_id")
        
        if not sucursal_name or not bpl_id:
            return render(request, self.template_name, {
                "error": "Nombre y BPL ID son requeridos",
            })
        
        try:
            with transaction.atomic():
                sucursal = Sucursal.objects.create(
                    name=sucursal_name.strip(),
                    bpl_id=int(bpl_id)
                )
                
                Salida.objects.filter(
                    normalize_status="error",
                    nombre_sucursal_origen__iexact=sucursal_name
                ).update(
                    normalize_status="pending",
                    normalize_notes="",
                    normalized_at=None
                )
                
                Salida.objects.filter(
                    normalize_status="error",
                    nombre_sucursal_destino__iexact=sucursal_name
                ).update(
                    normalize_status="pending",
                    normalize_notes="",
                    normalized_at=None
                )
                
                return redirect("salida_error_resolver")
        except Exception as e:
            return render(request, self.template_name, {
                "error": f"Error al crear sucursal: {str(e)}",
            })
    
    def _map_sucursal(self, request):
        original_name = request.POST.get("original_name")
        target_name = request.POST.get("target_name")
        field_type = request.POST.get("field_type", "both")  # origen, destino, or both
        
        if not original_name or not target_name:
            return render(request, self.template_name, {
                "error": "Nombre original y objetivo son requeridos",
            })
        
        try:
            with transaction.atomic():
                if field_type in ["origen", "both"]:
                    Salida.objects.filter(
                        nombre_sucursal_origen__iexact=original_name
                    ).update(
                        nombre_sucursal_origen=target_name,
                        normalize_status="pending",
                        normalize_notes="",
                        normalized_at=None
                    )
                
                if field_type in ["destino", "both"]:
                    Salida.objects.filter(
                        nombre_sucursal_destino__iexact=original_name
                    ).update(
                        nombre_sucursal_destino=target_name,
                        normalize_status="pending",
                        normalize_notes="",
                        normalized_at=None
                    )
                
                return redirect("salida_error_resolver")
        except Exception as e:
            return render(request, self.template_name, {
                "error": f"Error al mapear sucursal: {str(e)}",
            })
    
    def _create_product(self, request):
        code = request.POST.get("product_code")
        name = request.POST.get("product_name")
        group = request.POST.get("product_group", "")
        
        if not code or not name:
            return render(request, self.template_name, {
                "error": "Código y nombre son requeridos",
            })
        
        try:
            with transaction.atomic():
                product = Product.objects.create(
                    code=code.strip(),
                    name=name.strip(),
                    group=group.strip()
                )
                
                Salida.objects.filter(
                    normalize_status="error",
                    sku__iexact=code
                ).update(
                    normalize_status="pending",
                    normalize_notes="",
                    normalized_at=None
                )
                
                return redirect("salida_error_resolver")
        except Exception as e:
            return render(request, self.template_name, {
                "error": f"Error al crear producto: {str(e)}",
            })
    
    def _map_product(self, request):
        original_code = request.POST.get("original_code")
        target_code = request.POST.get("target_code")
        
        if not original_code or not target_code:
            return render(request, self.template_name, {
                "error": "Código original y objetivo son requeridos",
            })
        
        try:
            with transaction.atomic():
                Salida.objects.filter(
                    sku__iexact=original_code
                ).update(
                    sku=target_code,
                    normalize_status="pending",
                    normalize_notes="",
                    normalized_at=None
                )
                
                return redirect("salida_error_resolver")
        except Exception as e:
            return render(request, self.template_name, {
                "error": f"Error al mapear producto: {str(e)}",
            })
