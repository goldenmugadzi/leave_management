# Django Migration Management Guide

This guide explains how to use the automated migration management tools created for the BEII v1 project to handle all Django migrations without manual intervention.

## 🎯 Problem Solved

Previously, you had to run `makemigrations` and `migrate` for each Django app individually, which was time-consuming and error-prone. Now you have automated tools that handle all migrations for all apps in one command.

## 🛠️ Available Tools

### 1. Django Management Command: `migrate_all`

**Usage:**
```bash
python manage.py migrate_all
```

**Features:**
- ✅ Creates migration folders for apps that don't have them
- ✅ Generates migrations for all apps automatically
- ✅ Applies all migrations in the correct order
- ✅ Shows migration status before and after
- ✅ Handles database connection checks
- ✅ Provides detailed output and error handling

**Options:**
```bash
# Dry run - see what would be done without actually doing it
python manage.py migrate_all --dry-run

# Force migration creation even if no changes detected
python manage.py migrate_all --force
```

### 2. Shell Script: `run_all_migrations.sh`

**Usage:**
```bash
./run_all_migrations.sh
```

**Features:**
- ✅ Same functionality as the Django command
- ✅ Can be run from any directory (checks for manage.py)
- ✅ Exits on any error (set -e)
- ✅ Creates migration folders automatically
- ✅ Shows detailed progress

### 3. Python Script: `manage_all_migrations.py`

**Usage:**
```bash
python manage_all_migrations.py
```

**Features:**
- ✅ Standalone Python script (doesn't require Django command)
- ✅ Can be imported and used programmatically
- ✅ Comprehensive error handling
- ✅ Database connection validation

## 📋 What These Tools Do

### 1. **Migration Folder Creation**
- Automatically detects apps without migration folders
- Creates `migrations/` directory for each app
- Creates `__init__.py` file in each migration folder

### 2. **Migration Generation**
- Runs `python manage.py makemigrations` for all apps
- Handles dependencies between apps automatically
- Creates initial migrations for apps with models

### 3. **Migration Application**
- Runs `python manage.py migrate` for all apps
- Applies migrations in the correct dependency order
- Handles existing database tables gracefully

### 4. **Status Reporting**
- Shows migration status before and after
- Displays which migrations were applied
- Reports any errors or issues

## 🚀 Quick Start

### For Daily Use (Recommended)
```bash
# Activate your virtual environment
source /var/www/env-beii/bin/activate

# Run the Django management command
python manage.py migrate_all
```

### For Scripts/Automation
```bash
# Use the shell script
./run_all_migrations.sh
```

### For Development/Testing
```bash
# Dry run to see what would happen
python manage.py migrate_all --dry-run
```

## 📊 Migration Status

After running any of the tools, you'll see output like this:

```
📊 Final migration status:
ACE2
 [X] 0001_initial
 [X] 0002_initial
Ace
 [X] 0001_initial
Asset_Register
 [X] 0001_initial
...
```

- `[X]` = Migration applied
- `[ ]` = Migration pending
- `(no migrations)` = App has no models or migrations

## 🔧 Troubleshooting

### Issue: "Table already exists" Error
**Solution:** Run with `--fake-initial` flag:
```bash
python manage.py migrate --fake-initial
```

### Issue: Import Error with django_prometheus
**Solution:** Temporarily comment out `django_prometheus` in `INSTALLED_APPS`:
```python
# 'django_prometheus',  # Temporarily disabled due to import error
```

### Issue: Dependency on app with no migrations
**Solution:** Create initial migration for the problematic app:
```bash
python manage.py makemigrations app_name
```

### Issue: Database Connection Failed
**Solution:** Check your database settings and ensure the database server is running.

## 📁 Files Created

The tools create the following structure for each app:
```
app_name/
├── migrations/
│   ├── __init__.py
│   ├── 0001_initial.py
│   ├── 0002_initial.py
│   └── ...
```

## 🎯 Best Practices

1. **Always use the automated tools** instead of manual migration commands
2. **Run `--dry-run` first** when making significant changes
3. **Check migration status** after running the tools
4. **Backup your database** before running migrations in production
5. **Test migrations** in a development environment first

## 🔄 Workflow

### For New Development
1. Make changes to models
2. Run `python manage.py migrate_all`
3. Review the output
4. Test your application

### For Production Deployment
1. Backup database
2. Run `python manage.py migrate_all --dry-run`
3. Review planned changes
4. Run `python manage.py migrate_all`
5. Verify application functionality

### For Adding New Apps
1. Add the app to `INSTALLED_APPS` in settings.py
2. Create models in the app
3. Run `python manage.py migrate_all`
4. The tool will automatically create migration folders and migrations

## 📈 Benefits

- **Time Saving**: No need to run migrations for each app individually
- **Error Prevention**: Automatic dependency handling
- **Consistency**: All apps are migrated together
- **Visibility**: Clear status reporting
- **Automation**: Can be integrated into CI/CD pipelines

## 🆘 Support

If you encounter issues:

1. Check the error messages in the output
2. Verify database connectivity
3. Ensure all apps are properly configured in `INSTALLED_APPS`
4. Check for any import errors in app configurations
5. Review the troubleshooting section above

---

**Note:** These tools are designed to work with the BEII v1 project structure and Django configuration. They may need adjustments for other projects. 