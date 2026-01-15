import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ADB.settings')
django.setup()

from main.models import Salida, Sucursal
from collections import Counter

print('=' * 80)
print('🔍 ANÁLISIS DE INCONSISTENCIAS EN NOMBRES DE CEDIS')
print('=' * 80)

# Obtener todos los nombres de sucursales en la tabla maestra
print('\n📚 CEDIS REGISTRADOS EN LA BASE DE DATOS (Sucursal):')
sucursales_db = list(Sucursal.objects.values_list('name', flat=True).order_by('name'))
for i, suc in enumerate(sucursales_db, 1):
    print(f'  {i:2}. {suc}')

# Obtener todos los orígenes únicos de las salidas crudas
print('\n' + '-' * 80)
print('\n🚚 CEDIS ORIGEN EN SALIDAS (datos crudos):')
origenes_raw = Salida.objects.values_list('nombre_sucursal_origen', flat=True).distinct()
origenes_counter = Counter([o.strip() for o in origenes_raw if o and o.strip()])

print(f'\nTotal de orígenes únicos: {len(origenes_counter)}')
for origen, count in origenes_counter.most_common():
    # Verificar si existe en la BD
    existe = Sucursal.objects.filter(name__iexact=origen).exists()
    status = '✅' if existe else '❌'
    print(f'  {status} "{origen}" ({count} salidas)')

# Obtener todos los destinos únicos de las salidas crudas
print('\n' + '-' * 80)
print('\n📍 CEDIS DESTINO EN SALIDAS (datos crudos):')
destinos_raw = Salida.objects.values_list('nombre_sucursal_destino', flat=True).distinct()
destinos_counter = Counter([d.strip() for d in destinos_raw if d and d.strip()])

print(f'\nTotal de destinos únicos: {len(destinos_counter)}')
for destino, count in destinos_counter.most_common(20):  # Mostrar top 20
    # Verificar si existe en la BD
    existe = Sucursal.objects.filter(name__iexact=destino).exists()
    status = '✅' if existe else '❌'
    print(f'  {status} "{destino}" ({count} salidas)')

# Detectar inconsistencias
print('\n' + '=' * 80)
print('\n⚠️  CEDIS QUE NECESITAN MAPEO:')
print('\nEstos nombres aparecen en salidas pero NO están en la base de datos:')

no_encontrados = []
for origen, count in origenes_counter.items():
    if not Sucursal.objects.filter(name__iexact=origen).exists():
        no_encontrados.append((origen, count, 'origen'))

for destino, count in destinos_counter.items():
    if not Sucursal.objects.filter(name__iexact=destino).exists():
        # Evitar duplicados
        if not any(x[0] == destino for x in no_encontrados):
            no_encontrados.append((destino, count, 'destino'))

if no_encontrados:
    for nombre, count, tipo in sorted(no_encontrados, key=lambda x: -x[1]):
        print(f'\n  ❌ "{nombre}" ({count} veces como {tipo})')
        
        # Buscar similares
        import difflib
        similares = difflib.get_close_matches(nombre.lower(), 
                                              [s.lower() for s in sucursales_db], 
                                              n=3, cutoff=0.5)
        if similares:
            print(f'     💡 Sugerencias:')
            for sim in similares:
                # Encontrar el nombre original (con mayúsculas correctas)
                original = next(s for s in sucursales_db if s.lower() == sim)
                print(f'        → "{original}"')
else:
    print('  ✅ Todos los CEDIS están correctamente mapeados')

print('\n' + '=' * 80)
print('\n💡 SOLUCIÓN:')
print('   1. Ve a: http://localhost:2222/salidas/errores/')
print('   2. Mapea los CEDIS incorrectos a los correctos')
print('   3. O crea los CEDIS faltantes si son nuevos')
print('   4. Vuelve a normalizar las salidas')
print('=' * 80)
