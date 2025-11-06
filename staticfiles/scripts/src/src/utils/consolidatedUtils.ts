/**
 * Consolidated Utility Functions
 * Combines all common helper functions that were previously scattered across components
 */

import { FileValidationService } from '../services/FileValidationService';
import { NotificationResponseService } from '../services/NotificationResponseService';

// === DATE AND TIME UTILITIES ===

export interface IDateFormatOptions {
  format?: 'short' | 'long' | 'relative' | 'iso' | 'custom';
  customFormat?: string;
  timezone?: string;
  locale?: string;
}

/**
 * Format date with various options
 */
export const formatDate = (date: Date | string | number, options: IDateFormatOptions = {}): string => {
  const dateObj = typeof date === 'string' || typeof date === 'number' ? new Date(date) : date;
  
  if (isNaN(dateObj.getTime())) {
    return 'Invalid Date';
  }

  const { format = 'short', customFormat, locale } = options;

  switch (format) {
    case 'short':
      return dateObj.toLocaleDateString(locale || 'en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    
    case 'long':
      return dateObj.toLocaleDateString(locale || 'en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        weekday: 'long'
      });
    
    case 'relative':
      return getRelativeTimeString(dateObj);
    
    case 'iso':
      return dateObj.toISOString();
    
    case 'custom':
      if (customFormat) {
        return formatDateCustom(dateObj, customFormat);
      }
      return dateObj.toLocaleDateString();
    
    default:
      return dateObj.toLocaleDateString();
  }
};

/**
 * Get relative time string (e.g., "2 hours ago")
 */
export const getRelativeTimeString = (date: Date): string => {
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (diffInSeconds < 60) {
    return 'Just now';
  }

  const diffInMinutes = Math.floor(diffInSeconds / 60);
  if (diffInMinutes < 60) {
    return `${diffInMinutes} minute${diffInMinutes > 1 ? 's' : ''} ago`;
  }

  const diffInHours = Math.floor(diffInMinutes / 60);
  if (diffInHours < 24) {
    return `${diffInHours} hour${diffInHours > 1 ? 's' : ''} ago`;
  }

  const diffInDays = Math.floor(diffInHours / 24);
  if (diffInDays < 7) {
    return `${diffInDays} day${diffInDays > 1 ? 's' : ''} ago`;
  }

  const diffInWeeks = Math.floor(diffInDays / 7);
  if (diffInWeeks < 4) {
    return `${diffInWeeks} week${diffInWeeks > 1 ? 's' : ''} ago`;
  }

  const diffInMonths = Math.floor(diffInDays / 30);
  if (diffInMonths < 12) {
    return `${diffInMonths} month${diffInMonths > 1 ? 's' : ''} ago`;
  }

  const diffInYears = Math.floor(diffInDays / 365);
  return `${diffInYears} year${diffInYears > 1 ? 's' : ''} ago`;
};

/**
 * Custom date formatting
 */
export const formatDateCustom = (date: Date, format: string): string => {
  const replacements: Record<string, string> = {
    'YYYY': date.getFullYear().toString(),
    'YY': date.getFullYear().toString().slice(-2),
    'MM': String(date.getMonth() + 1).padStart(2, '0'),
    'M': String(date.getMonth() + 1),
    'DD': String(date.getDate()).padStart(2, '0'),
    'D': String(date.getDate()),
    'HH': String(date.getHours()).padStart(2, '0'),
    'H': String(date.getHours()),
    'mm': String(date.getMinutes()).padStart(2, '0'),
    'm': String(date.getMinutes()),
    'ss': String(date.getSeconds()).padStart(2, '0'),
    's': String(date.getSeconds())
  };

  let result = format;
  Object.entries(replacements).forEach(([key, value]) => {
    result = result.replace(new RegExp(key, 'g'), value);
  });

  return result;
};

// === STRING UTILITIES ===

/**
 * Capitalize first letter of string
 */
export const capitalize = (str: string): string => {
  if (!str) return str;
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
};

/**
 * Convert string to title case
 */
export const toTitleCase = (str: string): string => {
  if (!str) return str;
  return str.replace(/\w\S*/g, (txt) => 
    txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase()
  );
};

/**
 * Truncate string to specified length
 */
export const truncateString = (str: string, maxLength: number, suffix: string = '...'): string => {
  if (!str || str.length <= maxLength) return str;
  return str.substring(0, maxLength - suffix.length) + suffix;
};

