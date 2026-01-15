import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ADB.settings')
django.setup()

from main.models import Sucursal, Planificacion
from collections import Counter

print('=' * 80)
print('🔧 SOLUCIÓN: CREAR CEDIS FALTANTES')
print('=' * 80)

# Ver qué CEDIS hay en cendis
origenes = Planificacion.objects.values_list('cendis', flat=True).distinct()
counter = Counter([o.strip() for o in origenes if o and o.strip()])

print('\n📋 CEDIS en cendis:')
for origen in sorted(counter.keys()):
    print(f'  - "{origen}"')

print('\n📚 CEDIS en base de datos (case-insensitive match):')
sucursales_map = {s.name.lower(): s.name for s in Sucursal.objects.all()}

faltantes = []
for origen in counter.keys():
    if origen.lower() not in sucursales_map:
        faltantes.append(origen)
        print(f'  ❌ "{origen}" NO existe')
    else:
        nombre_db = sucursales_map[origen.lower()]
        if nombre_db != origen:
            print(f'  ⚠️  "{origen}" existe como "{nombre_db}" (diferente mayúsculas)')
        else:
            print(f'  ✅ "{origen}" existe')

if faltantes:
    print('\n' + '=' * 80)
    print('\n🔨 CREANDO CEDIS FALTANTES:\n')
    
    # Obtener el último bpl_id usado
    last_bpl = Sucursal.objects.order_by('-bpl_id').first()
    next_bpl = (last_bpl.bpl_id + 1) if last_bpl else 2000
    
    for nombre in faltantes:
        Sucursal.objects.create(name=nombre, bpl_id=next_bpl)
        print(f'  ✅ Creado: "{nombre}" (bpl_id: {next_bpl})')
        next_bpl += 1
    
    print(f'\n✅ Se crearon {len(faltantes)} CEDIS')
else:
    print('\n✅ Todos los CEDIS ya existen')

print('\n' + '=' * 80)
print('\n💡 SIGUIENTE PASO:')
print('   Normaliza planificación en:')
print('   http://localhost:2222/planificacion/normalizar/')
print('\n   El sistema ahora podrá normalizar el campo cendis')
print('   correctamente a sucursal_origen FK')
print('=' * 80)
