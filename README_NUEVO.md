# 🏢 Sistema ADB - Análisis y Distribución de Datos

**Versión:** 1.0  
**Framework:** Django 6.0.1  
**Base de Datos:** SQLite3  
**Estado:** ✅ Producción - 100% Funcional

---

## 📋 Descripción

Sistema web de normalización y análisis de datos logísticos para distribución entre **CEDIS** (Centros de Distribución) y **Sucursales**.

### ✨ Características Principales

- ✅ **Carga masiva** desde archivos Excel
- ✅ **Normalización automática** con vinculación a maestros
- ✅ **Resolución interactiva de errores** con sugerencias inteligentes (fuzzy matching)
- ✅ **Sistema de mapeos** para variaciones de nombres
- ✅ **Dashboard analítico** de cumplimiento (plan vs. ejecución)
- ✅ **Gestión de maestros** (Productos, Sucursales, CEDIS)
- ✅ **Performance optimizada** (bulk operations, transacciones atómicas)

---

## 📊 Estado Actual

```
Productos:        20,366
Sucursales:       46
CEDIS:            5
Planificaciones:  1,847 (100% normalizadas)
Salidas:          8,166 (100% normalizadas)
Mapeos:           9 (5 CEDIS + 4 Sucursales)
Errores:          0
```

---

## 🚀 Inicio Rápido

### Requisitos
- Python 3.14+
- Django 6.0.1
- SQLite3 (incluido con Python)

### Instalación

```bash
# Clonar repositorio (si aplica)
cd "C:\Users\bvelazco\Documents\Sistema ADB\ADBD"

# Instalar dependencias (si es primera vez)
pip install django

# Aplicar migraciones
python manage.py migrate

# Levantar servidor
python manage.py runserver 1111
```

### Acceso
Abrir navegador en: http://localhost:1111

---

## 🗂️ Estructura del Proyecto

```
ADBD/
├── manage.py                     # Comando principal Django
├── db.sqlite3                    # Base de datos
├── README.md                     # Este archivo ⭐
├── ANALISIS_SISTEMA.md          # Análisis técnico completo ⭐ NUEVO
├── PLAN_CORRECCIONES.md         # Plan de mejoras futuras ⭐ NUEVO
├── GUIA_RAPIDA.md               # Guía de referencia rápida ⭐ NUEVO
│
├── ADB/                          # Configuración Django
│   ├── settings.py              # Configuración principal
│   ├── urls.py                  # URLs principales
│   └── wsgi.py                  # WSGI application
│
├── main/                        # Aplicación principal
│   ├── models/                  # 12 modelos de datos
│   │   ├── planificacion.py
│   │   ├── planificacion_normalizada.py
│   │   ├── salida.py
│   │   ├── salida_normalizada.py
│   │   ├── cendis.py
│   │   ├── sucursal.py
│   │   ├── product.py
│   │   ├── mapeos.py            # Sistema de alias ⭐
│   │   └── ...
│   │
│   ├── views/                   # 13 vistas
│   │   ├── planificacion_normalize.py
│   │   ├── salida_normalize.py
│   │   ├── error_resolver.py    # Resolución interactiva ⭐
│   │   ├── biblioteca_maestros.py
│   │   ├── tablero_normalizado.py
│   │   └── ...
│   │
│   ├── migrations/              # 16 migraciones aplicadas
│   └── urls.py                  # URLs de la app
│
├── templates/                   # 16 plantillas HTML
│   ├── planificacion_normalizar.html
│   ├── salida_normalizar.html
│   ├── tablero_normalizado.html
│   ├── error_resolver.html      # UI de resolución ⭐
│   └── ...
│
├── scripts/                     # Scripts de utilidad
│   ├── analisis/               # 8 scripts de análisis
│   │   └── estado_actual.py    # Ver estado del sistema ⭐ NUEVO
│   ├── verificacion/           # 11 scripts de verificación
│   └── correccion/             # 17 scripts de corrección
│
└── docs/                       # Documentación técnica
    ├── ANALISIS_SISTEMA_COMPLETO.md
    ├── GUIA_RESOLUCION_ERRORES.md
    ├── CAMBIOS_NORMALIZACION.md
    └── ...
```

---

## 🔄 Flujo de Trabajo Típico

### 1. Cargar Datos
```
/planificacion/ → Subir Excel → Vista previa → Confirmar
```

### 2. Normalizar
```
/planificacion/normalizar/ → Seleccionar mes → "Normalizar pendientes"
```

### 3. Resolver Errores (si hay)
```
/planificacion/errores/ → Ver agrupados → Crear/Mapear/Ignorar
```

### 4. Analizar
```
/tablero/normalizado/ → Filtros → Ver plan vs. ejecución
```

---

## 🌐 URLs Principales

| Funcionalidad | URL | Descripción |
|--------------|-----|-------------|
| 🏠 Inicio | `/` | Página principal |
| 📤 Menú de subidas | `/subidas/` | Carga de archivos |
| 📋 Planificación | `/planificacion/` | Subir planificación |
| 🔧 Normalizar plan | `/planificacion/normalizar/` | Procesar datos |
| ❌ Errores plan | `/planificacion/errores/` | Resolución interactiva |
| 📦 Salidas | `/salidas/` | Subir salidas |
| 🔧 Normalizar salidas | `/salidas/normalizar/` | Procesar datos |
| ❌ Errores salidas | `/salidas/errores/` | Resolución interactiva |
| 📊 Dashboard | `/tablero/normalizado/` | Análisis cumplimiento |
| 🏢 CEDIS | `/biblioteca/cedis/` | Gestión de CEDIS |
| 🏪 Sucursales | `/biblioteca/sucursales/` | Gestión de Sucursales |

