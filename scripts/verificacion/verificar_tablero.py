import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ADB.settings')
import django
django.setup()

from main.models import PlanificacionNormalizada, SalidaNormalizada, Pvp
from collections import defaultdict
from decimal import Decimal
from datetime import date

plan_date = date(2026, 1, 14)
salida_date = date(2026, 1, 14)

# Cargar PVP
pvp_map = {p.sku.lower(): p.price for p in Pvp.objects.all()}

print(f'=== TABLERO PARA {plan_date} (Plan) y {salida_date} (Salida) ===\n')

# Agrupar por CEDIS
cedis_data = defaultdict(lambda: {
    'plan_unid': 0,
    'plan_usd': Decimal('0'),
    'salida_plan_unid': 0,
    'salida_plan_usd': Decimal('0'),
    'salida_noplan_unid': 0,
    'salida_noplan_usd': Decimal('0')
})

# Obtener planificaciones
plans = PlanificacionNormalizada.objects.filter(plan_month=plan_date).select_related('cedis_origen', 'product', 'sucursal')

# Crear lookup de planificaciones
plan_lookup = {}
for p in plans:
    cedis = p.cedis_origen.origin if p.cedis_origen else 'SIN CEDIS'
    qty = int(p.a_despachar_total or 0)
    price = pvp_map.get(p.item_code.lower() if p.item_code else '', Decimal('0'))
    
    cedis_data[cedis]['plan_unid'] += qty
    cedis_data[cedis]['plan_usd'] += Decimal(qty) * price
    
    # Guardar en lookup para matching
    key = (
        p.cedis_origen_id,
        p.item_code.lower() if p.item_code else '',
        p.sucursal_id
    )
    plan_lookup[key] = True

# Obtener salidas
salidas = SalidaNormalizada.objects.filter(fecha_salida=salida_date).select_related('cedis_origen', 'product', 'sucursal_destino')

for s in salidas:
    cedis = s.cedis_origen.origin if s.cedis_origen else 'SIN CEDIS'
    qty = int(s.cantidad or 0)
    price = pvp_map.get(s.sku.lower() if s.sku else '', Decimal('0'))
    
    # Verificar si está planificada
    key = (
        s.cedis_origen_id,
        s.sku.lower() if s.sku else '',
        s.sucursal_destino_id
    )
    
    if key in plan_lookup:
        cedis_data[cedis]['salida_plan_unid'] += qty
        cedis_data[cedis]['salida_plan_usd'] += Decimal(qty) * price
    else:
        cedis_data[cedis]['salida_noplan_unid'] += qty
        cedis_data[cedis]['salida_noplan_usd'] += Decimal(qty) * price

# Mostrar resultados
print('%-15s %10s %15s %12s %15s %10s %10s %12s %18s %12s %15s' % (
    'CEDIS', 'Plan Unid', 'Plan USD', 'Desp Plan U', 'Desp Plan $', '% Unid', '% USD', 
    'NO Plan U', 'NO Plan $', 'Total U', 'Total $'
))
print('-' * 160)

for cedis in sorted(cedis_data.keys()):
    d = cedis_data[cedis]
    pct_unid = (d['salida_plan_unid'] / d['plan_unid'] * 100) if d['plan_unid'] > 0 else 0
    pct_usd = (float(d['salida_plan_usd']) / float(d['plan_usd']) * 100) if d['plan_usd'] > 0 else 0
    total_unid = d['salida_plan_unid'] + d['salida_noplan_unid']
    total_usd = d['salida_plan_usd'] + d['salida_noplan_usd']
    
    print('%-15s %10d $%14.2f %12d $%14.2f %9.1f%% %9.1f%% %12d $%17.2f %12d $%14.2f' % (
        cedis, d['plan_unid'], d['plan_usd'], 
        d['salida_plan_unid'], d['salida_plan_usd'],
        pct_unid, pct_usd,
        d['salida_noplan_unid'], d['salida_noplan_usd'],
        total_unid, total_usd
    ))

print('\n📊 Este es el cálculo que debería mostrar el tablero')
