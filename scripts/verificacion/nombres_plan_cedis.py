import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ADB.settings')
django.setup()

from main.models import Planificacion, Cendis

print("=== NOMBRES DE CEDIS EN PLANIFICACIÓN (datos crudos) ===")
nombres_plan = Planificacion.objects.exclude(cendis__isnull=True).exclude(cendis="").values_list("cendis", flat=True).distinct()

for n in sorted(set(nombres_plan)):
    # Contar cuántos registros tienen este nombre
    count = Planificacion.objects.filter(cendis=n).count()
    print(f"  '{n}' → {count} registros")

print(f"\nTotal nombres únicos: {len(set(nombres_plan))}")

print("\n=== CEDIS OFICIALES REGISTRADOS ===")
cedis_oficiales = Cendis.objects.all().order_by("origin")
for c in cedis_oficiales:
    print(f"  '{c.origin}' (código: {c.code})")
