/**
 * Date utility functions
 * Centralized location for date formatting and manipulation used across the application
 */

/**
 * Format date for display (removes time component if present)
 * @param dateString - Date string that may include time
 * @returns Formatted date string for display
 */
export const formatDisplayDate = (dateString: string): string => {
  if (!dateString) return '';
  
  // If it includes 'T', it's a datetime string, extract just the date part
  if (dateString.includes('T')) {
    return dateString.split('T')[0];
  }
  
  // If it's already just a date, return as is
  return dateString;
};

/**
 * Format date for backend API calls (ensures YYYY-MM-DD format)
 * @param dateString - Date string to format
 * @returns Formatted date string or undefined if invalid
 */
export const formatDateForBackend = (dateString: string | undefined): string | undefined => {
  if (!dateString || dateString.trim() === '') {
    return undefined; // Don't send empty strings
  }
  
  // If it includes 'T', it's a datetime string, extract just the date part
  if (dateString.includes('T')) {
    return dateString.split('T')[0];
  }
  
  // If it's already in YYYY-MM-DD format, return as is
  if (/^\d{4}-\d{2}-\d{2}$/.test(dateString)) {
    return dateString;
  }
  
  // Try to parse and format the date
  try {
    const date = new Date(dateString);
    if (!isNaN(date.getTime())) {
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      return `${year}-${month}-${day}`;
    }
  } catch (error) {
    console.warn('Failed to parse date:', dateString, error);
  }
  
  return undefined; // Return undefined for invalid dates
};

/**
 * Check if a date string is in valid YYYY-MM-DD format
 * @param dateString - Date string to validate
 * @returns True if valid format
 */
export const isValidDateFormat = (dateString: string): boolean => {
  if (!dateString || typeof dateString !== 'string') return false;
  
  // Check if it matches YYYY-MM-DD format
  const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
  if (!dateRegex.test(dateString)) return false;
  
  // Check if it's a valid date
  const date = new Date(dateString);
  if (isNaN(date.getTime())) return false;
  
  // Check if the parsed date matches the input string (prevents dates like 2024-13-45)
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const formattedDate = `${year}-${month}-${day}`;
  
  return formattedDate === dateString;
};
