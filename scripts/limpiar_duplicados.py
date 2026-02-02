"""
Script para eliminar duplicados en PlanificacionNormalizada
"""
import os
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'ADB.settings'
django.setup()

from main.models import PlanificacionNormalizada
from django.db.models import Count, Min

print("=" * 60)
print("ELIMINANDO DUPLICADOS EN PLANIFICACION NORMALIZADA")
print("=" * 60)

# Contar antes
total_antes = PlanificacionNormalizada.objects.count()
print(f"\n📊 Registros antes: {total_antes}")

# Encontrar duplicados por (item_code, sucursal, cedis_origen, plan_month)
duplicates = (
    PlanificacionNormalizada.objects
    .values('item_code', 'sucursal', 'cedis_origen', 'plan_month')
    .annotate(
        count=Count('id'),
        min_id=Min('id')
    )
    .filter(count__gt=1)
)

print(f"\n🔍 Combinaciones duplicadas encontradas: {duplicates.count()}")

# Recopilar IDs a MANTENER (el primer registro de cada grupo)
ids_to_keep = set()
for dup in duplicates:
    ids_to_keep.add(dup['min_id'])

print(f"✅ IDs a mantener: {len(ids_to_keep)}")

# Eliminar los duplicados (todos excepto el min_id de cada grupo)
deleted_count = 0
for dup in duplicates:
    # Eliminar todos los registros del grupo EXCEPTO el min_id
    deleted = PlanificacionNormalizada.objects.filter(
        item_code=dup['item_code'],
        sucursal=dup['sucursal'],
        cedis_origen=dup['cedis_origen'],
        plan_month=dup['plan_month']
    ).exclude(id=dup['min_id']).delete()
    deleted_count += deleted[0]

print(f"\n🗑️ Registros eliminados: {deleted_count}")

# Contar después
total_despues = PlanificacionNormalizada.objects.count()
print(f"📊 Registros después: {total_despues}")

# Verificar el total de unidades
from django.db.models import Sum
total_unidades = PlanificacionNormalizada.objects.aggregate(total=Sum('a_despachar_total'))
print(f"\n✅ Total unidades planificadas: {total_unidades['total']}")

print("\n" + "=" * 60)
print("PROCESO COMPLETADO")
print("=" * 60)
