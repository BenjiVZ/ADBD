import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ADB.settings')
django.setup()

from main.models import Cendis, Salida
from django.db import transaction

print("=" * 80)
print("REVERTIR: Eliminar CEDIS agregados automáticamente")
print("=" * 80)

# Los CEDIS originales son solo estos 5
cedis_originales = [
    'La Yaguara',
    'Guatire I',
    'Guatire II',
    'Guatire 4',
    'Guatire 5'
]

print("\nCEDIS originales (los que deberían existir):")
for c in cedis_originales:
    print(f"  - {c}")

print("\nCEDIS actuales en la base de datos:")
for c in Cendis.objects.all():
    print(f"  - ID:{c.id} | Code:{c.code} | Origin:{c.origin}")

# Identificar CEDIS agregados automáticamente
cedis_a_eliminar = []
for c in Cendis.objects.all():
    if c.origin not in cedis_originales:
        cedis_a_eliminar.append(c)

if cedis_a_eliminar:
    print(f"\n❌ CEDIS agregados automáticamente (a eliminar):")
    for c in cedis_a_eliminar:
        count = Salida.objects.filter(nombre_sucursal_origen__iexact=c.origin).count()
        print(f"  - {c.origin} (Code: {c.code}) - {count} salidas afectadas")
    
    respuesta = input("\n¿Eliminar estos CEDIS? (s/n): ").strip().lower()
    
    if respuesta == 's':
        with transaction.atomic():
            for c in cedis_a_eliminar:
                # Marcar salidas como pending antes de eliminar
                Salida.objects.filter(
                    nombre_sucursal_origen__iexact=c.origin
                ).update(normalize_status='pending', normalize_notes='')
                
                print(f"  🗑️ Eliminando: {c.origin}")
                c.delete()
        
        print("\n✅ CEDIS eliminados")
        print(f"Total CEDIS ahora: {Cendis.objects.count()}")
    else:
        print("\n⏭️ Operación cancelada")
else:
    print("\n✅ No hay CEDIS agregados automáticamente")

print("\n" + "=" * 80)
