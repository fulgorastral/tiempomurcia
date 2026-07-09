@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo  Actualizando datos AEMET (Murcia y Caravaca)
echo ============================================
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 descargar_aemet_murcia.py %*
) else (
  python descargar_aemet_murcia.py %*
)
if errorlevel 1 (
  echo.
  echo Ha habido un error. Revisa el mensaje de arriba.
  pause
  exit /b 1
)
start "" "Murcia_app_explorador.html"
pause
