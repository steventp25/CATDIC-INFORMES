@echo off
setlocal
cd /d "%~dp0BACKEND"

rem Busca Python 3.14: primero el lanzador "py"; si no existe, la instalacion de Python en la carpeta del usuario.
set "PY_CMD="
where py >nul 2>nul && set "PY_CMD=py -3.14"
if not defined PY_CMD if exist "%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe" set "PY_CMD="%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe""
if not defined PY_CMD (
  echo No se encontro Python 3.14. Instalelo o avise al responsable del programa.
  pause
  exit /b 1
)

echo Abriendo CATDIC Informes en http://localhost:8000  (deje esta ventana abierta)
%PY_CMD% -m uvicorn main:app --host 127.0.0.1 --port 8000
if errorlevel 1 pause
