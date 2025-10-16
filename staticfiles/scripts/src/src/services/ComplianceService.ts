import { ICompliance, IComplianceRemark } from "../types/scheduleTypes";
import { getApiEndpoints, buildApiUrl } from "../config/apiEndpoints";

export interface IComplianceData {
  cs_id: string;
  show_site_visit: string;
  show_samples_required: string;
  compliance: ICompliance[];
  complianceRemarks: IComplianceRemark[];
}

export interface IComplianceResponse {
  success: boolean;
  message?: string;
  error?: string;
}

export interface IComplianceTable {
  bid_no: number;
  supplier: string;
  supplier_name: string;
  payment_terms: boolean;
  bid_validity: boolean;
  delivery_period: boolean;
  technical_specifications: boolean;
  valid_tax_clearance: boolean;
  registered_with_praz: boolean;
  site_visit: boolean;
  samples_required: boolean;
  decision: boolean;
  reject: boolean;
  remarks: string;
}

export class ComplianceService {
  private baseUrl: string;
  private csrfToken: string;

  constructor(baseUrl: string, csrfToken: string) {
    this.baseUrl = baseUrl;
    this.csrfToken = csrfToken;
  }

  /**
   * Save compliance data
   */
  async saveCompliance(complianceData: IComplianceData): Promise<IComplianceResponse> {
    try {
      const formData = new FormData();
      formData.append("cs_id", complianceData.cs_id);
      formData.append("show_site_visit", complianceData.show_site_visit);
      formData.append("show_samples_required", complianceData.show_samples_required);
      formData.append("compliance", JSON.stringify({ compliance: complianceData.compliance }));
      formData.append("complianceRemarks", JSON.stringify({ complianceRemarks: complianceData.complianceRemarks }));
      formData.append("csrfmiddlewaretoken", this.csrfToken);

      const response = await fetch(`${this.baseUrl}/save_compliance`, {
        method: "POST",
        headers: {
          "X-CSRFToken": this.csrfToken,
        },
        body: formData,
      });

      const data = await response.json();
      return data;
    } catch (error) {
      console.error("Error saving compliance:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to save compliance"
      };
    }
  }

  /**
   * Generate compliance table from bids
   */
  generateComplianceTable(bids: any[], existingCompliance?: ICompliance[]): IComplianceTable[] {
    return bids.map((bid) => {
      // Check if compliance already exists
      const existingComp = existingCompliance?.find(
        (compliance) => compliance.supplier_name === bid.supplier_name
      );

      if (existingComp) {
        return {
          ...existingComp,
          remarks: ""
        } as IComplianceTable;
      }

      // Generate new compliance entry
      return {
        bid_no: bid.bid_count || 0,
        supplier: bid.supplier || '',
        supplier_name: bid.supplier_name || '',
        payment_terms: false,
        bid_validity: false,
        delivery_period: false,
        technical_specifications: false,
        valid_tax_clearance: false,
        registered_with_praz: false,
        site_visit: false,
        samples_required: false,
        decision: false,
        reject: true,
        remarks: "",
      };
    });
  }

  /**
   * Generate compliance remarks from bids
   */
  generateComplianceRemarks(bids: any[], existingRemarks?: IComplianceRemark[]): IComplianceRemark[] {
    return bids.map((bid) => {
      // Check if compliance remarks already exist
      const existingRemark = existingRemarks?.find(
        (compR) => compR.supplier_name === bid.supplier_name
      );

      if (existingRemark) {
        return existingRemark;
      }

      // Generate new compliance remark entry
      return {
        bid_count: bid.bid_count || 0,
        supplier: bid.supplier || '',
        supplier_name: bid.supplier_name || '',
        remarks: "",
      };
    });
  }

  /**
   * Update compliance criteria
   */
  updateComplianceCriteria(
    compliance: IComplianceTable[],
    index: number,
    field: keyof IComplianceTable,
    value: boolean
  ): IComplianceTable[] {
    const updatedCompliance = [...compliance];
    const currentCompliance = updatedCompliance[index];
    
    if (currentCompliance) {
      (currentCompliance as any)[field] = value;
      
      // Update decision based on all compliance checks
      const keysToCheck = [
        'payment_terms', 'bid_validity', 'delivery_period',
        'technical_specifications', 'valid_tax_clearance', 'registered_with_praz'
      ];
      
      // Add conditional criteria based on requirements
      if (compliance.length > 0) {
        // This would need to be passed from the component context
        // For now, we'll assume these are always required
        keysToCheck.push('site_visit', 'samples_required');
      }
      
      const allValuesTrue = keysToCheck.every((key) => (currentCompliance as any)[key] === true);
      currentCompliance.decision = allValuesTrue;
      currentCompliance.reject = !allValuesTrue;
    }
    
    return updatedCompliance;
  }

