from rest_framework import serializers
from .models import Token

class TokenSerializer(serializers.ModelSerializer):
    meter = serializers.SerializerMethodField()
    customer = serializers.SerializerMethodField()
    cost_center = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    process_status = serializers.SerializerMethodField()

    class Meta:
        model = Token
        exclude = ['additional_attachments']

    def get_meter(self, obj):
        return str(obj.meter) if obj.meter else None

    def get_customer(self, obj):
        return str(obj.customer) if obj.customer else None

    def get_cost_center(self, obj):
        return str(obj.cost_center) if obj.cost_center else None

    def get_created_by(self, obj):
        return str(obj.created_by) if obj.created_by else None

    def get_process_status(self, obj):
        # Show the latest approval step and status if process exists
        if obj.process and hasattr(obj.process, 'approval_set'):
            last_approval = obj.process.approval_set.order_by('-id').first()
            if last_approval:
                return {
                    "step": str(last_approval.step),
                    "status": last_approval.approved,
                    "remarks": last_approval.remarks,
                    "updated_at": last_approval.updated_at if hasattr(last_approval, 'updated_at') else None
                }
            return "No approvals yet"
        return "No process"