import React, { useState, useEffect } from 'react';

interface ICommittee {
  memberUserName: string;
  memberName: string;
  memberPosition?: string;
  committeeStatus?: string;
  memberApproval?: string;
  committeeJustification?: string;
  committeeDate?: string;
}

interface IGmApproval {
  id: number;
  approver_name: string;
  approval: string;
  approval_date: string;
  justification: string;
}

interface IFmApproval {
  id: number;
  approver_name: string;
  approval: string;
  approval_date: string;
  justification: string;
}

interface ICurrentApprover {
  username?: string;
  justification?: string;
  role?: string;
  approval?: string;
}

interface ApprovalTableProps {
  csId: string;
  username: string;
  committeeMembers: ICommittee[];
  gmApproval: IGmApproval | null | undefined;
  fmApproval: IFmApproval | null | undefined;
  isCreator: boolean;
  onApprove: (role: string, username: string, approval: string, justification: string) => Promise<void>;
  currentUserRoles?: {
    fm_role: boolean;
    gm_role: boolean;
    procurement_role: boolean;
  };
}

interface ApprovalRow {
  id: string;
  role: string;
  roleDisplay: string;
  approver: string;
  approverName: string;
  status: 'pending' | 'approved' | 'rejected' | 'not_started';
  date?: string;
  justification?: string;
  canApprove: boolean;
  isCommittee: boolean;
  committeeMembers?: ICommittee[];
  memberUserName?: string; // For individual committee members
  memberPosition?: string; // For individual committee members
}

