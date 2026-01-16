import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ADB.settings')
django.setup()

from main.models import Salida, Sucursal

# Ver las salidas con error
errores = Salida.objects.filter(normalize_status="error")
print(f"Total errores: {errores.count()}\n")

# Ver qué nombres de sucursal destino están causando error
print("=== DETALLES DE ERRORES ===")
for e in errores[:20]:
    print(f"Fecha: {e.fecha_salida}")
    print(f"  Destino: repr='{repr(e.nombre_sucursal_destino)}' str='{e.nombre_sucursal_destino}'")
    print(f"  Propuesto: '{e.sucursal_destino_propuesto}'")
    print(f"  Notas: {e.normalize_notes}")
    print()

# Ver todas las sucursales únicas en Salida que contienen "ARAGUA"
print("\n=== NOMBRES CON 'ARAGUA' ===")
nombres_destino = Salida.objects.exclude(nombre_sucursal_destino__isnull=True).exclude(nombre_sucursal_destino="").values_list("nombre_sucursal_destino", flat=True).distinct()
for n in sorted(nombres_destino):
    if "ARAGUA" in n.upper():
        print(f"  repr='{repr(n)}' str='{n}'")

print(f"\nTotal nombres únicos: {len(nombres_destino)}")
