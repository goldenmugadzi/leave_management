"""
Enhanced ACE Reports Views with Exception Handling and Better Design
"""

import logging
import csv
from datetime import datetime, date
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction as db_transaction
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.template import loader
from django.utils import timezone
from django.utils.dateparse import parse_date
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from weasyprint import HTML, CSS

from .exceptions import (
    ACEReportException, 
    BudgetDataError, 
    ReportGenerationError, 
    DataValidationError,
    ExportError,
    PermissionError as ACEPermissionError
)
from .models import Ace2, AssetBudget, Transactions, AceReport
from .forms import AceReportForm
from it.users.models import UserProfile, Regions

# Set up logging
logger = logging.getLogger(__name__)

class ACEReportService:
    """Service class for handling ACE reports with proper exception handling"""
    
    @staticmethod
    def validate_user_permissions(user, region=None):
        """Validate that user has permission to view reports"""
        try:
            user_profile = UserProfile.objects.get(id=user.id)
            
            # Check if user has reporting role
            if not user_profile.roles.filter(application="ace").exists():
                raise ACEPermissionError("User does not have ACE reporting permissions")
            
            # Check region access if specified
            if region and user_profile.region != region:
                raise ACEPermissionError("User does not have access to this region's data")
                
            return user_profile
        except UserProfile.DoesNotExist:
            raise ACEPermissionError("User profile not found")
    
    @staticmethod
    def validate_date_range(start_date, end_date):
        """Validate date range inputs"""
        if not start_date or not end_date:
            raise DataValidationError("Both start and end dates are required")
        
        if start_date > end_date:
            raise DataValidationError("Start date cannot be after end date")
        
        # Check for reasonable date range (not more than 5 years)
        if (end_date - start_date).days > 1825:
            raise DataValidationError("Date range cannot exceed 5 years")
        
        return True
    
    @staticmethod
    def get_budget_summary(region, current_year=None):
        """Get budget summary with error handling"""
        try:
            if not current_year:
                current_year = timezone.now().year
            
            budgets = AssetBudget.objects.filter(
                region=region, 
                period=current_year
            ).exclude(
                allocated__isnull=True
            ).exclude(
                allocated=0
            ).order_by('-allocated')
            
            if not budgets.exists():
                logger.warning(f"No budgets found for region {region} in year {current_year}")
                return [], 0, 0, 0, 0
            
            budget_summary = []
            total_allocated = 0
            total_utilized = 0
            total_pending = 0
            total_available = 0
            
            for budget_item in budgets:
                try:
                    # Safely get budget values
                    allocated = budget_item.allocated or 0
                    withdrawn = budget_item.withdrawn or 0
                    to_be_withdrawn = budget_item.to_be_withdrawn or 0
                    balance = budget_item.balance or 0
                    
                    # Get ACE statistics for this budget
                    budget_aces = Ace2.objects.filter(
                        budget_id=budget_item,
                        date_created__year=current_year
                    ).exclude(
                        process__approval_set__approved="Rejected"
                    )
                    
                    ace_count = budget_aces.count()
                    total_ace_amount = budget_aces.aggregate(
                        total=Sum('amount')
                    )['total'] or 0
                    
                    avg_ace_amount = (
                        total_ace_amount / ace_count if ace_count > 0 else 0
                    )
                    
                    # Calculate percentages safely
                    if allocated > 0:
                        utilization_percentage = (withdrawn / allocated) * 100
                        pending_percentage = (to_be_withdrawn / allocated) * 100
                        available_percentage = (balance / allocated) * 100
                    else:
                        utilization_percentage = 0
                        pending_percentage = 0
                        available_percentage = 0
                    
                    total_commitment_percentage = (
                        utilization_percentage + pending_percentage
                    )
                    
                    # Determine health status
                    if balance > (allocated * 0.3):
                        health_status = 'good'
                    elif balance > (allocated * 0.1):
                        health_status = 'warning'
                    else:
                        health_status = 'critical'
                    
                    budget_summary.append({
                        'budget': budget_item,
                        'allocated': allocated,
                        'withdrawn': withdrawn,
                        'to_be_withdrawn': to_be_withdrawn,
                        'balance': balance,
                        'utilization_percentage': round(utilization_percentage, 2),
                        'pending_percentage': round(pending_percentage, 2),
                        'available_percentage': round(available_percentage, 2),
                        'total_commitment_percentage': round(total_commitment_percentage, 2),
                        'total_committed': withdrawn + to_be_withdrawn,
                        'ace_count': ace_count,
                        'avg_ace_amount': round(avg_ace_amount, 2),
                        'health_status': health_status
                    })
                    
                    # Add to totals
                    total_allocated += allocated
                    total_utilized += withdrawn
                    total_pending += to_be_withdrawn
                    total_available += balance
                    
                except Exception as e:
                    logger.error(f"Error processing budget {budget_item.budget_id}: {str(e)}")
                    continue
            
            return budget_summary, total_allocated, total_utilized, total_pending, total_available
            
        except Exception as e:
            logger.error(f"Error generating budget summary: {str(e)}")
            raise BudgetDataError(f"Failed to generate budget summary: {str(e)}")
    
    @staticmethod
    def get_ace_data(region, start_date=None, end_date=None, budget=None):
        """Get ACE data with proper filtering and error handling"""
        try:
            # Base query
            aces_query = Ace2.objects.filter(region=region)
            
            # Apply date filters
            if start_date and end_date:
                aces_query = aces_query.filter(
                    date_created__range=[start_date, end_date]
                )
            
            # Apply budget filter if specified
            if budget:
                aces_query = aces_query.filter(budget_id=budget)
            
            # Exclude rejected ACEs
            aces_query = aces_query.exclude(
                process__approval_set__approved="Rejected"
            )
            
            # Order by date (most recent first)
            aces = aces_query.order_by('-date_created')
            
            logger.info(f"Retrieved {aces.count()} ACE records for region {region}")
            return aces
            
        except Exception as e:
            logger.error(f"Error retrieving ACE data: {str(e)}")
            raise ReportGenerationError(f"Failed to retrieve ACE data: {str(e)}")


