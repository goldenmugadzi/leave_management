# Application Documentation

This folder contains documentation organized by Django application.

## Structure

Each subfolder corresponds to a Django app in the project:

- `ACE2/` - ACE2 application
- `Asset_Register/` - Asset Register application  
- `BatteryMaintenance/` - Battery Maintenance application
- `circuit_breaker_maintenance/` - Circuit Breaker Maintenance
- `finance/` - Finance module
- `fault_locator/` - Fault Locator application
- `inspections/` - Inspections application
- `it/` - IT module
- `safety/` - Safety application
- And more...

## Documentation Types

For each app, consider creating:

- `README.md` - Overview of the application
- `models.md` - Database model documentation
- `views.md` - View and business logic documentation
- `api.md` - API endpoints documentation
- `templates.md` - Template structure documentation
- `forms.md` - Form documentation
- `admin.md` - Admin interface documentation
- `deployment.md` - App-specific deployment notes

## Naming Convention

- Use lowercase with underscores
- Include the app name prefix if needed
- Use descriptive names

## Example Structure for an App:

```
finance/
├── README.md
├── models.md
├── views.md
├── api.md
├── forms.md
└── deployment.md
``` 