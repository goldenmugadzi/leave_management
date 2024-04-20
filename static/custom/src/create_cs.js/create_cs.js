"use strict";

var _createClass = function () { function defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, descriptor.key, descriptor); } } return function (Constructor, protoProps, staticProps) { if (protoProps) defineProperties(Constructor.prototype, protoProps); if (staticProps) defineProperties(Constructor, staticProps); return Constructor; }; }();

function _defineProperty(obj, key, value) { if (key in obj) { Object.defineProperty(obj, key, { value: value, enumerable: true, configurable: true, writable: true }); } else { obj[key] = value; } return obj; }

function _toConsumableArray(arr) { if (Array.isArray(arr)) { for (var i = 0, arr2 = Array(arr.length); i < arr.length; i++) { arr2[i] = arr[i]; } return arr2; } else { return Array.from(arr); } }

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

function _possibleConstructorReturn(self, call) { if (!self) { throw new ReferenceError("this hasn't been initialised - super() hasn't been called"); } return call && (typeof call === "object" || typeof call === "function") ? call : self; }

function _inherits(subClass, superClass) { if (typeof superClass !== "function" && superClass !== null) { throw new TypeError("Super expression must either be null or a function, not " + typeof superClass); } subClass.prototype = Object.create(superClass && superClass.prototype, { constructor: { value: subClass, enumerable: false, writable: true, configurable: true } }); if (superClass) Object.setPrototypeOf ? Object.setPrototypeOf(subClass, superClass) : subClass.__proto__ = superClass; }

var e = React.createElement;

