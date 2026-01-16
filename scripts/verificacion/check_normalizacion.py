import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ADB.settings')
django.setup()

from main.models import Planificacion, PlanificacionNormalizada, Cendis
from datetime import date

mes = date(2026, 1, 14)

print("=== ESTADO DE PLANIFICACIÓN ===")
total = Planificacion.objects.filter(plan_month=mes).count()
pendientes = Planificacion.objects.filter(plan_month=mes, normalize_status='pending').count()
ok = Planificacion.objects.filter(plan_month=mes, normalize_status='ok').count()
error = Planificacion.objects.filter(plan_month=mes, normalize_status='error').count()

print(f"Total registros: {total}")
print(f"Pendientes: {pendientes}")
print(f"OK: {ok}")
print(f"Error: {error}")

print("\n=== REGISTROS CON ERROR ===")
errores = Planificacion.objects.filter(plan_month=mes, normalize_status='error')[:10]
for e in errores:
    print(f"  CEDIS: '{e.cendis}', Sucursal: '{e.sucursal}', Notas: {e.normalize_notes}")

print("\n=== NORMALIZADOS ===")
normalizados = PlanificacionNormalizada.objects.filter(plan_month=mes).count()
print(f"Total normalizados: {normalizados}")

if normalizados > 0:
    print("\nPrimeros 10 normalizados:")
    for n in PlanificacionNormalizada.objects.filter(plan_month=mes)[:10]:
        print(f"  CEDIS: {n.cedis_origen.origin if n.cedis_origen else 'NULL'}, Sucursal: {n.sucursal.name if n.sucursal else 'NULL'}")
    
    print("\nAgrupados por CEDIS:")
    from django.db.models import Count
    por_cedis = PlanificacionNormalizada.objects.filter(plan_month=mes).values('cedis_origen__origin').annotate(total=Count('id')).order_by('-total')
    for grupo in por_cedis:
        print(f"  {grupo['cedis_origen__origin']}: {grupo['total']} registros")
