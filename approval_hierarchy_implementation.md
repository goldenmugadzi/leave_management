# Approval Hierarchy Implementation Guide

## Overview
This document outlines the implementation of a three-tier approval hierarchy with proper creator/viewer permissions for the BEII system.

## Hierarchy Structure

### 1. Component Committee Level
- **Purpose**: Technical and operational review
- **Participants**: Multiple committee members
- **Requirement**: All members must approve
- **Status Options**: Approved, Rejected, Pending

### 2. Finance Manager Level
- **Purpose**: Financial review and budget validation
- **Prerequisite**: All committee approvals complete
- **Status Options**: Approved, Rejected, Pending

### 3. General Manager Level
- **Purpose**: Final authorization and strategic approval
- **Prerequisite**: Finance Manager approval complete
- **Status Options**: Approved, Rejected, Pending

## Permission Model

### Creator Permissions
- **View**: Full access to all data and approval status
- **Edit**: Can modify document content, committee members, and basic information
- **Approve**: Cannot approve their own documents (conflict of interest)
- **Delete**: Can delete documents before any approvals
- **Resubmit**: Can resubmit rejected documents

### Viewer Permissions
- **View**: Read-only access to all data and approval status
- **Edit**: No editing capabilities
- **Approve**: No approval capabilities
- **Delete**: No deletion capabilities

### Approver Permissions
- **View**: Full access to document content and approval history
- **Edit**: Cannot edit document content (maintains integrity)
- **Approve**: Can approve/reject based on their role in hierarchy
- **Comment**: Can add justification for approval decisions

## Implementation Strategy

### 1. Backend Changes

#### User Permission Helper
```python
def get_user_permissions(user, document):
    """
    Determine user permissions for a specific document
    """
    permissions = {
        'can_view': True,
        'can_edit': False,
        'can_approve': False,
        'can_delete': False,
        'can_resubmit': False,
        'user_role': None,
        'is_creator': False,
        'is_approver': False
    }
    
    # Check if user is creator
    if document.created_by == user:
        permissions['is_creator'] = True
        permissions['can_edit'] = True
        permissions['can_delete'] = document.can_be_deleted()
        permissions['can_resubmit'] = document.can_be_resubmitted()
    
    # Check if user is an approver
    user_role = get_user_approval_role(user, document)
    if user_role:
        permissions['is_approver'] = True
        permissions['can_approve'] = user_role.can_approve_now(document)
        permissions['user_role'] = user_role
    
    return permissions

def get_user_approval_role(user, document):
    """
    Get user's role in the approval hierarchy for this document
    """
    # Check committee membership
    committee_member = document.get_committee_member(user)
    if committee_member:
        return ApprovalRole.COMMITTEE
    
    # Check finance manager role
    if user.has_role('Finance Manager', document.application):
        return ApprovalRole.FINANCE_MANAGER
    
    # Check general manager role
    if user.has_role('General Manager', document.application):
        return ApprovalRole.GENERAL_MANAGER
    
    return None
```

#### Document Status Management
```python
class DocumentStatus:
    DRAFT = 'draft'
    COMMITTEE_PENDING = 'committee_pending'
    COMMITTEE_APPROVED = 'committee_approved'
    COMMITTEE_REJECTED = 'committee_rejected'
    FM_PENDING = 'fm_pending'
    FM_APPROVED = 'fm_approved'
    FM_REJECTED = 'fm_rejected'
    GM_PENDING = 'gm_pending'
    GM_APPROVED = 'gm_approved'
    GM_REJECTED = 'gm_rejected'
    COMPLETED = 'completed'

def update_document_status(document):
    """
    Update document status based on current approvals
    """
    committee_status = document.get_committee_status()
    fm_status = document.get_fm_approval_status()
    gm_status = document.get_gm_approval_status()
    
    if committee_status == 'rejected':
        document.status = DocumentStatus.COMMITTEE_REJECTED
    elif committee_status == 'pending':
        document.status = DocumentStatus.COMMITTEE_PENDING
    elif committee_status == 'approved':
        if fm_status == 'rejected':
            document.status = DocumentStatus.FM_REJECTED
        elif fm_status == 'pending':
            document.status = DocumentStatus.FM_PENDING
        elif fm_status == 'approved':
            if gm_status == 'rejected':
                document.status = DocumentStatus.GM_REJECTED
            elif gm_status == 'pending':
                document.status = DocumentStatus.GM_PENDING
            elif gm_status == 'approved':
                document.status = DocumentStatus.COMPLETED
    
    document.save()
```

### 2. Frontend Changes

