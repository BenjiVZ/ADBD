import difflib
from collections import defaultdict
from decimal import Decimal

from django.db import transaction
from django.shortcuts import redirect, render
from django.views import View

from ..models import Cendis, Planificacion, Product, Salida, Sucursal, IgnorarCedis, IgnorarSucursal


class PlanificacionErrorResolverView(View):
    template_name = "planificacion_error_resolver.html"

    def get(self, request, *args, **kwargs):
        # Obtener errores agrupados
        errors = Planificacion.objects.filter(normalize_status="error")
        
        # Obtener nombres ignorados
        cedis_ignorados = set(IgnorarCedis.objects.values_list("nombre_crudo", flat=True))
        sucursales_ignoradas = set(IgnorarSucursal.objects.values_list("nombre_crudo", flat=True))
        
        # Agrupar por tipo de error
        cedis_origen_faltantes = defaultdict(list)
        sucursales_faltantes = defaultdict(list)
        productos_faltantes = defaultdict(list)
        otros_errores = defaultdict(list)
        
        # IDs de registros a marcar como ignorados
        ids_to_ignore = []
        
        for error in errors:
            notes = error.normalize_notes or ""
            # Buscar múltiples variantes de mensajes de error
            if ("CEDIS" in notes and "origen" in notes) or ("cedis" in notes and "origen" in notes) or ("almacén" in notes and "origen" in notes) or "origen no es un CEDIS" in notes or "Origen NO es un almacén CEDIS" in notes or "CEDIS (almacén) origen" in notes:
                origen_name = error.cendis
                # Verificar si está ignorado
                if origen_name and origen_name in cedis_ignorados:
                    ids_to_ignore.append(error.id)
                else:
                    cedis_origen_faltantes[origen_name].append(error.id)
            elif "Sucursal" in notes or "sucursal" in notes or "tienda" in notes:
                sucursal_name = error.sucursal
                # Verificar si está ignorado
                if sucursal_name and sucursal_name in sucursales_ignoradas:
                    ids_to_ignore.append(error.id)
                else:
                    sucursales_faltantes[sucursal_name].append(error.id)
            elif "Producto" in notes or "producto" in notes:
                product_code = error.item_code
                productos_faltantes[product_code].append(error.id)
            else:
                # Errores que no encajan en las categorías anteriores
                otros_errores[notes[:100]].append(error.id)
        
        # Marcar registros como ignorados si su nombre está en la lista de ignorados
        if ids_to_ignore:
            Planificacion.objects.filter(id__in=ids_to_ignore).update(
                normalize_status="ignored",
                normalize_notes="Ignorado por configuración de biblioteca"
            )
        
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
            "otros_errores": dict(otros_errores),
            "cedis_origen_suggestions": cedis_origen_suggestions,
            "sucursal_suggestions": sucursal_suggestions,
            "product_suggestions": product_suggestions,
            "all_sucursales": sorted(existing_sucursales),
            "all_cedis": sorted(existing_cendis),
            "all_products": sorted(existing_products, key=lambda x: x[0]),
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
                
                # Redirigir a normalizar para que procese los cambios
                # Si no hay más errores, ir a normalizar; si hay, quedarse aquí
                remaining_errors = Planificacion.objects.filter(normalize_status="error").count()
                if remaining_errors == 0:
                    return redirect("planning_normalize")
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
        
        # Obtener nombres ignorados
        cedis_ignorados = set(IgnorarCedis.objects.values_list("nombre_crudo", flat=True))
        sucursales_ignoradas = set(IgnorarSucursal.objects.values_list("nombre_crudo", flat=True))
        
        cedis_origen_faltantes = defaultdict(list)
        sucursales_destino_faltantes = defaultdict(list)
        productos_faltantes = defaultdict(list)
        otros_errores = defaultdict(list)
        
        # IDs de registros a marcar como ignorados
        ids_to_ignore = []
        
        for error in errors:
            notes = error.normalize_notes or ""
            # Detectar errores de CEDIS origen
            if ("CEDIS" in notes and "origen" in notes) or ("cedis" in notes and "origen" in notes) or ("almacén" in notes and "origen" in notes) or "origen NO es un almacén CEDIS" in notes or "Origen NO es un almacén CEDIS" in notes:
                cedis_name = error.nombre_sucursal_origen
                # Verificar si está ignorado
                if cedis_name and cedis_name in cedis_ignorados:
                    ids_to_ignore.append(error.id)
                else:
                    cedis_origen_faltantes[cedis_name].append(error.id)
            # Detectar errores de Sucursal destino
            elif "Sucursal" in notes or "sucursal" in notes or "tienda destino" in notes:
                # Usar sucursal_destino_propuesto como principal, fallback a nombre_sucursal_destino
                sucursal_name = error.sucursal_destino_propuesto or error.nombre_sucursal_destino
                # Verificar si está ignorado
                if sucursal_name and sucursal_name in sucursales_ignoradas:
                    ids_to_ignore.append(error.id)
                else:
                    sucursales_destino_faltantes[sucursal_name].append(error.id)
            # Detectar errores de Producto
            elif "Producto" in notes or "producto" in notes:
                product_code = error.sku
                productos_faltantes[product_code].append(error.id)
            else:
                # Otros errores
                otros_errores[notes[:100]].append(error.id)
        
        # Marcar registros como ignorados si su nombre está en la lista de ignorados
        if ids_to_ignore:
            Salida.objects.filter(id__in=ids_to_ignore).update(
                normalize_status="ignored",
                normalize_notes="Ignorado por configuración de biblioteca"
            )
        
        existing_cedis = list(Cendis.objects.values_list('origin', flat=True))
        existing_sucursales = list(Sucursal.objects.values_list('name', flat=True))
        existing_products = list(Product.objects.values_list('code', 'name'))
        
        # Sugerencias para CEDIS origen
        cedis_suggestions = {}
        for cedis_name in cedis_origen_faltantes.keys():
            if cedis_name:
                matches = difflib.get_close_matches(
                    cedis_name.lower(),
                    [c.lower() for c in existing_cedis],
                    n=3,
                    cutoff=0.6
                )
                cedis_suggestions[cedis_name] = [
                    c for c in existing_cedis
                    if c.lower() in matches
                ]
        
        # Sugerencias para Sucursales destino
        sucursal_suggestions = {}
        for sucursal_name in sucursales_destino_faltantes.keys():
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
        
        # Sugerencias para Productos
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
            "sucursales_destino_faltantes": dict(sucursales_destino_faltantes),
            "productos_faltantes": dict(productos_faltantes),
            "otros_errores": dict(otros_errores),
            "cedis_suggestions": cedis_suggestions,
            "sucursal_suggestions": sucursal_suggestions,
            "product_suggestions": product_suggestions,
            "all_sucursales": sorted(existing_sucursales),
            "all_cedis": sorted(existing_cedis),
            "all_products": sorted(existing_products, key=lambda x: x[0]),
            "total_errors": errors.count(),
        })
    
    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        
        if action == "create_cedis":
            return self._create_cedis(request)
        elif action == "map_cedis":
            return self._map_cedis(request)
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
        
        return redirect("salida_error_resolver")
    
    def _create_cedis(self, request):
        cedis_name = request.POST.get("cedis_name")
        cedis_code = request.POST.get("cedis_code")
        
        if not cedis_name or not cedis_code:
            return render(request, self.template_name, {
                "error": "Nombre y Código son requeridos",
            })
        
        try:
            with transaction.atomic():
                cedis = Cendis.objects.create(
                    origin=cedis_name.strip(),
                    code=cedis_code.strip()
                )
                
                Salida.objects.filter(
                    normalize_status="error",
                    nombre_sucursal_origen__iexact=cedis_name
                ).update(
                    normalize_status="pending",
                    normalize_notes="",
                    normalized_at=None
                )
                
                return redirect("salida_error_resolver")
        except Exception as e:
            return render(request, self.template_name, {
                "error": f"Error al crear CEDIS: {str(e)}",
            })
    
    def _map_cedis(self, request):
        original_name = request.POST.get("original_name")
        target_name = request.POST.get("target_name")
        
        if not original_name or not target_name:
            return render(request, self.template_name, {
                "error": "Nombre original y objetivo son requeridos",
            })
        
        try:
            with transaction.atomic():
                Salida.objects.filter(
                    nombre_sucursal_origen__iexact=original_name
                ).update(
                    nombre_sucursal_origen=target_name,
                    normalize_status="pending",
                    normalize_notes="",
                    normalized_at=None
                )
                
                return redirect("salida_error_resolver")
        except Exception as e:
            return render(request, self.template_name, {
                "error": f"Error al mapear CEDIS: {str(e)}",
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
                sucursal = Sucursal.objects.create(
                    name=sucursal_name.strip(),
                    bpl_id=int(bpl_id)
                )
                
                # Resetear errores que coincidan con origen
                Salida.objects.filter(
                    normalize_status="error",
                    nombre_sucursal_origen__iexact=sucursal_name
                ).update(
                    normalize_status="pending",
                    normalize_notes="",
                    normalized_at=None
                )
                
                # Resetear errores que coincidan con destino (nombre_sucursal_destino)
                Salida.objects.filter(
                    normalize_status="error",
                    nombre_sucursal_destino__iexact=sucursal_name
                ).update(
                    normalize_status="pending",
                    normalize_notes="",
                    normalized_at=None
                )
                
                # Resetear errores que coincidan con destino (sucursal_destino_propuesto)
                Salida.objects.filter(
                    normalize_status="error",
                    sucursal_destino_propuesto__iexact=sucursal_name
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
                    # Actualizar tanto nombre_sucursal_destino como sucursal_destino_propuesto
                    Salida.objects.filter(
                        nombre_sucursal_destino__iexact=original_name
                    ).update(
                        nombre_sucursal_destino=target_name,
                        normalize_status="pending",
                        normalize_notes="",
                        normalized_at=None
                    )
                    Salida.objects.filter(
                        sucursal_destino_propuesto__iexact=original_name
                    ).update(
                        sucursal_destino_propuesto=target_name,
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
    
    def _ignore_errors(self, request):
        error_ids = request.POST.getlist("error_ids")
        
        try:
            with transaction.atomic():
                Salida.objects.filter(id__in=error_ids).update(
                    normalize_status="ignored",
                    normalize_notes="Ignorado manualmente"
                )
                
                return redirect("salida_error_resolver")
        except Exception as e:
            return render(request, self.template_name, {
                "error": f"Error al ignorar: {str(e)}",
            })
