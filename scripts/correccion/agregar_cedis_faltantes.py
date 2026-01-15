import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ADB.settings')
django.setup()

from main.models import Cendis, Sucursal, Salida
from django.db import transaction

print("=" * 80)
print("SOLUCIÓN: Agregar CEDIS/Sucursales faltantes de Salidas")
print("=" * 80)

# Obtener valores únicos de origen en Salida
origenes = set(
    Salida.objects.exclude(nombre_sucursal_origen='')
    .values_list('nombre_sucursal_origen', flat=True)
    .distinct()
)

# Valores que NO están en CEDIS ni en Sucursal
cedis_existentes = set(c.origin.lower() for c in Cendis.objects.all())
sucursales_existentes = set(s.name.lower() for s in Sucursal.objects.all())

print(f"\n📊 Análisis de Orígenes:")
print(f"  Total únicos en Salida: {len(origenes)}")
print(f"  CEDIS existentes: {len(cedis_existentes)}")
print(f"  Sucursales existentes: {len(sucursales_existentes)}")

# Clasificar
origenes_son_sucursales = []
origenes_desconocidos = []

for origen in origenes:
    origen_lower = origen.strip().lower()
    if origen_lower in cedis_existentes:
        continue  # Ya está en CEDIS, OK
    elif origen_lower in sucursales_existentes:
        origenes_son_sucursales.append(origen)  # Es una sucursal (transferencia entre tiendas)
    else:
        origenes_desconocidos.append(origen)  # No está en ninguna tabla

print(f"\n✅ Orígenes que son CEDIS existentes: {len(origenes) - len(origenes_son_sucursales) - len(origenes_desconocidos)}")
print(f"⚠️ Orígenes que son SUCURSALES (transferencias): {len(origenes_son_sucursales)}")
print(f"❌ Orígenes DESCONOCIDOS: {len(origenes_desconocidos)}")

if origenes_son_sucursales:
    print(f"\n📋 Orígenes que son Sucursales (transferencias entre tiendas):")
    for nombre in sorted(origenes_son_sucursales):
        count = Salida.objects.filter(nombre_sucursal_origen__iexact=nombre).count()
        print(f"  - {nombre:30} ({count} registros)")

if origenes_desconocidos:
    print(f"\n❌ Orígenes DESCONOCIDOS (no están en CEDIS ni Sucursales):")
    for nombre in sorted(origenes_desconocidos):
        count = Salida.objects.filter(nombre_sucursal_origen__iexact=nombre).count()
        print(f"  - {nombre:30} ({count} registros)")
    
    print(f"\n🔧 OPCIONES:")
    print(f"  1. Agregar como CEDIS si son centros de distribución")
    print(f"  2. Ignorar si son errores de datos")
    print(f"  3. Crear mapeo manual en el resolvedor de errores")

# Agregar CEDIS comunes que faltan
print(f"\n" + "=" * 80)
print("SUGERENCIA: Agregar CEDIS comunes")
print("=" * 80)

cedis_sugeridos = [
    ("CORPORACION DAMASCO", "1000120"),  # Aparece en errores
]

print(f"\nCEDIS sugeridos para agregar:")
for origen, code in cedis_sugeridos:
    existe = Cendis.objects.filter(origin__iexact=origen).exists()
    if not existe:
        count = Salida.objects.filter(nombre_sucursal_origen__iexact=origen).count()
        print(f"  ➕ {origen:30} (code: {code}) - {count} registros afectados")
    else:
        print(f"  ✅ {origen:30} ya existe")

respuesta = input("\n¿Agregar estos CEDIS? (s/n): ").strip().lower()

if respuesta == 's':
    with transaction.atomic():
        for origen, code in cedis_sugeridos:
            if not Cendis.objects.filter(origin__iexact=origen).exists():
                Cendis.objects.create(origin=origen, code=code)
                print(f"  ✅ Creado: {origen}")
        
        # Marcar salidas afectadas como pending
        for origen, _ in cedis_sugeridos:
            updated = Salida.objects.filter(
                nombre_sucursal_origen__iexact=origen,
                normalize_status='error'
            ).update(normalize_status='pending')
            if updated:
                print(f"  ♻️ {updated} salidas marcadas como 'pending' para re-procesar")
    
    print(f"\n✅ CEDIS agregados exitosamente")
else:
    print(f"\n⏭️ Operación cancelada")

print(f"\n" + "=" * 80)
print("FIN")
print("=" * 80)
