# Instalación en Windows — Guía Completa

## Qué necesitas y cómo se relaciona todo

El sistema tiene tres componentes que deben funcionar juntos:

- **MySQL** es el motor de base de datos donde se guardan todos los datos: ventas, usuarios, configuración. Debe estar instalado y corriendo en tu equipo antes que cualquier otra cosa. Sin MySQL, la aplicación no puede arrancar.
- **Python** es el lenguaje en que está escrita la aplicación. El instalador crea un entorno aislado (`.venv`) con todas las librerías necesarias, de forma que no interfieren con otros programas de tu equipo.
- **El proyecto** son los archivos de código, plantillas y scripts SQL. Se conecta a MySQL usando las credenciales que configures en el archivo `.env`.

**El orden importa:** primero MySQL, luego Python, luego el proyecto.

Los archivos numerados en esta carpeta siguen ese orden:

| Archivo | Cuándo usarlo |
|---|---|
| `1_INSTALACION_WINDOWS.md` | Este documento — leer antes de empezar |
| `2_cargar_base_de_datos.bat` | Una sola vez, para crear tablas y cargar datos iniciales |
| `3_instalar_entorno.bat` | Una sola vez, después de instalar MySQL y Python |
| `4_abrir_app.bat` | Cada vez que quieras usar la aplicación |

---

## FASE 1 — Instalar MySQL

MySQL es el sistema que almacena todos los datos de la aplicación. Se instala una sola vez en el equipo y queda corriendo como servicio de Windows en segundo plano.

### Descarga

1. Ve a **https://dev.mysql.com/downloads/installer/**
2. Descarga **MySQL Installer for Windows** — el archivo más grande (mysql-installer-community-x.x.x.msi)
3. No es necesario crear cuenta — hay un enlace "No thanks, just start my download"

### Instalación paso a paso

1. Ejecuta el instalador descargado
2. En **"Choosing a Setup Type"** elige una opción:
   - **"Server only"** — instala solo el motor de base de datos (suficiente para este proyecto)
   - **"Developer Default"** — instala también MySQL Workbench, una interfaz gráfica para administrar la base de datos (recomendado si es tu primera vez)
3. Haz clic en **"Execute"** y espera a que descargue e instale los componentes
4. Continúa hasta **"Type and Networking"**:
   - Config Type: **Development Computer**
   - Port: **3306** (dejar por defecto — es el puerto estándar de MySQL)
5. En **"Authentication Method"**: deja la opción recomendada
6. En **"Accounts and Roles"**: define la contraseña para el usuario **`root`**
   - `root` es el administrador de MySQL
   - **Anota esta contraseña** — la necesitarás para inicializar la base de datos del proyecto
7. En **"Windows Service"**:
   - Deja marcado **"Configure MySQL Server as a Windows Service"**
   - Nombre del servicio: **MySQL80** (o el que aparezca)
   - Marca **"Start the MySQL Server at System Startup"** para que inicie automáticamente con Windows
8. Haz clic en **"Execute"** para aplicar la configuración y finaliza el instalador

> **Reinicia el equipo antes de continuar.** MySQL agrega su carpeta al PATH del sistema durante la instalación, pero las terminales y aplicaciones abiertas no detectan ese cambio hasta reiniciar. Sin reiniciar, los scripts de instalación del proyecto pueden fallar aunque MySQL esté correctamente instalado.

### Verificar que MySQL está funcionando

Abre **PowerShell** y ejecuta:

```powershell
mysql --version
```

Si ves algo como `mysql  Ver 8.0.xx Distrib 8.0.xx, for Win64`, MySQL está correctamente instalado.

Si el comando no se reconoce, significa que MySQL no está en el PATH. Agrégalo manualmente:
1. Abre el menú Inicio y busca **"Variables de entorno"**
2. Haz clic en **"Editar las variables de entorno del sistema"**
3. Haz clic en **"Variables de entorno..."**
4. En **"Variables del sistema"**, selecciona `Path` y haz clic en **"Editar"**
5. Haz clic en **"Nuevo"** y agrega: `C:\Program Files\MySQL\MySQL Server 8.0\bin`
6. Acepta todo y reinicia PowerShell

Para verificar que el servicio de MySQL está activo:
- Presiona `Win + R`, escribe `services.msc` y presiona Enter
- Busca **MySQL80** en la lista — el estado debe decir **"En ejecución"**
- Si está detenido, haz clic derecho → **Iniciar**

---

## FASE 2 — Instalar Python 3.11

Python es el entorno de ejecución de la aplicación. Se recomienda la versión **3.11** — las dependencias del proyecto están probadas con 3.11 y 3.12. Versiones más nuevas (3.13+) pueden tener incompatibilidades con algunas librerías.

### Descarga

1. Ve a **https://www.python.org/downloads/**
2. Busca la sección de versiones anteriores o usa el buscador de la página para encontrar **Python 3.11.x** (cualquier versión 3.11.x sirve, por ejemplo 3.11.9)
3. Descarga **"Windows installer (64-bit)"** para la versión 3.11.x que encuentres

> Si la página te ofrece descargar el **Python install manager** en lugar de un instalador directo, también puedes usarlo — dentro del install manager selecciona **Python 3.11.x** para instalar.

### Instalación paso a paso

1. Ejecuta el instalador descargado
2. **Antes de hacer clic en cualquier otra cosa**, marca la casilla **"Add Python 3.11 to PATH"** en la pantalla inicial — sin esto, el comando `python` no funcionará desde la terminal
3. Haz clic en **"Install Now"**
4. Espera a que termine y cierra el instalador

### Verificar la instalación

Abre una **nueva** ventana de PowerShell (importante — una ya abierta no detectará el PATH actualizado) y ejecuta:

