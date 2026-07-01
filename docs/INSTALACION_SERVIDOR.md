# Instalación en Servidor Remoto — Guía Completa

## En qué se diferencia un servidor de una instalación local

Un servidor es un equipo que corre Linux (Ubuntu) sin interfaz gráfica, accesible a través de la red. Las diferencias clave respecto a instalar en Windows local son:

| Aspecto | Windows local | Servidor Ubuntu |
|---|---|---|
| Acceso al equipo | Directamente en el equipo | Por SSH desde otra máquina |
| Instalar MySQL | Instalador gráfico (.msi) | Comando `apt install` en terminal |
| MySQL remoto | No necesario | Requiere configuración adicional |
| Transferir archivos | No aplica | WinSCP o SCP desde tu máquina |
| Instalar Python | Instalador .exe | Comando `apt install` |
| Comandos Python | `python`, `pip` | `python3.11`, `pip` |
| Activar entorno virtual | `.venv\Scripts\activate` | `source .venv/bin/activate` |
| Ejecutar scripts SQL | `mysql -u root -p` | `sudo mysql` |
| Ejecutar la app | Doble clic en `.bat` | `nohup python run.py &` |

La ventaja del servidor es que la aplicación queda disponible para todos los usuarios de la red, y herramientas como Power BI pueden conectarse directamente a la base de datos.

---

## FASE 1 — Preparar el servidor Ubuntu

Conéctate al servidor por SSH desde tu equipo:

```bash
ssh usuario@<IP_DEL_SERVIDOR>
```

Antes de instalar cualquier software, actualiza el sistema para tener los últimos parches de seguridad:

```bash
sudo apt update && sudo apt upgrade -y
```

- `update` descarga la lista de paquetes disponibles
- `upgrade` instala las actualizaciones disponibles
- `-y` evita preguntas de confirmación

---

## FASE 2 — Instalar y configurar MySQL

En Ubuntu, MySQL no viene preinstalado — debes descargarlo con el gestor de paquetes.

### Instalar MySQL Server

```bash
sudo apt install -y mysql-server
```

Verifica que el servicio quedó activo:

```bash
sudo systemctl status mysql
```

Debes ver `active (running)`. Si no está corriendo:

```bash
sudo systemctl start mysql
sudo systemctl enable mysql
```

### Crear el usuario de la aplicación

A diferencia de Windows, en Ubuntu el usuario `root` de MySQL no tiene contraseña por defecto y solo se puede acceder con `sudo mysql`. Crea un usuario dedicado para la aplicación:

```bash
sudo mysql
```

Dentro del prompt de MySQL, ejecuta:

```sql
CREATE USER 'admin_etl'@'%' IDENTIFIED BY 'Admin_Etl_2026';
GRANT ALL PRIVILEGES ON etl_ventas_db.* TO 'admin_etl'@'%';
FLUSH PRIVILEGES;
EXIT;
```

**Qué significa cada parte:**
- `'admin_etl'@'%'` — el usuario `admin_etl` puede conectarse desde cualquier IP (`%`)
- `GRANT ALL PRIVILEGES ON etl_ventas_db.*` — tiene acceso total solo a la base de datos del proyecto
- La base de datos `etl_ventas_db` aún no existe — se crea en la Fase 4 al ejecutar los scripts SQL

> En un entorno de producción real, usa una contraseña más segura que el ejemplo y restringe el acceso por IP si es posible.

Verifica que el usuario fue creado:

```bash
mysql -u admin_etl -p
```

Cuando pida contraseña, ingresa `Admin_Etl_2026`. Si ves el prompt `mysql>`, el usuario existe. Escribe `EXIT` para salir.

### Permitir conexiones remotas a MySQL

Por defecto, MySQL en Ubuntu solo acepta conexiones locales. Para que Power BI u otras herramientas externas puedan conectarse, debes cambiar esta configuración.

**Paso 1 — Modificar la dirección de escucha de MySQL:**

