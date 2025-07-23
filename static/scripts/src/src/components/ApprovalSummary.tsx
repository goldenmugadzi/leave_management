import React, { useState, useEffect } from 'react';

interface Document {
  cs_id: string;
  committeeMembers?: CommitteeMember[];
  financeManager?: { name: string };
  generalManager?: { name: string };
  committeeApprovalDate?: string;
  committeeJustification?: string;
  fmApproval?: string;
  fmApprovalDate?: string;
  fmJustification?: string;
  gmApproval?: string;
  gmApprovalDate?: string;
  gmJustification?: string;
}

interface CommitteeMember {
  name: string;
  approval: string;
}

interface UserPermissions {
  isApprover: boolean;
  userRole?: string;
  username: string;
  isCreator: boolean;
  canEdit: boolean;
  canDelete: boolean;
  canResubmit: boolean;
}

interface ApprovalSummaryProps {
  document: Document;
  permissions: UserPermissions;
}

interface ApprovalStep {
  name: string;
  status: 'pending' | 'approved' | 'rejected' | 'not_started';
  approvers: string[];
  canApprove: boolean;
  description: string;
  date?: string;
  justification?: string;
}

const ApprovalSummary: React.FC<ApprovalSummaryProps> = ({ 
  document, 
  permissions
}) => {
  const [approvalSteps, setApprovalSteps] = useState<ApprovalStep[]>([]);
  const [currentProgress, setCurrentProgress] = useState(0);
  // const { onApprove } = useScheduleContext();

  useEffect(() => {
    if (document) {
      const steps = buildApprovalSteps(document, permissions);
      setApprovalSteps(steps);
      
      // Calculate progress
      const completedSteps = steps.filter(step => step.status === 'approved').length;
      const totalSteps = steps.length;
      const progress = totalSteps > 0 ? (completedSteps / totalSteps) * 100 : 0;
      setCurrentProgress(progress);
    }
  }, [document, permissions]);

  const buildApprovalSteps = (doc: Document, perms: UserPermissions): ApprovalStep[] => {
    const steps: ApprovalStep[] = [];

    // Committee Step
    steps.push({
      name: 'Component Committee',
      status: getCommitteeStatus(doc),
      approvers: doc.committeeMembers?.map((m: CommitteeMember) => m.name) || [],
      canApprove: perms.isApprover && perms.userRole === 'committee',
      description: 'Technical and operational review by committee members',
      date: doc.committeeApprovalDate,
      justification: doc.committeeJustification
    });

    // Finance Manager Step
    steps.push({
      name: 'Finance Manager',
      status: getFMStatus(doc),
      approvers: doc.financeManager ? [doc.financeManager.name] : [],
      canApprove: perms.isApprover && perms.userRole === 'finance_manager',
      description: 'Financial review and budget validation',
      date: doc.fmApprovalDate,
      justification: doc.fmJustification
    });

    // General Manager Step
    steps.push({
      name: 'General Manager',
      status: getGMStatus(doc),
      approvers: doc.generalManager ? [doc.generalManager.name] : [],
      canApprove: perms.isApprover && perms.userRole === 'general_manager',
      description: 'Final authorization and strategic approval',
      date: doc.gmApprovalDate,
      justification: doc.gmJustification
    });

    return steps;
  };

  const getCommitteeStatus = (doc: Document): 'pending' | 'approved' | 'rejected' | 'not_started' => {
    if (!doc.committeeMembers || doc.committeeMembers.length === 0) {
      return 'not_started';
    }
    
    const approvals = doc.committeeMembers.map((m: CommitteeMember) => m.approval);
    if (approvals.some((a: string) => a === 'Rejected')) {
      return 'rejected';
    }
    if (approvals.every((a: string) => a === 'Approved')) {
      return 'approved';
    }
    return 'pending';
  };

  const getFMStatus = (doc: Document): 'pending' | 'approved' | 'rejected' | 'not_started' => {
    if (!doc.fmApproval) {
      return 'not_started';
    }
    if (doc.fmApproval === 'Rejected') {
      return 'rejected';
    }
    if (doc.fmApproval === 'Approved') {
      return 'approved';
    }
    return 'pending';
  };

  const getGMStatus = (doc: Document): 'pending' | 'approved' | 'rejected' | 'not_started' => {
    if (!doc.gmApproval) {
      return 'not_started';
    }
    if (doc.gmApproval === 'Rejected') {
      return 'rejected';
    }
    if (doc.gmApproval === 'Approved') {
      return 'approved';
    }
    return 'pending';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'rejected':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'approved':
        return (
          <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
        );
      case 'rejected':
        return (
          <svg className="w-5 h-5 text-red-600" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
          </svg>
        );
      case 'pending':
        return (
          <svg className="w-5 h-5 text-yellow-600" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
          </svg>
        );
      default:
        return (
          <svg className="w-5 h-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
          </svg>
        );
    }
  };

  const handleApprove = async (step: ApprovalStep, action: 'approve' | 'reject') => {
    if (!step.canApprove) {
      return;
    }

    const role = step.name === 'Component Committee' ? 'committee' : 
                 step.name === 'Finance Manager' ? 'finance_manager' : 'general_manager';
    
    try {
      // TODO: Implement approval logic
      console.log(`Approving ${role} with action: ${action}`);
      // await onApprove(role, permissions.username, action === 'approve' ? 'Approved' : 'Rejected', '');
    } catch (error) {
      console.error('Approval failed:', error);
    }
  };

  if (!document) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-12 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Approval Summary</h3>
          <p className="text-sm text-gray-600">Document: {document.cs_id}</p>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-blue-600">{Math.round(currentProgress)}%</div>
          <div className="text-sm text-gray-500">Complete</div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-6">
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${currentProgress}%` }}
          ></div>
        </div>
      </div>

      {/* Approval Steps */}
      <div className="space-y-4">
        {approvalSteps.map((step, index) => (
          <div key={index} className="border rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-3">
                <div className={`p-2 rounded-full ${getStatusColor(step.status)}`}>
                  {getStatusIcon(step.status)}
                </div>
                <div>
                  <h4 className="font-medium text-gray-900">{step.name}</h4>
                  <p className="text-sm text-gray-600">{step.description}</p>
                </div>
              </div>
              <div className="text-right">
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(step.status)}`}>
                  {step.status.charAt(0).toUpperCase() + step.status.slice(1)}
                </span>
              </div>
            </div>

            {/* Approvers */}
            {step.approvers.length > 0 && (
              <div className="mb-3">
                <p className="text-sm text-gray-600 mb-1">Approvers:</p>
                <div className="flex flex-wrap gap-2">
                  {step.approvers.map((approver, idx) => (
                    <span key={idx} className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-800">
                      {approver}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Approval Date */}
            {step.date && (
              <div className="mb-3">
                <p className="text-sm text-gray-600">
                  Date: {new Date(step.date).toLocaleDateString()}
                </p>
              </div>
            )}

            {/* Justification */}
            {step.justification && (
              <div className="mb-3">
                <p className="text-sm text-gray-600 mb-1">Justification:</p>
                <p className="text-sm bg-gray-50 p-2 rounded">{step.justification}</p>
              </div>
            )}

            {/* Action Buttons */}
            {step.canApprove && step.status === 'pending' && (
              <div className="flex space-x-2">
                <button
                  onClick={() => handleApprove(step, 'approve')}
                  className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                >
                  <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                  </svg>
                  Approve
                </button>
                <button
                  onClick={() => handleApprove(step, 'reject')}
                  className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                >
                  <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  Reject
                </button>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Creator Actions */}
      {permissions.isCreator && (
        <div className="mt-6 pt-4 border-t border-gray-200">
          <h4 className="font-medium text-gray-900 mb-3">Creator Actions</h4>
          <div className="flex space-x-2">
            {permissions.canEdit && (
              <button className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
                Edit Document
              </button>
            )}
            {permissions.canDelete && (
              <button className="inline-flex items-center px-3 py-2 border border-red-300 shadow-sm text-sm leading-4 font-medium rounded-md text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500">
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                Delete Document
              </button>
            )}
            {permissions.canResubmit && (
              <button className="inline-flex items-center px-3 py-2 border border-blue-300 shadow-sm text-sm leading-4 font-medium rounded-md text-blue-700 bg-white hover:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Resubmit
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ApprovalSummary; 