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
- Deteccion de nulos en columnas clave (advertencia).
- Si falta columna `porcentaje`, se completa con `25.0` (advertencia).

Resultado:

- Si faltan columnas criticas o hay basura numerica, se generan errores criticos y se bloquea la carga.

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
