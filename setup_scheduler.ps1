# Run this script as Administrator to schedule daily news agent runs
# Right-click -> "Run with PowerShell" as Admin

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe = (Get-Command python).Source
$MainScript = Join-Path $ScriptDir "src\main.py"

# --- Task 1: Daily CLI digest at 8:00 AM (with social media) ---
$TaskName = "BilaspurNewsAgent"
$Action1 = New-ScheduledTaskAction -Execute $PythonExe -Argument "$MainScript --social" -WorkingDirectory $ScriptDir
$Trigger1 = New-ScheduledTaskTrigger -Daily -At "08:00AM"
$Settings1 = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Days 0)
$Principal1 = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

Register-ScheduledTask -TaskName $TaskName -Action $Action1 -Trigger $Trigger1 -Settings $Settings1 -Principal $Principal1 -Force

# --- Task 2: Dashboard server (starts on boot, runs continuously) ---
$DashTaskName = "BilaspurNewsDashboard"
$Action2 = New-ScheduledTaskAction -Execute $PythonExe -Argument "$MainScript dashboard" -WorkingDirectory $ScriptDir
$Trigger2 = New-ScheduledTaskTrigger -AtStartup
$Settings2 = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Days 0)

Register-ScheduledTask -TaskName $DashTaskName -Action $Action2 -Trigger $Trigger2 -Settings $Settings2 -Principal $Principal1 -Force

Write-Host "========================================"
Write-Host "  Bilaspur News Agent - Scheduler Setup"
Write-Host "========================================"
Write-Host ""
Write-Host "Task 1: '$TaskName' - runs daily at 8:00 AM (CLI digest)"
Write-Host "Task 2: '$DashTaskName' - runs continuously on system startup (Dashboard and Scraper)"
Write-Host ""
Write-Host "Python: $PythonExe"
Write-Host "Script: $MainScript"
Write-Host ""
Write-Host "To test immediately:"
Write-Host "  Start-ScheduledTask -TaskName '$TaskName'"
Write-Host "  Start-ScheduledTask -TaskName '$DashTaskName'"
Write-Host ""
Write-Host "To view: Get-ScheduledTask -TaskName '$TaskName', '$DashTaskName'"
Write-Host "To remove:"
Write-Host "  Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false"
Write-Host "  Unregister-ScheduledTask -TaskName '$DashTaskName' -Confirm:`$false"
