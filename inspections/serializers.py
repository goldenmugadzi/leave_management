from rest_framework import serializers
from django.utils import timezone
from .models import (
    Customer, Contractor, ApplicationAttachment, ClientApplication, 
    ApplicationAssignment
)


class CustomerCacheSerializer(serializers.ModelSerializer):
    """Serializer for customer data in mobile API responses"""
    serverId = serializers.CharField(source='id', read_only=True)
    customerId = serializers.CharField(source='customer_id', read_only=True)
    fullName = serializers.CharField(source='full_name', read_only=True)
    phone = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    standPlotNumber = serializers.CharField(source='stand_plot_number', read_only=True)
    farmStreetName = serializers.CharField(source='farm_street_name', read_only=True)
    suburbTownship = serializers.CharField(source='suburb_township', read_only=True)
    district = serializers.CharField(read_only=True)
    lastSynced = serializers.DateTimeField(default=timezone.now, read_only=True)
    cacheExpires = serializers.SerializerMethodField()
    isActive = serializers.BooleanField(default=True, read_only=True)

    class Meta:
        model = Customer
        fields = [
            'serverId', 'customerId', 'fullName', 'phone', 'email',
            'standPlotNumber', 'farmStreetName', 'suburbTownship', 'district',
            'lastSynced', 'cacheExpires', 'isActive'
        ]

    def get_cacheExpires(self, obj):
        """Calculate cache expiration (24 hours from now)"""
        return timezone.now() + timezone.timedelta(hours=24)


class ContractorCacheSerializer(serializers.ModelSerializer):
    """Serializer for contractor data in mobile API responses"""
    serverId = serializers.CharField(source='id', read_only=True)
    contractorId = serializers.CharField(source='contractor_id', read_only=True)
    businessName = serializers.CharField(source='business_name', read_only=True)
    contactPerson = serializers.CharField(source='contact_person', read_only=True)
    phone = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    address = serializers.CharField(read_only=True)
    licenseNumber = serializers.CharField(source='license_number', read_only=True)
    businessRegistration = serializers.CharField(source='business_registration', read_only=True)
    lastSynced = serializers.DateTimeField(default=timezone.now, read_only=True)
    cacheExpires = serializers.SerializerMethodField()
    isActive = serializers.BooleanField(default=True, read_only=True)

    class Meta:
        model = Contractor
        fields = [
            'serverId', 'contractorId', 'businessName', 'contactPerson', 'phone', 'email',
            'address', 'licenseNumber', 'businessRegistration',
            'lastSynced', 'cacheExpires', 'isActive'
        ]

    def get_cacheExpires(self, obj):
        """Calculate cache expiration (24 hours from now)"""
        return timezone.now() + timezone.timedelta(hours=24)


class ApplicationAttachmentCacheSerializer(serializers.ModelSerializer):
    """Serializer for application attachments in mobile API responses"""
    serverId = serializers.CharField(source='id', read_only=True)
    applicationServerId = serializers.CharField(source='application_id', read_only=True)
    fileUrl = serializers.SerializerMethodField()
    fileType = serializers.CharField(source='file_type', read_only=True)
    description = serializers.CharField(read_only=True)
    fileSize = serializers.SerializerMethodField()
    uploadedAt = serializers.DateTimeField(source='uploaded_at', read_only=True)
    isCached = serializers.BooleanField(default=False, read_only=True)

    class Meta:
        model = ApplicationAttachment
        fields = [
            'serverId', 'applicationServerId', 'fileUrl', 'fileType', 'description',
            'fileSize', 'uploadedAt', 'isCached'
        ]

    def get_fileUrl(self, obj):
        """Generate file download URL"""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None

    def get_fileSize(self, obj):
        """Get file size in bytes"""
        if obj.file:
            try:
                return obj.file.size
            except (OSError, ValueError):
                return None
        return None


class ServerApplicationResponseSerializer(serializers.ModelSerializer):
    """Main serializer for application data in mobile API responses"""
    id = serializers.CharField(read_only=True)
    applicationNumber = serializers.CharField(source='application_number', read_only=True)
    applicationType = serializers.CharField(source='application_type', read_only=True)
    priority = serializers.CharField(read_only=True)
    customer = CustomerCacheSerializer(read_only=True)
    contractor = ContractorCacheSerializer(read_only=True)
    attachments = ApplicationAttachmentCacheSerializer(many=True, read_only=True)
    purpose = serializers.CharField(read_only=True)
    supplyType = serializers.CharField(source='supply_type', read_only=True)
    status = serializers.CharField(read_only=True)
    assignmentStatus = serializers.SerializerMethodField()
    assignedTo = serializers.SerializerMethodField()
    dueDate = serializers.SerializerMethodField()
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = ClientApplication
        fields = [
            'id', 'applicationNumber', 'applicationType', 'priority',
            'customer', 'contractor', 'attachments', 'purpose', 'supplyType',
            'status', 'assignmentStatus', 'assignedTo', 'dueDate',
            'createdAt', 'updatedAt'
        ]

    def get_assignmentStatus(self, obj):
        """Get assignment status from the most recent assignment"""
        assignment = obj.assignments.filter(assigned_to=self.context.get('user')).first()
        if assignment:
            return assignment.status
        return 'assigned'  # Default if no assignment found

    def get_assignedTo(self, obj):
        """Get assigned user ID"""
        assignment = obj.assignments.filter(assigned_to=self.context.get('user')).first()
        if assignment:
            return str(assignment.assigned_to.id)
        return None

    def get_dueDate(self, obj):
        """Get due date from the most recent assignment"""
        assignment = obj.assignments.filter(assigned_to=self.context.get('user')).first()
        if assignment and assignment.due_date:
            return assignment.due_date.isoformat()
        return None


