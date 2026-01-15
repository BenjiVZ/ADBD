import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ADB.settings')
django.setup()

from main.models import PlanificacionNormalizada, SalidaNormalizada

print('=' * 60)
print('DATOS NORMALIZADOS DISPONIBLES')
print('=' * 60)

# Planificaciones
plan_count = PlanificacionNormalizada.objects.count()
print(f'\n📋 Total Planificaciones Normalizadas: {plan_count}')

if plan_count > 0:
    print('\n📅 Fechas disponibles en Planificación:')
    for fecha in PlanificacionNormalizada.objects.values_list('plan_month', flat=True).distinct().order_by('-plan_month')[:5]:
        count = PlanificacionNormalizada.objects.filter(plan_month=fecha).count()
        print(f'  - {fecha} ({count} registros)')
    
    print('\n📦 Ejemplo de planificaciones:')
    for p in PlanificacionNormalizada.objects.select_related('product', 'sucursal').all()[:5]:
        sucursal_name = p.sucursal.name if p.sucursal else "N/A"
        product_name = p.product.name if p.product else "N/A"
        product_group = p.product.group if p.product and p.product.group else "SIN GRUPO"
        print(f'  {p.plan_month} | {sucursal_name} | {product_name} ({product_group}) | Qty: {p.a_despachar_total}')

print('\n' + '-' * 60)

# Salidas
salida_count = SalidaNormalizada.objects.count()
print(f'\n🚚 Total Salidas Normalizadas: {salida_count}')

if salida_count > 0:
    print('\n📅 Fechas disponibles en Salidas:')
    for fecha in SalidaNormalizada.objects.values_list('fecha_salida', flat=True).distinct().order_by('-fecha_salida')[:5]:
        count = SalidaNormalizada.objects.filter(fecha_salida=fecha).count()
        print(f'  - {fecha} ({count} registros)')
    
    print('\n📦 Ejemplo de salidas:')
    for s in SalidaNormalizada.objects.select_related('product', 'sucursal_origen', 'sucursal_destino').all()[:5]:
        origen_name = s.sucursal_origen.name if s.sucursal_origen else "N/A"
        destino_name = s.sucursal_destino.name if s.sucursal_destino else "N/A"
        product_name = s.product.name if s.product else "N/A"
        product_group = s.product.group if s.product and s.product.group else "SIN GRUPO"
        print(f'  {s.fecha_salida} | {origen_name} → {destino_name} | {product_name} ({product_group}) | Qty: {s.cantidad}')

print('\n' + '=' * 60)
print('\n💡 Si no hay datos, necesitas normalizar desde:')
print('   http://localhost:2222/planificacion/normalizar/')
print('   http://localhost:2222/salidas/normalizar/')
print('\n📊 Luego revisa el tablero en:')
print('   http://localhost:2222/tablero/normalizado/')
print('=' * 60)
