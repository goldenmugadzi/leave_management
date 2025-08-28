from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import json
import logging

from .models import WeeklyCollections, WeeklyRevenueLost, DebtorCategory
from .serializers import (
    WeeklyCollectionsSerializer, WeeklyRevenueLostSerializer, 
    DebtorCategorySerializer, DashboardDataSerializer
)

logger = logging.getLogger(__name__)


def generate_dashboard_html(collections_data, revenue_lost_data, debtors_data, metrics):
    """Generate HTML for the dashboard components"""
    
    # Generate metric cards HTML
    metric_cards_html = f'''
    <div class="grid grid-cols-5 gap-5 mt-5">
        <div class="metric-card">
            <h5>ENERGY SOLD</h5>
            <p class="text-2xl font-bold text-blue-600">{metrics['energy_sold']['value']} {metrics['energy_sold']['unit']}</p>
            <p class="text-sm text-gray-600">Target: {metrics['energy_sold']['target']} {metrics['energy_sold']['target_unit']}</p>
            <div class="progress-bar mt-2">
                <div class="progress-fill bg-blue-600" style="width: {metrics['energy_sold']['progress']}%"></div>
            </div>
        </div>
        
        <div class="metric-card">
            <h5>GROWTH</h5>
            <p class="text-2xl font-bold text-green-600">{metrics['growth']['value']} {metrics['growth']['unit']}</p>
            <p class="text-sm text-gray-600">Target: {metrics['growth']['target']} {metrics['growth']['target_unit']}</p>
            <div class="progress-bar mt-2">
                <div class="progress-fill bg-green-600" style="width: {metrics['growth']['progress']}%"></div>
            </div>
        </div>
        
        <div class="metric-card">
            <h5>REVENUE COLLECTION</h5>
            <p class="text-xl font-bold text-purple-600">USD {metrics['revenue_usd']['value']}M</p>
            <p class="text-xl font-bold text-purple-600">ZWL {metrics['revenue_zwl']['value']}M</p>
            <div class="progress-bar mt-2">
                <div class="progress-fill bg-purple-600" style="width: {metrics['revenue_usd']['progress']}%"></div>
            </div>
        </div>
        
        <div class="metric-card">
            <h5>FAULTS</h5>
            <p class="text-2xl font-bold text-red-600">{metrics['faults']['value']} {metrics['faults']['unit']}</p>
            <p class="text-sm text-gray-600">Target: {metrics['faults']['target']} {metrics['faults']['target_unit']}</p>
            <div class="progress-bar mt-2">
                <div class="progress-fill bg-red-600" style="width: {metrics['faults']['progress']}%"></div>
            </div>
        </div>
        
        <div class="metric-card">
            <h5>MAINTENANCE</h5>
            <p class="text-2xl font-bold text-orange-600">{metrics['maintenance']['value']} {metrics['maintenance']['unit']}</p>
            <p class="text-sm text-gray-600">Target: {metrics['maintenance']['target']} {metrics['maintenance']['target_unit']}</p>
            <div class="progress-bar mt-2">
                <div class="progress-fill bg-orange-600" style="width: {metrics['maintenance']['progress']}%"></div>
            </div>
        </div>
    </div>
    '''
    
    # Generate data tables HTML
    tables_html = f'''
    <div class="dashboard-grid grid grid-cols-3 gap-4 mt-10">
        <div class="dashboard-section">
            <div class="dashboard-section-header">💰 Weekly Collections</div>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Week</th>
                        <th>ZWL (M)</th>
                        <th>USD (M)</th>
                    </tr>
                </thead>
                <tbody>
                    {generate_collections_table_rows(collections_data)}
                </tbody>
            </table>
        </div>
        
        <div class="dashboard-section">
            <div class="dashboard-section-header">⚡ Weekly Revenue Lost</div>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Week</th>
                        <th>Faults (MWh)</th>
                        <th>Maintenance (MWh)</th>
                        <th>Total (MWh)</th>
                    </tr>
                </thead>
                <tbody>
                    {generate_revenue_lost_table_rows(revenue_lost_data)}
                </tbody>
            </table>
        </div>
        
        <div class="dashboard-section">
            <div class="dashboard-section-header">📊 Debtors by Category</div>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Category</th>
                        <th>Percentage (%)</th>
                    </tr>
                </thead>
                <tbody>
                    {generate_debtors_table_rows(debtors_data)}
                </tbody>
            </table>
        </div>
    </div>
    '''
    
    return metric_cards_html + tables_html


