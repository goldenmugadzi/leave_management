import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { 
  IBid, 
  ICompliance, 
  IComplianceRemark, 
  ISupplier,
  ICommittee,
  IUser,
  ICurrency,
  IProcPlan,
  IRank,
  IGmApproval,
  IFmApproval,
  ICurrentApprover,
  IUom
} from '../types/scheduleTypes';

// Core Schedule State Interface
export interface ScheduleState {
  // === BASIC SCHEDULE DATA ===
  csId: string;
  storedPrId: string;
  creator: string;
  createdAt: string;
  csOwner: string;
  procRef: string;
  username: string;
  
  // === REFERENCE DATA ===
  suppliers: ISupplier[];
  users: IUser[];
  currencies: ICurrency[];
  procPlans: IProcPlan[];
  currency: ICurrency | undefined;
  procPlan: IProcPlan | undefined;
  
  // === PR DATA ===
  prData: {
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
  };
  
  // === BID MANAGEMENT ===
  bidCount: number;
  currentBid: IBid | undefined;
  bids: IBid[];
  addBidModal: boolean;
  updateBidModal: boolean;
  
  // === COMPLIANCE MANAGEMENT ===
  compliance: ICompliance[];
  complianceRemarks: IComplianceRemark[];
  showSamples: string;
  showSiteVisit: string;
  
  // === RANKINGS & EVALUATION ===
  rankings: IRank[];
  
  // === COMMITTEE MANAGEMENT ===
  committeeMembers: ICommittee[];
  
  // === APPROVAL WORKFLOW ===
  gmApproval: IGmApproval | undefined;
  fmApproval: IFmApproval | undefined;
  approvalsComplete: boolean;
  approvalsJustificationModal: boolean;
  currentApprover: ICurrentApprover | undefined;
  currentUserRoles: {
    fm_role: boolean;
    gm_role: boolean;
    procurement_role: boolean;
  };
  
  // === ADDITIONAL FEATURES ===
  additionalNotes: string;
  buyersNotes: string;
  directPurchaseLimit: boolean;
  onAddSupplier: boolean;
  newSupplier: ISupplier;
  showSupplierDetails: boolean;
  supplierSearchTerm: string;
  showSupplierDropdown: boolean;
  uomSearchTerm: string;
  showUomDropdown: boolean;
  activeUomItem: string;
  expandedBids: Set<number>;
  
  // === VALIDATION STATE ===
  bidValidationErrors: string[];
  invalidFields: Set<string>;
  
  // === SEARCH STATE ===
  uomSearchResults: IUom[];
  isUomSearching: boolean;
  supplierSearchResults: ISupplier[];
  isSupplierSearching: boolean;
  debouncedUomSearchTerm: string;
  debouncedSupplierSearchTerm: string;
  
  // === LOADING STATES ===
  isLoading: boolean;
  loadingOperation: string;
  activeTab: string;
  loadedTabs: Set<string>;
  
  // === FILE MANAGEMENT ===
  advert: File | undefined;
  advertMetadata: {
    name: string;
    size: number;
    download_url: string;
    preview_url: string;
    mime_type: string;
    file_path?: string;
    is_base64?: boolean;
  } | null;
  
  // === RESPONSE NOTIFICATIONS ===
  response: {
    open: boolean;
    message: string;
    title: string;
    success: boolean;
  };
  
  // === PR INPUT STATE ===
  prIdInput: string;
  quantity: string;
}

// Actions Interface
export interface ScheduleActions {
  // === BASIC SETTERS ===
  setCsId: (id: string) => void;
  setStoredPrId: (id: string) => void;
  setCreator: (creator: string) => void;
  setCreatedAt: (date: string) => void;
  setCsOwner: (owner: string) => void;
  setProcRef: (ref: string) => void;
  setUsername: (username: string) => void;
  
  // === REFERENCE DATA ACTIONS ===
  setSuppliers: (suppliers: ISupplier[]) => void;
  setUsers: (users: IUser[]) => void;
  setCurrencies: (currencies: ICurrency[]) => void;
  setProcPlans: (plans: IProcPlan[]) => void;
  setCurrency: (currency: ICurrency | undefined) => void;
  setProcPlan: (plan: IProcPlan | undefined) => void;
  
