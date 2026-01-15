# 📊 ANÁLISIS COMPLETO DEL SISTEMA ADD

**Fecha:** 14 de enero de 2026  
**Proyecto:** ADB - Sistema de Análisis y Distribución de Datos  
**Framework:** Django 6.0.1  
**Base de Datos:** SQLite3

---

## 🎯 PROPÓSITO DEL SISTEMA

Sistema web para **normalizar, validar y analizar datos de distribución logística** entre CEDIS (Centros de Distribución) y Sucursales. Permite:

1. **Importar datos** desde archivos Excel (Planificación y Salidas)
2. **Normalizar datos crudos** vinculándolos con maestros (Productos, Sucursales, CEDIS)
3. **Resolver errores** de forma interactiva con sugerencias inteligentes
4. **Comparar plan vs. ejecución** en un tablero analítico
5. **Detectar productos faltantes** en catálogos

---

## 📁 ARQUITECTURA DEL PROYECTO

### Estructura de Carpetas
```
ADD/
├── ADB/                    # Configuración Django
│   ├── settings.py        # Configuración principal
│   ├── urls.py            # Rutas principales
│   └── wsgi.py            # WSGI application
├── main/                   # Aplicación principal
│   ├── models/            # Modelos de datos
│   ├── views/             # Lógica de vistas
│   ├── migrations/        # Migraciones de BD
│   ├── templatetags/      # Template tags personalizados
│   └── admin.py           # Interfaz admin
├── templates/             # Plantillas HTML
├── static/                # Archivos estáticos
├── media/                 # Archivos subidos
└── Scripts/               # Scripts de análisis
```

---

## 🗄️ MODELO DE DATOS

### 1️⃣ **Maestros de Datos** (Tablas de Referencia)

#### **Product** - Catálogo de Productos
```python
- code: str (único)           # Código del producto
- name: str                   # Nombre descriptivo
- group: str                  # Grupo/categoría
- manufacturer: str           # Fabricante
- category: str               # Categoría
- subcategory: str            # Subcategoría
- size: str                   # Tamaño/presentación
```
**Uso:** Maestro principal de productos. Se vincula con Planificación y Salidas.

#### **Sucursal** - Tiendas/Puntos de Venta
```python
- bpl_id: int (único)         # ID único de SAP/ERP
- name: str (único)           # Nombre de la sucursal
- created_at: datetime
```
**Uso:** Representa destinos (tiendas) donde se distribuyen productos.

#### **Cendis** - Centros de Distribución
```python
- code: str (único)           # Código del CEDIS
- origin: str                 # Nombre del origen
```
**Uso:** Representa orígenes (almacenes) desde donde se despachan productos.

#### **Pvp** - Precios de Venta al Público
```python
- product: FK(Product)        # Producto asociado
- sku: str (único)            # SKU específico
- description: str            # Descripción del SKU
- price: Decimal              # Precio de venta
```
**Uso:** Mapeo de SKUs a productos del maestro.

---

### 2️⃣ **Datos Crudos** (Raw Data)

#### **Planificacion** - Plan Mensual de Distribución
```python
- plan_month: date                    # Mes de planificación
- tipo_carga: str                     # Tipo de carga
- item_code: str                      # Código del producto
- item_name: str                      # Nombre del producto
- sucursal: str                       # Nombre de sucursal (sin normalizar)
- cendis: str                         # Nombre de CEDIS origen (sin normalizar)
- a_despachar_total: Decimal          # Cantidad a despachar
- normalize_status: str               # pending | ok | error | ignored
- normalize_notes: str                # Notas de errores
- normalized_at: datetime             # Fecha de normalización
```
**Estados:**
- `pending`: Pendiente de normalizar
- `ok`: Normalizado exitosamente
- `error`: Error en normalización
- `ignored`: Marcado para ignorar

**Índices:**
- `(normalize_status, plan_month)` - Filtrado rápido
- `(item_code)` - Búsqueda de productos
- `(sucursal)` - Búsqueda de sucursales
- `(plan_month, item_code, sucursal)` - Índice compuesto

#### **Salida** - Registro de Salidas Reales
```python
- salida: str                         # Número de salida
- fecha_salida: date                  # Fecha de salida
- nombre_sucursal_origen: str         # CEDIS origen (sin normalizar)
- nombre_almacen_origen: str          # Almacén específico
- sku: str                            # Código del producto
- descripcion: str                    # Descripción del SKU
- cantidad: Decimal                   # Cantidad despachada
- sucursal_destino_propuesto: str     # Destino propuesto
- entrada: str                        # Número de entrada
- fecha_entrada: date                 # Fecha de entrada
- nombre_sucursal_destino: str        # Sucursal destino (sin normalizar)
- nombre_almacen_destino: str         # Almacén específico
- comments: str                       # Comentarios
- normalize_status: str               # pending | ok | error
- normalize_notes: str                # Notas de errores
- normalized_at: datetime             # Fecha de normalización
```

**Índices:**
- `(normalize_status, fecha_salida)` - Filtrado rápido
- `(sku)` - Búsqueda de productos
- `(nombre_sucursal_origen)` - Búsqueda de origen
- `(nombre_sucursal_destino)` - Búsqueda de destino

