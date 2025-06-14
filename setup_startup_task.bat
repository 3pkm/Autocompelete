@echo off
REM

echo Creating startup task for KeywordAutomator...

REM
powershell -command "exit ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)"
if %errorlevel% neq 0 (
    echo This script needs to be run as Administrator to create a scheduled task.
    echo Please right-click this script and select "Run as Administrator".
    pause
    exit /b 1
)

REM
set "APP_DIR=%~dp0"
set "APP_DIR=%APP_DIR:~0,-1%"

REM
powershell -Command "& {
    $scriptPath = Join-Path -Path '%APP_DIR%' -ChildPath 'start_hidden.pyw'
    $pythonwPath = Join-Path -Path (Split-Path -Path (Get-Command python).Source) -ChildPath 'pythonw.exe'
    
    # Delete existing task if it exists
    Unregister-ScheduledTask -TaskName 'KeywordAutomator' -Confirm:$false -ErrorAction SilentlyContinue
    
    # Create a new task
    $action = New-ScheduledTaskAction -Execute $pythonwPath -Argument \"$scriptPath --minimized\"
    $trigger = New-ScheduledTaskTrigger -AtLogon
    $principal = New-ScheduledTaskPrincipal -UserId (Get-CimInstance -ClassName Win32_ComputerSystem | Select-Object -ExpandProperty UserName) -LogonType Interactive -RunLevel Highest
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 0) -Hidden
    
    Register-ScheduledTask -TaskName 'KeywordAutomator' -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description 'Start KeywordAutomator at logon'
}"

if %errorlevel% equ 0 (
    echo Startup task created successfully!
    echo KeywordAutomator will now start automatically when you log in.
) else (
    echo Failed to create startup task. Error code: %errorlevel%
)

pause
