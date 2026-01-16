import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ADB.settings')
django.setup()

from main.models import Cendis, MapeoCedis

print("=== TODOS LOS CEDIS EN LA BASE DE DATOS ===")
cedis_all = Cendis.objects.all().order_by("origin")
for c in cedis_all:
    print(f"  ID={c.id}, Código={c.code}, Nombre='{c.origin}'")

print(f"\nTotal: {cedis_all.count()}")

print("\n=== MAPEOS DE CEDIS ===")
mapeos = MapeoCedis.objects.select_related("cedis_oficial").all()
for m in mapeos:
    print(f"  '{m.nombre_crudo}' → '{m.cedis_oficial.origin}'")

print(f"\nTotal mapeos: {mapeos.count()}")
