/**
 * Authentication utility functions
 * Centralized location for auth-related helpers used across the application
 */

/**
 * Get CSRF token from cookies
 * @param name - Cookie name (typically 'csrftoken')
 * @returns CSRF token value or null if not found
 */
export const getCookie = (name: string): string | null => {
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

/**
 * Get CSRF token with fallback to empty string
 * @returns CSRF token or empty string
 */
export const getCsrfToken = (): string => {
  return getCookie("csrftoken") ?? "";
};
