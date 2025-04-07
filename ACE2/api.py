from rest_framework import viewsets, permissions, status, generics, filters
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend

from .models import Ace2, AssetBudget, Quotation, Transactions, Asset_budget_Virament
from approve.models import Process, Step, Approval
from it.users.models import UserProfile, Roles, Sections, Regions
from .serializers import (UserSerializer, AceSerializer, AssetBudgetSerializer, 
                         QuotationSerializer, TransactionSerializer, ViramentSerializer,
                         ApprovalSerializer, SectionSerializer, RegionSerializer)
from approve.views import intiate
from .views import approve_step

# Authentication endpoints
class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        user_serializer = UserSerializer(user)
        return Response({
            'token': token.key,
            'user': user_serializer.data
        })

@api_view(['POST'])
def api_logout(request):
    if request.user.is_authenticated:
        request.user.auth_token.delete()
        logout(request)
        return Response({"message": "Successfully logged out"}, status=status.HTTP_200_OK)
    return Response({"error": "You are not logged in"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def current_user(request):
    user = request.user
    serializer = UserSerializer(user)
    return Response(serializer.data)

# Data retrieval endpoints
class AceViewSet(viewsets.ModelViewSet):
    queryset = Ace2.objects.all()
    serializer_class = AceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['section', 'region', 'budget_id', 'classification']
    search_fields = ['Ace_id2', 'details_of_expenditure']
    ordering_fields = ['date_created', 'amount']
    
    def get_queryset(self):
        user = self.request.user
        # Get user's role for ACE application
        user_role = None
        for role in user.roles.all():
            if role.application == "ace":
                user_role = role.role
                break
        
        # Filter ACEs based on user role
        if user_role == "create":
            # Requestors see only their own ACEs
            return Ace2.objects.filter(requested_by=user)
        elif user_role == "pass":
            # Section heads see ACEs from their section
            return Ace2.objects.filter(section=user.section)
        else:
            # Other roles see ACEs from their region
            return Ace2.objects.filter(region=user.region)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        ace = self.get_object()
        comment = request.data.get('comment', '')
        
        # Check if the user can approve this ACE
        process = ace.process
        if process:
            if process.approval_set.exists():
                last_approval = process.approval_set.last()
                current_step = last_approval.step.step
                next_step = current_step + 1
            else:
                next_step = 1
                
            workflow = process.workflow
            try:
                step = Step.objects.get(step=next_step, workflow=workflow, 
                                      approver__in=request.user.roles.all())
                if approve_step(process.id, request.user.username, None):
                    # If this was the last approval, update budget
                    if next_step == len(workflow.step_set.all()):
                        transaction = Transactions.objects.filter(Ace_id2=ace).first()
                        if transaction:
                            transaction.approval_status = "approved by General Manager"
                            transaction.save()
                            
                            budget = ace.budget_id
                            if budget:
                                budget.balance = budget.balance - ace.amount
                                budget.withdrawn = budget.withdrawn + ace.amount
                                budget.to_be_withdrawn = budget.to_be_withdrawn - ace.amount
                                budget.save()
                    
                    return Response({'status': 'ACE request approved'})
                return Response({'error': 'Failed to approve'}, status=status.HTTP_400_BAD_REQUEST)
            except Step.DoesNotExist:
                return Response({'error': 'You are not authorized to approve this request'}, 
                              status=status.HTTP_403_FORBIDDEN)
        return Response({'error': 'No workflow process found'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        ace = self.get_object()
        comment = request.data.get('comment', '')
        
        # Similar logic to approve, but with rejection
        process = ace.process
        if process:
            if process.approval_set.exists():
                last_approval = process.approval_set.last()
                current_step = last_approval.step.step
                next_step = current_step + 1
            else:
                next_step = 1
                
            workflow = process.workflow
            try:
                step = Step.objects.get(step=next_step, workflow=workflow, 
                                      approver__in=request.user.roles.all())
                
                # Create a rejection approval
                approval = Approval(
                    step=step,
                    user=request.user,
                    process=process,
                    approved='Rejected',
                    comment=comment
                )
                approval.save()
                
                # If there was a budget allocation, release it
                budget = ace.budget_id
                if budget:
                    budget.to_be_withdrawn = budget.to_be_withdrawn - ace.amount
                    budget.save()
                
                return Response({'status': 'ACE request rejected'})
            except Step.DoesNotExist:
                return Response({'error': 'You are not authorized to reject this request'}, 
                              status=status.HTTP_403_FORBIDDEN)
        return Response({'error': 'No workflow process found'}, status=status.HTTP_400_BAD_REQUEST)

class BudgetViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AssetBudget.objects.all()
    serializer_class = AssetBudgetSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['section', 'region', 'period']
    search_fields = ['budget_name']
    
    def get_queryset(self):
        user = self.request.user
        return AssetBudget.objects.filter(region=user.region)
    
    @action(detail=True)
    def transactions(self, request, pk=None):
        budget = self.get_object()
        transactions = Transactions.objects.filter(budget=budget)
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)

class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Transactions.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['budget', 'section', 'region', 'approval_status']
    
    def get_queryset(self):
        user = self.request.user
        return Transactions.objects.filter(region=user.region)

class ViramentViewSet(viewsets.ModelViewSet):
    queryset = Asset_budget_Virament.objects.all()
    serializer_class = ViramentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['section', 'from_budget', 'to_budget']
    
    def get_queryset(self):
        user = self.request.user
        user_role = None
        for role in user.roles.all():
            if role.application == "virement":
                user_role = role.role
                break
        
        if user_role == "create":
            return Asset_budget_Virament.objects.filter(requested_by=user)
        elif user_role == "pass":
            return Asset_budget_Virament.objects.filter(section=user.section)
        else:
            return Asset_budget_Virament.objects.filter(region=user.region)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        virament = self.get_object()
        comment = request.data.get('comment', '')
        
        # Similar logic to ACE approval
        process = virament.process
        if process:
            # Process approval...
            if process.approval_set.exists():
                last_approval = process.approval_set.last()
                current_step = last_approval.step.step
                next_step = current_step + 1
            else:
                next_step = 1
                
            workflow = process.workflow
            try:
                step = Step.objects.get(step=next_step, workflow=workflow, 
                                      approver__in=request.user.roles.all())
                
                if approve_step(process.id, request.user.username, None):
                    # If this was the last approval, update budgets
                    if next_step == len(workflow.step_set.all()):
                        from_budget = virament.from_budget
                        to_budget = virament.to_budget
                        
                        # Update the budgets
                        from_budget.balance = from_budget.balance - virament.amount
                        from_budget.withdrawn = from_budget.withdrawn + virament.amount
                        from_budget.save()
                        
                        to_budget.balance = to_budget.balance + virament.amount
                        to_budget.allocated = to_budget.allocated + virament.amount
                        to_budget.save()
                        
                        # Update transaction
                        transaction = Transactions.objects.filter(virament=virament).first()
                        if transaction:
                            transaction.approval_status = "approved by General Manager"
                            transaction.save()
                    
                    return Response({'status': 'Virament approved'})
                return Response({'error': 'Failed to approve'}, status=status.HTTP_400_BAD_REQUEST)
            except Step.DoesNotExist:
                return Response({'error': 'You are not authorized to approve this request'}, 
                              status=status.HTTP_403_FORBIDDEN)
        return Response({'error': 'No workflow process found'}, status=status.HTTP_400_BAD_REQUEST)

# Support API endpoints
class SectionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Sections.objects.all()
    serializer_class = SectionSerializer
    permission_classes = [permissions.IsAuthenticated]

class RegionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Regions.objects.all()
    serializer_class = RegionSerializer
    permission_classes = [permissions.IsAuthenticated]

# My actioned items API endpoint
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def my_actioned_items(request):
    user = request.user
    region = user.region
    
    actioned_aces = []
    all_aces = Ace2.objects.filter(region=region)
    
    for ace in all_aces:
        process = ace.process
        if process and process.approval_set.exists():
            for approval in process.approval_set.all():
                if approval.user == user:
                    actioned_aces.append(ace)
                    break
    
    serializer = AceSerializer(actioned_aces, many=True, context={'request': request})
    return Response(serializer.data)
