import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ADB.settings')
django.setup()

from main.models import Cendis, MapeoCedis, Planificacion, PlanificacionNormalizada

print("=== PASO 1: Revertir nombres de CEDIS a los del Excel ===")

# Renombrar de vuelta
revertir = {
    "Guatire 1": "Guatire I",
    "Guatire 2": "Guatire II",
    "García Tuñón": "Guatire 4",
    "Forum": "Guatire 5",
}

for nombre_actual, nombre_excel in revertir.items():
    try:
        cedis = Cendis.objects.get(origin=nombre_actual)
        cedis.origin = nombre_excel
        cedis.save()
        print(f"✅ Revertido: '{nombre_actual}' → '{nombre_excel}'")
    except Cendis.DoesNotExist:
        print(f"⚠️ No encontrado: '{nombre_actual}'")

print("\n=== PASO 2: Eliminar mapeos que creé ===")

mapeos_eliminar = ["Guatire I", "Guatire II", "Guatire 4", "Guatire 5"]
for nombre in mapeos_eliminar:
    eliminados = MapeoCedis.objects.filter(nombre_crudo=nombre).delete()[0]
    if eliminados > 0:
        print(f"✅ Eliminado mapeo: '{nombre}'")

print("\n=== PASO 3: Limpiar normalizaciones para re-normalizar ===")

# Eliminar normalizaciones
PlanificacionNormalizada.objects.all().delete()
print("✅ Normalizaciones eliminadas")

# Resetear status
Planificacion.objects.all().update(
    normalize_status='pending',
    normalize_notes='',
    normalized_at=None
)
print("✅ Status reseteado a 'pending'")

print("\n=== RESUMEN ===")
print("\nCEDIS oficiales (nombres del Excel):")
for c in Cendis.objects.all().order_by("origin"):
    print(f"  - {c.origin} (código: {c.code})")

print("\nMapeos restantes:")
for m in MapeoCedis.objects.select_related("cedis_oficial").all():
    print(f"  - '{m.nombre_crudo}' → '{m.cedis_oficial.origin}'")

print("\n✅ Revertido completado.")
print("\n📋 Los nombres del Excel (Guatire I, II, 4, 5) son ahora los oficiales.")
print("📋 Ve a /planificacion/normalizar/ y normaliza de nuevo.")
