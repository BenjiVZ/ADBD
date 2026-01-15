# 🏭🏢 CLARIFICACIÓN DE TERMINOLOGÍA: CEDIS Y SUCURSALES

**Fecha:** 14 de enero de 2026

---

## ✅ TERMINOLOGÍA OFICIAL

### CEDIS (Centros de Distribución)
- **Definición:** Almacenes desde donde se despachan productos
- **Función:** Origen de distribución
- **Tabla:** `Cendis`
- **Símbolo:** 🏭

### Sucursales
- **Definición:** Tiendas/Puntos de venta donde se reciben productos
- **Función:** Destino de distribución (o transferencias entre tiendas)
- **Tabla:** `Sucursal`
- **Símbolo:** 🏢

---

## 📊 FLUJOS DE DISTRIBUCIÓN

### Flujo Principal: CEDIS → Sucursal
```
Almacén (CEDIS) → Tienda (Sucursal)
🏭 La Yaguara → 🏢 BARQUISIMETO
```

### Flujo Secundario: Sucursal → Sucursal
```
Tienda → Tienda (transferencia)
🏢 MARACAIBO → 🏢 PUERTO LA CRUZ
```

---

## 🔧 CAMBIOS APLICADOS

### 1. Modelos Actualizados

#### `main/models/cendis.py`
```python
class Cendis(models.Model):
    """Centro de Distribución (CEDIS) - Almacén desde donde se despachan productos"""
    origin = models.CharField(max_length=255, help_text="Nombre del almacén/centro de distribución")
    code = models.CharField(max_length=50, unique=True, help_text="Código único del CEDIS")

    class Meta:
        verbose_name = "CEDIS (Almacén)"
        verbose_name_plural = "CEDIS (Almacenes)"
```

#### `main/models/sucursal.py`
```python
class Sucursal(models.Model):
    """Sucursal - Tienda/Punto de venta donde se reciben productos"""
    bpl_id = models.IntegerField(unique=True, help_text="ID único de la sucursal en el sistema ERP")
    name = models.CharField(max_length=255, unique=True, help_text="Nombre de la tienda/sucursal")

    class Meta:
        verbose_name = "Sucursal (Tienda)"
        verbose_name_plural = "Sucursales (Tiendas)"
```

### 2. Planificación Normalizada

```python
class PlanificacionNormalizada(models.Model):
    """Planificación normalizada: Almacén (CEDIS) → Tienda (Sucursal)"""
    sucursal = models.ForeignKey(Sucursal, help_text="Tienda destino")
    cedis_origen = models.ForeignKey(Cendis, help_text="Almacén origen")
```

### 3. Salida Normalizada

```python
class SalidaNormalizada(models.Model):
    """Salida normalizada: Almacén (CEDIS) → Tienda (Sucursal) o Tienda → Tienda"""
    cedis_origen = models.ForeignKey(Cendis, help_text="Almacén origen (si aplica)")
    sucursal_destino = models.ForeignKey(Sucursal, help_text="Tienda destino")
```

### 4. Vista de Normalización - Planificación

**Antes:**
```python
# Normalizar sucursal DESTINO
# Normalizar CEDIS ORIGEN (cendis) - busca en tabla Cendis
```

**Después:**
```python
# Normalizar SUCURSAL DESTINO (tienda)
print(f"   🏢 Buscando sucursal (tienda): '{sucursal_key}'...")

# Normalizar CEDIS ORIGEN (almacén/centro de distribución)
print(f"   🏭 Buscando CEDIS (almacén): '{cendis_key}'...")
```

### 5. Vista de Normalización - Salidas

**Antes:**
```python
# ORIGEN debe ser CENDIS (tabla Cendis)
# DESTINO debe ser Sucursal (tabla Sucursal)
```

**Después:**
```python
# ORIGEN: Buscar primero en CEDIS (almacenes), si no existe, buscar en Sucursales (tiendas)
print(f"   🏭 Origen: '{origen_key}' -> ✅ CEDIS (almacén) encontrado")
print(f"   ⚠️ Origen '{origen_key}' es una SUCURSAL/TIENDA (transferencia entre tiendas)")

# DESTINO debe ser Sucursal/Tienda (tabla Sucursal)
print(f"   🏢 Buscando sucursal/tienda destino: '{destino_key}'...")
```

---

