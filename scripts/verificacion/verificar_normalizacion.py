import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ADB.settings')
django.setup()

from main.models import (
    Planificacion, Salida, Cendis, Sucursal, Product,
    PlanificacionNormalizada, SalidaNormalizada
)

print("=" * 80)
print("VERIFICACIÓN COMPLETA DEL SISTEMA DE NORMALIZACIÓN")
print("=" * 80)

# 1. ESTADO GENERAL
print("\n📊 ESTADO GENERAL DE LOS DATOS\n")
print(f"Planificacion (raw): {Planificacion.objects.count()} registros")
print(f"  - Pending: {Planificacion.objects.filter(normalize_status='pending').count()}")
print(f"  - OK: {Planificacion.objects.filter(normalize_status='ok').count()}")
print(f"  - Error: {Planificacion.objects.filter(normalize_status='error').count()}")
print(f"  - Ignored: {Planificacion.objects.filter(normalize_status='ignored').count()}")
print(f"\nPlanificacionNormalizada: {PlanificacionNormalizada.objects.count()} registros")

print(f"\nSalida (raw): {Salida.objects.count()} registros")
print(f"  - Pending: {Salida.objects.filter(normalize_status='pending').count()}")
print(f"  - OK: {Salida.objects.filter(normalize_status='ok').count()}")
print(f"  - Error: {Salida.objects.filter(normalize_status='error').count()}")
print(f"\nSalidaNormalizada: {SalidaNormalizada.objects.count()} registros")

# 2. MAESTROS
print("\n" + "=" * 80)
print("📚 MAESTROS DISPONIBLES\n")
print(f"Sucursales: {Sucursal.objects.count()}")
print(f"CEDIS: {Cendis.objects.count()}")
print(f"Productos: {Product.objects.count()}")

# 3. CEDIS DISPONIBLES
print("\n" + "=" * 80)
print("🏭 CEDIS DISPONIBLES (Tabla Cendis)\n")
for c in Cendis.objects.all():
    print(f"  ID:{c.id:3} | Code: {c.code:15} | Origin: {c.origin}")

# 4. SUCURSALES (primeras 10)
print("\n" + "=" * 80)
print("🏢 SUCURSALES DISPONIBLES (primeras 10)\n")
for s in Sucursal.objects.all()[:10]:
    print(f"  ID:{s.id:3} | BPL:{s.bpl_id:10} | Name: {s.name}")

# 5. ERRORES EN PLANIFICACION
print("\n" + "=" * 80)
print("❌ ERRORES EN PLANIFICACION (primeros 10)\n")
errores_plan = Planificacion.objects.filter(normalize_status='error')[:10]
if errores_plan:
    for i, p in enumerate(errores_plan, 1):
        print(f"\n{i}. ID:{p.id} | Mes:{p.plan_month}")
        print(f"   Sucursal RAW: '{p.sucursal}'")
        print(f"   CEDIS RAW: '{p.cendis}'")
        print(f"   Item Code: '{p.item_code}'")
        print(f"   Notas: {p.normalize_notes}")
else:
    print("✅ No hay errores en Planificacion")

# 6. ERRORES EN SALIDA
print("\n" + "=" * 80)
print("❌ ERRORES EN SALIDA (primeros 10)\n")
errores_salida = Salida.objects.filter(normalize_status='error')[:10]
if errores_salida:
    for i, s in enumerate(errores_salida, 1):
        print(f"\n{i}. ID:{s.id} | Fecha:{s.fecha_salida}")
        print(f"   Origen RAW: '{s.nombre_sucursal_origen}'")
        print(f"   Destino RAW: '{s.nombre_sucursal_destino}'")
        print(f"   SKU: '{s.sku}'")
        print(f"   Notas: {s.normalize_notes}")
else:
    print("✅ No hay errores en Salida")

# 7. VERIFICAR LÓGICA DE NORMALIZACIÓN
print("\n" + "=" * 80)
print("🔍 VERIFICACIÓN DE LÓGICA DE NORMALIZACIÓN\n")

# 7.1 Planificacion
print("PLANIFICACION:")
print("  - Campo 'sucursal' debe mapear a → Sucursal (tabla Sucursal)")
print("  - Campo 'cendis' debe mapear a → Cendis (tabla Cendis)")
print("  - Campo 'item_code' debe mapear a → Product (tabla Product)")

# 7.2 Salida
print("\nSALIDA:")
print("  - Campo 'nombre_sucursal_origen' debe mapear a → Cendis (tabla Cendis)")
print("  - Campo 'nombre_sucursal_destino' debe mapear a → Sucursal (tabla Sucursal)")
print("  - Campo 'sku' debe mapear a → Product (tabla Product)")

# 8. VERIFICAR REGISTROS NORMALIZADOS
print("\n" + "=" * 80)
print("✅ REGISTROS NORMALIZADOS (muestra)\n")

