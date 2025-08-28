# Dashboard Data Seeding Guide

This guide explains how to use the `seed_new_dashboard_data` management command to populate sample data for the new dashboard sections.

## Overview

The seeding command creates realistic sample data for three new dashboard sections:
- **Weekly Collections**: ZWL and USD collection amounts in millions
- **Weekly Revenue Lost**: MWh lost due to faults and maintenance
- **Debtor Categories**: Percentage breakdown by customer type

## Basic Usage

```bash
# Seed all data types with default settings (8 weeks, year 2025)
python manage.py seed_new_dashboard_data

# Clear existing data and reseed everything
python manage.py seed_new_dashboard_data --clear

# Seed data for a specific year and number of weeks
python manage.py seed_new_dashboard_data --year 2024 --weeks 12
```

## Command Options

### Data Control Options
- `--clear`: Clear existing data before seeding
- `--weeks WEEKS`: Number of weeks of data to generate (default: 8)
- `--year YEAR`: Year for the data (default: 2025)

### Selective Seeding Options
- `--locations-only`: Only create sample locations, skip data seeding
- `--collections-only`: Only seed weekly collections data
- `--revenue-lost-only`: Only seed weekly revenue lost data
- `--debtors-only`: Only seed debtor categories data

### Data Quality Options
- `--no-variations`: Skip adding realistic data variations (major faults, maintenance periods, etc.)

## Sample Data Characteristics

### Weekly Collections Data
- **National Level**: 800M - 1200M ZWL, 4M - 8M USD
- **Regional Level**: 400M - 800M ZWL, 2M - 5M USD
- **District Level**: 200M - 400M ZWL, 1M - 2.5M USD
- **Depot Level**: 50M - 150M ZWL, 0.3M - 0.8M USD

### Weekly Revenue Lost Data
- **National Level**: 150-300 MWh (faults), 100-200 MWh (maintenance)
- **Regional Level**: 80-150 MWh (faults), 40-100 MWh (maintenance)
- **District Level**: 40-80 MWh (faults), 20-50 MWh (maintenance)
- **Depot Level**: 10-30 MWh (faults), 5-20 MWh (maintenance)

### Debtor Categories
Eight customer categories with realistic percentage distributions:
- **Domestic**: ~35% (largest segment)
- **Commercial**: ~20% (second largest)
- **Industry**: ~15%
- **Government**: ~10%
- **Mining**: ~8%
- **Farming**: ~5%
- **Parastatal**: ~4%
- **Local Authority**: ~3%

Percentages are automatically normalized to sum to exactly 100% for each location.

## Location Hierarchy

The command creates sample data for multiple location levels:

### Sample Regions (Zimbabwe Provinces)
- Harare, Bulawayo, Manicaland, Mashonaland Central
- Mashonaland East, Mashonaland West, Masvingo
- Matabeleland North, Matabeleland South, Midlands

### Sample Districts
- Harare Central, Harare South
- Bulawayo Central, Bulawayo Industrial
- Mutare, Chipinge, Bindura, Shamva
- Marondera, Ruwa

### Sample Depots
- Harare Main Depot, Harare South Depot
- Bulawayo Central Depot, Bulawayo Industrial Depot
- Mutare Depot

## Realistic Data Variations

When not using `--no-variations`, the command adds realistic patterns:

### Major Events Simulation
- **Week 3**: Major fault simulation (2.5x normal fault-related revenue loss)
- **Week 6**: Maintenance shutdown (3x normal maintenance-related revenue loss)
- **Week 4**: Good collection week (1.3x normal collections)

### Seasonal Patterns (Debtor Categories)
- **Domestic**: Lower percentages in winter months
- **Commercial**: Higher percentages in summer months
- **Farming**: Peak percentages during harvest season
- **Mining**: Higher percentages in dry season
- **Others**: Stable year-round

## Examples

### Complete Fresh Setup
```bash
# Clear all data and create comprehensive sample dataset
python manage.py seed_new_dashboard_data --clear --weeks 12 --year 2025
```

### Testing Specific Features
```bash
# Test collections functionality only
python manage.py seed_new_dashboard_data --collections-only --weeks 4

# Test debtor categories with seasonal data
python manage.py seed_new_dashboard_data --debtors-only --year 2024

# Test revenue lost calculations
python manage.py seed_new_dashboard_data --revenue-lost-only --weeks 6
```

### Development Setup
```bash
# Quick setup for development (minimal data, no variations)
python manage.py seed_new_dashboard_data --weeks 4 --no-variations

# Just create locations for testing location filters
python manage.py seed_new_dashboard_data --locations-only
```

## Data Validation

The seeded data includes built-in validation:

### Weekly Collections
- All amounts are positive decimals
- Values are realistic for Zimbabwe's power sector
- Consistent scaling across location hierarchy

### Weekly Revenue Lost
- Total MWh = Faults MWh + Maintenance MWh (auto-calculated)
- All values are non-negative
- Realistic proportions between faults and maintenance

### Debtor Categories
- All percentages sum to exactly 100.00% per location
- Each category percentage is between 0.00% and 100.00%
- Realistic distribution based on Zimbabwe's customer base

## Troubleshooting

### Common Issues

1. **"Table doesn't exist" errors**
   - Run migrations first: `python manage.py migrate`

2. **"Duplicate key" errors**
   - Use `--clear` to remove existing data first

3. **Permission errors**
   - Ensure database user has INSERT/UPDATE/DELETE permissions

4. **Large dataset performance**
   - Use selective seeding options for faster execution
   - Consider using `--no-variations` for simpler data

### Verification Commands

```bash
# Check collections data
python manage.py shell -c "
from executive.general_dashboards.models import WeeklyCollections
print(f'Collections records: {WeeklyCollections.objects.count()}')
"

# Check revenue lost data
python manage.py shell -c "
from executive.general_dashboards.models import WeeklyRevenueLost
print(f'Revenue lost records: {WeeklyRevenueLost.objects.count()}')
"

# Check debtor categories
python manage.py shell -c "
from executive.general_dashboards.models import DebtorCategory
print(f'Debtor category records: {DebtorCategory.objects.count()}')
"
```

## Integration with Dashboard

After seeding, the data will be available through:
- Dashboard API endpoints (`/executive/general_dashboards/data/`)
- Location-based filtering (region, district, depot)
- Inline editing functionality
- Real-time updates and calculations

The seeded data provides a comprehensive foundation for testing all dashboard features including filtering, editing, calculations, and data visualization.