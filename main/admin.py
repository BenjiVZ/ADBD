from django.contrib import admin

from .models import (
    Planificacion,
    PlanificacionNormalizada,
    PlanningBatch,
    PlanningEntry,
    Prioridad,
    Product,
    Pvp,
    Salida,
    SalidaNormalizada,
    Cendis,
    GerenteRegional,
    Region,
    Sucursal,
    MapeoCedis,
    MapeoSucursal,
    IgnorarCedis,
    IgnorarSucursal,
)


# =====================================================
# SECCIÓN: SALIDAS (Admin Principal - Ocultas)
# =====================================================

@admin.register(Salida)
class SalidaAdmin(admin.ModelAdmin):
    list_display = (
        "salida",
        "fecha_salida",
        "sku",
        "descripcion",
        "cantidad",
        "nombre_sucursal_origen",
        "nombre_sucursal_destino",
        "normalize_status",
    )
    search_fields = ("salida", "sku", "descripcion")
    list_filter = ("fecha_salida", "normalize_status")
    ordering = ("-fecha_salida", "-id")
    
    def get_model_perms(self, request):
        return {}  # Ocultar de la sección Main


@admin.register(SalidaNormalizada)
class SalidaNormalizadaAdmin(admin.ModelAdmin):
    list_display = (
        "salida",
        "fecha_salida",
        "sku",
        "cedis_origen",
        "sucursal_destino",
        "cantidad",
        "product",
    )
    search_fields = ("salida", "sku", "descripcion")
    list_filter = ("fecha_salida", "cedis_origen", "sucursal_destino")
    ordering = ("-fecha_salida", "salida")
    
    def get_model_perms(self, request):
        return {}  # Ocultar de la sección Main


# Clases para Admin Site de Salidas (SIN get_model_perms)
class SalidaSeccionAdmin(admin.ModelAdmin):
    list_display = (
        "salida",
        "fecha_salida",
        "sku",
        "descripcion",
        "cantidad",
        "nombre_sucursal_origen",
        "nombre_sucursal_destino",
        "normalize_status",
    )
    search_fields = ("salida", "sku", "descripcion")
    list_filter = ("fecha_salida", "normalize_status")
    ordering = ("-fecha_salida", "-id")


class SalidaNormalizadaSeccionAdmin(admin.ModelAdmin):
    list_display = (
        "salida",
        "fecha_salida",
        "sku",
        "cedis_origen",
        "sucursal_destino",
        "cantidad",
        "product",
    )
    search_fields = ("salida", "sku", "descripcion")
    list_filter = ("fecha_salida", "cedis_origen", "sucursal_destino")
    ordering = ("-fecha_salida", "salida")


# =====================================================
# SECCIÓN: PLANIFICACIONES (Admin Principal - Ocultas)
# =====================================================

@admin.register(Planificacion)
class PlanificacionAdmin(admin.ModelAdmin):
    list_display = (
        "plan_month",
        "tipo_carga",
        "item_code",
        "item_name",
        "sucursal",
        "cendis",
        "a_despachar_total",
        "normalize_status",
    )
    search_fields = ("item_code", "item_name", "sucursal", "cendis")
    list_filter = ("plan_month", "tipo_carga", "normalize_status")
    ordering = ("-plan_month", "item_code")
    
    def get_model_perms(self, request):
        return {}  # Ocultar de la sección Main


@admin.register(PlanificacionNormalizada)
class PlanificacionNormalizadaAdmin(admin.ModelAdmin):
    list_display = (
        "plan_month",
        "item_code",
        "item_name",
        "sucursal",
        "product",
        "a_despachar_total",
    )
    search_fields = ("item_code", "item_name", "sucursal__name")
    list_filter = ("plan_month", "sucursal")
    ordering = ("-plan_month", "item_code")
    
    def get_model_perms(self, request):
        return {}  # Ocultar de la sección Main


