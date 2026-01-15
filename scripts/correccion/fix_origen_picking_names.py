import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ADB.settings')
django.setup()

from main.models import Planificacion

# Mapeo de nombres incorrectos a correctos
CORRECTIONS = {
    'Guatire I': 'GUATIRE I',
    'Guatire II': 'GUATIRE II',
    'Guaitre 4': 'GUATIRE 4',  # Corrige el typo también
    'Guatire 5': 'GUATIRE 5',
    'La Yaguara': 'LA YAGUARA',
    'la yaguara': 'LA YAGUARA',
    'guatire i': 'GUATIRE I',
    'guatire ii': 'GUATIRE II',
    'guatire 4': 'GUATIRE 4',
    'guatire 5': 'GUATIRE 5',
}

total_updated = 0

for incorrect, correct in CORRECTIONS.items():
    count = Planificacion.objects.filter(cendis=incorrect).update(cendis=correct)
    if count > 0:
        print(f"✅ Actualizado '{incorrect}' → '{correct}' ({count} registros)")
        total_updated += count
    else:
        print(f"ℹ️  No hay registros con '{incorrect}'")

print(f"\n✅ Total actualizado: {total_updated} registros")

# Mostrar los valores únicos actuales
print("\n📋 Valores actuales de cendis:")
origenes = Planificacion.objects.values_list('cendis', flat=True).distinct().order_by('cendis')
for origen in origenes:
    print(f"  - {origen}")
