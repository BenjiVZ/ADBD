import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ADB.settings')
django.setup()

from main.models import Planificacion, PlanificacionNormalizada
from django.db import transaction

print("=" * 80)
print("DIAGNÓSTICO: ¿Por qué PlanificacionNormalizada está vacía?")
print("=" * 80)

# Verificar relaciones
plan_ok = Planificacion.objects.filter(normalize_status='ok')
print(f"\nPlanificacion con status='ok': {plan_ok.count()}")

# Verificar si tienen registros normalizados
con_normalizada = 0
sin_normalizada = 0

for p in plan_ok[:10]:  # Revisar primeros 10
    if hasattr(p, 'normalizada'):
        try:
            norm = p.normalizada
            con_normalizada += 1
            print(f"✅ Planificacion ID {p.id} -> Tiene normalizada (ID: {norm.id})")
        except PlanificacionNormalizada.DoesNotExist:
            sin_normalizada += 1
            print(f"❌ Planificacion ID {p.id} -> NO tiene normalizada")
    else:
        sin_normalizada += 1
        print(f"❌ Planificacion ID {p.id} -> NO tiene atributo normalizada")

print(f"\nResumen (primeros 10):")
print(f"  Con normalizada: {con_normalizada}")
print(f"  Sin normalizada: {sin_normalizada}")

# Verificar si hay algún normalizado huérfano
normalizados_totales = PlanificacionNormalizada.objects.count()
print(f"\nTotal PlanificacionNormalizada en BD: {normalizados_totales}")

# Verificar raw_ids
if normalizados_totales > 0:
    print("\nPrimeros registros normalizados:")
    for norm in PlanificacionNormalizada.objects.all()[:5]:
        print(f"  ID: {norm.id} -> raw_id: {norm.raw_id}")
