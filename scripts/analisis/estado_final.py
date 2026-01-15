import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ADB.settings')
django.setup()

from main.models import (
    Planificacion, Salida, Cendis, Sucursal, Product,
    PlanificacionNormalizada, SalidaNormalizada
)

print("=" * 80)
print("ESTADO ACTUAL POST-CORRECCIONES")
print("=" * 80)

# Estado General
print("\nESTADO GENERAL:")
print(f"\nPlanificacion (raw): {Planificacion.objects.count()} registros")
print(f"  - Pending: {Planificacion.objects.filter(normalize_status='pending').count()}")
print(f"  - OK: {Planificacion.objects.filter(normalize_status='ok').count()}")
print(f"  - Error: {Planificacion.objects.filter(normalize_status='error').count()}")
print(f"\nPlanificacionNormalizada: {PlanificacionNormalizada.objects.count()} registros")

print(f"\nSalida (raw): {Salida.objects.count()} registros")
print(f"  - Pending: {Salida.objects.filter(normalize_status='pending').count()}")
print(f"  - OK: {Salida.objects.filter(normalize_status='ok').count()}")
print(f"  - Error: {Salida.objects.filter(normalize_status='error').count()}")
print(f"\nSalidaNormalizada: {SalidaNormalizada.objects.count()} registros")

# Maestros
print("\n" + "=" * 80)
print("MAESTROS:")
print(f"  Sucursales: {Sucursal.objects.count()}")
print(f"  CEDIS: {Cendis.objects.count()}")
print(f"  Productos: {Product.objects.count()}")

# Errores
print("\n" + "=" * 80)
print("ERRORES ACTUALES:")
plan_errors = Planificacion.objects.filter(normalize_status='error').count()
salida_errors = Salida.objects.filter(normalize_status='error').count()
print(f"  Planificacion: {plan_errors} errores")
print(f"  Salida: {salida_errors} errores")

if salida_errors > 0:
    print("\nPrimeros 5 errores en Salida:")
    for s in Salida.objects.filter(normalize_status='error')[:5]:
        print(f"  - Origen: '{s.nombre_sucursal_origen}' | Destino: '{s.nombre_sucursal_destino}'")
        print(f"    Nota: {s.normalize_notes[:80]}")

print("\n" + "=" * 80)
print("RESUMEN:")
print("=" * 80)
print(f"\nListo para normalizar:")
print(f"  - Planificacion: {Planificacion.objects.filter(normalize_status='pending').count()} registros pendientes")
print(f"  - Salida: {Salida.objects.filter(normalize_status='pending').count()} registros pendientes")
print(f"\nAcciones siguientes:")
print(f"  1. Normalizar desde: http://localhost:2222/planificacion/normalizar/")
print(f"  2. Normalizar desde: http://localhost:2222/salidas/normalizar/")
if salida_errors > 0:
    print(f"  3. Ejecutar: python agregar_cedis_faltantes.py")
    print(f"  4. O resolver desde: http://localhost:2222/salidas/errores/")

print("\n" + "=" * 80)