const ApprovalTable: React.FC<ApprovalTableProps> = ({
  csId,
  username,
  committeeMembers,
  gmApproval,
  fmApproval,
  isCreator,
  onApprove,
  currentUserRoles
}) => {
  const [loading, setLoading] = useState(true);
  const [currentApprover, setCurrentApprover] = useState<ICurrentApprover | null>(null);
  const [approvalModal, setApprovalModal] = useState(false);
  const [justification, setJustification] = useState('');
  const [approvalAction, setApprovalAction] = useState<'approve' | 'reject'>('approve');

  // Set loading to false since we don't need to fetch users for this component
  useEffect(() => {
    setLoading(false);
  }, []);

  // Build approval rows
  const buildApprovalRows = (): ApprovalRow[] => {
    const rows: ApprovalRow[] = [];



    // Add individual committee member rows
    if (committeeMembers.length > 0) {
      committeeMembers.forEach((member) => {
        const memberStatus = member.memberApproval === 'Approved' ? 'approved' : 
                           member.memberApproval === 'Rejected' ? 'rejected' : 'pending';
        
        rows.push({
          id: `committee_${member.memberUserName}`,
          role: 'committee',
          roleDisplay: 'Component Committee',
          approver: member.memberName,
          approverName: member.memberName,
          status: memberStatus,
          date: member.committeeDate,
          justification: member.committeeJustification,
          canApprove: member.memberUserName === username && (!member.memberApproval || member.memberApproval === 'Pending'),
          isCommittee: true,
          memberUserName: member.memberUserName,
          memberPosition: member.memberPosition
        });
      });
    } else {
      // If no committee members, add a placeholder row
      rows.push({
        id: 'committee',
        role: 'committee',
        roleDisplay: 'Component Committee',
        approver: 'No members assigned',
        approverName: 'No members assigned',
        status: 'not_started',
        canApprove: false,
        isCommittee: true
      });
    }

    // Finance Manager row
    const fmStatus = fmApproval && fmApproval.approval 
      ? (fmApproval.approval === 'Approved' ? 'approved' : 'rejected') 
      : 'pending';
    const committeeStatus = getCommitteeStatus();
    // Allow finance manager to approve if: user has FM role, is not creator, status is pending, and committee is approved or no committee members
    const fmCanApprove = (currentUserRoles?.fm_role || false) && !isCreator && fmStatus === 'pending' && (committeeStatus === 'approved' || committeeMembers.length === 0);
    
    // Debug logging for finance manager approval
    console.log('🔍 Finance Manager Approval Debug:', {
      currentUserRoles,
      fm_role: currentUserRoles?.fm_role,
      isCreator,
      fmStatus,
      committeeStatus,
      committeeMembersLength: committeeMembers.length,
      fmCanApprove,
      username,
      fmApproval
    });

    rows.push({
      id: 'finance_manager',
      role: 'finance_manager',
      roleDisplay: 'Finance Manager',
      approver: fmApproval?.approver_name || 'Pending Assignment',
      approverName: fmApproval?.approver_name || 'Pending Assignment',
      status: fmStatus,
      date: fmApproval?.approval_date,
      justification: fmApproval?.justification,
      canApprove: fmCanApprove,
      isCommittee: false
    });

    // General Manager row
    const gmStatus = gmApproval && gmApproval.approval 
      ? (gmApproval.approval === 'Approved' ? 'approved' : 'rejected') 
      : 'pending';
    // General manager can approve if: user has GM role, is not creator, status is pending, and finance manager is approved
    const gmCanApprove = (currentUserRoles?.gm_role || false) && !isCreator && gmStatus === 'pending' && fmStatus === 'approved';
    
    // Debug logging for general manager approval
    console.log('🔍 General Manager Approval Debug:', {
      gm_role: currentUserRoles?.gm_role,
      isCreator,
      gmStatus,
      fmStatus,
      gmCanApprove
    });

    rows.push({
      id: 'general_manager',
      role: 'general_manager',
      roleDisplay: 'General Manager',
      approver: gmApproval?.approver_name || 'Pending Assignment',
      approverName: gmApproval?.approver_name || 'Pending Assignment',
      status: gmStatus,
      date: gmApproval?.approval_date,
      justification: gmApproval?.justification,
      canApprove: gmCanApprove,
      isCommittee: false
    });

    return rows;
  };

  const getCommitteeStatus = (): 'pending' | 'approved' | 'rejected' | 'not_started' => {
    if (committeeMembers.length === 0) {
      return 'not_started';
    }
    
    const approvals = committeeMembers.map(m => m.memberApproval);
    if (approvals.some(a => a === 'Rejected')) {
      return 'rejected';
    }
    if (approvals.every(a => a === 'Approved')) {
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

  const handleApprovalAction = (row: ApprovalRow, action: 'approve' | 'reject') => {
    setCurrentApprover({
      username: row.memberUserName || username,
      role: row.role,
      approval: action === 'approve' ? 'Approved' : 'Rejected'
    });
    setApprovalAction(action);
    setJustification('');
    setApprovalModal(true);
  };

  const submitApproval = async () => {
    if (!currentApprover) return;

    try {
      await onApprove(
        currentApprover.role!,
        currentApprover.username!,
        currentApprover.approval!,
        justification
      );
      setApprovalModal(false);
      setCurrentApprover(null);
    } catch (error) {
      console.error('Approval failed:', error);
    }
  };

  const approvalRows = buildApprovalRows();

  if (loading) {
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
    <div className="bg-white rounded-lg shadow-lg">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">Approval Workflow</h3>
        <p className="text-sm text-gray-600">Document: {csId}</p>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Approval Level
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Approver
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Date
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Justification
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {approvalRows.map((row) => (
              <tr key={row.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className="flex-shrink-0 h-8 w-8">
                      {row.isCommittee ? (
                        <svg className="w-8 h-8 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                        </svg>
                      ) : row.role === 'finance_manager' ? (
                        <svg className="w-8 h-8 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      ) : (
                        <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      )}
                    </div>
                    <div className="ml-4">
                      <div className="text-sm font-medium text-gray-900">{row.roleDisplay}</div>
                      <div className="text-sm text-gray-500">
                        {row.isCommittee ? 'Technical and operational review' : 
                         row.role === 'finance_manager' ? 'Financial review and budget validation' :
                         'Final authorization and strategic approval'}
                      </div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {row.isCommittee && row.memberUserName ? (
                    <div className="flex items-center">
                      <div className="flex-shrink-0 h-10 w-10">
                        <div className="h-10 w-10 rounded-full bg-indigo-100 flex items-center justify-center">
                          <span className="text-sm font-medium text-indigo-600">
                            {row.approverName.split(' ').map(n => n[0]).join('').toUpperCase()}
                          </span>
                        </div>
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">{row.approverName}</div>
                        <div className="text-sm text-gray-500">@{row.memberUserName}</div>
                        {row.memberPosition && (
                          <div className="text-xs text-gray-400">{row.memberPosition}</div>
                        )}
                      </div>
                    </div>
                  ) : (
                    <div>
                      <div className="text-sm text-gray-900">{row.approverName}</div>
                      {row.isCommittee && row.committeeMembers && row.committeeMembers.length > 0 && (
                        <div className="text-xs text-gray-500">
                          {row.committeeMembers.length} member{row.committeeMembers.length !== 1 ? 's' : ''}
                        </div>
                      )}
                    </div>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className={`p-2 rounded-full ${getStatusColor(row.status)}`}>
                      {getStatusIcon(row.status)}
                    </div>
                    <span className={`ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(row.status)}`}>
                      {row.status.charAt(0).toUpperCase() + row.status.slice(1)}
                    </span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {row.date ? new Date(row.date).toLocaleDateString() : '-'}
                </td>
                <td className="px-6 py-4 text-sm text-gray-900 max-w-xs">
                  {row.justification ? (
                    <div className="truncate" title={row.justification}>
                      {row.justification}
                    </div>
                  ) : '-'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  {row.canApprove ? (
                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleApprovalAction(row, 'approve')}
                        className="inline-flex items-center px-2 py-1 border border-transparent text-xs font-medium rounded text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                      >
                        <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                        </svg>
                        Approve
                      </button>
                      <button
                        onClick={() => handleApprovalAction(row, 'reject')}
                        className="inline-flex items-center px-2 py-1 border border-transparent text-xs font-medium rounded text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                      >
                        <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                        Reject
                      </button>
                    </div>
                  ) : row.isCommittee && row.memberUserName && row.memberUserName === username && row.status === 'approved' ? (
                    <span className="text-gray-400">Already approved</span>
                  ) : row.isCommittee && row.memberUserName && row.memberUserName === username && row.status === 'rejected' ? (
                    <span className="text-gray-400">Already rejected</span>
                  ) : row.isCommittee && row.memberUserName && row.memberUserName !== username ? (
                    <span className="text-gray-400">Not your approval</span>
                  ) : (
                    <span className="text-gray-400">No actions available</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Approval Modal */}
      {approvalModal && currentApprover && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                {approvalAction === 'approve' ? 'Approve' : 'Reject'} {currentApprover.role?.replace('_', ' ').toUpperCase()}
              </h3>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Justification
                </label>
                <textarea
                  value={justification}
                  onChange={(e) => setJustification(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={3}
                  placeholder="Enter your justification..."
                />
              </div>
              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => setApprovalModal(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
                >
                  Cancel
                </button>
                <button
                  onClick={submitApproval}
                  className={`px-4 py-2 text-sm font-medium text-white rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                    approvalAction === 'approve' 
                      ? 'bg-green-600 hover:bg-green-700 focus:ring-green-500' 
                      : 'bg-red-600 hover:bg-red-700 focus:ring-red-500'
                  }`}
                >
                  {approvalAction === 'approve' ? 'Approve' : 'Reject'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ApprovalTable; 