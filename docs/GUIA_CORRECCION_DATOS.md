# 🔧 Sistema de Corrección de Datos Crudos

## ✅ Implementación Completada

### Nuevas Funcionalidades

Se han creado **2 pantallas nuevas** para corregir nombres mal escritos en datos crudos:

1. **Corrección de CEDIS** → `/correccion/cedis/`
2. **Corrección de Sucursales** → `/correccion/sucursales/`

---

## 🎯 Cómo Funciona

### Problema que Resuelve

Los datos crudos (Planificación y Salidas) contienen nombres mal escritos:
- ❌ "Valencia", "Valncia", "VALENCIA ", "valencia"
- ❌ "Aragua", "ARAGUA", "aragua  "
- ❌ Errores tipográficos manuales

Esto causa fallos al normalizar porque no encuentra coincidencias exactas.

### Solución

El sistema:
1. **Agrupa automáticamente** nombres similares usando algoritmo de similitud
2. **Muestra CEDIS/Sucursales oficiales** con sus IDs/códigos
3. **Permite asignar** el código oficial a cada grupo
4. **Reescribe los datos crudos** reemplazando nombres por códigos
5. Al normalizar, usa **códigos** (más confiables) en vez de nombres

---

## 📋 Uso Paso a Paso

### Para CEDIS

1. **Abrir**: http://localhost:8000/correccion/cedis/

2. **Ver estadísticas**:
   - Grupos detectados
   - Registros en Planificación
   - Registros en Salidas
   - CEDIS oficiales

3. **CEDIS Oficiales** (arriba):
   - Lista todos los CEDIS con código e ID
   - Copiar el **ID** para usar en los selectores

4. **Grupos de variantes**:
   - Cada grupo agrupa nombres similares
   - Muestra cuántos registros tiene cada variante
   - Click para expandir y ver detalles

5. **Asignar código oficial**:
   - En cada grupo, seleccionar el CEDIS oficial
   - **Usar el ID del CEDIS** (más confiable que el código)
   - Ejemplo: `1 - VAL001 (Valencia)`

6. **Aplicar correcciones**:
   - Click en "✅ Aplicar Correcciones"
   - El sistema reescribe todos los registros con el ID seleccionado
   - Muestra cuántos registros se actualizaron

### Para Sucursales

1. **Abrir**: http://localhost:8000/correccion/sucursales/

2. Similar a CEDIS pero con:
   - **BPL ID** en vez de código
   - Busca en más campos: `sucursal` (Planificación), `nombre_almacen_destino` y `nombre_sucursal_destino` (Salidas)

3. **Buscador incluido**:
   - Campo de búsqueda para filtrar sucursales oficiales
   - Útil cuando hay muchas sucursales

---

## 📊 Campos Modificados

### En Planificacion
- `cendis` → Se reemplaza con el ID del CEDIS oficial
- `sucursal` → Se reemplaza con el BPL ID de la sucursal oficial

### En Salida
- `nombre_almacen_origen` → Se reemplaza con el ID del CEDIS oficial
- `nombre_almacen_destino` → Se reemplaza con el BPL ID de la sucursal oficial
- `nombre_sucursal_destino` → Se reemplaza con el BPL ID de la sucursal oficial

---

## 🚀 Flujo Completo

```
1. Cargar datos crudos (Excel)
   ↓
2. Corregir CEDIS (/correccion/cedis/)
   ↓
3. Corregir Sucursales (/correccion/sucursales/)
   ↓
4. Normalizar Planificación (/planificacion/normalizar/)
   ↓
5. Normalizar Salidas (/salidas/normalizar/)
   ↓
6. Analizar en Tablero (/tablero/normalizado/)
```

---

## 🔍 Algoritmo de Agrupación

El sistema usa **SequenceMatcher** con umbral de similitud del 70%:

```python
# Ejemplo
"Valencia" → similitud con "Valncia" = 87% ✅ Se agrupan
"Valencia" → similitud con "Aragua" = 15% ❌ No se agrupan
```

Puedes ajustar el umbral en el código si necesitas más/menos sensibilidad.

---

## 💡 Ventajas

✅ **Sin Mapeos**: No usa tablas de mapeo intermedias, edita directamente  
✅ **Agrupación Inteligente**: Detecta automáticamente variantes similares  
✅ **Visual**: Interfaz clara con estadísticas y badges  
✅ **Seguro**: Usa transacciones atómicas (todo o nada)  
✅ **Reversible**: Los datos originales se pueden restaurar desde backup  
✅ **Eficiente**: Actualización en bulk, no registro por registro

---

## 📁 Archivos Creados

### Vistas
- `main/views/correccion_cedis.py` → Vista para corrección de CEDIS
- `main/views/correccion_sucursales.py` → Vista para corrección de Sucursales

### Templates
- `templates/correccion_cedis.html` → Interfaz para CEDIS
- `templates/correccion_sucursales.html` → Interfaz para Sucursales

### Verificación
- `scripts/verificacion/verificar_correcciones.py` → Script de análisis

### Actualizados
- `main/views/__init__.py` → Exports de nuevas vistas
- `main/urls.py` → URLs nuevas
- `main/views/upload_menu.py` → Opciones en menú principal

---

## 🎨 Diseño

### CEDIS (Morado/Azul)
- Gradiente: `#667eea` → `#764ba2`
- Tema profesional y técnico

### Sucursales (Rosa/Rojo)
- Gradiente: `#f093fb` → `#f5576c`
- Diferenciación visual clara

### Características UI
- **Responsive**: Se adapta a cualquier pantalla
- **Expandibles**: Grupos colapsables para mejor navegación
- **Badges**: Indicadores visuales de cantidad de registros
- **Hover effects**: Feedback visual en interacciones

---

## 🔧 Mantenimiento

### Ajustar Umbral de Similitud

En `correccion_cedis.py` o `correccion_sucursales.py`:

```python
# Línea ~155
def _agrupar_por_similitud(self, nombres_data, umbral=0.7):
    # Cambiar 0.7 (70%) a otro valor:
    # - 0.8 (80%) = Más estricto, menos agrupaciones
    # - 0.6 (60%) = Más permisivo, más agrupaciones
```

### Ver Agrupaciones sin Aplicar

El método `GET` solo muestra, no modifica nada. Prueba diferentes umbrales viendo la página.

---

## ✅ Estado Actual

- ✅ Sistema operativo
- ✅ Servidor corriendo en http://localhost:8000
- ✅ 5 CEDIS oficiales
- ✅ 46 Sucursales oficiales
- ✅ 1,847 Planificaciones
- ✅ 8,166 Salidas
- ✅ Acceso desde menú principal

---

## 📞 Siguiente Paso

1. Abrir navegador en: http://localhost:8000/subidas/
2. Click en "🔧 Corregir CEDIS"
3. Click en "🔧 Corregir Sucursales"
4. Revisar agrupaciones y aplicar correcciones
5. Normalizar datos como siempre

---

## 🐛 Solución de Problemas

### No aparecen grupos
→ Todos los nombres ya están correctos o no hay datos crudos

### Agrupación incorrecta
→ Ajustar umbral de similitud en el código

### Error al aplicar
→ Verificar que los IDs/BPL IDs existen en CEDIS/Sucursal

### Warning de static
→ Es normal, no afecta funcionamiento (ya documentado en PLAN_CORRECCIONES.md)

---

**¡Sistema listo para usar!** 🚀
