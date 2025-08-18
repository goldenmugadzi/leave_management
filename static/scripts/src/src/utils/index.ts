/**
 * Utility functions index
 * Central export point for all utility functions
 */

// Authentication utilities
export { getCookie, getCsrfToken } from './auth';

// Date utilities
export { formatDisplayDate, formatDateForBackend, isValidDateFormat } from './dateUtils';

// API utilities
export { 
  fetchWithRetry, 
  createDefaultRequestOptions, 
  createPostRequestOptions, 
  createFormDataRequestOptions 
} from './apiUtils';

// File utilities
export { 
  getDownloadFilename, 
  validateFile, 
  getFileExtension, 
  isAllowedFileExtension 
} from './fileUtils';
