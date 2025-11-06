import { ICommittee } from "../types/scheduleTypes";
import { getApiEndpoints, buildApiUrl } from "../config/apiEndpoints";

export interface ICommitteeData {
  cs_id: string;
  committee: ICommittee[];
}

export interface IApprovalData {
  cs_id: string;
  username: string;
  approval: string;
  justification: string;
  role?: string;
}

export interface ICommitteeResponse {
  success: boolean;
  message?: string;
  error?: string;
}

export interface IApprovalResponse {
  success: boolean;
  message?: string;
  error?: string;
  gm_approval?: any;
  fm_approval?: any;
}

export interface ICurrentUserRoles {
  fm_role: boolean;
  gm_role: boolean;
  procurement_role: boolean;
}

export class CommitteeService {
  private baseUrl: string;
  private csrfToken: string;

  constructor(baseUrl: string, csrfToken: string) {
    this.baseUrl = baseUrl;
    this.csrfToken = csrfToken;
  }

  /**
   * Save committee members
   */
  async saveCommittee(committeeData: ICommitteeData): Promise<ICommitteeResponse> {
    try {
      const formData = new FormData();
      formData.append("cs_id", committeeData.cs_id);
      formData.append("committee", JSON.stringify({ committee: committeeData.committee }));
      formData.append("csrfmiddlewaretoken", this.csrfToken);

      const response = await fetch(buildApiUrl(this.baseUrl, getApiEndpoints().CS_SAVE_COMMITTEE), {
        method: "POST",
        headers: {
          "X-CSRFToken": this.csrfToken,
        },
        body: formData,
      });

      const data = await response.json();
      return data;
    } catch (error) {
      console.error("Error saving committee:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to save committee"
      };
    }
  }

  /**
   * Handle committee approval
   */
  async handleCommitteeApproval(approvalData: IApprovalData): Promise<ICommitteeResponse> {
    try {
      const formData = new FormData();
      formData.append("cs_id", approvalData.cs_id);
      formData.append("username", approvalData.username);
      formData.append("approval", approvalData.approval);
      formData.append("justification", approvalData.justification);
      formData.append("csrfmiddlewaretoken", this.csrfToken);

      const response = await fetch(buildApiUrl(this.baseUrl, "/committee_approve"), {
        method: "POST",
        headers: {
          "X-CSRFToken": this.csrfToken,
        },
        body: formData,
      });

      const data = await response.json();
      return data;
    } catch (error) {
      console.error("Error handling committee approval:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to process committee approval"
      };
    }
  }

  /**
   * Handle FM/GM approval
   */
  async handleManagerApproval(approvalData: IApprovalData): Promise<IApprovalResponse> {
    try {
      if (!approvalData.role) {
        throw new Error("Role is required for manager approvals");
      }

      const formData = new FormData();
      formData.append("cs_id", approvalData.cs_id);
      formData.append("role", approvalData.role);
      formData.append("username", approvalData.username);
      formData.append("approval", approvalData.approval);
      formData.append("justification", approvalData.justification);
      formData.append("csrfmiddlewaretoken", this.csrfToken);

      const response = await fetch(buildApiUrl(this.baseUrl, "/approval_approve"), {
        method: "POST",
        headers: {
          "X-CSRFToken": this.csrfToken,
        },
        body: formData,
      });

      const data = await response.json();
      return data;
    } catch (error) {
      console.error("Error handling manager approval:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to process manager approval"
      };
    }
  }

