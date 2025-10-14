// Export main services
export { default as ScheduleApiService } from './scheduleApiService';
export { default as ScheduleBusinessLogic } from './scheduleBusinessLogic';
export { default as ServiceFactory } from './serviceFactory';

// Export service factory instance
import ServiceFactory from './serviceFactory';
export const serviceFactory = ServiceFactory.getInstance();

// Export types and interfaces
export type { ApiResponse, FileUploadResponse } from './scheduleApiService';

// Export configuration
export { API_CONFIG } from './serviceFactory';

// Re-export commonly used services for convenience
export const getApiService = () => serviceFactory.getApiService();
export const getBusinessLogicService = () => serviceFactory.getBusinessLogicService();
