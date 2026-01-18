"""
Script de prueba para verificar la funcionalidad de corrección de CEDIS y Sucursales.
Muestra los datos que se procesarían sin hacer cambios reales.
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ADB.settings')
django.setup()

from django.db.models import Count
from main.models import Cendis, Sucursal, Planificacion, Salida

def verificar_cedis():
    print("\n" + "="*80)
    print("🏭 VERIFICACIÓN DE CEDIS")
    print("="*80)
    
    # CEDIS oficiales
    cedis_oficiales = Cendis.objects.all()
    print(f"\n✅ CEDIS Oficiales registrados: {cedis_oficiales.count()}")
    for cedis in cedis_oficiales[:5]:
        print(f"   ID: {cedis.id:3d} | Code: {cedis.code:15s} | Origin: {cedis.origin}")
    if cedis_oficiales.count() > 5:
        print(f"   ... y {cedis_oficiales.count() - 5} más")
    
    # Nombres únicos en Planificacion
    cedis_planificacion = (
        Planificacion.objects.exclude(cendis__isnull=True)
        .exclude(cendis="")
        .values("cendis")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    
    print(f"\n📊 Nombres únicos en Planificación: {cedis_planificacion.count()}")
    for item in cedis_planificacion[:10]:
        print(f"   '{item['cendis']}' → {item['count']} registros")
    
    # Nombres únicos en Salida
    almacen_salida = (
        Salida.objects.exclude(nombre_almacen_origen__isnull=True)
        .exclude(nombre_almacen_origen="")
        .values("nombre_almacen_origen")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    
    print(f"\n📊 Nombres únicos en Salidas: {almacen_salida.count()}")
    for item in almacen_salida[:10]:
        print(f"   '{item['nombre_almacen_origen']}' → {item['count']} registros")


def verificar_sucursales():
    print("\n" + "="*80)
    print("🏪 VERIFICACIÓN DE SUCURSALES")
    print("="*80)
    
    # Sucursales oficiales
    sucursales_oficiales = Sucursal.objects.all()
    print(f"\n✅ Sucursales Oficiales registradas: {sucursales_oficiales.count()}")
    for sucursal in sucursales_oficiales[:5]:
        print(f"   BPL ID: {sucursal.bpl_id:5d} | Nombre: {sucursal.name}")
    if sucursales_oficiales.count() > 5:
        print(f"   ... y {sucursales_oficiales.count() - 5} más")
    
    # Nombres únicos en Planificacion
    sucursales_plan = (
        Planificacion.objects.exclude(sucursal__isnull=True)
        .exclude(sucursal="")
        .values("sucursal")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    
    print(f"\n📊 Nombres únicos en Planificación: {sucursales_plan.count()}")
    for item in sucursales_plan[:10]:
        print(f"   '{item['sucursal']}' → {item['count']} registros")
    
    # Nombres únicos en Salida (almacen_destino)
    almacen_dest = (
        Salida.objects.exclude(nombre_almacen_destino__isnull=True)
        .exclude(nombre_almacen_destino="")
        .values("nombre_almacen_destino")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    
    print(f"\n📊 Nombres únicos en Salidas (almacén destino): {almacen_dest.count()}")
    for item in almacen_dest[:10]:
        print(f"   '{item['nombre_almacen_destino']}' → {item['count']} registros")


if __name__ == "__main__":
    try:
        verificar_cedis()
        verificar_sucursales()
        
        print("\n" + "="*80)
        print("✅ Verificación completada")
        print("="*80)
        print("\n📌 Siguiente paso:")
        print("   1. Abrir: http://localhost:8000/correccion/cedis/")
        print("   2. Abrir: http://localhost:8000/correccion/sucursales/")
        print("   3. Agrupar variantes y asignar códigos oficiales")
        print("   4. Aplicar correcciones")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
