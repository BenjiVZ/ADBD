"""
Script de prueba para demostrar el sistema de mapeo mejorado por ID.

Este script muestra cómo el sistema ahora busca automáticamente por:
- Nombres (como antes)
- IDs numéricos (nuevo)
- Códigos (nuevo)

Uso:
    python scripts/test_mapeo_por_id.py
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ADB.settings')
django.setup()

from main.models import Cendis, Sucursal, MapeoCedis, MapeoSucursal


def test_mapeo_cedis():
    """Prueba el sistema de mapeo de CEDIS"""
    print("\n" + "="*70)
    print("🏭 PRUEBA DE MAPEO DE CEDIS")
    print("="*70)
    
    # Mostrar todos los CEDIS
    print("\n📋 CEDIS disponibles:")
    for cedis in Cendis.objects.all():
        print(f"   ID: {cedis.id} | Code: {cedis.code or 'N/A'} | Origin: {cedis.origin}")
    
    # Mostrar mapeos
    print("\n🔗 Mapeos de CEDIS existentes:")
    mapeos = MapeoCedis.objects.all()
    if mapeos:
        for mapeo in mapeos:
            cedis = mapeo.cedis_oficial
            print(f"   '{mapeo.nombre_crudo}' → {cedis.origin} (ID: {cedis.id}, Code: {cedis.code or 'N/A'})")
    else:
        print("   (No hay mapeos creados)")
    
    # Simular búsqueda como en normalización
    print("\n🔍 SIMULACIÓN DE BÚSQUEDA:")
    print("\nSupongamos que en tu Excel tienes estos valores en la columna CEDIS:")
    
    # Cargar mapeos como en normalización
    cendis_list = Cendis.objects.all()
    mapeos_cedis = MapeoCedis.objects.select_related('cedis_oficial').all()
    
    # Crear diccionarios de búsqueda
    cendis_map = {}
    for c in cendis_list:
        cendis_map[c.origin.lower()] = c
        cendis_map[str(c.id).lower()] = c
        if c.code:
            cendis_map[c.code.lower()] = c
    
    mapeos_cedis_dict = {}
    for m in mapeos_cedis:
        mapeos_cedis_dict[m.nombre_crudo.lower()] = m.cedis_oficial
        mapeos_cedis_dict[str(m.cedis_oficial.id).lower()] = m.cedis_oficial
        if m.cedis_oficial.code:
            mapeos_cedis_dict[m.cedis_oficial.code.lower()] = m.cedis_oficial
    
    # Probar diferentes búsquedas
    test_values = [
        ("1", "ID numérico del primer CEDIS"),
        ("valencia", "Nombre en minúsculas"),
        ("VALENCIA", "Nombre en mayúsculas"),
    ]
    
    # Agregar búsquedas basadas en CEDIS reales
    if cendis_list.exists():
        first_cedis = cendis_list.first()
        test_values.append((first_cedis.origin, "Nombre oficial"))
        test_values.append((str(first_cedis.id), "ID oficial"))
        if first_cedis.code:
            test_values.append((first_cedis.code, "Código oficial"))
    
    for valor_excel, descripcion in test_values:
        print(f"\n   Valor en Excel: '{valor_excel}' ({descripcion})")
        
        # Búsqueda directa
        cendis_key = valor_excel.strip().lower()
        cedis_encontrado = cendis_map.get(cendis_key)
        
        # Búsqueda en mapeos
        if not cedis_encontrado:
            cedis_encontrado = mapeos_cedis_dict.get(cendis_key)
        
        if cedis_encontrado:
            print(f"   ✅ Encontrado: {cedis_encontrado.origin} (ID: {cedis_encontrado.id})")
        else:
            print(f"   ❌ NO encontrado - Se marcará como error")


def test_mapeo_sucursales():
    """Prueba el sistema de mapeo de Sucursales"""
    print("\n" + "="*70)
    print("🏢 PRUEBA DE MAPEO DE SUCURSALES")
    print("="*70)
    
    # Mostrar algunas sucursales
    print("\n📋 Sucursales disponibles (primeras 10):")
    for sucursal in Sucursal.objects.all()[:10]:
        print(f"   BPL_ID: {sucursal.bpl_id} | Name: {sucursal.name}")
    
    total = Sucursal.objects.count()
    if total > 10:
        print(f"   ... y {total - 10} más")
    
    # Mostrar mapeos
    print("\n🔗 Mapeos de Sucursales existentes:")
    mapeos = MapeoSucursal.objects.all()
    if mapeos:
        for mapeo in mapeos:
            sucursal = mapeo.sucursal_oficial
            print(f"   '{mapeo.nombre_crudo}' → {sucursal.name} (BPL_ID: {sucursal.bpl_id})")
    else:
        print("   (No hay mapeos creados)")
    
    # Simular búsqueda como en normalización
    print("\n🔍 SIMULACIÓN DE BÚSQUEDA:")
    print("\nSupongamos que en tu Excel tienes estos valores en la columna Sucursal:")
    
    # Cargar mapeos como en normalización
    sucursales = Sucursal.objects.all()
    mapeos_sucursales = MapeoSucursal.objects.select_related('sucursal_oficial').all()
    
    # Crear diccionarios de búsqueda
    sucursales_map = {}
    for s in sucursales:
        sucursales_map[s.name.lower()] = s
        sucursales_map[str(s.bpl_id).lower()] = s
    
    mapeos_sucursales_dict = {}
    for m in mapeos_sucursales:
        mapeos_sucursales_dict[m.nombre_crudo.lower()] = m.sucursal_oficial
        mapeos_sucursales_dict[str(m.sucursal_oficial.bpl_id).lower()] = m.sucursal_oficial
    
    # Probar diferentes búsquedas
    test_values = []
    
    # Agregar búsquedas basadas en Sucursales reales
    if sucursales.exists():
        first_sucursal = sucursales.first()
        test_values.append((first_sucursal.name, "Nombre oficial"))
        test_values.append((str(first_sucursal.bpl_id), "BPL_ID oficial"))
        test_values.append((first_sucursal.name.upper(), "Nombre en mayúsculas"))
        test_values.append((first_sucursal.name.lower(), "Nombre en minúsculas"))
    
    for valor_excel, descripcion in test_values:
        print(f"\n   Valor en Excel: '{valor_excel}' ({descripcion})")
        
        # Búsqueda directa
        sucursal_key = valor_excel.strip().lower()
        sucursal_encontrada = sucursales_map.get(sucursal_key)
        
        # Búsqueda en mapeos
        if not sucursal_encontrada:
            sucursal_encontrada = mapeos_sucursales_dict.get(sucursal_key)
        
        if sucursal_encontrada:
            print(f"   ✅ Encontrada: {sucursal_encontrada.name} (BPL_ID: {sucursal_encontrada.bpl_id})")
        else:
            print(f"   ❌ NO encontrada - Se marcará como error")


def main():
    """Función principal"""
    print("\n" + "="*70)
    print("🔍 PRUEBA DEL SISTEMA DE MAPEO MEJORADO (con IDs)")
    print("="*70)
    print("\nEste script demuestra cómo el sistema ahora busca automáticamente por:")
    print("  1. Nombres (búsqueda directa)")
    print("  2. IDs numéricos (búsqueda directa)")
    print("  3. Códigos (búsqueda directa para CEDIS)")
    print("  4. Mapeos creados (incluyen automáticamente los IDs)")
    
    test_mapeo_cedis()
    test_mapeo_sucursales()
    
    print("\n" + "="*70)
    print("✅ PRUEBA COMPLETADA")
    print("="*70)
    print("\n💡 CONCLUSIÓN:")
    print("   - El sistema busca PRIMERO de forma directa (por nombre o ID)")
    print("   - Si no encuentra, busca en mapeos (que ahora incluyen IDs)")
    print("   - Puedes poner nombres o IDs en los Excel indistintamente")
    print("   - Los mapeos que crees funcionarán tanto por nombre como por ID")
    print("\n📚 Para más información, ver: docs/MAPEO_POR_ID.md\n")


if __name__ == "__main__":
    main()