---

### 3️⃣ **Datos Normalizados** (Cleaned Data)

#### **PlanificacionNormalizada** - Plan Vinculado a Maestros
```python
- raw: OneToOne(Planificacion)        # Registro crudo original
- plan_month: date
- tipo_carga: str
- item_code: str
- item_name: str
- sucursal: FK(Sucursal)              # ✅ Vinculado a maestro
- cedis_origen: FK(Cendis)            # ✅ Vinculado a maestro CEDIS
- product: FK(Product)                # ✅ Vinculado a maestro
- cendis: str                         # Referencia al nombre original
- a_despachar_total: Decimal
```

**Relación 1:1 con Planificacion:**
- Cada registro `raw` tiene máximo 1 normalizado
- `raw.normalizada` accede al registro normalizado
- Si se borra el raw, se borra el normalizado (`CASCADE`)

**Índices:**
- `(plan_month, item_code)` - Queries frecuentes
- `(plan_month, sucursal)` - Tablero por sucursal

#### **SalidaNormalizada** - Salida Vinculada a Maestros
```python
- raw: OneToOne(Salida)               # Registro crudo original
- salida: str
- fecha_salida: date
- sku: str
- descripcion: str
- cantidad: Decimal
- cedis_origen: FK(Cendis)            # ✅ Origen vinculado a CEDIS
- sucursal_destino: FK(Sucursal)      # ✅ Destino vinculado a Sucursal
- product: FK(Product)                # ✅ Producto vinculado
- origen_nombre: str                  # Nombre original del origen
- destino_nombre: str                 # Nombre original del destino
- entrada: str
- fecha_entrada: date
- comments: str
```

**Índices:**
- `(fecha_salida, sku)` - Queries frecuentes
- `(fecha_salida, cedis_origen)` - Tablero por origen
- `(fecha_salida, sucursal_destino)` - Tablero por destino

---

### 4️⃣ **Modelos Legacy** (Sistema Antiguo)

#### **PlanningBatch** - Lote de Planificación
```python
- plan_date: date
- sheet_name: str
- source_filename: str
- created_at: datetime
```

#### **PlanningEntry** - Entrada de Planificación Legacy
Campos extensos incluyendo `stock_tienda`, `stock_cedis`, `necesidad_urgente`, etc.

**Nota:** Sistema legacy que se está migrando a `Planificacion`.

---

## 🔄 FLUJO DE DATOS

### Flujo de Planificación

```
1. IMPORTACIÓN
   Excel → PlanningUploadView → PlanningBatch/PlanningEntry (legacy)
                              → Planificacion (raw)

2. SINCRONIZACIÓN
   PlanningEntry → _sync_from_legacy() → Planificacion

3. NORMALIZACIÓN
   Planificacion (raw) → PlanificacionNormalizeView
                      → Busca en maestros (Sucursal, Cendis, Product)
                      → PlanificacionNormalizada (con FKs)
   
   Si hay errores:
   Planificacion.normalize_status = "error"
   Planificacion.normalize_notes = "Sucursal no encontrada: XXX"

4. RESOLUCIÓN DE ERRORES
   PlanificacionErrorResolverView
   → Usuario crea/mapea Sucursales/CEDIS/Productos faltantes
   → Registros se marcan como "pending" para re-normalizar
   → Se ejecuta normalización nuevamente

5. VISUALIZACIÓN
   TableroNormalizadoView → Muestra datos de PlanificacionNormalizada
```

### Flujo de Salidas

```
1. IMPORTACIÓN
   Excel → SalidaUploadView → Salida (raw)

2. NORMALIZACIÓN
   Salida (raw) → SalidaNormalizeView
               → Busca en maestros (Cendis, Sucursal, Product)
               → SalidaNormalizada (con FKs)
   
   Si hay errores:
   Salida.normalize_status = "error"
   Salida.normalize_notes = "CEDIS origen no encontrado: XXX"

3. RESOLUCIÓN DE ERRORES
   SalidaErrorResolverView
   → Usuario crea/mapea CEDIS/Sucursales/Productos faltantes
   → Registros se marcan como "pending" para re-normalizar

4. VISUALIZACIÓN
   TableroNormalizadoView → Compara PlanificacionNormalizada vs SalidaNormalizada
```

---

## 🚀 VISTAS Y FUNCIONALIDADES

### 1️⃣ **Landing y Navegación**

#### `LandingView` - Página Principal
- **URL:** `/`
- **Template:** `landing.html` (probablemente)
- **Función:** Página de inicio con links a funcionalidades

#### `UploadMenuView` - Menú de Subidas
- **URL:** `/subidas/`
- **Template:** `upload_menu.html`
- **Función:** Menú centralizado para subir diferentes tipos de archivos

---

### 2️⃣ **Carga de Planificación**

