import React, { useEffect, useState, useCallback } from "react";
import { ScheduleProvider } from "../context/ScheduleContext";
import BidManager from "./Bids/BidManager";
import CommitteeManager from "./Committee/CommitteeManager";
import ComplianceChecker from "./Compliance/ComplianceChecker";
import ApprovalWorkflow from "./Approval/ApprovalWorkflow";
import { useScheduleApi } from "../hooks/useScheduleApi";
import { 
  IBid, 
  ICompliance, 
  IComplianceRemark, 
  ISupplier,
  ICommittee,
  IUser
} from "../types/scheduleTypes";

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

// Helper function for fetch with retry
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

export default function Schedule({
  base_url,
  username_,
  prid,
  csid,
}: {
  base_url: string;
  username_: string | null;
  prid: string | null;
  csid: string | null;
}) {
  // State
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [csId, setCsId] = useState<string>("");
  const [creator, setCreator] = useState<string>("");
  const [createdAt, setCreatedAt] = useState<string>("");
  const [suppliers, setSuppliers] = useState<ISupplier[]>([]);
  const [users, setUsers] = useState<IUser[]>([]);
  const [response, setResponse] = useState<{
    open: boolean;
    message: string;
    title: string;
    success: boolean;
  }>({
    open: false,
    message: "",
    title: "",
    success: false,
  });
  
  // API Functions
  const api = useScheduleApi({ base_url, setIsLoading });
  
  // Initialize component
  useEffect(() => {
    const cs_id = csid || '';
    const pr_id = prid || '';
    
    if (cs_id) {
      setCsId(cs_id);
      fetchCS(cs_id);
    } else if (pr_id) {
      onFetchPR(pr_id);
    }
    
    fetchUsers();
  }, [csid, prid]);
  
  // Fetch CS data
  const fetchCS = useCallback(async (cs_id: string) => {
    setIsLoading(true);
    
    try {
      const requestOptions = {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken") ?? "",
        },
      };
      
      const data = await fetchWithRetry(`${base_url}/api/restricted_bidding/cs/${cs_id}/`, requestOptions);
      
      // Extract basic metadata
      setCreator(data.creator || '');
      setCreatedAt(data.created_at || '');
      
    } catch (error) {
      console.error("Error fetching CS:", error);
      onOpenResponse("Error", "Failed to load CS data", false);
    } finally {
      setIsLoading(false);
    }
  }, [base_url]);
  
  // Fetch PR data
  const onFetchPR = useCallback(async (pr_id: string) => {
    setIsLoading(true);
    
    try {
      await api.fetchPR(pr_id);
      
      // Create a new CS
      const createData = await getCreateData(pr_id);
      if (createData && createData.cs_id) {
        setCsId(createData.cs_id);
        fetchCS(createData.cs_id);
      }
    } catch (error) {
      console.error("Error fetching PR:", error);
      onOpenResponse("Error", "Failed to load PR data", false);
    } finally {
      setIsLoading(false);
    }
  }, [api, base_url, fetchCS]);
  
  // Create a new CS
  const getCreateData = useCallback(async (pr_id: string) => {
    try {
      const requestOptions = {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken") ?? "",
        },
        body: JSON.stringify({
          pr_id: pr_id,
        }),
      };
      
      const data = await fetchWithRetry(`${base_url}/api/restricted_bidding/cs/`, requestOptions);
      return data;
    } catch (error) {
      console.error("Error creating CS:", error);
      onOpenResponse("Error", "Failed to create new CS", false);
      return null;
    }
  }, [base_url]);
  
  // Fetch users
  const fetchUsers = useCallback(async () => {
    try {
      const requestOptions = {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken") ?? "",
        },
      };
      
      const data = await fetchWithRetry(`${base_url}/api/users/`, requestOptions);
      
      if (Array.isArray(data)) {
        setUsers(data);
      }
    } catch (error) {
      console.error("Error fetching users:", error);
    }
  }, [base_url]);
  
  // Fetch suppliers
  const fetchSuppliers = useCallback(async () => {
    try {
      const requestOptions = {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken") ?? "",
        },
      };
      
      const data = await fetchWithRetry(`${base_url}/api/suppliers/`, requestOptions);
      
      if (Array.isArray(data)) {
        setSuppliers(data);
      }
    } catch (error) {
      console.error("Error fetching suppliers:", error);
    }
  }, [base_url]);
  
  // Fetch suppliers on component load
  useEffect(() => {
    fetchSuppliers();
  }, [fetchSuppliers]);
  
  // Handle saving a bid
  const handleSaveBid = useCallback(async (bid: IBid) => {
    try {
      const formData = new FormData();
      
      // Append bid data
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
      
      await fetchWithRetry(`${base_url}/api/restricted_bidding/cs/${csId}/bids/`, requestOptions);
      
      // Refresh data
      fetchCS(csId);
      onOpenResponse("Success", "Bid saved successfully", true);
    } catch (error) {
      console.error("Error saving bid:", error);
      onOpenResponse("Error", "Failed to save bid", false);
    }
  }, [csId, base_url, fetchCS]);
  
  // Handle deleting a bid
  const handleDeleteBid = useCallback(async (bid_count: number, supplier_name: string) => {
    try {
      const requestOptions = {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken") ?? "",
        },
      };
      
      await fetchWithRetry(`${base_url}/api/restricted_bidding/cs/${csId}/bids/${bid_count}/`, requestOptions);
      
      // Refresh data
      fetchCS(csId);
      onOpenResponse("Success", `Bid from ${supplier_name} deleted successfully`, true);
    } catch (error) {
      console.error("Error deleting bid:", error);
      onOpenResponse("Error", "Failed to delete bid", false);
    }
  }, [csId, base_url, fetchCS]);
  
  // Handle saving committee
  const handleSaveCommittee = useCallback(async (committee: ICommittee[]) => {
    try {
      const requestOptions = {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken") ?? "",
        },
        body: JSON.stringify({ committee }),
      };
      
      await fetchWithRetry(`${base_url}/api/restricted_bidding/cs/${csId}/committee/`, requestOptions);
      
      // Refresh data
      fetchCS(csId);
      onOpenResponse("Success", "Committee saved successfully", true);
    } catch (error) {
      console.error("Error saving committee:", error);
      onOpenResponse("Error", "Failed to save committee", false);
    }
  }, [csId, base_url, fetchCS]);
  
  // Handle saving compliance
  const handleSaveCompliance = useCallback(async (compliance: ICompliance[], remarks: IComplianceRemark[]) => {
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
      
      await fetchWithRetry(`${base_url}/api/restricted_bidding/cs/${csId}/compliance/`, requestOptions);
      
      // Refresh data
      fetchCS(csId);
      onOpenResponse("Success", "Compliance saved successfully", true);
    } catch (error) {
      console.error("Error saving compliance:", error);
      onOpenResponse("Error", "Failed to save compliance", false);
    }
  }, [csId, base_url, fetchCS]);
  
  // Handle approval action
  const handleApprove = useCallback(async (
    role: string,
    username: string,
    approval: string,
    justification: string
  ) => {
    try {
      const requestOptions = {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken") ?? "",
        },
        body: JSON.stringify({
          role,
          username,
          approval,
          justification,
        }),
      };
      
      await fetchWithRetry(`${base_url}/api/restricted_bidding/cs/${csId}/approval/`, requestOptions);
      
      // Refresh data
      fetchCS(csId);
      onOpenResponse("Success", `Successfully ${approval.toLowerCase()} the schedule`, true);
    } catch (error) {
      console.error("Error during approval:", error);
      onOpenResponse("Error", "Failed to process approval", false);
    }
  }, [csId, base_url, fetchCS]);
  
  // Show response notification
  const onOpenResponse = (title: string, message: string, success: boolean) => {
    setResponse({
      open: true,
      title,
      message,
      success,
    });
  };
  
  // Close response notification
  const onCloseResponse = () => {
    setResponse({
      open: false,
      title: "",
      message: "",
      success: false,
    });
  };

  // Loading indicator
  if (isLoading) {
    return (
      <div className="fixed inset-0 flex items-center justify-center z-50 bg-gray-800 bg-opacity-50">
        <div className="bg-white p-4 rounded-lg shadow-lg flex flex-col items-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-600 mb-3"></div>
          <p className="text-blue-800 font-medium">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <ScheduleProvider 
      base_url={base_url}
      csId={csId}
      username={username_ || ''}
    >
      <div className="px-4 py-5 sm:px-6">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-semibold text-gray-900">Comparative Schedule</h1>
          {csId && (
            <div className="text-sm text-gray-500">
              <p>CS ID: {csId}</p>
              <p>Created by: {creator}</p>
              <p>Created at: {createdAt}</p>
            </div>
          )}
        </div>
        
        <div className="mt-6 border-t border-gray-200 pt-6">
          {/* Main content with tabs for different sections */}
          <div className="grid grid-cols-1 gap-6">
            {/* Bids section */}
            <BidManager
              suppliers={suppliers}
              onSaveBid={handleSaveBid}
              onDeleteBid={handleDeleteBid}
            />
            
            {/* Committee section */}
            <CommitteeManager
              users={users}
              onSaveCommittee={handleSaveCommittee}
            />
            
            {/* Compliance section */}
            <ComplianceChecker
              onSaveCompliance={handleSaveCompliance}
            />
            
            {/* Approval workflow section */}
            <ApprovalWorkflow
              onApprove={handleApprove}
            />
          </div>
        </div>
      </div>
      
      {/* Response notification */}
      {response.open && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 transition-opacity" aria-hidden="true">
              <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
            </div>
            <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <div className="sm:flex sm:items-start">
                  <div className={`mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full ${
                    response.success ? "bg-green-100" : "bg-red-100"
                  } sm:mx-0 sm:h-10 sm:w-10`}>
                    {response.success ? (
                      <svg className="h-6 w-6 text-green-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                      </svg>
                    ) : (
                      <svg className="h-6 w-6 text-red-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    )}
                  </div>
                  <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left">
                    <h3 className="text-lg leading-6 font-medium text-gray-900">
                      {response.title}
                    </h3>
                    <div className="mt-2">
                      <p className="text-sm text-gray-500">
                        {response.message}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                <button
                  type="button"
                  onClick={onCloseResponse}
                  className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:ml-3 sm:w-auto sm:text-sm"
                >
                  OK
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </ScheduleProvider>
  );
}
