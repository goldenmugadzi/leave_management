  import React from 'react';
import { useCommitteeState } from '../../hooks/useCommitteeState';
import CommitteeManager from './CommitteeManager';
import { IUser, ICommittee } from '../../types/scheduleTypes';

interface CommitteeApprovalWrapperProps {
  users: IUser[];
  onSaveCommittee: (committee: ICommittee[]) => Promise<void>;
  onApprove: (username: string, approval: string, justification: string) => Promise<void>;
  isCreator?: boolean; // Add isCreator prop
  csrfToken?: string; // Add CSRF token prop
}

const CommitteeApprovalWrapper: React.FC<CommitteeApprovalWrapperProps> = ({
  users,
  onSaveCommittee,
  // onApprove,
  isCreator = false, // Default to false for safety
  csrfToken = "" // Default to empty string
}) => {
  const { committeeMembers } = useCommitteeState();

  return (
    <div className="space-y-8">
      {/* Committee Management Section */}
      {isCreator && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Committee Management</h2>
          <p className="text-sm text-gray-600 mb-6">
            {isCreator 
              ? "Add and manage committee members for this comparative schedule."
              : "View committee members for this comparative schedule. Only the creator can add or remove members."
            }
          </p>
          <CommitteeManager 
            users={users} 
            onSaveCommittee={onSaveCommittee}
            isCreator={isCreator} // Pass isCreator prop
            csrfToken={csrfToken} // Pass CSRF token prop
          />
        </div>
      )}

      {/* Summary Section */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Committee Summary</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-blue-50 p-4 rounded-lg">
            <h3 className="text-sm font-medium text-blue-800">Total Members</h3>
            <p className="text-2xl font-bold text-blue-900">{committeeMembers.length}</p>
          </div>
          <div className="bg-yellow-50 p-4 rounded-lg">
            <h3 className="text-sm font-medium text-yellow-800">Pending Approvals</h3>
            <p className="text-2xl font-bold text-yellow-900">
              {committeeMembers.filter(m => m.memberApproval === 'Pending').length}
            </p>
          </div>
          <div className="bg-green-50 p-4 rounded-lg">
            <h3 className="text-sm font-medium text-green-800">Approved</h3>
            <p className="text-2xl font-bold text-green-900">
              {committeeMembers.filter(m => m.memberApproval === 'Approved').length}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CommitteeApprovalWrapper; 