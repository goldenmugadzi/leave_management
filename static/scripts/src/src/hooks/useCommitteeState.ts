import { useState, useCallback } from 'react';
import { useScheduleContext } from '../context/ScheduleContext';
import { ICommittee } from '../types/scheduleTypes';

export const useCommitteeState = () => {
  const [localCommitteeMembers, setLocalCommitteeMembers] = useState<ICommittee[]>([]);
  const { committee: contextCommittee, setCommittee: setContextCommittee } = useScheduleContext();

  // Update both local and context state
  const updateCommitteeMembers = useCallback((members: ICommittee[]) => {
    setLocalCommitteeMembers(members);
    setContextCommittee(members);
  }, [setContextCommittee]);

  // Get the current committee members (prefer context, fallback to local)
  const committeeMembers = contextCommittee.length > 0 ? contextCommittee : localCommitteeMembers;

  return {
    committeeMembers,
    updateCommitteeMembers,
    setLocalCommitteeMembers
  };
}; 