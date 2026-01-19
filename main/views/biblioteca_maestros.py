"""
Vista para crear la biblioteca de CEDIS y Sucursales desde los datos crudos.
El sistema analiza los Excel subidos y pregunta al usuario cuáles son los nombres oficiales.
Los mapeos se guardan en tablas separadas (MapeoCedis, MapeoSucursal) SIN modificar los datos originales.
"""
from django.shortcuts import render, redirect
from django.views import View
from main.models import Planificacion, Salida, Cendis, Sucursal, MapeoCedis, MapeoSucursal


class BibliotecaCedisView(View):
    """
    Analiza los datos crudos para encontrar todos los nombres de CEDIS únicos
    y permite al usuario definir cuáles son oficiales o crear mapeos.
    """
    template_name = "biblioteca_cedis.html"

    def get(self, request):
        # Obtener todos los nombres únicos de CEDIS desde los datos crudos
        nombres_planificacion = set(
            Planificacion.objects.exclude(cendis__isnull=True)
            .exclude(cendis="")
            .values_list("cendis", flat=True)
            .distinct()
        )
        
        nombres_salida = set(
            Salida.objects.exclude(nombre_almacen_origen__isnull=True)
            .exclude(nombre_almacen_origen="")
            .values_list("nombre_almacen_origen", flat=True)
            .distinct()
        )
        
        # Unir todos los nombres encontrados
        todos_nombres = nombres_planificacion | nombres_salida
        
        # Obtener CEDIS ya registrados (oficiales)
        cedis_oficiales = {c.origin: c for c in Cendis.objects.all()}
        # También crear mapeo por ID y código para detectar IDs numéricos
        cedis_por_id = {str(c.id): c for c in Cendis.objects.all()}
        cedis_por_code = {c.code: c for c in Cendis.objects.all() if c.code}
        
        # Obtener mapeos existentes
        mapeos_existentes = {m.nombre_crudo: m for m in MapeoCedis.objects.select_related("cedis_oficial").all()}
        
        # Clasificar: oficiales vs mapeados vs sin registrar
        nombres_info = []
        for nombre in sorted(todos_nombres):
            # 1. Verificar si coincide por nombre exacto (origin)
            if nombre in cedis_oficiales:
                nombres_info.append({
                    "nombre": nombre,
                    "estado": "oficial",
                    "cedis": cedis_oficiales[nombre],
                    "mapeo": None,
                    "en_planificacion": nombre in nombres_planificacion,
                    "en_salida": nombre in nombres_salida,
                    "es_id": False,
                })
            # 2. Verificar si es un ID numérico que coincide con un CEDIS ID
            elif nombre.strip().isdigit() and nombre.strip() in cedis_por_id:
                cedis_encontrado = cedis_por_id[nombre.strip()]
                nombres_info.append({
                    "nombre": nombre,
                    "estado": "oficial",
                    "cedis": cedis_encontrado,
                    "mapeo": None,
                    "en_planificacion": nombre in nombres_planificacion,
                    "en_salida": nombre in nombres_salida,
                    "es_id": True,  # Marcar que se encontró por ID
                })
            # 3. Verificar si coincide por código
            elif nombre in cedis_por_code:
                nombres_info.append({
                    "nombre": nombre,
                    "estado": "oficial",
                    "cedis": cedis_por_code[nombre],
                    "mapeo": None,
                    "en_planificacion": nombre in nombres_planificacion,
                    "en_salida": nombre in nombres_salida,
                    "es_id": False,
                })
            # 4. Verificar si ya tiene un mapeo guardado
            elif nombre in mapeos_existentes:
                nombres_info.append({
                    "nombre": nombre,
                    "estado": "mapeado",
                    "cedis": mapeos_existentes[nombre].cedis_oficial,
                    "mapeo": mapeos_existentes[nombre],
                    "en_planificacion": nombre in nombres_planificacion,
                    "en_salida": nombre in nombres_salida,
                    "es_id": False,
                })
            # 5. Sin registrar ni mapear
            else:
                nombres_info.append({
                    "nombre": nombre,
                    "estado": "sin_registrar",
                    "cedis": None,
                    "mapeo": None,
                    "en_planificacion": nombre in nombres_planificacion,
                    "en_salida": nombre in nombres_salida,
                    "es_id": nombre.strip().isdigit(),  # Marcar si parece un ID
                })
        
        # Contar
        sin_registrar = [n for n in nombres_info if n["estado"] == "sin_registrar"]
        mapeados = [n for n in nombres_info if n["estado"] == "mapeado"]
        oficiales = [n for n in nombres_info if n["estado"] == "oficial"]
        
        context = {
            "nombres_info": nombres_info,
            "sin_registrar": sin_registrar,
            "mapeados": mapeados,
            "oficiales": oficiales,
            "cedis_list": Cendis.objects.all().order_by("origin"),
            "total_encontrados": len(todos_nombres),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        action = request.POST.get("action")
        
        if action == "crear_oficial":
            # Crear un nuevo CEDIS oficial
            nombre = request.POST.get("nombre", "").strip()
            codigo = request.POST.get("codigo", "").strip()
            if nombre:
                Cendis.objects.get_or_create(
                    origin=nombre,
                    defaults={"code": codigo or "0000"}
                )
        
        elif action == "mapear":
            # Crear un mapeo (SIN modificar datos originales)
            nombre_crudo = request.POST.get("nombre_crudo", "").strip()
            cedis_oficial_id = request.POST.get("cedis_oficial_id")
            
            if nombre_crudo and cedis_oficial_id:
                try:
                    cedis_oficial = Cendis.objects.get(id=cedis_oficial_id)
                    # Guardar el mapeo en la tabla de mapeos
                    MapeoCedis.objects.update_or_create(
                        nombre_crudo=nombre_crudo,
                        defaults={"cedis_oficial": cedis_oficial}
                    )
                except Cendis.DoesNotExist:
                    pass
        
        elif action == "eliminar_mapeo":
            mapeo_id = request.POST.get("mapeo_id")
            if mapeo_id:
                MapeoCedis.objects.filter(id=mapeo_id).delete()
        
        elif action == "eliminar_cedis":
            cedis_id = request.POST.get("cedis_id")
            if cedis_id:
                Cendis.objects.filter(id=cedis_id).delete()
        
        elif action == "crear_todos":
            # Crear todos los nombres sin registrar como oficiales
            nombres = request.POST.getlist("nombres[]")
            for nombre in nombres:
                if nombre.strip():
                    Cendis.objects.get_or_create(
                        origin=nombre.strip(),
                        defaults={"code": "0000"}
                    )
        
        return redirect("biblioteca_cedis")


class BibliotecaSucursalesView(View):
    """
    Analiza los datos crudos para encontrar todos los nombres de Sucursales únicos
    y permite al usuario definir cuáles son oficiales o crear mapeos.
    Los mapeos se guardan en tablas separadas SIN modificar los datos originales.
    """
    template_name = "biblioteca_sucursales.html"

    def get(self, request):
        # Obtener todos los nombres únicos de Sucursales desde Planificacion
        nombres_planificacion = set(
            Planificacion.objects.exclude(sucursal__isnull=True)
            .exclude(sucursal="")
            .values_list("sucursal", flat=True)
            .distinct()
        )
        
        # También de Salida (nombre_sucursal_destino)
        nombres_salida_destino = set(
            Salida.objects.exclude(nombre_sucursal_destino__isnull=True)
            .exclude(nombre_sucursal_destino="")
            .values_list("nombre_sucursal_destino", flat=True)
            .distinct()
        )
        
        # También de Salida (sucursal_destino_propuesto) - NUEVO
        nombres_salida_propuesto = set(
            Salida.objects.exclude(sucursal_destino_propuesto__isnull=True)
            .exclude(sucursal_destino_propuesto="")
            .values_list("sucursal_destino_propuesto", flat=True)
            .distinct()
        )
        
        # Unir todos los nombres encontrados
        todos_nombres = nombres_planificacion | nombres_salida_destino | nombres_salida_propuesto
        
        # Obtener Sucursales ya registradas (oficiales)
        sucursales_oficiales = {s.name: s for s in Sucursal.objects.all()}
        # También crear mapeo por BPL_ID para detectar IDs numéricos
        sucursales_por_bpl_id = {str(s.bpl_id): s for s in Sucursal.objects.all()}
        
        # Obtener mapeos existentes
        mapeos_existentes = {m.nombre_crudo: m for m in MapeoSucursal.objects.select_related("sucursal_oficial").all()}
        
        # Clasificar: oficiales vs mapeados vs sin registrar
        nombres_info = []
        for nombre in sorted(todos_nombres):
            # 1. Verificar si coincide por nombre exacto
            if nombre in sucursales_oficiales:
                nombres_info.append({
                    "nombre": nombre,
                    "estado": "oficial",
                    "sucursal": sucursales_oficiales[nombre],
                    "mapeo": None,
                    "en_planificacion": nombre in nombres_planificacion,
                    "en_salida": nombre in nombres_salida_destino or nombre in nombres_salida_propuesto,
                    "es_id": False,
                })
            # 2. Verificar si es un ID numérico que coincide con un BPL_ID
            elif nombre.strip().isdigit() and nombre.strip() in sucursales_por_bpl_id:
                sucursal_encontrada = sucursales_por_bpl_id[nombre.strip()]
                nombres_info.append({
                    "nombre": nombre,
                    "estado": "oficial",
                    "sucursal": sucursal_encontrada,
                    "mapeo": None,
                    "en_planificacion": nombre in nombres_planificacion,
                    "en_salida": nombre in nombres_salida_destino or nombre in nombres_salida_propuesto,
                    "es_id": True,  # Marcar que se encontró por ID
                })
            # 3. Verificar si ya tiene un mapeo guardado
            elif nombre in mapeos_existentes:
                nombres_info.append({
                    "nombre": nombre,
                    "estado": "mapeado",
                    "sucursal": mapeos_existentes[nombre].sucursal_oficial,
                    "mapeo": mapeos_existentes[nombre],
                    "en_planificacion": nombre in nombres_planificacion,
                    "en_salida": nombre in nombres_salida_destino or nombre in nombres_salida_propuesto,
                    "es_id": False,
                })
            # 4. Sin registrar ni mapear
            else:
                nombres_info.append({
                    "nombre": nombre,
                    "estado": "sin_registrar",
                    "sucursal": None,
                    "mapeo": None,
                    "en_planificacion": nombre in nombres_planificacion,
                    "en_salida": nombre in nombres_salida_destino or nombre in nombres_salida_propuesto,
                    "es_id": nombre.strip().isdigit(),  # Marcar si parece un ID
                })
        
        # Contar
        sin_registrar = [n for n in nombres_info if n["estado"] == "sin_registrar"]
        mapeados = [n for n in nombres_info if n["estado"] == "mapeado"]
        oficiales = [n for n in nombres_info if n["estado"] == "oficial"]
        
        context = {
            "nombres_info": nombres_info,
            "sin_registrar": sin_registrar,
            "mapeados": mapeados,
            "oficiales": oficiales,
            "sucursales_list": Sucursal.objects.all().order_by("name"),
            "total_encontrados": len(todos_nombres),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        action = request.POST.get("action")
        
        if action == "crear_oficial":
            # Crear una nueva Sucursal oficial
            nombre = request.POST.get("nombre", "").strip()
            bpl_id = request.POST.get("bpl_id", "").strip()
            if nombre:
                Sucursal.objects.get_or_create(
                    name=nombre,
                    defaults={"bpl_id": bpl_id or "0"}
                )
        
        elif action == "mapear":
            # Crear un mapeo (SIN modificar datos originales)
            nombre_crudo = request.POST.get("nombre_crudo", "").strip()
            sucursal_oficial_id = request.POST.get("sucursal_oficial_id")
            
            if nombre_crudo and sucursal_oficial_id:
                try:
                    sucursal_oficial = Sucursal.objects.get(id=sucursal_oficial_id)
                    # Guardar el mapeo en la tabla de mapeos
                    MapeoSucursal.objects.update_or_create(
                        nombre_crudo=nombre_crudo,
                        defaults={"sucursal_oficial": sucursal_oficial}
                    )
                except Sucursal.DoesNotExist:
                    pass
        
        elif action == "eliminar_mapeo":
            mapeo_id = request.POST.get("mapeo_id")
            if mapeo_id:
                MapeoSucursal.objects.filter(id=mapeo_id).delete()
        
        elif action == "eliminar_sucursal":
            sucursal_id = request.POST.get("sucursal_id")
            if sucursal_id:
                Sucursal.objects.filter(id=sucursal_id).delete()
        
        elif action == "crear_todos":
            # Crear todos los nombres sin registrar como oficiales
            nombres = request.POST.getlist("nombres[]")
            for nombre in nombres:
                if nombre.strip():
                    Sucursal.objects.get_or_create(
                        name=nombre.strip(),
                        defaults={"bpl_id": "0"}
                    )
        
        return redirect("biblioteca_sucursales")