  // === FILE MANAGEMENT ACTIONS ===
  setAdvert: (file: File | undefined) => void;
  setAdvertMetadata: (metadata: ScheduleState['advertMetadata']) => void;
  
  // === PR DATA ACTIONS ===
  setPrData: (data: Partial<ScheduleState['prData']> | ((prev: ScheduleState['prData']) => Partial<ScheduleState['prData']>)) => void;
  updatePrData: (field: string, value: string | boolean) => void;
  updateItemSelection: (itemId: string, included: boolean) => void;
  handleSelectAllItems: (selectAll: boolean) => void;
  
  // === BID MANAGEMENT ACTIONS ===
  setBidCount: (count: number) => void;
  setCurrentBid: (bid: IBid | undefined) => void;
  setBids: (bids: IBid[]) => void;
  addBid: (bid: IBid) => void;
  updateBid: (bidId: number, updates: Partial<IBid>) => void;
  deleteBid: (bidId: number) => void;
  setAddBidModal: (open: boolean) => void;
  setUpdateBidModal: (open: boolean) => void;
  
  // === COMPLIANCE ACTIONS ===
  setCompliance: (compliance: ICompliance[]) => void;
  setComplianceRemarks: (remarks: IComplianceRemark[]) => void;
  setShowSamples: (show: string) => void;
  setShowSiteVisit: (show: string) => void;
  
  // === RANKINGS ACTIONS ===
  setRankings: (rankings: IRank[]) => void;
  
  // === COMMITTEE ACTIONS ===
  setCommitteeMembers: (members: ICommittee[]) => void;
  updateCommitteeMembers: (members: ICommittee[]) => void;
  
  // === APPROVAL ACTIONS ===
  setGmApproval: (approval: IGmApproval | undefined) => void;
  setFmApproval: (approval: IFmApproval | undefined) => void;
  setApprovalsComplete: (complete: boolean) => void;
  setApprovalsJustificationModal: (open: boolean) => void;
  setCurrentApprover: (approver: ICurrentApprover | undefined | ((prev: ICurrentApprover | undefined) => ICurrentApprover | undefined)) => void;
  setCurrentUserRoles: (roles: ScheduleState['currentUserRoles']) => void;
  
  // === UTILITY ACTIONS ===
  setIsLoading: (loading: boolean) => void;
  setLoadingOperation: (operation: string) => void;
  setActiveTab: (tab: string) => void;
  setLoadedTabs: (tabs: Set<string>) => void;
  setResponse: (response: ScheduleState['response']) => void;
  
  // === ADDITIONAL FEATURES ACTIONS ===
  setAdditionalNotes: (notes: string) => void;
  setBuyersNotes: (notes: string) => void;
  setDirectPurchaseLimit: (limit: boolean) => void;
  setOnAddSupplier: (open: boolean) => void;
  setNewSupplier: (supplier: ISupplier) => void;
  setShowSupplierDetails: (show: boolean) => void;
  setSupplierSearchTerm: (term: string) => void;
  setShowSupplierDropdown: (show: boolean) => void;
  setUomSearchTerm: (term: string) => void;
  setShowUomDropdown: (show: boolean) => void;
  setActiveUomItem: (item: string) => void;
  setExpandedBids: (expanded: Set<number>) => void;
  
  // === VALIDATION ACTIONS ===
  setBidValidationErrors: (errors: string[]) => void;
  setInvalidFields: (fields: Set<string>) => void;
  
  // === SEARCH ACTIONS ===
  setUomSearchResults: (results: IUom[]) => void;
  setIsUomSearching: (searching: boolean) => void;
  setSupplierSearchResults: (results: ISupplier[]) => void;
  setIsSupplierSearching: (searching: boolean) => void;
  setDebouncedUomSearchTerm: (term: string) => void;
  setDebouncedSupplierSearchTerm: (term: string) => void;
  
  // === PR INPUT ACTIONS ===
  setPrIdInput: (input: string) => void;
  setQuantity: (qty: string) => void;
  
  // === COMPUTED ACTIONS ===
  isCreator: () => boolean;
  checkApprovalsComplete: () => boolean;
  allItemsSelected: () => boolean;
  
  // === RESET ACTIONS ===
  resetSchedule: () => void;
  resetBids: () => void;
  resetCompliance: () => void;
  
