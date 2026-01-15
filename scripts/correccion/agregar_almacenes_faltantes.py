import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ADB.settings')
django.setup()

from main.models import Cendis, Sucursal, Salida
from django.db import transaction

print("=" * 80)
print("SOLUCIÓN: Agregar VALENCIA como CEDIS (almacén)")
print("=" * 80)

# Verificar todos los orígenes únicos en Salida que tienen "Almacen" en nombre_almacen_origen
print("\n1. Buscando orígenes con almacén especificado...")
salidas_con_almacen = Salida.objects.exclude(nombre_almacen_origen='').values(
    'nombre_sucursal_origen', 'nombre_almacen_origen'
).distinct()

origenes_que_son_almacenes = set()
for s in salidas_con_almacen:
    origen = s['nombre_sucursal_origen']
    almacen = s['nombre_almacen_origen']
    if almacen and 'almac' in almacen.lower():  # Si menciona "almacén"
        origenes_que_son_almacenes.add(origen)

print(f"\nOrígenes que SON almacenes (tienen 'Almacen' en nombre_almacen_origen):")
for origen in sorted(origenes_que_son_almacenes):
    # Verificar si está en CEDIS
    en_cedis = Cendis.objects.filter(origin__iexact=origen).exists()
    en_sucursal = Sucursal.objects.filter(name__iexact=origen).exists()
    count = Salida.objects.filter(nombre_sucursal_origen__iexact=origen).count()
    
    status = "✅ En CEDIS" if en_cedis else "❌ NO en CEDIS"
    tipo = f"| En Sucursales: {'Sí' if en_sucursal else 'No'}"
    
    print(f"  {status:20} | {origen:30} | {count:5} registros {tipo}")

# Agregar los que faltan
print("\n" + "=" * 80)
print("2. Agregando almacenes faltantes a CEDIS...")
print("=" * 80)

almacenes_a_agregar = []
next_code = 1000200  # Empezar desde código alto

for origen in origenes_que_son_almacenes:
    if not Cendis.objects.filter(origin__iexact=origen).exists():
        almacenes_a_agregar.append((origen, str(next_code)))
        next_code += 1

if almacenes_a_agregar:
    print(f"\nSe agregarán {len(almacenes_a_agregar)} almacenes:")
    for origen, code in almacenes_a_agregar:
        count = Salida.objects.filter(nombre_sucursal_origen__iexact=origen).count()
        print(f"  + {origen:30} → Code: {code} ({count} registros)")
    
    respuesta = input("\n¿Proceder? (s/n): ").strip().lower()
    
    if respuesta == 's':
        with transaction.atomic():
            for origen, code in almacenes_a_agregar:
                Cendis.objects.create(origin=origen, code=code)
                print(f"  ✅ Creado: {origen}")
            
            # Marcar salidas afectadas como pending
            for origen, _ in almacenes_a_agregar:
                updated = Salida.objects.filter(
                    nombre_sucursal_origen__iexact=origen
                ).update(normalize_status='pending', normalize_notes='')
                print(f"  ♻️ {updated} salidas con origen '{origen}' marcadas como pending")
        
        print("\n✅ COMPLETADO")
        print(f"\nTotal CEDIS ahora: {Cendis.objects.count()}")
    else:
        print("\n⏭️ Operación cancelada")
else:
    print("\n✅ Todos los almacenes ya están en CEDIS")

print("\n" + "=" * 80)
