"""
Script de verificación para diagnosticar problemas con el tablero normalizado
"""
import os
import sys
import django
from datetime import date, datetime

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ADB.settings')
django.setup()

from main.models import PlanificacionNormalizada, SalidaNormalizada, Cendis, Sucursal
from main.views.tablero_normalizado import TableroNormalizadoView

def main():
    print("="*80)
    print("DIAGNÓSTICO DEL TABLERO NORMALIZADO")
    print("="*80)
    
    # 1. Verificar datos en base de datos
    print("\n1. CONTEO DE REGISTROS:")
    print(f"   - PlanificacionNormalizada: {PlanificacionNormalizada.objects.count()}")
    print(f"   - SalidaNormalizada: {SalidaNormalizada.objects.count()}")
    print(f"   - CEDIS: {Cendis.objects.count()}")
    print(f"   - Sucursales: {Sucursal.objects.count()}")
    
    # 2. Verificar fechas disponibles
    print("\n2. FECHAS DISPONIBLES:")
    plan_dates = list(PlanificacionNormalizada.objects.dates('plan_month', 'day'))
    salida_dates = list(SalidaNormalizada.objects.dates('fecha_salida', 'day'))
    print(f"   - Fechas de planificación: {plan_dates}")
    print(f"   - Fechas de salidas: {salida_dates}")
    
    # 3. Probar la vista
    print("\n3. PRUEBA DE LA VISTA:")
    view = TableroNormalizadoView()
    
    # Obtener fechas disponibles desde la vista
    plan_dates_view = view._available_plan_dates()
    salida_dates_view = view._available_salida_dates()
    print(f"   - Vista plan_dates: {plan_dates_view}")
    print(f"   - Vista salida_dates: {salida_dates_view}")
    
    # 4. Probar con la primera fecha disponible
    if plan_dates_view and salida_dates_view:
        test_plan_date = plan_dates_view[0]
        test_salida_date = salida_dates_view[0]
        
        print(f"\n4. PROBANDO CON FECHAS: plan={test_plan_date}, salida={test_salida_date}")
        
        # Obtener datos de plan
        plan_data = view._plan_by_dest_group(test_plan_date)
        print(f"   - Orígenes en plan_data: {len(plan_data)}")
        for origin_key, data in plan_data.items():
            origin_id, origin_name = origin_key
            total_destinos = len(data)
            total_qty = sum(
                sum(groups.values())
                for dest_data in data.values()
                for groups in [dest_data.get('groups', {})]
            )
            print(f"     * {origin_name} (ID={origin_id}): {total_destinos} destinos, cantidad total={total_qty}")
        
        # Obtener datos de salidas
        salida_data = view._salidas_by_origin_dest_group(test_salida_date, selected_origin_id=None)
        print(f"   - Orígenes en salida_data: {len(salida_data)}")
        for origin_key, data in salida_data.items():
            origin_id, origin_name = origin_key
            total_destinos = len(data)
            total_qty = sum(
                sum(groups.values())
                for dest_data in data.values()
                for groups in [dest_data.get('groups', {})]
            )
            print(f"     * {origin_name} (ID={origin_id}): {total_destinos} destinos, cantidad total={total_qty}")
        
        # Construir tabla
        table = view._build_comparison_table(plan_data, salida_data, test_plan_date, test_salida_date)
        print(f"\n5. TABLA CONSTRUIDA:")
        print(f"   - Total de orígenes en tabla: {len(table)}")
        for origen in table:
            print(f"     * {origen['origin_name']}: {len(origen['destinos'])} destinos")
            for destino in origen['destinos'][:3]:  # Primeros 3 destinos
                print(f"       - {destino['name']}: {len(destino['grupos'])} grupos")
        
        # Calcular resumen
        summary = view._calculate_summary(table)
        print(f"\n6. RESUMEN:")
        print(f"   - Total Planificado: {summary['total_plan']}")
        print(f"   - Total Enviado: {summary['total_salidas']}")
        print(f"   - % Cumplimiento: {summary['percent_general']}%")
        print(f"   - Total Destinos: {summary['total_destinos']}")
    else:
        print("\n❌ NO HAY FECHAS DISPONIBLES")
    
    # 5. Verificar registros con problemas
    print("\n7. VERIFICACIÓN DE DATOS:")
    
    # Planificaciones sin CEDIS origen
    sin_cedis = PlanificacionNormalizada.objects.filter(cedis_origen__isnull=True).count()
    print(f"   - Planificaciones sin CEDIS origen: {sin_cedis}")
    
    # Planificaciones sin sucursal
    sin_sucursal_plan = PlanificacionNormalizada.objects.filter(sucursal__isnull=True).count()
    print(f"   - Planificaciones sin sucursal: {sin_sucursal_plan}")
    
    # Salidas sin CEDIS origen
    salidas_sin_cedis = SalidaNormalizada.objects.filter(cedis_origen__isnull=True).count()
    print(f"   - Salidas sin CEDIS origen: {salidas_sin_cedis}")
    
    # Salidas sin sucursal destino
    salidas_sin_sucursal = SalidaNormalizada.objects.filter(sucursal_destino__isnull=True).count()
    print(f"   - Salidas sin sucursal destino: {salidas_sin_sucursal}")
    
    print("\n" + "="*80)
    print("DIAGNÓSTICO COMPLETADO")
    print("="*80)

if __name__ == "__main__":
    main()
