@echo off
setlocal
set "DIR=%~dp0"

set "PY_BIN=python"
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    set "PY_BIN=py -3"
)

if exist "%DIR%bootstrap.py" (
    if not defined PPL_WORKSPACE set "PPL_WORKSPACE=%DIR:~0,-1%"
)

if not exist "%DIR%.pro-pilot" if exist "%DIR%bootstrap.py" (
    echo [Pro-Pilot] Premier lancement detecte : synchronisation du socle...
    %PY_BIN% "%DIR%bootstrap.py"
)

set "PPL_SCRIPT=%DIR%.pro-pilot\tools\ppl.py"
if not exist "%PPL_SCRIPT%" (
    if exist "%DIR%ppl.py" (
        set "PPL_SCRIPT=%DIR%ppl.py"
    ) else if exist "%DIR%tools\ppl.py" (
        set "PPL_SCRIPT=%DIR%tools\ppl.py"
    ) else (
        echo [Pro-Pilot] Erreur : %PPL_SCRIPT% introuvable. Executez : %PY_BIN% bootstrap.py >&2
        exit /b 1
    )
)

%PY_BIN% "%PPL_SCRIPT%" %*
