# Instalación en Servidor Remoto (Ubuntu Linux)

Este documento describe los pasos para desplegar **ETL Project Manager** en un servidor remoto Ubuntu 24.04 LTS, permitiendo que la aplicación sea accesible de forma remota y que herramientas como Power BI se conecten a la base de datos.

## Visión General

El proceso prepara tu servidor para:
1. Ejecutar la aplicación Python 3.12 de ETL
2. Almacenar datos en MySQL con acceso remoto
3. Permitir conexiones externas desde aplicaciones como Power BI

## Paso 1: Actualizar el Sistema

Antes de instalar cualquier software, asegurate de que Ubuntu tenga los últimos parches de seguridad:

```bash
sudo apt update && sudo apt upgrade -y
```

**Qué hace:**
- `update` descarga la lista de software disponible
- `upgrade` instala las actualizaciones de seguridad
- `-y` evita preguntas de confirmación

---

## Paso 2: Instalar MySQL Server

Descarga e instala el motor de base de datos:

```bash
sudo apt install -y mysql-server
```

Verifica que MySQL esté funcionando:

```bash
sudo systemctl status mysql
```

Deberías ver: `active (running)`

---

## Paso 3: Abrir Firewall para MySQL

Por seguridad, los servidores vienen con todas las "puertas" cerradas. Para permitir conexiones externas a MySQL:

```bash
sudo ufw allow 3306/tcp
```

Permite tráfico hacia el puerto 3306 (puerto de MySQL).

---

## Paso 4: Crear Base de Datos y Usuario Admin

Accede a MySQL como root:

```bash
sudo mysql
```

Ejecuta estos comandos uno por uno dentro de MySQL:

```sql
CREATE DATABASE etl_ventas_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER 'admin_etl'@'%' IDENTIFIED BY 'Admin_Etl_2026';

GRANT ALL PRIVILEGES ON etl_ventas_db.* TO 'admin_etl'@'%';

FLUSH PRIVILEGES;

EXIT;
```

**Notas importantes:**
- `'%'` permite conexiones desde cualquier IP (incluyendo tu máquina local para Power BI)
- La contraseña debe ser segura en producción
- Las comillas simples son obligatorias en SQL

Verifica que el usuario fue creado correctamente:

```bash
mysql -u admin_etl -p
```

Cuando te pida contraseña, digita `Admin_Etl_2026` y presiona Enter.

---

## Paso 5: Permitir Conexiones Externas en MySQL

Por defecto, MySQL solo escucha peticiones locales. Necesitamos cambiar su configuración para escuchar desde cualquier IP:

```bash
sudo sed -i 's/127.0.0.1/0.0.0.0/' /etc/mysql/mysql.conf.d/mysqld.cnf
```

Reinicia MySQL para aplicar el cambio:

```bash
sudo systemctl restart mysql
```

**Qué hace:** Cambia la dirección de escucha de `127.0.0.1` (solo local) a `0.0.0.0` (todos).

---

## Paso 6: Subir el Proyecto al Servidor

### 6a) Preparar carpeta en el servidor

En tu servidor, crea la carpeta donde vivirá el proyecto:

```bash
sudo mkdir -p /var/www/ETL-Project-Manager
sudo chown -R $USER:$USER /var/www/ETL-Project-Manager
cd /var/www/ETL-Project-Manager
```

### 6b) Transferir archivos

Usa **WinSCP** (Windows) o **SCP** (Terminal):

**Con WinSCP:**
1. Nueva sesión con protocolo **SFTP**
2. Host: Dirección IP de tu servidor (ej: `45.55.41.26`)
3. Puerto: `22`
4. Usuario: `root` o el usuario que configuraste
5. Contraseña: La contraseña del servidor

En el panel derecho, navega a `/var/www/ETL-Project-Manager/`

**⚠️ NO copiar:**
- `.venv/` → Se instalará en el servidor
- `__pycache__/` → Se regenerará automáticamente
- `.git/` → Opcional, puede omitirse

Arrastra toda tu carpeta del proyecto (código, SQL, .env, requirements.txt, etc.) al servidor.

---

## Paso 7: Configurar Python 3 en el Servidor

### 7a) Instalar dependencias del sistema

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip build-essential python3-dev
```

Estas herramientas son necesarias para compilar algunas librerías de Python.

### 7b) Crear entorno virtual

En tu servidor, dentro de `/var/www/ETL-Project-Manager/`:

```bash
cd /var/www/ETL-Project-Manager
python3 -m venv .venv
```

### 7c) Activar el entorno virtual

```bash
source .venv/bin/activate
```

Deberias ver `(.venv)` al inicio del prompt del terminal, confirmando que está activo.

### 7d) Instalar dependencias del proyecto

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Paso 8: Configurar Variables de Entorno

Edita el archivo `.env` en el servidor:

```bash
nano .env
```

Debe contener (reemplaza con tus valores reales):

```
DATABASE_URL=mysql+pymysql://admin_etl:Admin_Etl_2026@localhost/etl_ventas_db
SECRET_KEY=genera-una-clave-aleatoria-y-segura-aqui
FLASK_ENV=production
FLASK_DEBUG=False
INITIAL_ADMIN_PASSWORD=tu_password_admin_muy_seguro
```

**Componentes de DATABASE_URL:**
- `mysql+pymysql://` → Controlador Python para MySQL
- `admin_etl:Admin_Etl_2026` → Usuario y contraseña de MySQL
- `localhost` → Servidor (mismo servidor físico)
- `etl_ventas_db` → Nombre de la base de datos

