import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ADB.settings')
django.setup()

from main.models import Cendis, Sucursal, Salida
from django.db import transaction

print("=" * 80)
print("AGREGANDO CEDIS Y SUCURSALES FALTANTES")
print("=" * 80)

# 1. Agregar CEDIS faltantes
cedis_a_agregar = [
    ("CORPORACION DAMASCO", "1000120"),
]

print("\nAGREGANDO CEDIS FALTANTES:")
with transaction.atomic():
    for origen, code in cedis_a_agregar:
        if not Cendis.objects.filter(origin__iexact=origen).exists():
            Cendis.objects.create(origin=origen, code=code)
            print(f"  + Creado CEDIS: {origen} (code: {code})")
            
            # Marcar salidas afectadas como pending
            updated = Salida.objects.filter(
                nombre_sucursal_origen__iexact=origen,
                normalize_status='error'
            ).update(normalize_status='pending', normalize_notes='')
            print(f"    -> {updated} salidas marcadas como 'pending'")
        else:
            print(f"  = Ya existe: {origen}")

# 2. Agregar Sucursales faltantes
sucursales_a_agregar = [
    ("Servicio Tecnico", 999),  # BPL ID temporal
]

print("\nAGREGANDO SUCURSALES FALTANTES:")
with transaction.atomic():
    for nombre, bpl_id in sucursales_a_agregar:
        if not Sucursal.objects.filter(name__iexact=nombre).exists():
            # Verificar que el BPL ID no esté en uso
            while Sucursal.objects.filter(bpl_id=bpl_id).exists():
                bpl_id += 1
            
            Sucursal.objects.create(name=nombre, bpl_id=bpl_id)
            print(f"  + Creada Sucursal: {nombre} (BPL: {bpl_id})")
            
            # Marcar salidas afectadas como pending
            updated = Salida.objects.filter(
                nombre_sucursal_destino__iexact=nombre,
                normalize_status='error'
            ).update(normalize_status='pending', normalize_notes='')
            print(f"    -> {updated} salidas marcadas como 'pending'")
        else:
            print(f"  = Ya existe: {nombre}")

print("\n" + "=" * 80)
print("RESUMEN FINAL")
print("=" * 80)

print(f"\nCEDIS totales: {Cendis.objects.count()}")
for c in Cendis.objects.all():
    print(f"  - {c.code}: {c.origin}")

print(f"\nSalidas pendientes: {Salida.objects.filter(normalize_status='pending').count()}")
print(f"Salidas con error: {Salida.objects.filter(normalize_status='error').count()}")

print("\n" + "=" * 80)
print("LISTO! Ahora normaliza desde:")
print("  http://localhost:2222/salidas/normalizar/")
print("=" * 80)
