import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ADB.settings')
django.setup()

from main.models import MapeoCedis, Cendis

print("=== MAPEOS DE CEDIS ACTUALES ===")
for m in MapeoCedis.objects.select_related('cedis_oficial').all():
    print(f"  '{m.nombre_crudo}' → '{m.cedis_oficial.origin}' (cedis_id={m.cedis_oficial_id})")

print("\n=== CEDIS (verificar que los IDs coincidan) ===")
for c in Cendis.objects.all():
    print(f"  ID={c.id}, Nombre='{c.origin}'")