**Seguridad:** Presiona `Ctrl+O` para guardar, `Enter`, y `Ctrl+X` para salir de nano.

Asegurate que solo el dueño pueda leer `.env` (contiene contraseña):

```bash
chmod 600 .env
```

---

## Paso 9: Cargar Scripts SQL

Desde la carpeta del proyecto, ejecuta los scripts en orden:

```bash
cd /var/www/ETL-Project-Manager/sql
```

Crear tablas de autenticación (usuario, roles):

```bash
mysql -u admin_etl -p etl_ventas_db < 01_auth_schema.sql
```

Crear tablas de negocio (ventas, dimensiones):

```bash
mysql -u admin_etl -p etl_ventas_db < 02_business_schema.sql
```

Cargar datos geográficos:

```bash
mysql -u admin_etl -p etl_ventas_db < 03_load_geography.sql
```

Cargar datos de clientes:

```bash
mysql -u admin_etl -p etl_ventas_db < 04_load_clients.sql
```

Cada comando te pedirá la contraseña: `Admin_Etl_2026`

---

## Paso 10: Ejecutar la Aplicación

Desde `/var/www/ETL-Project-Manager/`:

### Opción A: Ejecución en Primer Plano (para pruebas)

```bash
source .venv/bin/activate
python run.py
```

Deberías ver:

```
* Serving Flask app 'run'
* Debug mode: off
* Running on http://0.0.0.0:5000
```

Presiona `Ctrl+C` para detener.

### Opción B: Ejecución en Segundo Plano (Producción)

Para que la app siga ejecutándose aunque cierres la conexión SSH:

```bash
nohup python run.py > out.log 2>&1 &
```

**Ver logs en tiempo real:**

```bash
tail -f out.log
```

### Detener la Aplicación

```bash
pkill -f run.py
```

---

## Paso 11: Verificar Conectividad

### Desde tu máquina local (Windows/Mac)

Abre PowerShell y prueba la conexión a MySQL:

```powershell
mysql -h <IP_DEL_SERVIDOR> -u admin_etl -p -D etl_ventas_db
```

Sustituye `<IP_DEL_SERVIDOR>` con la IP de tu server (ej: `45.55.41.26`).

Si logras conectar, verás el prompt `mysql>`. Digita `EXIT` para salir.

### Probar la Aplicación Web

Abre tu navegador en:

```
http://<IP_DEL_SERVIDOR>:5000
```

Deberías ver la pantalla de login.

---

## Credenciales de Conexión para Power BI (o similar)

Una vez completados todos los pasos, usa estos datos en Power BI:

| Parámetro | Valor |
|-----------|-------|
| **Servidor** | `<IP_DEL_SERVIDOR>` (ej: 45.55.41.26) |
| **Puerto** | `3306` |
| **Base de datos** | `etl_ventas_db` |
| **Usuario** | `admin_etl` |
| **Contraseña** | `Admin_Etl_2026` |

---

## Mantenimiento

### Ver procesos del servidor

```bash
ps aux | grep python
```

### Revisar uso de disco

```bash
df -h
```

### Revisar uso de memoria

```bash
free -h
```

### Reiniciar MySQL

```bash
sudo systemctl restart mysql
```

### Ver logs de MySQL

```bash
sudo tail -f /var/log/mysql/error.log
```

---

## Solución de Problemas

### Error: "Connection refused" desde Power BI

- Verifica que el firewall abrió el puerto 3306: `sudo ufw status`
- Verifica que MySQL se reinició: `sudo systemctl restart mysql`
- Verifica la configuración de `mysqld.cnf`: `grep bind-address /etc/mysql/mysql.conf.d/mysqld.cnf`

### Error: "Access denied for user 'admin_etl'"

- Verifica la contraseña en `.env`
- Verifica que el usuario fue creado: `sudo mysql -e "SELECT User, Host FROM mysql.user;"`

### La aplicación se detiene inesperadamente

- Revisa los logs: `tail -f out.log`
- Verifica conectividad a base de datos con: `mysql -u admin_etl -p`

### Puerto 3306 ya está en uso

```bash
sudo lsof -i :3306
sudo kill -9 <PID>
```

---

## Próximos Pasos

- Configurar un **reverse proxy** (Nginx/Apache) para mayor seguridad
- Implementar **certificados SSL** para HTTPS
- Configurar **backups automáticos** de la base de datos
- Revisar [docs/VALIDACION.md](VALIDACION.md) para entender el flujo ETL
