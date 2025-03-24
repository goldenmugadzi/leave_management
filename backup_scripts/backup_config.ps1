# Backup Configuration
$CONFIG = @{
    BackupRoot = "C:\Backups\BEII"  # Change this to your desired backup location
    DatabaseName = "beii_db"  # Your database name
    DatabaseUser = "root"  # Your database user
    DatabasePassword = ""  # Your database password
    DatabaseHost = "localhost"  # Your database host
    RetentionDays = 7  # Number of days to keep backups
    MySQLPath = "C:\Program Files\MySQL\MySQL Server 8.0\bin"  # Update with your MySQL installation path
} 