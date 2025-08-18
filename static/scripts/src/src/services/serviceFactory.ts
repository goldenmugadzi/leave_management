import ScheduleApiService from './scheduleApiService';
import ScheduleBusinessLogic from './scheduleBusinessLogic';

// Configuration for services
const API_CONFIG = {
  baseUrl: typeof window !== 'undefined' ? window.location.origin : 'http://localhost:3000',
  timeout: 30000, // 30 seconds
  retryAttempts: 3,
  retryDelay: 1000, // 1 second
};

class ServiceFactory {
  private static instance: ServiceFactory;
  private apiService: ScheduleApiService | null = null;
  private businessLogicService: ScheduleBusinessLogic | null = null;

  private constructor() {}

  static getInstance(): ServiceFactory {
    if (!ServiceFactory.instance) {
      ServiceFactory.instance = new ServiceFactory();
    }
    return ServiceFactory.instance;
  }

  /**
   * Get or create API service instance
   */
  getApiService(): ScheduleApiService {
    if (!this.apiService) {
      this.apiService = new ScheduleApiService(API_CONFIG.baseUrl);
    }
    return this.apiService;
  }

  /**
   * Get or create business logic service instance
   */
  getBusinessLogicService(): ScheduleBusinessLogic {
    if (!this.businessLogicService) {
      this.businessLogicService = new ScheduleBusinessLogic(API_CONFIG.baseUrl);
    }
    return this.businessLogicService;
  }

  /**
   * Reset all services (useful for testing or when user logs out)
   */
  resetServices(): void {
    this.apiService = null;
    this.businessLogicService = null;
  }

  /**
   * Get API configuration
   */
  getApiConfig() {
    return { ...API_CONFIG };
  }

  /**
   * Update API configuration
   */
  updateApiConfig(newConfig: Partial<typeof API_CONFIG>): void {
    Object.assign(API_CONFIG, newConfig);
    
    // Reset services to use new configuration
    this.resetServices();
  }
}

export default ServiceFactory;
export { API_CONFIG };
