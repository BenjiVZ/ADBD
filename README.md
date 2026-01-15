# ADD - Sistema de Distribución

## Estructura del Proyecto

```
ADD/
├── ADB/                    # Configuración de Django
├── main/                   # Aplicación principal
│   ├── models/            # Modelos de datos
│   ├── views/             # Vistas
│   ├── migrations/        # Migraciones de base de datos
│   └── templatetags/      # Filtros personalizados
├── templates/             # Plantillas HTML
├── scripts/               # Scripts de utilidad
│   ├── analisis/         # Scripts de análisis de datos
│   ├── correccion/       # Scripts de corrección y migración
│   └── verificacion/     # Scripts de verificación
├── docs/                  # Documentación
├── manage.py              # Comando principal de Django
└── db.sqlite3            # Base de datos SQLite

## Scripts Organizados

### Análisis (`scripts/analisis/`)
- `analisis_completo.py` - Análisis completo del sistema
- `analyze_cedis.py` - Análisis de CEDIS
- `diagnostico_normalizacion.py` - Diagnóstico de normalización
- `diagnostico_valencia.py` - Diagnóstico específico de Valencia
- `estado_final.py` - Estado final del sistema
- `understand_plan_structure.py` - Análisis de estructura de planificación

### Verificación (`scripts/verificacion/`)
- `check_cedis_mismatch.py` - Verificar inconsistencias en CEDIS
- `check_errors.py` - Verificar errores generales
- `check_normalized_data.py` - Verificar datos normalizados
- `check_origen_errors.py` - Verificar errores de origen
- `verificar_cedis.py` - Verificar CEDIS
- `verificar_estado_datos.py` - Verificar estado de datos
- `verificar_fechas.py` - Verificar fechas
- `verificar_normalizacion.py` - Verificar normalización
- `ver_migraciones.py` - Ver migraciones aplicadas

### Corrección (`scripts/correccion/`)
- `agregar_almacenes_faltantes.py` - Agregar almacenes faltantes
- `agregar_cedis_faltantes.py` - Agregar CEDIS faltantes
- `agregar_faltantes_auto.py` - Agregar faltantes automáticamente
- `agregar_servicio_tecnico.py` - Agregar servicio técnico
- `corregir_migracion_sendis.py` - Corregir migración de SENDIS
- `create_missing_cedis.py` - Crear CEDIS faltantes
- `delete_duplicate_cedis.py` - Eliminar CEDIS duplicados
- `fix_cedis_names.py` - Corregir nombres de CEDIS
- `fix_origen_picking_names.py` - Corregir nombres de origen picking
- `limpiar_normalizaciones.py` - Limpiar normalizaciones
- `reparar_normalizacion.py` - Reparar normalización
- `revertir_cedis_auto.py` - Revertir CEDIS automáticos

## Documentación (`docs/`)
- `ANALISIS_SISTEMA_COMPLETO.md` - Análisis completo del sistema
- `CAMBIOS_NORMALIZACION.md` - Cambios en normalización
- `CLARIFICACION_CEDIS_SUCURSALES.md` - Clarificación sobre CEDIS y sucursales
- `CORRECCIONES_NORMALIZACION.md` - Correcciones de normalización
- `GUIA_RESOLUCION_ERRORES.md` - Guía para resolver errores

## Uso

Para ejecutar los scripts, usa:
```bash
python scripts/analisis/nombre_script.py
python scripts/verificacion/nombre_script.py
python scripts/correccion/nombre_script.py
```

Para ejecutar el servidor Django:
```bash
python manage.py runserver
```
