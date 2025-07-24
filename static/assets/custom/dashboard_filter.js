"use strict";

const e = React.createElement;
const domContainer = document.querySelector("#dashboard_filters");
const url = domContainer.getAttribute("data-baseurl");
// const BASE_URL = "http://localhost:8000";
const BASE_URL = url;
class DashboardFilter extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
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
      pbncs: [],
      weekly_sales: [],
      upos: [],
      weekly_outages: [],
      tds: [],
      weekly_faults_maintenance: [],
      current_month: "",
      maintenance: [],
      inspections: [],
      inspection_locations: [],
      inspections_count: [],
      maintenance_locations: [],
      maintenance_count: [],
      mnt: {},
      selectedRegion: "",
      selectedDistrict: "",
      selectedSection: "",
      authUser: {},
      // Metric cards data (will be loaded from API)
      metrics: {
        energy_sold: {
          value: "0",
          unit: "GWh",
          target: "0",
          target_unit: "GWh",
          progress: 0
        },
        growth: {
          value: "0",
          unit: "Clients",
          target: "0",
          target_unit: "Clients",
          progress: 0
        },
        revenue_usd: {
          value: "0",
          unit: "USD",
          target: "0",
          target_unit: "USD",
          progress: 0
        },
        revenue_zwl: {
          value: "0",
          unit: "ZWL",
          target: "0",
          target_unit: "ZWL",
          progress: 0
        },
        faults: {
          value: "0",
          unit: "Complaints",
          target: "0",
          target_unit: "",
          progress: 0
        },
        maintenance: {
          value: "0",
          unit: "Maintained",
          target: "0",
          target_unit: "",
          progress: 0
        }
      },
      // User permissions
      canEdit: false,
      userRoles: [],
      // Editing state
      editingCell: null,
      // {table: 'weekly_sales', row: 0, field: 'zwl'} or {type: 'metric', field: 'energy_sold_value'}
      editingValue: "",
      originalValue: ""
    };
    this.inspectionPieChartRef = React.createRef();
    this.inspectionBarChartRef = React.createRef();
    this.mmtPieChartRef = React.createRef();
    this.mmtBarChartRef = React.createRef();
    this.onFilterSelectCenters = this.onFilterSelectCenters.bind(this);
    this.inspectionChart = null;
    this.inspectionBarChart = null;
    this.mmtPieChart = null;
    this.mmtBarChart = null;
  }
  componentDidMount() {
    this.setState({
      region: this.props.region,
      district: this.props.district,
      section: this.props.section,
      depot: this.props.depot
    });
    this.getRegions();
    this.getDashboardData();
    this.getUserPermissions();
  }
  getUserPermissions = () => {
    fetch(`${BASE_URL}/dashboards/user_permissions`).then(response => response.json()).then(data => {
      console.log("User permissions data: ", data);
      this.setState({
        canEdit: data.canEdit || false,
        userRoles: data.userRoles || [],
        authUser: data.user || {}
      });
    }).catch(error => {
      console.error("Error loading user permissions:", error);
      this.setState({
        canEdit: false,
        userRoles: [],
        authUser: {}
      });
    });
  };
  onFilterSelectCenters(name_, event) {
    let {
      name,
      value
    } = event.target;
    if (name_ === "region") {
      let dist = this.state.allDistricts.filter(_district => _district.region_id === value);
      this.setState({
        districts: dist,
        selectedRegion: value,
        selectedDepot: "",
        selectedDistrict: ""
      });
      this.getFilterData(value, "", "");
    } else if (name_ === "district") {
      console.log("district: ", value, this.state.allDepots);
      let depos = this.state.allDepots.filter(_depot => parseInt(_depot.district_id) === parseInt(value));
      console.log("depots: ", depos);
      this.setState({
        depots: depos,
        selectedDepot: "",
        selectedDistrict: value,
        selectedRegion: ""
      });
      this.getFilterData("", value, "");
    } else if (name_ === "depot") {
      console.log("depot: ", value);
      this.setState({
        selectedDepot: value,
        selectedDistrict: "",
        selectedRegion: ""
      });
      this.getFilterData("", "", value);
    }

    // Filter by depot, filter by month, filter combined
  }
  getFilterData = (selectedRegion, selectedDistrict, selectedDepot) => {
    fetch(`${BASE_URL}/dashboards/dashboard_filter`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": this.getCookie("csrftoken")
      },
      body: JSON.stringify({
        region: selectedRegion,
        district: selectedDistrict,
        depot: selectedDepot
      })
    }).then(response => response.json()).then(data => {
      console.log("data: ", data);
      if (data) {
        console.log("running ...");
        let inspection_locations_, inspections_count_, maintenance_locations_, maintenance_count_, mtn_;
        try {
          inspection_locations_ = JSON.parse(data.inspection_locations);
        } catch (error) {
          console.error("Error parsing inspection_locations:", error);
          inspection_locations_ = []; // Set to empty array on error
        }
        try {
          inspections_count_ = JSON.parse(data.inspections_count);
        } catch (error) {
          console.error("Error parsing inspections_count_:", error);
          inspections_count_ = []; // Set to empty array on error
        }
        try {
          maintenance_locations_ = JSON.parse(data.maintenance_locations);
        } catch (error) {
          console.error("Error parsing maintenance_locations_:", error);
          maintenance_locations_ = []; // Set to empty array on error
        }
        try {
          maintenance_count_ = JSON.parse(data.maintenance_count);
        } catch (error) {
          console.error("Error parsing maintenance_count_:", error);
          maintenance_count_ = []; // Set to empty array on error
        }
        try {
          mtn_ = data.mtn;
        } catch (error) {
          console.error("Error parsing mtn_:", error);
          mtn_ = {}; // Set to empty dict on error
        }
        this.setState({
          inspection_locations: inspection_locations_,
          inspections_count: inspections_count_,
          maintenance_locations: maintenance_locations_,
          maintenance_count: maintenance_count_,
          mnt: mtn_,
          pbncs: data.pbncs || [],
          weekly_sales: data.weekly_sales || [],
          upos: data.upos || [],
          weekly_outages: data.weekly_outages || [],
          tds: data.tds || [],
          weekly_faults_maintenance: data.weekly_faults_maintenance || []
        });
        this.initComponents();
      }
    });
  };
  initComponents = () => {
    const baseColors = ["#f62c06", "#94834b", "#1288fe", "#c8a806", "#f02e0e", "#e118d5", "#0fb11c", "#3b3cf0", "#188350", "#c93986", "#90921e"];
    // Destroy the previous Chart instance, if it exists
    if (this.inspectionChart) {
      this.inspectionChart.destroy();
    }
    if (this.inspectionBarChart) {
      this.inspectionBarChart.destroy();
    }
    if (this.mmtPieChart) {
      this.mmtPieChart.destroy();
    }
    if (this.mmtBarChart) {
      this.mmtBarChart.destroy();
    }
    var inspectionData = {
      labels: this.state.inspection_locations,
      datasets: [{
        data: this.state.inspections_count,
        backgroundColor: baseColors,
        hoverBackgroundColor: baseColors
      }]
    };
    this.inspectionChart = new Chart(this.inspectionPieChartRef.current, {
      type: "pie",
      data: inspectionData,
      options: {
        plugins: {
          legend: {
            position: "left" // or 'bottom', 'left', 'right'
          }
        }
      }
    });
    var inspectionBarData = {
      labels: this.state.inspection_locations,
      datasets: [{
        data: this.state.inspections_count,
        backgroundColor: baseColors,
        hoverBackgroundColor: baseColors
      }]
    };
    this.inspectionBarChart = new Chart(this.inspectionBarChartRef.current, {
      type: "bar",
      data: inspectionBarData,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false
          }
        },
        scales: {
          y: {
            display: true,
            title: {
              display: true,
              text: "Frequency"
            },
            grid: {
              drawBorder: false,
              display: true,
              drawOnChartArea: true,
              drawTicks: false
            },
            ticks: {
              suggestedMin: 0,
              suggestedMax: 40,
              beginAtZero: true,
              padding: 15,
              font: {
                size: 14,
                family: "Open Sans",
                style: "normal",
                lineHeight: 2
              },
              color: "#282a87"
            }
          },
          x: {
            grid: {
              drawBorder: false,
              display: false,
              drawOnChartArea: false,
              drawTicks: false
            },
            ticks: {
              suggestedMin: 0,
              suggestedMax: 40,
              beginAtZero: true,
              padding: 15,
              font: {
                size: 14,
                family: "Open Sans",
                style: "normal",
                lineHeight: 2
              },
              color: "#282a87"
            }
          }
        }
      }
    });

    // Define the data for the pie chart (replace with your own data)
    var maintenanceData = {
      labels: this.state.maintenance_locations,
      datasets: [{
        data: this.state.maintenance_count,
        backgroundColor: baseColors,
        hoverBackgroundColor: baseColors
      }]
    };

    // Create the pie chart
    this.mmtPieChart = new Chart(this.mmtPieChartRef.current, {
      type: "pie",
      data: maintenanceData,
      options: {
        plugins: {
          legend: {
            position: "left" // or 'bottom', 'left', 'right'
          }
        }
      }
    });
    var mnt = this.state.mnt;
    let maintenanceDataset = [];
    Object.keys(mnt).forEach(key => {
      maintenanceDataset.push({
        label: key,
        data: mnt[key],
        // [1,2,3,4]
        fill: 2
      });
    });
    var maintenanceBarData = {
      labels: ["1", "2", "3", "4"],
      // ['January', 'December'],
      datasets: maintenanceDataset.map(data => {
        return {
          label: data.label,
          data: data.data,
          fill: 2
        };
      })
    };
    this.mmtBarChart = new Chart(this.mmtBarChartRef.current, {
      type: "line",
      data: maintenanceBarData,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true
          },
          filler: {
            propagate: false
          },
          "samples-filler-analyser": {
            target: "chart-analyser"
          }
        },
        scales: {
          y: {
            display: true,
            title: {
              display: true,
              text: "Frequency"
            },
            grid: {
              drawBorder: false,
              display: true,
              drawOnChartArea: true,
              drawTicks: false,
              borderDash: [5, 5]
            },
            ticks: {
              display: true,
              padding: 10,
              color: "#282a87",
              font: {
                size: 14,
                family: "Open Sans",
                style: "normal",
                lineHeight: 2
              }
            }
          },
          x: {
            display: true,
            title: {
              display: true,
              text: "Week"
            },
            grid: {
              drawBorder: false,
              display: false,
              drawOnChartArea: false,
              drawTicks: false,
              borderDash: [5, 5]
            },
            ticks: {
              display: true,
              color: "#282a87",
              padding: 20,
              font: {
                size: 14,
                family: "Open Sans",
                style: "normal",
                lineHeight: 2
              }
            }
          }
        }
      }
    });

    // var regions = this.state.regions;
    // var centers = this.state.districts;
    // var sections = this.state.sections;
    // const selectDistrict = document.getElementById("selectDistrict");
    // const submitDistrictForm = document.getElementById("submitDistrictForm");

    // // Add event listener to the select element
    // selectDistrict.addEventListener("change", function () {
    //   // Submit the form
    //   submitDistrictForm.submit();
    // });

    // // Get the select element and form
    // const selectRegion = document.getElementById("selectRegion");
    // const submitRegionForm = document.getElementById("submitRegionForm");

    // // Add event listener to the select element
    // selectRegion.addEventListener("change", function () {
    //   // Submit the form
    //   submitRegionForm.submit();
    // });
  };
  onMaintenanceMonthSelected(event) {
    event => {
      const newValue = event; //event.target.value;

      getThisMonthData(newValue);
    };
  }
  getThisMonthData(month) {
    // Create an XMLHttpRequest object
    const xhr = new XMLHttpRequest();
    res = {};
    const csrfToken = document.getElementById("selectInspForm").value;
    console.log("csrfToken: ", csrfToken);

    // Set up the request
    xhr.open("GET", `${BASE_URL}/dashboards/ajax?month=${month}`); // Replace with your actual URL and parameters

    xhr.setRequestHeader("X-CSRFToken", csrfToken);
    // Handle the response
    xhr.onload = function () {
      if (xhr.status === 200) {
        const responseData = xhr.responseText;
        res = JSON.parse(responseData);
        console.log("responsible data: ", responseData);
        // Clear existing data
        mChart.data.datasets = [];

        // Add new datasets
        Object.keys(res).forEach(key => {
          mChart.data.datasets.push({
            label: key,
            data: res[key]
          });
        });
        mChart.update(); // Render the chart with filtered data
      } else {
        console.error("Request failed with status:", xhr.status);
      }
    };

    // Send the request
    xhr.send();
    return res;
  }
  onInspectionMonthSelected(event) {
    const newValue = event; //event.target.value;

    getInspectionsMonthData(newValue);
  }
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
  getInspectionsMonthData(month) {
    // Create an XMLHttpRequest object
    const xhr = new XMLHttpRequest();
    res = {};
    const csrfToken = getCookie("csrf_token");
    console.log("csrfToken: ", csrfToken);
    // Set up the request
    xhr.open("GET", `${BASE_URL}/dashboards/inspections/ajax?month=${month}`); // Replace with your actual URL and parameters
    xhr.setRequestHeader("X-CSRFToken", csrfToken);

    // Handle the response
    xhr.onload = function () {
      if (xhr.status === 200) {
        const responseData = xhr.responseText;
        res = JSON.parse(responseData);
        let keysList = JSON.parse(res.keys_list);
        let valuesList = JSON.parse(res.values_list);
        console.log("responsible data: ", res, keysList, valuesList);
        // Clear existing data
        iChart.data.datasets = [];
        iChart.data.datasets.push({
          label: keysList,
          data: valuesList
        });
        iChart.update(); // Render the chart with filtered data
      } else {
        console.error("Request failed with status:", xhr.status);
      }
    };

    // Send the request
    xhr.send();
    return res;
  }

  // get service branch
  getRegions = () => {
    fetch(`${BASE_URL}/dashboards/regions`).then(response => response.json()).then(data => {
      console.log(data);
      this.setState({
        allRegions: data.regions,
        allDistricts: data.districts,
        allSections: data.sections,
        allDepots: data.depots,
        regions: data.regions,
        districts: data.districts,
        sections: data.sections,
        depots: data.depots,
        pbncs: data.pbncs || [],
        weekly_sales: data.weekly_sales || [],
        upos: data.upos || [],
        weekly_outages: data.weekly_outages || [],
        tds: data.tds || [],
        weekly_faults_maintenance: data.weekly_faults_maintenance || []
      });
    }).catch(error => {
      console.error("Error loading regions data:", error);
    });
  };
  getDashboardData = () => {
    fetch(`${BASE_URL}/dashboards/dashboard_data`).then(response => response.json()).then(data => {
      console.log("data: ", data);
      let inspection_locations_ = JSON.parse(data.inspection_locations);
      let inspections_count_ = JSON.parse(data.inspections_count);
      let maintenance_locations_ = JSON.parse(data.maintenance_locations);
      let maintenance_count_ = JSON.parse(data.maintenance_count);
      let mtn_ = data.mtn;

      // Update metrics if provided
      let updatedMetrics = this.state.metrics;
      if (data.metrics) {
        updatedMetrics = {
          ...this.state.metrics,
          ...data.metrics
        };
      }
      this.setState({
        inspection_locations: inspection_locations_,
        inspections_count: inspections_count_,
        maintenance_locations: maintenance_locations_,
        maintenance_count: maintenance_count_,
        mnt: mtn_,
        metrics: updatedMetrics,
        pbncs: data.pbncs || [],
        weekly_sales: data.weekly_sales || [],
        upos: data.upos || [],
        weekly_outages: data.weekly_outages || [],
        tds: data.tds || [],
        weekly_faults_maintenance: data.weekly_faults_maintenance || []
      });
      this.initComponents();
    }).catch(error => {
      console.error("Error loading dashboard data:", error);
    });
  };
  onServiceSelected = event => {
    console.log(event);
    const {
      name,
      checked
    } = event.target;
    this.setState({
      form: {
        ...this.state.form,
        services: {
          ...this.state.form.services,
          [name]: checked
        }
      }
    });
  };
  onInputChange = event => {
    console.log(event);
    const {
      name,
      value
    } = event.target;
    this.setState({
      form: {
        ...this.state.form,
        [name]: value
      }
    });
  };

  // Helper function to calculate progress percentage
  calculateProgress = (value, target) => {
    const numValue = parseFloat(value) || 0;
    const numTarget = parseFloat(target) || 0;
    if (numTarget <= 0) return 0;
    const progress = Math.round(numValue / numTarget * 100);
    return Math.min(progress, 100); // Cap at 100%
  };

  // Helper function to get progress bar color based on percentage
  getProgressColor = progress => {
    if (progress >= 90) return 'bg-green-600'; // Excellent - Green
    if (progress >= 75) return 'bg-blue-600'; // Good - Blue
    if (progress >= 50) return 'bg-yellow-600'; // Fair - Yellow
    if (progress >= 25) return 'bg-orange-600'; // Poor - Orange
    return 'bg-red-600'; // Very Poor - Red
  };

  // Editing functionality
  startEdit = (table, rowIndex, field, currentValue) => {
    this.setState({
      editingCell: {
        table,
        row: rowIndex,
        field
      },
      editingValue: currentValue,
      originalValue: currentValue
    });
  };
  cancelEdit = () => {
    this.setState({
      editingCell: null,
      editingValue: "",
      originalValue: ""
    });
  };
  handleEditChange = event => {
    this.setState({
      editingValue: event.target.value
    });
  };
  saveEdit = () => {
    const {
      editingCell,
      editingValue
    } = this.state;
    if (!editingCell) return;
    if (editingCell.type === 'metric') {
      // Handle metric editing
      const {
        field
      } = editingCell;
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
          updatedMetrics[metricKey].progress = Math.round(value / target * 100);
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
      // Handle table editing
      const {
        table,
        row,
        field
      } = editingCell;
      const updatedData = [...this.state[table]];

      // Convert numeric fields appropriately
      let valueToSave = editingValue;
      if (field === 'outages' || field === 'resolved' || field === 'pending' || field === 'faults' || field === 'maintenance' || field === 'completed') {
        valueToSave = parseInt(editingValue) || 0;
      }
      updatedData[row][field] = valueToSave;
      this.setState({
        [table]: updatedData,
        editingCell: null,
        editingValue: "",
        originalValue: ""
      });
      this.saveChangesToServer(table, row, field, valueToSave);
      console.log(`Saved ${table}[${row}].${field} = ${valueToSave}`);
    }
  };
  saveChangesToServer = (table, row, field, value) => {
    fetch(`${BASE_URL}/dashboards/save_dashboard_data`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": this.getCookie("csrftoken")
      },
      body: JSON.stringify({
        table: table,
        row: row,
        field: field,
        value: value,
        timestamp: new Date().toISOString()
      })
    }).then(response => response.json()).then(data => {
      if (data.success) {
        console.log("Changes saved successfully");
      } else {
        console.error("Failed to save changes:", data.error);
        // Optionally revert the changes on failure
      }
    }).catch(error => {
      console.error("Error saving changes:", error);
      // Optionally revert the changes on error
    });
  };
  renderEditableCell = (table, rowIndex, field, value, className = "") => {
    const {
      editingCell,
      editingValue,
      canEdit
    } = this.state;
    const isEditing = editingCell && editingCell.table === table && editingCell.row === rowIndex && editingCell.field === field;
    if (isEditing && canEdit) {
      return /*#__PURE__*/React.createElement("td", {
        className: `p-1 border border-gray-300 ${className}`
      }, /*#__PURE__*/React.createElement("div", {
        className: "flex items-center gap-1"
      }, /*#__PURE__*/React.createElement("input", {
        type: "text",
        value: editingValue,
        onChange: this.handleEditChange,
        className: "w-full text-xs p-1 border rounded focus:outline-none focus:ring-1 focus:ring-blue-500",
        autoFocus: true,
        onKeyDown: e => {
          if (e.key === 'Enter') this.saveEdit();
          if (e.key === 'Escape') this.cancelEdit();
        }
      }), /*#__PURE__*/React.createElement("button", {
        onClick: this.saveEdit,
        className: "text-green-600 hover:text-green-800 text-xs px-1",
        title: "Save"
      }, "\u2713"), /*#__PURE__*/React.createElement("button", {
        onClick: this.cancelEdit,
        className: "text-red-600 hover:text-red-800 text-xs px-1",
        title: "Cancel"
      }, "\u2717")));
    }
    return /*#__PURE__*/React.createElement("td", {
      className: `p-2 border border-gray-300 ${canEdit ? 'cursor-pointer hover:bg-gray-50' : ''} ${className}`,
      onClick: canEdit ? () => this.startEdit(table, rowIndex, field, value) : undefined,
      title: canEdit ? "Click to edit" : ""
    }, value);
  };
  renderEditableMetric = (metricKey, property, value, className = "") => {
    const {
      editingCell,
      editingValue,
      canEdit
    } = this.state;
    const fieldId = `${metricKey}_${property}`;
    const isEditing = editingCell && editingCell.type === 'metric' && editingCell.field === fieldId;
    if (isEditing && canEdit) {
      return /*#__PURE__*/React.createElement("div", {
        className: `inline-flex items-center gap-1 ${className}`
      }, /*#__PURE__*/React.createElement("input", {
        type: "text",
        value: editingValue,
        onChange: this.handleEditChange,
        className: "w-20 text-xs p-1 border rounded focus:outline-none focus:ring-1 focus:ring-blue-500",
        autoFocus: true,
        onKeyDown: e => {
          if (e.key === 'Enter') this.saveEdit();
          if (e.key === 'Escape') this.cancelEdit();
        }
      }), /*#__PURE__*/React.createElement("button", {
        onClick: this.saveEdit,
        className: "text-green-600 hover:text-green-800 text-xs",
        title: "Save"
      }, "\u2713"), /*#__PURE__*/React.createElement("button", {
        onClick: this.cancelEdit,
        className: "text-red-600 hover:text-red-800 text-xs",
        title: "Cancel"
      }, "\u2717"));
    }
    return /*#__PURE__*/React.createElement("span", {
      className: `${canEdit ? 'cursor-pointer hover:bg-gray-100' : ''} px-1 py-0.5 rounded ${className}`,
      onClick: canEdit ? () => this.setState({
        editingCell: {
          type: 'metric',
          field: fieldId
        },
        editingValue: value.toString(),
        originalValue: value.toString()
      }) : undefined,
      title: canEdit ? "Click to edit" : ""
    }, value);
  };
  render() {
    return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
      className: "grid grid-cols-1 gap-4 mb-3"
    }, /*#__PURE__*/React.createElement("div", {
      className: `w-auto bg-gradient-to-r ${this.state.canEdit ? 'from-green-50 to-green-100 border-l-4 border-green-400' : 'from-blue-50 to-blue-100 border-l-4 border-blue-400'} p-3 rounded`
    }, /*#__PURE__*/React.createElement("div", {
      className: "flex items-center"
    }, /*#__PURE__*/React.createElement("div", {
      className: `${this.state.canEdit ? 'text-green-800' : 'text-blue-800'} mr-2`
    }, this.state.canEdit ? '✏️' : 'ℹ️'), /*#__PURE__*/React.createElement("div", {
      className: `text-sm ${this.state.canEdit ? 'text-green-800' : 'text-blue-800'}`
    }, this.state.canEdit ? /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("strong", null, "Edit Mode Enabled:"), " You have permissions to edit dashboard data. Click on any metric values, progress bars, targets in the cards above or data cells in the tables below to edit. Press Enter to save or Escape to cancel.") : /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("strong", null, "View Only Mode:"), " You have read-only access to this dashboard. Contact your administrator if you need editing permissions."))))), /*#__PURE__*/React.createElement("div", {
      className: "grid grid-cols-1 gap-4"
    }, /*#__PURE__*/React.createElement("div", {
      className: "w-auto bg-white drop-shadow-md shadow shadow-gulf-blue-300 text-gulf-blue-950 rounded px-4 py-4"
    }, /*#__PURE__*/React.createElement("div", {
      className: "flex justify-around"
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        flex: 0.25
      },
      className: "flex justify-center"
    }, /*#__PURE__*/React.createElement("div", {
      className: "w-full"
    }, /*#__PURE__*/React.createElement("select", {
      id: "selectRegion",
      name: "selectedRegion",
      onChange: event => this.onFilterSelectCenters("region", event),
      className: "block w-full bg-gulf-blue-50 rounded-md border-0 px-2 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6"
    }, this.state.region ? /*#__PURE__*/React.createElement("option", null, this.state.region) : /*#__PURE__*/React.createElement("option", null, "Select Region"), this.state.regions.map(region => /*#__PURE__*/React.createElement("option", {
      value: region.id
    }, region.region))))), /*#__PURE__*/React.createElement("div", {
      style: {
        flex: 0.25
      },
      className: "flex justify-center"
    }, /*#__PURE__*/React.createElement("div", {
      className: "w-full"
    }, /*#__PURE__*/React.createElement("select", {
      id: "selectDistrict",
      name: "selectedDistrict",
      onChange: event => this.onFilterSelectCenters("district", event),
      className: "block w-full bg-gulf-blue-50 rounded-md border-0 px-2 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6"
    }, this.state.district ? /*#__PURE__*/React.createElement("option", null, this.state.district) : /*#__PURE__*/React.createElement("option", null, "Select district"), this.state.districts.map(district => /*#__PURE__*/React.createElement("option", {
      value: district.id
    }, district.district))))), /*#__PURE__*/React.createElement("div", {
      style: {
        flex: 0.25
      },
      className: "flex justify-center"
    }, /*#__PURE__*/React.createElement("div", {
      className: "w-full"
    }, /*#__PURE__*/React.createElement("select", {
      id: "selectDepot",
      name: "selectedDepot",
      onChange: event => this.onFilterSelectCenters("depot", event),
      className: "block w-full bg-gulf-blue-50 rounded-md border-0 px-2 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6"
    }, this.state.depot ? /*#__PURE__*/React.createElement("option", null, this.state.depot) : /*#__PURE__*/React.createElement("option", null, "Select Centre"), this.state.depots ? this.state.depots.map(depot => /*#__PURE__*/React.createElement("option", {
      value: depot.id
    }, depot.depot)) : null)))))), /*#__PURE__*/React.createElement("div", {
      className: "grid grid-cols-5 gap-4 mt-5"
    }, /*#__PURE__*/React.createElement("div", {
      className: "w-auto bg-gradient-to-r from-gulf-blue-100 to-gulf-blue-300 drop-shadow-md shadow shadow-gulf-blue-300 text-gulf-blue-900 rounded px-2 py-2"
    }, /*#__PURE__*/React.createElement("div", {
      className: "sm:flex lg:items-center lg:justify-between"
    }, /*#__PURE__*/React.createElement("div", {
      className: "min-w-0 flex-1"
    }, /*#__PURE__*/React.createElement("div", {
      className: "text-center text-lg font-bold text-gulf-blue-950 sm:truncate sm:tracking-tight"
    }, "ENERGY SOLD"), /*#__PURE__*/React.createElement("div", {
      className: "mt-2"
    }, /*#__PURE__*/React.createElement("a", {
      href: "#"
    }, /*#__PURE__*/React.createElement("div", {
      className: "border border-gulf-blue-200 hover:bg-gulf-blue-400 rounded-lg px-3 py-1 justify-between items-center sm:mt-0 sm:flex-row sm:flex-wrap"
    }, /*#__PURE__*/React.createElement("div", {
      className: "col-xl col-sm text-center mb-xl-0 mb-4"
    }, /*#__PURE__*/React.createElement("div", {
      className: "card"
    }, /*#__PURE__*/React.createElement("div", {
      className: "card-body p-2"
    }, /*#__PURE__*/React.createElement("div", {
      className: "row"
    }, /*#__PURE__*/React.createElement("div", {
      className: "col-8"
    }, /*#__PURE__*/React.createElement("div", {
      className: "numbers"
    }, /*#__PURE__*/React.createElement("p", {
      className: "text-xs mb-0 text-capitalize font-weight-bold"
    }, "Energy Sold (GWh)"), /*#__PURE__*/React.createElement("h6", {
      className: "font-weight-bolder mb-0"
    }, this.renderEditableMetric('energy_sold', 'value', this.state.metrics.energy_sold.value), " ", this.state.metrics.energy_sold.unit)), /*#__PURE__*/React.createElement("div", {
      className: "overflow-hidden bg-blue-50 h-1.5 rounded-full w-full"
    }, /*#__PURE__*/React.createElement("span", {
      className: `h-full w-full block rounded-full transition-all duration-300 ${this.state.canEdit ? 'cursor-pointer' : ''} ${this.getProgressColor(this.calculateProgress(this.state.metrics.energy_sold.value, this.state.metrics.energy_sold.target))}`,
      style: {
        width: `${this.calculateProgress(this.state.metrics.energy_sold.value, this.state.metrics.energy_sold.target)}%`
      },
      title: `Progress: ${this.calculateProgress(this.state.metrics.energy_sold.value, this.state.metrics.energy_sold.target)}% (${this.state.metrics.energy_sold.value}/${this.state.metrics.energy_sold.target})${this.state.canEdit ? ' - Click to edit' : ''}`,
      onClick: this.state.canEdit ? () => this.setState({
        editingCell: {
          type: 'metric',
          field: 'energy_sold_progress'
        },
        editingValue: this.calculateProgress(this.state.metrics.energy_sold.value, this.state.metrics.energy_sold.target).toString(),
        originalValue: this.calculateProgress(this.state.metrics.energy_sold.value, this.state.metrics.energy_sold.target).toString()
      }) : undefined
    })), /*#__PURE__*/React.createElement("p", {
      className: "text-xs text-muted mt-2 mb-0"
    }, "Monthly Target: ", this.renderEditableMetric('energy_sold', 'target', this.state.metrics.energy_sold.target), " ", this.state.metrics.energy_sold.target_unit)))))))))))), /*#__PURE__*/React.createElement("div", {
      className: "w-auto bg-gradient-to-r from-jade-100 to-jade-300 drop-shadow-md shadow shadow-jade-300 text-jade-900 rounded px-2 py-2"
    }, /*#__PURE__*/React.createElement("div", {
      className: "sm:flex lg:items-center lg:justify-between"
    }, /*#__PURE__*/React.createElement("div", {
      className: "min-w-0 flex-1"
    }, /*#__PURE__*/React.createElement("div", {
      className: "text-center text-lg font-bold text-jade-900 sm:truncate sm:tracking-tight"
    }, "GROWTH"), /*#__PURE__*/React.createElement("div", {
      className: "mt-2"
    }, /*#__PURE__*/React.createElement("a", {
      href: "#"
    }, /*#__PURE__*/React.createElement("div", {
      className: "border border-jade-200 hover:bg-jade-400 rounded-lg px-3 py-1 justify-between items-center sm:mt-0 sm:flex-row sm:flex-wrap"
    }, /*#__PURE__*/React.createElement("div", {
      className: "col-xl col-sm text-center mb-xl-0 mb-4"
    }, /*#__PURE__*/React.createElement("div", {
      className: "card"
    }, /*#__PURE__*/React.createElement("div", {
      className: "card-body p-2"
    }, /*#__PURE__*/React.createElement("div", {
      className: "row"
    }, /*#__PURE__*/React.createElement("div", {
      className: "col-8"
    }, /*#__PURE__*/React.createElement("div", {
      className: "numbers"
    }, /*#__PURE__*/React.createElement("p", {
      className: "text-xs mb-0 text-capitalize font-weight-bold"
    }, "Client Connected"), /*#__PURE__*/React.createElement("h6", {
      className: "font-weight-bolder mb-0"
    }, this.renderEditableMetric('growth', 'value', this.state.metrics.growth.value))), /*#__PURE__*/React.createElement("div", {
      className: "overflow-hidden bg-jade-50 h-1.5 rounded-full w-full"
    }, /*#__PURE__*/React.createElement("span", {
      className: `h-full w-full block rounded-full transition-all duration-300 ${this.state.canEdit ? 'cursor-pointer' : ''} ${this.getProgressColor(this.calculateProgress(this.state.metrics.growth.value, this.state.metrics.growth.target))}`,
      style: {
        width: `${this.calculateProgress(this.state.metrics.growth.value, this.state.metrics.growth.target)}%`
      },
      title: `Progress: ${this.calculateProgress(this.state.metrics.growth.value, this.state.metrics.growth.target)}% (${this.state.metrics.growth.value}/${this.state.metrics.growth.target})${this.state.canEdit ? ' - Click to edit' : ''}`,
      onClick: this.state.canEdit ? () => this.setState({
        editingCell: {
          type: 'metric',
          field: 'growth_progress'
        },
        editingValue: this.calculateProgress(this.state.metrics.growth.value, this.state.metrics.growth.target).toString(),
        originalValue: this.calculateProgress(this.state.metrics.growth.value, this.state.metrics.growth.target).toString()
      }) : undefined
    })), /*#__PURE__*/React.createElement("p", {
      className: "text-xs text-muted mt-2 mb-0"
    }, "YTD Target: ", this.renderEditableMetric('growth', 'target', this.state.metrics.growth.target), " ", this.state.metrics.growth.target_unit)))))))))))), /*#__PURE__*/React.createElement("div", {
      className: "w-auto bg-gradient-to-r from-royal-heath-100 to-royal-heath-300 drop-shadow-md shadow shadow-royal-heath-300 text-royal-heath-900 rounded px-2 py-2"
    }, /*#__PURE__*/React.createElement("div", {
      className: "sm:flex lg:items-center lg:justify-between"
    }, /*#__PURE__*/React.createElement("div", {
      className: "min-w-0 flex-1"
    }, /*#__PURE__*/React.createElement("div", {
      className: "text-center text-lg font-bold text-royal-heath-950 sm:truncate sm:tracking-tight"
    }, "REVENUE COLLECTION"), /*#__PURE__*/React.createElement("div", {
      className: "mt-2"
    }, /*#__PURE__*/React.createElement("a", {
      href: "#"
    }, /*#__PURE__*/React.createElement("div", {
      className: "border border-royal-heath-200 hover:bg-royal-heath-400 rounded-lg px-3 py-1 justify-between items-center sm:mt-0 sm:flex-row sm:flex-wrap"
    }, /*#__PURE__*/React.createElement("div", {
      className: "col-xl col-sm text-center mb-xl-0 mb-4"
    }, /*#__PURE__*/React.createElement("div", {
      className: "card"
    }, /*#__PURE__*/React.createElement("div", {
      className: "card-body p-2"
    }, /*#__PURE__*/React.createElement("div", {
      className: "row"
    }, /*#__PURE__*/React.createElement("div", {
      className: "col-8"
    }, /*#__PURE__*/React.createElement("div", {
      className: "numbers"
    }, /*#__PURE__*/React.createElement("p", {
      className: "text-xs mb-0 text-capitalize font-weight-bold"
    }, "Revenue Collected"), /*#__PURE__*/React.createElement("h6", {
      className: "font-weight-bolder mb-0"
    }, this.state.metrics.revenue_usd.unit, " ", this.renderEditableMetric('revenue_usd', 'value', this.state.metrics.revenue_usd.value)), /*#__PURE__*/React.createElement("h6", {
      className: "font-weight-bolder mb-0"
    }, this.state.metrics.revenue_zwl.unit, " ", this.renderEditableMetric('revenue_zwl', 'value', this.state.metrics.revenue_zwl.value))), /*#__PURE__*/React.createElement("div", {
      className: "overflow-hidden bg-royal-heath-50 h-1.5 rounded-full w-full"
    }, /*#__PURE__*/React.createElement("span", {
      className: `h-full w-full block rounded-full transition-all duration-300 ${this.state.canEdit ? 'cursor-pointer' : ''} ${this.getProgressColor(Math.round((this.calculateProgress(this.state.metrics.revenue_usd.value, this.state.metrics.revenue_usd.target) + this.calculateProgress(this.state.metrics.revenue_zwl.value, this.state.metrics.revenue_zwl.target)) / 2))}`,
      style: {
        width: `${Math.round((this.calculateProgress(this.state.metrics.revenue_usd.value, this.state.metrics.revenue_usd.target) + this.calculateProgress(this.state.metrics.revenue_zwl.value, this.state.metrics.revenue_zwl.target)) / 2)}%`
      },
      title: `Combined Progress: ${Math.round((this.calculateProgress(this.state.metrics.revenue_usd.value, this.state.metrics.revenue_usd.target) + this.calculateProgress(this.state.metrics.revenue_zwl.value, this.state.metrics.revenue_zwl.target)) / 2)}% | USD: ${this.calculateProgress(this.state.metrics.revenue_usd.value, this.state.metrics.revenue_usd.target)}% | ZWL: ${this.calculateProgress(this.state.metrics.revenue_zwl.value, this.state.metrics.revenue_zwl.target)}%${this.state.canEdit ? ' - Click to edit' : ''}`,
      onClick: this.state.canEdit ? () => this.setState({
        editingCell: {
          type: 'metric',
          field: 'revenue_combined_progress'
        },
        editingValue: Math.round((this.calculateProgress(this.state.metrics.revenue_usd.value, this.state.metrics.revenue_usd.target) + this.calculateProgress(this.state.metrics.revenue_zwl.value, this.state.metrics.revenue_zwl.target)) / 2).toString(),
        originalValue: Math.round((this.calculateProgress(this.state.metrics.revenue_usd.value, this.state.metrics.revenue_usd.target) + this.calculateProgress(this.state.metrics.revenue_zwl.value, this.state.metrics.revenue_zwl.target)) / 2).toString()
      }) : undefined
    })), /*#__PURE__*/React.createElement("p", {
      className: "text-xs text-muted mt-2 mb-0"
    }, "YTD Target: ", this.state.metrics.revenue_usd.unit, " ", this.renderEditableMetric('revenue_usd', 'target', this.state.metrics.revenue_usd.target)), /*#__PURE__*/React.createElement("p", {
      className: "text-xs text-muted mt-2 mb-0"
    }, "YTD Target: ", this.state.metrics.revenue_zwl.unit, " ", this.renderEditableMetric('revenue_zwl', 'target', this.state.metrics.revenue_zwl.target))))))))))))), /*#__PURE__*/React.createElement("div", {
      className: "w-auto bg-gradient-to-r from-gulf-blue-100 to-gulf-blue-300 drop-shadow-md shadow shadow-gulf-blue-300 text-gulf-blue-900 rounded px-2 py-2"
    }, /*#__PURE__*/React.createElement("div", {
      className: "sm:flex lg:items-center lg:justify-between"
    }, /*#__PURE__*/React.createElement("div", {
      className: "min-w-0 flex-1"
    }, /*#__PURE__*/React.createElement("div", {
      className: "text-center text-lg font-bold text-gulf-blue-950 sm:truncate sm:tracking-tight"
    }, "FAULTS"), /*#__PURE__*/React.createElement("div", {
      className: "mt-2"
    }, /*#__PURE__*/React.createElement("a", {
      href: "#"
    }, /*#__PURE__*/React.createElement("div", {
      className: "border border-gulf-blue-200 hover:bg-gulf-blue-400 rounded-lg px-3 py-1 justify-between items-center sm:mt-0 sm:flex-row sm:flex-wrap"
    }, /*#__PURE__*/React.createElement("div", {
      className: "col-xl col-sm text-center mb-xl-0 mb-4"
    }, /*#__PURE__*/React.createElement("div", {
      className: "card"
    }, /*#__PURE__*/React.createElement("div", {
      className: "card-body p-2"
    }, /*#__PURE__*/React.createElement("div", {
      className: "row"
    }, /*#__PURE__*/React.createElement("div", {
      className: "col-8"
    }, /*#__PURE__*/React.createElement("div", {
      className: "numbers"
    }, /*#__PURE__*/React.createElement("p", {
      className: "text-xs mb-0 text-capitalize font-weight-bold"
    }, "Compliants Received"), /*#__PURE__*/React.createElement("h6", {
      className: "font-weight-bolder mb-0"
    }, this.renderEditableMetric('faults', 'value', this.state.metrics.faults.value))), /*#__PURE__*/React.createElement("div", {
      className: "overflow-hidden bg-gulf-blue-50 h-1.5 rounded-full w-full"
    }, /*#__PURE__*/React.createElement("span", {
      className: `h-full w-full block rounded-full transition-all duration-300 ${this.state.canEdit ? 'cursor-pointer' : ''} ${this.getProgressColor(this.calculateProgress(this.state.metrics.faults.value, this.state.metrics.faults.target))}`,
      style: {
        width: `${this.calculateProgress(this.state.metrics.faults.value, this.state.metrics.faults.target)}%`
      },
      title: `Progress: ${this.calculateProgress(this.state.metrics.faults.value, this.state.metrics.faults.target)}% (${this.state.metrics.faults.value}/${this.state.metrics.faults.target})${this.state.canEdit ? ' - Click to edit' : ''}`,
      onClick: this.state.canEdit ? () => this.setState({
        editingCell: {
          type: 'metric',
          field: 'faults_progress'
        },
        editingValue: this.calculateProgress(this.state.metrics.faults.value, this.state.metrics.faults.target).toString(),
        originalValue: this.calculateProgress(this.state.metrics.faults.value, this.state.metrics.faults.target).toString()
      }) : undefined
    })), /*#__PURE__*/React.createElement("p", {
      className: "text-xs text-muted mt-2 mb-0"
    }, "YTD Target: ", this.renderEditableMetric('faults', 'target', this.state.metrics.faults.target))))))))))))), /*#__PURE__*/React.createElement("div", {
      className: "w-auto bg-gradient-to-r from-jade-100 to-jade-300 drop-shadow-md shadow shadow-jade-300 text-jade-900 rounded px-2 py-2"
    }, /*#__PURE__*/React.createElement("div", {
      className: "sm:flex lg:items-center lg:justify-between"
    }, /*#__PURE__*/React.createElement("div", {
      className: "min-w-0 flex-1"
    }, /*#__PURE__*/React.createElement("div", {
      className: "text-center text-lg font-bold text-jade-950 sm:truncate sm:tracking-tight"
    }, "MAINTENANCE"), /*#__PURE__*/React.createElement("div", {
      className: "mt-2"
    }, /*#__PURE__*/React.createElement("a", {
      href: "#"
    }, /*#__PURE__*/React.createElement("div", {
      className: "border border-jade-200 hover:bg-jade-400 rounded-lg px-3 py-1 justify-between items-center sm:mt-0 sm:flex-row sm:flex-wrap"
    }, /*#__PURE__*/React.createElement("div", {
      className: "col-xl col-sm text-center mb-xl-0 mb-4"
    }, /*#__PURE__*/React.createElement("div", {
      className: "card"
    }, /*#__PURE__*/React.createElement("div", {
      className: "card-body p-2"
    }, /*#__PURE__*/React.createElement("div", {
      className: "row"
    }, /*#__PURE__*/React.createElement("div", {
      className: "col-8"
    }, /*#__PURE__*/React.createElement("div", {
      className: "numbers"
    }, /*#__PURE__*/React.createElement("p", {
      className: "text-xs mb-0 text-capitalize font-weight-bold"
    }, "Maintained"), /*#__PURE__*/React.createElement("h6", {
      className: "font-weight-bolder mb-0"
    }, this.renderEditableMetric('maintenance', 'value', this.state.metrics.maintenance.value))), /*#__PURE__*/React.createElement("div", {
      className: "overflow-hidden bg-jade-50 h-1.5 rounded-full w-full"
    }, /*#__PURE__*/React.createElement("span", {
      className: `h-full w-full block rounded-full transition-all duration-300 ${this.state.canEdit ? 'cursor-pointer' : ''} ${this.getProgressColor(this.calculateProgress(this.state.metrics.maintenance.value, this.state.metrics.maintenance.target))}`,
      style: {
        width: `${this.calculateProgress(this.state.metrics.maintenance.value, this.state.metrics.maintenance.target)}%`
      },
      title: `Progress: ${this.calculateProgress(this.state.metrics.maintenance.value, this.state.metrics.maintenance.target)}% (${this.state.metrics.maintenance.value}/${this.state.metrics.maintenance.target})${this.state.canEdit ? ' - Click to edit' : ''}`,
      onClick: this.state.canEdit ? () => this.setState({
        editingCell: {
          type: 'metric',
          field: 'maintenance_progress'
        },
        editingValue: this.calculateProgress(this.state.metrics.maintenance.value, this.state.metrics.maintenance.target).toString(),
        originalValue: this.calculateProgress(this.state.metrics.maintenance.value, this.state.metrics.maintenance.target).toString()
      }) : undefined
    })), /*#__PURE__*/React.createElement("p", {
      className: "text-xs text-muted mt-2 mb-0"
    }, "YTD Target: ", this.renderEditableMetric('maintenance', 'target', this.state.metrics.maintenance.target)))))))))))))), /*#__PURE__*/React.createElement("div", {
      className: "grid grid-cols-4 gap-4 mt-10"
    }, /*#__PURE__*/React.createElement("div", {
      className: "w-auto bg-gradient-to-b from-gulf-blue-100 to-gulf-blue-200 drop-shadow-lg shadow-lg shadow-gulf-blue-400 text-gray-900 rounded-lg px-3 py-3 border border-gulf-blue-300"
    }, /*#__PURE__*/React.createElement("div", {
      className: "sm:flex lg:items-center lg:justify-between"
    }, /*#__PURE__*/React.createElement("div", {
      className: "min-w-0 flex-1"
    }, /*#__PURE__*/React.createElement("div", {
      className: "text-center text-xl font-bold text-gulf-blue-900 sm:truncate sm:tracking-tight mb-2 bg-white rounded-lg py-2 px-3 shadow-sm border border-gulf-blue-300"
    }, "\uD83D\uDCCA Weekly Sales"), /*#__PURE__*/React.createElement("div", {
      style: {
        height: "14rem"
      },
      className: "mt-2 h-20 overflow-auto"
    }, /*#__PURE__*/React.createElement("a", {
      href: "#"
    }, /*#__PURE__*/React.createElement("table", {
      className: "table-auto w-full text-sm border-collapse"
    }, /*#__PURE__*/React.createElement("thead", {
      className: "bg-gulf-blue-600 text-white"
    }, /*#__PURE__*/React.createElement("tr", {
      className: "bg-gulf-blue-600 transition-colors"
    }, /*#__PURE__*/React.createElement("th", {
      className: "text-left p-2 font-bold border border-gulf-blue-600"
    }, "Week"), /*#__PURE__*/React.createElement("th", {
      className: "text-left p-2 font-bold border border-gulf-blue-600"
    }, "ZWL"), /*#__PURE__*/React.createElement("th", {
      className: "text-left p-2 font-bold border border-gulf-blue-600"
    }, "USD"))), /*#__PURE__*/React.createElement("tbody", {
      className: "bg-white"
    }, this.state.weekly_sales ? this.state.weekly_sales.map((sale, index) => /*#__PURE__*/React.createElement("tr", {
      key: index,
      className: "hover:bg-gulf-blue-100 transition-colors"
    }, /*#__PURE__*/React.createElement("td", {
      className: "p-2 font-semibold text-gulf-blue-900 border border-gray-300"
    }, sale.week), this.renderEditableCell('weekly_sales', index, 'zwl', sale.zwl, 'text-gray-800 font-medium'), this.renderEditableCell('weekly_sales', index, 'usd', sale.usd, 'text-gray-800 font-medium'))) : null))))))), /*#__PURE__*/React.createElement("div", {
      className: "w-auto bg-gradient-to-b from-red-100 to-red-200 drop-shadow-lg shadow-lg shadow-red-400 text-gray-900 rounded-lg px-3 py-3 border border-red-300"
    }, /*#__PURE__*/React.createElement("div", {
      className: "sm:flex lg:items-center lg:justify-between"
    }, /*#__PURE__*/React.createElement("div", {
      className: "min-w-0 flex-1"
    }, /*#__PURE__*/React.createElement("div", {
      className: "text-center text-xl font-bold text-red-900 sm:truncate sm:tracking-tight mb-2 bg-white rounded-lg py-2 px-3 shadow-sm border border-red-300"
    }, "\u26A1 Weekly Power Outages"), /*#__PURE__*/React.createElement("div", {
      style: {
        height: "14rem"
      },
      className: "mt-2 h-20 overflow-auto"
    }, /*#__PURE__*/React.createElement("a", {
      href: "#"
    }, /*#__PURE__*/React.createElement("table", {
      className: "table-auto w-full text-sm border-collapse"
    }, /*#__PURE__*/React.createElement("thead", {
      className: "bg-red-600 text-white"
    }, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("th", {
      className: "text-left p-2 font-bold border border-red-600"
    }, "Week"), /*#__PURE__*/React.createElement("th", {
      className: "text-left p-2 font-bold border border-red-600"
    }, "Total"), /*#__PURE__*/React.createElement("th", {
      className: "text-left p-2 font-bold border border-red-600"
    }, "Resolved"), /*#__PURE__*/React.createElement("th", {
      className: "text-left p-2 font-bold border border-red-600"
    }, "Pending"))), /*#__PURE__*/React.createElement("tbody", {
      className: "bg-white"
    }, this.state.weekly_outages ? this.state.weekly_outages.map((outage, index) => /*#__PURE__*/React.createElement("tr", {
      key: index,
      className: "hover:bg-red-50 transition-colors"
    }, /*#__PURE__*/React.createElement("td", {
      className: "p-2 font-semibold text-red-900 border border-gray-300"
    }, outage.week), this.renderEditableCell('weekly_outages', index, 'outages', outage.outages, 'text-gray-800 font-medium'), this.renderEditableCell('weekly_outages', index, 'resolved', outage.resolved, 'text-green-700 font-medium'), this.renderEditableCell('weekly_outages', index, 'pending', outage.pending, 'text-red-700 font-medium'))) : null))))))), /*#__PURE__*/React.createElement("div", {
      className: "w-auto bg-gradient-to-b from-orange-100 to-orange-200 drop-shadow-lg shadow-lg shadow-orange-400 text-gray-900 rounded-lg px-3 py-3 border border-orange-300"
    }, /*#__PURE__*/React.createElement("div", {
      className: "sm:flex lg:items-center lg:justify-between"
    }, /*#__PURE__*/React.createElement("div", {
      className: "min-w-0 flex-1"
    }, /*#__PURE__*/React.createElement("div", {
      className: "text-center text-xl font-bold text-orange-900 sm:truncate sm:tracking-tight mb-2 bg-white rounded-lg py-2 px-3 shadow-sm border border-orange-300"
    }, "\uD83D\uDD27 Weekly Faults and Maintenance"), /*#__PURE__*/React.createElement("div", {
      style: {
        height: "14rem"
      },
      className: "mt-2 h-20 overflow-auto"
    }, /*#__PURE__*/React.createElement("a", {
      href: "#"
    }, /*#__PURE__*/React.createElement("table", {
      className: "table-auto w-full text-sm border-collapse"
    }, /*#__PURE__*/React.createElement("thead", {
      className: "bg-gulf-blue-600 text-white"
    }, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("th", {
      className: "text-left p-2 font-bold border border-gulf-blue-600"
    }, "Week"), /*#__PURE__*/React.createElement("th", {
      className: "text-left p-2 font-bold border border-gulf-blue-600"
    }, "Faults"), /*#__PURE__*/React.createElement("th", {
      className: "text-left p-2 font-bold border border-orange-600"
    }, "Maintenance"), /*#__PURE__*/React.createElement("th", {
      className: "text-left p-2 font-bold border border-orange-600"
    }, "Completed"), /*#__PURE__*/React.createElement("th", {
      className: "text-left p-2 font-bold border border-orange-600"
    }, "Pending"))), /*#__PURE__*/React.createElement("tbody", {
      className: "bg-white"
    }, this.state.weekly_faults_maintenance ? this.state.weekly_faults_maintenance.map((item, index) => /*#__PURE__*/React.createElement("tr", {
      key: index,
      className: "hover:bg-orange-50 transition-colors"
    }, /*#__PURE__*/React.createElement("td", {
      className: "p-2 font-semibold text-orange-900 border border-gray-300"
    }, item.week), this.renderEditableCell('weekly_faults_maintenance', index, 'faults', item.faults, 'text-red-700 font-medium'), this.renderEditableCell('weekly_faults_maintenance', index, 'maintenance', item.maintenance, 'text-blue-700 font-medium'), this.renderEditableCell('weekly_faults_maintenance', index, 'completed', item.completed, 'text-green-700 font-medium'), this.renderEditableCell('weekly_faults_maintenance', index, 'pending', item.pending, 'text-red-700 font-medium'))) : null))))))), /*#__PURE__*/React.createElement("div", {
      className: "w-auto bg-gradient-to-b from-purple-100 to-purple-200 drop-shadow-lg shadow-lg shadow-purple-400 text-gray-900 rounded-lg px-3 py-3 border border-purple-300"
    }, /*#__PURE__*/React.createElement("div", {
      className: "sm:flex lg:items-center lg:justify-between"
    }, /*#__PURE__*/React.createElement("div", {
      className: "min-w-0 flex-1"
    }, /*#__PURE__*/React.createElement("div", {
      className: "text-center text-xl font-bold text-purple-900 sm:truncate sm:tracking-tight mb-2 bg-white rounded-lg py-2 px-3 shadow-sm border border-purple-300"
    }, "\uD83D\uDCB0 Top Debtors"), /*#__PURE__*/React.createElement("div", {
      style: {
        height: "14rem"
      },
      className: "mt-2 h-20 overflow-auto"
    }, /*#__PURE__*/React.createElement("a", {
      href: "#"
    }, /*#__PURE__*/React.createElement("table", {
      className: "table-auto w-full text-sm border-collapse"
    }, /*#__PURE__*/React.createElement("thead", {
      className: "bg-purple-600 text-white"
    }, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("th", {
      className: "text-left p-2 font-bold border border-purple-600"
    }, "#"), /*#__PURE__*/React.createElement("th", {
      className: "text-left p-2 font-bold border border-purple-600"
    }, "Customer"), /*#__PURE__*/React.createElement("th", {
      className: "text-left p-2 font-bold border border-purple-600"
    }, "Amount"))), /*#__PURE__*/React.createElement("tbody", {
      className: "bg-white"
    }, this.state.tds && this.state.tds.length > 0 ? this.state.tds.map((td, index) => /*#__PURE__*/React.createElement("tr", {
      key: index,
      className: "hover:bg-purple-50 transition-colors"
    }, /*#__PURE__*/React.createElement("td", {
      className: "p-2 font-semibold text-purple-900 border border-gray-300"
    }, index + 1), this.renderEditableCell('tds', index, 'name', td.name, 'text-gray-800 font-medium'), this.renderEditableCell('tds', index, 'amount', td.amount, 'text-red-700 font-medium'))) : /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", {
      colSpan: "3",
      className: "p-2 text-center text-gray-500 border border-gray-300"
    }, "No debt data available")))))))))));
  }
}
const spid = domContainer.getAttribute("data-spid");
const region = domContainer.getAttribute("data-region");
const district = domContainer.getAttribute("data-district");
const section = domContainer.getAttribute("data-section");
const depot = domContainer.getAttribute("data-depot");
ReactDOM.render(e(DashboardFilter, {
  spid,
  region,
  district,
  section
}), domContainer);
