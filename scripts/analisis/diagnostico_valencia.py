import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ADB.settings')
django.setup()

from main.models import Cendis, Sucursal, Salida

print("=" * 80)
print("DIAGNÓSTICO: ¿Por qué VALENCIA se normaliza sin error?")
print("=" * 80)

# 1. Verificar si VALENCIA y LA YAGUARA están en CEDIS
print("\n1. ¿Están en la tabla CEDIS (almacenes)?")
valencia_cedis = Cendis.objects.filter(origin__iexact='VALENCIA')
yaguara_cedis = Cendis.objects.filter(origin__iexact='LA YAGUARA')

print(f"   VALENCIA en CEDIS: {valencia_cedis.exists()}")
if valencia_cedis.exists():
    for c in valencia_cedis:
        print(f"      - ID:{c.id} | Code:{c.code} | Origin:{c.origin}")

print(f"   LA YAGUARA en CEDIS: {yaguara_cedis.exists()}")
if yaguara_cedis.exists():
    for c in yaguara_cedis:
        print(f"      - ID:{c.id} | Code:{c.code} | Origin:{c.origin}")

# 2. Verificar si están en Sucursales
print("\n2. ¿Están en la tabla SUCURSALES (tiendas)?")
valencia_suc = Sucursal.objects.filter(name__iexact='VALENCIA')
yaguara_suc = Sucursal.objects.filter(name__iexact='LA YAGUARA')

print(f"   VALENCIA en Sucursales: {valencia_suc.exists()}")
if valencia_suc.exists():
    for s in valencia_suc:
        print(f"      - ID:{s.id} | BPL:{s.bpl_id} | Name:{s.name}")

print(f"   LA YAGUARA en Sucursales: {yaguara_suc.exists()}")
if yaguara_suc.exists():
    for s in yaguara_suc:
        print(f"      - ID:{s.id} | BPL:{s.bpl_id} | Name:{s.name}")

# 3. Verificar registros de Salida con estos orígenes
print("\n3. Registros en Salida con estos orígenes:")
salidas_valencia = Salida.objects.filter(nombre_sucursal_origen__iexact='VALENCIA')
salidas_yaguara = Salida.objects.filter(nombre_sucursal_origen__iexact='LA YAGUARA')

print(f"   Salidas con origen VALENCIA: {salidas_valencia.count()}")
print(f"      - Pending: {salidas_valencia.filter(normalize_status='pending').count()}")
print(f"      - OK: {salidas_valencia.filter(normalize_status='ok').count()}")
print(f"      - Error: {salidas_valencia.filter(normalize_status='error').count()}")

print(f"   Salidas con origen LA YAGUARA: {salidas_yaguara.count()}")
print(f"      - Pending: {salidas_yaguara.filter(normalize_status='pending').count()}")
print(f"      - OK: {salidas_yaguara.filter(normalize_status='ok').count()}")
print(f"      - Error: {salidas_yaguara.filter(normalize_status='error').count()}")

# 4. Ver algunos ejemplos
print("\n4. Ejemplos de salidas con VALENCIA como origen:")
for s in salidas_valencia[:3]:
    print(f"   ID:{s.id} | Origen:'{s.nombre_sucursal_origen}' | Almacen:'{s.nombre_almacen_origen}' | Destino:'{s.nombre_sucursal_destino}' | Status:{s.normalize_status}")

print("\n" + "=" * 80)
print("PROBLEMA IDENTIFICADO:")
print("=" * 80)

if valencia_suc.exists() and not valencia_cedis.exists():
    print("\n❌ VALENCIA está en Sucursales (tienda) pero NO en CEDIS (almacén)")
    print("   → El sistema lo trata como transferencia entre tiendas")
    print("   → DEBERÍA ser un almacén CEDIS según tus datos")
    print("\n✅ SOLUCIÓN: Agregar VALENCIA a la tabla CEDIS")

if yaguara_suc.exists() and yaguara_cedis.exists():
    print("\n⚠️ LA YAGUARA está en AMBAS tablas (Sucursal Y CEDIS)")
    print("   → Puede causar confusión")
    print("   → El sistema prioriza CEDIS correctamente")

print("\n" + "=" * 80)