```bash
sudo sed -i 's/bind-address.*=.*127\.0\.0\.1/bind-address = 0.0.0.0/' /etc/mysql/mysql.conf.d/mysqld.cnf
```

Esto cambia la dirección de escucha de `127.0.0.1` (solo local) a `0.0.0.0` (todas las interfaces).

Verifica el cambio:

```bash
grep bind-address /etc/mysql/mysql.conf.d/mysqld.cnf
```

Debes ver `bind-address = 0.0.0.0`.

**Paso 2 — Abrir el puerto en el firewall:**

```bash
sudo ufw allow 3306/tcp
sudo ufw status
```

**Paso 3 — Reiniciar MySQL para aplicar los cambios:**

```bash
sudo systemctl restart mysql
```

---

## FASE 3 — Instalar Python 3.11

La versión recomendada es **3.11**. Las dependencias del proyecto están probadas con 3.11 y 3.12. Versiones superiores pueden tener incompatibilidades.

```bash
sudo apt update
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip build-essential python3-dev
```

> El repositorio `deadsnakes/ppa` es necesario en Ubuntu 22.04+ para instalar versiones específicas de Python que no están en los repositorios oficiales por defecto.

Verifica la instalación:

```bash
python3.11 --version
```

Debes ver `Python 3.11.x`.

---

## FASE 4 — Transferir y configurar el proyecto

### Crear la carpeta en el servidor

```bash
sudo mkdir -p /var/www/ETL-Project-Manager
sudo chown -R $USER:$USER /var/www/ETL-Project-Manager
```

### Transferir los archivos desde Windows

Usa **WinSCP** (recomendado por su interfaz gráfica):

1. Abre WinSCP y crea una nueva sesión:
   - Protocolo: **SFTP**
   - Host: la IP de tu servidor (ej: `45.55.41.26`)
   - Puerto: `22`
   - Usuario y contraseña: los del servidor
2. En el panel derecho navega a `/var/www/ETL-Project-Manager/`
3. Copia todos los archivos del proyecto **excepto**:
   - `.venv/` — se creará en el servidor
   - `__pycache__/` — se regenera automáticamente
   - `.git/` — opcional, puede omitirse

Alternativamente, desde una terminal en Windows con SCP:

```powershell
scp -r C:\ruta\ETL-Project-Manager usuario@<IP>:/var/www/ETL-Project-Manager
```

### Crear el entorno virtual e instalar dependencias

En el servidor, dentro de la carpeta del proyecto:

```bash
cd /var/www/ETL-Project-Manager
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Deberías ver `(.venv)` al inicio del prompt, confirmando que el entorno está activo.

### Inicializar la base de datos

Ejecuta los cuatro scripts SQL en orden usando `sudo mysql` (que tiene privilegios de root para crear la base de datos):

```bash
cd /var/www/ETL-Project-Manager

sudo mysql < sql/01_auth_schema.sql
sudo mysql < sql/02_business_schema.sql
sudo mysql < sql/03_load_geography.sql
sudo mysql < sql/04_load_clients.sql
```

**Qué crea cada script:**

| Script | Contenido |
|---|---|
| `01_auth_schema.sql` | La base de datos `etl_ventas_db`, tablas de usuarios y roles, y los roles iniciales (`admin`, `analista`) |
| `02_business_schema.sql` | Tablas de negocio: dimensiones de geografía, tiempo y distribuidores, y la tabla de hechos de ventas |
| `03_load_geography.sql` | Departamentos y municipios de Colombia según el catálogo DANE |
| `04_load_clients.sql` | Grupos de distribuidores y distribuidores iniciales |

Verifica que el usuario `admin_etl` puede acceder a la base de datos ya creada:

```bash
mysql -u admin_etl -p etl_ventas_db
```

Si ves el prompt `mysql>`, todo está correcto. Escribe `EXIT` para salir.

### Configurar las variables de entorno

Edita el archivo `.env` en el servidor:

```bash
nano /var/www/ETL-Project-Manager/.env
```

Ajusta los valores:

```
DATABASE_URL=mysql+pymysql://admin_etl:Admin_Etl_2026@localhost/etl_ventas_db
SECRET_KEY=genera-una-clave-aleatoria-y-segura-aqui
FLASK_ENV=production
FLASK_DEBUG=False
INITIAL_ADMIN_PASSWORD=tu_password_admin_seguro
```

Para generar una `SECRET_KEY` segura:

```bash
python3.11 -c "import secrets; print(secrets.token_hex(32))"
```

Guarda con `Ctrl+O`, Enter, y cierra con `Ctrl+X`.

Protege el archivo (contiene contraseñas):

```bash
chmod 600 /var/www/ETL-Project-Manager/.env
```

---

## FASE 5 — Ejecutar la aplicación

### Opción A — En primer plano (para verificar que funciona)

```bash
cd /var/www/ETL-Project-Manager
source .venv/bin/activate
python run.py
```

Deberías ver:

```
* Serving Flask app
* Debug mode: off
* Running on http://0.0.0.0:5000
```

Abre en tu navegador: `http://<IP_DEL_SERVIDOR>:5000`