def generate_collections_table_rows(collections_data):
    """Generate table rows for weekly collections"""
    if not collections_data:
        return '<tr><td colspan="3" class="text-center text-gray-500">No data available</td></tr>'
    
    rows = ''
    for i, collection in enumerate(collections_data):
        rows += f'''
        <tr>
            <td>{collection.get('week', '')}</td>
            <td class="editable-cell" data-table="weekly_collections" data-row="{i}" data-field="zwl_millions" onclick="startEdit('weekly_collections', {i}, 'zwl_millions', {collection.get('zwl_millions', 0)})">{collection.get('zwl_millions', 0)}M</td>
            <td class="editable-cell" data-table="weekly_collections" data-row="{i}" data-field="usd_millions" onclick="startEdit('weekly_collections', {i}, 'usd_millions', {collection.get('usd_millions', 0)})">{collection.get('usd_millions', 0)}M</td>
        </tr>
        '''
    return rows


def generate_revenue_lost_table_rows(revenue_lost_data):
    """Generate table rows for weekly revenue lost"""
    if not revenue_lost_data:
        return '<tr><td colspan="4" class="text-center text-gray-500">No data available</td></tr>'
    
    rows = ''
    for i, revenue in enumerate(revenue_lost_data):
        rows += f'''
        <tr>
            <td>{revenue.get('week', '')}</td>
            <td class="editable-cell" data-table="weekly_revenue_lost" data-row="{i}" data-field="faults_mwh" onclick="startEdit('weekly_revenue_lost', {i}, 'faults_mwh', {revenue.get('faults_mwh', 0)})">{revenue.get('faults_mwh', 0)} MWh</td>
            <td class="editable-cell" data-table="weekly_revenue_lost" data-row="{i}" data-field="maintenance_mwh" onclick="startEdit('weekly_revenue_lost', {i}, 'maintenance_mwh', {revenue.get('maintenance_mwh', 0)})">{revenue.get('maintenance_mwh', 0)} MWh</td>
            <td class="non-editable-cell">{revenue.get('total_mwh', 0)} MWh</td>
        </tr>
        '''
    return rows


def generate_debtors_table_rows(debtors_data):
    """Generate table rows for debtors"""
    if not debtors_data:
        return '<tr><td colspan="3" class="text-center text-gray-500">No data available</td></tr>'
    
    rows = ''
    for i, debtor in enumerate(debtors_data):
        rows += f'''
        <tr>
            <td>{debtor.get('id', i + 1)}</td>
            <td>{debtor.get('category', '')}</td>
            <td class="editable-cell" data-table="debtors" data-row="{i}" data-field="percentage" onclick="startEdit('debtors', {i}, 'percentage', {debtor.get('percentage', 0)})">{debtor.get('percentage', 0)}%</td>
        </tr>
        '''
    return rows


def dashboard_index(request):
    """Main dashboard index view"""
    return render(request, 'general_dashboards/dashboard_index.html', {
        'title': 'Executive Dashboard'
    })


@api_view(['GET'])
# @permission_classes([IsAuthenticated])  # Temporarily disabled for testing
def get_regions(request):
    """Get all regions, districts, and depots for filtering"""
    try:
        from it.users.models import Regions, Districts, Depots
        
        # Get all regions
        regions = Regions.objects.all().values('id', 'region')
        
        # Get all districts with region info
        districts = Districts.objects.all().values('id', 'district', 'region_id')
        
        # Get all depots with district and region info
        depots = Depots.objects.all().values('id', 'depot', 'district_id')
        
        # Return HTML for HTMX to populate the filter dropdowns
        regions_html = '<option value="">Select Region</option>'
        for r in regions:
            regions_html += f'<option value="{r["id"]}">{r["region"]}</option>'
        
        districts_html = '<option value="">Select District</option>'
        for d in districts:
            districts_html += f'<option value="{d["id"]}" data-region="{d["region_id"]}">{d["district"]}</option>'
        
        depots_html = '<option value="">Select Depot</option>'
        for dep in depots:
            depots_html += f'<option value="{dep["id"]}" data-district="{dep["district_id"]}">{dep["depot"]}</option>'
        
        # Return HTML fragment
        return HttpResponse(f'''
        <script>
            document.getElementById('selectRegion').innerHTML = `{regions_html}`;
            document.getElementById('selectDistrict').innerHTML = `{districts_html}`;
            document.getElementById('selectDepot').innerHTML = `{depots_html}`;
        </script>
        ''', content_type='text/html')
        
    except Exception as e:
        logger.error(f"Error getting regions: {str(e)}")
        return HttpResponse(f'<p class="text-red-600">Error loading regions data: {str(e)}</p>', content_type='text/html')


