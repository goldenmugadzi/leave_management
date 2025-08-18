# Backup Script for BEII System
# Configuration
$CONFIG = @{
    BackupRoot = "C:\Backups\BEII"  # Change this to your desired backup location
    DatabaseName = "your_database_name"  # Update with your database name
    DatabaseUser = "your_database_user"  # Update with your database user
    DatabasePassword = "your_database_password"  # Update with your database password
    DatabaseHost = "localhost"  # Update with your database host
    RetentionDays = 7  # Number of days to keep backups
    MySQLPath = "C:\Program Files\MySQL\MySQL Server 8.0\bin"  # Update with your MySQL installation path
}

# Create timestamp for backup folder
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupPath = Join-Path $CONFIG.BackupRoot $timestamp

# Ensure backup directories exist
New-Item -ItemType Directory -Force -Path $backupPath | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $backupPath "database") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $backupPath "files") | Out-Null

# Function to log messages
function Write-Log {
    param($Message)
    $logMessage = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss'): $Message"
    Write-Output $logMessage
    Add-Content -Path (Join-Path $CONFIG.BackupRoot "backup.log") -Value $logMessage
}

# Database Backup
function Backup-Database {
    try {
        $dumpFile = Join-Path $backupPath "database\database_backup.sql"
        $mysqldumpPath = Join-Path $CONFIG.MySQLPath "mysqldump.exe"
        
        # Create database backup
        & $mysqldumpPath --single-transaction `
            --routines `
            --triggers `
            --events `
            --set-gtid-purged=OFF `
            -h $CONFIG.DatabaseHost `
            -u $CONFIG.DatabaseUser `
            -p"$($CONFIG.DatabasePassword)" `
            $CONFIG.DatabaseName > $dumpFile

        if ($LASTEXITCODE -eq 0) {
            Write-Log "Database backup completed successfully"
            # Compress the SQL file
            Compress-Archive -Path $dumpFile -DestinationPath "$dumpFile.zip"
            Remove-Item $dumpFile
            return $true
        } else {
            Write-Log "Database backup failed with exit code $LASTEXITCODE"
            return $false
        }
    }
    catch {
        Write-Log "Error during database backup: $_"
        return $false
    }
}

# File System Backup
function Backup-FileSystem {
    try {
        $projectRoot = $PSScriptRoot | Split-Path -Parent
        $excludeDirs = @(
            'node_modules',
            'staticfiles',
            '.git',
            'backup_scripts'
        )

        # Create a temporary file list
        $tempFile = Join-Path $env:TEMP "backup_file_list.txt"
        Get-ChildItem -Path $projectRoot -Recurse |
            Where-Object { 
                $item = $_
                -not ($excludeDirs | Where-Object { $item.FullName -like "*\$_*" })
            } |
            Select-Object -ExpandProperty FullName > $tempFile

        # Create ZIP archive
        $zipFile = Join-Path $backupPath "files\files_backup.zip"
        Compress-Archive -Path (Get-Content $tempFile) -DestinationPath $zipFile -Force

        Remove-Item $tempFile
        Write-Log "File system backup completed successfully"
        return $true
    }
    catch {
        Write-Log "Error during file system backup: $_"
        return $false
    }
}

# Cleanup old backups
function Remove-OldBackups {
    try {
        $cutoffDate = (Get-Date).AddDays(-$CONFIG.RetentionDays)
        Get-ChildItem -Path $CONFIG.BackupRoot -Directory |
            Where-Object { $_.CreationTime -lt $cutoffDate } |
            ForEach-Object {
                Remove-Item $_.FullName -Recurse -Force
                Write-Log "Removed old backup: $($_.Name)"
            }
    }
    catch {
        Write-Log "Error during cleanup: $_"
    }
}

# Main backup process
Write-Log "Starting backup process"

# Perform database backup
$dbSuccess = Backup-Database
if (-not $dbSuccess) {
    Write-Log "Database backup failed, stopping backup process"
    exit 1
}

# Perform file system backup
$filesSuccess = Backup-FileSystem
if (-not $filesSuccess) {
    Write-Log "File system backup failed"
    exit 1
}

# Cleanup old backups
Remove-OldBackups

Write-Log "Backup process completed successfully" 