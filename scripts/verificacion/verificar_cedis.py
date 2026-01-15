import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ADB.settings')
django.setup()

from main.models import Sucursal

print("CEDIS con códigos 1000XXX:")
cedis = Sucursal.objects.filter(bpl_id__gte=1000000).order_by('bpl_id')
print(f"Total: {cedis.count()}")

for c in cedis:
    print(f"  {c.bpl_id} - {c.name}")

if cedis.count() == 0:
    print("\n❌ NO HAY CEDIS CON CÓDIGOS 1000XXX")
    print("\nNecesito CREAR estos CEDIS en Sucursal:")
    print("  1000101 - La Yaguara")
    print("  1000105 - Guatire I")
    print("  1000106 - Guatire II")
    print("  1000114 - Guatire 4")
    print("  1000115 - Guatire 5")
