import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ADB.settings')
django.setup()

from main.models import Planificacion, Sucursal

print("=" * 80)
print("ANÁLISIS COMPLETO: cendis vs CEDIS en Sucursal")
print("=" * 80)

# 1. Valores únicos de cendis
origenes = list(Planificacion.objects.values_list('cendis', flat=True).distinct().order_by('cendis'))
print(f"\n1️⃣  cendis en Planificacion (tabla cruda): {len(origenes)}")
for origen in origenes:
    if origen:
        print(f"   - {origen}")

# 2. CEDIS que el usuario dice que tiene
cedis_usuario = {
    'La Yaguara': 1000101,
    'Guatire I': 1000105,
    'Guatire II': 1000106,
    'Guatire 4': 1000114,
    'Guatire 5': 1000115,
}

print(f"\n2️⃣  CEDIS que el usuario dice que tiene: {len(cedis_usuario)}")
for nombre, codigo in cedis_usuario.items():
    print(f"   - {codigo} {nombre}")

# 3. Buscar esos CEDIS en la tabla Sucursal
print(f"\n3️⃣  ¿Esos CEDIS existen en la tabla Sucursal?")
for nombre, codigo in cedis_usuario.items():
    existe = Sucursal.objects.filter(name__iexact=nombre).exists()
    existe_codigo = Sucursal.objects.filter(bpl_id=codigo).exists()
    
    status = "✅ EXISTE" if existe else "❌ NO EXISTE"
    status_codigo = "✅ EXISTE" if existe_codigo else "❌ NO EXISTE"
    
    print(f"   - {nombre}: {status}")
    print(f"     bpl_id {codigo}: {status_codigo}")
    
    if existe:
        suc = Sucursal.objects.get(name__iexact=nombre)
        print(f"     → Encontrado: {suc.name} (bpl_id: {suc.bpl_id})")

# 4. Lo que sí existe en Sucursal con nombres similares
print(f"\n4️⃣  Lo que SÍ existe en Sucursal (similares):")
guatires = Sucursal.objects.filter(name__icontains='guatire')
for s in guatires:
    print(f"   - {s.bpl_id} {s.name}")

yaguaras = Sucursal.objects.filter(name__icontains='yaguara')
for s in yaguaras:
    print(f"   - {s.bpl_id} {s.name}")

print("\n" + "=" * 80)
print("CONCLUSIÓN:")
print("=" * 80)
print("Los cendis NO coinciden exactamente con los CEDIS en Sucursal.")
print("Por eso el sistema te muestra errores.")
print("\nSOLUCIÓN:")
print("Crea los CEDIS faltantes en /planificacion/errores/ con los bpl_ids correctos:")
for nombre, codigo in cedis_usuario.items():
    print(f"  • {nombre} → bpl_id: {codigo}")
