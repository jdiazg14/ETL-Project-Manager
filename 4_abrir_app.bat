@echo off
setlocal
title ETL Project Manager - En ejecucion

REM Ejecutar siempre desde la carpeta raiz del proyecto
cd /d "%~dp0"

if not exist .venv\Scripts\activate (
	echo [ERROR] No se encontro el entorno virtual .venv.
	echo Ejecuta primero 3_instalar_entorno.bat
	pause
	exit /b 1
)

if not exist .env (
	echo [ERROR] No se encontro el archivo .env.
	echo Ejecuta primero 3_instalar_entorno.bat y edita el archivo .env
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