@admin.register(PlanningBatch)
class PlanningBatchAdmin(admin.ModelAdmin):
    list_display = ("plan_date", "sheet_name", "source_filename", "created_at")
    search_fields = ("sheet_name", "source_filename")
    list_filter = ("plan_date",)
    ordering = ("-plan_date", "-id")
    
    def get_model_perms(self, request):
        return {}  # Ocultar de la sección Main


@admin.register(PlanningEntry)
class PlanningEntryAdmin(admin.ModelAdmin):
    list_display = (
        "batch",
        "item_code",
        "item_name",
        "sucursal",
        "a_despachar_total",
        "stock_tienda",
        "stock_cedis",
    )
    search_fields = ("item_code", "item_name", "sucursal")
    list_filter = ("batch__plan_date", "necesidad_urgente")
    ordering = ("batch", "item_code")
    
    def get_model_perms(self, request):
        return {}  # Ocultar de la sección Main


# Clases para Admin Site de Planificaciones (SIN get_model_perms)
class PlanificacionSeccionAdmin(admin.ModelAdmin):
    list_display = (
        "plan_month",
        "tipo_carga",
        "item_code",
        "item_name",
        "sucursal",
        "cendis",
        "a_despachar_total",
        "normalize_status",
    )
    search_fields = ("item_code", "item_name", "sucursal", "cendis")
    list_filter = ("plan_month", "tipo_carga", "normalize_status")
    ordering = ("-plan_month", "item_code")


class PlanificacionNormalizadaSeccionAdmin(admin.ModelAdmin):
    list_display = (
        "plan_month",
        "item_code",
        "item_name",
        "sucursal",
        "product",
        "a_despachar_total",
    )
    search_fields = ("item_code", "item_name", "sucursal__name")
    list_filter = ("plan_month", "sucursal")
    ordering = ("-plan_month", "item_code")


class PlanningBatchSeccionAdmin(admin.ModelAdmin):
    list_display = ("plan_date", "sheet_name", "source_filename", "created_at")
    search_fields = ("sheet_name", "source_filename")
    list_filter = ("plan_date",)
    ordering = ("-plan_date", "-id")


class PlanningEntrySeccionAdmin(admin.ModelAdmin):
    list_display = (
        "batch",
        "item_code",
        "item_name",
        "sucursal",
        "a_despachar_total",
        "stock_tienda",
        "stock_cedis",
    )
    search_fields = ("item_code", "item_name", "sucursal")
    list_filter = ("batch__plan_date", "necesidad_urgente")
    ordering = ("batch", "item_code")


# =====================================================
# SECCIÓN: MAESTROS (Admin Principal)
# =====================================================

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "group", "manufacturer", "category", "subcategory", "size")
    search_fields = ("code", "name", "group", "manufacturer", "category", "subcategory", "size")
    list_filter = ("group", "manufacturer", "category", "subcategory")
    ordering = ("code",)


@admin.register(Pvp)
class PvpAdmin(admin.ModelAdmin):
    list_display = ("sku", "description", "price", "product")
    search_fields = ("sku", "description", "product__code", "product__name")
    list_filter = ("product",)
    ordering = ("sku",)


@admin.register(Cendis)
class CendisAdmin(admin.ModelAdmin):
    list_display = ("code", "origin")
    search_fields = ("code", "origin")
    ordering = ("code",)


@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display = ("bpl_id", "name", "region", "gerente")
    search_fields = ("bpl_id", "name", "region__name", "gerente__name")
    list_filter = ("gerente", "region")
    ordering = ("gerente", "region", "name")


@admin.register(GerenteRegional)
class GerenteRegionalAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "telefono", "created_at")
    search_fields = ("name", "email")
    ordering = ("name",)


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ("name", "gerente", "created_at")
    search_fields = ("name", "gerente__name")
    list_filter = ("gerente",)
    ordering = ("name",)


@admin.register(Prioridad)
class PrioridadAdmin(admin.ModelAdmin):
    list_display = ("name", "sort_order")
    search_fields = ("name",)
    ordering = ("sort_order", "name")


