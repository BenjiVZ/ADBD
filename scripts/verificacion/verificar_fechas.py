import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ADB.settings')
django.setup()

from main.models import PlanificacionNormalizada, SalidaNormalizada
import datetime

# Fecha que estás usando
fecha = datetime.date(2026, 1, 13)

print("=" * 80)
print(f"VERIFICANDO DATOS PARA FECHA: {fecha}")
print("=" * 80)

# Planificación
plan_count = PlanificacionNormalizada.objects.filter(plan_month=fecha).count()
print(f"\n📋 Planificaciones para {fecha}: {plan_count}")

if plan_count > 0:
    print("\nPrimeros 5 registros de Planificación:")
    for p in PlanificacionNormalizada.objects.filter(plan_month=fecha).select_related('cedis_origen', 'sucursal', 'product')[:5]:
        print(f"   - CEDIS: {p.cedis_origen.origin if p.cedis_origen else 'N/A'}")
        print(f"     Destino: {p.sucursal.name if p.sucursal else 'N/A'}")
        print(f"     Producto: {p.product.code if p.product else 'N/A'}")
        print(f"     Cantidad: {p.a_despachar_total}")
        print()

# Salidas
sal_count = SalidaNormalizada.objects.filter(fecha_salida=fecha).count()
print(f"\n📦 Salidas para {fecha}: {sal_count}")

if sal_count > 0:
    print("\nPrimeros 5 registros de Salidas:")
    for s in SalidaNormalizada.objects.filter(fecha_salida=fecha).select_related('cedis_origen', 'sucursal_destino', 'product')[:5]:
        print(f"   - CEDIS: {s.cedis_origen.origin if s.cedis_origen else 'N/A'}")
        print(f"     Destino: {s.sucursal_destino.name if s.sucursal_destino else 'N/A'}")
        print(f"     Producto: {s.product.code if s.product else 'N/A'}")
        print(f"     Cantidad: {s.cantidad}")
        print()

# Fechas disponibles
print("\n📅 Fechas disponibles en Planificación:")
plan_dates = PlanificacionNormalizada.objects.values_list('plan_month', flat=True).distinct().order_by('-plan_month')[:5]
for d in plan_dates:
    count = PlanificacionNormalizada.objects.filter(plan_month=d).count()
    print(f"   - {d}: {count} registros")

print("\n📅 Fechas disponibles en Salidas:")
sal_dates = SalidaNormalizada.objects.values_list('fecha_salida', flat=True).distinct().order_by('-fecha_salida')[:5]
for d in sal_dates:
    count = SalidaNormalizada.objects.filter(fecha_salida=d).count()
    print(f"   - {d}: {count} registros")
