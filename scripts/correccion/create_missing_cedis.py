import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ADB.settings')
django.setup()

from main.models import Sucursal

print('=' * 80)
print('🔧 CREANDO SUCURSALES FALTANTES PARA NORMALIZACIÓN')
print('=' * 80)

# Mapeo de nombres incorrectos a correctos
sucursales_a_crear = [
    # CEDIS Guatire con diferentes variantes
    {'name': 'GUATIRE 4', 'code': '1000114'},
    {'name': 'GUATIRE 5', 'code': '1000115'},
    {'name': 'GUATIRE I', 'code': '1000105'},
    
    # Servicio Tecnico (parece ser un centro de reparaciones)
    {'name': 'SERVICIO TECNICO', 'code': '9999999'},
    
    # Corporacion Damasco (oficina corporativa?)
    {'name': 'CORPORACION DAMASCO', 'code': '9999998'},
]

print('\n📝 Sucursales a crear:')
created = 0
skipped = 0

for data in sucursales_a_crear:
    # Verificar si ya existe (case-insensitive)
    if Sucursal.objects.filter(name__iexact=data['name']).exists():
        print(f'  ⏭️  "{data["name"]}" - Ya existe')
        skipped += 1
    else:
        Sucursal.objects.create(**data)
        print(f'  ✅ "{data["name"]}" - Creada (código: {data["code"]})')
        created += 1

print('\n' + '=' * 80)
print(f'\n📊 Resumen:')
print(f'   • Creadas: {created}')
print(f'   • Ya existían: {skipped}')
print(f'   • Total en BD ahora: {Sucursal.objects.count()}')

print('\n💡 Siguiente paso:')
print('   Vuelve a normalizar:')
print('   • http://localhost:2222/planificacion/normalizar/')
print('   • http://localhost:2222/salidas/normalizar/')
print('=' * 80)
