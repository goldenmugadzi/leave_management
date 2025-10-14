import { useMemo } from 'react';
import { serviceFactory } from '../services';

/**
 * Custom hook to access schedule services
 * This provides a clean interface for components to use our services
 */
export const useScheduleServices = () => {
  const services = useMemo(() => {
    const apiService = serviceFactory.getApiService();
    const businessLogicService = serviceFactory.getBusinessLogicService();
    
    return {
      api: apiService,
      businessLogic: businessLogicService,
      
      // Convenience methods for common operations
      initializeSchedule: businessLogicService.initializeSchedule.bind(businessLogicService),
      validateScheduleFields: businessLogicService.validateScheduleFields.bind(businessLogicService),
      validateBidForm: businessLogicService.validateBidForm.bind(businessLogicService),
      validateFile: businessLogicService.validateFile.bind(businessLogicService),
      
      // Direct API access for complex operations
      fetchCS: apiService.fetchCS.bind(apiService),
      saveSchedule: apiService.saveSchedule.bind(apiService),
      updateSchedule: apiService.updateSchedule.bind(apiService),
      saveBid: apiService.saveBid.bind(apiService),
      deleteBid: apiService.deleteBid.bind(apiService),
      saveCommittee: apiService.saveCommittee.bind(apiService),
      saveCompliance: apiService.saveCompliance.bind(apiService),
      uploadFile: apiService.uploadFile.bind(apiService),
      
      // Utility methods
      getCsrfToken: apiService.getCsrfToken.bind(apiService),
      refreshCsrfToken: apiService.refreshCsrfToken.bind(apiService),
      healthCheck: apiService.healthCheck.bind(apiService),
    };
  }, []);

  return services;
};

/**
 * Hook for getting just the API service
 */
export const useScheduleApi = () => {
  return useMemo(() => serviceFactory.getApiService(), []);
};

/**
 * Hook for getting just the business logic service
 */
export const useScheduleBusinessLogic = () => {
  return useMemo(() => serviceFactory.getBusinessLogicService(), []);
};

/**
 * Hook for getting the service factory (useful for advanced usage)
 */
export const useServiceFactory = () => {
  return useMemo(() => serviceFactory, []);
};