#### `PlanningUploadView` - Subir Excel de Planificación
- **URL:** `/planificacion/`
- **Template:** `planning_upload.html`
- **Método GET:** Muestra formulario de subida
- **Método POST:** 
  - Lee archivo Excel (.xlsx)
  - Detecta hojas disponibles
  - Muestra preview de datos
  - Crea `PlanningBatch` y `PlanningEntry` (legacy)

**Características:**
- ✅ Normalización de headers (quita acentos, espacios)
- ✅ Detección automática de columnas por nombres flexibles
- ✅ Validación de tipos de datos (decimales, fechas, booleanos)
- ✅ Preview antes de confirmar carga
- ✅ Selección de hoja específica

---

### 3️⃣ **Normalización de Planificación**

#### `PlanificacionNormalizeView` - Normalizar Datos de Planificación
- **URL:** `/planificacion/normalizar/`
- **Template:** `planificacion_normalizar.html`
- **Método GET:** 
  - Muestra resumen de registros (pending, ok, error)
  - Filtro por mes
  - Lista de errores (50 primeros)
  - Lista de pendientes (50 primeros)
  
- **Método POST:** 
  - Ejecuta normalización en lote
  - Pre-carga maestros en memoria (evita N+1 queries)
  - Usa transacciones atómicas
  - Bulk create/update para eficiencia

**Proceso de Normalización:**
```python
Para cada Planificacion (raw):
  1. Buscar sucursal en maestro (por nombre)
  2. Buscar CEDIS origen en maestro Cendis (por nombre)
  3. Buscar producto en maestro (por código)
  
  Si todo OK:
    - Crear/actualizar PlanificacionNormalizada
    - raw.normalize_status = "ok"
  
  Si hay errores:
    - raw.normalize_status = "error"
    - raw.normalize_notes = "Sucursal no encontrada: XXX"
```

**Optimizaciones Implementadas:**
- ✅ Pre-carga de maestros en memoria (1 query por maestro)
- ✅ Bulk create/update (1 query para múltiples registros)
- ✅ Transacciones atómicas (rollback si falla algo)
- ✅ Índices optimizados para queries frecuentes
- ✅ Eliminado `unique_together` conflictivo

**Rendimiento:**
- Antes: ~3000 queries para 1000 registros (30-60s)
- Después: ~5 queries para 1000 registros (<5s)

---

### 4️⃣ **Resolución de Errores de Planificación**

#### `PlanificacionErrorResolverView` - Resolver Errores Interactivamente
- **URL:** `/planificacion/errores/`
- **Template:** `planificacion_error_resolver.html`
- **Método GET:** 
  - Agrupa errores por tipo:
    - CEDIS origen no encontrados
    - Sucursales no encontradas
    - Productos no encontrados
  - Genera sugerencias con **fuzzy matching** (difflib)
  - Muestra contador de registros afectados

- **Método POST - Acciones:**

**1. `create_cedis_origen` - Crear CEDIS Origen Faltante**
```python
Inputs: cedis_name, cedis_code
Acción:
  1. Crear en tabla Cendis
  2. Actualizar Planificacion(cendis=cedis_name) → normalize_status="pending"
  3. Redirect a error resolver
```

**2. `map_cedis_origen` - Mapear CEDIS a Existente**
```python
Inputs: original_name, target_name
Acción:
  1. Actualizar Planificacion(cendis=original_name) → cendis=target_name
  2. Marcar como pending para re-normalizar
  3. Redirect a error resolver
```

**3. `create_sucursal` - Crear Sucursal Faltante**
```python
Inputs: sucursal_name, bpl_id
Acción:
  1. Crear en tabla Sucursal
  2. Actualizar Planificacion(sucursal=sucursal_name) → normalize_status="pending"
```

**4. `map_sucursal` - Mapear Sucursal a Existente**
```python
Inputs: original_name, target_name
Acción:
  1. Actualizar Planificacion(sucursal=original_name) → sucursal=target_name
  2. Marcar como pending para re-normalizar
```

**5. `create_product` - Crear Producto Faltante**
```python
Inputs: product_code, product_name, product_group (opcional)
Acción:
  1. Crear en tabla Product
  2. Actualizar Planificacion(item_code=product_code) → normalize_status="pending"
```

**6. `map_product` - Mapear Producto a Existente**
```python
Inputs: original_code, target_code
Acción:
  1. Actualizar Planificacion(item_code=original_code) → item_code=target_code
  2. Marcar como pending para re-normalizar
```

**7. `ignore_errors` - Ignorar Errores (solo Planificación)**
```python
Inputs: error_ids (lista)
Acción:
  1. Actualizar Planificacion(id__in=error_ids) → normalize_status="ignored"
  2. No aparecen más en lista de errores
```

**Fuzzy Matching:**
- Usa `difflib.get_close_matches()`
- Threshold: 0.6 (60% similitud)
- Retorna top 3 sugerencias
- Ejemplo: "CEDIS NORT" → sugiere "CEDIS NORTE"

---

### 5️⃣ **Carga y Normalización de Salidas**

#### `SalidaUploadView` - Subir Excel de Salidas
- **URL:** `/salidas/`
- **Template:** `salida_upload.html`
- Similar a `PlanningUploadView` pero para Salidas