# =====================================================
# SECCIÓN: MAPEOS E IGNORADOS
# =====================================================

@admin.register(MapeoCedis)
class MapeoCedisAdmin(admin.ModelAdmin):
    list_display = ("nombre_crudo", "cedis_oficial", "created_at")
    search_fields = ("nombre_crudo", "cedis_oficial__origin")
    list_filter = ("cedis_oficial",)
    ordering = ("nombre_crudo",)


@admin.register(MapeoSucursal)
class MapeoSucursalAdmin(admin.ModelAdmin):
    list_display = ("nombre_crudo", "sucursal_oficial", "created_at")
    search_fields = ("nombre_crudo", "sucursal_oficial__name")
    list_filter = ("sucursal_oficial",)
    ordering = ("nombre_crudo",)


@admin.register(IgnorarCedis)
class IgnorarCedisAdmin(admin.ModelAdmin):
    list_display = ("nombre_crudo", "razon", "created_at")
    search_fields = ("nombre_crudo", "razon")
    ordering = ("nombre_crudo",)


@admin.register(IgnorarSucursal)
class IgnorarSucursalAdmin(admin.ModelAdmin):
    list_display = ("nombre_crudo", "razon", "created_at")
    search_fields = ("nombre_crudo", "razon")
    ordering = ("nombre_crudo",)


# =====================================================
# CREAR ADMIN SITE PERSONALIZADO PARA SECCIONES
# =====================================================

class SalidasAdminSite(admin.AdminSite):
    site_header = "📦 Gestión de Salidas"
    site_title = "Salidas"
    index_title = "Administración de Salidas"


class PlanificacionesAdminSite(admin.AdminSite):
    site_header = "📋 Gestión de Planificaciones"
    site_title = "Planificaciones"
    index_title = "Administración de Planificaciones"


# Instancias de admin sites
salidas_admin = SalidasAdminSite(name='salidas_admin')
planificaciones_admin = PlanificacionesAdminSite(name='planificaciones_admin')

# =====================================================
# REGISTRAR MODELOS EN ADMIN SITE DE SALIDAS
# =====================================================
salidas_admin.register(Salida, SalidaSeccionAdmin)
salidas_admin.register(SalidaNormalizada, SalidaNormalizadaSeccionAdmin)
salidas_admin.register(Cendis, CendisAdmin)
salidas_admin.register(Sucursal, SucursalAdmin)
salidas_admin.register(Product, ProductAdmin)
salidas_admin.register(MapeoCedis, MapeoCedisAdmin)
salidas_admin.register(MapeoSucursal, MapeoSucursalAdmin)
salidas_admin.register(IgnorarCedis, IgnorarCedisAdmin)
salidas_admin.register(IgnorarSucursal, IgnorarSucursalAdmin)

# =====================================================
# REGISTRAR MODELOS EN ADMIN SITE DE PLANIFICACIONES
# =====================================================
planificaciones_admin.register(Planificacion, PlanificacionSeccionAdmin)
planificaciones_admin.register(PlanificacionNormalizada, PlanificacionNormalizadaSeccionAdmin)
planificaciones_admin.register(PlanningBatch, PlanningBatchSeccionAdmin)
planificaciones_admin.register(PlanningEntry, PlanningEntrySeccionAdmin)
planificaciones_admin.register(Cendis, CendisAdmin)
planificaciones_admin.register(Sucursal, SucursalAdmin)
planificaciones_admin.register(Product, ProductAdmin)
planificaciones_admin.register(Prioridad, PrioridadAdmin)
planificaciones_admin.register(MapeoCedis, MapeoCedisAdmin)
planificaciones_admin.register(MapeoSucursal, MapeoSucursalAdmin)
planificaciones_admin.register(IgnorarCedis, IgnorarCedisAdmin)
planificaciones_admin.register(IgnorarSucursal, IgnorarSucursalAdmin)