  // === BATCH ACTIONS ===
  initializeSchedule: (data: Partial<ScheduleState>) => void;
  updateScheduleData: (updates: Partial<ScheduleState>) => void;
}

// Combined Store Type
export type ScheduleStore = ScheduleState & ScheduleActions;

// Initial State
const initialState: ScheduleState = {
  // === BASIC SCHEDULE DATA ===
  csId: '',
  storedPrId: '',
  creator: '',
  createdAt: '',
  csOwner: '',
  procRef: '',
  username: '',
  
  // === REFERENCE DATA ===
  suppliers: [],
  users: [],
  currencies: [],
  procPlans: [],
  currency: undefined,
  procPlan: undefined,
  
  // === PR DATA ===
  prData: {
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
  },
  
  // === BID MANAGEMENT ===
  bidCount: 0,
  currentBid: undefined,
  bids: [],
  addBidModal: false,
  updateBidModal: false,
  
  // === COMPLIANCE MANAGEMENT ===
  compliance: [],
  complianceRemarks: [],
  showSamples: 'no',
  showSiteVisit: 'no',
  
  // === RANKINGS & EVALUATION ===
  rankings: [],
  
  // === COMMITTEE MANAGEMENT ===
  committeeMembers: [],
  
  // === APPROVAL WORKFLOW ===
  gmApproval: undefined,
  fmApproval: undefined,
  approvalsComplete: false,
  approvalsJustificationModal: false,
  currentApprover: undefined,
  currentUserRoles: {
    fm_role: false,
    gm_role: false,
    procurement_role: false
  },
  
  // === ADDITIONAL FEATURES ===
  additionalNotes: '',
  buyersNotes: '',
  directPurchaseLimit: true,
  onAddSupplier: false,
  newSupplier: {},
  showSupplierDetails: false,
  supplierSearchTerm: '',
  showSupplierDropdown: false,
  uomSearchTerm: '',
  showUomDropdown: false,
  activeUomItem: '',
  expandedBids: new Set(),
  
  // === VALIDATION STATE ===
  bidValidationErrors: [],
  invalidFields: new Set(),
  
  // === SEARCH STATE ===
  uomSearchResults: [],
  isUomSearching: false,
  supplierSearchResults: [],
  isSupplierSearching: false,
  debouncedUomSearchTerm: '',
  debouncedSupplierSearchTerm: '',
  
  // === LOADING STATES ===
  isLoading: false,
  loadingOperation: '',
  activeTab: 'details',
  loadedTabs: new Set(['details']),
  
  // === FILE MANAGEMENT ===
  advert: undefined,
  advertMetadata: null,
  
  // === RESPONSE NOTIFICATIONS ===
  response: {
    open: false,
    message: '',
    title: '',
    success: false
  },
  
  // === PR INPUT STATE ===
  prIdInput: '',
  quantity: ''
};