  /**
   * Fetch committee data for a schedule
   */
  async fetchCommitteeData(csId: string): Promise<{
    committee: ICommittee[];
    current_user_roles?: ICurrentUserRoles;
  }> {
    try {
      const response = await fetch(buildApiUrl(this.baseUrl, getApiEndpoints().CS_COMMITTEE_DATA(csId)), {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": this.csrfToken,
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      const data = await response.json();
      
      return {
        committee: data.committee || [],
        current_user_roles: data.current_user_roles
      };
    } catch (error) {
      console.error("Error fetching committee data:", error);
      throw error;
    }
  }

  /**
   * Fetch approval data for a schedule
   */
  async fetchApprovalData(csId: string): Promise<{
    gm_approval?: any;
    fm_approval?: any;
    current_user_roles?: ICurrentUserRoles;
  }> {
    try {
      const response = await fetch(buildApiUrl(this.baseUrl, getApiEndpoints().CS_APPROVALS_DATA(csId)), {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": this.csrfToken,
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      const data = await response.json();
      
      return {
        gm_approval: data.gm_approval,
        fm_approval: data.fm_approval,
        current_user_roles: data.current_user_roles
      };
    } catch (error) {
      console.error("Error fetching approval data:", error);
      throw error;
    }
  }

  /**
   * Check if user is committee member
   */
  isCommitteeMember(committee: ICommittee[], username: string): boolean {
    return committee.some(member => member.memberUserName === username);
  }

  /**
   * Check if user has approval role
   */
  hasApprovalRole(userRoles: ICurrentUserRoles, role: 'fm_role' | 'gm_role'): boolean {
    return userRoles[role] || false;
  }

  /**
   * Check if all committee approvals are complete
   */
  areCommitteeApprovalsComplete(committee: ICommittee[]): boolean {
    if (committee.length === 0) return true; // No committee members means auto-approved
    return committee.every(member => member.memberApproval === "Approved");
  }

  /**
   * Check if all approvals are complete
   */
  areAllApprovalsComplete(
    committee: ICommittee[],
    gmApproval: any,
    fmApproval: any
  ): boolean {
    const committeeApproved = this.areCommitteeApprovalsComplete(committee);
    const gmApproved = gmApproval && gmApproval.approval === "Approved";
    const fmApproved = fmApproval && fmApproval.approval === "Approved";

    return committeeApproved && gmApproved && fmApproved;
  }

  /**
   * Get approval status summary
   */
  getApprovalStatusSummary(
    committee: ICommittee[],
    gmApproval: any,
    fmApproval: any
  ): {
    committee: { status: string; count: number; total: number };
    gm: { status: string; approver?: string; date?: string };
    fm: { status: string; approver?: string; date?: string };
    overall: string;
  } {
    const committeeStatus = this.areCommitteeApprovalsComplete(committee) ? "Complete" : "Pending";
    const committeeCount = committee.filter(m => m.memberApproval === "Approved").length;
    
    const gmStatus = gmApproval?.approval === "Approved" ? "Complete" : "Pending";
    const fmStatus = fmApproval?.approval === "Approved" ? "Complete" : "Pending";
    
    const overall = this.areAllApprovalsComplete(committee, gmApproval, fmApproval) 
      ? "Complete" 
      : "Pending";

    return {
      committee: {
        status: committeeStatus,
        count: committeeCount,
        total: committee.length
      },
      gm: {
        status: gmStatus,
        approver: gmApproval?.approver_name,
        date: gmApproval?.approval_date
      },
      fm: {
        status: fmStatus,
        approver: fmApproval?.approver_name,
        date: fmApproval?.approval_date
      },
      overall
    };
  }

  /**
   * Validate approval data
   */
  validateApprovalData(approvalData: IApprovalData): { isValid: boolean; errors: string[] } {
    const errors: string[] = [];

    if (!approvalData.cs_id) {
      errors.push("CS ID is required");
    }

    if (!approvalData.username) {
      errors.push("Username is required");
    }

    if (!approvalData.approval) {
      errors.push("Approval decision is required");
    }

    if (approvalData.approval === "Rejected" && !approvalData.justification?.trim()) {
      errors.push("Justification is required for rejection");
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  /**
   * Check if user can perform approval action
   */
  canUserApprove(
    username: string,
    csOwner: string,
    committee: ICommittee[],
    userRoles: ICurrentUserRoles,
    approvalType: 'committee' | 'fm' | 'gm'
  ): { canApprove: boolean; reason?: string } {
    // Creators cannot approve their own documents
    if (username === csOwner) {
      return {
        canApprove: false,
        reason: "Creators cannot approve their own documents"
      };
    }

    switch (approvalType) {
      case 'committee':
        // Only committee members can perform committee approvals
        if (!this.isCommitteeMember(committee, username)) {
          return {
            canApprove: false,
            reason: "Only committee members can perform committee approvals"
          };
        }
        break;

      case 'fm':
        // Only users with FM role can perform FM approvals
        if (!this.hasApprovalRole(userRoles, 'fm_role')) {
          return {
            canApprove: false,
            reason: "Only finance managers can perform FM approvals"
          };
        }
        break;

      case 'gm':
        // Only users with GM role can perform GM approvals
        if (!this.hasApprovalRole(userRoles, 'gm_role')) {
          return {
            canApprove: false,
            reason: "Only general managers can perform GM approvals"
          };
        }
        break;
    }

    return { canApprove: true };
  }

  /**
   * Export committee data to CSV
   */
  exportCommitteeToCSV(committee: ICommittee[]): string {
    const headers = [
      'Member Name',
      'Position',
      'Username',
      'Approval Status',
      'Approval Date',
      'Justification'
    ];

    const csvContent = [
      headers.join(','),
      ...committee.map(member => [
        member.memberName || '',
        member.memberPosition || '',
        member.memberUserName || '',
        member.memberApproval || 'Pending',
        member.committeeDate || '',
        member.committeeJustification || ''
      ].join(','))
    ].join('\n');

    return csvContent;
  }
}
