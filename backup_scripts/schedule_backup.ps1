# Script to schedule the backup task
$taskName = "BEII_System_Backup"
$taskDescription = "Daily backup of BEII system database and files"
$scriptPath = Join-Path $PSScriptRoot "backup.ps1"

# Create the scheduled task action
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`""

# Create the trigger (daily at 1 AM)
$trigger = New-ScheduledTaskTrigger -Daily -At 1AM

# Set the principal (run with highest privileges)
$principal = New-ScheduledTaskPrincipal -UserID "NT AUTHORITY\SYSTEM" -LogonType ServiceAccount -RunLevel Highest

# Create the task settings
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd -RestartInterval (New-TimeSpan -Minutes 1) -RestartCount 3

# Register the scheduled task
Register-ScheduledTask -TaskName $taskName `
    -Description $taskDescription `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Settings $settings `
    -Force

Write-Host "Backup task scheduled successfully!"
Write-Host "Task Name: $taskName"
Write-Host "Next Run Time: $($trigger.StartBoundary)" 