# Instalación Local en Windows

Este documento describe los pasos para configurar y ejecutar la aplicación **ETL Project Manager** en tu máquina Windows local Durante desarrollo.

## Prerrequisitos

- **Python 3.11 o superior**
- **MySQL 8.x** (instalado y ejecutándose)
- **Pip** (actualizado)
- **Git** (para clonar el repositorio)

## Instalación Rápida (Recomendado)

Si deseas instalar y abrir la aplicación sin usar la terminal manualmente:

### Paso 1: Ejecutar el instalador automatizado

Haz doble clic en: `1_instalar_proyecto_windows.bat`

El script realiza automáticamente:
- Creación de `.venv` (entorno virtual aislado)
- Instalación de todas las dependencias
- Creación de `.env` desde `.env.example` (si no existe)
- Creación de acceso directo en **Escritorio** llamado `ETL Project Manager`

### Paso 2: Configurar base de datos

Edita el archivo `.env` con tus valores reales:

```
DATABASE_URL=mysql+pymysql://tu_usuario:tu_password@localhost/etl_ventas_db
SECRET_KEY=tu_clave_secreta_aqui
FLASK_ENV=development
FLASK_DEBUG=True
INITIAL_ADMIN_PASSWORD=tu_password_inicial
```

### Paso 3: Abrir la aplicación

Usa el acceso directo del escritorio que se creó automáticamente, o ejecuta:

```
2_abrir_app_windows.bat
```

La aplicación se abrirá en: `http://127.0.0.1:5000`

---

## Instalación Manual Paso a Paso

Si prefieres hacer todo manualmente o necesitas mayor control:

### Paso 1: Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd ETL-Project-Manager
```

### Paso 2: Crear entorno virtual

En **PowerShell**:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

En **Command Prompt (cmd)**:

```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

### Paso 3: Instalar dependencias

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Paso 4: Preparar base de datos

#### 4a) Crear la base de datos

Abre **MySQL Workbench** o **phpMyAdmin** y ejecuta:

```sql
CREATE DATABASE etl_ventas_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

#### 4b) Crear un usuario de acceso

```sql
CREATE USER 'etl_user'@'localhost' IDENTIFIED BY 'tu_password_aqui';
GRANT ALL PRIVILEGES ON etl_ventas_db.* TO 'etl_user'@'localhost';
FLUSH PRIVILEGES;
```

#### 4c) Ejecutar scripts de esquema

Ejecuta estos comandos en orden (en PowerShell, en la carpeta del proyecto):

```powershell
# Tablas de autenticación (usuarios, roles)
mysql -u etl_user -p etl_ventas_db < sql/01_auth_schema.sql

# Tablas de negocio (ventas, dimensiones)
mysql -u etl_user -p etl_ventas_db < sql/02_business_schema.sql

# Datos geográficos
mysql -u etl_user -p etl_ventas_db < sql/03_load_geography.sql

# Datos de clientes
mysql -u etl_user -p etl_ventas_db < sql/04_load_clients.sql
```

**Nota:** Cada comando te pedirá tu contraseña de MySQL.

### Paso 5: Configurar variables de entorno

Copia el archivo de plantilla:

```powershell
Copy-Item .env.example .env
```

Edita `.env` con tus valores reales. Ejemplo:

```
DATABASE_URL=mysql+pymysql://etl_user:tu_password@localhost/etl_ventas_db
SECRET_KEY=genera_una_clave_aleatoria_segura_aqui
FLASK_ENV=development
FLASK_DEBUG=True
INITIAL_ADMIN_PASSWORD=admin123
```

**`DATABASE_URL`** es la más importante. Componentes:
- `mysql+pymysql://` → Controlador de base de datos
- `etl_user:tu_password` → Usuario y contraseña de MySQL
- `localhost` → Servidor (local en tu máquina)
- `etl_ventas_db` → Nombre de la base de datos

### Paso 6: Ejecutar la aplicación

En PowerShell (con `.venv` activado):

```bash
python run.py
```

Deberías ver:

```
* Serving Flask app
* Debug mode: on
* Running on http://127.0.0.1:5000
```

Abre tu navegador en: **http://127.0.0.1:5000**

### Paso 7: Primer acceso

- **Usuario:** `admin`
- **Contraseña:** El valor que pusiste en `INITIAL_ADMIN_PASSWORD` en el archivo `.env`

---

## Solución de Problemas

### Error: "No module named 'flask'"

**Causa:** Dependencias no instaladas o entorno no activado.

**Solución:**
```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Error: "Connection refused: 127.0.0.1:3306"

**Causa:** MySQL no está corriendo.

**Solución:**
- Abre **Services** en Windows (`services.msc`)
- Busca **MySQL80** (o la versión que tengas)
- Si está parado, haz clic derecho → **Iniciar**

### Error: "Unknown user: 'etl_user'@'localhost'"

**Causa:** El usuario MySQL no fue creado.

**Solución:** Vuelve al Paso 4b y crea el usuario nuevamente.

### Error al leer archivos CSV/Excel: "No module named 'xlrd'" o similares

**Causa:** Librerías para leer Excel no instaladas.

**Solución:**
```bash
pip install openpyxl xlrd
```

### El acceso directo del Escritorio no se creó

**Causa:** Permisos del sistema.

**Solución:** Ejecuta `2_abrir_app_windows.bat` manualmente cada vez.

---

## Próximos Pasos

- Consulta [docs/VALIDACION.md](VALIDACION.md) para entender el flujo de validación ETL
- Revisa [README.md](../README.md) para ver la arquitectura del proyecto
- Para desplegar en un servidor remoto, consulta [docs/INSTALACION_SERVIDOR.md](INSTALACION_SERVIDOR.md)