var CreateCS = function (_React$Component) {
  _inherits(CreateCS, _React$Component);

  function CreateCS(props) {
    var _this$state;

    _classCallCheck(this, CreateCS);

    var _this = _possibleConstructorReturn(this, (CreateCS.__proto__ || Object.getPrototypeOf(CreateCS)).call(this, props));

    _this.getCreateData = function () {
      fetch("http://localhost:8000/comparative_schedule/create_data").then(function (response) {
        return response.json();
      }).then(function (data) {
        console.log("data: ", data);
        var plans = data.proc_plans ? data.proc_plans : [];
        var suppliers = data.suppliers ? data.suppliers : [];
        var pr_items = data.pr_items ? data.pr_items : [];
        _this.setState({
          procurement_plans: plans,
          suppliers: suppliers,
          pr_items: pr_items
        });
      });
    };

    _this.onAddCSItem = function (item_id) {
      // check is item already added
      var item = _this.state.cs_items.find(function (item) {
        return item.id === item_id;
      });
      console.log("item: ", item);
      if (item) {
        // update item selected to false
        item.selected = false;
        // update pr_items
        var pr_items = _this.state.pr_items.map(function (_item) {
          if (_item.id === item_id) {
            return item;
          }
          return _item;
        });
        // remove item
        var items = _this.state.cs_items.filter(function (item) {
          return item.id !== item_id;
        });
        _this.setState(Object.assign({}, _this.state, {
          cs_items: items,
          pr_items: pr_items
        }));
      } else {
        // find item in pr_items
        var _item2 = _this.state.pr_items.find(function (item) {
          return item.id === item_id;
        });
        // update pr_item selected to added
        _item2.selected = true;
        // update pr_items
        var _pr_items = _this.state.pr_items.map(function (_item) {
          if (_item.id === item_id) {
            return _item2;
          }
          return _item;
        });

        var item_count = _this.state.cs_item_count + 1;
        _this.setState(Object.assign({}, _this.state, {
          item_count: item_count,
          cs_items: [].concat(_toConsumableArray(_this.state.cs_items), [_item2]),
          pr_items: _pr_items
        }));
        console.log("cs_items: ", _this.state.cs_items);
        console.log("pr_items: ", _this.state.pr_items);
      }
    };

    _this.onAddBidModal = function () {
      var bid_count = _this.state.bid_count + 1;
      _this.setState(Object.assign({}, _this.state, {
        addBidModal: !_this.state.addBidModal,
        bid_count: bid_count,
        currentBid: {
          bid_count: bid_count
        }
      }));
    };

    _this.onUpdateBidModal = function (bid_no) {
      var bid = _this.state.bids.find(function (bid) {
        return bid.bid_no === bid_no;
      });
      _this.setState(Object.assign({}, _this.state, {
        addBidModal: !_this.state.addBidModal,
        currentBid: bid
      }));
    };

    _this.onCloseCurrentBid = function () {
      _this.setState(Object.assign({}, _this.state, {
        currentBid: {},
        addBidModal: false
      }));
    };

    _this.onCurrentBidChange = function (name_, event) {
      var currentBid = _this.state.currentBid;
      if (name_ === "bid_document") {
        var bid_file = event.target.files[0];
        currentBid[name_] = bid_file;
      } else if (name_ === "supplier") {
        var _event$target = event.target,
            name = _event$target.name,
            value = _event$target.value;

        console.log("value: ", value);
        var id_name = value ? value.split("-#-") : [];
        currentBid[name_] = id_name.length > 0 ? id_name[0] : "";
        currentBid["supplier_name"] = id_name.length >= 1 ? id_name[1] : "";
      } else {
        var _event$target2 = event.target,
            _name = _event$target2.name,
            _value = _event$target2.value;

        currentBid[name_] = _value;
      }
      _this.setState(Object.assign({}, _this.state, {
        currentBid: currentBid
      }));
    };

    _this.onCurrentBidItemChange = function (item_id, name_, event) {
      // check if item exists in current bid
      var item = _this.state.currentBid.items ? _this.state.currentBid.items.find(function (item) {
        return item.id === item_id;
      }) : null;
      console.log("item: ", item);
      // if item exists update item
      if (item) {
        var _event$target3 = event.target,
            name = _event$target3.name,
            value = _event$target3.value;

        item[name_] = value;
        // update item in current bid
        var items = _this.state.currentBid.items.map(function (_item) {
          if (_item.id === item_id) {
            return item;
          }
          return _item;
        });
        // update current bid
        var currentBid = _this.state.currentBid;
        currentBid.items = items;
        // update state
        _this.setState(Object.assign({}, _this.state, {
          currentBid: currentBid
        }));
      } else {
        // find item in cs_items
        var _item3 = _this.state.cs_items.find(function (item) {
          return item.id === item_id;
        });
        // create new item
        var new_item = {
          id: _item3.id,
          description: _item3.description,
          quantity: _item3.quantity,
          unit_of_measurement: _item3.unit_of_measurement,
          vat: _item3.vat,
          unit_price: _item3.unit_price,
          total_price: _item3.total_price
        };
        // update current bid items
        var _items = [];
        if (!_this.state.currentBid.items) {
          _items.push(new_item);
        } else {
          _items = [].concat(_toConsumableArray(_this.state.currentBid.items), [new_item]);
        }
        // update current bid
        var _currentBid = _this.state.currentBid;
        _currentBid.items = _items;
        // update state
        _this.setState(Object.assign({}, _this.state, {
          currentBid: _currentBid
        }));
      }
    };

    _this.onCurrentBidSave = function () {
      var currentBid = _this.state.currentBid;
      // check if current bid already exists
      if (currentBid.items) {
        var bid = _this.state.bids.find(function (bid) {
          return bid.bid_no === currentBid.bid_no;
        });
        if (bid) {
          // update bid
          var bids = _this.state.bids.map(function (bid) {
            if (bid.bid_no === currentBid.bid_no) {
              return currentBid;
            }
            return bid;
          });
          _this.setState(Object.assign({}, _this.state, {
            bids: bids,
            currentBid: {},
            addBidModal: false
          }));
        } else {
          // calculate total price for each item
          var items = currentBid.items.map(function (item) {
            item.total_price = item.quantity * item.unit_price;
            return item;
          });
          var _bids = _this.state.bids;
          var _bid = {
            supplier: currentBid.supplier,
            supplier_name: currentBid.supplier_name,
            bid_date: currentBid.bid_date,
            bid_no: currentBid.bid_count,
            bid_document: currentBid.bid_document,
            items: items
          };
          _bids.push(_bid);
          _this.setState(Object.assign({}, _this.state, {
            bids: _bids,
            currentBid: {},
            addBidModal: false
          }));
        }
      } else {
        alert("Please add items to the bid");
      }
    };

    _this.onDeleteBidModal = function (bid_no) {
      // reset bid no index
      var bid_count = _this.state.bid_count - 1;
      var bids = _this.state.bids.filter(function (bid) {
        return bid.bid_no !== bid_no;
      });
      // update bid_no index for all bids sequentially
      bids = bids.map(function (bid, index) {
        bid.bid_no = index + 1;
        return bid;
      });
      _this.setState(Object.assign({}, _this.state, {
        bids: bids,
        bid_count: bid_count
      }));
    };

    _this.onAddBid = function () {
      var bid_count = _this.state.bid_count + 1;
      _this.setState(Object.assign({}, _this.state, {
        bid_count: bid_count,
        bids: [].concat(_toConsumableArray(_this.state.bids), [{
          supplier: "",
          bid_date: "",
          bid_no: bid_count,
          bid_document: null,
          items: []
        }])
      }));
    };

    _this.onAddItemsModal = function () {
      console.log("Adding items ...");
      _this.setState(Object.assign({}, _this.state, {
        addItemsModal: !_this.state.addItemsModal
      }));
    };

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

    _this.onInputChange = function (event) {
      console.log(event);
      var _event$target4 = event.target,
          name = _event$target4.name,
          value = _event$target4.value;

      _this.setState(Object.assign({}, _this.state, _defineProperty({}, name, value)));
    };

    _this.onFileInputChange = function (name_, event) {
      console.log(event);
      _this.setState(Object.assign({}, _this.state, _defineProperty({}, name_, event.target.files[0])));
    };

    _this.state = (_this$state = {
      plan_ref: "",
      proc_plan: "",
      scope_of_work: "",
      pr_number: "",
      quantity: "",
      pr_date: "",
      closing_date: "",
      closing_time_hour: ""
    }, _defineProperty(_this$state, "pr_date", ""), _defineProperty(_this$state, "date_tender_opened", ""), _defineProperty(_this$state, "tender_adjudication_committee_date", ""), _defineProperty(_this$state, "advert", null), _defineProperty(_this$state, "bid_count", 0), _defineProperty(_this$state, "currentBid", {}), _defineProperty(_this$state, "bids", []), _defineProperty(_this$state, "addBidModal", false), _defineProperty(_this$state, "cs_items", []), _defineProperty(_this$state, "cs_item_count", 0), _defineProperty(_this$state, "addItemsModal", false), _defineProperty(_this$state, "pr_items", []), _defineProperty(_this$state, "suppliers", []), _defineProperty(_this$state, "procurement_plans", []), _defineProperty(_this$state, "authUser", {}), _this$state);
    _this.getCreateData = _this.getCreateData.bind(_this);
    _this.onAddBid = _this.onAddBid.bind(_this);
    _this.onAddItemsModal = _this.onAddItemsModal.bind(_this);
    return _this;
  }

  _createClass(CreateCS, [{
    key: "componentDidMount",
    value: function componentDidMount() {
      // this.setState({
      //   region: this.props.region,
      //   district: this.props.district,
      //   section: this.props.section,
      //   depot: this.props.depot,
      // });
      this.getCreateData();
    }
  }, {
    key: "onSelectChange",
    value: function onSelectChange(name_, event) {
      var _event$target5 = event.target,
          name = _event$target5.name,
          value = _event$target5.value;

      this.setState(Object.assign({}, this.state, _defineProperty({}, name_, value)));
    }
  }, {
    key: "onFilterSelectCenters",
    value: function onFilterSelectCenters(name_, event) {
      var _event$target6 = event.target,
          name = _event$target6.name,
          value = _event$target6.value;

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
    key: "render",
    value: function render() {
      var _this2 = this;

      var itemsModal = null;
      var bidsModal = null;

      if (this.state.addItemsModal) {
        itemsModal = React.createElement(
          "div",
          { className: "fixed inset-0 flex items-center justify-center z-50 pt-10 pb-20" },
          React.createElement(
            "div",
            { className: "bg-white rounded-lg shadow-lg p-6 max-h-screen overflow-y-auto" },
            React.createElement(
              "div",
              { className: "flex justify-between items-center mb-4" },
              React.createElement(
                "h3",
                { className: "text-lg font-medium" },
                "Modal Title"
              ),
              React.createElement(
                "button",
                {
                  type: "button",
                  className: "text-gray-400 hover:text-gray-500 focus:outline-none",
                  onClick: this.onAddItemsModal
                },
                React.createElement(
                  "svg",
                  {
                    className: "h-6 w-6",
                    fill: "none",
                    stroke: "currentColor",
                    viewBox: "0 0 24 24"
                  },
                  React.createElement("path", {
                    strokeLinecap: "round",
                    strokeLinejoin: "round",
                    strokeWidth: "2",
                    d: "M6 18L18 6M6 6l12 12"
                  })
                )
              )
            ),
            React.createElement(
              "div",
              null,
              React.createElement(
                "table",
                {
                  style: { width: "100%" },
                  className: "table-auto border-spacing-4"
                },
                React.createElement(
                  "thead",
                  null,
                  React.createElement(
                    "tr",
                    null,
                    React.createElement(
                      "th",
                      null,
                      "Add Item"
                    ),
                    React.createElement(
                      "th",
                      null,
                      "Item Description"
                    ),
                    React.createElement(
                      "th",
                      null,
                      "Quantity"
                    )
                  )
                ),
                React.createElement(
                  "tbody",
                  null,
                  this.state.pr_items.map(function (item, index) {
                    return React.createElement(
                      "tr",
                      null,
                      React.createElement(
                        "td",
                        null,
                        React.createElement("input", {
                          type: "checkbox",
                          checked: item.selected ? item.selected : false,
                          onChange: function onChange() {
                            return _this2.onAddCSItem(item.id);
                          }
                        })
                      ),
                      React.createElement(
                        "td",
                        null,
                        item.description
                      ),
                      React.createElement(
                        "td",
                        null,
                        item.quantity
                      )
                    );
                  })
                )
              )
            )
          )
        );
      }

      if (this.state.addBidModal) {
        bidsModal = React.createElement(
          "div",
          {
            id: "bid-" + this.state.currentBid,
            className: "fixed inset-0 flex items-center justify-center z-50 pt-10 pb-20"
          },
          React.createElement(
            "div",
            { className: "bg-white rounded-lg shadow-lg p-6 max-h-screen min-w-max overflow-y-auto" },
            React.createElement(
              "div",
              { className: "flex justify-between items-center mb-4" },
              React.createElement(
                "h3",
                { className: "text-lg font-medium" },
                "Modal Title"
              ),
              React.createElement(
                "button",
                {
                  type: "button",
                  className: "text-gray-400 hover:text-gray-500 focus:outline-none",
                  onClick: this.onCloseCurrentBid
                },
                React.createElement(
                  "svg",
                  {
                    className: "h-6 w-6",
                    fill: "none",
                    stroke: "currentColor",
                    viewBox: "0 0 24 24"
                  },
                  React.createElement("path", {
                    strokeLinecap: "round",
                    strokeLinejoin: "round",
                    strokeWidth: "2",
                    d: "M6 18L18 6M6 6l12 12"
                  })
                )
              )
            ),
            React.createElement(
              "div",
              { className: "px-4 sm:px-0 mt-6 bg-gulf-blue-300 rounded-md border-t border-gray-100 border-b border-gray-900/10 pb-12" },
              React.createElement(
                "div",
                { id: "bid_container", className: " rounded-md" },
                React.createElement(
                  "div",
                  { className: "flex justify-evenly mt-5  px-2 py-2 rounded-md" },
                  React.createElement(
                    "div",
                    { className: "flex-1 w-20 ml-1" },
                    React.createElement(
                      "label",
                      {
                        htmlFor: "supplier_name",
                        className: "block text-sm font-medium leading-6 text-gray-900"
                      },
                      "Supplier"
                    ),
                    React.createElement(
                      "div",
                      { className: "mt-2" },
                      React.createElement(
                        "select",
                        {
                          id: "supplier",
                          onChange: function onChange(e) {
                            return _this2.onCurrentBidChange("supplier", e);
                          },
                          className: "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6 chzn-select"
                        },
                        this.state.currentBid.supplier_name ? React.createElement(
                          "option",
                          { value: this.state.currentBid.supplier + "-#-" + this.state.currentBid.supplier_name },
                          this.state.currentBid.supplier_name
                        ) : "",
                        React.createElement(
                          "option",
                          null,
                          "Select Supplier"
                        ),
                        this.state.suppliers ? this.state.suppliers.map(function (supplier) {
                          return React.createElement(
                            "option",
                            { value: supplier.id + "-#-" + supplier.name },
                            supplier.name
                          );
                        }) : ""
                      )
                    )
                  ),
                  React.createElement(
                    "div",
                    { className: "flex-1 w-20 ml-1" },
                    React.createElement(
                      "label",
                      {
                        htmlFor: "bid_date",
                        className: "block text-sm font-medium leading-6 text-gray-900"
                      },
                      "Bid Date"
                    ),
                    React.createElement(
                      "div",
                      { className: "mt-2" },
                      React.createElement("input", {
                        name: "bid_date",
                        value: this.state.currentBid.bid_date,
                        onChange: function onChange(e) {
                          return _this2.onCurrentBidChange("bid_date", e);
                        },
                        type: "date",
                        required: "required",
                        className: "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                      })
                    )
                  ),
                  React.createElement(
                    "div",
                    { className: "flex-1 w-20 ml-1" },
                    React.createElement(
                      "label",
                      {
                        htmlFor: "supplier[bid][0]",
                        className: "block text-sm font-medium leading-6 text-gray-900"
                      },
                      "Bid No."
                    ),
                    React.createElement(
                      "div",
                      { className: "mt-2" },
                      React.createElement("input", {
                        name: "supplier[bid][0]",
                        type: "number",
                        value: "1",
                        id: "bid",
                        required: "required",
                        readOnly: true,
                        className: "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                      })
                    )
                  ),
                  React.createElement(
                    "div",
                    { className: "flex-1 w-40 ml-1" },
                    React.createElement(
                      "label",
                      {
                        htmlFor: "bid_document",
                        className: "block text-sm font-medium leading-6 text-gray-900"
                      },
                      "Bid Documents"
                    ),
                    React.createElement(
                      "div",
                      { className: "mt-2" },
                      React.createElement("input", {
                        name: "bid_document",
                        type: "file",
                        onChange: function onChange(e) {
                          return _this2.onCurrentBidChange("bid_document", e);
                        },
                        className: "block w-full rounded-md border-0 py-1.5 px-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                      })
                    )
                  )
                ),
                this.state.cs_items.map(function (item, index) {
                  return React.createElement(
                    "div",
                    { className: "flex justify-evenly mt-5  px-2 py-2 rounded-md" },
                    React.createElement(
                      "div",
                      { className: "flex-1 w-15 ml-1" },
                      React.createElement(
                        "label",
                        {
                          htmlFor: "item_name",
                          className: "block text-sm font-medium leading-6 text-gray-900"
                        },
                        "Item Description"
                      ),
                      React.createElement(
                        "div",
                        { className: "mt-2" },
                        React.createElement("input", {
                          name: "item_description",
                          defaultValue: item.description,
                          onChange: function onChange(e) {
                            return _this2.onCurrentBidItemChange(item.id, "description", e);
                          },
                          id: "item_description",
                          required: "required",
                          className: "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                        })
                      )
                    ),
                    React.createElement(
                      "div",
                      { className: "flex-1 w-15 ml-1" },
                      React.createElement(
                        "label",
                        {
                          htmlFor: "quantity",
                          className: "block text-sm font-medium leading-6 text-gray-900"
                        },
                        "Quantity"
                      ),
                      React.createElement(
                        "div",
                        { className: "mt-2" },
                        React.createElement("input", {
                          name: "quantity",
                          defaultValue: item.quantity,
                          onChange: function onChange(e) {
                            return _this2.onCurrentBidItemChange(item.id, "quantity", e);
                          },
                          type: "number",
                          id: "quantity",
                          className: "block inpt w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                        })
                      )
                    ),
                    React.createElement(
                      "div",
                      { className: "flex-1 w-15 ml-3" },
                      React.createElement(
                        "div",
                        null,
                        React.createElement(
                          "label",
                          {
                            htmlFor: "unit_of_measurement",
                            className: "block text-sm font-medium leading-6 text-gray-900"
                          },
                          "UOM"
                        ),
                        React.createElement(
                          "div",
                          { className: "mt-2" },
                          React.createElement(
                            "select",
                            {
                              id: "unit_of_measurement",
                              onChange: function onChange(e) {
                                return _this2.onCurrentBidItemChange(item.id, "unit_of_measurement", e);
                              },
                              autoComplete: "unit_of_measurement",
                              className: "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6"
                            },
                            item.unit_of_measurement ? React.createElement(
                              "option",
                              { value: item.unit_of_measurement },
                              item.unit_of_measurement
                            ) : "",
                            React.createElement(
                              "option",
                              { value: "Each" },
                              "Each"
                            ),
                            React.createElement(
                              "option",
                              { value: "Kgs" },
                              "Kg`s"
                            ),
                            React.createElement(
                              "option",
                              { value: "Grammes" },
                              "Grammes"
                            ),
                            React.createElement(
                              "option",
                              { value: "Litres" },
                              "Litres"
                            ),
                            React.createElement(
                              "option",
                              { value: "Metres" },
                              "Metres"
                            ),
                            React.createElement(
                              "option",
                              { value: "Bags" },
                              "Bags"
                            ),
                            React.createElement(
                              "option",
                              { value: "Packets" },
                              "Packets"
                            ),
                            React.createElement(
                              "option",
                              { value: "Cartons" },
                              "Cartons"
                            )
                          )
                        )
                      )
                    ),
                    React.createElement(
                      "div",
                      { className: "flex-1 w-15 ml-3" },
                      React.createElement(
                        "div",
                        null,
                        React.createElement(
                          "label",
                          {
                            htmlFor: "vat",
                            className: "block text-sm font-medium leading-6 text-gray-900"
                          },
                          "VAT"
                        ),
                        React.createElement(
                          "div",
                          { className: "mt-2" },
                          React.createElement(
                            "select",
                            {
                              id: "vat",
                              onChange: function onChange(e) {
                                return _this2.onCurrentBidItemChange(item.id, "vat", e);
                              },
                              autoComplete: "vat",
                              className: "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6"
                            },
                            item.vat ? React.createElement(
                              "option",
                              { value: item.vat },
                              item.vat
                            ) : "",
                            React.createElement(
                              "option",
                              { value: "Excl." },
                              "Excl."
                            ),
                            React.createElement(
                              "option",
                              { value: "Incl." },
                              "Incl."
                            )
                          )
                        )
                      )
                    ),
                    React.createElement(
                      "div",
                      { className: "flex-1 w-15 ml-1" },
                      React.createElement(
                        "label",
                        {
                          htmlFor: "unit_price",
                          className: "block text-sm font-medium leading-6 text-gray-900"
                        },
                        "Unit Price"
                      ),
                      React.createElement(
                        "div",
                        { className: "mt-2" },
                        React.createElement("input", {
                          name: "unit_price",
                          defaultValue: item.unit_price,
                          onChange: function onChange(e) {
                            return _this2.onCurrentBidItemChange(item.id, "unit_price", e);
                          },
                          type: "text",
                          id: "unit_price",
                          required: true,
                          className: "block inpt w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                        })
                      )
                    )
                  );
                })
              ),
              React.createElement(
                "div",
                { className: "flex justify-center mt-5 px-3 py-3" },
                React.createElement(
                  "div",
                  { className: "m-2" },
                  React.createElement(
                    "button",
                    {
                      onClick: this.onCurrentBidSave,
                      className: "rounded-md text-gray-50 text-sm bg-blue-925 hover:bg-blue-550 px-3 py-2 font-semibold leading-6"
                    },
                    React.createElement(
                      "span",
                      { className: "ml-2" },
                      "SAVE BID"
                    )
                  )
                ),
                React.createElement(
                  "div",
                  { className: "m-2" },
                  React.createElement(
                    "button",
                    {
                      onClick: this.onCloseCurrentBid,
                      type: "submit",
                      className: "rounded-md bg-red-danger hover:bg-orange-500 text-sm font-semibold px-3 py-2 text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
                    },
                    React.createElement(
                      "span",
                      { className: "ml-2" },
                      "CANCEL"
                    )
                  )
                )
              )
            )
          )
        );
      }

      return React.createElement(
        "div",
        null,
        itemsModal,
        bidsModal,
        React.createElement("input", { type: "hidden", name: "item_count", id: "item_count", value: "1" }),
        React.createElement(
          "div",
          { className: "space-y-12 px-5 py-5" },
          React.createElement(
            "div",
            { className: "px-4 sm:px-0" },
            React.createElement(
              "h3",
              { className: "text-base font-semibold leading-7 text-gray-900" },
              "COMPARATIVE SCHEDULE"
            ),
            React.createElement(
              "p",
              { className: "mt-1 max-w-2xl text-sm leading-6 text-gray-500" },
              "TENDER"
            )
          ),
          React.createElement(
            "div",
            { className: "px-4 sm:px-0 mt-6 bg-gulf-blue-300 rounded-md border-t border-gray-100 border-gray-900/10" },
            React.createElement(
              "h2",
              { className: "text-base font-semibold leading-6 text-gray-900" },
              "RFQ DETAILS"
            ),
            React.createElement(
              "div",
              { className: "flex justify-evenly mt-5 px-2 py-2" },
              React.createElement(
                "div",
                { className: "flex-1 w-40" },
                React.createElement(
                  "label",
                  {
                    htmlFor: "plan_ref",
                    className: "block text-sm font-medium leading-6 text-gray-900"
                  },
                  "Plan Ref"
                ),
                React.createElement(
                  "div",
                  { className: "mt-2" },
                  React.createElement("input", {
                    name: "plan_ref",
                    id: "plan_ref",
                    required: "required",
                    value: this.state.plan_ref,
                    readOnly: true,
                    className: "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                  })
                )
              ),
              React.createElement(
                "div",
                { className: "flex-1 w-40 ml-3" },
                React.createElement(
                  "div",
                  null,
                  React.createElement(
                    "label",
                    {
                      htmlFor: "designation",
                      className: "block text-sm font-medium leading-6 text-gray-900"
                    },
                    "Procurement Plan"
                  ),
                  React.createElement(
                    "div",
                    { className: "mt-2" },
                    React.createElement(
                      "select",
                      {
                        id: "proc_plan",
                        name: "proc_plan",
                        autoComplete: "proc_plan",
                        onChange: function onChange(e) {
                          return _this2.onSelectChange("proc_plan", e);
                        },
                        className: "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6 chzn-select"
                      },
                      React.createElement(
                        "option",
                        null,
                        "Select Procurement Plan Ref"
                      ),
                      this.state.procurement_plans ? this.state.procurement_plans.map(function (plan) {
                        return React.createElement(
                          "option",
                          { value: plan.id },
                          plan.description
                        );
                      }) : ""
                    )
                  )
                )
              )
            ),
            React.createElement(
              "div",
              { className: "flex justify-evenly mt-5  px-2 py-2 rounded-md" },
              React.createElement(
                "div",
                { className: "flex-1 w-100" },
                React.createElement(
                  "label",
                  {
                    htmlFor: "scope",
                    className: "block text-sm font-medium leading-6 text-gray-900"
                  },
                  "Scope of Work"
                ),
                React.createElement(
                  "div",
                  { className: "mt-2" },
                  React.createElement("textarea", {
                    id: "scope",
                    name: "scope_of_work",
                    type: "scope",
                    value: this.state.scope_of_work,
                    onChange: this.onInputChange,
                    className: "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                  })
                )
              )
            ),
            React.createElement(
              "div",
              { className: "flex justify-evenly mt-5  px-2 py-2 rounded-md" },
              React.createElement(
                "div",
                { className: "flex-1 w-20 ml-1" },
                React.createElement(
                  "label",
                  {
                    htmlFor: "pr_number",
                    className: "block text-sm font-medium leading-6 text-gray-900"
                  },
                  "PR No."
                ),
                React.createElement(
                  "div",
                  { className: "mt-2" },
                  React.createElement("input", {
                    name: "pr_number",
                    value: this.state.pr_number,
                    onChange: this.onInputChange,
                    id: "pr_number",
                    required: "required",
                    className: "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                  })
                )
              ),
              React.createElement(
                "div",
                { className: "flex-1 w-20 ml-1" },
                React.createElement(
                  "label",
                  {
                    htmlFor: "quantity",
                    className: "block text-sm font-medium leading-6 text-gray-900"
                  },
                  "Quantity"
                ),
                React.createElement(
                  "div",
                  { className: "mt-2" },
                  React.createElement("input", {
                    name: "quantity",
                    value: this.state.quantity,
                    onChange: this.onInputChange,
                    type: "number",
                    required: "required",
                    className: "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                  })
                )
              ),
              React.createElement(
                "div",
                { className: "flex-1 w-20 ml-1" },
                React.createElement(
                  "label",
                  {
                    htmlFor: "pr_date",
                    className: "block text-sm font-medium leading-6 text-gray-900"
                  },
                  "PR Date"
                ),
                React.createElement(
                  "div",
                  { className: "mt-2" },
                  React.createElement("input", {
                    name: "pr_date",
                    value: this.state.pr_date,
                    onChange: this.onInputChange,
                    type: "date",
                    required: "required",
                    className: "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                  })
                )
              ),
              React.createElement(
                "div",
                { className: "flex-1 w-20 ml-1" },
                React.createElement(
                  "label",
                  {
                    htmlFor: "closing_date",
                    className: "block text-sm font-medium leading-6 text-gray-900"
                  },
                  "Closing Date"
                ),
                React.createElement(
                  "div",
                  { className: "mt-2" },
                  React.createElement("input", {
                    name: "closing_date",
                    value: this.state.closing_date,
                    onChange: this.onInputChange,
                    type: "date",
                    required: "required",
                    className: "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                  })
                )
              ),
              React.createElement(
                "div",
                { className: "flex-1 w-20 ml-1" },
                React.createElement(
                  "div",
                  null,
                  React.createElement(
                    "label",
                    {
                      htmlFor: "closing_time",
                      className: "block text-sm font-medium leading-6 text-gray-900"
                    },
                    "Closing Time"
                  ),
                  React.createElement(
                    "div",
                    { className: "mt-2 text-gray-900" },
                    React.createElement(
                      "div",
                      { className: "flex px-1" },
                      React.createElement(
                        "select",
                        {
                          name: "closing_time_hour",
                          onChange: function onChange(e) {
                            return _this2.onSelectChange("closing_time_hour", e);
                          },
                          className: "rounded-md block border-none w-full py-1.5 text-gray-900 sm:max-w-xs sm:text-sm sm:leading-6"
                        },
                        React.createElement(
                          "option",
                          { value: "10:00" },
                          "10:00"
                        ),
                        React.createElement(
                          "option",
                          { value: "14:00" },
                          "14:00"
                        )
                      )
                    )
                  )
                )
              )
            ),
            React.createElement(
              "div",
              { className: "flex justify-evenly mt-5  px-2 py-2 rounded-md" },
              React.createElement(
                "div",
                { className: "flex-1 w-20 ml-1" },
                React.createElement(
                  "label",
                  {
                    htmlFor: "proc_plan_ref",
                    className: "block text-sm font-medium leading-6 text-gray-900"
                  },
                  "Procurement Plan Ref"
                ),
                React.createElement(
                  "div",
                  { className: "mt-2" },
                  React.createElement("input", {
                    id: "proc_plan_ref",
                    value: this.state.proc_plan,
                    readOnly: true,
                    className: "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                  })
                )
              ),
              React.createElement(
                "div",
                { className: "flex-1 w-20 ml-1" },
                React.createElement(
                  "label",
                  {
                    htmlFor: "pr_date",
                    className: "block text-sm font-medium leading-6 text-gray-900"
                  },
                  "Ref Date"
                ),
                React.createElement(
                  "div",
                  { className: "mt-2" },
                  React.createElement("input", {
                    name: "pr_date",
                    value: this.state.pr_date,
                    onChange: this.onInputChange,
                    type: "date",
                    required: "required",
                    className: "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                  })
                )
              ),
              React.createElement(
                "div",
                { className: "flex-1 w-20 ml-1" },
                React.createElement(
                  "label",
                  {
                    htmlFor: "date_tender_opened",
                    className: "block text-sm font-medium leading-6 text-gray-900"
                  },
                  "Tender Box Opened On"
                ),
                React.createElement(
                  "div",
                  { className: "mt-2" },
                  React.createElement("input", {
                    name: "date_tender_opened",
                    value: this.state.date_tender_opened,
                    onChange: this.onInputChange,
                    type: "date",
                    required: "required",
                    className: "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                  })
                )
              ),
              React.createElement(
                "div",
                { className: "flex-1 w-40 ml-1" },
                React.createElement(
                  "label",
                  {
                    htmlFor: "tender_adjudication_committee_date",
                    className: "block text-sm font-medium leading-6 text-gray-900"
                  },
                  "Tender Committee Date"
                ),
                React.createElement(
                  "div",
                  { className: "mt-2" },
                  React.createElement("input", {
                    name: "tender_adjudication_committee_date",
                    value: this.state.tender_adjudication_committee_date,
                    onChange: this.onInputChange,
                    type: "date",
                    required: "required",
                    className: "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                  })
                )
              )
            ),
            React.createElement(
              "div",
              { className: "flex justify-evenly mt-5  px-2 py-2 rounded-md" },
              React.createElement(
                "div",
                { className: "flex-1 w-full ml-1" },
                React.createElement(
                  "label",
                  {
                    htmlFor: "advert",
                    className: "block text-sm font-medium leading-6 text-gray-900"
                  },
                  "Tender Advert"
                ),
                React.createElement(
                  "div",
                  { className: "mt-2" },
                  React.createElement("input", {
                    name: "advert",
                    onChange: function onChange(e) {
                      return _this2.onFileInputChange("advert", e);
                    },
                    type: "file",
                    id: "advert",
                    required: "required",
                    readOnly: true,
                    className: "block w-full rounded-md border-0 py-1.5 px-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                  })
                )
              )
            )
          ),
          this.state.bids.length === 0 ? React.createElement(
            "div",
            { className: "m-2" },
            React.createElement(
              "button",
              {
                style: { width: "100%" },
                onClick: this.onAddItemsModal,
                className: "rounded-md bg-nepal-950 hover:bg-nepal-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
              },
              "ADD SCHEDULE ITEMS"
            )
          ) : "",
          this.state.bids.map(function (bid, index) {
            return React.createElement(
              "div",
              {
                id: "opening_rfq",
                className: "px-4 sm:px-0 mt-6 bg-gulf-blue-300 rounded-md border-t border-gray-100 border-b border-gray-900/10 pb-12"
              },
              React.createElement(
                "div",
                { id: "bid_container", className: " rounded-md" },
                React.createElement(
                  "div",
                  { className: "flex justify-evenly mt-5  px-2 py-2 rounded-md" },
                  React.createElement(
                    "div",
                    { className: "flex-1 w-20 ml-1" },
                    React.createElement(
                      "label",
                      {
                        htmlFor: "supplier_name",
                        className: "block text-sm font-medium leading-6 text-gray-900"
                      },
                      "Supplier"
                    ),
                    React.createElement(
                      "div",
                      { className: "mt-2" },
                      React.createElement(
                        "p",
                        null,
                        bid.supplier_name
                      )
                    )
                  ),
                  React.createElement(
                    "div",
                    { className: "flex-1 w-20 ml-1" },
                    React.createElement(
                      "label",
                      {
                        htmlFor: "bid_date",
                        className: "block text-sm font-medium leading-6 text-gray-900"
                      },
                      "Bid Date"
                    ),
                    React.createElement(
                      "div",
                      { className: "mt-2" },
                      React.createElement(
                        "p",
                        null,
                        bid.bid_date
                      )
                    )
                  ),
                  React.createElement(
                    "div",
                    { className: "flex-1 w-20 ml-1" },
                    React.createElement(
                      "label",
                      {
                        htmlFor: "supplier[bid][0]",
                        className: "block text-sm font-medium leading-6 text-gray-900"
                      },
                      "Bid No."
                    ),
                    React.createElement(
                      "div",
                      { className: "mt-2" },
                      React.createElement(
                        "p",
                        null,
                        bid.bid_no
                      )
                    )
                  ),
                  React.createElement(
                    "div",
                    { className: "flex-1 w-40 ml-1" },
                    React.createElement(
                      "label",
                      {
                        htmlFor: "bid_document",
                        className: "block text-sm font-medium leading-6 text-gray-900"
                      },
                      "Bid Documents"
                    ),
                    React.createElement(
                      "div",
                      { className: "mt-2" },
                      React.createElement(
                        "a",
                        {
                          href: bid.bid_document ? URL.createObjectURL(bid.bid_document) : "",
                          target: "_blank",
                          rel: "noopener noreferrer"
                        },
                        bid.bid_document ? bid.bid_document.name : ""
                      )
                    )
                  )
                ),
                bid.items.map(function (item, index) {
                  return React.createElement(
                    "div",
                    { className: "flex justify-evenly mt-5  px-2 py-2 rounded-md" },
                    React.createElement(
                      "div",
                      { className: "flex-1 w-15 ml-1" },
                      React.createElement(
                        "label",
                        {
                          htmlFor: "item_name",
                          className: "block text-sm font-medium leading-6 text-gray-900"
                        },
                        "Item Description"
                      ),
                      React.createElement(
                        "div",
                        { className: "mt-2" },
                        React.createElement(
                          "p",
                          null,
                          item.description
                        )
                      )
                    ),
                    React.createElement(
                      "div",
                      { className: "flex-1 w-15 ml-1" },
                      React.createElement(
                        "label",
                        {
                          htmlFor: "quantity",
                          className: "block text-sm font-medium leading-6 text-gray-900"
                        },
                        "Quantity"
                      ),
                      React.createElement(
                        "div",
                        { className: "mt-2" },
                        React.createElement(
                          "p",
                          null,
                          item.quantity
                        )
                      )
                    ),
                    React.createElement(
                      "div",
                      { className: "flex-1 w-15 ml-3" },
                      React.createElement(
                        "div",
                        null,
                        React.createElement(
                          "label",
                          {
                            htmlFor: "unit_of_measurement",
                            className: "block text-sm font-medium leading-6 text-gray-900"
                          },
                          "UOM"
                        ),
                        React.createElement(
                          "div",
                          { className: "mt-2" },
                          React.createElement(
                            "p",
                            null,
                            item.unit_of_measurement
                          )
                        )
                      )
                    ),
                    React.createElement(
                      "div",
                      { className: "flex-1 w-15 ml-3" },
                      React.createElement(
                        "div",
                        null,
                        React.createElement(
                          "label",
                          {
                            htmlFor: "vat",
                            className: "block text-sm font-medium leading-6 text-gray-900"
                          },
                          "VAT"
                        ),
                        React.createElement(
                          "div",
                          { className: "mt-2" },
                          React.createElement(
                            "p",
                            null,
                            item.vat
                          )
                        )
                      )
                    ),
                    React.createElement(
                      "div",
                      { className: "flex-1 w-15 ml-1" },
                      React.createElement(
                        "label",
                        {
                          htmlFor: "unit_price",
                          className: "block text-sm font-medium leading-6 text-gray-900"
                        },
                        "Unit Price"
                      ),
                      React.createElement(
                        "div",
                        { className: "mt-2" },
                        React.createElement(
                          "p",
                          null,
                          item.unit_price
                        )
                      )
                    ),
                    React.createElement(
                      "div",
                      { className: "flex-1 w-15 ml-1" },
                      React.createElement(
                        "label",
                        {
                          htmlFor: "total_price",
                          className: "block text-sm font-medium leading-6 text-gray-900"
                        },
                        "Total Price"
                      ),
                      React.createElement(
                        "div",
                        { className: "mt-2" },
                        React.createElement(
                          "p",
                          null,
                          item.total_price
                        )
                      )
                    )
                  );
                })
              ),
              React.createElement(
                "div",
                { className: "flex justify-center mt-5 px-3 py-3" },
                React.createElement(
                  "div",
                  { className: "m-2" },
                  React.createElement(
                    "button",
                    {
                      onClick: function onClick() {
                        return _this2.onUpdateBidModal(bid.bid_no);
                      },
                      className: "rounded-md text-gray-50 text-sm bg-blue-925 hover:bg-blue-550 px-3 py-2 font-semibold leading-6"
                    },
                    "UPDATE BID"
                  )
                ),
                React.createElement(
                  "div",
                  { className: "m-2" },
                  React.createElement(
                    "button",
                    {
                      onClick: function onClick() {
                        return _this2.onDeleteBidModal(bid.bid_no);
                      },
                      type: "submit",
                      className: "rounded-md bg-red-danger hover:bg-orange-500 text-sm font-semibold px-3 py-2 text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
                    },
                    "DELETE BID"
                  )
                )
              )
            );
          }),
          this.state.cs_items.length > 0 ? React.createElement(
            "div",
            { className: "m-2" },
            React.createElement(
              "button",
              {
                style: { width: "100%" },
                onClick: this.onAddBidModal,
                className: "rounded-md bg-nepal-950 hover:bg-nepal-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
              },
              "ADD BID"
            )
          ) : ""
        ),
        React.createElement(
          "div",
          { className: "flex mt-10 px-3 py-3" },
          React.createElement(
            "div",
            { className: "flex-1 w-30 m-2" },
            React.createElement(
              "button",
              {
                style: { width: "100%" },
                className: "rounded-md py-1.5 text-sm hover:bg-nepal-300 font-semibold leading-6 text-gray-900"
              },
              "CANCEL"
            )
          ),
          React.createElement(
            "div",
            { className: "flex-1 w-30 m-2" },
            React.createElement(
              "button",
              {
                style: { width: "100%" },
                type: "submit",
                name: "add_supplier",
                className: "rounded-md bg-nepal-950 hover:bg-nepal-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
              },
              "SAVE & ADD SUPPLIER"
            )
          ),
          React.createElement(
            "div",
            { className: "flex-1 w-30 m-2" },
            React.createElement(
              "button",
              {
                style: { width: "100%" },
                type: "submit",
                name: "save_next",
                className: "rounded-md bg-blue-925 hover:bg-blue-550 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
              },
              "SAVE"
            )
          )
        )
      );
    }
  }]);

  return CreateCS;
}(React.Component);

var domContainer = document.querySelector("#create_comparative_schedule");
var spid = domContainer.getAttribute("data-spid");
var region = domContainer.getAttribute("data-region");
var district = domContainer.getAttribute("data-district");
var section = domContainer.getAttribute("data-section");
var depot = domContainer.getAttribute("data-depot");
ReactDOM.render(e(CreateCS, { spid: spid, region: region, district: district, section: section }), domContainer);