@echo off
setlocal
title Instalador ETL - Configurando entorno...
echo Cargando, por favor espera...

REM Ejecutar siempre desde la carpeta del proyecto
cd /d "%~dp0"

:: Comprobar si Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no esta instalado. Por favor instala Python 3.x y vuelve a intentarlo.
    pause
    exit /b 1
)

REM Crear entorno virtual si no existe
if not exist .venv (
    echo Creando entorno virtual de Python...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] No fue posible crear el entorno virtual .venv.
        pause
        exit /b 1
    )
)

REM Instalar dependencias
echo Instalando librerias necesarias (Pandas, Flask, SQLAlchemy, etc.)...
call .venv\Scripts\activate
if %errorlevel% neq 0 (
    echo [ERROR] No fue posible activar el entorno virtual .venv.
    pause
    exit /b 1
)

pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Fallo la instalacion de dependencias.
    pause
    exit /b 1
)

REM Crear archivo .env si no existe
if not exist .env (
    copy /Y .env.example .env >nul
    echo [AVISO] Se creo el archivo .env desde .env.example. Debes revisar sus valores.
)

REM Crear acceso directo en el escritorio para abrir la app
powershell -NoProfile -ExecutionPolicy Bypass -Command "$desktop=[Environment]::GetFolderPath('Desktop');$s=(New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $desktop 'ETL Project Manager.lnk'));$s.TargetPath='%~dp0%2_abrir_app_windows.bat';$s.WorkingDirectory='%~dp0';$s.IconLocation='%SystemRoot%\System32\SHELL32.dll,220';$s.Description='Abrir ETL Project Manager';$s.Save()"
if %errorlevel% neq 0 (
    echo [AVISO] No fue posible crear el acceso directo automatico en el escritorio.
) else (
    echo [OK] Se creo el acceso directo "ETL Project Manager" en el escritorio.
)

echo.
echo [OK] Entorno configurado correctamente.
echo Ahora puedes usar el icono del escritorio para abrir el programa.
pause