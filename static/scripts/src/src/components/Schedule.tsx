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

// Helper function to format date
const formatDisplayDate = (dateString: string) => {
  if (!dateString) return '';
  
  // If it includes 'T', it's a datetime string, extract just the date part
  if (dateString.includes('T')) {
    return dateString.split('T')[0];
  }
  
  // If it's already just a date, return as is
  return dateString;
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
  { id: 'pr-items', label: 'PR Items', icon: '📦' },
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
  const [storedPrId, setStoredPrId] = useState<string>(""); // Store PR ID from CS data
  const [creator, setCreator] = useState<string>("");
  const [createdAt, setCreatedAt] = useState<string>("");
  const [suppliers, setSuppliers] = useState<ISupplier[]>([]);
  const [users, setUsers] = useState<IUser[]>([]);
  const [activeTab, setActiveTab] = useState<TabId>('details');
  const [loadedTabs, setLoadedTabs] = useState<Set<TabId>>(new Set(['details']));
  
  // Additional state variables from ScheduleRef.tsx
  // const [requesterRole] = useState<string>(""); // For future role-based features
  const [  ,setCsOwner] = useState<string>("");
  const [procRef, setProcRef] = useState<string>("");
  const [currency, setCurrency] = useState<ICurrency>();
  const [currencies, setCurrencies] = useState<ICurrency[]>([]);
  const [procPlan, setProcPlan] = useState<IProcPlan>();
  const [procPlans, setProcPlans] = useState<IProcPlan[]>([]);
  const [quantity] = useState<string>("");
  const [advert, setAdvert] = useState<File>();
  const [existingAdvert, setExistingAdvert] = useState<string>(""); // Base64 encoded existing advert
  
  // Simple usage to satisfy linter - will be used properly in dropdowns later
  const currenciesCount = currencies.length;
  const procPlansCount = procPlans.length;
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
      // Set creator and created_at for new schedule (will be updated with full name after users are loaded)
      setCreator(username_ ?? "");
      setCreatedAt(new Date().toISOString());
      onFetchPR(pr_id);
    } else {
      setUsername(username_ ?? "");
      // Set creator and created_at for new schedule (will be updated with full name after users are loaded)
      setCreator(username_ ?? "");
      setCreatedAt(new Date().toISOString());
    }
    
    fetchUsers();
  }, [csid, prid, username_]);
  
  // Update creator name with full name once users are loaded (for new schedules)
  useEffect(() => {
    if (users.length > 0 && creator === username && username) {
      const currentUser = users.find(user => user.username === username);
      if (currentUser) {
        const displayName = `${currentUser.first_name} ${currentUser.last_name}`.trim();
        if (displayName && displayName !== username) {
          setCreator(displayName);
        }
      }
    }
  }, [users, creator, username]);
  
  // Fetch CS data - optimized
  const fetchCS = useCallback(async (cs_id: string) => {
    setIsLoading(true);
    setLoadingOperation("Loading comparative schedule data");
    
    try {
      const data = await fetchWithRetry(buildApiUrl(base_url, getApiEndpoints().CS_DETAILS(cs_id)), defaultRequestOptions);
      console.log("CS Basic Data:", data);
      // Data is now returned as normal JSON, no double encoding
      const parsedData = data;
      // Extract basic metadata
      setCreator(parsedData.creator || '');
      setCreatedAt(parsedData.created_at || '');
      
      // Set CS ID from response
      setCsId(parsedData.cs_id || cs_id);
      
      // Set PR ID from response (needed for item updates)
      if (parsedData.pr_id) {
        setStoredPrId(parsedData.pr_id.toString());
      }
      
      // Set reference data from response (now included in lightweight response)
      if (parsedData.users) {
        setUsers(parsedData.users);
      }
      if (parsedData.suppliers) {
        setSuppliers(parsedData.suppliers);
      }
      if (parsedData.proc_plans) {
        setProcPlans(parsedData.proc_plans);
      }
      if (parsedData.currencies) {
        setCurrencies(parsedData.currencies);
      }
      
      // Set currency and proc plan if available
      if (parsedData.currency) {
        setCurrency(parsedData.currency);
      }
      if (parsedData.proc_plan) {
        setProcPlan(parsedData.proc_plan);
        setProcRef(parsedData.proc_plan.proc_ref || '');
      }
      
      // Set existing advert if available
      if (parsedData.advert) {
        setExistingAdvert(parsedData.advert);
      }
      
      // Extract PR/CS data - backend returns all fields at root level
      setPrData({
        pr_number: parsedData.pr_number || '',
        pr_date: parsedData.pr_date || '',
        reference_date: parsedData.ref_date || '',
        procurement_plan_description: parsedData.proc_plan?.description || '',
        procurement_plan_id: parsedData.proc_plan?.id || '',
        currency: parsedData.currency?.currency || '',
        closing_date: parsedData.closing_date || '',
        closing_time: parsedData.closing_time || '',
        cs_opened_date: parsedData.cs_opened || '',
        scope_of_work: parsedData.scope_of_work || '',
        tac_date: parsedData.tac_date || '',
        region: parsedData.region || '',
        show_site_visit: parsedData.show_site_visit || false,
        show_samples_required: parsedData.show_samples_required || false,
        internal_notes: parsedData.additional_notes || '',
        items: []
      });
      
      // Process items from both cs_items (included in CS) and pr_items (available from PR)
      const allItems: Array<{
        id: string;
        name: string;
        quantity: number;
        unit: string;
        status: string;
        included: boolean;
      }> = [];
      
      // Add CS items (already included in this schedule)
      if (parsedData.cs_items && Array.isArray(parsedData.cs_items)) {
        parsedData.cs_items.forEach((item: {
          id: number;
          item_required: string;
          quantity: number;
          unit_of_measurement: string;
        }) => {
          allItems.push({
            id: item.id?.toString() || '',
            name: item.item_required || '',
            quantity: item.quantity || 0,
            unit: item.unit_of_measurement || '',
            status: 'included_in_cs',
            included: true
          });
        });
      }
      
      // Add PR items (available items from original PR)
      if (parsedData.pr_items && Array.isArray(parsedData.pr_items)) {
        parsedData.pr_items.forEach((item: {
          id: number;
          item_required: string;
          quantity: number;
          unit_of_measurement: string;
          ordered?: boolean;
        }) => {
          // Check if this item is already in cs_items to avoid duplicates
          const existsInCS = allItems.some(csItem => csItem.id === item.id?.toString());
          if (!existsInCS) {
            allItems.push({
              id: item.id?.toString() || '',
              name: item.item_required || '',
              quantity: item.quantity || 0,
              unit: item.unit_of_measurement || '',
              status: item.ordered ? 'used_in_other_schedule' : 'available',
              included: false
            });
          }
        });
      }
      
      // Update prData with processed items
      setPrData(prev => ({
        ...prev,
        items: allItems
      }));
      
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
    const prBasicResponse = await api.fetchPR(pr_id);
    console.log("prResponse basic: ", prBasicResponse);
      // Populate PR data from response based on actual get_create_data response structure
      if (prBasicResponse && prBasicResponse.success) {
        // Set basic PR data immediately (fast UI update)
        setPrData({
          pr_number: prBasicResponse.pr_id || '',
          pr_date: prBasicResponse.pr_date || '',
          reference_date: prBasicResponse.pr_date || '', // Use pr_date as reference if no separate field
          procurement_plan_description: prBasicResponse.proc_plan?.description || '',
          procurement_plan_id: prBasicResponse.proc_plan?.id || '',
          currency: '', // Will be populated from currencies list
          closing_date: '',
          closing_time: '',
          cs_opened_date: '',
          scope_of_work: prBasicResponse.scope_of_work || '',
          tac_date: '',
          region: '', // Will need to be set separately
          show_site_visit: false,
          show_samples_required: false,
          internal_notes: '',
          items: [] // Will be loaded in background
        });
        
        // Set procPlan state for validation
        if (prBasicResponse.proc_plan) {
          setProcPlan(prBasicResponse.proc_plan);
        }

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
                  status: string;
                  included: boolean;
                }) => ({
                  id: item.id.toString(),
                  name: item.item_required,
                  quantity: item.quantity,
                  unit: item.unit_of_measurement,
                  status: item.status || (item.ordered ? 'used_in_other_schedule' : 'available'),
                  included: item.included !== undefined ? item.included : !item.ordered
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
  
  // Note: Suppliers are now loaded as part of CS basic data, no separate fetch needed
  
  // Load tab data when tab becomes active
  const loadTabData = useCallback(async (tabId: TabId) => {
    // For PR items tab, always reload when CS ID exists to ensure complete data
    if (loadedTabs.has(tabId) && !(tabId === 'pr-items' && csId)) {
      return;
    }
    if (!csId && tabId !== 'pr-items') return;
    
    setLoadingOperation(`Loading ${tabId} data`);
    
    try {
      switch (tabId) {
        case 'bids': {
          // Load bids data using optimized endpoint
          console.log('Loading bids data...');
          const bidsData = await fetchWithRetry(
            buildApiUrl(base_url, getApiEndpoints().CS_BIDS_DATA(csId)), 
            defaultRequestOptions
          );
          console.log('Bids data loaded:', bidsData);
          break;
        }
          
        case 'committee': {
          // Load committee data using optimized endpoint
          console.log('Loading committee data...');
          const committeeData = await fetchWithRetry(
            buildApiUrl(base_url, getApiEndpoints().CS_COMMITTEE_DATA(csId)), 
            defaultRequestOptions
          );
          console.log('Committee data loaded:', committeeData);
          break;
        }
          
        case 'compliance': {
          // Load compliance data using optimized endpoint
          console.log('Loading compliance data...');
          const complianceData = await fetchWithRetry(
            buildApiUrl(base_url, getApiEndpoints().CS_COMPLIANCE_DATA(csId)), 
            defaultRequestOptions
          );
          console.log('Compliance data loaded:', complianceData);
          break;
        }
          
        case 'approval': {
          // Load approval data using optimized endpoint
          console.log('Loading approval data...');
          const approvalData = await fetchWithRetry(
            buildApiUrl(base_url, getApiEndpoints().CS_APPROVALS_DATA(csId)), 
            defaultRequestOptions
          );
          console.log('Approval data loaded:', approvalData);
          break;
        }
          
        case 'pr-items': {
          // Load PR items data for the CS
          console.log('Loading PR items data...');
          setLoadingOperation("Loading PR items data");
          
          if (csId) {
            // For existing CS, use CS-specific endpoint that returns ALL PR items with their status
            // Always fetch for existing CS to ensure we have complete data
            console.log('Fetching PR items for existing CS:', csId);
            try {
              const itemsResponse = await fetchWithRetry(
                buildApiUrl(base_url, getApiEndpoints().CS_PR_ITEMS_MANAGEMENT(csId)), 
                defaultRequestOptions
              );
              
              if (itemsResponse && itemsResponse.success) {
                console.log('✅ CS PR items loaded:', itemsResponse.pr_items?.length || 0, 'items');
                setPrData(prev => ({
                  ...prev,
                  items: itemsResponse.pr_items?.map((item: {
                    id: number;
                    item_required: string;
                    quantity: number;
                    unit_of_measurement: string;
                    status: string;
                    included: boolean;
                  }) => ({
                    id: item.id.toString(),
                    name: item.item_required,
                    quantity: item.quantity,
                    unit: item.unit_of_measurement,
                    status: item.status,
                    included: item.included
                  })) || []
                }));
              } else {
                console.warn('Failed to load CS PR items:', itemsResponse);
              }
            } catch (error) {
              console.error('Error loading CS PR items:', error);
            }
          } else {
            // For new CS (no CS ID yet), use regular PR items endpoint
            const effectivePrId = prid || storedPrId;
            if (effectivePrId && prData.items.length === 0) {
              console.log('Fetching PR items for new CS, PR ID:', effectivePrId);
              const itemsResponse = await api.fetchPRItems(effectivePrId, 1, 50);
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
                    status: string;
                    included: boolean;
                  }) => ({
                    id: item.id.toString(),
                    name: item.item_required,
                    quantity: item.quantity,
                    unit: item.unit_of_measurement,
                    status: item.status || (item.ordered ? 'used_in_other_schedule' : 'available'),
                    included: item.included !== undefined ? item.included : !item.ordered
                  })) || []
                }));
              } else {
                console.warn('Failed to load PR items:', itemsResponse);
              }
            } else if (!effectivePrId) {
              console.warn('No PR ID available to load items');
            } else {
              console.log('PR items already loaded:', prData.items.length, 'items');
            }
          }
          setLoadingOperation('');
          break;
        }
      }
      
      setLoadedTabs(prev => new Set([...prev, tabId]));
    } catch (error) {
      console.error(`Error loading ${tabId} data:`, error);
    } finally {
      setLoadingOperation('');
    }
  }, [loadedTabs, csId, base_url, defaultRequestOptions, prid, storedPrId, prData.items.length, api]);
  
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
        // setAdvert(file);
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

  // Handle select all/deselect all items - only affects available items
  const handleSelectAllItems = useCallback((selectAll: boolean) => {
    setPrData(prev => ({
      ...prev,
      items: prev.items.map(item => ({
        ...item,
        // Only skip items used in other schedules - allow toggling current schedule items
        included: item.status === 'used_in_other_schedule' ? item.included : selectAll
      }))
    }));
  }, []);

  // Check if all available items are selected
  const allItemsSelected = useMemo(() => {
    const availableItems = prData.items.filter(item => item.status !== 'used_in_other_schedule');
    return availableItems.length > 0 && availableItems.every(item => item.included);
  }, [prData.items]);

  // Handle updating selected items
  const handleUpdateSelectedItems = useCallback(async () => {
    const effectivePrId = prid || storedPrId; // Use prop prid or stored PR ID from CS data
    
    console.log("Update Items Debug:", {
      csId: csId,
      prid: prid, 
      storedPrId: storedPrId,
      effectivePrId: effectivePrId
    });
    
    if (!csId || !effectivePrId) {
      onOpenResponse("Error", "CS ID and PR ID are required to update items", false);
      return;
    }

    setIsLoading(true);
    setLoadingOperation("Updating selected items");

    try {
      // Send all items that need to be updated - newly selected available items and existing items being removed
      const itemsToUpdate = prData.items.filter(item => 
        // Include newly selected available items
        (item.included && (item.status === 'available' || !item.status)) ||
        // Include items currently in schedule (whether selected or deselected for removal)
        item.status === 'included_in_cs'
      );
      
              if (itemsToUpdate.length === 0) {
          onOpenResponse("Info", "No items to update", false);
          return;
        }
        
        const formData = new FormData();
        formData.append("cs_id", csId);
        formData.append("pr_id", effectivePrId!); // Non-null assertion since we checked above
        formData.append("json_data", JSON.stringify({
          cs_items: itemsToUpdate.map((item: { id: string; name: string; quantity: number; unit: string; included: boolean; status: string }) => ({
          id: item.id,
          item_required: item.name,
          quantity: item.quantity,
          unit_of_measurement: item.unit,
          included: item.included
        }))
      }));
      formData.append("csrfmiddlewaretoken", csrfToken);

      const requestOptions = {
        method: "POST",
        headers: {
          "X-CSRFToken": csrfToken,
        },
        body: formData,
      };

      const data = await fetchWithRetry(buildApiUrl(base_url, getApiEndpoints().CS_UPDATE_ITEMS()), requestOptions);
      
      if (data.success) {
        onOpenResponse("Success", "Selected items updated successfully", true);
        // Refresh PR items to reflect the changes
        api.fetchPRItems(effectivePrId!, 1, 50) // Non-null assertion since we checked above
          .then(itemsResponse => {
            if (itemsResponse && itemsResponse.success) {
              setPrData(prev => ({
                ...prev,
                items: itemsResponse.pr_items?.map((item: {
                  id: number;
                  item_required: string;
                  quantity: number;
                  unit_of_measurement: string;
                  ordered: boolean;
                  status: string;
                  included: boolean;
                }) => ({
                  id: item.id.toString(),
                  name: item.item_required,
                  quantity: item.quantity,
                  unit: item.unit_of_measurement,
                  status: item.status || (item.ordered ? 'used_in_other_schedule' : 'available'),
                  included: item.included !== undefined ? item.included : !item.ordered
                })) || []
              }));
            }
          });
      } else {
        onOpenResponse("Error", data.message || "Failed to update items", false);
      }
    } catch (error) {
      console.error("Error updating items:", error);
      onOpenResponse("Error", "Failed to update selected items", false);
    } finally {
      setIsLoading(false);
      setLoadingOperation("");
    }
  }, [csId, prid, storedPrId, prData.items, csrfToken, base_url, api]);

  // === FORM HANDLING FUNCTIONS ===
  
  // Handle dropdown selections
  const onSelectChange = useCallback((name: string, event: React.ChangeEvent<HTMLSelectElement>) => {
    const { value } = event.target;
    
    switch (name) {
      case 'currency': {
        const selectedCurrency = currencies.find(c => c.id.toString() === value);
        setCurrency(selectedCurrency);
        break;
      }
      case 'procPlan': {
        const selectedProcPlan = procPlans.find(p => p.id.toString() === value);
        setProcPlan(selectedProcPlan);
        setProcRef(selectedProcPlan?.proc_ref || '');
        break;
      }
      case 'showSiteVisit':
        updatePrData('show_site_visit', value === 'yes');
        break;
      case 'showSamples':
        updatePrData('show_samples_required', value === 'yes');
        break;
      default:
        console.warn(`Unknown select: ${name}`);
    }
  }, [currencies, procPlans, updatePrData]);



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
    console.log("prData", prData);
    
    try {
      const formData = new FormData();
      formData.append("proc_ref", procRef);
      formData.append("scope_of_work", prData.scope_of_work);
      formData.append("currency", JSON.stringify(currency?.id));
      formData.append("proc_plan_id", prData.procurement_plan_id || "");
      formData.append("pr_number", prData.pr_number);
      formData.append("quantity", quantity);
      formData.append("pr_date", prData.pr_date);
      formData.append("closing_date", prData.closing_date);
      formData.append("ref_date", prData.reference_date);
      formData.append("closing_time", prData.closing_time);
      formData.append("date_tender_opened", prData.cs_opened_date);
      formData.append("username", username);
      formData.append("tender_adjudication_committee_date", prData.tac_date);

      console.log("formData", formData);
      
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
        
        // Update creator and created_at if not already set (for new schedules)
        if (!creator) {
          // Try to find the user's full name from the users list, otherwise use username
          const currentUser = users.find(user => user.username === username);
          const displayName = currentUser ? 
            `${currentUser.first_name} ${currentUser.last_name}`.trim() || username : 
            username;
          setCreator(displayName);
        }
        if (!createdAt) {
          setCreatedAt(new Date().toISOString());
        }
        
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
                    <div className="text-sm text-gray-900 bg-gray-50 p-2 rounded border">
                      {formatDisplayDate(createdAt)}
                    </div>
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
                        <option value={prData.procurement_plan_id} selected>{prData.procurement_plan_description}</option>
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
                    <select 
                      className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      onChange={(e) => onSelectChange("currency", e)}
                      value={currency?.id || ""}
                    >
                      {/* <option value="">Select Currency</option> */}
                      {currency && (
                        <option value={currency.id} selected>{currency.currency}</option>
                      )}
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

                </div>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Advertisement Document</label>
                    <div className="border-2 border-dashed border-gray-300 rounded-lg p-4">
                      {advert ? (
                        <div className="text-center">
                          <svg className="mx-auto h-12 w-12 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          <div className="mt-2">
                            <p className="text-sm text-green-600 font-medium">{advert.name}</p>
                            <p className="text-xs text-gray-500">{(advert.size / 1024 / 1024).toFixed(2)} MB</p>
                            <button
                              type="button"
                              onClick={() => setAdvert(undefined)}
                              className="mt-2 text-sm text-red-600 hover:text-red-500"
                            >
                              Remove file
                            </button>
                          </div>
                        </div>
                      ) : existingAdvert ? (
                        <div className="text-center">
                          <svg className="mx-auto h-12 w-12 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                          </svg>
                          <div className="mt-2">
                            <p className="text-sm text-blue-600 font-medium">Existing Advertisement Document</p>
                            <button
                              type="button"
                              onClick={() => {
                                const link = document.createElement('a');
                                link.href = `data:application/octet-stream;base64,${existingAdvert}`;
                                link.download = 'advertisement.pdf';
                                link.click();
                              }}
                              className="mt-2 text-sm text-blue-600 hover:text-blue-500 underline"
                            >
                              Download Current Document
                            </button>
                            <div className="mt-2">
                              <label htmlFor="advert-upload-replace" className="cursor-pointer">
                                <span className="text-sm text-gray-600 hover:text-gray-500">Replace with new file</span>
                                <input 
                                  id="advert-upload-replace" 
                                  type="file" 
                                  className="sr-only" 
                                  accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
                                  onChange={(e) => {
                                    const file = e.target.files?.[0];
                                    if (file) {
                                      setAdvert(file);
                                      setExistingAdvert(''); // Clear existing when new file is selected
                                    }
                                  }}
                                />
                              </label>
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="text-center">
                          <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                            <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                          </svg>
                          <div className="mt-2">
                            <label htmlFor="advert-upload" className="cursor-pointer">
                              <span className="text-sm text-blue-600 hover:text-blue-500">Upload advertisement</span>
                              <input 
                                id="advert-upload" 
                                type="file" 
                                className="sr-only" 
                                accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
                                onChange={(e) => {
                                  const file = e.target.files?.[0];
                                  if (file) setAdvert(file);
                                }}
                              />
                            </label>
                            <p className="text-xs text-gray-500">PDF, DOC, or image up to 10MB</p>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
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
      case 'pr-items':
        return (
          <Suspense fallback={<SectionLoader />}>
            <div className="space-y-6">
              {!csId ? (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
                  <div className="flex items-center">
                    <svg className="w-6 h-6 text-yellow-600 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                    </svg>
                    <div>
                      <h3 className="text-lg font-medium text-yellow-800">Schedule Details Required</h3>
                      <p className="text-yellow-700 mt-1">Please save the schedule details first before managing PR items.</p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Purchase Request Items */}
                  <div className="bg-white p-6 rounded-lg shadow-sm border">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4 border-b pb-2">Purchase Request Items</h3>
                    
                    {isLoading && loadingOperation === "Loading PR items data" ? (
                      <div className="flex items-center justify-center py-8">
                        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-600 mr-3"></div>
                        <span className="text-gray-600">Loading PR items...</span>
                      </div>
                    ) : prData.items.length === 0 ? (
                      <div className="text-center py-8">
                        <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V9a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                        </svg>
                        <h3 className="mt-2 text-sm font-medium text-gray-900">No PR items found</h3>
                        <p className="mt-1 text-sm text-gray-500">
                          {!(prid || storedPrId) 
                            ? "Please load PR data from the Details tab first." 
                            : "This purchase request has no items to display."
                          }
                        </p>
                      </div>
                    ) : (
                      <>
                        <div className="overflow-x-auto">
                          <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                              <tr>
                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                  <input 
                                    type="checkbox" 
                                    className="h-4 w-4 text-blue-600 border-gray-300 rounded" 
                                    checked={allItemsSelected}
                                    onChange={(e) => handleSelectAllItems(e.target.checked)}
                                    title={allItemsSelected ? "Deselect all items" : "Select all items"}
                                  />
                                </th>
                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Item Required</th>
                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Quantity</th>
                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Unit of Measurement</th>
                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                              </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                              {prData.items.map((item) => (
                                                          <tr key={item.id} className={
                              item.status === 'included_in_cs' ? 'bg-blue-50' : 
                              item.status === 'used_in_other_schedule' ? 'bg-gray-50' : ''
                            }>
                                <td className="px-4 py-3 whitespace-nowrap">
                                  <input 
                                    type="checkbox" 
                                    className="h-4 w-4 text-blue-600 border-gray-300 rounded" 
                                    checked={item.included}
                                    disabled={item.status === 'used_in_other_schedule'}
                                    onChange={() => updateItemSelection(item.id, !item.included)}
                                                                      title={
                                    item.status === 'used_in_other_schedule' 
                                      ? 'This item is already used in another schedule and cannot be modified' 
                                      : item.status === 'included_in_cs'
                                      ? 'This item is currently used in this schedule (can be removed if no bids exist)'
                                      : 'Click to include/exclude this item from the schedule'
                                  }
                                  />
                                </td>
                                <td className="px-4 py-3 text-sm text-gray-900">
                                  {item.name}
                                  {item.status === 'included_in_cs' && (
                                    <span className="ml-2 text-xs text-green-600">(Used in this schedule)</span>
                                  )}
                                  {item.status === 'used_in_other_schedule' && (
                                    <span className="ml-2 text-xs text-gray-500">(Used in other schedule)</span>
                                  )}
                                </td>
                                <td className="px-4 py-3 text-sm text-gray-900">{item.quantity}</td>
                                <td className="px-4 py-3 text-sm text-gray-900">{item.unit}</td>
                                <td className="px-4 py-3 whitespace-nowrap">
                                                                  {item.status === 'included_in_cs' ? (
                                  <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                                    In Schedule (Editable)
                                  </span>
                                ) : item.status === 'used_in_other_schedule' ? (
                                  <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-600">
                                    Used Elsewhere (Locked)
                                  </span>
                                ) : (
                                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                                    item.included 
                                      ? "bg-green-100 text-green-800" 
                                      : "bg-yellow-100 text-yellow-800"
                                  }`}>
                                    {item.included ? "Selected" : "Available"}
                                  </span>
                                )}
                                </td>
                              </tr>
                            ))}
                            </tbody>
                          </table>
                        </div>
                        <div className="mt-4 flex justify-between items-center">
                          <div className="text-sm text-gray-500">
                            Select items to include in this comparative schedule. Items already in this schedule can be removed unless bids exist.
                                                      <div className="text-xs text-gray-400 mt-1 space-y-1">
                            {prData.items.some(item => item.status === 'included_in_cs') && (
                              <div className="flex items-center">
                                <div className="w-3 h-3 bg-blue-100 rounded mr-2"></div>
                                <span>Blue background: Items in this schedule (can be edited)</span>
                              </div>
                            )}
                            {prData.items.some(item => item.status === 'used_in_other_schedule') && (
                              <div className="flex items-center">
                                <div className="w-3 h-3 bg-gray-100 rounded mr-2"></div>
                                <span>Gray background: Items used in other schedules (locked)</span>
                              </div>
                            )}
                            {prData.items.some(item => item.status === 'available' || (!item.status)) && (
                              <div className="flex items-center">
                                <div className="w-3 h-3 bg-white border border-gray-300 rounded mr-2"></div>
                                <span>White background: Available items that can be selected</span>
                              </div>
                            )}
                          </div>
                          </div>
                          <button 
                            onClick={handleUpdateSelectedItems}
                            disabled={!csId || isLoading || prData.items.filter(item => item.included && (item.status === 'available' || item.status === 'included_in_cs' || !item.status)).length === 0}
                            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center"
                          >
                            {isLoading ? (
                              <>
                                <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-white mr-2"></div>
                                Updating...
                              </>
                            ) : (
                              <>
                                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                </svg>
                                Update Selected Items
                              </>
                            )}
                          </button>
                        </div>
                      </>
                    )}
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
                </div>
              )}
            </div>
          </Suspense>
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
          {(csId || creator || createdAt) && (
            <div className="text-sm text-gray-500">
              {csId && <p>CS ID: {csId}</p>}
              {creator && <p>Created by: {creator}</p>}
              {createdAt && <p>Created at: {formatDisplayDate(createdAt)}</p>}
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