## 📋 MENSAJES DE ERROR ACTUALIZADOS

### Planificación

**Antes:**
- "Sucursal destino no encontrada: XXX"
- "CEDIS origen no encontrado: YYY"

**Después:**
- "Sucursal (tienda) destino no encontrada: XXX"
- "CEDIS (almacén) origen no encontrado: YYY"

### Salidas

**Antes:**
- "CEDIS origen no encontrado: XXX"
- "Sucursal destino no encontrada: YYY"

**Después:**
- "Origen no encontrado (ni en almacenes/CEDIS ni en tiendas/sucursales): XXX"
- "Sucursal/tienda destino no encontrada: YYY"

---

## 🎯 ESTADO DE LOS DATOS

### CEDIS (Almacenes) Actuales: 7
```
1. 1000101 - La Yaguara
2. 1000105 - Guatire I
3. 1000106 - Guatire II
4. 1000114 - Guatire 4
5. 1000115 - Guatire 5
6. 1000120 - CORPORACION DAMASCO
7. 1000999 - Servicio Tecnico*

* Servicio Tecnico puede funcionar como almacén o tienda según el contexto
```

### Sucursales (Tiendas) Actuales: 47
```
Ejemplos:
- ACARIGUA (BPL: 89)
- BARQUISIMETO (BPL: 41)
- MARACAIBO (BPL: múltiples sucursales)
- PUERTO LA CRUZ (BPL: múltiples)
- Servicio Tecnico (BPL: 999)
... (43 sucursales más)
```

---

## 💡 BENEFICIOS DE LA CLARIFICACIÓN

### 1. Mejor Comprensión del Sistema
✅ Usuarios entienden inmediatamente que CEDIS = Almacenes
✅ Sucursales claramente identificadas como Tiendas

### 2. Mensajes Más Claros
✅ Logs más descriptivos durante normalización
✅ Errores más fáciles de entender y resolver

### 3. Documentación Mejorada
✅ Docstrings en modelos explican la función de cada entidad
✅ Help text en campos para el admin de Django

### 4. Mantenimiento Simplificado
✅ Nuevos desarrolladores entienden el dominio rápidamente
✅ Código auto-documentado

---

## 🔍 EJEMPLOS DE USO

### Planificación (Almacén → Tienda)
```
Mes: Enero 2026
CEDIS Origen: La Yaguara (Almacén) 🏭
Sucursal Destino: BARQUISIMETO (Tienda) 🏢
Producto: PROD123
Cantidad: 1000 unidades

Flujo: Almacén La Yaguara despacha 1000 unidades a Tienda BARQUISIMETO
```

### Salida (Almacén → Tienda)
```
Fecha: 13-01-2026
Origen: LA YAGUARA (Almacén CEDIS) 🏭
Destino: MATURIN (Tienda) 🏢
SKU: D0009454
Cantidad: 50 unidades

Flujo: Almacén La Yaguara envía 50 unidades a Tienda Maturín
```

### Salida (Tienda → Tienda - Transferencia)
```
Fecha: 13-01-2026
Origen: MARACAIBO (Tienda) 🏢
Destino: PUERTO LA CRUZ (Tienda) 🏢
SKU: D0008136
Cantidad: 25 unidades

Flujo: Tienda Maracaibo transfiere 25 unidades a Tienda Puerto La Cruz
```

---

## 📚 ARCHIVOS MODIFICADOS

1. ✅ `main/models/cendis.py` - Metadatos y docstring
2. ✅ `main/models/sucursal.py` - Metadatos y docstring
3. ✅ `main/models/planificacion_normalizada.py` - Help text y docstring
4. ✅ `main/models/salida_normalizada.py` - Help text y docstring
5. ✅ `main/views/planificacion_normalize.py` - Comentarios y mensajes
6. ✅ `main/views/salida_normalize.py` - Comentarios y mensajes

---

## ✅ CONCLUSIÓN

La terminología ahora es **cristalina** en todo el sistema:

- **CEDIS** = Almacenes/Centros de Distribución (Origen) 🏭
- **Sucursales** = Tiendas/Puntos de Venta (Destino) 🏢

Los cambios son **no-destructivos** (solo metadatos y mensajes) y mejoran significativamente la comprensión del sistema sin afectar funcionalidad.

---

**Aplicado por:** Sistema de Correcciones  
**Fecha:** 14 de enero de 2026
