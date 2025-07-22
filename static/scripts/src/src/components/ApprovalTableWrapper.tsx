import React from 'react';
import { useScheduleContext } from '../context/ScheduleContext';
import ApprovalTable from './ApprovalTable';
import { IGmApproval, IFmApproval } from '../types/scheduleTypes';

interface ApprovalTableWrapperProps {
  csId: string;
  username: string;
  gmApproval: IGmApproval | null | undefined;
  fmApproval: IFmApproval | null | undefined;
  isCreator: boolean;
  onApprove: (role: string, username: string, approval: string, justification: string) => Promise<void>;
}

const ApprovalTableWrapper: React.FC<ApprovalTableWrapperProps> = ({
  csId,
  username,
  gmApproval,
  fmApproval,
  isCreator,
  onApprove
}) => {
  const { committee } = useScheduleContext();

  console.log("🔍 ApprovalTableWrapper - Committee from context:", {
    count: committee.length,
    members: committee.map(m => ({
      name: m.memberName,
      username: m.memberUserName,
      approval: m.memberApproval
    }))
  });

  return (
    <div>
      {/* Debug Panel */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
        <h3 className="text-sm font-medium text-blue-800 mb-2">ApprovalTableWrapper Debug</h3>
        <div className="text-xs text-blue-700 space-y-1">
          <p>Committee count: {committee.length}</p>
          <p>Committee data: {JSON.stringify(committee, null, 2)}</p>
        </div>
      </div>
      
      <ApprovalTable
        csId={csId}
        username={username}
        committeeMembers={committee}
        gmApproval={gmApproval}
        fmApproval={fmApproval}
        isCreator={isCreator}
        onApprove={onApprove}
      />
    </div>
  );
};

export default ApprovalTableWrapper; 