@login_required
def ace_reports_enhanced(request):
    """Enhanced ACE reports view with better error handling and design"""
    try:
        # Validate user permissions
        user_profile = ACEReportService.validate_user_permissions(request.user)
        current_year = timezone.now().year
        
        if request.method == 'POST':
            form = AceReportForm(request.POST)
            
            if form.is_valid():
                try:
                    start_date = form.cleaned_data['start_date']
                    end_date = form.cleaned_data['end_date']
                    region = form.cleaned_data['region']
                    budget = form.cleaned_data.get('budget_id')
                    
                    # Validate date range
                    ACEReportService.validate_date_range(start_date, end_date)
                    
                    # Validate region access
                    ACEReportService.validate_user_permissions(request.user, region)
                    
                    # Get ACE data
                    aces = ACEReportService.get_ace_data(
                        region, start_date, end_date, budget
                    )
                    
                    # Get budget summary
                    budget_summary, total_allocated, total_utilized, total_pending, total_available = (
                        ACEReportService.get_budget_summary(region, current_year)
                    )
                    
                    # Save report if specific budget is selected
                    report = None
                    if budget:
                        try:
                            with db_transaction.atomic():
                                report = AceReport.objects.create(
                                    start_date=start_date,
                                    end_date=end_date,
                                    region=region,
                                    budget_id=budget
                                )
                                logger.info(f"Created report {report.report_id2}")
                        except Exception as e:
                            logger.error(f"Error saving report: {str(e)}")
                            messages.warning(request, "Report generated but not saved to database")
                    
                    context = {
                        'aces': aces,
                        'report': report,
                        'budget_summary': budget_summary,
                        'current_year': current_year,
                        'total_allocated': total_allocated,
                        'total_utilized': total_utilized,
                        'total_pending': total_pending,
                        'total_available': total_available,
                        'start_date': start_date,
                        'end_date': end_date,
                        'region': region,
                        'form': form
                    }
                    
                    return render(request, 'finance/ace2/ace_reports_enhanced.html', context)
                    
                except (DataValidationError, ACEPermissionError, BudgetDataError, ReportGenerationError) as e:
                    logger.error(f"Report generation error: {str(e)}")
                    messages.error(request, str(e))
                    
                except Exception as e:
                    logger.error(f"Unexpected error in report generation: {str(e)}")
                    messages.error(request, "An unexpected error occurred while generating the report")
            
            else:
                messages.error(request, "Please correct the form errors")
        
        # Default view - show current year summary
        try:
            region = user_profile.region
            budget_summary, total_allocated, total_utilized, total_pending, total_available = (
                ACEReportService.get_budget_summary(region, current_year)
            )
            
            form = AceReportForm(user=user_profile)
            
            context = {
                'ace_report_form': form,
                'budget_summary': budget_summary,
                'current_year': current_year,
                'total_allocated': total_allocated,
                'total_utilized': total_utilized,
                'total_pending': total_pending,
                'total_available': total_available,
                'default_view': True
            }
            
            return render(request, 'finance/ace2/ace_reports_enhanced.html', context)
            
        except Exception as e:
            logger.error(f"Error in default view: {str(e)}")
            messages.error(request, "Error loading budget summary")
            
            # Fallback to basic form
            form = AceReportForm(user=user_profile) if user_profile else AceReportForm()
            return render(request, 'finance/ace2/ace_reports_enhanced.html', {
                'ace_report_form': form,
                'current_year': current_year,
                'error': True
            })
    
    except ACEPermissionError as e:
        logger.error(f"Permission error: {str(e)}")
        return HttpResponseForbidden("You do not have permission to view ACE reports")
    
    except Exception as e:
        logger.error(f"Unexpected error in ace_reports_enhanced: {str(e)}")
        messages.error(request, "An unexpected error occurred")
        return redirect('/dashboard')


