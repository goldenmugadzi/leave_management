/**
 * API utility functions
 * Centralized location for API-related helpers used across the application
 */

/**
 * Fetch with retry capability
 * @param url - API endpoint URL
 * @param options - Fetch options
 * @param retries - Number of retry attempts (default: 3)
 * @param delay - Delay between retries in milliseconds (default: 1000)
 * @returns Promise with API response data
 */
export const fetchWithRetry = async (
  url: string, 
  options: RequestInit, 
  retries: number = 3, 
  delay: number = 1000
): Promise<any> => {
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

/**
 * Create default request options with CSRF token
 * @param csrfToken - CSRF token for authentication
 * @returns RequestInit object with default headers
 */
export const createDefaultRequestOptions = (csrfToken: string): RequestInit => ({
  method: "GET",
  headers: {
    "Content-Type": "application/json",
    "X-CSRFToken": csrfToken,
  },
});

/**
 * Create POST request options with CSRF token
 * @param csrfToken - CSRF token for authentication
 * @param body - Request body
 * @returns RequestInit object for POST requests
 */
export const createPostRequestOptions = (csrfToken: string, body: any): RequestInit => ({
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "X-CSRFToken": csrfToken,
  },
  body: JSON.stringify(body),
});

/**
 * Create FormData request options with CSRF token
 * @param csrfToken - CSRF token for authentication
 * @param formData - FormData object
 * @returns RequestInit object for FormData requests
 */
export const createFormDataRequestOptions = (csrfToken: string, formData: FormData): RequestInit => ({
  method: "POST",
  headers: {
    "X-CSRFToken": csrfToken,
  },
  body: formData,
});
