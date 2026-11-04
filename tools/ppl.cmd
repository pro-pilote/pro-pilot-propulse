@echo off
setlocal
set "DIR=%~dp0"

if not exist "%DIR%.pro-pilot" if exist "%DIR%bootstrap.py" (
    echo [Pro-Pilot] Premier lancement detecte : synchronisation du socle...
    python "%DIR%bootstrap.py"
)

set "PPL_SCRIPT=%DIR%.pro-pilot\tools\ppl.py"
if not exist "%PPL_SCRIPT%" (
    if exist "%DIR%ppl.py" (
        set "PPL_SCRIPT=%DIR%ppl.py"
    ) else if exist "%DIR%tools\ppl.py" (
        set "PPL_SCRIPT=%DIR%tools\ppl.py"
    ) else (
        echo [Pro-Pilot] Erreur : %PPL_SCRIPT% introuvable. Executez : python bootstrap.py >&2
        exit /b 1
    )
)

python "%PPL_SCRIPT%" %*
