import React, { createContext, useContext, useState, ReactNode, Dispatch, SetStateAction } from 'react';
import { ICompliance, IComplianceRemark, IBid, IPrItems, ICommittee, ICurrentApprover } from '../types/scheduleTypes';

interface ScheduleContextType {
  base_url: string;
  csId: string;
  username: string;
  bids: IBid[];
  prItems: IPrItems[];
  committee: ICommittee[];
  compliance: ICompliance[];
  complianceRemarks: IComplianceRemark[];
  currentApprover: ICurrentApprover | null;
  setBids: Dispatch<SetStateAction<IBid[]>>;
  setPrItems: Dispatch<SetStateAction<IPrItems[]>>;
  setCommittee: Dispatch<SetStateAction<ICommittee[]>>;
  setCompliance: Dispatch<SetStateAction<ICompliance[]>>;
  setComplianceRemarks: Dispatch<SetStateAction<IComplianceRemark[]>>;
  setCurrentApprover: Dispatch<SetStateAction<ICurrentApprover | null>>;
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
}

const defaultContextValue: ScheduleContextType = {
  base_url: '',
  csId: '',
  username: '',
  bids: [],
  prItems: [],
  committee: [],
  compliance: [],
  complianceRemarks: [],
  currentApprover: null,
  setBids: () => {},
  setPrItems: () => {},
  setCommittee: () => {},
  setCompliance: () => {},
  setComplianceRemarks: () => {},
  setCurrentApprover: () => {},
  isLoading: false,
  setIsLoading: () => {},
};

export const ScheduleContext = createContext<ScheduleContextType>(defaultContextValue);

export const useScheduleContext = () => useContext(ScheduleContext);

interface ScheduleProviderProps {
  children: ReactNode;
  base_url: string;
  csId: string;
  username: string;
}

export const ScheduleProvider: React.FC<ScheduleProviderProps> = ({ 
  children, 
  base_url,
  csId,
  username,
}) => {
  const [bids, setBids] = useState<IBid[]>([]);
  const [prItems, setPrItems] = useState<IPrItems[]>([]);
  const [committee, setCommittee] = useState<ICommittee[]>([]);
  const [compliance, setCompliance] = useState<ICompliance[]>([]);
  const [complianceRemarks, setComplianceRemarks] = useState<IComplianceRemark[]>([]);
  const [currentApprover, setCurrentApprover] = useState<ICurrentApprover | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const value = {
    base_url,
    csId,
    username,
    bids,
    prItems,
    committee,
    compliance,
    complianceRemarks,
    currentApprover,
    setBids,
    setPrItems,
    setCommittee,
    setCompliance,
    setComplianceRemarks,
    setCurrentApprover,
    isLoading,
    setIsLoading,
  };

  return (
    <ScheduleContext.Provider value={value}>
      {children}
    </ScheduleContext.Provider>
  );
}; 