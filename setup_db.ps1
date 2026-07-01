# setup_db.ps1 — Inicialización de base de datos ETL Project Manager
# Este script es invocado por 2_cargar_base_de_datos.bat

Set-Location $PSScriptRoot

function Log($msg) {
    Write-Host $msg
    Add-Content "install_log.txt" $msg
}

Set-Content "install_log.txt" "Inicio: $(Get-Date)"
Write-Host ""
Write-Host "=========================================================="
Write-Host "  ETL Project Manager - Carga de Base de Datos"
Write-Host "  Crea las tablas, carga los datos iniciales y configura"
Write-Host "  automaticamente el usuario y la conexion en .env"
Write-Host "  Es seguro ejecutarlo mas de una vez (no duplica datos)."
Write-Host "=========================================================="
Write-Host ""

# Verificar scripts SQL
if (-not (Test-Path "sql\01_auth_schema.sql")) {
    Log "[ERROR] No se encontro la carpeta sql\ con los scripts."
    Log "Asegurate de ejecutar este archivo desde la raiz del proyecto."
    exit 1
}

# Verificar mysql en PATH
if (-not (Get-Command "mysql" -ErrorAction SilentlyContinue)) {
    Log "[ERROR] No se encontro el comando 'mysql' en el PATH."
    Log "Ruta habitual: C:\Program Files\MySQL\MySQL Server 8.0\bin"
    Log "Reinicia el equipo e intenta de nuevo."
    exit 1
}

# Leer credenciales
Write-Host "Ingresa tus credenciales de administrador MySQL (usuario root)."
Write-Host ""
$mysqlUser = Read-Host "Usuario MySQL [root]"
if ([string]::IsNullOrWhiteSpace($mysqlUser)) { $mysqlUser = "root" }

$securePass = Read-Host "Contrasena MySQL" -AsSecureString
$mysqlPass = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePass)
)
Write-Host ""

# Crear archivo de configuracion MySQL temporal (evita pasar contrasena por linea de comandos)
$cnfPath = "etl_tmp.cnf"
"[client]`ndefault-character-set=utf8mb4`nuser=$mysqlUser`npassword=$mysqlPass" | Set-Content $cnfPath -Encoding ascii
Log "[cnf] Archivo de credenciales temporal creado"

# Verificar conexion
$testOut = & mysql "--defaults-extra-file=$cnfPath" -e "SELECT 1;" 2>&1
if ($LASTEXITCODE -ne 0 -or ("$testOut" -match "ERROR")) {
    Log "[ERROR] No fue posible conectarse a MySQL:"
    Log "$testOut"
    Log "Verifica la contrasena y que el servicio MySQL80 este corriendo (services.msc)"
    Remove-Item $cnfPath -Force -ErrorAction SilentlyContinue
    exit 1
}
Log "[OK] Conexion a MySQL verificada"
Write-Host ""

# Verificar si la BD ya existe
$dbCheck = & mysql "--defaults-extra-file=$cnfPath" -e "SHOW DATABASES LIKE 'etl_ventas_db';" 2>&1
if ("$dbCheck" -match "etl_ventas_db") {
    Write-Host "[AVISO] La base de datos 'etl_ventas_db' ya existe."
    Write-Host "Los scripts son seguros: usan IF NOT EXISTS e INSERT IGNORE."
    Write-Host ""
    $confirm = Read-Host "Continuar de todas formas? (s/n)"
    if ($confirm -ne "s") {
        Write-Host "Operacion cancelada."
        Remove-Item $cnfPath -Force -ErrorAction SilentlyContinue
        exit 0
    }
    Write-Host ""
}

# Ejecutar scripts SQL
$scripts = @(
    @{ file = "sql\01_auth_schema.sql";    desc = "Base de datos y tablas de autenticacion" },
    @{ file = "sql\02_business_schema.sql"; desc = "Tablas de negocio" },
    @{ file = "sql\03_load_geography.sql";  desc = "Datos geograficos (departamentos y municipios)" },
    @{ file = "sql\04_load_clients.sql";    desc = "Datos de clientes (distribuidores)" }
)

Write-Host "Ejecutando scripts SQL..."
Write-Host ""

for ($i = 0; $i -lt $scripts.Count; $i++) {
    $s = $scripts[$i]
    Write-Host "[$($i+1)/4] $($s.desc)..."
    $out = cmd /c "mysql `"--defaults-extra-file=$cnfPath`" < `"$($s.file)`" 2>&1"
    Add-Content "install_log.txt" $out
    if ($LASTEXITCODE -ne 0) {
        Log ""
        Log "[ERROR] Fallo $($s.file)"
        Log "Detalle en install_log.txt"
        Remove-Item $cnfPath -Force -ErrorAction SilentlyContinue
        exit 1
    }
    Log "[OK] $($s.file) completado"
}
Write-Host ""

# Crear usuario dedicado para la aplicacion
Write-Host "Creando usuario dedicado para la aplicacion..."
$chars = (65..90) + (97..122) + (48..57)
$appPass = -join ($chars | Get-Random -Count 16 | ForEach-Object { [char]$_ })

$createSql = "CREATE USER IF NOT EXISTS 'etl_user'@'localhost' IDENTIFIED BY '$appPass'; GRANT ALL PRIVILEGES ON etl_ventas_db.* TO 'etl_user'@'localhost'; FLUSH PRIVILEGES;"
& mysql "--defaults-extra-file=$cnfPath" -e $createSql 2>&1 | Out-Null

if ($LASTEXITCODE -eq 0) {
    Log "[OK] Usuario 'etl_user' creado con acceso a etl_ventas_db"
    $dbUser = "etl_user"
    $dbPass = $appPass
} else {
    Write-Host "[AVISO] No fue posible crear 'etl_user'. Se usara el usuario administrador."
    $dbUser = $mysqlUser
    $dbPass = $mysqlPass
}

# Eliminar archivo de credenciales temporal
Remove-Item $cnfPath -Force -ErrorAction SilentlyContinue

# Configurar .env
Write-Host ""
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Log "[OK] Archivo .env creado desde plantilla"
    }
}

if (Test-Path ".env") {
    $dbUrl = "DATABASE_URL=mysql+pymysql://${dbUser}:${dbPass}@localhost/etl_ventas_db?charset=utf8mb4"
    (Get-Content ".env") -replace "^DATABASE_URL=.*", $dbUrl | Set-Content ".env" -Encoding ascii
    Log "[OK] DATABASE_URL configurado en .env automaticamente"
} else {
    Write-Host "[AVISO] No se encontro .env.example. Configura DATABASE_URL manualmente."
}

Write-Host ""
Write-Host "=========================================================="
Write-Host "  Listo. Base de datos y conexion configuradas."
Write-Host ""
Write-Host "  Aun debes editar el archivo .env para definir:"
Write-Host "    - SECRET_KEY              (clave de seguridad)"
Write-Host "    - INITIAL_ADMIN_PASSWORD  (contrasena del usuario admin)"
Write-Host ""
Write-Host "  Siguiente paso: ejecuta 3_instalar_entorno.bat"
Write-Host "=========================================================="
Write-Host ""