#### `SalidaNormalizeView` - Normalizar Salidas
- **URL:** `/salidas/normalizar/`
- **Template:** `salida_normalizar.html`
- Similar a `PlanificacionNormalizeView`

**Diferencias Clave:**
- **Origen:** Debe ser CEDIS (tabla `Cendis`)
- **Destino:** Debe ser Sucursal (tabla `Sucursal`)
- **Producto:** Se busca por SKU en lugar de item_code
- **No tiene estado "ignored"** (solo pending, ok, error)

#### `SalidaErrorResolverView` - Resolver Errores de Salidas
- **URL:** `/salidas/errores/`
- **Template:** `salida_error_resolver.html`
- Funcionalidad similar a `PlanificacionErrorResolverView`
- **No tiene opción "ignorar"**

---

### 6️⃣ **Tablero Analítico**

#### `TableroNormalizadoView` - Comparación Plan vs. Salidas
- **URL:** `/tablero/normalizado/`
- **Template:** `tablero_normalizado.html`
- **Función:** Dashboard de análisis comparativo

**Características:**
- ✅ Filtro por fecha de plan
- ✅ Filtro por fecha de salida
- ✅ Filtro por CEDIS origen
- ✅ Comparación por origen → destino → grupo de producto
- ✅ Cálculo de % cumplimiento
- ✅ Resumen agregado
- ✅ Export a CSV

**Estructura de Comparación:**
```
ORIGEN (CEDIS)
  └─ DESTINO (Sucursal)
      └─ GRUPO (Categoría de producto)
          ├─ Plan: 1000 unidades
          ├─ Salida Real: 850 unidades
          └─ % Cumplimiento: 85%
```

**Queries Optimizadas:**
- `select_related()` para evitar N+1
- Agregación en Python (no en BD) para flexibilidad
- Índices en campos de filtrado frecuente

---

### 7️⃣ **Detección de Productos Faltantes**

#### `MissingProductsView` - Productos Sin Maestro
- **URL:** `/faltantes/`
- **Template:** `missing_products.html`
- **Función:** Lista productos en datos crudos que no existen en maestro

#### `PvpIssuesView` - Problemas con SKUs/PVP
- **URL:** `/pvp/faltantes/`
- **Template:** `pvp_issues.html`
- **Función:** Lista SKUs sin mapeo a productos del maestro

---

## 🔧 OPTIMIZACIONES IMPLEMENTADAS

### 1️⃣ **Eliminación de N+1 Queries**

**Problema Anterior:**
```python
for raw in queryset:
    sucursal = Sucursal.objects.filter(name__iexact=raw.sucursal).first()  # Query!
    product = Product.objects.filter(code__iexact=raw.item_code).first()   # Query!
    # 1000 registros = 2000-3000 queries
```

**Solución Implementada:**
```python
# Pre-cargar TODO en memoria (1 query por tabla)
sucursales = Sucursal.objects.all()
products = Product.objects.all()

sucursales_map = {s.name.lower(): s for s in sucursales}
products_map = {p.code.lower(): p for p in products}

for raw in queryset:
    sucursal = sucursales_map.get(raw.sucursal.strip().lower())  # Lookup en memoria!
    product = products_map.get(raw.item_code.strip().lower())    # Sin queries!
```

**Resultado:**
- Antes: ~3000 queries
- Después: ~5 queries

---

### 2️⃣ **Bulk Operations**

**Problema Anterior:**
```python
for raw in queryset:
    norm = PlanificacionNormalizada(...)
    norm.save()  # 1 query por registro!
```

**Solución Implementada:**
```python
to_create = []
to_update = []

for raw in queryset:
    if existing:
        to_update.append(...)
    else:
        to_create.append(...)

# 1 query para todos los creates
PlanificacionNormalizada.objects.bulk_create(to_create)

# 1 query para todos los updates
PlanificacionNormalizada.objects.bulk_update(to_update, fields=[...])
```

---

### 3️⃣ **Transacciones Atómicas**

**Problema Anterior:**
```python
# Si falla a mitad, algunos registros quedan marcados como "ok" incorrectamente
```

**Solución Implementada:**
```python
with transaction.atomic():
    # Todo el proceso de normalización
    # Si algo falla, ROLLBACK completo
    # Garantiza consistencia
```

---

### 4️⃣ **Eliminación de unique_together Conflictivo**

**Problema Anterior:**
```python
class PlanificacionNormalizada(models.Model):
    raw = models.OneToOneField(...)
    unique_together = ["plan_month", "item_code", "sucursal"]
    # ❌ Error: Múltiples raw con mismo (plan_month, item_code, sucursal)
```

**Solución Implementada:**
```python
class PlanificacionNormalizada(models.Model):
    raw = models.OneToOneField(...)  # 1 raw = 1 normalizado
    # ✅ Sin unique_together
    # ✅ Índices para performance sin restricción
```

---

### 5️⃣ **Índices Estratégicos**

