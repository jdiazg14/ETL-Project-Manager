# Validacion del Proceso ETL

Este documento describe las validaciones que ejecuta la aplicacion durante la carga de archivos ETL.

## Flujo general

El endpoint `POST /etl/upload` ejecuta una validacion unificada en tres etapas:

1. Validacion de formato
2. Validacion de integridad
3. Validacion de reglas de negocio

Si existen errores criticos, la carga no se puede confirmar.
Si solo existen advertencias, la carga se puede confirmar.

## Etapa 1: Validacion de formato (bloqueante)

Objetivo: asegurar que el archivo tenga estructura y tipos de datos utilizables.

Validaciones realizadas:

- Extension permitida: `csv`, `xls`, `xlsx`.
- Lectura correcta del archivo con `pandas`.
- Normalizacion de encabezados.
- Mapeo de columnas esperadas con sinonimos.
- Verificacion de columnas criticas requeridas.
- Conversion estricta de columnas numericas.
- Deteccion de valores no numericos por fila y columna.
- **Validacion de valores negativos en cantidades y montos:** se verifica que `cantidad_despachada`, `cantidad_devuelta`, `cantidad_vendida`, `bruto_despacho`, `bruto_devuelto`, `bruto_vendido` y `neto_vendido` sean >= 0 (previene violacion de restriccion `chk_fac_cantidades_nonnegative` en BD).
- Deteccion de nulos en columnas clave (advertencia).
- Si falta columna `porcentaje`, se completa con `25.0` (advertencia).

Resultado:

- Si faltan columnas criticas, hay basura numerica, o existen valores negativos en cantidades, se generan errores criticos y se bloquea la carga.

## Etapa 2: Validacion de integridad (bloqueante)

Objetivo: validar coherencia contra datos existentes en base de datos.

Validaciones realizadas:

- Sorteos duplicados en `Fact_Ventas`.
- Codigos de distribuidor inexistentes en `Dim_Distribuidor`.
- Fecha invalida construida desde columnas `anio`, `mes`, `dia`.

Resultado:

- Cualquier incumplimiento genera error critico y bloquea la confirmacion de carga.

## Etapa 3: Reglas de negocio contables (no bloqueante)

Objetivo: detectar inconsistencias de calidad de dato sin frenar el proceso si no hay errores criticos.

Reglas evaluadas por fila:

1. `Despachada - Devuelta == Vendida`
2. `Bruto despacho - Bruto devuelto == Bruto vendido`
3. `Neto vendido == Bruto vendido * (100 - Porcentaje) / 100`

Resultado:

- Las inconsistencias se registran como advertencias.
- Las advertencias no bloquean la carga.

## Confirmacion de carga

El endpoint `POST /etl/confirm-upload` solo inserta en base de datos cuando:

- Ya se ejecuto la validacion unificada.
- No existen errores criticos (`puede_cargar = true`).

Adicionalmente:

- Inserta datos en `Fact_Ventas` de forma transaccional.
- Registra auditoria inmutable en `etl_project_logs` con accion `CARGA`.

## Fuentes tecnicas verificadas

- `app/etl/routes.py`
- `app/etl/processors.py`
- `app/models.py`

## Mejoras Recientes (Marzo 2026)

### Validacion previa de cantidades negativas (Prevención en Python)

Para evitar que errores de negocio lleguen hasta SQL, se agregó validación en **ETAPA 1** que detecta valores negativos antes de cualquier INSERT:

**Ubicación:** `app/etl/routes.py` → `validar_formato()`

**Comportamiento:**
- Sistema revisa cada valor en columnas de cantidad y monto
- Si detecta un negativo, lo agrega a `errores_criticos`
- Bloquea la carga (botón "Guardar" permanece deshabilitado)
- Usuario ve mensaje claro: "Columna 'vendida': valores negativos en filas 3, 5, 8"

**Ventaja:** El error se detecta y comunica en la etapa de validación, no como excepción SQL cruda.

### Manejo amigable de errores de integridad SQL

Si a pesar de la validación previa ocurre una violación de restricción en BD (ej: `check constraint 'chk_fac_cantidades_nonnegative' violated`):

**Ubicación:** `app/etl/routes.py` → `confirm_upload()` endpoint

**Captura especial:**
```python
except IntegrityError:
    return {'error': 'Error de Integridad: Se detectaron cantidades negativas que no cumplen con las reglas de negocio. Revise el archivo y vuelva a cargarlo.'}
```

**Antes:** Usuario veía traza cruda de pymysql/SQLAlchemy (líneas de código, SQL completo)

**Después:** Mensaje genérico y profesional en español

### Deshabilitacion del boton "Guardar" ante errores

Cambio en interfaz (`app/templates/etl/upload.html`):

**Antes:** Botón se rehabilitaba tras un error (permitiendo intentar guardar de nuevo)

**Después:** Botón permanece deshabilitado cuando hay error (requiere recargar archivo)

**Lógica:** Como el archivo contiene datos inválidos, no tiene sentido permitir reintentos. Usuario debe corregir el origen.

---