@login_required
def ace_report_detail_csv_enhanced(request, report_id2=None):
    """Enhanced CSV export with better error handling"""
    try:
        # Validate user permissions
        user_profile = ACEReportService.validate_user_permissions(request.user)
        
        if report_id2:
            # Export specific report
            report = get_object_or_404(AceReport, report_id2=report_id2)
            
            # Validate region access
            ACEReportService.validate_user_permissions(request.user, report.region)
            
            # Get ACE data
            aces = ACEReportService.get_ace_data(
                report.region, 
                report.start_date, 
                report.end_date, 
                report.budget_id
            )
            
            filename = f"ace_report_{report.report_id2}_{report.start_date}_{report.end_date}.csv"
            
        else:
            # Export based on parameters
            start_date = parse_date(request.GET.get('start_date'))
            end_date = parse_date(request.GET.get('end_date'))
            region_id = request.GET.get('region')
            budget_id = request.GET.get('budget_id')
            all_budgets = request.GET.get('all_budgets')
            
            # Validate parameters
            if not start_date or not end_date:
                raise DataValidationError("Start and end dates are required")
            
            ACEReportService.validate_date_range(start_date, end_date)
            
            # Get region
            if region_id:
                region = get_object_or_404(Regions, id=region_id)
                ACEReportService.validate_user_permissions(request.user, region)
            else:
                region = user_profile.region
            
            # Get budget if specified
            budget = None
            if budget_id and not all_budgets:
                budget = get_object_or_404(AssetBudget, budget_id=budget_id)
            
            # Get ACE data
            aces = ACEReportService.get_ace_data(region, start_date, end_date, budget)
            
            # Generate filename
            if all_budgets or not budget_id:
                filename = f"ace_report_all_budgets_{start_date}_{end_date}.csv"
            else:
                filename = f"ace_report_budget_{budget_id}_{start_date}_{end_date}.csv"
        
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        writer = csv.writer(response)
        
        # Write headers
        writer.writerow([
            'ACE ID',
            'Details of Expenditure',
            'Requested By',
            'Section',
            'Date Created',
            'Budget',
            'Amount',
            'Currency',
            'Transaction Status',
            'Approval Status',
            'Actioned By',
            'Action Date',
            'Region'
        ])
        
        # Write data rows
        for ace in aces:
            try:
                # Get transaction info safely
                transaction = Transactions.objects.filter(Ace_id2=ace).first()
                
                # Get approval info safely
                latest_approval = None
                if ace.process and ace.process.approval_set.exists():
                    latest_approval = ace.process.approval_set.last()
                
                approval_status = latest_approval.approved if latest_approval else 'Pending'
                actioned_by = (
                    latest_approval.user.get_full_name() 
                    if latest_approval and latest_approval.user 
                    else 'N/A'
                )
                action_date = (
                    latest_approval.approved_at.strftime('%Y-%m-%d') 
                    if latest_approval and hasattr(latest_approval, 'approved_at') and latest_approval.approved_at
                    else 'N/A'
                )
                
                # Get section name safely
                section_name = ace.section.section if ace.section else 'N/A'
                
                writer.writerow([
                    ace.Ace_id2 or 'N/A',
                    ace.details_of_expenditure or 'N/A',
                    ace.requested_by.get_full_name() if ace.requested_by else 'N/A',
                    section_name,
                    ace.date_created.strftime('%Y-%m-%d') if ace.date_created else 'N/A',
                    ace.budget_id.budget_name if ace.budget_id else 'N/A',
                    ace.amount or 0,
                    ace.currency or 'N/A',
                    transaction.approval_status if transaction else 'N/A',
                    approval_status,
                    actioned_by,
                    action_date,
                    ace.region.region if ace.region else 'N/A'
                ])
                
            except Exception as e:
                logger.error(f"Error writing ACE {ace.Ace_id2} to CSV: {str(e)}")
                # Write a minimal row to avoid breaking the export
                writer.writerow([
                    ace.Ace_id2 or 'N/A',
                    'Error retrieving data',
                    'N/A', 'N/A', 'N/A', 'N/A', 0, 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A'
                ])
        
        logger.info(f"CSV export completed: {filename}")
        return response
        
    except (DataValidationError, ACEPermissionError) as e:
        logger.error(f"Export error: {str(e)}")
        messages.error(request, str(e))
        return redirect('/ace/reports')
    
    except Exception as e:
        logger.error(f"Unexpected error in CSV export: {str(e)}")
        raise ExportError(f"Failed to export CSV: {str(e)}")


