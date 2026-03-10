# Sistema de Validación por Capas - ETL Project Manager

## 📋 Resumen de Implementación

Este documento describe el sistema de validación por capas implementado en el módulo ETL para garantizar la calidad de los datos antes de su persistencia en la base de datos.

**Fecha de implementación:** Marzo 2026  
**Archivos modificados:**
- `app/etl/routes.py`
- `app/templates/etl/upload.html`

---

## 🎯 Objetivo

Implementar un sistema robusto de validación que verifique la integridad y consistencia de los datos cargados **antes** de persistirlos en la base de datos, proporcionando retroalimentación detallada al usuario para facilitar la corrección de errores.

Este enfoque es fundamental para la **Metodología de la Tesis**, ya que garantiza que solo datos válidos y consistentes ingresen al Data Warehouse.

---

## 🏗️ Arquitectura del Sistema

### Diagrama de Flujo

```
┌─────────────────────┐
│  Usuario carga      │
│  archivo (CSV/XLSX) │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  CAPA 1: VALIDACIÓN │
│  DE FORMATO (Pandas)│
├─────────────────────┤
│ • Valores nulos     │
│ • Tipos de datos    │
│ • Columnas críticas │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  CAPA 2: VALIDACIÓN │
│  DE INTEGRIDAD (SQL)│
├─────────────────────┤
│ • Sorteo duplicado  │
│ • Distribuidores    │
│   no registrados    │
└──────────┬──────────┘
           │
      ¿Hay errores?
           │
    ┌──────┴──────┐
    │             │
   SÍ            NO
    │             │
    ▼             ▼
┌───────┐   ┌──────────────┐
│ JSON  │   │ Vista Previa │
│ 400   │   │   (HTML)     │
└───┬───┘   └──────┬───────┘
    │              │
    ▼              ▼
┌──────────┐  ┌────────────┐
│ Mostrar  │  │ Confirmar  │
│ Errores  │  │   Carga    │
└──────────┘  └────────────┘
```

---

## 📦 CAPA 1: Validaciones de Formato (Pandas)

### Objetivo
Verificar la integridad estructural del archivo **antes** de realizar consultas a la base de datos.

### Validaciones Implementadas

#### 1.1. Normalización de Columnas
- **Qué hace:** Limpia y estandariza los nombres de columnas
- **Implementación:** `.str.strip().str.lower()`
- **Beneficio:** Permite identificar columnas independientemente de mayúsculas/minúsculas o espacios

#### 1.2. Mapeo de Columnas Esperadas
- **Columnas críticas detectadas:**
  - `sorteo`: número de sorteo
  - `distribuidor`: código del distribuidor
  - `vendida`: cantidad vendida
  - `bruto_vendido`: valor bruto de ventas
  - `neto_vendido`: valor neto de ventas

- **Variantes aceptadas:**
  ```python
  {
      'sorteo': ['sorteo', 'numero sorteo', 'num sorteo'],
      'distribuidor': ['distribuidor', 'codigo distribuidor', 'cod distribuidor'],
      'vendida': ['vendida', 'cantidad vendida', 'cant vendida'],
      # ...
  }
  ```

#### 1.3. Validación de Valores Nulos
- **Columnas verificadas:** Sorteo, Distribuidor, Vendida
- **Reporte:** Cantidad de valores nulos por columna
- **Ejemplo de error:**
  ```json
  {
      "valores_nulos": [
          "Sorteo: 3 valores nulos",
          "Distribuidor: 1 valores nulos"
      ]
  }
  ```

#### 1.4. Validación de Tipos Numéricos
- **Columnas verificadas:** `bruto_vendido`, `neto_vendido`
- **Método:** `pd.to_numeric(df[col], errors='raise')`
- **Ejemplo de error:**
  ```json
  {
      "formato_numerico": [
          "bruto vendido: contiene valores no numéricos"
      ]
  }
  ```

---

