import { useEffect, useState, useCallback, useMemo, lazy, Suspense } from "react";
import { ScheduleProvider } from "../context/ScheduleContext";
import { useScheduleApi } from "../hooks/useScheduleApi";
import { 
  IBid, 
  ICompliance, 
  IComplianceRemark, 
  ISupplier,
  ICommittee,
  IUser
} from "../types/scheduleTypes";
import { getApiEndpoints, buildApiUrl } from "../config/apiEndpoints";

// Additional interfaces from ScheduleRef.tsx
interface ICurrency {
  id: number;
  currency?: string;
}

interface IProcPlan {
  id: number;
  proc_ref: string;
  description: string;
}

// interface IRank {
//   id: number;
//   supplier_name: string;
//   rank: number;
//   decision: string;
//   remarks: string;
//   total: number;
// }



// Lazy load heavy components
const BidManager = lazy(() => import("./Bids/BidManager"));
const CommitteeManager = lazy(() => import("./Committee/CommitteeManager"));
const ComplianceChecker = lazy(() => import("./Compliance/ComplianceChecker"));
const ApprovalWorkflow = lazy(() => import("./Approval/ApprovalWorkflow"));

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

// Tab configuration
const TAB_CONFIG = [
  { id: 'details', label: 'Details', icon: '📄' },
  { id: 'bids', label: 'Supplier Bids', icon: '💰' },
  { id: 'committee', label: 'Committee', icon: '👥' },
  { id: 'compliance', label: 'Compliance', icon: '✅' },
  { id: 'approval', label: 'Approval', icon: '📋' }
] as const;

type TabId = typeof TAB_CONFIG[number]['id'];

