/**
 * API Endpoints Configuration
 * 
 * This file centralizes all API endpoints for easy management and configuration.
 * 
 * HOW TO USE:
 * 1. Change API_MODULES values to match your Django app names
 * 2. Use getCurrentModule() to automatically detect module from URL path
 * 3. Update individual endpoints in API_ENDPOINTS as needed
 * 
 * EXAMPLES:
 * - Auto-detection: getCurrentModule() returns the appropriate module based on URL
 * - Manual override: setCurrentModule(API_MODULES.DIRECT_PURCHASE)
 * - Get base URL: getBaseUrl(base_url, path) returns the full base URL
 * 
 * USAGE IN CODE:
 * import { API_ENDPOINTS, buildApiUrl, getCurrentModule } from '../config/apiEndpoints';
 * const module = getCurrentModule();
 * const url = buildApiUrl(base_url, API_ENDPOINTS.USERS);
 */

// API Endpoints Configuration
// Change these module names to match your Django URL patterns

export const API_MODULES = {
  // Change these module names based on your Django apps
  RESTRICTED_BIDDING: 'restricted_bidding',
  COMPARATIVE_SCHEDULES: 'comperative_schedule', 
  DIRECT_PURCHASE: 'direct_purchase'
} as const;

// Current module state (will be set dynamically)
let currentModule: string = API_MODULES.COMPARATIVE_SCHEDULES;

// Function to determine module from URL path
export const getCurrentModule = (): string => {
  if (typeof window !== 'undefined') {
    const path = window.location.pathname;
    
    switch (true) {
      case path.includes('/direct_purchase/'):
        return API_MODULES.DIRECT_PURCHASE;
      case path.includes('/restricted_bidding/'):
        return API_MODULES.RESTRICTED_BIDDING;
      case path.includes('/comperative_schedule/'):
        return API_MODULES.COMPARATIVE_SCHEDULES;
      default:
        return API_MODULES.COMPARATIVE_SCHEDULES; // fallback
    }
  }
  return currentModule;
};

// Function to set current module (for manual override)
export const setCurrentModule = (module: string): void => {
  currentModule = module;
};

// Function to get base URL (matching main.tsx logic)
export const getBaseUrl = (baseUrl: string, path?: string): string => {
  const currentPath = path || (typeof window !== 'undefined' ? window.location.pathname : '');
  
  // If baseUrl already contains the module path, don't add it again
  if (baseUrl.includes('/direct_purchase')) {
    return baseUrl;
  }
  if (baseUrl.includes('/restricted_bidding')) {
    return baseUrl;
  }
  if (baseUrl.includes('/comperative_schedule')) {
    return baseUrl;
  }
  
  // Otherwise, determine module and append it
  switch (true) {
    case currentPath.includes('/direct_purchase/'):
      return `${baseUrl}/${API_MODULES.DIRECT_PURCHASE}`;
    case currentPath.includes('/restricted_bidding/'):
      return `${baseUrl}/${API_MODULES.RESTRICTED_BIDDING}`;
    case currentPath.includes('/comperative_schedule/'):
      return `${baseUrl}/${API_MODULES.COMPARATIVE_SCHEDULES}`;
    default:
      return `${baseUrl}/${API_MODULES.COMPARATIVE_SCHEDULES}`; // fallback
  }
};