/**
 * Generate slug from string
 */
export const generateSlug = (str: string): string => {
  return str
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_-]+/g, '-')
    .replace(/^-+|-+$/g, '');
};

/**
 * Check if string is valid email
 */
export const isValidEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

/**
 * Check if string is valid phone number
 */
export const isValidPhoneNumber = (phone: string): boolean => {
  const phoneRegex = /^[\+]?[1-9][\d]{0,15}$/;
  return phoneRegex.test(phone.replace(/[\s\-\(\)]/g, ''));
};

// === NUMBER UTILITIES ===

/**
 * Format number with commas
 */
export const formatNumber = (num: number, decimals: number = 0): string => {
  if (isNaN(num)) return '0';
  return num.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  });
};

/**
 * Format currency
 */
export const formatCurrency = (
  amount: number, 
  currency: string = 'USD', 
  locale: string = 'en-US'
): string => {
  if (isNaN(amount)) return '$0.00';
  
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: currency
  }).format(amount);
};

/**
 * Calculate percentage
 */
export const calculatePercentage = (value: number, total: number, decimals: number = 2): number => {
  if (total === 0) return 0;
  return Number(((value / total) * 100).toFixed(decimals));
};

/**
 * Round number to specified decimals
 */
export const roundToDecimals = (num: number, decimals: number = 2): number => {
  return Number(Math.round(Number(num + 'e' + decimals)) + 'e-' + decimals);
};

/**
 * Check if number is within range
 */
export const isInRange = (value: number, min: number, max: number, inclusive: boolean = true): boolean => {
  if (inclusive) {
    return value >= min && value <= max;
  }
  return value > min && value < max;
};

// === ARRAY UTILITIES ===

/**
 * Remove duplicates from array
 */
export const removeDuplicates = <T>(array: T[], key?: keyof T): T[] => {
  if (!key) {
    return [...new Set(array)];
  }
  
  const seen = new Set();
  return array.filter(item => {
    const value = item[key];
    if (seen.has(value)) {
      return false;
    }
    seen.add(value);
    return true;
  });
};

/**
 * Group array by key
 */
export const groupBy = <T>(array: T[], key: keyof T): Record<string, T[]> => {
  return array.reduce((groups, item) => {
    const groupKey = String(item[key]);
    if (!groups[groupKey]) {
      groups[groupKey] = [];
    }
    groups[groupKey].push(item);
    return groups;
  }, {} as Record<string, T[]>);
};

/**
 * Sort array by multiple keys
 */
export const sortByMultiple = <T>(
  array: T[], 
  sortKeys: Array<{ key: keyof T; direction: 'asc' | 'desc' }>
): T[] => {
  return [...array].sort((a, b) => {
    for (const { key, direction } of sortKeys) {
      const aVal = a[key];
      const bVal = b[key];
      
      if (aVal < bVal) return direction === 'asc' ? -1 : 1;
      if (aVal > bVal) return direction === 'asc' ? 1 : -1;
    }
    return 0;
  });
};

/**
 * Chunk array into smaller arrays
 */
export const chunkArray = <T>(array: T[], chunkSize: number): T[][] => {
  const chunks: T[][] = [];
  for (let i = 0; i < array.length; i += chunkSize) {
    chunks.push(array.slice(i, i + chunkSize));
  }
  return chunks;
};

// === OBJECT UTILITIES ===

/**
 * Deep clone object
 */
export const deepClone = <T>(obj: T): T => {
  if (obj === null || typeof obj !== 'object') {
    return obj;
  }
  
  if (obj instanceof Date) {
    return new Date(obj.getTime()) as unknown as T;
  }
  
  if (obj instanceof Array) {
    return obj.map(item => deepClone(item)) as unknown as T;
  }
  
  if (typeof obj === 'object') {
    const cloned = {} as T;
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        cloned[key] = deepClone(obj[key]);
      }
    }
    return cloned;
  }
  
  return obj;
};

/**
 * Merge objects deeply
 */
