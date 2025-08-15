import { getApiEndpoints, buildApiUrl } from '../config/apiEndpoints';
import { IBid, ICompliance, IComplianceRemark, ICommittee } from '../types/scheduleTypes';

// Helper function to get CSRF token
const getCookie = (name: string) => {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + '=') {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
};

// Helper function to fetch with retry capability
const fetchWithRetry = async (url: string, options: RequestInit, retries = 3, delay = 1000) => {
  try {
    const response = await fetch(url, options);
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    if (retries > 0) {
      await new Promise((resolve) => setTimeout(resolve, delay));
      return fetchWithRetry(url, options, retries - 1, delay * 2);
    }
    throw error;
  }
};

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

export interface FileUploadResponse {
  success: boolean;
  message?: string;
  metadata?: {
    original_name: string;
    size: number;
    mime_type: string;
  };
  download_url?: string;
  preview_url?: string;
  file_path?: string;
}

export class ScheduleApiService {
  private baseUrl: string;
  private csrfToken: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
    this.csrfToken = getCookie("csrftoken") ?? "";
  }

  /**
   * Get current CSRF token (useful for components that need it)
   */
  getCsrfToken(): string {
    return this.csrfToken;
  }

  /**
   * Refresh CSRF token (useful if token expires)
   */
  refreshCsrfToken(): void {
    this.csrfToken = getCookie("csrftoken") ?? "";
  }

  /**
   * Generic GET request with error handling
   */
  private async get<T>(endpoint: string): Promise<ApiResponse<T>> {
    try {
      const url = buildApiUrl(this.baseUrl, endpoint);
      const response = await fetchWithRetry(url, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": this.csrfToken,
        },
      });
      
      return { success: true, data: response };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : String(error)
      };
    }
  }

  /**
   * Generic POST request with error handling
   */
  private async post<T>(endpoint: string, data?: any, isFormData: boolean = false): Promise<ApiResponse<T>> {
    try {
      const url = buildApiUrl(this.baseUrl, endpoint);
      
      let body: string | FormData;
      let headers: Record<string, string> = { "X-CSRFToken": this.csrfToken };
      
      if (isFormData) {
        body = data;
        // Don't set Content-Type for FormData, let browser set it with boundary
      } else {
        body = JSON.stringify(data);
        headers["Content-Type"] = "application/json";
      }

      const response = await fetchWithRetry(url, {
        method: "POST",
        headers,
        body,
      });
      
      return { success: true, data: response };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : String(error)
      };
    }
  }



  /**
   * Generic DELETE request with error handling
   */
  private async delete<T>(endpoint: string): Promise<ApiResponse<T>> {
    try {
      const url = buildApiUrl(this.baseUrl, endpoint);
      const response = await fetchWithRetry(url, {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": this.csrfToken,
        },
      });
      
      return { success: true, data: response };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : String(error)
      };
    }
  }

  // === SCHEDULE CRUD OPERATIONS ===

  /**
   * Fetch Comparative Schedule data
   */
  async fetchCS(csId: string): Promise<ApiResponse<any>> {
    return this.get(`/cs_data/${csId}`);
  }

  /**
   * Save new Comparative Schedule
   */
  async saveSchedule(formData: FormData): Promise<ApiResponse<any>> {
    return this.post(getApiEndpoints().CS_SAVE, formData, true);
  }

  /**
   * Update existing Comparative Schedule
   */
  async updateSchedule(formData: FormData): Promise<ApiResponse<any>> {
    return this.post(getApiEndpoints().CS_UPDATE(), formData, true);
  }

  /**
   * Update PR items in a schedule
   */
  async updateScheduleItems(csId: string, prId: string, items: any[]): Promise<ApiResponse<any>> {
    const formData = new FormData();
    formData.append("cs_id", csId);
    formData.append("pr_id", prId);
    formData.append("json_data", JSON.stringify({
      cs_items: items
    }));
    formData.append("csrfmiddlewaretoken", this.csrfToken);

    return this.post(getApiEndpoints().CS_UPDATE_ITEMS(), formData, true);
  }

  // === PURCHASE REQUEST OPERATIONS ===

  /**
   * Fetch Purchase Request basic data
   */
  async fetchPR(prId: string): Promise<ApiResponse<any>> {
    return this.get(getApiEndpoints().PR_BASIC(prId));
  }

  /**
   * Fetch PR Items with pagination
   */
  async fetchPRItems(prId: string, page: number = 1, pageSize: number = 50): Promise<ApiResponse<any>> {
    return this.get(`${getApiEndpoints().PR_ITEMS(prId)}?page=${page}&page_size=${pageSize}`);
  }

  /**
   * Fetch PR Attachments
   */
  async fetchPRAttachments(prId: string): Promise<ApiResponse<any>> {
    return this.get(getApiEndpoints().PR_ATTACHMENTS(prId));
  }

  // === REFERENCE DATA OPERATIONS ===

  /**
   * Fetch all reference data (suppliers, users, currencies, proc plans)
   */
  async fetchReferenceData(): Promise<ApiResponse<any>> {
    return this.get(getApiEndpoints().REFERENCE_DATA());
  }

  /**
   * Fetch suppliers with search
   */
  async fetchSuppliers(search?: string, limit: number = 100): Promise<ApiResponse<any>> {
    const endpoint = search 
      ? `${getApiEndpoints().SUPPLIERS}?search=${encodeURIComponent(search)}&limit=${limit}`
      : getApiEndpoints().SUPPLIERS;
    return this.get(endpoint);
  }

  /**
   * Fetch users
   */
  async fetchUsers(limit: number = 100): Promise<ApiResponse<any>> {
    return this.get(`${getApiEndpoints().USERS}?limit=${limit}`);
  }

  /**
   * Fetch currencies
   */
  async fetchCurrencies(): Promise<ApiResponse<any>> {
    return this.get(getApiEndpoints().CURRENCIES);
  }

  /**
   * Fetch procurement plans
   */
  async fetchProcPlans(): Promise<ApiResponse<any>> {
    return this.get(getApiEndpoints().PROC_PLANS);
  }

  /**
   * Fetch UOM (Units of Measurement) with search
   */
  async fetchUOM(search?: string, limit: number = 100): Promise<ApiResponse<any>> {
    const endpoint = search 
      ? `${getApiEndpoints().UOM}?search=${encodeURIComponent(search)}&limit=${limit}`
      : getApiEndpoints().UOM;
    return this.get(endpoint);
  }

  // === BID OPERATIONS ===

  /**
   * Save bid
   */
  async saveBid(csId: string, bid: IBid): Promise<ApiResponse<any>> {
    const formData = new FormData();
    
    // Append bid data as JSON
    const bidWithoutFile = { ...bid };
    delete bidWithoutFile.bid_document;
    
    formData.append('bid_data', JSON.stringify(bidWithoutFile));
    
    // Append file if present
    if (bid.bid_document) {
      formData.append('bid_document', bid.bid_document);
    }
    
    formData.append("csrfmiddlewaretoken", this.csrfToken);

    return this.post(getApiEndpoints().CS_BIDS(csId), formData, true);
  }

  /**
   * Delete bid
   */
  async deleteBid(csId: string, bidCount: number): Promise<ApiResponse<any>> {
    return this.delete(getApiEndpoints().CS_BID_DELETE(csId, bidCount));
  }

  /**
   * Fetch bids for a schedule
   */
  async fetchBids(csId: string): Promise<ApiResponse<any>> {
    return this.get(getApiEndpoints().CS_BIDS_DATA(csId));
  }

  // === COMMITTEE OPERATIONS ===

  /**
   * Save committee members
   */
  async saveCommittee(committee: ICommittee[]): Promise<ApiResponse<any>> {
    const formData = new FormData();
    formData.append("committee", JSON.stringify({ committee }));
    formData.append("csrfmiddlewaretoken", this.csrfToken);

    return this.post(getApiEndpoints().CS_SAVE_COMMITTEE, formData, true);
  }

  /**
   * Fetch committee data
   */
  async fetchCommittee(csId: string): Promise<ApiResponse<any>> {
    return this.get(getApiEndpoints().CS_COMMITTEE_DATA(csId));
  }

  /**
   * Approve committee member
   */
  async approveCommitteeMember(csId: string, username: string, approval: string, justification: string): Promise<ApiResponse<any>> {
    const formData = new FormData();
    formData.append("cs_id", csId);
    formData.append("username", username);
    formData.append("approval", approval);
    formData.append("justification", justification);
    formData.append("csrfmiddlewaretoken", this.csrfToken);

    return this.post("/committee_approve", formData, true);
  }

  // === COMPLIANCE OPERATIONS ===

  /**
   * Save compliance data
   */
  async saveCompliance(csId: string, compliance: ICompliance[], remarks: IComplianceRemark[], showSiteVisit: string, showSamples: string): Promise<ApiResponse<any>> {
    const formData = new FormData();
    formData.append("cs_id", csId);
    formData.append("show_site_visit", showSiteVisit);
    formData.append("show_samples_required", showSamples);
    formData.append("compliance", JSON.stringify({ compliance }));
    formData.append("complianceRemarks", JSON.stringify({ complianceRemarks: remarks }));
    formData.append("csrfmiddlewaretoken", this.csrfToken);

    return this.post("/save_compliance", formData, true);
  }

  /**
   * Fetch compliance data
   */
  async fetchCompliance(csId: string): Promise<ApiResponse<any>> {
    return this.get(getApiEndpoints().CS_COMPLIANCE_DATA(csId));
  }

  /**
   * Close CS and generate rankings
   */
  async closeCSAndGenerateRankings(csId: string): Promise<ApiResponse<any>> {
    const formData = new FormData();
    formData.append("cs_id", csId);
    formData.append("csrfmiddlewaretoken", this.csrfToken);

    return this.post("/close_compliance", formData, true);
  }

  // === APPROVAL OPERATIONS ===

  /**
   * Fetch approval data
   */
  async fetchApprovals(csId: string): Promise<ApiResponse<any>> {
    return this.get(getApiEndpoints().CS_APPROVALS_DATA(csId));
  }

  /**
   * Approve (FM/GM approval)
   */
  async approve(role: string, username: string, approval: string, justification: string): Promise<ApiResponse<any>> {
    const formData = new FormData();
    formData.append("role", role);
    formData.append("username", username);
    formData.append("approval", approval);
    formData.append("justification", justification);
    formData.append("csrfmiddlewaretoken", this.csrfToken);

    return this.post("/approval_approve", formData, true);
  }

  // === FILE OPERATIONS ===

  /**
   * Upload file
   */
  async uploadFile(file: File, fileType: string = 'general', description?: string): Promise<ApiResponse<FileUploadResponse>> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('file_type', fileType);
    if (description) {
      formData.append('description', description);
    }

    return this.post(getApiEndpoints().FILE_UPLOAD(), formData, true);
  }

  /**
   * Delete file
   */
  async deleteFile(filePath: string): Promise<ApiResponse<any>> {
    return this.delete(getApiEndpoints().FILE_DELETE(filePath));
  }

  /**
   * Get CS files metadata
   */
  async getCSFiles(csId: string): Promise<ApiResponse<any>> {
    return this.get(getApiEndpoints().CS_FILES(csId));
  }

  // === ADDITIONAL FEATURES ===

  /**
   * Save additional notes
   */
  async saveAdditionalNotes(csId: string, notes: string): Promise<ApiResponse<any>> {
    const formData = new FormData();
    formData.append("cs_id", csId);
    formData.append("additional_notes", notes);
    formData.append("csrfmiddlewaretoken", this.csrfToken);

    return this.post("/save_additional_notes", formData, true);
  }

  /**
   * Save buyer's notes
   */
  async saveBuyersNotes(csId: string, notes: string): Promise<ApiResponse<any>> {
    const formData = new FormData();
    formData.append("cs_id", csId);
    formData.append("buyers_notes", notes);
    formData.append("csrfmiddlewaretoken", this.csrfToken);

    return this.post("/save_buyers_notes", formData, true);
  }

  /**
   * Fetch rankings
   */
  async fetchRankings(csId: string): Promise<ApiResponse<any>> {
    return this.get(`/api/cs-rankings/${csId}/`);
  }

  // === UTILITY METHODS ===

  /**
   * Check if API is accessible
   */
  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(buildApiUrl(this.baseUrl, '/health'), {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });
      return response.ok;
    } catch {
      return false;
    }
  }

  /**
   * Get API base URL
   */
  getBaseUrl(): string {
    return this.baseUrl;
  }
}

export default ScheduleApiService;
