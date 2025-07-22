import React, { useState } from 'react';
import { useScheduleContext } from '../../context/ScheduleContext';

interface ICommittee {
  memberUserName: string;
  memberName: string;
  memberPosition?: string;
  committeeStatus?: string;
  memberApproval?: string;
  committeeJustification?: string;
  committeeDate?: string;
}

interface CommitteeApprovalTableProps {
  onApprove: (username: string, approval: string, justification: string) => Promise<void>;
}

const CommitteeApprovalTable: React.FC<CommitteeApprovalTableProps> = ({
  onApprove
}) => {
  const { committee, username } = useScheduleContext();
  const [approvalModal, setApprovalModal] = useState(false);
  const [currentMember, setCurrentMember] = useState<ICommittee | null>(null);
  const [justification, setJustification] = useState('');
  const [approvalAction, setApprovalAction] = useState<'approve' | 'reject'>('approve');

  const handleApprovalAction = (member: ICommittee, action: 'approve' | 'reject') => {
    setCurrentMember(member);
    setApprovalAction(action);
    setJustification('');
    setApprovalModal(true);
  };

  const submitApproval = async () => {
    if (!currentMember) return;

    try {
      await onApprove(
        currentMember.memberUserName,
        approvalAction === 'approve' ? 'Approved' : 'Rejected',
        justification
      );
      setApprovalModal(false);
      setCurrentMember(null);
      setJustification('');
    } catch (error) {
      console.error('Approval failed:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Approved':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'Rejected':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'Approved':
        return (
          <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
        );
      case 'Rejected':
        return (
          <svg className="w-5 h-5 text-red-600" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
          </svg>
        );
      default:
        return (
          <svg className="w-5 h-5 text-yellow-600" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
          </svg>
        );
    }
  };

  if (committee.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="text-center">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No Committee Members</h3>
          <p className="mt-1 text-sm text-gray-500">Committee members need to be added before approvals can be processed.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">Committee Member Approvals</h3>
        <p className="text-sm text-gray-600">Review and approve committee member submissions</p>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Member
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Position
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
            {committee.map((member) => (
              <tr key={member.memberUserName} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className="flex-shrink-0 h-10 w-10">
                      <div className="h-10 w-10 rounded-full bg-indigo-100 flex items-center justify-center">
                        <span className="text-sm font-medium text-indigo-600">
                          {member.memberName.split(' ').map(n => n[0]).join('').toUpperCase()}
                        </span>
                      </div>
                    </div>
                    <div className="ml-4">
                      <div className="text-sm font-medium text-gray-900">{member.memberName}</div>
                      <div className="text-sm text-gray-500">@{member.memberUserName}</div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {member.memberPosition || 'Not specified'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className={`p-2 rounded-full ${getStatusColor(member.memberApproval || 'Pending')}`}>
                      {getStatusIcon(member.memberApproval || 'Pending')}
                    </div>
                    <span className={`ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(member.memberApproval || 'Pending')}`}>
                      {member.memberApproval || 'Pending'}
                    </span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {member.committeeDate ? new Date(member.committeeDate).toLocaleDateString() : '-'}
                </td>
                <td className="px-6 py-4 text-sm text-gray-900 max-w-xs">
                  {member.committeeJustification ? (
                    <div className="truncate" title={member.committeeJustification}>
                      {member.committeeJustification}
                    </div>
                  ) : '-'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  {member.memberUserName === username && (!member.memberApproval || member.memberApproval === 'Pending') ? (
                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleApprovalAction(member, 'approve')}
                        className="inline-flex items-center px-2 py-1 border border-transparent text-xs font-medium rounded text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                      >
                        <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                        </svg>
                        Approve
                      </button>
                      <button
                        onClick={() => handleApprovalAction(member, 'reject')}
                        className="inline-flex items-center px-2 py-1 border border-transparent text-xs font-medium rounded text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                      >
                        <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                        Reject
                      </button>
                    </div>
                  ) : member.memberUserName === username ? (
                    <span className="text-gray-400">Already {member.memberApproval?.toLowerCase()}</span>
                  ) : (
                    <span className="text-gray-400">Not your approval</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Approval Modal */}
      {approvalModal && currentMember && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                {approvalAction === 'approve' ? 'Approve' : 'Reject'} Committee Member
              </h3>
              <div className="mb-4">
                <p className="text-sm text-gray-600 mb-2">
                  Member: <span className="font-medium">{currentMember.memberName}</span>
                </p>
                <p className="text-sm text-gray-600 mb-4">
                  Position: <span className="font-medium">{currentMember.memberPosition || 'Not specified'}</span>
                </p>
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

export default CommitteeApprovalTable; 