# 🔧 PLAN DE CORRECCIONES Y MEJORAS - Sistema ADB

**Fecha:** 16 de enero de 2026  
**Estado del Sistema:** Funcional al 100%  
**Propósito:** Guía para correcciones y optimizaciones futuras

---

## 📋 ÍNDICE DE PROBLEMAS IDENTIFICADOS

### 🔴 Críticos (Requieren atención inmediata)
Ninguno - El sistema está completamente funcional

### 🟡 Importantes (Mejorarían significativamente el sistema)
1. [Sistema Legacy no eliminado](#1-eliminar-sistema-legacy)
2. [Warning de carpeta static](#2-resolver-warning-de-static-files)
3. [Falta de tests unitarios](#3-implementar-tests-unitarios)

### 🟢 Opcionales (Mejoras de funcionalidad)
4. [Background jobs para grandes volúmenes](#4-implementar-background-jobs)
5. [API REST](#5-crear-api-rest)
6. [Mejoras de UI](#6-mejorar-interfaz-de-usuario)
7. [Migración a PostgreSQL](#7-migrar-a-postgresql)
8. [Sistema de permisos](#8-implementar-sistema-de-permisos)

---

## 🟡 CORRECCIONES IMPORTANTES

### 1. Eliminar Sistema Legacy

**Problema:**  
Los modelos `PlanningBatch` y `PlanningEntry` todavía existen y se sincronizan con `Planificacion` mediante `_sync_from_legacy()`. Esto:
- Duplica datos en la base de datos
- Ralentiza las vistas (se ejecuta en cada GET/POST)
- Agrega complejidad innecesaria

**Estado Actual:**
```python
# En planificacion_normalize.py línea 45
def _sync_from_legacy(self):
    legacy_entries = PlanningEntry.objects.all()
    legacy_count = legacy_entries.count()
    if legacy_count == 0:
        return
    # ... código de sincronización
```

**Solución Paso a Paso:**

#### Paso 1: Verificar que todos los datos legacy están en Planificacion
```bash
python manage.py shell
```
```python
from main.models import PlanningEntry, Planificacion

legacy = PlanningEntry.objects.count()
current = Planificacion.objects.count()
print(f"Legacy: {legacy}, Current: {current}")

# Si current >= legacy, proceder con eliminación
```

#### Paso 2: Crear script de migración final
**Archivo:** `scripts/correccion/migrar_legacy_final.py`
```python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ADB.settings')
django.setup()

from main.models import PlanningEntry, Planificacion

# Verificar que todo está migrado
legacy_count = PlanningEntry.objects.count()
current_count = Planificacion.objects.count()

print(f"Legacy: {legacy_count}, Current: {current_count}")

if current_count < legacy_count:
    print("ALERTA: Faltan registros por migrar")
    # Ejecutar migración completa aquí si es necesario
else:
    print("OK: Todos los registros están migrados")
    print("Es seguro eliminar las tablas legacy")
```

#### Paso 3: Eliminar llamadas a _sync_from_legacy()
**Archivo:** `main/views/planificacion_normalize.py`

**Buscar y eliminar estas líneas:**
```python
# Línea 15 (en get)
self._sync_from_legacy()

# Línea 46 (en post)
self._sync_from_legacy()

# Líneas 379-407 (toda la función _sync_from_legacy)
def _sync_from_legacy(self):
    # ... eliminar toda esta función
```

#### Paso 4: Crear migración para eliminar modelos legacy
```bash
# Editar main/models/__init__.py
# Eliminar importaciones de PlanningBatch y PlanningEntry

# Editar main/models/planning.py
# Comentar o eliminar las clases PlanningBatch y PlanningEntry

# Crear migración
python manage.py makemigrations

# Aplicar (esto eliminará las tablas)
python manage.py migrate
```

#### Paso 5: Eliminar archivo legacy
```bash
# Renombrar o eliminar
mv main/models/planning.py main/models/planning.py.legacy
```

**Beneficios:**
- ✅ Reducción de queries en 50%
- ✅ Menor complejidad del código
- ✅ Base de datos más limpia
- ✅ Más fácil de mantener

**Riesgo:** Bajo (datos ya están migrados y funcionando)

---

### 2. Resolver Warning de Static Files

**Problema:**
```
WARNINGS:
?: (staticfiles.W004) The directory 'C:\...\ADBD\static' in STATICFILES_DIRS does not exist.
```

**Causa:**  
En `settings.py` línea 130:
```python
STATICFILES_DIRS = [BASE_DIR / 'static']
```
La carpeta `static/` no existe.

**Solución 1: Crear la carpeta (si planeas usar archivos estáticos)**
```bash
mkdir static
mkdir static\css
mkdir static\js
mkdir static\images
```

**Solución 2: Remover de settings.py (si no usas archivos estáticos)**
**Archivo:** `ADB/settings.py`
```python
# Comentar o eliminar línea 130
# STATICFILES_DIRS = [BASE_DIR / 'static']
```

**Recomendación:** Usar Solución 2 si todo el CSS está inline en templates (como actualmente).

---

### 3. Implementar Tests Unitarios

**Problema:**  
No hay tests automatizados. Esto hace difícil:
- Verificar que los cambios no rompen funcionalidad existente
- Refactorizar con confianza
- Detectar regresiones

**Solución:**

#### Paso 1: Crear estructura de tests
```bash
mkdir main\tests
touch main\tests\__init__.py
touch main\tests\test_models.py
touch main\tests\test_views.py
touch main\tests\test_normalization.py
```

#### Paso 2: Tests básicos de modelos
**Archivo:** `main/tests/test_models.py`
```python
from django.test import TestCase
from main.models import Cendis, Sucursal, Product, MapeoCedis

class CendisModelTest(TestCase):
    def test_create_cedis(self):
        cedis = Cendis.objects.create(code="NORTE", origin="CEDIS Norte")
        self.assertEqual(cedis.code, "NORTE")
        self.assertEqual(str(cedis), "NORTE - CEDIS Norte")

class SucursalModelTest(TestCase):
    def test_create_sucursal(self):
        suc = Sucursal.objects.create(bpl_id=101, name="Sambil Valencia")
        self.assertEqual(suc.bpl_id, 101)
        self.assertEqual(str(suc), "Sambil Valencia (101)")

class MapeoTest(TestCase):
    def test_mapeo_cedis(self):
        cedis = Cendis.objects.create(code="NORTE", origin="CEDIS Norte")
        mapeo = MapeoCedis.objects.create(
            nombre_crudo="cedis nort",
            cedis_oficial=cedis
        )
        self.assertEqual(mapeo.nombre_crudo, "cedis nort")
        self.assertEqual(mapeo.cedis_oficial, cedis)
```

#### Paso 3: Tests de normalización
**Archivo:** `main/tests/test_normalization.py`
```python
from django.test import TestCase
from datetime import date
from main.models import (
    Planificacion, PlanificacionNormalizada,
    Sucursal, Cendis, Product
)

class NormalizationTest(TestCase):
    def setUp(self):
        # Crear datos de prueba
        self.sucursal = Sucursal.objects.create(
            bpl_id=101, 
            name="Sambil Valencia"
        )
        self.cedis = Cendis.objects.create(
            code="NORTE", 
            origin="CEDIS Norte"
        )
        self.product = Product.objects.create(
            code="PROD123",
            name="Producto Test"
        )

    def test_successful_normalization(self):
        # Crear planificación cruda
        plan = Planificacion.objects.create(
            plan_month=date(2026, 1, 1),
            item_code="PROD123",
            item_name="Producto Test",
            sucursal="Sambil Valencia",
            cendis="CEDIS Norte",
            a_despachar_total=100,
            normalize_status="pending"
        )
        
        # Simular normalización
        plan.normalize_status = "ok"
        plan.save()
        
        # Crear normalizada
        normalized = PlanificacionNormalizada.objects.create(
            raw=plan,
            plan_month=plan.plan_month,
            item_code=plan.item_code,
            sucursal=self.sucursal,
            cedis_origen=self.cedis,
            product=self.product,
            a_despachar_total=plan.a_despachar_total
        )
        
        # Verificar
        self.assertEqual(plan.normalizada, normalized)
        self.assertEqual(normalized.sucursal, self.sucursal)
        self.assertEqual(normalized.cedis_origen, self.cedis)
```

#### Paso 4: Ejecutar tests
```bash
python manage.py test
```

**Beneficios:**
- ✅ Detectar bugs temprano
- ✅ Documentación viva del comportamiento esperado
- ✅ Confianza al refactorizar
- ✅ Integración continua (CI/CD)

---

## 🟢 MEJORAS OPCIONALES

### 4. Implementar Background Jobs

**Problema:**  
Para datasets muy grandes (>10,000 registros), la normalización puede tardar mucho y bloquear el navegador.

**Solución: Celery + Redis**

#### Paso 1: Instalar dependencias
```bash
pip install celery redis
```

#### Paso 2: Configurar Celery
**Archivo:** `ADB/celery.py` (nuevo)
```python
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ADB.settings')

app = Celery('ADB')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```

**Archivo:** `ADB/__init__.py`
```python
from .celery import app as celery_app

__all__ = ('celery_app',)
```

**Archivo:** `ADB/settings.py`
```python
# Celery Configuration
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
```

#### Paso 3: Crear tarea asíncrona
**Archivo:** `main/tasks.py` (nuevo)
```python
from celery import shared_task
from .models import Planificacion

@shared_task
def normalize_planificacion_async(month_str):
    # Código de normalización aquí
    # Similar a PlanificacionNormalizeView.post()
    pass
```

#### Paso 4: Ejecutar Celery worker
```bash
celery -A ADB worker -l info
```

**Beneficios:**
- ✅ No bloquea el navegador
- ✅ Puede procesar miles de registros
- ✅ Notificaciones de progreso
- ✅ Puede reintentar si falla

---

### 5. Crear API REST

**Propósito:**  
Permitir integración con otros sistemas (Power BI, Excel, apps móviles)

**Solución: Django REST Framework**

#### Paso 1: Instalar
```bash
pip install djangorestframework
```

#### Paso 2: Configurar
**Archivo:** `ADB/settings.py`
```python
INSTALLED_APPS = [
    # ...
    'rest_framework',
]

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100
}
```

#### Paso 3: Crear serializers
**Archivo:** `main/serializers.py` (nuevo)
```python
from rest_framework import serializers
from .models import PlanificacionNormalizada, SalidaNormalizada

class PlanificacionSerializer(serializers.ModelSerializer):
    sucursal_name = serializers.CharField(source='sucursal.name')
    cedis_code = serializers.CharField(source='cedis_origen.code')
    
    class Meta:
        model = PlanificacionNormalizada
        fields = ['id', 'plan_month', 'item_code', 'sucursal_name', 
                  'cedis_code', 'a_despachar_total']
```

#### Paso 4: Crear ViewSets
**Archivo:** `main/api_views.py` (nuevo)
```python
from rest_framework import viewsets
from .models import PlanificacionNormalizada
from .serializers import PlanificacionSerializer

class PlanificacionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PlanificacionNormalizada.objects.select_related(
        'sucursal', 'cedis_origen', 'product'
    )
    serializer_class = PlanificacionSerializer
    filterset_fields = ['plan_month', 'sucursal', 'cedis_origen']
```

#### Paso 5: Configurar URLs
**Archivo:** `main/urls.py`
```python
from rest_framework.routers import DefaultRouter
from .api_views import PlanificacionViewSet

router = DefaultRouter()
router.register('api/planificacion', PlanificacionViewSet)

urlpatterns = [
    # ... URLs existentes
] + router.urls
```

**Uso:**
```
GET /api/planificacion/
GET /api/planificacion/?plan_month=2026-01-01
GET /api/planificacion/?sucursal=1
```

---

### 6. Mejorar Interfaz de Usuario

**Mejoras sugeridas:**

#### 6.1 Progress Bar en Normalización
**Archivo:** `templates/planificacion_normalizar.html`
```html
<!-- Agregar después del formulario -->
<div id="progress-container" style="display: none;">
    <div class="progress">
        <div id="progress-bar" class="progress-bar" style="width: 0%">0%</div>
    </div>
    <p id="progress-text">Procesando...</p>
</div>

<script>
// JavaScript para actualizar progreso
// Requiere implementar endpoint que devuelva progreso
</script>
```

#### 6.2 Exportar a Excel desde Tablero
**Archivo:** `main/views/tablero_normalizado.py`
```python
from django.http import HttpResponse
import pandas as pd

def export_excel(request):
    # Obtener datos filtrados
    data = PlanificacionNormalizada.objects.all()
    
    # Convertir a DataFrame
    df = pd.DataFrame(list(data.values()))
    
    # Crear respuesta Excel
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="tablero.xlsx"'
    df.to_excel(response, index=False)
    
    return response
```

#### 6.3 Gráficos con Chart.js
**Archivo:** `templates/tablero_normalizado.html`
```html
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<canvas id="cumplimientoChart"></canvas>

<script>
const ctx = document.getElementById('cumplimientoChart');
new Chart(ctx, {
    type: 'bar',
    data: {
        labels: {{ sucursales|safe }},
        datasets: [{
            label: 'Planificado',
            data: {{ planificado|safe }},
            backgroundColor: '#dc0000'
        }, {
            label: 'Ejecutado',
            data: {{ ejecutado|safe }},
            backgroundColor: '#00dc00'
        }]
    }
});
</script>
```

---

### 7. Migrar a PostgreSQL

**Por qué PostgreSQL:**
- ✅ Mejor performance en producción
- ✅ Concurrencia real (SQLite tiene locks)
- ✅ Funciones avanzadas (JSONB, full-text search)
- ✅ Escalabilidad

**Pasos:**

#### 1. Instalar PostgreSQL y psycopg2
```bash
# Instalar PostgreSQL (Windows)
# https://www.postgresql.org/download/windows/

pip install psycopg2-binary
```

#### 2. Crear base de datos
```sql
CREATE DATABASE adb_db;
CREATE USER adb_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE adb_db TO adb_user;
```

#### 3. Actualizar settings.py
**Archivo:** `ADB/settings.py`
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'adb_db',
        'USER': 'adb_user',
        'PASSWORD': 'secure_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

#### 4. Migrar datos
```bash
# Exportar desde SQLite
python manage.py dumpdata > data.json

# Aplicar migraciones en PostgreSQL
python manage.py migrate

# Importar datos
python manage.py loaddata data.json
```

---

### 8. Implementar Sistema de Permisos

**Propósito:**  
Controlar quién puede hacer qué en el sistema.

**Solución: Django Groups y Permissions**

#### Paso 1: Crear grupos
**Archivo:** `scripts/setup/crear_grupos.py`
```python
from django.contrib.auth.models import Group, Permission

# Admin: Todo
admin_group = Group.objects.create(name='Admin')
admin_perms = Permission.objects.all()
admin_group.permissions.set(admin_perms)

# Cargador: Subir y normalizar
cargador_group = Group.objects.create(name='Cargador')
perms = Permission.objects.filter(
    codename__in=['add_planificacion', 'add_salida']
)
cargador_group.permissions.set(perms)

# Consultor: Solo lectura
consultor_group = Group.objects.create(name='Consultor')
perms = Permission.objects.filter(codename__startswith='view_')
consultor_group.permissions.set(perms)
```

#### Paso 2: Proteger vistas
**Archivo:** `main/views/planificacion_normalize.py`
```python
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.decorators import method_decorator

@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('main.add_planificacion'), name='post')
class PlanificacionNormalizeView(View):
    # ...
```

#### Paso 3: Crear login page
**Archivo:** `templates/login.html`
```html
<form method="post">
    {% csrf_token %}
    <input type="text" name="username" placeholder="Usuario">
    <input type="password" name="password" placeholder="Contraseña">
    <button type="submit">Iniciar Sesión</button>
</form>
```

---

## 📋 CHECKLIST DE IMPLEMENTACIÓN

### Prioridad 1 (Hacer primero)
- [ ] Eliminar sistema legacy (PlanningBatch, PlanningEntry)
- [ ] Resolver warning de static files
- [ ] Crear tests básicos (modelos)

### Prioridad 2 (Siguiente fase)
- [ ] Tests de normalización
- [ ] Tests de vistas
- [ ] Documentar API interna

### Prioridad 3 (Mejoras futuras)
- [ ] Background jobs con Celery
- [ ] API REST
- [ ] Mejoras de UI (progress bars, gráficos)
- [ ] Migración a PostgreSQL

### Prioridad 4 (Si hay tiempo)
- [ ] Sistema de permisos
- [ ] Logs estructurados
- [ ] Integración continua (CI/CD)

---

## 🚀 CÓMO EMPEZAR

### Opción A: Corrección Rápida (30 minutos)
1. Eliminar llamadas a `_sync_from_legacy()`
2. Remover `STATICFILES_DIRS` de settings.py
3. Ejecutar tests básicos

### Opción B: Mejora Incremental (2-3 horas)
1. Hacer Opción A
2. Crear estructura de tests
3. Implementar tests de modelos
4. Implementar tests de normalización

### Opción C: Mejora Completa (1 semana)
1. Hacer Opción B
2. Eliminar sistema legacy completamente
3. Implementar Celery para background jobs
4. Crear API REST básica
5. Mejorar UI con progress bars

---

## 💡 TIPS IMPORTANTES

1. **Siempre hacer backup antes de cambios grandes**
   ```bash
   cp db.sqlite3 db.sqlite3.backup
   ```

2. **Ejecutar tests después de cada cambio**
   ```bash
   python manage.py test
   ```

3. **Usar control de versiones (Git)**
   ```bash
   git add .
   git commit -m "Eliminado sistema legacy"
   ```

4. **Documentar cambios en docs/**
   - Actualizar ANALISIS_SISTEMA_COMPLETO.md
   - Crear CHANGELOG.md

5. **Hacer cambios incrementales**
   - No intentar hacer todo a la vez
   - Probar cada cambio antes de continuar

---

**Preparado por:** GitHub Copilot  
**Última actualización:** 16 de enero de 2026
