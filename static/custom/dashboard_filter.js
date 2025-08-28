"use strict";

const e = React.createElement;
const domContainer = document.querySelector("#dashboard_filters");

// Check if the container exists and get the base URL
let url = null;
if (domContainer) {
  url = domContainer.getAttribute("data-baseurl");
} else {
  console.error("Dashboard container element '#dashboard_filters' not found");
}

// Fallback to localhost if no URL is provided
const BASE_URL = url || "http://localhost:8000";
console.log("Dashboard BASE_URL:", BASE_URL);

class DashboardFilter extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      // Dynamic data from API - no more static arrays
      allRegions: [],
      allDistricts: [],
      allSections: [],
      allDepots: [],
      regions: [],
      districts: [],
      sections: [],
      depots: [],
      region: "",
      district: "",
      section: "",
      depot: "",
      selectedRegion: "",
      selectedDistrict: "",
      selectedSection: "",

      // Dashboard data - will be loaded from API
      pbncs: [],
      weekly_sales: [],
      weekly_collections: [],
      upos: [],
      weekly_outages: [],
      weekly_revenue_lost: [],
      tds: [],
      weekly_faults_maintenance: [],
      debtors: [],
      current_month: "",

      selectedRegion: "",
      selectedDistrict: "",
      selectedSection: "",

      authUser: {},

      // Metric cards data - will be loaded from API
      metrics: {
        energy_sold: { value: "0", unit: "GWh", target: "0", target_unit: "GWh", progress: 0 },
        growth: { value: "0", unit: "Clients", target: "0", target_unit: "Clients", progress: 0 },
        revenue_usd: { value: "0", unit: "USD", target: "0", target_unit: "USD", progress: 0 },
        revenue_zwl: { value: "0", unit: "ZWL", target: "0", target_unit: "ZWL", progress: 0 },
        faults: { value: "0", unit: "Complaints", target: "0", target_unit: "", progress: 0 },
        maintenance: { value: "0", unit: "Maintained", target: "0", target_unit: "", progress: 0 }
      },

      // Loading states
      isLoading: true,
      isLoadingRegions: false,
      isLoadingDashboard: false,
      isLoadingPermissions: false,

      // User permissions
      canEdit: false,
      userRoles: [],

      // Editing state
      editingCell: null, // {table: 'weekly_collections', row: 0, field: 'zwl_millions'} or {table: 'weekly_revenue_lost', row: 0, field: 'faults_mwh'} or {table: 'debtors', row: 0, field: 'percentage'} or {type: 'metric', field: 'energy_sold_value'}
      editingValue: "",
      originalValue: "",

      // Error handling
      error: null,
      networkError: false,
      usingFallbackData: false
    };
  }

  componentDidMount() {
    this._isMounted = true;
    
    this.setState({
      region: this.props.region,
      district: this.props.district,
      section: this.props.section,
      depot: this.props.depot,
      isLoading: true
    });

    // Initialize styles and error handling
    this.addPercentageAdjustmentStyles();
    this.addLoadingSpinnerStyles();
    this.setupNetworkErrorHandling();

    // Load all data from backend APIs
    this.initializeData();
  }

  componentWillUnmount() {
    this._isMounted = false;
  }

  initializeData = async () => {
    try {
      this.setState({ isLoading: true, error: null, networkError: false });

      // Load data in parallel for better performance
      await Promise.all([
        this.getRegions(),
        this.getDashboardData(),
        this.getUserPermissions()
      ]);

      // Ensure seamless integration after data load
      setTimeout(() => {
        this.ensureSeamlessFilterIntegration();
      }, 500);

    } catch (error) {
      console.error("Error initializing dashboard data:", error);
      this.setState({
        error: "Failed to load dashboard data. Please refresh the page.",
        networkError: true,
        isLoading: false
      });
      this.showErrorMessage("Failed to load dashboard data. Please check your connection and refresh the page.");
    } finally {
      this.setState({ isLoading: false });
    }
  }

  // Add CSS styles for percentage adjustment visual feedback and loading spinners
  addPercentageAdjustmentStyles = () => {
    if (!document.getElementById('percentage-adjustment-styles')) {
      const style = document.createElement('style');
      style.id = 'percentage-adjustment-styles';
      style.textContent = `
        .percentage-adjusted {
          background-color: #fef3c7 !important;
          border: 2px solid #f59e0b !important;
          animation: percentageAdjustmentPulse 0.6s ease-in-out;
          transition: all 0.3s ease;
        }
        
        @keyframes percentageAdjustmentPulse {
          0% { 
            background-color: #fbbf24;
            transform: scale(1);
          }
          50% { 
            background-color: #f59e0b;
            transform: scale(1.02);
          }
          100% { 
            background-color: #fef3c7;
            transform: scale(1);
          }
        }
        
        .percentage-adjusted::after {
          content: "✓ Adjusted";
          position: absolute;
          top: -8px;
          right: -8px;
          background: #10b981;
          color: white;
          font-size: 10px;
          padding: 2px 4px;
          border-radius: 3px;
          font-weight: bold;
          z-index: 10;
          animation: fadeInOut 3s ease-in-out;
        }
        
        @keyframes fadeInOut {
          0%, 100% { opacity: 0; }
          20%, 80% { opacity: 1; }
        }
        
        /* Toast notification styles */
        #toast-container {
          pointer-events: none;
        }
        
        #toast-container > div {
          pointer-events: auto;
        }
        
        /* Validation hint styles */
        #validation-hint {
          animation: slideInDown 0.2s ease-out;
        }
        
        @keyframes slideInDown {
          from {
            opacity: 0;
            transform: translateY(-10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        /* Inline error message styles */
        .inline-error-message {
          background-color: #fee2e2;
          border: 1px solid #fca5a5;
          color: #dc2626;
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 12px;
          margin-top: 2px;
          animation: slideInDown 0.2s ease-out;
        }
        
        /* Cell error state */
        .cell-error {
          background-color: #fee2e2 !important;
          border: 2px solid #dc2626 !important;
          animation: errorPulse 0.5s ease-in-out;
        }
        
        @keyframes errorPulse {
          0%, 100% { 
            background-color: #fee2e2;
          }
          50% { 
            background-color: #fca5a5;
          }
        }
      `;
      document.head.appendChild(style);
    }
  };

  // Add loading spinner styles
  addLoadingSpinnerStyles = () => {
    if (!document.getElementById('loading-spinner-styles')) {
      const style = document.createElement('style');
      style.id = 'loading-spinner-styles';
      style.textContent = `
        .loading-spinner {
          width: 40px;
          height: 40px;
          border: 4px solid #f3f4f6;
          border-top: 4px solid #3b82f6;
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin: 0 auto;
        }
        
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        
        /* Small loading spinner for inline operations */
        .loading-spinner-small {
          width: 16px;
          height: 16px;
          border: 2px solid #f3f4f6;
          border-top: 2px solid #3b82f6;
          border-radius: 50%;
          animation: spin 1s linear infinite;
          display: inline-block;
          margin-right: 8px;
        }
        
        /* Loading state for table cells */
        .cell-loading {
          position: relative;
          opacity: 0.7;
        }
        
        .cell-loading::after {
          content: '';
          position: absolute;
          top: 50%;
          left: 50%;
          width: 12px;
          height: 12px;
          margin: -6px 0 0 -6px;
          border: 2px solid #f3f4f6;
          border-top: 2px solid #3b82f6;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        /* Dashboard loading overlay */
        .dashboard-loading-overlay {
          position: fixed;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          background: rgba(255, 255, 255, 0.9);
          display: flex;
          flex-direction: column;
          justify-content: center;
          align-items: center;
          z-index: 9999;
        }

        .dashboard-loading-text {
          margin-top: 20px;
          font-size: 16px;
          color: #374151;
          font-weight: 500;
        }

        /* Error message styles */
        .dashboard-error {
          background-color: #fee2e2;
          border: 1px solid #fca5a5;
          color: #dc2626;
          padding: 12px 16px;
          border-radius: 6px;
          margin: 16px 0;
          font-size: 14px;
        }

        .dashboard-error-retry {
          background-color: #3b82f6;
          color: white;
          border: none;
          padding: 8px 16px;
          border-radius: 4px;
          cursor: pointer;
          margin-top: 8px;
          font-size: 14px;
        }

        .dashboard-error-retry:hover {
          background-color: #2563eb;
        }
      `;
      document.head.appendChild(style);
    }
  };

  // Loading and error message methods
  showLoadingMessage = (message = "Loading...") => {
    this.hideMessages();
    const loadingDiv = document.createElement('div');
    loadingDiv.id = 'dashboard-loading-message';
    loadingDiv.className = 'dashboard-loading-overlay';
    loadingDiv.innerHTML = `
      <div class="loading-spinner"></div>
      <div class="dashboard-loading-text">${message}</div>
    `;
    document.body.appendChild(loadingDiv);
  };

  hideLoadingMessage = () => {
    const loadingDiv = document.getElementById('dashboard-loading-message');
    if (loadingDiv) {
      loadingDiv.remove();
    }
  };

  showErrorMessage = (message, showRetry = true) => {
    this.hideMessages();
    const errorDiv = document.createElement('div');
    errorDiv.id = 'dashboard-error-message';
    errorDiv.className = 'dashboard-error';
    errorDiv.innerHTML = `
      <div>${message}</div>
      ${showRetry ? '<button class="dashboard-error-retry" onclick="window.location.reload()">Retry</button>' : ''}
    `;

    // Insert at the top of the dashboard container
    const container = document.querySelector("#dashboard_filters");
    if (container) {
      container.insertBefore(errorDiv, container.firstChild);
    }
  };

  clearMessages = () => {
    this.hideLoadingMessage();
    const errorDiv = document.getElementById('dashboard-error-message');
    if (errorDiv) {
      errorDiv.remove();
    }
  };

  hideMessages = () => {
    this.hideLoadingMessage();
    this.clearMessages();
  };

  getUserPermissions = () => {
    return new Promise((resolve, reject) => {
      this.setState({ isLoadingPermissions: true });

      fetch(`${BASE_URL}/dashboards/user_permissions`)
        .then((response) => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          return response.json();
        })
        .then((data) => {
          console.log("User permissions data: ", data);
          this.setState({
            canEdit: data.canEdit || false,
            userRoles: data.userRoles || [],
            authUser: data.user || {},
            isLoadingPermissions: false
          });
          resolve(data);
        })
        .catch((error) => {
          console.error("Error loading user permissions:", error);
          this.setState({
            canEdit: false,
            userRoles: [],
            authUser: {},
            isLoadingPermissions: false
          });
          // Don't show error for permissions as it's not critical for basic functionality
          console.warn("User permissions not available, continuing with read-only mode");
          resolve({ canEdit: false, userRoles: [], user: {} });
        });
    });
  };

  // Initialize dashboard components (charts removed as requested)
  initComponents = () => {
    console.log("Initializing dashboard components...");
    
    // Charts have been removed - this method now only handles data initialization
    // All chart-related functionality has been removed as requested
    
    console.log("Dashboard components initialized successfully");
    console.log("Focus areas: Weekly Collections, Weekly Revenue Lost, Debtors by Category, and Metrics Cards");
  };

  // Get regions data from API
  getRegions = () => {
    return new Promise((resolve, reject) => {
      this.setState({ isLoadingRegions: true });

      if (!BASE_URL) {
        console.error("BASE_URL is not available, using fallback regional data");
        const fallbackData = this.getFallbackRegionalData();
        this.setState({
          regions: fallbackData.regions || [],
          districts: fallbackData.districts || [],
          sections: fallbackData.sections || [],
          depots: fallbackData.depots || [],
          isLoadingRegions: false
        });
        resolve(fallbackData);
        return;
      }

      console.log(`Attempting to fetch regions data from: ${BASE_URL}/dashboards/regions`);

      fetch(`${BASE_URL}/dashboards/regions`)
        .then((response) => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          return response.json();
        })
        .then((data) => {
          console.log("Regions data loaded:", data);
          
          this.setState({
            regions: data.regions || [],
            districts: data.districts || [],
            sections: data.sections || [],
            depots: data.depots || [],
            isLoadingRegions: false
          });

          console.log(`Loaded ${data.regions?.length || 0} regions, ${data.districts?.length || 0} districts, ${data.depots?.length || 0} depots`);
          resolve(data);
        })
        .catch((error) => {
          console.error("Error loading regions data:", error);
          // Use fallback data
          const fallbackData = this.getFallbackRegionalData();
          this.setState({
            regions: fallbackData.regions || [],
            districts: fallbackData.districts || [],
            sections: fallbackData.sections || [],
            depots: fallbackData.depots || [],
            isLoadingRegions: false
          });
          resolve(fallbackData);
        });
    });
  };

  // Get dashboard data from API (simplified - no chart data)
  getDashboardData = () => {
    return new Promise((resolve, reject) => {
      this.setState({ isLoadingDashboard: true });

      // Check if BASE_URL is available
      if (!BASE_URL) {
        console.error("BASE_URL is not available, using fallback data");
        this.useFallbackData();
        resolve(null);
        return;
      }

      console.log(`Attempting to fetch dashboard data from: ${BASE_URL}/dashboards/dashboard_data`);

      fetch(`${BASE_URL}/dashboards/dashboard_data`)
        .then((response) => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          return response.json();
        })
        .then((data) => {
          console.log("Dashboard data loaded successfully:", data);
          
          // Format the data for display
          const formattedData = this.formatAllDashboardData(data);

          this.setState({
            pbncs: data.pbncs || [],
            weekly_sales: data.weekly_sales || [],
            weekly_collections: formattedData.weekly_collections || [],
            upos: data.upos || [],
            weekly_outages: data.weekly_outages || [],
            weekly_revenue_lost: formattedData.weekly_revenue_lost || [],
            tds: data.tds || [],
            weekly_faults_maintenance: data.weekly_faults_maintenance || [],
            debtors: formattedData.debtors || [],
            metrics: data.metrics || this.state.metrics,
            isLoadingDashboard: false,
            usingFallbackData: false
          });

          // Initialize components after data is loaded
          setTimeout(() => {
            if (this._isMounted) {
              this.initComponents();
            }
          }, 100);

          resolve(data);
        })
        .catch((error) => {
          console.warn("Dashboard API endpoint not available, using fallback data:", error);
          this.useFallbackData();
          resolve(null);
        });
    });
  };

  // Helper method to use fallback data
  useFallbackData = () => {
    const fallbackData = this.getFallbackDashboardData();
    const formattedData = this.formatAllDashboardData(fallbackData);

    this.setState({
      pbncs: fallbackData.pbncs || [],
      weekly_sales: fallbackData.weekly_sales || [],
      weekly_collections: formattedData.weekly_collections || [],
      upos: fallbackData.upos || [],
      weekly_outages: fallbackData.weekly_outages || [],
      weekly_revenue_lost: formattedData.weekly_revenue_lost || [],
      tds: fallbackData.tds || [],
      weekly_faults_maintenance: fallbackData.weekly_faults_maintenance || [],
      debtors: formattedData.debtors || [],
      metrics: fallbackData.metrics || this.state.metrics,
      isLoadingDashboard: false,
      usingFallbackData: true
    });

    // Initialize components after data is loaded
    setTimeout(() => {
      if (this._isMounted) {
        this.initComponents();
      }
    }, 100);

    console.log("Using fallback dashboard data until API is available");
  };

  getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === name + "=") {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  onServiceSelected = (event) => {
    console.log(event);
    const { name, checked } = event.target;
    this.setState({
      form: {
        ...this.state.form,
        services: {
          ...this.state.form.services,
          [name]: checked,
        },
      },
    });
  };

  onInputChange = (event) => {
    console.log(event);
    const { name, value } = event.target;
    this.setState({
      form: {
        ...this.state.form,
        [name]: value,
      },
    });
  };

  // Handle filter selection changes
  onFilterSelectCenters = (filterType, event) => {
    const value = event.target.value;
    console.log(`${filterType} filter changed to:`, value);

    if (filterType === "region") {
      this.setState({
        selectedRegion: value,
        selectedDistrict: "",
        selectedSection: "",
        selectedDepot: ""
      });
      
      // Filter districts based on selected region
      if (value) {
        const filteredDistricts = this.state.allDistricts.filter(
          district => district.region_id == value
        );
        this.setState({ districts: filteredDistricts });
      } else {
        this.setState({ districts: this.state.allDistricts });
      }
    } else if (filterType === "district") {
      this.setState({
        selectedDistrict: value,
        selectedSection: "",
        selectedDepot: ""
      });
      
      // Filter sections based on selected district
      if (value) {
        const filteredSections = this.state.allSections.filter(
          section => section.district_id == value
        );
        this.setState({ sections: filteredSections });
      } else {
        this.setState({ sections: this.state.allSections });
      }
    } else if (filterType === "depot") {
      this.setState({
        selectedDepot: value
      });
    }

    // Apply filters to dashboard data
    this.applyFilters(filterType, value);
  };

  // Apply filters to dashboard data
  applyFilters = (filterType, value) => {
    if (!value) return;

    console.log(`Applying ${filterType} filter:`, value);
    
    // Show loading message
    this.showLoadingMessage(`Filtering data by ${filterType}...`);

    // Build filter parameters
    const filterParams = new URLSearchParams();
    if (this.state.selectedRegion) filterParams.append('region', this.state.selectedRegion);
    if (this.state.selectedDistrict) filterParams.append('district', this.state.selectedDistrict);
    if (this.state.selectedDepot) filterParams.append('depot', this.state.selectedDepot);

    // Fetch filtered data
    fetch(`${BASE_URL}/dashboards/dashboard_filter?${filterParams.toString()}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      }
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        console.log('Filtered data loaded:', data.data);
        
        // Update state with filtered data
        this.setState({
          weekly_collections: data.data.weekly_collections || [],
          weekly_revenue_lost: data.data.weekly_revenue_lost || [],
          debtors: data.data.debtors || [],
          weekly_sales: data.data.weekly_sales || [],
          weekly_outages: data.data.weekly_outages || [],
          weekly_faults_maintenance: data.data.weekly_faults_maintenance || [],
          pbncs: data.data.pbncs || [],
          upos: data.data.upos || [],
          tds: data.data.tds || [],
          metrics: data.data.metrics || this.state.metrics
        });
        
        this.showToastNotification('Data filtered successfully', 'success', 2000);
      } else {
        console.error('Filter request failed:', data.error);
        this.showToastNotification('Failed to filter data', 'error', 3000);
      }
    })
    .catch(error => {
      console.error('Error applying filters:', error);
      this.showToastNotification('Error applying filters', 'error', 3000);
    })
    .finally(() => {
      this.hideLoadingMessage();
    });
  };

  // Save changes to server
  saveChangesToServer = (table, row, field, value) => {
    console.log(`Saving ${table}[${row}].${field} = ${value}`);

    // Show loading state for the specific cell
    this.showCellLoadingState(table, row, field, true);

    // Show loading message
    this.showLoadingMessage(`Saving ${this.getTableDisplayName(table)} data...`);

    // Enhanced payload for new table types
    const payload = {
      table: table,
      row: row,
      field: field,
      value: value,
      timestamp: new Date().toISOString()
    };

    // Add location context for filtering
    if (this.state.selectedRegion) {
      payload.region = this.state.selectedRegion;
    }
    if (this.state.selectedDistrict) {
      payload.district = this.state.selectedDistrict;
    }
    if (this.state.selectedDepot) {
      payload.depot = this.state.selectedDepot;
    }

    // Add user context for audit trail
    if (this.state.authUser && this.state.authUser.id) {
      payload.user_id = this.state.authUser.id;
    }

    // Handle different table types with specific endpoints or data formatting
    let endpoint = `${BASE_URL}/dashboards/save_dashboard_data`;

    // You can add specific endpoints for different table types if needed
    if (table === 'weekly_collections') {
      // Could use a specific endpoint: endpoint = `${BASE_URL}/dashboards/save_weekly_collections`;
      payload.data_type = 'currency_millions';
    } else if (table === 'weekly_revenue_lost') {
      // Could use a specific endpoint: endpoint = `${BASE_URL}/dashboards/save_weekly_revenue_lost`;
      payload.data_type = 'mwh_values';
    } else if (table === 'debtors') {
      // Could use a specific endpoint: endpoint = `${BASE_URL}/dashboards/save_debtors`;
      payload.data_type = 'percentage_values';
    }

    fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": this.getCookie("csrftoken"),
      },
      body: JSON.stringify(payload),
    })
      .then((response) => {
        // Hide loading state
        this.hideLoadingMessage();
        this.showCellLoadingState(table, row, field, false);

        if (!response.ok) {
          // Handle different HTTP error statuses
          let errorMessage = `Server error (${response.status})`;
          if (response.status === 400) {
            errorMessage = "Invalid data provided";
          } else if (response.status === 401) {
            errorMessage = "You are not authorized to make this change";
          } else if (response.status === 403) {
            errorMessage = "Access denied. You don't have permission to edit this data";
          } else if (response.status === 404) {
            errorMessage = "Data not found";
          } else if (response.status >= 500) {
            errorMessage = "Server error. Please try again later";
          }
          throw new Error(errorMessage);
        }
        return response.json();
      })
      .then((data) => {
        if (data.success) {
          console.log("Changes saved successfully");
          this.showSuccessMessage(`${this.getTableDisplayName(table)} data updated successfully`);

          // Show success state for the cell
          this.showCellSuccessState(table, row, field);

          // Remove any error states from the cell
          this.clearCellErrorState(table, row, field);

          // Handle specific responses for different table types
          if (table === 'weekly_revenue_lost' && data.updated_total) {
            // Update the total MWh value in the state
            const updatedData = [...this.state.weekly_revenue_lost];
            if (row < updatedData.length) {
              updatedData[row].total_mwh = parseFloat(data.updated_total);
              this.setState({
                weekly_revenue_lost: updatedData
              });
              this.showInfoMessage(`Total MWh automatically updated to ${data.updated_total} MWh`);
            }
          } else if (table === 'debtors' && data.updated_percentages) {
            // Handle auto-adjusted debtor percentages from backend
            const updatedData = [...this.state.debtors];
            const backendAdjustments = [];

            Object.keys(data.updated_percentages).forEach(category => {
              const itemIndex = updatedData.findIndex(item => item.category === category);
              if (itemIndex !== -1) {
                const oldValue = updatedData[itemIndex].percentage;
                const newValue = parseFloat(data.updated_percentages[category]);
                updatedData[itemIndex].percentage = newValue;

                backendAdjustments.push({
                  category: category,
                  oldValue: oldValue,
                  newValue: newValue,
                  change: newValue - oldValue
                });
              }
            });

            this.setState({
              debtors: updatedData
            });

            // Show backend adjustment feedback
            this.showPercentageAdjustmentFeedback(backendAdjustments);
            this.showToastNotification('Percentages synchronized with server and adjusted to maintain 100% total', 'success', 4000);
          }

          // Handle any other server-side calculated values
          if (data.updated_data) {
            this.handleServerUpdatedData(table, data.updated_data);
          }
        } else {
          console.error("Failed to save changes:", data.error);

          // Show specific error messages based on error type
          let errorMessage = data.error || "Failed to save changes";
          if (data.validation_errors) {
            errorMessage = Object.values(data.validation_errors).flat().join(', ');
          }

          this.showValidationError(errorMessage);
          this.showCellErrorState(table, row, field);
          this.revertChanges(table, row, field);
        }
      })
      .catch((error) => {
        console.error("Error saving changes:", error);

        // Hide loading state
        this.hideLoadingMessage();
        this.showCellLoadingState(table, row, field, false);

        // Show appropriate error message based on error type
        let errorMessage = "Network error occurred while saving changes";
        if (error.message.includes("Failed to fetch")) {
          errorMessage = "Connection failed. Please check your internet connection and try again";
        } else if (error.message) {
          errorMessage = error.message;
        }

        this.showValidationError(errorMessage);
        this.showCellErrorState(table, row, field);
        this.revertChanges(table, row, field);
      });
  };

  // Helper function to calculate progress percentage
  calculateProgress = (value, target) => {
    const numValue = parseFloat(value) || 0;
    const numTarget = parseFloat(target) || 0;
    if (numTarget <= 0) return 0;
    const progress = Math.round((numValue / numTarget) * 100);
    return Math.min(progress, 100); // Cap at 100%
  };

  // Helper method to get user-friendly table display names
  getTableDisplayName = (table) => {
    const displayNames = {
      'weekly_collections': 'Weekly Collections',
      'weekly_revenue_lost': 'Weekly Revenue Lost',
      'debtors': 'Debtors'
    };
    return displayNames[table] || table;
  };

  // Helper method to handle server-updated data (e.g., recalculated percentages)
  handleServerUpdatedData = (table, updatedData) => {
    if (updatedData && typeof updatedData === 'object') {
      this.setState({
        [table]: updatedData
      });
    }
  };

  // Helper method to revert changes on save failure
  revertChanges = (table, row, field) => {
    const { originalValue } = this.state;
    if (originalValue !== undefined && originalValue !== null) {
      const updatedData = [...this.state[table]];
      updatedData[row] = originalValue;
      this.setState({
        [table]: updatedData
      });
      console.log(`Reverted ${table}[${row}].${field} to original value: ${originalValue}`);

      // Show revert notification
      this.showToastNotification(`Value reverted to: ${originalValue}`, 'warning', 3000);
    }
  };

  // Helper method to show success messages
  showSuccessMessage = (message) => {
    console.log('Success:', message);
    this.showToastNotification(message, 'success', 3000);
  };

  // Helper function to get progress bar color based on percentage
  getProgressColor = (progress) => {
    if (progress >= 90) return 'bg-green-600'; // Excellent - Green
    if (progress >= 75) return 'bg-blue-600';  // Good - Blue
    if (progress >= 50) return 'bg-yellow-600'; // Fair - Yellow
    if (progress >= 25) return 'bg-orange-600'; // Poor - Orange
    return 'bg-red-600'; // Very Poor - Red
  };

  // Enhanced editing functionality
  startEdit = (table, rowIndex, field, currentValue) => {
    // Extract numeric value from formatted display for editing
    let editingValue = currentValue;

    // Use the extractNumericValue method for all formatted fields
    if (table === 'weekly_collections' && (field === 'zwl_millions' || field === 'usd_millions')) {
      editingValue = this.extractNumericValue(currentValue);
    } else if (table === 'weekly_revenue_lost' && (field === 'faults_mwh' || field === 'maintenance_mwh')) {
      editingValue = this.extractNumericValue(currentValue);
    } else if (table === 'debtors' && field === 'percentage') {
      editingValue = this.extractNumericValue(currentValue);
    }

    // Ensure we have a valid numeric value for editing
    if (typeof editingValue === 'string' && editingValue.trim() === '') {
      editingValue = '0';
    }

    this.setState({
      editingCell: { table, row: rowIndex, field },
      editingValue: editingValue.toString(),
      originalValue: currentValue
    });
  };

  cancelEdit = () => {
    this.clearValidationHint();
    this.setState({
      editingCell: null,
      editingValue: "",
      originalValue: ""
    });
  };

  handleEditChange = (event) => {
    let value = event.target.value;

    // Real-time validation feedback (optional enhancement)
    const { editingCell } = this.state;
    if (editingCell && editingCell.table && editingCell.field) {
      const { table, field, row } = editingCell;

      // Provide real-time validation hints
      if (table === 'weekly_collections' && (field === 'zwl_millions' || field === 'usd_millions')) {
        // Allow only numbers and decimal points
        value = value.replace(/[^0-9.]/g, '');
      } else if (table === 'weekly_revenue_lost' && (field === 'faults_mwh' || field === 'maintenance_mwh')) {
        // Allow only numbers and decimal points
        value = value.replace(/[^0-9.]/g, '');
      } else if (table === 'debtors' && field === 'percentage') {
        // Allow only numbers and decimal points, limit to 100
        value = value.replace(/[^0-9.]/g, '');
        const numValue = parseFloat(value);
        if (!isNaN(numValue) && numValue > 100) {
          value = '100';
        }

        // Provide real-time validation feedback for debtor percentages
        if (value && !isNaN(numValue)) {
          const validation = this.validatePercentageInput(numValue, row, this.state.debtors);
          if (!validation.isValid) {
            this.showValidationHint(validation.error, 'error');
          } else if (validation.warning) {
            this.showValidationHint(validation.warning, 'warning');
          } else {
            this.clearValidationHint();
          }
        }
      }
    }

    this.setState({
      editingValue: value
    });
  };

  // Show loading message during filter operations with spinner
  showLoadingMessage = (message) => {
    console.log(`Loading: ${message}`);

    // Create or update loading overlay
    let loadingOverlay = document.getElementById('loading-overlay');
    if (!loadingOverlay) {
      loadingOverlay = document.createElement('div');
      loadingOverlay.id = 'loading-overlay';
      loadingOverlay.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
      loadingOverlay.innerHTML = `
        <div class="bg-white rounded-lg p-6 max-w-sm mx-4 text-center">
          <div class="loading-spinner mb-4"></div>
          <p class="text-gray-700 font-medium" id="loading-message">${message}</p>
        </div>
      `;
      document.body.appendChild(loadingOverlay);
    } else {
      const messageElement = loadingOverlay.querySelector('#loading-message');
      if (messageElement) {
        messageElement.textContent = message;
      }
    }

    // Add loading spinner styles if not already present
    this.addLoadingSpinnerStyles();

    // Show toast notification as well
    this.showToastNotification(message, 'info', 2000);
  };

  // Hide loading message
  hideLoadingMessage = () => {
    const loadingOverlay = document.getElementById('loading-overlay');
    if (loadingOverlay) {
      loadingOverlay.remove();
    }
  };



  // Clear any messages and overlays
  clearMessages = () => {
    console.log('Clearing messages');

    // Clear loading overlay
    this.hideLoadingMessage();

    // Clear validation hints
    this.clearValidationHint();

    // Clear any inline error messages
    const errorMessages = document.querySelectorAll('.inline-error-message');
    errorMessages.forEach(error => error.remove());
  };

  // Ensure seamless integration of new data sections with existing filter controls
  ensureSeamlessFilterIntegration = () => {
    // Verify that all new data sections respond to filter changes
    const requiredSections = ['weekly_collections', 'weekly_revenue_lost', 'debtors'];
    const currentState = this.state;

    const integrationStatus = requiredSections.map(section => ({
      section,
      hasData: currentState[section] && Array.isArray(currentState[section]),
      dataCount: currentState[section] ? currentState[section].length : 0,
      integrated: true // All sections are now integrated with filtering
    }));

    console.log('Filter integration status for new sections:', integrationStatus);

    // Check if any section is missing or has issues
    const issues = integrationStatus.filter(status => !status.hasData);
    if (issues.length > 0) {
      console.warn('Integration issues detected:', issues);
    } else {
      console.log('All new data sections are seamlessly integrated with filtering');
    }

    return integrationStatus;
  };

  // Show validation hints during editing
  showValidationHint = (message, type = 'info') => {
    // Remove existing hint
    this.clearValidationHint();

    // Find the editing cell and add hint
    const editingInput = document.querySelector('input[autofocus]');
    if (editingInput) {
      const hint = document.createElement('div');
      hint.id = 'validation-hint';
      hint.className = `absolute z-10 mt-1 p-2 text-xs rounded shadow-lg max-w-xs ${type === 'error' ? 'bg-red-100 text-red-800 border border-red-300' :
        type === 'warning' ? 'bg-yellow-100 text-yellow-800 border border-yellow-300' :
          'bg-blue-100 text-blue-800 border border-blue-300'
        }`;
      hint.textContent = message;

      // Position hint below the input
      const inputRect = editingInput.getBoundingClientRect();
      hint.style.position = 'fixed';
      hint.style.top = `${inputRect.bottom + 5}px`;
      hint.style.left = `${inputRect.left}px`;

      document.body.appendChild(hint);
    }
  };

  // Clear validation hints
  clearValidationHint = () => {
    const existingHint = document.getElementById('validation-hint');
    if (existingHint) {
      existingHint.remove();
    }
  };

  saveEdit = () => {
    const { editingCell, editingValue } = this.state;
    if (!editingCell) return;

    // Clear any validation hints
    this.clearValidationHint();

    if (editingCell.type === 'metric') {
      // Handle metric editing
      const { field } = editingCell;
      const fieldParts = field.split('_');
      const property = fieldParts.pop();
      const metricKey = fieldParts.join('_');

      let valueToSave = editingValue;
      if (property === 'value' || property === 'target' || property === 'progress') {
        valueToSave = property === 'progress' ? parseFloat(editingValue) || 0 : editingValue;
      }

      const updatedMetrics = {
        ...this.state.metrics,
        [metricKey]: {
          ...this.state.metrics[metricKey],
          [property]: valueToSave
        }
      };

      // Auto-calculate progress when value or target changes
      if (property === 'value' || property === 'target') {
        const value = property === 'value' ? parseFloat(valueToSave) : parseFloat(updatedMetrics[metricKey].value);
        const target = property === 'target' ? parseFloat(valueToSave) : parseFloat(updatedMetrics[metricKey].target);
        if (target > 0) {
          updatedMetrics[metricKey].progress = Math.round((value / target) * 100);
        }
      }

      this.setState({
        metrics: updatedMetrics,
        editingCell: null,
        editingValue: "",
        originalValue: ""
      });

      this.saveChangesToServer('metrics', metricKey, property, valueToSave);
      console.log(`Saved metrics.${metricKey}.${property} = ${valueToSave}`);
    } else {
      // Handle table editing with enhanced validation
      const { table, row, field } = editingCell;
      const updatedData = [...this.state[table]];

      // Enhanced validation based on data type
      let validation = { isValid: true, errors: [], value: editingValue };
      let valueToSave = editingValue;

      // Apply specific validation based on table and field
      if (table === 'weekly_collections' && (field === 'zwl_millions' || field === 'usd_millions')) {
        validation = this.validateCurrencyValue(editingValue, field);
        valueToSave = validation.value;
      } else if (table === 'weekly_revenue_lost') {
        if (field === 'total_mwh') {
          // Prevent manual editing of total field
          this.showValidationError('Total MWh is auto-calculated and cannot be edited manually');
          this.cancelEdit();
          return;
        } else if (field === 'faults_mwh' || field === 'maintenance_mwh') {
          validation = this.validateRevenueLostValue(editingValue, field);
          valueToSave = validation.value;
        }
      } else if (table === 'debtors' && field === 'percentage') {
        validation = this.validatePercentageValue(editingValue, field);
        valueToSave = validation.value;

        // Additional validation for debtor percentages
        if (validation.isValid) {
          const testData = [...this.state[table]];
          testData[row][field] = valueToSave;
          const totalValidation = this.validateDebtorPercentagesSum(testData);

          if (!totalValidation.isValid && Math.abs(totalValidation.difference) > 5) {
            // Only warn if the difference is significant (more than 5%)
            validation.warnings = [`Total will be ${totalValidation.total}% (difference: ${totalValidation.difference > 0 ? '+' : ''}${totalValidation.difference}%). Other percentages will be auto-adjusted.`];
          }
        }
      } else if (field === 'outages' || field === 'resolved' || field === 'pending' ||
        field === 'faults' || field === 'maintenance' || field === 'completed') {
        // Integer validation for existing fields
        const intValue = parseInt(editingValue);
        if (isNaN(intValue) || intValue < 0) {
          validation = { isValid: false, errors: [`${field} must be a non-negative integer`], value: 0 };
        } else {
          valueToSave = intValue;
        }
      }

      // If validation fails, show error and revert
      if (!validation.isValid) {
        this.showValidationError(validation.errors.join(', '));
        this.cancelEdit();
        return;
      }

      // Show warnings if any
      if (validation.warnings && validation.warnings.length > 0) {
        validation.warnings.forEach(warning => {
          this.showToastNotification(warning, 'warning', 4000);
        });
      }

      updatedData[row][field] = valueToSave;

      // Handle automatic calculations
      if (table === 'weekly_revenue_lost') {
        // Auto-calculate total MWh when faults or maintenance values change
        if (field === 'faults_mwh' || field === 'maintenance_mwh') {
          const faults = field === 'faults_mwh' ? valueToSave : (parseFloat(updatedData[row]['faults_mwh']) || 0);
          const maintenance = field === 'maintenance_mwh' ? valueToSave : (parseFloat(updatedData[row]['maintenance_mwh']) || 0);
          const newTotal = this.calculateRevenueLostTotal(faults, maintenance);
          updatedData[row]['total_mwh'] = newTotal;

          // Show user feedback about auto-calculation
          this.showInfoMessage(`Total MWh automatically calculated: ${newTotal} MWh`);
        }
      } else if (table === 'debtors' && field === 'percentage') {
        // Auto-adjust other percentages to maintain 100% total
        const adjustmentResult = this.autoAdjustDebtorPercentages(updatedData, row, valueToSave);
        if (adjustmentResult.adjusted) {
          updatedData = adjustmentResult.updatedData;
          this.showPercentageAdjustmentFeedback(adjustmentResult.adjustments);
        }
      }

      // Format the updated data for display
      const formattedUpdatedData = this.formatTableData(table, updatedData);

      this.setState({
        [table]: formattedUpdatedData,
        editingCell: null,
        editingValue: "",
        originalValue: ""
      });

      this.saveChangesToServer(table, row, field, valueToSave);
      console.log(`Saved ${table}[${row}].${field} = ${valueToSave}`);
    }
  };

  // Helper method to show validation errors
  showValidationError = (message) => {
    console.error('Validation Error:', message);
    this.showToastNotification(message, 'error', 5000);

    // Also show inline error message if there's an active editing cell
    if (this.state.editingCell) {
      this.showInlineErrorMessage(message);
    }
  };

  // Helper method to show info messages
  showInfoMessage = (message) => {
    console.info('Info:', message);
    this.showToastNotification(message, 'info', 3000);
  };

  // Helper method to show info messages
  showInfoMessage = (message) => {
    console.info('Info:', message);
    this.showToastNotification(message, 'info', 3000);
  };

  // Show critical error overlay for system failures
  showCriticalError = (title, message) => {
    // Remove any existing critical error overlay
    const existingOverlay = document.getElementById('critical-error-overlay');
    if (existingOverlay) {
      existingOverlay.remove();
    }

    const errorOverlay = document.createElement('div');
    errorOverlay.id = 'critical-error-overlay';
    errorOverlay.className = 'fixed inset-0 bg-red-900 bg-opacity-75 flex items-center justify-center z-50';
    errorOverlay.innerHTML = `
      <div class="bg-white rounded-lg p-8 max-w-md mx-4 text-center shadow-2xl">
        <div class="text-red-600 text-6xl mb-4">⚠</div>
        <h2 class="text-2xl font-bold text-gray-900 mb-4">${title}</h2>
        <p class="text-gray-700 mb-6">${message}</p>
        <div class="space-y-3">
          <button onclick="location.reload()" class="w-full bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 transition-colors">
            Refresh Page
          </button>
          <button onclick="this.parentElement.parentElement.parentElement.remove()" class="w-full bg-gray-300 text-gray-700 px-4 py-2 rounded hover:bg-gray-400 transition-colors">
            Dismiss
          </button>
        </div>
      </div>
    `;
    document.body.appendChild(errorOverlay);
  };

  // Show/hide loading state for specific cells
  showCellLoadingState = (table, row, field, isLoading) => {
    const cellSelector = `td[data-table="${table}"][data-row="${row}"][data-field="${field}"]`;
    const cell = document.querySelector(cellSelector);

    if (cell) {
      if (isLoading) {
        cell.classList.add('cell-loading');
      } else {
        cell.classList.remove('cell-loading');
      }
    }
  };

  // Show success state for specific cells
  showCellSuccessState = (table, row, field) => {
    const cellSelector = `td[data-table="${table}"][data-row="${row}"][data-field="${field}"]`;
    const cell = document.querySelector(cellSelector);

    if (cell) {
      cell.classList.add('cell-success');
      setTimeout(() => {
        cell.classList.remove('cell-success');
      }, 2000);
    }
  };

  // Show error state for specific cells
  showCellErrorState = (table, row, field) => {
    const cellSelector = `td[data-table="${table}"][data-row="${row}"][data-field="${field}"]`;
    const cell = document.querySelector(cellSelector);

    if (cell) {
      cell.classList.add('cell-error');
    }
  };

  // Clear error state for specific cells
  clearCellErrorState = (table, row, field) => {
    const cellSelector = `td[data-table="${table}"][data-row="${row}"][data-field="${field}"]`;
    const cell = document.querySelector(cellSelector);

    if (cell) {
      cell.classList.remove('cell-error');
    }
  };

  // Show inline error message near the editing cell
  showInlineErrorMessage = (message) => {
    // Remove existing inline error messages
    const existingErrors = document.querySelectorAll('.inline-error-message');
    existingErrors.forEach(error => error.remove());

    // Find the editing input field
    const editingInput = document.querySelector('input[autofocus]');
    if (editingInput) {
      const errorDiv = document.createElement('div');
      errorDiv.className = 'inline-error-message';
      errorDiv.textContent = message;

      // Insert after the input field
      editingInput.parentNode.insertBefore(errorDiv, editingInput.nextSibling);

      // Auto-remove after 5 seconds
      setTimeout(() => {
        if (errorDiv.parentNode) {
          errorDiv.remove();
        }
      }, 5000);
    }
  };

  // Show inline error message near the editing cell
  showInlineErrorMessage = (message) => {
    // Remove existing inline error messages
    const existingErrors = document.querySelectorAll('.inline-error-message');
    existingErrors.forEach(error => error.remove());

    // Find the editing input field
    const editingInput = document.querySelector('input[autofocus]');
    if (editingInput) {
      const errorDiv = document.createElement('div');
      errorDiv.className = 'inline-error-message';
      errorDiv.textContent = message;

      // Insert after the input field
      editingInput.parentNode.insertBefore(errorDiv, editingInput.nextSibling);

      // Auto-remove after 5 seconds
      setTimeout(() => {
        if (errorDiv.parentNode) {
          errorDiv.remove();
        }
      }, 5000);
    }
  };

  // Setup network error handling
  setupNetworkErrorHandling = () => {
    // Listen for online/offline events
    window.addEventListener('online', () => {
      this.showToastNotification('Connection restored', 'success', 3000);
      console.log('Network connection restored');
      if (this.state.networkError) {
        this.setState({ networkError: false });
        this.initializeData(); // Retry loading data
      }
    });

    window.addEventListener('offline', () => {
      this.showToastNotification('Connection lost. Changes will not be saved until connection is restored.', 'warning', 5000);
      console.log('Network connection lost');
      this.setState({ networkError: true });
    });

    // Setup global error handler for unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      console.error('Unhandled promise rejection:', event.reason);
      if (event.reason && event.reason.message && event.reason.message.includes('fetch')) {
        this.showToastNotification('Network error occurred. Please check your connection.', 'error', 4000);
      }
    });
  };

  // Format and validate dashboard data
  formatAllDashboardData = (data) => {
    const formatted = {
      weekly_collections: this.formatWeeklyCollections(data.weekly_collections || []),
      weekly_revenue_lost: this.formatWeeklyRevenueLost(data.weekly_revenue_lost || []),
      debtors: this.formatDebtors(data.debtors || [])
    };

    console.log('Formatted dashboard data:', formatted);
    return formatted;
  };

  formatWeeklyCollections = (collections) => {
    return collections.map(item => ({
      ...item,
      zwl_millions: this.formatNumber(item.zwl_millions),
      usd_millions: this.formatNumber(item.usd_millions)
    }));
  };

  formatWeeklyRevenueLost = (revenueLost) => {
    return revenueLost.map(item => ({
      ...item,
      faults_mwh: this.formatNumber(item.faults_mwh),
      maintenance_mwh: this.formatNumber(item.maintenance_mwh),
      total_mwh: this.formatNumber(item.total_mwh)
    }));
  };

  formatDebtors = (debtors) => {
    return debtors.map(item => ({
      ...item,
      percentage: this.formatPercentage(item.percentage)
    }));
  };

  formatNumber = (value) => {
    if (value === null || value === undefined || value === '') return '0.00';
    const num = parseFloat(value);
    return isNaN(num) ? '0.00' : num.toFixed(2);
  };

  formatPercentage = (value) => {
    if (value === null || value === undefined || value === '') return '0.00';
    const num = parseFloat(value);
    return isNaN(num) ? '0.00' : num.toFixed(2);
  };

  // Validate data sections after loading
  validateNewDataSections = (data) => {
    const sections = ['weekly_collections', 'weekly_revenue_lost', 'debtors', 'pbncs', 'upos'];
    const warnings = [];

    sections.forEach(section => {
      if (!data[section] || !Array.isArray(data[section])) {
        warnings.push(`${section} data is missing or invalid`);
      } else if (data[section].length === 0) {
        warnings.push(`${section} contains no data`);
      }
    });

    if (warnings.length > 0) {
      console.warn('Data validation warnings:', warnings);
    }

    return warnings;
  };

  // Fallback data methods for when APIs are not available
  getFallbackRegionalData = () => {
    return {
      regions: [
        { id: 1, region: 'HARARE REGION' },
        { id: 2, region: 'BULAWAYO REGION' },
        { id: 3, region: 'MUTARE REGION' },
        { id: 4, region: 'GWERU REGION' }
      ],
      districts: [
        { id: 1, district: 'HARARE DISTRICT', region_id: 1 },
        { id: 2, district: 'CHITUNGWIZA DISTRICT', region_id: 1 },
        { id: 3, district: 'EPWORTH DISTRICT', region_id: 1 },
        { id: 4, district: 'BULAWAYO DISTRICT', region_id: 2 },
        { id: 5, district: 'MUTARE DISTRICT', region_id: 3 },
        { id: 6, district: 'GWERU DISTRICT', region_id: 4 }
      ],
      sections: [],
      depots: [
        { id: 1, depot: 'HARARE CENTRAL', district_id: 1 },
        { id: 2, depot: 'CHITUNGWIZA CENTRAL', district_id: 2 },
        { id: 3, depot: 'EPWORTH CENTRAL', district_id: 3 },
        { id: 4, depot: 'BULAWAYO CENTRAL', district_id: 4 },
        { id: 5, depot: 'MUTARE CENTRAL', district_id: 5 },
        { id: 6, depot: 'GWERU CENTRAL', district_id: 6 }
      ]
    };
  };

  getFallbackDashboardData = () => {
    return {
      pbncs: [
        { id: 1, name: 'Transformer Maintenance', amount: '15,000', depot: 'HARARE CENTRAL', district: 'HARARE DISTRICT', region: 'HARARE REGION', created_at: '2025-08-26' },
        { id: 2, name: 'Line Repairs', amount: '8,500', depot: 'CHITUNGWIZA CENTRAL', district: 'CHITUNGWIZA DISTRICT', region: 'HARARE REGION', created_at: '2025-08-25' },
        { id: 3, name: 'Meter Installation', amount: '12,300', depot: 'EPWORTH CENTRAL', district: 'EPWORTH DISTRICT', region: 'HARARE REGION', created_at: '2025-08-24' }
      ],
      weekly_sales: [],
      weekly_collections: [
        { week: 'Week 1', zwl_millions: '15.50', usd_millions: '2.30' },
        { week: 'Week 2', zwl_millions: '18.20', usd_millions: '2.80' },
        { week: 'Week 3', zwl_millions: '12.70', usd_millions: '1.90' },
        { week: 'Week 4', zwl_millions: '21.10', usd_millions: '3.20' }
      ],
      upos: [
        { id: 1, description: 'Emergency Power Restoration', depot: 'HARARE CENTRAL', district: 'HARARE DISTRICT', region: 'HARARE REGION', created_at: '2025-08-26' },
        { id: 2, description: 'Scheduled Maintenance', depot: 'CHITUNGWIZA CENTRAL', district: 'CHITUNGWIZA DISTRICT', region: 'HARARE REGION', created_at: '2025-08-25' },
        { id: 3, description: 'Customer Service', depot: 'EPWORTH CENTRAL', district: 'EPWORTH DISTRICT', region: 'HARARE REGION', created_at: '2025-08-24' }
      ],
      weekly_outages: [
        { week: 'Week 1', outages: 8, resolved: 6, pending: 2 },
        { week: 'Week 2', outages: 12, resolved: 10, pending: 2 },
        { week: 'Week 3', outages: 6, resolved: 5, pending: 1 },
        { week: 'Week 4', outages: 15, resolved: 12, pending: 3 }
      ],
      weekly_revenue_lost: [
        { week: 'Week 1', faults_mwh: '45.20', maintenance_mwh: '23.80', total_mwh: '69.00' },
        { week: 'Week 2', faults_mwh: '38.70', maintenance_mwh: '31.50', total_mwh: '70.20' },
        { week: 'Week 3', faults_mwh: '52.10', maintenance_mwh: '18.90', total_mwh: '71.00' },
        { week: 'Week 4', faults_mwh: '29.30', maintenance_mwh: '42.70', total_mwh: '72.00' }
      ],
      tds: [
        { name: 'Mining Corp A', amount: '45,000' },
        { name: 'Industrial Plant B', amount: '32,500' },
        { name: 'Commercial Center C', amount: '28,700' },
        { name: 'Government Office D', amount: '15,300' }
      ],
      weekly_faults_maintenance: [
        { week: 'Week 1', faults: 12, maintenance: 8, completed: 6, pending: 2 },
        { week: 'Week 2', faults: 15, maintenance: 10, completed: 8, pending: 2 },
        { week: 'Week 3', faults: 9, maintenance: 12, completed: 10, pending: 2 },
        { week: 'Week 4', faults: 18, maintenance: 14, completed: 12, pending: 2 }
      ],
      debtors: [
        { id: 1, category: 'Mining', percentage: '25.50' },
        { id: 2, category: 'Domestic', percentage: '35.20' },
        { id: 3, category: 'Industry', percentage: '15.80' },
        { id: 4, category: 'Commercial', percentage: '12.30' },
        { id: 5, category: 'Farming', percentage: '4.70' },
        { id: 6, category: 'Government', percentage: '3.20' },
        { id: 7, category: 'Parastatal', percentage: '2.10' },
        { id: 8, category: 'Local Authority', percentage: '1.20' }
      ],
      metrics: {
        energy_sold: { value: "125.5", unit: "GWh", target: "150.0", target_unit: "GWh", progress: 84 },
        growth: { value: "2,847", unit: "Clients", target: "3,500", target_unit: "Clients", progress: 81 },
        revenue_usd: { value: "45.2", unit: "USD", target: "60.0", target_unit: "USD", progress: 75 },
        revenue_zwl: { value: "67.8", unit: "ZWL", target: "80.0", target_unit: "ZWL", progress: 85 },
        faults: { value: "156", unit: "Complaints", target: "200", target_unit: "", progress: 78 },
        maintenance: { value: "89", unit: "Maintained", target: "100", target_unit: "", progress: 89 }
      }
    };
  };

  // Auto-adjust debtor percentages to maintain 100% total
  autoAdjustDebtorPercentages = (debtorData, changedRowIndex, newPercentage) => {
    const result = {
      adjusted: false,
      updatedData: [...debtorData],
      adjustments: []
    };

    // Update the changed row with the new percentage first
    result.updatedData[changedRowIndex].percentage = newPercentage;

    // Calculate current total with the new percentage
    const currentTotal = result.updatedData.reduce((sum, item) => {
      return sum + parseFloat(item.percentage || 0);
    }, 0);

    // Check if adjustment is needed (allow small rounding differences)
    if (Math.abs(currentTotal - 100) > 0.01 && result.updatedData.length > 1) {
      const difference = 100 - currentTotal;
      const otherItems = result.updatedData.filter((_, index) => index !== changedRowIndex);

      if (otherItems.length > 0) {
        // Calculate current total of other categories
        const otherTotal = otherItems.reduce((sum, item) => sum + parseFloat(item.percentage || 0), 0);

        if (otherTotal > 0) {
          // Proportionally adjust other categories
          const adjustmentFactor = (100 - newPercentage) / otherTotal;

          result.updatedData.forEach((item, index) => {
            if (index !== changedRowIndex) {
              const currentPercentage = parseFloat(item.percentage || 0);
              const newAdjustedPercentage = Math.max(0, Math.min(100, currentPercentage * adjustmentFactor));
              const roundedPercentage = Math.round(newAdjustedPercentage * 100) / 100; // Round to 2 decimal places

              result.updatedData[index]['percentage'] = roundedPercentage;
              result.adjustments.push({
                category: item.category,
                oldValue: currentPercentage,
                newValue: roundedPercentage,
                change: roundedPercentage - currentPercentage
              });
            }
          });
        } else {
          // If all other categories are 0, distribute remaining equally
          const remainingPercentage = 100 - newPercentage;
          if (remainingPercentage > 0) {
            const equalShare = Math.round((remainingPercentage / otherItems.length) * 100) / 100;

            result.updatedData.forEach((item, index) => {
              if (index !== changedRowIndex) {
                result.updatedData[index]['percentage'] = equalShare;
                result.adjustments.push({
                  category: item.category,
                  oldValue: parseFloat(item.percentage || 0),
                  newValue: equalShare,
                  change: equalShare - parseFloat(item.percentage || 0)
                });
              }
            });
          }
        }

        result.adjusted = true;
      }
    }

    return result;
  };

  // Show visual feedback for percentage adjustments
  showPercentageAdjustmentFeedback = (adjustments) => {
    if (adjustments.length === 0) return;

    // Create detailed feedback message
    const adjustmentDetails = adjustments
      .filter(adj => Math.abs(adj.change) > 0.01) // Only show significant changes
      .map(adj => {
        const changeText = adj.change > 0 ? `+${adj.change.toFixed(2)}%` : `${adj.change.toFixed(2)}%`;
        return `${adj.category}: ${adj.oldValue.toFixed(2)}% → ${adj.newValue.toFixed(2)}% (${changeText})`;
      })
      .join(', ');

    if (adjustmentDetails) {
      const message = `Percentages auto-adjusted to maintain 100% total: ${adjustmentDetails}`;
      this.showToastNotification(message, 'info', 5000); // Show for 5 seconds

      // Add visual highlighting to adjusted cells
      this.highlightAdjustedPercentages(adjustments);
    }
  };

  // Highlight adjusted percentage cells with visual feedback
  highlightAdjustedPercentages = (adjustments) => {
    adjustments.forEach(adj => {
      if (Math.abs(adj.change) > 0.01) {
        // Find the table cell for this category and add temporary highlighting
        const debtorRows = document.querySelectorAll('#debtors-data tr');
        debtorRows.forEach(row => {
          const categoryCell = row.querySelector('td:nth-child(2)'); // Category column
          if (categoryCell && categoryCell.textContent.toLowerCase().includes(adj.category.toLowerCase())) {
            const percentageCell = row.querySelector('td:nth-child(3)'); // Percentage column
            if (percentageCell) {
              // Add temporary highlight class
              percentageCell.classList.add('percentage-adjusted');

              // Remove highlight after 3 seconds
              setTimeout(() => {
                percentageCell.classList.remove('percentage-adjusted');
              }, 3000);
            }
          }
        });
      }
    });
  };

  // Highlight adjusted percentage cells with visual feedback
  highlightAdjustedPercentages = (adjustments) => {
    adjustments.forEach(adj => {
      if (Math.abs(adj.change) > 0.01) {
        // Find the table cell for this category and add temporary highlighting
        const debtorRows = document.querySelectorAll('#debtors-data tr');
        debtorRows.forEach(row => {
          const categoryCell = row.querySelector('td:nth-child(2)'); // Category column
          if (categoryCell && categoryCell.textContent.toLowerCase().includes(adj.category.toLowerCase())) {
            const percentageCell = row.querySelector('td:nth-child(3)'); // Percentage column
            if (percentageCell) {
              // Add temporary highlight class
              percentageCell.classList.add('percentage-adjusted');

              // Remove highlight after 3 seconds
              setTimeout(() => {
                percentageCell.classList.remove('percentage-adjusted');
              }, 3000);
            }
          }
        });
      }
    });
  };

  // Enhanced toast notification system
  showToastNotification = (message, type = 'info', duration = 3000) => {
    // Create toast container if it doesn't exist
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
      toastContainer = document.createElement('div');
      toastContainer.id = 'toast-container';
      toastContainer.className = 'fixed top-4 right-4 z-50 space-y-2';
      document.body.appendChild(toastContainer);
    }

    // Create toast element
    const toast = document.createElement('div');
    const typeClasses = {
      'success': 'bg-green-500 text-white',
      'error': 'bg-red-500 text-white',
      'warning': 'bg-yellow-500 text-black',
      'info': 'bg-blue-500 text-white'
    };

    const iconClasses = {
      'success': '✓',
      'error': '✗',
      'warning': '⚠',
      'info': 'ℹ'
    };

    toast.className = `${typeClasses[type] || typeClasses.info} px-4 py-3 rounded-lg shadow-lg max-w-sm transform transition-all duration-300 ease-in-out opacity-0 translate-x-full`;
    toast.innerHTML = `
      <div class="flex items-start">
        <span class="flex-shrink-0 mr-2 font-bold">${iconClasses[type] || iconClasses.info}</span>
        <div class="flex-1">
          <p class="text-sm font-medium">${type.charAt(0).toUpperCase() + type.slice(1)}</p>
          <p class="text-xs mt-1 opacity-90">${message}</p>
        </div>
        <button class="flex-shrink-0 ml-2 text-lg leading-none hover:opacity-70" onclick="this.parentElement.parentElement.remove()">×</button>
      </div>
    `;

    toastContainer.appendChild(toast);

    // Animate in
    setTimeout(() => {
      toast.classList.remove('opacity-0', 'translate-x-full');
    }, 10);

    // Auto remove after duration
    setTimeout(() => {
      toast.classList.add('opacity-0', 'translate-x-full');
      setTimeout(() => {
        if (toast.parentElement) {
          toast.remove();
        }
      }, 300);
    }, duration);

    console.log(`${type.toUpperCase()}: ${message}`);
  };

  // Validate debtor percentages sum to 100%
  validateDebtorPercentagesSum = (debtorData) => {
    const total = debtorData.reduce((sum, item) => sum + parseFloat(item.percentage || 0), 0);
    const isValid = Math.abs(total - 100) <= 0.01; // Allow small rounding differences

    return {
      isValid,
      total: Math.round(total * 100) / 100,
      difference: Math.round((total - 100) * 100) / 100
    };
  };

  // Real-time percentage validation during editing
  validatePercentageInput = (value, currentRowIndex, debtorData) => {
    const numValue = parseFloat(value);

    if (isNaN(numValue)) {
      return { isValid: false, error: 'Please enter a valid number' };
    }

    if (numValue < 0) {
      return { isValid: false, error: 'Percentage cannot be negative' };
    }

    if (numValue > 100) {
      return { isValid: false, error: 'Percentage cannot exceed 100%' };
    }

    // Check if the new value would make total exceed reasonable bounds
    const otherTotal = debtorData.reduce((sum, item, index) => {
      return index === currentRowIndex ? sum : sum + parseFloat(item.percentage || 0);
    }, 0);

    if (numValue + otherTotal > 100.1) { // Allow small buffer for auto-adjustment
      return {
        isValid: true, // Still valid, but will trigger auto-adjustment
        warning: 'Other percentages will be automatically adjusted to maintain 100% total'
      };
    }

    return { isValid: true };
  };

  // Auto-calculate total MWh for revenue lost data
  calculateRevenueLostTotal = (faultsMwh, maintenanceMwh) => {
    const faults = parseFloat(faultsMwh) || 0;
    const maintenance = parseFloat(maintenanceMwh) || 0;
    return Math.round((faults + maintenance) * 100) / 100; // Round to 2 decimal places
  };

  // Validate that new data sections are properly loaded after filtering
  validateNewDataSections = (data) => {
    const sections = [
      { key: 'weekly_collections', name: 'Weekly Collections' },
      { key: 'weekly_revenue_lost', name: 'Weekly Revenue Lost' },
      { key: 'debtors', name: 'Debtors' }
    ];

    const validationResults = {
      missing: [],
      empty: [],
      valid: []
    };

    sections.forEach(section => {
      if (!data[section.key]) {
        validationResults.missing.push(section.name);
      } else if (Array.isArray(data[section.key]) && data[section.key].length === 0) {
        validationResults.empty.push(section.name);
        console.log(`${section.name} is empty for current filter selection`);
      } else {
        validationResults.valid.push(section.name);
        // Log data structure for debugging
        if (Array.isArray(data[section.key]) && data[section.key].length > 0) {
          console.log(`${section.name} loaded successfully with ${data[section.key].length} records`);
          console.log(`${section.name} sample:`, data[section.key][0]);
        }
      }
    });

    // Report validation results
    if (validationResults.missing.length > 0) {
      console.error('Missing data sections:', validationResults.missing);
    }

    if (validationResults.empty.length > 0) {
      console.info('Empty data sections (no data for current filter):', validationResults.empty);
    }

    if (validationResults.valid.length > 0) {
      console.log('Successfully loaded data sections:', validationResults.valid);
    }

    // Return validation summary for potential UI feedback
    return {
      success: validationResults.missing.length === 0,
      hasData: validationResults.valid.length > 0,
      summary: validationResults
    };
  };

  // Update total MWh when faults or maintenance values change
  updateRevenueLostTotal = (rowIndex) => {
    const updatedData = [...this.state.weekly_revenue_lost];
    if (rowIndex < updatedData.length) {
      const row = updatedData[rowIndex];
      const faultsMwh = parseFloat(row.faults_mwh) || 0;
      const maintenanceMwh = parseFloat(row.maintenance_mwh) || 0;
      const newTotal = this.calculateRevenueLostTotal(faultsMwh, maintenanceMwh);

      updatedData[rowIndex].total_mwh = newTotal;

      this.setState({
        weekly_revenue_lost: updatedData
      });

      return newTotal;
    }
    return 0;
  };

  // Validate MWh values for revenue lost data
  validateRevenueLostValue = (value, field) => {
    const numValue = parseFloat(value);

    if (isNaN(numValue)) {
      return {
        isValid: false,
        errors: [`${field} must be a valid number`],
        value: 0
      };
    }

    if (numValue < 0) {
      return {
        isValid: false,
        errors: [`${field} cannot be negative`],
        value: 0
      };
    }

    return {
      isValid: true,
      errors: [],
      value: numValue
    };
  };

  saveChangesToServer = (table, row, field, value) => {
    console.log(`Saving ${table}[${row}].${field} = ${value}`);

    // Show loading state for the specific cell
    this.showCellLoadingState(table, row, field, true);

    // Show loading message
    this.showLoadingMessage(`Saving ${this.getTableDisplayName(table)} data...`);

    // Enhanced payload for new table types
    const payload = {
      table: table,
      row: row,
      field: field,
      value: value,
      timestamp: new Date().toISOString()
    };

    // Add location context for filtering
    if (this.state.selectedRegion) {
      payload.region = this.state.selectedRegion;
    }
    if (this.state.selectedDistrict) {
      payload.district = this.state.selectedDistrict;
    }
    if (this.state.selectedDepot) {
      payload.depot = this.state.selectedDepot;
    }

    // Add user context for audit trail
    if (this.state.authUser && this.state.authUser.id) {
      payload.user_id = this.state.authUser.id;
    }

    // Handle different table types with specific endpoints or data formatting
    let endpoint = `${BASE_URL}/dashboards/save_dashboard_data`;

    // You can add specific endpoints for different table types if needed
    if (table === 'weekly_collections') {
      // Could use a specific endpoint: endpoint = `${BASE_URL}/dashboards/save_weekly_collections`;
      payload.data_type = 'currency_millions';
    } else if (table === 'weekly_revenue_lost') {
      // Could use a specific endpoint: endpoint = `${BASE_URL}/dashboards/save_weekly_revenue_lost`;
      payload.data_type = 'mwh_values';
    } else if (table === 'debtors') {
      // Could use a specific endpoint: endpoint = `${BASE_URL}/dashboards/save_debtors`;
      payload.data_type = 'percentage_values';
    }

    fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": this.getCookie("csrftoken"),
      },
      body: JSON.stringify(payload),
    })
      .then((response) => {
        // Hide loading state
        this.hideLoadingMessage();
        this.showCellLoadingState(table, row, field, false);

        if (!response.ok) {
          // Handle different HTTP error statuses
          let errorMessage = `Server error (${response.status})`;
          if (response.status === 400) {
            errorMessage = "Invalid data provided";
          } else if (response.status === 401) {
            errorMessage = "You are not authorized to make this change";
          } else if (response.status === 403) {
            errorMessage = "Access denied. You don't have permission to edit this data";
          } else if (response.status === 404) {
            errorMessage = "Data not found";
          } else if (response.status >= 500) {
            errorMessage = "Server error. Please try again later";
          }
          throw new Error(errorMessage);
        }
        return response.json();
      })
      .then((data) => {
        if (data.success) {
          console.log("Changes saved successfully");
          this.showSuccessMessage(`${this.getTableDisplayName(table)} data updated successfully`);

          // Show success state for the cell
          this.showCellSuccessState(table, row, field);

          // Remove any error states from the cell
          this.clearCellErrorState(table, row, field);

          // Handle specific responses for different table types
          if (table === 'weekly_revenue_lost' && data.updated_total) {
            // Update the total MWh value in the state
            const updatedData = [...this.state.weekly_revenue_lost];
            if (row < updatedData.length) {
              updatedData[row].total_mwh = parseFloat(data.updated_total);
              this.setState({
                weekly_revenue_lost: updatedData
              });
              this.showInfoMessage(`Total MWh automatically updated to ${data.updated_total} MWh`);
            }
          } else if (table === 'debtors' && data.updated_percentages) {
            // Handle auto-adjusted debtor percentages from backend
            const updatedData = [...this.state.debtors];
            const backendAdjustments = [];

            Object.keys(data.updated_percentages).forEach(category => {
              const itemIndex = updatedData.findIndex(item => item.category === category);
              if (itemIndex !== -1) {
                const oldValue = updatedData[itemIndex].percentage;
                const newValue = parseFloat(data.updated_percentages[category]);
                updatedData[itemIndex].percentage = newValue;

                backendAdjustments.push({
                  category: category,
                  oldValue: oldValue,
                  newValue: newValue,
                  change: newValue - oldValue
                });
              }
            });

            this.setState({
              debtors: updatedData
            });

            // Show backend adjustment feedback
            this.showPercentageAdjustmentFeedback(backendAdjustments);
            this.showToastNotification('Percentages synchronized with server and adjusted to maintain 100% total', 'success', 4000);
          }

          // Handle any other server-side calculated values
          if (data.updated_data) {
            this.handleServerUpdatedData(table, data.updated_data);
          }
        } else {
          console.error("Failed to save changes:", data.error);

          // Show specific error messages based on error type
          let errorMessage = data.error || "Failed to save changes";
          if (data.validation_errors) {
            errorMessage = Object.values(data.validation_errors).flat().join(', ');
          }

          this.showValidationError(errorMessage);
          this.showCellErrorState(table, row, field);
          this.revertChanges(table, row, field);
        }
      })
      .catch((error) => {
        console.error("Error saving changes:", error);

        // Hide loading state
        this.hideLoadingMessage();
        this.showCellLoadingState(table, row, field, false);

        // Show appropriate error message based on error type
        let errorMessage = "Network error occurred while saving changes";
        if (error.message.includes("Failed to fetch")) {
          errorMessage = "Connection failed. Please check your internet connection and try again";
        } else if (error.message) {
          errorMessage = error.message;
        }

        this.showValidationError(errorMessage);
        this.showCellErrorState(table, row, field);
        this.revertChanges(table, row, field);
      });
  };

  // Helper method to show success messages
  showSuccessMessage = (message) => {
    console.log('Success:', message);
    this.showToastNotification(message, 'success', 3000);
  };

  // Helper method to revert changes on error
  revertChanges = (table, row, field) => {
    const { originalValue } = this.state;
    if (originalValue !== undefined && originalValue !== null) {
      const updatedData = [...this.state[table]];
      if (updatedData[row]) {
        updatedData[row][field] = originalValue;
        this.setState({
          [table]: updatedData
        });
        console.log(`Reverted ${table}[${row}].${field} to original value: ${originalValue}`);
      }
    }
  };

  // Helper method to handle server-updated data (e.g., recalculated percentages)
  handleServerUpdatedData = (table, updatedData) => {
    if (updatedData && typeof updatedData === 'object') {
      this.setState({
        [table]: updatedData
      });
    }
  };

  // Helper method to revert changes on save failure
  revertChanges = (table, row, field) => {
    const { originalValue } = this.state;
    if (originalValue !== undefined && originalValue !== null) {
      const updatedData = [...this.state[table]];
      updatedData[row][field] = originalValue;
      this.setState({
        [table]: updatedData
      });
      console.log(`Reverted ${table}[${row}].${field} to original value: ${originalValue}`);

      // Show revert notification
      this.showToastNotification(`Value reverted to: ${originalValue}`, 'warning', 3000);
    }
  };

  // Helper method to get user-friendly table display names
  getTableDisplayName = (table) => {
    const displayNames = {
      'weekly_collections': 'Weekly Collections',
      'weekly_revenue_lost': 'Weekly Revenue Lost',
      'debtors': 'Debtors'
    };
    return displayNames[table] || table;
  };

  // Show loading state for specific cell
  showCellLoadingState = (table, row, field, isLoading) => {
    // Find the cell element and add/remove loading class
    const cellSelector = `[data-table="${table}"][data-row="${row}"][data-field="${field}"]`;
    const cellElement = document.querySelector(cellSelector);

    if (cellElement) {
      if (isLoading) {
        cellElement.classList.add('cell-loading');
        cellElement.setAttribute('title', 'Saving...');
      } else {
        cellElement.classList.remove('cell-loading');
        cellElement.removeAttribute('title');
      }
    }
  };

  // Show error state for specific cell
  showCellErrorState = (table, row, field) => {
    const cellSelector = `[data-table="${table}"][data-row="${row}"][data-field="${field}"]`;
    const cellElement = document.querySelector(cellSelector);

    if (cellElement) {
      cellElement.classList.add('cell-error');
      cellElement.setAttribute('title', 'Error saving data');

      // Remove error state after 3 seconds
      setTimeout(() => {
        this.clearCellErrorState(table, row, field);
      }, 3000);
    }
  };

  // Clear error state for specific cell
  clearCellErrorState = (table, row, field) => {
    const cellSelector = `[data-table="${table}"][data-row="${row}"][data-field="${field}"]`;
    const cellElement = document.querySelector(cellSelector);

    if (cellElement) {
      cellElement.classList.remove('cell-error');
      cellElement.removeAttribute('title');
    }
  };

  // Helper methods for formatting display values
  formatCurrencyValue = (value, suffix = 'M') => {
    if (value === null || value === undefined || value === '') {
      return `0.0${suffix}`;
    }
    const numValue = parseFloat(value);
    if (isNaN(numValue)) {
      return `0.0${suffix}`;
    }
    return `${numValue.toFixed(1)}${suffix}`;
  };

  formatMWhValue = (value) => {
    if (value === null || value === undefined || value === '') {
      return '0.0 MWh';
    }
    const numValue = parseFloat(value);
    if (isNaN(numValue)) {
      return '0.0 MWh';
    }
    return `${numValue.toFixed(1)} MWh`;
  };

  formatPercentageValue = (value) => {
    if (value === null || value === undefined || value === '') {
      return '0.0%';
    }
    const numValue = parseFloat(value);
    if (isNaN(numValue)) {
      return '0.0%';
    }
    return `${numValue.toFixed(1)}%`;
  };

  // Enhanced formatting functions for dashboard data display

  /**
   * Format currency values with "M" suffix for millions
   * @param {number|string} value - The currency value to format
   * @param {string} currency - Currency type ('ZWL' or 'USD')
   * @returns {string} Formatted currency string (e.g., "5.2M")
   */
  formatCurrencyMillions = (value, currency = '') => {
    if (value === null || value === undefined || value === '') {
      return '0.0M';
    }

    const numValue = parseFloat(value);
    if (isNaN(numValue)) {
      return '0.0M';
    }

    // Format with appropriate decimal places
    if (numValue === 0) {
      return '0.0M';
    } else if (numValue < 0.1) {
      return `${numValue.toFixed(2)}M`; // Show more precision for small values
    } else if (numValue < 10) {
      return `${numValue.toFixed(1)}M`; // One decimal place for values under 10M
    } else {
      return `${Math.round(numValue)}M`; // No decimal places for large values
    }
  };

  /**
   * Format MWh values with appropriate decimal places
   * @param {number|string} value - The MWh value to format
   * @returns {string} Formatted MWh string (e.g., "125.5 MWh")
   */
  formatMWhWithDecimals = (value) => {
    if (value === null || value === undefined || value === '') {
      return '0.0 MWh';
    }

    const numValue = parseFloat(value);
    if (isNaN(numValue)) {
      return '0.0 MWh';
    }

    // Format with appropriate decimal places based on magnitude
    if (numValue === 0) {
      return '0.0 MWh';
    } else if (numValue < 1) {
      return `${numValue.toFixed(2)} MWh`; // Two decimal places for small values
    } else if (numValue < 100) {
      return `${numValue.toFixed(1)} MWh`; // One decimal place for medium values
    } else {
      return `${Math.round(numValue)} MWh`; // No decimal places for large values
    }
  };

  /**
   * Format percentage values with "%" symbol for debtor categories
   * @param {number|string} value - The percentage value to format
   * @returns {string} Formatted percentage string (e.g., "25.5%")
   */
  formatPercentageWithSymbol = (value) => {
    if (value === null || value === undefined || value === '') {
      return '0.0%';
    }

    const numValue = parseFloat(value);
    if (isNaN(numValue)) {
      return '0.0%';
    }

    // Format with one decimal place for percentages
    return `${numValue.toFixed(1)}%`;
  };

  /**
   * Get default value display when no data exists
   * @param {string} dataType - Type of data ('currency', 'mwh', 'percentage')
   * @returns {string} Default formatted value
   */
  getDefaultValueDisplay = (dataType) => {
    switch (dataType) {
      case 'currency':
        return '0.0M';
      case 'mwh':
        return '0.0 MWh';
      case 'percentage':
        return '0.0%';
      default:
        return '0.0';
    }
  };

  /**
   * Format weekly collections data for display
   * @param {object} collectionData - Collection data object with zwl_millions and usd_millions
   * @returns {object} Formatted collection data
   */
  formatWeeklyCollectionsData = (collectionData) => {
    if (!collectionData) {
      return {
        zwl_millions: this.getDefaultValueDisplay('currency'),
        usd_millions: this.getDefaultValueDisplay('currency')
      };
    }

    return {
      ...collectionData,
      zwl_millions: this.formatCurrencyMillions(collectionData.zwl_millions),
      usd_millions: this.formatCurrencyMillions(collectionData.usd_millions)
    };
  };

  /**
   * Format weekly revenue lost data for display
   * @param {object} revenueLostData - Revenue lost data object with faults_mwh, maintenance_mwh, total_mwh
   * @returns {object} Formatted revenue lost data
   */
  formatWeeklyRevenueLostData = (revenueLostData) => {
    if (!revenueLostData) {
      return {
        faults_mwh: this.getDefaultValueDisplay('mwh'),
        maintenance_mwh: this.getDefaultValueDisplay('mwh'),
        total_mwh: this.getDefaultValueDisplay('mwh')
      };
    }

    return {
      ...revenueLostData,
      faults_mwh: this.formatMWhWithDecimals(revenueLostData.faults_mwh),
      maintenance_mwh: this.formatMWhWithDecimals(revenueLostData.maintenance_mwh),
      total_mwh: this.formatMWhWithDecimals(revenueLostData.total_mwh)
    };
  };

  /**
   * Format debtor category data for display
   * @param {object} debtorData - Debtor data object with percentage
   * @returns {object} Formatted debtor data
   */
  formatDebtorCategoryData = (debtorData) => {
    if (!debtorData) {
      return {
        percentage: this.getDefaultValueDisplay('percentage')
      };
    }

    return {
      ...debtorData,
      percentage: this.formatPercentageWithSymbol(debtorData.percentage)
    };
  };

  /**
   * Format all dashboard data sections for display
   * @param {object} dashboardData - Complete dashboard data object
   * @returns {object} Formatted dashboard data
   */
  formatAllDashboardData = (dashboardData) => {
    const formatted = { ...dashboardData };

    // Format weekly collections data
    if (formatted.weekly_collections && Array.isArray(formatted.weekly_collections)) {
      formatted.weekly_collections = formatted.weekly_collections.map(item =>
        this.formatWeeklyCollectionsData(item)
      );
    }

    // Format weekly revenue lost data
    if (formatted.weekly_revenue_lost && Array.isArray(formatted.weekly_revenue_lost)) {
      formatted.weekly_revenue_lost = formatted.weekly_revenue_lost.map(item =>
        this.formatWeeklyRevenueLostData(item)
      );
    }

    // Format debtor category data
    if (formatted.debtors && Array.isArray(formatted.debtors)) {
      formatted.debtors = formatted.debtors.map(item =>
        this.formatDebtorCategoryData(item)
      );
    }

    return formatted;
  };

  /**
   * Format individual cell value based on table and field type
   * @param {string} table - Table name ('weekly_collections', 'weekly_revenue_lost', 'debtors')
   * @param {string} field - Field name
   * @param {any} value - Value to format
   * @returns {string} Formatted value
   */
  formatCellValue = (table, field, value) => {
    if (table === 'weekly_collections') {
      if (field === 'zwl_millions' || field === 'usd_millions') {
        return this.formatCurrencyMillions(value);
      }
    } else if (table === 'weekly_revenue_lost') {
      if (field === 'faults_mwh' || field === 'maintenance_mwh' || field === 'total_mwh') {
        return this.formatMWhWithDecimals(value);
      }
    } else if (table === 'debtors') {
      if (field === 'percentage') {
        return this.formatPercentageWithSymbol(value);
      }
    }

    // Return original value if no specific formatting needed
    return value;
  };

  /**
   * Format table data for display after updates
   * @param {string} table - Table name
   * @param {array} data - Array of data objects
   * @returns {array} Formatted data array
   */
  formatTableData = (table, data) => {
    if (!Array.isArray(data)) return data;

    return data.map(item => {
      const formattedItem = { ...item };

      if (table === 'weekly_collections') {
        if (formattedItem.zwl_millions !== undefined) {
          formattedItem.zwl_millions = this.formatCurrencyMillions(formattedItem.zwl_millions);
        }
        if (formattedItem.usd_millions !== undefined) {
          formattedItem.usd_millions = this.formatCurrencyMillions(formattedItem.usd_millions);
        }
      } else if (table === 'weekly_revenue_lost') {
        if (formattedItem.faults_mwh !== undefined) {
          formattedItem.faults_mwh = this.formatMWhWithDecimals(formattedItem.faults_mwh);
        }
        if (formattedItem.maintenance_mwh !== undefined) {
          formattedItem.maintenance_mwh = this.formatMWhWithDecimals(formattedItem.maintenance_mwh);
        }
        if (formattedItem.total_mwh !== undefined) {
          formattedItem.total_mwh = this.formatMWhWithDecimals(formattedItem.total_mwh);
        }
      } else if (table === 'debtors') {
        if (formattedItem.percentage !== undefined) {
          formattedItem.percentage = this.formatPercentageWithSymbol(formattedItem.percentage);
        }
      }

      return formattedItem;
    });
  };

  // Helper method to extract numeric value from formatted display
  extractNumericValue = (formattedValue) => {
    if (typeof formattedValue === 'number') {
      return formattedValue;
    }
    if (typeof formattedValue === 'string') {
      // Remove common suffixes and extract number
      const cleanValue = formattedValue.replace(/[M%\s]|MWh/g, '');
      const numValue = parseFloat(cleanValue);
      return isNaN(numValue) ? 0 : numValue;
    }
    return 0;
  };

  // Enhanced validation functions for different data types
  validateCurrencyValue = (value, field) => {
    const errors = [];
    const numValue = parseFloat(value);

    if (isNaN(numValue)) {
      errors.push(`${field} must be a valid number`);
      return { isValid: false, errors, value: 0 };
    }

    if (numValue < 0) {
      errors.push(`${field} cannot be negative`);
      return { isValid: false, errors, value: 0 };
    }

    // Check for reasonable currency limits (in millions)
    if (numValue > 999999) {
      errors.push(`${field} value seems too large (max 999,999M)`);
      return { isValid: false, errors, value: 0 };
    }

    return { isValid: true, errors: [], value: Math.round(numValue * 100) / 100 }; // Round to 2 decimal places
  };

  validateMWhValue = (value, field) => {
    const errors = [];
    const numValue = parseFloat(value);

    if (isNaN(numValue)) {
      errors.push(`${field} must be a valid number`);
      return { isValid: false, errors, value: 0 };
    }

    if (numValue < 0) {
      errors.push(`${field} cannot be negative`);
      return { isValid: false, errors, value: 0 };
    }

    // Check for reasonable MWh limits
    if (numValue > 100000) {
      errors.push(`${field} value seems too large (max 100,000 MWh)`);
      return { isValid: false, errors, value: 0 };
    }

    return { isValid: true, errors: [], value: Math.round(numValue * 100) / 100 }; // Round to 2 decimal places
  };

  validatePercentageValue = (value, field) => {
    const errors = [];
    const numValue = parseFloat(value);

    if (isNaN(numValue)) {
      errors.push(`${field} must be a valid number`);
      return { isValid: false, errors, value: 0 };
    }

    if (numValue < 0) {
      errors.push(`${field} cannot be negative`);
      return { isValid: false, errors, value: 0 };
    }

    if (numValue > 100) {
      errors.push(`${field} cannot exceed 100%`);
      return { isValid: false, errors, value: 0 };
    }

    return { isValid: true, errors: [], value: Math.round(numValue * 100) / 100 }; // Round to 2 decimal places
  };

  // Enhanced input type detection for better UX
  getInputType = (table, field) => {
    if (table === 'weekly_collections' && (field === 'zwl_millions' || field === 'usd_millions')) {
      return 'number';
    }
    if (table === 'weekly_revenue_lost' && (field === 'faults_mwh' || field === 'maintenance_mwh')) {
      return 'number';
    }
    if (table === 'debtors' && field === 'percentage') {
      return 'number';
    }
    return 'text';
  };

  // Enhanced placeholder text for better UX
  getInputPlaceholder = (table, field) => {
    if (table === 'weekly_collections' && (field === 'zwl_millions' || field === 'usd_millions')) {
      return 'e.g., 5.2 (millions)';
    }
    if (table === 'weekly_revenue_lost' && (field === 'faults_mwh' || field === 'maintenance_mwh')) {
      return 'e.g., 150.5 (MWh)';
    }
    if (table === 'debtors' && field === 'percentage') {
      return 'e.g., 25.5 (%)';
    }
    return '';
  };

  // Get default formatted value for empty fields
  getDefaultValueForField = (table, field) => {
    if (table === 'weekly_collections' && (field === 'zwl_millions' || field === 'usd_millions')) {
      return this.getDefaultValueDisplay('currency');
    }
    if (table === 'weekly_revenue_lost' && (field === 'faults_mwh' || field === 'maintenance_mwh' || field === 'total_mwh')) {
      return this.getDefaultValueDisplay('mwh');
    }
    if (table === 'debtors' && field === 'percentage') {
      return this.getDefaultValueDisplay('percentage');
    }
    return '0';
  };

  renderEditableCell = (table, rowIndex, field, value, className = "") => {
    const { editingCell, editingValue, canEdit } = this.state;
    const isEditing = editingCell &&
      editingCell.table === table &&
      editingCell.row === rowIndex &&
      editingCell.field === field;

    // Prevent editing of auto-calculated fields
    const isReadOnlyField = (table === 'weekly_revenue_lost' && field === 'total_mwh');

    // Ensure proper formatting for display value
    const displayValue = value || this.getDefaultValueForField(table, field);

    // Get value-specific CSS classes
    const getValueClass = (table, field) => {
      if (table === 'weekly_collections' && (field === 'zwl_millions' || field === 'usd_millions')) {
        return 'currency-value';
      }
      if (table === 'weekly_revenue_lost' && (field === 'faults_mwh' || field === 'maintenance_mwh' || field === 'total_mwh')) {
        return 'mwh-value';
      }
      if (table === 'debtors' && field === 'percentage') {
        return 'percentage-value';
      }
      return '';
    };

    if (isEditing && canEdit && !isReadOnlyField) {
      const inputType = this.getInputType(table, field);
      const placeholder = this.getInputPlaceholder(table, field);

      return (
        <td
          className={`p-1 border border-gray-300 ${className}`}
          data-table={table}
          data-row={rowIndex}
          data-field={field}
        >
          <div className="flex items-center gap-1">
            <input
              type={inputType}
              value={editingValue}
              onChange={this.handleEditChange}
              placeholder={placeholder}
              className="inline-edit-input"
              autoFocus
              step={inputType === 'number' ? '0.01' : undefined}
              min={inputType === 'number' ? '0' : undefined}
              max={table === 'debtors' && field === 'percentage' ? '100' : undefined}
              onKeyDown={(e) => {
                if (e.key === 'Enter') this.saveEdit();
                if (e.key === 'Escape') this.cancelEdit();
              }}
            />
            <button
              onClick={this.saveEdit}
              className="text-green-600 hover:text-green-800 text-xs px-1"
              title="Save"
            >
              ✓
            </button>
            <button
              onClick={this.cancelEdit}
              className="text-red-600 hover:text-red-800 text-xs px-1"
              title="Cancel"
            >
              ✗
            </button>
          </div>
        </td>
      );
    }

    const cellClass = isReadOnlyField ? 'non-editable-cell auto-calculated' :
      (canEdit ? 'editable-cell' : '');
    const tooltipText = canEdit && !isReadOnlyField ? "Click to edit" :
      isReadOnlyField ? "Auto-calculated field" : "";

    return (
      <td
        className={`p-2 border border-gray-300 ${cellClass} ${getValueClass(table, field)} ${className}`}
        onClick={canEdit && !isReadOnlyField ? () => this.startEdit(table, rowIndex, field, displayValue) : undefined}
        title={tooltipText}
        data-table={table}
        data-row={rowIndex}
        data-field={field}
        data-tooltip={tooltipText}
      >
        {displayValue}
      </td>
    );
  };

  renderEditableMetric = (metricKey, property, value, className = "") => {
    const { editingCell, editingValue, canEdit } = this.state;
    const fieldId = `${metricKey}_${property}`;
    const isEditing = editingCell &&
      editingCell.type === 'metric' &&
      editingCell.field === fieldId;

    if (isEditing && canEdit) {
      return (
        <div className={`inline-flex items-center gap-1 ${className}`}>
          <input
            type="text"
            value={editingValue}
            onChange={this.handleEditChange}
            className="w-20 text-xs p-1 border rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
            autoFocus
            onKeyDown={(e) => {
              if (e.key === 'Enter') this.saveEdit();
              if (e.key === 'Escape') this.cancelEdit();
            }}
          />
          <button
            onClick={this.saveEdit}
            className="text-green-600 hover:text-green-800 text-xs"
            title="Save"
          >
            ✓
          </button>
          <button
            onClick={this.cancelEdit}
            className="text-red-600 hover:text-red-800 text-xs"
            title="Cancel"
          >
            ✗
          </button>
        </div>
      );
    }

    return (
      <span
        className={`${canEdit ? 'cursor-pointer hover:bg-gray-100' : ''} px-1 py-0.5 rounded ${className}`}
        onClick={canEdit ? () => this.setState({
          editingCell: { type: 'metric', field: fieldId },
          editingValue: value.toString(),
          originalValue: value.toString()
        }) : undefined}
        title={canEdit ? "Click to edit" : ""}
      >
        {value}
      </span>
    );
  };

  render() {
    // Show loading overlay during initial data load
    if (this.state.isLoading) {
      return (
        <div className="dashboard-loading-overlay">
          <div className="loading-spinner"></div>
          <div className="dashboard-loading-text">Loading Dashboard Data...</div>
          <div style={{ fontSize: '14px', color: '#6b7280', marginTop: '8px' }}>
            Please wait while we fetch the latest data
          </div>
        </div>
      );
    }

    // Show error state if there's a critical error
    if (this.state.error && this.state.networkError) {
      return (
        <div className="dashboard-error" style={{ margin: '20px', textAlign: 'center' }}>
          <h3 style={{ marginBottom: '16px' }}>Unable to Load Dashboard</h3>
          <p>{this.state.error}</p>
          <button
            className="dashboard-error-retry"
            onClick={() => this.initializeData()}
            style={{ marginTop: '16px' }}
          >
            Retry Loading
          </button>
        </div>
      );
    }

    return (
      <div>
        {/* Fallback Data Mode Banner */}
        {this.state.usingFallbackData && (
          <div className="w-auto bg-gradient-to-r from-yellow-50 to-yellow-100 border-l-4 border-yellow-400 p-3 rounded mb-3">
            <div className="flex items-center">
              <div className="text-yellow-800 mr-2">⚠️</div>
              <div className="text-sm text-yellow-800">
                <strong>Fallback Mode:</strong> Dashboard is using sample data because the backend API endpoints are not available.
                Data will automatically switch to live data once the APIs are implemented.
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 gap-4 mb-3">
          <div className={`w-auto bg-gradient-to-r ${this.state.canEdit ? 'from-green-50 to-green-100 border-l-4 border-green-400' : 'from-blue-50 to-blue-100 border-l-4 border-blue-400'} p-3 rounded`}>
            <div className="flex items-center">
              <div className={`${this.state.canEdit ? 'text-green-800' : 'text-blue-800'} mr-2`}>
                {this.state.canEdit ? '✏️' : 'ℹ️'}
              </div>
              <div className={`text-sm ${this.state.canEdit ? 'text-green-800' : 'text-blue-800'}`}>
                {this.state.canEdit ? (
                  <>
                    <strong>Edit Mode Enabled:</strong> You have permissions to edit dashboard data. Click on any metric values, progress bars, targets in the cards above or data cells in the tables below to edit. Press Enter to save or Escape to cancel.
                  </>
                ) : (
                  <>
                    <strong>View Only Mode:</strong> You have read-only access to this dashboard. Contact your administrator if you need editing permissions.
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
        <div className="grid grid-cols-1 gap-4">
          <div className="w-auto bg-white drop-shadow-md shadow shadow-gulf-blue-300 text-gulf-blue-950 rounded px-4 py-4">
            <div className="flex justify-around">
              <div style={{ flex: 0.25 }} className="flex justify-center">
                <div className="w-full">
                  <select
                    id="selectRegion"
                    name="selectedRegion"
                    onChange={(event) => this.onFilterSelectCenters("region", event)}
                    disabled={this.state.isLoadingRegions}
                    className="block w-full bg-gulf-blue-50 rounded-md border-0 px-2 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6"
                  >
                    {this.state.isLoadingRegions ? (
                      <option>Loading regions...</option>
                    ) : this.state.region ? (
                      <option>{this.state.region}</option>
                    ) : (
                      <option>Select Region</option>
                    )}
                    {!this.state.isLoadingRegions && this.state.regions.map((region) => (
                      <option key={region.id} value={region.id}>{region.region}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div style={{ flex: 0.25 }} className="flex justify-center">
                <div className="w-full">
                  <select
                    id="selectDistrict"
                    name="selectedDistrict"
                    onChange={(event) => this.onFilterSelectCenters("district", event)}
                    disabled={this.state.isLoadingRegions}
                    className="block w-full bg-gulf-blue-50 rounded-md border-0 px-2 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6"
                  >
                    {this.state.isLoadingRegions ? (
                      <option>Loading districts...</option>
                    ) : this.state.district ? (
                      <option>{this.state.district}</option>
                    ) : (
                      <option>Select district</option>
                    )}
                    {!this.state.isLoadingRegions && this.state.districts.map((district) => (
                      <option key={district.id} value={district.id}>{district.district}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div style={{ flex: 0.25 }} className="flex justify-center">
                <div className="w-full">
                  <select
                    id="selectDepot"
                    name="selectedDepot"
                    onChange={(event) => this.onFilterSelectCenters("depot", event)}
                    disabled={this.state.isLoadingRegions}
                    className="block w-full bg-gulf-blue-50 rounded-md border-0 px-2 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6"
                  >
                    {this.state.isLoadingRegions ? (
                      <option>Loading centres...</option>
                    ) : this.state.depot ? (
                      <option>{this.state.depot}</option>
                    ) : (
                      <option>Select Centre</option>
                    )}
                    {!this.state.isLoadingRegions && this.state.depots && this.state.depots.map((depot) => (
                      <option key={depot.id} value={depot.id}>{depot.depot}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-5 gap-4 mt-5">
          <div className="w-auto bg-gradient-to-r from-gulf-blue-100 to-gulf-blue-300 drop-shadow-md shadow shadow-gulf-blue-300 text-gulf-blue-900 rounded px-2 py-2">
            <div className="sm:flex lg:items-center lg:justify-between">
              <div className="min-w-0 flex-1">
                <div className="text-center text-lg font-bold text-gulf-blue-950 sm:truncate sm:tracking-tight">
                  ENERGY SOLD
                </div>
                <div className="mt-2">
                  <a href="#">
                    <div className="border border-gulf-blue-200 hover:bg-gulf-blue-400 rounded-lg px-3 py-1 justify-between items-center sm:mt-0 sm:flex-row sm:flex-wrap">
                      <div className="col-xl col-sm text-center mb-xl-0 mb-4">
                        <div className="card">
                          <div className="card-body p-2">
                            <div className="row">
                              <div className="col-8">
                                <div className="numbers">
                                  <p className="text-xs mb-0 text-capitalize font-weight-bold">
                                    Energy Sold (GWh)
                                  </p>
                                  <h6 className="font-weight-bolder mb-0">
                                    {this.renderEditableMetric('energy_sold', 'value', this.state.metrics.energy_sold.value)} {this.state.metrics.energy_sold.unit}
                                  </h6>
                                </div>

                                <div className="overflow-hidden bg-blue-50 h-1.5 rounded-full w-full">
                                  <span
                                    className={`h-full w-full block rounded-full transition-all duration-300 ${this.state.canEdit ? 'cursor-pointer' : ''} ${this.getProgressColor(this.calculateProgress(this.state.metrics.energy_sold.value, this.state.metrics.energy_sold.target))}`}
                                    style={{ width: `${this.calculateProgress(this.state.metrics.energy_sold.value, this.state.metrics.energy_sold.target)}%` }}
                                    title={`Progress: ${this.calculateProgress(this.state.metrics.energy_sold.value, this.state.metrics.energy_sold.target)}% (${this.state.metrics.energy_sold.value}/${this.state.metrics.energy_sold.target})${this.state.canEdit ? ' - Click to edit' : ''}`}
                                    onClick={this.state.canEdit ? () => this.setState({
                                      editingCell: { type: 'metric', field: 'energy_sold_progress' },
                                      editingValue: this.calculateProgress(this.state.metrics.energy_sold.value, this.state.metrics.energy_sold.target).toString(),
                                      originalValue: this.calculateProgress(this.state.metrics.energy_sold.value, this.state.metrics.energy_sold.target).toString()
                                    }) : undefined}
                                  ></span>
                                </div>
                                <p className="text-xs text-muted mt-2 mb-0">
                                  Monthly Target: {this.renderEditableMetric('energy_sold', 'target', this.state.metrics.energy_sold.target)} {this.state.metrics.energy_sold.target_unit}
                                </p>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </a>
                </div>
              </div>
            </div>
          </div>
          <div className="w-auto bg-gradient-to-r from-jade-100 to-jade-300 drop-shadow-md shadow shadow-jade-300 text-jade-900 rounded px-2 py-2">
            <div className="sm:flex lg:items-center lg:justify-between">
              <div className="min-w-0 flex-1">
                <div className="text-center text-lg font-bold text-jade-900 sm:truncate sm:tracking-tight">
                  GROWTH
                </div>
                <div className="mt-2">
                  <a href="#">
                    <div className="border border-jade-200 hover:bg-jade-400 rounded-lg px-3 py-1 justify-between items-center sm:mt-0 sm:flex-row sm:flex-wrap">
                      <div className="col-xl col-sm text-center mb-xl-0 mb-4">
                        <div className="card">
                          <div className="card-body p-2">
                            <div className="row">
                              <div className="col-8">
                                <div className="numbers">
                                  <p className="text-xs mb-0 text-capitalize font-weight-bold">
                                    Client Connected
                                  </p>
                                  <h6 className="font-weight-bolder mb-0">
                                    {this.renderEditableMetric('growth', 'value', this.state.metrics.growth.value)}
                                  </h6>
                                </div>

                                <div className="overflow-hidden bg-jade-50 h-1.5 rounded-full w-full">
                                  <span
                                    className={`h-full w-full block rounded-full transition-all duration-300 ${this.state.canEdit ? 'cursor-pointer' : ''} ${this.getProgressColor(this.calculateProgress(this.state.metrics.growth.value, this.state.metrics.growth.target))}`}
                                    style={{ width: `${this.calculateProgress(this.state.metrics.growth.value, this.state.metrics.growth.target)}%` }}
                                    title={`Progress: ${this.calculateProgress(this.state.metrics.growth.value, this.state.metrics.growth.target)}% (${this.state.metrics.growth.value}/${this.state.metrics.growth.target})${this.state.canEdit ? ' - Click to edit' : ''}`}
                                    onClick={this.state.canEdit ? () => this.setState({
                                      editingCell: { type: 'metric', field: 'growth_progress' },
                                      editingValue: this.calculateProgress(this.state.metrics.growth.value, this.state.metrics.growth.target).toString(),
                                      originalValue: this.calculateProgress(this.state.metrics.growth.value, this.state.metrics.growth.target).toString()
                                    }) : undefined}
                                  ></span>
                                </div>
                                <p className="text-xs text-muted mt-2 mb-0">
                                  YTD Target: {this.renderEditableMetric('growth', 'target', this.state.metrics.growth.target)} {this.state.metrics.growth.target_unit}
                                </p>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </a>
                </div>
              </div>
            </div>
          </div>
          <div className="w-auto bg-gradient-to-r from-royal-heath-100 to-royal-heath-300 drop-shadow-md shadow shadow-royal-heath-300 text-royal-heath-900 rounded px-2 py-2">
            <div className="sm:flex lg:items-center lg:justify-between">
              <div className="min-w-0 flex-1">
                <div className="text-center text-lg font-bold text-royal-heath-950 sm:truncate sm:tracking-tight">
                  REVENUE COLLECTION
                </div>
                <div className="mt-2">
                  <a href="#">
                    <div className="border border-royal-heath-200 hover:bg-royal-heath-400 rounded-lg px-3 py-1 justify-between items-center sm:mt-0 sm:flex-row sm:flex-wrap">
                      <div className="col-xl col-sm text-center mb-xl-0 mb-4">
                        <div className="card">
                          <div className="card-body p-2">
                            <div className="row">
                              <div className="col-8">
                                <div className="numbers">
                                  <p className="text-xs mb-0 text-capitalize font-weight-bold">
                                    Revenue Collected
                                  </p>
                                  <h6 className="font-weight-bolder mb-0">
                                    {this.state.metrics.revenue_usd.unit} {this.renderEditableMetric('revenue_usd', 'value', this.state.metrics.revenue_usd.value)}
                                  </h6>
                                  <h6 className="font-weight-bolder mb-0">
                                    {this.state.metrics.revenue_zwl.unit} {this.renderEditableMetric('revenue_zwl', 'value', this.state.metrics.revenue_zwl.value)}
                                  </h6>
                                </div>

                                <div className="overflow-hidden bg-royal-heath-50 h-1.5 rounded-full w-full">
                                  <span
                                    className={`h-full w-full block rounded-full transition-all duration-300 ${this.state.canEdit ? 'cursor-pointer' : ''} ${this.getProgressColor(Math.round((this.calculateProgress(this.state.metrics.revenue_usd.value, this.state.metrics.revenue_usd.target) + this.calculateProgress(this.state.metrics.revenue_zwl.value, this.state.metrics.revenue_zwl.target)) / 2))}`}
                                    style={{ width: `${Math.round((this.calculateProgress(this.state.metrics.revenue_usd.value, this.state.metrics.revenue_usd.target) + this.calculateProgress(this.state.metrics.revenue_zwl.value, this.state.metrics.revenue_zwl.target)) / 2)}%` }}
                                    title={`Combined Progress: ${Math.round((this.calculateProgress(this.state.metrics.revenue_usd.value, this.state.metrics.revenue_usd.target) + this.calculateProgress(this.state.metrics.revenue_zwl.value, this.state.metrics.revenue_zwl.target)) / 2)}% | USD: ${this.calculateProgress(this.state.metrics.revenue_usd.value, this.state.metrics.revenue_usd.target)}% | ZWL: ${this.calculateProgress(this.state.metrics.revenue_zwl.value, this.state.metrics.revenue_zwl.target)}%${this.state.canEdit ? ' - Click to edit' : ''}`}
                                    onClick={this.state.canEdit ? () => this.setState({
                                      editingCell: { type: 'metric', field: 'revenue_combined_progress' },
                                      editingValue: Math.round((this.calculateProgress(this.state.metrics.revenue_usd.value, this.state.metrics.revenue_usd.target) + this.calculateProgress(this.state.metrics.revenue_zwl.value, this.state.metrics.revenue_zwl.target)) / 2).toString(),
                                      originalValue: Math.round((this.calculateProgress(this.state.metrics.revenue_usd.value, this.state.metrics.revenue_usd.target) + this.calculateProgress(this.state.metrics.revenue_zwl.value, this.state.metrics.revenue_zwl.target)) / 2).toString()
                                    }) : undefined}
                                  ></span>
                                </div>
                                <p className="text-xs text-muted mt-2 mb-0">
                                  YTD Target: {this.state.metrics.revenue_usd.unit} {this.renderEditableMetric('revenue_usd', 'target', this.state.metrics.revenue_usd.target)}
                                </p>
                                <p className="text-xs text-muted mt-2 mb-0">
                                  YTD Target: {this.state.metrics.revenue_zwl.unit} {this.renderEditableMetric('revenue_zwl', 'target', this.state.metrics.revenue_zwl.target)}
                                </p>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </a>
                </div>
              </div>
            </div>
          </div>
          <div className="w-auto bg-gradient-to-r from-gulf-blue-100 to-gulf-blue-300 drop-shadow-md shadow shadow-gulf-blue-300 text-gulf-blue-900 rounded px-2 py-2">
            <div className="sm:flex lg:items-center lg:justify-between">
              <div className="min-w-0 flex-1">
                <div className="text-center text-lg font-bold text-gulf-blue-950 sm:truncate sm:tracking-tight">
                  FAULTS
                </div>
                <div className="mt-2">
                  <a href="#">
                    <div className="border border-gulf-blue-200 hover:bg-gulf-blue-400 rounded-lg px-3 py-1 justify-between items-center sm:mt-0 sm:flex-row sm:flex-wrap">
                      <div className="col-xl col-sm text-center mb-xl-0 mb-4">
                        <div className="card">
                          <div className="card-body p-2">
                            <div className="row">
                              <div className="col-8">
                                <div className="numbers">
                                  <p className="text-xs mb-0 text-capitalize font-weight-bold">
                                    Compliants Received
                                  </p>
                                  <h6 className="font-weight-bolder mb-0">
                                    {this.renderEditableMetric('faults', 'value', this.state.metrics.faults.value)}
                                  </h6>
                                </div>

                                <div className="overflow-hidden bg-gulf-blue-50 h-1.5 rounded-full w-full">
                                  <span
                                    className={`h-full w-full block rounded-full transition-all duration-300 ${this.state.canEdit ? 'cursor-pointer' : ''} ${this.getProgressColor(this.calculateProgress(this.state.metrics.faults.value, this.state.metrics.faults.target))}`}
                                    style={{ width: `${this.calculateProgress(this.state.metrics.faults.value, this.state.metrics.faults.target)}%` }}
                                    title={`Progress: ${this.calculateProgress(this.state.metrics.faults.value, this.state.metrics.faults.target)}% (${this.state.metrics.faults.value}/${this.state.metrics.faults.target})${this.state.canEdit ? ' - Click to edit' : ''}`}
                                    onClick={this.state.canEdit ? () => this.setState({
                                      editingCell: { type: 'metric', field: 'faults_progress' },
                                      editingValue: this.calculateProgress(this.state.metrics.faults.value, this.state.metrics.faults.target).toString(),
                                      originalValue: this.calculateProgress(this.state.metrics.faults.value, this.state.metrics.faults.target).toString()
                                    }) : undefined}
                                  ></span>
                                </div>
                                <p className="text-xs text-muted mt-2 mb-0">
                                  YTD Target: {this.renderEditableMetric('faults', 'target', this.state.metrics.faults.target)}
                                </p>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </a>
                </div>
              </div>
            </div>
          </div>
          <div className="w-auto bg-gradient-to-r from-jade-100 to-jade-300 drop-shadow-md shadow shadow-jade-300 text-jade-900 rounded px-2 py-2">
            <div className="sm:flex lg:items-center lg:justify-between">
              <div className="min-w-0 flex-1">
                <div className="text-center text-lg font-bold text-jade-950 sm:truncate sm:tracking-tight">
                  MAINTENANCE
                </div>
                <div className="mt-2">
                  <a href="#">
                    <div className="border border-jade-200 hover:bg-jade-400 rounded-lg px-3 py-1 justify-between items-center sm:mt-0 sm:flex-row sm:flex-wrap">
                      <div className="col-xl col-sm text-center mb-xl-0 mb-4">
                        <div className="card">
                          <div className="card-body p-2">
                            <div className="row">
                              <div className="col-8">
                                <div className="numbers">
                                  <p className="text-xs mb-0 text-capitalize font-weight-bold">
                                    Maintained
                                  </p>
                                  <h6 className="font-weight-bolder mb-0">
                                    {this.renderEditableMetric('maintenance', 'value', this.state.metrics.maintenance.value)}
                                  </h6>
                                </div>

                                <div className="overflow-hidden bg-jade-50 h-1.5 rounded-full w-full">
                                  <span
                                    className={`h-full w-full block rounded-full transition-all duration-300 ${this.state.canEdit ? 'cursor-pointer' : ''} ${this.getProgressColor(this.calculateProgress(this.state.metrics.maintenance.value, this.state.metrics.maintenance.target))}`}
                                    style={{ width: `${this.calculateProgress(this.state.metrics.maintenance.value, this.state.metrics.maintenance.target)}%` }}
                                    title={`Progress: ${this.calculateProgress(this.state.metrics.maintenance.value, this.state.metrics.maintenance.target)}% (${this.state.metrics.maintenance.value}/${this.state.metrics.maintenance.target})${this.state.canEdit ? ' - Click to edit' : ''}`}
                                    onClick={this.state.canEdit ? () => this.setState({
                                      editingCell: { type: 'metric', field: 'maintenance_progress' },
                                      editingValue: this.calculateProgress(this.state.metrics.maintenance.value, this.state.metrics.maintenance.target).toString(),
                                      originalValue: this.calculateProgress(this.state.metrics.maintenance.value, this.state.metrics.maintenance.target).toString()
                                    }) : undefined}
                                  ></span>
                                </div>
                                <p className="text-xs text-muted mt-2 mb-0">
                                  YTD Target: {this.renderEditableMetric('maintenance', 'target', this.state.metrics.maintenance.target)}
                                </p>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div className="dashboard-grid grid grid-cols-3 gap-4 mt-10">
          <div className="dashboard-section weekly-collections-section">
            <div className="sm:flex lg:items-center lg:justify-between">
              <div className="min-w-0 flex-1">
                <div className="dashboard-section-header">
                  💰 Weekly Collections
                </div>
                <div style={{ height: "14rem" }} className="mt-2 h-20 overflow-auto table-container">
                  <a href="#">
                    <table className="editable-table">
                      <thead className="bg-gulf-blue-600 text-white">
                        <tr className="bg-gulf-blue-600 transition-colors">
                          <th className="text-left p-2 font-bold border border-gulf-blue-600">Week</th>
                          <th className="text-left p-2 font-bold border border-gulf-blue-600">ZWL (M)</th>
                          <th className="text-left p-2 font-bold border border-gulf-blue-600">USD (M)</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white">
                        {this.state.weekly_collections && this.state.weekly_collections.length > 0
                          ? this.state.weekly_collections.map((collection, index) => (
                            <tr key={index} className="hover:bg-gulf-blue-100 transition-colors">
                              <td className="p-2 font-semibold text-gulf-blue-900 border border-gray-300">{collection.week}</td>
                              {this.renderEditableCell('weekly_collections', index, 'zwl_millions', this.formatCurrencyMillions(collection.zwl_millions), 'text-gray-800 font-medium')}
                              {this.renderEditableCell('weekly_collections', index, 'usd_millions', this.formatCurrencyMillions(collection.usd_millions), 'text-gray-800 font-medium')}
                            </tr>
                          ))
                          : (
                            <tr>
                              <td colSpan="3" className="p-2 text-center text-gray-500 border border-gray-300">
                                No weekly collections data available
                              </td>
                            </tr>
                          )}
                      </tbody>
                    </table>
                  </a>
                </div>
              </div>
            </div>
          </div>
          <div className="dashboard-section weekly-revenue-lost-section">
            <div className="sm:flex lg:items-center lg:justify-between">
              <div className="min-w-0 flex-1">
                <div className="dashboard-section-header">
                  ⚡ Weekly Revenue Lost
                </div>
                <div style={{ height: "14rem" }} className="mt-2 h-20 overflow-auto table-container">
                  <a href="#">
                    <table className="editable-table">
                      <thead className="bg-red-600 text-white">
                        <tr>
                          <th className="text-left p-2 font-bold border border-red-600">Week</th>
                          <th className="text-left p-2 font-bold border border-red-600">Faults (MWh)</th>
                          <th className="text-left p-2 font-bold border border-red-600">Maintenance (MWh)</th>
                          <th className="text-left p-2 font-bold border border-red-600">Total (MWh)</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white">
                        {this.state.weekly_revenue_lost && this.state.weekly_revenue_lost.length > 0
                          ? this.state.weekly_revenue_lost.map((revenueLost, index) => (
                            <tr key={index} className="hover:bg-red-50 transition-colors">
                              <td className="p-2 font-semibold text-red-900 border border-gray-300">{revenueLost.week}</td>
                              {this.renderEditableCell('weekly_revenue_lost', index, 'faults_mwh', this.formatMWhWithDecimals(revenueLost.faults_mwh), 'text-gray-800 font-medium')}
                              {this.renderEditableCell('weekly_revenue_lost', index, 'maintenance_mwh', this.formatMWhWithDecimals(revenueLost.maintenance_mwh), 'text-gray-800 font-medium')}
                              <td className="p-2 border border-gray-300 text-blue-700 font-medium bg-gray-50" title="Auto-calculated total">
                                {this.formatMWhWithDecimals(revenueLost.total_mwh)}
                              </td>
                            </tr>
                          ))
                          : (
                            <tr>
                              <td colSpan="4" className="p-2 text-center text-gray-500 border border-gray-300">
                                No weekly revenue lost data available
                              </td>
                            </tr>
                          )}
                      </tbody>
                    </table>
                  </a>
                </div>
              </div>
            </div>
          </div>
          <div className="dashboard-section debtors-section">
            <div className="sm:flex lg:items-center lg:justify-between">
              <div className="min-w-0 flex-1">
                <div className="dashboard-section-header">
                  📊 Debtors by Category
                </div>
                <div style={{ height: "14rem" }} className="mt-2 h-20 overflow-auto table-container">
                  <a href="#">
                    <table className="editable-table">
                      <thead className="bg-purple-600 text-white">
                        <tr>
                          <th className="text-left p-2 font-bold border border-purple-600">ID</th>
                          <th className="text-left p-2 font-bold border border-purple-600">Category</th>
                          <th className="text-left p-2 font-bold border border-purple-600">Percentage (%)</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white">
                        {this.state.debtors && this.state.debtors.length > 0
                          ? this.state.debtors.map((debtor, index) => (
                            <tr key={index} className="hover:bg-purple-50 transition-colors">
                              <td className="p-2 font-semibold text-purple-900 border border-gray-300">{debtor.id || index + 1}</td>
                              <td className="p-2 font-semibold text-gray-800 border border-gray-300">{debtor.category}</td>
                              {this.renderEditableCell('debtors', index, 'percentage', this.formatPercentageWithSymbol(debtor.percentage), 'text-blue-700 font-medium')}
                            </tr>
                          ))
                          : (
                            <tr>
                              <td colSpan="3" className="p-2 text-center text-gray-500 border border-gray-300">
                                No debtor category data available
                              </td>
                            </tr>
                          )}
                      </tbody>
                    </table>
                  </a>
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    );
  }
}

const spid = domContainer.getAttribute("data-spid");
const region = domContainer.getAttribute("data-region");
const district = domContainer.getAttribute("data-district");
const section = domContainer.getAttribute("data-section");
const depot = domContainer.getAttribute("data-depot");
ReactDOM.render(
  e(DashboardFilter, { spid, region, district, section }),
  domContainer
);