## 🔗 CAPA 2: Validaciones de Integridad (SQLAlchemy)

### Objetivo
Verificar la consistencia con los datos maestros existentes en la base de datos.

### Validaciones Implementadas

#### 2.1. Sorteo Duplicado
- **Qué verifica:** Si el número de sorteo ya existe en `Fact_Ventas`
- **Query:** `FactVentas.query.filter_by(sorteo=int(sorteo_numero)).first()`
- **Previene:** Carga duplicada del mismo sorteo
- **Ejemplo de error:**
  ```json
  {
      "sorteo": "El sorteo 12345 ya existe en la base de datos"
  }
  ```

#### 2.2. Distribuidores No Registrados
- **Qué verifica:** Si todos los códigos de distribuidor existen en `Dim_Distribuidor`
- **Método:**
  1. Extrae códigos únicos del archivo
  2. Consulta distribuidores existentes en BD
  3. Identifica códigos faltantes
- **Query:**
  ```python
  DimDistribuidor.query.filter(
      DimDistribuidor.codigo_distribuidor.in_(codigos_archivo_str)
  ).all()
  ```
- **Ejemplo de error:**
  ```json
  {
      "distribuidores_faltantes": ["282056", "195328", "104521"]
  }
  ```

---

## 🎨 Frontend: Visualización de Errores

### Sistema de Mensajes Dinámicos

El archivo `upload.html` incluye un contenedor de mensajes que se actualiza dinámicamente:

```html
<div id="mensajesValidacion" class="hidden mb-6 rounded-lg border px-4 py-4 text-sm"></div>
```

### Categorías de Mensajes

1. **Cargando** (Azul)
   - Indicador de procesamiento
   - Ícono: spinner animado

2. **Error de Formato** (Naranja)
   - Columnas faltantes
   - Valores no numéricos

3. **Valores Nulos** (Amarillo)
   - Conteo de nulos por columna

4. **Sorteo Duplicado** (Rojo)
   - Advertencia de duplicación

5. **Distribuidores Faltantes** (Púrpura)
   - Lista de códigos no registrados
   - Formato: "• Falta crear el distribuidor **282056**"

### Función JavaScript de Renderizado

```javascript
function mostrarErroresValidacion(reporte) {
    // Itera sobre cada categoría de error
    // Construye HTML con estilos Tailwind específicos
    // Renderiza en el contenedor con scroll automático
}
```

---

## 🔄 Flujo de Datos

### 1. Envío del Formulario
```javascript
formUpload.addEventListener('submit', function(e) {
    e.preventDefault();
    const formData = new FormData(formUpload);
    
    fetch(formUpload.action, {
        method: 'POST',
        body: formData
    })
    .then(response => {
        // Manejo de respuesta HTML (200) o JSON (400)
    });
});
```

### 2. Respuesta del Backend

**Caso 1: Errores de Validación (400)**
```json
{
    "formato": "Faltan columnas críticas: sorteo",
    "valores_nulos": ["Distribuidor: 2 valores nulos"],
    "distribuidores_faltantes": ["282056"]
}
```

**Caso 2: Validación Exitosa (200)**
```html
<!-- Vista previa con tabla HTML -->
<div class="preview-container">
    <table>...</table>
</div>
```

### 3. Almacenamiento en Sesión

Al aprobar validaciones, los datos se guardan en sesión para el siguiente paso:

```python
session['upload_data'] = {
    'filename': file.filename,
    'data': df.to_json(orient='split'),
    'columnas_mapeadas': columnas_mapeadas
}
```

---

## 📊 Ejemplo de Uso

### Archivo de Entrada (CSV)

```csv
Sorteo,Distribuidor,Vendida,Bruto Vendido,Neto Vendido
12345,195328,100,500000,450000
12345,282056,75,375000,337500
12345,,50,250000,225000
```

### Errores Detectados

1. **Valores Nulos:**
   - `Distribuidor: 1 valores nulos` (fila 3)