```powershell
python --version
```

Debes ver `Python 3.11.x`. Si aparece un error o una versión diferente, cierra y vuelve a abrir PowerShell y reintenta.

---

## FASE 3 — Configurar el proyecto

Esta fase se realiza **una sola vez** por equipo. Después de completarla, solo necesitas el paso de la Fase 4 para el uso diario.

### Paso 1 — Obtener los archivos del proyecto

**Opción A — Clonar con Git:**

```powershell
git clone <url-del-repositorio>
cd ETL-Project-Manager
```

**Opción B — Copiar la carpeta:**

Si ya tienes la carpeta del proyecto, asegúrate de que esté en una ruta sin espacios ni caracteres especiales. Por ejemplo: `C:\Proyectos\ETL-Project-Manager`.

### Paso 2 — Inicializar la base de datos

Haz doble clic en el archivo `2_cargar_base_de_datos.bat` que está en esta carpeta.

El script pedirá tu usuario y contraseña de MySQL (usa `root` con la contraseña que definiste en la Fase 1) y ejecutará los cuatro scripts SQL en orden:

| Script | Qué crea |
|---|---|
| `01_auth_schema.sql` | La base de datos `etl_ventas_db`, tablas de usuarios y roles, y los roles iniciales (`admin`, `analista`) |
| `02_business_schema.sql` | Tablas de negocio: dimensiones de geografía, tiempo y distribuidores, y la tabla de hechos de ventas con sus restricciones |
| `03_load_geography.sql` | Departamentos y municipios de Colombia según el catálogo DANE |
| `04_load_clients.sql` | Grupos de distribuidores y distribuidores iniciales |

> El script es seguro de ejecutar más de una vez. Los scripts SQL usan `IF NOT EXISTS` para tablas e `INSERT IGNORE` para datos, por lo que no duplican información existente.

### Paso 3 — Instalar el entorno Python

Haz doble clic en el archivo `3_instalar_entorno.bat` que está en esta carpeta.

**Qué hace el script:**
- Verifica que Python esté instalado
- Crea el entorno virtual `.venv` con todas las librerías necesarias (Flask, pandas, SQLAlchemy, etc.)
- Crea el archivo `.env` desde la plantilla si no existe aún
- Crea un acceso directo **ETL Project Manager** en el Escritorio

> El script es seguro de ejecutar más de una vez. Si `.venv` y `.env` ya existen, no los sobreescribe — solo verifica que las dependencias estén al día.

### Paso 4 — Configurar el archivo .env

El script `2_cargar_base_de_datos.bat` ya creó el archivo `.env` y configuró automáticamente `DATABASE_URL` con el usuario `etl_user` que se creó durante la carga.

Solo debes completar dos variables manualmente. Abre `.env` con cualquier editor de texto:

```
DATABASE_URL=mysql+pymysql://etl_user:...  ← ya configurado automáticamente
SECRET_KEY=reemplaza_con_una_clave_segura  ← debes completar
FLASK_ENV=development
FLASK_DEBUG=True
INITIAL_ADMIN_PASSWORD=tu_password_admin   ← debes completar
```

**`SECRET_KEY`** — clave aleatoria para proteger las sesiones de usuario. Genera una con:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

**`INITIAL_ADMIN_PASSWORD`** — contraseña con la que podrás entrar a la aplicación por primera vez con el usuario `admin`.

> El archivo `.env` contiene contraseñas — no lo compartas ni lo subas a repositorios públicos. Está incluido en `.gitignore` para protegerlo.

---

## FASE 4 — Uso diario

Una vez completada la Fase 3, para abrir la aplicación usa el acceso directo **ETL Project Manager** en el Escritorio, o haz doble clic en:

```
4_abrir_app.bat
```

La aplicación abre automáticamente el navegador en: **http://127.0.0.1:5000**

**Credenciales iniciales:**
- Usuario: `admin`
- Contraseña: el valor que definiste en `INITIAL_ADMIN_PASSWORD` dentro de `.env`

> El usuario `admin` se crea automáticamente al iniciar por primera vez, solo si la tabla de usuarios está vacía y el rol `admin` existe en la base de datos (lo crea `01_auth_schema.sql`).

---

## Solución de problemas

### "No se reconoce 'python' como comando"
Python no está en el PATH. Reinstálalo marcando la casilla **"Add Python 3.11 to PATH"** en el instalador.

### "No se reconoce 'mysql' como comando"
MySQL no está en el PATH. Agrega `C:\Program Files\MySQL\MySQL Server 8.0\bin` a la variable de entorno `Path` (ver Fase 1).

### "No module named 'flask'"
El entorno virtual no está activado o las dependencias no se instalaron. Ejecuta `2_instalar_entorno.bat` nuevamente.

### "Connection refused: 127.0.0.1:3306"
MySQL no está corriendo. Abre `services.msc`, busca **MySQL80** y haz clic en **Iniciar**.

### "Unknown database 'etl_ventas_db'"
Los scripts SQL no se han ejecutado. Corre `3_cargar_base_de_datos.bat`.

### "Access denied for user 'root'@'localhost'"
La contraseña en `DATABASE_URL` dentro de `.env` no coincide con la contraseña de MySQL. Corrígela.

### Error al leer Excel: "No module named 'xlrd'"

```powershell
.\.venv\Scripts\Activate.ps1
pip install openpyxl xlrd
```

### PowerShell bloquea la ejecución de scripts (.ps1)

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

---

## Próximos pasos

- Para entender el flujo de validación ETL: [docs/VALIDACION.md](docs/VALIDACION.md)
- Para desplegar en un servidor remoto Ubuntu: [docs/INSTALACION_SERVIDOR.md](docs/INSTALACION_SERVIDOR.md)