@login_required
def ace_report_detail_pdf_enhanced(request, report_id2=None):
    """Enhanced PDF export with better error handling"""
    try:
        # Validate user permissions
        user_profile = ACEReportService.validate_user_permissions(request.user)
        
        if report_id2:
            # Export specific report
            report = get_object_or_404(AceReport, report_id2=report_id2)
            
            # Validate region access
            ACEReportService.validate_user_permissions(request.user, report.region)
            
            # Get ACE data and budget summary
            aces = ACEReportService.get_ace_data(
                report.region, 
                report.start_date, 
                report.end_date, 
                report.budget_id
            )
            
            budget_summary, total_allocated, total_utilized, total_pending, total_available = (
                ACEReportService.get_budget_summary(report.region)
            )
            
            filename = f"ace_report_{report.report_id2}.pdf"
            
        else:
            # Export based on parameters
            start_date = parse_date(request.GET.get('start_date'))
            end_date = parse_date(request.GET.get('end_date'))
            region_id = request.GET.get('region')
            
            # Validate parameters
            if not start_date or not end_date:
                raise DataValidationError("Start and end dates are required")
            
            ACEReportService.validate_date_range(start_date, end_date)
            
            # Get region
            if region_id:
                region = get_object_or_404(Regions, id=region_id)
                ACEReportService.validate_user_permissions(request.user, region)
            else:
                region = user_profile.region
            
            # Get data
            aces = ACEReportService.get_ace_data(region, start_date, end_date)
            budget_summary, total_allocated, total_utilized, total_pending, total_available = (
                ACEReportService.get_budget_summary(region)
            )
            
            filename = f"ace_report_{start_date}_{end_date}.pdf"
        
        # Render template
        template = loader.get_template('finance/ace2/ace_reports_enhanced.html')
        context = {
            'aces': aces,
            'budget_summary': budget_summary,
            'current_year': timezone.now().year,
            'total_allocated': total_allocated,
            'total_utilized': total_utilized,
            'total_pending': total_pending,
            'total_available': total_available,
            'request': request,
            'print_mode': True
        }
        
        html = template.render(context, request)
        
        # Generate PDF
        css_string = """
        @page {
            size: A4;
            margin: 1in;
        }
        body {
            font-family: Arial, sans-serif;
            font-size: 12px;
            line-height: 1.4;
        }
        .action-buttons,
        .quick-actions {
            display: none !important;
        }
        """
        
        pdf = HTML(string=html).write_pdf(stylesheets=[CSS(string=css_string)])
        
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        logger.info(f"PDF export completed: {filename}")
        return response
        
    except (DataValidationError, ACEPermissionError) as e:
        logger.error(f"PDF export error: {str(e)}")
        messages.error(request, str(e))
        return redirect('/ace/reports')
    
    except Exception as e:
        logger.error(f"Unexpected error in PDF export: {str(e)}")
        raise ExportError(f"Failed to export PDF: {str(e)}")


