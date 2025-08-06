#!/bin/bash

# Django Migration Management Script
# This script automates the entire migration process for all Django apps

set -e  # Exit on any error

echo "🚀 Django Migration Management Script"
echo "=================================================="

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo "❌ Error: manage.py not found. Please run this script from the Django project root."
    exit 1
fi

# Function to create migration folders for apps that don't have them
create_migration_folders() {
    echo "🔍 Checking for missing migration folders..."
    
    # Find all Python files that might be Django apps
    find . -name "models.py" -type f | while read -r model_file; do
        app_dir=$(dirname "$model_file")
        migrations_dir="$app_dir/migrations"
        
        if [ ! -d "$migrations_dir" ]; then
            echo "📁 Creating migration folder for $(basename "$app_dir")"
            mkdir -p "$migrations_dir"
            
            # Create __init__.py if it doesn't exist
            if [ ! -f "$migrations_dir/__init__.py" ]; then
                touch "$migrations_dir/__init__.py"
                echo "   ✅ Created __init__.py for $(basename "$app_dir")"
            fi
        fi
    done
}

# Function to show migration status
show_migration_status() {
    echo "📊 Current Migration Status:"
    python manage.py showmigrations
}

# Main execution
echo "🔌 Checking database connection..."
python manage.py check --database default

echo "📋 Creating migration folders for missing apps..."
create_migration_folders

echo "📊 Initial migration status:"
show_migration_status

echo ""
echo "🔄 Running makemigrations for all apps..."
if python manage.py makemigrations; then
    echo "✅ makemigrations completed successfully"
else
    echo "❌ makemigrations failed"
    exit 1
fi

echo ""
echo "🚀 Running migrate for all apps..."
if python manage.py migrate; then
    echo "✅ migrate completed successfully"
else
    echo "❌ migrate failed"
    exit 1
fi

echo ""
echo "📊 Final migration status:"
show_migration_status

echo ""
echo "🎉 Migration process completed successfully!"
echo "All apps have been migrated and are up to date." 