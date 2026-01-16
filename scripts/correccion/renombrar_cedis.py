import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ADB.settings')
django.setup()

from main.models import Cendis, MapeoCedis

print("=== PASO 1: Renombrar CEDIS a nombres correctos ===")

# Mapeo: nombre_actual → nombre_correcto
renombrar = {
    "Guatire I": "Guatire 1",
    "Guatire II": "Guatire 2",
    "Guatire 4": "García Tuñón",
    "Guatire 5": "Forum",
}

for nombre_actual, nombre_correcto in renombrar.items():
    try:
        cedis = Cendis.objects.get(origin=nombre_actual)
        cedis.origin = nombre_correcto
        cedis.save()
        print(f"✅ Renombrado: '{nombre_actual}' → '{nombre_correcto}'")
    except Cendis.DoesNotExist:
        print(f"⚠️ No encontrado: '{nombre_actual}'")

print("\n=== PASO 2: Crear mapeos de nombres del Excel a CEDIS correctos ===")

# Los nombres del Excel se mapearán a los CEDIS correctos
mapeos_crear = {
    "Guatire I": "Guatire 1",
    "Guatire II": "Guatire 2",
    "Guatire 4": "García Tuñón",
    "Guatire 5": "Forum",
}

for nombre_excel, nombre_cedis in mapeos_crear.items():
    try:
        cedis_oficial = Cendis.objects.get(origin=nombre_cedis)
        mapeo, created = MapeoCedis.objects.get_or_create(
            nombre_crudo=nombre_excel,
            defaults={"cedis_oficial": cedis_oficial}
        )
        if created:
            print(f"✅ Mapeo creado: '{nombre_excel}' → '{nombre_cedis}'")
        else:
            print(f"⚠️ Mapeo ya existe: '{nombre_excel}' → '{nombre_cedis}'")
    except Cendis.DoesNotExist:
        print(f"❌ CEDIS no encontrado: '{nombre_cedis}'")

print("\n=== RESUMEN ===")
print("\nCEDIS oficiales:")
for c in Cendis.objects.all().order_by("origin"):
    print(f"  - {c.origin} (código: {c.code})")

print("\nMapeos:")
for m in MapeoCedis.objects.select_related("cedis_oficial").all():
    print(f"  - '{m.nombre_crudo}' → '{m.cedis_oficial.origin}'")

print("\n✅ Corrección completada.")
print("\n📋 Próximos pasos:")
print("1. Ve a /planificacion/normalizar/")
print("2. Haz clic en 'Limpiar y re-normalizar enero 2026'")
print("3. El tablero se actualizará con los nombres correctos")
