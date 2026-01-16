import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ADB.settings')
django.setup()

from main.models import Cendis, MapeoCedis, Planificacion

print("=== PASO 1: Eliminar CEDIS y mapeos incorrectos ===")

# Eliminar mapeos
MapeoCedis.objects.all().delete()
print("✅ Mapeos eliminados")

# Eliminar CEDIS incorrectos
Cendis.objects.all().delete()
print("✅ CEDIS eliminados")

print("\n=== PASO 2: Crear CEDIS correctos basados en tu segunda tabla ===")

cedis_correctos = [
    {"origin": "La Yaguara", "code": "1000101"},
    {"origin": "Guatire 1", "code": "1000102"},
    {"origin": "Guatire 2", "code": "1000103"},
    {"origin": "García Tuñón", "code": "1000104"},
    {"origin": "Forum", "code": "1000105"},
]

for data in cedis_correctos:
    cedis, created = Cendis.objects.get_or_create(
        origin=data["origin"],
        defaults={"code": data["code"]}
    )
    if created:
        print(f"✅ Creado: {cedis.origin} (código: {cedis.code})")
    else:
        print(f"⚠️ Ya existe: {cedis.origin}")

print("\n=== PASO 3: Verificar nombres en Planificación ===")
nombres_plan = Planificacion.objects.exclude(cendis__isnull=True).exclude(cendis="").values_list("cendis", flat=True).distinct()
print("Nombres encontrados en Planificación:")
for n in sorted(set(nombres_plan)):
    print(f"  '{n}'")

print("\n=== PASO 4: Crear mapeos automáticos basados en patrones ===")

# Mapeos sugeridos
mapeos_sugeridos = {
    "Guatire I": "Guatire 1",
    "Guatire II": "Guatire 2",
    "Guatire 4": "García Tuñón",
    "Guatire 5": "Forum",
}

for nombre_crudo, nombre_oficial in mapeos_sugeridos.items():
    try:
        cedis_oficial = Cendis.objects.get(origin=nombre_oficial)
        mapeo, created = MapeoCedis.objects.get_or_create(
            nombre_crudo=nombre_crudo,
            defaults={"cedis_oficial": cedis_oficial}
        )
        if created:
            print(f"✅ Mapeo creado: '{nombre_crudo}' → '{nombre_oficial}'")
        else:
            print(f"⚠️ Mapeo ya existe: '{nombre_crudo}' → '{nombre_oficial}'")
    except Cendis.DoesNotExist:
        print(f"❌ CEDIS no encontrado: '{nombre_oficial}'")

# Mapeos de Salida (los que ya tenías)
mapeos_salida = {
    "Almacen General LA YAGUARA": "La Yaguara",
    "Almacen Principal G4": "García Tuñón",
    "Almacen Principal G5": "Forum",
    "Almacén General Galpón Guatire": "Guatire 1",
    "Almacén Principal Guatire 2": "Guatire 2",
}

for nombre_crudo, nombre_oficial in mapeos_salida.items():
    try:
        cedis_oficial = Cendis.objects.get(origin=nombre_oficial)
        mapeo, created = MapeoCedis.objects.get_or_create(
            nombre_crudo=nombre_crudo,
            defaults={"cedis_oficial": cedis_oficial}
        )
        if created:
            print(f"✅ Mapeo creado: '{nombre_crudo}' → '{nombre_oficial}'")
    except Cendis.DoesNotExist:
        print(f"❌ CEDIS no encontrado: '{nombre_oficial}'")

print("\n=== RESUMEN FINAL ===")
print(f"CEDIS oficiales: {Cendis.objects.count()}")
print(f"Mapeos: {MapeoCedis.objects.count()}")
print("\n✅ Corrección completada. Ahora ve a /planificacion/normalizar/ y haz 'Limpiar y re-normalizar'")
