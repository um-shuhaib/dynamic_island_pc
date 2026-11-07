# Dynamic Island Windows Installer
$ErrorActionPreference = "Stop"

$AppName = "DynamicIsland"
$DisplayName = "Dynamic Island Desktop"
$Version = "1.0.0"
$Publisher = "Dynamic Island Developers"

$InstallDir = "$env:LOCALAPPDATA\Programs\$AppName"

# Locate source DynamicIsland directory
$SourceDir = "$PSScriptRoot\DynamicIsland"
if (-not (Test-Path $SourceDir)) {
    $SourceDir = "$PSScriptRoot\..\..\dist\DynamicIsland"
}

if (-not (Test-Path "$SourceDir\DynamicIsland.exe")) {
    Write-Error "Cannot find DynamicIsland.exe in $SourceDir"
    exit 1
}

Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "  Installing Dynamic Island Desktop..." -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan

# 1. Terminate any running instances
Write-Host "[1/5] Stopping any running instances..." -ForegroundColor Yellow
Stop-Process -Name "DynamicIsland" -Force -ErrorAction SilentlyContinue

# 2. Copy files to %LOCALAPPDATA%\Programs\DynamicIsland
Write-Host "[2/5] Copying application files to $InstallDir..." -ForegroundColor Yellow
if (-not (Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
}
Copy-Item -Path "$SourceDir\*" -Destination $InstallDir -Recurse -Force

# 3. Create uninstaller script in InstallDir
Write-Host "[3/5] Setting up uninstaller..." -ForegroundColor Yellow
$UninstallBatContent = "@echo off`r`npowershell.exe -NoProfile -ExecutionPolicy Bypass -File `"%~dp0Uninstall.ps1`""
Set-Content -Path "$InstallDir\Uninstall.bat" -Value $UninstallBatContent -Encoding ASCII

$UninstallPs1Content = @'
Add-Type -AssemblyName System.Windows.Forms
$AppName = "DynamicIsland"
$InstallDir = $PSScriptRoot

$result = [System.Windows.Forms.MessageBox]::Show(
    "Are you sure you want to completely uninstall Dynamic Island Desktop?",
    "Confirm Uninstall",
    [System.Windows.Forms.MessageBoxButtons]::YesNo,
    [System.Windows.Forms.MessageBoxIcon]::Question
)

if ($result -ne [System.Windows.Forms.DialogResult]::Yes) {
    exit 0
}

# 1. Kill running instances
Stop-Process -Name "DynamicIsland" -Force -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 800

# 2. Remove desktop shortcut
$Desktop = [System.Environment]::GetFolderPath("Desktop")
if (Test-Path "$Desktop\Dynamic Island.lnk") {
    Remove-Item -Path "$Desktop\Dynamic Island.lnk" -Force -ErrorAction SilentlyContinue
}

# 3. Remove Start Menu folder
$StartMenu = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Dynamic Island"
if (Test-Path $StartMenu) {
    Remove-Item -Path $StartMenu -Recurse -Force -ErrorAction SilentlyContinue
}

# 4. Remove Registry entries
Remove-Item -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\$AppName" -Recurse -Force -ErrorAction SilentlyContinue
Remove-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" -Name $AppName -ErrorAction SilentlyContinue

# 5. Remove config if user desires
$ConfigDir = "$env:APPDATA\dynamic_island"
if (Test-Path $ConfigDir) {
    Remove-Item -Path $ConfigDir -Recurse -Force -ErrorAction SilentlyContinue
}

# 6. Delete install dir using delayed cmd process
Start-Process -FilePath "cmd.exe" -ArgumentList "/c timeout /t 2 /nobreak >nul & rmdir /s /q `"$InstallDir`"" -WindowStyle Hidden

[System.Windows.Forms.MessageBox]::Show(
    "Dynamic Island has been successfully uninstalled from your PC.",
    "Dynamic Island Uninstaller",
    [System.Windows.Forms.MessageBoxButtons]::OK,
    [System.Windows.Forms.MessageBoxIcon]::Information
)
'@
Set-Content -Path "$InstallDir\Uninstall.ps1" -Value $UninstallPs1Content -Encoding UTF8

# 4. Create Desktop & Start Menu Shortcuts
Write-Host "[4/5] Creating shortcuts..." -ForegroundColor Yellow
$WshShell = New-Object -ComObject WScript.Shell

# Desktop shortcut
$DesktopPath = [System.Environment]::GetFolderPath("Desktop")
$DesktopShortcut = $WshShell.CreateShortcut("$DesktopPath\Dynamic Island.lnk")
$DesktopShortcut.TargetPath = "$InstallDir\DynamicIsland.exe"
$DesktopShortcut.WorkingDirectory = "$InstallDir"
$DesktopShortcut.Description = "Dynamic Island Desktop Overlay"
$DesktopShortcut.Save()

# Start Menu shortcuts
$StartMenuDir = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Dynamic Island"
if (-not (Test-Path $StartMenuDir)) {
    New-Item -ItemType Directory -Path $StartMenuDir -Force | Out-Null
}
$StartShortcut = $WshShell.CreateShortcut("$StartMenuDir\Dynamic Island.lnk")
$StartShortcut.TargetPath = "$InstallDir\DynamicIsland.exe"
$StartShortcut.WorkingDirectory = "$InstallDir"
$StartShortcut.Save()

$UninstShortcut = $WshShell.CreateShortcut("$StartMenuDir\Uninstall Dynamic Island.lnk")
$UninstShortcut.TargetPath = "$InstallDir\Uninstall.bat"
$UninstShortcut.WorkingDirectory = "$InstallDir"
$UninstShortcut.Save()

# 5. Register in Windows Settings / Add or Remove Programs
Write-Host "[5/5] Registering in Windows Add or Remove Programs..." -ForegroundColor Yellow
$RegPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\$AppName"
if (-not (Test-Path $RegPath)) {
    New-Item -Path $RegPath -Force | Out-Null
}
Set-ItemProperty -Path $RegPath -Name "DisplayName" -Value $DisplayName
Set-ItemProperty -Path $RegPath -Name "DisplayVersion" -Value $Version
Set-ItemProperty -Path $RegPath -Name "Publisher" -Value $Publisher
Set-ItemProperty -Path $RegPath -Name "DisplayIcon" -Value "$InstallDir\DynamicIsland.exe"
Set-ItemProperty -Path $RegPath -Name "InstallLocation" -Value $InstallDir
Set-ItemProperty -Path $RegPath -Name "UninstallString" -Value "`"$InstallDir\Uninstall.bat`""
Set-ItemProperty -Path $RegPath -Name "NoModify" -Value 1 -Type DWord
Set-ItemProperty -Path $RegPath -Name "NoRepair" -Value 1 -Type DWord
Set-ItemProperty -Path $RegPath -Name "EstimatedSize" -Value 95000 -Type DWord

Write-Host "==============================================" -ForegroundColor Green
Write-Host "  Installation Successful!" -ForegroundColor Green
Write-Host "  Starting Dynamic Island now..." -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Green

Start-Process -FilePath "$InstallDir\DynamicIsland.exe" -WorkingDirectory "$InstallDir"
