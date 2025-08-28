"""
Unit tests for dashboard enhancement models.

This module contains comprehensive test cases for the new dashboard models:
- WeeklyCollections: Tests for weekly collections data in ZWL and USD
- WeeklyRevenueLost: Tests for revenue lost due to faults and maintenance
- DebtorCategory: Tests for debtor category percentages and validation

To run these tests:
    python manage.py test executive.general_dashboards.tests

To run specific test classes:
    python manage.py test executive.general_dashboards.tests.WeeklyCollectionsModelTest
    python manage.py test executive.general_dashboards.tests.WeeklyRevenueLostModelTest
    python manage.py test executive.general_dashboards.tests.DebtorCategoryModelTest

Requirements covered:
- Model validation and constraints (Requirement 7.6)
- Automatic calculations (Requirements 2.3, 2.4, 3.4, 3.6)
- Location-based filtering (Requirements 6.1, 6.2, 6.3)
- Audit trail functionality (Requirements 4.8, 5.5, 7.5)
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from decimal import Decimal
from datetime import datetime

from .models import WeeklyCollections, WeeklyRevenueLost, DebtorCategory
from it.users.models import UserProfile, Regions, Districts, Depots


class WeeklyCollectionsModelTest(TestCase):
    """Test cases for WeeklyCollections model"""
    
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = UserProfile.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test location data
        self.region = Regions.objects.create(region='Test Region', code='TR')
        self.district = Districts.objects.create(
            district='Test District', 
            code='TD', 
            region_id='1'
        )
        self.depot = Depots.objects.create(
            depot='Test Depot',
            code='TDP',
            district=self.district,
            region=self.region
        )
    
    def test_create_weekly_collections_valid_data(self):
        """Test creating WeeklyCollections with valid data"""
        collection = WeeklyCollections.objects.create(
            week='Week 1',
            zwl_millions=Decimal('5.25'),
            usd_millions=Decimal('2.75'),
            region=self.region,
            year=2025,
            week_number=1,
            updated_by=self.user
        )
        
        self.assertEqual(collection.week, 'Week 1')
        self.assertEqual(collection.zwl_millions, Decimal('5.25'))
        self.assertEqual(collection.usd_millions, Decimal('2.75'))
        self.assertEqual(collection.region, self.region)
        self.assertEqual(collection.year, 2025)
        self.assertEqual(collection.week_number, 1)
        self.assertEqual(collection.updated_by, self.user)
        self.assertIsNotNone(collection.created_at)
        self.assertIsNotNone(collection.updated_at)
    
    def test_weekly_collections_string_representation(self):
        """Test string representation of WeeklyCollections"""
        collection = WeeklyCollections.objects.create(
            week='Week 2',
            zwl_millions=Decimal('10.50'),
            usd_millions=Decimal('5.25'),
            region=self.region,
            year=2025,
            week_number=2
        )
        
        expected_str = f"Week 2 - {self.region} (ZWL: 10.50M, USD: 5.25M)"
        self.assertEqual(str(collection), expected_str)
    
    def test_weekly_collections_string_representation_global(self):
        """Test string representation without location (Global)"""
        collection = WeeklyCollections.objects.create(
            week='Week 3',
            zwl_millions=Decimal('15.75'),
            usd_millions=Decimal('7.80'),
            year=2025,
            week_number=3
        )
        
        expected_str = "Week 3 - Global (ZWL: 15.75M, USD: 7.80M)"
        self.assertEqual(str(collection), expected_str)
    
    def test_weekly_collections_negative_values_validation(self):
        """Test that negative values are not allowed"""
        with self.assertRaises(ValidationError):
            collection = WeeklyCollections(
                week='Week 4',
                zwl_millions=Decimal('-5.25'),
                usd_millions=Decimal('2.75'),
                year=2025,
                week_number=4
            )
            collection.full_clean()
    
    def test_weekly_collections_week_number_validation(self):
        """Test week number validation (1-53)"""
        # Test invalid week number (0)
        with self.assertRaises(ValidationError):
            collection = WeeklyCollections(
                week='Week 0',
                zwl_millions=Decimal('5.25'),
                usd_millions=Decimal('2.75'),
                year=2025,
                week_number=0
            )
            collection.full_clean()
        
        # Test invalid week number (54)
        with self.assertRaises(ValidationError):
            collection = WeeklyCollections(
                week='Week 54',
                zwl_millions=Decimal('5.25'),
                usd_millions=Decimal('2.75'),
                year=2025,
                week_number=54
            )
            collection.full_clean()
    
    def test_weekly_collections_unique_constraint(self):
        """Test unique constraint on week_number, year, and location"""
        # Create first collection
        WeeklyCollections.objects.create(
            week='Week 5',
            zwl_millions=Decimal('5.25'),
            usd_millions=Decimal('2.75'),
            region=self.region,
            year=2025,
            week_number=5
        )
        
        # Try to create duplicate - should raise IntegrityError
        with self.assertRaises(IntegrityError):
            WeeklyCollections.objects.create(
                week='Week 5',
                zwl_millions=Decimal('10.50'),
                usd_millions=Decimal('5.50'),
                region=self.region,
                year=2025,
                week_number=5
            )
    
    def test_weekly_collections_location_filtering(self):
        """Test location-based filtering functionality"""
        # Create collections for different locations
        region_collection = WeeklyCollections.objects.create(
            week='Week 6',
            zwl_millions=Decimal('5.25'),
            usd_millions=Decimal('2.75'),
            region=self.region,
            year=2025,
            week_number=6
        )
        
        district_collection = WeeklyCollections.objects.create(
            week='Week 6',
            zwl_millions=Decimal('3.50'),
            usd_millions=Decimal('1.75'),
            district=self.district,
            year=2025,
            week_number=6
        )
        
        depot_collection = WeeklyCollections.objects.create(
            week='Week 6',
            zwl_millions=Decimal('2.25'),
            usd_millions=Decimal('1.25'),
            depot=self.depot,
            year=2025,
            week_number=6
        )
        
        # Test filtering by region
        region_collections = WeeklyCollections.objects.filter(region=self.region)
        self.assertEqual(region_collections.count(), 1)
        self.assertEqual(region_collections.first(), region_collection)
        
        # Test filtering by district
        district_collections = WeeklyCollections.objects.filter(district=self.district)
        self.assertEqual(district_collections.count(), 1)
        self.assertEqual(district_collections.first(), district_collection)
        
        # Test filtering by depot
        depot_collections = WeeklyCollections.objects.filter(depot=self.depot)
        self.assertEqual(depot_collections.count(), 1)
        self.assertEqual(depot_collections.first(), depot_collection)
    
    def test_weekly_collections_audit_trail(self):
        """Test audit trail functionality"""
        collection = WeeklyCollections.objects.create(
            week='Week 7',
            zwl_millions=Decimal('5.25'),
            usd_millions=Decimal('2.75'),
            year=2025,
            week_number=7,
            updated_by=self.user
        )
        
        # Check initial audit fields
        self.assertEqual(collection.updated_by, self.user)
        self.assertIsNotNone(collection.created_at)
        self.assertIsNotNone(collection.updated_at)
        
        # Update the collection
        original_updated_at = collection.updated_at
        collection.zwl_millions = Decimal('10.50')
        collection.save()
        
        # Check that updated_at changed
        self.assertGreater(collection.updated_at, original_updated_at)


class WeeklyRevenueLostModelTest(TestCase):
    """Test cases for WeeklyRevenueLost model"""
    
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = UserProfile.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        
        # Create test location data
        self.region = Regions.objects.create(region='Test Region 2', code='TR2')
        self.district = Districts.objects.create(
            district='Test District 2', 
            code='TD2', 
            region_id='2'
        )
        self.depot = Depots.objects.create(
            depot='Test Depot 2',
            code='TDP2',
            district=self.district,
            region=self.region
        )
    
    def test_create_weekly_revenue_lost_valid_data(self):
        """Test creating WeeklyRevenueLost with valid data"""
        revenue_lost = WeeklyRevenueLost.objects.create(
            week='Week 1',
            faults_mwh=Decimal('15.50'),
            maintenance_mwh=Decimal('8.25'),
            region=self.region,
            year=2025,
            week_number=1,
            updated_by=self.user
        )
        
        self.assertEqual(revenue_lost.week, 'Week 1')
        self.assertEqual(revenue_lost.faults_mwh, Decimal('15.50'))
        self.assertEqual(revenue_lost.maintenance_mwh, Decimal('8.25'))
        self.assertEqual(revenue_lost.total_mwh, Decimal('23.75'))  # Auto-calculated
        self.assertEqual(revenue_lost.region, self.region)
        self.assertEqual(revenue_lost.year, 2025)
        self.assertEqual(revenue_lost.week_number, 1)
        self.assertEqual(revenue_lost.updated_by, self.user)
    
    def test_weekly_revenue_lost_auto_calculation(self):
        """Test automatic calculation of total MWh"""
        revenue_lost = WeeklyRevenueLost.objects.create(
            week='Week 2',
            faults_mwh=Decimal('20.75'),
            maintenance_mwh=Decimal('12.50'),
            year=2025,
            week_number=2
        )
        
        # Total should be automatically calculated
        expected_total = Decimal('20.75') + Decimal('12.50')
        self.assertEqual(revenue_lost.total_mwh, expected_total)
    
    def test_weekly_revenue_lost_auto_calculation_on_update(self):
        """Test automatic recalculation when values are updated"""
        revenue_lost = WeeklyRevenueLost.objects.create(
            week='Week 3',
            faults_mwh=Decimal('10.00'),
            maintenance_mwh=Decimal('5.00'),
            year=2025,
            week_number=3
        )
        
        # Initial total
        self.assertEqual(revenue_lost.total_mwh, Decimal('15.00'))
        
        # Update values
        revenue_lost.faults_mwh = Decimal('25.00')
        revenue_lost.maintenance_mwh = Decimal('15.00')
        revenue_lost.save()
        
        # Total should be recalculated
        self.assertEqual(revenue_lost.total_mwh, Decimal('40.00'))
    
    def test_weekly_revenue_lost_string_representation(self):
        """Test string representation of WeeklyRevenueLost"""
        revenue_lost = WeeklyRevenueLost.objects.create(
            week='Week 4',
            faults_mwh=Decimal('18.25'),
            maintenance_mwh=Decimal('9.75'),
            region=self.region,
            year=2025,
            week_number=4
        )
        
        expected_str = f"Week 4 - {self.region} (Total: 28.00 MWh)"
        self.assertEqual(str(revenue_lost), expected_str)
    
    def test_weekly_revenue_lost_string_representation_global(self):
        """Test string representation without location (Global)"""
        revenue_lost = WeeklyRevenueLost.objects.create(
            week='Week 5',
            faults_mwh=Decimal('22.50'),
            maintenance_mwh=Decimal('11.25'),
            year=2025,
            week_number=5
        )
        
        expected_str = "Week 5 - Global (Total: 33.75 MWh)"
        self.assertEqual(str(revenue_lost), expected_str)
    
    def test_weekly_revenue_lost_negative_values_validation(self):
        """Test that negative values are not allowed"""
        with self.assertRaises(ValidationError):
            revenue_lost = WeeklyRevenueLost(
                week='Week 6',
                faults_mwh=Decimal('-15.50'),
                maintenance_mwh=Decimal('8.25'),
                year=2025,
                week_number=6
            )
            revenue_lost.full_clean()
        
        with self.assertRaises(ValidationError):
            revenue_lost = WeeklyRevenueLost(
                week='Week 7',
                faults_mwh=Decimal('15.50'),
                maintenance_mwh=Decimal('-8.25'),
                year=2025,
                week_number=7
            )
            revenue_lost.full_clean()
    
    def test_weekly_revenue_lost_week_number_validation(self):
        """Test week number validation (1-53)"""
        # Test invalid week number (0)
        with self.assertRaises(ValidationError):
            revenue_lost = WeeklyRevenueLost(
                week='Week 0',
                faults_mwh=Decimal('15.50'),
                maintenance_mwh=Decimal('8.25'),
                year=2025,
                week_number=0
            )
            revenue_lost.full_clean()
        
        # Test invalid week number (54)
        with self.assertRaises(ValidationError):
            revenue_lost = WeeklyRevenueLost(
                week='Week 54',
                faults_mwh=Decimal('15.50'),
                maintenance_mwh=Decimal('8.25'),
                year=2025,
                week_number=54
            )
            revenue_lost.full_clean()
    
    def test_weekly_revenue_lost_unique_constraint(self):
        """Test unique constraint on week_number, year, and location"""
        # Create first revenue lost record
        WeeklyRevenueLost.objects.create(
            week='Week 8',
            faults_mwh=Decimal('15.50'),
            maintenance_mwh=Decimal('8.25'),
            region=self.region,
            year=2025,
            week_number=8
        )
        
        # Try to create duplicate - should raise IntegrityError
        with self.assertRaises(IntegrityError):
            WeeklyRevenueLost.objects.create(
                week='Week 8',
                faults_mwh=Decimal('20.00'),
                maintenance_mwh=Decimal('10.00'),
                region=self.region,
                year=2025,
                week_number=8
            )
    
    def test_weekly_revenue_lost_location_filtering(self):
        """Test location-based filtering functionality"""
        # Create revenue lost records for different locations
        region_revenue_lost = WeeklyRevenueLost.objects.create(
            week='Week 9',
            faults_mwh=Decimal('15.50'),
            maintenance_mwh=Decimal('8.25'),
            region=self.region,
            year=2025,
            week_number=9
        )
        
        district_revenue_lost = WeeklyRevenueLost.objects.create(
            week='Week 9',
            faults_mwh=Decimal('12.00'),
            maintenance_mwh=Decimal('6.50'),
            district=self.district,
            year=2025,
            week_number=9
        )
        
        depot_revenue_lost = WeeklyRevenueLost.objects.create(
            week='Week 9',
            faults_mwh=Decimal('8.75'),
            maintenance_mwh=Decimal('4.25'),
            depot=self.depot,
            year=2025,
            week_number=9
        )
        
        # Test filtering by region
        region_records = WeeklyRevenueLost.objects.filter(region=self.region)
        self.assertEqual(region_records.count(), 1)
        self.assertEqual(region_records.first(), region_revenue_lost)
        
        # Test filtering by district
        district_records = WeeklyRevenueLost.objects.filter(district=self.district)
        self.assertEqual(district_records.count(), 1)
        self.assertEqual(district_records.first(), district_revenue_lost)
        
        # Test filtering by depot
        depot_records = WeeklyRevenueLost.objects.filter(depot=self.depot)
        self.assertEqual(depot_records.count(), 1)
        self.assertEqual(depot_records.first(), depot_revenue_lost)
    
    def test_weekly_revenue_lost_audit_trail(self):
        """Test audit trail functionality"""
        revenue_lost = WeeklyRevenueLost.objects.create(
            week='Week 10',
            faults_mwh=Decimal('15.50'),
            maintenance_mwh=Decimal('8.25'),
            year=2025,
            week_number=10,
            updated_by=self.user
        )
        
        # Check initial audit fields
        self.assertEqual(revenue_lost.updated_by, self.user)
        self.assertIsNotNone(revenue_lost.created_at)
        self.assertIsNotNone(revenue_lost.updated_at)
        
        # Update the record
        original_updated_at = revenue_lost.updated_at
        revenue_lost.faults_mwh = Decimal('20.00')
        revenue_lost.save()
        
        # Check that updated_at changed and total was recalculated
        self.assertGreater(revenue_lost.updated_at, original_updated_at)
        self.assertEqual(revenue_lost.total_mwh, Decimal('28.25'))  # 20.00 + 8.25


class DebtorCategoryModelTest(TestCase):
    """Test cases for DebtorCategory model"""
    
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = UserProfile.objects.create_user(
            username='testuser3',
            email='test3@example.com',
            password='testpass123'
        )
        
        # Create test location data
        self.region = Regions.objects.create(region='Test Region 3', code='TR3')
        self.district = Districts.objects.create(
            district='Test District 3', 
            code='TD3', 
            region_id='3'
        )
        self.depot = Depots.objects.create(
            depot='Test Depot 3',
            code='TDP3',
            district=self.district,
            region=self.region
        )
    
    def test_create_debtor_category_valid_data(self):
        """Test creating DebtorCategory with valid data"""
        debtor_category = DebtorCategory.objects.create(
            category='mining',
            percentage=Decimal('25.50'),
            region=self.region,
            year=2025,
            month=1,
            updated_by=self.user
        )
        
        self.assertEqual(debtor_category.category, 'mining')
        self.assertEqual(debtor_category.percentage, Decimal('25.50'))
        self.assertEqual(debtor_category.region, self.region)
        self.assertEqual(debtor_category.year, 2025)
        self.assertEqual(debtor_category.month, 1)
        self.assertEqual(debtor_category.updated_by, self.user)
        self.assertIsNotNone(debtor_category.created_at)
        self.assertIsNotNone(debtor_category.updated_at)
    
    def test_debtor_category_string_representation(self):
        """Test string representation of DebtorCategory"""
        debtor_category = DebtorCategory.objects.create(
            category='domestic',
            percentage=Decimal('35.75'),
            region=self.region,
            year=2025,
            month=2
        )
        
        expected_str = f"Domestic - {self.region} (35.75%)"
        self.assertEqual(str(debtor_category), expected_str)
    
    def test_debtor_category_string_representation_global(self):
        """Test string representation without location (Global)"""
        debtor_category = DebtorCategory.objects.create(
            category='industry',
            percentage=Decimal('15.25'),
            year=2025,
            month=3
        )
        
        expected_str = "Industry - Global (15.25%)"
        self.assertEqual(str(debtor_category), expected_str)
    
    def test_debtor_category_choices(self):
        """Test that all category choices are valid"""
        valid_categories = [
            'mining', 'domestic', 'industry', 'commercial', 
            'farming', 'government', 'parastatal', 'local_authority'
        ]
        
        for category in valid_categories:
            debtor_category = DebtorCategory.objects.create(
                category=category,
                percentage=Decimal('12.50'),
                year=2025,
                month=4
            )
            self.assertEqual(debtor_category.category, category)
    
    def test_debtor_category_percentage_validation(self):
        """Test percentage validation (0.00 to 100.00)"""
        # Test negative percentage
        with self.assertRaises(ValidationError):
            debtor_category = DebtorCategory(
                category='mining',
                percentage=Decimal('-5.00'),
                year=2025,
                month=5
            )
            debtor_category.full_clean()
        
        # Test percentage over 100
        with self.assertRaises(ValidationError):
            debtor_category = DebtorCategory(
                category='mining',
                percentage=Decimal('105.00'),
                year=2025,
                month=6
            )
            debtor_category.full_clean()
        
        # Test valid boundary values
        debtor_category_zero = DebtorCategory.objects.create(
            category='mining',
            percentage=Decimal('0.00'),
            year=2025,
            month=7
        )
        self.assertEqual(debtor_category_zero.percentage, Decimal('0.00'))
        
        debtor_category_hundred = DebtorCategory.objects.create(
            category='domestic',
            percentage=Decimal('100.00'),
            year=2025,
            month=8
        )
        self.assertEqual(debtor_category_hundred.percentage, Decimal('100.00'))
    
    def test_debtor_category_month_validation(self):
        """Test month validation (1-12)"""
        # Test invalid month (0)
        with self.assertRaises(ValidationError):
            debtor_category = DebtorCategory(
                category='mining',
                percentage=Decimal('25.00'),
                year=2025,
                month=0
            )
            debtor_category.full_clean()
        
        # Test invalid month (13)
        with self.assertRaises(ValidationError):
            debtor_category = DebtorCategory(
                category='mining',
                percentage=Decimal('25.00'),
                year=2025,
                month=13
            )
            debtor_category.full_clean()
    
    def test_debtor_category_unique_constraint(self):
        """Test unique constraint on category, year, month, and location"""
        # Create first debtor category
        DebtorCategory.objects.create(
            category='mining',
            percentage=Decimal('25.00'),
            region=self.region,
            year=2025,
            month=9
        )
        
        # Try to create duplicate - should raise IntegrityError
        with self.assertRaises(IntegrityError):
            DebtorCategory.objects.create(
                category='mining',
                percentage=Decimal('30.00'),
                region=self.region,
                year=2025,
                month=9
            )
    
    def test_debtor_category_location_filtering(self):
        """Test location-based filtering functionality"""
        # Create debtor categories for different locations
        region_debtor = DebtorCategory.objects.create(
            category='mining',
            percentage=Decimal('25.00'),
            region=self.region,
            year=2025,
            month=10
        )
        
        district_debtor = DebtorCategory.objects.create(
            category='domestic',
            percentage=Decimal('35.00'),
            district=self.district,
            year=2025,
            month=10
        )
        
        depot_debtor = DebtorCategory.objects.create(
            category='industry',
            percentage=Decimal('15.00'),
            depot=self.depot,
            year=2025,
            month=10
        )
        
        # Test filtering by region
        region_debtors = DebtorCategory.objects.filter(region=self.region)
        self.assertEqual(region_debtors.count(), 1)
        self.assertEqual(region_debtors.first(), region_debtor)
        
        # Test filtering by district
        district_debtors = DebtorCategory.objects.filter(district=self.district)
        self.assertEqual(district_debtors.count(), 1)
        self.assertEqual(district_debtors.first(), district_debtor)
        
        # Test filtering by depot
        depot_debtors = DebtorCategory.objects.filter(depot=self.depot)
        self.assertEqual(depot_debtors.count(), 1)
        self.assertEqual(depot_debtors.first(), depot_debtor)
    
    def test_debtor_category_audit_trail(self):
        """Test audit trail functionality"""
        debtor_category = DebtorCategory.objects.create(
            category='commercial',
            percentage=Decimal('20.00'),
            year=2025,
            month=11,
            updated_by=self.user
        )
        
        # Check initial audit fields
        self.assertEqual(debtor_category.updated_by, self.user)
        self.assertIsNotNone(debtor_category.created_at)
        self.assertIsNotNone(debtor_category.updated_at)
        
        # Update the record
        original_updated_at = debtor_category.updated_at
        debtor_category.percentage = Decimal('25.00')
        debtor_category.save()
        
        # Check that updated_at changed
        self.assertGreater(debtor_category.updated_at, original_updated_at)
    
    def test_validate_percentages_sum_to_100(self):
        """Test class method for validating percentages sum to 100%"""
        # Test valid percentages that sum to 100
        valid_categories_data = [
            {'category': 'mining', 'percentage': '25.00'},
            {'category': 'domestic', 'percentage': '35.00'},
            {'category': 'industry', 'percentage': '20.00'},
            {'category': 'commercial', 'percentage': '20.00'}
        ]
        
        # Should not raise an exception
        try:
            DebtorCategory.validate_percentages_sum_to_100(valid_categories_data)
        except ValueError:
            self.fail("validate_percentages_sum_to_100 raised ValueError unexpectedly!")
        
        # Test invalid percentages that don't sum to 100
        invalid_categories_data = [
            {'category': 'mining', 'percentage': '25.00'},
            {'category': 'domestic', 'percentage': '35.00'},
            {'category': 'industry', 'percentage': '20.00'},
            {'category': 'commercial', 'percentage': '15.00'}  # Total = 95%
        ]
        
        with self.assertRaises(ValueError) as context:
            DebtorCategory.validate_percentages_sum_to_100(invalid_categories_data)
        
        self.assertIn("must sum to 100%", str(context.exception))
    
    def test_auto_adjust_percentages(self):
        """Test class method for auto-adjusting percentages"""
        # Create initial debtor categories
        mining = DebtorCategory.objects.create(
            category='mining',
            percentage=Decimal('25.00'),
            region=self.region,
            year=2025,
            month=12
        )
        
        domestic = DebtorCategory.objects.create(
            category='domestic',
            percentage=Decimal('35.00'),
            region=self.region,
            year=2025,
            month=12
        )
        
        industry = DebtorCategory.objects.create(
            category='industry',
            percentage=Decimal('20.00'),
            region=self.region,
            year=2025,
            month=12
        )
        
        commercial = DebtorCategory.objects.create(
            category='commercial',
            percentage=Decimal('20.00'),
            region=self.region,
            year=2025,
            month=12
        )
        
        # Test auto-adjustment when mining percentage changes to 50%
        location_filter = {
            'region': self.region,
            'year': 2025,
            'month': 12
        }
        
        updated_percentages = DebtorCategory.auto_adjust_percentages(
            location_filter, 'mining', 50.00
        )
        
        # Verify that other percentages were adjusted proportionally
        # Remaining 50% should be distributed proportionally among other categories
        # Original total of others: 35 + 20 + 20 = 75
        # New total should be 50, so adjustment factor = 50/75 = 2/3
        
        domestic.refresh_from_db()
        industry.refresh_from_db()
        commercial.refresh_from_db()
        
        # Check that percentages were adjusted (approximately)
        expected_domestic = Decimal('35.00') * (Decimal('50.00') / Decimal('75.00'))
        expected_industry = Decimal('20.00') * (Decimal('50.00') / Decimal('75.00'))
        expected_commercial = Decimal('20.00') * (Decimal('50.00') / Decimal('75.00'))
        
        # Allow for small rounding differences
        self.assertAlmostEqual(float(domestic.percentage), float(expected_domestic), places=1)
        self.assertAlmostEqual(float(industry.percentage), float(expected_industry), places=1)
        self.assertAlmostEqual(float(commercial.percentage), float(expected_commercial), places=1)
        
        # Verify the method returned the updated percentages
        self.assertIn('domestic', updated_percentages)
        self.assertIn('industry', updated_percentages)
        self.assertIn('commercial', updated_percentages)
    
    def test_clean_method_validation(self):
        """Test the clean method validation"""
        # Test valid percentage
        debtor_category = DebtorCategory(
            category='farming',
            percentage=Decimal('50.00'),
            year=2025,
            month=12
        )
        
        # Should not raise an exception
        try:
            debtor_category.clean()
        except ValidationError:
            self.fail("clean() raised ValidationError unexpectedly!")
        
        # Test invalid percentage (over 100)
        invalid_debtor_category = DebtorCategory(
            category='farming',
            percentage=Decimal('150.00'),
            year=2025,
            month=12
        )
        
        with self.assertRaises(ValidationError):
            invalid_debtor_category.clean()
    
    def test_save_method_calls_full_clean(self):
        """Test that save method calls full_clean for validation"""
        # This should raise ValidationError due to invalid percentage
        with self.assertRaises(ValidationError):
            DebtorCategory.objects.create(
                category='government',
                percentage=Decimal('150.00'),  # Invalid percentage
                year=2025,
                month=12
            )