**Planificacion:**
```python
indexes = [
    models.Index(fields=["normalize_status", "plan_month"]),      # Filtrado
    models.Index(fields=["item_code"]),                           # Búsqueda
    models.Index(fields=["sucursal"]),                            # Búsqueda
    models.Index(fields=["plan_month", "item_code", "sucursal"]), # Compuesto
]
```

**Salida:**
```python
indexes = [
    models.Index(fields=["normalize_status", "fecha_salida"]),
    models.Index(fields=["sku"]),
    models.Index(fields=["nombre_sucursal_origen"]),
    models.Index(fields=["nombre_sucursal_destino"]),
]
```

**PlanificacionNormalizada:**
```python
indexes = [
    models.Index(fields=["plan_month", "item_code"]),
    models.Index(fields=["plan_month", "sucursal"]),
]
```

**SalidaNormalizada:**
```python
indexes = [
    models.Index(fields=["fecha_salida", "sku"]),
    models.Index(fields=["fecha_salida", "cedis_origen"]),
    models.Index(fields=["fecha_salida", "sucursal_destino"]),
]
```

---

### 6️⃣ **Optimización de _sync_from_legacy()**

**Problema Anterior:**
```python
def _sync_from_legacy():
    # Se ejecutaba en cada GET/POST
    # Creaba registros redundantes
```

**Solución Implementada:**
```python
def _sync_from_legacy():
    legacy_count = PlanningEntry.objects.count()
    if legacy_count == 0:
        return  # No hay trabajo
    
    existing_count = Planificacion.objects.count()
    if existing_count >= legacy_count * 0.8:
        return  # Ya sincronizado ≥80%
    
    # Sincronizar solo si es necesario
```

---

## 🎨 TEMPLATES Y UI

### Templates Principales

1. **`landing.html`** - Página principal (inferido)
2. **`upload_menu.html`** - Menú de subidas
3. **`planning_upload.html`** - Subir planificación
4. **`planificacion_normalizar.html`** - Normalizar planificación
5. **`planificacion_error_resolver.html`** - Resolver errores de planificación
6. **`salida_upload.html`** - Subir salidas
7. **`salida_normalizar.html`** - Normalizar salidas
8. **`salida_error_resolver.html`** - Resolver errores de salidas
9. **`tablero_normalizado.html`** - Dashboard comparativo
10. **`missing_products.html`** - Productos faltantes
11. **`pvp_issues.html`** - Problemas de PVP

### Template Tags Personalizados

**`dict_extras.py`** - Helpers para diccionarios en templates
- Permite acceder a diccionarios con claves dinámicas en templates Django

---

## 📋 SCRIPTS DE ANÁLISIS

### Scripts Disponibles

1. **`analisis_completo.py`** - Analiza discrepancias entre cendis y Sucursal
2. **`analyze_cedis.py`** - Análisis de CEDIS
3. **`check_cedis_mismatch.py`** - Verifica desajustes de CEDIS
4. **`check_errors.py`** - Verifica errores de normalización
5. **`check_normalized_data.py`** - Verifica datos normalizados
6. **`check_origen_errors.py`** - Verifica errores de origen
7. **`create_missing_cedis.py`** - Crea CEDIS faltantes
8. **`delete_duplicate_cedis.py`** - Elimina CEDIS duplicados
9. **`fix_cedis_names.py`** - Corrige nombres de CEDIS
10. **`fix_origen_picking_names.py`** - Corrige nombres de origen
11. **`understand_plan_structure.py`** - Analiza estructura de planes
12. **`verificar_cedis.py`** - Verifica CEDIS

---

## 🔐 ADMIN DE DJANGO

### Modelos Registrados

```python
@admin.register(Product)          # Gestión de productos
@admin.register(Pvp)              # Gestión de PVP
@admin.register(Cendis)           # Gestión de CEDIS
@admin.register(PlanningBatch)    # Lotes de planificación
@admin.register(PlanningEntry)    # Entradas legacy
@admin.register(Salida)           # Salidas crudas
@admin.register(Planificacion)    # Planificación cruda (inferido)
@admin.register(Sucursal)         # Sucursales (inferido)
```

**Características:**
- ✅ Búsqueda por campos clave
- ✅ Filtros por fechas, estados
- ✅ Ordenamiento lógico
- ✅ Visualización de campos importantes

**URL:** `http://localhost:2222/admin/`

---

## ⚙️ CONFIGURACIÓN

### Settings Clave

```python
DEBUG = True
ALLOWED_HOSTS = ['*']
CSRF_TRUSTED_ORIGINS = [
    'https://*.trycloudflare.com',
    'http://localhost:2222',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

### Aplicaciones Instaladas

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'main',  # Aplicación principal
]
```

---

## 🚦 ESTADOS Y FLUJOS

### Estados de Normalización

#### Planificacion/Salida (raw)
```
pending → [normalizar] → ok ✅
                      → error ❌ → [resolver] → pending (re-procesar)
                      → ignored ⚠️ (solo Planificacion)
```

#### PlanificacionNormalizada/SalidaNormalizada
```
created → [actualizado si raw cambia]
deleted ← [si raw se borra (CASCADE)]
```

---

## 🔑 CONCEPTOS CLAVE

