# Sistema de Resolución Interactiva de Errores

## 🎯 ¿Qué hace este sistema?

Cuando normalizas datos de **Planificación** o **Salidas**, algunos registros pueden fallar porque:
- ❌ Sucursales no existen en el maestro
- ❌ Productos no existen en el catálogo
- ❌ Errores de escritura o variaciones de nombres

Este sistema te permite **resolver estos errores de forma interactiva** sin necesidad de:
- Editar archivos Excel manualmente
- Modificar la base de datos con SQL
- Re-cargar los datos desde cero

---

## 📍 Cómo usar el sistema

### 1. Normaliza tus datos como siempre

**Planificación:**
- Ve a: http://localhost:2222/planificacion/normalizar/
- Haz clic en "Normalizar pendientes"

**Salidas:**
- Ve a: http://localhost:2222/salidas/normalizar/
- Haz clic en "Normalizar pendientes"

### 2. Si hay errores, verás un botón rojo

El sistema mostrará:
```
🔧 Resolver X errores
```

### 3. Haz clic en "Resolver Errores"

Te llevará a una pantalla interactiva que muestra:

#### 📊 **Errores agrupados por tipo:**
- 🏢 Sucursales no encontradas
- 📦 Productos no encontrados

#### 💡 **Sugerencias automáticas:**
El sistema usa **fuzzy matching** para sugerirte opciones similares:
- Si tienes "CEDIS NORT" → sugiere "CEDIS NORTE"
- Si tienes "PROD123" → sugiere "PROD12345"

---

## 🛠️ Opciones para resolver cada error

### Opción 1: ➕ **Crear Nuevo**

Crea la sucursal o producto faltante:

**Para Sucursales:**
- Nombre: CEDIS NORTE
- BPL ID: 101

**Para Productos:**
- Código: PROD123
- Nombre: Producto ejemplo
- Grupo: ABARROTES (opcional)

✅ **Resultado:** Se crea el registro y todos los errores relacionados se marcan como "pending" para re-normalizar.

---

### Opción 2: 🔗 **Mapear a Existente**

Corrige variaciones o errores de escritura:

**Ejemplo:**
- **Nombre en datos:** "CEDIS NORT" (con error)
- **Mapear a:** "CEDIS NORTE" (correcto)

✅ **Resultado:** Todos los registros con "CEDIS NORT" se actualizan automáticamente a "CEDIS NORTE" y se marcan como "pending".

---

### Opción 3: ❌ **Ignorar** (solo Planificación)

Marca el error como ignorado si no necesitas normalizarlo:

✅ **Resultado:** Los registros se marcan como "ignored" y no aparecen más en la lista de errores.

---

## 🔄 Flujo completo de ejemplo

### Ejemplo 1: Sucursal con error de escritura

1. **Error detectado:**
   ```
   🏢 Sucursal no encontrada: "CEDIS NORT"
   25 registros afectados
   ```

2. **Sistema sugiere:**
   ```
   💡 Sugerencias similares:
   [CEDIS NORTE] [CEDIS NORESTE]
   ```

3. **Acción:** Haces clic en "CEDIS NORTE"
   - Se abre modal con:
     - Nombre en datos: CEDIS NORT
     - Mapear a: CEDIS NORTE ✓

4. **Resultado:**
   - ✅ 25 registros actualizados a "CEDIS NORTE"
   - ✅ Marcados como "pending"
   - 🔄 Vuelves a normalizar y ahora pasan correctamente

---

### Ejemplo 2: Producto nuevo que no existe

1. **Error detectado:**
   ```
   📦 Producto no encontrado: "PROD789"
   10 registros afectados
   ```

2. **No hay sugerencias (producto realmente nuevo)**

3. **Acción:** Haces clic en "➕ Crear Nuevo Producto"
   - Código: PROD789
   - Nombre: Aceite de Oliva 500ml
   - Grupo: ABARROTES

4. **Resultado:**
   - ✅ Producto creado en maestro
   - ✅ 10 registros marcados como "pending"
   - 🔄 Vuelves a normalizar y ahora pasan correctamente

---

## 🎨 Interfaz visual

### Vista de errores agrupados:
```
🔧 Resolver Errores de Planificación

Total de errores: 45

🏢 Sucursales No Encontradas
┌──────────────────────────────────────┐
│ CEDIS NORT                 [25 registros] │
│ 💡 Sugerencias: CEDIS NORTE            │
│ [➕ Crear] [🔗 Mapear] [❌ Ignorar]    │
└──────────────────────────────────────┘

📦 Productos No Encontrados
┌──────────────────────────────────────┐
│ PROD789                    [20 registros] │
│ 💡 Sin sugerencias                     │
│ [➕ Crear] [🔗 Mapear] [❌ Ignorar]    │
└──────────────────────────────────────┘
```

---

## 📋 Ventajas del sistema

✅ **Rápido:** Resuelves 100+ errores en minutos
✅ **Visual:** Ves claramente qué está fallando
✅ **Inteligente:** Sugerencias automáticas
✅ **Seguro:** Transacciones atómicas, no rompe datos
✅ **Eficiente:** Actualiza múltiples registros de una vez
✅ **Sin re-trabajo:** No necesitas volver a cargar archivos Excel

---

## 🚀 Workflow recomendado

```
1. Cargar archivos Excel
   ↓
2. Normalizar datos
   ↓
3. ¿Hay errores? → Ir a "Resolver Errores"
   ↓
4. Crear/mapear lo necesario
   ↓
5. Volver a normalizar
   ↓
6. ✅ Todo OK → Ver tablero normalizado
```

---

## 🔗 URLs del sistema

| Funcionalidad | URL |
|---------------|-----|
| Normalizar Planificación | `/planificacion/normalizar/` |
| Resolver Errores Planificación | `/planificacion/errores/` |
| Normalizar Salidas | `/salidas/normalizar/` |
| Resolver Errores Salidas | `/salidas/errores/` |

---

## 💡 Tips

1. **Usa sugerencias:** El fuzzy matching es muy preciso
2. **Crea maestros primero:** Importa sucursales/productos antes de normalizar
3. **Mapea patrones comunes:** Si ves "CEDIS" vs "C.E.D.I.S", mapea uno al otro
4. **No ignores a la ligera:** Solo ignora si realmente no necesitas el dato

---

## 🐛 Troubleshooting

**Problema:** "No encuentro el botón de resolver errores"
- ✅ Solo aparece si hay errores (contador > 0)

**Problema:** "Las sugerencias no aparecen"
- ✅ Normal si el nombre es muy diferente o único
- ℹ️ El fuzzy matching requiere 60% de similitud mínima

**Problema:** "No puedo crear sucursal (error duplicate)"
- ✅ Ya existe con ese BPL ID, usa "Mapear" en su lugar

**Problema:** "Después de mapear sigue apareciendo el error"
- ✅ Vuelve a normalizar, los registros se marcaron como "pending"
