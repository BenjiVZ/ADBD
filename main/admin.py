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
    Sucursal,
)


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


@admin.register(PlanningBatch)
class PlanningBatchAdmin(admin.ModelAdmin):
    list_display = ("plan_date", "sheet_name", "source_filename", "created_at")
    search_fields = ("sheet_name", "source_filename")
    list_filter = ("plan_date",)
    ordering = ("-plan_date", "-id")


@admin.register(PlanningEntry)
class PlanningEntryAdmin(admin.ModelAdmin):
    list_display = (
        "batch",
        "external_id",
        "item_code",
        "item_name",
        "sucursal",
        "a_despachar_total",
        "stock_tienda",
        "stock_cedis",
        "necesidad_urgente",
    )
    search_fields = (
        "batch__plan_date",
        "batch__sheet_name",
        "external_id",
        "item_code",
        "item_name",
        "sucursal",
    )
    list_filter = ("batch__plan_date", "necesidad_urgente", "no_planificar")
    ordering = ("batch", "item_code")


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
        "normalized_at",
    )
    search_fields = (
        "salida",
        "sku",
        "descripcion",
        "nombre_sucursal_origen",
        "nombre_sucursal_destino",
        "entrada",
        "normalize_notes",
    )
    list_filter = ("fecha_salida", "fecha_entrada", "normalize_status")
    ordering = ("-fecha_salida", "-id")


@admin.register(Prioridad)
class PrioridadAdmin(admin.ModelAdmin):
    list_display = ("name", "sort_order")
    search_fields = ("name",)
    ordering = ("sort_order", "name")


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
        "normalized_at",
    )
    search_fields = ("item_code", "item_name", "sucursal", "cendis", "normalize_notes")
    list_filter = ("plan_month", "tipo_carga", "normalize_status")
    ordering = ("-plan_month", "item_code")


@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display = ("bpl_id", "name")
    search_fields = ("bpl_id", "name")
    ordering = ("name",)


@admin.register(PlanificacionNormalizada)
class PlanificacionNormalizadaAdmin(admin.ModelAdmin):
    list_display = (
        "plan_month",
        "item_code",
        "item_name",
        "sucursal",
        "product",
        "a_despachar_total",
        "updated_at",
    )
    search_fields = ("item_code", "item_name", "sucursal__name", "product__code", "product__name")
    list_filter = ("plan_month", "sucursal")
    ordering = ("-plan_month", "item_code")


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
        "updated_at",
    )
    search_fields = (
        "salida",
        "sku",
        "descripcion",
        "cedis_origen__origin",
        "sucursal_destino__name",
        "product__code",
        "product__name",
    )
    list_filter = ("fecha_salida", "cedis_origen", "sucursal_destino")
    ordering = ("-fecha_salida", "salida")
