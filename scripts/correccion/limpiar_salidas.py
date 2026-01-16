import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ADB.settings')
django.setup()

from main.models import Salida, SalidaNormalizada
from datetime import date

print("=== LIMPIANDO SALIDAS NORMALIZADAS ===")

# Eliminar todas las salidas normalizadas
deleted = SalidaNormalizada.objects.all().delete()[0]
print(f"✅ Eliminadas {deleted} salidas normalizadas")

# Resetear status de todas las salidas
updated = Salida.objects.all().update(
    normalize_status='pending',
    normalize_notes='',
    normalized_at=None
)
print(f"✅ Reseteadas {updated} salidas a 'pending'")

print("\n📋 Ahora ve a /salidas/normalizar/ y haz clic en 'Normalizar pendientes'")
