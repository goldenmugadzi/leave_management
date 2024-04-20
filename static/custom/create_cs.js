"use strict";

const e = React.createElement;

class CreateCS extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      plan_ref: "",
      proc_plan: "",
      scope_of_work: "",
      pr_number: "",
      quantity: "",
      pr_date: "",
      closing_date: "",
      closing_time_hour: "",
      pr_date: "",
      date_tender_opened: "",
      tender_adjudication_committee_date: "",
      advert: null,
      bid_count: 0,
      currentBid: {},
      bids: [],
      addBidModal: false,
      cs_items: [],
      cs_item_count: 0,
      addItemsModal: false,

      pr_items: [],
      suppliers: [],
      procurement_plans: [],
      authUser: {},
    };
    this.getCreateData = this.getCreateData.bind(this);
    this.onAddBid = this.onAddBid.bind(this);
    this.onAddItemsModal = this.onAddItemsModal.bind(this);
  }

  componentDidMount() {
    // this.setState({
    //   region: this.props.region,
    //   district: this.props.district,
    //   section: this.props.section,
    //   depot: this.props.depot,
    // });
    this.getCreateData();
  }

  getCreateData = () => {
    fetch(`http://localhost:8000/comparative_schedule/create_data`)
      .then((response) => response.json())
      .then((data) => {
        console.log("data: ", data);
        let plans = data.proc_plans ? data.proc_plans : [];
        let suppliers = data.suppliers ? data.suppliers : [];
        let pr_items = data.pr_items ? data.pr_items : [];
        this.setState({
          procurement_plans: plans,
          suppliers: suppliers,
          pr_items: pr_items,
        });
      });
  };

  onAddCSItem = (item_id) => {
    // check is item already added
    let item = this.state.cs_items.find((item) => item.id === item_id);
    console.log("item: ", item);
    if (item) {
      // update item selected to false
      item.selected = false;
      // update pr_items
      let pr_items = this.state.pr_items.map((_item) => {
        if (_item.id === item_id) {
          return item;
        }
        return _item;
      });
      // remove item
      let items = this.state.cs_items.filter((item) => item.id !== item_id);
      this.setState({
        ...this.state,
        cs_items: items,
        pr_items: pr_items,
      });
    } else {
      // find item in pr_items
      let item = this.state.pr_items.find((item) => item.id === item_id);
      // update pr_item selected to added
      item.selected = true;
      // update pr_items
      let pr_items = this.state.pr_items.map((_item) => {
        if (_item.id === item_id) {
          return item;
        }
        return _item;
      });

      let item_count = this.state.cs_item_count + 1;
      this.setState({
        ...this.state,
        item_count: item_count,
        cs_items: [...this.state.cs_items, item],
        pr_items: pr_items,
      });
      console.log("cs_items: ", this.state.cs_items);
      console.log("pr_items: ", this.state.pr_items);
    }
  };

  onAddBidModal = () => {
    let bid_count = this.state.bid_count + 1;
    this.setState({
      ...this.state,
      addBidModal: !this.state.addBidModal,
      bid_count: bid_count,
      currentBid: {
        bid_count: bid_count,
      },
    });
  };

  onUpdateBidModal = (bid_no) => {
    let bid = this.state.bids.find((bid) => bid.bid_no === bid_no);
    this.setState({
      ...this.state,
      addBidModal: !this.state.addBidModal,
      currentBid: bid,
    });
  };

  onCloseCurrentBid = () => {
    this.setState({
      ...this.state,
      currentBid: {},
      addBidModal: false,
    });
  };

  onCurrentBidChange = (name_, event) => {
    let currentBid = this.state.currentBid;
    if (name_ === "bid_document") {
      let bid_file = event.target.files[0];
      currentBid[name_] = bid_file;
    } else if(name_ === "supplier"){
      let { name, value } = event.target;
      console.log("value: ", value);
      let id_name = value? value.split("-#-"): [];
      currentBid[name_] = id_name.length > 0? id_name[0]: "";
      currentBid["supplier_name"] = id_name.length >= 1? id_name[1]: "";
    } else {
      let { name, value } = event.target;
      currentBid[name_] = value;
    }
    this.setState({
      ...this.state,
      currentBid: currentBid,
    });
  };

  onCurrentBidItemChange = (item_id, name_, event) => {
    // check if item exists in current bid
    let item = this.state.currentBid.items
      ? this.state.currentBid.items.find((item) => item.id === item_id)
      : null;
    console.log("item: ", item);
    // if item exists update item
    if (item) {
      let { name, value } = event.target;
      item[name_] = value;
      // update item in current bid
      let items = this.state.currentBid.items.map((_item) => {
        if (_item.id === item_id) {
          return item;
        }
        return _item;
      });
      // update current bid
      let currentBid = this.state.currentBid;
      currentBid.items = items;
      // update state
      this.setState({
        ...this.state,
        currentBid: currentBid,
      });
    } else {
      // find item in cs_items
      let item = this.state.cs_items.find((item) => item.id === item_id);
      // create new item
      let new_item = {
        id: item.id,
        description: item.description,
        quantity: item.quantity,
        unit_of_measurement: item.unit_of_measurement,
        vat: item.vat,
        unit_price: item.unit_price,
        total_price: item.total_price,
      };
      // update current bid items
      let items = [];
      if (!this.state.currentBid.items) {
        items.push(new_item);
      } else {
        items = [...this.state.currentBid.items, new_item];
      }
      // update current bid
      let currentBid = this.state.currentBid;
      currentBid.items = items;
      // update state
      this.setState({
        ...this.state,
        currentBid: currentBid,
      });
    }
  };

  onCurrentBidSave = () => {
    let currentBid = this.state.currentBid;
    // check if current bid already exists
    if (currentBid.items) {
      let bid = this.state.bids.find(
        (bid) => bid.bid_no === currentBid.bid_no
      );
      if (bid) {
        // update bid
        let bids = this.state.bids.map((bid) => {
          if (bid.bid_no === currentBid.bid_no) {
            return currentBid;
          }
          return bid;
        });
        this.setState({
          ...this.state,
          bids: bids,
          currentBid: {},
          addBidModal: false,
        });
      } else {
          // calculate total price for each item
          let items = currentBid.items.map((item) => {
            item.total_price = item.quantity * item.unit_price;
            return item;
          });
          let bids = this.state.bids;
          let bid = {
            supplier: currentBid.supplier,
            supplier_name: currentBid.supplier_name,
            bid_date: currentBid.bid_date,
            bid_no: currentBid.bid_count,
            bid_document: currentBid.bid_document,
            items: items,
          };
          bids.push(bid);
          this.setState({
            ...this.state,
            bids: bids,
            currentBid: {},
            addBidModal: false,
          });

      }
    } else {
      alert("Please add items to the bid");
    }
  };

  onDeleteBidModal = (bid_no) => {
    // reset bid no index
    let bid_count = this.state.bid_count - 1;
    let bids = this.state.bids.filter((bid) => bid.bid_no !== bid_no);
    // update bid_no index for all bids sequentially
    bids = bids.map((bid, index) => {
      bid.bid_no = index + 1;
      return bid;
    });
    this.setState({
      ...this.state,
      bids: bids,
      bid_count: bid_count,
    });
  };

  onAddBid = () => {
    let bid_count = this.state.bid_count + 1;
    this.setState({
      ...this.state,
      bid_count: bid_count,
      bids: [
        ...this.state.bids,
        {
          supplier: "",
          bid_date: "",
          bid_no: bid_count,
          bid_document: null,
          items: [],
        },
      ],
    });
  };

  onAddItemsModal = () => {
    console.log("Adding items ...");
    this.setState({
      ...this.state,
      addItemsModal: !this.state.addItemsModal,
    });
  };

  onSelectChange(name_, event) {
    let { name, value } = event.target;
    this.setState({
      ...this.state,
      [name_]: value,
    });
  }

  onFilterSelectCenters(name_, event) {
    let { name, value } = event.target;
    if (name_ === "region") {
      let dist = this.state.allDistricts.filter(
        (_district) => _district.region_id === value
      );
      this.setState({
        districts: dist,
        selectedRegion: value,
        selectedDepot: "",
        selectedDistrict: "",
      });
      this.getFilterData(value, "", "");
    } else if (name_ === "district") {
      console.log("district: ", value, this.state.allDepots);
      let depos = this.state.allDepots.filter(
        (_depot) => parseInt(_depot.district_id) === parseInt(value)
      );
      console.log("depots: ", depos);
      this.setState({
        depots: depos,
        selectedDepot: "",
        selectedDistrict: value,
        selectedRegion: "",
      });
      this.getFilterData("", value, "");
    } else if (name_ === "depot") {
      console.log("depot: ", value);
      this.setState({
        selectedDepot: value,
        selectedDistrict: "",
        selectedRegion: "",
      });
      this.getFilterData("", "", value);
    }

    // Filter by depot, filter by month, filter combined
  }

  getFilterData = (selectedRegion, selectedDistrict, selectedDepot) => {
    fetch(`http://localhost:8000/dashboards/dashboard_filter`, {
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
        console.log("data: ", data);
        if (data) {
          console.log("running ...");
          let inspection_locations_,
            inspections_count_,
            maintenance_locations_,
            maintenance_count_,
            mtn_;
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
      });
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

  getDashboardData = () => {
    fetch(`http://localhost:8000/dashboards/dashboard_data`)
      .then((response) => response.json())
      .then((data) => {
        console.log("data: ", data);
        let inspection_locations_ = JSON.parse(data.inspection_locations);
        let inspections_count_ = JSON.parse(data.inspections_count);
        let maintenance_locations_ = JSON.parse(data.maintenance_locations);
        let maintenance_count_ = JSON.parse(data.maintenance_count);
        let mtn_ = data.mtn;

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
      });
  };

  onInputChange = (event) => {
    console.log(event);
    const { name, value } = event.target;
    this.setState({
      ...this.state,
      [name]: value,
    });
  };

  onFileInputChange = (name_, event) => {
    console.log(event);
    this.setState({
      ...this.state,
      [name_]: event.target.files[0],
    });
  };

  render() {
    var itemsModal = null;
    var bidsModal = null;

    if (this.state.addItemsModal) {
      itemsModal = (
        <div className="fixed inset-0 flex items-center justify-center z-50 pt-10 pb-20">
          <div className="bg-white rounded-lg shadow-lg p-6 max-h-screen overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium">Modal Title</h3>
              <button
                type="button"
                className="text-gray-400 hover:text-gray-500 focus:outline-none"
                onClick={this.onAddItemsModal}
              >
                <svg
                  className="h-6 w-6"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>
            <div>
              <table
                style={{ width: "100%" }}
                className="table-auto border-spacing-4"
              >
                <thead>
                  <tr>
                    <th>Add Item</th>
                    <th>Item Description</th>
                    <th>Quantity</th>
                  </tr>
                </thead>
                <tbody>
                  {this.state.pr_items.map((item, index) => {
                    return (
                      <tr>
                        <td>
                          <input
                            type="checkbox"
                            checked={item.selected ? item.selected : false}
                            onChange={() => this.onAddCSItem(item.id)}
                          />
                        </td>
                        <td>{item.description}</td>
                        <td>{item.quantity}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      );
    }

    if (this.state.addBidModal) {
      bidsModal = (
        <div
          id={"bid-" + this.state.currentBid}
          className="fixed inset-0 flex items-center justify-center z-50 pt-10 pb-20"
        >
          <div className="bg-white rounded-lg shadow-lg p-6 max-h-screen min-w-max overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium">Modal Title</h3>
              <button
                type="button"
                className="text-gray-400 hover:text-gray-500 focus:outline-none"
                onClick={this.onCloseCurrentBid}
              >
                <svg
                  className="h-6 w-6"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>
            <div className="px-4 sm:px-0 mt-6 bg-gulf-blue-300 rounded-md border-t border-gray-100 border-b border-gray-900/10 pb-12">
              <div id="bid_container" className=" rounded-md">
                <div className="flex justify-evenly mt-5  px-2 py-2 rounded-md">
                  <div className="flex-1 w-20 ml-1">
                    <label
                      htmlFor="supplier_name"
                      className="block text-sm font-medium leading-6 text-gray-900"
                    >
                      Supplier
                    </label>
                    <div className="mt-2">
                      <select
                        id="supplier"
                        onChange={(e) => this.onCurrentBidChange("supplier", e)}
                        className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6 chzn-select"
                      >
                      {this.state.currentBid.supplier_name ? (
                        <option value={this.state.currentBid.supplier + "-#-" + this.state.currentBid.supplier_name}>
                          {this.state.currentBid.supplier_name}
                        </option>
                      ) : (
                        ""
                      )}
                        <option>Select Supplier</option>
                        {this.state.suppliers? this.state.suppliers.map((supplier) => (
                          <option value={supplier.id + "-#-" + supplier.name}>{supplier.name}</option>
                        )): ""}
                      </select>
                    </div>
                  </div>
                  <div className="flex-1 w-20 ml-1">
                    <label
                      htmlFor="bid_date"
                      className="block text-sm font-medium leading-6 text-gray-900"
                    >
                      Bid Date
                    </label>
                    <div className="mt-2">
                      <input
                        name="bid_date"
                        value={this.state.currentBid.bid_date}
                        onChange={(e) => this.onCurrentBidChange("bid_date", e)}
                        type="date"
                        required="required"
                        className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                      />
                    </div>
                  </div>
                  <div className="flex-1 w-20 ml-1">
                    <label
                      htmlFor="supplier[bid][0]"
                      className="block text-sm font-medium leading-6 text-gray-900"
                    >
                      Bid No.
                    </label>
                    <div className="mt-2">
                      <input
                        name="supplier[bid][0]"
                        type="number"
                        value="1"
                        id="bid"
                        required="required"
                        readOnly
                        className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                      />
                    </div>
                  </div>
                  <div className="flex-1 w-40 ml-1">
                    <label
                      htmlFor="bid_document"
                      className="block text-sm font-medium leading-6 text-gray-900"
                    >
                      Bid Documents
                    </label>
                    <div className="mt-2">
                      <input
                        name="bid_document"
                        type="file"
                        onChange={(e) =>
                          this.onCurrentBidChange("bid_document", e)
                        }
                        className="block w-full rounded-md border-0 py-1.5 px-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                      />
                    </div>
                  </div>
                </div>

                {this.state.cs_items.map((item, index) => {
                  return (
                    <div className="flex justify-evenly mt-5  px-2 py-2 rounded-md">
                      <div className="flex-1 w-15 ml-1">
                        <label
                          htmlFor="item_name"
                          className="block text-sm font-medium leading-6 text-gray-900"
                        >
                          Item Description
                        </label>
                        <div className="mt-2">
                          <input
                            name="item_description"
                            defaultValue={item.description}
                            onChange={(e) =>
                              this.onCurrentBidItemChange(
                                item.id,
                                "description",
                                e
                              )
                            }
                            id="item_description"
                            required="required"
                            className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                          />
                        </div>
                      </div>
                      <div className="flex-1 w-15 ml-1">
                        <label
                          htmlFor="quantity"
                          className="block text-sm font-medium leading-6 text-gray-900"
                        >
                          Quantity
                        </label>
                        <div className="mt-2">
                          <input
                            name="quantity"
                            defaultValue={item.quantity}
                            onChange={(e) =>
                              this.onCurrentBidItemChange(
                                item.id,
                                "quantity",
                                e
                              )
                            }
                            type="number"
                            id="quantity"
                            className="block inpt w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                          />
                        </div>
                      </div>
                      <div className="flex-1 w-15 ml-3">
                        <div>
                          <label
                            htmlFor="unit_of_measurement"
                            className="block text-sm font-medium leading-6 text-gray-900"
                          >
                            UOM
                          </label>
                          <div className="mt-2">
                            <select
                              id="unit_of_measurement"
                              onChange={(e) =>
                                this.onCurrentBidItemChange(
                                  item.id,
                                  "unit_of_measurement",
                                  e
                                )
                              }
                              autoComplete="unit_of_measurement"
                              className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6"
                            >
                              {item.unit_of_measurement ? (
                                <option value={item.unit_of_measurement}>
                                  {item.unit_of_measurement}
                                </option>
                              ) : (
                                ""
                              )}
                              <option value="Each">Each</option>
                              <option value="Kgs">Kg`s</option>
                              <option value="Grammes">Grammes</option>
                              <option value="Litres">Litres</option>
                              <option value="Metres">Metres</option>
                              <option value="Bags">Bags</option>
                              <option value="Packets">Packets</option>
                              <option value="Cartons">Cartons</option>
                            </select>
                          </div>
                        </div>
                      </div>
                      <div className="flex-1 w-15 ml-3">
                        <div>
                          <label
                            htmlFor="vat"
                            className="block text-sm font-medium leading-6 text-gray-900"
                          >
                            VAT
                          </label>
                          <div className="mt-2">
                            <select
                              id="vat"
                              onChange={(e) =>
                                this.onCurrentBidItemChange(item.id, "vat", e)
                              }
                              autoComplete="vat"
                              className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6"
                            >
                            {item.vat ? (
                              <option value={item.vat}>
                                {item.vat}
                              </option>
                            ) : (
                              ""
                            )}
                              <option value="Excl.">Excl.</option>
                              <option value="Incl.">Incl.</option>
                            </select>
                          </div>
                        </div>
                      </div>
                      <div className="flex-1 w-15 ml-1">
                        <label
                          htmlFor="unit_price"
                          className="block text-sm font-medium leading-6 text-gray-900"
                        >
                          Unit Price
                        </label>
                        <div className="mt-2">
                          <input
                            name="unit_price"
                            defaultValue={item.unit_price}
                            onChange={(e) =>
                              this.onCurrentBidItemChange(
                                item.id,
                                "unit_price",
                                e
                              )
                            }
                            type="text"
                            id="unit_price"
                            required
                            className="block inpt w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                          />
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>

              <div className="flex justify-center mt-5 px-3 py-3">
                <div className="m-2">
                  <button
                    onClick={this.onCurrentBidSave}
                    className="rounded-md text-gray-50 text-sm bg-blue-925 hover:bg-blue-550 px-3 py-2 font-semibold leading-6"
                  >
                    <span className="ml-2">SAVE BID</span>
                  </button>
                </div>
                <div className="m-2">
                  <button
                    onClick={this.onCloseCurrentBid}
                    type="submit"
                    className="rounded-md bg-red-danger hover:bg-orange-500 text-sm font-semibold px-3 py-2 text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
                  >
                    <span className="ml-2">CANCEL</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      );
    }

    return (
      <div>
        {itemsModal}
        {bidsModal}
        <input type="hidden" name="item_count" id="item_count" value="1" />
        <div className="space-y-12 px-5 py-5">
          <div className="px-4 sm:px-0">
            <h3 className="text-base font-semibold leading-7 text-gray-900">
              COMPARATIVE SCHEDULE
            </h3>
            <p className="mt-1 max-w-2xl text-sm leading-6 text-gray-500">
              TENDER
            </p>
          </div>
          <div className="px-4 sm:px-0 mt-6 bg-gulf-blue-300 rounded-md border-t border-gray-100 border-gray-900/10">
            <h2 className="text-base font-semibold leading-6 text-gray-900">
              RFQ DETAILS
            </h2>

            <div className="flex justify-evenly mt-5 px-2 py-2">
              <div className="flex-1 w-40">
                <label
                  htmlFor="plan_ref"
                  className="block text-sm font-medium leading-6 text-gray-900"
                >
                  Plan Ref
                </label>
                <div className="mt-2">
                  <input
                    name="plan_ref"
                    id="plan_ref"
                    required="required"
                    value={this.state.plan_ref}
                    readOnly
                    className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                  />
                </div>
              </div>
              <div className="flex-1 w-40 ml-3">
                <div>
                  <label
                    htmlFor="designation"
                    className="block text-sm font-medium leading-6 text-gray-900"
                  >
                    Procurement Plan
                  </label>
                  <div className="mt-2">
                    <select
                      id="proc_plan"
                      name="proc_plan"
                      autoComplete="proc_plan"
                      onChange={(e) => this.onSelectChange("proc_plan", e)}
                      className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6 chzn-select"
                    >
                      <option>Select Procurement Plan Ref</option>
                      {this.state.procurement_plans
                        ? this.state.procurement_plans.map((plan) => (
                            <option value={plan.id}>{plan.description}</option>
                          ))
                        : ""}
                    </select>
                  </div>
                </div>
              </div>
            </div>
            <div className="flex justify-evenly mt-5  px-2 py-2 rounded-md">
              <div className="flex-1 w-100">
                <label
                  htmlFor="scope"
                  className="block text-sm font-medium leading-6 text-gray-900"
                >
                  Scope of Work
                </label>
                <div className="mt-2">
                  <textarea
                    id="scope"
                    name="scope_of_work"
                    type="scope"
                    value={this.state.scope_of_work}
                    onChange={this.onInputChange}
                    className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                  ></textarea>
                </div>
              </div>
            </div>
            <div className="flex justify-evenly mt-5  px-2 py-2 rounded-md">
              <div className="flex-1 w-20 ml-1">
                <label
                  htmlFor="pr_number"
                  className="block text-sm font-medium leading-6 text-gray-900"
                >
                  PR No.
                </label>
                <div className="mt-2">
                  <input
                    name="pr_number"
                    value={this.state.pr_number}
                    onChange={this.onInputChange}
                    id="pr_number"
                    required="required"
                    className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                  />
                </div>
              </div>
              <div className="flex-1 w-20 ml-1">
                <label
                  htmlFor="quantity"
                  className="block text-sm font-medium leading-6 text-gray-900"
                >
                  Quantity
                </label>
                <div className="mt-2">
                  <input
                    name="quantity"
                    value={this.state.quantity}
                    onChange={this.onInputChange}
                    type="number"
                    required="required"
                    className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                  />
                </div>
              </div>
              <div className="flex-1 w-20 ml-1">
                <label
                  htmlFor="pr_date"
                  className="block text-sm font-medium leading-6 text-gray-900"
                >
                  PR Date
                </label>
                <div className="mt-2">
                  <input
                    name="pr_date"
                    value={this.state.pr_date}
                    onChange={this.onInputChange}
                    type="date"
                    required="required"
                    className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                  />
                </div>
              </div>
              <div className="flex-1 w-20 ml-1">
                <label
                  htmlFor="closing_date"
                  className="block text-sm font-medium leading-6 text-gray-900"
                >
                  Closing Date
                </label>
                <div className="mt-2">
                  <input
                    name="closing_date"
                    value={this.state.closing_date}
                    onChange={this.onInputChange}
                    type="date"
                    required="required"
                    className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                  />
                </div>
              </div>
              <div className="flex-1 w-20 ml-1">
                <div>
                  <label
                    htmlFor="closing_time"
                    className="block text-sm font-medium leading-6 text-gray-900"
                  >
                    Closing Time
                  </label>
                  <div className="mt-2 text-gray-900">
                    <div className="flex px-1">
                      <select
                        name="closing_time_hour"
                        onChange={(e) =>
                          this.onSelectChange("closing_time_hour", e)
                        }
                        className="rounded-md block border-none w-full py-1.5 text-gray-900 sm:max-w-xs sm:text-sm sm:leading-6"
                      >
                        <option value="10:00">10:00</option>
                        <option value="14:00">14:00</option>
                      </select>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div className="flex justify-evenly mt-5  px-2 py-2 rounded-md">
              <div className="flex-1 w-20 ml-1">
                <label
                  htmlFor="proc_plan_ref"
                  className="block text-sm font-medium leading-6 text-gray-900"
                >
                  Procurement Plan Ref
                </label>
                <div className="mt-2">
                  <input
                    id="proc_plan_ref"
                    value={this.state.proc_plan}
                    readOnly
                    className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                  />
                </div>
              </div>
              <div className="flex-1 w-20 ml-1">
                <label
                  htmlFor="pr_date"
                  className="block text-sm font-medium leading-6 text-gray-900"
                >
                  Ref Date
                </label>
                <div className="mt-2">
                  <input
                    name="pr_date"
                    value={this.state.pr_date}
                    onChange={this.onInputChange}
                    type="date"
                    required="required"
                    className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                  />
                </div>
              </div>
              <div className="flex-1 w-20 ml-1">
                <label
                  htmlFor="date_tender_opened"
                  className="block text-sm font-medium leading-6 text-gray-900"
                >
                  Tender Box Opened On
                </label>
                <div className="mt-2">
                  <input
                    name="date_tender_opened"
                    value={this.state.date_tender_opened}
                    onChange={this.onInputChange}
                    type="date"
                    required="required"
                    className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                  />
                </div>
              </div>
              <div className="flex-1 w-40 ml-1">
                <label
                  htmlFor="tender_adjudication_committee_date"
                  className="block text-sm font-medium leading-6 text-gray-900"
                >
                  Tender Committee Date
                </label>
                <div className="mt-2">
                  <input
                    name="tender_adjudication_committee_date"
                    value={this.state.tender_adjudication_committee_date}
                    onChange={this.onInputChange}
                    type="date"
                    required="required"
                    className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                  />
                </div>
              </div>
            </div>
            <div className="flex justify-evenly mt-5  px-2 py-2 rounded-md">
              <div className="flex-1 w-full ml-1">
                <label
                  htmlFor="advert"
                  className="block text-sm font-medium leading-6 text-gray-900"
                >
                  Tender Advert
                </label>
                <div className="mt-2">
                  <input
                    name="advert"
                    onChange={(e) => this.onFileInputChange("advert", e)}
                    type="file"
                    id="advert"
                    required="required"
                    readOnly
                    className="block w-full rounded-md border-0 py-1.5 px-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                  />
                </div>
              </div>
            </div>
          </div>

          {this.state.bids.length === 0 ? (
            <div className="m-2">
              <button
                style={{ width: "100%" }}
                onClick={this.onAddItemsModal}
                className="rounded-md bg-nepal-950 hover:bg-nepal-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
              >
                ADD SCHEDULE ITEMS
              </button>
            </div>
          ) : (
            ""
          )}

          {this.state.bids.map((bid, index) => {
            return (
              <div
                id="opening_rfq"
                className="px-4 sm:px-0 mt-6 bg-gulf-blue-300 rounded-md border-t border-gray-100 border-b border-gray-900/10 pb-12"
              >
                <div id="bid_container" className=" rounded-md">
                  <div className="flex justify-evenly mt-5  px-2 py-2 rounded-md">
                    <div className="flex-1 w-20 ml-1">
                      <label
                        htmlFor="supplier_name"
                        className="block text-sm font-medium leading-6 text-gray-900"
                      >
                        Supplier
                      </label>
                      <div className="mt-2">
                        <p>{bid.supplier_name}</p>
                      </div>
                    </div>
                    <div className="flex-1 w-20 ml-1">
                      <label
                        htmlFor="bid_date"
                        className="block text-sm font-medium leading-6 text-gray-900"
                      >
                        Bid Date
                      </label>
                      <div className="mt-2">
                        <p>{bid.bid_date}</p>
                      </div>
                    </div>
                    <div className="flex-1 w-20 ml-1">
                      <label
                        htmlFor="supplier[bid][0]"
                        className="block text-sm font-medium leading-6 text-gray-900"
                      >
                        Bid No.
                      </label>
                      <div className="mt-2">
                        <p>{bid.bid_no}</p>
                      </div>
                    </div>
                    <div className="flex-1 w-40 ml-1">
                      <label
                        htmlFor="bid_document"
                        className="block text-sm font-medium leading-6 text-gray-900"
                      >
                        Bid Documents
                      </label>
                      <div className="mt-2">
                        <a
                          href={bid.bid_document? URL.createObjectURL(bid.bid_document): ""}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          {bid.bid_document? bid.bid_document.name: ""}
                        </a>
                      </div>
                    </div>
                  </div>

                  {bid.items.map((item, index) => {
                    return (
                      <div className="flex justify-evenly mt-5  px-2 py-2 rounded-md">
                        <div className="flex-1 w-15 ml-1">
                          <label
                            htmlFor="item_name"
                            className="block text-sm font-medium leading-6 text-gray-900"
                          >
                            Item Description
                          </label>
                          <div className="mt-2">
                            <p>{item.description}</p>
                          </div>
                        </div>
                        <div className="flex-1 w-15 ml-1">
                          <label
                            htmlFor="quantity"
                            className="block text-sm font-medium leading-6 text-gray-900"
                          >
                            Quantity
                          </label>
                          <div className="mt-2">
                            <p>{item.quantity}</p>
                          </div>
                        </div>
                        <div className="flex-1 w-15 ml-3">
                          <div>
                            <label
                              htmlFor="unit_of_measurement"
                              className="block text-sm font-medium leading-6 text-gray-900"
                            >
                              UOM
                            </label>
                            <div className="mt-2">
                              <p>{item.unit_of_measurement}</p>
                            </div>
                          </div>
                        </div>
                        <div className="flex-1 w-15 ml-3">
                          <div>
                            <label
                              htmlFor="vat"
                              className="block text-sm font-medium leading-6 text-gray-900"
                            >
                              VAT
                            </label>
                            <div className="mt-2">
                              <p>{item.vat}</p>
                            </div>
                          </div>
                        </div>
                        <div className="flex-1 w-15 ml-1">
                          <label
                            htmlFor="unit_price"
                            className="block text-sm font-medium leading-6 text-gray-900"
                          >
                            Unit Price
                          </label>
                          <div className="mt-2">
                            <p>{item.unit_price}</p>
                          </div>
                        </div>
                        <div className="flex-1 w-15 ml-1">
                          <label
                            htmlFor="total_price"
                            className="block text-sm font-medium leading-6 text-gray-900"
                          >
                            Total Price
                          </label>
                          <div className="mt-2">
                            <p>{item.total_price}</p>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>

                <div className="flex justify-center mt-5 px-3 py-3">
                  <div className="m-2">
                    <button
                      onClick={() => this.onUpdateBidModal(bid.bid_no)}
                      className="rounded-md text-gray-50 text-sm bg-blue-925 hover:bg-blue-550 px-3 py-2 font-semibold leading-6"
                    >
                      UPDATE BID
                    </button>
                  </div>
                  <div className="m-2">
                    <button
                      onClick={() => this.onDeleteBidModal(bid.bid_no)}
                      type="submit"
                      className="rounded-md bg-red-danger hover:bg-orange-500 text-sm font-semibold px-3 py-2 text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
                    >
                      DELETE BID
                    </button>
                  </div>
                </div>
              </div>
            );
          })}

          {this.state.cs_items.length > 0 ? (
            <div className="m-2">
              <button
                style={{ width: "100%" }}
                onClick={this.onAddBidModal}
                className="rounded-md bg-nepal-950 hover:bg-nepal-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
              >
                ADD BID
              </button>
            </div>
          ): ""}

        </div>

        <div className="flex mt-10 px-3 py-3">
          <div className="flex-1 w-30 m-2">
            <button
              style={{ width: "100%" }}
              className="rounded-md py-1.5 text-sm hover:bg-nepal-300 font-semibold leading-6 text-gray-900"
            >
              CANCEL
            </button>
          </div>
          <div className="flex-1 w-30 m-2">
            <button
              style={{ width: "100%" }}
              type="submit"
              name="add_supplier"
              className="rounded-md bg-nepal-950 hover:bg-nepal-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
            >
              SAVE & ADD SUPPLIER
            </button>
          </div>
          <div className="flex-1 w-30 m-2">
            <button
              style={{ width: "100%" }}
              type="submit"
              name="save_next"
              className="rounded-md bg-blue-925 hover:bg-blue-550 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
            >
              SAVE
            </button>
          </div>
        </div>
      </div>
    );
  }
}

const domContainer = document.querySelector("#create_comparative_schedule");
const spid = domContainer.getAttribute("data-spid");
const region = domContainer.getAttribute("data-region");
const district = domContainer.getAttribute("data-district");
const section = domContainer.getAttribute("data-section");
const depot = domContainer.getAttribute("data-depot");
ReactDOM.render(e(CreateCS, { spid, region, district, section }), domContainer);
