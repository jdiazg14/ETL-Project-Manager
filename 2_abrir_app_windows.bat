@echo off
setlocal
title Sistema ETL - En ejecucion

REM Ejecutar siempre desde la carpeta del proyecto
cd /d "%~dp0"

if not exist .venv\Scripts\activate (
	echo [ERROR] No se encontro el entorno virtual .venv.
	echo Ejecuta primero 1_instalar_proyecto_windows.bat
	pause
	exit /b 1
)

if not exist .env (
	echo [ERROR] No se encontro el archivo .env.
	echo Ejecuta primero 1_instalar_proyecto_windows.bat y configura el .env
	pause
	exit /b 1
)

echo Iniciando servidor local...
call .venv\Scripts\activate
if %errorlevel% neq 0 (
	echo [ERROR] No fue posible activar el entorno virtual .venv.
	pause
	exit /b 1
)

REM Opcional: abrir el navegador automaticamente
start http://127.0.0.1:5000
python run.py
pause