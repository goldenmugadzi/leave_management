from rest_framework import serializers
from django.contrib.auth import get_user_model
from it.users.models import UserProfile, Roles, Sections, Regions, CostCenter
from approve.models import Process, Step, Approval
from .models import Ace2, AssetBudget, Quotation, Transactions, Asset_budget_Virament

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'section', 'region', 'roles']
        
    def get_roles(self, obj):
        roles = {}
        for role in obj.roles.all():
            if role.application not in roles:
                roles[role.application] = role.role
        return roles

class SectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sections
        fields = ['id', 'section', 'code']

class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Regions
        fields = ['id', 'region', 'code']

class QuotationSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Quotation
        fields = ['id', 'quotation_file', 'file_url']
        
    def get_file_url(self, obj):
        if obj.quotation_file:
            return self.context['request'].build_absolute_uri(obj.quotation_file.url)
        return None

class AssetBudgetSerializer(serializers.ModelSerializer):
    section_name = serializers.SerializerMethodField()
    region_name = serializers.SerializerMethodField()
    cost_center_code = serializers.SerializerMethodField()
    
    class Meta:
        model = AssetBudget
        fields = ['budget_id', 'section_code', 'section_name', 'budget_name', 'allocated', 
              'withdrawn', 'balance', 'awaiting_sanctioning', 'period', 'region_name', 'cost_center_code']
    
    def get_section_name(self, obj):
        return obj.section if obj.section else ""
    
    def get_region_name(self, obj):
        return obj.region.region if obj.region else ""
    
    def get_cost_center_code(self, obj):
        return obj.cost_center.code if getattr(obj, 'cost_center', None) else ""

class ApprovalSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    step_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Approval
        fields = ['id', 'step', 'step_name', 'user', 'user_name', 'approved', 'approved_at', 'comment']
        
    def get_user_name(self, obj):
        return obj.user.get_full_name() if obj.user else ""
    
    def get_step_name(self, obj):
        return obj.step.to

class AceSerializer(serializers.ModelSerializer):
    requested_by_name = serializers.SerializerMethodField()
    section_name = serializers.SerializerMethodField()
    region_name = serializers.SerializerMethodField()
    budget_name = serializers.SerializerMethodField()
    approval_status = serializers.SerializerMethodField()
    quotations = QuotationSerializer(source='quotation_set', many=True, read_only=True)
    approvals = serializers.SerializerMethodField()
    cost_center_code = serializers.SerializerMethodField()
    
    class Meta:
        model = Ace2
        fields = ['Ace_id2', 'details_of_expenditure', 'amount', 'requested_by', 'requested_by_name',
                  'section', 'section_name', 'region_name', 'date_created', 'budget_id', 'budget_name',
                  'classification', 'approval_status', 'quotations', 'approvals', 'asset_number',
              'currency', 'quantity', 'cost_center_code']
    
    def get_requested_by_name(self, obj):
        return obj.requested_by.get_full_name() if obj.requested_by else ""
    
    def get_section_name(self, obj):
        return obj.section.section if obj.section else ""
    
    def get_region_name(self, obj):
        return obj.region.region if obj.region else ""
    
    def get_budget_name(self, obj):
        return obj.budget_id.budget_name if obj.budget_id else ""
    
    def get_approval_status(self, obj):
        if obj.process and obj.process.approval_set.exists():
            last_approval = obj.process.approval_set.last()
            return last_approval.approved
        return "Pending"
    
    def get_approvals(self, obj):
        if obj.process and obj.process.approval_set.exists():
            approvals = obj.process.approval_set.all()
            return ApprovalSerializer(approvals, many=True).data
        return []
    
    def get_cost_center_code(self, obj):
        return obj.cost_center.code if getattr(obj, 'cost_center', None) else ""

class TransactionSerializer(serializers.ModelSerializer):
    budget_name = serializers.SerializerMethodField()
    section_name = serializers.SerializerMethodField()
    region_name = serializers.SerializerMethodField()
    ace_id = serializers.SerializerMethodField()
    cost_center_code = serializers.SerializerMethodField()
    
    class Meta:
        model = Transactions
        fields = ['id', 'Ace_id2', 'ace_id', 'details_of_expenditure', 'approval_status', 
              'region', 'region_name', 'amount', 'budget', 'budget_name', 'section', 'section_name', 'cost_center_code']
    
    def get_budget_name(self, obj):
        return obj.budget.budget_name if obj.budget else ""
    
    def get_section_name(self, obj):
        return obj.section.section if obj.section else ""
    
    def get_region_name(self, obj):
        return obj.region.region if obj.region else ""
    
    def get_ace_id(self, obj):
        return obj.Ace_id2.Ace_id2 if obj.Ace_id2 else ""
    
    def get_cost_center_code(self, obj):
        return obj.cost_center.code if getattr(obj, 'cost_center', None) else ""

class ViramentSerializer(serializers.ModelSerializer):
    requested_by_name = serializers.SerializerMethodField()
    section_name = serializers.SerializerMethodField()
    from_budget_name = serializers.SerializerMethodField()
    to_budget_name = serializers.SerializerMethodField()
    approval_status = serializers.SerializerMethodField()
    cost_center_code = serializers.SerializerMethodField()
    
    class Meta:
        model = Asset_budget_Virament
        fields = ['virament_id', 'from_budget', 'from_budget_name', 'to_budget', 'to_budget_name',
                  'amount', 'reason', 'date_created', 'requested_by', 'requested_by_name',
              'section', 'section_name', 'approval_status', 'cost_center_code']
    
    def get_requested_by_name(self, obj):
        return obj.requested_by.get_full_name() if obj.requested_by else ""
    
    def get_section_name(self, obj):
        return obj.section.section if obj.section else ""
    
    def get_from_budget_name(self, obj):
        return obj.from_budget.budget_name if obj.from_budget else ""
    
    def get_to_budget_name(self, obj):
        return obj.to_budget.budget_name if obj.to_budget else ""
    
    def get_approval_status(self, obj):
        if obj.process and obj.process.approval_set.exists():
            last_approval = obj.process.approval_set.last()
            return last_approval.approved
        return "Pending"
    
    def get_cost_center_code(self, obj):
        return obj.cost_center.code if getattr(obj, 'cost_center', None) else ""
