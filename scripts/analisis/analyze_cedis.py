import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ADB.settings')
django.setup()

from main.models import Planificacion, Salida, Sucursal
from collections import Counter

print('=' * 80)
print('🔍 ANÁLISIS DE CAMPOS cendis Y CEDIS')
print('=' * 80)

# CEDIS registrados en la BD
print('\n📚 CEDIS EN BASE DE DATOS:')
sucursales_db = list(Sucursal.objects.values_list('name', flat=True).order_by('name'))
sucursales_map = {s.lower(): s for s in sucursales_db}
print(f'Total: {len(sucursales_db)}')
for suc in sucursales_db[:10]:
    print(f'  • {suc}')
if len(sucursales_db) > 10:
    print(f'  ... y {len(sucursales_db) - 10} más')

# Campo cendis en Planificacion
print('\n' + '-' * 80)
print('\n📋 PLANIFICACION - Campo cendis:')
origenes_plan = Planificacion.objects.values_list('cendis', flat=True).distinct()
counter_plan = Counter([o.strip() for o in origenes_plan if o and o.strip()])

print(f'\nTotal únicos en cendis: {len(counter_plan)}')
print('\nTop 20:')
for origen, count in sorted(counter_plan.items(), key=lambda x: -x[1])[:20]:
    existe = origen.lower() in sucursales_map
    status = '✅' if existe else '❌'
    print(f'  {status} "{origen}" ({count} registros)')

# Campo nombre_sucursal_origen en Salida
print('\n' + '-' * 80)
print('\n🚚 SALIDA - Campo nombre_sucursal_origen:')
origenes_salida = Salida.objects.values_list('nombre_sucursal_origen', flat=True).distinct()
counter_salida = Counter([o.strip() for o in origenes_salida if o and o.strip()])

print(f'\nTotal únicos en nombre_sucursal_origen: {len(counter_salida)}')
print('\nTodos:')
for origen, count in sorted(counter_salida.items(), key=lambda x: -x[1]):
    existe = origen.lower() in sucursales_map
    status = '✅' if existe else '❌'
    
    sugerencias = []
    if not existe:
        import difflib
        matches = difflib.get_close_matches(origen.lower(), sucursales_map.keys(), n=2, cutoff=0.6)
        sugerencias = [sucursales_map[m] for m in matches]
    
    print(f'  {status} "{origen}" ({count} salidas)')
    if sugerencias:
        print(f'      💡 Sugerencias: {", ".join(sugerencias)}')

# Campo nombre_sucursal_destino en Salida
print('\n' + '-' * 80)
print('\n📍 SALIDA - Campo nombre_sucursal_destino:')
destinos_salida = Salida.objects.values_list('nombre_sucursal_destino', flat=True).distinct()
counter_destino = Counter([d.strip() for d in destinos_salida if d and d.strip()])

print(f'\nTotal únicos en nombre_sucursal_destino: {len(counter_destino)}')
print('\nTop 30:')
for destino, count in sorted(counter_destino.items(), key=lambda x: -x[1])[:30]:
    existe = destino.lower() in sucursales_map
    status = '✅' if existe else '❌'
    
    sugerencias = []
    if not existe:
        import difflib
        matches = difflib.get_close_matches(destino.lower(), sucursales_map.keys(), n=2, cutoff=0.6)
        sugerencias = [sucursales_map[m] for m in matches]
    
    print(f'  {status} "{destino}" ({count} salidas)')
    if sugerencias:
        print(f'      💡 Sugerencias: {", ".join(sugerencias)}')

print('\n' + '=' * 80)
print('\n💡 CONCLUSIÓN:')
print('   Los campos cendis, nombre_sucursal_origen y nombre_sucursal_destino')
print('   deben coincidir con los nombres exactos en la tabla Sucursal.')
print('\n   Usa el sistema de resolución de errores para mapearlos:')
print('   • http://localhost:2222/planificacion/errores/')
print('   • http://localhost:2222/salidas/errores/')
print('=' * 80)
