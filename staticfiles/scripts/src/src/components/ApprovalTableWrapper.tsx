import React from 'react';
import ApprovalTable from './ApprovalTable';
import { IGmApproval, IFmApproval, ICommittee } from '../types/scheduleTypes';

interface ApprovalTableWrapperProps {
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

const ApprovalTableWrapper: React.FC<ApprovalTableWrapperProps> = ({
  csId,
  username,
  committeeMembers,
  gmApproval,
  fmApproval,
  isCreator,
  onApprove,
  currentUserRoles
}) => {



  return (
    <div>
      <ApprovalTable
        csId={csId}
        username={username}
        committeeMembers={committeeMembers}
        gmApproval={gmApproval}
        fmApproval={fmApproval}
        isCreator={isCreator}
        onApprove={onApprove}
        currentUserRoles={currentUserRoles}
      />
    </div>
  );
};

export default ApprovalTableWrapper; 