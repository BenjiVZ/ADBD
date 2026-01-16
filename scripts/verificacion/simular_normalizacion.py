import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ADB.settings')
django.setup()

from main.models import Salida, SalidaNormalizada, Cendis, MapeoCedis
from datetime import date

fecha = date(2026, 1, 14)

print("=== SIMULACIÓN DE NORMALIZACIÓN ===")

# Cargar mapeos
mapeos_cedis = MapeoCedis.objects.select_related('cedis_oficial').all()
mapeos_cedis_dict = {m.nombre_crudo.lower(): m.cedis_oficial for m in mapeos_cedis}
print(f"Mapeos CEDIS: {list(mapeos_cedis_dict.keys())}")

# Cargar CEDIS
cendis_list = Cendis.objects.all()
cendis_map = {c.origin.lower(): c for c in cendis_list}
print(f"CEDIS oficiales: {list(cendis_map.keys())}")

# Probar con cada registro de salida
salidas = Salida.objects.filter(fecha_salida=fecha)
print(f"\nTotal salidas: {salidas.count()}")

resultados = {}
for raw in salidas:
    origen = raw.nombre_almacen_origen or ""
    origen_key = origen.strip().lower()
    
    # Buscar en CEDIS
    cedis_origen = cendis_map.get(origen_key)
    
    # Si no, buscar en mapeos
    if not cedis_origen:
        cedis_origen = mapeos_cedis_dict.get(origen_key)
    
    if cedis_origen:
        cedis_nombre = cedis_origen.origin
    else:
        cedis_nombre = f"NO ENCONTRADO: {origen}"
    
    if cedis_nombre not in resultados:
        resultados[cedis_nombre] = {"count": 0, "origen_raw": origen}
    resultados[cedis_nombre]["count"] += 1

print("\n=== RESULTADOS ESPERADOS ===")
for cedis, info in sorted(resultados.items()):
    print(f"  {cedis}: {info['count']} registros (desde '{info['origen_raw']}')")