---

## 📁 Scripts Organizados

### Análisis (`scripts/analisis/`)
- `estado_actual.py` ⭐ NUEVO - Ver estado general del sistema
- `analisis_completo.py` - Análisis detallado
- `diagnostico_normalizacion.py` - Diagnóstico de normalización
- `analyze_cedis.py` - Análisis de CEDIS

### Verificación (`scripts/verificacion/`)
- `check_normalized_data.py` - Verificar datos normalizados
- `check_errors.py` - Verificar errores generales
- `verificar_cedis.py` - Verificar CEDIS
- `verificar_estado_datos.py` - Verificar estado de datos

### Corrección (`scripts/correccion/`)
- `limpiar_normalizaciones.py` - Limpiar y re-normalizar
- `agregar_faltantes_auto.py` - Agregar CEDIS/Sucursales faltantes
- `corregir_cedis_mapeo.py` - Corregir mapeos
- `reparar_normalizacion.py` - Reparar inconsistencias

### Uso de Scripts
```bash
# Ver estado del sistema
cd scripts\analisis
python estado_actual.py

# Verificar datos
cd ..\verificacion
python check_normalized_data.py

# Correcciones (con precaución)
cd ..\correccion
python limpiar_normalizaciones.py
```

---

## 📚 Documentación

### ⭐ Documentación Nueva (Enero 2026)
- **[ANALISIS_SISTEMA.md](ANALISIS_SISTEMA.md)** - 📊 Análisis técnico completo del sistema
- **[PLAN_CORRECCIONES.md](PLAN_CORRECCIONES.md)** - 🔧 Plan de mejoras y correcciones
- **[GUIA_RAPIDA.md](GUIA_RAPIDA.md)** - 🚀 Referencia rápida de uso diario

### Para Usuarios
- **[docs/GUIA_RESOLUCION_ERRORES.md](docs/GUIA_RESOLUCION_ERRORES.md)** - Cómo resolver errores

### Para Desarrolladores
- **[docs/ANALISIS_SISTEMA_COMPLETO.md](docs/ANALISIS_SISTEMA_COMPLETO.md)** - Documentación original
- **[docs/CAMBIOS_NORMALIZACION.md](docs/CAMBIOS_NORMALIZACION.md)** - Historial de optimizaciones

---

## ⚡ Características Destacadas

### 1. Sistema de Mapeos
Normaliza automáticamente variaciones de nombres sin modificar datos crudos:
- "Guatire I" → CEDIS "Guatire 1"
- "SAMBIL VALENCIA" → Sucursal "Sambil Valencia"

### 2. Resolución Interactiva de Errores
- **Fuzzy Matching:** Sugerencias inteligentes para errores de escritura
- **Agrupación:** Errores agrupados por tipo
- **Acciones en lote:** Una corrección afecta múltiples registros

### 3. Performance Optimizada
- **Antes:** 1,000 registros = 3,000+ queries, 30-60 segundos
- **Ahora:** 1,000 registros = ~5 queries, 2-5 segundos
- **Mejora:** 10-20x más rápido

### 4. Integridad de Datos
- ✅ Transacciones atómicas (todo o nada)
- ✅ Datos crudos preservados (auditoría completa)
- ✅ Relaciones OneToOne (raw → normalizada)
- ✅ Foreign Keys (integridad referencial)

---

## 🛠️ Comandos Útiles

### Django
```bash
# Levantar servidor
python manage.py runserver 1111

# Shell interactivo
python manage.py shell

# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Ver estado de migraciones
python manage.py showmigrations
```

### Análisis Rápido
```bash
# Ver estado del sistema
python scripts\analisis\estado_actual.py

# Verificar datos normalizados
python scripts\verificacion\check_normalized_data.py
```

---

## ⚠️ Problemas Comunes

### "Port already in use"
```bash
# Usar otro puerto
python manage.py runserver 2222
```

### "Database is locked"
Cerrar todas las instancias del servidor.

### Normalización lenta
- Normalizar por mes/fecha específica
- Ver PLAN_CORRECCIONES.md para implementar Celery

---

## 🎯 Próximas Mejoras

Ver [PLAN_CORRECCIONES.md](PLAN_CORRECCIONES.md) para plan detallado:

### Prioridad Alta
- [ ] Eliminar sistema legacy (PlanningBatch, PlanningEntry)
- [ ] Resolver warning de static files
- [ ] Implementar tests unitarios

### Prioridad Media
- [ ] Background jobs con Celery (para grandes volúmenes)
- [ ] API REST (integración con otros sistemas)
- [ ] Mejoras de UI (progress bars, gráficos)

---

## 📞 Soporte

### Backup
```bash
# Hacer backup de la base de datos
copy db.sqlite3 db.sqlite3.backup
```

### Logs
El servidor muestra logs en consola con:
- Queries ejecutadas
- Errores de normalización
- Warnings del sistema

### Verificar Estado
```bash
cd scripts\analisis
python estado_actual.py
```

---

## 📄 Licencia

Sistema interno - Uso exclusivo de la organización.

---

## 👥 Créditos

**Desarrollado por:** Equipo ADB  
**Análisis y optimización:** GitHub Copilot  
**Última actualización:** 16 de enero de 2026

---

## 🚀 Quick Start

```bash
# 1. Navegar al proyecto
cd "C:\Users\bvelazco\Documents\Sistema ADB\ADBD"

# 2. Levantar servidor
python manage.py runserver 1111

# 3. Abrir navegador
# http://localhost:1111
```

**¡Listo para usar!** 🎉
