"""
Script para agregar sucursales faltantes y corregir mapeos
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ADB.settings')
import django
django.setup()

from main.models import Sucursal

# Sucursales a crear
sucursales_nuevas = [
    {"name": "ARAGUA", "bpl_id": 9999},  # Crear ARAGUA
    {"name": "GUATIRE", "bpl_id": 9998},  # Crear GUATIRE (diferente de GUATIRE 2022)
    {"name": "LECHERIAS", "bpl_id": 9997},  # Crear alias LECHERIAS
]

for s in sucursales_nuevas:
    obj, created = Sucursal.objects.get_or_create(name=s["name"], defaults={"bpl_id": s["bpl_id"]})
    if created:
        print(f"✅ Creada sucursal: {s['name']}")
    else:
        print(f"⚠️ Ya existe sucursal: {s['name']}")

print("\n✅ Sucursales creadas/verificadas")
