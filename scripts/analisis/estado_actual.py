import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ADB.settings')
django.setup()

from main.models import (
    Planificacion, PlanificacionNormalizada,
    Salida, SalidaNormalizada,
    Cendis, Sucursal, Product,
    MapeoCedis, MapeoSucursal
)

print("=" * 80)
print("ESTADO ACTUAL DEL SISTEMA")
print("=" * 80)

# Maestros
print("\nMAESTROS DE DATOS:")
print(f"  - Productos: {Product.objects.count():,}")
print(f"  - Sucursales: {Sucursal.objects.count():,}")
print(f"  - CEDIS: {Cendis.objects.count():,}")
print(f"  - Mapeos CEDIS: {MapeoCedis.objects.count():,}")
print(f"  - Mapeos Sucursales: {MapeoSucursal.objects.count():,}")

# Planificación
print("\nPLANIFICACION:")
total_plan = Planificacion.objects.count()
pending_plan = Planificacion.objects.filter(normalize_status='pending').count()
ok_plan = Planificacion.objects.filter(normalize_status='ok').count()
error_plan = Planificacion.objects.filter(normalize_status='error').count()
ignored_plan = Planificacion.objects.filter(normalize_status='ignored').count()
normalized_plan = PlanificacionNormalizada.objects.count()

print(f"  - Total registros: {total_plan:,}")
print(f"  - Normalizados (ok): {ok_plan:,}")
print(f"  - Pendientes: {pending_plan:,}")
print(f"  - Con errores: {error_plan:,}")
print(f"  - Ignorados: {ignored_plan:,}")
print(f"  - Registros en PlanificacionNormalizada: {normalized_plan:,}")

# Salidas
print("\nSALIDAS:")
total_sal = Salida.objects.count()
pending_sal = Salida.objects.filter(normalize_status='pending').count()
ok_sal = Salida.objects.filter(normalize_status='ok').count()
error_sal = Salida.objects.filter(normalize_status='error').count()
normalized_sal = SalidaNormalizada.objects.count()

print(f"  - Total registros: {total_sal:,}")
print(f"  - Normalizados (ok): {ok_sal:,}")
print(f"  - Pendientes: {pending_sal:,}")
print(f"  - Con errores: {error_sal:,}")
print(f"  - Registros en SalidaNormalizada: {normalized_sal:,}")

# Verificar consistencia
print("\nVERIFICACION DE CONSISTENCIA:")
inconsistencia_plan = ok_plan - normalized_plan
inconsistencia_sal = ok_sal - normalized_sal

if inconsistencia_plan == 0:
    print(f"  OK - Planificacion consistente (ok={ok_plan:,}, normalizada={normalized_plan:,})")
else:
    print(f"  ALERTA - Planificacion inconsistente: {inconsistencia_plan:,} registros marcados 'ok' sin normalizar")

if inconsistencia_sal == 0:
    print(f"  OK - Salidas consistente (ok={ok_sal:,}, normalizada={normalized_sal:,})")
else:
    print(f"  ALERTA - Salidas inconsistente: {inconsistencia_sal:,} registros marcados 'ok' sin normalizar")

print("\n" + "=" * 80)