Presiona `Ctrl+C` para detener.

### Opción B — En segundo plano (uso normal en producción)

Para que la app siga corriendo aunque cierres la conexión SSH:

```bash
cd /var/www/ETL-Project-Manager
source .venv/bin/activate
nohup python run.py > out.log 2>&1 &
```

Ver los logs en tiempo real:

```bash
tail -f /var/www/ETL-Project-Manager/out.log
```

Detener la aplicación:

```bash
pkill -f run.py
```

Verificar que está corriendo:

```bash
ps aux | grep python
```

---

## Credenciales para conectar Power BI (u otras herramientas)

Una vez completados todos los pasos, usa estos datos para conectar Power BI u otras herramientas de análisis:

| Parámetro | Valor |
|---|---|
| **Servidor** | IP del servidor (ej: `45.55.41.26`) |
| **Puerto** | `3306` |
| **Base de datos** | `etl_ventas_db` |
| **Usuario** | `admin_etl` |
| **Contraseña** | La que definiste en el Paso de creación de usuario |

---

## Mantenimiento

Ver procesos Python activos:

```bash
ps aux | grep python
```

Revisar logs de la aplicación:

```bash
tail -f /var/www/ETL-Project-Manager/out.log
```

Revisar logs de MySQL:

```bash
sudo tail -f /var/log/mysql/error.log
```

Reiniciar MySQL:

```bash
sudo systemctl restart mysql
```

Revisar uso de disco y memoria:

```bash
df -h
free -h
```

---

## Solución de problemas

### "Connection refused" desde Power BI

Verifica paso a paso:

```bash
sudo ufw status                                          # Puerto 3306 abierto?
sudo systemctl status mysql                              # MySQL corriendo?
grep bind-address /etc/mysql/mysql.conf.d/mysqld.cnf    # bind-address = 0.0.0.0?
```

### "Access denied for user 'admin_etl'"

```bash
sudo mysql -e "SELECT User, Host FROM mysql.user;"    # Verificar que el usuario existe
```

Si no existe, vuelve a la sección "Crear el usuario de la aplicación" en la Fase 2.

### La aplicación se detiene inesperadamente

```bash
tail -f /var/www/ETL-Project-Manager/out.log    # Ver el error exacto
mysql -u admin_etl -p etl_ventas_db             # Verificar conexión a BD
```

### Puerto 3306 ya está en uso

```bash
sudo lsof -i :3306
sudo kill -9 <PID>
```

### "No module named 'flask'" en el servidor

El entorno virtual no está activado:

```bash
source /var/www/ETL-Project-Manager/.venv/bin/activate
pip install -r requirements.txt
```

---

## Próximos pasos recomendados

- Configurar un **reverse proxy con Nginx** para servir la app en el puerto 80/443
- Implementar **certificados SSL** (Let's Encrypt) para HTTPS
- Configurar **backups automáticos** de la base de datos con `mysqldump`
- Revisar [VALIDACION.md](VALIDACION.md) para entender el flujo ETL
