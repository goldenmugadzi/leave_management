import React from 'react';
import { useScheduleContext } from '../../context/ScheduleContext';
import CommitteeManager from './CommitteeManager';
import CommitteeApprovalTable from './CommitteeApprovalTable';
import { IUser, ICommittee } from '../../types/scheduleTypes';

interface CommitteeApprovalWrapperProps {
  users: IUser[];
  onSaveCommittee: (committee: ICommittee[]) => Promise<void>;
  onApprove: (username: string, approval: string, justification: string) => Promise<void>;
}

const CommitteeApprovalWrapper: React.FC<CommitteeApprovalWrapperProps> = ({
  users,
  onSaveCommittee,
  onApprove
}) => {
  const { committee } = useScheduleContext();

  return (
    <div className="space-y-8">
      {/* Committee Management Section */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Committee Management</h2>
        <p className="text-sm text-gray-600 mb-6">
          Add and manage committee members for this comparative schedule.
        </p>
        <CommitteeManager 
          users={users} 
          onSaveCommittee={onSaveCommittee} 
        />
      </div>

      {/* Committee Approval Section */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Committee Approvals</h2>
        <p className="text-sm text-gray-600 mb-6">
          Review and approve committee member submissions. Only committee members can approve their own submissions.
        </p>
        <CommitteeApprovalTable onApprove={onApprove} />
      </div>

      {/* Summary Section */}
      {committee.length > 0 && (
        <div className="bg-blue-50 rounded-lg p-4">
          <h3 className="text-sm font-medium text-blue-900 mb-2">Committee Summary</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <span className="text-blue-700 font-medium">Total Members:</span>
              <span className="ml-2 text-blue-600">{committee.length}</span>
            </div>
            <div>
              <span className="text-blue-700 font-medium">Approved:</span>
              <span className="ml-2 text-green-600">
                {committee.filter(m => m.memberApproval === 'Approved').length}
              </span>
            </div>
            <div>
              <span className="text-blue-700 font-medium">Pending:</span>
              <span className="ml-2 text-yellow-600">
                {committee.filter(m => !m.memberApproval || m.memberApproval === 'Pending').length}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CommitteeApprovalWrapper; 