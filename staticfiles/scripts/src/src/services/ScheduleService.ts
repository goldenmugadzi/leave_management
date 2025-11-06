import { getApiEndpoints, buildApiUrl } from "../config/apiEndpoints";

export interface IScheduleData {
  cs_id?: string;
  pr_id?: string;
  proc_ref?: string;
  scope_of_work?: string;
  currency_id?: string;
  proc_plan_id?: string;
  pr_number?: string;
  quantity?: string;
  pr_date?: string;
  closing_date?: string;
  ref_date?: string;
  closing_time?: string;
  cs_opened_date?: string;
  username?: string;
  tac_date?: string;
  advert?: string; // Only file paths - file uploads handled by dedicated APIs
  additional_notes?: string;
  buyers_notes?: string;
}

export interface IScheduleResponse {
  success: boolean;
  cs_id?: string;
  cs_owner?: string;
  message?: string;
  error?: string;
}

export class ScheduleService {
  private baseUrl: string;
  private csrfToken: string;

  constructor(baseUrl: string, csrfToken: string) {
    this.baseUrl = baseUrl;
    this.csrfToken = csrfToken;
  }

  /**
   * Save a new comparative schedule
   */
  async saveSchedule(scheduleData: IScheduleData): Promise<IScheduleResponse> {
    try {
      const formData = new FormData();
      
      // Helper function to clean empty values
      const cleanValue = (value: any): any => {
        if (typeof value === 'string' && value.trim() === '') {
          return undefined; // Don't send empty strings
        }
        return value;
      };
      
      // Map frontend field names to backend field names
      const fieldMapping: Record<string, string> = {
        'currency_id': 'currency',
        'proc_plan_id': 'proc_plan',
        'ref_date': 'ref_date',
        'cs_opened_date': 'date_tender_opened',
        'tac_date': 'tender_adjudication_committee_date'
      };
      
      // Append all schedule data with value cleaning and field mapping
      Object.entries(scheduleData).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          // Clean all values to prevent empty string validation errors
          const cleanedValue = cleanValue(value);
          if (cleanedValue !== undefined) {
            // Use mapped field name if available, otherwise use original key
            const backendFieldName = fieldMapping[key] || key;
            
            if (key === 'proc_plan_id') {
              // Only JSON stringify proc_plan_id, not currency_id
              formData.append(backendFieldName, JSON.stringify(cleanedValue));
            } else if (key === 'advert') {
              // Only handle string file paths - file uploads handled by dedicated APIs
              if (typeof cleanedValue === 'string' && cleanedValue.trim()) {
                formData.append(backendFieldName, cleanedValue);
              }
            } else {
              formData.append(backendFieldName, String(cleanedValue));
            }
          }
        }
      });
      
      formData.append("csrfmiddlewaretoken", this.csrfToken);

      const response = await fetch(buildApiUrl(this.baseUrl, getApiEndpoints().CS_SAVE), {
        method: "POST",
        headers: {
          "X-CSRFToken": this.csrfToken,
        },
        body: formData,
      });

      const data = await response.json();
      return data;
    } catch (error) {
      console.error("Error saving schedule:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to save schedule"
      };
    }
  }

  /**
   * Update an existing comparative schedule
   */
  async updateSchedule(csId: string, scheduleData: Partial<IScheduleData>): Promise<IScheduleResponse> {
    try {
      const formData = new FormData();
      formData.append("cs_id", csId);
      
      // Helper function to clean empty values
      const cleanValue = (value: any): any => {
        if (typeof value === 'string' && value.trim() === '') {
          return undefined; // Don't send empty strings
        }
        return value;
      };
      
      // Map frontend field names to backend field names
      const fieldMapping: Record<string, string> = {
        'currency_id': 'currency',
        'proc_plan_id': 'proc_plan',
        'ref_date': 'ref_date',
        'cs_opened_date': 'date_tender_opened',
        'tac_date': 'tender_adjudication_committee_date'
      };
      
      // Append updated data with value cleaning and field mapping
      Object.entries(scheduleData).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          // Clean all values to prevent empty string validation errors
          const cleanedValue = cleanValue(value);
          if (cleanedValue !== undefined) {
            // Use mapped field name if available, otherwise use original key
            const backendFieldName = fieldMapping[key] || key;
            
            if (key === 'proc_plan_id') {
              // Only JSON stringify proc_plan_id, not currency_id
              formData.append(backendFieldName, JSON.stringify(cleanedValue));
            } else if (key === 'advert') {
              // Only handle string file paths - file uploads handled by dedicated APIs
              if (typeof cleanedValue === 'string' && cleanedValue.trim()) {
                formData.append(backendFieldName, cleanedValue);
              }
            } else {
              formData.append(backendFieldName, String(cleanedValue));
            }
          }
        }
      });
      
      formData.append("csrfmiddlewaretoken", this.csrfToken);

      const response = await fetch(buildApiUrl(this.baseUrl, getApiEndpoints().CS_UPDATE()), {
        method: "POST",
        headers: {
          "X-CSRFToken": this.csrfToken,
        },
        body: formData,
      });

      const data = await response.json();
      return data;
    } catch (error) {
      console.error("Error updating schedule:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to update schedule"
      };
    }
  }

  /**
   * Fetch comparative schedule details
   */
  async fetchScheduleDetails(csId: string): Promise<any> {
    try {
      const response = await fetch(buildApiUrl(this.baseUrl, getApiEndpoints().CS_DETAILS(csId)), {
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
      return data;
    } catch (error) {
      console.error("Error fetching schedule details:", error);
      throw error;
    }
  }

  /**
   * Update PR items in a schedule
   */
  async updateScheduleItems(csId: string, prId: string, items: any[]): Promise<IScheduleResponse> {
    try {
      const formData = new FormData();
      formData.append("cs_id", csId);
      formData.append("pr_id", prId);
      formData.append("json_data", JSON.stringify({
        cs_items: items.map(item => ({
          id: item.id,
          item_required: item.name,
          quantity: item.quantity,
          unit_of_measurement: item.unit,
          included: item.included
        }))
      }));
      formData.append("csrfmiddlewaretoken", this.csrfToken);

      const response = await fetch(buildApiUrl(this.baseUrl, getApiEndpoints().CS_UPDATE_ITEMS()), {
        method: "POST",
        headers: {
          "X-CSRFToken": this.csrfToken,
        },
        body: formData,
      });

      const data = await response.json();
      return data;
    } catch (error) {
      console.error("Error updating schedule items:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to update schedule items"
      };
    }
  }

  /**
   * Save additional notes
   */
  async saveAdditionalNotes(csId: string, notes: string): Promise<IScheduleResponse> {
    try {
      const formData = new FormData();
      formData.append("cs_id", csId);
      formData.append("additional_notes", notes);
      formData.append("csrfmiddlewaretoken", this.csrfToken);

      const response = await fetch(buildApiUrl(this.baseUrl, getApiEndpoints().CS_ADDITIONAL_NOTES), {
        method: "POST",
        headers: {
          "X-CSRFToken": this.csrfToken,
        },
        body: formData,
      });

      const data = await response.json();
      return data;
    } catch (error) {
      console.error("Error saving additional notes:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to save additional notes"
      };
    }
  }

  /**
   * Save buyer's notes
   */
  async saveBuyersNotes(csId: string, notes: string): Promise<IScheduleResponse> {
    try {
      const formData = new FormData();
      formData.append("cs_id", csId);
      formData.append("buyers_notes", notes);
      formData.append("csrfmiddlewaretoken", this.csrfToken);

      const response = await fetch(buildApiUrl(this.baseUrl, getApiEndpoints().CS_BUYERS_NOTES), {
        method: "POST",
        headers: {
          "X-CSRFToken": this.csrfToken,
        },
        body: formData,
      });

      const data = await response.json();
      return data;
    } catch (error) {
      console.error("Error saving buyer's notes:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to save buyer's notes"
      };
    }
  }

  /**
   * Close comparative schedule and generate rankings
   */
  async closeSchedule(csId: string): Promise<{ success: boolean; rankings?: any[]; message?: string; error?: string }> {
    try {
      const formData = new FormData();
      formData.append("cs_id", csId);
      formData.append("csrfmiddlewaretoken", this.csrfToken);

      const response = await fetch(buildApiUrl(this.baseUrl, getApiEndpoints().CS_CLOSE_COMPLIANCE), {
        method: "POST",
        headers: {
          "X-CSRFToken": this.csrfToken,
        },
        body: formData,
      });

      const data = await response.json();
      return data;
    } catch (error) {
      console.error("Error closing schedule:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to close schedule"
      };
    }
  }

  /**
   * Fetch reference data (currencies, procurement plans, etc.)
   */
  async fetchReferenceData(): Promise<any> {
    try {
      const response = await fetch(buildApiUrl(this.baseUrl, getApiEndpoints().REFERENCE_DATA()), {
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
      return data;
    } catch (error) {
      console.error("Error fetching reference data:", error);
      throw error;
    }
  }

  /**
   * Fetch users
   */
  async fetchUsers(limit: number = 100): Promise<any[]> {
    try {
      const response = await fetch(buildApiUrl(this.baseUrl, `${getApiEndpoints().USERS}?limit=${limit}`), {
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
      return Array.isArray(data) ? data : [];
    } catch (error) {
      console.error("Error fetching users:", error);
      throw error;
    }
  }

  /**
   * Fetch PR data
   */
  async fetchPR(prId: string): Promise<any> {
    try {
      const response = await fetch(buildApiUrl(this.baseUrl, getApiEndpoints().CS_CREATE_DATA(prId)), {
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
      return data;
    } catch (error) {
      console.error("Error fetching PR data:", error);
      throw error;
    }
  }

  /**
   * Fetch PR items
   */
  async fetchPRItems(prId: string): Promise<any> {
    try {
      const response = await fetch(buildApiUrl(this.baseUrl, getApiEndpoints().PR_ITEMS(prId)), {
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
      return data;
    } catch (error) {
      console.error("Error fetching PR items:", error);
      throw error;
    }
  }
}
