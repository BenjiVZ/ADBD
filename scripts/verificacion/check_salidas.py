import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ADB.settings')
django.setup()

from main.models import Salida, SalidaNormalizada, Cendis
from datetime import date

fecha = date(2026, 1, 14)

print("=== ESTADO DE SALIDAS ===")
total = Salida.objects.filter(fecha_salida=fecha).count()
pendientes = Salida.objects.filter(fecha_salida=fecha, normalize_status='pending').count()
ok = Salida.objects.filter(fecha_salida=fecha, normalize_status='ok').count()
error = Salida.objects.filter(fecha_salida=fecha, normalize_status='error').count()

print(f"Fecha: {fecha}")
print(f"Total registros: {total}")
print(f"Pendientes: {pendientes}")
print(f"OK: {ok}")
print(f"Error: {error}")

print("\n=== SALIDAS NORMALIZADAS ===")
normalizadas = SalidaNormalizada.objects.filter(fecha_salida=fecha).count()
print(f"Total normalizadas: {normalizadas}")

if normalizadas > 0:
    print("\nAgrupadas por CEDIS origen:")
    from django.db.models import Count, Sum
    por_cedis = SalidaNormalizada.objects.filter(fecha_salida=fecha).values('cedis_origen__origin').annotate(
        total=Count('id'),
        cantidad=Sum('cantidad')
    ).order_by('-cantidad')
    for grupo in por_cedis:
        print(f"  {grupo['cedis_origen__origin']}: {grupo['total']} registros, {grupo['cantidad']} unidades")

print("\n=== NOMBRES DE CEDIS EN SALIDAS RAW (origen) ===")
nombres_origen = Salida.objects.filter(fecha_salida=fecha).exclude(nombre_almacen_origen__isnull=True).exclude(nombre_almacen_origen="").values_list("nombre_almacen_origen", flat=True).distinct()
for n in sorted(set(nombres_origen)):
    count = Salida.objects.filter(fecha_salida=fecha, nombre_almacen_origen=n).count()
    print(f"  '{n}' → {count} registros")

print("\n=== CEDIS OFICIALES ===")
for c in Cendis.objects.all().order_by("origin"):
    print(f"  '{c.origin}'")