2. **Distribuidores Faltantes:**
   - `282056` (no existe en `Dim_Distribuidor`)

### Visualización en Frontend

```
┌──────────────────────────────────────────────────┐
│ ⚠️ Errores de Validación                        │
├──────────────────────────────────────────────────┤
│ ┃ Valores Nulos Detectados:                     │
│ ┃ • Distribuidor: 1 valores nulos               │
├──────────────────────────────────────────────────┤
│ ┃ Distribuidores No Registrados:                │
│ ┃ Los siguientes códigos no existen en la BD:   │
│ ┃ • Falta crear el distribuidor 282056          │
└──────────────────────────────────────────────────┘
```

---

## 🧪 Pruebas Recomendadas

### Test 1: Archivo con Columnas Faltantes
```csv
Sorteo,Vendida
12345,100
```
**Resultado esperado:** Error de formato - falta columna "Distribuidor"

### Test 2: Valores No Numéricos
```csv
Sorteo,Distribuidor,Vendida,Bruto Vendido
12345,195328,100,ABC
```
**Resultado esperado:** Error de formato numérico en "bruto vendido"

### Test 3: Sorteo Duplicado
- Cargar un archivo con sorteo que ya existe en `Fact_Ventas`
**Resultado esperado:** Error de integridad - sorteo duplicado

### Test 4: Distribuidor No Registrado
```csv
Sorteo,Distribuidor,Vendida
12345,999999,100
```
**Resultado esperado:** Error de integridad - distribuidor 999999 no existe

### Test 5: Archivo Válido
```csv
Sorteo,Distribuidor,Vendida,Bruto Vendido,Neto Vendido
12346,195328,100,500000,450000
```
**Resultado esperado:** Vista previa exitosa

---

## 📚 Beneficios para la Tesis

### 1. Calidad de Datos
- Garantiza que solo datos válidos ingresen al Data Warehouse
- Previene inconsistencias en reportes analíticos

### 2. Trazabilidad
- Cada validación está documentada en código
- Comentarios metodológicos facilitan explicación en documentación

### 3. Experiencia de Usuario
- Errores claros y accionables
- Retroalimentación inmediata sin recargas de página

### 4. Escalabilidad
- Fácil agregar nuevas validaciones
- Estructura modular por capas

---

## 🔧 Extensiones Futuras

### Validaciones Adicionales Recomendadas

1. **Validación de Rangos:**
   - Verificar que `cantidad_vendida ≤ cantidad_despachada`
   - Validar que `neto_vendido ≤ bruto_vendido`

2. **Validación de Fechas:**
   - Verificar que la fecha del sorteo sea válida
   - Validar coherencia temporal

3. **Validación de Municipios:**
   - Verificar que el municipio del distribuidor coincida con los datos maestros

4. **Límites de Negocio:**
   - Validar que las ventas no excedan el cupo asignado al distribuidor

### Mejoras de Performance

- **Caching:** Almacenar distribuidores válidos en caché Redis
- **Validación Asíncrona:** Procesar archivos grandes en background con Celery
- **Paginación:** Validar en lotes para archivos muy grandes

---

## 📝 Conclusión

El sistema de validación por capas implementado proporciona:

✅ **Robustez:** Múltiples niveles de verificación  
✅ **Claridad:** Mensajes de error específicos y accionables  
✅ **Eficiencia:** Validaciones Pandas antes de consultas SQL  
✅ **Mantenibilidad:** Código bien documentado y modular  
✅ **Usabilidad:** Interfaz intuitiva con feedback visual  

Este sistema es un componente clave de la arquitectura ETL y sirve como base para los capítulos de **Metodología** y **Desarrollo** de la tesis.

---

**Desarrollado por:** Juan Carlos  
**Proyecto:** ETL Project Manager  
**Tecnologías:** Flask, Pandas, SQLAlchemy, Tailwind CSS, JavaScript ES6