// Create Store
export const useScheduleStore = create<ScheduleStore>()(
  devtools(
    persist(
      (set, get) => ({
        ...initialState,
        
        // === BASIC SETTERS ===
        setCsId: (id) => set({ csId: id }),
        setStoredPrId: (id) => set({ storedPrId: id }),
        setCreator: (creator) => set({ creator }),
        setCreatedAt: (date) => set({ createdAt: date }),
        setCsOwner: (owner) => set({ csOwner: owner }),
        setProcRef: (ref) => set({ procRef: ref }),
        setUsername: (username) => set({ username }),
        
        // === REFERENCE DATA ACTIONS ===
        setSuppliers: (suppliers) => set({ suppliers }),
        setUsers: (users) => set({ users }),
        setCurrencies: (currencies) => set({ currencies }),
        setProcPlans: (plans) => set({ procPlans: plans }),
        setCurrency: (currency) => set({ currency }),
        setProcPlan: (plan) => set({ procPlan: plan }),
        
        // === FILE MANAGEMENT ACTIONS ===
        setAdvert: (file) => set({ advert: file }),
        setAdvertMetadata: (metadata) => set({ advertMetadata: metadata }),
        
        // === PR DATA ACTIONS ===
        setPrData: (data) => set((state) => ({
          ...state,
          prData: typeof data === 'function' 
            ? { ...state.prData, ...data(state.prData) }
            : { ...state.prData, ...data }
        })),
        
        updatePrData: (field, value) => set((state) => ({
          prData: { ...state.prData, [field]: value }
        })),
        
        updateItemSelection: (itemId, included) => set((state) => ({
          prData: {
            ...state.prData,
            items: state.prData.items.map(item => 
              item.id === itemId ? { ...item, included } : item
            )
          }
        })),
        
        handleSelectAllItems: (selectAll) => set((state) => ({
          prData: {
            ...state.prData,
            items: state.prData.items.map(item => ({
              ...item,
              included: item.status === 'used_in_other_schedule' ? item.included : selectAll
            }))
          }
        })),
        
        // === BID MANAGEMENT ACTIONS ===
        setBidCount: (count) => set({ bidCount: count }),
        setCurrentBid: (bid) => set({ currentBid: bid }),
        setBids: (bids) => set({ bids }),
        
        addBid: (bid) => set((state) => ({
          bids: [...state.bids, bid],
          bidCount: state.bidCount + 1
        })),
        
        updateBid: (bidId, updates) => set((state) => ({
          bids: state.bids.map(bid => 
            bid.bid_count === bidId ? { ...bid, ...updates } : bid
          )
        })),
        
        deleteBid: (bidId) => set((state) => ({
          bids: state.bids.filter(bid => bid.bid_count !== bidId),
          bidCount: Math.max(0, state.bidCount - 1)
        })),
        
        setAddBidModal: (open) => set({ addBidModal: open }),
        setUpdateBidModal: (open) => set({ updateBidModal: open }),
        
        // === COMPLIANCE ACTIONS ===
        setCompliance: (compliance) => set({ compliance }),
        setComplianceRemarks: (remarks) => set({ complianceRemarks: remarks }),
        setShowSamples: (show) => set({ showSamples: show }),
        setShowSiteVisit: (show) => set({ showSiteVisit: show }),
        
        // === RANKINGS ACTIONS ===
        setRankings: (rankings) => set({ rankings }),
        
        // === COMMITTEE ACTIONS ===
        setCommitteeMembers: (members) => set({ committeeMembers: members }),
        
        updateCommitteeMembers: (members) => set({ committeeMembers: members }),
        
        // === APPROVAL ACTIONS ===
        setGmApproval: (approval) => set({ gmApproval: approval }),
        setFmApproval: (approval) => set({ fmApproval: approval }),
        setApprovalsComplete: (complete) => set({ approvalsComplete: complete }),
        setApprovalsJustificationModal: (open) => set({ approvalsJustificationModal: open }),
        setCurrentApprover: (approver) => set((state) => ({
          currentApprover: typeof approver === 'function' 
            ? approver(state.currentApprover) 
            : approver
        })),
        setCurrentUserRoles: (roles) => set({ currentUserRoles: roles }),
        
        // === UTILITY ACTIONS ===
        setIsLoading: (loading) => set({ isLoading: loading }),
        setLoadingOperation: (operation) => set({ loadingOperation: operation }),
        setActiveTab: (tab) => set({ activeTab: tab }),
        setLoadedTabs: (tabs) => set({ loadedTabs: tabs }),
        setResponse: (response) => set({ response }),
        
        // === ADDITIONAL FEATURES ACTIONS ===
        setAdditionalNotes: (notes) => set({ additionalNotes: notes }),
        setBuyersNotes: (notes) => set({ buyersNotes: notes }),
        setDirectPurchaseLimit: (limit) => set({ directPurchaseLimit: limit }),
        setOnAddSupplier: (open) => set({ onAddSupplier: open }),
        setNewSupplier: (supplier) => set({ newSupplier: supplier }),
        setShowSupplierDetails: (show) => set({ showSupplierDetails: show }),
        setSupplierSearchTerm: (term) => set({ supplierSearchTerm: term }),
        setShowSupplierDropdown: (show) => set({ showSupplierDropdown: show }),
        setUomSearchTerm: (term) => set({ uomSearchTerm: term }),
        setShowUomDropdown: (show) => set({ showUomDropdown: show }),
        setActiveUomItem: (item) => set({ activeUomItem: item }),
        setExpandedBids: (expanded) => set({ expandedBids: expanded }),
        
        // === VALIDATION ACTIONS ===
        setBidValidationErrors: (errors) => set({ bidValidationErrors: errors }),
        setInvalidFields: (fields) => set({ invalidFields: fields }),
        
        // === SEARCH ACTIONS ===
        setUomSearchResults: (results) => set({ uomSearchResults: results }),
        setIsUomSearching: (searching) => set({ isUomSearching: searching }),
        setSupplierSearchResults: (results) => set({ supplierSearchResults: results }),
        setIsSupplierSearching: (searching) => set({ isSupplierSearching: searching }),
        setDebouncedUomSearchTerm: (term) => set({ debouncedUomSearchTerm: term }),
        setDebouncedSupplierSearchTerm: (term) => set({ debouncedSupplierSearchTerm: term }),
        
        // === PR INPUT ACTIONS ===
        setPrIdInput: (input) => set({ prIdInput: input }),
        setQuantity: (qty) => set({ quantity: qty }),
        
        // === COMPUTED ACTIONS ===
        isCreator: () => {
          const state = get();
          if (!state.csId || state.csId === "") return true;
          if (!state.csOwner || state.csOwner === "") return true;
          return state.username === state.csOwner;
        },
        
        checkApprovalsComplete: () => {
          const state = get();
          const committeeApproved = state.committeeMembers.length === 0 || 
            state.committeeMembers.every(m => m.memberApproval === "Approved");
          const gmApproved = !!state.gmApproval && state.gmApproval.approval === "Approved";
          const fmApproved = !!state.fmApproval && state.fmApproval.approval === "Approved";
          
          const allComplete = committeeApproved && gmApproved && fmApproved;
          set({ approvalsComplete: allComplete });
          return allComplete;
        },
        
        allItemsSelected: () => {
          const state = get();
          const availableItems = state.prData.items.filter(item => item.status !== 'used_in_other_schedule');
          return availableItems.length > 0 && availableItems.every(item => item.included);
        },
        
        // === RESET ACTIONS ===
        resetSchedule: () => set(initialState),
        resetBids: () => set({ bids: [], bidCount: 0, currentBid: undefined }),
        resetCompliance: () => set({ compliance: [], complianceRemarks: [] }),
        
        // === BATCH ACTIONS ===
        initializeSchedule: (data) => set((state) => ({ ...state, ...data })),
        
        updateScheduleData: (updates) => set((state) => ({ ...state, ...updates }))
      }),
      {
        name: 'schedule-store',
        partialize: (state) => ({
          // Only persist non-sensitive data
          csId: state.csId,
          storedPrId: state.storedPrId,
          creator: state.creator,
          createdAt: state.createdAt,
          csOwner: state.csOwner,
          procRef: state.procRef,
          username: state.username,
          // Don't persist sensitive data like bids, compliance, etc.
        })
      }
    ),
    {
      name: 'schedule-store'
    }
  )
);

