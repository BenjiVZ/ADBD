import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ADB.settings')
django.setup()

from main.models import Sucursal

# CEDIS duplicados que creamos con mayúsculas incorrectas (bpl_id 97-100)
cedis_to_delete = Sucursal.objects.filter(bpl_id__in=[97, 98, 99, 100])

print("🗑️  CEDIS a eliminar:")
for cedis in cedis_to_delete:
    print(f"  - {cedis.name} (bpl_id: {cedis.bpl_id})")

deleted_count = cedis_to_delete.count()
cedis_to_delete.delete()

print(f"\n✅ Eliminados {deleted_count} CEDIS duplicados")
print("\nAhora cuando normalices, el sistema te mostrará los errores de cendis")
print("y TÚ decides si crearlos o mapearlos.")