// API endpoints (without module prefix since base_url already includes it)
export const API_ENDPOINTS = {
    // User and Supplier APIs
    USERS: `/api/users/`,
    SUPPLIERS: `/api/suppliers/`,
    
    // Reference Data APIs
    CURRENCIES: `/api/currencies/`,
    PROC_PLANS: `/api/proc_plans/`,
    
    // Purchase Request APIs (legacy - for backward compatibility)
    PR_CREATE_DATA: (pr_id: string) => `/create_data/${pr_id}`,
    CS_CREATE_DATA: (pr_id: string) => `/create_data/${pr_id}/`,
    CS_DETAILS: (cs_id: string) => `/cs_data/${cs_id}/`,
    // CS_SAVE: () => `/save`,
    // New focused APIs
    PR_BASIC: (pr_id: string) => `/api/pr-basic/${pr_id}/`,
    PR_ITEMS: (pr_id: string) => `/api/pr-items/${pr_id}/`,
    PR_ATTACHMENTS: (pr_id: string) => `/api/pr-attachments/${pr_id}/`,
    REFERENCE_DATA: () => `/api/reference-data/`,
    
    // Schedule APIs
    CS_SAVE: `/save`,
    CS_UPDATE: () => `/update`,
    CS_UPDATE_ITEMS: () => `/update_pritem_ordered`,
    CS_BIDS_API: (cs_id: string) => `/api_cs_bids/${cs_id}`,
    CS_COMPLIANCE_API: (cs_id: string) => `/api_cs_compliance/${cs_id}`,
    CS_COMMITTEE_API: (cs_id: string) => `/api_cs_committee/${cs_id}`,
    
    // CS Items APIs
    CS_ITEMS: (cs_id: string) => `/cs/${cs_id}/items/`,
    
    // Bid Management APIs
    CS_BIDS: (cs_id: string) => `/cs/${cs_id}/bids/`,
    CS_BID_DELETE: (cs_id: string, bid_count: number) => `/cs/${cs_id}/bids/${bid_count}/`,
    
    // Committee APIs
    CS_COMMITTEE: (cs_id: string) => `/cs/${cs_id}/committee/`,
    CS_SAVE_COMMITTEE: `/save_committee`,
    
    // Compliance APIs
    CS_COMPLIANCE: (cs_id: string) => `/cs/${cs_id}/compliance/`,
    CS_CLOSE_COMPLIANCE: `/close_compliance`,
    
    // Notes APIs
    CS_ADDITIONAL_NOTES: `/save_additional_notes`,
    CS_BUYERS_NOTES: `/save_buyers_notes`,
    
    // Approval APIs
    CS_APPROVAL: (cs_id: string) => `/cs/${cs_id}/approval/`,
    
    // Tab-specific APIs (for optimized loading)
    CS_BIDS_DATA: (cs_id: string) => `/api/cs-bids/${cs_id}/`,
    CS_COMMITTEE_DATA: (cs_id: string) => `/api/cs-committee/${cs_id}/`,
    CS_COMPLIANCE_DATA: (cs_id: string) => `/api/cs-compliance/${cs_id}/`,
    CS_APPROVALS_DATA: (cs_id: string) => `/api/cs-approvals/${cs_id}/`,
    CS_PR_ITEMS_MANAGEMENT: (cs_id: string) => `/api/cs-pr-items-management/${cs_id}/`,
} as const;

// Dynamic API endpoints function (for backward compatibility)
export const getApiEndpoints = () => API_ENDPOINTS;

// Helper function to build full URL
export const buildApiUrl = (base_url: string, endpoint: string): string => {
  return `${base_url}${endpoint}`;
};

// Helper function to get endpoint for specific module
export const getModuleEndpoint = (module: keyof typeof API_MODULES, path: string): string => {
  return `/${API_MODULES[module]}${path}`;
};

// Configuration object for easy switching between modules
export const MODULE_CONFIG = {
  restrictedBidding: {
    users: `/${API_MODULES.RESTRICTED_BIDDING}/api/users/`,
    suppliers: `/${API_MODULES.RESTRICTED_BIDDING}/api/suppliers/`,
  },
  comparativeSchedules: {
    users: `/${API_MODULES.COMPARATIVE_SCHEDULES}/api/users/`,
    suppliers: `/${API_MODULES.COMPARATIVE_SCHEDULES}/api/suppliers/`,
  },
  directPurchase: {
    users: `/${API_MODULES.DIRECT_PURCHASE}/api/users/`,
    suppliers: `/${API_MODULES.DIRECT_PURCHASE}/api/suppliers/`,
  }
} as const;

// Default export for convenience
export default {
  API_MODULES,
  API_ENDPOINTS,
  getApiEndpoints,
  getCurrentModule,
  setCurrentModule,
  getBaseUrl,
  buildApiUrl,
  getModuleEndpoint,
  MODULE_CONFIG
}; 