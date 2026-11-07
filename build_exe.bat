@echo off
setlocal
cd /d "%~dp0"
echo ========================================================
echo   Building Dynamic Island Windows Standalone EXE
echo ========================================================
echo.
python -m pip install pyinstaller --quiet
pyinstaller --noconsole --name "DynamicIsland" --onedir run.py
echo.
echo Build finished! The executable is located in dist\DynamicIsland\DynamicIsland.exe
pause