### 1️⃣ **Normalización**
Proceso de vincular datos crudos (strings) con maestros (ForeignKeys):
- `"La Yaguara"` (string) → `Cendis.objects.get(origin="La Yaguara")` (FK)
- `"PROD123"` (string) → `Product.objects.get(code="PROD123")` (FK)

### 2️⃣ **Maestros**
Tablas de referencia con datos limpios y únicos:
- `Product` - Catálogo de productos
- `Sucursal` - Lista de tiendas
- `Cendis` - Lista de almacenes

### 3️⃣ **Raw vs. Normalizado**
- **Raw:** Datos crudos del Excel (strings, posibles errores)
- **Normalizado:** Datos vinculados a maestros (ForeignKeys)

### 4️⃣ **OneToOneField**
```python
class PlanificacionNormalizada:
    raw = models.OneToOneField(Planificacion)
```
- 1 registro raw → 1 registro normalizado (máximo)
- Acceso bidireccional: `raw.normalizada` y `normalizada.raw`
- Cascade: borrar raw → borra normalizado

### 5️⃣ **Bulk Operations**
Operaciones en lote para eficiencia:
- `bulk_create()` - Crear múltiples registros (1 query)
- `bulk_update()` - Actualizar múltiples registros (1 query)

### 6️⃣ **Fuzzy Matching**
Algoritmo de similitud de strings para sugerencias:
```python
difflib.get_close_matches("CEDIS NORT", ["CEDIS NORTE", "CEDIS SUR"], cutoff=0.6)
# → ["CEDIS NORTE"]
```

---

## 📊 RENDIMIENTO

### Métricas de Optimización

| Métrica | Antes | Después | Mejora |
|---------|-------|---------|--------|
| Queries (1000 registros) | ~3000 | ~5 | 99.8% ↓ |
| Tiempo (1000 registros) | 30-60s | <5s | 85-95% ↓ |
| Consistencia | ❌ Riesgo de inconsistencias | ✅ Transacciones atómicas | 100% ↑ |
| Escalabilidad | ❌ O(n) queries | ✅ O(1) queries | ∞ |

### Queries Típicas

**Normalización (optimizada):**
```sql
-- Pre-carga de maestros (3 queries)
SELECT * FROM main_sucursal;
SELECT * FROM main_cendis;
SELECT * FROM main_product;

-- Bulk create (1 query)
INSERT INTO main_planificacionnormalizada VALUES (...), (...), ...;

-- Bulk update (1 query)
UPDATE main_planificacion SET normalize_status='ok' WHERE id IN (...);
```

**Total: ~5 queries para 1000+ registros**

---

## 🎯 CASOS DE USO

### Caso 1: Usuario Sube Excel de Planificación

1. Usuario va a `/planificacion/`
2. Sube archivo Excel con columnas: `Plan Month`, `Item Code`, `Sucursal`, `CENDIS`, `A Despachar Total`
3. Sistema lee Excel y crea registros en `Planificacion` (raw)
4. Usuario va a `/planificacion/normalizar/`
5. Sistema intenta normalizar:
   - ✅ Encuentra sucursal "TIENDA 1" → vincula FK
   - ✅ Encuentra CEDIS "La Yaguara" → vincula FK
   - ❌ No encuentra producto "PROD999" → marca error
6. Usuario ve 1 error en pantalla
7. Usuario hace clic en "Resolver errores"
8. Sistema sugiere "PROD99" (fuzzy match)
9. Usuario elige:
   - **Opción A:** Crear "PROD999" como nuevo producto
   - **Opción B:** Mapear "PROD999" → "PROD99" (era un typo)
10. Sistema actualiza `Planificacion.item_code` y marca como `pending`
11. Usuario vuelve a normalizar
12. ✅ Ahora todo normaliza exitosamente

### Caso 2: Usuario Compara Plan vs. Salidas

1. Usuario va a `/tablero/normalizado/`
2. Selecciona:
   - Mes de plan: Enero 2026
   - Fecha de salida: 2026-01-10
   - Origen: La Yaguara
3. Sistema muestra tabla:
```
CEDIS: La Yaguara
  └─ TIENDA 1
      ├─ ABARROTES: Plan 1000 | Salida 850 | 85% ✅
      └─ BEBIDAS: Plan 500 | Salida 600 | 120% ⚠️
  └─ TIENDA 2
      └─ ABARROTES: Plan 800 | Salida 800 | 100% ✅
```
4. Usuario identifica:
   - ✅ TIENDA 1 - ABARROTES: 85% cumplimiento (aceptable)
   - ⚠️ TIENDA 1 - BEBIDAS: 120% sobrecumplimiento (revisar)
   - ✅ TIENDA 2 - ABARROTES: 100% cumplimiento (perfecto)

### Caso 3: Usuario Detecta Productos Faltantes

1. Usuario va a `/faltantes/`
2. Sistema muestra:
```
Productos en datos crudos que NO existen en maestro:
- PROD999 (usado en 25 registros)
- PROD888 (usado en 10 registros)
```
3. Usuario va a admin → Product → Agregar PROD999 y PROD888
4. Usuario vuelve a normalizar
5. ✅ Ahora los registros se normalizan correctamente

