@echo off
setlocal
title Dynamic Island - Windows Uninstaller
echo ========================================================
echo       Dynamic Island for Windows - Uninstall
echo ========================================================
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "& {
    Add-Type -AssemblyName System.Windows.Forms;
    $res = [System.Windows.Forms.MessageBox]::Show(
        'Are you sure you want to completely uninstall Dynamic Island Desktop?',
        'Confirm Uninstall',
        [System.Windows.Forms.MessageBoxButtons]::YesNo,
        [System.Windows.Forms.MessageBoxIcon]::Question
    );
    
    if ($res -ne [System.Windows.Forms.DialogResult]::Yes) { exit 0 };

    Write-Host 'Closing running instances...' -ForegroundColor Yellow;
    Stop-Process -Name 'DynamicIsland' -Force -ErrorAction SilentlyContinue;
    Get-Process | Where-Object { $_.CommandLine -like '*run.py*' } | Stop-Process -Force -ErrorAction SilentlyContinue;
    Start-Sleep -Milliseconds 600;

    Write-Host 'Removing shortcuts...' -ForegroundColor Yellow;
    $Desktop = [System.Environment]::GetFolderPath('Desktop');
    Remove-Item -Path \"$Desktop\Dynamic Island.lnk\" -Force -ErrorAction SilentlyContinue;

    $StartMenu = \"$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Dynamic Island\";
    Remove-Item -Path $StartMenu -Recurse -Force -ErrorAction SilentlyContinue;

    Write-Host 'Removing registry entries...' -ForegroundColor Yellow;
    Remove-Item -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\DynamicIsland' -Recurse -Force -ErrorAction SilentlyContinue;
    Remove-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -Name 'DynamicIsland' -ErrorAction SilentlyContinue;

    Write-Host 'Cleaning files...' -ForegroundColor Yellow;
    $InstallDir = \"$env:LOCALAPPDATA\Programs\DynamicIsland\";
    if (Test-Path $InstallDir) {
        Start-Process -FilePath 'cmd.exe' -ArgumentList \"/c timeout /t 1 /nobreak >nul & rmdir /s /q `\"$InstallDir`\"\" -WindowStyle Hidden;
    }

    [System.Windows.Forms.MessageBox]::Show(
        'Dynamic Island has been successfully uninstalled from your PC.',
        'Uninstallation Complete',
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Information
    );
}"