@api_view(['GET'])
# @permission_classes([IsAuthenticated])  # Temporarily disabled for testing
def get_dashboard_data(request):
    """Get complete dashboard data including new sections"""
    try:
        # Get filter parameters
        region_id = request.GET.get('region')
        district_id = request.GET.get('district')
        depot_id = request.GET.get('depot')
        
        # Build location filter
        location_filter = Q()
        if depot_id:
            location_filter = Q(depot_id=depot_id)
        elif district_id:
            location_filter = Q(district_id=district_id)
        elif region_id:
            location_filter = Q(region_id=region_id)
        
        # Get current year and month
        current_year = timezone.now().year
        current_month = timezone.now().month
        
        # Get weekly collections data
        if location_filter:
            weekly_collections = WeeklyCollections.objects.filter(
                location_filter & Q(year=current_year)
            ).order_by('week_number')
        else:
            # If no location filter, get all data for current year
            weekly_collections = WeeklyCollections.objects.filter(
                year=current_year
            ).order_by('week_number')
        
        # Get weekly revenue lost data
        if location_filter:
            weekly_revenue_lost = WeeklyRevenueLost.objects.filter(
                location_filter & Q(year=current_year)
            ).order_by('week_number')
        else:
            # If no location filter, get all data for current year
            weekly_revenue_lost = WeeklyRevenueLost.objects.filter(
                year=current_year
            ).order_by('week_number')
        
        # Get debtors data
        if location_filter:
            debtors = DebtorCategory.objects.filter(
                location_filter & Q(year=current_year, month=current_month)
            ).order_by('category')
        else:
            # If no location filter, get all data for current year/month
            debtors = DebtorCategory.objects.filter(
                year=current_year, month=current_month
            ).order_by('category')
        
        # Serialize the data
        collections_data = WeeklyCollectionsSerializer(weekly_collections, many=True).data
        revenue_lost_data = WeeklyRevenueLostSerializer(weekly_revenue_lost, many=True).data
        debtors_data = DebtorCategorySerializer(debtors, many=True).data
        
        # Debug logging
        logger.info(f"Found {len(collections_data)} collections, {len(revenue_lost_data)} revenue lost, {len(debtors_data)} debtors")
        if collections_data:
            logger.info(f"Sample collection: {collections_data[0]}")
        
        # Calculate metrics from actual data
        total_zwl = sum(float(c.get('zwl_millions', 0)) for c in collections_data) if collections_data else 0
        total_usd = sum(float(c.get('usd_millions', 0)) for c in collections_data) if collections_data else 0
        total_faults = sum(float(r.get('faults_mwh', 0)) for r in revenue_lost_data) if revenue_lost_data else 0
        total_maintenance = sum(float(r.get('maintenance_mwh', 0)) for r in revenue_lost_data) if revenue_lost_data else 0
        
        # Prepare response with existing dashboard structure
        dashboard_data = {
            'weekly_collections': collections_data,
            'weekly_revenue_lost': revenue_lost_data,
            'debtors': debtors_data,
            
            # Include existing dashboard sections (empty for now)
            'pbncs': [],
            'weekly_sales': [],
            'upos': [],
            'weekly_outages': [],
            'tds': [],
            'weekly_faults_maintenance': [],
            
            # Metrics data calculated from actual data
            'metrics': {
                'energy_sold': {'value': f'{total_zwl:.1f}', 'unit': 'M ZWL', 'target': '1000.0', 'target_unit': 'M ZWL', 'progress': min(100, int((total_zwl / 1000.0) * 100))},
                'growth': {'value': f'{len(collections_data)}', 'unit': 'Weeks', 'target': '52', 'target_unit': 'Weeks', 'progress': min(100, int((len(collections_data) / 52.0) * 100))},
                'revenue_usd': {'value': f'{total_usd:.1f}', 'unit': 'M', 'target': '500.0', 'target_unit': 'M', 'progress': min(100, int((total_usd / 500.0) * 100))},
                'revenue_zwl': {'value': f'{total_zwl:.1f}', 'unit': 'M', 'target': '1000.0', 'target_unit': 'M', 'progress': min(100, int((total_zwl / 1000.0) * 100))},
                'faults': {'value': f'{total_faults:.1f}', 'unit': 'MWh', 'target': '100.0', 'target_unit': 'MWh', 'progress': min(100, int((total_faults / 100.0) * 100))},
                'maintenance': {'value': f'{total_maintenance:.1f}', 'unit': 'MWh', 'target': '50.0', 'target_unit': 'MWh', 'progress': min(100, int((total_maintenance / 50.0) * 100))}
            },
            
            # Chart data
            'inspection_locations': '[]',
            'inspections_count': '[]',
            'maintenance_locations': '[]',
            'maintenance_count': '[]',
            'mnt': {}
        }
        
        # Generate HTML for the dashboard
        html_content = generate_dashboard_html(collections_data, revenue_lost_data, debtors_data, dashboard_data['metrics'])
        
        return HttpResponse(html_content, content_type='text/html')
        
    except Exception as e:
        logger.error(f"Error getting dashboard data: {str(e)}")
        return HttpResponse('<p class="text-red-600">Error loading dashboard data</p>', content_type='text/html')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_dashboard_data(request):
    """Save dashboard data with support for new sections"""
    try:
        data = request.data
        table_type = data.get('table')
        row_index = data.get('row')
        field = data.get('field')
        value = data.get('value')
        
        if not all([table_type, field, value is not None]):
            return Response({
                'success': False,
                'error': 'Missing required parameters'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Handle different table types
        if table_type == 'weekly_collections':
            result = save_weekly_collections(request, row_index, field, value)
        elif table_type == 'weekly_revenue_lost':
            result = save_weekly_revenue_lost(request, row_index, field, value)
        elif table_type == 'debtors':
            result = save_debtor_category(request, row_index, field, value)
        else:
            return Response({
                'success': False,
                'error': f'Unsupported table type: {table_type}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(result)
        
    except Exception as e:
        logger.error(f"Error saving dashboard data: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to save data'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def save_weekly_collections(request, row_index, field, value):
    """Save weekly collections data"""
    try:
        # Get the record to update
        collections = WeeklyCollections.objects.filter(year=2025).order_by('week_number')
        if row_index >= len(collections):
            return {'success': False, 'error': 'Invalid row index'}
        
        collection = collections[row_index]
        
        # Update the field
        if field == 'zwl_millions':
            collection.zwl_millions = float(value)
        elif field == 'usd_millions':
            collection.usd_millions = float(value)
        else:
            return {'success': False, 'error': f'Invalid field: {field}'}
        
        collection.updated_by = request.user
        collection.save()
        
        return {
            'success': True,
            'message': 'Weekly collections updated successfully',
            'data': WeeklyCollectionsSerializer(collection).data
        }
        
    except (ValueError, ValidationError) as e:
        return {'success': False, 'error': f'Validation error: {str(e)}'}
    except Exception as e:
        logger.error(f"Error saving weekly collections: {str(e)}")
        return {'success': False, 'error': 'Failed to save weekly collections'}


def save_weekly_revenue_lost(request, row_index, field, value):
    """Save weekly revenue lost data"""
    try:
        # Get the record to update
        revenue_lost = WeeklyRevenueLost.objects.filter(year=2025).order_by('week_number')
        if row_index >= len(revenue_lost):
            return {'success': False, 'error': 'Invalid row index'}
        
        record = revenue_lost[row_index]
        
        # Update the field
        if field == 'faults_mwh':
            record.faults_mwh = float(value)
        elif field == 'maintenance_mwh':
            record.maintenance_mwh = float(value)
        else:
            return {'success': False, 'error': f'Invalid field: {field}'}
        
        # Total will be auto-calculated in the model's save method
        record.updated_by = request.user
        record.save()
        
        return {
            'success': True,
            'message': 'Weekly revenue lost updated successfully',
            'data': WeeklyRevenueLostSerializer(record).data
        }
        
    except (ValueError, ValidationError) as e:
        return {'success': False, 'error': f'Validation error: {str(e)}'}
    except Exception as e:
        logger.error(f"Error saving weekly revenue lost: {str(e)}")
        return {'success': False, 'error': 'Failed to save weekly revenue lost'}


def save_debtor_category(request, row_index, field, value):
    """Save debtor category data"""
    try:
        # Get the record to update
        debtors = DebtorCategory.objects.filter(year=2025, month=timezone.now().month).order_by('category')
        if row_index >= len(debtors):
            return {'success': False, 'error': 'Invalid row index'}
        
        debtor = debtors[row_index]
        
        # Update the field
        if field == 'percentage':
            new_percentage = float(value)
            
            # Validate percentage range
            if new_percentage < 0 or new_percentage > 100:
                return {'success': False, 'error': 'Percentage must be between 0 and 100'}
            
            # Get other categories for the same location and time period
            other_categories = DebtorCategory.objects.filter(
                year=debtor.year,
                month=debtor.month,
                region=debtor.region,
                district=debtor.district,
                depot=debtor.depot
            ).exclude(pk=debtor.pk)
            
            # Calculate total percentage including this category
            total_percentage = sum([cat.percentage for cat in other_categories]) + new_percentage
            
            if total_percentage > 100:
                return {'success': False, 'error': f'Total percentage cannot exceed 100%. Current total: {total_percentage}%'}
            
            debtor.percentage = new_percentage
        else:
            return {'success': False, 'error': f'Invalid field: {field}'}
        
        debtor.updated_by = request.user
        debtor.save()
        
        return {
            'success': True,
            'message': 'Debtor category updated successfully',
            'data': DebtorCategorySerializer(debtor).data
        }
        
    except (ValueError, ValidationError) as e:
        return {'success': False, 'error': f'Validation error: {str(e)}'}
    except Exception as e:
        logger.error(f"Error saving debtor category: {str(e)}")
        return {'success': False, 'error': 'Failed to save debtor category'}


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_permissions(request):
    """Get user permissions for dashboard editing"""
    try:
        user = request.user
        
        # Check if user can edit dashboard data
        can_edit = user.is_staff or user.groups.filter(name__in=['admin', 'editor', 'manager']).exists()
        
        # Get user roles
        user_roles = list(user.groups.values_list('name', flat=True))
        
        return Response({
            'success': True,
            'canEdit': can_edit,
            'userRoles': user_roles,
            'user': {
                'username': user.username,
                'firstName': getattr(user, 'first_name', ''),
                'lastName': getattr(user, 'last_name', '')
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting user permissions: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to retrieve user permissions'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_sample_data(request):
    """Create sample data for testing the new dashboard sections"""
    try:
        from it.users.models import Regions, Districts, Depots
        
        # Get or create sample location
        region, _ = Regions.objects.get_or_create(region="HARARE REGION")
        district, _ = Districts.objects.get_or_create(
            district="HARARE DISTRICT",
            region=region
        )
        depot, _ = Depots.objects.get_or_create(
            depot="HARARE CENTRAL",
            district=district
        )
        
        current_year = timezone.now().year
        current_month = timezone.now().month
        
        # Create sample weekly collections data
        for week_num in range(1, 7):
            WeeklyCollections.objects.get_or_create(
                week=f"Week {week_num}",
                year=current_year,
                week_number=week_num,
                region=region,
                district=district,
                depot=depot,
                defaults={
                    'zwl_millions': round(5.0 + week_num * 0.5, 2),
                    'usd_millions': round(2.0 + week_num * 0.3, 2),
                    'updated_by': request.user
                }
            )
        
        # Create sample weekly revenue lost data
        for week_num in range(1, 7):
            WeeklyRevenueLost.objects.get_or_create(
                week=f"Week {week_num}",
                year=current_year,
                week_number=week_num,
                region=region,
                district=district,
                depot=depot,
                defaults={
                    'faults_mwh': round(10.0 + week_num * 2.0, 2),
                    'maintenance_mwh': round(5.0 + week_num * 1.5, 2),
                    'updated_by': request.user
                }
            )
        
        # Create sample debtor categories
        categories = [
            ('mining', 25.0),
            ('domestic', 20.0),
            ('industry', 15.0),
            ('commercial', 12.0),
            ('farming', 10.0),
            ('government', 8.0),
            ('parastatal', 6.0),
            ('local_authority', 4.0)
        ]
        
        for category, percentage in categories:
            DebtorCategory.objects.get_or_create(
                category=category,
                year=current_year,
                month=current_month,
                region=region,
                district=district,
                depot=depot,
                defaults={
                    'percentage': percentage,
                    'updated_by': request.user
                }
            )
        
        return Response({
            'success': True,
            'message': 'Sample data created successfully',
            'data': {
                'weekly_collections_count': 6,
                'weekly_revenue_lost_count': 6,
                'debtor_categories_count': 8
            }
        })
        
    except Exception as e:
        logger.error(f"Error creating sample data: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to create sample data'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
