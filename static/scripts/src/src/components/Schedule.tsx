import { useEffect, useState, useCallback, useMemo, lazy, Suspense } from "react";
import { ScheduleProvider } from "../context/ScheduleContext";
import { useScheduleApi } from "../hooks/useScheduleApi";
import { useCommitteeState } from "../hooks/useCommitteeState";
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

interface IBidItem {
  id?: number;
  item_required?: string;
  unit_of_measurement?: string;
  vat?: string;
  quantity?: number;
  total_price?: number;
  unit_price?: number;
  ordered?: boolean;
}

interface IRank {
  id: number;
  supplier_name: string;
  rank: number;
  decision: string;
  remarks: string;
  total: number;
}

interface IGmApproval {
  id: number;
  approver_name: string;
  approval: string;
  approval_date: string;
  justification: string;
}

interface IFmApproval {
  id: number;
  approver_name: string;
  approval: string;
  approval_date: string;
  justification: string;
}

interface ICurrentApprover {
  username?: string;
  justification?: string;
  role?: string;
  approval?: string;
}

interface IUomItem {
  id: string;
  unit: string;
  name: string;
}

// Lazy load heavy components
const CommitteeApprovalWrapper = lazy(() => import("./Committee/CommitteeApprovalWrapper"));
const ApprovalTableWrapper = lazy(() => import("./ApprovalTableWrapper"));

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

// Helper function to get file object URL (from ScheduleRef.tsx)
const onGetFileObjectUrl = (fileData: string | File | null | undefined): string | undefined => {
  try {
    if (typeof fileData === "string") {
      const decodedFileData = atob(fileData);
      const uint8Array = new Uint8Array(decodedFileData.length);
      for (let i = 0; i < decodedFileData.length; i++) {
        uint8Array[i] = decodedFileData.charCodeAt(i);
      }

      const file = new Blob([uint8Array], { type: "application/pdf" });
      console.log("file: ", file);

      return URL.createObjectURL(file);
    } else if (fileData) {
      console.log("fileData: ", fileData);
      return URL.createObjectURL(fileData);
    }
    return undefined;
  } catch (err) {
    console.log("error: ", err);
    return undefined;
  }
};

// Helper function to calculate bid total (ensures proper number conversion)
const calculateBidTotal = (items: IBidItem[] | undefined): number => {
  if (!items || items.length === 0) return 0;
  
  const total = items.reduce((sum, item) => {
    const itemTotal = Number(item.total_price) || 0;
    console.log("🧮 Item total calculation:", { 
      item: item.item_required, 
      raw_total_price: item.total_price,
      converted_total: itemTotal 
    });
    return sum + itemTotal;
  }, 0);
  
  console.log("💵 Bid total calculation result:", { 
    itemsCount: items.length, 
    total,
    items: items.map(i => ({ name: i.item_required, total: Number(i.total_price) || 0 }))
  });
  
  return total;
};