// Selector hooks for better performance
export const useScheduleSelector = <T>(selector: (state: ScheduleState) => T) => 
  useScheduleStore(selector);

// Common selectors
export const useScheduleBasicInfo = () => useScheduleSelector(state => ({
  csId: state.csId,
  creator: state.creator,
  createdAt: state.createdAt,
  csOwner: state.csOwner,
  username: state.username
}));

export const useSchedulePermissions = () => {
  const currentUserRoles = useScheduleSelector(state => state.currentUserRoles);
  const { isCreator } = useScheduleStore();
  return { isCreator, currentUserRoles };
};

export const useScheduleBids = () => useScheduleSelector(state => ({
  bids: state.bids,
  bidCount: state.bidCount,
  currentBid: state.currentBid
}));

export const useScheduleCompliance = () => useScheduleSelector(state => ({
  compliance: state.compliance,
  complianceRemarks: state.complianceRemarks,
  showSamples: state.showSamples,
  showSiteVisit: state.showSiteVisit
}));

export const useScheduleCommittee = () => useScheduleSelector(state => ({
  committeeMembers: state.committeeMembers
}));

export const useScheduleApprovals = () => useScheduleSelector(state => ({
  gmApproval: state.gmApproval,
  fmApproval: state.fmApproval,
  approvalsComplete: state.approvalsComplete,
  currentApprover: state.currentApprover,
  currentUserRoles: state.currentUserRoles
}));

export const useScheduleLoading = () => useScheduleSelector(state => ({
  isLoading: state.isLoading,
  loadingOperation: state.loadingOperation
}));

export const useScheduleResponse = () => useScheduleSelector(state => ({
  response: state.response
}));