#### Permission-Aware Components
```typescript
interface UserPermissions {
  canView: boolean;
  canEdit: boolean;
  canApprove: boolean;
  canDelete: boolean;
  canResubmit: boolean;
  userRole: string | null;
  isCreator: boolean;
  isApprover: boolean;
}

const useDocumentPermissions = (documentId: string) => {
  const [permissions, setPermissions] = useState<UserPermissions | null>(null);
  
  useEffect(() => {
    fetchUserPermissions(documentId).then(setPermissions);
  }, [documentId]);
  
  return permissions;
};

const DocumentView = ({ documentId }: { documentId: string }) => {
  const permissions = useDocumentPermissions(documentId);
  const [document, setDocument] = useState(null);
  
  if (!permissions?.canView) {
    return <AccessDenied />;
  }
  
  return (
    <div>
      {/* Document content */}
      <DocumentContent 
        document={document} 
        readOnly={!permissions.canEdit}
      />
      
      {/* Approval section */}
      <ApprovalSection 
        document={document}
        permissions={permissions}
      />
      
      {/* Action buttons */}
      <ActionButtons 
        permissions={permissions}
        document={document}
      />
    </div>
  );
};
```

#### Approval Workflow Component
```typescript
const ApprovalWorkflow = ({ document, permissions }: ApprovalWorkflowProps) => {
  const [currentStep, setCurrentStep] = useState(0);
  
  const approvalSteps = [
    {
      name: 'Committee Review',
      status: document.committeeStatus,
      approvers: document.committeeMembers,
      canApprove: permissions.isApprover && permissions.userRole === 'committee'
    },
    {
      name: 'Finance Manager',
      status: document.fmStatus,
      approvers: [document.financeManager],
      canApprove: permissions.isApprover && permissions.userRole === 'finance_manager'
    },
    {
      name: 'General Manager',
      status: document.gmStatus,
      approvers: [document.generalManager],
      canApprove: permissions.isApprover && permissions.userRole === 'general_manager'
    }
  ];
  
  return (
    <div className="approval-workflow">
      {approvalSteps.map((step, index) => (
        <ApprovalStep
          key={index}
          step={step}
          isActive={index === currentStep}
          canInteract={step.canApprove}
        />
      ))}
    </div>
  );
};
```

### 3. API Endpoints

#### Get User Permissions
```python
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_permissions(request, document_id):
    """
    Get user permissions for a specific document
    """
    try:
        document = get_document_by_id(document_id)
        permissions = get_user_permissions(request.user, document)
        
        return Response({
            'success': True,
            'permissions': permissions
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=400)
```

#### Update Document
```python
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_document(request, document_id):
    """
    Update document (creators only)
    """
    try:
        document = get_document_by_id(document_id)
        permissions = get_user_permissions(request.user, document)
        
        if not permissions['can_edit']:
            return Response({
                'success': False,
                'error': 'You do not have permission to edit this document'
            }, status=403)
        
        # Update document logic
        serializer = DocumentSerializer(document, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'document': serializer.data
            })
        else:
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=400)
            
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=400)
```

## Approval Summary Component

### Features
1. **Real-time Status**: Shows current approval stage
2. **Progress Indicator**: Visual representation of approval progress
3. **Approval History**: Complete audit trail
4. **Next Actions**: Clear indication of what happens next
5. **Permission-Based Actions**: Only show actions user can perform

### Implementation
```typescript
const ApprovalSummary = ({ document, permissions }: ApprovalSummaryProps) => {
  const approvalProgress = calculateApprovalProgress(document);
  
  return (
    <div className="approval-summary">
      {/* Progress Bar */}
      <ProgressBar progress={approvalProgress.percentage} />
      
      {/* Current Status */}
      <StatusBadge status={document.status} />
      
      {/* Approval Timeline */}
      <ApprovalTimeline approvals={document.approvals} />
      
      {/* Next Actions */}
      {permissions.canApprove && (
        <ApprovalActions 
          document={document}
          userRole={permissions.userRole}
        />
      )}
      
      {/* Creator Actions */}
      {permissions.isCreator && (
        <CreatorActions 
          document={document}
          permissions={permissions}
        />
      )}
    </div>
  );
};
```

## Security Considerations

### 1. Server-Side Validation
- Always validate permissions on the server
- Never trust client-side permission checks
- Use Django's permission system

### 2. Audit Trail
- Log all approval actions
- Track who made changes and when
- Maintain approval history

### 3. Data Integrity
- Prevent approvers from editing document content
- Maintain approval chain integrity
- Validate approval prerequisites

## Testing Strategy

### 1. Unit Tests
- Test permission logic
- Test approval workflow
- Test status transitions

### 2. Integration Tests
- Test complete approval flow
- Test permission enforcement
- Test API endpoints

### 3. User Acceptance Tests
- Test creator workflow
- Test viewer workflow
- Test approver workflow

## Migration Plan

### Phase 1: Backend Implementation
1. Implement permission helpers
2. Update models with status fields
3. Create API endpoints
4. Add audit logging

### Phase 2: Frontend Implementation
1. Create permission-aware components
2. Implement approval workflow UI
3. Add approval summary component
4. Update existing views

### Phase 3: Testing & Deployment
1. Comprehensive testing
2. User training
3. Gradual rollout
4. Monitoring and feedback

## Conclusion

This implementation provides:
- Clear separation between creator and viewer permissions
- Robust approval hierarchy
- Comprehensive audit trail
- Secure permission enforcement
- Scalable architecture

The system ensures that creators have full control over their documents while maintaining the integrity of the approval process through proper role-based access control. 