---

## 🐛 PROBLEMAS COMUNES Y SOLUCIONES

### Problema 1: "CEDIS origen no encontrado"

**Causa:** Nombre en Excel no coincide con tabla `Cendis`

**Solución 1 - Crear CEDIS:**
```python
# En /planificacion/errores/
Crear nuevo CEDIS:
  origin: "La Yaguara"
  code: "LY01"
```

**Solución 2 - Mapear:**
```python
# En /planificacion/errores/
Mapear:
  De: "La Yaguara" (con espacio extra)
  A: "La Yaguara" (correcto)
```

### Problema 2: "Sucursal destino no encontrada"

**Causa:** Nombre en Excel no coincide con tabla `Sucursal`

**Solución:**
```python
# En /planificacion/errores/
Crear nueva Sucursal:
  name: "TIENDA MARACAY"
  bpl_id: 1000050
```

### Problema 3: "Producto no encontrado"

**Causa:** Código en Excel no existe en tabla `Product`

**Solución:**
```python
# En /planificacion/errores/
Crear nuevo Producto:
  code: "PROD999"
  name: "Producto X"
  group: "ABARROTES"
```

### Problema 4: Normalización Muy Lenta

**Causa:** N+1 queries (versión antigua del código)

**Solución:** Ya implementada en versión actual:
- Pre-carga de maestros
- Bulk operations
- Transacciones atómicas

### Problema 5: Error "unique_together constraint failed"

**Causa:** Múltiples raw con mismos valores + unique_together

**Solución:** Ya implementada - `unique_together` eliminado

---

## 📚 DOCUMENTACIÓN RELACIONADA

### Archivos de Documentación

1. **`GUIA_RESOLUCION_ERRORES.md`** (228 líneas)
   - Guía completa del sistema de resolución de errores
   - Flujos de ejemplo
   - Capturas de pantalla (probablemente)

2. **`CAMBIOS_NORMALIZACION.md`** (156 líneas)
   - Historial de optimizaciones
   - Problemas corregidos
   - Métricas de mejora

3. **`ANALISIS_SISTEMA_COMPLETO.md`** (este documento)
   - Análisis técnico completo del sistema

---

## 🔮 ARQUITECTURA TÉCNICA

### Patrón de Diseño

**MTV (Model-Template-View)** - Estándar de Django:
```
Request → URL Router → View → Model (BD) → Template → Response
```

### Capas del Sistema

```
┌─────────────────────────────────────────┐
│           PRESENTACIÓN                  │
│  (Templates HTML + CSS + JavaScript)    │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│           LÓGICA DE NEGOCIO             │
│  (Views: normalización, resolución)     │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│           ACCESO A DATOS                │
│  (Models: ORM de Django)                │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│           BASE DE DATOS                 │
│  (SQLite3)                              │
└─────────────────────────────────────────┘
```

### Flujo de Request

```
Usuario → navegador → http://localhost:2222/planificacion/normalizar/
                                  ↓
                        ADB/urls.py (router principal)
                                  ↓
                        main/urls.py (router app)
                                  ↓
                        PlanificacionNormalizeView.post()
                                  ↓
                        Models (Planificacion, PlanificacionNormalizada)
                                  ↓
                        Template (planificacion_normalizar.html)
                                  ↓
Usuario ← HTML renderizado ← Response HTTP
```

---

## 🎓 CONCEPTOS DJANGO CLAVE UTILIZADOS

### 1. Class-Based Views (CBV)
```python
class PlanificacionNormalizeView(View):
    def get(self, request):
        # Lógica para GET
    
    def post(self, request):
        # Lógica para POST
```

### 2. ORM (Object-Relational Mapping)
```python
# SQL abstraído
Planificacion.objects.filter(normalize_status="pending")

# Equivale a:
# SELECT * FROM main_planificacion WHERE normalize_status = 'pending';
```

### 3. Migraciones
```python
# Historial de cambios en BD
0001_initial.py                    # Tablas iniciales
0008_planificacion_normalizada.py  # Agregado modelo
0012_change_sucursal_origen.py     # Cambio de campo
```

### 4. OneToOneField con related_name
```python
raw = models.OneToOneField(Planificacion, related_name="normalizada")

# Acceso:
planificacion.normalizada  # ← Acceso inverso
normalizada.raw            # → Acceso directo
```

### 5. select_related() y prefetch_related()
```python
# Optimización de queries
PlanificacionNormalizada.objects.select_related(
    'product', 'sucursal', 'cedis_origen'
)
# 1 query con JOIN en lugar de N+1 queries
```

### 6. Transacciones Atómicas
```python
with transaction.atomic():
    # Todo-o-nada
    # Si falla, rollback completo
```

### 7. Bulk Operations
```python
# Eficiencia
Model.objects.bulk_create([obj1, obj2, obj3])  # 1 query
Model.objects.bulk_update(objs, fields=['f1'])  # 1 query
```

---

## 📈 PRÓXIMOS PASOS SUGERIDOS