  /**
   * Check all compliance criteria for a supplier
   */
  checkAllCompliance(
    compliance: IComplianceTable[],
    index: number,
    showSiteVisit: string,
    showSamples: string
  ): IComplianceTable[] {
    const updatedCompliance = [...compliance];
    const currentCompliance = updatedCompliance[index];
    
    if (currentCompliance) {
      // Check all required criteria
      const keysToCheck = [
        'payment_terms', 'bid_validity', 'delivery_period',
        'technical_specifications', 'valid_tax_clearance', 'registered_with_praz'
      ];
      
      if (showSiteVisit === "yes") keysToCheck.push('site_visit');
      if (showSamples === "yes") keysToCheck.push('samples_required');

      // Set all criteria to true
      keysToCheck.forEach(key => {
        (currentCompliance as any)[key] = true;
      });

      // Update decision and reject status
      currentCompliance.decision = true;
      currentCompliance.reject = false;
    }
    
    return updatedCompliance;
  }

  /**
   * Update compliance remarks
   */
  updateComplianceRemarks(
    complianceRemarks: IComplianceRemark[],
    supplierName: string,
    remarks: string
  ): IComplianceRemark[] {
    return complianceRemarks.map((remark) => {
      if (remark.supplier_name === supplierName) {
        return {
          ...remark,
          remarks: remarks,
        };
      }
      return remark;
    });
  }

  /**
   * Validate compliance data before saving
   */
  validateComplianceData(complianceData: IComplianceData): { isValid: boolean; errors: string[] } {
    const errors: string[] = [];

    if (!complianceData.cs_id) {
      errors.push("CS ID is required");
    }

    if (!complianceData.compliance || complianceData.compliance.length === 0) {
      errors.push("Compliance data is required");
    }

    if (!complianceData.complianceRemarks || complianceData.complianceRemarks.length === 0) {
      errors.push("Compliance remarks are required");
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  /**
   * Check if at least one bid is compliant
   */
  hasCompliantBids(compliance: IComplianceTable[]): boolean {
    return compliance.some(comp => comp.decision === true);
  }

  /**
   * Get compliance summary statistics
   */
  getComplianceSummary(compliance: IComplianceTable[]): {
    total: number;
    compliant: number;
    nonCompliant: number;
    pending: number;
  } {
    const total = compliance.length;
    const compliant = compliance.filter(comp => comp.decision === true).length;
    const nonCompliant = compliance.filter(comp => comp.decision === false).length;
    const pending = total - compliant - nonCompliant;

    return {
      total,
      compliant,
      nonCompliant,
      pending
    };
  }

  /**
   * Export compliance data to CSV
   */
  exportComplianceToCSV(compliance: IComplianceTable[]): string {
    const headers = [
      'Bid No',
      'Supplier Name',
      'Payment Terms',
      'Bid Validity',
      'Delivery Period',
      'Technical Specs',
      'Tax Clearance',
      'PRAZ Registered',
      'Site Visit',
      'Samples Required',
      'Decision',
      'Remarks'
    ];

    const csvContent = [
      headers.join(','),
      ...compliance.map(comp => [
        comp.bid_no,
        comp.supplier_name,
        comp.payment_terms ? 'Yes' : 'No',
        comp.bid_validity ? 'Yes' : 'No',
        comp.delivery_period ? 'Yes' : 'No',
        comp.technical_specifications ? 'Yes' : 'No',
        comp.valid_tax_clearance ? 'Yes' : 'No',
        comp.registered_with_praz ? 'Yes' : 'No',
        comp.site_visit ? 'Yes' : 'No',
        comp.samples_required ? 'Yes' : 'No',
        comp.decision ? 'Compliant' : 'Non-Compliant',
        comp.remarks
      ].join(','))
    ].join('\n');

    return csvContent;
  }

  /**
   * Fetch compliance data for a schedule
   */
  async fetchComplianceData(csId: string): Promise<{
    compliance: ICompliance[];
    complianceRemarks: IComplianceRemark[];
  }> {
    try {
      const response = await fetch(buildApiUrl(this.baseUrl, getApiEndpoints().CS_COMPLIANCE_DATA(csId)), {
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
        compliance: data.compliance || [],
        complianceRemarks: data.compliance_remarks || []
      };
    } catch (error) {
      console.error("Error fetching compliance data:", error);
      throw error;
    }
  }
}
