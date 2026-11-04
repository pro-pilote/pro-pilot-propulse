@echo off
setlocal
set "DIR=%~dp0"
set "VENV_PY=%DIR%.venv\Scripts\python.exe"

if exist "%VENV_PY%" goto :run

echo [Pro-Tools] Initialisation automatique de Python 3.12 portable et des dependances dans .venv... >&2
if not exist "%DIR%.uv\uv.exe" (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$env:UV_INSTALL_DIR='%DIR%.uv'; $env:INSTALLER_NO_MODIFY_PATH='1'; irm https://astral.sh/uv/install.ps1 | iex" >nul
)
"%DIR%.uv\uv.exe" venv --python 3.12 "%DIR%.venv" --quiet
"%DIR%.uv\uv.exe" pip install --python "%VENV_PY%" --quiet -r "%DIR%requirements.txt"

:run
"%VENV_PY%" "%DIR%ppl.py" %*
