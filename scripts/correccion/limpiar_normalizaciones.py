"""
Script para limpiar todas las normalizaciones y restablecer el estado inicial.
Borra todos los registros normalizados y resetea el estado de las tablas originales.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ADB.settings')
django.setup()

from django.db import transaction
from main.models.planificacion import Planificacion
from main.models.salida import Salida
from main.models.planificacion_normalizada import PlanificacionNormalizada
from main.models.salida_normalizada import SalidaNormalizada


def limpiar_normalizaciones():
    """Limpia todas las normalizaciones y resetea estados."""
    
    print("=" * 80)
    print("LIMPIEZA DE NORMALIZACIONES")
    print("=" * 80)
    
    # Mostrar estado actual
    print("\n📊 Estado ANTES de la limpieza:")
    planificacion_total = Planificacion.objects.count()
    planificacion_ok = Planificacion.objects.filter(normalize_status='ok').count()
    planificacion_norm = PlanificacionNormalizada.objects.count()
    
    salida_total = Salida.objects.count()
    salida_ok = Salida.objects.filter(normalize_status='ok').count()
    salida_norm = SalidaNormalizada.objects.count()
    
    print(f"\nPlanificacion:")
    print(f"  - Total: {planificacion_total}")
    print(f"  - Estado 'ok': {planificacion_ok}")
    print(f"  - Registros normalizados: {planificacion_norm}")
    
    print(f"\nSalida:")
    print(f"  - Total: {salida_total}")
    print(f"  - Estado 'ok': {salida_ok}")
    print(f"  - Registros normalizados: {salida_norm}")
    
    # Confirmación
    print("\n" + "⚠️ " * 30)
    print("⚠️  ADVERTENCIA: Esta operación:")
    print("⚠️  1. Borrará TODOS los registros de PlanificacionNormalizada")
    print("⚠️  2. Borrará TODOS los registros de SalidaNormalizada")
    print("⚠️  3. Reseteará el estado de TODOS los registros a 'pending'")
    print("⚠️ " * 30)
    
    confirmacion = input("\n¿Deseas continuar? (escribe 'SI' para confirmar): ")
    
    if confirmacion.strip().upper() != 'SI':
        print("\n❌ Operación cancelada por el usuario.")
        return
    
    print("\n🔄 Iniciando limpieza...")
    
    try:
        with transaction.atomic():
            # 1. Borrar registros normalizados
            print("\n🗑️  Borrando registros normalizados...")
            deleted_plan = PlanificacionNormalizada.objects.all().delete()
            print(f"   ✓ PlanificacionNormalizada: {deleted_plan[0]} registros eliminados")
            
            deleted_sal = SalidaNormalizada.objects.all().delete()
            print(f"   ✓ SalidaNormalizada: {deleted_sal[0]} registros eliminados")
            
            # 2. Resetear estado de Planificacion
            print("\n🔄 Reseteando estado de Planificacion...")
            updated_plan = Planificacion.objects.all().update(
                normalize_status='pending',
                normalize_notes='',
                normalized_at=None
            )
            print(f"   ✓ {updated_plan} registros actualizados a 'pending'")
            
            # 3. Resetear estado de Salida
            print("\n🔄 Reseteando estado de Salida...")
            updated_sal = Salida.objects.all().update(
                normalize_status='pending',
                normalize_notes='',
                normalized_at=None
            )
            print(f"   ✓ {updated_sal} registros actualizados a 'pending'")
        
        print("\n" + "=" * 80)
        print("✅ LIMPIEZA COMPLETADA CON ÉXITO")
        print("=" * 80)
        
        # Mostrar estado final
        print("\n📊 Estado DESPUÉS de la limpieza:")
        planificacion_pending = Planificacion.objects.filter(normalize_status='pending').count()
        planificacion_norm_final = PlanificacionNormalizada.objects.count()
        
        salida_pending = Salida.objects.filter(normalize_status='pending').count()
        salida_norm_final = SalidaNormalizada.objects.count()
        
        print(f"\nPlanificacion:")
        print(f"  - Total: {planificacion_total}")
        print(f"  - Estado 'pending': {planificacion_pending}")
        print(f"  - Registros normalizados: {planificacion_norm_final}")
        
        print(f"\nSalida:")
        print(f"  - Total: {salida_total}")
        print(f"  - Estado 'pending': {salida_pending}")
        print(f"  - Registros normalizados: {salida_norm_final}")
        
        print("\n✨ El sistema está listo para normalizar desde cero.")
        print("   Puedes iniciar el proceso en:")
        print("   - http://localhost:2222/planificacion/normalizar/")
        print("   - http://localhost:2222/salidas/normalizar/")
        
    except Exception as e:
        print(f"\n❌ ERROR durante la limpieza: {e}")
        print("   La transacción ha sido revertida.")
        raise


if __name__ == '__main__':
    limpiar_normalizaciones()
