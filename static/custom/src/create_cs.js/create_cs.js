"use strict";

var _typeof = typeof Symbol === "function" && typeof Symbol.iterator === "symbol" ? function (obj) { return typeof obj; } : function (obj) { return obj && typeof Symbol === "function" && obj.constructor === Symbol && obj !== Symbol.prototype ? "symbol" : typeof obj; };

var _createClass = function () { function defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, descriptor.key, descriptor); } } return function (Constructor, protoProps, staticProps) { if (protoProps) defineProperties(Constructor.prototype, protoProps); if (staticProps) defineProperties(Constructor, staticProps); return Constructor; }; }();

function _toConsumableArray(arr) { if (Array.isArray(arr)) { for (var i = 0, arr2 = Array(arr.length); i < arr.length; i++) { arr2[i] = arr[i]; } return arr2; } else { return Array.from(arr); } }

function _defineProperty(obj, key, value) { if (key in obj) { Object.defineProperty(obj, key, { value: value, enumerable: true, configurable: true, writable: true }); } else { obj[key] = value; } return obj; }

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

function _possibleConstructorReturn(self, call) { if (!self) { throw new ReferenceError("this hasn't been initialised - super() hasn't been called"); } return call && (typeof call === "object" || typeof call === "function") ? call : self; }

function _inherits(subClass, superClass) { if (typeof superClass !== "function" && superClass !== null) { throw new TypeError("Super expression must either be null or a function, not " + typeof superClass); } subClass.prototype = Object.create(superClass && superClass.prototype, { constructor: { value: subClass, enumerable: false, writable: true, configurable: true } }); if (superClass) Object.setPrototypeOf ? Object.setPrototypeOf(subClass, superClass) : subClass.__proto__ = superClass; }

var e = React.createElement;
var BASE_URL = "http://localhost:8000";
// const BASE_URL = "http://172.16.8.98:9300";