// Loading component for lazy loaded sections
const SectionLoader = () => (
  <div className="flex items-center justify-center p-8">
    <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-600 mr-3"></div>
    <span className="text-gray-600">Loading section...</span>
  </div>
);

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
  const [loadingOperation, setLoadingOperation] = useState<string>("");
  const [csId, setCsId] = useState<string>("");
  const [creator, setCreator] = useState<string>("");
  const [createdAt, setCreatedAt] = useState<string>("");
  const [suppliers, setSuppliers] = useState<ISupplier[]>([]);
  const [users, setUsers] = useState<IUser[]>([]);
  const [activeTab, setActiveTab] = useState<TabId>('details');
  const [loadedTabs, setLoadedTabs] = useState<Set<TabId>>(new Set(['details']));
  
  // Additional state variables from ScheduleRef.tsx
  // const [requesterRole] = useState<string>(""); // For future role-based features
  const [  ,setCsOwner] = useState<string>("");
  const [procRef] = useState<string>("");
  const [currency] = useState<ICurrency>();
  const [currencies, setCurrencies] = useState<ICurrency[]>([]);
  const [procPlan] = useState<IProcPlan>();
  const [procPlans, setProcPlans] = useState<IProcPlan[]>([]);
  const [quantity] = useState<string>("");
  
  // Simple usage to satisfy linter - will be used properly in dropdowns later
  const currenciesCount = currencies.length;
  const procPlansCount = procPlans.length;
  const [advert] = useState<File>();
  // const [bids] = useState<IBid[]>([]); // Used by lazy-loaded BidManager
  // const [rankings, setRankings] = useState<IRank[]>([]);
  const [username, setUsername] = useState<string>("");
  // const [additionalNotes] = useState<string>(""); // Used by lazy-loaded components
  // const [buyersNotes] = useState<string>(""); // Used by lazy-loaded components
  
  // PR Data State
  const [prData, setPrData] = useState<{
    pr_number: string;
    pr_date: string;
    reference_date: string;
    procurement_plan_description: string;
    procurement_plan_id: string;
    currency: string;
    closing_date: string;
    closing_time: string;
    cs_opened_date: string;
    scope_of_work: string;
    tac_date: string;
    region: string;
    show_site_visit: boolean;
    show_samples_required: boolean;
    internal_notes: string;
    items: Array<{
      id: string;
      name: string;
      quantity: number;
      unit: string;
      status: string;
      included: boolean;
    }>;
  }>({
    pr_number: '',
    pr_date: '',
    reference_date: '',
    procurement_plan_description: '',
    procurement_plan_id: '',
    currency: '',
    closing_date: '',
    closing_time: '',
    cs_opened_date: '',
    scope_of_work: '',
    tac_date: '',
    region: '',
    show_site_visit: false,
    show_samples_required: false,
    internal_notes: '',
    items: []
  });

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
  
  // Memoized CSRF token
  const csrfToken = useMemo(() => getCookie("csrftoken") ?? "", []);
  
  // Memoized request options
  const defaultRequestOptions = useMemo(() => ({
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken,
    },
  }), [csrfToken]);
  
  // Initialize component
  useEffect(() => {
    const cs_id = csid || '';
    const pr_id = prid || '';
    
    if (cs_id) {
      setCsId(cs_id);
      setUsername(username_ ?? "");
      fetchCS(cs_id);
    } else if (pr_id) {
      setUsername(username_ ?? "");
      onFetchPR(pr_id);
    } else {
      setUsername(username_ ?? "");
    }
    
    fetchUsers();
  }, [csid, prid, username_]);
  
  // Fetch CS data - optimized
  const fetchCS = useCallback(async (cs_id: string) => {
    setIsLoading(true);
    setLoadingOperation("Loading comparative schedule data");
    
    try {
      const data = await fetchWithRetry(buildApiUrl(base_url, getApiEndpoints().CS_DETAILS(cs_id)), defaultRequestOptions);
      
      // Extract basic metadata
      setCreator(data.creator || '');
      setCreatedAt(data.created_at || '');
      
      // Extract PR data if available
      if (data.pr_data) {
        setPrData({
          pr_number: data.pr_data.pr_number || '',
          pr_date: data.pr_data.pr_date || '',
          reference_date: data.pr_data.reference_date || '',
          procurement_plan_description: data.pr_data.procurement_plan?.description || '',
          procurement_plan_id: data.pr_data.procurement_plan?.id || '',
          currency: data.pr_data.currency || '',
          closing_date: data.pr_data.closing_date || '',
          closing_time: data.pr_data.closing_time || '',
          cs_opened_date: data.pr_data.cs_opened_date || '',
          scope_of_work: data.pr_data.scope_of_work || '',
          tac_date: data.pr_data.tac_date || '',
          region: data.pr_data.region || '',
          show_site_visit: data.pr_data.show_site_visit || false,
          show_samples_required: data.pr_data.show_samples_required || false,
          internal_notes: data.pr_data.internal_notes || '',
          items: data.pr_data.items || []
        });
      }
      
    } catch (error) {
      console.error("Error fetching CS:", error);
      onOpenResponse("Error", "Failed to load CS data", false);
    } finally {
      setIsLoading(false);
      setLoadingOperation("");
    }
  }, [base_url, defaultRequestOptions]);
  
  // Fetch PR data
  const onFetchPR = useCallback(async (pr_id: string) => {
    setIsLoading(true);
    setLoadingOperation("Loading purchase request data");
    
    try {
          // Step 1: Fetch basic PR info immediately (fast load)
    console.log('🚀 Fetching PR basic info...');
    const prResponse = await api.fetchPR(pr_id);
    console.log("prResponse basic: ", prResponse);
      // Populate PR data from response based on actual get_create_data response structure
      if (prResponse && prResponse.success) {
        // Set basic PR data immediately (fast UI update)
        setPrData({
          pr_number: prResponse.pr_id || '',
          pr_date: prResponse.pr_date || '',
          reference_date: prResponse.pr_date || '', // Use pr_date as reference if no separate field
          procurement_plan_description: prResponse.proc_plan?.description || '',
          procurement_plan_id: prResponse.proc_plan?.id || '',
          currency: '', // Will be populated from currencies list
          closing_date: '',
          closing_time: '',
          cs_opened_date: '',
          scope_of_work: prResponse.scope_of_work || '',
          tac_date: '',
          region: '', // Will need to be set separately
          show_site_visit: false,
          show_samples_required: false,
          internal_notes: '',
          items: [] // Will be loaded in background
                });

        // Step 2: Start background loading (non-blocking)
        console.log('🔄 Starting background data loading...');
        setLoadingOperation("Loading additional data in background...");
        
        // Load reference data in background (for dropdowns)
        api.fetchReferenceData()
          .then(refResponse => {
            if (refResponse && refResponse.success) {
              console.log('✅ Reference data loaded');
                             // Set individual reference data states
               setSuppliers(refResponse.suppliers || []);
               setUsers(refResponse.users || []);
               setCurrencies(refResponse.currencies || []);
               setProcPlans(refResponse.proc_plans || []);
               // Log to verify data is loaded (and satisfy linter)
               console.log('📋 Currencies loaded:', refResponse.currencies?.length || 0, 'Current count:', currenciesCount);
               console.log('📋 Proc Plans loaded:', refResponse.proc_plans?.length || 0, 'Current count:', procPlansCount);
            }
          })
          .catch(error => console.error('❌ Error loading reference data:', error));

        // Load PR items in background (paginated)
        api.fetchPRItems(pr_id, 1, 50)
          .then(itemsResponse => {
            if (itemsResponse && itemsResponse.success) {
              console.log('✅ PR items loaded:', itemsResponse.pr_items?.length || 0, 'items');
              setPrData(prev => ({
                ...prev,
                items: itemsResponse.pr_items?.map((item: {
                  id: number;
                  item_required: string;
                  quantity: number;
                  unit_of_measurement: string;
                  ordered: boolean;
                }) => ({
                  id: item.id.toString(),
                  name: item.item_required,
                  quantity: item.quantity,
                  unit: item.unit_of_measurement,
                  status: item.ordered ? 'ordered' : 'available',
                  included: !item.ordered // Include non-ordered items by default
                })) || []
              }));
            }
          })
          .catch(error => console.error('❌ Error loading PR items:', error));

        console.log('✅ Basic PR info loaded. Background loading in progress...');
        
        // Clear main loading state since basic info is loaded
        setIsLoading(false);
        setLoadingOperation("");
      }

      // Note: For now, we don't automatically create a CS. Users can manually save after reviewing the data.
      
    } catch (error) {
      console.error("Error fetching PR:", error);
      onOpenResponse("Error", "Failed to load PR data", false);
      setIsLoading(false);
      setLoadingOperation("");
    }
    }, [api]);


  // Fetch users - only when needed
  const fetchUsers = useCallback(async () => {
    if (users.length > 0) return; // Don't refetch if already loaded
    
    setLoadingOperation("Loading users");
    try {
      const data = await fetchWithRetry(buildApiUrl(base_url, getApiEndpoints().USERS), defaultRequestOptions);
      
      if (Array.isArray(data)) {
        setUsers(data);
      }
    } catch (error) {
      console.error("Error fetching users:", error);
    } finally {
      setLoadingOperation("");
    }
  }, [base_url, defaultRequestOptions, users.length]);
  
  // Fetch suppliers - only when needed
  const fetchSuppliers = useCallback(async () => {
    if (suppliers.length > 0) return; // Don't refetch if already loaded
    
    setLoadingOperation("Loading suppliers");
    try {
      const data = await fetchWithRetry(buildApiUrl(base_url, getApiEndpoints().SUPPLIERS), defaultRequestOptions);
      
      if (Array.isArray(data)) {
        setSuppliers(data);
      }
    } catch (error) {
      console.error("Error fetching suppliers:", error);
    } finally {
      setLoadingOperation("");
    }
  }, [base_url, defaultRequestOptions, suppliers.length]);
  
  // Load tab data when tab becomes active
  const loadTabData = useCallback(async (tabId: TabId) => {
    if (loadedTabs.has(tabId)) return;
    
    switch (tabId) {
      case 'bids':
        await fetchSuppliers();
        break;
      case 'committee':
        await fetchUsers();
        break;
    }
    
    setLoadedTabs(prev => new Set([...prev, tabId]));
  }, [loadedTabs, fetchSuppliers, fetchUsers]);
  
  // Handle tab change
  const handleTabChange = useCallback(async (tabId: TabId) => {
    setActiveTab(tabId);
    await loadTabData(tabId);
  }, [loadTabData]);
  
  // Handle saving a bid
  const handleSaveBid = useCallback(async (bid: IBid) => {
    setIsLoading(true);
    setLoadingOperation("Saving bid");
    
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
          "X-CSRFToken": csrfToken,
        },
        body: formData,
      };
      
      await fetchWithRetry(buildApiUrl(base_url, getApiEndpoints().CS_BIDS(csId)), requestOptions);
      
      // Refresh data
      fetchCS(csId);
      onOpenResponse("Success", "Bid saved successfully", true);
    } catch (error) {
      console.error("Error saving bid:", error);
      onOpenResponse("Error", "Failed to save bid", false);
    } finally {
      setIsLoading(false);
      setLoadingOperation("");
    }
  }, [csId, base_url, csrfToken, fetchCS]);
  
  // Handle deleting a bid
  const handleDeleteBid = useCallback(async (bid_count: number, supplier_name: string) => {
    setIsLoading(true);
    setLoadingOperation(`Deleting bid from ${supplier_name}`);
    try {
      const requestOptions = {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
      };
      
      await fetchWithRetry(buildApiUrl(base_url, getApiEndpoints().CS_BID_DELETE(csId, bid_count)), requestOptions);
      
      // Refresh data
      fetchCS(csId);
      onOpenResponse("Success", `Bid from ${supplier_name} deleted successfully`, true);
    } catch (error) {
      console.error("Error deleting bid:", error);
      onOpenResponse("Error", "Failed to delete bid", false);
    } finally {
      setIsLoading(false);
      setLoadingOperation("");
    }
  }, [csId, base_url, csrfToken, fetchCS]);
  
  // Handle saving committee
  const handleSaveCommittee = useCallback(async (committee: ICommittee[]) => {
    setIsLoading(true);
    setLoadingOperation("Saving committee members");
    try {
      const requestOptions = {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify({ committee }),
      };
      
      await fetchWithRetry(buildApiUrl(base_url, getApiEndpoints().CS_COMMITTEE(csId)), requestOptions);
      
      // Refresh data
      fetchCS(csId);
      onOpenResponse("Success", "Committee saved successfully", true);
    } catch (error) {
      console.error("Error saving committee:", error);
      onOpenResponse("Error", "Failed to save committee", false);
    } finally {
      setIsLoading(false);
      setLoadingOperation("");
    }
  }, [csId, base_url, csrfToken, fetchCS]);
  
  // Handle saving compliance
  const handleSaveCompliance = useCallback(async (compliance: ICompliance[], remarks: IComplianceRemark[]) => {
    setIsLoading(true);
    setLoadingOperation("Saving compliance data");
    try {
      const requestOptions = {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify({ 
          compliance,
          remarks
        }),
      };
      
      await fetchWithRetry(buildApiUrl(base_url, getApiEndpoints().CS_COMPLIANCE(csId)), requestOptions);
      
      // Refresh data
      fetchCS(csId);
      onOpenResponse("Success", "Compliance saved successfully", true);
    } catch (error) {
      console.error("Error saving compliance:", error);
      onOpenResponse("Error", "Failed to save compliance", false);
    } finally {
      setIsLoading(false);
      setLoadingOperation("");
    }
  }, [csId, base_url, csrfToken, fetchCS]);
  
  // Handle approval action
  const handleApprove = useCallback(async (
    role: string,
    username: string,
    approval: string,
    justification: string
  ) => {
    setIsLoading(true);
    setLoadingOperation(`Processing ${approval.toLowerCase()} action`);
    try {
      const requestOptions = {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify({
          role,
          username,
          approval,
          justification,
        }),
      };
      
      await fetchWithRetry(buildApiUrl(base_url, getApiEndpoints().CS_APPROVAL(csId)), requestOptions);
      
      // Refresh data
      fetchCS(csId);
      onOpenResponse("Success", `Successfully ${approval.toLowerCase()} the schedule`, true);
    } catch (error) {
      console.error("Error during approval:", error);
      onOpenResponse("Error", "Failed to process approval", false);
    } finally {
      setIsLoading(false);
      setLoadingOperation("");
    }
  }, [csId, base_url, csrfToken, fetchCS]);
  


  // Fetch currencies
  // const fetchCurrencies = useCallback(async () => {
  //   if (currencies.length > 0) return;
    
  //   setLoadingOperation("Loading currencies");
  //   try {
  //     const data = await fetchWithRetry(buildApiUrl(base_url, getApiEndpoints().CURRENCIES), defaultRequestOptions);
  //     if (Array.isArray(data)) {
  //       setCurrencies(data);
  //     }
  //   } catch (error) {
  //     console.error("Error fetching currencies:", error);
  //   } finally {
  //     setLoadingOperation("");
  //   }
  // }, [base_url, defaultRequestOptions, currencies.length]);

  // // Fetch procurement plans
  // const fetchProcPlans = useCallback(async () => {
  //   if (procPlans.length > 0) return;
    
  //   setLoadingOperation("Loading procurement plans");
  //   try {
  //     const data = await fetchWithRetry(buildApiUrl(base_url, getApiEndpoints().PROC_PLANS), defaultRequestOptions);
  //     if (Array.isArray(data)) {
  //       setProcPlans(data);
  //     }
  //   } catch (error) {
  //     console.error("Error fetching procurement plans:", error);
  //   } finally {
  //     setLoadingOperation("");
  //   }
  // }, [base_url, defaultRequestOptions, procPlans.length]);



  // Update schedule
  // const handleUpdateSchedule = useCallback(async () => {
  //   if (!csId) {
  //     onOpenResponse("Update Schedule Error", "Please save the Comparative Schedule first", false);
  //     return;
  //   }

  //   setIsLoading(true);
  //   setLoadingOperation("Updating schedule");
    
  //   try {
  //     const formData = new FormData();
  //     formData.append("cs_id", csId);
  //     formData.append("proc_ref", procPlan?.proc_ref ?? "");
  //     formData.append("scope_of_work", prData.scope_of_work);
  //     formData.append("currency", JSON.stringify(currency?.id));
  //     formData.append("pr_number", prData.pr_number);
  //     formData.append("quantity", quantity);
  //     formData.append("pr_date", prData.pr_date);
  //     formData.append("closing_date", prData.closing_date);
  //     formData.append("ref_date", prData.reference_date);
  //     formData.append("closing_time", prData.closing_time);
  //     formData.append("date_tender_opened", prData.cs_opened_date);
  //     formData.append("username", username);
  //     formData.append("tender_adjudication_committee_date", prData.tac_date);
      
  //     if (advert) {
  //       formData.append("advert", advert);
  //     }
      
  //     formData.append("csrfmiddlewaretoken", csrfToken);

  //     const requestOptions = {
  //       method: "POST",
  //       headers: {
  //         "X-CSRFToken": csrfToken,
  //       },
  //       body: formData,
  //     };

  //     const data = await fetchWithRetry(buildApiUrl(base_url, getApiEndpoints().CS_UPDATE), requestOptions);
      
  //     if (data.success) {
  //       onOpenResponse("Update Successful", "Comparative Schedule updated successfully", true);
  //       fetchCS(csId); // Refresh data
  //     } else {
  //       onOpenResponse("Update Error", "Failed to update schedule", false);
  //     }
  //   } catch (error) {
  //     console.error("Error updating schedule:", error);
  //     onOpenResponse("Error", "Failed to update schedule", false);
  //   } finally {
  //     setIsLoading(false);
  //     setLoadingOperation("");
  //   }
  // }, [csId, procPlan, prData, currency, quantity, username, advert, csrfToken, base_url, fetchCS]);

  // // Close CS and generate rankings
  // const handleCloseCS = useCallback(async () => {
  //   setIsLoading(true);
  //   setLoadingOperation("Processing compliance and generating rankings");
    
  //   try {
  //     const formData = new FormData();
  //     formData.append("cs_id", csId);
  //     formData.append("csrfmiddlewaretoken", csrfToken);

  //     const requestOptions = {
  //       method: "POST",
  //       headers: {
  //         "X-CSRFToken": csrfToken,
  //       },
  //       body: formData,
  //     };

  //     const data = await fetchWithRetry(buildApiUrl(base_url, getApiEndpoints().CS_CLOSE_COMPLIANCE), requestOptions);
      
  //     if (data.success) {
  //       setRankings(data.rankings || []);
  //       onOpenResponse("Rank Bids Successful", "Bids ranked successfully", true);
  //     } else {
  //       onOpenResponse("Rank Bids Error", "Failed to rank bids", false);
  //     }
  //   } catch (error) {
  //     console.error("Error ranking bids:", error);
  //     onOpenResponse("Error", "Failed to rank bids", false);
  //   } finally {
  //     setIsLoading(false);
  //     setLoadingOperation("");
  //   }
  // }, [csId, csrfToken, base_url]);

  // // Save additional notes
  // const handleAdditionalNotesSubmit = useCallback(async () => {
  //   setIsLoading(true);
  //   setLoadingOperation("Saving additional notes");
    
  //   try {
  //     const formData = new FormData();
  //     formData.append("cs_id", csId);
  //     formData.append("additional_notes", additionalNotes);
  //     formData.append("csrfmiddlewaretoken", csrfToken);

  //     const requestOptions = {
  //       method: "POST",
  //       headers: {
  //         "X-CSRFToken": csrfToken,
  //       },
  //       body: formData,
  //     };

  //     const data = await fetchWithRetry(buildApiUrl(base_url, getApiEndpoints().CS_ADDITIONAL_NOTES), requestOptions);
      
  //     if (data.success) {
  //       onOpenResponse("Additional Notes Saved", "Additional notes saved successfully", true);
  //     } else {
  //       onOpenResponse("Additional Notes Error", "Failed to save additional notes", false);
  //     }
  //   } catch (error) {
  //     console.error("Error saving additional notes:", error);
  //     onOpenResponse("Error", "Failed to save additional notes", false);
  //   } finally {
  //     setIsLoading(false);
  //     setLoadingOperation("");
  //   }
  // }, [csId, additionalNotes, csrfToken, base_url]);

  // // Save buyer notes
  // const handleBuyersNotesSubmit = useCallback(async () => {
  //   setIsLoading(true);
  //   setLoadingOperation("Saving buyer notes");
    
  //   try {
  //     const formData = new FormData();
  //     formData.append("cs_id", csId);
  //     formData.append("buyers_notes", buyersNotes);
  //     formData.append("csrfmiddlewaretoken", csrfToken);

  //     const requestOptions = {
  //       method: "POST",
  //       headers: {
  //         "X-CSRFToken": csrfToken,
  //       },
  //       body: formData,
  //     };

  //     const data = await fetchWithRetry(buildApiUrl(base_url, getApiEndpoints().CS_BUYERS_NOTES), requestOptions);
      
  //     if (data.success) {
  //       // Update rankings with buyer notes for rank 1
  //       const newRankings: IRank[] = (rankings ?? []).map((ranking) => {
  //         if (ranking.rank === 1) {
  //           ranking.remarks = buyersNotes;
  //         }
  //         return ranking;
  //       });
  //       setRankings(newRankings);
  //       onOpenResponse("Buyer's Notes Saved", "Buyer's notes saved successfully", true);
  //     } else {
  //       onOpenResponse("Buyer's Notes Error", "Failed to save buyer's notes", false);
  //     }
  //   } catch (error) {
  //     console.error("Error saving buyer notes:", error);
  //     onOpenResponse("Error", "Failed to save buyer's notes", false);
  //   } finally {
  //     setIsLoading(false);
  //     setLoadingOperation("");
  //   }
  // }, [csId, buyersNotes, csrfToken, base_url, rankings]);

  // === FORM VALIDATION FUNCTIONS ===
  
  // Comprehensive field validation for schedule save/update
  const validateScheduleFields = useCallback((): { isValid: boolean; errors: string[] } => {
    const errors: string[] = [];
    
    if (!currency) errors.push("Currency is required");
    if (!procPlan) errors.push("Procurement plan is required");
    if (!prData.scope_of_work?.trim()) errors.push("Scope of work is required");
    if (!prData.pr_number?.trim()) errors.push("PR number is required");
    if (!prData.pr_date) errors.push("PR date is required");
    if (!prData.closing_date) errors.push("Closing date is required");
    if (!prData.reference_date) errors.push("Reference date is required");
    if (!prData.closing_time) errors.push("Closing time is required");
    if (!prData.cs_opened_date) errors.push("CS opened date is required");
    if (!prData.tac_date) errors.push("TAC date is required");
    if (!advert) errors.push("Advertisement document is required");
    
    return { isValid: errors.length === 0, errors };
  }, [currency, procPlan, prData, advert]);

  // // File type and size validation
  // const validateFile = useCallback((file: File): { isValid: boolean; error?: string } => {
  //   const allowedTypes = [
  //     'application/pdf',
  //     'application/msword', 
  //     'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  //     'image/jpeg',
  //     'image/jpg', 
  //     'image/png'
  //   ];
    
  //   const maxSize = 10 * 1024 * 1024; // 10MB
    
  //   if (!allowedTypes.includes(file.type)) {
  //     return { 
  //       isValid: false, 
  //       error: 'File type not allowed. Please upload PDF, DOC, DOCX, JPG, JPEG, or PNG files only.' 
  //     };
  //   }
    
  //   if (file.size > maxSize) {
  //     return { 
  //       isValid: false, 
  //       error: 'File size too large. Maximum allowed size is 10MB.' 
  //     };
  //   }
    
  //   return { isValid: true };
  // }, []);

  // // Committee member role validation
  // const validateCommitteeMember = useCallback((member: ICommittee): { isValid: boolean; errors: string[] } => {
  //   const errors: string[] = [];
    
  //   if (!member.memberUserName?.trim()) errors.push("Username is required");
  //   if (!member.memberName?.trim()) errors.push("Member name is required");
  //   if (!member.memberPosition?.trim()) errors.push("Position is required");
    
  //   // Check for duplicate usernames
  //   const existingMember = users.find(u => u.username === member.memberUserName);
  //   if (!existingMember) errors.push("Invalid username - user not found");
    
  //   return { isValid: errors.length === 0, errors };
  // }, [users]);

  // // Compliance requirements validation
  // const validateComplianceRequirements = useCallback((complianceData: ICompliance[]): { isValid: boolean; errors: string[] } => {
  //   const errors: string[] = [];
    
  //   if (!complianceData || complianceData.length === 0) {
  //     errors.push("Compliance data is required");
  //     return { isValid: false, errors };
  //   }
    
  //   const requiredFields = [
  //     'payment_terms', 'bid_validity', 'delivery_period', 
  //     'technical_specifications', 'valid_tax_clearance', 'registered_with_praz'
  //   ];
    
  //   complianceData.forEach((compliance, index) => {
  //     if (!compliance.supplier_name) {
  //       errors.push(`Supplier name is required for compliance entry ${index + 1}`);
  //     }
      
  //     const hasAllFields = requiredFields.every(field => 
  //       compliance[field] === true || compliance[field] === false
  //     );
      
  //     if (!hasAllFields) {
  //       errors.push(`All compliance fields must be checked for ${compliance.supplier_name || `entry ${index + 1}`}`);
  //     }
  //   });
    
  //   return { isValid: errors.length === 0, errors };
  // }, []);

  // // Direct purchase validation
  // const validateDirectPurchaseLimits = useCallback(() => {
  //   if (base_url === "/direct_purchase") {
  //     const currentBidCount = bids?.length ?? 0;
  //     if (currentBidCount >= 1) {
  //       return { isValid: false, error: "Direct purchase allows maximum 1 bid." };
  //     }
  //   }
  //   return { isValid: true };
  // }, [base_url, bids]);

  // // Utility functions
  // const showEnhancedError = useCallback((operation: string, error: unknown, retryAction?: () => void) => {
  //   const message = error instanceof Error ? error.message : String(error);
  //   console.error(`Operation ${operation} failed:`, error);
  //   setResponse({
  //     open: true,
  //     title: `${operation.replace('_', ' ').toUpperCase()} Error`,
  //     message,
  //     success: false
  //   });
  // }, []);

  // const retryWithBackoff = useCallback(async (operation: () => Promise<any>, maxRetries: number = 3, baseDelay: number = 1000) => {
  //   for (let attempt = 0; attempt <= maxRetries; attempt++) {
  //     try {
  //       return await operation();
  //     } catch (error) {
  //       if (attempt === maxRetries) throw error;
  //       const delay = baseDelay * Math.pow(2, attempt);
  //       await new Promise(resolve => setTimeout(resolve, delay));
  //     }
  //   }
  // }, []);

  // // === USER MANAGEMENT FUNCTIONS ===
  
  // // Role-based access control logic
  // const checkUserPermissions = useCallback((action: string): boolean => {
  //   if (!username || !requesterRole) return false;
    
  //   switch (action) {
  //     case 'create_schedule':
  //       return ['procurement', 'admin'].includes(requesterRole);
  //     case 'edit_schedule':
  //       return username === csOwner || ['admin'].includes(requesterRole);
  //     case 'add_bids':
  //       return username === csOwner || ['procurement', 'admin'].includes(requesterRole);
  //     case 'approve_committee':
  //       return ['committee_member', 'admin'].includes(requesterRole);
  //     case 'final_approval':
  //       return ['gm', 'fm', 'admin'].includes(requesterRole);
  //     default:
  //       return false;
  //   }
  // }, [username, requesterRole, csOwner]);

  // // Username-based permission checks
  // const isScheduleOwner = useCallback((): boolean => {
  //   return username === csOwner;
  // }, [username, csOwner]);

  // // === FILE MANAGEMENT FUNCTIONS ===
  
  // // File upload with validation
  // const onFileInputChange = useCallback((name: string, event: React.ChangeEvent<HTMLInputElement>) => {
  //   const file = event.target.files?.[0];
  //   if (!file) return;
    
  //   const validation = validateFile(file);
  //   if (!validation.isValid) {
  //     onOpenResponse("File Upload Error", validation.error || "Invalid file", false);
  //     return;
  //   }
    
  //   switch (name) {
  //     case 'advert':
  //       setAdvert(file);
  //       break;
  //     default:
  //       console.warn(`Unknown file input: ${name}`);
  //   }
  // }, [validateFile]);

  // === FORM HANDLING FUNCTIONS - WILL BE DEFINED AFTER updatePrData ===

  // === ENHANCED DATA UPDATES & SYNCHRONIZATION ===
  


  // Cascading data updates after operations
  const refreshAllData = useCallback(async () => {
    if (csId) {
      await fetchCS(csId);
    }
  }, [csId, fetchCS]);

  // Show response notification
  const onOpenResponse = useCallback((title: string, message: string, success: boolean) => {
    setResponse({
      open: true,
      title,
      message,
      success,
    });
  }, []);
  
  // Close response notification
  const onCloseResponse = useCallback(() => {
    setResponse({
      open: false,
      title: "",
      message: "",
      success: false,
    });
  }, []);

  // Handle manual PR fetch
  const [prIdInput, setPrIdInput] = useState<string>("");
  
  const handleFetchPR = useCallback(async () => {
    if (!prIdInput.trim()) {
      onOpenResponse("Error", "Please enter a valid PR ID", false);
      return;
    }
    
    await onFetchPR(prIdInput.trim());
    setPrIdInput(""); // Clear input after successful fetch
  }, [prIdInput, onFetchPR]);

  // Handle PR data updates
  const updatePrData = useCallback((field: string, value: string | boolean) => {
    setPrData(prev => ({
      ...prev,
      [field]: value
    }));
  }, []);

  // Handle item selection updates
  const updateItemSelection = useCallback((itemId: string, included: boolean) => {
    setPrData(prev => ({
      ...prev,
      items: prev.items.map(item => 
        item.id === itemId ? { ...item, included } : item
      )
    }));
  }, []);

  // === FORM HANDLING FUNCTIONS ===
  
  // Handle dropdown selections
  // const onSelectChange = useCallback((name: string, event: React.ChangeEvent<HTMLSelectElement>) => {
  //   const { value } = event.target;
    
      //   switch (name) {
    //     case 'currency': {
    //       const selectedCurrency = currencies.find(c => c.id.toString() === value);
    //       setCurrency(selectedCurrency);
    //       break;
  //     }
  //     case 'procPlan': {
  //       const selectedProcPlan = procPlans.find(p => p.id.toString() === value);
  //       setProcPlan(selectedProcPlan);
  //       setProcRef(selectedProcPlan?.proc_ref || '');
  //       break;
  //     }
  //     case 'showSiteVisit':
  //       updatePrData('show_site_visit', value === 'yes');
  //       break;
  //     case 'showSamples':
  //       updatePrData('show_samples_required', value === 'yes');
  //       break;
  //     default:
  //       console.warn(`Unknown select: ${name}`);
  //   }
  // }, [currencies, procPlans, updatePrData]);



  // Enhanced save schedule details with validation
  const handleSaveScheduleDetails = useCallback(async () => {
    // Validate fields before saving
    const validation = validateScheduleFields();
    if (!validation.isValid) {
      onOpenResponse("Validation Error", validation.errors.join(', '), false);
      return;
    }

    setIsLoading(true);
    setLoadingOperation("Saving schedule details");
    
    try {
      const formData = new FormData();
      formData.append("proc_ref", procRef);
      formData.append("scope_of_work", prData.scope_of_work);
      formData.append("currency", JSON.stringify(currency?.id));
      formData.append("pr_number", prData.pr_number);
      formData.append("quantity", quantity);
      formData.append("pr_date", prData.pr_date);
      formData.append("closing_date", prData.closing_date);
      formData.append("ref_date", prData.reference_date);
      formData.append("closing_time", prData.closing_time);
      formData.append("date_tender_opened", prData.cs_opened_date);
      formData.append("username", username);
      formData.append("tender_adjudication_committee_date", prData.tac_date);
      
      if (advert) {
        formData.append("advert", advert);
      }
      
      formData.append("csrfmiddlewaretoken", csrfToken);

      const requestOptions = {
        method: "POST",
        headers: {
          "X-CSRFToken": csrfToken,
        },
        body: formData,
      };
      
      const data = await fetchWithRetry(buildApiUrl(base_url, getApiEndpoints().CS_SAVE), requestOptions);
      
      if (data.success) {
        setCsId(data.cs_id);
        setCsOwner(data.cs_owner);
        onOpenResponse("Success", "Comparative Schedule saved successfully", true);
        await refreshAllData(); // Cascading update
      } else {
        onOpenResponse("Error", "Failed to save schedule", false);
      }
    } catch (error) {
      console.error("Error saving schedule details:", error);
      onOpenResponse("Error", "Failed to save schedule details", false);
    } finally {
      setIsLoading(false);
      setLoadingOperation("");
    }
  }, [validateScheduleFields, procRef, prData, currency, quantity, username, advert, csrfToken, base_url, refreshAllData]);

  // Memoized tab content
  const renderTabContent = useMemo(() => {
    switch (activeTab) {
      case 'details':
        return (
          <div className="space-y-6">
            {/* PR Fetch Section */}
            <div className="bg-blue-50 p-6 rounded-lg shadow-sm border border-blue-200">
              <h3 className="text-lg font-semibold text-blue-900 mb-4 flex items-center">
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Load Purchase Request Data
              </h3>
              <div className="flex flex-col md:flex-row gap-4 items-end">
                <div className="flex-1">
                  <label className="block text-sm font-medium text-blue-700 mb-2">
                    Enter PR ID to load data into this schedule
                  </label>
                  <input
                    type="text"
                    value={prIdInput}
                    onChange={(e) => setPrIdInput(e.target.value)}
                    placeholder="Enter Purchase Request ID (e.g., PR-2024-001)"
                    className="w-full p-3 border border-blue-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    onKeyPress={(e) => e.key === 'Enter' && handleFetchPR()}
                  />
                </div>
                <button
                  onClick={handleFetchPR}
                  disabled={!prIdInput.trim() || isLoading}
                  className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center min-w-max"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v4m0 0v4" />
                  </svg>
                  {isLoading ? 'Loading...' : 'Fetch PR Data'}
                </button>
              </div>
              <p className="text-sm text-blue-600 mt-2">
                This will populate all fields below with data from the specified Purchase Request.
              </p>
            </div>

            {/* Basic Schedule Information */}
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 border-b pb-2">Basic Information</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">CS ID</label>
                  <div className="text-sm text-gray-900 bg-gray-50 p-2 rounded border">{csId}</div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Created by</label>
                  <div className="text-sm text-gray-900 bg-gray-50 p-2 rounded border">{creator}</div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Created at</label>
                  <div className="text-sm text-gray-900 bg-gray-50 p-2 rounded border">{createdAt}</div>
                </div>
              </div>
            </div>

            {/* Procurement Information */}
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 border-b pb-2">Procurement Details</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">PR Number</label>
                    <input 
                      type="text" 
                      className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Enter PR Number"
                      value={prData.pr_number}
                      onChange={(e) => updatePrData('pr_number', e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">PR Date</label>
                    <input 
                      type="date" 
                      className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      value={prData.pr_date}
                      onChange={(e) => updatePrData('pr_date', e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Reference Date</label>
                    <input 
                      type="date" 
                      className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      value={prData.reference_date}
                      onChange={(e) => updatePrData('reference_date', e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Procurement Plan</label>
                    <select className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                      {prData?.procurement_plan_description && (
                        <option value={prData.procurement_plan_id}>{prData.procurement_plan_description}</option>
                      )}
                      <option value="">Select Procurement Plan</option>
                      {procPlans.map((plan) => (
                        <option key={plan.id} value={plan.id}>{plan.description}</option>
                      ))}
                    </select>
                  </div>
                </div>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Currency</label>
                    <select className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                      <option value="">Select Currency</option>
                      {currencies.map((currency) => (
                        <option key={currency.id} value={currency.id}>{currency.currency}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Closing Date</label>
                    <input 
                      type="date" 
                      className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      value={prData.closing_date}
                      onChange={(e) => updatePrData('closing_date', e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Closing Time</label>
                    <input 
                      type="time" 
                      className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      value={prData.closing_time}
                      onChange={(e) => updatePrData('closing_time', e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">CS Opened Date</label>
                    <input 
                      type="date" 
                      className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      value={prData.cs_opened_date}
                      onChange={(e) => updatePrData('cs_opened_date', e.target.value)}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Scope of Work */}
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 border-b pb-2">Scope of Work</h3>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
                <textarea 
                  rows={4}
                  className="w-full p-3 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter detailed scope of work..."
                  value={prData.scope_of_work}
                  onChange={(e) => updatePrData('scope_of_work', e.target.value)}
                ></textarea>
              </div>
            </div>

            {/* Additional Information */}
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 border-b pb-2">Additional Information</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">TAC Date</label>
                    <input 
                      type="date" 
                      className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      value={prData.tac_date}
                      onChange={(e) => updatePrData('tac_date', e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Region</label>
                    <div className="text-sm text-gray-900 bg-gray-50 p-2 rounded border">Eastern Region</div>
                  </div>
                  <div className="flex items-center space-x-4">
                    <label className="flex items-center">
                      <input type="checkbox" className="mr-2 h-4 w-4 text-blue-600 border-gray-300 rounded" />
                      <span className="text-sm text-gray-700">Show Site Visit Requirement</span>
                    </label>
                  </div>
                  <div className="flex items-center space-x-4">
                    <label className="flex items-center">
                      <input type="checkbox" className="mr-2 h-4 w-4 text-blue-600 border-gray-300 rounded" />
                      <span className="text-sm text-gray-700">Show Samples Required</span>
                    </label>
                  </div>
                </div>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Advertisement Document</label>
                    <div className="border-2 border-dashed border-gray-300 rounded-lg p-4">
                      <div className="text-center">
                        <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                          <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                        <div className="mt-2">
                          <label htmlFor="advert-upload" className="cursor-pointer">
                            <span className="text-sm text-blue-600 hover:text-blue-500">Upload advertisement</span>
                            <input id="advert-upload" type="file" className="sr-only" accept=".pdf,.doc,.docx,.jpg,.jpeg,.png" />
                          </label>
                          <p className="text-xs text-gray-500">PDF, DOC, or image up to 10MB</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Purchase Request Items */}
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 border-b pb-2">Purchase Request Items</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        <input type="checkbox" className="h-4 w-4 text-blue-600 border-gray-300 rounded" />
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Item Required</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Quantity</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Unit of Measurement</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {prData.items.map((item) => (
                      <tr key={item.id}>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <input 
                            type="checkbox" 
                            className="h-4 w-4 text-blue-600 border-gray-300 rounded" 
                            checked={item.included}
                            onChange={() => updateItemSelection(item.id, !item.included)}
                          />
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-900">{item.name}</td>
                        <td className="px-4 py-3 text-sm text-gray-900">{item.quantity}</td>
                        <td className="px-4 py-3 text-sm text-gray-900">{item.unit}</td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                            {item.included ? "Included" : "Available"}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="mt-4 flex justify-between items-center">
                <div className="text-sm text-gray-500">
                  Select items to include in this comparative schedule
                </div>
                <button className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition-colors">
                  Update Selected Items
                </button>
              </div>
            </div>

            {/* Additional Notes */}
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 border-b pb-2">Additional Notes</h3>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Internal Notes</label>
                <textarea 
                  rows={3}
                  className="w-full p-3 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Add any additional notes or special instructions..."
                  value={prData.internal_notes}
                  onChange={(e) => updatePrData('internal_notes', e.target.value)}
                ></textarea>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <div className="flex flex-wrap gap-3">
                <button 
                  onClick={handleSaveScheduleDetails}
                  className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 transition-colors flex items-center"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                  </svg>
                  Save Schedule Details
                </button>
                <button className="bg-green-600 text-white px-6 py-2 rounded hover:bg-green-700 transition-colors flex items-center">
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  Export PDF
                </button>
                <button className="bg-gray-600 text-white px-6 py-2 rounded hover:bg-gray-700 transition-colors flex items-center">
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2v0" />
                  </svg>
                  Duplicate Schedule
                </button>
                <button className="bg-red-600 text-white px-6 py-2 rounded hover:bg-red-700 transition-colors flex items-center">
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                  Cancel Schedule
                </button>
              </div>
            </div>
          </div>
        );
      case 'bids':
        return (
          <Suspense fallback={<SectionLoader />}>
            <BidManager
              suppliers={suppliers}
              onSaveBid={handleSaveBid}
              onDeleteBid={handleDeleteBid}
            />
          </Suspense>
        );
      case 'committee':
        return (
          <Suspense fallback={<SectionLoader />}>
            <CommitteeManager
              users={users}
              onSaveCommittee={handleSaveCommittee}
            />
          </Suspense>
        );
      case 'compliance':
        return (
          <Suspense fallback={<SectionLoader />}>
            <ComplianceChecker
              onSaveCompliance={handleSaveCompliance}
            />
          </Suspense>
        );
      case 'approval':
        return (
          <Suspense fallback={<SectionLoader />}>
            <ApprovalWorkflow
              onApprove={handleApprove}
            />
          </Suspense>
        );
      default:
        return null;
    }
  }, [activeTab, csId, creator, createdAt, suppliers, users, handleSaveBid, handleDeleteBid, handleSaveCommittee, handleSaveCompliance, handleApprove, prData, updatePrData, updateItemSelection, handleSaveScheduleDetails, prIdInput, handleFetchPR, isLoading]);

  // Loading indicator
  if (isLoading) {
    return (
      <div className="fixed inset-0 flex items-center justify-center z-50 bg-gray-800 bg-opacity-50">
        <div className="bg-white p-4 rounded-lg shadow-lg flex flex-col items-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-600 mb-3"></div>
          <p className="text-blue-800 font-medium">{loadingOperation || "Loading..."}</p>
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
      <div className="min-h-screen bg-gray-50">
      <div className="px-4 py-5 sm:px-6">
          <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-semibold text-gray-900">Comparative Schedule</h1>
          {csId && (
            <div className="text-sm text-gray-500">
              <p>CS ID: {csId}</p>
              <p>Created by: {creator}</p>
              <p>Created at: {createdAt}</p>
            </div>
          )}
        </div>
        
          {/* Tab Navigation */}
          <div className="border-b border-gray-200 mb-6">
            <nav className="-mb-px flex space-x-8" aria-label="Tabs">
              {TAB_CONFIG.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => handleTabChange(tab.id)}
                  className={`${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  } whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm flex items-center gap-2 transition-colors duration-200`}
                  aria-current={activeTab === tab.id ? 'page' : undefined}
                >
                  <span>{tab.icon}</span>
                  {tab.label}
                  {!loadedTabs.has(tab.id) && tab.id !== 'details' && (
                    <span className="ml-1 text-xs text-gray-400">•</span>
                  )}
                </button>
              ))}
            </nav>
          </div>
          
          {/* Tab Content */}
          <div className="transition-all duration-200">
            {renderTabContent}
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
