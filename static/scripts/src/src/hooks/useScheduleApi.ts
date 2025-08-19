import { useState, useCallback } from 'react';
import { IBid, ICompliance, IComplianceRemark, IPrItems, ICommittee } from '../types/scheduleTypes';
import { API_ENDPOINTS, getApiEndpoints, buildApiUrl } from '../config/apiEndpoints';
import { getCookie, fetchWithRetry } from '../utils';

export interface UseScheduleApiProps {
  base_url: string;
  setIsLoading: (loading: boolean) => void;
}

export function useScheduleApi({ base_url, setIsLoading }: UseScheduleApiProps) {
  const [error, setError] = useState<string | null>(null);

  /**
   * Fetch Purchase Requisition basic data (focused API)
   */
  const fetchPR = useCallback(async (pr_id: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const requestOptions = {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken") ?? "",
        },
      };
      
      const data = await fetchWithRetry(
                    buildApiUrl(base_url, API_ENDPOINTS.PR_BASIC(pr_id)),
        requestOptions
      );
      console.log("fetchPR basic data: ", data);
      return data;
    } catch (err) {
      setError(`Failed to fetch PR: ${err instanceof Error ? err.message : String(err)}`);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [base_url, setIsLoading]);

  /**
   * Fetch PR Items with pagination (new focused API)
   */
  const fetchPRItems = useCallback(async (pr_id: string, page: number = 1, pageSize: number = 50) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const requestOptions = {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken") ?? "",
        },
      };
      
      const data = await fetchWithRetry(
        buildApiUrl(base_url, `${API_ENDPOINTS.PR_ITEMS(pr_id)}?page=${page}&page_size=${pageSize}`),
        requestOptions
      );
      console.log("fetchPRItems data: ", data);
      return data;
    } catch (err) {
      setError(`Failed to fetch PR items: ${err instanceof Error ? err.message : String(err)}`);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [base_url, setIsLoading]);

  /**
   * Fetch PR Attachments (new focused API)
   */
  const fetchPRAttachments = useCallback(async (pr_id: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const requestOptions = {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken") ?? "",
        },
      };
      
      const data = await fetchWithRetry(
        buildApiUrl(base_url, API_ENDPOINTS.PR_ATTACHMENTS(pr_id)),
        requestOptions
      );
      console.log("fetchPRAttachments data: ", data);
      return data;
    } catch (err) {
      setError(`Failed to fetch PR attachments: ${err instanceof Error ? err.message : String(err)}`);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [base_url, setIsLoading]);

  /**
   * Fetch Reference Data (new focused API)
   */
  const fetchReferenceData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const requestOptions = {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken") ?? "",
        },
      };
      
      const data = await fetchWithRetry(
        buildApiUrl(base_url, API_ENDPOINTS.REFERENCE_DATA()),
        requestOptions
      );
      console.log("fetchReferenceData data: ", data);
      return data;
    } catch (err) {
      setError(`Failed to fetch reference data: ${err instanceof Error ? err.message : String(err)}`);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [base_url, setIsLoading]);

  /**
   * Fetch CS data
   */
  const fetchCS = useCallback(async (cs_id: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const requestOptions = {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken") ?? "",
        },
      };
      
      const data = await fetchWithRetry(
        buildApiUrl(base_url, `/cs_data/${cs_id}`),
        requestOptions
      );
      
      return data;
    } catch (err) {
      setError(`Failed to fetch CS: ${err instanceof Error ? err.message : String(err)}`);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [base_url, setIsLoading]);

  /**
   * Submit CS Items
   */
  const submitCSItems = useCallback(async (cs_id: string, items: IPrItems[]) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const requestOptions = {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken") ?? "",
        },
        body: JSON.stringify({ 
          items 
        }),
      };
      
      const data = await fetchWithRetry(
        buildApiUrl(base_url, getApiEndpoints().CS_ITEMS(cs_id)),
        requestOptions
      );
      
      return data;
    } catch (err) {
      setError(`Failed to submit CS items: ${err instanceof Error ? err.message : String(err)}`);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [base_url, setIsLoading]);

  /**
   * Save bids
   */
  const saveBid = useCallback(async (cs_id: string, bid: IBid) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const formData = new FormData();
      
      // Append bid data as JSON
      const bidWithoutFile = { ...bid };
      delete bidWithoutFile.bid_document;
      
      formData.append('bid_data', JSON.stringify(bidWithoutFile));
      
      // Append file if present
      if (bid.bid_document) {
        formData.append('bid_document', bid.bid_document);
      }
      
      const requestOptions = {
        method: "POST",
        headers: {
          "X-CSRFToken": getCookie("csrftoken") ?? "",
        },
        body: formData,
      };
      
      const data = await fetchWithRetry(
        buildApiUrl(base_url, getApiEndpoints().CS_BIDS(cs_id)),
        requestOptions
      );
      
      return data;
    } catch (err) {
      setError(`Failed to save bid: ${err instanceof Error ? err.message : String(err)}`);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [base_url, setIsLoading]);

  /**
   * Delete bid
   */
  const deleteBid = useCallback(async (cs_id: string, bid_count: number) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const requestOptions = {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken") ?? "",
        },
      };
      
      await fetchWithRetry(
        buildApiUrl(base_url, getApiEndpoints().CS_BID_DELETE(cs_id, bid_count)),
        requestOptions
      );
      
      return true;
    } catch (err) {
      setError(`Failed to delete bid: ${err instanceof Error ? err.message : String(err)}`);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [base_url, setIsLoading]);

  /**
   * Save committee
   */
  const saveCommittee = useCallback(async (cs_id: string, committee: ICommittee[]) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const requestOptions = {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken") ?? "",
        },
        body: JSON.stringify({ committee }),
      };
      
      const data = await fetchWithRetry(
        `${base_url}/api/restricted_bidding/cs/${cs_id}/committee/`,
        requestOptions
      );
      
      return data;
    } catch (err) {
      setError(`Failed to save committee: ${err instanceof Error ? err.message : String(err)}`);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [base_url, setIsLoading]);

  /**
   * Save compliance
   */
  const saveCompliance = useCallback(async (cs_id: string, compliance: ICompliance[], remarks: IComplianceRemark[]) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const requestOptions = {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken") ?? "",
        },
        body: JSON.stringify({ 
          compliance,
          remarks
        }),
      };
      
      const data = await fetchWithRetry(
        `${base_url}/api/restricted_bidding/cs/${cs_id}/compliance/`,
        requestOptions
      );
      
      return data;
    } catch (err) {
      setError(`Failed to save compliance: ${err instanceof Error ? err.message : String(err)}`);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [base_url, setIsLoading]);

  /**
   * Save schedule
   */
  const saveSchedule = useCallback(async (cs_id: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const requestOptions = {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken") ?? "",
        },
      };
      
      const data = await fetchWithRetry(
        `${base_url}/api/restricted_bidding/cs/${cs_id}/save/`,
        requestOptions
      );
      
      return data;
    } catch (err) {
      setError(`Failed to save schedule: ${err instanceof Error ? err.message : String(err)}`);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [base_url, setIsLoading]);

  /**
   * Update schedule
   */
  const updateSchedule = useCallback(async (cs_id: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const requestOptions = {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken") ?? "",
        },
      };
      
      const data = await fetchWithRetry(
        `${base_url}/api/restricted_bidding/cs/${cs_id}/update/`,
        requestOptions
      );
      
      return data;
    } catch (err) {
      setError(`Failed to update schedule: ${err instanceof Error ? err.message : String(err)}`);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [base_url, setIsLoading]);

  /**
   * Upload file using optimized handler
   */
  const uploadFile = useCallback(async (file: File, fileType: string = 'general', description?: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('file_type', fileType);
      if (description) {
        formData.append('description', description);
      }
      
      const requestOptions = {
        method: "POST",
        headers: {
          "X-CSRFToken": getCookie("csrftoken") ?? "",
        },
        body: formData,
      };
      
      const data = await fetchWithRetry(
        buildApiUrl(base_url, API_ENDPOINTS.FILE_UPLOAD()),
        requestOptions
      );
      
      return data;
    } catch (err) {
      setError(`Failed to upload file: ${err instanceof Error ? err.message : String(err)}`);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [base_url, setIsLoading]);

  /**
   * Get CS files metadata
   */
  const getCSFiles = useCallback(async (cs_id: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const requestOptions = {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken") ?? "",
        },
      };
      
      const data = await fetchWithRetry(
        buildApiUrl(base_url, API_ENDPOINTS.CS_FILES(cs_id)),
        requestOptions
      );
      
      return data;
    } catch (err) {
      setError(`Failed to get CS files: ${err instanceof Error ? err.message : String(err)}`);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [base_url, setIsLoading]);

  /**
   * Delete file using optimized handler
   */
  const deleteFile = useCallback(async (filePath: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const requestOptions = {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken") ?? "",
        },
      };
      
      const data = await fetchWithRetry(
        buildApiUrl(base_url, API_ENDPOINTS.FILE_DELETE(filePath)),
        requestOptions
      );
      
      return data;
    } catch (err) {
      setError(`Failed to delete file: ${err instanceof Error ? err.message : String(err)}`);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [base_url, setIsLoading]);

  return {
    fetchPR,
    fetchPRItems,
    fetchPRAttachments,
    fetchReferenceData,
    fetchCS,
    submitCSItems,
    saveBid,
    deleteBid,
    saveCommittee,
    saveCompliance,
    saveSchedule,
    updateSchedule,
    uploadFile,
    getCSFiles,
    deleteFile,
    error
  };
} 