### Mejoras de Performance

1. **Caché de Redis**
   - Cachear maestros frecuentemente usados
   - Reducir queries repetitivas

2. **Celery para Tareas Asíncronas**
   - Normalización en background
   - Evitar timeouts en navegador

3. **PostgreSQL en Producción**
   - Mejor performance que SQLite
   - Soporte para concurrencia

### Mejoras Funcionales

1. **Importación Incremental**
   - Solo importar registros nuevos
   - Evitar duplicados

2. **Historial de Cambios**
   - Auditoría de quién creó/mapeó qué
   - Rollback de operaciones

3. **Validaciones Pre-Importación**
   - Validar Excel antes de cargar
   - Alertas de posibles errores

4. **Dashboard Mejorado**
   - Gráficos interactivos (Chart.js)
   - Filtros avanzados
   - Drill-down por categorías

### Mejoras de UX

1. **Feedback en Tiempo Real**
   - Progress bar durante normalización
   - Notificaciones toast

2. **Búsqueda Avanzada**
   - Filtros combinados
   - Exportación a Excel

3. **Ayuda Contextual**
   - Tooltips explicativos
   - Tutoriales interactivos

---

## 🔒 SEGURIDAD

### Configuración Actual (Desarrollo)

```python
DEBUG = True                    # ⚠️ Desactivar en producción
SECRET_KEY = 'django-insecure-...'  # ⚠️ Cambiar en producción
ALLOWED_HOSTS = ['*']          # ⚠️ Restringir en producción
```

### Recomendaciones para Producción

1. **Variables de Entorno**
   ```python
   SECRET_KEY = os.environ.get('SECRET_KEY')
   DEBUG = os.environ.get('DEBUG', 'False') == 'True'
   ```

2. **HTTPS Only**
   ```python
   SECURE_SSL_REDIRECT = True
   SESSION_COOKIE_SECURE = True
   CSRF_COOKIE_SECURE = True
   ```

3. **Autenticación**
   ```python
   # Agregar login_required a vistas sensibles
   from django.contrib.auth.decorators import login_required
   ```

4. **Rate Limiting**
   - Prevenir abuso de endpoints

5. **Backup Automático**
   - Respaldo diario de BD

---

## 📞 CONTACTO Y SOPORTE

### Recursos del Proyecto

- **Repositorio:** (agregar si existe)
- **Documentación:** Ver archivos `.md` en raíz
- **Admin Django:** `http://localhost:2222/admin/`

### Comandos Útiles

```bash
# Servidor de desarrollo
python manage.py runserver 2222

# Migraciones
python manage.py makemigrations
python manage.py migrate

# Shell interactivo
python manage.py shell

# Crear superusuario
python manage.py createsuperuser

# Ejecutar scripts
python analisis_completo.py
python verificar_cedis.py
```

---

## 📝 RESUMEN EJECUTIVO

### ¿Qué hace el sistema?

Sistema web Django para normalizar y analizar datos de distribución logística:
1. **Importa** Excel de planificación y salidas
2. **Normaliza** vinculando strings a maestros (Sucursales, CEDIS, Productos)
3. **Detecta errores** y ofrece resolución interactiva con fuzzy matching
4. **Compara** plan vs. ejecución real en tablero analítico
5. **Identifica** productos faltantes en catálogos

### Tecnologías Principales

- **Backend:** Django 6.0.1 (Python)
- **Base de Datos:** SQLite3 (desarrollo)
- **Frontend:** HTML + CSS + JavaScript (templates Django)
- **Librerías:** openpyxl (Excel), difflib (fuzzy matching)

### Optimizaciones Clave

- ✅ Pre-carga de maestros (elimina N+1)
- ✅ Bulk operations (1 query para múltiples registros)
- ✅ Transacciones atómicas (consistencia garantizada)
- ✅ Índices estratégicos (performance de queries)
- ✅ Eliminado unique_together conflictivo

### Performance

- **Antes:** ~3000 queries, 30-60s para 1000 registros
- **Después:** ~5 queries, <5s para 1000 registros
- **Mejora:** 99.8% reducción en queries, 85-95% en tiempo

---

## 🎉 CONCLUSIÓN

Este es un sistema **robusto, optimizado y funcional** para gestión de datos logísticos. 

**Fortalezas:**
- ✅ Arquitectura limpia y bien estructurada
- ✅ Optimizaciones de performance implementadas
- ✅ Resolución interactiva de errores con UX amigable
- ✅ Fuzzy matching para sugerencias inteligentes
- ✅ Dashboard analítico comparativo
- ✅ Documentación extensa

**Oportunidades de Mejora:**
- ⚠️ Migrar a PostgreSQL para producción
- ⚠️ Agregar autenticación robusta
- ⚠️ Implementar tareas asíncronas (Celery)
- ⚠️ Mejorar UI con framework moderno (React/Vue)

**Resultado:** Sistema en producción listo con optimizaciones menores pendientes.

---

**Generado:** 14 de enero de 2026  
**Versión:** 1.0  
**Autor:** Análisis Técnico Completo
