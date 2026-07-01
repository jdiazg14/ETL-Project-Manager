# ETL-Project-Manager

Aplicación Flask para carga ETL de ventas, validación por capas y persistencia transaccional en MySQL.

## Por dónde empezar

Los archivos en la raíz del proyecto están numerados en el orden en que debes usarlos:

| Archivo | Qué es |
|---|---|
| `1_INSTALACION_WINDOWS.md` | Guía completa de instalación en Windows (leer primero) |
| `2_cargar_base_de_datos.bat` | Inicializa la base de datos MySQL |
| `3_instalar_entorno.bat` | Instala el entorno Python del proyecto |
| `4_abrir_app.bat` | Abre la aplicación (uso diario) |

Para instalar en un servidor remoto Ubuntu, consulta [docs/INSTALACION_SERVIDOR.md](docs/INSTALACION_SERVIDOR.md).

---

## Qué hace el sistema

- Gestiona autenticación y sesión de usuarios con roles.
- Permite cargar archivos CSV/XLS/XLSX para procesamiento ETL.
- Ejecuta validación por capas antes de guardar.
- Persiste registros en tablas dimensionales y de hechos.
- Genera trazabilidad de cargas en auditoría ETL.

## Documentación

| Documento | Descripción |
|---|---|
| [1_INSTALACION_WINDOWS.md](1_INSTALACION_WINDOWS.md) | Instalación completa en Windows con fases detalladas |
| [docs/INSTALACION_SERVIDOR.md](docs/INSTALACION_SERVIDOR.md) | Despliegue en servidor remoto Ubuntu |
| [docs/VALIDACION.md](docs/VALIDACION.md) | Flujo de validación del proceso ETL |

## Stack tecnológico

- Backend: Flask
- ORM: Flask-SQLAlchemy / SQLAlchemy
- Autenticación: Flask-Login
- Formularios: Flask-WTF
- Procesamiento de datos: pandas / numpy
- Base de datos: MySQL (driver `pymysql`)

## Estructura del proyecto

```
ETL-Project-Manager/
├── 1_INSTALACION_WINDOWS.md          # Leer antes de instalar
├── 2_cargar_base_de_datos.bat         # Inicializa MySQL
├── 3_instalar_entorno.bat             # Instala entorno Python
├── 4_abrir_app.bat                    # Abre la aplicación
├── run.py                             # Punto de entrada
├── config.py                          # Configuración por entorno
├── requirements.txt                   # Dependencias Python
├── .env.example                       # Plantilla de variables de entorno
├── .flaskenv                          # Configuración Flask (FLASK_APP)
├── app/
│   ├── __init__.py                    # Factory de la aplicación
│   ├── models.py                      # Modelos de base de datos
│   ├── auth/                          # Autenticación (login, registro)
│   ├── config/                        # Configuración (usuarios, roles, distribuidores)
│   ├── etl/                           # Carga ETL (rutas, procesadores)
│   └── templates/                     # Plantillas HTML
├── sql/
│   ├── 01_auth_schema.sql             # Crea BD, tablas de auth y roles iniciales
│   ├── 02_business_schema.sql         # Tablas de negocio y tabla de hechos
│   ├── 03_load_geography.sql          # Departamentos y municipios (DANE)
│   └── 04_load_clients.sql            # Grupos de distribuidores y distribuidores
└── docs/
    ├── INSTALACION_SERVIDOR.md        # Guía de despliegue en Ubuntu
    └── VALIDACION.md                  # Flujo de validación ETL
```

## Variables de entorno

Copia `.env.example` como `.env` y ajusta los valores:

| Variable | Descripción |
|---|---|
| `DATABASE_URL` | Cadena de conexión MySQL: `mysql+pymysql://usuario:password@host/etl_ventas_db` |
| `SECRET_KEY` | Clave aleatoria para firmar sesiones Flask |
| `FLASK_ENV` | `development` o `production` |
| `FLASK_DEBUG` | `True` o `False` |
| `INITIAL_ADMIN_PASSWORD` | Contraseña del usuario `admin` creado al iniciar por primera vez |

## Notas operativas

- El esquema de base de datos se carga con los scripts SQL en orden — el proyecto no ejecuta migraciones automáticas.
- Al iniciar, se crea el usuario `admin` solo si la tabla de usuarios está vacía y el rol `admin` existe en la base de datos.
- Python requerido: **3.11** (compatible con 3.12; versiones superiores no garantizadas con las dependencias actuales).
- El archivo `.flaskenv` configura `FLASK_APP=run.py` y es detectado automáticamente por Flask — no requiere edición.
