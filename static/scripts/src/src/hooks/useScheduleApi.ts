import { useState, useCallback } from 'react';
import { IBid, ICompliance, IComplianceRemark, IPrItems, ICommittee } from '../types/scheduleTypes';

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

export interface UseScheduleApiProps {
  base_url: string;
  setIsLoading: (loading: boolean) => void;
}

export function useScheduleApi({ base_url, setIsLoading }: UseScheduleApiProps) {
  const [error, setError] = useState<string | null>(null);

  /**
   * Fetch Purchase Requisition data
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
        `${base_url}/api/purchase_requisitions/${pr_id}/`,
        requestOptions
      );
      
      return data;
    } catch (err) {
      setError(`Failed to fetch PR: ${err instanceof Error ? err.message : String(err)}`);
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
        `${base_url}/api/restricted_bidding/cs/${cs_id}/`,
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
        `${base_url}/api/restricted_bidding/cs/${cs_id}/items/`,
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
        `${base_url}/api/restricted_bidding/cs/${cs_id}/bids/`,
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
        `${base_url}/api/restricted_bidding/cs/${cs_id}/bids/${bid_count}/`,
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

  return {
    fetchPR,
    fetchCS,
    submitCSItems,
    saveBid,
    deleteBid,
    saveCommittee,
    saveCompliance,
    saveSchedule,
    updateSchedule,
    error
  };
} 