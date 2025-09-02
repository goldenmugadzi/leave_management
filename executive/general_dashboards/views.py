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
from .forms import DashboardDataBulkImportForm
from it.users.models import Regions, Districts, Depots

logger = logging.getLogger(__name__)


def generate_dashboard_html(collections_data, revenue_lost_data, debtors_data, metrics, is_authenticated=False, access_level='none', show_aggregated_view=False):
    """Generate HTML for the dashboard components with role-based context"""
    
    # Add access level notice
    access_notice = ''
    if not is_authenticated:
        access_notice = '''
        <div class="bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 p-4 mb-6" role="alert">
            <div class="flex">
                <div class="flex-shrink-0">
                    <svg class="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
                    </svg>
                </div>
                <div class="ml-3">
                    <p class="text-sm">
                        <strong>Note:</strong> You are viewing the dashboard in read-only mode. 
                        <a href="/admin/login/" class="font-medium underline hover:text-yellow-600">Log in</a> to edit data.
                    </p>
                </div>
            </div>
        </div>
        '''
    elif access_level == 'authenticated_user':
        access_notice = '''
        <div class="bg-blue-100 border-l-4 border-blue-500 text-blue-700 p-4 mb-6" role="alert">
            <div class="flex">
                <div class="flex-shrink-0">
                    <svg class="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z" clip-rule="evenodd" />
                    </svg>
                </div>
                <div class="ml-3">
                    <p class="text-sm">
                        <strong>Dashboard View:</strong> You can view data across all regions, districts, and depots. Use the filters to focus on specific locations.
                    </p>
                </div>
            </div>
        </div>
        '''
    
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
                    {generate_collections_table_rows(collections_data, is_authenticated)}
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
                    {generate_revenue_lost_table_rows(revenue_lost_data, is_authenticated)}
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
                    {generate_debtors_table_rows(debtors_data, is_authenticated)}
                </tbody>
            </table>
        </div>
    </div>
    '''
    
    return access_notice + metric_cards_html + tables_html


def generate_collections_table_rows(collections_data, is_authenticated=False):
    """Generate table rows for weekly collections"""
    if not collections_data:
        return '<tr><td colspan="3" class="text-center text-gray-500">No data available</td></tr>'
    
    rows = ''
    for i, collection in enumerate(collections_data):
        if is_authenticated:
            rows += f'''
            <tr>
                <td>{collection.get('week', '')}</td>
                <td class="editable-cell" data-table="weekly_collections" data-row="{i}" data-field="zwl_millions" onclick="startEdit('weekly_collections', {i}, 'zwl_millions', {collection.get('zwl_millions', 0)})">{collection.get('zwl_millions', 0)}M</td>
                <td class="editable-cell" data-table="weekly_collections" data-row="{i}" data-field="usd_millions" onclick="startEdit('weekly_collections', {i}, 'usd_millions', {collection.get('usd_millions', 0)})">{collection.get('usd_millions', 0)}M</td>
            </tr>
            '''
        else:
            rows += f'''
            <tr>
                <td>{collection.get('week', '')}</td>
                <td class="non-editable-cell">{collection.get('zwl_millions', 0)}M</td>
                <td class="non-editable-cell">{collection.get('usd_millions', 0)}M</td>
            </tr>
            '''
    return rows


def generate_revenue_lost_table_rows(revenue_lost_data, is_authenticated=False):
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


def generate_debtors_table_rows(debtors_data, is_authenticated=False):
    """Generate table rows for debtors"""
    if not debtors_data:
        return '<tr><td colspan="3" class="text-center text-gray-500">No data available</td></tr>'
    
    rows = ''
    for i, debtor in enumerate(debtors_data):
        if is_authenticated:
            rows += f'''
            <tr>
                <td>{i + 1}</td>
                <td>{debtor.get('category', '')}</td>
                <td class="editable-cell" data-table="debtors" data-row="{i}" data-field="percentage" onclick="startEdit('debtors', {i}, 'percentage', {debtor.get('percentage', 0)})">{debtor.get('percentage', 0)}%</td>
            </tr>
            '''
        else:
            rows += f'''
            <tr>
                <td>{debtor.get('id', i + 1)}</td>
                <td>{debtor.get('category', '')}</td>
                <td class="non-editable-cell">{debtor.get('percentage', 0)}%</td>
            </tr>
            '''
    return rows


def dashboard_index(request):
    """Main dashboard index view"""
    return render(request, 'general_dashboards/dashboard_index.html', {
        'title': 'Executive Dashboard',
        'is_authenticated': request.user.is_authenticated
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_regions(request):
    """Get regions, districts, and depots based on user's access level"""
    
    try:
        # Get user's allowed locations and default region
        allowed_locations = get_user_allowed_locations(request.user)
        access_level, _ = get_user_dashboard_access_level(request.user)
        
        # Get user's default region for auto-selection
        from it.users.models import UserProfile
        try:
            user_profile = UserProfile.objects.get(id=request.user.id)
            default_region_id = user_profile.region.id if user_profile.region else None
            default_district_id = user_profile.district.id if user_profile.district else None
            default_depot_id = user_profile.depot.id if user_profile.depot else None
        except UserProfile.DoesNotExist:
            default_region_id = None
            default_district_id = None
            default_depot_id = None
        
        # Build HTML options with default selection
        regions_html = '<option value="">All Regions</option>'
        for r in allowed_locations['regions']:
            selected = 'selected' if r["id"] == default_region_id else ''
            regions_html += f'<option value="{r["id"]}" {selected}>{r["region"]}</option>'
        
        districts_html = '<option value="">All Districts</option>'
        for d in allowed_locations['districts']:
            selected = 'selected' if d["id"] == default_district_id else ''
            districts_html += f'<option value="{d["id"]}" data-region="{d["region_id"]}" {selected}>{d["district"]}</option>'
        
        depots_html = '<option value="">All Depots</option>'
        for dep in allowed_locations['depots']:
            selected = 'selected' if dep["id"] == default_depot_id else ''
            depots_html += f'<option value="{dep["id"]}" data-district="{dep["district_id"]}" {selected}>{dep["depot"]}</option>'
        
        # Add a simple notice for all authenticated users
        notice_html = ''
        if access_level == 'authenticated_user':
            notice_html = '''
            <div class="bg-blue-100 border-l-4 border-blue-500 text-blue-700 p-3 mb-4" role="alert">
                <div class="flex">
                    <div class="flex-shrink-0">
                        <svg class="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
                            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
                        </svg>
                    </div>
                    <div class="ml-3">
                        <p class="text-sm">
                            <strong>Dashboard View:</strong> You can view data across all regions, districts, and depots. Use the filters above to focus on specific locations.
                        </p>
                    </div>
                </div>
            </div>
            '''
        
        # Return HTML fragment with notice and updated dropdowns
        return HttpResponse(f'''
        {notice_html}
        <script>
            document.getElementById('selectRegion').innerHTML = `{regions_html}`;
            document.getElementById('selectDistrict').innerHTML = `{districts_html}`;
            document.getElementById('selectDepot').innerHTML = `{depots_html}`;
            
            // Trigger filter application if user has a default region selected
            setTimeout(function() {{
                if (document.getElementById('selectRegion').value || 
                    document.getElementById('selectDistrict').value || 
                    document.getElementById('selectDepot').value) {{
                    if (typeof applyFilters === 'function') {{
                        applyFilters();
                    }}
                }}
            }}, 100);
        </script>
        ''', content_type='text/html')
        
    except Exception as e:
        logger.error(f"Error getting regions: {str(e)}")
        return HttpResponse(f'<p class="text-red-600">Error loading regions data: {str(e)}</p>', content_type='text/html')


@api_view(['GET'])
@permission_classes([])
@csrf_exempt
def get_dashboard_data(request):
    """Get complete dashboard data including new sections with role-based access control"""
    # Get authentication status from query parameter (passed from frontend)
    auth_param = request.GET.get('auth', 'false')
    is_authenticated = auth_param.lower() == 'true'
    
    try:
        # Get user's access level and default filter
        if is_authenticated and request.user.is_authenticated:
            access_level, user_default_filter = get_user_dashboard_access_level(request.user)
            show_aggregated_view = False  # No special aggregated view needed
        else:
            # For unauthenticated users, no access to any specific data
            access_level = 'none'
            user_default_filter = Q(pk__isnull=True)
            show_aggregated_view = False
        
        # Get current year and month first (needed for flexible filtering)
        current_year = timezone.now().year
        current_month = timezone.now().month

        # Get filter parameters from URL
        region_id = request.GET.get('region')
        district_id = request.GET.get('district')
        depot_id = request.GET.get('depot')

        # For authenticated users, determine the best filter to use
        if access_level == 'authenticated_user':
            # Try filters in order of specificity, falling back to broader filters if no data found
            location_filter = _get_flexible_location_filter(
                region_id, district_id, depot_id, current_year, current_month
            )
            if not location_filter:
                # If no specific filters provided, use user's default region
                location_filter = user_default_filter
        else:
            # No access users get no data
            location_filter = Q(pk__isnull=True)
        
        # Apply location filter to data queries
        base_collections_query = WeeklyCollections.objects.filter(year=current_year)
        base_revenue_query = WeeklyRevenueLost.objects.filter(year=current_year)
        base_debtors_query = DebtorCategory.objects.filter(year=current_year, month=current_month)
        
        if location_filter and access_level == 'authenticated_user':
            # Apply the location filter (either requested or user's default region)
            weekly_collections = base_collections_query.filter(location_filter).order_by('week_number')
            weekly_revenue_lost = base_revenue_query.filter(location_filter).order_by('week_number')
            debtors = base_debtors_query.filter(location_filter).order_by('category')
        elif access_level == 'authenticated_user':
            # If no filter and authenticated, show all data
            weekly_collections = base_collections_query.order_by('week_number')
            weekly_revenue_lost = base_revenue_query.order_by('week_number')
            debtors = base_debtors_query.order_by('category')
        else:
            # Unauthenticated users get no data
            weekly_collections = base_collections_query.none()
            weekly_revenue_lost = base_revenue_query.none()
            debtors = base_debtors_query.none()
        
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
        
        # Generate HTML for the dashboard with access level context
        html_content = generate_dashboard_html(
            collections_data, 
            revenue_lost_data, 
            debtors_data, 
            dashboard_data['metrics'], 
            is_authenticated,
            access_level,
            show_aggregated_view
        )
        
        return HttpResponse(html_content, content_type='text/html')
        
    except Exception as e:
        logger.error(f"Error getting dashboard data: {str(e)}")
        return HttpResponse('<p class="text-red-600">Error loading dashboard data</p>', content_type='text/html')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_dashboard_data(request):
    """Save dashboard data with role-based access control"""
    try:
        # Check if user has permission to edit dashboard data
        can_edit = check_user_can_edit_dashboard(request.user)
        if not can_edit:
            return Response({
                'success': False,
                'error': 'Insufficient permissions. Only users with Manager role for dashboards can edit data.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get data from request
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
    # Authentication is already checked in the main save function
    try:
        # Get the record to update
        current_year = timezone.now().year
        collections = WeeklyCollections.objects.filter(year=current_year).order_by('week_number')
        if row_index >= len(collections):
            return {'success': False, 'error': 'Invalid row index'}
        print("collections:", collections)
        collection = collections[row_index]
        print("collection:", collection)
        # Update the field - convert to Decimal to match model field type
        from decimal import Decimal
        if field == 'zwl_millions':
            collection.zwl_millions = Decimal(str(value))
        elif field == 'usd_millions':
            collection.usd_millions = Decimal(str(value))
        else:
            return {'success': False, 'error': f'Invalid field: {field}'}
        
        # Set updated_by to None since we don't have the actual user object in AJAX calls
        collection.updated_by = None
        collection.save()
        print("collection saved:", collection)
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
    # Authentication is already checked in the main save function
    try:
        # Get the record to update
        current_year = timezone.now().year
        revenue_lost = WeeklyRevenueLost.objects.filter(year=current_year).order_by('week_number')
        if row_index >= len(revenue_lost):
            return {'success': False, 'error': 'Invalid row index'}
        
        record = revenue_lost[row_index]
        
        # Update the field - convert to Decimal to match model field type
        from decimal import Decimal
        if field == 'faults_mwh':
            record.faults_mwh = Decimal(str(value))
        elif field == 'maintenance_mwh':
            record.maintenance_mwh = Decimal(str(value))
        else:
            return {'success': False, 'error': f'Invalid field: {field}'}
        
        # Total will be auto-calculated in the model's save method
        # Set updated_by to None since we don't have the actual user object in AJAX calls
        record.updated_by = None
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
    # Authentication is already checked in the main save function
    try:
        # Get the record to update
        debtors = DebtorCategory.objects.filter(year=2025, month=timezone.now().month).order_by('category')
        if row_index >= len(debtors):
            return {'success': False, 'error': 'Invalid row index'}
        
        debtor = debtors[row_index]
        
        # Update the field - convert to Decimal to match model field type
        from decimal import Decimal
        if field == 'percentage':
            new_percentage = Decimal(str(value))
            
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
        
        # Set updated_by to None since we don't have the actual user object in AJAX calls
        debtor.updated_by = None
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

def download_csv_template(request):
    """Download CSV template for dashboard data"""
    data_type = request.GET.get('type', 'weekly_collections')

    if data_type == 'weekly_collections':
        template_data = [
            ['week', 'week_number', 'zwl_millions', 'usd_millions', 'region', 'district', 'depot'],
            ['Week 1', '1', '5.20', '2.30', 'HARARE REGION', 'HARARE DISTRICT', 'HARARE CENTRAL'],
            ['Week 2', '2', '5.70', '2.60', 'HARARE REGION', 'HARARE DISTRICT', 'HARARE CENTRAL'],
            ['Week 3', '3', '6.20', '2.90', 'HARARE REGION', 'HARARE DISTRICT', 'HARARE CENTRAL'],
        ]
        filename = 'weekly_collections_template.csv'
    elif data_type == 'weekly_revenue_lost':
        template_data = [
            ['week', 'week_number', 'faults_mwh', 'maintenance_mwh', 'region', 'district', 'depot'],
            ['Week 1', '1', '12.00', '6.50', 'HARARE REGION', 'HARARE DISTRICT', 'HARARE CENTRAL'],
            ['Week 2', '2', '14.00', '8.00', 'HARARE REGION', 'HARARE DISTRICT', 'HARARE CENTRAL'],
            ['Week 3', '3', '16.00', '9.50', 'HARARE REGION', 'HARARE DISTRICT', 'HARARE CENTRAL'],
        ]
        filename = 'weekly_revenue_lost_template.csv'
    elif data_type == 'debtor_categories':
        template_data = [
            ['category', 'percentage', 'region', 'district', 'depot'],
            ['mining', '25.00', 'HARARE REGION', 'HARARE DISTRICT', 'HARARE CENTRAL'],
            ['domestic', '20.00', 'HARARE REGION', 'HARARE DISTRICT', 'HARARE CENTRAL'],
            ['industry', '15.00', 'HARARE REGION', 'HARARE DISTRICT', 'HARARE CENTRAL'],
        ]
        filename = 'debtor_categories_template.csv'
    else:
        return HttpResponse('Invalid data type', status=400)
    
    # Create CSV response
    import csv
    from io import StringIO
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerows(template_data)
    
    response = HttpResponse(output.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


def _get_flexible_location_filter(region_id, district_id, depot_id, current_year, current_month):
    """
    Get the most appropriate location filter based on available data.
    Tries filters in order of specificity, falling back to broader filters if no data found.

    Returns Q() if no filters provided, otherwise returns the best filter that has data.
    """
    from django.db.models import Q

    # If no filters provided, return empty Q (will use user's default later)
    if not any([region_id, district_id, depot_id]):
        return Q()

    # Try depot-level filter first (most specific)
    if depot_id:
        depot_filter = Q(depot_id=depot_id)
        if (_has_dashboard_data(depot_filter, current_year, current_month)):
            return depot_filter

    # Fall back to district-level filter
    if district_id:
        district_filter = Q(district_id=district_id)
        if (_has_dashboard_data(district_filter, current_year, current_month)):
            return district_filter

    # Fall back to region-level filter
    if region_id:
        region_filter = Q(region_id=region_id)
        if (_has_dashboard_data(region_filter, current_year, current_month)):
            return region_filter

    # If no specific filters have data, return the most specific filter provided
    # This ensures the user sees something rather than an empty dashboard
    if depot_id:
        return Q(depot_id=depot_id)
    elif district_id:
        return Q(district_id=district_id)
    elif region_id:
        return Q(region_id=region_id)

    return Q()


def _has_dashboard_data(location_filter, year, month):
    """
    Check if there's any dashboard data for the given location filter.
    Returns True if at least one type of data exists.
    """
    from .models import WeeklyCollections, WeeklyRevenueLost, DebtorCategory

    return (
        WeeklyCollections.objects.filter(location_filter, year=year).exists() or
        WeeklyRevenueLost.objects.filter(location_filter, year=year).exists() or
        DebtorCategory.objects.filter(location_filter, year=year, month=month).exists()
    )


def check_user_can_edit_dashboard(user):
    """Check if user has permission to edit dashboard data - simplified for single role system"""
    # Check if user has the manager role for dashboards application
    from it.users.models import UserProfile
    try:
        user_profile = UserProfile.objects.get(id=user.id)
        return user_profile.roles.filter(application='dashboards', role='manager').exists() or user.is_staff
    except UserProfile.DoesNotExist:
        return user.is_staff


def get_user_dashboard_access_level(user):
    """
    Determine user's dashboard access level - now simplified for single role system
    Returns: ('level', default_location_filter)
    All authenticated users can view all data but default to their region
    """
    from it.users.models import UserProfile, Roles
    
    try:
        user_profile = UserProfile.objects.get(id=user.id)
        
        # All authenticated users can view all data, but we return their default region for initial view
        default_filter = Q()
        if user_profile.region:
            default_filter = Q(region_id=user_profile.region.id)
        elif user_profile.district:
            default_filter = Q(district_id=user_profile.district.id)
        elif user_profile.depot:
            default_filter = Q(depot_id=user_profile.depot.id)
        
        return 'authenticated_user', default_filter
        
    except UserProfile.DoesNotExist:
        return 'none', Q(pk__isnull=True)  # No access filter


def get_user_allowed_locations(user):
    """
    Get locations that user is allowed to filter by
    Returns: dict with 'regions', 'districts', 'depots' lists
    Now simplified - all authenticated users can view all locations
    """
    from it.users.models import UserProfile, Regions, Districts, Depots
    
    try:
        user_profile = UserProfile.objects.get(id=user.id)
        
        # All authenticated users can see all locations
        return {
            'regions': list(Regions.objects.all().values('id', 'region')),
            'districts': list(Districts.objects.all().values('id', 'district', 'region_id')),
            'depots': list(Depots.objects.all().values('id', 'depot', 'district_id'))
        }
            
    except UserProfile.DoesNotExist:
        return {
            'regions': [],
            'districts': [],
            'depots': []
        }


def bulk_upload_dashboard_data(request):
    """Bulk upload dashboard data from CSV/Excel files"""
    try:
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'error': 'User not authenticated. Please log in and try again.'
            }, status=401)
        
        # Check permissions
        if not check_user_can_edit_dashboard(request.user):
            return JsonResponse({
                'success': False,
                'error': 'Insufficient permissions. Only users with Manager role for dashboards can edit data.'
            }, status=403)
        
        # Get form data
        form = DashboardDataBulkImportForm(request.POST, request.FILES)
        if not form.is_valid():
            return JsonResponse({
                'success': False,
                'error': 'Invalid form data',
                'errors': form.errors
            }, status=400)
        
        # Process file
        try:
            file = form.cleaned_data['file']
            data_type = form.cleaned_data['data_type']
            year = form.cleaned_data['year']
            
            # Import data based on type
            if data_type == 'weekly_collections':
                result = import_weekly_collections_from_file(file, year, request.user)
            elif data_type == 'weekly_revenue_lost':
                result = import_weekly_revenue_lost_from_file(file, year, request.user)
            elif data_type == 'debtor_categories':
                month = form.cleaned_data.get('month')
                if not month:
                    return JsonResponse({
                        'success': False,
                        'error': 'Month is required for debtor categories'
                    }, status=400)
                result = import_debtor_categories_from_file(file, year, month, request.user)
            else:
                return JsonResponse({
                    'success': False,
                    'error': f'Unsupported data type: {data_type}'
                }, status=400)
                
        except KeyError as e:
            return JsonResponse({
                'success': False,
                'error': f'Missing required field: {e}'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error processing form data: {str(e)}'
            }, status=400)
        
        return JsonResponse(result)
        
    except Exception as e:
        print(f"Error in bulk upload: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Upload failed'
        }, status=500)


def import_weekly_collections_from_file(file, year, user):
    """Import weekly collections data from uploaded file"""
    try:
        import pandas as pd
        from decimal import Decimal
        
        # Read file
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)
        
        # Validate required columns
        required_cols = ['week', 'week_number', 'zwl_millions', 'usd_millions', 'region', 'district', 'depot']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            return {'success': False, 'error': f'Missing required columns: {missing_cols}'}
        
        # Process data
        records_created = 0
        records_updated = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Get or create location objects
                region, _ = Regions.objects.get_or_create(
                    region=row['region'],
                    defaults={'code': row['region'][:2].upper()}
                )
                
                district, _ = Districts.objects.get_or_create(
                    district=row['district'],
                    region_id=region.region,
                    defaults={'code': row['district'][:2].upper()}
                )
                
                depot, _ = Depots.objects.get_or_create(
                    depot=row['depot'],
                    district=district,
                    region=region,
                    defaults={'code': row['depot'][:2].upper()}
                )
                
                # Check if record exists
                existing_record = WeeklyCollections.objects.filter(
                    week=row['week'],
                    year=year,
                    week_number=row['week_number'],
                    region=region,
                    district=district,
                    depot=depot
                ).first()
                
                if existing_record:
                    # Update existing record
                    existing_record.zwl_millions = Decimal(str(row['zwl_millions']))
                    existing_record.usd_millions = Decimal(str(row['usd_millions']))
                    existing_record.updated_by = user
                    existing_record.save()
                    records_updated += 1
                else:
                    # Create new record
                    WeeklyCollections.objects.create(
                        week=row['week'],
                        year=year,
                        week_number=row['week_number'],
                        region=region,
                        district=district,
                        depot=depot,
                        zwl_millions=Decimal(str(row['zwl_millions'])),
                        usd_millions=Decimal(str(row['usd_millions'])),
                        updated_by=user
                    )
                    records_created += 1
                    
            except Exception as e:
                errors.append(f"Row {index + 1}: {str(e)}")
        
        return {
            'success': True,
            'message': f'Successfully imported data: {records_created} created, {records_updated} updated',
            'data': {
                'created': records_created,
                'updated': records_updated,
                'errors': errors
            }
        }
        
    except Exception as e:
        return {'success': False, 'error': f'Import failed: {str(e)}'}


def import_weekly_revenue_lost_from_file(file, year, user):
    """Import weekly revenue lost data from uploaded file"""
    try:
        import pandas as pd
        from decimal import Decimal
        
        # Read file
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)
        
        # Validate required columns
        required_cols = ['week', 'week_number', 'faults_mwh', 'maintenance_mwh', 'region', 'district', 'depot']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            return {'success': False, 'error': f'Missing required columns: {missing_cols}'}
        
        # Process data
        records_created = 0
        records_updated = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Get or create location objects
                region, _ = Regions.objects.get_or_create(
                    region=row['region'],
                    defaults={'code': row['region'][:2].upper()}
                )
                
                district, _ = Districts.objects.get_or_create(
                    district=row['district'],
                    region_id=region.region,
                    defaults={'code': row['district'][:2].upper()}
                )
                
                depot, _ = Depots.objects.get_or_create(
                    depot=row['depot'],
                    district=district,
                    region=region,
                    defaults={'code': row['depot'][:2].upper()}
                )
                
                # Check if record exists
                existing_record = WeeklyRevenueLost.objects.filter(
                    week=row['week'],
                    year=year,
                    week_number=row['week_number'],
                    region=region,
                    district=district,
                    depot=depot
                ).first()
                
                if existing_record:
                    # Update existing record
                    existing_record.faults_mwh = Decimal(str(row['faults_mwh']))
                    existing_record.maintenance_mwh = Decimal(str(row['maintenance_mwh']))
                    existing_record.updated_by = user
                    existing_record.save()
                    records_updated += 1
                else:
                    # Create new record
                    WeeklyRevenueLost.objects.create(
                        week=row['week'],
                        year=year,
                        week_number=row['week_number'],
                        region=region,
                        district=district,
                        depot=depot,
                        faults_mwh=Decimal(str(row['faults_mwh'])),
                        maintenance_mwh=Decimal(str(row['maintenance_mwh'])),
                        updated_by=user
                    )
                    records_created += 1
                    
            except Exception as e:
                errors.append(f"Row {index + 1}: {str(e)}")
        
        return {
            'success': True,
            'message': f'Successfully imported data: {records_created} created, {records_updated} updated',
            'data': {
                'created': records_created,
                'updated': records_updated,
                'errors': errors
            }
        }
        
    except Exception as e:
        return {'success': False, 'error': f'Import failed: {str(e)}'}





def import_debtor_categories_from_file(file, year, month, user):
    """Import debtor categories data from uploaded file"""
    try:
        import pandas as pd
        from decimal import Decimal
        
        # Read file
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)
        
        # Validate required columns
        required_cols = ['category', 'percentage', 'region', 'district', 'depot']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            return {'success': False, 'error': f'Missing required columns: {missing_cols}'}
        
        # Process data
        records_created = 0
        records_updated = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Get or create location objects
                region, _ = Regions.objects.get_or_create(
                    region=row['region'],
                    defaults={'code': row['region'][:2].upper()}
                )
                
                district, _ = Districts.objects.get_or_create(
                    district=row['district'],
                    region_id=region.region,
                    defaults={'code': row['district'][:2].upper()}
                )
                
                depot, _ = Depots.objects.get_or_create(
                    depot=row['depot'],
                    district=district,
                    region=region,
                    defaults={'code': row['depot'][:2].upper()}
                )
                
                # Check if record exists
                existing_record = DebtorCategory.objects.filter(
                    category=row['category'],
                    year=year,
                    month=month,
                    region=region,
                    district=district,
                    depot=depot
                ).first()
                
                if existing_record:
                    # Update existing record
                    existing_record.percentage = Decimal(str(row['percentage']))
                    existing_record.updated_by = user
                    existing_record.save()
                    records_updated += 1
                else:
                    # Create new record
                    DebtorCategory.objects.create(
                        category=row['category'],
                        year=year,
                        month=month,
                        region=region,
                        district=district,
                        depot=depot,
                        percentage=Decimal(str(row['percentage'])),
                        updated_by=user
                    )
                    records_created += 1
                    
            except Exception as e:
                errors.append(f"Row {index + 1}: {str(e)}")
        
        return {
            'success': True,
            'message': f'Successfully imported data: {records_created} created, {records_updated} updated',
            'data': {
                'created': records_created,
                'updated': records_updated,
                'errors': errors
            }
        }
        
    except Exception as e:
        return {'success': False, 'error': f'Import failed: {str(e)}'}