var CreateCS = function (_React$Component) {
  _inherits(CreateCS, _React$Component);

  function CreateCS(props) {
    _classCallCheck(this, CreateCS);

    var _this = _possibleConstructorReturn(this, (CreateCS.__proto__ || Object.getPrototypeOf(CreateCS)).call(this, props));

    _this.onGetFileObjectUrl = function (fileData) {
      if (typeof fileData === "string") {
        var decodedFileData = atob(fileData);
        var uint8Array = new Uint8Array(decodedFileData.length);
        for (var i = 0; i < decodedFileData.length; i++) {
          uint8Array[i] = decodedFileData.charCodeAt(i);
        }

        var file = new Blob([uint8Array], { type: "application/pdf" });
        console.log("file: ", file);

        return URL.createObjectURL(file);
      } else {
        console.log("fileData: ", fileData);
        return URL.createObjectURL(fileData);
      }
    };

    _this.getCSData = function (cs_id) {
      fetch(BASE_URL + "/comperative_schedule/cs_data/" + cs_id).then(function (response) {
        return response.json();
      }).then(function (data_) {
        var _Object$assign;

        var data = JSON.parse(data_);
        console.log("cs data: ", data, typeof data === "undefined" ? "undefined" : _typeof(data));
        var requester_role = data.requester_role ? data.requester_role : "";
        var bids_object = data.bids ? data.bids : [];
        var bids = Object.keys(bids_object).map(function (key) {
          var new_obj = bids_object[key];
          return Object.assign({}, new_obj, {
            bid_document_url: _this.onGetFileObjectUrl(new_obj.bid_document)
          });
        });

        var compliance = data.compliance ? data.compliance : [];
        var complianceRemarks = data.complianceRemarks ? data.complianceRemarks : [];
        var rankings = data.rankings ? data.rankings : [];
        var committee = data.committee ? data.committee : [];
        var gm_approval = data.gm_approval ? data.gm_approval : null;
        var fm_approval = data.fm_approval ? data.fm_approval : null;
        var pr_date = data.pr_date ? data.pr_date : "";
        var proc_plan = data.proc_plan ? data.proc_plan : "";
        var scope_of_work = data.scope_of_work ? data.scope_of_work : "";
        var pr_number = data.pr_number ? data.pr_number : "";
        var quantity = data.quantity ? data.quantity : "";
        var closing_date = data.closing_date ? data.closing_date : "";
        var ref_date = data.ref_date ? data.ref_date : "";
        var closing_time = data.closing_time ? data.closing_time : "";
        var tender_adjudication_committee_date = data.tac_date ? data.tac_date : "";
        var cs_opened = data.cs_opened ? data.cs_opened : false;

        var proc_plans = data.proc_plans ? data.proc_plans : [];
        var uom = data.uom ? data.uom : [];
        var suppliers = data.suppliers ? data.suppliers : [];
        var pr_items = data.pr_items ? data.pr_items : [];
        var pr_attachments = data.pr_attachments ? data.pr_attachments : [];
        var cs_items = data.cs_items ? data.cs_items : [];
        var users = data.users ? data.users : [];
        var cs_owner = data.cs_owner ? data.cs_owner : "";

        var advert_url = _this.onGetFileObjectUrl(data.advert);

        var pr_at_list = pr_attachments.map(function (pr_attachment) {
          return Object.assign({}, pr_attachment, {
            attachment_url: _this.onGetFileObjectUrl(pr_attachment.file)
          });
        });
        var committeeApprovalComplete = committee.filter(function (member) {
          return member.memberApproval === "" || member.memberApproval === null || member.memberApproval === undefined || member.memberApproval === "Rejected";
        }).length === 0;

        _this.setState(Object.assign({}, _this.state, (_Object$assign = {
          requester_role: requester_role,
          cs_owner: cs_owner,
          committeeApprovalComplete: committeeApprovalComplete,
          proc_plans: proc_plans,
          uom: uom,
          suppliers: suppliers,
          users: users,

          date_tender_opened: cs_opened,
          ref_date: ref_date,
          proc_ref: proc_plan.proc_ref,
          proc_plan: proc_plan,
          scope_of_work: scope_of_work,
          pr_number: pr_number,
          quantity: quantity,
          pr_date: pr_date,
          closing_date: closing_date,
          closing_time_hour: closing_time
        }, _defineProperty(_Object$assign, "ref_date", ref_date), _defineProperty(_Object$assign, "tender_adjudication_committee_date", tender_adjudication_committee_date), _defineProperty(_Object$assign, "advert", advert), _defineProperty(_Object$assign, "advert_url", advert_url), _defineProperty(_Object$assign, "bids", bids), _defineProperty(_Object$assign, "cs_items", cs_items), _defineProperty(_Object$assign, "compliance", compliance), _defineProperty(_Object$assign, "complianceRemarks", complianceRemarks), _defineProperty(_Object$assign, "rankings", rankings), _defineProperty(_Object$assign, "committeeMembers", committee), _defineProperty(_Object$assign, "gmApproval", gm_approval), _defineProperty(_Object$assign, "fmApproval", fm_approval), _defineProperty(_Object$assign, "pr_items", pr_items), _defineProperty(_Object$assign, "pr_attachments", pr_at_list), _Object$assign)));
      });
    };

    _this.getCreateData = function (pr_id) {
      console.log("cs pr_id: ", pr_id);

      fetch(BASE_URL + "/comperative_schedule/create_data/" + pr_id).then(function (response) {
        return response.json();
      }).then(function (data) {
        console.log("data: ", data);
        var scope_of_work = data.scope_of_work ? data.scope_of_work : "";
        var proc_ref = data.proc_ref ? data.proc_ref : "";
        var plans = data.proc_plans ? data.proc_plans : [];
        var uom = data.uom ? data.uom : [];
        var suppliers = data.suppliers ? data.suppliers : [];
        var pr_items = data.pr_items ? data.pr_items : [];
        var pr_attachments = data.pr_attachments ? data.pr_attachments : [];
        var pr_id = data.pr_id ? data.pr_id : "";
        var pr_date = data.pr_date ? data.pr_date : "";
        var users = data.users ? data.users : [];

        var pr_at_list = pr_attachments.map(function (pr_attachment) {
          return Object.assign({}, pr_attachment, {
            attachment_url: _this.onGetFileObjectUrl(pr_attachment.file)
          });
        });
        _this.setState({
          scope_of_work: scope_of_work,
          proc_ref: proc_ref,
          proc_plans: plans,
          uom: uom,
          suppliers: suppliers,
          pr_items: pr_items,
          pr_attachments: pr_at_list,
          pr_number: pr_id,
          pr_date: pr_date,
          users: users
        });
      });
    };

    _this.onFetchPR = function (pr_id) {
      console.log("cs pr_id: ", pr_id);

      fetch(BASE_URL + "/comperative_schedule/create_data/" + pr_id).then(function (response) {
        return response.json();
      }).then(function (data) {
        console.log("data: ", data);
        if (data && data.success) {
          var scope_of_work = data.scope_of_work ? data.scope_of_work : "";
          var proc_ref = data.proc_ref ? data.proc_ref : "";
          var proc_plan = data.proc_plan ? data.proc_plan : null;
          var plans = data.proc_plans ? data.proc_plans : [];
          var uom = data.uom ? data.uom : "";
          var suppliers = data.suppliers ? data.suppliers : [];
          var pr_items = data.pr_items ? data.pr_items : [];
          var pr_attachments = data.pr_attachments ? data.pr_attachments : [];
          var _pr_id = data.pr_id ? data.pr_id : "";
          var pr_date = data.pr_date ? data.pr_date : "";
          var users = data.users ? data.users : [];

          var pr_at_list = pr_attachments.map(function (pr_attachment) {
            return Object.assign({}, pr_attachment, {
              attachment_url: _this.onGetFileObjectUrl(pr_attachment.file)
            });
          });
          _this.setState({
            scope_of_work: scope_of_work,
            proc_ref: proc_ref,
            proc_plan: proc_plan,
            proc_plans: plans,
            uom: uom,
            suppliers: suppliers,
            pr_items: pr_items,
            pr_attachments: pr_at_list,
            pr_number: _pr_id,
            pr_date: pr_date,
            users: users,
            fetchPR: false
          });

          alert("PR fetched successfully");
        } else {
          alert("PR Number not found");
        }
      });
    };

    _this.onFetchPrNumberChange = function (event) {
      var _event$target = event.target,
          name = _event$target.name,
          value = _event$target.value;

      _this.setState(Object.assign({}, _this.state, {
        pr_number: value
      }));
    };

    _this.onCommitteeChange = function (name_, event) {
      var _event$target2 = event.target,
          name = _event$target2.name,
          value = _event$target2.value;

      console.log("name: ", name_, "value: ", value);
      var member = _this.state.member;
      member[name_] = value;
      _this.setState(Object.assign({}, _this.state, {
        member: member
      }));
    };

    _this.onAddCommitteeMembers = function () {
      var members = _this.state.committeeMembers;
      var member_ = _this.state.member;
      if (member_.memberUserName === "") {
        alert("Please select a user");
      }
      // check if memberUserName exists
      var member = members.find(function (_member) {
        return _member.memberUserName === _this.state.member.memberUserName;
      });
      // check if memberUserName is the one creating
      var currentUserFlag = _this.state.member.memberUserName === _this.state.username;
      if (member) {
        alert("Committee Member already added.");
      } else if (currentUserFlag) {
        alert("You cannot add yourself. Please choose another user.");
      } else {
        members.push(_this.state.member);
        _this.setState(Object.assign({}, _this.state, {
          committeeMembers: members,
          member: {
            memberUserName: "",
            memberName: "",
            memberPosition: "",
            memberApproval: ""
          }
        }));
      }
    };

    _this.onRemoveCommitteeMember = function (index, username) {
      var members = _this.state.committeeMembers.filter(function (member, _index) {
        return _index !== index;
      });
      if (members.length < _this.state.committeeMembers.length) {
        _this.setState(Object.assign({}, _this.state, {
          committeeMembers: members
        }));
      }
      _this.deleteCommitteeMember(username);
    };

    _this.deleteCommitteeMember = function (username) {
      var form_data = new FormData();
      form_data.append("cs_id", _this.state.cs_id);
      form_data.append("username", username);
      form_data.append("csrfmiddlewaretoken", _this.getCookie("csrftoken"));

      fetch(BASE_URL + "/comperative_schedule/delete_committee_member", {
        method: "POST",
        headers: {
          "X-CSRFToken": _this.getCookie("csrftoken")
        },
        body: form_data
      }).then(function (response) {
        return response.json();
      }).then(function (data) {
        console.log("data: ", data);
        if (data.success) {
          alert("Committee member deleted successfully");
        } else {
          alert("Error deleting Committee member");
        }
      });
    };

    _this.onCommitteeJustificationModal = function (username) {
      _this.setState(Object.assign({}, _this.state, {
        currentApprover: {
          username: username,
          justification: ""
        },
        committeeJustificationModal: !_this.state.committeeJustificationModal
      }));
    };

    _this.onCommitteeJustificationChange = function (event) {
      var _event$target3 = event.target,
          name = _event$target3.name,
          value = _event$target3.value;

      var currentApprover = _this.state.currentApprover;
      currentApprover[name] = value;
      _this.setState(Object.assign({}, _this.state, {
        currentApprover: currentApprover
      }));
    };

    _this.onCommitteeApprove = function (username, approval, justification) {
      var form_data = new FormData();
      form_data.append("cs_id", _this.state.cs_id);
      form_data.append("username", username);
      form_data.append("approval", approval);
      form_data.append("justification", justification);
      form_data.append("csrfmiddlewaretoken", _this.getCookie("csrftoken"));

      fetch(BASE_URL + "/comperative_schedule/committee_approve", {
        method: "POST",
        headers: {
          "X-CSRFToken": _this.getCookie("csrftoken")
        },
        body: form_data
      }).then(function (response) {
        return response.json();
      }).then(function (data) {
        console.log("data: ", data);
        if (data.success) {
          var committeeDate = data.committee_date;
          var committeeApproval = data.committe_approval;
          var memberName = data.committee_fullname;
          var members = _this.state.committeeMembers.map(function (member) {
            if (member.memberUserName === username) {
              member.committee_date = committeeDate;
              member.member_approval = committeeApproval;
            }
            return member;
          });
          _this.setState(Object.assign({}, _this.state, {
            committeeMembers: members
          }));
          if (committeeApproval === "Approved") {
            alert("Committee approved successfully by " + memberName);
            // reload page
            window.location.reload();
          } else {
            alert("Committee rejected successfully by " + memberName);
            window.location.reload();
          }
        } else {
          alert("Error approving Committee");
        }
      });
    };

    _this.onSubmitCommitee = function () {
      var form_data = new FormData();
      form_data.append("cs_id", _this.state.cs_id);
      form_data.append("committee", JSON.stringify({
        committee: _this.state.committeeMembers
      }));
      form_data.append("csrfmiddlewaretoken", _this.getCookie("csrftoken"));

      fetch(BASE_URL + "/comperative_schedule/save_committee", {
        method: "POST",
        headers: {
          "X-CSRFToken": _this.getCookie("csrftoken")
        },
        body: form_data
      }).then(function (response) {
        return response.json();
      }).then(function (data) {
        console.log("data: ", data);
        if (data.success) {
          alert("Committee saved successfully");
        } else {
          alert("Error saving Committee");
        }
      });
    };

    _this.onApprovalApprove = function (role, username, approval, justification) {
      var form_data = new FormData();
      form_data.append("cs_id", _this.state.cs_id);
      form_data.append("role", role);
      form_data.append("username", username);
      form_data.append("approval", approval);
      form_data.append("justification", justification);
      form_data.append("csrfmiddlewaretoken", _this.getCookie("csrftoken"));

      fetch(BASE_URL + "/comperative_schedule/approval_approve", {
        method: "POST",
        headers: {
          "X-CSRFToken": _this.getCookie("csrftoken")
        },
        body: form_data
      }).then(function (response) {
        return response.json();
      }).then(function (data) {
        console.log("data: ", data);
        if (data.success) {
          var _role = data.role;
          var _approval = data.approval;
          if (_role === "finance_manager") {
            var fm_approval = data.fm_approval ? data.fm_approval : null;
            _this.setState({
              fmApproval: fm_approval
            });
          } else if (_role === "general_manager") {
            var gm_approval = data.gm_approval ? data.gm_approval : null;
            _this.setState({
              gmApproval: gm_approval
            });
          }
          if (_approval === "Approved") {
            alert("Approval successfull");
            // reload page
            window.location.reload();
          } else {
            alert("Rejected successfully");
            window.location.reload();
          }
        } else {
          alert("Error approving Approval");
        }
      });
    };

    _this.onApprovalJustificationModal = function (username, role) {
      _this.setState(Object.assign({}, _this.state, {
        currentApprover: {
          username: username,
          role: role,
          justification: ""
        },
        approvalsJustificationModal: !_this.state.approvalsJustificationModal
      }));
    };

    _this.onSaveSupplier = function () {
      var form_data = new FormData();
      form_data.append("supplier_name", _this.state.newSupplier.supplier_name);
      form_data.append("csrfmiddlewaretoken", _this.getCookie("csrftoken"));

      fetch(BASE_URL + "/comperative_schedule/save_supplier", {
        method: "POST",
        headers: {
          "X-CSRFToken": _this.getCookie("csrftoken")
        },
        body: form_data
      }).then(function (response) {
        return response.json();
      }).then(function (data) {
        console.log("data: ", data);
        if (data.success) {
          alert("Supplier saved successfully");
          _this.setState(Object.assign({}, _this.state, {
            onAddSupplier: false,
            newSupplier: {
              supplier_name: "",
              supplier_contact: "",
              supplier_email: "",
              supplier_address: ""
            }
          }));
        } else {
          alert("Error saving Supplier");
        }
      });
    };

    _this.onApprovalJustificationChange = function (name_, event) {
      var _event$target4 = event.target,
          name = _event$target4.name,
          value = _event$target4.value;

      var currentApprover = _this.state.currentApprover;
      currentApprover[name] = value;
      _this.setState(Object.assign({}, _this.state, {
        currentApprover: currentApprover
      }));
    };

    _this.onAddCSItem = function (item_id, ordered) {
      // check is item already added
      var item = _this.state.cs_items.find(function (item) {
        return item.id === item_id;
      });
      console.log("item: ", item);
      if (item) {
        // update item selected to false
        item.ordered = false;
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
        _item2.ordered = true;
        _item2.item_required = _item2.item_required;
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
      }
    };

    _this.onSubmitCSItems = function () {
      var form_data = new FormData();
      form_data.append("cs_id", _this.state.cs_id);
      form_data.append("pr_id", _this.state.pr_number);
      form_data.append("json_data", JSON.stringify({
        cs_items: _this.state.cs_items
      }));
      form_data.append("csrfmiddlewaretoken", _this.getCookie("csrftoken"));

      fetch(BASE_URL + "/comperative_schedule/update_pritem_ordered", {
        method: "POST",
        headers: {
          "X-CSRFToken": _this.getCookie("csrftoken")
        },
        body: form_data
      }).then(function (response) {
        return response.json();
      }).then(function (data) {
        console.log("data: ", data);
        if (data.success) {
          alert("Items saved successfully");
        } else {
          alert("Error saving Items");
        }
      });
      _this.setState(Object.assign({}, _this.state, {
        addItemsModal: false
      }));
    };

    _this.onAddSuppliersModal = function () {
      _this.setState(Object.assign({}, _this.state, {
        onAddSupplier: !_this.state.onAddSupplier
      }));
    };

    _this.onSupplierChange = function (name_, event) {
      var _event$target5 = event.target,
          name = _event$target5.name,
          value = _event$target5.value;


      _this.setState(Object.assign({}, _this.state, {
        newSupplier: Object.assign({}, _this.state.newSupplier, _defineProperty({}, name, value))
      }));
    };

    _this.onAddBidModal = function () {
      var bid_count = _this.state.bids.length + 1;
      _this.setState(Object.assign({}, _this.state, {
        addBidModal: !_this.state.addBidModal,
        bid_count: bid_count,
        currentBid: {
          bid_count: bid_count
        }
      }));
    };

    _this.onUpdateBidModal = function (bid_count) {
      var bid = _this.state.bids.find(function (bid) {
        return bid.bid_count === bid_count;
      });
      _this.setState(Object.assign({}, _this.state, {
        updateBidModal: !_this.state.updateBidModal,
        currentBid: bid
      }));
    };

    _this.onCloseCurrentBid = function () {
      var bid_count = _this.state.bids.length - 1;
      _this.setState(Object.assign({}, _this.state, {
        currentBid: {},
        addBidModal: false,
        updateBidModal: false,
        bid_count: bid_count
      }));
    };

    _this.onCloseUpdateBidBid = function () {
      _this.setState(Object.assign({}, _this.state, {
        currentBid: {},
        updateBidModal: false
      }));
    };

    _this.onCurrentBidChange = function (name_, event) {
      var currentBid = _this.state.currentBid;
      if (name_ === "bid_document") {
        var bid_file = event.target.files[0];
        var bid_document_url = _this.onGetFileObjectUrl(event.target.files[0]);
        currentBid[name_] = bid_file;
        currentBid.bid_document_url = bid_document_url;
      } else if (name_ === "supplier") {
        var _event$target6 = event.target,
            name = _event$target6.name,
            value = _event$target6.value;

        console.log("value: ", value);
        var id_name = value ? value.split("-#-") : [];
        currentBid[name_] = id_name.length > 0 ? id_name[0] : "";
        currentBid["supplier_name"] = id_name.length >= 1 ? id_name[1] : "";
      } else {
        var _event$target7 = event.target,
            _name = _event$target7.name,
            _value = _event$target7.value;

        currentBid[name_] = _value;
      }
      _this.setState(Object.assign({}, _this.state, {
        currentBid: currentBid
      }));
    };

    _this.onCurrentBidItemChange = function (description, name_, event) {
      // check if item exists in current bid
      console.log("description: ", description);
      var item = _this.state.currentBid.items ? _this.state.currentBid.items.find(function (item) {
        return item.item_required === description;
      }) : null;
      console.log("item: ", item);
      // if item exists update item
      if (item) {
        var _event$target8 = event.target,
            name = _event$target8.name,
            value = _event$target8.value;

        item[name_] = value;
        // update item in current bid
        var items = _this.state.currentBid.items.map(function (_item) {
          if (_item.item_required === description) {
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
          return item.item_required === description;
        });
        // create new item
        var new_item = {
          item_required: _item3.item_required,
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
      // console.log currentBid item details
      console.log("currentBid: ", currentBid);
      if (currentBid.supplier_name === "" || currentBid.supplier_name === undefined) {
        alert("Please select a supplier");
        return;
      } else if (currentBid.bid_date === "" || currentBid.bid_date === undefined) {
        alert("Please select a bid date");
        return;
      } else {
        // check if current bid already exists
        if (currentBid.items) {
          console.log("state bids found: ", _this.state.bids);
          var bid = _this.state.bids.find(function (bid) {
            return bid && bid.bid_count === currentBid.bid_count;
          });
          console.log("bid found: ", bid);
          if (bid) {
            // update bid
            console.log("currentBid 1: ", currentBid);
            var items = currentBid.items.map(function (item) {
              item.total_price = item.quantity * item.unit_price;
              return item;
            });
            currentBid.items = items;
            console.log("currentBid: ", currentBid);
            _this.onSaveBid(currentBid);
            var bids = _this.state.bids.map(function (bid) {
              if (bid.bid_count === currentBid.bid_count) {
                return currentBid;
              }
              return bid;
            });

            _this.setState(Object.assign({}, _this.state, {
              bids: bids,
              currentBid: {},
              updateBidModal: false
            }));
          } else {
            // calculate total price for each item
            var _items2 = currentBid.items.map(function (item) {
              item.total_price = item.quantity * item.unit_price;
              return item;
            });
            // update current bid items
            currentBid.items = _items2;
            _this.onSaveBid(currentBid);

            var _bids = _this.state.bids;
            console.log("currentBid: ", currentBid);
            _bids.push(currentBid);
            // check if compliance for supplier exists
            var compliances = _this.state.compliance;
            var compliance = compliances.find(function (compliance) {
              return compliance.supplier_name === currentBid.supplier_name;
            });
            var compliance_ = {};
            if (!compliance) {
              compliance_ = {
                bid_no: currentBid.bid_count,
                supplier: currentBid.supplier,
                supplier_name: currentBid.supplier_name,
                payment_terms: false,
                bid_validity: false,
                delivery_period: false,
                technical_specifications: false,
                valid_tax_clearance: false,
                registered_with_praz: false,
                tax_status: false,
                site_visit: false,
                samples_required: false,
                decision: false,
                reject: true,
                remarks: ""
              };
              compliances.push(compliance_);
            }

            var complianceRemarks = _this.state.complianceRemarks;
            var complianceRemark = complianceRemarks.find(function (complianceRemark) {
              return complianceRemark.supplier_name === currentBid.supplier_name;
            });

            if (!complianceRemark) {
              var complianceRemark_ = {
                bid_count: currentBid.bid_count,
                supplier: currentBid.supplier,
                supplier_name: currentBid.supplier_name,
                remarks: ""
              };
              complianceRemarks.push(complianceRemark_);
            }

            _this.setState(Object.assign({}, _this.state, {
              bids: _bids,
              currentBid: {},
              addBidModal: false,
              compliance: compliances,
              complianceRemarks: complianceRemarks
            }));
          }
        } else {
          alert("Please add items to the bid");
        }
      }
    };

    _this.onSaveBid = function (currentBid) {
      var form_data = new FormData();

      // add enctype to form data
      form_data.enctype = "multipart/form-data";
      form_data.append("cs_id", _this.state.cs_id);
      form_data.append("bid_no", currentBid.bid_count);
      form_data.append("supplier_id", currentBid.supplier);
      form_data.append("supplier_name", currentBid.supplier_name);
      form_data.append("bid_date", currentBid.bid_date);
      form_data.append("json_data", JSON.stringify({
        bid_items: currentBid.items
      }));
      form_data.append("bid_document", currentBid.bid_document);
      form_data.append("csrfmiddlewaretoken", _this.getCookie("csrftoken"));

      fetch(BASE_URL + "/comperative_schedule/save_bid", {
        method: "POST",
        headers: {
          "X-CSRFToken": _this.getCookie("csrftoken")
        },
        body: form_data
      }).then(function (response) {
        return response.json();
      }).then(function (data) {
        console.log("data: ", data);
        if (data.success) {
          alert("Bid saved successfully");
        } else {
          alert("Error saving Bid");
        }
      });
    };

    _this.onSaveSchedule = function () {
      var form_data = new FormData();
      // add enctype to form data
      form_data.enctype = "multipart/form-data";
      form_data.append("proc_ref", _this.state.proc_ref);
      form_data.append("scope_of_work", _this.state.scope_of_work);
      form_data.append("pr_number", _this.state.pr_number);
      form_data.append("quantity", _this.state.quantity);
      form_data.append("pr_date", _this.state.pr_date);
      form_data.append("closing_date", _this.state.closing_date);
      form_data.append("ref_date", _this.state.ref_date);
      form_data.append("closing_time_hour", _this.state.closing_time_hour);
      form_data.append("date_tender_opened", _this.state.date_tender_opened);
      form_data.append("username", _this.state.username);
      form_data.append("tender_adjudication_committee_date", _this.state.tender_adjudication_committee_date);
      form_data.append("advert", _this.state.advert);
      form_data.append("csrfmiddlewaretoken", _this.getCookie("csrftoken"));

      fetch(BASE_URL + "/comperative_schedule/save", {
        method: "POST",
        headers: {
          "X-CSRFToken": _this.getCookie("csrftoken")
        },
        body: form_data
      }).then(function (response) {
        return response.json();
      }).then(function (data) {
        console.log("comperative schedule saved data: ", data);
        if (data.success) {
          alert("Comparative Schedule saved successfully" + " " + data.cs_id);
          _this.setState(Object.assign({}, _this.state, {
            cs_id: data.cs_id,
            cs_owner: data.cs_owner
          }));
        } else {
          alert("Error saving Comparative Schedule");
        }
      });
    };

    _this.onUpdateSchedule = function () {
      var form_data = new FormData();
      // add enctype to form data
      form_data.enctype = "multipart/form-data";
      form_data.append("cs_id", _this.state.cs_id);
      form_data.append("proc_ref", _this.state.proc_ref);
      form_data.append("scope_of_work", _this.state.scope_of_work);
      form_data.append("pr_number", _this.state.pr_number);
      form_data.append("quantity", _this.state.quantity);
      form_data.append("pr_date", _this.state.pr_date);
      form_data.append("closing_date", _this.state.closing_date);
      form_data.append("ref_date", _this.state.ref_date);
      form_data.append("closing_time_hour", _this.state.closing_time_hour);
      form_data.append("date_tender_opened", _this.state.date_tender_opened);
      form_data.append("username", _this.state.username);
      form_data.append("tender_adjudication_committee_date", _this.state.tender_adjudication_committee_date);
      form_data.append("advert", _this.state.advert);
      form_data.append("csrfmiddlewaretoken", _this.getCookie("csrftoken"));

      fetch(BASE_URL + "/comperative_schedule/update", {
        method: "POST",
        headers: {
          "X-CSRFToken": _this.getCookie("csrftoken")
        },
        body: form_data
      }).then(function (response) {
        return response.json();
      }).then(function (data) {
        console.log("data: ", data);
        if (data.success) {
          alert("Comparative Schedule updated successfully" + " " + data.cs_id);
        } else {
          alert("Error updating Comparative Schedule");
        }
      });
    };

    _this.onDeleteBidModal = function (bid_count, supplier_name) {
      // reset bid no index
      var bid_count_ = _this.state.bid_count - 1;
      var bids = _this.state.bids.filter(function (bid) {
        return bid.bid_count !== bid_count;
      });
      // update bid_count index for all bids sequentially
      bids = bids.map(function (bid, index) {
        bid.bid_count = index + 1;
        return bid;
      });
      _this.setState(Object.assign({}, _this.state, {
        bids: bids,
        bid_count: bid_count_
      }));
      _this.deleteBid(bid_count, supplier_name);
    };

    _this.deleteBid = function (bid_count, supplier_name) {
      var form_data = new FormData();
      form_data.append("cs_id", _this.state.cs_id);
      form_data.append("bid_count", bid_count);
      form_data.append("supplier_name", supplier_name);
      form_data.append("csrfmiddlewaretoken", _this.getCookie("csrftoken"));

      fetch(BASE_URL + "/comperative_schedule/delete_bid", {
        method: "POST",
        headers: {
          "X-CSRFToken": _this.getCookie("csrftoken")
        },
        body: form_data
      }).then(function (response) {
        return response.json();
      }).then(function (data) {
        console.log("data: ", data);
        if (data.success) {
          alert("Bid deleted successfully");
        } else {
          alert("Error deleting Bid");
        }
      });
    };

    _this.onAddBid = function () {
      var bid_count = _this.state.bid_count + 1;
      _this.setState(Object.assign({}, _this.state, {
        bid_count: bid_count,
        bids: [].concat(_toConsumableArray(_this.state.bids), [{
          supplier: "",
          bid_date: "",
          bid_count: bid_count,
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

    _this.onInputChange = function (event) {
      console.log(event);
      var _event$target9 = event.target,
          name = _event$target9.name,
          value = _event$target9.value;

      _this.setState(Object.assign({}, _this.state, _defineProperty({}, name, value)));
    };

    _this.onFileInputChange = function (name_, event) {
      var _Object$assign4;

      console.log(event);
      var file = event.target.files[0];
      var fileUrl = _this.onGetFileObjectUrl(file);
      _this.setState(Object.assign({}, _this.state, (_Object$assign4 = {}, _defineProperty(_Object$assign4, name_, file), _defineProperty(_Object$assign4, "advert_url", fileUrl), _Object$assign4)));
    };

    _this.onAddComplianceTable = function () {
      // add bid compliance
      var compliances = _this.state.bids.map(function (bid) {
        return {
          bid_no: bid.bid_count,
          supplier: bid.supplier,
          supplier_name: bid.supplier_name,
          payment_terms: false,
          bid_validity: false,
          delivery_period: false,
          technical_specifications: false,
          valid_tax_clearance: false,
          registered_with_praz: false,
          tax_status: false,
          site_visit: false,
          samples_required: false,
          decision: false,
          reject: true,
          remarks: ""
        };
      });

      var complianceRemarks = _this.state.bids.map(function (bid) {
        return {
          bid_count: bid.bid_count,
          supplier: bid.supplier,
          supplier_name: bid.supplier_name,
          remarks: ""
        };
      });

      _this.setState(Object.assign({}, _this.state, {
        compliance: compliances,
        complianceRemarks: complianceRemarks,
        complianceTable: !_this.state.complianceTable
      }));
    };

    _this.onComplianceItemsChange = function (name_, event) {
      console.log("name and value: ", name_, event);
      var _event$target10 = event.target,
          name = _event$target10.name,
          value = _event$target10.value;

      var compliance = _this.state.compliance;
      var updatedComplianceList = compliance.map(function (compliance_, index) {
        var _compliance = {};
        if (_this.state.showSamples && _this.state.showSiteVisit) {
          _compliance = {
            payment_terms: compliance_.payment_terms,
            bid_validity: compliance_.bid_validity,
            delivery_period: compliance_.delivery_period,
            technical_specifications: compliance_.technical_specifications,
            valid_tax_clearance: compliance_.valid_tax_clearance,
            registered_with_praz: compliance_.registered_with_praz,
            tax_status: compliance_.tax_status,
            site_visit: compliance_.site_visit,
            samples_required: compliance_.samples_required
          };
        } else if (_this.state.showSamples && !_this.state.showSiteVisit) {
          _compliance = {
            payment_terms: compliance_.payment_terms,
            bid_validity: compliance_.bid_validity,
            delivery_period: compliance_.delivery_period,
            technical_specifications: compliance_.technical_specifications,
            valid_tax_clearance: compliance_.valid_tax_clearance,
            registered_with_praz: compliance_.registered_with_praz,
            tax_status: compliance_.tax_status,
            samples_required: compliance_.samples_required
          };
        } else if (!_this.state.showSamples && _this.state.showSiteVisit) {
          _compliance = {
            payment_terms: compliance_.payment_terms,
            bid_validity: compliance_.bid_validity,
            delivery_period: compliance_.delivery_period,
            technical_specifications: compliance_.technical_specifications,
            valid_tax_clearance: compliance_.valid_tax_clearance,
            registered_with_praz: compliance_.registered_with_praz,
            tax_status: compliance_.tax_status,
            site_visit: compliance_.site_visit
          };
        } else {
          _compliance = {
            payment_terms: compliance_.payment_terms,
            bid_validity: compliance_.bid_validity,
            delivery_period: compliance_.delivery_period,
            technical_specifications: compliance_.technical_specifications,
            valid_tax_clearance: compliance_.valid_tax_clearance,
            registered_with_praz: compliance_.registered_with_praz,
            tax_status: compliance_.tax_status
          };
        }

        // set compliance_['decision'] to true if all compliance are true
        var compliance_values = Object.values(_compliance);
        console.log("compliances: ", compliance_values);
        var decision = compliance_values.every(function (value) {
          return value === true;
        });
        compliance_["decision"] = decision;
        compliance_["reject"] = !decision;

        return compliance_;
      });

      _this.setState(Object.assign({}, _this.state, _defineProperty({
        compliance: updatedComplianceList
      }, name_, value)));
    };

    _this.onComplianceChange = function (index, event) {
      var _event$target11 = event.target,
          name = _event$target11.name,
          checked = _event$target11.checked;

      console.log("name: ", name, "checked: ", checked);
      var compliance = _this.state.compliance;
      compliance[index][name] = checked;
      // filter decision and reject from list
      var _compliance = {};
      if (_this.state.showSamples && _this.state.showSiteVisit) {
        _compliance = {
          payment_terms: compliance[index].payment_terms,
          bid_validity: compliance[index].bid_validity,
          delivery_period: compliance[index].delivery_period,
          technical_specifications: compliance[index].technical_specifications,
          valid_tax_clearance: compliance[index].valid_tax_clearance,
          registered_with_praz: compliance[index].registered_with_praz,
          tax_status: compliance[index].tax_status,
          site_visit: compliance[index].site_visit,
          samples_required: compliance[index].samples_required
        };
      } else if (_this.state.showSamples && !_this.state.showSiteVisit) {
        _compliance = {
          payment_terms: compliance[index].payment_terms,
          bid_validity: compliance[index].bid_validity,
          delivery_period: compliance[index].delivery_period,
          technical_specifications: compliance[index].technical_specifications,
          valid_tax_clearance: compliance[index].valid_tax_clearance,
          registered_with_praz: compliance[index].registered_with_praz,
          tax_status: compliance[index].tax_status,
          samples_required: compliance[index].samples_required
        };
      } else if (!_this.state.showSamples && _this.state.showSiteVisit) {
        _compliance = {
          payment_terms: compliance[index].payment_terms,
          bid_validity: compliance[index].bid_validity,
          delivery_period: compliance[index].delivery_period,
          technical_specifications: compliance[index].technical_specifications,
          valid_tax_clearance: compliance[index].valid_tax_clearance,
          registered_with_praz: compliance[index].registered_with_praz,
          tax_status: compliance[index].tax_status,
          site_visit: compliance[index].site_visit
        };
      } else {
        _compliance = {
          payment_terms: compliance[index].payment_terms,
          bid_validity: compliance[index].bid_validity,
          delivery_period: compliance[index].delivery_period,
          technical_specifications: compliance[index].technical_specifications,
          valid_tax_clearance: compliance[index].valid_tax_clearance,
          registered_with_praz: compliance[index].registered_with_praz,
          tax_status: compliance[index].tax_status
        };
      }

      // set compliance[index]['decision'] to true if all compliance are true
      var compliance_values = Object.values(_compliance);
      console.log("compliances: ", compliance_values);
      var decision = compliance_values.every(function (value) {
        return value === true;
      });
      compliance[index]["decision"] = decision;
      compliance[index]["reject"] = !decision;

      _this.setState(Object.assign({}, _this.state, {
        compliance: compliance
      }));
    };

    _this.onComplianceRemarksChange = function (supplier_name, event) {
      var _event$target12 = event.target,
          name = _event$target12.name,
          value = _event$target12.value;

      console.log("name: ", name, "value: ", value, "supplier_name: ", supplier_name);
      var complianceRemarks = _this.state.complianceRemarks;
      var index = complianceRemarks.findIndex(function (item) {
        return item.supplier_name === supplier_name;
      });
      if (index !== -1) {
        complianceRemarks[index]["remarks"] = value;
        _this.setState(Object.assign({}, _this.state, {
          complianceRemarks: complianceRemarks
        }));
      } else {
        complianceRemarks.push({
          supplier_name: supplier_name,
          remarks: value
        });
        _this.setState(Object.assign({}, _this.state, {
          complianceRemarks: complianceRemarks
        }));
      }
    };

    _this.onSaveCompliance = function () {
      var form_data = new FormData();
      form_data.append("cs_id", _this.state.cs_id);
      form_data.append("compliance", JSON.stringify({
        compliance: _this.state.compliance
      }));
      form_data.append("complianceRemarks", JSON.stringify({
        complianceRemarks: _this.state.complianceRemarks
      }));
      form_data.append("csrfmiddlewaretoken", _this.getCookie("csrftoken"));

      fetch(BASE_URL + "/comperative_schedule/save_compliance", {
        method: "POST",
        headers: {
          "X-CSRFToken": _this.getCookie("csrftoken")
        },
        body: form_data
      }).then(function (response) {
        return response.json();
      }).then(function (data) {
        console.log("data: ", data);
        if (data.success) {
          alert("Compliance saved successfully");
        } else {
          alert("Error saving Compliance");
        }
      });
    };

    _this.onCloseCS = function () {
      var form_data = new FormData();
      form_data.append("cs_id", _this.state.cs_id);
      form_data.append("csrfmiddlewaretoken", _this.getCookie("csrftoken"));

      fetch(BASE_URL + "/comperative_schedule/close_compliance", {
        method: "POST",
        headers: {
          "X-CSRFToken": _this.getCookie("csrftoken")
        },
        body: form_data
      }).then(function (response) {
        return response.json();
      }).then(function (data) {
        console.log("data: ", data);
        if (data.success) {
          var rankings = data.rankings;
          _this.setState(Object.assign({}, _this.state, {
            rankings: rankings,
            rankingTable: true
          }));
          alert("Schedule closed successfully");
        } else {
          alert("Error saving Schedule");
        }
      });
    };

    _this.state = {
      requester_role: "",
      cs_id: "",
      cs_owner: "",
      committeeApprovalComplete: false,
      plan_ref: "",
      proc_ref: "",
      proc_plan: null,
      scope_of_work: "",
      pr_number: "",
      pr_attachments: [],
      quantity: "",
      pr_date: "",
      closing_date: "",
      closing_time_hour: "",
      ref_date: "",
      date_tender_opened: "",
      tender_adjudication_committee_date: "",
      advert: null,
      advert_url: null,
      bid_count: 0,
      currentBid: {},
      bids: [],
      addBidModal: false,
      updateBidModal: false,
      cs_items: [],
      cs_item_count: 0,
      addItemsModal: false,

      complianceTable: false,
      compliance: [],
      complianceRemarks: [],
      showSamples: "",
      showSiteVisit: "",

      rankingTable: false,
      rankings: [],

      committeeTable: false,
      committeeMembers: [],
      committeeJustificationModal: false,
      member: {
        memberName: "",
        memberUserName: "",
        memberPosition: "",
        memberApproval: ""
      },
      gmApproval: null,
      fmApproval: null,
      approvalsJustificationModal: false,
      users: [],
      currentApprover: {
        username: "",
        justification: "",
        role: ""
      },

      pr_items: [],
      suppliers: [],
      proc_plans: [],
      uom: null,
      authUser: {},
      username: "",

      fetchPR: false,
      onAddSupplier: false,
      newSupplier: {
        supplier_name: "",
        supplier_contact: "",
        supplier_email: "",
        supplier_address: ""
      }
    };
    _this.getCreateData = _this.getCreateData.bind(_this);
    _this.onAddBid = _this.onAddBid.bind(_this);
    _this.onUpdateBidModal = _this.onUpdateBidModal.bind(_this);
    _this.onAddItemsModal = _this.onAddItemsModal.bind(_this);
    _this.onCommitteeChange = _this.onCommitteeChange.bind(_this);
    _this.onGetFileObjectUrl = _this.onGetFileObjectUrl.bind(_this);
    _this.onComplianceItemsChange = _this.onComplianceItemsChange.bind(_this);
    _this.onComplianceRemarksChange = _this.onComplianceRemarksChange.bind(_this);
    _this.onCommitteeApprove = _this.onCommitteeApprove.bind(_this);
    _this.onCommitteeJustificationChange = _this.onCommitteeJustificationChange.bind(_this);
    _this.onCommitteeJustificationModal = _this.onCommitteeJustificationModal.bind(_this);
    _this.onApprovalJustificationModal = _this.onApprovalJustificationModal.bind(_this);
    _this.onApprovalJustificationChange = _this.onApprovalJustificationChange.bind(_this);
    _this.onSupplierChange = _this.onSupplierChange.bind(_this);
    return _this;
  }

  _createClass(CreateCS, [{
    key: "componentDidMount",
    value: function componentDidMount() {
      console.log("props: ", this.props);
      if (this.props.csid !== "") {
        this.setState({
          username: this.props.username,
          cs_id: this.props.csid
        });
        this.getCSData(this.props.csid);
      } else if (this.props.prid !== "") {
        this.setState({
          username: this.props.username,
          pr_number: this.props.prid
        });
        this.getCreateData(this.props.prid);
      } else {
        this.setState({
          username: this.props.username,
          fetchPR: true
        });
      }
    }
  }, {
    key: "onSelectChange",
    value: function onSelectChange(name_, event) {
      var _event$target13 = event.target,
          name = _event$target13.name,
          value = _event$target13.value;

      this.setState(Object.assign({}, this.state, _defineProperty({}, name_, value)));
    }
  }, {
    key: "onFilterSelectCenters",
    value: function onFilterSelectCenters(name_, event) {
      var _event$target14 = event.target,
          name = _event$target14.name,
          value = _event$target14.value;

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
      var updateBidModal = null;
      var complianceTable = null;
      var rankingTable = null;
      var committeeTable = null;
      var rejectJustification = null;
      var approvalsTable = null;
      var rejectApprovalJustification = null;
      var supplierModal = null;

      if (this.state.onAddSupplier) {
        supplierModal = React.createElement(
          "div",
          { className: "fixed inset-0 flex items-center justify-center z-50 pt-10 pb-20" },
          React.createElement(
            "div",
            { className: "bg-gulf-blue-100 rounded-lg shadow-lg p-6 max-h-screen overflow-y-auto" },
            React.createElement(
              "div",
              { className: "flex justify-between items-center mb-4" },
              React.createElement(
                "h3",
                { className: "text-lg font-medium" },
                "ADD SUPPLIER"
              ),
              React.createElement(
                "button",
                {
                  type: "button",
                  className: "text-gray-400 hover:text-gray-500 focus:outline-none",
                  onClick: this.onAddSuppliersModal
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
              { className: "overflow-auto px-2 py-2 mt-5 rounded-md bg-gulf-blue-300" },
              React.createElement(
                "div",
                null,
                React.createElement(
                  "div",
                  { className: "flex-1 w-full ml-1" },
                  React.createElement(
                    "label",
                    {
                      htmlFor: "supplier_name",
                      className: "block text-sm font-medium leading-6 text-gray-900"
                    },
                    "Supplier Name"
                  ),
                  React.createElement(
                    "div",
                    { className: "mt-2" },
                    React.createElement("input", {
                      name: "supplier_name",
                      onChange: function onChange(e) {
                        return _this2.onSupplierChange("supplier_name", e);
                      },
                      type: "text",
                      required: "required",
                      className: "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                    })
                  )
                )
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
                      onClick: this.onAddSuppliersModal,
                      className: "rounded-md text-gray-50 text-sm bg-gray-300 hover:bg-blue-550 px-3 py-2 font-semibold leading-6"
                    },
                    React.createElement(
                      "span",
                      { className: "ml-2" },
                      "CANCEL"
                    )
                  )
                ),
                React.createElement(
                  "div",
                  { className: "m-2" },
                  React.createElement(
                    "button",
                    {
                      onClick: this.onSaveSupplier,
                      className: "rounded-md text-gray-50 text-sm bg-blue-925 hover:bg-blue-550 px-3 py-2 font-semibold leading-6"
                    },
                    React.createElement(
                      "span",
                      { className: "ml-2" },
                      "SAVE SUPPLIER"
                    )
                  )
                )
              )
            )
          )
        );
      }

      if (this.state.approvalsJustificationModal) {
        rejectApprovalJustification = React.createElement(
          "div",
          { className: "fixed inset-0 flex items-center justify-center z-50 pt-10 pb-20" },
          React.createElement(
            "div",
            { className: "bg-gulf-blue-100 rounded-lg shadow-lg p-6 max-h-screen overflow-y-auto" },
            React.createElement(
              "div",
              { className: "flex justify-between items-center mb-4" },
              React.createElement(
                "h3",
                { className: "text-lg font-medium" },
                "Reason for rejection"
              ),
              React.createElement(
                "button",
                {
                  type: "button",
                  className: "text-gray-400 hover:text-gray-500 focus:outline-none",
                  onClick: this.onApprovalJustificationModal
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
              { className: "overflow-auto px-2 py-2 mt-5 rounded-md bg-gulf-blue-300" },
              React.createElement(
                "div",
                null,
                React.createElement(
                  "div",
                  { className: "flex-1 w-full ml-1" },
                  React.createElement(
                    "label",
                    {
                      htmlFor: "bid_date",
                      className: "block text-sm font-medium leading-6 text-gray-900"
                    },
                    "Justification"
                  ),
                  React.createElement(
                    "div",
                    { className: "mt-2" },
                    React.createElement("textarea", {
                      name: "justification",
                      onChange: function onChange(e) {
                        return _this2.onApprovalJustificationChange("justification", e);
                      },
                      type: "text",
                      required: "required",
                      className: "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                    })
                  )
                )
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
                      onClick: this.onApprovalJustificationModal,
                      className: "rounded-md text-gray-50 text-sm bg-gray-300 hover:bg-blue-550 px-3 py-2 font-semibold leading-6"
                    },
                    React.createElement(
                      "span",
                      { className: "ml-2" },
                      "CANCEL"
                    )
                  )
                ),
                React.createElement(
                  "div",
                  { className: "m-2" },
                  React.createElement(
                    "button",
                    {
                      onClick: function onClick() {
                        return _this2.onApprovalApprove(_this2.state.currentApprover.role, _this2.state.currentApprover.username, "Rejected", _this2.state.currentApprover.justification);
                      },
                      className: "rounded-md text-gray-50 text-sm bg-blue-925 hover:bg-blue-550 px-3 py-2 font-semibold leading-6"
                    },
                    React.createElement(
                      "span",
                      { className: "ml-2" },
                      "PROCEED"
                    )
                  )
                )
              )
            )
          )
        );
      }

      if (this.state.committeeJustificationModal) {
        rejectJustification = React.createElement(
          "div",
          { className: "fixed inset-0 flex items-center justify-center z-50 pt-10 pb-20" },
          React.createElement(
            "div",
            { className: "bg-gulf-blue-100 rounded-lg shadow-lg p-6 max-h-screen overflow-y-auto" },
            React.createElement(
              "div",
              { className: "flex justify-between items-center mb-4" },
              React.createElement(
                "h3",
                { className: "text-lg font-medium" },
                "Reason for rejection"
              ),
              React.createElement(
                "button",
                {
                  type: "button",
                  className: "text-gray-400 hover:text-gray-500 focus:outline-none",
                  onClick: this.onCommitteeJustificationModal
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
              { className: "overflow-auto px-2 py-2 mt-5 rounded-md bg-gulf-blue-300" },
              React.createElement(
                "div",
                null,
                React.createElement(
                  "div",
                  { className: "flex-1 w-full ml-1" },
                  React.createElement(
                    "label",
                    {
                      htmlFor: "bid_date",
                      className: "block text-sm font-medium leading-6 text-gray-900"
                    },
                    "Justification"
                  ),
                  React.createElement(
                    "div",
                    { className: "mt-2" },
                    React.createElement("textarea", {
                      name: "justification",
                      onChange: function onChange(e) {
                        return _this2.onCommitteeJustificationChange("justification", e);
                      },
                      type: "text",
                      required: "required",
                      className: "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                    })
                  )
                )
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
                      onClick: this.onCommitteeJustificationModal,
                      className: "rounded-md text-gray-50 text-sm bg-gray-300 hover:bg-blue-550 px-3 py-2 font-semibold leading-6"
                    },
                    React.createElement(
                      "span",
                      { className: "ml-2" },
                      "CANCEL"
                    )
                  )
                ),
                React.createElement(
                  "div",
                  { className: "m-2" },
                  React.createElement(
                    "button",
                    {
                      onClick: function onClick() {
                        return _this2.onCommitteeApprove(_this2.state.currentApprover.username, "Rejected", _this2.state.currentApprover.justification);
                      },
                      className: "rounded-md text-gray-50 text-sm bg-blue-925 hover:bg-blue-550 px-3 py-2 font-semibold leading-6"
                    },
                    React.createElement(
                      "span",
                      { className: "ml-2" },
                      "PROCEED"
                    )
                  )
                )
              )
            )
          )
        );
      }

      if (this.state.addItemsModal) {
        itemsModal = React.createElement(
          "div",
          { className: "fixed inset-0 flex items-center justify-center z-50 pt-10 pb-20" },
          React.createElement(
            "div",
            { className: "bg-gulf-blue-100 rounded-lg shadow-lg p-6 max-h-screen overflow-y-auto" },
            React.createElement(
              "div",
              { className: "flex justify-between items-center mb-4" },
              React.createElement(
                "h3",
                { className: "text-lg font-medium" },
                "SELECT SCHEDULE ITEMS"
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
              { className: "overflow-auto px-2 py-2 mt-5 rounded-md bg-gulf-blue-300" },
              React.createElement(
                "table",
                {
                  style: { width: "100%" },
                  className: "table-auto w-full text-left"
                },
                React.createElement(
                  "thead",
                  null,
                  React.createElement(
                    "tr",
                    { className: "text-gray-900" },
                    React.createElement(
                      "th",
                      { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                      "Select"
                    ),
                    React.createElement(
                      "th",
                      { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                      "Item"
                    ),
                    React.createElement(
                      "th",
                      { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
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
                      { className: "text-gray-900" },
                      React.createElement(
                        "td",
                        { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                        React.createElement("input", {
                          type: "checkbox",
                          checked: item.ordered ? item.ordered : false,
                          onChange: function onChange() {
                            return _this2.onAddCSItem(item.id, item.ordered);
                          }
                        })
                      ),
                      React.createElement(
                        "td",
                        { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                        item.item_required
                      ),
                      React.createElement(
                        "td",
                        { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                        item.quantity
                      )
                    );
                  })
                )
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
                      onClick: this.onSubmitCSItems,
                      className: "rounded-md text-gray-50 text-sm bg-blue-925 hover:bg-blue-550 px-3 py-2 font-semibold leading-6"
                    },
                    React.createElement(
                      "span",
                      { className: "ml-2" },
                      "SAVE SCHEDULE ITEMS"
                    )
                  )
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
            { className: "bg-gulf-blue-100 rounded-lg shadow-lg p-6 max-h-screen min-w-max overflow-y-auto" },
            React.createElement(
              "div",
              { className: "flex justify-between items-center mb-4" },
              React.createElement(
                "h3",
                { className: "text-lg font-medium" },
                "ADD BID DETAILS"
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
                          {
                            value: this.state.currentBid.supplier + "-#-" + this.state.currentBid.supplier_name
                          },
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
                            {
                              value: supplier.id + "-#-" + supplier.name
                            },
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
                          defaultValue: item.item_required,
                          onChange: function onChange(e) {
                            return _this2.onCurrentBidItemChange(item.item_required, "item_required", e);
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
                            return _this2.onCurrentBidItemChange(item.item_required, "quantity", e);
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
                                return _this2.onCurrentBidItemChange(item.item_required, "unit_of_measurement", e);
                              },
                              autoComplete: "unit_of_measurement",
                              className: "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6"
                            },
                            item.unit_of_measurement ? React.createElement(
                              "option",
                              { value: item.unit_of_measurement },
                              item.unit_of_measurement
                            ) : "",
                            _this2.state.uom ? _this2.state.uom.map(function (uom) {
                              return React.createElement(
                                "option",
                                { value: uom.name },
                                uom.name
                              );
                            }) : React.createElement(
                              "option",
                              null,
                              "No Units"
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
                              defaultValue: item.vat,
                              onChange: function onChange(e) {
                                return _this2.onCurrentBidItemChange(item.item_required, "vat", e);
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
                              null,
                              "Select Vat"
                            ),
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
                            return _this2.onCurrentBidItemChange(item.item_required, "unit_price", e);
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

      if (this.state.updateBidModal) {
        updateBidModal = React.createElement(
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
                  onClick: this.onCloseUpdateBidBid
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
                          {
                            value: this.state.currentBid.supplier + "-#-" + this.state.currentBid.supplier_name
                          },
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
                            {
                              value: supplier.id + "-#-" + supplier.name
                            },
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
                this.state.currentBid.items.map(function (item, index) {
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
                          defaultValue: item.item_required,
                          onChange: function onChange(e) {
                            return _this2.onCurrentBidItemChange(item.item_required, "item_required", e);
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
                            return _this2.onCurrentBidItemChange(item.item_required, "quantity", e);
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
                              defaultValue: item.unit_of_measurement,
                              onChange: function onChange(e) {
                                return _this2.onCurrentBidItemChange(item.item_required, "unit_of_measurement", e);
                              },
                              autoComplete: "unit_of_measurement",
                              className: "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6"
                            },
                            item.unit_of_measurement ? React.createElement(
                              "option",
                              { value: item.unit_of_measurement },
                              item.unit_of_measurement
                            ) : "",
                            _this2.state.uom ? _this2.state.uom.map(function (uom) {
                              return React.createElement(
                                "option",
                                { value: uom.name },
                                uom.name
                              );
                            }) : React.createElement(
                              "option",
                              null,
                              "No Units"
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
                              defaultValue: item.vat,
                              onChange: function onChange(e) {
                                return _this2.onCurrentBidItemChange(item.item_required, "vat", e);
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
                            return _this2.onCurrentBidItemChange(item.item_required, "unit_price", e);
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

      complianceTable = React.createElement(
        "div",
        { className: "bg-gulf-blue-300 shadow shadow-nepal-300 text-gray-700 rounded px-2 py-2" },
        React.createElement(
          "div",
          { className: "space-y-12 px-5 py-5" },
          React.createElement(
            "div",
            { className: "px-4 sm:px-0 mt-6 border-t border-gray-100 border-gray-900/10" },
            React.createElement(
              "h2",
              { className: "text-base font-semibold leading-6 text-gray-900" },
              "COMPLIANCE TABLE"
            ),
            React.createElement(
              "p",
              { className: "mt-1 max-w-2xl text-sm leading-6 text-gray-500" },
              "Key: Comply/ Not Comply (Y/ N), Not Stated (NS)"
            ),
            React.createElement(
              "div",
              { className: "flex justify-evenly mt-5 bg-gulf-blue-300 px-2 py-2 rounded-md" },
              React.createElement(
                "div",
                { className: "flex-1 w-45" },
                React.createElement(
                  "label",
                  {
                    htmlFor: "site_visit",
                    className: "block text-sm font-medium leading-6 text-gray-900"
                  },
                  "Site visit required?"
                ),
                React.createElement(
                  "div",
                  { className: "mt-2" },
                  React.createElement(
                    "select",
                    {
                      id: "site_visit",
                      name: "showSiteVisit",
                      onChange: function onChange(e) {
                        return _this2.onComplianceItemsChange("showSiteVisit", e);
                      },
                      autoComplete: "site_visit",
                      className: "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6 chzn-select"
                    },
                    React.createElement(
                      "option",
                      { value: "" },
                      "Select Option"
                    ),
                    React.createElement(
                      "option",
                      { value: "yes" },
                      "Yes"
                    ),
                    React.createElement(
                      "option",
                      { value: "no" },
                      "No"
                    )
                  )
                )
              ),
              React.createElement(
                "div",
                { className: "flex-1 w-45" },
                React.createElement(
                  "div",
                  null,
                  React.createElement(
                    "label",
                    {
                      htmlFor: "samples",
                      className: "block text-sm font-medium leading-6 text-gray-900"
                    },
                    "Are Samples Required?"
                  ),
                  React.createElement(
                    "div",
                    { className: "mt-2" },
                    React.createElement(
                      "select",
                      {
                        id: "samples",
                        name: "showSamples",
                        onChange: function onChange(e) {
                          return _this2.onComplianceItemsChange("showSamples", e);
                        },
                        autoComplete: "samples",
                        className: "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6 chzn-select"
                      },
                      React.createElement(
                        "option",
                        { value: "" },
                        "Select Option"
                      ),
                      React.createElement(
                        "option",
                        { value: "yes" },
                        "Yes"
                      ),
                      React.createElement(
                        "option",
                        { value: "no" },
                        "No"
                      )
                    )
                  )
                )
              )
            ),
            React.createElement(
              "div",
              { className: "overflow-auto px-2 py-2 mt-5 rounded-md bg-gulf-blue-300" },
              React.createElement(
                "table",
                { className: "table-auto w-full text-left" },
                React.createElement(
                  "thead",
                  null,
                  React.createElement(
                    "tr",
                    { className: "text-gray-900" },
                    React.createElement(
                      "th",
                      { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                      "Bid No."
                    ),
                    React.createElement(
                      "th",
                      { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                      "Name of Supplier"
                    ),
                    React.createElement(
                      "th",
                      { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                      "Payment ",
                      React.createElement("br", null),
                      "Terms"
                    ),
                    React.createElement(
                      "th",
                      { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                      "Bid ",
                      React.createElement("br", null),
                      "Validity"
                    ),
                    React.createElement(
                      "th",
                      { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                      "Delivery ",
                      React.createElement("br", null),
                      "Period"
                    ),
                    React.createElement(
                      "th",
                      { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                      "Technical ",
                      React.createElement("br", null),
                      "Specifications"
                    ),
                    React.createElement(
                      "th",
                      { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                      "Valid ",
                      React.createElement("br", null),
                      "Tax Clearance"
                    ),
                    React.createElement(
                      "th",
                      { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                      "Registered ",
                      React.createElement("br", null),
                      "with PRAZ?"
                    ),
                    React.createElement(
                      "th",
                      { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                      "Tax ",
                      React.createElement("br", null),
                      "Status"
                    ),
                    this.state.showSiteVisit === "yes" ? React.createElement(
                      "th",
                      {
                        id: "site_visit_header",
                        className: "site-visit-header border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2"
                      },
                      "Site Visit",
                      React.createElement("br", null),
                      "Done?"
                    ) : "",
                    this.state.showSamples === "yes" ? React.createElement(
                      "th",
                      {
                        id: "samples_header",
                        className: "samples-header border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2"
                      },
                      "Samples ",
                      React.createElement("br", null),
                      "Delivered?"
                    ) : "",
                    React.createElement(
                      "th",
                      { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                      "Accept"
                    ),
                    React.createElement(
                      "th",
                      { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                      "Reject"
                    )
                  )
                ),
                React.createElement(
                  "tbody",
                  null,
                  this.state.compliance.map(function (comp, key) {
                    return React.createElement(
                      "tr",
                      null,
                      React.createElement(
                        "td",
                        { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                        key + 1
                      ),
                      React.createElement(
                        "td",
                        { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                        comp.supplier_name
                      ),
                      React.createElement(
                        "td",
                        { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                        React.createElement("input", {
                          name: "payment_terms",
                          checked: comp.payment_terms ? comp.payment_terms : false,
                          onChange: function onChange(e) {
                            return _this2.onComplianceChange(key, e);
                          },
                          id: "payment_terms",
                          type: "checkbox"
                        })
                      ),
                      React.createElement(
                        "td",
                        { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                        React.createElement("input", {
                          name: "bid_validity",
                          checked: comp.bid_validity ? comp.bid_validity : false,
                          onChange: function onChange(e) {
                            return _this2.onComplianceChange(key, e);
                          },
                          id: "bid_validity",
                          type: "checkbox"
                        })
                      ),
                      React.createElement(
                        "td",
                        { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                        React.createElement("input", {
                          name: "delivery_period",
                          checked: comp.delivery_period ? comp.delivery_period : false,
                          onChange: function onChange(e) {
                            return _this2.onComplianceChange(key, e);
                          },
                          id: "delivery_period",
                          type: "checkbox"
                        })
                      ),
                      React.createElement(
                        "td",
                        { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                        React.createElement("input", {
                          name: "technical_specifications",
                          checked: comp.technical_specifications ? comp.technical_specifications : false,
                          onChange: function onChange(e) {
                            return _this2.onComplianceChange(key, e);
                          },
                          id: "technical_specifications",
                          type: "checkbox"
                        })
                      ),
                      React.createElement(
                        "td",
                        { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                        React.createElement("input", {
                          name: "valid_tax_clearance",
                          checked: comp.valid_tax_clearance ? comp.valid_tax_clearance : false,
                          onChange: function onChange(e) {
                            return _this2.onComplianceChange(key, e);
                          },
                          id: "valid_tax_clearance",
                          type: "checkbox"
                        })
                      ),
                      React.createElement(
                        "td",
                        { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                        React.createElement("input", {
                          name: "registered_with_praz",
                          checked: comp.registered_with_praz ? comp.registered_with_praz : false,
                          onChange: function onChange(e) {
                            return _this2.onComplianceChange(key, e);
                          },
                          id: "registered_with_praz",
                          type: "checkbox"
                        })
                      ),
                      React.createElement(
                        "td",
                        { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                        React.createElement("input", {
                          name: "tax_status",
                          checked: comp.tax_status ? comp.tax_status : false,
                          onChange: function onChange(e) {
                            return _this2.onComplianceChange(key, e);
                          },
                          id: "tax_status",
                          type: "checkbox"
                        })
                      ),
                      _this2.state.showSiteVisit === "yes" ? React.createElement(
                        "td",
                        {
                          id: "site_visit_header",
                          className: "site-visit-header border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2"
                        },
                        React.createElement("input", {
                          name: "site_visit",
                          checked: comp.site_visit ? comp.site_visit : false,
                          onChange: function onChange(e) {
                            return _this2.onComplianceChange(key, e);
                          },
                          id: "site_visit",
                          type: "checkbox"
                        })
                      ) : "",
                      _this2.state.showSamples === "yes" ? React.createElement(
                        "td",
                        {
                          id: "samples_header",
                          className: "samples-header border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2"
                        },
                        React.createElement("input", {
                          name: "samples_required",
                          checked: comp.samples_required ? comp.samples_required : false,
                          onChange: function onChange(e) {
                            return _this2.onComplianceChange(key, e);
                          },
                          id: "samples_required",
                          type: "checkbox"
                        })
                      ) : "",
                      React.createElement(
                        "td",
                        { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                        React.createElement("input", {
                          name: "decision",
                          checked: comp.decision ? comp.decision : false,
                          onChange: function onChange(e) {
                            return _this2.onComplianceChange(key, e);
                          },
                          id: "decision",
                          type: "checkbox"
                        })
                      ),
                      React.createElement(
                        "td",
                        { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                        React.createElement("input", {
                          name: "reject",
                          checked: comp.reject ? comp.reject : false,
                          onChange: function onChange(e) {
                            return _this2.onComplianceChange(key, e);
                          },
                          id: "reject",
                          type: "checkbox"
                        })
                      )
                    );
                  })
                )
              )
            ),
            React.createElement(
              "div",
              { className: "px-2 py-2 mt-5 rounded-sm bg-gulf-blue-300" },
              React.createElement(
                "table",
                { className: "table-auto w-full text-left" },
                React.createElement(
                  "thead",
                  null,
                  React.createElement(
                    "tr",
                    { className: "text-gray-900" },
                    React.createElement(
                      "th",
                      { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                      "Supplier"
                    ),
                    React.createElement(
                      "th",
                      { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                      "Remarks"
                    )
                  )
                ),
                React.createElement(
                  "tbody",
                  null,
                  this.state.complianceRemarks.map(function (bid, key) {
                    return React.createElement(
                      "tr",
                      null,
                      React.createElement(
                        "td",
                        { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                        bid.supplier_name
                      ),
                      React.createElement(
                        "td",
                        { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                        React.createElement("input", {
                          name: "remarks",
                          defaultValue: bid.remarks,
                          onChange: function onChange(e) {
                            return _this2.onComplianceRemarksChange(bid.supplier_name, e);
                          },
                          type: "text",
                          className: "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6 chzn-select"
                        })
                      )
                    );
                  })
                )
              )
            )
          )
        ),
        this.state.username === this.state.cs_owner ? React.createElement(
          "div",
          { className: "flex justify-center mt-5 px-3 py-3" },
          React.createElement(
            "div",
            { className: "flex-1 m-2" },
            React.createElement(
              "button",
              {
                style: { width: "100%" },
                onClick: this.onSaveCompliance,
                name: "save_next",
                className: "rounded-md bg-blue-925 hover:bg-blue-550 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
              },
              "SAVE COMPLIANCES"
            )
          )
        ) : ""
      );

      rankingTable = React.createElement(
        "div",
        { className: "bg-gulf-blue-300 shadow shadow-nepal-300 text-gray-700 rounded px-2 py-2" },
        React.createElement(
          "div",
          { className: "space-y-12 px-5 py-5" },
          React.createElement(
            "div",
            { className: "px-4 sm:px-0 mt-6 border-t border-gray-100 border-gray-900/10" },
            React.createElement(
              "h2",
              { className: "text-base font-semibold leading-6 text-gray-900" },
              "RANKING TABLE"
            ),
            React.createElement(
              "div",
              { className: "overflow-auto px-2 py-2 mt-5 rounded-md bg-gulf-blue-300" },
              React.createElement(
                "table",
                { className: "table-auto w-full text-left" },
                React.createElement(
                  "thead",
                  null,
                  React.createElement(
                    "tr",
                    { className: "text-gray-900" },
                    React.createElement(
                      "th",
                      { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                      "ID"
                    ),
                    React.createElement(
                      "th",
                      { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                      "Name of Supplier"
                    ),
                    React.createElement(
                      "th",
                      { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                      "Rank"
                    ),
                    React.createElement(
                      "th",
                      { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                      "Decision"
                    ),
                    React.createElement(
                      "th",
                      { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                      "Remarks"
                    ),
                    React.createElement(
                      "th",
                      { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                      "Total"
                    )
                  )
                ),
                React.createElement(
                  "tbody",
                  null,
                  this.state.rankings.map(function (rank, key) {
                    return React.createElement(
                      "tr",
                      { className: "text-gray-900" },
                      React.createElement(
                        "td",
                        { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                        key + 1
                      ),
                      React.createElement(
                        "td",
                        { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                        rank.supplier_name
                      ),
                      React.createElement(
                        "td",
                        { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                        rank.rank
                      ),
                      React.createElement(
                        "td",
                        { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                        rank.decision
                      ),
                      React.createElement(
                        "td",
                        { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                        rank.remarks
                      ),
                      React.createElement(
                        "td",
                        { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                        rank.total
                      )
                    );
                  })
                )
              )
            )
          )
        )
      );

      committeeTable = React.createElement(
        "div",
        { className: "bg-gulf-blue-300 shadow shadow-nepal-300 text-gray-700 rounded px-2 py-2" },
        React.createElement(
          "div",
          { className: "space-y-12 px-5 py-5" },
          React.createElement(
            "div",
            { className: "px-4 sm:px-0 mt-6 border-t border-gray-100 border-gray-900/10" },
            React.createElement(
              "h2",
              { className: "text-base font-semibold leading-6 text-gray-900" },
              "Committee Members"
            ),
            React.createElement(
              "div",
              { className: "overflow-auto px-2 py-2 mt-5 rounded-md bg-gulf-blue-300" },
              React.createElement(
                "table",
                { className: "table-auto w-full text-left" },
                React.createElement(
                  "tbody",
                  null,
                  React.createElement(
                    "tr",
                    { className: "text-gray-900" },
                    React.createElement(
                      "td",
                      { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                      React.createElement(
                        "div",
                        null,
                        React.createElement(
                          "label",
                          {
                            htmlFor: "memberPosition",
                            className: "block text-sm font-medium leading-6 text-gray-900"
                          },
                          "Member Position"
                        ),
                        React.createElement(
                          "div",
                          { className: "mt-2" },
                          this.state.username === this.state.cs_owner ? React.createElement(
                            "select",
                            {
                              onChange: function onChange(text) {
                                return _this2.onCommitteeChange("memberPosition", text);
                              },
                              id: "memberPosition",
                              name: "memberPosition",
                              autoComplete: "memberPosition",
                              className: "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6 chzn-select"
                            },
                            React.createElement(
                              "option",
                              { value: "" },
                              "Select Option"
                            ),
                            React.createElement(
                              "option",
                              { value: "chairman" },
                              "Chairman"
                            ),
                            React.createElement(
                              "option",
                              { value: "finance" },
                              "Finance"
                            ),
                            React.createElement(
                              "option",
                              { value: "procurement" },
                              "Procurement"
                            ),
                            React.createElement(
                              "option",
                              { value: "user" },
                              "User"
                            ),
                            React.createElement(
                              "option",
                              { value: "other" },
                              "Other"
                            )
                          ) : ""
                        )
                      )
                    ),
                    React.createElement(
                      "td",
                      { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                      React.createElement(
                        "div",
                        null,
                        React.createElement(
                          "label",
                          {
                            htmlFor: "memberUserName",
                            className: "block text-sm font-medium leading-6 text-gray-900"
                          },
                          "Select User"
                        ),
                        React.createElement(
                          "div",
                          { className: "mt-2" },
                          this.state.username === this.state.cs_owner ? React.createElement(
                            "select",
                            {
                              onChange: function onChange(text) {
                                return _this2.onCommitteeChange("memberUserName", text);
                              },
                              id: "memberUserName",
                              name: "memberUserName",
                              autoComplete: "memberUserName",
                              className: "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6 chzn-select"
                            },
                            this.state.users ? this.state.users.map(function (user) {
                              return React.createElement(
                                "option",
                                { value: user.username },
                                user.first_name + " " + user.last_name
                              );
                            }) : ""
                          ) : ""
                        )
                      )
                    ),
                    React.createElement("td", { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" }),
                    React.createElement(
                      "td",
                      { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                      this.state.username === this.state.cs_owner ? React.createElement(
                        "div",
                        { className: "w-30" },
                        React.createElement(
                          "button",
                          {
                            style: { width: "100%" },
                            onClick: this.onAddCommitteeMembers,
                            name: "save_next",
                            className: "rounded-md bg-blue-925 hover:bg-blue-550 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
                          },
                          "ADD MEMBER"
                        )
                      ) : ""
                    )
                  ),
                  this.state.committeeMembers.map(function (member, key) {
                    return React.createElement(
                      "tr",
                      { className: "text-gray-900" },
                      React.createElement(
                        "td",
                        { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                        member.memberPosition
                      ),
                      React.createElement(
                        "td",
                        { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                        member.memberName ? member.memberName : member.memberUserName
                      ),
                      React.createElement(
                        "td",
                        { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                        member.committeeDate
                      ),
                      React.createElement(
                        "td",
                        { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                        member.memberApproval === "Approved" && "APPROVED",
                        member.memberApproval === "Rejected" && "REJECTED",
                        (member.memberApproval === "" || member.memberApproval === null) && React.createElement(
                          "div",
                          { className: "flex justify-content-evenly" },
                          _this2.state.username === _this2.state.cs_owner ? React.createElement(
                            "div",
                            { className: "m-2" },
                            React.createElement(
                              "button",
                              {
                                onClick: function onClick() {
                                  return _this2.onRemoveCommitteeMember(key, member.memberUserName);
                                },
                                name: "save_next",
                                className: "rounded-md bg-blue-925 hover:bg-blue-550 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
                              },
                              "REMOVE"
                            )
                          ) : "",
                          _this2.state.username === member.memberUserName ? React.createElement(
                            "div",
                            { className: "flex justify-content-evenly" },
                            React.createElement(
                              "div",
                              { className: "m-2" },
                              React.createElement(
                                "button",
                                {
                                  onClick: function onClick() {
                                    return _this2.onCommitteeApprove(member.memberUserName, "Approved", "");
                                  },
                                  name: "save_next",
                                  className: "rounded-md bg-blue-925 hover:bg-blue-550 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
                                },
                                "APPROVE"
                              )
                            ),
                            React.createElement(
                              "div",
                              { className: "m-2" },
                              React.createElement(
                                "button",
                                {
                                  onClick: function onClick() {
                                    return _this2.onCommitteeJustificationModal(member.memberUserName);
                                  },
                                  name: "save_next",
                                  className: "rounded-md bg-blue-925 hover:bg-blue-550 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
                                },
                                "REJECT"
                              )
                            )
                          ) : ""
                        )
                      )
                    );
                  })
                )
              )
            )
          )
        )
      );

      approvalsTable = React.createElement(
        "div",
        { className: "bg-gulf-blue-300 shadow shadow-nepal-300 text-gray-700 rounded px-2 py-2" },
        React.createElement(
          "div",
          { className: "space-y-12 px-5 py-5" },
          React.createElement(
            "div",
            { className: "px-4 sm:px-0 mt-6 border-t border-gray-100 border-gray-900/10" },
            React.createElement(
              "h2",
              { className: "text-base font-semibold leading-6 text-gray-900" },
              "Approvals"
            ),
            React.createElement(
              "div",
              { className: "overflow-auto px-2 py-2 mt-5 rounded-md bg-gulf-blue-300" },
              React.createElement(
                "table",
                { className: "table-auto w-full text-left" },
                React.createElement(
                  "tbody",
                  null,
                  React.createElement(
                    "tr",
                    { className: "text-gray-900" },
                    React.createElement(
                      "td",
                      { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                      "FINANCE MANAGER"
                    ),
                    React.createElement(
                      "td",
                      { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                      this.state.fmApproval && this.state.fmApproval.approval === "Approved" && "APPROVED",
                      this.state.fmApproval && this.state.fmApproval.approval === "Rejected" && "REJECTED",
                      this.state.committeeApprovalComplete && React.createElement(
                        "div",
                        { className: "flex justify-content-evenly" },
                        this.state.requester_role === 'check' && Object.keys(this.state.fmApproval).length === 0 ? React.createElement(
                          "div",
                          { className: "flex justify-content-evenly" },
                          React.createElement(
                            "div",
                            { className: "m-2" },
                            React.createElement(
                              "button",
                              {
                                onClick: function onClick() {
                                  return _this2.onApprovalApprove("finance_manager", _this2.state.username, "Approved", "");
                                },
                                name: "save_next",
                                className: "rounded-md bg-blue-925 hover:bg-blue-550 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
                              },
                              "APPROVE"
                            )
                          ),
                          React.createElement(
                            "div",
                            { className: "m-2" },
                            React.createElement(
                              "button",
                              {
                                onClick: function onClick() {
                                  return _this2.onApprovalJustificationModal(_this2.state.username, "finance_manager");
                                },
                                name: "save_next",
                                className: "rounded-md bg-blue-925 hover:bg-blue-550 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
                              },
                              "REJECT"
                            )
                          )
                        ) : ""
                      )
                    ),
                    React.createElement(
                      "td",
                      { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                      this.state.fmApproval && this.state.fmApproval.justification
                    ),
                    React.createElement(
                      "td",
                      { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                      this.state.fmApproval && this.state.fmApproval.approval_date
                    )
                  ),
                  React.createElement(
                    "tr",
                    { className: "text-gray-900" },
                    React.createElement(
                      "td",
                      { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                      "GENERAL MANAGER"
                    ),
                    React.createElement(
                      "td",
                      { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                      this.state.gmApproval && this.state.gmApproval.approval === "Approved" && "APPROVED",
                      this.state.gmApproval && this.state.gmApproval.approval === "Rejected" && "REJECTED",
                      React.createElement(
                        "div",
                        { className: "flex justify-content-evenly" },
                        this.state.fmApproval && this.state.fmApproval.approval === "Approved" && this.state.requester_role === 'approve' && Object.keys(this.state.gmApproval).length === 0 ? React.createElement(
                          "div",
                          { className: "flex justify-content-evenly" },
                          React.createElement(
                            "div",
                            { className: "m-2" },
                            React.createElement(
                              "button",
                              {
                                onClick: function onClick() {
                                  return _this2.onApprovalApprove("general_manager", _this2.state.username, "Approved", "");
                                },
                                name: "save_next",
                                className: "rounded-md bg-blue-925 hover:bg-blue-550 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
                              },
                              "APPROVE"
                            )
                          ),
                          React.createElement(
                            "div",
                            { className: "m-2" },
                            React.createElement(
                              "button",
                              {
                                onClick: function onClick() {
                                  return _this2.onApprovalJustificationModal(_this2.state.username, "general_manager");
                                },
                                name: "save_next",
                                className: "rounded-md bg-blue-925 hover:bg-blue-550 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
                              },
                              "REJECT"
                            )
                          )
                        ) : ""
                      )
                    ),
                    React.createElement(
                      "td",
                      { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                      this.state.gmApproval && this.state.gmApproval.justification
                    ),
                    React.createElement(
                      "td",
                      { className: "border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2" },
                      this.state.gmApproval && this.state.gmApproval.approval_date
                    )
                  )
                )
              )
            )
          )
        )
      );

      var csDetailsView = React.createElement(
        "div",
        { className: "px-4 sm:px-0 mt-6 bg-gulf-blue-300 rounded-md border-t border-gray-100 border-gray-900/10" },
        React.createElement(
          "h2",
          { className: "text-base font-semibold leading-6 text-gray-900" },
          "COMPERATIVE SCHEDULE DETAILS"
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
                    this.state.closing_time_hour ? React.createElement(
                      "option",
                      { value: this.state.closing_time_hour },
                      this.state.closing_time_hour
                    ) : "",
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
                    return _this2.onSelectChange("proc_ref", e);
                  },
                  className: "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6 chzn-select"
                },
                this.state.proc_plan ? React.createElement(
                  "option",
                  { value: this.state.proc_plan.id },
                  this.state.proc_plan.name
                ) : "",
                this.state.proc_plans ? this.state.proc_plans.map(function (plan) {
                  return React.createElement(
                    "option",
                    { value: plan.proc_ref },
                    plan.description
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
                htmlFor: "pr_date",
                className: "block text-sm font-medium leading-6 text-gray-900"
              },
              "Ref Date"
            ),
            React.createElement(
              "div",
              { className: "mt-2" },
              React.createElement("input", {
                name: "ref_date",
                value: this.state.ref_date,
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
          ),
          React.createElement(
            "div",
            { className: "flex-1 w-40 ml-2" },
            React.createElement(
              "label",
              {
                htmlFor: "bid_document",
                className: "block text-sm font-medium leading-6 text-gray-900"
              },
              "Advert Document"
            ),
            React.createElement(
              "div",
              { className: "mt-2" },
              React.createElement(
                "a",
                { href: this.state.advert_url, rel: "noopener noreferrer" },
                "View Advert Document"
              )
            )
          )
        ),
        React.createElement(
          "div",
          { className: "flex justify-evenly mt-5  px-2 py-2 rounded-md" },
          this.state.pr_attachments.length > 0 && this.state.pr_attachments.map(function (attachment, key) {
            return React.createElement(
              "div",
              { className: "flex-1 w-20 ml-1" },
              React.createElement(
                "div",
                { className: "mt-2" },
                React.createElement(
                  "div",
                  { className: "rounded bg-white border border-1 shadow-lg text-center m-2" },
                  React.createElement(
                    "a",
                    { href: attachment.attachment_url,
                      className: "text-center text-blue-600  p-3 sm whitespace-normal max-w-full" },
                    attachment.name
                  )
                )
              )
            );
          })
        ),
        this.state.username === this.state.cs_owner || !this.state.cs_id ? React.createElement(
          "div",
          { className: "flex justify-center mt-10 px-3 py-3" },
          this.state.cs_id ? React.createElement(
            "div",
            { className: "w-30 m-2" },
            React.createElement(
              "button",
              {
                style: { width: "100%" },
                onClick: this.onUpdateSchedule,
                name: "save_next",
                className: "rounded-md bg-blue-925 hover:bg-blue-550 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
              },
              "UPDATE SCHEDULE"
            )
          ) : React.createElement(
            "div",
            { className: "w-30 m-2" },
            React.createElement(
              "button",
              {
                style: { width: "100%" },
                onClick: this.onSaveSchedule,
                name: "save_next",
                className: "rounded-md bg-blue-925 hover:bg-blue-550 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
              },
              "SAVE SCHEDULE"
            )
          )
        ) : ""
      );

      return React.createElement(
        "div",
        null,
        itemsModal,
        bidsModal,
        supplierModal,
        updateBidModal,
        rejectJustification,
        rejectApprovalJustification,
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
              "CS NO: ",
              this.state.cs_id
            ),
            this.state.fetchPR && React.createElement(
              "div",
              { className: "flex justify-evenly items-end mt-5 px-2 py-2" },
              React.createElement(
                "div",
                { className: "flex-1 w-40" },
                React.createElement(
                  "label",
                  {
                    htmlFor: "pr_number",
                    className: "block text-sm font-medium leading-6 text-gray-900"
                  },
                  "Enter PR Number"
                ),
                React.createElement(
                  "div",
                  { className: "mt-2" },
                  React.createElement("input", {
                    name: "pr_number",
                    id: "pr_number",
                    onChange: this.onFetchPrNumberChange,
                    defaultValue: this.state.pr_number,
                    className: "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                  })
                )
              ),
              React.createElement(
                "div",
                { className: "flex-1 ml-2 w-40" },
                React.createElement(
                  "div",
                  { className: "w-30" },
                  React.createElement(
                    "button",
                    {
                      style: { width: "100%" },
                      onClick: function onClick() {
                        return _this2.onFetchPR(_this2.state.pr_number);
                      },
                      name: "save_next",
                      className: "rounded-md bg-blue-925 hover:bg-blue-550 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
                    },
                    "FETCH PR"
                  )
                )
              )
            ),
            csDetailsView
          ),
          this.state.username === this.state.cs_owner ? React.createElement(
            "div",
            { style: { width: "100%" }, className: "flex justify-content-evenly mt-5 px-3 py-3" },
            React.createElement(
              "div",
              { className: "m-2" },
              React.createElement(
                "button",
                {
                  style: { width: "100%" },
                  onClick: this.onAddSuppliersModal,
                  className: "rounded-md bg-nepal-950 hover:bg-nepal-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
                },
                "ADD SUPPLIERS"
              )
            ),
            this.state.bids.length < 1 ? React.createElement(
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
            ) : ""
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
                        bid.bid_count
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
                          href: bid.bid_document_url,
                          target: "_blank",
                          rel: "noopener noreferrer"
                        },
                        "View Document"
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
                          item.item_required
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
              _this2.state.username === _this2.state.cs_owner ? React.createElement(
                "div",
                { className: "flex justify-center mt-5 px-3 py-3" },
                React.createElement(
                  "div",
                  { className: "m-2" },
                  React.createElement(
                    "button",
                    {
                      onClick: function onClick() {
                        return _this2.onUpdateBidModal(bid.bid_count);
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
                        return _this2.onDeleteBidModal(bid.bid_count, bid.supplier_name);
                      },
                      type: "submit",
                      className: "rounded-md bg-red-danger hover:bg-orange-500 text-sm font-semibold px-3 py-2 text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
                    },
                    "DELETE BID"
                  )
                )
              ) : ""
            );
          }),
          this.state.cs_items.length > 0 && this.state.username === this.state.cs_owner ? React.createElement(
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
          ) : "",
          this.state.bids.length > 0 && this.state.compliance.length < 1 && this.state.username === this.state.cs_owner ? React.createElement(
            "div",
            { className: "m-2" },
            React.createElement(
              "button",
              {
                style: { width: "100%" },
                onClick: this.onAddComplianceTable,
                className: "rounded-md bg-nepal-950 hover:bg-nepal-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
              },
              "ADD COMPLIANCES"
            )
          ) : "",
          this.state.compliance.length > 0 ? complianceTable : "",
          this.state.compliance.length > 0 && this.state.username === this.state.cs_owner ? React.createElement(
            "div",
            { className: "m-2" },
            React.createElement(
              "button",
              {
                style: { width: "100%" },
                onClick: this.onCloseCS,
                className: "rounded-md bg-nepal-950 hover:bg-nepal-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
              },
              "RANK BIDS"
            )
          ) : "",
          this.state.rankings.length > 0 ? rankingTable : "",
          this.state.rankings.length > 0 ? committeeTable : "",
          this.state.committeeMembers.length > 0 && this.state.username === this.state.cs_owner ? React.createElement(
            "div",
            { className: "m-2" },
            React.createElement(
              "button",
              {
                style: { width: "100%" },
                onClick: this.onSubmitCommitee,
                className: "rounded-md bg-nepal-950 hover:bg-nepal-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
              },
              "SUBMIT COMMITTEE"
            )
          ) : "",
          this.state.committeeMembers.length > 2 ? approvalsTable : ""
        )
      );
    }
  }]);

  return CreateCS;
}(React.Component);

var domContainer = document.querySelector("#create_comparative_schedule");
var username = domContainer.getAttribute("data-username");
var prid = domContainer.getAttribute("data-prid");
var csid = domContainer.getAttribute("data-csid");
ReactDOM.render(e(CreateCS, { username: username, prid: prid, csid: csid }), domContainer);