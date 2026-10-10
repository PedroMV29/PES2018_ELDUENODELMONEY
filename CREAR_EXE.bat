@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if errorlevel 1 (
  echo No se encontro el lanzador py de Python. Instala Python para Windows.
  pause
  exit /b 1
)
py -3 -m pip install --upgrade pyinstaller
if errorlevel 1 goto error
py -3 -m PyInstaller --noconfirm --clean --onefile --windowed --name "PES2018_ELDUEÑODELMONEY" "PES2018_ELDUEÑODELMONEY_3_4.py"
if errorlevel 1 goto error
echo.
echo EXE generado en: %~dp0dist\PES2018_ELDUEÑODELMONEY.exe
pause
exit /b 0
:error
echo Error: no se pudo generar el ejecutable.
pause
exit /b 1