@login_required
def asset_budget_report_enhanced(request, budget_id):
    """Enhanced asset budget report with better error handling"""
    try:
        # Validate user permissions
        user_profile = ACEReportService.validate_user_permissions(request.user)
        
        # Get budget
        budget = get_object_or_404(AssetBudget, pk=budget_id)
        
        # Validate region access
        ACEReportService.validate_user_permissions(request.user, budget.region)
        
        # Get ACE data
        aces = Ace2.objects.filter(budget_id=budget).exclude(
            process__approval_set__approved="Rejected"
        ).order_by('-date_created')
        
        # Calculate statistics
        total_used = aces.aggregate(total=Sum('amount'))['total'] or 0
        
        # Safely get budget values
        allocated = budget.allocated or 0
        withdrawn = budget.withdrawn or 0
        awaiting_sanctioning = budget.awaiting_sanctioning or 0
        balance = budget.balance or 0
        
        # Calculate utilization rate
        utilization_rate = (withdrawn / allocated * 100) if allocated > 0 else 0
        
        # Get ACE status counts
        status_counts = {
            'approved': 0,
            'pending': 0,
            'rejected': 0,
            'unknown': 0
        }
        
        for ace in aces:
            try:
                if ace.process and ace.process.approval_set.exists():
                    status = ace.process.approval_set.last().approved
                    if status == "Approved":
                        status_counts['approved'] += 1
                    elif status == "Rejected":
                        status_counts['rejected'] += 1
                    else:
                        status_counts['pending'] += 1
                else:
                    status_counts['unknown'] += 1
            except Exception as e:
                logger.error(f"Error getting status for ACE {ace.Ace_id2}: {str(e)}")
                status_counts['unknown'] += 1
        
        # Get monthly usage data
        try:
            end_date = timezone.now()
            start_date = end_date.replace(month=1, day=1)  # Start of current year
            
            monthly_usage = aces.filter(
                date_created__gte=start_date,
                date_created__lte=end_date
            ).annotate(
                month=TruncMonth('date_created')
            ).values('month').annotate(
                total_amount=Sum('amount'),
                ace_count=Count('Ace_id')
            ).order_by('month')
            
            # Format monthly data for chart
            monthly_data = {
                'labels': [],
                'amounts': [],
                'counts': []
            }
            
            for item in monthly_usage:
                if item['month']:
                    monthly_data['labels'].append(item['month'].strftime('%b %Y'))
                    monthly_data['amounts'].append(float(item['total_amount'] or 0))
                    monthly_data['counts'].append(item['ace_count'])
                    
        except Exception as e:
            logger.error(f"Error generating monthly data: {str(e)}")
            monthly_data = {'labels': [], 'amounts': [], 'counts': []}
        
        # Calculate additional metrics
        avg_ace_amount = total_used / aces.count() if aces.count() > 0 else 0
        
        context = {
            'budget': budget,
            'aces': aces,
            'total_used': total_used,
            'allocated': allocated,
            'withdrawn': withdrawn,
            'awaiting_sanctioning': awaiting_sanctioning,
            'balance': balance,
            'utilization_rate': round(utilization_rate, 2),
            'approved_count': status_counts['approved'],
            'pending_count': status_counts['pending'],
            'rejected_count': status_counts['rejected'],
            'unknown_count': status_counts['unknown'],
            'monthly_data': monthly_data,
            'avg_ace_amount': avg_ace_amount,
            'total_aces': aces.count(),
        }
        
        return render(request, 'finance/ace2/asset_budget_report_enhanced.html', context)
        
    except ACEPermissionError as e:
        logger.error(f"Permission error: {str(e)}")
        return HttpResponseForbidden("You do not have permission to view this budget report")
    
    except Exception as e:
        logger.error(f"Error in asset budget report: {str(e)}")
        messages.error(request, "Error loading budget report")
        return redirect('/ace/budgets')
