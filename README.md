# ETL-Project-Manager

Aplicación Flask para carga ETL de ventas, validación por capas y persistencia transaccional en MySQL.

## Documentación principal

- Validaciones del proceso ETL: [docs/VALIDACION.md](docs/VALIDACION.md)
- Prerrequisitos e instalación: [docs/INSTALACION.md](docs/INSTALACION.md)

## Qué hace el sistema

- Gestiona autenticación y sesión de usuarios con roles.
- Permite cargar archivos CSV/XLS/XLSX para procesamiento ETL.
- Ejecuta validación por capas antes de guardar.
- Persiste registros en tablas dimensionales y de hechos.
- Genera trazabilidad de cargas en auditoría ETL.

## Stack tecnológico

- Backend: Flask
- ORM: Flask-SQLAlchemy / SQLAlchemy
- Autenticación: Flask-Login
- Formularios: Flask-WTF
- Procesamiento de datos: pandas
- Base de datos: MySQL (driver `pymysql`)

## Estructura funcional

- Aplicación y factory: `app/__init__.py`
- Modelos: `app/models.py`
- ETL (rutas/flujo): `app/etl/routes.py`
- ETL (lectura/limpieza): `app/etl/processors.py`
- Configuración por entorno: `config.py`
- Punto de entrada: `run.py`
- Scripts SQL: `sql/01_auth_schema.sql`, `sql/02_business_schema.sql`, `sql/03_load_clients.sql`, `sql/03_load_geography.sql`

## Variables de entorno

Usa `/.env.example` como plantilla para crear `/.env`.

Variables del proyecto:

- `DATABASE_URL`
- `SECRET_KEY`
- `FLASK_ENV`
- `FLASK_DEBUG`
- `INITIAL_ADMIN_PASSWORD`

## Notas operativas

- El proyecto no ejecuta migraciones automáticas.
- El esquema y los datos base se cargan con scripts SQL.
- Al iniciar, se crea usuario `admin` solo si no hay usuarios y existe el rol `admin` en base de datos.
- El archivo temporal del upload se guarda en `uploads/tmp` durante el flujo de validación/confirmación.
