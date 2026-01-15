import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ADB.settings')
django.setup()

from main.models import Planificacion, Sucursal
from collections import Counter

print("🔍 VERIFICANDO ERRORES DE cendis\n")

# Obtener todos los CEDIS registrados
sucursales = set(Sucursal.objects.values_list('name', flat=True))
print(f"📋 CEDIS registrados: {len(sucursales)}")
for s in sorted(sucursales):
    print(f"  ✅ {s}")

print("\n" + "="*60)

# Verificar cendis en planificaciones pendientes
planificaciones_pendientes = Planificacion.objects.filter(normalize_status='pending')
origenes = planificaciones_pendientes.values_list('cendis', flat=True)
origen_counter = Counter(origenes)

print(f"\n🔍 cendis en planificaciones pendientes:")
print(f"Total planificaciones pendientes: {planificaciones_pendientes.count()}")

errores_origen = {}
correctos_origen = {}

for origen, count in origen_counter.items():
    # Buscar coincidencia case-insensitive
    origen_encontrado = None
    for suc in sucursales:
        if suc.lower() == origen.strip().lower():
            origen_encontrado = suc
            break
    
    if origen_encontrado:
        correctos_origen[origen] = (count, origen_encontrado)
    else:
        errores_origen[origen] = count

if errores_origen:
    print(f"\n❌ ERRORES - CEDIS NO ENCONTRADOS ({len(errores_origen)} diferentes):")
    for origen, count in sorted(errores_origen.items(), key=lambda x: -x[1]):
        print(f"  ❌ '{origen}' - {count} registros")
else:
    print("\n✅ Todos los cendis tienen CEDIS correspondientes")

if correctos_origen:
    print(f"\n✅ CORRECTOS ({len(correctos_origen)} diferentes):")
    for origen, (count, matched) in sorted(correctos_origen.items()):
        if origen != matched:
            print(f"  ⚠️  '{origen}' → coincide con '{matched}' - {count} registros")
        else:
            print(f"  ✅ '{origen}' - {count} registros")

print("\n" + "="*60)
print(f"\n📊 RESUMEN:")
print(f"  Total CEDIS con errores: {len(errores_origen)}")
print(f"  Total registros con errores: {sum(errores_origen.values())}")
print(f"  Total CEDIS correctos: {len(correctos_origen)}")
print(f"  Total registros correctos: {sum(c for c, _ in correctos_origen.values())}")
