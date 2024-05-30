"use strict";

const e = React.createElement;
const domContainer = document.querySelector("#create_comparative_schedule");
const url = domContainer.getAttribute("data-baseurl");
// const BASE_URL = "http://localhost:8000";
const BASE_URL = url;

class CreateCS extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      requester_role: "",
      cs_id: "",
      cs_owner: "",
      creator: "",
      created_at: "",
      committeeApprovalComplete: false,
      plan_ref: "",
      proc_ref: "",
      currency: null,
      currencies: [],
      proc_plan: null,
      scope_of_work: "",
      pr_number: "",
      pr_attachments: [],
      quantity: "",
      pr_date: "",
      closing_date: "",
      closing_time: "",
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
      showSamples: "no",
      showSiteVisit: "no",

      rankingTable: false,
      rankings: [],

      committeeTable: false,
      committeeMembers: [],
      committeeJustificationModal: false,
      member: {
        memberName: "",
        memberUserName: "",
        memberPosition: "",
        memberApproval: "",
      },
      gmApproval: null,
      fmApproval: null,
      approvalsComplete: false,
      approvalsJustificationModal: false,
      users: [],
      currentApprover: {
        username: "",
        justification: "",
        role: "",
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
        supplier_address: "",
      },
    };
    this.getCreateData = this.getCreateData.bind(this);
    this.onAddBid = this.onAddBid.bind(this);
    this.onUpdateBidModal = this.onUpdateBidModal.bind(this);
    this.onAddItemsModal = this.onAddItemsModal.bind(this);
    this.onCommitteeChange = this.onCommitteeChange.bind(this);
    this.onGetFileObjectUrl = this.onGetFileObjectUrl.bind(this);
    this.onComplianceItemsChange = this.onComplianceItemsChange.bind(this);
    this.onComplianceRemarksChange = this.onComplianceRemarksChange.bind(this);
    this.onCommitteeApprove = this.onCommitteeApprove.bind(this);
    this.onCommitteeJustificationChange =
      this.onCommitteeJustificationChange.bind(this);
    this.onCommitteeJustificationModal =
      this.onCommitteeJustificationModal.bind(this);
    this.onApprovalJustificationModal = this.onApprovalJustificationModal.bind(this);
    this.onApprovalJustificationChange = this.onApprovalJustificationChange.bind(this);
    this.onSupplierChange = this.onSupplierChange.bind(this);
  }

  componentDidMount() {
    console.log("props: ", this.props);
    if (this.props.csid !== "") {
      this.setState({
        username: this.props.username,
        cs_id: this.props.csid,
      });
      this.getCSData(this.props.csid);
    } else if(this.props.prid !== "") {
      this.setState({
        username: this.props.username,
        pr_number: this.props.prid,
      });
      this.getCreateData(this.props.prid);
    } else {
      this.setState({
        username: this.props.username,
        fetchPR: true,
      });
    }
  }

  onGetFileObjectUrl = (fileData) => {
    try{

      if (typeof fileData === "string") {
        const decodedFileData = atob(fileData);
        const uint8Array = new Uint8Array(decodedFileData.length);
        for (let i = 0; i < decodedFileData.length; i++) {
          uint8Array[i] = decodedFileData.charCodeAt(i);
        }
  
        const file = new Blob([uint8Array], { type: "application/pdf" });
        console.log("file: ", file);
  
        return URL.createObjectURL(file);
      } else {
        console.log("fileData: ", fileData);
        return URL.createObjectURL(fileData);
      }

    } catch(err) {
      console.log("error: ", error);
    }
  };

  getCSData = (cs_id) => {
    fetch(`${BASE_URL}/comperative_schedule/cs_data/${cs_id}`)
      .then((response) => response.json())
      .then((data_) => {
        let data = JSON.parse(data_);
        console.log("cs data: ", data, typeof data);
        let requester_role = data.requester_role ? data.requester_role : "";
        let creator = data.creator ? data.creator : "";
        let created_at = data.created_at ? data.created_at : "";
        let bids_object = data.bids ? data.bids : [];
        let bids = [];
        if(bids_object.length !== 0) {
          bids = Object.keys(bids_object).map((key) => {
            let new_obj = bids_object[key];
            return {
              ...new_obj,
              bid_document_url: this.onGetFileObjectUrl(new_obj.bid_document),
            };
          });
        }
        let sorted_bids = bids.sort((a, b) => a.bid_no - b.bid_no);

        let compliance = data.compliance ? data.compliance : [];
        let complianceRemarks = data.complianceRemarks
          ? data.complianceRemarks
          : [];
        let rankings = data.rankings ? data.rankings : [];
        let committee = data.committee ? data.committee : [];
        let gm_approval = data.gm_approval ? data.gm_approval : null;
        let fm_approval = data.fm_approval ? data.fm_approval : null;
        let pr_date = data.pr_date ? data.pr_date : "";
        let proc_plan = data.proc_plan ? data.proc_plan : "";
        let scope_of_work = data.scope_of_work ? data.scope_of_work : "";
        let pr_number = data.pr_number ? data.pr_number : "";
        let quantity = data.quantity ? data.quantity : "";
        let closing_date = data.closing_date ? data.closing_date : "";
        let ref_date = data.ref_date ? data.ref_date : "";
        let closing_time = data.closing_time ? data.closing_time : "";
        let tender_adjudication_committee_date = data.tac_date
          ? data.tac_date
          : "";
        let cs_opened = data.cs_opened ? data.cs_opened : false;

        let proc_plans = data.proc_plans ? data.proc_plans : [];
        let uom = data.uom ? data.uom : [];
        let suppliers = data.suppliers ? data.suppliers : [];
        let pr_items = data.pr_items ? data.pr_items : [];
        let pr_attachments = data.pr_attachments ? data.pr_attachments : [];
        let cs_items = data.cs_items ? data.cs_items : [];
        let users = data.users ? data.users : [];
        // Sort users by full name (first_name + " " + last_name)
        users.sort((user1, user2) => {
          const fullName1 = user1.first_name + " " + user1.last_name;
          const fullName2 = user2.first_name + " " + user2.last_name;
          return fullName1.localeCompare(fullName2);
        });
        let cs_owner = data.cs_owner ? data.cs_owner : "";
        let currencies = data.currencies ? data.currencies : [];
        let currency = data.currency ? data.currency : "";

        let advert_url = this.onGetFileObjectUrl(data.advert);
        let pr_at_list = [];
        if(pr_attachments.length > 0) {
          pr_at_list = pr_attachments.map((pr_attachment) => {
            return {
              ...pr_attachment,
              attachment_url: this.onGetFileObjectUrl(pr_attachment.file),
            };
          });
        }

        let committeeApprovalComplete = committee.filter(
          (member) => (member.memberApproval === "" || member.memberApproval === null || member.memberApproval === undefined || member.memberApproval === "Rejected")
        ).length === 0;
        
        console.log("gm_approval: ", gm_approval, fm_approval, gm_approval.approval, fm_approval.approval);
        let approvalsComplete = gm_approval.approval !== "" && fm_approval.approval !== "" && gm_approval.approval !== undefined && fm_approval.approval !== undefined;

        this.setState({
          ...this.state,
          requester_role: requester_role,
          creator: creator,
          created_at: created_at,
          cs_owner: cs_owner,
          committeeApprovalComplete: committeeApprovalComplete,
          approvalsComplete: approvalsComplete,
          proc_plans: proc_plans,
          currencies: currencies,
          currency: currency,
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
          closing_time: closing_time,
          ref_date: ref_date,
          tender_adjudication_committee_date:
            tender_adjudication_committee_date,
          advert: advert,
          advert_url: advert_url,
          bids: sorted_bids,
          cs_items: cs_items,
          compliance: compliance,
          complianceRemarks: complianceRemarks,
          rankings: rankings,
          committeeMembers: committee,
          gmApproval: gm_approval,
          fmApproval: fm_approval,
          pr_items: pr_items,
          pr_attachments: pr_at_list,
        });
      })
      .catch((error) => console.log("error: ", error))
  };

  getCreateData = (pr_id) => {
    console.log("cs pr_id: ", pr_id);

    fetch(`${BASE_URL}/comperative_schedule/create_data/${pr_id}`)
      .then((response) => response.json())
      .then((data) => {
        console.log("data: ", data);
        let scope_of_work = data.scope_of_work ? data.scope_of_work : "";
        let proc_ref = data.proc_ref ? data.proc_ref : "";
        let plans = data.proc_plans ? data.proc_plans : [];
        let uom = data.uom ? data.uom : [];
        let suppliers = data.suppliers ? data.suppliers : [];
        let pr_items = data.pr_items ? data.pr_items : [];
        let pr_attachments = data.pr_attachments ? data.pr_attachments : [];
        let pr_id = data.pr_id ? data.pr_id : "";
        let pr_date = data.pr_date ? data.pr_date : "";
        let users = data.users ? data.users : [];
        let currencies = data.currencies ? data.currencies : [];
        // Sort users by full name (first_name + " " + last_name)
        users.sort((user1, user2) => {
          const fullName1 = user1.first_name + " " + user1.last_name;
          const fullName2 = user2.first_name + " " + user2.last_name;
          return fullName1.localeCompare(fullName2);
        });
        let pr_at_list = [];
        if(pr_items.length === 0) {
          pr_at_list = pr_attachments.map((pr_attachment) => {
            return {
              ...pr_attachment,
              attachment_url: this.onGetFileObjectUrl(pr_attachment.file),
            };
          });
        }
        this.setState({
          scope_of_work: scope_of_work,
          currencies: currencies,
          proc_ref: proc_ref,
          proc_plans: plans,
          uom: uom,
          suppliers: suppliers,
          pr_items: pr_items,
          pr_attachments: pr_at_list,
          pr_number: pr_id,
          pr_date: pr_date,
          users: users,
        });
      })
      .catch((error) => console.log("error: ", error))
  };

  onFetchPR = (pr_id) => {
    console.log("cs pr_id: ", pr_id);

    fetch(`${BASE_URL}/comperative_schedule/create_data/${pr_id}`)
      .then((response) => response.json())
      .then((data) => {
        console.log("data: ", data);
        if(data && data.success) {
          let scope_of_work = data.scope_of_work ? data.scope_of_work : "";
          let proc_ref = data.proc_ref ? data.proc_ref : "";
          let proc_plan = data.proc_plan ? data.proc_plan : null;
          let plans = data.proc_plans ? data.proc_plans : [];
          let currencies = data.currencies ? data.currencies : [];
          let uom = data.uom ? data.uom : "";
          let suppliers = data.suppliers ? data.suppliers : [];
          let pr_items = data.pr_items ? data.pr_items : [];
          let pr_attachments = data.pr_attachments ? data.pr_attachments : [];
          let pr_id = data.pr_id ? data.pr_id : "";
          let pr_date = data.pr_date ? data.pr_date : "";
          let users = data.users ? data.users : [];
          let pr_at_list = [];
          if(pr_attachments.length > 0){
            pr_at_list = pr_attachments.map((pr_attachment) => {
              return {
                ...pr_attachment,
                attachment_url: this.onGetFileObjectUrl(pr_attachment.file),
              };
            });
          }
          this.setState({
            scope_of_work: scope_of_work,
            proc_ref: proc_ref,
            proc_plan: {
              description: proc_plan.name,
              id: proc_plan.id,
              proc_ref: proc_plan.proc_ref,
            },
            proc_plans: plans,
            currencies: currencies,
            uom: uom,
            suppliers: suppliers,
            pr_items: pr_items,
            pr_attachments: pr_at_list,
            pr_number: pr_id,
            pr_date: pr_date,
            users: users,
            fetchPR: false,
          });
      
          alert("PR fetched successfully");
        } else {
          alert("PR Number not found");
        }
      })
      .catch((error) => console.log("error: ", error))
  };

  onFetchPrNumberChange = (event) => {
    let { name, value } = event.target;
    this.setState({
      ...this.state,
      pr_number: value,
    });
  }

  onCommitteeChange = (name_, event) => {
    let { name, value } = event.target;
    console.log("name: ", name_, "value: ", value);
    let member = this.state.member;
    if (name_ === "memberUserName") {
      let user = this.state.users.find((user) => user.username === value);
      member.memberName = user.first_name + " " + user.last_name;
      member[name_] = value;
    } else{
      member[name_] = value;
    }
    this.setState({
      ...this.state,
      member: member,
    });
  };

  onAddCommitteeMembers = () => {
    let members = this.state.committeeMembers;
    let member_ = this.state.member;
    if (member_.memberUserName === "" || member_.memberPosition === "") {
      alert("Please select a user");
    }
    // check if memberUserName exists
    let member = members.find(
      (_member) => _member.memberUserName === this.state.member.memberUserName
    );
    // check if memberUserName is the one creating
    let currentUserFlag =
      this.state.member.memberUserName === this.state.username;
    let positionFlag = members.find(
      (_member) => _member.memberPosition === this.state.member.memberPosition
    );
    if (member) {
      alert("Committee Member already added.");
    } else if (currentUserFlag) {
      alert("You cannot add yourself. Please choose another user.");
    } else if(positionFlag){
      alert(this.state.member.memberPosition+", already exists, please add a different one.")
    } else {
      members.push(this.state.member);
      this.setState({
        ...this.state,
        committeeMembers: members,
        member: {
          memberUserName: "",
          memberName: "",
          memberPosition: "",
          memberApproval: "",
        },
      });
    }
  };

  onRemoveCommitteeMember = (index, username) => {
    let members = this.state.committeeMembers.filter(
      (member, _index) => _index !== index
    );
    if (members.length < this.state.committeeMembers.length) {
      this.setState({
        ...this.state,
        committeeMembers: members,
      });
    }
    this.deleteCommitteeMember(username);
  };

  deleteCommitteeMember = (username) => {
    let form_data = new FormData();
    form_data.append("cs_id", this.state.cs_id);
    form_data.append("username", username);
    form_data.append("csrfmiddlewaretoken", this.getCookie("csrftoken"));

    fetch(`${BASE_URL}/comperative_schedule/delete_committee_member`, {
      method: "POST",
      headers: {
        "X-CSRFToken": this.getCookie("csrftoken"),
      },
      body: form_data,
    })
      .then((response) => response.json())
      .then((data) => {
        console.log("data: ", data);
        if (data.success) {
          alert("Committee member deleted successfully");
        } else {
          alert("Error deleting Committee member");
        }
      });
  };

  onCommitteeJustificationModal = (username) => {
    this.setState({
      ...this.state,
      currentApprover: {
        username: username,
        justification: "",
      },
      committeeJustificationModal: !this.state.committeeJustificationModal,
    });
  };

  onCommitteeJustificationChange = (name_, event) => {
    console.log("event: ", event);
    let { value } = event.target;
    let currentApprover = this.state.currentApprover;
    currentApprover[name_] = value;
    this.setState({
      ...this.state,
      currentApprover: currentApprover,
    });
  };

  onCommitteeApprove = (username, approval, justification) => {
    let form_data = new FormData();
    console.log("approval: ", approval, justification);
    if (approval === "Rejected" && justification === "") {
      alert("Please enter justification");
      return;
    }
    form_data.append("cs_id", this.state.cs_id);
    form_data.append("username", username);
    form_data.append("approval", approval);
    form_data.append("justification", justification);
    form_data.append("csrfmiddlewaretoken", this.getCookie("csrftoken"));

    fetch(`${BASE_URL}/comperative_schedule/committee_approve`, {
      method: "POST",
      headers: {
        "X-CSRFToken": this.getCookie("csrftoken"),
      },
      body: form_data,
    })
      .then((response) => response.json())
      .then((data) => {
        console.log("data: ", data);
        if (data.success) {
          let committeeDate = data.committee_date;
          let committeeApproval = data.committee_approval;
          let memberName = data.committee_fullname;
          let members = [];
          if(this.state.committeeMembers && this.state.committeeMembers.length > 0) {
            members = this.state.committeeMembers.map((member) => {
              if (member.memberUserName === username) {
                member.committee_date = committeeDate;
                member.member_approval = committeeApproval;
              }
              return member;
            });
          }
          this.setState({
            ...this.state,
            committeeMembers: members,
          });
          console.log("committeeApproval: ", committeeApproval, justification);
          alert("Approval Done!!");
          // reload page
          window.location.reload();
        //   if (committeeApproval === "Approved") {
        //     alert("Committee approved successfully");
        //     // reload page
        //     // window.location.reload();
        //   } else if(committeeApproval === "Rejected") {
        //     alert("Committee rejected successfully");
        //     // window.location.reload();
        //   } else {
        //     alert("Error approving Committee");
        //     // window.location.reload();
        //   }
        } else {
          alert("Error approving Committee");
        }
      }).catch((err) => console.log("onCommitteeApprove error: ", err));
  };

  onSubmitCommitee = () => {
    let form_data = new FormData();
    form_data.append("cs_id", this.state.cs_id);
    form_data.append(
      "committee",
      JSON.stringify({
        committee: this.state.committeeMembers,
      })
    );
    form_data.append("csrfmiddlewaretoken", this.getCookie("csrftoken"));

    fetch(`${BASE_URL}/comperative_schedule/save_committee`, {
      method: "POST",
      headers: {
        "X-CSRFToken": this.getCookie("csrftoken"),
      },
      body: form_data,
    })
      .then((response) => response.json())
      .then((data) => {
        console.log("data: ", data);
        if (data.success) {
          alert("Committee saved successfully");
        } else {
          alert("Error saving Committee");
        }
      });
  };

  onApprovalApprove = (role, username, approval, justification) => {
    console.log("approval: ", approval, justification);
    if(approval === "Rejected" && justification === "") {
      alert("Please enter justification");
      return;
    }
    let form_data = new FormData();
    form_data.append("cs_id", this.state.cs_id);
    form_data.append("role", role);
    form_data.append("username", username);
    form_data.append("approval", approval);
    form_data.append("justification", justification);
    form_data.append("csrfmiddlewaretoken", this.getCookie("csrftoken"));

    fetch(`${BASE_URL}/comperative_schedule/approval_approve`, {
      method: "POST",
      headers: {
        "X-CSRFToken": this.getCookie("csrftoken"),
      },
      body: form_data,
    })
      .then((response) => response.json())
      .then((data) => {
        console.log("data: ", data);
        if (data.success) {
          let role = data.role;
          let approval = data.approval;
          if (role === "finance_manager") {
            let fm_approval = data.fm_approval ? data.fm_approval : null;
            this.setState({
              fmApproval: fm_approval,
            });
          } else if(role === "general_manager") {
            let gm_approval = data.gm_approval ? data.gm_approval : null;
            this.setState({
              gmApproval: gm_approval,
            });
          }
          if (approval === "Approved") {
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

  onApprovalJustificationModal = (username, role) => {
    this.setState({
      ...this.state,
      currentApprover: {
        username: username,
        role: role,
        justification: "",
      },
      approvalsJustificationModal: !this.state.approvalsJustificationModal,
    });
  };

  onSaveSupplier = () => {
    let form_data = new FormData();
    form_data.append("supplier_name", this.state.newSupplier.supplier_name);
    form_data.append("csrfmiddlewaretoken", this.getCookie("csrftoken"));

    fetch(`${BASE_URL}/comperative_schedule/save_supplier`, {
      method: "POST",
      headers: {
        "X-CSRFToken": this.getCookie("csrftoken"),
      },
      body: form_data,
    })
      .then((response) => response.json())
      .then((data) => {
        console.log("data: ", data);
        if (data.success) {
          alert("Supplier saved successfully");
          this.setState({
            ...this.state,
            onAddSupplier: false,
            newSupplier: {
              supplier_name: "",
              supplier_contact: "",
              supplier_email: "",
              supplier_address: "",
            },
          });
        } else {
          alert("Error saving Supplier");
        }
      });
  };

  onApprovalJustificationChange = (name_, event) => {
    console.log("event: ", event);
    let { value } = event.target;
    let currentApprover = this.state.currentApprover;
    currentApprover[name_] = value;
    this.setState({
      ...this.state,
      currentApprover: currentApprover,
    });
  };

  onAddCSItem = (item_id, ordered) => {
    // check is item already added
    let item = this.state.cs_items.find((item) => item.id === item_id);
    console.log("item: ", item);
    if (item) {
      // update item selected to false
      item.ordered = false;
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
      item.ordered = true;
      item.item_name = item.item_required;
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
    }
  };

  onSubmitCSItems = () => {
    if (this.state.cs_items.length === 0) {
      alert("Please add items to the Comparative Schedule");
      return;
    }
    let form_data = new FormData();
    form_data.append("cs_id", this.state.cs_id);
    form_data.append("pr_id", this.state.pr_number);
    form_data.append(
      "json_data",
      JSON.stringify({
        cs_items: this.state.cs_items,
      })
    );
    form_data.append("csrfmiddlewaretoken", this.getCookie("csrftoken"));

    fetch(`${BASE_URL}/comperative_schedule/update_pritem_ordered`, {
      method: "POST",
      headers: {
        "X-CSRFToken": this.getCookie("csrftoken"),
      },
      body: form_data,
    })
      .then((response) => response.json())
      .then((data) => {
        console.log("data: ", data);
        if (data.success) {
          alert("Items saved successfully");
        } else {
          alert("Error saving Items");
        }
      });
    this.setState({
      ...this.state,
      addItemsModal: false,
    });
  };

  onAddSuppliersModal = () => {
    this.setState({
      ...this.state,
      onAddSupplier: !this.state.onAddSupplier,
    });
  };

  onSupplierChange = (name_, event) => {
    let { name, value } = event.target;

    this.setState({
      ...this.state,
      newSupplier: {
        ...this.state.newSupplier,
        [name]: value,
      },
    });
  };

  onAddBidModal = () => {
    let bid_count = this.state.bids.length + 1;
    let items = this.state.cs_items
    console.log("items: ", items)
    this.setState({
      ...this.state,
      addBidModal: !this.state.addBidModal,
      bid_count: bid_count,
      currentBid: {
        bid_count: bid_count,
        items: items
      },
    });
  };

  onUpdateBidModal = (bid_count) => {
    let bid = this.state.bids.find((bid) => bid.bid_count === bid_count);
    this.setState({
      ...this.state,
      updateBidModal: !this.state.updateBidModal,
      currentBid: bid,
    });
  };

  onCloseCurrentBid = () => {
    let bid_count = this.state.bids.length - 1;
    this.setState({
      ...this.state,
      currentBid: {},
      addBidModal: false,
      updateBidModal: false,
      bid_count: bid_count,
    });
  };

  onCloseUpdateBidBid = () => {
    this.setState({
      ...this.state,
      currentBid: {},
      updateBidModal: false,
    });
  };

  onCurrentBidChange = (name_, event) => {
    let currentBid = this.state.currentBid;
    if (name_ === "bid_document") {
      let bid_file = event.target.files[0];
      let bid_document_url = this.onGetFileObjectUrl(event.target.files[0]);
      currentBid[name_] = bid_file;
      currentBid.bid_document_url = bid_document_url;
    } else if (name_ === "supplier") {
      let { name, value } = event.target;
      console.log("value: ", value);
      let id_name = value ? value.split("-#-") : [];
      currentBid[name_] = id_name.length > 0 ? id_name[0] : "";
      currentBid["supplier_name"] = id_name.length >= 1 ? id_name[1] : "";
    } else {
      let { name, value } = event.target;
      currentBid[name_] = value;
    }
    this.setState({
      ...this.state,
      currentBid: currentBid,
    });
  };

  onCurrentBidItemChange = (description, name_, event, bid_no) => {

    let { name, value } = event.target
    console.log("name: ", name, " value: ", value, " bid no: ", bid_no)
    console.log("description: ", description);

    let items = this.state.currentBid.items

    let new_items = items? items.map((it, index) => {
      if(it.item_required === description){
        return {
          ...it,
          [name_]: value
        }
      } else {
        return it
      }
    }): []

    this.setState({
      ...this.state,
      currentBid: {
        ...this.state.currentBid,
        items: new_items
      }
    })


  };

  onCurrentBidSave = () => {
    let currentBid = this.state.currentBid;
    if (
      currentBid.supplier_name === "" ||
      currentBid.supplier_name === undefined
    ) {
      alert("Please select a supplier");
      return;
    } else if (
      currentBid.bid_date === "" ||
      currentBid.bid_date === undefined
    ) {
      alert("Please select a bid date");
      return;
    } else if (
      currentBid.bid_document === "" ||
      currentBid.bid_document === undefined
    ) {
      alert("Please select a bid document");
      return;
    } else {
      
      // check if current bid already exists
      if (currentBid.items) {
        console.log("state bids found: ", this.state.bids);
        let bid = this.state.bids.find(
          (bid) => bid && bid.bid_count === currentBid.bid_count
        );
        console.log("bid found: ", bid);
        if (bid) {
          // update bid
          console.log("currentBid 1: ", currentBid);
          let items = [];
          if(this.state.currentBid.items && this.state.currentBid.items.length > 0){
            items = currentBid.items.map((item) => {
              item.total_price = item.quantity * item.unit_price;
              return item;
            });
          }

          let missingFields = items.filter(
            (item) =>
              item.quantity === "" || item.quantity === undefined ||
              item.unit_price === "" || item.unit_price === undefined ||
              item.vat === "" || item.vat === undefined ||
              item.unit_of_measurement === "" || item.unit_of_measurement === undefined ||
              item.total_price === "" || item.total_price === undefined
          );

          if (missingFields.length > 0) {
            alert("Please fill in all required fields");
            return;
          }
          currentBid.items = items;
          console.log("currentBid: ", currentBid);
          let bids = [];
          if(this.state.bids && this.state.bids.length > 0) {
            bids = this.state.bids.map((bid) => {
              if (bid.bid_count === currentBid.bid_count) {
                return {
                  ...currentBid,
                  bid_document: currentBid.bid_document ? currentBid.bid_document : bid.bid_document,
                };
              }
              return bid;
            });
            bids.sort((a, b) => a.bid_count - b.bid_count);
          }
          this.onSaveBid(currentBid, bids, undefined, undefined);
        } else {
          // calculate total price for each item
          let items = [];
          if(currentBid.items && currentBid.items.length > 0){
            items = currentBid.items.map((item) => {
              item.total_price = item.quantity * item.unit_price;
              return item;
            });
          }

          let missingFields = items.filter(
            (item) =>
              item.quantity === "" || item.quantity === undefined ||
              item.unit_price === "" || item.unit_price === undefined ||
              item.vat === "" || item.vat === undefined ||
              item.unit_of_measurement === "" || item.unit_of_measurement === undefined ||
              item.total_price === "" || item.total_price === undefined
          );

          if (missingFields.length > 0) {
            alert("Please fill in all required fields");
            return;
          }
          // update current bid items
          currentBid.items = items;

          let bids = this.state.bids;
          console.log("currentBid: ", currentBid);
          bids.push(currentBid);
          bids.sort((a, b) => a.bid_count - b.bid_count);

          // check if compliance for supplier exists
          let compliances = this.state.compliance;
          let compliance = compliances.find(
            (compliance) => compliance.supplier_name === currentBid.supplier_name
          );
          let compliance_ = {};
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
              remarks: "",
            };
            compliances.push(compliance_);
          }
  
          let complianceRemarks = this.state.complianceRemarks;
          let complianceRemark = complianceRemarks.find(
            (complianceRemark) =>
              complianceRemark.supplier_name === currentBid.supplier_name
          );
  
          if (!complianceRemark) {
            let complianceRemark_ = {
              bid_count: currentBid.bid_count,
              supplier: currentBid.supplier,
              supplier_name: currentBid.supplier_name,
              remarks: "",
            };
            complianceRemarks.push(complianceRemark_);
          }
          this.onSaveBid(currentBid, bids, compliance, complianceRemarks);

        }
      } else {
        alert("Please add items to the bid");
      }
    }
  };

  onSaveBid = (currentBid, bids, compliances, complianceRemarks) => {
    let form_data = new FormData();

    // add enctype to form data
    form_data.enctype = "multipart/form-data";
    form_data.append("cs_id", this.state.cs_id);
    form_data.append("bid_no", currentBid.bid_count);
    form_data.append("supplier_id", currentBid.supplier);
    form_data.append("supplier_name", currentBid.supplier_name);
    form_data.append("bid_date", currentBid.bid_date);
    form_data.append(
      "json_data",
      JSON.stringify({
        bid_items: currentBid.items,
      })
    );
    form_data.append("bid_document", currentBid.bid_document);
    form_data.append("csrfmiddlewaretoken", this.getCookie("csrftoken"));

    fetch(`${BASE_URL}/comperative_schedule/save_bid`, {
      method: "POST",
      headers: {
        "X-CSRFToken": this.getCookie("csrftoken"),
      },
      body: form_data,
    })
      .then((response) => response.json())
      .then((data) => {
        console.log("data: ", data);
        if (data.success) {
  
          this.setState({
            ...this.state,
            bids: bids ? bids : this.state.bids,
            compliance: compliances ? compliances : this.state.compliance,
            complianceRemarks: complianceRemarks ? complianceRemarks : this.state.complianceRemarks
          });

          alert("Bid saved successfully");
        } else {
          alert("Error saving Bid");
        }
      })
      .catch(err => console.log("onSaveBid: ", err));
      this.setState({
        ...this.state,
        currentBid: null,
        addBidModal: false,
        updateBidModal: false,
      });
  };

  onSaveSchedule = () => {

    if(!this.state.currency || !this.state.proc_ref || !this.state.scope_of_work || !this.state.pr_number || !this.state.pr_date || !this.state.closing_date || !this.state.ref_date || !this.state.closing_time || !this.state.date_tender_opened || !this.state.tender_adjudication_committee_date) {
      alert("Please fill in all required fields");
      return;
    }
    if(this.state.pr_items.length === 0) {
      alert("Cannot create a Comparative Schedule without Purchase Request items.");
      return;
    }
    let form_data = new FormData();
    // add enctype to form data
    form_data.enctype = "multipart/form-data";
    form_data.append("proc_ref", this.state.proc_ref);
    form_data.append("scope_of_work", this.state.scope_of_work);
    form_data.append("currency", this.state.currency);
    form_data.append("pr_number", this.state.pr_number);
    form_data.append("quantity", this.state.quantity);
    form_data.append("pr_date", this.state.pr_date);
    form_data.append("closing_date", this.state.closing_date);
    form_data.append("ref_date", this.state.ref_date);
    form_data.append("closing_time", this.state.closing_time);
    form_data.append("date_tender_opened", this.state.date_tender_opened);
    form_data.append("username", this.state.username);
    form_data.append(
      "tender_adjudication_committee_date",
      this.state.tender_adjudication_committee_date
    );
    form_data.append("advert", this.state.advert);
    form_data.append("csrfmiddlewaretoken", this.getCookie("csrftoken"));

    fetch(`${BASE_URL}/comperative_schedule/save`, {
      method: "POST",
      headers: {
        "X-CSRFToken": this.getCookie("csrftoken"),
      },
      body: form_data,
    })
      .then((response) => response.json())
      .then((data) => {
        console.log("comperative schedule saved data: ", data);
        if (data.success) {
          alert("Comparative Schedule saved successfully" + " " + data.cs_id);
          this.setState({
            ...this.state,
            cs_id: data.cs_id,
            cs_owner: data.cs_owner,
          });
        } else {
          alert("Error saving Comparative Schedule");
        }
      }).catch(err => console.log("onSaveSchedule: ", err));
  };

  onUpdateSchedule = () => {
    if(this.state.cs_id === "" || this.state.cs_id === undefined) {
      alert("Please save the Comparative Schedule first");
      return;
    }
    if(!this.state.currency || !this.state.proc_ref || !this.state.scope_of_work || !this.state.pr_number || !this.state.pr_date || !this.state.closing_date || !this.state.ref_date || !this.state.closing_time || !this.state.date_tender_opened || !this.state.tender_adjudication_committee_date) {
      alert("Please fill in all required fields");
      return;
    }
    let form_data = new FormData();
    // add enctype to form data
    form_data.enctype = "multipart/form-data";
    form_data.append("cs_id", this.state.cs_id);
    form_data.append("proc_ref", this.state.proc_ref);
    form_data.append("scope_of_work", this.state.scope_of_work);
    form_data.append("currency", this.state.currency);
    form_data.append("pr_number", this.state.pr_number);
    form_data.append("quantity", this.state.quantity);
    form_data.append("pr_date", this.state.pr_date);
    form_data.append("closing_date", this.state.closing_date);
    form_data.append("ref_date", this.state.ref_date);
    form_data.append("closing_time", this.state.closing_time);
    form_data.append("date_tender_opened", this.state.date_tender_opened);
    form_data.append("username", this.state.username);
    form_data.append(
      "tender_adjudication_committee_date",
      this.state.tender_adjudication_committee_date
    );
    form_data.append("advert", this.state.advert);
    form_data.append("csrfmiddlewaretoken", this.getCookie("csrftoken"));

    fetch(`${BASE_URL}/comperative_schedule/update`, {
      method: "POST",
      headers: {
        "X-CSRFToken": this.getCookie("csrftoken"),
      },
      body: form_data,
    })
      .then((response) => response.json())
      .then((data) => {
        console.log("data: ", data);
        if (data.success) {
          alert("Comparative Schedule updated successfully" + " " + data.cs_id);
        } else {
          alert("Error updating Comparative Schedule");
        }
      }).catch(err => console.log("onUpdateSchedule: ", err));
  };

  onDeleteBidModal = (bid_count, supplier_name) => {
    // reset bid no index
    let bid_count_ = this.state.bid_count - 1;
    let bids = this.state.bids.filter((bid) => bid.bid_count !== bid_count);
    // update bid_count index for all bids sequentially
    bids = bids.map((bid, index) => {
      bid.bid_count = index + 1;
      return bid;
    });
    this.setState({
      ...this.state,
      bids: bids,
      bid_count: bid_count_,
    });
    this.deleteBid(bid_count, supplier_name);
  };

  deleteBid = (bid_count, supplier_name) => {
    let form_data = new FormData();
    form_data.append("cs_id", this.state.cs_id);
    form_data.append("bid_count", bid_count);
    form_data.append("supplier_name", supplier_name);
    form_data.append("csrfmiddlewaretoken", this.getCookie("csrftoken"));

    fetch(`${BASE_URL}/comperative_schedule/delete_bid`, {
      method: "POST",
      headers: {
        "X-CSRFToken": this.getCookie("csrftoken"),
      },
      body: form_data,
    })
      .then((response) => response.json())
      .then((data) => {
        console.log("data: ", data);
        if (data.success) {
          alert("Bid deleted successfully");
        } else {
          alert("Error deleting Bid");
        }
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
          bid_count: bid_count,
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
    let file = event.target.files[0];
    let fileUrl = this.onGetFileObjectUrl(file);
    this.setState({
      ...this.state,
      [name_]: file,
      advert_url: fileUrl,
    });
  };

  onAddComplianceTable = () => {
    // add bid compliance
    if(this.state.bids.length === 0) {
      alert("Please add bids first");
      return;
    }
    let compliances = this.state.bids.map((bid) => {
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
        remarks: "",
      };
    });

    let complianceRemarks = this.state.bids.map((bid) => {
      return {
        bid_count: bid.bid_count,
        supplier: bid.supplier,
        supplier_name: bid.supplier_name,
        remarks: "",
      };
    });

    this.setState({
      ...this.state,
      compliance: compliances,
      complianceRemarks: complianceRemarks,
      complianceTable: !this.state.complianceTable,
    });
  };

  onComplianceItemsChange = (name_, event) => {
    let { name, value } = event.target;
    console.log("name: ", name, "value: ", value);
    let compliance = this.state.compliance;
    if(compliance.length === 0) {
      alert("Please add bids first");
      return;
    }
    console.log("showSamples: ", this.state.showSamples, "showSiteVisit: ", this.state.showSiteVisit, value, name);
    let updatedComplianceList = compliance.map((compliance_, index) => {
      let _compliance = {};
      let site_visit = compliance_.site_visit;
      let samples_required = compliance_.samples_required;
      if (name === "showSiteVisit") {
        if(value === "no"){
          site_visit = false;
        }
      } else if (name === "showSamples") {
        if(value === "no"){
          samples_required = false;
        }
      }
      
      console.log("other value: ", value)
      console.log("site_visit: ", site_visit, "samples_required: ", samples_required);
      console.log("showSamples: ", this.state.showSamples, "showSiteVisit: ", this.state.showSiteVisit);
      _compliance = {
        payment_terms: compliance_.payment_terms,
        bid_validity: compliance_.bid_validity,
        delivery_period: compliance_.delivery_period,
        technical_specifications: compliance_.technical_specifications,
        valid_tax_clearance: compliance_.valid_tax_clearance,
        registered_with_praz: compliance_.registered_with_praz,
        site_visit: site_visit,
        samples_required: samples_required,
      };

      // set compliance_['decision'] to true if all compliance are true
      let allValuesTrue = true;
      for (const key in _compliance) {
        if (_compliance.hasOwnProperty(key)) {
          if (key === "site_visit" && value === "no") {
            continue;
          } else if (key === "samples_required" && value === "no") {
            continue;
          } else if (!_compliance[key]) {
            allValuesTrue = false;
            break;
          }
        }
      }

      compliance_["decision"] = allValuesTrue;
      compliance_["reject"] = !allValuesTrue;

      return compliance_;
    });
    console.log("state: ", this.state.showSamples, this.state.showSiteVisit)
    this.setState({
      ...this.state,
      [name]: value,
      compliance: updatedComplianceList,
    });
  };

  onComplianceChange = (index, event) => {
    let { name, checked } = event.target;
    console.log("name: ", name, "checked: ", checked);
    let compliance = this.state.compliance;
    compliance[index][name] = checked;
    // // filter decision and reject from list
    // let _compliance = {};
    // if (this.state.showSamples && this.state.showSiteVisit) {
    //   _compliance = {
    //     payment_terms: compliance[index].payment_terms,
    //     bid_validity: compliance[index].bid_validity,
    //     delivery_period: compliance[index].delivery_period,
    //     technical_specifications: compliance[index].technical_specifications,
    //     valid_tax_clearance: compliance[index].valid_tax_clearance,
    //     registered_with_praz: compliance[index].registered_with_praz,
    //     site_visit: compliance[index].site_visit,
    //     samples_required: compliance[index].samples_required,
    //   };
    // } else if (this.state.showSamples && !this.state.showSiteVisit) {
    //   _compliance = {
    //     payment_terms: compliance[index].payment_terms,
    //     bid_validity: compliance[index].bid_validity,
    //     delivery_period: compliance[index].delivery_period,
    //     technical_specifications: compliance[index].technical_specifications,
    //     valid_tax_clearance: compliance[index].valid_tax_clearance,
    //     registered_with_praz: compliance[index].registered_with_praz,
    //     samples_required: compliance[index].samples_required,
    //   };
    // } else if (!this.state.showSamples && this.state.showSiteVisit) {
    //   _compliance = {
    //     payment_terms: compliance[index].payment_terms,
    //     bid_validity: compliance[index].bid_validity,
    //     delivery_period: compliance[index].delivery_period,
    //     technical_specifications: compliance[index].technical_specifications,
    //     valid_tax_clearance: compliance[index].valid_tax_clearance,
    //     registered_with_praz: compliance[index].registered_with_praz,
    //     site_visit: compliance[index].site_visit,
    //   };
    // } else {
    //   _compliance = {
    //     payment_terms: compliance[index].payment_terms,
    //     bid_validity: compliance[index].bid_validity,
    //     delivery_period: compliance[index].delivery_period,
    //     technical_specifications: compliance[index].technical_specifications,
    //     valid_tax_clearance: compliance[index].valid_tax_clearance,
    //     registered_with_praz: compliance[index].registered_with_praz,
    //   };
    // }

    // // set compliance[index]['decision'] to true if all compliance are true
    // let compliance_values = Object.values(_compliance);
    // console.log("compliances: ", compliance_values);
    // let decision = compliance_values.every((value) => value === true);
    let _compliance = {
      payment_terms: compliance[index].payment_terms,
      bid_validity: compliance[index].bid_validity,
      delivery_period: compliance[index].delivery_period,
      technical_specifications: compliance[index].technical_specifications,
      valid_tax_clearance: compliance[index].valid_tax_clearance,
      registered_with_praz: compliance[index].registered_with_praz,
      site_visit: compliance[index].site_visit,
      samples_required: compliance[index].samples_required,
    };

    // set compliance_['decision'] to true if all compliance are true
    let allValuesTrue = true;
    for (const key in _compliance) {
      if (_compliance.hasOwnProperty(key)) {
        if (key === "site_visit" && this.state.showSiteVisit === "no") {
          continue;
        } else if (key === "samples_required" && this.state.showSamples === "no") {
          continue;
        } else if (!_compliance[key]) {
          allValuesTrue = false;
          break;
        }
      }
    }
    compliance[index]["decision"] = allValuesTrue;
    compliance[index]["reject"] = !allValuesTrue;

    this.setState({
      ...this.state,
      compliance: compliance,
    });
  };

  onComplianceRemarksChange = (supplier_name, event) => {
    let { name, value } = event.target;
    console.log(
      "name: ",
      name,
      "value: ",
      value,
      "supplier_name: ",
      supplier_name
    );
    let complianceRemarks = this.state.complianceRemarks;
    let index = complianceRemarks.findIndex(
      (item) => item.supplier_name === supplier_name
    );
    if (index !== -1) {
      complianceRemarks[index]["remarks"] = value;
      this.setState({
        ...this.state,
        complianceRemarks: complianceRemarks,
      });
    } else {
      complianceRemarks.push({
        supplier_name: supplier_name,
        remarks: value,
      });
      this.setState({
        ...this.state,
        complianceRemarks: complianceRemarks,
      });
    }
  };

  onSaveCompliance = () => {
    let form_data = new FormData();
    form_data.append("cs_id", this.state.cs_id);
    form_data.append(
      "compliance",
      JSON.stringify({
        compliance: this.state.compliance,
      })
    );
    form_data.append(
      "complianceRemarks",
      JSON.stringify({
        complianceRemarks: this.state.complianceRemarks,
      })
    );
    form_data.append("csrfmiddlewaretoken", this.getCookie("csrftoken"));

    fetch(`${BASE_URL}/comperative_schedule/save_compliance`, {
      method: "POST",
      headers: {
        "X-CSRFToken": this.getCookie("csrftoken"),
      },
      body: form_data,
    })
      .then((response) => response.json())
      .then((data) => {
        console.log("data: ", data);
        if (data.success) {
          alert("Compliance saved successfully");
        } else {
          alert("Error saving Compliance");
        }
      });
  };

  onCloseCS = () => {
    let form_data = new FormData();
    form_data.append("cs_id", this.state.cs_id);
    form_data.append("csrfmiddlewaretoken", this.getCookie("csrftoken"));

    fetch(`${BASE_URL}/comperative_schedule/close_compliance`, {
      method: "POST",
      headers: {
        "X-CSRFToken": this.getCookie("csrftoken"),
      },
      body: form_data,
    })
      .then((response) => response.json())
      .then((data) => {
        console.log("data: ", data);
        if (data.success) {
          let rankings = data.rankings;
          this.setState({
            ...this.state,
            rankings: rankings,
            rankingTable: true,
          });
          alert("Bids ranked successfully");
        } else {
          alert("Error saving Schedule");
        }
      });
  };

  render() {

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
      supplierModal = (
        <div className="fixed inset-0 flex items-center justify-center z-50 pt-10 pb-20">
          <div className="bg-gulf-blue-100 rounded-lg shadow-lg p-6 max-h-screen overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium">ADD SUPPLIER</h3>
              <button
                type="button"
                className="text-gray-400 hover:text-gray-500 focus:outline-none"
                onClick={this.onAddSuppliersModal}
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
            <div className="overflow-auto px-2 py-2 mt-5 rounded-md bg-gulf-blue-300">
              <div>
                <div className="flex-1 w-full ml-1">
                  <label
                    htmlFor="supplier_name"
                    className="block text-sm font-medium leading-6 text-gray-900"
                  >
                    Supplier Name
                  </label>
                  <div className="mt-2">
                    <input
                      name="supplier_name"
                      onChange={(e) =>
                        this.onSupplierChange("supplier_name", e)
                      }
                      type="text"
                      required="required"
                      className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                    />
                  </div>
                </div>
              </div>

              <div className="flex justify-center mt-5 px-3 py-3">
                <div className="m-2">
                  <button
                    onClick={this.onAddSuppliersModal}
                    className="rounded-md text-gray-50 text-sm bg-gray-300 hover:bg-blue-550 px-3 py-2 font-semibold leading-6"
                  >
                    <span className="ml-2">CANCEL</span>
                  </button>
                </div>
                <div className="m-2">
                  <button
                    onClick={this.onSaveSupplier}
                    className="rounded-md text-gray-50 text-sm bg-blue-925 hover:bg-blue-550 px-3 py-2 font-semibold leading-6"
                  >
                    <span className="ml-2">SAVE SUPPLIER</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      );
    }

    if (this.state.approvalsJustificationModal) {
      rejectApprovalJustification = (
        <div className="fixed inset-0 flex items-center justify-center z-50 pt-10 pb-20">
          <div className="bg-gulf-blue-100 rounded-lg shadow-lg p-6 max-h-screen overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium">Reason for rejection</h3>
              <button
                type="button"
                className="text-gray-400 hover:text-gray-500 focus:outline-none"
                onClick={this.onApprovalJustificationModal}
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
            <div className="overflow-auto px-2 py-2 mt-5 rounded-md bg-gulf-blue-300">
              <div>
                <div className="flex-1 w-full ml-1">
                  <label
                    htmlFor="bid_date"
                    className="block text-sm font-medium leading-6 text-gray-900"
                  >
                    Justification
                  </label>
                  <div className="mt-2">
                    <textarea
                      name="justification"
                      onChange={(e) =>
                        this.onApprovalJustificationChange("justification", e)
                      }
                      type="text"
                      required="required"
                      className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                    />
                  </div>
                </div>
              </div>

              <div className="flex justify-center mt-5 px-3 py-3">
                <div className="m-2">
                  <button
                    onClick={this.onApprovalJustificationModal}
                    className="rounded-md text-gray-50 text-sm bg-gray-300 hover:bg-blue-550 px-3 py-2 font-semibold leading-6"
                  >
                    <span className="ml-2">CANCEL</span>
                  </button>
                </div>
                <div className="m-2">
                  <button
                    onClick={() =>
                      this.onApprovalApprove(
                        this.state.currentApprover.role,
                        this.state.currentApprover.username,
                        "Rejected",
                        this.state.currentApprover.justification
                      )
                    }
                    className="rounded-md text-gray-50 text-sm bg-blue-925 hover:bg-blue-550 px-3 py-2 font-semibold leading-6"
                  >
                    <span className="ml-2">PROCEED</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      );
    }

    if (this.state.committeeJustificationModal) {
      rejectJustification = (
        <div className="fixed inset-0 flex items-center justify-center z-50 pt-10 pb-20">
          <div className="bg-gulf-blue-100 rounded-lg shadow-lg p-6 max-h-screen overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium">Reason for rejection</h3>
              <button
                type="button"
                className="text-gray-400 hover:text-gray-500 focus:outline-none"
                onClick={this.onCommitteeJustificationModal}
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
            <div className="overflow-auto px-2 py-2 mt-5 rounded-md bg-gulf-blue-300">
              <div>
                <div className="flex-1 w-full ml-1">
                  <label
                    htmlFor="bid_date"
                    className="block text-sm font-medium leading-6 text-gray-900"
                  >
                    Justification
                  </label>
                  <div className="mt-2">
                    <textarea
                      name="justification"
                      onChange={(e) =>
                        this.onCommitteeJustificationChange("justification", e)
                      }
                      type="text"
                      required="required"
                      className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                    />
                  </div>
                </div>
              </div>

              <div className="flex justify-center mt-5 px-3 py-3">
                <div className="m-2">
                  <button
                    onClick={this.onCommitteeJustificationModal}
                    className="rounded-md text-gray-50 text-sm bg-gray-300 hover:bg-blue-550 px-3 py-2 font-semibold leading-6"
                  >
                    <span className="ml-2">CANCEL</span>
                  </button>
                </div>
                <div className="m-2">
                  <button
                    onClick={() =>
                      this.onCommitteeApprove(
                        this.state.currentApprover.username,
                        "Rejected",
                        this.state.currentApprover.justification
                      )
                    }
                    className="rounded-md text-gray-50 text-sm bg-blue-925 hover:bg-blue-550 px-3 py-2 font-semibold leading-6"
                  >
                    <span className="ml-2">PROCEED</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      );
    }

    if (this.state.addItemsModal) {
      itemsModal = (
        <div className="fixed inset-0 flex items-center justify-center z-50 pt-10 pb-20">
          <div className="bg-gulf-blue-100 rounded-lg shadow-lg p-6 max-h-screen overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium">SELECT SCHEDULE ITEMS</h3>
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
            <div className="overflow-auto px-2 py-2 mt-5 rounded-md bg-gulf-blue-300">
              <table
                style={{ width: "100%" }}
                className="table-auto w-full text-left"
              >
                <thead>
                  <tr className="text-gray-900">
                    <th className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                      Select
                    </th>
                    <th className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                      Item
                    </th>
                    <th className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                      Quantity
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {this.state.pr_items && this.state.pr_items.map((item, index) => {
                    return (
                      <tr key={index} className="text-gray-900">
                        <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                          <input
                            type="checkbox"
                            checked={item.ordered ? item.ordered : false}
                            onChange={() =>
                              this.onAddCSItem(item.id, item.ordered)
                            }
                          />
                        </td>
                        <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                          {item.item_required}
                        </td>
                        <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                          {item.quantity}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>

              <div className="flex justify-center mt-5 px-3 py-3">
                <div className="m-2">
                  <button
                    onClick={this.onSubmitCSItems}
                    className="rounded-md text-gray-50 text-sm bg-blue-925 hover:bg-blue-550 px-3 py-2 font-semibold leading-6"
                  >
                    <span className="ml-2">SAVE SCHEDULE ITEMS</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      );
    }

    if (this.state.addBidModal) {
      bidsModal = (
        <div
          id={"bid-" + this.state.currentBid.bid_count}
          className="fixed inset-0 flex items-center justify-center z-50 pt-10 pb-20"
        >
          <div className="bg-gulf-blue-100 rounded-lg shadow-lg p-6 max-h-screen min-w-max overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium">ADD BID DETAILS</h3>
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
                          <option
                            value={
                              this.state.currentBid.supplier +
                              "-#-" +
                              this.state.currentBid.supplier_name
                            }
                          >
                            {this.state.currentBid.supplier_name}
                          </option>
                        ) : (
                          ""
                        )}
                        <option>Select Supplier</option>
                        {this.state.suppliers
                          ? this.state.suppliers.map((supplier) => (
                              <option
                                value={supplier.id + "-#-" + supplier.name}
                              >
                                {supplier.name}
                              </option>
                            ))
                          : ""}
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
                        name=""
                        type="number"
                        value={this.state.currentBid.bid_count}
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

                {this.state.cs_items && this.state.cs_items.map((item, index) => {
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
                            defaultValue={item.item_required}
                            onChange={(e) =>
                              this.onCurrentBidItemChange(
                                item.item_required,
                                "item_required",
                                e,
                                this.state.currentBid.bid_count
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
                                item.item_required,
                                "quantity",
                                e,
                                this.state.currentBid.bid_count
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
                                  item.item_required,
                                  "unit_of_measurement",
                                  e,
                                  this.state.currentBid.bid_count
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
                              {this.state.uom ? this.state.uom.map((uom) => (
                                <option value={uom.name}>{uom.name}</option>
                              )): <option>No Units</option>}
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
                                this.onCurrentBidItemChange(
                                  item.item_required,
                                  "vat",
                                  e,
                                  this.state.currentBid.bid_count
                                )
                              }
                              autoComplete="vat"
                              className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6"
                            >
                              {item.vat ? (
                                <option value={item.vat}>{item.vat}</option>
                              ) : (
                                ""
                              )}
                              <option value="">Select VAT</option>
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
                                item.item_required,
                                "unit_price",
                                e,
                                this.state.currentBid.bid_count
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

    if (this.state.updateBidModal) {
      updateBidModal = (
        <div
          id={"bid-" + this.state.currentBid.bid_count}
          className="fixed inset-0 flex items-center justify-center z-50 pt-10 pb-20"
        >
          <div className="bg-white rounded-lg shadow-lg p-6 max-h-screen min-w-max overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium">Update Bid</h3>
              <button
                type="button"
                className="text-gray-400 hover:text-gray-500 focus:outline-none"
                onClick={this.onCloseUpdateBidBid}
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
                          <option
                            value={
                              this.state.currentBid.supplier +
                              "-#-" +
                              this.state.currentBid.supplier_name
                            }
                          >
                            {this.state.currentBid.supplier_name}
                          </option>
                        ) : (
                          ""
                        )}
                        <option>Select Supplier</option>
                        {this.state.suppliers
                          ? this.state.suppliers.map((supplier) => (
                              <option
                                value={supplier.id + "-#-" + supplier.name}
                              >
                                {supplier.name}
                              </option>
                            ))
                          : ""}
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

                {this.state.currentBid.items && this.state.currentBid.items.map((item, index) => {
                  return (
                    <div key={index} className="flex justify-evenly mt-5  px-2 py-2 rounded-md">
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
                            defaultValue={item.item_required}
                            onChange={(e) =>
                              this.onCurrentBidItemChange(
                                item.item_required,
                                "item_required",
                                e,
                                this.state.currentBid.bid_count
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
                                item.item_required,
                                "quantity",
                                e,
                                this.state.currentBid.bid_count
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
                              defaultValue={item.unit_of_measurement}
                              onChange={(e) =>
                                this.onCurrentBidItemChange(
                                  item.item_required,
                                  "unit_of_measurement",
                                  e,
                                  this.state.currentBid.bid_count
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
                              {this.state.uom ? this.state.uom.map((uom) => (
                                <option value={uom.name}>{uom.name}</option>
                              )): <option>No Units</option>}
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
                              defaultValue={item.vat}
                              onChange={(e) =>
                                this.onCurrentBidItemChange(
                                  item.item_required,
                                  "vat",
                                  e,
                                  this.state.currentBid.bid_count
                                )
                              }
                              autoComplete="vat"
                              className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6"
                            >
                              {item.vat ? (
                                <option value={item.vat}>{item.vat}</option>
                              ) : (
                                ""
                              )}
                              <option value="">Select VAT</option>
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
                                item.item_required,
                                "unit_price",
                                e,
                                this.state.currentBid.bid_count
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

    complianceTable = (
      <div className="bg-gulf-blue-300 shadow shadow-nepal-300 text-gray-700 rounded px-2 py-2">
        <div className="space-y-12 px-5 py-5">
          <div className="px-4 sm:px-0 mt-6 border-t border-gray-100 border-gray-900/10">
            <h2 className="text-base font-semibold leading-6 text-gray-900">
              COMPLIANCE TABLE
            </h2>
            <p className="mt-1 max-w-2xl text-sm leading-6 text-gray-500">
              Key: Comply/ Not Comply (Y/ N), Not Stated (NS)
            </p>
            <div className="flex justify-evenly mt-5 bg-gulf-blue-300 px-2 py-2 rounded-md">
              <div className="flex-1 w-45">
                <label
                  htmlFor="site_visit"
                  className="block text-sm font-medium leading-6 text-gray-900"
                >
                  Site visit required?
                </label>
                <div className="mt-2">
                  <select
                    id="site_visit"
                    name="showSiteVisit"
                    onChange={(e) =>
                      this.onComplianceItemsChange("showSiteVisit", e)
                    }
                    disabled={(this.state.username === this.state.cs_owner) || (this.state.cs_owner === "") ? false : true}
                    autoComplete="site_visit"
                    className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6 chzn-select"
                  >
                    <option value="">Select Option</option>
                    <option value="yes">Yes</option>
                    <option value="no">No</option>
                  </select>
                </div>
              </div>
              <div className="flex-1 w-45">
                <div>
                  <label
                    htmlFor="samples"
                    className="block text-sm font-medium leading-6 text-gray-900"
                  >
                    Are Samples Required?
                  </label>
                  <div className="mt-2">
                    <select
                      id="samples"
                      name="showSamples"
                      onChange={(e) =>
                        this.onComplianceItemsChange("showSamples", e)
                      }
                      disabled={(this.state.username === this.state.cs_owner) || (this.state.cs_owner === "") ? false : true}
                      autoComplete="samples"
                      className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6 chzn-select"
                    >
                      <option value="">Select Option</option>
                      <option value="yes">Yes</option>
                      <option value="no">No</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>

            <div className="overflow-auto px-2 py-2 mt-5 rounded-md bg-gulf-blue-300">
              <table className="table-auto w-full text-left">
                <thead>
                  <tr className="text-gray-900">
                    <th className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                      #
                    </th>
                    <th className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                      Name of Supplier
                    </th>
                    <th className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                      Payment <br />
                      Terms
                    </th>
                    <th className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                      Bid <br />
                      Validity
                    </th>
                    <th className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                      Delivery <br />
                      Period
                    </th>
                    <th className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                      Technical <br />
                      Specifications
                    </th>
                    <th className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                      Valid <br />
                      Tax Clearance
                    </th>
                    <th className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                      Registered <br />
                      with PRAZ?
                    </th>
                    {/* <th className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                      Tax <br />
                      Status
                    </th> */}
                    {this.state.showSiteVisit === "yes" ? (
                      <th
                        id="site_visit_header"
                        className="site-visit-header border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2"
                      >
                        Site Visit
                        <br />
                        Done?
                      </th>
                    ) : (
                      ""
                    )}
                    {this.state.showSamples === "yes" ? (
                      <th
                        id="samples_header"
                        className="samples-header border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2"
                      >
                        Samples <br />
                        Delivered?
                      </th>
                    ) : (
                      ""
                    )}

                    <th className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                      Accept
                    </th>
                    <th className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                      Reject
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {this.state.compliance && this.state.compliance.map((comp, key) => {
                    return (
                      <tr key={key}>
                        <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                          {key + 1}
                        </td>
                        <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                          {comp.supplier_name}
                        </td>
                        <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                          <input
                            name="payment_terms"
                            checked={
                              comp.payment_terms ? comp.payment_terms : false
                            }
                            onChange={(e) => this.onComplianceChange(key, e)}
                            disabled={(this.state.username === this.state.cs_owner) || (this.state.cs_owner === "") ? false : true}
                            id="payment_terms"
                            type="checkbox"
                          />
                        </td>
                        <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                          <input
                            name="bid_validity"
                            checked={
                              comp.bid_validity ? comp.bid_validity : false
                            }
                            onChange={(e) => this.onComplianceChange(key, e)}
                            disabled={(this.state.username === this.state.cs_owner) || (this.state.cs_owner === "") ? false : true}
                            id="bid_validity"
                            type="checkbox"
                          />
                        </td>
                        <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                          <input
                            name="delivery_period"
                            checked={
                              comp.delivery_period
                                ? comp.delivery_period
                                : false
                            }
                            onChange={(e) => this.onComplianceChange(key, e)}
                            disabled={(this.state.username === this.state.cs_owner) || (this.state.cs_owner === "") ? false : true}
                            id="delivery_period"
                            type="checkbox"
                          />
                        </td>
                        <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                          <input
                            name="technical_specifications"
                            checked={
                              comp.technical_specifications
                                ? comp.technical_specifications
                                : false
                            }
                            onChange={(e) => this.onComplianceChange(key, e)}
                            disabled={(this.state.username === this.state.cs_owner) || (this.state.cs_owner === "") ? false : true}
                            id="technical_specifications"
                            type="checkbox"
                          />
                        </td>
                        <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                          <input
                            name="valid_tax_clearance"
                            checked={
                              comp.valid_tax_clearance
                                ? comp.valid_tax_clearance
                                : false
                            }
                            onChange={(e) => this.onComplianceChange(key, e)}
                            disabled={(this.state.username === this.state.cs_owner) || (this.state.cs_owner === "") ? false : true}
                            id="valid_tax_clearance"
                            type="checkbox"
                          />
                        </td>
                        <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                          <input
                            name="registered_with_praz"
                            checked={
                              comp.registered_with_praz
                                ? comp.registered_with_praz
                                : false
                            }
                            onChange={(e) => this.onComplianceChange(key, e)}
                            disabled={(this.state.username === this.state.cs_owner) || (this.state.cs_owner === "") ? false : true}
                            id="registered_with_praz"
                            type="checkbox"
                          />
                        </td>
                        {/* <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                          <input
                            name="tax_status"
                            checked={comp.tax_status ? comp.tax_status : false}
                            onChange={(e) => this.onComplianceChange(key, e)}
                            disabled={(this.state.username === this.state.cs_owner) || (this.state.cs_owner === "") ? false : true}
                            id="tax_status"
                            type="checkbox"
                          />
                        </td> */}
                        {this.state.showSiteVisit === "yes" ? (
                          <td
                            id="site_visit_header"
                            className="site-visit-header border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2"
                          >
                            <input
                              name="site_visit"
                              checked={
                                comp.site_visit ? comp.site_visit : false
                              }
                              onChange={(e) => this.onComplianceChange(key, e)}
                              disabled={(this.state.username === this.state.cs_owner) || (this.state.cs_owner === "") ? false : true}
                              id="site_visit"
                              type="checkbox"
                            />
                          </td>
                        ) : (
                          ""
                        )}
                        {this.state.showSamples === "yes" ? (
                          <td
                            id="samples_header"
                            className="samples-header border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2"
                          >
                            <input
                              name="samples_required"
                              checked={
                                comp.samples_required
                                  ? comp.samples_required
                                  : false
                              }
                              onChange={(e) => this.onComplianceChange(key, e)}
                              disabled={(this.state.username === this.state.cs_owner) || (this.state.cs_owner === "") ? false : true}
                              id="samples_required"
                              type="checkbox"
                            />
                          </td>
                        ) : (
                          ""
                        )}
                        <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                          <input
                            name="decision"
                            checked={comp.decision ? comp.decision : false}
                            onChange={(e) => this.onComplianceChange(key, e)}
                            disabled={(this.state.username === this.state.cs_owner) || (this.state.cs_owner === "") ? false : true}
                            id="decision"
                            type="checkbox"
                          />
                        </td>
                        <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                          <input
                            name="reject"
                            checked={comp.reject ? comp.reject : false}
                            onChange={(e) => this.onComplianceChange(key, e)}
                            disabled={(this.state.username === this.state.cs_owner) || (this.state.cs_owner === "") ? false : true}
                            id="reject"
                            type="checkbox"
                          />
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <div className="px-2 py-2 mt-5 rounded-sm bg-gulf-blue-300">
              <table className="table-auto w-full text-left">
                <thead>
                  <tr className="text-gray-900">
                    <th className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                      Supplier
                    </th>
                    <th className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                      Remarks
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {this.state.complianceRemarks && this.state.complianceRemarks.map((bid, key) => {
                    return (
                      <tr>
                        <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                          {bid.supplier_name}
                        </td>
                        <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                          <input
                            name="remarks"
                            defaultValue={bid.remarks}
                            onChange={(e) =>
                              this.onComplianceRemarksChange(
                                bid.supplier_name,
                                e
                              )
                            }
                            disabled={(this.state.username === this.state.cs_owner) || (this.state.cs_owner === "") ? false : true}
                            type="text"
                            className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6 chzn-select"
                          />
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {this.state.username === this.state.cs_owner && !this.state.approvalsComplete ? (
          <div className="flex justify-center mt-5 px-3 py-3">
            <div className="flex-1 m-2">
              <button
                style={{ width: "100%" }}
                onClick={this.onSaveCompliance}
                name="save_next"
                className="rounded-md bg-blue-925 hover:bg-blue-550 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
              >
                SAVE COMPLIANCES
              </button>
            </div>
          </div>
        ) : (
          ""
        )}
      </div>
    );

    rankingTable = (
      <div className="bg-gulf-blue-300 shadow shadow-nepal-300 text-gray-700 rounded px-2 py-2">
        <div className="space-y-12 px-5 py-5">
          <div className="px-4 sm:px-0 mt-6 border-t border-gray-100 border-gray-900/10">
            <h2 className="text-base font-semibold leading-6 text-gray-900">
              RANKING TABLE
            </h2>

            <div className="overflow-auto px-2 py-2 mt-5 rounded-md bg-gulf-blue-300">
              <table className="table-auto w-full text-left">
                <thead>
                  <tr className="text-gray-900">
                    <th className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                      ID
                    </th>
                    <th className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                      Name of Supplier
                    </th>
                    <th className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                      Rank
                    </th>
                    <th className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                      Decision
                    </th>
                    <th className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                      Remarks
                    </th>
                    <th className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                      Total
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {this.state.rankings && this.state.rankings.map((rank, key) => {
                    return (
                      <tr className="text-gray-900">
                        <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                          {key + 1}
                        </td>
                        <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                          {rank.supplier_name}
                        </td>
                        <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                          {rank.rank}
                        </td>
                        <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                          {rank.decision}
                        </td>
                        <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                          {rank.remarks}
                        </td>
                        <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                          {rank.total}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    );

    committeeTable = (
      <div className="bg-gulf-blue-300 shadow shadow-nepal-300 text-gray-700 rounded px-2 py-2">
        <div className="space-y-12 px-5 py-5">
          <div className="px-4 sm:px-0 mt-6 border-t border-gray-100 border-gray-900/10">
            <h2 className="text-base font-semibold leading-6 text-gray-900">
              Committee Members
            </h2>

            <div className="overflow-auto px-2 py-2 mt-5 rounded-md bg-gulf-blue-300">
              <table className="table-auto w-full text-left">
                <tbody>
                  <tr className="text-gray-900">
                    <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                      <div>
                        <div className="mt-2">
                          {this.state.username === this.state.cs_owner ? (
                            <select
                              onChange={(text) =>
                                this.onCommitteeChange("memberPosition", text)
                              }
                              id="memberPosition"
                              name="memberPosition"
                              autoComplete="memberPosition"
                              className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6 chzn-select"
                            >
                              <option value="">Select Member Position</option>
                              <option value="chairman">Chairman</option>
                              <option value="finance">Finance</option>
                              <option value="procurement">Procurement</option>
                              <option value="user">User</option>
                              <option value="other">Other</option>
                            </select>
                          ) : (
                            ""
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                      <div>
                        <div className="mt-2">
                          {this.state.username === this.state.cs_owner ? (
                            <select
                              onChange={(text) =>
                                this.onCommitteeChange("memberUserName", text)
                              }
                              id="memberUserName"
                              name="memberUserName"
                              autoComplete="memberUserName"
                              className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6 chzn-select"
                            >
                              <option value="">Select User</option>
                              {this.state.users
                                ? this.state.users.map((user) => (
                                    <option value={user.username}>
                                      {user.first_name + " " + user.last_name}
                                    </option>
                                  ))
                                : <option value="">No Users</option>}

                            </select>
                          ) : (
                            ""
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2"></td>
                    <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                      {this.state.username === this.state.cs_owner && !this.state.approvalsComplete && this.state.member.memberPosition !== "" && this.state.member.memberUserName !== "" ? (
                        <div className="w-30">
                          <button
                            style={{ width: "100%" }}
                            onClick={this.onAddCommitteeMembers}
                            name="save_next"
                            className="rounded-md bg-blue-925 hover:bg-blue-550 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
                          >
                            ADD MEMBER
                          </button>
                        </div>
                      ) : (
                        ""
                      )}
                    </td>
                    <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2"></td>
                  </tr>
                  <tr className="text-gray-900">
                    <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                      CREATED BY
                    </td>
                    <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                      {this.state.creator}
                    </td>
                    <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                      INITIATED
                    </td>
                    <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">

                    </td>
                    <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                      {this.state.created_at ? this.state.created_at.split(".")[0] : ""}
                    </td>
                  </tr>
                  {this.state.committeeMembers && this.state.committeeMembers.map((member, key) => {
                    return (
                      <tr className="text-gray-900">
                        <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                          {member.memberPosition.toUpperCase()}
                        </td>
                        <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                          {member.memberName
                            ? member.memberName
                            : member.memberUserName}
                        </td>
                        <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                          {member.memberApproval === "Approved" && "APPROVED"}
                          {member.memberApproval === "Rejected" && "REJECTED"}
                          {(member.memberApproval === "" || member.memberApproval === null) && (
                            <div className="flex justify-content-evenly">
                              {this.state.username === this.state.cs_owner && !this.state.approvalsComplete ? (
                                <div className="m-2">
                                  <button
                                    onClick={() =>
                                      this.onRemoveCommitteeMember(
                                        key,
                                        member.memberUserName
                                      )
                                    }
                                    name="save_next"
                                    className="rounded-md bg-blue-925 hover:bg-blue-550 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
                                  >
                                    REMOVE
                                  </button>
                                </div>
                              ) : (
                                ""
                              )}
                              {this.state.username === member.memberUserName? (
                                <div className="flex justify-content-evenly">
                                  <div className="m-2">
                                    <button
                                      onClick={() =>
                                        this.onCommitteeApprove(
                                          member.memberUserName,
                                          "Approved",
                                          ""
                                        )
                                      }
                                      name="save_next"
                                      className="rounded-md bg-blue-925 hover:bg-blue-550 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
                                    >
                                      APPROVE
                                    </button>
                                  </div>
                                  <div className="m-2">
                                    <button
                                      onClick={() =>
                                        this.onCommitteeJustificationModal(member.memberUserName)
                                      }
                                      name="save_next"
                                      className="rounded-md bg-blue-925 hover:bg-blue-550 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
                                    >
                                      REJECT
                                    </button>
                                  </div>
                                </div>
                              ) : (
                                ""
                              )}
                            </div>
                          )}
                        </td>
                        <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                          {member.committeeJustification}
                        </td>
                        <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                          {member.committeeDate ? member.committeeDate.split(".")[0] : ""}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    );

    approvalsTable = (
      <div className="bg-gulf-blue-300 shadow shadow-nepal-300 text-gray-700 rounded px-2 py-2">
        <div className="space-y-12 px-5 py-5">
          <div className="px-4 sm:px-0 mt-6 border-t border-gray-100 border-gray-900/10">
            <h2 className="text-base font-semibold leading-6 text-gray-900">
              Approvals
            </h2>

            <div className="overflow-auto px-2 py-2 mt-5 rounded-md bg-gulf-blue-300">
              <table className="table-auto w-full text-left">
                <tbody>
                  <tr className="text-gray-900">
                    <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                      FINANCE MANAGER
                    </td>
                    <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                      {this.state.fmApproval && this.state.fmApproval.approver_name}
                    </td>
                    <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                      {this.state.fmApproval && this.state.fmApproval.approval === "Rejected" && this.state.fmApproval.justification}
                    </td>
                    <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                      {this.state.fmApproval && this.state.fmApproval.approval === "Approved" && "APPROVED"}
                      {this.state.fmApproval && this.state.fmApproval.approval === "Rejected" && "REJECTED"}
                      {this.state.committeeApprovalComplete && (
                          <div className="flex justify-content-evenly">
                            {(this.state.requester_role === 'check') && Object.keys(this.state.fmApproval).length === 0 ? (
                              <div className="flex justify-content-evenly">
                                <div className="m-2">
                                  <button
                                    onClick={() =>
                                      this.onApprovalApprove(
                                        "finance_manager",
                                        this.state.username,
                                        "Approved",
                                        ""
                                      )
                                    }
                                    name="save_next"
                                    className="rounded-md bg-blue-925 hover:bg-blue-550 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
                                  >
                                    APPROVE
                                  </button>
                                </div>
                                <div className="m-2">
                                  <button
                                    onClick={() =>
                                      this.onApprovalJustificationModal(this.state.username, "finance_manager")
                                    }
                                    name="save_next"
                                    className="rounded-md bg-blue-925 hover:bg-blue-550 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
                                  >
                                    REJECT
                                  </button>
                                </div>
                              </div>
                            ) : (
                              ""
                            )}
                          </div>
                        )
                      }
                    </td>
                    <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                      {this.state.fmApproval && this.state.fmApproval.approval_date ? this.state.fmApproval.approval_date.split(".")[0] : ""}
                    </td>
                  </tr>
                  <tr className="text-gray-900">
                    <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                      GENERAL MANAGER
                    </td>
                    <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                      {this.state.gmApproval && this.state.gmApproval.approver_name}
                    </td>
                    <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                      {this.state.gmApproval && this.state.gmApproval.approval === "Rejected" && this.state.gmApproval.justification}
                    </td>
                    <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                      {this.state.gmApproval && this.state.gmApproval.approval === "Approved" && "APPROVED"}
                      {this.state.gmApproval && this.state.gmApproval.approval === "Rejected" && "REJECTED"}
                      {(
                            <div className="flex justify-content-evenly">
                              {(this.state.fmApproval) && (this.state.fmApproval.approval === "Approved") && (this.state.requester_role === 'approve') && Object.keys(this.state.gmApproval).length === 0 ? (
                                <div className="flex justify-content-evenly">
                                  <div className="m-2">
                                    <button
                                      onClick={() =>
                                        this.onApprovalApprove(
                                          "general_manager",
                                          this.state.username,
                                          "Approved",
                                          ""
                                        )
                                      }
                                      name="save_next"
                                      className="rounded-md bg-blue-925 hover:bg-blue-550 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
                                    >
                                      APPROVE
                                    </button>
                                  </div>
                                  <div className="m-2">
                                    <button
                                      onClick={() =>
                                        this.onApprovalJustificationModal(this.state.username, "general_manager")
                                      }
                                      name="save_next"
                                      className="rounded-md bg-blue-925 hover:bg-blue-550 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
                                    >
                                      REJECT
                                    </button>
                                  </div>
                                </div>
                              ) : (
                                ""
                              )}
                            </div>
                          )
                    }
                    </td>
                    <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                      {this.state.gmApproval && this.state.gmApproval.approval_date ? this.state.gmApproval.approval_date.split(".")[0] : ""}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    );

    var csDetailsView = (  
    <div className="px-4 sm:px-0 mt-6 bg-gulf-blue-300 rounded-md border-t border-gray-100 border-gray-900/10">
      <h2 className="text-base font-semibold leading-6 text-gray-900">
        COMPERATIVE SCHEDULE DETAILS
      </h2>

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
              disabled={(this.state.username === this.state.cs_owner) || (this.state.cs_owner === "") ? false : true}
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
              disabled={(this.state.username === this.state.cs_owner) || (this.state.cs_owner === "") ? false : true}
              id="pr_number"
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
              disabled={(this.state.username === this.state.cs_owner) || (this.state.cs_owner === "") ? false : true}
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
              disabled={(this.state.username === this.state.cs_owner) || (this.state.cs_owner === "") ? false : true}
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
                  name="closing_time"
                  onChange={(e) =>
                    this.onSelectChange("closing_time", e)
                  }
                  disabled={(this.state.username === this.state.cs_owner) || (this.state.cs_owner === "") ? false : true}
                  className="rounded-md block border-none w-full py-1.5 text-gray-900 sm:max-w-xs sm:text-sm sm:leading-6"
                >
                  {this.state.closing_time ? (
                    <option value={this.state.closing_time}>
                      {this.state.closing_time}
                    </option>
                  ) : ( 
                    <option value="">Select Closing Time</option>
                  )}
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
                onChange={(e) => this.onSelectChange("proc_ref", e)}
                disabled={(this.state.username === this.state.cs_owner) || (this.state.cs_owner === "") ? false : true}
                className="block w-full rounded-md border-0 py-1.5 px-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6 chzn-select"
              >
                {this.state.proc_plan ? (
                  <option value={this.state.proc_plan.proc_ref}>
                    {this.state.proc_plan.description}
                  </option>
                ) : (
                  ""
                )}
                {this.state.proc_plans
                  ? this.state.proc_plans.map((plan) => (
                      <option value={plan.proc_ref}>
                        {plan.description}
                      </option>
                    ))
                  : ""}
              </select>
            </div>
        </div>
        <div className="flex-1 w-20 ml-1">
            <label
              htmlFor="currency"
              className="block text-sm font-medium leading-6 text-gray-900"
            >
              Currency
            </label>
            <div className="mt-2">
              <select
                id="currency"
                name="currency"
                autoComplete="currency"
                onChange={(e) => this.onSelectChange("currency", e)}
                disabled={(this.state.username === this.state.cs_owner) || (this.state.cs_owner === "") ? false : true}
                className="block w-full rounded-md border-0 py-1.5 px-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6 chzn-select"
              >
                {this.state.currency ? (
                  <option value={this.state.currency.id}>
                    {this.state.currency.currency}
                  </option>
                ) : (
                  <option value="">Select Currency</option>
                )}
                {this.state.currencies
                  ? this.state.currencies.map((currency) => (
                      <option value={currency.id}>
                        {currency.currency}
                      </option>
                    ))
                  : ""}
              </select>
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
              name="ref_date"
              value={this.state.ref_date}
              onChange={this.onInputChange}
              disabled={(this.state.username === this.state.cs_owner) || (this.state.cs_owner === "") ? false : true}
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
              disabled={(this.state.username === this.state.cs_owner) || (this.state.cs_owner === "") ? false : true}
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
              disabled={(this.state.username === this.state.cs_owner) || (this.state.cs_owner === "") ? false : true}
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
              disabled={(this.state.username === this.state.cs_owner) || (this.state.cs_owner === "") ? false : true}
              type="file"
              id="advert"
              required="required"
              readOnly
              className="block w-full rounded-md border-0 py-1.5 px-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
            />
          </div>
        </div>
        <div className="flex-1 w-40 ml-2">
          <label
            htmlFor="bid_document"
            className="block text-sm font-medium leading-6 text-gray-900"
          >
            Advert Document
          </label>
          <div className="mt-2">
            <a href={this.state.advert_url} rel="noopener noreferrer">
              View Advert Document
            </a>
          </div>
        </div>
      </div>
      <div className="flex justify-evenly mt-5  px-2 py-2 rounded-md">
        {(this.state.pr_attachments.length > 0) && this.state.pr_attachments.map((attachment, key) => {
          return (
            <div className="flex-1 w-20 ml-1">
              <div className="mt-2">
                <div className="rounded bg-white border border-1 shadow-lg text-center m-2">
                    <a href={attachment.attachment_url}
                        className="text-center text-blue-600  p-3 sm whitespace-normal max-w-full">{ attachment.name }</a>
                </div>
              </div>
            </div>
          )
        })
        }
      </div>
      
      {(this.state.username === this.state.cs_owner ||
      !this.state.cs_id) && !this.state.approvalsComplete ? (
        <div className="flex justify-center mt-10 px-3 py-3">
          {this.state.cs_id ? (
            <div className="w-30 m-2">
              <button
                style={{ width: "100%" }}
                onClick={this.onUpdateSchedule}
                name="save_next"
                className="rounded-md bg-blue-925 hover:bg-blue-550 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
              >
                UPDATE SCHEDULE
              </button>
            </div>
          ) : (
            <div className="w-30 m-2">
              <button
                style={{ width: "100%" }}
                onClick={this.onSaveSchedule}
                name="save_next"
                className="rounded-md bg-blue-925 hover:bg-blue-550 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
              >
                SAVE SCHEDULE
              </button>
            </div>
          )}
        </div>
      ) : (
        ""
      )}
    </div>
    )

    return (
      <div>
        {itemsModal}
        {bidsModal}
        {supplierModal}
        {updateBidModal}
        {rejectJustification}
        {rejectApprovalJustification}
        <div className="space-y-12 px-5 py-5">
          <div className="px-4 sm:px-0">
            <h3 className="text-base font-semibold leading-7 text-gray-900">
              COMPARATIVE SCHEDULE
            </h3>
            <p className="mt-1 max-w-2xl text-sm leading-6 text-gray-500">
              CS NO: {this.state.cs_id}
            </p>
            {this.state.fetchPR && (
              <div>
              <div className="m-2">
            <button
              style={{ width: "100%" }}
              onClick={this.onAddSuppliersModal}
              className="rounded-md bg-nepal-950 hover:bg-nepal-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
            >
              ADD NEW SUPPLIER
            </button>
          </div>
              <div className="flex justify-evenly items-end mt-5 px-2 py-2">
              
              <div className="flex-1 w-40">
                <label
                  htmlFor="pr_number"
                  className="block text-sm font-medium leading-6 text-gray-900"
                >
                  Enter PR Number
                </label>
                <div className="mt-2">
                  <input
                    name="pr_number"
                    id="pr_number"
                    onChange={this.onFetchPrNumberChange}
                    defaultValue={this.state.pr_number}
                    className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                  />
                </div>
              </div>
              <div className="flex-1 ml-2 w-40">
                <div className="w-30">
                  <button
                    style={{ width: "100%" }}
                    onClick={() => this.onFetchPR(this.state.pr_number)}
                    name="save_next"
                    className="rounded-md bg-blue-925 hover:bg-blue-550 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
                  >
                    FETCH PR
                  </button>
                </div>
              </div>
            </div>
            </div>
            
            
      ) }
            {csDetailsView}
          </div>

          {this.state.username === this.state.cs_owner && this.state.bids.length < 1 ? (
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

          {this.state.bids && this.state.bids.map((bid, index) => {
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
                        <p>{bid.bid_count}</p>
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
                          href={bid.bid_document_url}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          View Document
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
                            <p>
                              {item.item_required}
                            </p>
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

                {this.state.username === this.state.cs_owner && !this.state.approvalsComplete ? (
                  <div className="flex justify-center mt-5 px-3 py-3">
                    <div className="m-2">
                      <button
                        onClick={() => this.onUpdateBidModal(bid.bid_count)}
                        className="rounded-md text-gray-50 text-sm bg-blue-925 hover:bg-blue-550 px-3 py-2 font-semibold leading-6"
                      >
                        UPDATE BID
                      </button>
                    </div>
                    <div className="m-2">
                      <button
                        onClick={() =>
                          this.onDeleteBidModal(
                            bid.bid_count,
                            bid.supplier_name
                          )
                        }
                        type="submit"
                        className="rounded-md bg-red-danger hover:bg-orange-500 text-sm font-semibold px-3 py-2 text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
                      >
                        DELETE BID
                      </button>
                    </div>
                  </div>
                ) : (
                  ""
                )}
              </div>
            );
          })}

          {this.state.cs_items.length > 0 &&
          this.state.username === this.state.cs_owner && !this.state.approvalsComplete ? (
            <div className="m-2">
              <button
                style={{ width: "100%" }}
                onClick={this.onAddBidModal}
                className="rounded-md bg-nepal-950 hover:bg-nepal-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
              >
                ADD BID
              </button>
            </div>
          ) : (
            ""
          )}

          {this.state.bids.length > 0 &&
          this.state.compliance.length < 1 &&
          this.state.username === this.state.cs_owner && !this.state.approvalsComplete ? (
            <div className="m-2">
              <button
                style={{ width: "100%" }}
                onClick={this.onAddComplianceTable}
                className="rounded-md bg-nepal-950 hover:bg-nepal-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
              >
                ADD COMPLIANCES
              </button>
            </div>
          ) : (
            ""
          )}

          {this.state.compliance.length > 0 ? complianceTable : ""}

          {this.state.compliance.length > 0 &&
          this.state.username === this.state.cs_owner && !this.state.approvalsComplete ? (
            <div className="m-2">
              <button
                style={{ width: "100%" }}
                onClick={this.onCloseCS}
                className="rounded-md bg-nepal-950 hover:bg-nepal-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
              >
                RANK BIDS
              </button>
            </div>
          ) : (
            ""
          )}

          {this.state.rankings.length > 0 ? rankingTable : ""}

          {this.state.rankings.length > 0 ? committeeTable : ""}

          {this.state.committeeMembers.length > 0 &&
          this.state.username === this.state.cs_owner && !this.state.approvalsComplete ? (
            <div className="m-2">
              <button
                style={{ width: "100%" }}
                onClick={this.onSubmitCommitee}
                className="rounded-md bg-nepal-950 hover:bg-nepal-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
              >
                SUBMIT COMMITTEE
              </button>
            </div>
          ) : (
            ""
          )}
          {this.state.committeeMembers.length > 2 ? approvalsTable : ""}

          <div className="m-2">
              <button
                style={{ width: "100%" }}
                onClick={() => {
                  console.log("going back ...")
                  window.history.back();
                }}
                className="rounded-md bg-nepal-950 hover:bg-nepal-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
              >
                GO BACK TO SCHEDULES
              </button>
            </div>
        </div>
      </div>
    );
  }
}

const username = domContainer.getAttribute("data-username");
const prid = domContainer.getAttribute("data-prid");
const csid = domContainer.getAttribute("data-csid");
ReactDOM.render(e(CreateCS, { username, prid, csid }), domContainer);