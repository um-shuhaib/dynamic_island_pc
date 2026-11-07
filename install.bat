@echo off
setlocal enabledelayedexpansion
title Dynamic Island - Windows Installer
echo ========================================================
echo       Dynamic Island for Windows - Quick Setup
echo ========================================================
echo.

:: 1. Check Python installation
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in your PATH.
    echo Please install Python 3.10+ from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo [1/4] Installing Python dependencies...
python -m pip install -r "%~dp0requirements.txt" --quiet
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Pip install had issues, retrying with user flag...
    python -m pip install --user -r "%~dp0requirements.txt"
)

echo [2/4] Registering shortcuts and application...
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "& {
    $AppName = 'DynamicIsland';
    $DisplayName = 'Dynamic Island Desktop';
    $InstallDir = \"$env:LOCALAPPDATA\Programs\$AppName\";
    $SourceDir = '%~dp0';
    
    if (-not (Test-Path $InstallDir)) { New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null };
    Copy-Item -Path \"$SourceDir\dynamic_island\" -Destination \"$InstallDir\dynamic_island\" -Recurse -Force;
    Copy-Item -Path \"$SourceDir\run.py\" -Destination \"$InstallDir\run.py\" -Force;
    Copy-Item -Path \"$SourceDir\requirements.txt\" -Destination \"$InstallDir\requirements.txt\" -Force;
    Copy-Item -Path \"$SourceDir\uninstall.bat\" -Destination \"$InstallDir\uninstall.bat\" -Force;

    # Python executable for launcher
    $PythonExe = (Get-Command python).Source;
    $Pythonw = Join-Path (Split-Path $PythonExe) 'pythonw.exe';
    if (-not (Test-Path $Pythonw)) { $Pythonw = $PythonExe };

    # Create launch batch in install dir
    $LaunchCmd = \"@echo off`r`nstart `\"`\" `\"$Pythonw`\" `\"$InstallDir\run.py`\" %*\";
    Set-Content -Path \"$InstallDir\DynamicIsland.bat\" -Value $LaunchCmd -Encoding ASCII;

    # Desktop shortcut
    $Wsh = New-Object -ComObject WScript.Shell;
    $Desktop = [System.Environment]::GetFolderPath('Desktop');
    $Sc = $Wsh.CreateShortcut(\"$Desktop\Dynamic Island.lnk\");
    $Sc.TargetPath = \"$InstallDir\DynamicIsland.bat\";
    $Sc.WorkingDirectory = $InstallDir;
    $Sc.WindowStyle = 7; # Minimized
    $Sc.Description = 'Dynamic Island Desktop Overlay';
    $Sc.Save();

    # Start Menu shortcuts
    $StartDir = \"$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Dynamic Island\";
    if (-not (Test-Path $StartDir)) { New-Item -ItemType Directory -Path $StartDir -Force | Out-Null };
    $Sm = $Wsh.CreateShortcut(\"$StartDir\Dynamic Island.lnk\");
    $Sm.TargetPath = \"$InstallDir\DynamicIsland.bat\";
    $Sm.WorkingDirectory = $InstallDir;
    $Sm.WindowStyle = 7;
    $Sm.Save();

    $Un = $Wsh.CreateShortcut(\"$StartDir\Uninstall Dynamic Island.lnk\");
    $Un.TargetPath = \"$InstallDir\uninstall.bat\";
    $Un.WorkingDirectory = $InstallDir;
    $Un.Save();

    # Windows Add/Remove Programs Registry Registration
    $Reg = \"HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\$AppName\";
    if (-not (Test-Path $Reg)) { New-Item -Path $Reg -Force | Out-Null };
    Set-ItemProperty -Path $Reg -Name 'DisplayName' -Value $DisplayName;
    Set-ItemProperty -Path $Reg -Name 'DisplayVersion' -Value '1.0.0';
    Set-ItemProperty -Path $Reg -Name 'Publisher' -Value 'Dynamic Island Developers';
    Set-ItemProperty -Path $Reg -Name 'InstallLocation' -Value $InstallDir;
    Set-ItemProperty -Path $Reg -Name 'UninstallString' -Value \"`\"$InstallDir\uninstall.bat`\"\";
    Set-ItemProperty -Path $Reg -Name 'NoModify' -Value 1 -Type DWord;
    Set-ItemProperty -Path $Reg -Name 'NoRepair' -Value 1 -Type DWord;
}"

echo [3/4] Setup complete!
echo [4/4] Starting Dynamic Island...
start "" pythonw run.py

echo.
echo ========================================================
echo   Dynamic Island is now installed!
echo   - Desktop and Start Menu shortcuts created.
echo   - Can be uninstalled anytime from Windows Settings.
echo ========================================================
timeout /t 3 >nul
