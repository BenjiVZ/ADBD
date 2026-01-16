"""
Script para diagnosticar el problema de sucursales destino
"""
import os
import sys
import django

# Agregar path del proyecto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ADB.settings')
django.setup()

from main.models import Salida, SalidaNormalizada, Sucursal

# Contar cuántos tienen cada campo
total = Salida.objects.count()
con_destino = Salida.objects.exclude(nombre_sucursal_destino='').count()
con_propuesto = Salida.objects.exclude(sucursal_destino_propuesto='').count()

print(f'Total salidas: {total}')
print(f'Con nombre_sucursal_destino: {con_destino}')
print(f'Con sucursal_destino_propuesto: {con_propuesto}')

# Ver algunos ejemplos
print('\nEjemplos:')
for s in Salida.objects.all()[:5]:
    print(f'  destino="{s.nombre_sucursal_destino}" | propuesto="{s.sucursal_destino_propuesto}"')

# Ver sucursales únicas en propuesto
print('\n--- Sucursales destino únicas en sucursal_destino_propuesto ---')
propuestos = set(Salida.objects.exclude(sucursal_destino_propuesto='').values_list('sucursal_destino_propuesto', flat=True))
print(f'Total únicas: {len(propuestos)}')
for p in sorted(propuestos)[:20]:
    print(f'  - {p}')

# Verificar cuáles de esas existen en la tabla Sucursal
print('\n--- Verificando cuáles existen en tabla Sucursal ---')
sucursales_db = set(Sucursal.objects.values_list('name', flat=True))
sucursales_db_lower = {s.lower() for s in sucursales_db}

encontradas = 0
no_encontradas = []
for p in propuestos:
    if p.lower() in sucursales_db_lower:
        encontradas += 1
    else:
        no_encontradas.append(p)

print(f'Encontradas: {encontradas}')
print(f'No encontradas: {len(no_encontradas)}')
if no_encontradas:
    print('Ejemplos no encontradas:')
    for nf in sorted(no_encontradas)[:10]:
        print(f'  - "{nf}"')
