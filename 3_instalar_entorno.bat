@echo off
setlocal
title ETL Project Manager - Instalador de entorno Python

echo ==========================================================
echo   ETL Project Manager - Paso 3: Instalar entorno Python
echo   Este script es seguro de ejecutar mas de una vez.
echo   El entorno virtual y el archivo .env NO se sobreescriben
echo   si ya existen.
echo ==========================================================
echo.

REM Ejecutar siempre desde la carpeta raiz del proyecto
cd /d "%~dp0"

:: Comprobar si Python esta instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no esta instalado o no esta en el PATH.
    echo         Instala Python 3.11 y marca la opcion "Add Python to PATH".
    pause
    exit /b 1
)

REM Crear entorno virtual solo si no existe
if exist .venv (
    echo [OK] Entorno virtual .venv ya existe, reutilizando...
) else (
    echo Creando entorno virtual de Python...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] No fue posible crear el entorno virtual .venv.
        pause
        exit /b 1
    )
    echo [OK] Entorno virtual creado.
)

REM Activar entorno virtual
call .venv\Scripts\activate
if %errorlevel% neq 0 (
    echo [ERROR] No fue posible activar el entorno virtual .venv.
    pause
    exit /b 1
)

REM Instalar o verificar dependencias
echo Verificando dependencias (Pandas, Flask, SQLAlchemy, etc.)...
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [ERROR] Fallo la instalacion de dependencias.
    pause
    exit /b 1
)
echo [OK] Dependencias verificadas.

REM Crear archivo .env solo si no existe
if exist .env (
    echo [OK] Archivo .env ya existe, no sera modificado.
) else (
    copy /Y .env.example .env >nul
    echo [AVISO] Se creo el archivo .env desde .env.example.
    echo         Edita el archivo .env con tus credenciales antes de abrir la app.
)

REM Crear acceso directo en el escritorio
powershell -NoProfile -ExecutionPolicy Bypass -Command "$desktop=[Environment]::GetFolderPath('Desktop');$s=(New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $desktop 'ETL Project Manager.lnk'));$s.TargetPath='%~dp04_abrir_app.bat';$s.WorkingDirectory='%~dp0';$s.IconLocation='%SystemRoot%\System32\SHELL32.dll,220';$s.Description='Abrir ETL Project Manager';$s.Save()"
if %errorlevel% neq 0 (
    echo [AVISO] No fue posible crear el acceso directo en el escritorio.
) else (
    echo [OK] Acceso directo "ETL Project Manager" actualizado en el escritorio.
)

echo.
echo ==========================================================
echo   Listo. Proximos pasos:
echo   1. Edita el archivo .env con tus credenciales de MySQL
echo   2. Usa el icono del escritorio o 4_abrir_app.bat para abrir la app
echo ==========================================================
pause
