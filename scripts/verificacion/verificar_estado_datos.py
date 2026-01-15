import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ADB.settings')
django.setup()

from main.models import Planificacion, Salida, PlanificacionNormalizada, SalidaNormalizada, Cendis

print("=" * 80)
print("ESTADO DE DATOS EN EL SISTEMA")
print("=" * 80)

# CEDIS
cedis_count = Cendis.objects.count()
print(f"\n🏭 CEDIS registrados: {cedis_count}")
for c in Cendis.objects.all():
    print(f"   - {c.origin} ({c.code})")

# Planificacion
plan_total = Planificacion.objects.count()
plan_pending = Planificacion.objects.filter(normalize_status='pending').count()
plan_ok = Planificacion.objects.filter(normalize_status='ok').count()
plan_error = Planificacion.objects.filter(normalize_status='error').count()
plan_norm = PlanificacionNormalizada.objects.count()

print(f"\n📋 Planificacion (datos crudos):")
print(f"   Total: {plan_total}")
print(f"   Pending: {plan_pending}")
print(f"   OK: {plan_ok}")
print(f"   Error: {plan_error}")
print(f"   Normalizados: {plan_norm}")

if plan_total > 0 and plan_norm == 0:
    print("   ⚠️  Tienes datos de planificación pero NO están normalizados")
    print("   ➡️  Ve a: http://localhost:2222/planificacion/normalizar/")

# Salida
sal_total = Salida.objects.count()
sal_pending = Salida.objects.filter(normalize_status='pending').count()
sal_ok = Salida.objects.filter(normalize_status='ok').count()
sal_error = Salida.objects.filter(normalize_status='error').count()
sal_norm = SalidaNormalizada.objects.count()

print(f"\n📦 Salida (datos crudos):")
print(f"   Total: {sal_total}")
print(f"   Pending: {sal_pending}")
print(f"   OK: {sal_ok}")
print(f"   Error: {sal_error}")
print(f"   Normalizados: {sal_norm}")

if sal_total > 0 and sal_norm == 0:
    print("   ⚠️  Tienes datos de salidas pero NO están normalizados")
    print("   ➡️  Ve a: http://localhost:2222/salidas/normalizar/")

print("\n" + "=" * 80)
if plan_norm == 0 or sal_norm == 0:
    print("⚠️  NECESITAS NORMALIZAR LOS DATOS")
    print("=" * 80)
    print("\n1. Normaliza Planificación: http://localhost:2222/planificacion/normalizar/")
    print("2. Normaliza Salidas: http://localhost:2222/salidas/normalizar/")
    print("3. Luego revisa el tablero: http://localhost:2222/tablero/")
else:
    print("✅ Todos los datos están normalizados")
    print("=" * 80)
