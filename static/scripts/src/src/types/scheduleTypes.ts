// Common interfaces for the Schedule component and related components

export interface ICurrency {
  id: number;
  currency?: string;
}

export interface IProcPlan {
  id: number;
  proc_ref: string;
  description: string;
}

export interface IPRAttachment {
  id: number;
  attachment_url: string;
  file: string;
  name: string;
}

export interface IBid {
  id?: number;
  supplier?: string;
  supplier_name?: string;
  bid_date?: string;
  encoded_bid_document?: string;
  bid_document?: File | null;
  bid_document_url?: string;
  bid_count?: number;
  items?: IBidItem[];
}

export interface IBidItem {
  id?: number;
  item_required?: string;
  unit_of_measurement?: string;
  vat?: string;
  quantity?: number;
  total_price?: number;
  unit_price?: number;
  ordered?: boolean;
}

export interface ICompliance {
  supplier_name?: string;
  supplier?: string;
  bid_no?: number;
  payment_terms?: boolean;
  bid_validity?: boolean;
  delivery_period?: boolean;
  technical_specifications?: boolean;
  valid_tax_clearance?: boolean;
  registered_with_praz?: boolean;
  site_visit?: boolean;
  samples_required?: boolean;
  decision?: boolean;
  reject?: boolean;
  [key: string]: unknown; // Allow dynamic properties
}

export interface IComplianceRemark {
  id?: number;
  remarks?: string;
  supplier_name?: string;
  bid_no?: number;
  [key: string]: unknown; // Replace 'any' with 'unknown' for better type safety
}

export interface IRank {
  id: number;
  supplier_name: string;
  rank: number;
  decision: string;
  remarks: string;
  total: number;
}

export interface ICommittee {
  memberUserName: string;
  memberName: string;
  memberPosition?: string;
  committeeStatus?: string;
  memberApproval?: string;
  committeeJustification?: string;
  committeeDate?: string;
}

export interface IMember {
  memberName: string;
  memberUserName: string;
  memberPosition?: string;
  memberApproval?: string;
}

export interface IGmApproval {
  id: number;
  approver_name: string;
  approval: string;
  approval_date: string;
  justification: string;
}

export interface IFmApproval {
  id: number;
  approver_name: string;
  approval: string;
  approval_date: string;
  justification: string;
}

export interface IUser {
  id: number;
  username: string;
  role: string;
  first_name: string;
  last_name: string;
}

export interface ICurrentApprover {
  username?: string;
  justification?: string;
  role?: string;
}

export interface IPrItems {
  id?: number;
  item_required?: string;
  quantity?: number;
  unit_of_measurement?: string;
  ordered?: boolean;
}

export interface ISupplier {
  id?: number;
  supplier_name?: string;
  name?: string;
  contact_person?: string;
  email?: string;
  phone_number?: string;
  address?: string;
  tax_number?: string;
  registration_number?: string;
  business_type?: string;
}

export interface IUom {
  id?: number;
  unit?: string;
  name?: string;
}

export interface IResponse {
  open: boolean;
  message: string;
  title: string;
  success: boolean;
}

export interface IUserOptions {
  value: string;
  label: string;
}