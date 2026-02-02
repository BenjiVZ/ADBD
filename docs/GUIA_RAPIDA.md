# 🚀 GUÍA RÁPIDA - Sistema ADB

**Versión:** 1.0  
**Última actualización:** 16 de enero de 2026

---

## ⚡ INICIO RÁPIDO

### Levantar el servidor
```bash
cd "C:\Users\bvelazco\Documents\Sistema ADB\ADBD"
python manage.py runserver 1111
```

Acceder a: http://localhost:1111

---

## 🗺️ NAVEGACIÓN RÁPIDA

| Funcionalidad | URL | Descripción |
|--------------|-----|-------------|
| 🏠 Inicio | `/` | Página principal |
| 📤 Subir archivos | `/subidas/` | Menú de carga |
| 📋 Subir planificación | `/planificacion/` | Cargar Excel planificación |
| 🔧 Normalizar planificación | `/planificacion/normalizar/` | Procesar planificación |
| ❌ Errores planificación | `/planificacion/errores/` | Resolver errores |
| 📦 Subir salidas | `/salidas/` | Cargar Excel salidas |
| 🔧 Normalizar salidas | `/salidas/normalizar/` | Procesar salidas |
| ❌ Errores salidas | `/salidas/errores/` | Resolver errores |
| 📊 Tablero | `/tablero/normalizado/` | Dashboard de análisis |
| 🏢 CEDIS | `/biblioteca/cedis/` | Gestión de CEDIS |
| 🏪 Sucursales | `/biblioteca/sucursales/` | Gestión de Sucursales |

---

## 📊 ESTADO ACTUAL

```
Productos:        20,366
Sucursales:       46
CEDIS:            5
Planificaciones:  1,847 (100% normalizadas)
Salidas:          8,166 (100% normalizadas)
Errores:          0
```

---

## 🔄 FLUJO TÍPICO DE TRABAJO

### 1️⃣ Cargar Planificación
```
/planificacion/ → Seleccionar Excel → Subir → Vista previa → Confirmar
```

### 2️⃣ Normalizar
```
/planificacion/normalizar/ → Seleccionar mes → Click "Normalizar pendientes"
```

### 3️⃣ Resolver Errores (si hay)
```
/planificacion/errores/ → Ver errores agrupados → Crear/Mapear/Ignorar → Re-normalizar
```

### 4️⃣ Analizar
```
/tablero/normalizado/ → Filtrar por mes → Ver plan vs. ejecución
```

---

## 📁 ESTRUCTURA DE ARCHIVOS IMPORTANTES

```
ADBD/
├── manage.py                     ← Comando principal Django
├── db.sqlite3                    ← Base de datos
├── ANALISIS_SISTEMA.md          ← Análisis completo ⭐ NUEVO
├── PLAN_CORRECCIONES.md         ← Plan de mejoras ⭐ NUEVO
│
├── ADB/
│   ├── settings.py              ← Configuración
│   └── urls.py                  ← URLs principales
│
├── main/
│   ├── models/                  ← 12 modelos
│   │   ├── planificacion.py
│   │   ├── planificacion_normalizada.py
│   │   ├── salida.py
│   │   ├── salida_normalizada.py
│   │   ├── cendis.py
│   │   ├── sucursal.py
│   │   ├── product.py
│   │   ├── mapeos.py
│   │   └── ...
│   │
│   ├── views/                   ← 13 vistas
│   │   ├── planificacion_normalize.py
│   │   ├── salida_normalize.py
│   │   ├── error_resolver.py
│   │   ├── biblioteca_maestros.py
│   │   └── ...
│   │
│   ├── migrations/              ← 16 migraciones
│   └── urls.py                  ← URLs de la app
│
├── templates/                   ← 16 plantillas HTML
│   ├── planificacion_normalizar.html
│   ├── salida_normalizar.html
│   ├── tablero_normalizado.html
│   └── ...
│
├── scripts/
│   ├── analisis/               ← Scripts de análisis
│   │   └── estado_actual.py    ← Ver estado ⭐ NUEVO
│   ├── verificacion/           ← Scripts de verificación
│   └── correccion/             ← Scripts de corrección
│
└── docs/                       ← Documentación
    ├── ANALISIS_SISTEMA_COMPLETO.md
    ├── GUIA_RESOLUCION_ERRORES.md
    └── ...
```

---

## 🛠️ COMANDOS ÚTILES

### Django
```bash
# Levantar servidor
python manage.py runserver 1111

# Abrir shell de Django
python manage.py shell

# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Ver migraciones
python manage.py showmigrations

# Crear superusuario
python manage.py createsuperuser
```

### Scripts de análisis
```bash
# Ver estado del sistema
cd scripts\analisis
python estado_actual.py

# Diagnóstico de normalización
python diagnostico_normalizacion.py

# Análisis completo
python analisis_completo.py
```

### Scripts de verificación
```bash
cd scripts\verificacion

# Verificar datos normalizados
python check_normalized_data.py

# Verificar errores
python check_errors.py

# Verificar CEDIS
python verificar_cedis.py
```

---

## 🔍 CONSULTAS SQL ÚTILES

### Abrir shell de Django
```bash
python manage.py shell
```

### Ver estadísticas
```python
from main.models import *

# Contar registros
print(f"Productos: {Product.objects.count()}")
print(f"Sucursales: {Sucursal.objects.count()}")
print(f"CEDIS: {Cendis.objects.count()}")

# Ver planificaciones por estado
print(f"OK: {Planificacion.objects.filter(normalize_status='ok').count()}")
print(f"Pending: {Planificacion.objects.filter(normalize_status='pending').count()}")
print(f"Error: {Planificacion.objects.filter(normalize_status='error').count()}")

# Ver errores recientes
errors = Planificacion.objects.filter(normalize_status='error')[:5]
for e in errors:
    print(f"{e.id}: {e.normalize_notes}")
```

