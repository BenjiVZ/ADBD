"""Listar todas las sucursales"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ADB.settings')
import django
django.setup()

from main.models import Sucursal

print('Sucursales existentes:')
for s in Sucursal.objects.order_by('name'):
    print(f'  - "{s.name}"')
