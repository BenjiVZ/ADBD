# 🆔 Sistema de Mapeo Mejorado - Búsqueda por ID

**Fecha:** 19 de enero de 2026  
**Versión:** 2.0

---

## 📋 ¿Qué cambió?

El sistema de mapeo ahora **automáticamente incluye IDs** en la búsqueda de normalización, además de nombres.

### ✅ ANTES (solo nombres)
```
Excel: "Valencia"  → Busca en mapeo → CEDIS oficial
```

### ✅ AHORA (nombres + IDs)
```
Excel: "Valencia" → Busca en mapeo → CEDIS oficial
Excel: "5"        → Busca en mapeo → CEDIS oficial (mismo resultado)
Excel: "VAL"      → Busca en mapeo → CEDIS oficial (mismo resultado)
```

---

## 🔍 ¿Cómo funciona?

### Orden de búsqueda para CEDIS:

1. **Búsqueda directa** en tabla Cendis:
   - Por `origin` (nombre): "Guatire 1"
   - Por `id`: 1, 2, 3, 4, 5
   - Por `code`: "GUA", "VAL", "CAR"

2. **Búsqueda en mapeos** MapeoCedis:
   - Por `nombre_crudo`: lo que guardaste en el mapeo
   - Por `id` del CEDIS mapeado: automático ✨
   - Por `code` del CEDIS mapeado: automático ✨

### Orden de búsqueda para Sucursales:

1. **Búsqueda directa** en tabla Sucursal:
   - Por `name`: "Sambil Valencia"
   - Por `bpl_id`: 1, 2, 3... 46

2. **Búsqueda en mapeos** MapeoSucursal:
   - Por `nombre_crudo`: lo que guardaste en el mapeo
   - Por `bpl_id` de la sucursal mapeada: automático ✨

---

## 💡 Ejemplos Prácticos

### Ejemplo 1: Mapeo de CEDIS por nombre

**Crear mapeo:**
```
nombre_crudo = "VALENCIA I"
cedis_oficial = Cendis(id=2, origin="Valencia", code="VAL")
```

**Búsquedas que funcionan en Excel:**
- ✅ "VALENCIA I" → encuentra por nombre_crudo
- ✅ "Valencia" → encuentra por origin directo
- ✅ "2" → encuentra por ID (automático desde el mapeo) ✨
- ✅ "VAL" → encuentra por code (automático desde el mapeo) ✨

### Ejemplo 2: Mapeo de Sucursal por ID

**Crear mapeo:**
```
nombre_crudo = "25"
sucursal_oficial = Sucursal(bpl_id=25, name="Sambil Valencia")
```

**Búsquedas que funcionan en Excel:**
- ✅ "25" → encuentra por nombre_crudo o bpl_id directo
- ✅ "Sambil Valencia" → encuentra por name directo
- ✅ "SAMBIL VALENCIA" → encuentra si name coincide (case insensitive)

### Ejemplo 3: Contenido crudo con ID numérico

**Si en tu Excel de Planificación tienes:**
```
Sucursal: "25"
CEDIS: "2"
```

**Antes de normalizar, creas mapeos:**
- No hace falta! El sistema busca directamente por bpl_id=25 y cedis.id=2

**Pero si quieres mapear un alias:**
```python
# En caso de que "25" sea un alias de otra sucursal
MapeoSucursal.objects.create(
    nombre_crudo="25",
    sucursal_oficial=Sucursal.objects.get(bpl_id=15)  # Mapea 25 → 15
)
```

---

## 🎯 Ventajas

### 1. **Flexibilidad total**
Puedes poner en los Excel:
- Nombres completos: "Guatire 1"
- IDs numéricos: "1", "2", "3"
- Códigos cortos: "GUA", "VAL", "CAR"
- Alias personalizados: "Valencia I", "VALENCIA"

### 2. **Menos errores de normalización**
El sistema encuentra coincidencias automáticamente sin crear mapeos adicionales.

### 3. **Mapeos más inteligentes**
Cuando creas un mapeo, automáticamente incluye:
- El ID del registro oficial
- El código (si existe)
- El nombre original

### 4. **Compatibilidad con datos antiguos**
Si ya tienes mapeos creados por nombre, ahora también funcionan por ID sin cambios.

---

## 📊 Casos de Uso

### Caso 1: Excel con IDs numéricos
```
| Sucursal | CEDIS | Producto |
|----------|-------|----------|
| 25       | 2     | ABC123   |
| 30       | 5     | XYZ789   |
```
✅ Se normaliza directamente sin mapeos

### Caso 2: Excel con nombres variados
```
| Sucursal         | CEDIS      | Producto |
|------------------|------------|----------|
| SAMBIL VALENCIA  | Valencia   | ABC123   |
| Sambil Valencia  | VALENCIA I | XYZ789   |
```
✅ Creas mapeos para "SAMBIL VALENCIA" y "VALENCIA I"
✅ Automáticamente funciona con ID "25" y "2" también

### Caso 3: Excel mixto
```
| Sucursal | CEDIS      | Producto |
|----------|------------|----------|
| 25       | Valencia   | ABC123   |
| Sambil   | 2          | XYZ789   |
```
✅ Funciona perfectamente con búsqueda híbrida

---

## 🔧 Implementación Técnica

### En `planificacion_normalize.py`:

```python
# Mapeos ahora incluyen IDs automáticamente
mapeos_cedis_dict = {}
for m in mapeos_cedis:
    mapeos_cedis_dict[m.nombre_crudo.lower()] = m.cedis_oficial
    mapeos_cedis_dict[str(m.cedis_oficial.id).lower()] = m.cedis_oficial
    if m.cedis_oficial.code:
        mapeos_cedis_dict[m.cedis_oficial.code.lower()] = m.cedis_oficial

mapeos_sucursales_dict = {}
for m in mapeos_sucursales:
    mapeos_sucursales_dict[m.nombre_crudo.lower()] = m.sucursal_oficial
    mapeos_sucursales_dict[str(m.sucursal_oficial.bpl_id).lower()] = m.sucursal_oficial
```

### Búsqueda mejorada:

```python
# Busca por nombre, ID o código (lo que venga en el Excel)
sucursal_key = raw.sucursal.strip().lower()

# 1. Búsqueda directa (nombre o BPL_ID)
sucursal = sucursales_map.get(sucursal_key)

# 2. Búsqueda en mapeos (ahora incluye IDs automáticamente)
if not sucursal:
    sucursal = mapeos_sucursales_dict.get(sucursal_key)
```

---

## 📝 Notas Importantes

1. **Los mapeos existentes siguen funcionando** - No necesitas modificarlos
2. **La búsqueda es case-insensitive** - "VALENCIA" = "valencia" = "Valencia"
3. **Los IDs se convierten a string y lowercase** - 25 = "25"
4. **El orden de búsqueda importa** - Primero directo, luego mapeos
5. **No se modifican datos crudos** - Los mapeos son solo para normalización

---

## ✅ Resultado

Ahora puedes:
- ✅ Poner IDs directamente en los Excel
- ✅ Crear mapeos por nombre que automáticamente incluyen IDs
- ✅ Mezclar nombres e IDs en el mismo archivo
- ✅ Tener menos errores de normalización
- ✅ Mayor flexibilidad en formatos de entrada

---

**¡Tu sistema es más inteligente ahora! 🚀**
