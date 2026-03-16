# Prerrequisitos e Instalacion

Este documento describe lo necesario para ejecutar la aplicacion localmente.

## Prerrequisitos

- Python 3.11
- MySQL 8.x
- Pip actualizado

## Instalacion automatica en Windows (recomendada)

Si deseas instalar y abrir la aplicacion sin usar terminal manualmente:

1. Ejecuta `1_instalar_proyecto_windows.bat` con doble clic.
2. El instalador realiza automaticamente:
	- Creacion de `.venv` (si no existe)
	- Instalacion de dependencias
	- Creacion de `.env` desde `.env.example` (si no existe)
	- Creacion de acceso directo en Escritorio: `ETL Project Manager`
3. Edita el archivo `.env` con tus valores reales (base de datos y claves).
4. Usa el acceso directo del escritorio (o `2_abrir_app_windows.bat`) para abrir la app diariamente.

Nota:

- Si el acceso directo no se crea por permisos del sistema, ejecuta manualmente `2_abrir_app_windows.bat`.

## 1) Clonar y entrar al proyecto

```bash
git clone <url-del-repositorio>
cd ETL-Project-Manager
```

## 2) Crear entorno virtual

Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
```

## 3) Instalar dependencias

```bash
pip install -r requirements.txt
```

## 4) Crear base de datos y cargar scripts SQL

Ejecuta en este orden los archivos de la carpeta `sql/`:

1. `sql/01_auth_schema.sql`
2. `sql/02_business_schema.sql`
3. `sql/03_load_clients.sql`
4. `sql/03_load_geography.sql`

Nota:

- El sistema espera que exista el rol `admin` para poder crear el usuario inicial automaticamente.

## 5) Configurar variables de entorno

Usa la plantilla:

```bash
cp .env.example .env
```

En Windows PowerShell, si no tienes `cp`:

```powershell
Copy-Item .env.example .env
```

Edita `.env` con tus valores reales:

- `DATABASE_URL`
- `SECRET_KEY`
- `FLASK_ENV`
- `FLASK_DEBUG`
- `INITIAL_ADMIN_PASSWORD`

Ejemplo de `DATABASE_URL`:

`mysql+pymysql://root:tu_password@localhost/etl_ventas_db`

## 6) Ejecutar la aplicacion

```bash
python run.py
```

La aplicacion queda disponible en:

`http://127.0.0.1:5000`

## 7) Primer acceso

Si la tabla de usuarios esta vacia y existe el rol `admin` en BD, el sistema crea automaticamente:

- Usuario: `admin`
- Contrasena: valor de `INITIAL_ADMIN_PASSWORD`

## Solucion de problemas comunes

- Error de conexion a BD: revisa `DATABASE_URL` y que MySQL este activo.
- Error por rol admin ausente: inserta el rol `admin` en la tabla `role` y reinicia la app.
- Error al leer XLS/XLSX: valida que el archivo no este corrupto y que se instalo `xlrd`/`openpyxl`.
