"use strict";

var _createClass = function () { function defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, descriptor.key, descriptor); } } return function (Constructor, protoProps, staticProps) { if (protoProps) defineProperties(Constructor.prototype, protoProps); if (staticProps) defineProperties(Constructor, staticProps); return Constructor; }; }();

function _defineProperty(obj, key, value) { if (key in obj) { Object.defineProperty(obj, key, { value: value, enumerable: true, configurable: true, writable: true }); } else { obj[key] = value; } return obj; }

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

function _possibleConstructorReturn(self, call) { if (!self) { throw new ReferenceError("this hasn't been initialised - super() hasn't been called"); } return call && (typeof call === "object" || typeof call === "function") ? call : self; }

function _inherits(subClass, superClass) { if (typeof superClass !== "function" && superClass !== null) { throw new TypeError("Super expression must either be null or a function, not " + typeof superClass); } subClass.prototype = Object.create(superClass && superClass.prototype, { constructor: { value: subClass, enumerable: false, writable: true, configurable: true } }); if (superClass) Object.setPrototypeOf ? Object.setPrototypeOf(subClass, superClass) : subClass.__proto__ = superClass; }

var e = React.createElement;

var DashboardFilter = function (_React$Component) {
  _inherits(DashboardFilter, _React$Component);

  function DashboardFilter(props) {
    var _this$state;

    _classCallCheck(this, DashboardFilter);

    var _this = _possibleConstructorReturn(this, (DashboardFilter.__proto__ || Object.getPrototypeOf(DashboardFilter)).call(this, props));

    _this.getFilterData = function (selectedRegion, selectedDistrict, selectedDepot) {
      fetch("http://localhost:8000/dashboards/dashboard_filter", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": _this.getCookie("csrftoken")
        },
        body: JSON.stringify({
          region: selectedRegion,
          district: selectedDistrict,
          depot: selectedDepot
        })
      }).then(function (response) {
        return response.json();
      }).then(function (data) {

        console.log("data: ", data);
        if (data) {
          console.log("running ...");
          var inspection_locations_ = void 0,
              inspections_count_ = void 0,
              maintenance_locations_ = void 0,
              maintenance_count_ = void 0,
              mtn_ = void 0;
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

          _this.setState({
            inspection_locations: inspection_locations_,
            inspections_count: inspections_count_,
            maintenance_locations: maintenance_locations_,
            maintenance_count: maintenance_count_,
            mnt: mtn_,
            pbncs: data.pbncs,
            upos: data.upos,
            tds: data.tds
          });

          _this.initComponents();
        }
      });
    };

    _this.initComponents = function () {
      var baseColors = ["#f62c06", "#94834b", "#1288fe", "#c8a806", "#f02e0e", "#e118d5", "#0fb11c", "#3b3cf0", "#188350", "#c93986", "#90921e"];
      // Destroy the previous Chart instance, if it exists
      if (_this.inspectionChart) {
        _this.inspectionChart.destroy();
      }
      if (_this.inspectionBarChart) {
        _this.inspectionBarChart.destroy();
      }
      if (_this.mmtPieChart) {
        _this.mmtPieChart.destroy();
      }
      if (_this.mmtBarChart) {
        _this.mmtBarChart.destroy();
      }

      var inspectionData = {
        labels: _this.state.inspection_locations,
        datasets: [{
          data: _this.state.inspections_count,
          backgroundColor: baseColors,
          hoverBackgroundColor: baseColors
        }]
      };

      _this.inspectionChart = new Chart(_this.inspectionPieChartRef.current, {
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
        labels: _this.state.inspection_locations,
        datasets: [{
          data: _this.state.inspections_count,
          backgroundColor: baseColors,
          hoverBackgroundColor: baseColors
        }]
      };

      _this.inspectionBarChart = new Chart(_this.inspectionBarChartRef.current, {
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
        labels: _this.state.maintenance_locations,
        datasets: [{
          data: _this.state.maintenance_count,
          backgroundColor: baseColors,
          hoverBackgroundColor: baseColors
        }]
      };

      // Create the pie chart
      _this.mmtPieChart = new Chart(_this.mmtPieChartRef.current, {
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

      var mnt = _this.state.mnt;
      var maintenanceDataset = [];

      Object.keys(mnt).forEach(function (key) {
        maintenanceDataset.push({
          label: key,
          data: mnt[key], // [1,2,3,4]
          fill: 2
        });
      });

      var maintenanceBarData = {
        labels: ["1", "2", "3", "4"], // ['January', 'December'],
        datasets: maintenanceDataset.map(function (data) {
          return {
            label: data.label,
            data: data.data,
            fill: 2
          };
        })
      };

      _this.mmtBarChart = new Chart(_this.mmtBarChartRef.current, {
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

    _this.getRegions = function () {

      fetch("http://localhost:8000/dashboards/regions").then(function (response) {
        return response.json();
      }).then(function (data) {
        console.log(data);
        _this.setState({
          allRegions: data.regions,
          allDistricts: data.districts,
          allSections: data.sections,
          allDepots: data.depots,
          regions: data.regions,
          districts: data.districts,
          sections: data.sections,
          depots: data.depots,
          pbncs: data.pbncs,
          upos: data.upos,
          tds: data.tds
        });
      });
    };

    _this.getDashboardData = function () {
      fetch("http://localhost:8000/dashboards/dashboard_data").then(function (response) {
        return response.json();
      }).then(function (data) {

        console.log("data: ", data);
        var inspection_locations_ = JSON.parse(data.inspection_locations);
        var inspections_count_ = JSON.parse(data.inspections_count);
        var maintenance_locations_ = JSON.parse(data.maintenance_locations);
        var maintenance_count_ = JSON.parse(data.maintenance_count);
        var mtn_ = data.mtn;

        _this.setState({
          inspection_locations: inspection_locations_,
          inspections_count: inspections_count_,
          maintenance_locations: maintenance_locations_,
          maintenance_count: maintenance_count_,
          mnt: mtn_,
          pbncs: data.pbncs,
          upos: data.upos,
          tds: data.tds
        });

        _this.initComponents();
      });
    };

    _this.onServiceSelected = function (event) {
      console.log(event);
      var _event$target = event.target,
          name = _event$target.name,
          checked = _event$target.checked;

      _this.setState({
        form: Object.assign({}, _this.state.form, {
          services: Object.assign({}, _this.state.form.services, _defineProperty({}, name, checked))
        })
      });
    };

    _this.onInputChange = function (event) {
      console.log(event);
      var _event$target2 = event.target,
          name = _event$target2.name,
          value = _event$target2.value;

      _this.setState({
        form: Object.assign({}, _this.state.form, _defineProperty({}, name, value))
      });
    };

    _this.state = (_this$state = {
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
      upos: [],
      tds: [],
      current_month: "",
      maintenance: [],
      inspections: [],

      inspection_locations: [],
      inspections_count: [],

      maintenance_locations: [],
      maintenance_count: [],
      mnt: {}

    }, _defineProperty(_this$state, "selectedRegion", ""), _defineProperty(_this$state, "selectedDistrict", ""), _defineProperty(_this$state, "selectedSection", ""), _defineProperty(_this$state, "authUser", {}), _this$state);
    _this.inspectionPieChartRef = React.createRef();
    _this.inspectionBarChartRef = React.createRef();
    _this.mmtPieChartRef = React.createRef();
    _this.mmtBarChartRef = React.createRef();
    _this.onFilterSelectCenters = _this.onFilterSelectCenters.bind(_this);

    _this.inspectionChart = null;
    _this.inspectionBarChart = null;
    _this.mmtPieChart = null;
    _this.mmtBarChart = null;
    return _this;
  }

  _createClass(DashboardFilter, [{
    key: "componentDidMount",
    value: function componentDidMount() {
      this.setState({
        region: this.props.region,
        district: this.props.district,
        section: this.props.section,
        depot: this.props.depot
      });
      this.getRegions();
      this.getDashboardData();
    }
  }, {
    key: "onFilterSelectCenters",
    value: function onFilterSelectCenters(name_, event) {
      var _event$target3 = event.target,
          name = _event$target3.name,
          value = _event$target3.value;

      if (name_ === "region") {
        var dist = this.state.allDistricts.filter(function (_district) {
          return _district.region_id === value;
        });
        this.setState({
          districts: dist,
          selectedRegion: value,
          selectedDepot: "",
          selectedDistrict: ""
        });
        this.getFilterData(value, "", "");
      } else if (name_ === "district") {
        console.log("district: ", value, this.state.allDepots);
        var depos = this.state.allDepots.filter(function (_depot) {
          return parseInt(_depot.district_id) === parseInt(value);
        });
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
  }, {
    key: "onMaintenanceMonthSelected",
    value: function onMaintenanceMonthSelected(event) {
      (function (event) {
        var newValue = event; //event.target.value;

        getThisMonthData(newValue);
      });
    }
  }, {
    key: "getThisMonthData",
    value: function getThisMonthData(month) {
      // Create an XMLHttpRequest object
      var xhr = new XMLHttpRequest();
      res = {};

      var csrfToken = document.getElementById("selectInspForm").value;
      console.log("csrfToken: ", csrfToken);

      // Set up the request
      xhr.open("GET", "http://localhost:8000/dashboards/ajax?month=" + month); // Replace with your actual URL and parameters

      xhr.setRequestHeader("X-CSRFToken", csrfToken);
      // Handle the response
      xhr.onload = function () {
        if (xhr.status === 200) {
          var responseData = xhr.responseText;
          res = JSON.parse(responseData);
          console.log("responsible data: ", responseData);
          // Clear existing data
          mChart.data.datasets = [];

          // Add new datasets
          Object.keys(res).forEach(function (key) {
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
  }, {
    key: "onInspectionMonthSelected",
    value: function onInspectionMonthSelected(event) {
      var newValue = event; //event.target.value;

      getInspectionsMonthData(newValue);
    }
  }, {
    key: "getCookie",
    value: function getCookie(name) {
      var cookieValue = null;
      if (document.cookie && document.cookie !== "") {
        var cookies = document.cookie.split(";");
        for (var i = 0; i < cookies.length; i++) {
          var cookie = cookies[i].trim();
          if (cookie.substring(0, name.length + 1) === name + "=") {
            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
            break;
          }
        }
      }
      return cookieValue;
    }
  }, {
    key: "getInspectionsMonthData",
    value: function getInspectionsMonthData(month) {
      // Create an XMLHttpRequest object
      var xhr = new XMLHttpRequest();
      res = {};

      var csrfToken = getCookie("csrf_token");
      console.log("csrfToken: ", csrfToken);
      // Set up the request
      xhr.open("GET", "http://localhost:8000/dashboards/inspections/ajax?month=" + month); // Replace with your actual URL and parameters
      xhr.setRequestHeader("X-CSRFToken", csrfToken);

      // Handle the response
      xhr.onload = function () {
        if (xhr.status === 200) {
          var responseData = xhr.responseText;
          res = JSON.parse(responseData);
          var keysList = JSON.parse(res.keys_list);
          var valuesList = JSON.parse(res.values_list);
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

  }, {
    key: "render",
    value: function render() {
      var _this2 = this;

      return React.createElement(
        "div",
        null,
        React.createElement(
          "div",
          { className: "grid grid-cols-1 gap-4" },
          React.createElement(
            "div",
            { className: "w-auto bg-white drop-shadow-md shadow shadow-gulf-blue-300 text-gulf-blue-950 rounded px-4 py-4" },
            React.createElement(
              "div",
              { className: "flex justify-around" },
              React.createElement(
                "div",
                { style: { flex: 0.25 }, className: "flex justify-center" },
                React.createElement(
                  "div",
                  { className: "w-full" },
                  React.createElement(
                    "select",
                    {
                      id: "selectRegion",
                      name: "selectedRegion",
                      onChange: function onChange(event) {
                        return _this2.onFilterSelectCenters("region", event);
                      },
                      className: "block w-full bg-gulf-blue-50 rounded-md border-0 px-2 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6"
                    },
                    this.state.region ? React.createElement(
                      "option",
                      null,
                      this.state.region
                    ) : React.createElement(
                      "option",
                      null,
                      "Select Region"
                    ),
                    this.state.regions.map(function (region) {
                      return React.createElement(
                        "option",
                        { value: region.id },
                        region.region
                      );
                    })
                  )
                )
              ),
              React.createElement(
                "div",
                { style: { flex: 0.25 }, className: "flex justify-center" },
                React.createElement(
                  "div",
                  { className: "w-full" },
                  React.createElement(
                    "select",
                    {
                      id: "selectDistrict",
                      name: "selectedDistrict",
                      onChange: function onChange(event) {
                        return _this2.onFilterSelectCenters("district", event);
                      },
                      className: "block w-full bg-gulf-blue-50 rounded-md border-0 px-2 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6"
                    },
                    this.state.district ? React.createElement(
                      "option",
                      null,
                      this.state.district
                    ) : React.createElement(
                      "option",
                      null,
                      "Select district"
                    ),
                    this.state.districts.map(function (district) {
                      return React.createElement(
                        "option",
                        { value: district.id },
                        district.district
                      );
                    })
                  )
                )
              ),
              React.createElement(
                "div",
                { style: { flex: 0.25 }, className: "flex justify-center" },
                React.createElement(
                  "div",
                  { className: "w-full" },
                  React.createElement(
                    "select",
                    {
                      id: "selectDepot",
                      name: "selectedDepot",
                      onChange: function onChange(event) {
                        return _this2.onFilterSelectCenters("depot", event);
                      },
                      className: "block w-full bg-gulf-blue-50 rounded-md border-0 px-2 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6"
                    },
                    this.state.depot ? React.createElement(
                      "option",
                      null,
                      this.state.depot
                    ) : React.createElement(
                      "option",
                      null,
                      "Select Centre"
                    ),
                    this.state.depots ? this.state.depots.map(function (depot) {
                      return React.createElement(
                        "option",
                        { value: depot.id },
                        depot.depot
                      );
                    }) : null
                  )
                )
              )
            )
          )
        ),
        React.createElement(
          "div",
          { className: "grid grid-cols-5 gap-4 mt-5" },
          React.createElement(
            "div",
            { className: "w-auto bg-gradient-to-r from-gulf-blue-100 to-gulf-blue-300 drop-shadow-md shadow shadow-gulf-blue-300 text-gulf-blue-900 rounded px-2 py-2" },
            React.createElement(
              "div",
              { className: "sm:flex lg:items-center lg:justify-between" },
              React.createElement(
                "div",
                { className: "min-w-0 flex-1" },
                React.createElement(
                  "div",
                  { className: "text-center text-lg font-bold text-gulf-blue-950 sm:truncate sm:tracking-tight" },
                  "REVENUE ASSURANCE"
                ),
                React.createElement(
                  "div",
                  { className: "mt-2" },
                  React.createElement(
                    "a",
                    { href: "#" },
                    React.createElement(
                      "div",
                      { className: "border border-gulf-blue-200 hover:bg-gulf-blue-400 rounded-lg px-3 py-1 justify-between items-center sm:mt-0 sm:flex-row sm:flex-wrap" },
                      React.createElement(
                        "div",
                        { className: "col-xl col-sm text-center mb-xl-0 mb-4" },
                        React.createElement(
                          "div",
                          { className: "card" },
                          React.createElement(
                            "div",
                            { className: "card-body p-2" },
                            React.createElement(
                              "div",
                              { className: "row" },
                              React.createElement(
                                "div",
                                { className: "col-8" },
                                React.createElement(
                                  "div",
                                  { className: "numbers" },
                                  React.createElement(
                                    "p",
                                    { className: "text-xs mb-0 text-capitalize font-weight-bold" },
                                    "Points Visited"
                                  ),
                                  React.createElement(
                                    "h6",
                                    { className: "font-weight-bolder mb-0" },
                                    "600"
                                  )
                                ),
                                React.createElement(
                                  "div",
                                  { className: "overflow-hidden bg-blue-50 h-1.5 rounded-full w-full" },
                                  React.createElement("span", {
                                    className: "h-full bg-gulf-blue-900 w-full block rounded-full",
                                    style: { width: "60%" }
                                  })
                                ),
                                React.createElement(
                                  "p",
                                  { className: "text-xs text-muted mt-2 mb-0" },
                                  "Monthly Target:1000"
                                )
                              )
                            )
                          )
                        )
                      )
                    )
                  )
                )
              )
            )
          ),
          React.createElement(
            "div",
            { className: "w-auto bg-gradient-to-r from-jade-100 to-jade-300 drop-shadow-md shadow shadow-jade-300 text-jade-900 rounded px-2 py-2" },
            React.createElement(
              "div",
              { className: "sm:flex lg:items-center lg:justify-between" },
              React.createElement(
                "div",
                { className: "min-w-0 flex-1" },
                React.createElement(
                  "div",
                  { className: "text-center text-lg font-bold text-jade-900 sm:truncate sm:tracking-tight" },
                  "GROWTH"
                ),
                React.createElement(
                  "div",
                  { className: "mt-2" },
                  React.createElement(
                    "a",
                    { href: "#" },
                    React.createElement(
                      "div",
                      { className: "border border-jade-200 hover:bg-jade-400 rounded-lg px-3 py-1 justify-between items-center sm:mt-0 sm:flex-row sm:flex-wrap" },
                      React.createElement(
                        "div",
                        { className: "col-xl col-sm text-center mb-xl-0 mb-4" },
                        React.createElement(
                          "div",
                          { className: "card" },
                          React.createElement(
                            "div",
                            { className: "card-body p-2" },
                            React.createElement(
                              "div",
                              { className: "row" },
                              React.createElement(
                                "div",
                                { className: "col-8" },
                                React.createElement(
                                  "div",
                                  { className: "numbers" },
                                  React.createElement(
                                    "p",
                                    { className: "text-xs mb-0 text-capitalize font-weight-bold" },
                                    "Connected"
                                  ),
                                  React.createElement(
                                    "h6",
                                    { className: "font-weight-bolder mb-0" },
                                    "900"
                                  )
                                ),
                                React.createElement(
                                  "div",
                                  { className: "overflow-hidden bg-jade-50 h-1.5 rounded-full w-full" },
                                  React.createElement("span", {
                                    className: "h-full bg-jade-900 w-full block rounded-full",
                                    style: { width: "90%" }
                                  })
                                ),
                                React.createElement(
                                  "p",
                                  { className: "text-xs text-muted mt-2 mb-0" },
                                  "YTD Target:1000"
                                )
                              )
                            )
                          )
                        )
                      )
                    )
                  )
                )
              )
            )
          ),
          React.createElement(
            "div",
            { className: "w-auto bg-gradient-to-r from-royal-heath-100 to-royal-heath-300 drop-shadow-md shadow shadow-royal-heath-300 text-royal-heath-900 rounded px-2 py-2" },
            React.createElement(
              "div",
              { className: "sm:flex lg:items-center lg:justify-between" },
              React.createElement(
                "div",
                { className: "min-w-0 flex-1" },
                React.createElement(
                  "div",
                  { className: "text-center text-lg font-bold text-royal-heath-950 sm:truncate sm:tracking-tight" },
                  "INSPECTIONS"
                ),
                React.createElement(
                  "div",
                  { className: "mt-2" },
                  React.createElement(
                    "a",
                    { href: "#" },
                    React.createElement(
                      "div",
                      { className: "border border-royal-heath-200 hover:bg-royal-heath-400 rounded-lg px-3 py-1 justify-between items-center sm:mt-0 sm:flex-row sm:flex-wrap" },
                      React.createElement(
                        "div",
                        { className: "col-xl col-sm text-center mb-xl-0 mb-4" },
                        React.createElement(
                          "div",
                          { className: "card" },
                          React.createElement(
                            "div",
                            { className: "card-body p-2" },
                            React.createElement(
                              "div",
                              { className: "row" },
                              React.createElement(
                                "div",
                                { className: "col-8" },
                                React.createElement(
                                  "div",
                                  { className: "numbers" },
                                  React.createElement(
                                    "p",
                                    { className: "text-xs mb-0 text-capitalize font-weight-bold" },
                                    "Inspected"
                                  ),
                                  React.createElement(
                                    "h6",
                                    { className: "font-weight-bolder mb-0" },
                                    "100"
                                  )
                                ),
                                React.createElement(
                                  "div",
                                  { className: "overflow-hidden bg-royal-heath-50 h-1.5 rounded-full w-full" },
                                  React.createElement("span", {
                                    className: "h-full bg-royal-heath-900 w-full block rounded-full",
                                    style: { width: "10%" }
                                  })
                                ),
                                React.createElement(
                                  "p",
                                  { className: "text-xs text-muted mt-2 mb-0" },
                                  "YTD Target:1000"
                                )
                              )
                            )
                          )
                        )
                      )
                    )
                  )
                )
              )
            )
          ),
          React.createElement(
            "div",
            { className: "w-auto bg-gradient-to-r from-gulf-blue-100 to-gulf-blue-300 drop-shadow-md shadow shadow-gulf-blue-300 text-gulf-blue-900 rounded px-2 py-2" },
            React.createElement(
              "div",
              { className: "sm:flex lg:items-center lg:justify-between" },
              React.createElement(
                "div",
                { className: "min-w-0 flex-1" },
                React.createElement(
                  "div",
                  { className: "text-center text-lg font-bold text-gulf-blue-950 sm:truncate sm:tracking-tight" },
                  "FAULTS"
                ),
                React.createElement(
                  "div",
                  { className: "mt-2" },
                  React.createElement(
                    "a",
                    { href: "#" },
                    React.createElement(
                      "div",
                      { className: "border border-gulf-blue-200 hover:bg-gulf-blue-400 rounded-lg px-3 py-1 justify-between items-center sm:mt-0 sm:flex-row sm:flex-wrap" },
                      React.createElement(
                        "div",
                        { className: "col-xl col-sm text-center mb-xl-0 mb-4" },
                        React.createElement(
                          "div",
                          { className: "card" },
                          React.createElement(
                            "div",
                            { className: "card-body p-2" },
                            React.createElement(
                              "div",
                              { className: "row" },
                              React.createElement(
                                "div",
                                { className: "col-8" },
                                React.createElement(
                                  "div",
                                  { className: "numbers" },
                                  React.createElement(
                                    "p",
                                    { className: "text-xs mb-0 text-capitalize font-weight-bold" },
                                    "Unresolved"
                                  ),
                                  React.createElement(
                                    "h6",
                                    { className: "font-weight-bolder mb-0" },
                                    "700"
                                  )
                                ),
                                React.createElement(
                                  "div",
                                  { className: "overflow-hidden bg-gulf-blue-50 h-1.5 rounded-full w-full" },
                                  React.createElement("span", {
                                    className: "h-full bg-gulf-blue-900 w-full block rounded-full",
                                    style: { width: "70%" }
                                  })
                                ),
                                React.createElement(
                                  "p",
                                  { className: "text-xs text-muted mt-2 mb-0" },
                                  "YTD Target:1000"
                                )
                              )
                            )
                          )
                        )
                      )
                    )
                  )
                )
              )
            )
          ),
          React.createElement(
            "div",
            { className: "w-auto bg-gradient-to-r from-jade-100 to-jade-300 drop-shadow-md shadow shadow-jade-300 text-jade-900 rounded px-2 py-2" },
            React.createElement(
              "div",
              { className: "sm:flex lg:items-center lg:justify-between" },
              React.createElement(
                "div",
                { className: "min-w-0 flex-1" },
                React.createElement(
                  "div",
                  { className: "text-center text-lg font-bold text-jade-950 sm:truncate sm:tracking-tight" },
                  "MAINTENANCE"
                ),
                React.createElement(
                  "div",
                  { className: "mt-2" },
                  React.createElement(
                    "a",
                    { href: "#" },
                    React.createElement(
                      "div",
                      { className: "border border-jade-200 hover:bg-jade-400 rounded-lg px-3 py-1 justify-between items-center sm:mt-0 sm:flex-row sm:flex-wrap" },
                      React.createElement(
                        "div",
                        { className: "col-xl col-sm text-center mb-xl-0 mb-4" },
                        React.createElement(
                          "div",
                          { className: "card" },
                          React.createElement(
                            "div",
                            { className: "card-body p-2" },
                            React.createElement(
                              "div",
                              { className: "row" },
                              React.createElement(
                                "div",
                                { className: "col-8" },
                                React.createElement(
                                  "div",
                                  { className: "numbers" },
                                  React.createElement(
                                    "p",
                                    { className: "text-xs mb-0 text-capitalize font-weight-bold" },
                                    "Maintained"
                                  ),
                                  React.createElement(
                                    "h6",
                                    { className: "font-weight-bolder mb-0" },
                                    "950"
                                  )
                                ),
                                React.createElement(
                                  "div",
                                  { className: "overflow-hidden bg-jade-50 h-1.5 rounded-full w-full" },
                                  React.createElement("span", {
                                    className: "h-full bg-jade-900 w-full block rounded-full",
                                    style: { width: "95%" }
                                  })
                                ),
                                React.createElement(
                                  "p",
                                  { className: "text-xs text-muted mt-2 mb-0" },
                                  "YTD Target:1000"
                                )
                              )
                            )
                          )
                        )
                      )
                    )
                  )
                )
              )
            )
          )
        ),
        React.createElement(
          "div",
          { className: "grid grid-cols-5 gap-4 mt-10" },
          React.createElement(
            "div",
            { className: "w-auto bg-gulf-blue-200 drop-shadow-md shadow shadow-gulf-blue-300 text-gray-900 rounded px-2 py-2" },
            React.createElement(
              "div",
              { className: "sm:flex lg:items-center lg:justify-between" },
              React.createElement(
                "div",
                { className: "min-w-0 flex-1" },
                React.createElement(
                  "div",
                  { className: "text-center text-lg font-bold sm:truncate sm:tracking-tight" },
                  "Top PBNC Customers"
                ),
                React.createElement(
                  "div",
                  { style: { height: "14rem" }, className: "mt-2 h-20 overflow-auto" },
                  React.createElement(
                    "a",
                    { href: "#" },
                    React.createElement(
                      "table",
                      { className: "table-auto" },
                      React.createElement(
                        "thead",
                        null,
                        React.createElement(
                          "tr",
                          null,
                          React.createElement("th", null),
                          React.createElement("th", null),
                          React.createElement("th", null)
                        )
                      ),
                      React.createElement(
                        "tbody",
                        null,
                        this.state.pbncs ? this.state.pbncs.map(function (pbnc, index) {
                          return React.createElement(
                            "tr",
                            null,
                            React.createElement(
                              "td",
                              null,
                              index + 1
                            ),
                            React.createElement(
                              "td",
                              null,
                              pbnc.name
                            ),
                            React.createElement(
                              "td",
                              null,
                              pbnc.amount
                            )
                          );
                        }) : null
                      )
                    )
                  )
                )
              )
            )
          ),
          React.createElement(
            "div",
            { className: "w-auto bg-royal-heath-200 drop-shadow-md shadow shadow-royal-heath-300 text-gray-900 rounded px-2 py-2" },
            React.createElement(
              "div",
              { className: "sm:flex lg:items-center lg:justify-between" },
              React.createElement(
                "div",
                { className: "min-w-0 flex-1" },
                React.createElement(
                  "div",
                  { className: "text-center text-lg font-bold sm:truncate sm:tracking-tight" },
                  "Unresolved Power Outages"
                ),
                React.createElement(
                  "div",
                  { style: { height: "14rem" }, className: "mt-2 h-20 overflow-auto" },
                  React.createElement(
                    "a",
                    { href: "#" },
                    React.createElement(
                      "table",
                      { className: "table-auto" },
                      React.createElement(
                        "thead",
                        null,
                        React.createElement(
                          "tr",
                          null,
                          React.createElement("th", null),
                          React.createElement("th", null)
                        )
                      ),
                      React.createElement(
                        "tbody",
                        null,
                        this.state.upos ? this.state.upos.map(function (upo, index) {
                          return React.createElement(
                            "tr",
                            null,
                            React.createElement(
                              "td",
                              null,
                              index + 1
                            ),
                            React.createElement(
                              "td",
                              null,
                              upo.description
                            )
                          );
                        }) : null
                      )
                    )
                  )
                )
              )
            )
          ),
          React.createElement(
            "div",
            { className: "w-auto bg-citron-200 drop-shadow-md shadow shadow-citron-300 text-gray-900 rounded px-2 py-2" },
            React.createElement(
              "div",
              { className: "sm:flex lg:items-center lg:justify-between" },
              React.createElement(
                "div",
                { className: "min-w-0 flex-1" },
                React.createElement(
                  "div",
                  { className: "text-center text-lg font-bold text-gulf-blue-950 sm:truncate sm:tracking-tight" },
                  "Inspection breakdown"
                ),
                React.createElement(
                  "div",
                  { style: { height: "14rem" }, className: "mt-2 h-20 overflow-auto" },
                  React.createElement(
                    "a",
                    { href: "#" },
                    React.createElement("canvas", { id: "Inspection", ref: this.inspectionPieChartRef })
                  )
                )
              )
            )
          ),
          React.createElement(
            "div",
            { className: "w-auto bg-gulf-blue-200 drop-shadow-md shadow shadow-gulf-blue-300 text-gulf-blue-900 rounded px-2 py-2" },
            React.createElement(
              "div",
              { className: "sm:flex lg:items-center lg:justify-between" },
              React.createElement(
                "div",
                { className: "min-w-0 flex-1" },
                React.createElement(
                  "div",
                  { className: "text-center text-lg font-bold text-gulf-blue-950 sm:truncate sm:tracking-tight" },
                  "Top Debtors"
                ),
                React.createElement(
                  "div",
                  { style: { height: "14rem" }, className: "mt-2 h-20 overflow-auto" },
                  React.createElement(
                    "a",
                    { href: "#" },
                    React.createElement(
                      "table",
                      { className: "table-auto" },
                      React.createElement(
                        "thead",
                        null,
                        React.createElement(
                          "tr",
                          null,
                          React.createElement("th", null),
                          React.createElement("th", null),
                          React.createElement("th", null)
                        )
                      ),
                      React.createElement(
                        "tbody",
                        null,
                        this.state.tds ? this.state.tds.map(function (td, index) {
                          return React.createElement(
                            "tr",
                            null,
                            React.createElement(
                              "td",
                              null,
                              index + 1
                            ),
                            React.createElement(
                              "td",
                              null,
                              td.name
                            ),
                            React.createElement(
                              "td",
                              null,
                              td.amount
                            )
                          );
                        }) : null
                      )
                    )
                  )
                )
              )
            )
          ),
          React.createElement(
            "div",
            { className: "w-auto bg-citron-200 drop-shadow-md shadow shadow-citron-300 text-gray-900 rounded px-2 py-2" },
            React.createElement(
              "div",
              { className: "sm:flex lg:items-center lg:justify-between" },
              React.createElement(
                "div",
                { className: "min-w-0 flex-1" },
                React.createElement(
                  "div",
                  { className: "text-center text-lg font-bold text-gulf-blue-950 sm:truncate sm:tracking-tight" },
                  "Maintanance breakdown"
                ),
                React.createElement(
                  "div",
                  { style: { height: "14rem" }, className: "mt-2 h-20 overflow-auto" },
                  React.createElement(
                    "a",
                    { href: "#" },
                    React.createElement("canvas", { id: "Maintenance", ref: this.mmtPieChartRef })
                  )
                )
              )
            )
          )
        ),
        React.createElement(
          "div",
          { className: "grid grid-cols-2 mt-4 gap-4" },
          React.createElement(
            "div",
            { className: "w-auto bg-gulf-blue-200 shadow shadow-gulf-blue-300 text-gulf-blue-700 rounded px-2 py-2" },
            React.createElement(
              "div",
              { className: "sm:flex lg:items-center lg:justify-between" },
              React.createElement(
                "div",
                { className: "min-w-0 flex-1" },
                React.createElement(
                  "div",
                  { className: "text-center text-lg font-bold text-gulf-blue-950 sm:truncate sm:tracking-tight" },
                  "Maintanance"
                ),
                React.createElement(
                  "div",
                  { className: "flex justify-center" },
                  React.createElement(
                    "select",
                    {
                      id: "filterMaintenanceButton",
                      className: "block w-full rounded-md border-0 px-2 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6"
                    },
                    this.state.current_month ? React.createElement(
                      "option",
                      { value: this.state.current_month.id },
                      this.state.current_month.name
                    ) : null,
                    React.createElement(
                      "option",
                      { value: "1" },
                      "January"
                    ),
                    React.createElement(
                      "option",
                      { value: "2" },
                      "February"
                    ),
                    React.createElement(
                      "option",
                      { value: "3" },
                      "March"
                    ),
                    React.createElement(
                      "option",
                      { value: "4" },
                      "April"
                    ),
                    React.createElement(
                      "option",
                      { value: "5" },
                      "May"
                    ),
                    React.createElement(
                      "option",
                      { value: "6" },
                      "June"
                    ),
                    React.createElement(
                      "option",
                      { value: "7" },
                      "July"
                    ),
                    React.createElement(
                      "option",
                      { value: "8" },
                      "August"
                    ),
                    React.createElement(
                      "option",
                      { value: "9" },
                      "September"
                    ),
                    React.createElement(
                      "option",
                      { value: "10" },
                      "October"
                    ),
                    React.createElement(
                      "option",
                      { value: "11" },
                      "November"
                    ),
                    React.createElement(
                      "option",
                      { value: "12" },
                      "December"
                    )
                  )
                ),
                React.createElement(
                  "div",
                  null,
                  React.createElement("canvas", {
                    id: "maintenanceBarChart",
                    ref: this.mmtBarChartRef,
                    className: "chart-canvas",
                    width: "400",
                    height: "400"
                  })
                )
              )
            )
          ),
          React.createElement(
            "div",
            { className: "w-auto bg-gulf-blue-200 shadow shadow-gulf-blue-300 text-gulf-blue-700 rounded px-2 py-2" },
            React.createElement(
              "div",
              { className: "sm:flex lg:items-center lg:justify-between" },
              React.createElement(
                "div",
                { className: "min-w-0 flex-1" },
                React.createElement(
                  "div",
                  { className: "text-center text-lg font-bold text-gulf-blue-950 sm:truncate sm:tracking-tight" },
                  "Inspections"
                ),
                React.createElement(
                  "div",
                  { className: "flex justify-center" },
                  React.createElement("input", {
                    id: "selectInspForm",
                    type: "hidden",
                    name: "csrfmiddlewaretoken",
                    value: "{{csrf_token}}"
                  }),
                  React.createElement(
                    "select",
                    {
                      id: "filterInspectionsButton",
                      className: "block w-full rounded-md border-0 px-2 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6"
                    },
                    this.state.current_month ? React.createElement(
                      "option",
                      { value: this.state.current_month.id },
                      this.state.current_month.name
                    ) : null,
                    React.createElement(
                      "option",
                      { value: "1" },
                      "January"
                    ),
                    React.createElement(
                      "option",
                      { value: "2" },
                      "February"
                    ),
                    React.createElement(
                      "option",
                      { value: "3" },
                      "March"
                    ),
                    React.createElement(
                      "option",
                      { value: "4" },
                      "April"
                    ),
                    React.createElement(
                      "option",
                      { value: "5" },
                      "May"
                    ),
                    React.createElement(
                      "option",
                      { value: "6" },
                      "June"
                    ),
                    React.createElement(
                      "option",
                      { value: "7" },
                      "July"
                    ),
                    React.createElement(
                      "option",
                      { value: "8" },
                      "August"
                    ),
                    React.createElement(
                      "option",
                      { value: "9" },
                      "September"
                    ),
                    React.createElement(
                      "option",
                      { value: "10" },
                      "October"
                    ),
                    React.createElement(
                      "option",
                      { value: "11" },
                      "November"
                    ),
                    React.createElement(
                      "option",
                      { value: "12" },
                      "December"
                    )
                  )
                ),
                React.createElement(
                  "div",
                  null,
                  React.createElement("canvas", {
                    id: "inspectionBarChart",
                    ref: this.inspectionBarChartRef,
                    className: "chart-canvas",
                    width: "400",
                    height: "400"
                  })
                )
              )
            )
          )
        )
      );
    }
  }]);

  return DashboardFilter;
}(React.Component);

var domContainer = document.querySelector("#dashboard_filters");
var spid = domContainer.getAttribute("data-spid");
var region = domContainer.getAttribute("data-region");
var district = domContainer.getAttribute("data-district");
var section = domContainer.getAttribute("data-section");
var depot = domContainer.getAttribute("data-depot");
ReactDOM.render(e(DashboardFilter, { spid: spid, region: region, district: district, section: section }), domContainer);