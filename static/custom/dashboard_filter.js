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
      upos: [],
      tds: [],
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

      authUser: {}
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
      depot: this.props.depot,
    });
    this.getRegions();
    this.getDashboardData();
  }

  onFilterSelectCenters(name_, event) {
    let { name, value } = event.target
    if(name_ === "region") {
      let dist = this.state.allDistricts.filter((_district) => _district.region_id === value)
      this.setState({
        districts: dist, 
        selectedRegion: value,
        selectedDepot: "",
        selectedDistrict: "",
      });
      this.getFilterData(value, "", "")
    } else if(name_ === "district") {
      console.log("district: ", value, this.state.allDepots)
      let depos = this.state.allDepots.filter((_depot) => parseInt(_depot.district_id) === parseInt(value))
      console.log("depots: ", depos)
      this.setState({
        depots: depos, 
        selectedDepot: "",
        selectedDistrict: value,
        selectedRegion: "",
      });
      this.getFilterData("", value, "")
    } else if(name_ === "depot"){
      console.log("depot: ", value)
      this.setState({
        selectedDepot: value,
        selectedDistrict: "",
        selectedRegion: "",
      })
      this.getFilterData("", "", value)
    }

    // Filter by depot, filter by month, filter combined
    
  }

  getFilterData = (selectedRegion, selectedDistrict, selectedDepot) => {
    fetch(`${BASE_URL}/dashboards/dashboard_filter`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": this.getCookie("csrftoken"),
        },
        body: JSON.stringify({
          region: selectedRegion,
          district: selectedDistrict,
          depot: selectedDepot,
        }),
      })
      .then((response) => response.json())
      .then((data) => {

        console.log("data: ", data)
        if(data){
          console.log("running ...")
          let inspection_locations_,inspections_count_,maintenance_locations_,maintenance_count_,mtn_;
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
              pbncs: data.pbncs,
              upos: data.upos,
              tds: data.tds,
          });

          this.initComponents();
        }
      })
  };

  initComponents = () => {
    const baseColors = [
      "#f62c06",
      "#94834b",
      "#1288fe",
      "#c8a806",
      "#f02e0e",
      "#e118d5",
      "#0fb11c",
      "#3b3cf0",
      "#188350",
      "#c93986",
      "#90921e",
    ];
    // Destroy the previous Chart instance, if it exists
    if (this.inspectionChart) {
      this.inspectionChart.destroy();
    }
    if(this.inspectionBarChart) {
      this.inspectionBarChart.destroy();
    }
    if(this.mmtPieChart){
      this.mmtPieChart.destroy();
    }
    if(this.mmtBarChart){
      this.mmtBarChart.destroy();
    }

    var inspectionData = {
      labels: this.state.inspection_locations,
      datasets: [
        {
          data: this.state.inspections_count,
          backgroundColor: baseColors,
          hoverBackgroundColor: baseColors,
        },
      ],
    };

    this.inspectionChart = new Chart(this.inspectionPieChartRef.current, {
      type: "pie",
      data: inspectionData,
      options: {
        plugins: {
          legend: {
            position: "left", // or 'bottom', 'left', 'right'
          },
        },
      },
    });

    var inspectionBarData = {
      labels: this.state.inspection_locations,
      datasets: [
        {
          data: this.state.inspections_count,
          backgroundColor: baseColors,
          hoverBackgroundColor: baseColors,
        },
      ],
    };

    this.inspectionBarChart = new Chart(this.inspectionBarChartRef.current, {
      type: "bar",
      data: inspectionBarData,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false,
          },
        },
        scales: {
          y: {
            display: true,
            title: {
              display: true,
              text: "Frequency",
            },
            grid: {
              drawBorder: false,
              display: true,
              drawOnChartArea: true,
              drawTicks: false,
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
                lineHeight: 2,
              },
              color: "#282a87",
            },
          },
          x: {
            grid: {
              drawBorder: false,
              display: false,
              drawOnChartArea: false,
              drawTicks: false,
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
                lineHeight: 2,
              },
              color: "#282a87",
            },
          },
        },
      },
    });

    // Define the data for the pie chart (replace with your own data)
    var maintenanceData = {
      labels: this.state.maintenance_locations,
      datasets: [
        {
          data: this.state.maintenance_count,
          backgroundColor: baseColors,
          hoverBackgroundColor: baseColors,
        },
      ],
    };

    // Create the pie chart
    this.mmtPieChart = new Chart(this.mmtPieChartRef.current, {
      type: "pie",
      data: maintenanceData,
      options: {
        plugins: {
          legend: {
            position: "left", // or 'bottom', 'left', 'right'
          },
        },
      },
    });

    var mnt = this.state.mnt;
    let maintenanceDataset = [];

    Object.keys(mnt).forEach((key) => {
      maintenanceDataset.push({
        label: key,
        data: mnt[key], // [1,2,3,4]
        fill: 2,
      });
    });

    var maintenanceBarData = {
      labels: ["1", "2", "3", "4"], // ['January', 'December'],
      datasets: maintenanceDataset.map((data) => {
        return {
          label: data.label,
          data: data.data,
          fill: 2,
        };
      }),
    };

    this.mmtBarChart = new Chart(this.mmtBarChartRef.current, {
      type: "line",
      data: maintenanceBarData,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
          },
          filler: {
            propagate: false,
          },
          "samples-filler-analyser": {
            target: "chart-analyser",
          },
        },
        scales: {
          y: {
            display: true,
            title: {
              display: true,
              text: "Frequency",
            },
            grid: {
              drawBorder: false,
              display: true,
              drawOnChartArea: true,
              drawTicks: false,
              borderDash: [5, 5],
            },
            ticks: {
              display: true,
              padding: 10,
              color: "#282a87",
              font: {
                size: 14,
                family: "Open Sans",
                style: "normal",
                lineHeight: 2,
              },
            },
          },
          x: {
            display: true,
            title: {
              display: true,
              text: "Week",
            },
            grid: {
              drawBorder: false,
              display: false,
              drawOnChartArea: false,
              drawTicks: false,
              borderDash: [5, 5],
            },
            ticks: {
              display: true,
              color: "#282a87",
              padding: 20,
              font: {
                size: 14,
                family: "Open Sans",
                style: "normal",
                lineHeight: 2,
              },
            },
          },
        },
      },
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
    (event) => {
      const newValue = event//event.target.value;

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
        Object.keys(res).forEach((key) => {
          mChart.data.datasets.push({
            label: key,
            data: res[key],
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
    const newValue = event //event.target.value;

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
    xhr.open(
      "GET",
      `${BASE_URL}/dashboards/inspections/ajax?month=${month}`
    ); // Replace with your actual URL and parameters
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
          data: valuesList,
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

    fetch(`${BASE_URL}/dashboards/regions`)
      .then((response) => response.json())
      .then((data) => {
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
          pbncs: data.pbncs,
          upos: data.upos,
          tds: data.tds,
        });
      });
  };

  getDashboardData = () => {
    fetch(`${BASE_URL}/dashboards/dashboard_data`)
      .then((response) => response.json())
      .then((data) => {

        console.log("data: ", data)
        let inspection_locations_ = JSON.parse(data.inspection_locations)
        let inspections_count_ = JSON.parse(data.inspections_count)
        let maintenance_locations_ = JSON.parse(data.maintenance_locations)
        let maintenance_count_ = JSON.parse(data.maintenance_count)
        let mtn_ = data.mtn

        this.setState({
            inspection_locations: inspection_locations_,
            inspections_count: inspections_count_,
            maintenance_locations: maintenance_locations_,
            maintenance_count: maintenance_count_,
            mnt: mtn_,
            pbncs: data.pbncs,
            upos: data.upos,
            tds: data.tds,
        });

        this.initComponents();
      })
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

  render() {


    return (
      <div>
        <div className="grid grid-cols-1 gap-4">
          <div className="w-auto bg-white drop-shadow-md shadow shadow-gulf-blue-300 text-gulf-blue-950 rounded px-4 py-4">
            <div className="flex justify-around">
              <div style={{flex: 0.25}} className="flex justify-center">
                <div className="w-full">
                  <select
                    id="selectRegion"
                    name="selectedRegion"
                    onChange={(event) => this.onFilterSelectCenters("region", event)}
                    className="block w-full bg-gulf-blue-50 rounded-md border-0 px-2 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6"
                  >
                    {this.state.region ? (
                      <option>{this.state.region}</option>
                    ) : (
                      <option>Select Region</option>
                    )}
                    {this.state.regions.map((region) => (
                      <option value={region.id}>{region.region}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div style={{flex: 0.25}} className="flex justify-center">
                <div className="w-full">
                  <select
                    id="selectDistrict"
                    name="selectedDistrict"
                    onChange={(event) => this.onFilterSelectCenters("district", event)}
                    className="block w-full bg-gulf-blue-50 rounded-md border-0 px-2 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6"
                  >
                    {this.state.district ? (
                      <option>{this.state.district}</option>
                    ) : (
                      <option>Select district</option>
                    )}
                    {this.state.districts.map((district) => (
                      <option value={district.id}>{district.district}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div style={{flex: 0.25}} className="flex justify-center">
                <div className="w-full">
                  <select
                    id="selectDepot"
                    name="selectedDepot"
                    onChange={(event) => this.onFilterSelectCenters("depot", event)}
                    className="block w-full bg-gulf-blue-50 rounded-md border-0 px-2 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6"
                  >
                    {this.state.depot ? (
                      <option>{this.state.depot}</option>
                    ) : (
                      <option>Select Centre</option>
                    )}
                    {this.state.depots? this.state.depots.map((depot) => (
                      <option value={depot.id}>{depot.depot}</option>
                    )): null}
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
                                  <h6 className="font-weight-bolder mb-0">1000 GWh</h6>
                                </div>

                                <div className="overflow-hidden bg-blue-50 h-1.5 rounded-full w-full">
                                  <span
                                    className="h-full bg-gulf-blue-900 w-full block rounded-full"
                                    style={{width: "10%"}}
                                  ></span>
                                </div>
                                <p className="text-xs text-muted mt-2 mb-0">
                                  Monthly Target:100000 GWh
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
                                  <h6 className="font-weight-bolder mb-0">9000</h6>
                                </div>

                                <div className="overflow-hidden bg-jade-50 h-1.5 rounded-full w-full">
                                  <span
                                    className="h-full bg-jade-900 w-full block rounded-full"
                                    style={{width: "90%"}}
                                  ></span>
                                </div>
                                <p className="text-xs text-muted mt-2 mb-0">
                                  YTD Target:10000 Clients
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
                                  <h6 className="font-weight-bolder mb-0">USD 17000000</h6>
                                  <h6 className="font-weight-bolder mb-0">ZWL 6000000000</h6>
                                </div>

                                <div className="overflow-hidden bg-royal-heath-50 h-1.5 rounded-full w-full">
                                  <span
                                    className="h-full bg-royal-heath-900 w-full block rounded-full"
                                    style={{width: "17%"}}
                                  ></span>
                                </div>
                                <p className="text-xs text-muted mt-2 mb-0">
                                  YTD Target:USD 10000000
                                </p>
                                <p className="text-xs text-muted mt-2 mb-0">
                                  YTD Target:ZWL 6000000000
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
                                  <h6 className="font-weight-bolder mb-0">8000</h6>
                                </div>

                                <div className="overflow-hidden bg-gulf-blue-50 h-1.5 rounded-full w-full">
                                  <span
                                    className="h-full bg-gulf-blue-900 w-full block rounded-full"
                                    style={{width: "70%"}}
                                  ></span>
                                </div>
                                <p className="text-xs text-muted mt-2 mb-0">
                                  YTD Target:10000
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
                                  <h6 className="font-weight-bolder mb-0">950</h6>
                                </div>

                                <div className="overflow-hidden bg-jade-50 h-1.5 rounded-full w-full">
                                  <span
                                    className="h-full bg-jade-900 w-full block rounded-full"
                                    style={{width: "95%"}}
                                  ></span>
                                </div>
                                <p className="text-xs text-muted mt-2 mb-0">
                                  YTD Target:1000
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
        <div className="grid grid-cols-5 gap-4 mt-10">
          <div className="w-auto bg-gulf-blue-200 drop-shadow-md shadow shadow-gulf-blue-300 text-gray-900 rounded px-2 py-2">
            <div className="sm:flex lg:items-center lg:justify-between">
              <div className="min-w-0 flex-1">
                <div className="text-center text-lg font-bold sm:truncate sm:tracking-tight">
                  Top PBNC Customers
                </div>
                <div style={{height: "14rem"}} className="mt-2 h-20 overflow-auto">
                  <a href="#">
                    <table className="table-auto">
                      <thead>
                        <tr>
                          <th></th>
                          <th></th>
                          <th></th>
                        </tr>
                      </thead>
                      <tbody>
                        {this.state.pbncs
                          ? this.state.pbncs.map((pbnc, index) => (
                              <tr>
                                <td>{index + 1}</td>
                                <td>{pbnc.name}</td>
                                <td>{pbnc.amount}</td>
                              </tr>
                            ))
                          : null}
                      </tbody>
                    </table>
                  </a>
                </div>
              </div>
            </div>
          </div>
          <div className="w-auto bg-royal-heath-200 drop-shadow-md shadow shadow-royal-heath-300 text-gray-900 rounded px-2 py-2">
            <div className="sm:flex lg:items-center lg:justify-between">
              <div className="min-w-0 flex-1">
                <div className="text-center text-lg font-bold sm:truncate sm:tracking-tight">
                  Unresolved Power Outages
                </div>
                <div style={{height: "14rem"}} className="mt-2 h-20 overflow-auto">
                  <a href="#">
                    <table className="table-auto">
                      <thead>
                        <tr>
                          <th></th>
                          <th></th>
                        </tr>
                      </thead>
                      <tbody>
                        {this.state.upos
                          ? this.state.upos.map((upo, index) => (
                              <tr>
                                <td>{index + 1}</td>
                                <td>{upo.description}</td>
                              </tr>
                            ))
                          : null}
                      </tbody>
                    </table>
                  </a>
                </div>
              </div>
            </div>
          </div>
          <div className="w-auto bg-citron-200 drop-shadow-md shadow shadow-citron-300 text-gray-900 rounded px-2 py-2">
            <div className="sm:flex lg:items-center lg:justify-between">
              <div className="min-w-0 flex-1">
                <div className="text-center text-lg font-bold text-gulf-blue-950 sm:truncate sm:tracking-tight">
                  Inspection breakdown
                </div>
                <div style={{height: "14rem"}} className="mt-2 h-20 overflow-auto">
                  <a href="#">
                    <canvas id="Inspection" ref={this.inspectionPieChartRef}></canvas>
                  </a>
                </div>
              </div>
            </div>
          </div>
          <div className="w-auto bg-gulf-blue-200 drop-shadow-md shadow shadow-gulf-blue-300 text-gulf-blue-900 rounded px-2 py-2">
            <div className="sm:flex lg:items-center lg:justify-between">
              <div className="min-w-0 flex-1">
                <div className="text-center text-lg font-bold text-gulf-blue-950 sm:truncate sm:tracking-tight">
                  Top Debtors
                </div>
                <div style={{height: "14rem"}} className="mt-2 h-20 overflow-auto">
                  <a href="#">
                    <table className="table-auto">
                      <thead>
                        <tr>
                          <th></th>
                          <th></th>
                          <th></th>
                        </tr>
                      </thead>
                      <tbody>
                        {this.state.tds
                          ? this.state.tds.map((td, index) => (
                              <tr>
                                <td>{(index + 1)}</td>
                                <td>{td.name}</td>
                                <td>{td.amount}</td>
                              </tr>
                            ))
                          : null}
                      </tbody>
                    </table>
                  </a>
                </div>
              </div>
            </div>
          </div>
          <div className="w-auto bg-citron-200 drop-shadow-md shadow shadow-citron-300 text-gray-900 rounded px-2 py-2">
            <div className="sm:flex lg:items-center lg:justify-between">
              <div className="min-w-0 flex-1">
                <div className="text-center text-lg font-bold text-gulf-blue-950 sm:truncate sm:tracking-tight">
                  Maintenance breakdown
                </div>
                <div style={{height: "14rem"}} className="mt-2 h-20 overflow-auto">
                  <a href="#">
                    <canvas id="Maintenance" ref={this.mmtPieChartRef}></canvas>
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div className="grid grid-cols-2 mt-4 gap-4">
          <div className="w-auto bg-gulf-blue-200 shadow shadow-gulf-blue-300 text-gulf-blue-700 rounded px-2 py-2">
            <div className="sm:flex lg:items-center lg:justify-between">
              <div className="min-w-0 flex-1">
                <div className="text-center text-lg font-bold text-gulf-blue-950 sm:truncate sm:tracking-tight">
                  Maintenance
                </div>
                <div className="flex justify-center">
                  <select
                    id="filterMaintenanceButton"
                    className="block w-full rounded-md border-0 px-2 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6"
                  >
                    {this.state.current_month ? (
                      <option value={this.state.current_month.id}>
                        {this.state.current_month.name}
                      </option>
                    ) : null}
                    <option value="1">January</option>
                    <option value="2">February</option>
                    <option value="3">March</option>
                    <option value="4">April</option>
                    <option value="5">May</option>
                    <option value="6">June</option>
                    <option value="7">July</option>
                    <option value="8">August</option>
                    <option value="9">September</option>
                    <option value="10">October</option>
                    <option value="11">November</option>
                    <option value="12">December</option>
                  </select>
                </div>
                <div>
                  <canvas
                    id="maintenanceBarChart"
                    ref={this.mmtBarChartRef}
                    className="chart-canvas"
                    width="400"
                    height="400"
                  ></canvas>
                </div>
              </div>
            </div>
          </div>
          <div className="w-auto bg-gulf-blue-200 shadow shadow-gulf-blue-300 text-gulf-blue-700 rounded px-2 py-2">
            <div className="sm:flex lg:items-center lg:justify-between">
              <div className="min-w-0 flex-1">
                <div className="text-center text-lg font-bold text-gulf-blue-950 sm:truncate sm:tracking-tight">
                  Inspections
                </div>
                <div className="flex justify-center">
                  <input
                    id="selectInspForm"
                    type="hidden"
                    name="csrfmiddlewaretoken"
                    value="{{csrf_token}}"
                  />
                  <select
                    id="filterInspectionsButton"
                    className="block w-full rounded-md border-0 px-2 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6"
                  >
                    {this.state.current_month ? (
                      <option value={this.state.current_month.id}>
                        {this.state.current_month.name}
                      </option>
                    ) : null}
                    <option value="1">January</option>
                    <option value="2">February</option>
                    <option value="3">March</option>
                    <option value="4">April</option>
                    <option value="5">May</option>
                    <option value="6">June</option>
                    <option value="7">July</option>
                    <option value="8">August</option>
                    <option value="9">September</option>
                    <option value="10">October</option>
                    <option value="11">November</option>
                    <option value="12">December</option>
                  </select>
                </div>
                <div>
                  <canvas
                    id="inspectionBarChart"
                    ref={this.inspectionBarChartRef}
                    className="chart-canvas"
                    width="400"
                    height="400"
                  ></canvas>
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
