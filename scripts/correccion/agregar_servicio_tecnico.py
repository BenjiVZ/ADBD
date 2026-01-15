import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ADB.settings')
django.setup()

from main.models import Cendis, Salida
from django.db import transaction

print("Agregando 'Servicio Tecnico' como CEDIS...")

with transaction.atomic():
    c = Cendis.objects.create(origin='Servicio Tecnico', code='1000999')
    print(f"  Creado: {c.origin} (code: {c.code})")
    
    updated = Salida.objects.filter(
        nombre_sucursal_origen__iexact='Servicio Tecnico',
        normalize_status='error'
    ).update(normalize_status='pending', normalize_notes='')
    
    print(f"  {updated} salidas marcadas como pending")

print("\nListo! Todos los CEDIS agregados.")
print(f"Total CEDIS: {Cendis.objects.count()}")
print(f"Errores restantes: {Salida.objects.filter(normalize_status='error').count()}")
