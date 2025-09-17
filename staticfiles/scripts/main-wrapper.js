/**
 * Wrapper script for main.js to handle getBoundingClientRect errors
 * This script provides defensive checks before calling getBoundingClientRect
 */

console.log('[WRAPPER] Main wrapper script loaded');

// Override getBoundingClientRect with a safe version
const originalGetBoundingClientRect = Element.prototype.getBoundingClientRect;

Element.prototype.getBoundingClientRect = function() {
  try {
    // Check if element is still in the DOM
    if (!this || !this.isConnected) {
      console.warn('[WRAPPER] getBoundingClientRect called on disconnected element:', this);
      return {
        top: 0,
        left: 0,
        bottom: 0,
        right: 0,
        width: 0,
        height: 0,
        x: 0,
        y: 0
      };
    }
    
    // Call the original method
    return originalGetBoundingClientRect.call(this);
  } catch (error) {
    console.error('[WRAPPER] Error in getBoundingClientRect:', error);
    return {
      top: 0,
      left: 0,
      bottom: 0,
      right: 0,
      width: 0,
      height: 0,
      x: 0,
      y: 0
    };
  }
};

// Override fetch to log API calls
const originalFetch = window.fetch;
window.fetch = function(...args) {
  const [url, options] = args;
  console.log('[WRAPPER] API call:', url, options?.method || 'GET');
  
  return originalFetch.apply(this, args)
    .then(response => {
      console.log('[WRAPPER] API response:', url, response.status, response.statusText);
      return response;
    })
    .catch(error => {
      console.error('[WRAPPER] API error:', url, error);
      throw error;
    });
};

// Add error handling for XMLHttpRequest as well
const originalXHROpen = XMLHttpRequest.prototype.open;
XMLHttpRequest.prototype.open = function(method, url, ...args) {
  console.log('[WRAPPER] XHR call:', method, url);
  return originalXHROpen.call(this, method, url, ...args);
};

console.log('[WRAPPER] All overrides installed successfully');

// Add a global error handler for unhandled errors
window.addEventListener('error', function(event) {
  if (event.error && event.error.message && 
      event.error.message.includes('getBoundingClientRect')) {
    console.error('Caught getBoundingClientRect error:', event.error);
    event.preventDefault(); // Prevent the error from breaking the page
    return true;
  }
});

// Export a safe element query function
window.safeQuerySelector = function(selector) {
  try {
    const element = document.querySelector(selector);
    if (!element) {
      console.warn(`Element not found: ${selector}`);
      return null;
    }
    return element;
  } catch (error) {
    console.error(`Error querying selector ${selector}:`, error);
    return null;
  }
};

// Export a safe getBoundingClientRect function
window.safeGetBoundingClientRect = function(element) {
  if (!element) {
    console.warn('safeGetBoundingClientRect called with null/undefined element');
    return {
      top: 0,
      left: 0,
      bottom: 0,
      right: 0,
      width: 0,
      height: 0,
      x: 0,
      y: 0
    };
  }
  
  try {
    return element.getBoundingClientRect();
  } catch (error) {
    console.error('Error in safeGetBoundingClientRect:', error);
    return {
      top: 0,
      left: 0,
      bottom: 0,
      right: 0,
      width: 0,
      height: 0,
      x: 0,
      y: 0
    };
  }
};

console.log('Main.js wrapper loaded successfully'); 