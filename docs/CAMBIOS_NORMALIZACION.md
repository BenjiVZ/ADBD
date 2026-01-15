# Correcciones en el Sistema de Normalización

## Fecha: 14 de enero de 2026

## Resumen de Problemas Corregidos

### ✅ 1. Eliminación de N+1 Queries
**Problema anterior:** Cada registro procesado ejecutaba 2-3 queries individuales
- `Sucursal.objects.filter(name__iexact=...).first()` por cada raw
- `Product.objects.filter(code__iexact=...).first()` por cada raw
- **Resultado:** 1000 registros = 3000+ queries

**Solución implementada:**
- Pre-carga de todos los datos en memoria una sola vez:
  ```python
  sucursales_map = {s.name.lower(): s for s in Sucursal.objects.all()}
  products_map = {p.code.lower(): p for p in Product.objects.all()}
  ```
- **Resultado:** 1000 registros = 2 queries iniciales + bulk operations

### ✅ 2. Implementación de Transacciones Atómicas
**Problema anterior:** Si fallaba una operación, se marcaban registros como "ok" incorrectamente

**Solución implementada:**
```python
with transaction.atomic():
    # Todo el proceso de normalización
    # Si algo falla, se hace rollback completo
```

### ✅ 3. Uso de Bulk Operations
**Problema anterior:** Cada save() era una query individual

**Solución implementada:**
```python
# Acumular operaciones
to_create = []
to_update = []

# Ejecutar en lote
PlanificacionNormalizada.objects.bulk_create(to_create)
PlanificacionNormalizada.objects.bulk_update(to_update, fields=[...])
Planificacion.objects.bulk_update(to_update_raw, ['normalize_status', ...])
```

### ✅ 4. Eliminación de unique_together Conflictivo
**Problema anterior:** 
- `unique_together = ["plan_month", "item_code", "sucursal"]` en PlanificacionNormalizada
- `unique_together = ["salida", "fecha_salida", "sku"]` en SalidaNormalizada
- Ambos conflictuaban con `OneToOneField(raw)` causando errores cuando múltiples raw tenían mismos valores

**Solución implementada:**
- Eliminado `unique_together` de ambos modelos
- Relación OneToOne garantiza 1 raw = 1 normalizado
- Agregados índices para mantener performance

### ✅ 5. Optimización de _sync_from_legacy()
**Problema anterior:** Se ejecutaba en cada GET/POST creando registros redundantes

**Solución implementada:**
```python
def _sync_from_legacy():
    # Verificar si hay trabajo por hacer
    if legacy_count == 0:
        return
    
    # Si ya se sincronizó ≥80%, skip
    if existing_count >= legacy_count * 0.8:
        return
```

### ✅ 6. Índices Agregados para Performance

**Planificacion:**
- `["normalize_status", "plan_month"]` - para filtrar pendientes/errores por mes
- `["item_code"]` - para búsquedas de productos
- `["sucursal"]` - para búsquedas de sucursales
- `["plan_month", "item_code", "sucursal"]` - índice compuesto

**Salida:**
- `["normalize_status", "fecha_salida"]` - para filtrar por estado y fecha
- `["sku"]` - para búsquedas de productos
- `["nombre_sucursal_origen"]` - para búsquedas de origen
- `["nombre_sucursal_destino"]` - para búsquedas de destino

**PlanificacionNormalizada:**
- `["plan_month", "item_code"]` - queries frecuentes
- `["plan_month", "sucursal"]` - queries del tablero

**SalidaNormalizada:**
- `["fecha_salida", "sku"]` - queries frecuentes
- `["fecha_salida", "sucursal_origen"]` - para tablero por origen
- `["fecha_salida", "sucursal_destino"]` - para tablero por destino

## Mejoras de Performance Esperadas

### Antes:
- 1000 registros: ~3000 queries, ~30-60 segundos
- Sin transacciones: inconsistencias en caso de error
- Bloqueo del navegador durante proceso

### Después:
- 1000 registros: ~5 queries, ~2-5 segundos
- Con transacciones: todo o nada
- Performance 10-20x mejor

## Archivos Modificados

1. `main/views/planificacion_normalize.py`
   - Agregado `transaction.atomic()`
   - Pre-carga de datos
   - Bulk operations
   - Optimización de `_sync_from_legacy()`

2. `main/views/salida_normalize.py`
   - Agregado `transaction.atomic()`
   - Pre-carga de datos
   - Bulk operations

3. `main/models/planificacion_normalizada.py`
   - Removido `unique_together`
   - Agregados índices

4. `main/models/salida_normalizada.py`
   - Removido `unique_together`
   - Agregados índices

5. `main/models/planificacion.py`
   - Agregados índices

6. `main/models/salida.py`
   - Agregados índices

## Migración Aplicada

```bash
python manage.py makemigrations
python manage.py migrate
```

**Migración creada:** `0010_alter_planificacionnormalizada_unique_together_and_more.py`

## Próximos Pasos Recomendados

1. **Testing:** Probar normalización con datasets grandes (>1000 registros)
2. **Monitoring:** Verificar que no haya errores de integridad
3. **Cleanup:** Eliminar registros duplicados en raw si existen
4. **Background Jobs:** Considerar Celery para procesos muy grandes (>10k registros)

## Notas Importantes

- ⚠️ Los cambios son **backwards compatible** - no requieren migración de datos
- ✅ OneToOne sigue garantizando 1 raw = 1 normalizado
- ✅ Los índices mejorarán todas las queries existentes
- ✅ Las transacciones previenen inconsistencias