export const deepMerge = <T extends Record<string, any>>(target: T, ...sources: Partial<T>[]): T => {
  if (!sources.length) return target;
  
  const source = sources.shift();
  if (source === undefined) return target;
  
  if (isObject(target) && isObject(source)) {
    for (const key in source) {
      if (isObject(source[key])) {
        if (!target[key]) Object.assign(target, { [key]: {} });
        deepMerge(target[key] as Record<string, any>, source[key] as Record<string, any>);
      } else {
        Object.assign(target, { [key]: source[key] });
      }
    }
  }
  
  return deepMerge(target, ...sources);
};

/**
 * Check if value is object
 */
export const isObject = (item: any): item is Record<string, any> => {
  return item && typeof item === 'object' && !Array.isArray(item);
};

/**
 * Pick specific keys from object
 */
export const pick = <T extends Record<string, any>, K extends keyof T>(obj: T, keys: K[]): Pick<T, K> => {
  const result = {} as Pick<T, K>;
  keys.forEach(key => {
    if (key in obj) {
      result[key] = obj[key];
    }
  });
  return result;
};

/**
 * Omit specific keys from object
 */
export const omit = <T, K extends keyof T>(obj: T, keys: K[]): Omit<T, K> => {
  const result = { ...obj };
  keys.forEach(key => {
    delete result[key];
  });
  return result;
};

// === VALIDATION UTILITIES ===

/**
 * Validate required fields
 */
export const validateRequired = (data: Record<string, any>, requiredFields: string[]): string[] => {
  const errors: string[] = [];
  
  requiredFields.forEach(field => {
    const value = data[field];
    if (value === undefined || value === null || value === '' || 
        (Array.isArray(value) && value.length === 0)) {
      errors.push(`${field} is required`);
    }
  });
  
  return errors;
};

/**
 * Validate field length
 */
export const validateLength = (
  value: string, 
  fieldName: string, 
  minLength?: number, 
  maxLength?: number
): string[] => {
  const errors: string[] = [];
  
  if (minLength !== undefined && value.length < minLength) {
    errors.push(`${fieldName} must be at least ${minLength} characters long`);
  }
  
  if (maxLength !== undefined && value.length > maxLength) {
    errors.push(`${fieldName} must be no more than ${maxLength} characters long`);
  }
  
  return errors;
};

/**
 * Validate numeric range
 */
export const validateNumericRange = (
  value: number, 
  fieldName: string, 
  min?: number, 
  max?: number
): string[] => {
  const errors: string[] = [];
  
  if (min !== undefined && value < min) {
    errors.push(`${fieldName} must be at least ${min}`);
  }
  
  if (max !== undefined && value > max) {
    errors.push(`${fieldName} must be no more than ${max}`);
  }
  
  return errors;
};

// === FILE UTILITIES ===

/**
 * Get file size in human readable format
 */
export const getFileSizeString = (bytes: number): string => {
  return FileValidationService.formatFileSize(bytes);
};

/**
 * Get file extension
 */
export const getFileExtension = (filename: string): string => {
  const lastDotIndex = filename.lastIndexOf('.');
  if (lastDotIndex === -1) return '';
  return filename.substring(lastDotIndex).toLowerCase();
};

/**
 * Check if file is image
 */
export const isImageFile = (file: File): boolean => {
  return FileValidationService.isImage(file);
};

/**
 * Check if file is document
 */
export const isDocumentFile = (file: File): boolean => {
  return FileValidationService.isDocument(file);
};

// === NOTIFICATION UTILITIES ===

/**
 * Show success notification
 */
export const showSuccess = (message: string, title?: string): void => {
  NotificationResponseService.getInstance().showSuccessToast(message, title);
};

/**
 * Show error notification
 */
export const showError = (message: string, title?: string): void => {
  NotificationResponseService.getInstance().showErrorToast(message, title);
};

/**
 * Show warning notification
 */
export const showWarning = (message: string, title?: string): void => {
  NotificationResponseService.getInstance().showWarningToast(message, title);
};

/**
 * Show info notification
 */
export const showInfo = (message: string, title?: string): void => {
  NotificationResponseService.getInstance().showInfoToast(message, title);
};

// === URL UTILITIES ===

/**
 * Build query string from object
 */
export const buildQueryString = (params: Record<string, any>): string => {
  const searchParams = new URLSearchParams();
  
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      if (Array.isArray(value)) {
        value.forEach(item => searchParams.append(key, String(item)));
      } else {
        searchParams.append(key, String(value));
      }
    }
  });
  
  return searchParams.toString();
};

/**
 * Parse query string to object
 */