plan_norm = PlanificacionNormalizada.objects.select_related(
    'raw', 'sucursal', 'cedis_origen', 'product'
).first()

if plan_norm:
    print("PLANIFICACION NORMALIZADA (ejemplo):")
    print(f"  Raw ID: {plan_norm.raw_id}")
    print(f"  Sucursal: {plan_norm.sucursal.name if plan_norm.sucursal else 'NULL'} (FK a Sucursal)")
    print(f"  CEDIS Origen: {plan_norm.cedis_origen.origin if plan_norm.cedis_origen else 'NULL'} (FK a Cendis)")
    print(f"  Product: {plan_norm.product.code if plan_norm.product else 'NULL'} (FK a Product)")
else:
    print("⚠️ No hay registros de PlanificacionNormalizada")

salida_norm = SalidaNormalizada.objects.select_related(
    'raw', 'cedis_origen', 'sucursal_destino', 'product'
).first()

if salida_norm:
    print("\nSALIDA NORMALIZADA (ejemplo):")
    print(f"  Raw ID: {salida_norm.raw_id}")
    print(f"  CEDIS Origen: {salida_norm.cedis_origen.origin if salida_norm.cedis_origen else 'NULL'} (FK a Cendis)")
    print(f"  Sucursal Destino: {salida_norm.sucursal_destino.name if salida_norm.sucursal_destino else 'NULL'} (FK a Sucursal)")
    print(f"  Product: {salida_norm.product.code if salida_norm.product else 'NULL'} (FK a Product)")
else:
    print("\n⚠️ No hay registros de SalidaNormalizada")

# 9. ANÁLISIS DE VALORES RAW vs MAESTROS
print("\n" + "=" * 80)
print("🔬 ANÁLISIS: Valores RAW vs Maestros\n")

# 9.1 Valores únicos de cendis en Planificacion
cendis_raw_plan = set(
    Planificacion.objects.exclude(cendis='')
    .values_list('cendis', flat=True)
    .distinct()
)
print(f"Valores únicos de 'cendis' en Planificacion: {len(cendis_raw_plan)}")
for val in sorted(cendis_raw_plan):
    # Verificar si existe en maestro Cendis
    existe = Cendis.objects.filter(origin__iexact=val).exists()
    status = "✅" if existe else "❌"
    print(f"  {status} '{val}'")

# 9.2 Valores únicos de sucursal en Planificacion
sucursales_raw_plan = set(
    Planificacion.objects.exclude(sucursal='')
    .values_list('sucursal', flat=True)
    .distinct()
)
print(f"\nValores únicos de 'sucursal' en Planificacion: {len(sucursales_raw_plan)}")
if len(sucursales_raw_plan) <= 20:
    for val in sorted(sucursales_raw_plan):
        existe = Sucursal.objects.filter(name__iexact=val).exists()
        status = "✅" if existe else "❌"
        print(f"  {status} '{val}'")
else:
    print(f"  (Demasiados valores, mostrando primeros 20)")
    for val in sorted(list(sucursales_raw_plan)[:20]):
        existe = Sucursal.objects.filter(name__iexact=val).exists()
        status = "✅" if existe else "❌"
        print(f"  {status} '{val}'")

# 9.3 Valores únicos de nombre_sucursal_origen en Salida
origenes_raw_salida = set(
    Salida.objects.exclude(nombre_sucursal_origen='')
    .values_list('nombre_sucursal_origen', flat=True)
    .distinct()
)
print(f"\nValores únicos de 'nombre_sucursal_origen' en Salida: {len(origenes_raw_salida)}")
for val in sorted(origenes_raw_salida):
    existe = Cendis.objects.filter(origin__iexact=val).exists()
    status = "✅" if existe else "❌"
    print(f"  {status} '{val}'")

# 9.4 Valores únicos de nombre_sucursal_destino en Salida
destinos_raw_salida = set(
    Salida.objects.exclude(nombre_sucursal_destino='')
    .values_list('nombre_sucursal_destino', flat=True)
    .distinct()
)
print(f"\nValores únicos de 'nombre_sucursal_destino' en Salida: {len(destinos_raw_salida)}")
if len(destinos_raw_salida) <= 20:
    for val in sorted(destinos_raw_salida):
        existe = Sucursal.objects.filter(name__iexact=val).exists()
        status = "✅" if existe else "❌"
        print(f"  {status} '{val}'")
else:
    print(f"  (Demasiados valores, mostrando primeros 20)")
    for val in sorted(list(destinos_raw_salida)[:20]):
        existe = Sucursal.objects.filter(name__iexact=val).exists()
        status = "✅" if existe else "❌"
        print(f"  {status} '{val}'")

print("\n" + "=" * 80)
print("FIN DEL ANÁLISIS")
print("=" * 80)
