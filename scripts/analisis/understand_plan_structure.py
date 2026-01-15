import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ADB.settings')
django.setup()

from main.models import Planificacion, Sucursal

print('=' * 80)
print('🔍 ENTENDIENDO ESTRUCTURA DE PLANIFICACION')
print('=' * 80)

# Ver algunos ejemplos
print('\n📋 Ejemplos de registros de Planificacion:\n')
for p in Planificacion.objects.all()[:5]:
    print(f'  Plan Month: {p.plan_month}')
    print(f'  Producto: {p.item_code} - {p.item_name}')
    print(f'  cendis (CEDIS): "{p.cendis}"')
    print(f'  sucursal (DESTINO): "{p.sucursal}"')
    print(f'  Cantidad: {p.a_despachar_total}')
    print(f'  ---')

print('\n' + '=' * 80)
print('\n💡 INTERPRETACIÓN:')
print('   cendis = CEDIS desde donde se enviará')
print('   sucursal = Sucursal destino que recibirá el producto')
print('\n   Para el tablero necesitamos:')
print('   1. CEDIS origen (cendis)')
print('   2. Sucursal destino (sucursal)')
print('   3. Comparar plan vs salidas por esta combinación')
print('=' * 80)