export const parseQueryString = (queryString: string): Record<string, string> => {
  const params: Record<string, string> = {};
  const searchParams = new URLSearchParams(queryString);
  
  searchParams.forEach((value, key) => {
    params[key] = value;
  });
  
  return params;
};

/**
 * Get URL parameters
 */
export const getUrlParams = (): Record<string, string> => {
  return parseQueryString(window.location.search);
};

/**
 * Update URL parameters
 */
export const updateUrlParams = (params: Record<string, any>, replace: boolean = false): void => {
  const currentParams = getUrlParams();
  const newParams = { ...currentParams, ...params };
  const queryString = buildQueryString(newParams);
  
  const newUrl = `${window.location.pathname}${queryString ? '?' + queryString : ''}`;
  
  if (replace) {
    window.history.replaceState({}, '', newUrl);
  } else {
    window.history.pushState({}, '', newUrl);
  }
};

// === STORAGE UTILITIES ===

/**
 * Set local storage item with expiration
 */
export const setLocalStorageWithExpiry = (key: string, value: any, ttl: number): void => {
  const item = {
    value,
    expiry: Date.now() + ttl
  };
  localStorage.setItem(key, JSON.stringify(item));
};

/**
 * Get local storage item with expiration check
 */
export const getLocalStorageWithExpiry = <T>(key: string): T | null => {
  const itemStr = localStorage.getItem(key);
  if (!itemStr) return null;
  
  try {
    const item = JSON.parse(itemStr);
    if (Date.now() > item.expiry) {
      localStorage.removeItem(key);
      return null;
    }
    return item.value;
  } catch {
    return null;
  }
};

/**
 * Remove local storage item
 */
export const removeLocalStorage = (key: string): void => {
  localStorage.removeItem(key);
};

/**
 * Clear all local storage
 */
export const clearLocalStorage = (): void => {
  localStorage.clear();
};

// === DEBOUNCE AND THROTTLE ===

/**
 * Debounce function execution
 */
export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  delay: number
): ((...args: Parameters<T>) => void) => {
  let timeoutId: ReturnType<typeof setTimeout>;
  
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func(...args), delay);
  };
};

/**
 * Throttle function execution
 */
export const throttle = <T extends (...args: any[]) => any>(
  func: T,
  delay: number
): ((...args: Parameters<T>) => void) => {
  let lastCall = 0;
  
  return (...args: Parameters<T>) => {
    const now = Date.now();
    if (now - lastCall >= delay) {
      lastCall = now;
      func(...args);
    }
  };
};

// === ERROR HANDLING ===

/**
 * Safe JSON parse with error handling
 */
export const safeJsonParse = <T>(jsonString: string, fallback: T): T => {
  try {
    return JSON.parse(jsonString);
  } catch {
    return fallback;
  }
};

/**
 * Safe JSON stringify with error handling
 */
export const safeJsonStringify = (obj: any, fallback: string = ''): string => {
  try {
    return JSON.stringify(obj);
  } catch {
    return fallback;
  }
};

/**
 * Execute function with error handling
 */
export const executeSafely = <T>(
  fn: () => T, 
  fallback: T, 
  errorHandler?: (error: Error) => void
): T => {
  try {
    return fn();
  } catch (error) {
    if (errorHandler) {
      errorHandler(error instanceof Error ? error : new Error(String(error)));
    }
    return fallback;
  }
};

// === PERFORMANCE UTILITIES ===

/**
 * Measure execution time of function
 */
export const measureExecutionTime = <T>(
  fn: () => T, 
  label: string = 'Function execution'
): T => {
  const start = performance.now();
  const result = fn();
  const end = performance.now();
  
  console.log(`${label}: ${(end - start).toFixed(2)}ms`);
  return result;
};

/**
 * Sleep for specified milliseconds
 */
export const sleep = (ms: number): Promise<void> => {
  return new Promise(resolve => setTimeout(resolve, ms));
};

/**
 * Retry function with exponential backoff
 */
export const retryWithBackoff = async <T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  baseDelay: number = 1000
): Promise<T> => {
  let lastError: Error;
  
  for (let i = 0; i <= maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));
      
      if (i === maxRetries) {
        throw lastError;
      }
      
      const delay = baseDelay * Math.pow(2, i);
      await sleep(delay);
    }
  }
  
  throw lastError!;
};
