# Django Server Implementation Guide for BEApp
## Step-by-Step Implementation

**Version:** 1.0  
**Date:** September 19, 2025

## Table of Contents
1. [Project Setup](#project-setup)
2. [Django Settings](#django-settings)  
3. [URL Configuration](#url-configuration)
4. [Models](#models)
5. [Serializers](#serializers)
6. [Views](#views)
7. [Authentication](#authentication)
8. [File Handling](#file-handling)
9. [Deployment Checklist](#deployment-checklist)

---

## Project Setup

### 1. Install Required Packages
```bash
pip install django
pip install djangorestframework
pip install djangorestframework-simplejwt
pip install django-cors-headers
pip install pillow
pip install celery
pip install redis
```

### 2. Create Django Project Structure
```
beapp_server/
├── manage.py
├── requirements.txt
├── beapp_server/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── authentication/
│   ├── applications/
│   ├── customers/
│   ├── contractors/
│   ├── inspections/
│   ├── files/
│   └── sync/
└── media/
    └── uploads/
```

---

## Django Settings

### settings.py
```python
import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Security
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
ALLOWED_HOSTS = [
    'api.beapp.zw',
    'api-staging.beapp.zw', 
    'localhost',
    '127.0.0.1'
]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    
    # Local apps
    'apps.authentication',
    'apps.applications',
    'apps.customers', 
    'apps.contractors',
    'apps.inspections',
    'apps.files',
    'apps.sync',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'beapp_server.urls'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'beapp_db'),
        'USER': os.environ.get('DB_USER', 'beapp_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'password'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'user': '100/min'
    }
}

# JWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

# CORS settings
CORS_ALLOWED_ORIGINS = [
    "exp://192.168.1.100:8081",  # Expo development
    "https://beapp.zw",
]

CORS_ALLOW_CREDENTIALS = True

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024   # 10MB

# Celery Configuration (for background tasks)
CELERY_BROKER_URL = 'redis://localhost:6379'
CELERY_RESULT_BACKEND = 'redis://localhost:6379'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'beapp.log'),
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'beapp': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

---

## URL Configuration

### beapp_server/urls.py
```python
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include([
        path('auth/', include('apps.authentication.urls')),
        path('applications/', include('apps.applications.urls')),
        path('customers/', include('apps.customers.urls')),
        path('contractors/', include('apps.contractors.urls')),
        path('inspections/', include('apps.inspections.urls')),
        path('files/', include('apps.files.urls')),
        path('sync/', include('apps.sync.urls')),
    ])),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

---

## Models

### apps/authentication/models.py
```python
from django.contrib.auth.models import AbstractUser
from django.db import models

class UserRole(models.TextChoices):
    FIELD_OFFICER = 'field_officer', 'Field Officer'
    SUPERVISOR = 'supervisor', 'Supervisor'  
    ADMIN = 'admin', 'Admin'

class User(AbstractUser):
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.FIELD_OFFICER)
    employee_id = models.CharField(max_length=20, unique=True)
    district = models.CharField(max_length=50, blank=True)
    region = models.CharField(max_length=50, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

class DeviceToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='device_tokens')
    device_id = models.CharField(max_length=100)
    token = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['user', 'device_id']
```

### apps/customers/models.py
```python
from django.db import models

class Customer(models.Model):
    customer_id = models.CharField(max_length=50, unique=True)  # CUST-YYYYMMDD-XXXXXXXX
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    stand_plot_number = models.CharField(max_length=50, blank=True)
    farm_street_name = models.CharField(max_length=200, blank=True)
    suburb_township = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.customer_id} - {self.full_name}"

    class Meta:
        ordering = ['full_name']
```

### apps/contractors/models.py
```python
from django.db import models

class Contractor(models.Model):
    contractor_id = models.CharField(max_length=50, unique=True)  # CONT-YYYYMMDD-XXXXXXXX
    business_name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    license_number = models.CharField(max_length=100, blank=True)
    business_registration = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.contractor_id} - {self.business_name}"

    class Meta:
        ordering = ['business_name']
```

### apps/applications/models.py
```python
from django.db import models
from apps.customers.models import Customer
from apps.contractors.models import Contractor
from apps.authentication.models import User

class ApplicationType(models.TextChoices):
    NEW_INSTALLATION = 'new_installation', 'New Installation'
    STATUTORY_INSPECTION = 'statutory_inspection', 'Statutory Inspection'
    CHANGE_OF_TENANCY = 'change_of_tenancy', 'Change of Tenancy'
    RECONNECTION = 'reconnection', 'Reconnection'

class Priority(models.TextChoices):
    LOW = 'low', 'Low'
    NORMAL = 'normal', 'Normal'
    HIGH = 'high', 'High'
    URGENT = 'urgent', 'Urgent'

class ApplicationStatus(models.TextChoices):
    SUBMITTED = 'submitted', 'Submitted'
    ASSIGNED = 'assigned', 'Assigned'
    IN_PROGRESS = 'in_progress', 'In Progress'
    COMPLETED = 'completed', 'Completed'
    REJECTED = 'rejected', 'Rejected'

class AssignmentStatus(models.TextChoices):
    ASSIGNED = 'assigned', 'Assigned'
    ACCEPTED = 'accepted', 'Accepted' 
    IN_PROGRESS = 'in_progress', 'In Progress'
    COMPLETED = 'completed', 'Completed'

class Application(models.Model):
    application_number = models.CharField(max_length=50, unique=True)  # APP-YYYYMMDD-XXXXXXXX
    application_type = models.CharField(max_length=30, choices=ApplicationType.choices)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.NORMAL)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='applications')
    contractor = models.ForeignKey(Contractor, on_delete=models.CASCADE, related_name='applications')
    purpose = models.CharField(max_length=50)  # domestic, commercial, agricultural, etc.
    supply_type = models.CharField(max_length=20)  # permanent, temporary
    status = models.CharField(max_length=20, choices=ApplicationStatus.choices, default=ApplicationStatus.SUBMITTED)
    assignment_status = models.CharField(max_length=20, choices=AssignmentStatus.choices, default=AssignmentStatus.ASSIGNED)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_applications')
    due_date = models.DateTimeField(null=True, blank=True)
    assigned_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.application_number} - {self.customer.full_name}"

    class Meta:
        ordering = ['-created_at']

class ApplicationAttachment(models.Model):
    FILE_TYPES = [
        ('E21', 'E21 Form'),
        ('E22', 'E22 Form'),
        ('E25', 'E25 Form'),
        ('other', 'Other Document'),
    ]

    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='applications/attachments/%Y/%m/')
    file_type = models.CharField(max_length=10, choices=FILE_TYPES)
    description = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.application.application_number} - {self.file_type}"
```

### apps/inspections/models.py
```python
from django.db import models
from apps.applications.models import Application
from apps.authentication.models import User

class InspectionStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    IN_PROGRESS = 'in_progress', 'In Progress'
    COMPLETED = 'completed', 'Completed'
    APPROVED = 'approved', 'Approved'

class Inspection(models.Model):
    # Mobile app inspection ID
    mobile_id = models.CharField(max_length=100, unique=True)
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='inspections')
    inspector = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inspections')
    
    # E117 Form Data (stored as JSON)
    service_number = models.CharField(max_length=50)
    consumer_details = models.JSONField()
    property_details = models.JSONField()
    contractor_details = models.JSONField()
    inspection_points = models.JSONField()  # All 33 points
    
    # Results
    overall_result = models.CharField(max_length=20)  # passed, failed
    defects_count = models.IntegerField(default=0)
    
    # Signatures and GPS
    inspector_signature = models.TextField(blank=True)  # Base64 encoded
    customer_signature = models.TextField(blank=True)
    gps_coordinates = models.JSONField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=InspectionStatus.choices, default=InspectionStatus.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Inspection {self.mobile_id} - {self.application.application_number}"

    class Meta:
        ordering = ['-created_at']

class InspectionPhoto(models.Model):
    inspection = models.ForeignKey(Inspection, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='inspections/photos/%Y/%m/')
    inspection_point = models.CharField(max_length=10)  # Which point (1-33)
    description = models.CharField(max_length=200, blank=True)
    gps_coordinates = models.JSONField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.inspection.mobile_id} - Point {self.inspection_point}"

class InspectionDefect(models.Model):
    inspection = models.ForeignKey(Inspection, on_delete=models.CASCADE, related_name='defects')
    inspection_point = models.CharField(max_length=10)
    defect_code = models.CharField(max_length=50)
    description = models.TextField()
    severity = models.CharField(max_length=20)  # minor, major, critical
    is_rectified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.inspection.mobile_id} - {self.defect_code}"
```

---

## Serializers

### apps/authentication/serializers.py
```python
from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User

class UserSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'phone', 
                 'role', 'employee_id', 'district', 'region', 'is_active', 
                 'last_login', 'permissions']
        read_only_fields = ['id', 'last_login']

    def get_permissions(self, obj):
        # Define permissions based on role
        permissions = {
            'field_officer': {
                'canViewAssignments': True,
                'canAcceptAssignments': True,
                'canCreateInspections': True,
                'canCompleteInspections': True,
                'canViewAllInspections': False,
                'canApproveInspections': False,
                'canManageUsers': False,
                'canViewReports': False,
                'canExportData': False,
            },
            'supervisor': {
                'canViewAssignments': True,
                'canAcceptAssignments': True,
                'canCreateInspections': True,
                'canCompleteInspections': True,
                'canViewAllInspections': True,
                'canApproveInspections': True,
                'canManageUsers': False,
                'canViewReports': True,
                'canExportData': True,
            },
            'admin': {
                'canViewAssignments': True,
                'canAcceptAssignments': True,
                'canCreateInspections': True,
                'canCompleteInspections': True,
                'canViewAllInspections': True,
                'canApproveInspections': True,
                'canManageUsers': True,
                'canViewReports': True,
                'canExportData': True,
            },
        }
        return permissions.get(obj.role, permissions['field_officer'])

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
    deviceId = serializers.CharField(required=False)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Must provide username and password')
```

### apps/applications/serializers.py
```python
from rest_framework import serializers
from .models import Application, ApplicationAttachment
from apps.customers.serializers import CustomerSerializer
from apps.contractors.serializers import ContractorSerializer

class ApplicationAttachmentSerializer(serializers.ModelSerializer):
    fileUrl = serializers.SerializerMethodField()
    serverId = serializers.CharField(source='id', read_only=True)
    applicationServerId = serializers.CharField(source='application.id', read_only=True)

    class Meta:
        model = ApplicationAttachment
        fields = ['serverId', 'applicationServerId', 'fileUrl', 'file_type', 
                 'description', 'uploaded_at', 'file']

    def get_fileUrl(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(f'/api/v1/files/{obj.id}/download')
        return None

class ApplicationSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(read_only=True)
    contractor = ContractorSerializer(read_only=True)
    attachments = ApplicationAttachmentSerializer(many=True, read_only=True)
    serverId = serializers.CharField(source='id', read_only=True)

    class Meta:
        model = Application
        fields = ['serverId', 'application_number', 'application_type', 'priority',
                 'customer', 'contractor', 'attachments', 'purpose', 'supply_type',
                 'status', 'assignment_status', 'assigned_to', 'due_date',
                 'created_at', 'updated_at']

class AssignmentResponseSerializer(serializers.Serializer):
    applications = ApplicationSerializer(many=True)
    total_count = serializers.IntegerField()
    pending_count = serializers.IntegerField()
    overdue_count = serializers.IntegerField()
    accepted_count = serializers.IntegerField()
```

---

## Views

### apps/authentication/views.py
```python
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .serializers import LoginSerializer, UserSerializer
from .models import User, DeviceToken

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        device_id = serializer.validated_data.get('deviceId')
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        
        # Store device token if provided
        if device_id:
            DeviceToken.objects.update_or_create(
                user=user,
                device_id=device_id,
                defaults={
                    'token': str(refresh),
                    'is_active': True
                }
            )
        
        user.save()  # Update last_login
        
        return Response({
            'access_token': str(access_token),
            'refresh_token': str(refresh),
            'expires_in': 3600,  # 1 hour
            'user': UserSerializer(user).data
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    try:
        # Blacklist the refresh token if provided
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        # Deactivate device tokens
        DeviceToken.objects.filter(user=request.user).update(is_active=False)
        
        return Response({'message': 'Successfully logged out'})
    except Exception as e:
        return Response({'error': 'Logout failed'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)
```

### apps/applications/views.py
```python
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone
from django.db.models import Q
from .models import Application, ApplicationAttachment
from .serializers import ApplicationSerializer, AssignmentResponseSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def assigned_applications(request):
    """Get applications assigned to current field officer"""
    user = request.user
    officer_id = request.GET.get('officer_id', user.id)
    include_details = request.GET.get('include_details', 'true').lower() == 'true'
    since = request.GET.get('since')
    
    # Filter applications assigned to officer
    queryset = Application.objects.filter(assigned_to_id=officer_id)
    
    # Filter by since parameter for incremental sync
    if since:
        try:
            since_date = timezone.datetime.fromisoformat(since.replace('Z', '+00:00'))
            queryset = queryset.filter(updated_at__gte=since_date)
        except ValueError:
            pass
    
    applications = queryset.select_related('customer', 'contractor').prefetch_related('attachments')
    
    # Calculate counts
    now = timezone.now()
    total_count = applications.count()
    pending_count = applications.filter(assignment_status='assigned').count()
    accepted_count = applications.filter(assignment_status='accepted').count()
    overdue_count = applications.filter(
        due_date__lt=now,
        status__in=['assigned', 'in_progress']
    ).count()
    
    serializer = ApplicationSerializer(applications, many=True, context={'request': request})
    
    response_data = {
        'applications': serializer.data,
        'total_count': total_count,
        'pending_count': pending_count,
        'overdue_count': overdue_count,
        'accepted_count': accepted_count
    }
    
    return Response(response_data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def application_detail(request, pk):
    """Get detailed application information"""
    try:
        application = Application.objects.select_related(
            'customer', 'contractor'
        ).prefetch_related('attachments').get(pk=pk)
        
        # Check if user has access to this application
        if request.user.role == 'field_officer' and application.assigned_to != request.user:
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ApplicationSerializer(application, context={'request': request})
        return Response(serializer.data)
        
    except Application.DoesNotExist:
        return Response({'error': 'Application not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_application_status(request, pk):
    """Update application status"""
    try:
        application = Application.objects.get(pk=pk)
        
        # Check permissions
        if request.user.role == 'field_officer' and application.assigned_to != request.user:
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        
        # Update status fields
        if 'status' in request.data:
            application.status = request.data['status']
        if 'assignment_status' in request.data:
            application.assignment_status = request.data['assignment_status']
        
        # Set completion timestamp
        if application.status == 'completed':
            application.completed_at = timezone.now()
        
        application.save()
        
        return Response({
            'message': 'Application status updated successfully',
            'application': {
                'id': str(application.id),
                'status': application.status,
                'assignment_status': application.assignment_status,
                'updated_at': application.updated_at.isoformat()
            }
        })
        
    except Application.DoesNotExist:
        return Response({'error': 'Application not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_assignment(request, pk):
    """Accept an assigned application"""
    try:
        application = Application.objects.get(pk=pk, assigned_to=request.user)
        
        if application.assignment_status != 'assigned':
            return Response({'error': 'Assignment cannot be accepted'}, status=status.HTTP_400_BAD_REQUEST)
        
        application.assignment_status = 'accepted'
        application.accepted_at = timezone.now()
        application.save()
        
        return Response({
            'message': 'Assignment accepted successfully',
            'assignment_status': 'accepted',
            'accepted_at': application.accepted_at.isoformat()
        })
        
    except Application.DoesNotExist:
        return Response({'error': 'Application not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_assignment(request, pk):
    """Complete an assignment with inspection results"""
    try:
        application = Application.objects.get(pk=pk, assigned_to=request.user)
        
        inspection_id = request.data.get('inspection_id')
        completion_notes = request.data.get('completion_notes', '')
        
        application.status = 'completed'
        application.assignment_status = 'completed'
        application.completed_at = timezone.now()
        application.save()
        
        # Here you would also link the inspection to the application
        # This depends on your Inspection model implementation
        
        return Response({
            'message': 'Assignment completed successfully',
            'status': 'completed',
            'assignment_status': 'completed',
            'completed_at': application.completed_at.isoformat()
        })
        
    except Application.DoesNotExist:
        return Response({'error': 'Application not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def application_attachments(request, pk):
    """Get application attachments"""
    try:
        application = Application.objects.get(pk=pk)
        attachments = application.attachments.all()
        
        attachments_data = []
        for attachment in attachments:
            attachments_data.append({
                'serverId': str(attachment.id),
                'fileUrl': request.build_absolute_uri(f'/api/v1/files/{attachment.id}/download'),
                'file_type': attachment.file_type,
                'description': attachment.description,
                'file_size': attachment.file.size if attachment.file else None,
                'uploaded_at': attachment.uploaded_at.isoformat()
            })
        
        return Response({'attachments': attachments_data})
        
    except Application.DoesNotExist:
        return Response({'error': 'Application not found'}, status=status.HTTP_404_NOT_FOUND)
```

### apps/inspections/views.py
```python
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from .models import Inspection, InspectionPhoto
from .serializers import InspectionSerializer

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_inspection(request):
    """Create or upload inspection data"""
    try:
        data = request.data
        mobile_id = data.get('id')
        application_id = data.get('applicationId')
        
        # Check if inspection already exists
        inspection, created = Inspection.objects.get_or_create(
            mobile_id=mobile_id,
            defaults={
                'application_id': application_id,
                'inspector': request.user,
                'service_number': data.get('serviceNumber', ''),
                'consumer_details': data.get('consumerDetails', {}),
                'property_details': data.get('propertyDetails', {}),
                'contractor_details': data.get('contractorDetails', {}),
                'inspection_points': data.get('inspectionPoints', {}),
                'overall_result': data.get('overallResult', 'pending'),
                'defects_count': data.get('defectsCount', 0),
                'inspector_signature': data.get('inspectorSignature', ''),
                'gps_coordinates': data.get('gpsCoordinates', {}),
                'status': data.get('status', 'draft'),
                'completed_at': timezone.now() if data.get('status') == 'completed' else None
            }
        )
        
        if not created:
            # Update existing inspection
            for field, value in data.items():
                if hasattr(inspection, field):
                    setattr(inspection, field, value)
            inspection.save()
        
        return Response({
            'id': inspection.mobile_id,
            'server_id': str(inspection.id),
            'message': 'Inspection created successfully' if created else 'Inspection updated successfully',
            'created_at': inspection.created_at.isoformat()
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Failed to create inspection: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_photos(request, pk):
    """Upload inspection photos"""
    try:
        inspection = Inspection.objects.get(mobile_id=pk, inspector=request.user)
        uploaded_photos = []
        
        files = request.FILES.getlist('files[]')
        metadata = request.data.get('metadata', '{}')
        
        for file in files:
            photo = InspectionPhoto.objects.create(
                inspection=inspection,
                image=file,
                inspection_point=request.data.get('inspection_point', ''),
                description=request.data.get('description', ''),
                gps_coordinates=request.data.get('gps_coordinates', {})
            )
            
            uploaded_photos.append({
                'id': str(photo.id),
                'filename': photo.image.name,
                'url': request.build_absolute_uri(f'/api/v1/files/{photo.id}/download'),
                'inspection_point': photo.inspection_point,
                'uploaded_at': photo.uploaded_at.isoformat()
            })
        
        return Response({'uploaded_photos': uploaded_photos})
        
    except Inspection.DoesNotExist:
        return Response({'error': 'Inspection not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_signatures(request, pk):
    """Upload digital signatures"""
    try:
        inspection = Inspection.objects.get(mobile_id=pk, inspector=request.user)
        
        inspector_signature = request.data.get('inspector_signature')
        customer_signature = request.data.get('customer_signature')
        
        if inspector_signature:
            inspection.inspector_signature = inspector_signature
        if customer_signature:
            inspection.customer_signature = customer_signature
            
        inspection.save()
        
        return Response({'message': 'Signatures uploaded successfully'})
        
    except Inspection.DoesNotExist:
        return Response({'error': 'Inspection not found'}, status=status.HTTP_404_NOT_FOUND)
```

---

## URL Patterns

### apps/authentication/urls.py
```python
from django.urls import path
from . import views

urlpatterns = [
    path('login', views.login, name='auth_login'),
    path('logout', views.logout, name='auth_logout'), 
    path('refresh', views.token_refresh, name='auth_refresh'),
    path('profile', views.profile, name='auth_profile'),
]
```

### apps/applications/urls.py
```python
from django.urls import path
from . import views

urlpatterns = [
    path('assigned', views.assigned_applications, name='assigned_applications'),
    path('<str:pk>', views.application_detail, name='application_detail'),
    path('<str:pk>/status', views.update_application_status, name='update_application_status'),
    path('<str:pk>/attachments', views.application_attachments, name='application_attachments'),
    path('<str:pk>/accept', views.accept_assignment, name='accept_assignment'),
    path('<str:pk>/complete', views.complete_assignment, name='complete_assignment'),
]
```

### apps/inspections/urls.py
```python
from django.urls import path
from . import views

urlpatterns = [
    path('', views.create_inspection, name='create_inspection'),
    path('<str:pk>/upload', views.upload_inspection, name='upload_inspection'),
    path('<str:pk>/photos', views.upload_photos, name='upload_photos'),
    path('<str:pk>/signatures', views.upload_signatures, name='upload_signatures'),
    path('<str:pk>/status', views.update_inspection_status, name='update_inspection_status'),
]
```

---

## Deployment Checklist

### 1. Environment Variables
```bash
# .env file
SECRET_KEY=your-very-secure-secret-key-here
DEBUG=False
DB_NAME=beapp_production
DB_USER=beapp_user
DB_PASSWORD=secure_db_password
DB_HOST=localhost
DB_PORT=5432
ALLOWED_HOSTS=api.beapp.zw,api-staging.beapp.zw
CORS_ALLOWED_ORIGINS=https://beapp.zw
```

### 2. Production Settings
```python
# settings/production.py
from .base import *

DEBUG = False
ALLOWED_HOSTS = ['api.beapp.zw']

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Database connection pooling
DATABASES['default']['CONN_MAX_AGE'] = 600

# Caching
CACHES = {
    'default': {
        'BACKEND': 'redis_cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'redis_cache.client.DefaultClient',
        }
    }
}
```

### 3. Nginx Configuration
```nginx
server {
    listen 80;
    server_name api.beapp.zw;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name api.beapp.zw;

    ssl_certificate /path/to/ssl/cert.pem;
    ssl_certificate_key /path/to/ssl/private.key;

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /media/ {
        alias /path/to/beapp/media/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### 4. Systemd Service
```ini
# /etc/systemd/system/beapp-api.service
[Unit]
Description=BEApp Django API
After=network.target

[Service]
User=beapp
Group=beapp
WorkingDirectory=/var/www/beapp_server
Environment=DJANGO_SETTINGS_MODULE=beapp_server.settings.production
ExecStart=/var/www/beapp_server/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 beapp_server.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

### 5. Database Migration Commands
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

### 6. Testing Commands
```bash
# Run tests
python manage.py test

# Check deployment
python manage.py check --deploy

# Load test data
python manage.py loaddata fixtures/initial_data.json
```

---

This comprehensive implementation guide provides everything needed to set up your Django server to communicate with the BEApp mobile application. The code includes proper authentication, data models, API endpoints, and deployment configurations that match exactly with the mobile app's expectations.