class AssignmentResponseSerializer(serializers.Serializer):
    """Serializer for the main assignment response"""
    applications = ServerApplicationResponseSerializer(many=True)
    totalCount = serializers.IntegerField()
    pendingCount = serializers.IntegerField()
    overdueCount = serializers.IntegerField()
    acceptedCount = serializers.IntegerField()


class ApplicationDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed application view"""
    id = serializers.CharField(source='id', read_only=True)
    applicationNumber = serializers.CharField(source='application_number', read_only=True)
    applicationType = serializers.CharField(source='application_type', read_only=True)
    priority = serializers.CharField(read_only=True)
    customer = CustomerCacheSerializer(read_only=True)
    contractor = ContractorCacheSerializer(read_only=True)
    attachments = ApplicationAttachmentCacheSerializer(many=True, read_only=True)
    purpose = serializers.CharField(read_only=True)
    supplyType = serializers.CharField(source='supply_type', read_only=True)
    status = serializers.CharField(read_only=True)
    assignmentStatus = serializers.SerializerMethodField()
    assignedTo = serializers.SerializerMethodField()
    dueDate = serializers.SerializerMethodField()
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)
    additionalDetails = serializers.SerializerMethodField()

    class Meta:
        model = ClientApplication
        fields = [
            'id', 'applicationNumber', 'applicationType', 'priority',
            'customer', 'contractor', 'attachments', 'purpose', 'supplyType',
            'status', 'assignmentStatus', 'assignedTo', 'dueDate',
            'createdAt', 'updatedAt', 'additionalDetails'
        ]

    def get_assignmentStatus(self, obj):
        """Get assignment status from the most recent assignment"""
        assignment = obj.assignments.filter(assigned_to=self.context.get('user')).first()
        if assignment:
            return assignment.status
        return 'assigned'

    def get_assignedTo(self, obj):
        """Get assigned user ID"""
        assignment = obj.assignments.filter(assigned_to=self.context.get('user')).first()
        if assignment:
            return str(assignment.assigned_to.id)
        return None

    def get_dueDate(self, obj):
        """Get due date from the most recent assignment"""
        assignment = obj.assignments.filter(assigned_to=self.context.get('user')).first()
        if assignment and assignment.due_date:
            return assignment.due_date.isoformat()
        return None

    def get_additionalDetails(self, obj):
        """Get additional installation details"""
        return {
            'installation_address': f"{obj.customer.stand_plot_number or ''} {obj.customer.farm_street_name or ''}, {obj.customer.suburb_township or ''}".strip(),
            'meter_type': 'Single Phase' if obj.single_phase_required else 'Three Phase',
            'load_requirement': f"{obj.main_switch_size_kva or 0} kVA",
            'special_instructions': obj.notes or ''
        }


class AcceptAssignmentSerializer(serializers.Serializer):
    """Serializer for accepting an assignment"""
    officer_id = serializers.CharField(required=False)
    accepted_at = serializers.DateTimeField(default=timezone.now)
    estimated_completion = serializers.DateTimeField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True)


class UpdateStatusSerializer(serializers.Serializer):
    """Serializer for updating assignment status"""
    assignment_status = serializers.ChoiceField(choices=[
        'assigned', 'accepted', 'in_progress', 'completed'
    ])
    status = serializers.ChoiceField(choices=[
        'submitted', 'assigned', 'in_progress', 'completed', 'rejected'
    ])
    officer_id = serializers.CharField(required=False)
    updated_at = serializers.DateTimeField(default=timezone.now)
    notes = serializers.CharField(required=False, allow_blank=True)
    location = serializers.DictField(required=False)


class CompleteAssignmentSerializer(serializers.Serializer):
    """Serializer for completing an assignment"""
    officer_id = serializers.CharField(required=False)
    completed_at = serializers.DateTimeField(default=timezone.now)
    inspection_result = serializers.ChoiceField(choices=['passed', 'failed'])
    inspection_id = serializers.CharField(required=False)
    completion_notes = serializers.CharField(required=False, allow_blank=True)
    photos_uploaded = serializers.BooleanField(default=False)
    documents_uploaded = serializers.BooleanField(default=False)
