import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ADB.settings')
django.setup()

from main.models import Planificacion, PlanificacionNormalizada, Salida, SalidaNormalizada

print("=" * 80)
print("REPARACIÓN: Re-normalizar registros marcados como 'ok' sin normalizada")
print("=" * 80)

# 1. Contar planificaciones "ok" sin normalizada
plan_ok = Planificacion.objects.filter(normalize_status='ok')
plan_sin_norm = []

for p in plan_ok:
    try:
        _ = p.normalizada
    except PlanificacionNormalizada.DoesNotExist:
        plan_sin_norm.append(p.id)

print(f"\n📊 Planificacion:")
print(f"  Total con status='ok': {plan_ok.count()}")
print(f"  Sin registro normalizado: {len(plan_sin_norm)}")

# 2. Contar salidas "ok" sin normalizada
salida_ok = Salida.objects.filter(normalize_status='ok')
salida_sin_norm = []

for s in salida_ok:
    try:
        _ = s.normalizada
    except SalidaNormalizada.DoesNotExist:
        salida_sin_norm.append(s.id)

print(f"\n📊 Salida:")
print(f"  Total con status='ok': {salida_ok.count()}")
print(f"  Sin registro normalizado: {len(salida_sin_norm)}")

# 3. Cambiar estado a "pending" para re-procesar
if plan_sin_norm:
    print(f"\n🔧 Marcando {len(plan_sin_norm)} planificaciones como 'pending' para re-procesar...")
    Planificacion.objects.filter(id__in=plan_sin_norm).update(normalize_status='pending')
    print(f"✅ Actualizados")

if salida_sin_norm:
    print(f"\n🔧 Marcando {len(salida_sin_norm)} salidas como 'pending' para re-procesar...")
    Salida.objects.filter(id__in=salida_sin_norm).update(normalize_status='pending')
    print(f"✅ Actualizados")

print("\n" + "=" * 80)
print("✅ REPARACIÓN COMPLETADA")
print("=" * 80)
print("\nAhora puedes ejecutar la normalización desde el navegador:")
print("  - Planificación: http://localhost:2222/planificacion/normalizar/")
print("  - Salidas: http://localhost:2222/salidas/normalizar/")
