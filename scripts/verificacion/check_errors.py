import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ADB.settings')
django.setup()

from main.models import Planificacion, Salida, Sucursal, Product
from collections import defaultdict

print('=' * 70)
print('🔍 REVISIÓN DE ERRORES EN NORMALIZACIÓN')
print('=' * 70)

# Errores en Planificación
print('\n📋 PLANIFICACIÓN - Datos sin normalizar:')
plan_sin_norm = Planificacion.objects.filter(normalize_status__in=['pending', 'error'])
if plan_sin_norm.exists():
    errores_sucursal = defaultdict(int)
    errores_producto = defaultdict(int)
    
    for p in plan_sin_norm:
        if p.sucursal:
            sucursal_lower = p.sucursal.strip().lower()
            if not Sucursal.objects.filter(name__iexact=sucursal_lower).exists():
                errores_sucursal[p.sucursal.strip()] += 1
        
        if p.item_code:
            code_lower = p.item_code.strip().lower()
            if not Product.objects.filter(code__iexact=code_lower).exists():
                errores_producto[p.item_code.strip()] += 1
    
    if errores_sucursal:
        print(f'\n  ⚠️  {len(errores_sucursal)} sucursales NO encontradas:')
        for suc, count in sorted(errores_sucursal.items(), key=lambda x: -x[1])[:10]:
            print(f'    - "{suc}" ({count} veces)')
    
    if errores_producto:
        print(f'\n  ⚠️  {len(errores_producto)} productos NO encontrados:')
        for prod, count in sorted(errores_producto.items(), key=lambda x: -x[1])[:10]:
            print(f'    - "{prod}" ({count} veces)')
    
    print(f'\n  👉 Resuelve estos errores en:')
    print(f'     http://localhost:2222/planificacion/errores/')
else:
    print('  ✅ Sin errores pendientes')

# Errores en Salidas
print('\n' + '-' * 70)
print('\n🚚 SALIDAS - Datos sin normalizar:')
salida_sin_norm = Salida.objects.filter(normalize_status__in=['pending', 'error'])
if salida_sin_norm.exists():
    errores_origen = defaultdict(int)
    errores_destino = defaultdict(int)
    errores_producto = defaultdict(int)
    
    for s in salida_sin_norm:
        if s.nombre_sucursal_origen:
            origen_lower = s.nombre_sucursal_origen.strip().lower()
            if not Sucursal.objects.filter(name__iexact=origen_lower).exists():
                errores_origen[s.nombre_sucursal_origen.strip()] += 1
        
        if s.nombre_sucursal_destino:
            destino_lower = s.nombre_sucursal_destino.strip().lower()
            if not Sucursal.objects.filter(name__iexact=destino_lower).exists():
                errores_destino[s.nombre_sucursal_destino.strip()] += 1
        
        if s.sku:
            code_lower = s.sku.strip().lower()
            if not Product.objects.filter(code__iexact=code_lower).exists():
                errores_producto[s.sku.strip()] += 1
    
    if errores_origen:
        print(f'\n  ⚠️  {len(errores_origen)} orígenes NO encontrados:')
        for orig, count in sorted(errores_origen.items(), key=lambda x: -x[1])[:10]:
            print(f'    - "{orig}" ({count} veces)')
    
    if errores_destino:
        print(f'\n  ⚠️  {len(errores_destino)} destinos NO encontrados:')
        for dest, count in sorted(errores_destino.items(), key=lambda x: -x[1])[:10]:
            print(f'    - "{dest}" ({count} veces)')
    
    if errores_producto:
        print(f'\n  ⚠️  {len(errores_producto)} productos NO encontrados:')
        for prod, count in sorted(errores_producto.items(), key=lambda x: -x[1])[:10]:
            print(f'    - "{prod}" ({count} veces)')
    
    print(f'\n  👉 Resuelve estos errores en:')
    print(f'     http://localhost:2222/salidas/errores/')
else:
    print('  ✅ Sin errores pendientes')

print('\n' + '=' * 70)
print('\n💡 SISTEMA DE RESOLUCIÓN DE ERRORES:')
print('   1. Abre la URL de errores (arriba)')
print('   2. Verás sugerencias automáticas con fuzzy matching')
print('   3. Opciones para cada error:')
print('      • MAPEAR: Vincular con sucursal/producto existente')
print('      • CREAR: Crear nueva sucursal/producto')
print('      • IGNORAR: Marcar como ignorado')
print('   4. Después vuelve a normalizar')
print('=' * 70)