// Helper function for fetch with retry
const fetchWithRetry = async (url: string, options: RequestInit, retries = 3, delay = 1000) => {
  try {
    // Making API request
    const response = await fetch(url, options);
    // Response received
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    const data = await response.json();
    // Data parsed successfully
    return data;
  } catch (error) {
    console.error("🔍 fetchWithRetry - Error:", error);
    if (retries > 0) {
      // Retrying request
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
  { id: 'committee', label: 'Committee & Approvals', icon: '👥' },
  { id: 'compliance', label: 'Compliance', icon: '✅' },
  { id: 'rankings', label: 'Rankings & Evaluation', icon: '🏆' }
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
  const [csOwner, setCsOwner] = useState<string>("");
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
  const [username, setUsername] = useState<string>("");
  
  // Enhanced bid management state
  const [bidCount, setBidCount] = useState<number>(0);
  const [currentBid, setCurrentBid] = useState<IBid>();
  const [bids, setBids] = useState<IBid[]>([]);
  const [addBidModal, setAddBidModal] = useState<boolean>(false);
  const [updateBidModal, setUpdateBidModal] = useState<boolean>(false);
  
  // Compliance management state
  const [compliance, setCompliance] = useState<ICompliance[]>([]);
  const [complianceRemarks, setComplianceRemarks] = useState<IComplianceRemark[]>([]);
  const [showSamples, setShowSamples] = useState<string>("no");
  const [showSiteVisit, setShowSiteVisit] = useState<string>("no");
  
  // Rankings and evaluation state
  const [rankings, setRankings] = useState<IRank[]>([]);
  
  // Committee management state
  const { committeeMembers, updateCommitteeMembers } = useCommitteeState();
  
  // Approval workflow state
  const [gmApproval, setGmApproval] = useState<IGmApproval>();
  const [fmApproval, setFmApproval] = useState<IFmApproval>();
  const [approvalsComplete, setApprovalsComplete] = useState<boolean>(false);
  const [approvalsJustificationModal, setApprovalsJustificationModal] = useState<boolean>(false);
  const [currentApprover, setCurrentApprover] = useState<ICurrentApprover>();
  const [currentUserRoles, setCurrentUserRoles] = useState<{
    fm_role: boolean;
    gm_role: boolean;
    procurement_role: boolean;
  }>({
    fm_role: false,
    gm_role: false,
    procurement_role: false
  });
  
  // Additional features state
  const [additionalNotes, setAdditionalNotes] = useState<string>("");
  const [buyersNotes, setBuyersNotes] = useState<string>("");
  const [directPurchaseLimit, setDirectPurchaseLimit] = useState<boolean>(true);
  const [onAddSupplier, setOnAddSupplier] = useState<boolean>(false);
  const [newSupplier, setNewSupplier] = useState<ISupplier>({});
  const [showSupplierDetails, setShowSupplierDetails] = useState<boolean>(false);
  const [supplierSearchTerm, setSupplierSearchTerm] = useState<string>("");
  const [showSupplierDropdown, setShowSupplierDropdown] = useState<boolean>(false);
  const [uomSearchTerm, setUomSearchTerm] = useState<string>("");
  const [showUomDropdown, setShowUomDropdown] = useState<boolean>(false);
  const [activeUomItem, setActiveUomItem] = useState<string>("");
  const [expandedBids, setExpandedBids] = useState<Set<number>>(new Set());
  
  // Bid Modal Validation State
  const [bidValidationErrors, setBidValidationErrors] = useState<string[]>([]);
  const [invalidFields, setInvalidFields] = useState<Set<string>>(new Set());
  
  // UOM Server-side Search State
  const [uomSearchResults, setUomSearchResults] = useState<IUomItem[]>([]);
  const [isUomSearching, setIsUomSearching] = useState<boolean>(false);
  const [debouncedUomSearchTerm, setDebouncedUomSearchTerm] = useState<string>('');
  
  // Supplier Server-side Search State
  const [supplierSearchResults, setSupplierSearchResults] = useState<ISupplier[]>([]);
  const [isSupplierSearching, setIsSupplierSearching] = useState<boolean>(false);
  const [debouncedSupplierSearchTerm, setDebouncedSupplierSearchTerm] = useState<string>('');
  
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
      
      // Load reference data for new schedules (currencies, proc plans, etc.)
      console.log('🔄 Loading reference data for new schedule...');
      api.fetchReferenceData()
        .then(refResponse => {
          if (refResponse && refResponse.success) {
            console.log('✅ Reference data loaded for new schedule');
            setSuppliers(refResponse.suppliers || []);
            setUsers(refResponse.users || []);
            setCurrencies(refResponse.currencies || []);
            setProcPlans(refResponse.proc_plans || []);
            console.log('📋 Currencies loaded:', refResponse.currencies?.length || 0);
            console.log('📋 Proc Plans loaded:', refResponse.proc_plans?.length || 0);
          }
        })
        .catch(error => {
          console.error('❌ Error loading reference data for new schedule:', error);
          // Fallback: still fetch users even if reference data fails
          fetchUsers();
        });
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
      console.log("CS Owner from API:", data.cs_owner);
      console.log("Users in data:", data.users ? data.users.length : 'undefined');
      console.log("Committee in data:", data.committee ? data.committee.length : 'undefined');
      console.log("Compliance in data:", data.compliance ? data.compliance.length : 'undefined');
      console.log("Rankings in data:", data.rankings ? data.rankings.length : 'undefined');
      console.log("Data keys:", Object.keys(data));
      // Data is now returned as normal JSON, no double encoding
      const parsedData = data;
      // Extract basic metadata
      setCreator(parsedData.creator || '');
      setCreatedAt(parsedData.created_at || '');
      
      // Set CS ID from response
      setCsId(parsedData.cs_id || cs_id);
      
      // Set CS owner from response (needed for permission checks)
      setCsOwner(parsedData.cs_owner || '');
      
      // Set PR ID from response (needed for item updates)
      if (parsedData.pr_id) {
        setStoredPrId(parsedData.pr_id.toString());
      }
      
      // Set reference data from response (now included in lightweight response)
      if (parsedData.users) {
        console.log('🔍 Users loaded from CS data:', parsedData.users.length);
        setUsers(parsedData.users);
      } else {
        console.log('🔍 No users found in CS data, will fetch separately');
        // Fallback: fetch users if not included in CS data
        fetchUsers();
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
      
      // Load bids data if available
      if (parsedData.bids && Array.isArray(parsedData.bids)) {
        setBids(parsedData.bids);
        setBidCount(parsedData.bids.length);
      }
      
      // Load committee data if available
      if (parsedData.committee && Array.isArray(parsedData.committee)) {
        console.log('🔍 Committee data loaded:', parsedData.committee.length, 'members');
        updateCommitteeMembers(parsedData.committee);
      }
      
      // Load compliance data if available
      if (parsedData.compliance && Array.isArray(parsedData.compliance)) {
        console.log('🔍 Compliance data loaded:', parsedData.compliance.length, 'items');
        setCompliance(parsedData.compliance);
      }
      
      // Load compliance remarks if available
      if (parsedData.complianceRemarks && Array.isArray(parsedData.complianceRemarks)) {
        console.log('🔍 Compliance remarks loaded:', parsedData.complianceRemarks.length, 'remarks');
        setComplianceRemarks(parsedData.complianceRemarks);
      }
      
      // Load rankings data if available
      if (parsedData.rankings && Array.isArray(parsedData.rankings)) {
        console.log('🔍 Rankings data loaded:', parsedData.rankings.length, 'rankings');
        setRankings(parsedData.rankings);
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
               console.log('🔍 Users loaded from reference data:', refResponse.users?.length || 0);
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


  // Fetch users - optimized for better performance
  const fetchUsers = useCallback(async () => {
    // Skip if users already loaded to avoid unnecessary API calls
    if (users.length > 0) {
      return;
    }
    
    setLoadingOperation("Loading users");
    try {
      const data = await fetchWithRetry(
        buildApiUrl(base_url, `${getApiEndpoints().USERS}?limit=100`), 
        defaultRequestOptions
      );
      
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
          
          // Set bids data to state
          if (bidsData && bidsData.success && bidsData.bids) {
            setBids(bidsData.bids);
            setBidCount(bidsData.bids.length);
          } else if (bidsData && Array.isArray(bidsData)) {
            setBids(bidsData);
            setBidCount(bidsData.length);
          }
          break;
        }
          
        case 'committee': {
          // Load committee and approval data (merged tab)
          const committeeUrl = buildApiUrl(base_url, getApiEndpoints().CS_COMMITTEE_DATA(csId));
          
          const [committeeData, approvalData] = await Promise.all([
            fetchWithRetry(
            committeeUrl, 
            defaultRequestOptions
            ),
            fetchWithRetry(
              buildApiUrl(base_url, getApiEndpoints().CS_APPROVALS_DATA(csId)), 
              defaultRequestOptions
            )
          ]);
          
          // Load users only if not already loaded (lazy loading for better performance)
          if (users.length === 0) {
            await fetchUsers();
          }
          
          // Store the loaded committee data in state
          if (committeeData && committeeData.committee) {
            updateCommitteeMembers(committeeData.committee);
          }
          
          // Store approval data if available
          if (approvalData) {
            if (approvalData.gm_approval) {
              setGmApproval(approvalData.gm_approval);
            }
            if (approvalData.fm_approval) {
              setFmApproval(approvalData.fm_approval);
            }
            if (approvalData.current_user_roles) {
              setCurrentUserRoles(approvalData.current_user_roles);
            }
          }
          break;
        }
          
        case 'compliance': {
          // Load compliance data and rankings (merged tab)
          console.log('Loading compliance data and rankings...');
          const complianceData = await fetchWithRetry(
            buildApiUrl(base_url, getApiEndpoints().CS_COMPLIANCE_DATA(csId)), 
            defaultRequestOptions
          );
          console.log('Compliance data loaded:', complianceData);
          
          // Store the loaded compliance data in state
          if (complianceData && complianceData.compliance) {
            setCompliance(complianceData.compliance);
            console.log("Loaded existing compliance data:", complianceData.compliance.length, "records");
          }
          if (complianceData && complianceData.compliance_remarks) {
            setComplianceRemarks(complianceData.compliance_remarks);
            console.log("Loaded existing compliance remarks:", complianceData.compliance_remarks.length, "records");
          }
          
          // Also try to load existing rankings if they exist
          try {
            const rankingsResponse = await fetch(`${base_url}/api/cs-rankings/${csId}/`, defaultRequestOptions);
            if (rankingsResponse.ok) {
              const rankingsData = await rankingsResponse.json();
              if (rankingsData && rankingsData.rankings && rankingsData.rankings.length > 0) {
                setRankings(rankingsData.rankings);
                console.log("Loaded existing rankings:", rankingsData.rankings.length, "records");
              }
            }
          } catch (error) {
            console.log("No existing rankings found or error loading rankings:", error);
          }
          break;
        }
          
        case 'pr-items': {
          // Load PR items data for the CS with smooth transitions
          console.log('Loading PR items data...');
          setLoadingOperation("Loading PR items data");
          
          // Add small delay to prevent jarring transitions
          await new Promise(resolve => setTimeout(resolve, 150));
          
          try {
            if (csId) {
              // For existing CS, use CS-specific endpoint that returns ALL PR items with their status
              console.log('Fetching PR items for existing CS:', csId);
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
          } catch (error) {
            console.error('Error loading PR items:', error);
          }
          
          // Smooth transition out of loading state
          await new Promise(resolve => setTimeout(resolve, 100));
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
      
      // Close the modal
      if (addBidModal) {
        setAddBidModal(false);
      }
      if (updateBidModal) {
        setUpdateBidModal(false);
      }
      setCurrentBid(undefined);
      setSupplierSearchTerm("");
      setShowSupplierDropdown(false);
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
    // Only creators can save committee
    const creatorCheck = isCreator();
    console.log("🔐 handleSaveCommittee - Creator check:", {
      creatorCheck,
      csId,
      username,
      csOwner,
      isLoading
    });
    
    if (!creatorCheck) {
      onOpenResponse("Access Denied", "Only the creator can save committee data.", false);
      return;
    }
    setIsLoading(true);
    setLoadingOperation("Saving committee members");
    try {
      const formData = new FormData();
      formData.append("cs_id", csId);
      formData.append("committee", JSON.stringify({ committee }));
      formData.append("csrfmiddlewaretoken", csrfToken);
      
      const requestOptions = {
        method: "POST",
        headers: {
          "X-CSRFToken": csrfToken,
        },
        body: formData,
      };
      
      await fetchWithRetry(buildApiUrl(base_url, getApiEndpoints().CS_SAVE_COMMITTEE), requestOptions);
      
      // Update both local and context state
      updateCommitteeMembers(committee);
      
      // Also refresh committee data from server to ensure consistency
      try {
        const committeeData = await fetchWithRetry(
          buildApiUrl(base_url, getApiEndpoints().CS_COMMITTEE_DATA(csId)), 
          defaultRequestOptions
        );
        if (committeeData && committeeData.committee) {
          updateCommitteeMembers(committeeData.committee);
        }
      } catch (error) {
        console.error("Error refreshing committee data:", error);
      }
      
      onOpenResponse("Success", "Committee saved successfully", true);
    } catch (error) {
      console.error("Error saving committee:", error);
      onOpenResponse("Error", "Failed to save committee", false);
    } finally {
      setIsLoading(false);
      setLoadingOperation("");
    }
  }, [csId, base_url, csrfToken, fetchCS]);
  
  
  // Check if all approvals are complete
  const checkApprovalsComplete = useCallback(() => {
    // Committee is approved if there are no members OR if all members have approved
    const committeeApproved = committeeMembers.length === 0 || committeeMembers.every(m => m.memberApproval === "Approved");
    const gmApproved = !!gmApproval && gmApproval.approval === "Approved";
    const fmApproved = !!fmApproval && fmApproval.approval === "Approved";
    

    
    const allComplete = committeeApproved && gmApproved && fmApproved;
    setApprovalsComplete(allComplete);
    
    return allComplete;
  }, [committeeMembers, gmApproval, fmApproval]);

  // Update approvals status when data changes
  useEffect(() => {
    checkApprovalsComplete();
  }, [checkApprovalsComplete]);

  // Load committee data when component mounts or csId changes
  useEffect(() => {
    if (csId && activeTab === 'committee') {
      loadTabData('committee');
    }
  }, [csId, activeTab]);
  
  // Handle approval action
  const handleApprove = useCallback(async (
    role: string,
    targetUsername: string, // Renamed for clarity - this is the user being approved
    approval: string,
    justification: string
  ) => {
    // Check if user is creator
    const userIsCreator = isCreator();
    
    // Find current logged-in user info for debugging
    const currentLoggedInUser = users.find(user => user.username === username);
    const targetUser = users.find(user => user.username === targetUsername);
    
    console.log("🔐 handleApprove - User info debug:", {
      currentLoggedInUsername: username,
      targetUsername: targetUsername,
      currentLoggedInUser: currentLoggedInUser ? {
        username: currentLoggedInUser.username,
        first_name: currentLoggedInUser.first_name,
        last_name: currentLoggedInUser.last_name,
        displayName: `${currentLoggedInUser.first_name} ${currentLoggedInUser.last_name}`
      } : null,
      targetUser: targetUser ? {
        username: targetUser.username,
        first_name: targetUser.first_name,
        last_name: targetUser.last_name,
        displayName: `${targetUser.first_name} ${targetUser.last_name}`
      } : null,
      userIsCreator,
      csOwner
    });
    
    // For committee approvals: only committee members can approve
    if (role === 'committee') {
      // Check if the CURRENT USER (not the target user) is a committee member
      const isCommitteeMember = committeeMembers.some(member => member.memberUserName === username);
      
      console.log("🔐 Committee approval debug:", {
        role,
        currentLoggedInUsername: username,
        targetUsername: targetUsername,
        userIsCreator,
        isCommitteeMember,
        committeeMembers: committeeMembers.map(m => ({ 
          memberUserName: m.memberUserName, 
          memberPosition: m.memberPosition 
        })),
        csOwner,
        usernameComparisons: committeeMembers.map(m => ({
          member: m.memberUserName,
          currentLoggedIn: username,
          match: m.memberUserName === username
        }))
      });
      
      // Only committee members can perform committee approvals
      if (!isCommitteeMember) {
        if (userIsCreator) {
          onOpenResponse("Access Denied", "Creators cannot approve their own documents unless they are committee members. Please add yourself to the committee first.", false);
        } else {
          onOpenResponse("Access Denied", "Only committee members can perform committee approvals.", false);
        }
        return;
      }
    } else {
      // For non-committee approvals (FM/GM): creators cannot approve
      if (userIsCreator) {
        onOpenResponse("Access Denied", "Creators cannot approve their own documents. Only committee members can perform approval actions.", false);
        return;
      }
    }
    setIsLoading(true);
    setLoadingOperation(`Processing ${approval.toLowerCase()} action`);
    try {
      // Handle committee approvals differently
      if (role === 'committee') {
        const formData = new FormData();
        formData.append("cs_id", csId);
        formData.append("username", targetUsername); // Use targetUsername - the person being approved
        formData.append("approval", approval);
        formData.append("justification", justification);
        formData.append("csrfmiddlewaretoken", csrfToken);
        
        const requestOptions = {
          method: "POST",
          headers: {
            "X-CSRFToken": csrfToken,
          },
          body: formData,
        };
        
        await fetchWithRetry(buildApiUrl(base_url, "/committee_approve"), requestOptions);
        
        // Refresh committee data
        const committeeData = await fetchWithRetry(
          buildApiUrl(base_url, getApiEndpoints().CS_COMMITTEE_DATA(csId)), 
          defaultRequestOptions
        );
        if (committeeData && committeeData.committee) {
          updateCommitteeMembers(committeeData.committee);
        }
      } else {
        // Handle finance manager and general manager approvals
        // For FM/GM approvals, use the current logged-in user's username
        const formData = new FormData();
        formData.append("cs_id", csId);
        formData.append("role", role);
        formData.append("username", username); // Current logged-in user for FM/GM approvals
        formData.append("approval", approval);
        formData.append("justification", justification);
        formData.append("csrfmiddlewaretoken", csrfToken);
        
        const requestOptions = {
          method: "POST",
          headers: {
            "X-CSRFToken": csrfToken,
          },
          body: formData,
        };
        
        const data = await fetchWithRetry(buildApiUrl(base_url, "/approval_approve"), requestOptions);
        
        // Update approval state based on role
        if (role === 'general_manager') {
          setGmApproval({
            id: data.gm_approval?.id || 1,
            approver_name: data.gm_approval?.approver_name || username,
            approval,
            approval_date: data.gm_approval?.approval_date || new Date().toISOString(),
            justification
          });
        } else if (role === 'finance_manager') {
          setFmApproval({
            id: data.fm_approval?.id || 1,
            approver_name: data.fm_approval?.approver_name || username,
            approval,
            approval_date: data.fm_approval?.approval_date || new Date().toISOString(),
            justification
          });
        }
      }
      
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
  }, [csId, base_url, csrfToken, fetchCS, updateCommitteeMembers, committeeMembers]);


  


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
    if (!procPlan && !prData.procurement_plan_id) errors.push("Procurement plan is required");
    if (!prData.scope_of_work?.trim()) errors.push("Scope of work is required");
    if (!prData.pr_number?.trim()) errors.push("PR number is required");
    if (!prData.pr_date) errors.push("PR date is required");
    if (!prData.closing_date) errors.push("Closing date is required");
    if (!prData.reference_date) errors.push("Reference date is required");
    if (!prData.closing_time) errors.push("Closing time is required");
    if (!prData.cs_opened_date) errors.push("CS opened date is required");
    if (!prData.tac_date) errors.push("TAC date is required");
    // Check for either new advert file or existing advert document
    if (!advert && !existingAdvert) errors.push("Advertisement document is required");
    
    return { isValid: errors.length === 0, errors };
  }, [currency, procPlan, prData, advert, existingAdvert]);

  // File type and size validation
  const validateFile = useCallback((file: File): { isValid: boolean; error?: string } => {
    const allowedTypes = [
      'application/pdf',
      'application/msword', 
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'image/jpeg',
      'image/jpg', 
      'image/png'
    ];
    
    const maxSize = 10 * 1024 * 1024; // 10MB
    
    if (!allowedTypes.includes(file.type)) {
      return { 
        isValid: false, 
        error: 'File type not allowed. Please upload PDF, DOC, DOCX, JPG, JPEG, or PNG files only.' 
      };
    }
    
    if (file.size > maxSize) {
      return { 
        isValid: false, 
        error: 'File size too large. Maximum allowed size is 10MB.' 
      };
    }
    
    return { isValid: true };
  }, []);





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

  // Helper function to check if current user is the creator
  const isCreator = useCallback((): boolean => {
    const result = (() => {
      // For new schedules (no csId), always return true
      if (!csId || csId === "") {
        return true;
      }
      // For existing schedules, check if current user is the creator
      // Use csOwner (username) instead of creator (full name)
      // If csOwner is empty and we're still loading, return true to avoid blocking operations
      // This prevents the "Access Denied" modal during initial load
      if (!csOwner || csOwner === "") {
        // If we're loading, assume user is creator to prevent blocking
        // The backend will handle the actual permission check
        return true;
      }
      return username === csOwner;
    })();
    
    // isCreator permission check completed
    
    return result;
  }, [username, creator, csOwner, csId, isLoading]);

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
    console.log('🔄 Updating item selection:', { itemId, included });
    setPrData(prev => {
      const updatedItems = prev.items.map(item => 
        item.id === itemId ? { ...item, included } : item
      );
      
      console.log('📊 Item selection updated:', {
        totalItems: updatedItems.length,
        selectedItems: updatedItems.filter(item => item.included).length,
        itemDetails: updatedItems.find(item => item.id === itemId)
      });
      
      return {
        ...prev,
        items: updatedItems
      };
    });
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
    const effectivePrId = prid || storedPrId || prData.pr_number; // Use prop prid, stored PR ID, or PR number from data
    
    console.log("Update Items Debug:", {
      csId: csId,
      prid: prid, 
      storedPrId: storedPrId,
      prDataPrNumber: prData.pr_number,
      effectivePrId: effectivePrId,
      hasCsId: !!csId,
      hasEffectivePrId: !!effectivePrId
    });
    
    if (!csId) {
      onOpenResponse("Error", "CS ID is required to update items", false);
      return;
    }
    
    if (!effectivePrId) {
      onOpenResponse("Error", "PR ID is required to update items. Please ensure the PR is properly linked to this schedule.", false);
      return;
    }

    // Check if bids exist - if true, do not allow form submission
    if (bids && bids.length > 0) {
      onOpenResponse("Update Blocked", "Cannot update PR items when bids exist. Please delete all bids before updating items.", false);
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
      
      console.log('📤 Items to update:', {
        totalItems: prData.items.length,
        itemsToUpdate: itemsToUpdate.length,
        selectedItems: prData.items.filter(item => item.included).length,
        itemsDetails: itemsToUpdate.map(item => ({
          id: item.id,
          name: item.name,
          status: item.status,
          included: item.included
        }))
      });
      
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
        
        // Refresh both CS items and PR items to get the complete updated state
        try {
          // Fetch updated CS data to get the new CS items
          const updatedCSData = await fetchWithRetry(buildApiUrl(base_url, getApiEndpoints().CS_DETAILS(csId)), defaultRequestOptions);
          
          // Fetch updated PR items
          const itemsResponse = await api.fetchPRItems(effectivePrId!, 1, 50);
          
          if (updatedCSData && itemsResponse && itemsResponse.success) {
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
            if (updatedCSData.cs_items && Array.isArray(updatedCSData.cs_items)) {
              updatedCSData.cs_items.forEach((item: {
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
            if (itemsResponse.pr_items && Array.isArray(itemsResponse.pr_items)) {
              itemsResponse.pr_items.forEach((item: {
                id: number;
                item_required: string;
                quantity: number;
                unit_of_measurement: string;
                ordered?: boolean;
                status?: string;
                included?: boolean;
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
            
            // Update prData with the complete merged items
            setPrData(prev => ({
              ...prev,
              items: allItems
            }));
            
            console.log('✅ Items refreshed successfully:', {
              csItems: updatedCSData.cs_items?.length || 0,
              prItems: itemsResponse.pr_items?.length || 0,
              totalItems: allItems.length,
              includedItems: allItems.filter(item => item.included).length
            });
          }
        } catch (refreshError) {
          console.error("Error refreshing items after update:", refreshError);
          // Fallback: just refresh the entire CS data
          fetchCS(csId);
        }
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
  }, [csId, prid, storedPrId, prData.items, csrfToken, base_url, api, bids]);

  // === ENHANCED BID MANAGEMENT FUNCTIONS ===
  


  // Set direct purchase limit
  const onSetDirectPurchaseLimit = useCallback(() => {
    if (base_url === "/direct_purchase") {
      const limit = (bids?.length ?? 0) >= 1 ? false : true;
      setDirectPurchaseLimit(limit);
    }
  }, [base_url, bids]);

  // Add supplier modal
  const onAddSuppliersModal = useCallback(() => {
    setOnAddSupplier(!onAddSupplier);
  }, [onAddSupplier]);

  // Handle supplier change
  const onSupplierChange = useCallback((event: { target: { name: string; value: string } }) => {
    const { name, value } = event.target;
    setNewSupplier({
      ...newSupplier,
      [name]: value,
    });
  }, [newSupplier]);

  // Add bid modal
  const onAddBidModal = useCallback(() => {
    // Only creators can add bids
    if (!isCreator()) {
      onOpenResponse("Access Denied", "Only the creator can add bids to this schedule.", false);
      return;
    }

    // Convert selected PR items to bid items format
    const selectedPrItems = prData.items.filter(item => item.included);
    const bidItems: IBidItem[] = selectedPrItems.map(item => ({
      id: parseInt(item.id),
      item_required: item.name,
      unit_of_measurement: item.unit,
      quantity: item.quantity,
      unit_price: 0,
      total_price: 0,
      vat: "0",
      ordered: false
    }));

    setCurrentBid({
      bid_count: bidCount + 1,
      items: bidItems,
    });
    setAddBidModal(!addBidModal);
    setSupplierSearchTerm(""); // Clear search when opening modal
    setShowSupplierDropdown(false); // Hide dropdown
    console.log("currentBid with PR items: ", { bid_count: bidCount + 1, items: bidItems });
  }, [bidCount, prData.items, addBidModal, isCreator, onOpenResponse]);

  // Update bid modal
  const onUpdateBidModal = useCallback((bid_count: number) => {
    console.log("🔧 Edit bid triggered:", { bid_count, bids: bids.length, isCreator: isCreator() });
    
    // Only creators can update bids
    if (!isCreator()) {
      onOpenResponse("Access Denied", "Only the creator can edit bids in this schedule.", false);
      return;
    }

    const bid = bids.find((bid) => bid && bid.bid_count === bid_count);
    console.log("🔧 Found bid for editing:", bid);
    
    if (bid) {
      setCurrentBid(bid);
      // Populate supplier search term for editing
      setSupplierSearchTerm(bid.supplier_name || '');
      setUpdateBidModal(true); // Always set to true for edit mode
      console.log("🔧 Edit modal opened for bid:", bid.bid_count);
    } else {
      console.error("❌ Bid not found for editing:", bid_count);
      onOpenResponse("Error", `Bid #${bid_count} not found for editing.`, false);
    }
  }, [bids, isCreator, onOpenResponse]);

  // Close current bid modal
  const onCloseCurrentBid = useCallback(() => {
    setAddBidModal(false);
    setCurrentBid(undefined);
    setSupplierSearchTerm(""); // Clear search when closing modal
    setShowSupplierDropdown(false); // Hide dropdown
    setBidValidationErrors([]); // Clear validation errors
    setInvalidFields(new Set()); // Clear invalid fields
  }, []);

  // Close update bid modal
  const onCloseUpdateBidBid = useCallback(() => {
    setUpdateBidModal(false);
    setCurrentBid(undefined);
    setSupplierSearchTerm(""); // Clear search when closing modal
    setShowSupplierDropdown(false); // Hide dropdown
    setBidValidationErrors([]); // Clear validation errors
    setInvalidFields(new Set()); // Clear invalid fields
  }, []);

  // Handle current bid changes
  const onCurrentBidChange = useCallback((
    name_: string,
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const { name, value } = event.target;
    console.log("name: ", name, "value: ", value);
    
    // Clear validation errors for this field when user starts typing
    if (invalidFields.has(name)) {
      const newInvalidFields = new Set(invalidFields);
      newInvalidFields.delete(name);
      setInvalidFields(newInvalidFields);
      
      // Remove related error messages
      const newErrors = bidValidationErrors.filter(error => 
        !error.toLowerCase().includes(name.toLowerCase())
      );
      setBidValidationErrors(newErrors);
    }
    
    if (name_ === "supplier_name") {
      setCurrentBid({
        ...currentBid,
        supplier_name: value,
      });
    } else if (name_ === "bid_date") {
      setCurrentBid({
        ...currentBid,
        bid_date: value,
      });
    }
  }, [currentBid, invalidFields, bidValidationErrors]);



  // Handle bid document change with enhanced file handling
  const onBidDocumentChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const validation = validateFile(file);
      if (!validation.isValid) {
        onOpenResponse("File Upload Error", validation.error || "Invalid file", false);
        return;
      }
      
      // Enhanced file handling - log file details for debugging
      console.log('📄 File uploaded:', {
        name: file.name,
        size: file.size,
        type: file.type,
        lastModified: new Date(file.lastModified).toISOString(),
        isEditMode: !!currentBid?.bid_count
      });
      
      setCurrentBid({
        ...currentBid,
        bid_document: file,
      });
      
      onOpenResponse("File Uploaded", `File "${file.name}" uploaded successfully`, true);
    } else {
      console.log("📄 No file selected or file input cleared");
    }
  }, [currentBid, validateFile]);

  // Handle current bid item changes with auto-calculation
  const onCurrentBidItemChange = useCallback((
    description: string,
    name_: string,
    event: { target: { name: string; value: string } },
    bid_no: string
  ) => {
    const { value } = event.target;
    console.log("🔢 Bid item change:", { field: name_, value, description, bid_no });
    
    // Clear validation errors for this field when user starts typing
    const itemIndex = currentBid?.items?.findIndex(item => item.item_required === description) ?? -1;
    const fieldKey = `item_${itemIndex}_${name_}`;
    
    if (invalidFields.has(fieldKey)) {
      const newInvalidFields = new Set(invalidFields);
      newInvalidFields.delete(fieldKey);
      setInvalidFields(newInvalidFields);
      
      // Remove related error messages
      const newErrors = bidValidationErrors.filter(error => 
        !error.toLowerCase().includes(description.toLowerCase()) || 
        !error.toLowerCase().includes(name_.toLowerCase())
      );
      setBidValidationErrors(newErrors);
    }
    
    if (currentBid?.items) {
      const updatedItems = currentBid.items.map((item) => {
        if (item.item_required === description) {
          const updatedItem = {
            ...item,
            [name_]: name_ === "quantity" || name_ === "unit_price" ? 
              parseFloat(value) || 0 : value,
          };
          
          // Auto-calculate total price when quantity or unit_price changes
          if (name_ === "quantity" || name_ === "unit_price") {
            const quantity = name_ === "quantity" ? parseFloat(value) || 0 : Number(item.quantity) || 0;
            const unitPrice = name_ === "unit_price" ? parseFloat(value) || 0 : Number(item.unit_price) || 0;
            const calculatedTotal = quantity * unitPrice;
            updatedItem.total_price = calculatedTotal;
            
            console.log("💰 Total calculation:", { 
              item: description, 
              quantity, 
              unitPrice, 
              calculatedTotal,
              originalQuantity: item.quantity,
              originalUnitPrice: item.unit_price
            });
          }
          
          return updatedItem;
        }
        return item;
      });
      
      console.log("📊 Updated bid items:", updatedItems);
      
      setCurrentBid({
        ...currentBid,
        items: updatedItems,
      });
    }
  }, [currentBid, invalidFields, bidValidationErrors]);

  // Enhanced save bid function with direct purchase validation
  const onSaveBid = useCallback((bid: IBid, bids: IBid[], bid_count?: number) => {
    console.log("💾 onSaveBid called:", { 
      bid: bid.bid_count, 
      bid_count, 
      isEditMode: !!bid_count,
      totalBids: bids.length 
    });
    
    // Only creators can save bids
    if (!isCreator()) {
      onOpenResponse("Access Denied", "Only the creator can save bids to this schedule.", false);
      return;
    }
    
    // Direct purchase validation
    if (base_url === "/direct_purchase" && bids.length >= 1 && !bid_count) {
      onOpenResponse("Direct Purchase Limit", "Direct purchase allows maximum 1 bid only", false);
      return;
    }
    
    // File validation
    if (bid.bid_document && bid.bid_document instanceof File) {
      const fileValidation = validateFile(bid.bid_document);
      if (!fileValidation.isValid) {
        onOpenResponse("File Validation Error", fileValidation.error || "Invalid file", false);
        return;
      }
    }

    const form_data: FormData = new FormData();

    form_data.append("cs_id", csId);
    form_data.append("bid_count", bid?.bid_count ? bid?.bid_count?.toString() : "");
    form_data.append("supplier", bid.supplier ?? "");
    form_data.append("supplier_name", bid.supplier_name ?? "");
    form_data.append("bid_date", bid.bid_date ?? "");
    // Handle bid document - preserve existing document if no new file is uploaded
    if (bid.bid_document instanceof File) {
      form_data.append("bid_document", bid.bid_document);
    } else if (bid.encoded_bid_document) {
      // For existing encoded documents, send as string
      form_data.append("bid_document", bid.encoded_bid_document);
    } else if (bid.bid_document_url) {
      // For existing document URLs, send as string
      form_data.append("bid_document", bid.bid_document_url);
    } else {
      form_data.append("bid_document", "");
    }
    form_data.append(
      "json_data",
      JSON.stringify({
        items: bid.items,
      })
    );
    form_data.append("csrfmiddlewaretoken", csrfToken);

    console.log("📤 Sending bid data:", {
      cs_id: csId,
      bid_count: bid?.bid_count,
      supplier_name: bid.supplier_name,
      items_count: bid.items?.length || 0
    });

    fetch(`${base_url}/save_bid`, {
      method: "POST",
      headers: {
        "X-CSRFToken": csrfToken,
      },
      body: form_data,
    })
      .then((response) => response.json())
      .then((data) => {
        console.log("📥 Save bid response:", data);
        if (data.success) {
          const isEditMode = !!bid_count;
          const message = isEditMode ? "Bid updated successfully" : "Bid saved successfully";
          onOpenResponse("Save Bid Success", message, true);
          
          if (isEditMode) {
            // Update existing bid in the list
            const updatedBids = bids.map(existingBid => 
              existingBid.bid_count === bid.bid_count ? bid : existingBid
            );
            setBids(updatedBids);
          } else {
            // Add new bid to the list
            setBids([...bids, bid]);
            setBidCount(bidCount + 1);
          }
          
          setAddBidModal(false);
          setUpdateBidModal(false);
          setCurrentBid(undefined);
          setSupplierSearchTerm("");
          setShowSupplierDropdown(false);
          onSetDirectPurchaseLimit();
        } else {
          onOpenResponse("Save Bid Error", data.message || "Failed to save bid, please try again.", false);
        }
      })
      .catch((error) => {
        console.error("❌ Save bid error:", error);
        onOpenResponse("Save Bid Error", "Network error occurred while saving bid.", false);
      });
   }, [csId, csrfToken, base_url, bidCount, onSetDirectPurchaseLimit, validateFile, isCreator]);

  // Helper function to check if a field is invalid
  const isFieldInvalid = useCallback((fieldName: string) => {
    return invalidFields.has(fieldName);
  }, [invalidFields]);

  // Server-side search for UOM
  const searchUom = useCallback(async (searchQuery: string) => {
    if (!searchQuery || searchQuery.length < 2) {
      setUomSearchResults([]);
      return;
    }

    setIsUomSearching(true);
    try {
      const url = buildApiUrl(base_url, `${getApiEndpoints().UOM}?search=${encodeURIComponent(searchQuery)}&limit=100`);
      const response = await fetch(url);
      const data = await response.json();
      
      if (data.uom) {
        setUomSearchResults(data.uom);
      }
    } catch (error) {
      console.error('Error searching UOM:', error);
      setUomSearchResults([]);
    } finally {
      setIsUomSearching(false);
    }
  }, [base_url]);

  // Trigger UOM search when debounced search term changes
  useEffect(() => {
    searchUom(debouncedUomSearchTerm);
  }, [debouncedUomSearchTerm, searchUom]);

  // Debounce UOM search term
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedUomSearchTerm(uomSearchTerm);
    }, 300);

    return () => clearTimeout(timer);
  }, [uomSearchTerm]);

  // Server-side search for Suppliers
  const searchSuppliers = useCallback(async (searchQuery: string) => {
    if (!searchQuery || searchQuery.length < 2) {
      setSupplierSearchResults([]);
      return;
    }

    setIsSupplierSearching(true);
    try {
      const url = buildApiUrl(base_url, `${getApiEndpoints().SUPPLIERS}?search=${encodeURIComponent(searchQuery)}&limit=100`);
      console.log('🔍 Searching suppliers at URL:', url);
      const response = await fetch(url);
      console.log('🔍 Supplier search response status:', response.status);
      const data = await response.json();
      console.log('🔍 Supplier search data:', data);
      
      if (data.suppliers) {
        setSupplierSearchResults(data.suppliers);
      } else if (Array.isArray(data)) {
        // Fallback for old API format
        setSupplierSearchResults(data);
      } else {
        setSupplierSearchResults([]);
      }
    } catch (error) {
      console.error('Error searching suppliers:', error);
      // Fallback to local filtering if server search fails
      const filteredSuppliers = suppliers.filter(supplier => 
        (supplier.supplier_name || supplier.name || '')
          .toLowerCase()
          .includes(searchQuery.toLowerCase())
      );
      setSupplierSearchResults(filteredSuppliers);
    } finally {
      setIsSupplierSearching(false);
    }
  }, [base_url, suppliers]);

  // Trigger supplier search when debounced search term changes
  useEffect(() => {
    searchSuppliers(debouncedSupplierSearchTerm);
  }, [debouncedSupplierSearchTerm, searchSuppliers]);

  // Debounce supplier search term
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSupplierSearchTerm(supplierSearchTerm);
    }, 300);

    return () => clearTimeout(timer);
  }, [supplierSearchTerm]);

  // Bid validation function
  const validateBidForm = useCallback(() => {
    const errors: string[] = [];
    const invalidFieldSet = new Set<string>();
    
    // Validate supplier
    if (!currentBid?.supplier_name) {
      errors.push("Please select a supplier");
      invalidFieldSet.add("supplier");
    }
    
    // Validate bid date
    if (!currentBid?.bid_date) {
      errors.push("Please select a bid date");
      invalidFieldSet.add("bid_date");
    }
    
    // Validate bid document
    if (!currentBid?.bid_document && !currentBid?.encoded_bid_document && !currentBid?.bid_document_url) {
      errors.push("Please select a bid document");
      invalidFieldSet.add("bid_document");
    }
    
    // Validate bid items
    if (!currentBid?.items || currentBid.items.length === 0) {
      errors.push("Please add at least one item to the bid");
    } else {
      // Validate each bid item
      currentBid.items.forEach((item, index) => {
        if (!item.quantity) {
          errors.push(`Item "${item.item_required}": Quantity is required`);
          invalidFieldSet.add(`item_${index}_quantity`);
        }
        if (!item.unit_price) {
          errors.push(`Item "${item.item_required}": Unit price is required`);
          invalidFieldSet.add(`item_${index}_unit_price`);
        }
        if (!item.unit_of_measurement) {
          errors.push(`Item "${item.item_required}": Unit of measurement is required`);
          invalidFieldSet.add(`item_${index}_unit_of_measurement`);
        }
        if (!item.vat) {
          errors.push(`Item "${item.item_required}": VAT selection is required`);
          invalidFieldSet.add(`item_${index}_vat`);
        }
      });
    }
    
    setBidValidationErrors(errors);
    setInvalidFields(invalidFieldSet);
    
    return errors.length === 0;
  }, [currentBid]);

  // Save current bid
  const onCurrentBidSave = useCallback(() => {
    console.log("💾 Save bid triggered:", { 
      currentBid, 
      isCreator: isCreator(),
      updateBidModal,
      addBidModal 
    });
    
    // Only creators can save bids
    if (!isCreator()) {
      onOpenResponse("Access Denied", "Only the creator can save bids to this schedule.", false);
      return;
    }
    
    // Clear previous validation errors
    setBidValidationErrors([]);
    setInvalidFields(new Set());
    
    // Validate form
    if (!validateBidForm()) {
      return; // Stop if validation fails
    }
    
    // Check if current bid already exists (edit mode)
    if (currentBid?.items) {
      const existingBid = bids.find((bid) => bid && bid.bid_count === currentBid.bid_count);
      console.log("🔍 Existing bid check:", { 
        currentBidCount: currentBid.bid_count, 
        existingBid: existingBid ? existingBid.bid_count : null,
        isEditMode: !!existingBid 
      });
      
      if (existingBid) {
        // Update existing bid
        console.log("🔄 Updating existing bid:", currentBid.bid_count);
        onSaveBid(currentBid, bids, currentBid.bid_count);
      } else {
        // Create new bid
        console.log("🆕 Creating new bid");
        onSaveBid(currentBid, bids);
      }
    }
  }, [currentBid, bids, onSaveBid, isCreator, updateBidModal, addBidModal, validateBidForm]);

  // Enhanced delete bid with compliance cleanup
  const deleteBid = useCallback((bid_count: number, supplier_name: string) => {
    // Only creators can delete bids
    if (!isCreator()) {
      onOpenResponse("Access Denied", "Only the creator can delete bids from this schedule.", false);
      return;
    }
    const form_data: FormData = new FormData();
    form_data.append("cs_id", csId);
    form_data.append("bid_count", JSON.stringify(bid_count));
    form_data.append("supplier_name", supplier_name);
    form_data.append("csrfmiddlewaretoken", csrfToken);

    fetch(`${base_url}/delete_bid`, {
      method: "POST",
      headers: {
        "X-CSRFToken": csrfToken,
      },
      body: form_data,
    })
      .then((response) => response.json())
      .then((data) => {
        console.log("data: ", data);
        if (data.success) {
          // Delete compliance if bid_no and supplier_name
          const updatedCompliance = compliance?.filter(
            (compliance_) =>
              compliance_.supplier_name !== supplier_name &&
              compliance_.bid_no !== bid_count
          );

          const updatedComplianceRemarks = complianceRemarks?.filter(
            (complianceRemark_) =>
              complianceRemark_.supplier_name !== supplier_name &&
              complianceRemark_.bid_no !== bid_count
          );
          
          setCompliance(updatedCompliance);
          setComplianceRemarks(updatedComplianceRemarks);
          
          onOpenResponse("Delete Bid Successful", "Bid deleted successfully", true);
          
          // Reset bid no index
          const newBidCount = bidCount > 0 ? bidCount - 1 : 0;
          const newBids = bids?.filter((bid) => bid.bid_count !== bid_count);
          
          // Update bid_count index for all bids sequentially
          const updatedBids = newBids?.map((bid, index) => {
            bid.bid_count = index + 1;
            return bid;
          });
          
          setBids(updatedBids || []);
          setBidCount(newBidCount);
          onSetDirectPurchaseLimit();
        } else {
          onOpenResponse("Delete Bid Error", "Failed to delete bid", false);
        }
             });
   }, [csId, csrfToken, base_url, compliance, complianceRemarks, bidCount, bids, onSetDirectPurchaseLimit]);



  // === COMPLIANCE MANAGEMENT FUNCTIONS ===

  // Add compliance table
  const onAddComplianceTable = useCallback(() => {
    // Only creators can add compliance tables
    if (!isCreator()) {
      onOpenResponse("Access Denied", "Only the creator can generate compliance tables.", false);
      return;
    }
    // add bid compliance
    if (bids && bids.length === 0) {
      onOpenResponse("Add Compliance Table Error", "Please add bids first", false);
      return;
    }
    
    const compliances = bids?.map((bid) => {
      // check if compliance already exists
      const comp = compliance?.find(
        (compliance) => compliance.supplier_name === bid.supplier_name
      );
      if (comp) {
        return comp;
      } else {
        return {
          bid_no: bid.bid_count,
          supplier: bid.supplier,
          supplier_name: bid.supplier_name,
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
      }
    });

    const complianceRemarks_ = bids?.map((bid) => {
      // check if compliance remarks already exist
      const comp = complianceRemarks?.find(
        (compR) => compR.supplier_name === bid.supplier_name
      );
      if (comp) {
        return comp;
      } else {
        return {
          bid_count: bid.bid_count,
          supplier: bid.supplier,
          supplier_name: bid.supplier_name,
          remarks: "",
        };
      }
    });

    setCompliance(compliances || []);
    setComplianceRemarks(complianceRemarks_ || []);
    
    console.log("Generated compliance table:", {
      bids_count: bids?.length || 0,
      compliance_count: compliances?.length || 0,
      remarks_count: complianceRemarks_?.length || 0
    });
  }, [bids, compliance, complianceRemarks]);



  // Handle compliance change
  const onComplianceChange = useCallback((
    index: number,
    event: { target: { name: string; checked: boolean } }
  ) => {
    const { name, checked } = event.target;
    console.log("name : ", name, "checked: ", checked);
    console.log("compliance: ", compliance);
    
    if (compliance && compliance.length > 0) {
      const currentCompliances = [...compliance];
      const currentCompliance = currentCompliances[index];
      console.log("currentCompliance: ", currentCompliance);
      currentCompliance[name] = checked;
      console.log("currentCompliance: ", name, currentCompliance);

      // Set decision based on all compliance checks
      const keysToCheck = [
        'payment_terms', 'bid_validity', 'delivery_period',
        'technical_specifications', 'valid_tax_clearance', 'registered_with_praz'
      ];
      
      if (showSiteVisit === "yes") keysToCheck.push('site_visit');
      if (showSamples === "yes") keysToCheck.push('samples_required');

      const allValuesTrue = keysToCheck.every((key) => currentCompliance[key] === true);
      currentCompliance["decision"] = allValuesTrue;
      currentCompliance["reject"] = !allValuesTrue;

      setCompliance(currentCompliances);
    }
  }, [compliance, showSiteVisit, showSamples]);

  // Handle compliance remarks change
  const onComplianceRemarksChange = useCallback((
    supplier_name: string,
    event: { target: { name: string; value: string } }
  ) => {
    const { value } = event.target;
    console.log("supplier_name: ", supplier_name, "value: ", value);
    
    if (complianceRemarks && complianceRemarks.length > 0) {
      const updatedRemarks = complianceRemarks.map((remark) => {
        if (remark.supplier_name === supplier_name) {
          return {
            ...remark,
            remarks: value,
          };
        }
        return remark;
      });
      setComplianceRemarks(updatedRemarks);
    }
  }, [complianceRemarks]);

  // Handle check all for a specific compliance row
  const onCheckAllCompliance = useCallback((index: number) => {
    if (compliance && compliance.length > 0) {
      const currentCompliances = [...compliance];
      const currentCompliance = currentCompliances[index];
      
      // Check all required criteria
      const keysToCheck = [
        'payment_terms', 'bid_validity', 'delivery_period',
        'technical_specifications', 'valid_tax_clearance', 'registered_with_praz'
      ];
      
      if (showSiteVisit === "yes") keysToCheck.push('site_visit');
      if (showSamples === "yes") keysToCheck.push('samples_required');

      // Set all criteria to true
      keysToCheck.forEach(key => {
        currentCompliance[key] = true;
      });

      // Update decision and reject status
      currentCompliance["decision"] = true;
      currentCompliance["reject"] = false;

      setCompliance(currentCompliances);
      console.log(`All compliance criteria checked for ${currentCompliance.supplier_name}`);
    }
  }, [compliance, showSiteVisit, showSamples]);

  // Save compliance
  const onSaveCompliance = useCallback(() => {
    // Only creators can save compliance
    if (!isCreator()) {
      onOpenResponse("Access Denied", "Only the creator can save compliance data.", false);
      return;
    }
    if (!compliance || compliance.length === 0) {
      onOpenResponse("Save Compliance Error", "Please add compliance data first", false);
      return;
    }

    setIsLoading(true);
    setLoadingOperation("Saving compliance data");

    // Format data to match backend expectations (similar to the working JS versions)
    const form_data: FormData = new FormData();
    form_data.append("cs_id", csId);
    form_data.append("show_site_visit", showSiteVisit);
    form_data.append("show_samples_required", showSamples);
    form_data.append(
      "compliance",
      JSON.stringify({
        compliance: compliance,
      })
    );
    form_data.append(
      "complianceRemarks",
      JSON.stringify({
        complianceRemarks: complianceRemarks,
      })
    );
    form_data.append("csrfmiddlewaretoken", csrfToken);

    console.log("Saving compliance data:", {
      cs_id: csId,
      compliance_count: compliance.length,
      remarks_count: complianceRemarks.length,
      show_site_visit: showSiteVisit,
      show_samples: showSamples
    });

    fetch(`${base_url}/save_compliance`, {
      method: "POST",
      headers: {
        "X-CSRFToken": csrfToken,
      },
      body: form_data,
    })
      .then((response) => response.json())
      .then((data) => {
        console.log("save compliance response: ", data);
        if (data.success) {
          onOpenResponse("Save Compliance Success", "Compliance data saved successfully", true);
          // Refresh the CS data to ensure persistence
          if (csId) {
            fetchCS(csId);
          }
        } else {
          onOpenResponse("Save Compliance Error", data.message || "Failed to save compliance, please try again.", false);
        }
      })
      .catch((error) => {
        console.error("Error saving compliance:", error);
        onOpenResponse("Error", "Failed to save compliance", false);
      })
      .finally(() => {
        setIsLoading(false);
        setLoadingOperation("");
      });
  }, [compliance, complianceRemarks, csId, csrfToken, base_url, fetchCS, showSiteVisit, showSamples]);

  // Close CS and generate rankings
  const onCloseCS = useCallback(() => {
    // Only creators can close CS and generate rankings
    if (!isCreator()) {
      onOpenResponse("Access Denied", "Only the creator can generate rankings.", false);
      return;
    }
    // Validation: Check if compliance data exists
    if (!compliance || compliance.length === 0) {
      onOpenResponse("Generate Rankings Error", "Please complete compliance evaluation first", false);
      return;
    }

    // Validation: Check if at least one bid is compliant
    const compliantBids = compliance.filter(comp => comp.decision === true);
    if (compliantBids.length === 0) {
      onOpenResponse("Generate Rankings Error", "No compliant bids found. Please review compliance evaluation.", false);
      return;
    }

    setIsLoading(true);
    setLoadingOperation("Generating bid rankings");

    const form_data: FormData = new FormData();
    form_data.append("cs_id", csId);
    form_data.append("csrfmiddlewaretoken", csrfToken);

    fetch(`${base_url}/close_compliance`, {
      method: "POST",
      headers: {
        "X-CSRFToken": csrfToken,
      },
      body: form_data,
    })
      .then((response) => response.json())
      .then((data) => {
        console.log("close CS data: ", data);
        if (data.success) {
          const rankings = data.rankings;
          setRankings(rankings);
          onOpenResponse("Rank Bids Successful", `Successfully generated rankings for ${rankings.length} bids`, true);
        } else {
          onOpenResponse("Rank Bids Error", data.message || "Failed to rank bids, please try again", false);
        }
      })
      .catch((error) => {
        console.error("Error closing CS:", error);
        onOpenResponse("Error", "Failed to rank bids", false);
      })
      .finally(() => {
        setIsLoading(false);
        setLoadingOperation("");
      });
  }, [csId, csrfToken, base_url, compliance]);

  // === ADDITIONAL FEATURES ===

  // Handle additional notes change
  const onAdditionalNotesChange = useCallback((event: { target: { name: string; value: string } }) => {
    const { value } = event.target;
    setAdditionalNotes(value);
  }, []);

  // Submit additional notes
  const onAdditionalNotesSubmit = useCallback(() => {
    const form_data: FormData = new FormData();
    form_data.append("cs_id", csId);
    form_data.append("additional_notes", additionalNotes);
    form_data.append("csrfmiddlewaretoken", csrfToken);

    fetch(`${base_url}/save_additional_notes`, {
      method: "POST",
      headers: {
        "X-CSRFToken": csrfToken,
      },
      body: form_data,
    })
      .then((response) => response.json())
      .then((data) => {
        console.log("additional notes data: ", data);
        if (data.success) {
          onOpenResponse("Additional Notes Saved", "Additional notes saved successfully", true);
        } else {
          onOpenResponse("Additional Notes Error", "Failed to save additional notes", false);
        }
      })
      .catch((error) => {
        console.error("Error saving additional notes:", error);
        onOpenResponse("Error", "Failed to save additional notes", false);
      });
  }, [csId, additionalNotes, csrfToken, base_url]);

  // Handle buyer notes change
  const onBuyersNotesChange = useCallback((event: { target: { name: string; value: string } }) => {
    const { value } = event.target;
    setBuyersNotes(value);
  }, []);

  // Submit buyer notes
  const onBuyersNotesSubmit = useCallback(() => {
    // Only creators can submit buyer's notes
    if (!isCreator()) {
      onOpenResponse("Access Denied", "Only the creator can submit buyer's notes.", false);
      return;
    }
    const form_data: FormData = new FormData();
    form_data.append("cs_id", csId);
    form_data.append("buyers_notes", buyersNotes);
    form_data.append("csrfmiddlewaretoken", csrfToken);

    fetch(`${base_url}/save_buyers_notes`, {
      method: "POST",
      headers: {
        "X-CSRFToken": csrfToken,
      },
      body: form_data,
    })
      .then((response) => response.json())
      .then((data) => {
        console.log("buyers notes data: ", data);
        if (data.success) {
          // Update rankings with buyer notes for rank 1
          const newRankings = (rankings ?? []).map((ranking) => {
            if (ranking.rank === 1) {
              ranking.remarks = buyersNotes;
            }
            return ranking;
          });
          setRankings(newRankings);
          onOpenResponse("Buyer's Notes Saved", "Buyer's notes saved successfully", true);
        } else {
          onOpenResponse("Buyer's Notes Error", "Failed to save buyer's notes", false);
        }
      })
      .catch((error) => {
        console.error("Error saving buyer notes:", error);
        onOpenResponse("Error", "Failed to save buyer's notes", false);
      });
  }, [csId, buyersNotes, csrfToken, base_url, rankings]);



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
        // Update prData with the selected procurement plan
        if (selectedProcPlan) {
          updatePrData('procurement_plan_id', selectedProcPlan.id.toString());
          updatePrData('procurement_plan_description', selectedProcPlan.description);
        } else {
          updatePrData('procurement_plan_id', '');
          updatePrData('procurement_plan_description', '');
        }
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
      formData.append("proc_plan_id", (procPlan?.id || prData.procurement_plan_id || "").toString());
      formData.append("pr_number", prData.pr_number);
      formData.append("quantity", quantity.toString());
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
            {/* PR Fetch Section - Visible to creator or when creating new schedule */}
            {(isCreator() || !csId || csId === "") && (
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
                  {!csId 
                    ? "Load existing Purchase Request data to populate this new schedule."
                    : "This will populate all fields below with data from the specified Purchase Request."
                  }
                </p>
              </div>
            )}

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
                      className={`w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${!isCreator() ? 'bg-gray-100 cursor-not-allowed' : ''}`}
                      placeholder="Enter PR Number"
                      value={prData.pr_number}
                      onChange={(e) => updatePrData('pr_number', e.target.value)}
                      readOnly={!isCreator()}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">PR Date</label>
                    <input 
                      type="date" 
                      className={`w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${!isCreator() ? 'bg-gray-100 cursor-not-allowed' : ''}`}
                      value={prData.pr_date}
                      onChange={(e) => updatePrData('pr_date', e.target.value)}
                      readOnly={!isCreator()}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Reference Date</label>
                    <input 
                      type="date" 
                      className={`w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${!isCreator() ? 'bg-gray-100 cursor-not-allowed' : ''}`}
                      value={prData.reference_date}
                      onChange={(e) => updatePrData('reference_date', e.target.value)}
                      readOnly={!isCreator()}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Procurement Plan</label>
                    <select 
                      className={`w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${!isCreator() ? 'bg-gray-100 cursor-not-allowed' : ''}`}
                      onChange={(e) => onSelectChange("procPlan", e)}
                      value={procPlan?.id || prData.procurement_plan_id || ""}
                      disabled={!isCreator()}
                    >
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
                      className={`w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${!isCreator() ? 'bg-gray-100 cursor-not-allowed' : ''}`}
                      onChange={(e) => onSelectChange("currency", e)}
                      value={currency?.id || ""}
                      disabled={!isCreator()}
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
                      className={`w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${!isCreator() ? 'bg-gray-100 cursor-not-allowed' : ''}`}
                      value={prData.closing_date}
                      onChange={(e) => updatePrData('closing_date', e.target.value)}
                      readOnly={!isCreator()}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Closing Time</label>
                    <input 
                      type="time" 
                      className={`w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${!isCreator() ? 'bg-gray-100 cursor-not-allowed' : ''}`}
                      value={prData.closing_time}
                      onChange={(e) => updatePrData('closing_time', e.target.value)}
                      readOnly={!isCreator()}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">CS Opened Date</label>
                    <input 
                      type="date" 
                      className={`w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${!isCreator() ? 'bg-gray-100 cursor-not-allowed' : ''}`}
                      value={prData.cs_opened_date}
                      onChange={(e) => updatePrData('cs_opened_date', e.target.value)}
                      readOnly={!isCreator()}
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
                  className={`w-full p-3 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${!isCreator() ? 'bg-gray-100 cursor-not-allowed' : ''}`}
                  placeholder="Enter detailed scope of work..."
                  value={prData.scope_of_work}
                  onChange={(e) => updatePrData('scope_of_work', e.target.value)}
                  readOnly={!isCreator()}
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
                      className={`w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${!isCreator() ? 'bg-gray-100 cursor-not-allowed' : ''}`}
                      value={prData.tac_date}
                      onChange={(e) => updatePrData('tac_date', e.target.value)}
                      readOnly={!isCreator()}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Region</label>
                    <div className="text-sm text-gray-900 bg-gray-50 p-2 rounded border">
                      {prData.region || 'Not specified'}
                    </div>
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
                            {isCreator() && (
                              <button
                                type="button"
                                onClick={() => setAdvert(undefined)}
                                className="mt-2 text-sm text-red-600 hover:text-red-500"
                              >
                                Remove file
                              </button>
                            )}
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
                            {isCreator() && (
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
                            )}
                          </div>
                        </div>
                      ) : (
                        <div className="text-center">
                          <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                            <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                          </svg>
                          {isCreator() ? (
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
                          ) : (
                            <div className="mt-2">
                              <p className="text-sm text-gray-500">No advertisement document uploaded</p>
                            </div>
                          )}
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
                {isCreator() && (
                  <button 
                    onClick={handleSaveScheduleDetails}
                    className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 transition-colors flex items-center"
                  >
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                    </svg>
                    Save Schedule Details
                  </button>
                )}
                {/* <button className="bg-green-600 text-white px-6 py-2 rounded hover:bg-green-700 transition-colors flex items-center">
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
                </button> */}
                {isCreator() && (
                  <button className="bg-red-600 text-white px-6 py-2 rounded hover:bg-red-700 transition-colors flex items-center">
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                    Cancel Schedule
                  </button>
                )}
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
                      <div className="transition-all duration-300 ease-in-out">
                        {/* Skeleton loading for PR items */}
                        <div className="space-y-3">
                          {[...Array(5)].map((_, i) => (
                            <div key={i} className="animate-pulse bg-gray-200 rounded-lg p-4 flex items-center space-x-4">
                              <div className="w-4 h-4 bg-gray-300 rounded"></div>
                              <div className="flex-1">
                                <div className="h-4 bg-gray-300 rounded w-3/4 mb-2"></div>
                                <div className="h-3 bg-gray-300 rounded w-1/2"></div>
                              </div>
                              <div className="w-16 h-6 bg-gray-300 rounded"></div>
                            </div>
                          ))}
                        </div>
                        <div className="flex items-center justify-center py-4 mt-6">
                          <div className="animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-blue-600 mr-3"></div>
                          <span className="text-gray-600 font-medium">Loading PR items...</span>
                        </div>
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
                      <div className="transition-all duration-500 ease-in-out">
                        {/* Summary Statistics */}
                        <div className="mb-4 p-4 bg-gray-50 rounded-lg">
                          <p className="text-sm text-gray-600">
                            <span className="font-medium text-gray-900">Total Items: {prData.items.length}</span>
                            {prData.items.length > 0 && (
                              <>
                                <span className="mx-2">|</span>
                                <span className="text-green-700">Available: {prData.items.filter(item => item.status === 'available' || !item.status).length}</span>
                                <span className="mx-2">|</span>
                                <span className="text-orange-700">Used Elsewhere: {prData.items.filter(item => item.status === 'used_in_other_schedule').length}</span>
                                <span className="mx-2">|</span>
                                <span className="text-blue-700">Included Here: {prData.items.filter(item => item.included || item.status === 'included_in_cs').length}</span>
                              </>
                            )}
                          </p>
                        </div>
                        
                        <div className="overflow-x-auto transform transition-all duration-300 ease-in-out">
                          <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                              <tr>
                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                  {isCreator() && (
                                    <input 
                                      type="checkbox" 
                                      className="h-4 w-4 text-blue-600 border-gray-300 rounded" 
                                      checked={allItemsSelected}
                                      onChange={(e) => handleSelectAllItems(e.target.checked)}
                                      title={allItemsSelected ? "Deselect all items" : "Select all items"}
                                    />
                                  )}
                                </th>
                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Item Required</th>
                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Quantity</th>
                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Unit of Measurement</th>
                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                              </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                              {(() => {
                                const filteredItems = prData.items.filter(item => isCreator() ? true : (item.included || item.status === 'included_in_cs'));
                                console.log('PR Items Debug:', {
                                  totalItems: prData.items.length,
                                  isCreator: isCreator(),
                                  username: username,
                                  creator: creator,
                                  csId: csId,
                                  filteredItemsCount: filteredItems.length,
                                  items: prData.items.slice(0, 3) // Show first 3 items for debugging
                                });
                                return filteredItems.map((item) => (
                                  <tr key={item.id} className={
                                    item.status === 'included_in_cs' ? 'bg-blue-50' : 
                                    item.status === 'used_in_other_schedule' ? 'bg-gray-50' : ''
                                  }>
                                    <td className="px-4 py-3 whitespace-nowrap">
                                      {isCreator() ? (
                                        <div className="flex items-center">
                                          {item.included && item.status !== 'included_in_cs' && (
                                            <div className="w-2 h-2 bg-red-500 rounded-full mr-2" title="Newly selected"></div>
                                          )}
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
                                        </div>
                                      ) : (
                                        <div className="w-4 h-4 flex items-center justify-center">
                                          {item.included && (
                                            <svg className="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                                              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                            </svg>
                                          )}
                                        </div>
                                      )}
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
                                ));
                              })()}
                                                      </tbody>
                          </table>
                        </div>
                        <div className="mt-4 flex justify-between items-center">
                          <div className="text-sm text-gray-500">
                            {isCreator() ? (
                              <>
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
                              </>
                            ) : (
                              <>
                                View of selected items in this comparative schedule. Only the creator can modify item selections.
                                <div className="text-xs text-gray-400 mt-1 space-y-1">
                                  {prData.items.some(item => item.status === 'included_in_cs') && (
                                    <div className="flex items-center">
                                      <div className="w-3 h-3 bg-blue-100 rounded mr-2"></div>
                                      <span>Blue background: Items currently in this schedule</span>
                                    </div>
                                  )}
                                  <div className="flex items-center">
                                    <svg className="w-3 h-3 text-green-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
                                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                    </svg>
                                    <span>Green checkmark: Selected items</span>
                                  </div>
                                </div>
                              </>
                            )}
                          </div>
                          {isCreator() && (
                            <button 
                              onClick={handleUpdateSelectedItems}
                              disabled={!csId || isLoading || prData.items.filter(item => item.included && (item.status === 'available' || item.status === 'included_in_cs' || !item.status)).length === 0 || ( bids && bids.length > 0)}
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
                          )}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Additional Notes */}
                  <div className="bg-white p-6 rounded-lg shadow-sm border">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4 border-b pb-2">Additional Notes</h3>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Internal Notes</label>
                      <textarea 
                        rows={3}
                        className={`w-full p-3 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${!isCreator() ? 'bg-gray-100 cursor-not-allowed' : ''}`}
                        placeholder="Add any additional notes or special instructions..."
                        value={prData.internal_notes}
                        onChange={(e) => updatePrData('internal_notes', e.target.value)}
                        readOnly={!isCreator()}
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
            <div className="space-y-6">
              {!csId ? (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
                  <div className="flex items-center">
                    <svg className="w-6 h-6 text-yellow-600 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                    </svg>
                    <div>
                      <h3 className="text-lg font-medium text-yellow-800">Schedule Required</h3>
                      <p className="text-yellow-700 mt-1">Please save the schedule details first before managing bids.</p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Bid Management Header */}
                  <div className="bg-white p-6 rounded-lg shadow-sm border">
                    <div className="flex justify-between items-center">
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                          <svg className="w-5 h-5 mr-2 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                          </svg>
                          Supplier Bids Management
                        </h3>
                        <p className="text-gray-600 mt-1">
                          {isCreator() 
                            ? "Add and manage supplier bids for this comparative schedule."
                            : "View supplier bids for this comparative schedule. Only the creator can modify bids."
                          }
                        </p>
                      </div>
                      {isCreator() ? (
                        <div className="flex space-x-3">
                          <button
                            onClick={onAddSuppliersModal}
                            className="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700 transition-colors flex items-center"
                          >
                            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                            </svg>
                            Add Supplier
                          </button>
                          <button
                            onClick={onAddBidModal}
                            disabled={prData.items.filter(item => item.included).length === 0}
                            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center"
                          >
                            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                            </svg>
                            Add New Bid
                          </button>
                        </div>
                      ) : (
                        <div className="text-sm text-gray-500">
                          View-only mode - Only the creator can manage bids
                        </div>
                      )}
                    </div>
                    
                    {directPurchaseLimit && base_url === "/direct_purchase" && (
                      <div className="mt-4 bg-orange-50 border border-orange-200 rounded-lg p-3">
                        <p className="text-orange-800 text-sm">
                          <svg className="w-4 h-4 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                          </svg>
                          Direct Purchase Mode: Maximum 1 bid allowed.
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Existing Bids Display */}
                  <div className="bg-white p-6 rounded-lg shadow-sm border">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4 border-b pb-2">Current Bids</h3>
                    
                    {bids.length === 0 ? (
                      <div className="text-center py-8">
                        <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V9a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                        </svg>
                        <h3 className="mt-2 text-sm font-medium text-gray-900">No bids submitted yet</h3>
                        <p className="mt-1 text-sm text-gray-500">
                          {isCreator() 
                            ? "Get started by adding a new supplier bid."
                            : "No bids have been submitted for this schedule yet."
                          }
                        </p>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {bids.map((bid, index) => {
                          const bidId = bid.bid_count || index;
                          const isExpanded = expandedBids.has(bidId);
                          
                          return (
                            <div key={index} className="border border-gray-200 rounded-lg overflow-hidden">
                              {/* Header - Always Visible */}
                              <div className="p-4 hover:bg-gray-50 cursor-pointer" 
                                   onClick={() => {
                                     const newExpanded = new Set(expandedBids);
                                     if (isExpanded) {
                                       newExpanded.delete(bidId);
                                     } else {
                                       newExpanded.add(bidId);
                                     }
                                     setExpandedBids(newExpanded);
                                   }}>
                                <div className="flex justify-between items-start">
                                  <div className="flex-1">
                                    <div className="flex items-center mb-2">
                                      <h4 className="text-lg font-medium text-gray-900 mr-3">
                                        Bid #{bid.bid_count} - {bid.supplier_name}
                                      </h4>
                                      <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                                        Active
                                      </span>
                                      <svg className={`w-5 h-5 ml-2 transform transition-transform ${isExpanded ? 'rotate-180' : ''}`} 
                                           fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
                                      </svg>
                                    </div>
                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-600">
                                      <div>
                                        <span className="font-medium">Bid Date:</span> {formatDisplayDate(bid.bid_date || '')}
                                      </div>
                                      <div>
                                        <span className="font-medium">Items:</span> {bid.items?.length || 0} items
                                      </div>
                                      <div>
                                        <span className="font-medium">Total:</span> ${calculateBidTotal(bid.items).toLocaleString()}
                                      </div>
                                    </div>
                                                                         {(bid.encoded_bid_document || bid.bid_document || bid.bid_document_url) && (
                                        <div className="mt-2">
                                          <a
                                            href={
                                              bid.bid_document_url || 
                                              onGetFileObjectUrl(bid.encoded_bid_document) ||
                                              onGetFileObjectUrl(bid.bid_document) ||
                                              "#"
                                            }
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            onClick={(e) => {
                                              e.stopPropagation();
                                              console.log("📄 Small document click:", {
                                                bid_document_url: bid.bid_document_url,
                                                encoded_bid_document: bid.encoded_bid_document ? "present" : "missing",
                                                bid_document: bid.bid_document ? "present" : "missing"
                                              });
                                            }}
                                            className="text-xs text-blue-600 hover:text-blue-800 hover:underline"
                                          >
                                            📄 View Document
                                          </a>
                                        </div>
                                      )}
                                  </div>
                                  {isCreator() && (
                                    <div className="flex space-x-2 ml-4" onClick={(e) => e.stopPropagation()}>
                                      <button
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          console.log("🔘 Edit button clicked for bid:", bid.bid_count);
                                          onUpdateBidModal(bid.bid_count || 0);
                                        }}
                                        className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                                      >
                                        Edit
                                      </button>
                                      <button
                                        onClick={() => {
                                          if (window.confirm(`Are you sure you want to delete the bid from ${bid.supplier_name}?`)) {
                                            deleteBid(bid.bid_count || 0, bid.supplier_name || '');
                                          }
                                        }}
                                        className="text-red-600 hover:text-red-800 text-sm font-medium"
                                      >
                                        Delete
                                      </button>
                                    </div>
                                  )}
                                </div>
                              </div>
                              
                              {/* Expandable Details */}
                              {isExpanded && (
                                <div className="border-t bg-gray-50 p-4">
                                  <div className="space-y-4">
                                    {/* Bid Items */}
                                    <div>
                                      <h5 className="text-md font-medium text-gray-900 mb-3">Bid Items</h5>
                                      {bid.items && bid.items.length > 0 ? (
                                        <div className="overflow-x-auto">
                                          <table className="min-w-full divide-y divide-gray-200" style={{ overflow: 'visible' }}>
                                            <thead className="bg-gray-100">
                                              <tr>
                                                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Item</th>
                                                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Unit</th>
                                                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Qty</th>
                                                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Unit Price</th>
                                                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">VAT</th>
                                                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Total</th>
                                              </tr>
                                            </thead>
                                            <tbody className="bg-white divide-y divide-gray-200">
                                              {bid.items.map((item, itemIndex) => (
                                                <tr key={itemIndex}>
                                                  <td className="px-3 py-2 text-sm text-gray-900">{item.item_required}</td>
                                                  <td className="px-3 py-2 text-sm text-gray-600">{item.unit_of_measurement || '-'}</td>
                                                  <td className="px-3 py-2 text-sm text-gray-900">{item.quantity}</td>
                                                  <td className="px-3 py-2 text-sm text-gray-900">${(Number(item.unit_price) || 0).toLocaleString()}</td>
                                                  <td className="px-3 py-2 text-sm text-gray-600">{item.vat || '-'}</td>
                                                  <td className="px-3 py-2 text-sm font-medium text-gray-900">${(Number(item.total_price) || 0).toLocaleString()}</td>
                                                </tr>
                                              ))}
                                            </tbody>
                                            <tfoot className="bg-gray-50">
                                              <tr>
                                                <td colSpan={5} className="px-3 py-2 text-sm font-medium text-gray-900 text-right">Grand Total:</td>
                                                <td className="px-3 py-2 text-sm font-bold text-gray-900">
                                                  ${calculateBidTotal(bid.items).toLocaleString()}
                                                </td>
                                              </tr>
                                            </tfoot>
                                          </table>
                                        </div>
                                      ) : (
                                        <p className="text-sm text-gray-500">No items in this bid</p>
                                      )}
                                    </div>
                                    
                                    {/* Additional Details */}
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                                             <div>
                                         <h6 className="text-sm font-medium text-gray-900 mb-2">Supplier Details</h6>
                                         <div className="text-sm text-gray-600">
                                           <p><span className="font-medium">Name:</span> {bid.supplier_name}</p>
                                         </div>
                                       </div>
                                                                             <div>
                                         <h6 className="text-sm font-medium text-gray-900 mb-2">Documents</h6>
                                         <div className="text-sm text-gray-600">
                                                                                      {bid.encoded_bid_document || bid.bid_document || bid.bid_document_url ? (
                                              <a
                                                href={
                                                  bid.bid_document_url || 
                                                  onGetFileObjectUrl(bid.encoded_bid_document) ||
                                                  onGetFileObjectUrl(bid.bid_document) ||
                                                  "#"
                                                }
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="text-blue-600 hover:text-blue-800 hover:underline flex items-center"
                                                onClick={() => {
                                                  // Debug logging
                                                  console.log("📄 Document click:", {
                                                    bid_document_url: bid.bid_document_url,
                                                    encoded_bid_document: bid.encoded_bid_document ? "present" : "missing",
                                                    bid_document: bid.bid_document ? "present" : "missing",
                                                    generatedUrl: onGetFileObjectUrl(bid.encoded_bid_document) || onGetFileObjectUrl(bid.bid_document)
                                                  });
                                                }}
                                              >
                                                <svg className="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                                </svg>
                                                View/Download Bid Document
                                                <svg className="w-3 h-3 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                                                </svg>
                                              </a>
                                            ) : (
                                              <p>No documents attached</p>
                                            )}
                                         </div>
                                       </div>
                                    </div>
                                  </div>
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </Suspense>
        );
      case 'committee':
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
                      <h3 className="text-lg font-medium text-yellow-800">Schedule Required</h3>
                      <p className="text-yellow-700 mt-1">Please save the schedule before managing committee and approvals.</p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="space-y-6">
                  <CommitteeApprovalWrapper
                    users={users}
                    onSaveCommittee={handleSaveCommittee}
                    onApprove={(username: string, approval: string, justification: string) => 
                      handleApprove('committee', username, approval, justification)
                    }
                    isCreator={isCreator()}
                    csrfToken={csrfToken}
                  />

                  {/* GM/FM Approval Table */}
                  <ApprovalTableWrapper
                    csId={csId}
                    username={username}
                    gmApproval={gmApproval}
                    fmApproval={fmApproval}
                    isCreator={isCreator()}
                    onApprove={handleApprove}
                    currentUserRoles={currentUserRoles}
                  />

                  {/* Approval Summary */}
                  <div className="bg-white p-6 rounded-lg shadow-sm border">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4 border-b pb-2">Approval Summary</h3>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-gray-600">Committee Approval:</span>
                        <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                          committeeMembers.every(m => m.memberApproval === "Approved")
                            ? "bg-green-100 text-green-800"
                            : committeeMembers.some(m => m.memberApproval === "Rejected")
                            ? "bg-red-100 text-red-800"
                            : "bg-yellow-100 text-yellow-800"
                        }`}>
                          {committeeMembers.every(m => m.memberApproval === "Approved")
                            ? "Complete"
                            : committeeMembers.some(m => m.memberApproval === "Rejected")
                            ? "Rejected"
                            : "Pending"
                          }
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-gray-600">GM Approval:</span>
                        <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                          gmApproval?.approval === "Approved" 
                            ? "bg-green-100 text-green-800"
                            : gmApproval?.approval === "Rejected"
                            ? "bg-red-100 text-red-800"
                            : "bg-yellow-100 text-yellow-800"
                        }`}>
                          {gmApproval?.approval === "Approved" 
                            ? "Complete"
                            : gmApproval?.approval === "Rejected"
                            ? "Rejected"
                            : "Pending"
                          }
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-gray-600">FM Approval:</span>
                        <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                          fmApproval?.approval === "Approved" 
                            ? "bg-green-100 text-green-800"
                            : fmApproval?.approval === "Rejected"
                            ? "bg-red-100 text-red-800"
                            : "bg-yellow-100 text-yellow-800"
                        }`}>
                          {fmApproval?.approval === "Approved" 
                            ? "Complete"
                            : fmApproval?.approval === "Rejected"
                            ? "Rejected"
                            : "Pending"
                          }
                        </span>
                      </div>
                      <div className="flex justify-between items-center border-t pt-3">
                        <span className="text-gray-900 font-medium">Overall Status:</span>
                        <span className={`px-3 py-1 text-sm font-semibold rounded-full ${
                          approvalsComplete
                            ? "bg-green-100 text-green-800"
                            : "bg-yellow-100 text-yellow-800"
                        }`}>
                          {approvalsComplete ? "All Approvals Complete" : "Approvals Pending"}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </Suspense>
        );
      case 'compliance':
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
                      <h3 className="text-lg font-medium text-yellow-800">Schedule Required</h3>
                      <p className="text-yellow-700 mt-1">Please save the schedule and add bids before managing compliance.</p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Compliance Requirements Setup */}
                  <div className="bg-white p-6 rounded-lg shadow-sm border">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4 border-b pb-2 flex items-center">
                      <svg className="w-5 h-5 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      Compliance Requirements Setup
                    </h3>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Site Visit Required</label>
                        <select 
                          className={`w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${!isCreator() ? 'bg-gray-100 cursor-not-allowed' : ''}`}
                          value={showSiteVisit}
                          onChange={(e) => setShowSiteVisit(e.target.value)}
                          disabled={!isCreator()}
                        >
                          <option value="no">No</option>
                          <option value="yes">Yes</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Samples Required</label>
                        <select 
                          className={`w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${!isCreator() ? 'bg-gray-100 cursor-not-allowed' : ''}`}
                          value={showSamples}
                          onChange={(e) => setShowSamples(e.target.value)}
                          disabled={!isCreator()}
                        >
                          <option value="no">No</option>
                          <option value="yes">Yes</option>
                        </select>
                      </div>
                    </div>
                    
                    {isCreator() ? (
                      <div className="mt-4">
                        <button
                          onClick={onAddComplianceTable}
                          disabled={bids.length === 0}
                          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center"
                        >
                          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                          </svg>
                          {compliance.length > 0 ? "Update Compliance Table" : "Generate Compliance Table"}
                        </button>
                      </div>
                    ) : (
                      <div className="mt-4 text-sm text-gray-500">
                        Only the creator can generate and update compliance tables.
                      </div>
                    )}
                  </div>

                  {/* Compliance Table */}
                  {compliance.length > 0 && (
                    <div className="bg-white p-6 rounded-lg shadow-sm border">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4 border-b pb-2">Compliance Evaluation</h3>
                      
                      <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                          <thead className="bg-gray-50">
                            <tr>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Supplier</th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Payment Terms</th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Bid Validity</th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Delivery Period</th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Technical Specs</th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tax Clearance</th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">PRAZ Registered</th>
                              {showSiteVisit === "yes" && (
                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Site Visit</th>
                              )}
                              {showSamples === "yes" && (
                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Samples</th>
                              )}
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Decision</th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Remarks</th>
                            </tr>
                          </thead>
                          <tbody className="bg-white divide-y divide-gray-200">
                            {compliance.map((comp, index) => (
                              <tr key={index} className={comp.decision ? "bg-green-50" : "bg-red-50"}>
                                <td className="px-4 py-3 text-sm font-medium text-gray-900">{comp.supplier_name}</td>
                                <td className="px-4 py-3 text-sm">
                                  {isCreator() ? (
                                    <button
                                      onClick={() => onCheckAllCompliance(index)}
                                      className="bg-blue-500 text-white px-2 py-1 rounded text-xs hover:bg-blue-600 transition-colors"
                                      title="Check all compliance criteria"
                                    >
                                      Check All
                                    </button>
                                  ) : (
                                    <span className="text-gray-500 text-xs">View Only</span>
                                  )}
                                </td>
                                <td className="px-4 py-3 text-sm">
                                  {isCreator() ? (
                                    <input
                                      type="checkbox"
                                      checked={comp.payment_terms}
                                      onChange={(e) => onComplianceChange(index, e)}
                                      name="payment_terms"
                                      className="h-4 w-4 text-blue-600 border-gray-300 rounded"
                                    />
                                  ) : (
                                    <div className="w-4 h-4 flex items-center justify-center">
                                      {comp.payment_terms && (
                                        <svg className="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                        </svg>
                                      )}
                                    </div>
                                  )}
                                </td>
                                <td className="px-4 py-3 text-sm">
                                  {isCreator() ? (
                                    <input
                                      type="checkbox"
                                      checked={comp.bid_validity}
                                      onChange={(e) => onComplianceChange(index, e)}
                                      name="bid_validity"
                                      className="h-4 w-4 text-blue-600 border-gray-300 rounded"
                                    />
                                  ) : (
                                    <div className="w-4 h-4 flex items-center justify-center">
                                      {comp.bid_validity && (
                                        <svg className="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                        </svg>
                                      )}
                                    </div>
                                  )}
                                </td>
                                <td className="px-4 py-3 text-sm">
                                  {isCreator() ? (
                                    <input
                                      type="checkbox"
                                      checked={comp.delivery_period}
                                      onChange={(e) => onComplianceChange(index, e)}
                                      name="delivery_period"
                                      className="h-4 w-4 text-blue-600 border-gray-300 rounded"
                                    />
                                  ) : (
                                    <div className="w-4 h-4 flex items-center justify-center">
                                      {comp.delivery_period && (
                                        <svg className="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                        </svg>
                                      )}
                                    </div>
                                  )}
                                </td>
                                <td className="px-4 py-3 text-sm">
                                  {isCreator() ? (
                                    <input
                                      type="checkbox"
                                      checked={comp.technical_specifications}
                                      onChange={(e) => onComplianceChange(index, e)}
                                      name="technical_specifications"
                                      className="h-4 w-4 text-blue-600 border-gray-300 rounded"
                                    />
                                  ) : (
                                    <div className="w-4 h-4 flex items-center justify-center">
                                      {comp.technical_specifications && (
                                        <svg className="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                        </svg>
                                      )}
                                    </div>
                                  )}
                                </td>
                                <td className="px-4 py-3 text-sm">
                                  {isCreator() ? (
                                    <input
                                      type="checkbox"
                                      checked={comp.valid_tax_clearance}
                                      onChange={(e) => onComplianceChange(index, e)}
                                      name="valid_tax_clearance"
                                      className="h-4 w-4 text-blue-600 border-gray-300 rounded"
                                    />
                                  ) : (
                                    <div className="w-4 h-4 flex items-center justify-center">
                                      {comp.valid_tax_clearance && (
                                        <svg className="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                        </svg>
                                      )}
                                    </div>
                                  )}
                                </td>
                                <td className="px-4 py-3 text-sm">
                                  {isCreator() ? (
                                    <input
                                      type="checkbox"
                                      checked={comp.registered_with_praz}
                                      onChange={(e) => onComplianceChange(index, e)}
                                      name="registered_with_praz"
                                      className="h-4 w-4 text-blue-600 border-gray-300 rounded"
                                    />
                                  ) : (
                                    <div className="w-4 h-4 flex items-center justify-center">
                                      {comp.registered_with_praz && (
                                        <svg className="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                        </svg>
                                      )}
                                    </div>
                                  )}
                                </td>
                                {showSiteVisit === "yes" && (
                                  <td className="px-4 py-3 text-sm">
                                    {isCreator() ? (
                                      <input
                                        type="checkbox"
                                        checked={comp.site_visit}
                                        onChange={(e) => onComplianceChange(index, e)}
                                        name="site_visit"
                                        className="h-4 w-4 text-blue-600 border-gray-300 rounded"
                                      />
                                    ) : (
                                      <div className="w-4 h-4 flex items-center justify-center">
                                        {comp.site_visit && (
                                          <svg className="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                          </svg>
                                        )}
                                      </div>
                                    )}
                                  </td>
                                )}
                                {showSamples === "yes" && (
                                  <td className="px-4 py-3 text-sm">
                                    {isCreator() ? (
                                      <input
                                        type="checkbox"
                                        checked={comp.samples_required}
                                        onChange={(e) => onComplianceChange(index, e)}
                                        name="samples_required"
                                        className="h-4 w-4 text-blue-600 border-gray-300 rounded"
                                      />
                                    ) : (
                                      <div className="w-4 h-4 flex items-center justify-center">
                                        {comp.samples_required && (
                                          <svg className="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                          </svg>
                                        )}
                                      </div>
                                    )}
                                  </td>
                                )}
                                <td className="px-4 py-3 text-sm">
                                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                                    comp.decision ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
                                  }`}>
                                    {comp.decision ? "Compliant" : "Non-Compliant"}
                                  </span>
                                </td>
                                <td className="px-4 py-3 text-sm">
                                  {isCreator() ? (
                                    <input
                                      type="text"
                                      value={complianceRemarks.find(r => r.supplier_name === comp.supplier_name)?.remarks || ''}
                                      onChange={(e) => onComplianceRemarksChange(comp.supplier_name || '', e)}
                                      name="remarks"
                                      placeholder="Add remarks..."
                                      className="w-full p-1 text-xs border border-gray-300 rounded"
                                    />
                                  ) : (
                                    <span className="text-xs text-gray-600">
                                      {complianceRemarks.find(r => r.supplier_name === comp.supplier_name)?.remarks || '-'}
                                    </span>
                                  )}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                      
                      {isCreator() ? (
                        <div className="mt-4 flex justify-between">
                          <button
                            onClick={onSaveCompliance}
                            className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 transition-colors flex items-center"
                          >
                            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                            </svg>
                            Save Compliance
                          </button>
                          
                          <button
                            onClick={onCloseCS}
                            disabled={compliance.every(c => !c.decision)}
                            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center"
                          >
                            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            Generate Rankings
                          </button>
                        </div>
                      ) : (
                        <div className="mt-4 text-sm text-gray-500 text-center">
                          Only the creator can save compliance data and generate rankings.
                        </div>
                      )}
                    </div>
                  )}

                  {/* Rankings Table */}
                  {rankings.length > 0 && (
                    <div className="bg-white p-6 rounded-lg shadow-sm border">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4 border-b pb-2 flex items-center">
                        <svg className="w-5 h-5 mr-2 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                        </svg>
                        Bid Rankings & Evaluation
                      </h3>
                      
                      <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                          <thead className="bg-gray-50">
                            <tr>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Rank</th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Supplier Name</th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total Amount</th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Decision</th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Remarks</th>
                            </tr>
                          </thead>
                          <tbody className="bg-white divide-y divide-gray-200">
                            {rankings.map((rank, index) => (
                              <tr key={index} className={rank.rank === 1 ? "bg-yellow-50" : ""}>
                                <td className="px-4 py-3 text-sm font-medium">
                                  <div className="flex items-center">
                                    {rank.rank === 1 && (
                                      <svg className="w-5 h-5 text-yellow-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                                      </svg>
                                    )}
                                    #{rank.rank}
                                  </div>
                                </td>
                                <td className="px-4 py-3 text-sm font-medium text-gray-900">{rank.supplier_name}</td>
                                <td className="px-4 py-3 text-sm text-gray-900">${rank.total.toLocaleString()}</td>
                                <td className="px-4 py-3 text-sm">
                                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                                    rank.decision === "Accepted" ? "bg-green-100 text-green-800" : 
                                    rank.decision === "Rejected" ? "bg-red-100 text-red-800" : "bg-yellow-100 text-yellow-800"
                                  }`}>
                                    {rank.decision || ""}
                                  </span>
                                </td>
                                <td className="px-4 py-3 text-sm text-gray-900">
                                  {rank.rank === 1 ? (
                                    <div className="space-y-2">
                                      {isCreator() ? (
                                        <>
                                          <textarea
                                            value={buyersNotes}
                                            onChange={onBuyersNotesChange}
                                            placeholder="Add buyer's notes for the winning bid..."
                                            className="w-full p-2 text-sm border border-gray-300 rounded"
                                            rows={2}
                                          />
                                          <button
                                            onClick={onBuyersNotesSubmit}
                                            className="text-xs bg-blue-600 text-white px-2 py-1 rounded hover:bg-blue-700"
                                          >
                                            Save Notes
                                          </button>
                                        </>
                                      ) : (
                                        <span className="text-sm text-gray-600">
                                          {buyersNotes || 'No notes added yet'}
                                        </span>
                                      )}
                                    </div>
                                  ) : (
                                    rank.remarks || '-'
                                  )}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                      
                      {/* Additional Notes Section */}
                      <div className="mt-6 border-t pt-4">
                        <h4 className="text-md font-semibold text-gray-900 mb-3">Additional Notes</h4>
                        <textarea
                          value={additionalNotes}
                          onChange={onAdditionalNotesChange}
                          placeholder="Add any additional notes about the evaluation process..."
                          className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                          rows={3}
                        />
                        <button
                          onClick={onAdditionalNotesSubmit}
                          className="mt-2 bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700 transition-colors flex items-center"
                        >
                          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                          </svg>
                          Save Additional Notes
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </Suspense>
        );
      case 'rankings':
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
                      <h3 className="text-lg font-medium text-yellow-800">Schedule Required</h3>
                      <p className="text-yellow-700 mt-1">Please save the schedule and complete compliance evaluation before managing rankings.</p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Rankings Table */}
                  <div className="bg-white p-6 rounded-lg shadow-sm border">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4 border-b pb-2 flex items-center">
                      <svg className="w-5 h-5 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                      </svg>
                      Supplier Rankings & Evaluation
                    </h3>
                    
                    {rankings.length > 0 ? (
                      <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                          <thead className="bg-gray-50">
                            <tr>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Rank</th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Supplier</th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total Score</th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Decision</th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Remarks</th>
                            </tr>
                          </thead>
                          <tbody className="bg-white divide-y divide-gray-200">
                            {rankings.map((rank, index) => (
                              <tr key={rank.id || index} className={rank.decision === 'Awarded' ? "bg-green-50" : "bg-gray-50"}>
                                <td className="px-4 py-3 text-sm font-medium text-gray-900">
                                  <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-blue-100 text-blue-800 text-xs font-medium">
                                    {rank.rank}
                                  </span>
                                </td>
                                <td className="px-4 py-3 text-sm font-medium text-gray-900">{rank.supplier_name}</td>
                                <td className="px-4 py-3 text-sm text-gray-900">{rank.total}</td>
                                <td className="px-4 py-3 text-sm">
                                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                    rank.decision === 'Awarded' 
                                      ? 'bg-green-100 text-green-800' 
                                      : rank.decision === 'Rejected'
                                      ? 'bg-red-100 text-red-800'
                                      : 'bg-yellow-100 text-yellow-800'
                                  }`}>
                                    {rank.decision || 'Pending'}
                                  </span>
                                </td>
                                <td className="px-4 py-3 text-sm text-gray-900">{rank.remarks || '-'}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ) : (
                      <div className="text-center py-8">
                        <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                        </svg>
                        <h3 className="mt-2 text-sm font-medium text-gray-900">No Rankings Available</h3>
                        <p className="mt-1 text-sm text-gray-500">
                          Rankings will appear here after the evaluation process is completed.
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </Suspense>
        );
      default:
        return null;
    }
  }, [activeTab, csId, creator, createdAt, suppliers, users, handleSaveBid, handleDeleteBid, handleSaveCommittee, onSaveCompliance, handleApprove, prData, updatePrData, updateItemSelection, handleSaveScheduleDetails, prIdInput, handleFetchPR, isLoading]);

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

      {/* Approval Justification Modal */}
      {approvalsJustificationModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 transition-opacity" aria-hidden="true">
              <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
            </div>
            <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <div className="sm:flex sm:items-start">
                  <div className="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-blue-100 sm:mx-0 sm:h-10 sm:w-10">
                    <svg className="h-6 w-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left w-full">
                    <h3 className="text-lg leading-6 font-medium text-gray-900">
                      {currentApprover?.role} Approval Action
                    </h3>
                    <div className="mt-4">
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Choose your action:
                      </label>
                      <div className="space-y-3 mb-4">
                        <label className="flex items-center">
                          <input
                            type="radio"
                            name="approvalAction"
                            value="Approved"
                            className="h-4 w-4 text-blue-600 border-gray-300 focus:ring-blue-500"
                            onChange={(e) => setCurrentApprover(prev => ({...prev!, approval: e.target.value}))}
                          />
                          <span className="ml-2 text-sm text-gray-700">Approve</span>
                        </label>
                        <label className="flex items-center">
                          <input
                            type="radio"
                            name="approvalAction"
                            value="Rejected"
                            className="h-4 w-4 text-red-600 border-gray-300 focus:ring-red-500"
                            onChange={(e) => setCurrentApprover(prev => ({...prev!, approval: e.target.value}))}
                          />
                          <span className="ml-2 text-sm text-gray-700">Reject</span>
                        </label>
                      </div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Justification:
                      </label>
                      <textarea
                        rows={4}
                        className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        placeholder="Please provide justification for your decision..."
                        value={currentApprover?.justification || ''}
                        onChange={(e) => setCurrentApprover(prev => ({...prev!, justification: e.target.value}))}
                      />
                    </div>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                <button
                  type="button"
                  onClick={async () => {
                    if (!currentApprover?.approval) {
                      onOpenResponse("Error", "Please select an approval action", false);
                      return;
                    }
                    if (currentApprover.approval === "Rejected" && !currentApprover.justification?.trim()) {
                      onOpenResponse("Error", "Justification is required for rejection", false);
                      return;
                    }
                    
                    await handleApprove(
                      currentApprover.role!,
                      currentApprover.username!,
                      currentApprover.approval,
                      currentApprover.justification || ''
                    );
                    
                    setApprovalsJustificationModal(false);
                    setCurrentApprover(undefined);
                  }}
                  className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:ml-3 sm:w-auto sm:text-sm"
                >
                  Submit
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setApprovalsJustificationModal(false);
                    setCurrentApprover(undefined);
                  }}
                  className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                >
                  Cancel
                </button>
              </div>
            </div>
                     </div>
         </div>
       )}

       {/* Add/Edit Bid Modal - Only for creators */}
       {(() => {
         const shouldShowModal = (addBidModal || updateBidModal) && currentBid && isCreator();
                  // Modal visibility check
         return shouldShowModal;
       })() && (
         <div className="fixed inset-0 z-50" style={{ overflow: 'visible' }}>
           <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0" style={{ overflow: 'visible' }}>
             <div className="fixed inset-0 transition-opacity" aria-hidden="true">
               <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
             </div>
             <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
             <div className="inline-block align-bottom bg-white rounded-lg text-left shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full" style={{ overflow: 'visible' }}>
               <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                 <div className="sm:flex sm:items-start">
                   <div className="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-blue-100 sm:mx-0 sm:h-10 sm:w-10">
                     <svg className="h-6 w-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                       <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                     </svg>
                   </div>
                   <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left w-full">
                     <h3 className="text-lg leading-6 font-medium text-gray-900">
                       {addBidModal ? 'Add New Bid' : 'Edit Bid'} #{currentBid?.bid_count}
                     </h3>
                     
                     {/* Validation Errors Display */}
                     {bidValidationErrors.length > 0 && (
                       <div className="mt-4 bg-red-50 border border-red-200 rounded-md p-4">
                         <div className="flex">
                           <div className="flex-shrink-0">
                             <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                               <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                             </svg>
                           </div>
                           <div className="ml-3">
                             <h3 className="text-sm font-medium text-red-800">
                               Please fix the following errors:
                             </h3>
                             <div className="mt-2 text-sm text-red-700">
                               <ul className="list-disc pl-5 space-y-1">
                                 {bidValidationErrors.map((error, index) => (
                                   <li key={index}>{error}</li>
                                 ))}
                               </ul>
                             </div>
                           </div>
                         </div>
                       </div>
                     )}
                     
                     <div className="mt-4 space-y-4">
                       {/* Supplier Selection */}
                       <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                         <div className="relative">
                           <label className="block text-sm font-medium text-gray-700 mb-2">Supplier</label>
                           <div className="relative">
                             <input
                               type="text"
                               placeholder="Search and select supplier..."
                               className={`w-full p-2 border rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500 pr-8 ${
                                 isFieldInvalid("supplier") 
                                   ? "border-red-300 focus:ring-red-500 focus:border-red-500" 
                                   : "border-gray-300"
                               }`}
                               value={supplierSearchTerm}
                               onChange={(e) => {
                                 setSupplierSearchTerm(e.target.value);
                                 setShowSupplierDropdown(true);
                               }}
                               onFocus={() => setShowSupplierDropdown(true)}
                               onBlur={() => {
                                 // Delay hiding dropdown to allow selection
                                 setTimeout(() => setShowSupplierDropdown(false), 200);
                               }}
                             />
                             <div className="absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none">
                               <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                 <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
                               </svg>
                             </div>
                             
                             {/* Dropdown */}
                             {showSupplierDropdown && (
                               <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto">
                                 {isSupplierSearching ? (
                                   <div className="px-3 py-2 text-gray-500 text-sm">
                                     Searching...
                                   </div>
                                 ) : (
                                   <>
                                     {supplierSearchResults.length > 0 ? (
                                       supplierSearchResults.map((supplier) => (
                                       <div
                                         key={supplier.id}
                                         className="px-3 py-2 cursor-pointer hover:bg-blue-50 hover:text-blue-900"
                                         onMouseDown={(e) => {
                                           e.preventDefault(); // Prevent input blur
                                           const supplierName = supplier.supplier_name || supplier.name || '';
                                           setSupplierSearchTerm(supplierName);
                                           setCurrentBid({
                                             ...currentBid,
                                             supplier: supplier.id?.toString(),
                                             supplier_name: supplierName,
                                           });
                                           setShowSupplierDropdown(false);
                                         }}
                                       >
                                         <div className="font-medium text-gray-900">
                                           {supplier.supplier_name || supplier.name}
                                         </div>
                                         {supplier.id && (
                                           <div className="text-xs text-gray-500">ID: {supplier.id}</div>
                                         )}
                                       </div>
                                     ))
                                   ) : (
                                     <div className="px-3 py-2 text-gray-500 text-sm">
                                       {supplierSearchTerm.length >= 2 ? 'No suppliers found' : 'Type to search suppliers...'}
                                     </div>
                                   )}
                                 </>
                               )}
                               </div>
                             )}
                           </div>
                         </div>
                         <div>
                           <label className="block text-sm font-medium text-gray-700 mb-2">Bid Date</label>
                           <input
                             type="date"
                             className={`w-full p-2 border rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                               isFieldInvalid("bid_date") 
                                 ? "border-red-300 focus:ring-red-500 focus:border-red-500" 
                                 : "border-gray-300"
                             }`}
                             value={currentBid?.bid_date || ''}
                             onChange={(e) => onCurrentBidChange('bid_date', e)}
                             name="bid_date"
                           />
                         </div>
                       </div>

                       {/* Bid Document */}
                       <div>
                         <label className="block text-sm font-medium text-gray-700 mb-2">Bid Document</label>
                         <input
                           type="file"
                           className={`w-full p-2 border rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                             isFieldInvalid("bid_document") 
                               ? "border-red-300 focus:ring-red-500 focus:border-red-500" 
                               : "border-gray-300"
                           }`}
                           accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
                           onChange={onBidDocumentChange}
                         />
                         <p className="text-xs text-gray-500 mt-1">PDF, DOC, or image files only (max 10MB)</p>
                         
                         {/* File Preview */}
                         {(currentBid?.bid_document || currentBid?.encoded_bid_document || currentBid?.bid_document_url) && (
                           <div className="mt-2 p-3 bg-gray-50 border border-gray-200 rounded">
                             <div className="flex items-center">
                               <svg className="w-5 h-5 text-blue-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                 <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                               </svg>
                               <div className="flex-1">
                                 {currentBid.bid_document instanceof File ? (
                                   <>
                                     <p className="text-sm font-medium text-gray-900">{currentBid.bid_document.name}</p>
                                     <p className="text-xs text-gray-500">
                                       {(currentBid.bid_document.size / 1024 / 1024).toFixed(2)} MB - {currentBid.bid_document.type}
                                     </p>
                                   </>
                                 ) : (
                                   <>
                                     <p className="text-sm font-medium text-gray-900">Existing document attached</p>
                                     <p className="text-xs text-gray-500">
                                       {currentBid.encoded_bid_document ? 'Encoded document' : 
                                        currentBid.bid_document_url ? 'Document URL available' : 'Document attached'}
                                     </p>
                                   </>
                                 )}
                               </div>
                               <button
                                 type="button"
                                 onClick={() => setCurrentBid({
                                   ...currentBid, 
                                   bid_document: undefined,
                                   encoded_bid_document: undefined,
                                   bid_document_url: undefined
                                 })}
                                 className="text-red-600 hover:text-red-800 text-sm"
                               >
                                 Remove
                               </button>
                             </div>
                           </div>
                         )}
                       </div>

                       {/* Bid Items */}
                       <div>
                         <h4 className="text-md font-medium text-gray-900 mb-3">Bid Items & Pricing</h4>
                         <div className="overflow-visible">
                           <table className="min-w-full divide-y divide-gray-200">
                             <thead className="bg-gray-50">
                               <tr>
                                 <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Item</th>
                                 <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Unit of Measure</th>
                                 <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Quantity</th>
                                 <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Unit Price</th>
                                 <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">VAT</th>
                                 <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Total Price</th>
                               </tr>
                             </thead>
                             <tbody className="bg-white divide-y divide-gray-200">
                               {currentBid?.items?.map((item, index) => (
                                 <tr key={index} style={{ overflow: 'visible' }}>
                                   <td className="px-4 py-2 text-sm font-medium text-gray-900">
                                     {item.item_required}
                                   </td>
                                   <td className="px-4 py-2 text-sm" style={{ position: 'relative', overflow: 'visible' }}>
                                     <div className="relative" style={{ position: 'relative', overflow: 'visible' }}>
                                       <input
                                         type="text"
                                         className={`w-full p-1 text-sm border rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500 pr-6 ${
                                           isFieldInvalid(`item_${index}_unit_of_measurement`) 
                                             ? "border-red-300 focus:ring-red-500 focus:border-red-500" 
                                             : "border-gray-300"
                                         }`}
                                         placeholder="Search UOM..."
                                         value={activeUomItem === item.item_required ? uomSearchTerm : (item.unit_of_measurement || '')}
                                         onChange={(e) => {
                                           setUomSearchTerm(e.target.value);
                                           setActiveUomItem(item.item_required || '');
                                           setShowUomDropdown(true);
                                         }}
                                         onFocus={() => {
                                           setActiveUomItem(item.item_required || '');
                                           setUomSearchTerm(item.unit_of_measurement || '');
                                           setShowUomDropdown(true);
                                         }}
                                         onBlur={() => {
                                           setTimeout(() => setShowUomDropdown(false), 200);
                                         }}
                                       />
                                       <div className="absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none">
                                         <svg className="w-3 h-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                           <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
                                         </svg>
                                       </div>
                                       
                                       {/* UOM Dropdown */}
                                       {showUomDropdown && activeUomItem === item.item_required && (
                                         <div 
                                           className="absolute z-[9999] w-full bg-white border border-gray-300 rounded-md shadow-lg overflow-auto" 
                                           style={{ 
                                             maxHeight: '180px',
                                             top: index >= (currentBid?.items?.length || 0) - 2 ? 'auto' : '100%',
                                             bottom: index >= (currentBid?.items?.length || 0) - 2 ? '100%' : 'auto',
                                             marginTop: index >= (currentBid?.items?.length || 0) - 2 ? '0' : '4px',
                                             marginBottom: index >= (currentBid?.items?.length || 0) - 2 ? '4px' : '0'
                                           }}
                                         >
                                           {isUomSearching ? (
                                             <div className="px-2 py-1 text-gray-500 text-sm">
                                               Searching...
                                             </div>
                                           ) : (
                                             <>
                                               {uomSearchResults.length > 0 ? (
                                                 uomSearchResults.map((uomItem) => (
                                                   <div
                                                     key={uomItem.id}
                                                     className="px-2 py-1 cursor-pointer hover:bg-blue-50 hover:text-blue-900 text-sm"
                                                     onMouseDown={(e) => {
                                                       e.preventDefault();
                                                       onCurrentBidItemChange(
                                                         item.item_required || '',
                                                         'unit_of_measurement',
                                                         { target: { name: 'unit_of_measurement', value: uomItem.name || '' } },
                                                         currentBid.bid_count?.toString() || ''
                                                       );
                                                       setUomSearchTerm(uomItem?.name || '');
                                                       setShowUomDropdown(false);
                                                     }}
                                                   >
                                                     {uomItem.name} ({uomItem.unit})
                                                   </div>
                                                 ))
                                               ) : (
                                                 <div className="px-2 py-1 text-gray-500 text-sm">
                                                   {uomSearchTerm.length >= 2 ? 'No UOM found' : 'Type to search UOM...'}
                                                 </div>
                                               )}
                                             </>
                                           )}
                                         </div>
                                       )}
                                     </div>
                                   </td>
                                   <td className="px-4 py-2 text-sm">
                                     <input
                                       type="number"
                                       className={`w-full p-1 text-sm border rounded ${
                                         isFieldInvalid(`item_${index}_quantity`) 
                                           ? "border-red-300 focus:ring-red-500 focus:border-red-500" 
                                           : "border-gray-300"
                                       }`}
                                       value={item.quantity || ''}
                                       onChange={(e) => onCurrentBidItemChange(
                                         item.item_required || '',
                                         'quantity',
                                         e,
                                         currentBid.bid_count?.toString() || ''
                                       )}
                                       name="quantity"
                                     />
                                   </td>
                                   <td className="px-4 py-2 text-sm">
                                     <input
                                       type="number"
                                       step="0.01"
                                       className={`w-full p-1 text-sm border rounded ${
                                         isFieldInvalid(`item_${index}_unit_price`) 
                                           ? "border-red-300 focus:ring-red-500 focus:border-red-500" 
                                           : "border-gray-300"
                                       }`}
                                       value={item.unit_price || ''}
                                       onChange={(e) => onCurrentBidItemChange(
                                         item.item_required || '',
                                         'unit_price',
                                         e,
                                         currentBid.bid_count?.toString() || ''
                                       )}
                                       name="unit_price"
                                     />
                                   </td>
                                   <td className="px-4 py-2 text-sm">
                                                                            <select
                                         className={`w-full p-1 text-sm border rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                                           isFieldInvalid(`item_${index}_vat`) 
                                             ? "border-red-300 focus:ring-red-500 focus:border-red-500" 
                                             : "border-gray-300"
                                         }`}
                                         value={item.vat || ''}
                                         onChange={(e) => onCurrentBidItemChange(
                                           item.item_required || '',
                                           'vat',
                                           e,
                                           currentBid.bid_count?.toString() || ''
                                         )}
                                         name="vat"
                                       >
                                       <option value="">Select VAT</option>
                                       <option value="Incl.">VAT Included</option>
                                       <option value="Excl.">VAT Excluded</option>
                                     </select>
                                   </td>
                                   <td className="px-4 py-2 text-sm">
                                     <input
                                       type="number"
                                       step="0.01"
                                       className="w-full p-1 text-sm border border-gray-300 rounded bg-gray-50"
                                       value={item.total_price || ''}
                                       readOnly
                                       name="total_price"
                                       title="Auto-calculated: Quantity × Unit Price"
                                     />
                                   </td>
                                 </tr>
                               ))}
                             </tbody>
                           </table>
                         </div>
                         <div className="mt-2 text-right">
                           <span className="text-sm font-medium text-gray-700">
                             Grand Total: ${calculateBidTotal(currentBid?.items || []).toLocaleString()}
                           </span>
                         </div>
                       </div>
                     </div>
                   </div>
                 </div>
               </div>
               <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                 <button
                   type="button"
                   onClick={onCurrentBidSave}
                   className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:ml-3 sm:w-auto sm:text-sm"
                 >
                   Save Bid
                 </button>
                 <button
                   type="button"
                   onClick={() => {
                     if (addBidModal) {
                       onCloseCurrentBid();
                     } else {
                       onCloseUpdateBidBid();
                     }
                   }}
                   className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                 >
                   Cancel
                 </button>
               </div>
             </div>
           </div>
         </div>
       )}

       {/* Add Supplier Modal */}
       {onAddSupplier && (
         <div className="fixed inset-0 z-50 overflow-y-auto">
           <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
             <div className="fixed inset-0 transition-opacity" aria-hidden="true">
               <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
             </div>
             <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
             <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
               <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                 <div className="sm:flex sm:items-start">
                   <div className="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-green-100 sm:mx-0 sm:h-10 sm:w-10">
                     <svg className="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                       <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                     </svg>
                   </div>
                   <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left w-full">
                     <h3 className="text-lg leading-6 font-medium text-gray-900">
                       Add New Supplier
                     </h3>
                     <div className="mt-4 space-y-4">
                       {/* Search Existing Suppliers */}
                       <div>
                         <label className="block text-sm font-medium text-gray-700 mb-2">Search Existing Suppliers</label>
                         <div className="relative">
                           <input
                             type="text"
                             className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500 pr-8"
                             placeholder="Search for existing suppliers..."
                             value={supplierSearchTerm}
                             onChange={(e) => {
                               setSupplierSearchTerm(e.target.value);
                               setShowSupplierDropdown(true);
                             }}
                             onFocus={() => setShowSupplierDropdown(true)}
                             onBlur={() => {
                               setTimeout(() => setShowSupplierDropdown(false), 200);
                             }}
                           />
                           <div className="absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none">
                             <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                               <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                             </svg>
                           </div>
                           
                           {/* Search Results Dropdown */}
                           {showSupplierDropdown && supplierSearchTerm && (
                             <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto">
                               {isSupplierSearching ? (
                                 <div className="px-3 py-2 text-gray-500 text-sm">
                                   Searching...
                                 </div>
                               ) : (
                                 <>
                                   {supplierSearchResults.length > 0 ? (
                                     supplierSearchResults.map((supplier) => (
                                                                          <div
                                         key={supplier.id}
                                         className="px-3 py-2 cursor-pointer hover:bg-blue-50 hover:text-blue-900"
                                         onMouseDown={(e) => {
                                           e.preventDefault();
                                           const supplierName = supplier.supplier_name || supplier.name || '';
                                           setSupplierSearchTerm(supplierName);
                                           setNewSupplier({
                                             ...newSupplier,
                                             supplier_name: supplierName,
                                             id: supplier.id
                                           });
                                           setShowSupplierDropdown(false);
                                           onOpenResponse("Supplier Found", `Supplier "${supplierName}" already exists in the system.`, true);
                                         }}
                                       >
                                         <div className="font-medium text-gray-900">
                                           {supplier.supplier_name || supplier.name}
                                         </div>
                                         {supplier.id && (
                                           <div className="text-xs text-gray-500">ID: {supplier.id}</div>
                                         )}
                                       </div>
                                     ))
                                   ) : (
                                     <div className="px-3 py-2 text-gray-500 text-sm">
                                       {supplierSearchTerm.length >= 2 ? 'No existing suppliers found. You can add a new one below.' : 'Type to search suppliers...'}
                                     </div>
                                   )}
                                 </>
                               )}
                             </div>
                           )}
                         </div>
                       </div>

                       {/* Divider */}
                       <div className="relative">
                         <div className="absolute inset-0 flex items-center">
                           <div className="w-full border-t border-gray-300" />
                         </div>
                         <div className="relative flex justify-center text-sm">
                           <span className="px-2 bg-white text-gray-500">OR</span>
                         </div>
                       </div>

                       {/* Add New Supplier */}
                       <div>
                         <label className="block text-sm font-medium text-gray-700 mb-2">Add New Supplier</label>
                         <input
                           type="text"
                           className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                           placeholder="Enter new supplier name"
                           value={newSupplier.supplier_name || ''}
                           onChange={(e) => onSupplierChange({ target: { name: 'supplier_name', value: e.target.value } })}
                           name="supplier_name"
                         />
                       </div>

                       {/* Optional Supplier Details Toggle */}
                       <div className="flex items-center">
                         <button
                           type="button"
                           onClick={() => setShowSupplierDetails(!showSupplierDetails)}
                           className="text-sm text-blue-600 hover:text-blue-800 flex items-center"
                         >
                           <svg className={`w-4 h-4 mr-1 transition-transform ${showSupplierDetails ? 'rotate-90' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                             <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
                           </svg>
                           {showSupplierDetails ? 'Hide' : 'Add'} Optional Details
                         </button>
                       </div>

                       {/* Optional Supplier Details */}
                       {showSupplierDetails && (
                         <div className="space-y-4 pl-4 border-l-2 border-gray-200">
                           <div>
                             <label className="block text-sm font-medium text-gray-700 mb-2">Contact Person</label>
                             <input
                               type="text"
                               className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                               placeholder="Enter contact person name"
                               value={newSupplier.contact_person || ''}
                               onChange={(e) => onSupplierChange({ target: { name: 'contact_person', value: e.target.value } })}
                               name="contact_person"
                             />
                           </div>
                           <div>
                             <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
                             <input
                               type="email"
                               className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                               placeholder="Enter email address"
                               value={newSupplier.email || ''}
                               onChange={(e) => onSupplierChange({ target: { name: 'email', value: e.target.value } })}
                               name="email"
                             />
                           </div>
                           <div>
                             <label className="block text-sm font-medium text-gray-700 mb-2">Phone Number</label>
                             <input
                               type="tel"
                               className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                               placeholder="Enter phone number"
                               value={newSupplier.phone_number || ''}
                               onChange={(e) => onSupplierChange({ target: { name: 'phone_number', value: e.target.value } })}
                               name="phone_number"
                             />
                           </div>
                           <div>
                             <label className="block text-sm font-medium text-gray-700 mb-2">Address</label>
                             <textarea
                               className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                               placeholder="Enter business address"
                               rows={3}
                               value={newSupplier.address || ''}
                               onChange={(e) => onSupplierChange({ target: { name: 'address', value: e.target.value } })}
                               name="address"
                             />
                           </div>
                           <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                             <div>
                               <label className="block text-sm font-medium text-gray-700 mb-2">Tax Number</label>
                               <input
                                 type="text"
                                 className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                 placeholder="Enter tax number"
                                 value={newSupplier.tax_number || ''}
                                 onChange={(e) => onSupplierChange({ target: { name: 'tax_number', value: e.target.value } })}
                                 name="tax_number"
                               />
                             </div>
                             <div>
                               <label className="block text-sm font-medium text-gray-700 mb-2">Registration Number</label>
                               <input
                                 type="text"
                                 className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                 placeholder="Enter registration number"
                                 value={newSupplier.registration_number || ''}
                                 onChange={(e) => onSupplierChange({ target: { name: 'registration_number', value: e.target.value } })}
                                 name="registration_number"
                               />
                             </div>
                           </div>
                           <div>
                             <label className="block text-sm font-medium text-gray-700 mb-2">Business Type</label>
                             <select
                               className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                               value={newSupplier.business_type || ''}
                               onChange={(e) => onSupplierChange({ target: { name: 'business_type', value: e.target.value } })}
                               name="business_type"
                             >
                               <option value="">Select business type</option>
                               <option value="Sole Proprietorship">Sole Proprietorship</option>
                               <option value="Partnership">Partnership</option>
                               <option value="Private Limited Company">Private Limited Company</option>
                               <option value="Public Limited Company">Public Limited Company</option>
                               <option value="Government Entity">Government Entity</option>
                               <option value="Non-Profit Organization">Non-Profit Organization</option>
                               <option value="Other">Other</option>
                             </select>
                           </div>
                         </div>
                       )}
                     </div>
                   </div>
                 </div>
               </div>
               <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                 <button
                   type="button"
                   onClick={async () => {
                     // Check if this is an existing supplier (has ID)
                     if (newSupplier.id) {
                       onOpenResponse("Supplier Exists", "This supplier already exists in the system. Please use the search function to find existing suppliers.", false);
                       return;
                     }

                     // Validate supplier data
                     if (!newSupplier.supplier_name?.trim()) {
                       onOpenResponse("Error", "Please enter a supplier name", false);
                       return;
                     }

                     // Check if supplier name already exists
                     const existingSupplier = suppliers.find(s => 
                       (s.supplier_name || s.name || '').toLowerCase() === (newSupplier.supplier_name || '').toLowerCase()
                     );
                     
                     if (existingSupplier) {
                       onOpenResponse("Supplier Exists", `Supplier "${newSupplier.supplier_name || ''}" already exists in the system.`, false);
                       return;
                     }

                     setIsLoading(true);
                     setLoadingOperation("Saving supplier");

                     try {
                       const formData = new FormData();
                       formData.append("supplier_name", newSupplier.supplier_name || '');
                       
                       // Add optional fields if provided
                       if (newSupplier.contact_person) {
                         formData.append("contact_person", newSupplier.contact_person);
                       }
                       if (newSupplier.email) {
                         formData.append("email", newSupplier.email);
                       }
                       if (newSupplier.phone_number) {
                         formData.append("phone_number", newSupplier.phone_number);
                       }
                       if (newSupplier.address) {
                         formData.append("address", newSupplier.address);
                       }
                       if (newSupplier.tax_number) {
                         formData.append("tax_number", newSupplier.tax_number);
                       }
                       if (newSupplier.registration_number) {
                         formData.append("registration_number", newSupplier.registration_number);
                       }
                       if (newSupplier.business_type) {
                         formData.append("business_type", newSupplier.business_type);
                       }
                       
                       formData.append("csrfmiddlewaretoken", csrfToken);

                       const requestOptions = {
                         method: "POST",
                         headers: {
                           "X-CSRFToken": csrfToken,
                         },
                         body: formData,
                       };

                       const data = await fetchWithRetry(
                         buildApiUrl(base_url, '/save_supplier'), 
                         requestOptions
                       );

                       if (data.success) {
                         // Add to suppliers list locally
                         const newSupplierData = {
                           id: data.supplier_id || Date.now(), // Fallback ID
                           supplier_name: newSupplier.supplier_name,
                           name: newSupplier.supplier_name,
                           contact_person: newSupplier.contact_person,
                           email: newSupplier.email,
                           phone_number: newSupplier.phone_number,
                           address: newSupplier.address,
                           tax_number: newSupplier.tax_number,
                           registration_number: newSupplier.registration_number,
                           business_type: newSupplier.business_type
                         };
                         setSuppliers(prev => [...prev, newSupplierData]);
                         
                         setOnAddSupplier(false);
                         setNewSupplier({});
                         setSupplierSearchTerm("");
                         setShowSupplierDetails(false);
                         onOpenResponse("Success", "Supplier added successfully", true);
                       } else {
                         onOpenResponse("Error", data.message || "Failed to save supplier", false);
                       }
                     } catch (error) {
                       console.error("Error saving supplier:", error);
                       onOpenResponse("Error", "Failed to save supplier. Please try again.", false);
                     } finally {
                       setIsLoading(false);
                       setLoadingOperation("");
                     }
                   }}
                   className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-green-600 text-base font-medium text-white hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 sm:ml-3 sm:w-auto sm:text-sm"
                 >
                   Add Supplier
                 </button>
                 <button
                   type="button"
                   onClick={() => {
                     setOnAddSupplier(false);
                     setNewSupplier({});
                     setSupplierSearchTerm("");
                     setShowSupplierDetails(false);
                   }}
                   className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                 >
                   Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </ScheduleProvider>
  );
}