### Resetear normalización
```python
from main.models import Planificacion, PlanificacionNormalizada

# Resetear un mes específico
month = date(2026, 1, 1)
Planificacion.objects.filter(plan_month=month).update(
    normalize_status='pending',
    normalize_notes='',
    normalized_at=None
)
PlanificacionNormalizada.objects.filter(plan_month=month).delete()

print("Listo para re-normalizar")
```

### Ver datos normalizados
```python
from main.models import PlanificacionNormalizada

# Ver primeros 10 registros normalizados
for p in PlanificacionNormalizada.objects.select_related(
    'sucursal', 'cedis_origen', 'product'
)[:10]:
    print(f"{p.item_code} → {p.sucursal.name} desde {p.cedis_origen.code}")
```

---

## ⚠️ PROBLEMAS COMUNES

### Problema: "No module named 'main'"
**Solución:**
```bash
# Asegúrate de estar en el directorio correcto
cd "C:\Users\bvelazco\Documents\Sistema ADB\ADBD"
python manage.py runserver
```

### Problema: "Port already in use"
**Solución:**
```bash
# Usar otro puerto
python manage.py runserver 2222
```

### Problema: "Database is locked"
**Causa:** SQLite no soporta múltiples escrituras simultáneas  
**Solución:**
```bash
# Cerrar todas las instancias del servidor
# O migrar a PostgreSQL (ver PLAN_CORRECCIONES.md)
```

### Problema: Normalización lenta
**Causa:** Muchos registros para procesar  
**Solución:**
- Normalizar por mes/fecha específica
- Implementar Celery para background jobs (ver PLAN_CORRECCIONES.md)

### Problema: Errores de normalización
**Solución:**
1. Ir a `/planificacion/errores/` o `/salidas/errores/`
2. Ver errores agrupados
3. Crear/mapear entidades faltantes
4. Re-normalizar automáticamente

---

## 📈 MÉTRICAS DE PERFORMANCE

### Normalización
- **1,000 registros:** ~2-5 segundos
- **Queries totales:** ~5 (optimizado)
- **Tasa de éxito:** 100% (con mapeos correctos)

### Tablero
- **Tiempo de carga:** <1 segundo
- **Registros simultáneos:** Miles sin problema

---

## 🎯 CASOS DE USO RÁPIDOS

### Agregar nuevo CEDIS
```
1. /biblioteca/cedis/
2. Crear CEDIS oficial → Ingresar código y nombre
3. Listo (auto-normalizará registros con ese nombre)
```

### Mapear variación de nombre
```
1. /biblioteca/cedis/ o /biblioteca/sucursales/
2. Buscar nombre en tabla
3. Click "Mapear a existente" → Seleccionar oficial
4. Listo (auto-normalizará registros con esa variación)
```

### Limpiar y re-normalizar un mes
```
1. /planificacion/normalizar/
2. Seleccionar mes
3. Click "Limpiar normalizaciones de este mes"
4. Click "Normalizar pendientes"
```

### Exportar datos para análisis
```
1. /tablero/normalizado/
2. Aplicar filtros
3. (Futura función: Click "Exportar a Excel")
```

### Ver productos faltantes
```
1. /faltantes/
2. Ver lista de SKUs sin producto en maestro
3. Agregar productos al maestro
```

---

## 📚 DOCUMENTACIÓN ADICIONAL

- **Análisis completo:** [ANALISIS_SISTEMA.md](ANALISIS_SISTEMA.md)
- **Plan de correcciones:** [PLAN_CORRECCIONES.md](PLAN_CORRECCIONES.md)
- **Guía de errores:** [docs/GUIA_RESOLUCION_ERRORES.md](docs/GUIA_RESOLUCION_ERRORES.md)
- **Análisis original:** [docs/ANALISIS_SISTEMA_COMPLETO.md](docs/ANALISIS_SISTEMA_COMPLETO.md)

---

## 🆘 SOPORTE

### Logs del sistema
```bash
# Ver logs en consola donde corre el servidor
# El servidor muestra:
# - Queries ejecutadas
# - Errores de normalización
# - Warnings
```

### Verificar estado
```bash
cd scripts\analisis
python estado_actual.py
```

### Backup de base de datos
```bash
# Copiar base de datos
copy db.sqlite3 db.sqlite3.backup_%date:~-4,4%%date:~-10,2%%date:~-7,2%
```

### Restaurar backup
```bash
# Restaurar desde backup
copy db.sqlite3.backup db.sqlite3
```

---

## ✅ CHECKLIST DIARIO

### Antes de trabajar
- [ ] Hacer backup de db.sqlite3
- [ ] Levantar servidor
- [ ] Verificar que no hay errores pendientes

### Después de cargar datos
- [ ] Normalizar datos cargados
- [ ] Resolver errores si hay
- [ ] Verificar en tablero que los datos se ven correctos

### Antes de cerrar
- [ ] Verificar que todos los datos están normalizados (0 pending)
- [ ] Cerrar servidor correctamente (Ctrl+C)

---

## 🎓 TIPS PRO

1. **Usa filtros en el tablero** para análisis específicos
2. **Crea mapeos** en lugar de modificar datos crudos
3. **Normaliza por fecha/mes** en lugar de todo a la vez
4. **Revisa logs** si algo no funciona como esperado
5. **Usa scripts de verificación** periódicamente

---

**Preparado por:** GitHub Copilot  
**Última actualización:** 16 de enero de 2026
