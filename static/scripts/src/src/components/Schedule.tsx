import React, { useEffect, useState } from "react";
import Select, { GroupBase, StylesConfig } from "react-select";

interface ICurrency {
  id: number;
  currency?: string;
}

// interface ICsProcPlan {
//     id: string;
//     name: string;
// }

interface IProcPlan {
  id: number;
  proc_ref: string;
  description: string;
}

interface IPRAttachment {
  id: number;
  attachment_url: string;
  file: string;
  name: string;
}

interface IBid {
  id?: number;
  supplier?: string;
  supplier_name?: string;
  bid_date?: string;
  encoded_bid_document?: string;
  bid_document?: File | null;
  bid_document_url?: string;
  bid_count?: number;
  items?: IBidItem[];
}

interface IBidItem {
  id?: number;
  item_required?: string;
  unit_of_measurement?: string;
  vat?: string;
  quantity?: number;
  total_price?: number;
  unit_price?: number;
  ordered?: boolean;
}

interface ICompliance {
  supplier_name?: string;
  supplier?: string;
  bid_no?: number;
  payment_terms?: boolean;
  bid_validity?: boolean;
  delivery_period?: boolean;
  technical_specifications?: boolean;
  valid_tax_clearance?: boolean;
  registered_with_praz?: boolean;
  site_visit?: boolean;
  samples_required?: boolean;
  decision?: boolean;
  reject?: boolean;
  [key: string]: unknown; // Add an index signature to allow dynamic properties
}

interface IComplianceRemark {
  id?: number;
  remarks?: string;
  supplier_name?: string;
  bid_no?: number;
  [key: string]: any; // Add an index signature to allow dynamic properties
}

interface IRank {
  id: number;
  supplier_name: string;
  rank: number;
  decision: string;
  remarks: string;
  total: number;
}

interface ICommittee {
  memberUserName: string;
  memberName: string;
  memberPosition?: string;
  committeeStatus?: string;
  memberApproval?: string;
  committeeJustification?: string;
  committeeDate?: string;
}

interface IMember {
  memberName: string;
  memberUserName: string;
  memberPosition?: string;
  memberApproval?: string;
}

interface IGmApproval {
  id: number;
  approver_name: string;
  approval: string;
  approval_date: string;
  justification: string;
}

interface IFmApproval {
  id: number;
  approver_name: string;
  approval: string;
  approval_date: string;
  justification: string;
}

interface IUser {
  id: number;
  username: string;
  role: string;
  first_name: string;
  last_name: string;
}

// interface IMemberOptions {
//   value: string;
//   label: string;
// }

interface ICurrentApprover {
  username?: string;
  justification?: string;
  role?: string;
}

interface IPrItems {
  id?: number;
  item_required?: string;
  quantity?: number;
  unit_of_measurement?: string;
  ordered?: boolean;
}

interface ISupplier {
  id?: number;
  supplier_name?: string;
  name?: string;
}

interface IUom {
  id?: number;
  name: string;
}

interface IResponse {
  open: boolean;
  message: string;
  title: string;
  success: boolean;
}

interface IUserOptions {
  value: string;
  label: string;
}

// interface IScheduleDetails {
//   requester_role: string;
//   cs_id: string;
//   cs_owner: string;
//   creator: string;
//   pr_id: string;
//   pr_number: string;
//   pr_date: string;
//   additional_notes: string;
//   scope_of_work: string;
//   closing_date: string;
//   closing_time: string;
//   advert: string;
//   ref_date: string;
//   cs_opened: string;
//   tac_date: string;
//   show_site_visit: string;
//   show_samples_required: string;
//   created_by: string;
//   section: string;
//   region: string;
//   created_at: string;
// }

export default function Schedule({
  base_url,
  username_,
  prid,
  csid,
}: {
  base_url: string;
  username_: string | null;
  prid: string | null;
  csid: string | null;
}) {
  //   const [loading, setLoading] = useState<boolean>(false);
  const [requesterRole, setRequesterRole] = useState<string>("");
  const [csId, setCsId] = useState<string>("");
  const [csOwner, setCsOwner] = useState<string>("");
  const [creator, setCreator] = useState<string>("");
  const [createdAt, setCreatedAt] = useState<string>("");
  const [committeeApprovalComplete, setCommitteeApprovalComplete] =
    useState<boolean>(false);
  //   const [planRef, setPlanRef] = useState<string>("");
  const [procRef, setProcRef] = useState<string>("");
  const [currency, setCurrency] = useState<ICurrency>();
  const [currencies, setCurrencies] = useState<ICurrency[]>();
  const [procPlan, setProcPlan] = useState<IProcPlan>();
  const [scopeOfWork, setScopeOfWork] = useState<string>("");
  const [prNumber, setPrNumber] = useState<string>("");
  const [prAttachments, setPrAttachments] = useState<IPRAttachment[]>();
  const [quantity, setQuantity] = useState<string>("");
  const [prDate, setPrDate] = useState<string>("");
  const [closingDate, setClosingDate] = useState<string>("");
  const [closingTime, setClosingTime] = useState<string>("");
  const [refDate, setRefDate] = useState<string>("");
  const [dateTenderOpened, setDateTenderOpened] = useState<string>("");
  const [tenderAdjudicationCommitteeDate, setTenderAdjudicationCommitteeDate] =
    useState<string>("");
  const [advert, setAdvert] = useState<File>();
  const [advertUrl, setAdvertUrl] = useState<string>();
  const [bidCount, setBidCount] = useState<number>(0);
  const [currentBid, setCurrentBid] = useState<IBid>();
  const [bids, setBids] = useState<IBid[]>();
  const [addBidModal, setAddBidModal] = useState<boolean>(false);
  const [updateBidModal, setUpdateBidModal] = useState<boolean>(false);
  const [csItems, setCsItems] = useState<IBidItem[]>();
  const [csItemCount, setCsItemCount] = useState<number>();
  const [addItemsModal, setAddItemsModal] = useState<boolean>(false);
  const [complianceTable, setComplianceTable] = useState<boolean>(false);
  const [compliance, setCompliance] = useState<ICompliance[]>();
  const [complianceRemarks, setComplianceRemarks] =
    useState<IComplianceRemark[]>();
  const [showSamples, setShowSamples] = useState<string>("no");
  const [showSiteVisit, setShowSiteVisit] = useState<string>("no");
  //   const [rankingTable, setRankingTable] = useState<boolean>(false);
  const [rankings, setRankings] = useState<IRank[]>();
  //   const [committeeTable, setCommitteeTable] = useState<boolean>(false);
  const [committeeMembers, setCommitteeMembers] = useState<ICommittee[]>();
  const [committeeJustificationModal, setCommitteeJustificationModal] =
    useState<boolean>(false);
  const [member, setMember] = useState<IMember>();
  const [gmApproval, setGmApproval] = useState<IGmApproval>();
  const [fmApproval, setFmApproval] = useState<IFmApproval>();
  const [approvalsComplete, setApprovalsComplete] = useState<boolean>(false);
  const [approvalsJustificationModal, setApprovalsJustificationModal] =
    useState<boolean>(false);
  const [users, setUsers] = useState<IUser[]>();
  //   const [selectUserOptions, setSelectUserOptions] = useState<IMemberOptions[]>([
  //     { value: "chairman", label: "Chairman" },
  //     { value: "finance", label: "Finance" },
  //     { value: "procurement", label: "Procurement" },
  //     { value: "user", label: "User" },
  //     { value: "other", label: "Other" },
  //   ]);
  const [searchedUser, setSearchedUser] = useState<string>("");
  //   const [selectedUser, setSelectedUser] = useState<IUser>();
  const [filteredUsers, setFilteredUsers] = useState<IUser[]>();
  const [currentApprover, setCurrentApprover] = useState<ICurrentApprover>();
  const [prItems, setPrItems] = useState<IPrItems[]>();
  const [suppliers, setSuppliers] = useState<ISupplier[]>();
  const [procPlans, setProcPlans] = useState<IProcPlan[]>();
  const [uom, setUom] = useState<IUom[]>();
  //   const [authUser, setAuthUser] = useState<IUser>();
  const [username, setUsername] = useState<string>("");
  const [fetchPR, setFetchPR] = useState<boolean>(false);
  const [onAddSupplier, setOnAddSupplier] = useState<boolean>(false);
  const [newSupplier, setNewSupplier] = useState<ISupplier>();
  const [response, setResponse] = useState<IResponse>();
  const [additionalNotes, setAdditionalNotes] = useState<string>("");
  const [buyersNotes, setBuyersNotes] = useState<string>("");
  const [directPurchaseLimit, setDirectPurchaseLimit] = useState<boolean>(true)

  useEffect(() => {
    if (csid) {
      setCsId(csid);
      setUsername(username_ ?? "");
      // get data
      getCSData(csid);
    } else if (prid) {
      setUsername(username_ ?? "");
      setPrNumber(prid ?? "");
      // get data
      getCreateData(prid);
    } else {
      setUsername(username_ ?? "");
      setFetchPR(true);
    }
  }, [username_, csid, prid]);

  const userOptions: IUserOptions[] | undefined = users?.map((user) => {
    return {
      value: user.username,
      label: user.first_name + " " + user.last_name + ":- " + user.username,
    };
  });

  const customStyles: StylesConfig<
    IUserOptions,
    false,
    GroupBase<IUserOptions>
  > = {
    control: (provided) => ({
      ...provided,
      backgroundColor: "white",
      borderColor: "gray",
      minHeight: "40px",
      height: "40px",
      boxShadow: "none",
    }),
    valueContainer: (provided) => ({
      ...provided,
      height: "40px",
      padding: "0 6px",
    }),
    input: (provided) => ({
      ...provided,
      margin: "0px",
    }),
    indicatorSeparator: () => ({
      display: "none",
    }),
    indicatorsContainer: (provided) => ({
      ...provided,
      height: "40px",
    }),
    menu: (provided) => ({
      ...provided,
      zIndex: 9999,
      height: "200px",
    }),
    option: (provided, state) => ({
      ...provided,
      backgroundColor: state.isSelected ? "lightgray" : "white",
      color: "black",
      "&:hover": {
        backgroundColor: "lightblue",
      },
    }),
  };

  const onSetDirectPurchaseLimit = () => {
    onSetDirectPurchaseLimit()
  }

  const onGetFileObjectUrl = (fileData: string | File | undefined) => {
    try {
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
        return fileData ? URL.createObjectURL(fileData) : undefined;
      }
    } catch (err) {
      console.log("error: ", err);
    }
  };

  const getCSData = (cs_id: string) => {
    fetch(`${base_url}/cs_data/${cs_id}`)
      .then((response) => response.json())
      .then((data_) => {
        const data: object = JSON.parse(data_);
        console.log("cs data: ", data, typeof data);
        const requester_role: string | undefined = (
          data as { requester_role?: string }
        ).requester_role
          ? (data as { requester_role?: string }).requester_role
          : "";
        setRequesterRole(requester_role ?? "");
        const creator = (data as { creator?: string }).creator
          ? (data as { creator?: string }).creator
          : "";
        setCreator(creator ?? "");
        const created_at = (data as { created_at?: string }).created_at
          ? (data as { created_at?: string }).created_at
          : "";
        setCreatedAt(created_at ?? "");
        const bids_object: IBid[] | undefined = (data as { bids?: IBid[] }).bids
          ? (data as { bids?: IBid[] }).bids
          : [];
        let bids: IBid[] = [];
        if (bids_object && bids_object.length !== 0) {
          bids = Object.keys(bids_object).map((key: string) => {
            const new_obj: IBid = bids_object[parseInt(key)];
            return {
              ...new_obj,
              bid_document_url:
                onGetFileObjectUrl(new_obj.encoded_bid_document ?? undefined) ??
                "",
            };
          });
        }
        const sorted_bids: IBid[] = bids.sort(
          (a: IBid, b: IBid) => (a.bid_count ?? 0) - (b?.bid_count ?? 0)
        );
        setBids(sorted_bids);
        const bid_count: number = bids?.length ?? 0;
        setBidCount(bid_count);
        
        if(base_url === "/direct_purchase"){
            const limit: boolean = bids?.length??0 >= 1 ? false : true;
            setDirectPurchaseLimit(limit)
        }

        const compliance = (data as { compliance?: ICompliance[] }).compliance
          ? (data as { compliance?: ICompliance[] }).compliance
          : [];
        setCompliance(compliance);
        const complianceRemarks = (
          data as { compliance_remarks?: IComplianceRemark[] }
        ).compliance_remarks
          ? (data as { compliance_remarks?: IComplianceRemark[] })
              .compliance_remarks
          : [];
        setComplianceRemarks(complianceRemarks);
        const rankings = (data as { rankings?: IRank[] }).rankings
          ? (data as { rankings?: IRank[] }).rankings
          : [];
        if (rankings) {
          rankings.sort((a: IRank, b: IRank) => a.rank - b.rank);
        }
        setRankings(rankings);
        const committee = (data as { committee?: ICommittee[] }).committee
          ? (data as { committee?: ICommittee[] }).committee
          : [];
        setCommitteeMembers(committee);
        const gm_approval = (data as { gm_approval?: IGmApproval }).gm_approval
          ? (data as { gm_approval?: IGmApproval }).gm_approval
          : null;
        setGmApproval(gm_approval ?? undefined);
        const fm_approval = (data as { fm_approval?: IFmApproval }).fm_approval
          ? (data as { fm_approval?: IFmApproval }).fm_approval
          : null;
        setFmApproval(fm_approval ?? undefined);
        const pr_date = (data as { pr_date?: string }).pr_date
          ? (data as { pr_date?: string }).pr_date
          : "";
        setPrDate(pr_date ?? "");
        const proc_ref = (data as { proc_ref?: string }).proc_ref
          ? (data as { proc_ref?: string }).proc_ref
          : "";
        setProcRef(proc_ref ?? "");
        const proc_plan = (data as { proc_plan?: IProcPlan }).proc_plan
          ? (data as { proc_plan?: IProcPlan }).proc_plan
          : undefined;
        setProcPlan(proc_plan);
        const scope_of_work = (data as { scope_of_work?: string }).scope_of_work
          ? (data as { scope_of_work?: string }).scope_of_work
          : "";
        setScopeOfWork(scope_of_work ?? "");
        const pr_number = (data as { pr_number?: string }).pr_number
          ? (data as { pr_number?: string }).pr_number
          : "";
        setPrNumber(pr_number ?? "");
        const quantity = (data as { quantity?: string }).quantity
          ? (data as { quantity?: string }).quantity
          : "";
        setQuantity(quantity ?? "");
        const closing_date = (data as { closing_date?: string }).closing_date
          ? (data as { closing_date?: string }).closing_date
          : "";
        setClosingDate(closing_date ?? "");
        const ref_date = (data as { ref_date?: string }).ref_date
          ? (data as { ref_date?: string }).ref_date
          : "";
        setRefDate(ref_date ?? "");
        const closing_time = (data as { closing_time?: string }).closing_time
          ? (data as { closing_time?: string }).closing_time
          : "";
        setClosingTime(closing_time ?? "");
        const tender_adjudication_committee_date = (
          data as { tac_date?: string }
        ).tac_date
          ? (data as { tac_date?: string }).tac_date
          : "";
        setTenderAdjudicationCommitteeDate(
          tender_adjudication_committee_date ?? ""
        );
        const cs_opened = (data as { cs_opened?: string }).cs_opened
          ? (data as { cs_opened?: string }).cs_opened
          : "";
        setDateTenderOpened(cs_opened ?? "");
        const additionalNotes = (data as { additional_notes?: string })
          .additional_notes
          ? (data as { additional_notes?: string }).additional_notes
          : "";
        setAdditionalNotes(additionalNotes ?? "");
        const buyersNotes = (data as { buyers_notes?: string }).buyers_notes
          ? (data as { buyers_notes?: string }).buyers_notes
          : "";
        setBuyersNotes(buyersNotes ?? "");

        const proc_plans = (data as { proc_plans?: IProcPlan[] }).proc_plans
          ? (data as { proc_plans?: IProcPlan[] }).proc_plans
          : [];
        setProcPlans(proc_plans);
        const uom = (data as { uom?: IUom[] }).uom
          ? (data as { uom?: IUom[] }).uom
          : undefined;
        setUom(uom);
        const suppliers_ = (data as { suppliers?: ISupplier[] }).suppliers
          ? (data as { suppliers?: ISupplier[] }).suppliers
          : [];
        setSuppliers(suppliers_);
        const pr_items = (data as { pr_items?: IPrItems[] }).pr_items
          ? (data as { pr_items?: IPrItems[] }).pr_items
          : [];
        setPrItems(pr_items);
        const pr_attachments = (data as { pr_attachments?: IPRAttachment[] })
          .pr_attachments
          ? (data as { pr_attachments?: IPRAttachment[] }).pr_attachments
          : [];
        setPrAttachments(pr_attachments);
        const cs_items = (data as { cs_items?: IBidItem[] }).cs_items
          ? (data as { cs_items?: IBidItem[] }).cs_items
          : [];
        setCsItems(cs_items as IBidItem[] | undefined);
        const users = (data as { users?: IUser[] }).users
          ? (data as { users?: IUser[] }).users
          : [];
        users?.sort((user1, user2) => {
          const fullName1 = user1.first_name + " " + user1.last_name;
          const fullName2 = user2.first_name + " " + user2.last_name;
          return fullName1.localeCompare(fullName2);
        });
        setUsers(users);
        const cs_owner = (data as { cs_owner?: string }).cs_owner
          ? (data as { cs_owner?: string }).cs_owner
          : "";
        setCsOwner(cs_owner ?? "");
        const currencies = (data as { currencies?: ICurrency[] }).currencies
          ? (data as { currencies?: ICurrency[] }).currencies
          : [];
        setCurrencies(currencies);
        const currency = (data as { currency?: ICurrency }).currency
          ? (data as { currency?: ICurrency }).currency
          : undefined;
        setCurrency(currency);
        const advert = (data as { advert?: string }).advert
          ? (data as { advert?: string }).advert
          : "";
        const advert_url = onGetFileObjectUrl(advert ?? "");
        setAdvertUrl(advert_url);
        let pr_at_list: IPRAttachment[] = [];
        if (pr_attachments && pr_attachments.length > 0) {
          pr_at_list = pr_attachments.map((pr_attachment) => {
            return {
              ...pr_attachment,
              attachment_url: onGetFileObjectUrl(pr_attachment.file) ?? "",
            };
          });
        }
        setPrAttachments(pr_at_list);

        const committeeApprovalComplete =
          committee?.filter(
            (member) =>
              member.memberApproval === "" ||
              member.memberApproval === null ||
              member.memberApproval === undefined ||
              member.memberApproval === "Rejected"
          ).length === 0;
        setCommitteeApprovalComplete(committeeApprovalComplete);

        const approvalsComplete =
          gm_approval?.approval !== "" &&
          fm_approval?.approval !== "" &&
          gm_approval?.approval !== undefined &&
          fm_approval?.approval !== undefined;
        setApprovalsComplete(approvalsComplete);

        const showSiteVisit =
          (data as { show_site_visit?: boolean }).show_site_visit === true
            ? "yes"
            : "no";
        setShowSiteVisit(showSiteVisit);
        const showSamples =
          (data as { show_samples_required?: boolean })
            .show_samples_required === true
            ? "yes"
            : "no";
        setShowSamples(showSamples);
      })
      .catch((error) => console.log("error: ", error));
  };

  const getCreateData = (pr_id: string) => {
    console.log("cs pr_id: ", pr_id);

    fetch(`${base_url}/create_data/${pr_id}`)
      .then((response) => response.json())
      .then((data) => {
        console.log("data: ", data);
        const scope_of_work = (data as { scope_of_work?: string }).scope_of_work
          ? (data as { scope_of_work?: string }).scope_of_work
          : "";
        setScopeOfWork(scope_of_work ?? "");
        const proc_ref = (data as { proc_ref?: string }).proc_ref
          ? (data as { proc_ref?: string }).proc_ref
          : "";

        setProcRef(proc_ref ?? "");
        const plans = (data as { proc_plans?: IProcPlan[] }).proc_plans
          ? (data as { proc_plans?: IProcPlan[] }).proc_plans
          : [];
        setProcPlans(plans);
        const uom = (data as { uom?: IUom[] }).uom
          ? (data as { uom?: IUom[] }).uom
          : undefined;
        setUom(uom);
        const suppliers = (data as { suppliers?: ISupplier[] }).suppliers
          ? (data as { suppliers?: ISupplier[] }).suppliers
          : [];
        setSuppliers(suppliers);
        const pr_items = (data as { pr_items?: IPrItems[] }).pr_items
          ? (data as { pr_items?: IPrItems[] }).pr_items
          : [];
        setPrItems(pr_items);
        const pr_attachments = (data as { pr_attachments?: IPRAttachment[] })
          .pr_attachments
          ? (data as { pr_attachments?: IPRAttachment[] }).pr_attachments
          : [];
        setPrAttachments(pr_attachments);
        const pr_id = (data as { pr_id?: string }).pr_id
          ? (data as { pr_id?: string }).pr_id
          : "";
        setPrNumber(pr_id ?? "");
        const pr_date = (data as { pr_date?: string }).pr_date
          ? (data as { pr_date?: string }).pr_date
          : "";
        setPrDate(pr_date ?? "");
        const users = (data as { users?: IUser[] }).users
          ? (data as { users?: IUser[] }).users
          : [];
        const currencies = (data as { currencies?: ICurrency[] }).currencies
          ? (data as { currencies?: ICurrency[] }).currencies
          : [];
        // Sort users by full name (first_name + " " + last_name)
        users?.sort((user1, user2) => {
          const fullName1 = user1.first_name + " " + user1.last_name;
          const fullName2 = user2.first_name + " " + user2.last_name;
          return fullName1.localeCompare(fullName2);
        });
        setUsers(users);
        setCurrencies(currencies);
        let pr_at_list: IPRAttachment[];
        if (pr_items && pr_items.length === 0) {
          pr_at_list =
            pr_attachments?.map((pr_attachment) => {
              return {
                ...pr_attachment,
                attachment_url: onGetFileObjectUrl(pr_attachment.file) ?? "",
              };
            }) ?? [];
          setPrAttachments(pr_at_list);
        }
      })
      .catch((error) => console.log("error: ", error));
  };

  const onFetchPR = (pr_id: string) => {
    console.log("cs pr_id: ", pr_id);

    fetch(`${base_url}/create_data/${pr_id}`)
      .then((response) => response.json())
      .then((data) => {
        console.log("data: ", data);
        if (data && data.success) {
          const pr_items = (data as { pr_items?: IPrItems[] }).pr_items
            ? (data as { pr_items?: IPrItems[] }).pr_items
            : undefined;
          if (!pr_items || pr_items?.length < 1) {
            // set response message
            onOpenResponse(
              "Fetch PR Error",
              "This Purchase Request is either empty or has no items. Please check and try again.",
              false
            );
            return;
          }
          setPrItems(pr_items);
          const scope_of_work = (data as { scope_of_work?: string })
            .scope_of_work
            ? (data as { scope_of_work?: string }).scope_of_work
            : "";
          setScopeOfWork(scope_of_work ?? "");
          const proc_ref = (data as { proc_ref?: string }).proc_ref
            ? (data as { proc_ref?: string }).proc_ref
            : "";
          setProcRef(proc_ref ?? "");
          const proc_plan = (data as { proc_plan?: IProcPlan }).proc_plan
            ? (data as { proc_plan?: IProcPlan }).proc_plan
            : undefined;
          setProcPlan(proc_plan);
          const plans = (data as { proc_plans?: IProcPlan[] }).proc_plans
            ? (data as { proc_plans?: IProcPlan[] }).proc_plans
            : [];
          setProcPlans(plans);
          const currencies = (data as { currencies?: ICurrency[] }).currencies
            ? (data as { currencies?: ICurrency[] }).currencies
            : [];
          setCurrencies(currencies);
          const uom = (data as { uom?: IUom[] }).uom
            ? (data as { uom?: IUom[] }).uom
            : undefined;
          setUom(uom);
          const suppliers = (data as { suppliers?: ISupplier[] }).suppliers
            ? (data as { suppliers?: ISupplier[] }).suppliers
            : [];
          setSuppliers(suppliers);
          const pr_attachments = (data as { pr_attachments?: IPRAttachment[] })
            .pr_attachments
            ? (data as { pr_attachments?: IPRAttachment[] }).pr_attachments
            : [];
          const pr_id = (data as { pr_id?: string }).pr_id
            ? (data as { pr_id?: string }).pr_id
            : "";
          setPrNumber(pr_id ?? "");
          const pr_date = (data as { pr_date?: string }).pr_date
            ? (data as { pr_date?: string }).pr_date
            : "";
          setPrDate(pr_date ?? "");
          const users = (data as { users?: IUser[] }).users
            ? (data as { users?: IUser[] }).users
            : [];
          setUsers(users);
          let pr_at_list: IPRAttachment[];
          if (pr_attachments && pr_attachments.length > 0) {
            pr_at_list =
              pr_attachments?.map((pr_attachment) => {
                return {
                  ...pr_attachment,
                  attachment_url: onGetFileObjectUrl(pr_attachment.file) ?? "",
                };
              }) ?? undefined;
            setPrAttachments(pr_at_list);
          }
          setFetchPR(false);

          onOpenResponse(
            "Fetch PR Success",
            "Purchase Request fetched successfully",
            true
          );
        } else {
          onOpenResponse(
            "Fetch PR Error",
            "PR Number not found. Please try again.",
            false
          );
        }
      })
      .catch((error) => console.log("error: ", error));
  };

  const onFetchPrNumberChange = (event: {
    target: { name: string; value: string };
  }) => {
    const { value } = event.target;
    setPrNumber(value);
  };

  const onCommitteeChange = (
    name_: string,
    event: { target: { name: string; value: string } }
  ) => {
    const { value } = event.target;
    console.log("name: ", name_, "value: ", value);
    let memberNames: string;
    let memberValue: string;
    if (name_ === "memberUserName") {
      const user = users?.find((user) => user.username === value);
      memberNames = user?.first_name + " " + user?.last_name;
      //   member_[name_] = value;
      memberValue = value;
      const thisMember: IMember = {
        memberName: memberNames,
        memberUserName: memberValue,
        ...member,
      };
      setMember(thisMember);
    } else if (name_ === "memberPosition") {
      // member_[name_] = value;
      memberValue = value;
      const thisMember: IMember = {
        ...member,
        memberName: member?.memberName ?? "",
        memberUserName: member?.memberUserName ?? "",
        memberPosition: memberValue ?? undefined,
      };
      setMember(thisMember);
    } else {
      // member_[name_] = value;
      memberValue = value;
      const thisMember: IMember = {
        memberUserName: memberValue ?? "",
        memberName: member?.memberName ?? "",
        ...member,
      };
      setMember(thisMember);
    }
  };

  const onCommitteeSelect = (name_: string, username: string) => {
    console.log(filteredUsers, onSearchUser, searchedUser);
    let fullname: string = "";
    let memberName: string = "";
    let memberUserName: string = "";
    if (name_ === "memberUserName") {
      const user: IUser | undefined = users?.find(
        (user) => user.username === username
      );
      fullname = user?.first_name + " " + user?.last_name;
      memberName = fullname;
      memberUserName = username;
    }
    const thisMember: IMember = {
      ...member,
      memberName: memberName,
      memberUserName: memberUserName,
    };
    setMember(thisMember);
    setSearchedUser(fullname);
    // setSelectedUser(undefined);
    setFilteredUsers([]);
  };

  const onRemoveCommitteeMember = (index: number, username: string) => {
    const members = committeeMembers?.filter((_, _index) => _index !== index);
    if (
      members &&
      committeeMembers &&
      members.length < committeeMembers.length
    ) {
      setCommitteeMembers(members);
    }
    deleteCommitteeMember(username);
  };

  const deleteCommitteeMember = (username: string) => {
    const form_data: FormData = new FormData();
    form_data.append("cs_id", csId);
    form_data.append("username", username);
    form_data.append("csrfmiddlewaretoken", getCookie("csrftoken") ?? "");

    fetch(`${base_url}/delete_committee_member`, {
      method: "POST",
      headers: {
        "X-CSRFToken": getCookie("csrftoken") ?? "",
      },
      body: form_data,
    })
      .then((response) => response.json())
      .then((data) => {
        console.log("data: ", data);
        if (data.success) {
          onOpenResponse(
            "Remove Committee Member Success",
            "Committee member removed successfully",
            true
          );
        } else {
          onOpenResponse(
            "Remove Committee Member Error",
            "Error deleting Committee member",
            false
          );
        }
      });
  };

  const onCommitteeJustificationModal = (justification: string) => {
    setCurrentApprover({
      ...currentApprover,
      justification: justification,
      username: username,
    });
    setCommitteeJustificationModal(!committeeJustificationModal);
  };

  const onCommitteeJustificationModalClose = () => {
    setCurrentApprover({
      justification: "",
      username: "",
      role: "",
    });
    setCommitteeJustificationModal(!committeeJustificationModal);
  };

  const onCommitteeJustificationChange = (event: {
    target: { value: string };
  }) => {
    console.log("event: ", event);
    const { value } = event.target;
    const justification: string = value;
    setCurrentApprover({
      ...currentApprover,
      justification: justification,
    });
  };

  const onCommitteeApprove = (
    username: string,
    approval: string,
    justification: string
  ) => {
    const form_data: FormData = new FormData();
    console.log("approval: ", approval, justification);
    if (approval === "Rejected" && justification === "") {
      onOpenResponse(
        "Committee Member Approval Error",
        "Justification is required. Please add justification before submitting.",
        false
      );
      return;
    }
    form_data.append("cs_id", csId);
    form_data.append("username", username);
    form_data.append("approval", approval);
    form_data.append("justification", justification);
    form_data.append("csrfmiddlewaretoken", getCookie("csrftoken") ?? "");

    fetch(`${base_url}/committee_approve`, {
      method: "POST",
      headers: {
        "X-CSRFToken": getCookie("csrftoken") ?? "",
      },
      body: form_data,
    })
      .then((response) => response.json())
      .then((data) => {
        console.log("data: ", data);
        if (data.success) {
          const committeeDate = (data as { committee_date?: string })
            .committee_date
            ? (data as { committee_date?: string }).committee_date
            : "";
          const committeeApproval = (data as { committee_approval?: string })
            .committee_approval
            ? (data as { committee_approval?: string }).committee_approval
            : "";
          //   const memberName = (data as { member_name?: string }).member_name
          //     ? (data as { member_name?: string }).member_name
          //     : "";
          let members: ICommittee[] = [];
          if (committeeMembers && committeeMembers.length > 0) {
            members = committeeMembers.map((member) => {
              if (member.memberUserName === username) {
                member.committeeDate = committeeDate;
                member.memberApproval = committeeApproval;
              }
              return member;
            });
          }
          setCommitteeMembers(members);
          // @TODO: check committee approval value
          onOpenResponse(
            "Committee Member Approval Success",
            "You have successfully approved this schedule.",
            true
          );
          // reload page
          window.location.href = base_url + "/comperative_schedules";
        } else {
          onOpenResponse(
            "Committee Member Approval Error",
            "Failed to submit your approval please try again.",
            false
          );
        }
      })
      .catch((err) => console.log("onCommitteeApprove error: ", err));
  };

  const onSubmitCommitee = () => {
    const form_data: FormData = new FormData();
    form_data.append("cs_id", csId);
    form_data.append(
      "committee",
      JSON.stringify({
        committee: committeeMembers,
      })
    );
    form_data.append("csrfmiddlewaretoken", getCookie("csrftoken") ?? "");

    fetch(`${base_url}/save_committee`, {
      method: "POST",
      headers: {
        "X-CSRFToken": getCookie("csrftoken") ?? "",
      },
      body: form_data,
    })
      .then((response) => response.json())
      .then((data) => {
        console.log("data: ", data);
        if (data.success) {
          onOpenResponse(
            "Submit Committee Member Success",
            "You have successfully submitted this committee",
            true
          );
        } else {
          onOpenResponse(
            "Submit Committee Member Error",
            "Failed to submit this committee please try again",
            false
          );
        }
      });
  };

  const onApprovalApprove = (
    role: string,
    username: string,
    approval: string,
    justification: string
  ) => {
    console.log("approval: ", approval, justification);
    if (approval === "Rejected" && justification === "") {
      onOpenResponse(
        "Approval Error",
        "Justification is required. Please add justification before submitting.",
        false
      );
      return;
    }
    const form_data: FormData = new FormData();
    form_data.append("cs_id", csId);
    form_data.append("role", role);
    form_data.append("username", username);
    form_data.append("approval", approval);
    form_data.append("justification", justification);
    form_data.append("csrfmiddlewaretoken", getCookie("csrftoken") ?? "");

    fetch(`${base_url}/approval_approve`, {
      method: "POST",
      headers: {
        "X-CSRFToken": getCookie("csrftoken") ?? "",
      },
      body: form_data,
    })
      .then((response) => response.json())
      .then((data) => {
        console.log("data: ", data);
        if (data.success) {
          const role = (data as { role?: string }).role
            ? (data as { role?: string }).role
            : "";
          const approval = (data as { approval?: string }).approval
            ? (data as { approval?: string }).approval
            : "";
          if (role === "finance_manager") {
            const fm_approval = (data as { fm_approval?: IFmApproval })
              .fm_approval
              ? (data as { fm_approval?: IFmApproval }).fm_approval
              : undefined;
            setFmApproval(fm_approval);
          } else if (role === "general_manager") {
            const gm_approval = (data as { gm_approval?: IGmApproval })
              .gm_approval
              ? (data as { gm_approval?: IGmApproval }).gm_approval
              : undefined;
            setGmApproval(gm_approval);
          }
          if (approval === "Approved") {
            onOpenResponse(
              "Approval Success",
              "You have successfully approved this RFQ.",
              true
            );

            // reload page
            window.location.href = base_url + "/comperative_schedules";
          } else {
            onOpenResponse(
              "Approval Success",
              "You have successfully rejected this RFQ.",
              true
            );
            window.location.href = base_url + "/comperative_schedules";
          }
        } else {
          onOpenResponse(
            "Approval Error",
            "Failed to submit your approval. Please try again.",
            false
          );
        }
      });
  };

  const onApprovalJustificationModal = (username: string, role: string) => {
    setCurrentApprover({
      username: username,
      justification: "",
      role: role,
    });
    setApprovalsJustificationModal(!approvalsJustificationModal);
  };

  const onApprovalJustificationModalClose = () => {
    setCurrentApprover({
      username: "",
      justification: "",
      role: "",
    });
    setApprovalsJustificationModal(!approvalsJustificationModal);
  };

  const onSaveSupplier = () => {
    const form_data: FormData = new FormData();
    form_data.append("supplier_name", newSupplier?.supplier_name ?? "");
    form_data.append("csrfmiddlewaretoken", getCookie("csrftoken") ?? "");

    fetch(`${base_url}/save_supplier`, {
      method: "POST",
      headers: {
        "X-CSRFToken": getCookie("csrftoken") ?? "",
      },
      body: form_data,
    })
      .then((response) => response.json())
      .then((data) => {
        console.log("data: ", data);
        if (data.success) {
          onOpenResponse(
            "Add New Supplier Success",
            "New supplier added successfully",
            true
          );
          setOnAddSupplier(false);
          setNewSupplier({
            id: 0,
            name: "",
            supplier_name: "",
          });
          const suppliers_ = (data as { suppliers?: ISupplier[] }).suppliers
            ? (data as { suppliers?: ISupplier[] }).suppliers
            : [];
          setSuppliers(suppliers_);
        } else {
          onOpenResponse(
            "Add New Supplier Error",
            "Failed to add new supplier, please try again.",
            false
          );
        }
      });
  };

  const onApprovalJustificationChange = (event: {
    target: { value: string };
  }) => {
    console.log("event: ", event);
    const { value } = event.target;
    const justification = value;
    setCurrentApprover({
      ...currentApprover,
      justification: justification,
    });
  };

  const onAddCSItem = (item_id: number) => {
    // check is item already added
    const item = csItems?.find((item) => item.id === item_id);
    console.log("item: ", item);
    if (item) {
      // update item selected to false
      item.ordered = false;
      // update pr_items
      const pr_items = prItems?.map((_item) => {
        if (_item.id === item_id) {
          return {
            id: item.id,
            item_required: item.item_required,
            unit_of_measurement: item.unit_of_measurement,
            quantity: item.quantity,
            ordered: false,
          };
        }
        return _item;
      });
      // remove item
      const items = csItems?.filter((item) => item.id !== item_id);
      setCsItems(items);
      setPrItems(pr_items);
    } else {
      // find item in pr_items
      const prItem = prItems?.find((item) => item.id === item_id);
      // update pr_item selected to added
      if (!prItem) {
        return;
      }
      prItem.ordered = true;
      //   item.item_required = item.item_required;
      // update pr_items
      const pr_items = prItems?.map((_item) => {
        if (_item.id === item_id) {
          return prItem;
        }
        return _item;
      });

      const item_count = csItemCount ? csItemCount + 1 : 1;
      setCsItemCount(item_count);
      setCsItems([...(csItems ?? []), { ...prItem }]);
      setPrItems(pr_items);
    }
  };

  const onSubmitCSItems = () => {
    if (csItems && csItems.length === 0) {
      onOpenResponse(
        "Submit Schedule Items Error",
        "Please add items to the Comparative Schedule",
        false
      );
      return;
    }
    const form_data: FormData = new FormData();
    form_data.append("cs_id", csId);
    form_data.append("pr_id", prNumber);
    form_data.append(
      "json_data",
      JSON.stringify({
        cs_items: csItems,
      })
    );
    form_data.append("csrfmiddlewaretoken", getCookie("csrftoken") ?? "");

    fetch(`${base_url}/update_pritem_ordered`, {
      method: "POST",
      headers: {
        "X-CSRFToken": getCookie("csrftoken") ?? "",
      },
      body: form_data,
    })
      .then((response) => response.json())
      .then((data) => {
        console.log("data: ", data);
        if (data.success) {
          onOpenResponse(
            "Submit Schedule Items Success",
            "Items submitted successfully",
            true
          );
        } else {
          onOpenResponse(
            "Submit Schedule Items Error",
            "Failed to submit schedule items, please try again.",
            false
          );
        }
      });
    setAddItemsModal(false);
  };

  const onAddSuppliersModal = () => {
    setOnAddSupplier(!onAddSupplier);
  };

  const onSupplierChange = (event: {
    target: { name: string; value: string };
  }) => {
    const { name, value } = event.target;
    setNewSupplier({
      ...newSupplier,
      [name]: value,
    });
  };

  const onAddBidModal = () => {
    setCurrentBid({
        bid_count: bidCount + 1,
        items: csItems,
        });
    setAddBidModal(!addBidModal);
    console.log("currentBid: ", currentBid, addBidModal);
  };

  const onUpdateBidModal = (bid_count: number) => {
    const bid = bids?.find((bid) => bid.bid_count === bid_count);
    setUpdateBidModal(!updateBidModal);
    setCurrentBid(bid);
  };

  const onCloseCurrentBid = () => {
    setUpdateBidModal(false);
    setAddBidModal(false);
    setCurrentBid({});
  };

  const onCloseUpdateBidBid = () => {
    setUpdateBidModal(false);
    setCurrentBid({});
  };

  const onCurrentBidChange = (
    name_: string,
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    if (name_ === "supplier") {
      const { value } = event.target;
      console.log("value: ", value);
      const id_name = value ? value.split("-#-") : [];
      const supplier: string = id_name.length > 0 ? id_name[0] : "";
      const supplier_name: string = id_name.length >= 1 ? id_name[1] : "";
      setCurrentBid({
        ...currentBid,
        supplier: supplier,
        supplier_name: supplier_name,
      });
    } else {
      const { value } = event.target;
      setCurrentBid({
        ...currentBid,
        [name_]: value,
      });
    }
  };

  const onCurrentBidSupplierChange = (
    name_: string,
    event: React.ChangeEvent<HTMLSelectElement>
  ) => {
    if (name_ === "supplier") {
      const { value } = event.target;
      console.log("value: ", value);
      const id_name = value ? value.split("-#-") : [];
      const supplier: string = id_name.length > 0 ? id_name[0] : "";
      const supplier_name: string = id_name.length >= 1 ? id_name[1] : "";
      setCurrentBid({
        ...currentBid,
        supplier: supplier,
        supplier_name: supplier_name,
      });
    } else {
      const { value } = event.target;
      setCurrentBid({
        ...currentBid,
        [name_]: value,
      });
    }
  };

  const onBidDocumentChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const bid_file = event.target.files && event.target.files[0];
    const bid_document_url = onGetFileObjectUrl(bid_file ?? undefined);
    const bid_document: File | null = bid_file;
    setCurrentBid({
      ...currentBid,
      bid_document: bid_document,
      bid_document_url: bid_document_url || "",
    });
  };

  const onCurrentBidItemChange = (
    description: string,
    name_: string,
    event: { target: { name: string; value: string } },
    bid_no: string
  ) => {
    const { name, value } = event.target;
    console.log("name: ", name, " value: ", value, " bid no: ", bid_no);
    console.log("description: ", description);

    const items = currentBid && currentBid.items;

    const new_items = items
      ? items.map((it) => {
          if (it.item_required === description) {
            return {
              ...it,
              [name_]: value,
            };
          } else {
            return it;
          }
        })
      : [];

    setCurrentBid({
      ...currentBid,
      items: new_items,
    });
  };

  const onCurrentBidSave = () => {
    if (
      currentBid?.supplier_name === "" ||
      currentBid?.supplier_name === undefined
    ) {
      onOpenResponse("Submit Bid Error", "Please select a supplier", false);
      return;
    } else if (
      currentBid.bid_date === "" ||
      currentBid.bid_date === undefined
    ) {
      onOpenResponse("Submit Bid Error", "Please select a bid date", false);
      return;
    } else if (currentBid?.bid_document === undefined) {
      onOpenResponse("Submit Bid Error", "Please select a bid document", false);
      return;
    } else {
      // check if current bid already exists
      if (currentBid.items) {
        const bid =
          bids &&
          bids.find((bid) => bid && bid.bid_count === currentBid.bid_count);
        console.log("bid found: ", bid);
        if (bid) {
          // update bid
          console.log("currentBid 1: ", currentBid);
          let items: IBidItem[];
          if (currentBid.items && currentBid.items.length > 0) {
            items = currentBid.items.map((item) => {
              item.total_price =
                item.quantity && item.unit_price
                  ? item.quantity * item.unit_price
                  : 0;
              return item;
            });

            const missingFields = items.filter(
              (item) =>
                item.quantity === undefined ||
                item.unit_price === undefined ||
                item.vat === "" ||
                item.vat === undefined ||
                item.unit_of_measurement === "" ||
                item.unit_of_measurement === undefined ||
                item.total_price === undefined
            );

            if (missingFields.length > 0) {
              onOpenResponse(
                "Submit Bid Error",
                "Please fill in all required fields",
                false
              );
              return;
            }
            currentBid.items = items;
            console.log("currentBid: ", currentBid);
            let bids_: IBid[] = [];
            if (bids && bids.length > 0) {
              bids_ = bids.map((bid) => {
                if (bid.bid_count === currentBid.bid_count) {
                  return {
                    ...currentBid,
                    bid_document: currentBid.bid_document
                      ? currentBid.bid_document
                      : bid.bid_document,
                    bid_document_url: onGetFileObjectUrl(
                      currentBid.bid_document ?? undefined
                    ),
                  };
                }
                return bid;
              });

              bids_.sort((a, b) =>
                a.bid_count && b.bid_count ? a.bid_count - b.bid_count : 0
              );
              onSaveBid(currentBid, bids_, undefined);
            }
          }
        } else {
          // calculate total price for each item
          let items: IBidItem[] = [];
          if (currentBid.items && currentBid.items.length > 0) {
            items = currentBid.items.map((item) => {
              item.total_price =
                item.quantity &&
                item.unit_price &&
                item.quantity * item.unit_price;
              return item;
            });
          }

          const missingFields = items.filter(
            (item) =>
              item.quantity === undefined ||
              item.unit_price === undefined ||
              item.vat === "" ||
              item.vat === undefined ||
              item.unit_of_measurement === "" ||
              item.unit_of_measurement === undefined ||
              item.total_price === undefined
          );

          if (missingFields.length > 0) {
            onOpenResponse(
              "Submit Bid Error",
              "Please fill in all required fields",
              false
            );
            return;
          }
          // update current bid items
          currentBid.items = items;

          bids?.sort((a, b) =>
            a.bid_count && b.bid_count ? a.bid_count - b.bid_count : 0
          );
          onSaveBid(currentBid, bids ?? []);
        }
      } else {
        onOpenResponse(
          "Submit Bid Error",
          "Please add items to the bid",
          false
        );
      }
    }
  };

  const onSaveBid = (bid: IBid, bids: IBid[], bid_count?: number) => {
    console.log("bid_count: ", bid_count);
    const form_data: FormData = new FormData();

    form_data.append("cs_id", csId);
    form_data.append(
      "bid_count",
      bid?.bid_count ? bid?.bid_count?.toString() : ""
    );
    form_data.append("supplier", bid.supplier ?? "");
    form_data.append("supplier_name", bid.supplier_name ?? "");
    form_data.append("bid_date", bid.bid_date ?? "");
    form_data.append("bid_document", bid.bid_document ?? "");
    form_data.append(
      "json_data",
      JSON.stringify({
        items: bid.items,
      })
    );
    form_data.append("csrfmiddlewaretoken", getCookie("csrftoken") ?? "");

    fetch(`${base_url}/save_bid`, {
      method: "POST",
      headers: {
        "X-CSRFToken": getCookie("csrftoken") ?? "",
      },
      body: form_data,
    })
      .then((response) => response.json())
      .then((data) => {
        console.log("data: ", data, bids);
        if (data.success) {
          onOpenResponse("Save Bid Success", "Bid saved successfully", true);
          setBids([...bids, bid]);
          setAddBidModal(false);
          setUpdateBidModal(false);
          setCurrentBid({});
          setBidCount(bidCount+1);
          if(base_url === "/direct_purchase"){
              const limit: boolean = bids?.length??0 >= 1 ? false : true;
              setDirectPurchaseLimit(limit)
          }
        } else {
          onOpenResponse(
            "Save Bid Error",
            "Failed to save bid, please try again.",
            false
          );
        }
      });
  };

  const onDeleteBidModal = (
    bid_count: number | undefined,
    supplier_name: string | undefined
  ) => {
    onOpenResponse(
      "Delete Bid",
      "Are you sure you want to delete this bid? This action cannot be undone",
      false
    );
    deleteBid(bid_count ?? 0, supplier_name ?? "");
    onSetDirectPurchaseLimit()
  };

  const onSaveSchedule = () => {
    if (
      !currency ||
      !procRef ||
      !scopeOfWork ||
      !prNumber ||
      !prDate ||
      !closingDate ||
      !refDate ||
      !closingTime ||
      !dateTenderOpened ||
      !tenderAdjudicationCommitteeDate
    ) {
      onOpenResponse(
        "Submit Schedule Error",
        "Please fill in all required fields",
        false
      );
      return;
    }
    if (prItems && prItems.length === 0) {
      onOpenResponse(
        "Submit Schedule Error",
        "Cannot create a Comparative Schedule without Purchase Request items.",
        false
      );
      return;
    }
    const form_data: FormData = new FormData();
    // add enctype to form data
    // form_data.enctype = "multipart/form-data";
    form_data.append("proc_ref", procRef);
    form_data.append("scope_of_work", scopeOfWork);
    form_data.append("currency", JSON.stringify(currency.id));
    form_data.append("pr_number", prNumber);
    form_data.append("quantity", quantity);
    form_data.append("pr_date", prDate);
    form_data.append("closing_date", closingDate);
    form_data.append("ref_date", refDate);
    form_data.append("closing_time", closingTime);
    form_data.append("date_tender_opened", dateTenderOpened);
    form_data.append("username", username ?? "");
    form_data.append(
      "tender_adjudication_committee_date",
      tenderAdjudicationCommitteeDate
    );
    form_data.append("advert", JSON.stringify(advert));
    form_data.append("csrfmiddlewaretoken", getCookie("csrftoken") ?? "");

    fetch(`${base_url}/save`, {
      method: "POST",
      headers: {
        "X-CSRFToken": getCookie("csrftoken") ?? "",
      },
      body: form_data,
    })
      .then((response) => response.json())
      .then((data) => {
        console.log("comperative schedule saved data: ", data);
        if (data.success) {
          onOpenResponse(
            "Submit Schedule Successful",
            "Comparative Schedule saved successfully",
            true
          );
          setCsId(data.cs_id);
          setCsOwner(data.cs_owner);
        } else {
          onOpenResponse(
            "Submit Schedule Error",
            "Failed to submit schedule, please try again.",
            false
          );
        }
      })
      .catch((err) => console.log("onSaveSchedule: ", err));
  };

  const onUpdateSchedule = () => {
    if (csId === "" || csId === undefined) {
      onOpenResponse(
        "Update Schedule Error",
        "Please save the Comparative Schedule first",
        false
      );
      return;
    }
    setProcRef(procPlan?.proc_ref??"")
    console.log("currency ...", currency, "procRef: ", procPlan?.proc_ref, "scopeOfWork: ", scopeOfWork, "prNumber: ", prNumber, "prDate: ", prDate, "closingDate: ", closingDate, "refDate: ", refDate, "closingTime: ", closingTime, "dateTenderOpened: ", dateTenderOpened, "tenderAdjudicationCommitteeDate: ", tenderAdjudicationCommitteeDate);
    if (
      !currency ||
      !procPlan ||
      !scopeOfWork ||
      !prNumber ||
      !prDate ||
      !closingDate ||
      !refDate ||
      !closingTime ||
      !dateTenderOpened ||
      !tenderAdjudicationCommitteeDate
    ) {
      onOpenResponse(
        "Update Schedule Error",
        "Please fill in all required fields",
        false
      );
      return;
    }
    const form_data: FormData = new FormData();
    // console.log("currency ...", this.state);
    // add enctype to form data
    // form_data.enctype = "multipart/form-data";
    form_data.append("cs_id", csId);
    form_data.append("proc_ref", procPlan?.proc_ref ?? "");
    form_data.append("scope_of_work", scopeOfWork);
    form_data.append("currency", JSON.stringify(currency.id));
    form_data.append("pr_number", prNumber);
    form_data.append("quantity", quantity);
    form_data.append("pr_date", prDate);
    form_data.append("closing_date", closingDate);
    form_data.append("ref_date", refDate);
    form_data.append("closing_time", closingTime);
    form_data.append("date_tender_opened", dateTenderOpened);
    form_data.append("username", username ?? "");
    form_data.append(
      "tender_adjudication_committee_date",
      tenderAdjudicationCommitteeDate
    );
    form_data.append("advert", JSON.stringify(advert));
    form_data.append("csrfmiddlewaretoken", getCookie("csrftoken") ?? "");

    fetch(`${base_url}/update`, {
      method: "POST",
      headers: {
        "X-CSRFToken": getCookie("csrftoken") ?? "",
      },
      body: form_data,
    })
      .then((response) => response.json())
      .then((data) => {
        console.log("data: ", data);
        if (data.success) {
          onOpenResponse(
            "Update Schedule Successful",
            "Comparative Schedule updated successfully",
            true
          );
        } else {
          onOpenResponse(
            "Update Schedule Error",
            "Failed to submit schedule, please try again.",
            false
          );
        }
      })
      .catch((err) => console.log("onUpdateSchedule: ", err));
  };

  const deleteBid = (bid_count: number, supplier_name: string) => {
    const form_data: FormData = new FormData();
    form_data.append("cs_id", csId);
    form_data.append("bid_count", JSON.stringify(bid_count));
    form_data.append("supplier_name", supplier_name);
    form_data.append("csrfmiddlewaretoken", getCookie("csrftoken") ?? "");

    fetch(`${base_url}/delete_bid`, {
      method: "POST",
      headers: {
        "X-CSRFToken": getCookie("csrftoken") ?? "",
      },
      body: form_data,
    })
      .then((response) => response.json())
      .then((data) => {
        console.log("data: ", data);
        if (data.success) {
          // delete compliance if bid_no and supplier_name
          const _compliance = compliance?.filter(
            (compliance_) =>
              compliance_.supplier_name !== supplier_name &&
              compliance_.bid_no !== bid_count
          );

          const complianceRemark = complianceRemarks?.filter(
            (complianceRemark_) =>
              complianceRemark_.supplier_name !== supplier_name &&
              complianceRemark_.bid_no !== bid_count
          );
          setCompliance(_compliance);
          setComplianceRemarks(complianceRemark);
          onOpenResponse(
            "Delete Bid Successful",
            "Bid deleted successfully",
            true
          );
        } else {
          onOpenResponse(
            "Delete Bid Error",
            "Failed to delete schedule",
            false
          );
        }
        
        if (response?.open) {
          window.location.reload();
        }

        // reset bid no index
        const bid_count_ = bidCount > 0? bidCount - 1: 0;
        const newBids = bids?.filter((bid) => bid.bid_count !== bid_count);
        // update bid_count index for all bids sequentially
        const updatedBids = newBids?.map((bid, index) => {
          bid.bid_count = index + 1;
          return bid;
        });
        setBidCount(bid_count_);
        setBids(updatedBids);
      });
  };

  const onAddItemsModal = () => {
    setAddItemsModal(!addItemsModal);
  };

  const onSelectChange = (
    name_: string,
    event: React.ChangeEvent<HTMLSelectElement>
  ) => {
    const { value } = event.target;

    if (name_ === "closing_time") {
      setClosingTime(value);
    } else if (name_ === "proc_ref") {
      setProcRef(value);
    } else if (name_ === "currency") {
      setCurrency({
        id: parseInt(value),
      });
    }
  };

  const onAddCommitteeMembers = () => {
    if (!member?.memberUserName || !member?.memberPosition) {
      onOpenResponse(
        "Add Committee Member Error",
        "Please select a user",
        false
      );
    } else {
      // check if memberUserName exists
      const member_ = committeeMembers?.find(
        (_member) => _member.memberUserName === member?.memberUserName
      );
      // check if memberUserName is the one creating
      const currentUserFlag = member?.memberUserName === username;
      // check if memberPosition exists
      const positionFlag = committeeMembers?.find(
        (_member) => _member.memberPosition === member?.memberPosition
      );
      console.log(
        "member_: ",
        member_,
        "currentUserFlag: ",
        currentUserFlag,
        "positionFlag: ",
        positionFlag
      );
      console.log("owner: ", username, "member: ", member?.memberUserName);
      if (member_) {
        onOpenResponse(
          "Add Committee Member Error",
          "Committee Member already added.",
          false
        );
      } else if (currentUserFlag) {
        onOpenResponse(
          "Add Committee Member Error",
          "You cannot add yourself. Please choose another user.",
          false
        );
      } else if (positionFlag) {
        onOpenResponse(
          "Add Committee Member Error",
          member?.memberPosition +
            ", already exists, please add a different one.",
          false
        );
      } else {
        const members = [
          ...(committeeMembers ?? []),
          {
            memberUserName: member?.memberUserName ?? "",
            memberName: member?.memberName ?? "",
            memberPosition: member?.memberPosition ?? "",
            memberApproval: "",
          },
        ];
        setCommitteeMembers(members);
        setMember({
          memberUserName: "",
          memberName: "",
          memberPosition: "",
          memberApproval: "",
        });
        setSearchedUser("");
      }
    }
  };

  const onFileInputChange = (
    name_: string,
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    console.log(event);
    const file = event?.target?.files ? event?.target?.files[0] : undefined;
    const fileUrl = onGetFileObjectUrl(file);
    if (name_ === "advert") {
      setAdvert(file);
      setAdvertUrl(fileUrl);
    }
  };

  const getCookie = (name: string) => {
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
  };

  const onAddComplianceTable = () => {
    // add bid compliance
    if (bids && bids.length === 0) {
      onOpenResponse(
        "Add Compliance Table Error",
        "Please add bids first",
        false
      );
      return;
    }
    const compliances = bids?.map((bid) => {
      // check is compliance already exists
      const comp = compliance?.find(
        (compliance) => compliance.supplier_name === bid.supplier_name
      );
      if (comp) {
        return comp;
      } else {
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
          site_visit: false,
          samples_required: false,
          decision: false,
          reject: true,
          remarks: "",
        };
      }
    });

    const complianceRemarks_ = bids?.map((bid) => {
      // check is compliance already exists
      const comp = complianceRemarks?.find(
        (compR) => compR.supplier_name === bid.supplier_name
      );
      if (comp) {
        return comp;
      } else {
        return {
          bid_count: bid.bid_count,
          supplier: bid.supplier,
          supplier_name: bid.supplier_name,
          remarks: "",
        };
      }
    });

    setCompliance(compliances);
    setComplianceRemarks(complianceRemarks_);
    setComplianceTable(!complianceTable);
  };

  const onComplianceItemsChange = (
    name_: string,
    event: { target: { name: string; value: string } }
  ) => {
    const { name, value } = event.target;
    console.log("name: ", name, "value: ", value);
    if (name_ === "showSiteVisit") {
      setShowSiteVisit(value);
    } else if (name_ === "showSamples") {
      setShowSamples(value);
    }

    if (compliance && compliance.length === 0) {
      onOpenResponse(
        "Add Compliance Table Error",
        "Please add bids first",
        false
      );
      return;
    }

    const updatedComplianceList = compliance?.map((compliance_) => {
      let _compliance = {};
      const site_visit = compliance_.site_visit;
      const samples_required = compliance_.samples_required;

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
      const keysToCheck = Object.keys(_compliance).filter(
        (key) =>
          key !== "decision" &&
          key !== "reject" &&
          key !== "remarks" &&
          key !== "supplier_name" &&
          key !== "bid_no" &&
          key !== "supplier"
      );
      console.log("keysToCheck: ", keysToCheck);
      const allValuesTrue = keysToCheck.every((key) => {
        if (key === "site_visit" && showSiteVisit === "no") return true;
        if (key === "samples_required" && showSamples === "no") return true;
        return compliance_[key];
      });
      compliance_["decision"] = allValuesTrue;
      compliance_["reject"] = !allValuesTrue;

      return compliance_;
    });

    setCompliance(updatedComplianceList);
  };

  const onComplianceChange = (
    index: number,
    event: { target: { name: string; checked: boolean } }
  ) => {
    const { name, checked } = event.target;
    console.log("name : ", name, "checked: ", checked);
    console.log("compliance: ", compliance);
    if (compliance && compliance.length > 0) {
      const currentCompliances = compliance;
      const currentCompliance = currentCompliances[index];
      console.log("currentCompliance: ", currentCompliance);
      currentCompliance[name] = checked;
      console.log("currentCompliance: ", name, currentCompliance);

      if (name === "decision") {
        const updatedCompliances = currentCompliances.map((compliance_) => {
          if (compliance_.supplier_name === currentCompliance.supplier_name) {
            return {
              ...compliance_,
              decision: checked,
              reject: !checked,
              payment_terms: checked,
              bid_validity: checked,
              delivery_period: checked,
              technical_specifications: checked,
              valid_tax_clearance: checked,
              registered_with_praz: checked,
              site_visit: showSiteVisit === "yes" ? checked : false,
              samples_required: showSamples === "yes" ? checked : false,
            };
          } else {
            return compliance_;
          }
        });
        setCompliance(updatedCompliances);
      } else {
        console.log("currentCompliance else: ", currentCompliance);
        const keysToCheck = Object.keys(currentCompliance).filter(
          (key) =>
            key !== "decision" &&
            key !== "reject" &&
            key !== "remarks" &&
            key !== "supplier_name" &&
            key !== "bid_no" &&
            key !== "supplier"
        );
        console.log("keysToCheck: ", keysToCheck);
        const allValuesTrue = keysToCheck.every((key) => {
          if (key === "site_visit" && showSiteVisit === "no") return true;
          if (key === "samples_required" && showSamples === "no") return true;
          return currentCompliance[key];
        });
        currentCompliance["decision"] = allValuesTrue;
        currentCompliance["reject"] = !allValuesTrue;

        const updatedCompliances = currentCompliances.map((compliance_) => {
          if (compliance_.supplier_name === currentCompliance.supplier_name) {
            return currentCompliance;
          } else {
            return compliance_;
          }
        });
        setCompliance(updatedCompliances);
      }
    }
  };

  const onComplianceRemarksChange = (
    supplier_name: string,
    event: { target: { name: string; value: string } }
  ) => {
    const { name, value } = event.target;
    console.log(
      "name: ",
      name,
      "value: ",
      value,
      "supplier_name: ",
      supplier_name
    );

    const index = complianceRemarks?.findIndex(
      (item) => item.supplier_name === supplier_name
    );
    if (index !== -1) {
      const updatedComplianceRemarks = Object.entries(
        complianceRemarks ?? {}
      ).map(([key, value_]) => {
        if (key === String(index)) {
          value_.remarks = value;
          return value_;
        }
        return value_;
      });
      setComplianceRemarks(updatedComplianceRemarks);
    } else {
      complianceRemarks?.push({
        supplier_name: supplier_name,
        remarks: value,
      });

      setComplianceRemarks(complianceRemarks);
    }
  };

  const onSaveCompliance = () => {
    const form_data: FormData = new FormData();
    form_data.append("cs_id", csId);
    form_data.append("show_site_visit", showSiteVisit);
    form_data.append("show_samples_required", showSamples);
    form_data.append(
      "compliance",
      JSON.stringify({
        compliance: compliance,
      })
    );
    form_data.append(
      "complianceRemarks",
      JSON.stringify({
        complianceRemarks: complianceRemarks,
      })
    );
    form_data.append("csrfmiddlewaretoken", getCookie("csrftoken") ?? "");

    fetch(`${base_url}/save_compliance`, {
      method: "POST",
      headers: {
        "X-CSRFToken": getCookie("csrftoken") ?? "",
      },
      body: form_data,
    })
      .then((response) => response.json())
      .then((data) => {
        console.log("data: ", data);
        if (data.success) {
          onOpenResponse(
            "Submit Compliances Successful",
            "Compliances submitted successfully",
            true
          );
        } else {
          onOpenResponse(
            "Submit Compliances Error",
            "Failed to submit compiances, please try again.",
            false
          );
        }
      });
  };

  const onCloseCS = () => {
    const form_data: FormData = new FormData();
    form_data.append("cs_id", csId);
    form_data.append("csrfmiddlewaretoken", getCookie("csrftoken") ?? "");

    fetch(`${base_url}/close_compliance`, {
      method: "POST",
      headers: {
        "X-CSRFToken": getCookie("csrftoken") ?? "",
      },
      body: form_data,
    })
      .then((response) => response.json())
      .then((data) => {
        console.log("data: ", data);
        if (data.success) {
          const rankings = data.rankings;
          setRankings(rankings);
          //   setRankingTable(true);
          onOpenResponse(
            "Rank Bids Successful",
            "Bids ranked successfully",
            true
          );
        } else {
          onOpenResponse(
            "Rank Bids Error",
            "Failed to rank bids, please try again",
            false
          );
        }
      });
  };

  const onOpenResponse = (title: string, message: string, success: boolean) => {
    setResponse({
      open: true,
      title: title,
      message: message,
      success: success,
    });
  };

  const onCloseResponse = () => {
    setResponse({
      open: false,
      title: "",
      message: "",
      success: false,
    });
  };

  const onSearchUser = (event: { target: { name: string; value: string } }) => {
    console.log("searching user ...");
    const { value } = event.target;
    console.log("valued: ", value);

    if (value.length > 3) {
      const filteredOptions = users?.filter((user) => {
        console.log("user: ", user);
        return (
          (user.first_name.toLowerCase() || "").includes(value.toLowerCase()) ||
          (user.last_name.toLowerCase() || "").includes(value.toLowerCase())
        );
      });

      setSearchedUser(value);
      setFilteredUsers(filteredOptions);
    } else {
      setSearchedUser(value);
      setFilteredUsers([]);
    }
  };

  const onAdditionalNotesChange = (event: {
    target: { name: string; value: string };
  }) => {
    const { value } = event.target;
    setAdditionalNotes(value);
  };

  const onAdditionalNotesSubmit = () => {
    const form_data: FormData = new FormData();
    form_data.append("cs_id", csId);
    form_data.append("additional_notes", additionalNotes);
    form_data.append("csrfmiddlewaretoken", getCookie("csrftoken") ?? "");

    fetch(`${base_url}/save_additional_notes`, {
      method: "POST",
      headers: {
        "X-CSRFToken": getCookie("csrftoken") ?? "",
      },
      body: form_data,
    })
      .then((response) => response.json())
      .then((data) => {
        console.log("data: ", data);
        if (data.success) {
          onOpenResponse(
            "Additional Notes Saved",
            "Additional notes saved successfully",
            true
          );
        } else {
          onOpenResponse(
            "Additional Notes Error",
            "Failed to save additional notes, please try again",
            false
          );
        }
      });
  };

  const onBuyersNotesChange = (event: {
    target: { name: string; value: string };
  }) => {
    const { value } = event.target;
    setBuyersNotes(value);
  };

  const onBuyersNotesSubmit = () => {
    const form_data: FormData = new FormData();
    form_data.append("cs_id", csId);
    form_data.append("buyers_notes", buyersNotes);
    form_data.append("csrfmiddlewaretoken", getCookie("csrftoken") ?? "");

    fetch(`${base_url}/save_buyers_notes`, {
      method: "POST",
      headers: {
        "X-CSRFToken": getCookie("csrftoken") ?? "",
      },
      body: form_data,
    })
      .then((response) => response.json())
      .then((data) => {
        console.log("data: ", data);
        if (data.success) {
          onOpenResponse(
            "Buyer's Notes Saved",
            "Buyer's notes saved successfully",
            true
          );
        } else {
          onOpenResponse(
            "Buyer's Notes Error",
            "Failed to save Buyer's notes, please try again",
            false
          );
        }
      });
  };

  const getCommitteeClassNames = (approvalStatus: string) => {
    const baseClasses = "grid grid-cols-5 gap-4 px-2 py-2 m-2 rounded-md";
    let statusClasses = "";
  
    switch (approvalStatus) {
      case "Approved":
        statusClasses = "bg-green-100 hover:bg-green-200 text-green-700 hover:text-green-900 border before:border-green-400 after:border-green-700 border-green-400";
        break;
      case "Rejected":
        statusClasses = "bg-red-100 hover:bg-red-200 text-red-700 hover:text-red-900 border before:border-red-400 after:border-red-700 border-red-400";
        break;
      case "":
        statusClasses = "bg-blue-100 hover:bg-blue-200 text-blue-700 hover:text-blue-900 border before:border-gray-400 after:border-gray-700 border-gray-400";
        break;
      default:
        statusClasses = "bg-blue-100 hover:bg-blue-200 text-blue-700 hover:text-blue-900 border before:border-gray-400 after:border-gray-700 border-gray-400";
        break;
    }
  
    return `${statusClasses} ${baseClasses}`;
  };

  const itemsModal = (
    <div className="fixed inset-0 flex items-center justify-center z-50 pt-10 pb-20">
      <div className="bg-gulf-blue-50 rounded-lg shadow-lg p-6 h-5/6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium">SELECT SCHEDULE ITEMS</h3>
          <button
            type="button"
            className="text-gray-400 hover:text-gray-500 focus:outline-none"
            onClick={onAddItemsModal}
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
        <div className="px-2 py-2 mt-3 rounded-md bg-gulf-blue-300 h-4/5 overflow-y-auto">
          <table
            style={{ width: "100%" }}
            className="table-auto w-full text-left"
          >
            <thead>
              <tr className="text-gray-900">
                <th className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                  Item
                </th>
                <th className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                  Quantity
                </th>
                <th className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                  Action
                </th>
              </tr>
            </thead>
            <tbody>
              {prItems &&
                prItems.map((item, index) => {
                  return (
                    <tr key={index} className="text-gray-900">
                      <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                        {item.item_required}
                      </td>
                      <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                        {item.quantity}
                      </td>
                      <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                        <input
                          type="checkbox"
                          checked={item.ordered ? item.ordered : false}
                          onChange={() => onAddCSItem(item.id ?? 0)}
                        />
                      </td>
                    </tr>
                  );
                })}
            </tbody>
          </table>
        </div>
        <div className="flex justify-center mt-1 px-3 py-3">
            <div className="m-2">
              <button
                onClick={onSubmitCSItems}
                className="rounded-md text-gray-50 text-sm bg-blue-925 hover:bg-blue-550 px-3 py-2 font-semibold leading-6"
              >
                <span className="ml-2">SAVE SCHEDULE ITEMS</span>
              </button>
            </div>
          </div>
      </div>
    </div>
  );

  const bidsModal = (
    <div
      id={"bid-" + currentBid?.bid_count}
      className="fixed inset-0 flex items-center justify-center z-50 pt-10 pb-20"
    >
      <div className="transition-all duration-300 bg-gulf-blue-50 p-4 rounded-lg border-l-4 border-blue-600 rounded-lg shadow-lg p-6 max-h-screen min-w-max overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium">ADD BID DETAILS</h3>
          <button
            type="button"
            className="text-gray-400 hover:text-gray-500 focus:outline-none"
            onClick={onCloseCurrentBid}
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
        <div className="px-4 sm:px-0 mt-6 rounded-md border-t border-gray-100 border-b border-gray-900/10 pb-12">
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
                    onChange={(e) => onCurrentBidSupplierChange("supplier", e)}
                    className="block w-full rounded-md border-0 py-1.5 px-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6 chzn-select"
                  >
                    {currentBid?.supplier_name ? (
                      <option
                        value={
                          currentBid?.supplier +
                          "-#-" +
                          currentBid?.supplier_name
                        }
                      >
                        {currentBid?.supplier_name}
                      </option>
                    ) : (
                      ""
                    )}
                    <option>Select Supplier</option>
                    {suppliers
                      ? suppliers?.map((supplier) => (
                          <option value={supplier?.id + "-#-" + supplier?.name}>
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
                    value={currentBid?.bid_date}
                    onChange={(e) => onCurrentBidChange("bid_date", e)}
                    type="date"
                    required
                    className="block w-full rounded-md border-0 py-1.5 px-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
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
                    value={bidCount+1}
                    id="bid"
                    required
                    readOnly
                    className="block w-full rounded-md border-0 py-1.5 px-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
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
                    onChange={(e) => onBidDocumentChange(e)}
                    className="block w-full rounded-md border-0 py-1.5 px-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                  />
                </div>
              </div>
            </div>

            {csItems &&
              csItems.map((item) => {
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
                            onCurrentBidItemChange(
                              item.item_required ?? "",
                              "item_required",
                              e,
                              currentBid?.bid_count?.toString() ?? ""
                            )
                          }
                          id="item_description"
                          required
                          className="block w-full rounded-md border-0 py-1.5 px-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
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
                          required
                          defaultValue={item.quantity}
                          onChange={(e) =>
                            onCurrentBidItemChange(
                              item.item_required ?? "",
                              "quantity",
                              e,
                              currentBid?.bid_count?.toString() ?? ""
                            )
                          }
                          type="number"
                          id="quantity"
                          className="block inpt w-full rounded-md border-0 py-1.5 px-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
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
                              onCurrentBidItemChange(
                                item.item_required ?? "",
                                "unit_of_measurement",
                                e,
                                currentBid?.bid_count?.toString() ?? ""
                              )
                            }
                            autoComplete="unit_of_measurement"
                            className="block w-full rounded-md border-0 py-1.5 px-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6"
                          >
                            {item.unit_of_measurement ? (
                              <option value={item.unit_of_measurement}>
                                {item.unit_of_measurement}
                              </option>
                            ) : (
                              ""
                            )}
                            {uom ? (
                              uom.map((uom) => (
                                <option value={uom.name}>{uom.name}</option>
                              ))
                            ) : (
                              <option>No Units</option>
                            )}
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
                              onCurrentBidItemChange(
                                item.item_required ?? "",
                                "vat",
                                e,
                                currentBid?.bid_count?.toString() ?? ""
                              )
                            }
                            autoComplete="vat"
                            className="block w-full rounded-md border-0 py-1.5 px-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6"
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
                            onCurrentBidItemChange(
                              item.item_required ?? "",
                              "unit_price",
                              e,
                              currentBid?.bid_count?.toString() ?? ""
                            )
                          }
                          type="text"
                          id="unit_price"
                          required
                          className="block inpt w-full rounded-md border-0 py-1.5 px-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
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
                onClick={onCloseCurrentBid}
                type="submit"
                className="rounded-md bg-gray-700 hover:bg-gray-600 text-sm font-semibold px-3 py-2 text-white shadow-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2"
              >
                <span className="ml-2">CANCEL</span>
              </button>
            </div>
            <div className="m-2">
              <button
                onClick={onCurrentBidSave}
                className="rounded-md text-blue-50 text-sm bg-blue-600 hover:bg-blue-500 px-3 py-2 font-semibold leading-6"
              >
                <span className="ml-2">SAVE BID</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const responseModal = (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-end justify-center min-h-screen px-4 text-center md:items-center sm:block sm:p-0">
        <div
          //   enter="transition ease-out duration-300 transform"
          //   enterStart="opacity-0"
          //   enterEnd="opacity-100"
          //   leave="transition ease-in duration-200 transform"
          //   leaveStart="opacity-100"
          //   leaveEnd="opacity-0"
          className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-40"
        ></div>

        <div
          //   enter="transition ease-out duration-300 transform"
          //   enterStart="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
          //   enterEnd="opacity-100 translate-y-0 sm:scale-100"
          //   leave="transition ease-in duration-200 transform"
          //   leaveStart="opacity-100 translate-y-0 sm:scale-100"
          //   leaveEnd="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
          className="inline-block w-full max-w-xl p-8 my-20 overflow-hidden text-left transition-all transform bg-white rounded-lg shadow-xl 2xl:max-w-2xl"
        >
          <div className="flex items-center justify-between space-x-4">
            <h1 className="text-xl font-medium text-gray-800">
              {response?.title}
            </h1>

            <button
              type="button"
              onClick={onCloseResponse}
              className="text-gray-600 focus:outline-none hover:text-gray-700"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="w-6 h-6"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </button>
          </div>

          <p
            className={`mt-5 text-sm p-2 rounded-md ${
              response?.success
                ? "bg-green-100 text-green-700"
                : "bg-red-100 text-red-700"
            }`}
          >
            {response?.message}
          </p>

          <form>
            <div className="flex justify-evenly mt-6">
              <button
                type="button"
                style={{ width: "100%" }}
                onClick={onCloseResponse}
                className="px-3 py-2 text-sm tracking-wide text-white capitalize transition-colors duration-200 transform bg-gulf-blue-600 rounded-md dark:bg-gulf-blue-800 dark:hover:bg-gulf-blue-700 dark:focus:bg-gulf-blue-700 hover:bg-gulf-blue-600 focus:outline-none focus:bg-gulf-blue-500 focus:ring focus:ring-gulf-blue-300 focus:ring-opacity-50"
              >
                CLOSE
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );

  const complianceTableComp = (
    <div className="transition-all duration-300 bg-gulf-blue-100 p-4 rounded-lg border-l-4 border-blue-600">
      <div className="space-y-12 px-5 py-5">
        <div className="px-4 sm:px-0 mt-6 border-t border-gray-100 border-gray-900/10">
          <h2 className="text-base font-semibold leading-6 text-gray-900">
            COMPLIANCE TABLE
          </h2>
          <p className="mt-1 max-w-2xl text-sm leading-6 text-gray-500">
            Key: Comply/ Not Comply (Y/ N), Not Stated (NS)
          </p>
          <div className="flex justify-evenly mt-5  px-2 py-2 rounded-md">
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
                  onChange={(e) => onComplianceItemsChange("showSiteVisit", e)}
                  disabled={
                    username === csOwner || csOwner === "" ? false : true
                  }
                  autoComplete="site_visit"
                  className="block w-full rounded-md border-0 py-2 px-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6 chzn-select"
                >
                  {showSiteVisit ? (
                    <option value={showSiteVisit}>{showSiteVisit}</option>
                  ) : (
                    ""
                  )}
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
                    onChange={(e) => onComplianceItemsChange("showSamples", e)}
                    disabled={
                      username === csOwner || csOwner === "" ? false : true
                    }
                    autoComplete="samples"
                    className="block w-full rounded-md border-0 py-2 px-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6 chzn-select"
                  >
                    {showSamples ? (
                      <option value={showSamples}>{showSamples}</option>
                    ) : (
                      ""
                    )}
                    <option value="">Select Option</option>
                    <option value="yes">Yes</option>
                    <option value="no">No</option>
                  </select>
                </div>
              </div>
            </div>
          </div>

          <div className="overflow-auto px-2 py-2 mt-5 rounded-md ">
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
                  {showSiteVisit === "yes" ? (
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
                  {showSamples === "yes" ? (
                    <th
                      id="samples_header"
                      className="samples-header border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2"
                    >
                      Samples <br />
                      Required?
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
                {compliance &&
                  compliance.map((comp, key) => {
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
                            onChange={(e) => onComplianceChange(key, e)}
                            disabled={
                              username === csOwner || csOwner === ""
                                ? false
                                : true
                            }
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
                            onChange={(e) => onComplianceChange(key, e)}
                            disabled={
                              username === csOwner || csOwner === ""
                                ? false
                                : true
                            }
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
                            onChange={(e) => onComplianceChange(key, e)}
                            disabled={
                              username === csOwner || csOwner === ""
                                ? false
                                : true
                            }
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
                            onChange={(e) => onComplianceChange(key, e)}
                            disabled={
                              username === csOwner || csOwner === ""
                                ? false
                                : true
                            }
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
                            onChange={(e) => onComplianceChange(key, e)}
                            disabled={
                              username === csOwner || csOwner === ""
                                ? false
                                : true
                            }
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
                            onChange={(e) => onComplianceChange(key, e)}
                            disabled={
                              username === csOwner || csOwner === ""
                                ? false
                                : true
                            }
                            id="registered_with_praz"
                            type="checkbox"
                          />
                        </td>
                        {showSiteVisit === "yes" ? (
                          <td
                            id="site_visit_header"
                            className="site-visit-header border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2"
                          >
                            <input
                              name="site_visit"
                              checked={
                                comp.site_visit ? comp.site_visit : false
                              }
                              onChange={(e) => onComplianceChange(key, e)}
                              disabled={
                                username === csOwner || csOwner === ""
                                  ? false
                                  : true
                              }
                              id="site_visit"
                              type="checkbox"
                            />
                          </td>
                        ) : (
                          ""
                        )}
                        {showSamples === "yes" ? (
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
                              onChange={(e) => onComplianceChange(key, e)}
                              disabled={
                                username === csOwner || csOwner === ""
                                  ? false
                                  : true
                              }
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
                            onChange={(e) => onComplianceChange(key, e)}
                            disabled={
                              username === csOwner || csOwner === ""
                                ? false
                                : true
                            }
                            id="decision"
                            type="checkbox"
                          />
                        </td>
                        <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                          <input
                            name="reject"
                            checked={comp.reject ? comp.reject : false}
                            onChange={(e) => onComplianceChange(key, e)}
                            disabled={
                              username === csOwner || csOwner === ""
                                ? false
                                : true
                            }
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
          <div className="px-2 py-2 mt-5 rounded-sm ">
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
                {complianceRemarks &&
                  complianceRemarks.map((bid, key) => {
                    return (
                      <tr key={"cr" + key}>
                        <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                          {bid.supplier_name}
                        </td>
                        <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                          <input
                            name="remarks"
                            defaultValue={bid.remarks}
                            onChange={(e) =>
                              onComplianceRemarksChange(
                                bid.supplier_name ?? "",
                                e
                              )
                            }
                            disabled={
                              username === csOwner || csOwner === ""
                                ? false
                                : true
                            }
                            type="text"
                            className="block w-full rounded-md border-0 py-1.5 text-gray-900 px-2 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6 chzn-select"
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

      {username === csOwner && !approvalsComplete ? (
        <div className="flex justify-center mt-5 px-3 py-3">
          <div className="flex-1 m-2">
            <button
              style={{ width: "100%" }}
              onClick={onSaveCompliance}
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

  //   const loadingModal = (
  //     <div className="fixed inset-0 z-50 overflow-y-auto">
  //       <div className="flex items-end justify-center min-h-screen px-4 text-center md:items-center sm:block sm:p-0">
  //         <div
  //         //   enter="transition ease-out duration-300 transform"
  //         //   enterStart="opacity-0"
  //         //   enterEnd="opacity-100"
  //         //   leave="transition ease-in duration-200 transform"
  //         //   leaveStart="opacity-100"
  //         //   leaveEnd="opacity-0"
  //           className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-40"
  //         ></div>

  //         <div
  //         //   enter="transition ease-out duration-300 transform"
  //         //   enterStart="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
  //         //   enterEnd="opacity-100 translate-y-0 sm:scale-100"
  //         //   leave="transition ease-in duration-200 transform"
  //         //   leaveStart="opacity-100 translate-y-0 sm:scale-100"
  //         //   leaveEnd="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
  //           className="inline-block w-full max-w-xl p-8 my-20 overflow-hidden text-left transition-all transform bg-white rounded-lg shadow-xl 2xl:max-w-2xl"
  //         >
  //           <div className="flex items-center justify-between space-x-4">
  //             <h1 className="text-xl font-medium text-gray-800">
  //                 Loading ...
  //             </h1>
  //           </div>

  //           <p
  //             className={`mt-5 text-sm p-2 rounded-md bg-gulf-blue-100 text-gulf-blue-700`}
  //           >
  //             Please wait ...
  //           </p>
  //         </div>
  //       </div>
  //     </div>
  //   );

  const supplierModal = (
    <div className="fixed inset-0 flex items-center justify-center z-50 pt-10 pb-20">
      <div className="bg-gulf-blue-100 rounded-lg shadow-lg p-6 max-h-screen overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium">ADD SUPPLIER</h3>
          <button
            type="button"
            className="text-gray-400 hover:text-gray-500 focus:outline-none"
            onClick={onAddSuppliersModal}
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
                  onChange={(e) => onSupplierChange(e)}
                  type="text"
                  required
                  className="block w-full rounded-md border-0 py-1.5 text-gray-900 px-2 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                />
              </div>
            </div>
          </div>

          <div className="flex justify-center mt-5 px-3 py-3">
            <div className="m-2">
              <button
                onClick={onAddSuppliersModal}
                className="rounded-md text-gray-50 text-sm bg-gray-300 hover:bg-blue-550 px-3 py-2 font-semibold leading-6"
              >
                <span className="ml-2">CANCEL</span>
              </button>
            </div>
            <div className="m-2">
              <button
                onClick={onSaveSupplier}
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

  const rejectApprovalJustification = (
    <div className="fixed inset-0 flex items-center justify-center z-50 pt-10 pb-20">
      <div className="bg-gulf-blue-100 rounded-lg shadow-lg p-6 max-h-screen overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium">Reason for rejection</h3>
          <button
            type="button"
            className="text-gray-400 hover:text-gray-500 focus:outline-none"
            onClick={onApprovalJustificationModalClose}
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
                  onChange={(e) => onApprovalJustificationChange(e)}
                  required
                  className="block w-full rounded-md border-0 py-1.5 text-gray-900 px-2 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                />
              </div>
            </div>
          </div>

          <div className="flex justify-center mt-5 px-3 py-3">
            <div className="m-2">
              <button
                onClick={onApprovalJustificationModalClose}
                className="rounded-md text-gray-50 text-sm bg-gray-300 hover:bg-blue-550 px-3 py-2 font-semibold leading-6"
              >
                <span className="ml-2">CANCEL</span>
              </button>
            </div>
            <div className="m-2">
              <button
                onClick={() =>
                  onApprovalApprove(
                    currentApprover?.role ?? "",
                    currentApprover?.username ?? "",
                    "Rejected",
                    currentApprover?.justification ?? ""
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

  const rejectJustification = (
    <div className="fixed inset-0 flex items-center justify-center z-50 pt-10 pb-20">
      <div className="bg-gulf-blue-100 rounded-lg shadow-lg p-6 max-h-screen overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium">Reason for rejection</h3>
          <button
            type="button"
            className="text-gray-400 hover:text-gray-500 focus:outline-none"
            onClick={onCommitteeJustificationModalClose}
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
                  onChange={(e) => onCommitteeJustificationChange(e)}
                  required
                  className="block w-full rounded-md border-0 py-1.5 text-gray-900 px-2 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                />
              </div>
            </div>
          </div>

          <div className="flex justify-center mt-5 px-3 py-3">
            <div className="m-2">
              <button
                onClick={onCommitteeJustificationModalClose}
                className="rounded-md text-gray-50 text-sm bg-gray-300 hover:bg-blue-550 px-3 py-2 font-semibold leading-6"
              >
                <span className="ml-2">CANCEL</span>
              </button>
            </div>
            <div className="m-2">
              <button
                onClick={() =>
                  onCommitteeApprove(
                    currentApprover?.username ?? "",
                    "Rejected",
                    currentApprover?.justification ?? ""
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

  const updateBidModalComp = (
    <div
      id={"bid-" + currentBid?.bid_count}
      className="fixed inset-0 flex items-center justify-center z-50 pt-10 pb-20"
    >
      <div className="transition-all duration-300 bg-gulf-blue-50 p-4 rounded-lg border-l-4 border-blue-600 rounded-lg shadow-lg p-6 max-h-screen min-w-max overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium">Update Bid</h3>
          <button
            type="button"
            className="text-gray-400 hover:text-gray-500 focus:outline-none"
            onClick={onCloseUpdateBidBid}
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
        <div className="px-4 sm:px-0 mt-6 rounded-md border-t border-gray-100 border-b border-gray-900/10 pb-12">
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
                    onChange={(e) => onCurrentBidSupplierChange("supplier", e)}
                    className="block w-full rounded-md border-0 py-1.5 text-gray-900 px-2 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6 chzn-select"
                  >
                    {currentBid?.supplier_name ? (
                      <option
                        value={
                          currentBid?.supplier +
                          "-#-" +
                          currentBid?.supplier_name
                        }
                      >
                        {currentBid?.supplier_name}
                      </option>
                    ) : (
                      ""
                    )}
                    <option>Select Supplier</option>
                    {suppliers
                      ? suppliers.map((supplier) => (
                          <option value={supplier.id + "-#-" + supplier.name}>
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
                    value={currentBid?.bid_date}
                    onChange={(e) => onCurrentBidChange("bid_date", e)}
                    type="date"
                    required
                    className="block w-full rounded-md border-0 py-1.5 text-gray-900 px-2 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
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
                    value={currentBid?.bid_count}
                    id="bid"
                    required
                    readOnly
                    className="block w-full rounded-md border-0 py-1.5 text-gray-900 px-2 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
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
                    onChange={(e) => onBidDocumentChange(e)}
                    className="block w-full rounded-md border-0 py-1.5 px-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                  />
                </div>
              </div>
            </div>

            {currentBid?.items &&
              currentBid?.items.map((item, index) => {
                return (
                  <div
                    key={index}
                    className="flex justify-evenly mt-5  px-2 py-2 rounded-md"
                  >
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
                            onCurrentBidItemChange(
                              item.item_required ?? "",
                              "item_required",
                              e,
                              currentBid?.bid_count?.toString() ?? ""
                            )
                          }
                          id="item_description"
                          required
                          className="block w-full rounded-md border-0 py-1.5 text-gray-900 px-2 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
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
                            onCurrentBidItemChange(
                              item.item_required ?? "",
                              "quantity",
                              e,
                              currentBid?.bid_count?.toString() ?? ""
                            )
                          }
                          type="number"
                          id="quantity"
                          className="block inpt w-full rounded-md border-0 py-1.5 text-gray-900 px-2 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
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
                              onCurrentBidItemChange(
                                item.item_required ?? "",
                                "unit_of_measurement",
                                e,
                                currentBid?.bid_count?.toString() ?? ""
                              )
                            }
                            autoComplete="unit_of_measurement"
                            className="block w-full rounded-md border-0 py-1.5 text-gray-900 px-2 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6"
                          >
                            {item.unit_of_measurement ? (
                              <option value={item.unit_of_measurement}>
                                {item.unit_of_measurement}
                              </option>
                            ) : (
                              ""
                            )}
                            {uom ? (
                              uom.map((uom) => (
                                <option value={uom.name}>{uom.name}</option>
                              ))
                            ) : (
                              <option>No Units</option>
                            )}
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
                              onCurrentBidItemChange(
                                item.item_required ?? "",
                                "vat",
                                e,
                                currentBid?.bid_count?.toString() ?? ""
                              )
                            }
                            autoComplete="vat"
                            className="block w-full rounded-md border-0 py-1.5 text-gray-900 px-2 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6"
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
                            onCurrentBidItemChange(
                              item.item_required ?? "",
                              "unit_price",
                              e,
                              currentBid?.bid_count?.toString() ?? ""
                            )
                          }
                          type="text"
                          id="unit_price"
                          required
                          className="block inpt w-full rounded-md border-0 py-1.5 text-gray-900 px-2 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
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
                onClick={onCloseCurrentBid}
                type="submit"
                className="rounded-md bg-gray-700 hover:bg-gray-600 text-sm font-semibold px-3 py-2 text-white shadow-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2"
              >
                <span className="ml-2">CANCEL</span>
              </button>
            </div>
            <div className="m-2">
              <button
                onClick={onCurrentBidSave}
                className="rounded-md text-blue-50 text-sm bg-blue-600 hover:bg-blue-500 px-3 py-2 font-semibold leading-6"
              >
                <span className="ml-2">SAVE BID</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const approvalsTable = (
    <div className="transition-all duration-300 bg-gulf-blue-100 p-4 rounded-lg border-l-4 border-blue-600">
      <div className="space-y-12 px-5 py-5">
        <div className="px-4 sm:px-0 mt-6 border-t border-gray-100 border-gray-900/10">
          <h2 className="text-base font-semibold leading-6 text-gray-900">
            Approvals
          </h2>

          <div className="overflow-auto px-2 py-2 mt-5 rounded-md">
            <table className="table-auto w-full text-left">
              <tbody>
                <tr className="text-gray-900">
                  <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                    FINANCE MANAGER
                  </td>
                  <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                    {fmApproval && fmApproval?.approver_name}
                  </td>
                  <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                    {fmApproval &&
                      fmApproval?.approval === "Rejected" &&
                      fmApproval?.justification}
                  </td>
                  <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                    {fmApproval &&
                      fmApproval?.approval === "Approved" &&
                      "APPROVED"}
                    {fmApproval &&
                      fmApproval?.approval === "Rejected" &&
                      "REJECTED"}
                    {committeeApprovalComplete && (
                      <div className="flex justify-content-evenly">
                        {requesterRole === "check" &&
                        Object.keys(fmApproval ?? {}).length === 0 ? (
                          <div className="flex justify-content-evenly">
                            <div className="m-2">
                              <button
                                onClick={() =>
                                  onApprovalApprove(
                                    "finance_manager",
                                    username ?? "",
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
                                  onApprovalJustificationModal(
                                    username ?? "",
                                    "finance_manager"
                                  )
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
                    {fmApproval && fmApproval?.approval_date
                      ? fmApproval?.approval_date.split(".")[0]
                      : ""}
                  </td>
                </tr>
                <tr className="text-gray-900">
                  <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                    GENERAL MANAGER
                  </td>
                  <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                    {gmApproval && gmApproval.approver_name}
                  </td>
                  <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                    {gmApproval &&
                      gmApproval.approval === "Rejected" &&
                      gmApproval.justification}
                  </td>
                  <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                    {gmApproval &&
                      gmApproval.approval === "Approved" &&
                      "APPROVED"}
                    {gmApproval &&
                      gmApproval.approval === "Rejected" &&
                      "REJECTED"}
                    {
                      <div className="flex justify-content-evenly">
                        {fmApproval &&
                        fmApproval?.approval === "Approved" &&
                        requesterRole === "approve" &&
                        Object.keys(gmApproval ?? {}).length === 0 ? (
                          <div className="flex justify-content-evenly">
                            <div className="m-2">
                              <button
                                onClick={() =>
                                  onApprovalApprove(
                                    "general_manager",
                                    username ?? "",
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
                                  onApprovalJustificationModal(
                                    username ?? "",
                                    "general_manager"
                                  )
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
                    }
                  </td>
                  <td className="border-b before:border-gray-700 after:border-gray-700 border-gray-700 px-2 py-2">
                    {gmApproval && gmApproval.approval_date
                      ? gmApproval.approval_date.split(".")[0]
                      : ""}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );

  const csDetailsView = (
    <div className="transition-all duration-300 bg-gulf-blue-100 p-4 rounded-lg border-l-4 border-blue-600">
      <h2 className="text-base font-semibold leading-6 text-gray-900">
        COMPERATIVE SCHEDULE DETAILS
      </h2>
      <p className="mt-1 max-w-2xl text-sm leading-6 text-gray-500">
        CS NO: {csId}
      </p>

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
              value={scopeOfWork}
              disabled={username === csOwner || csOwner === "" ? false : true}
              onChange={(e) => setScopeOfWork(e.target.value)}
              className="block w-full rounded-md border-0 py-1.5 px-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
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
              value={prNumber}
              onChange={(e) => setCsOwner(e.target.value)}
              disabled={username === csOwner || csOwner === "" ? false : true}
              id="pr_number"
              required
              className="block w-full rounded-md border-0 py-1.5 px-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
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
              value={prDate}
              onChange={(e) => setPrDate(e.target.value)}
              disabled={username === csOwner || csOwner === "" ? false : true}
              type="date"
              required
              className="block w-full rounded-md border-0 py-1.5 text-gray-900 px-2 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
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
              value={closingDate}
              onChange={(e) => setClosingDate(e.target.value)}
              disabled={username === csOwner || csOwner === "" ? false : true}
              type="date"
              required
              className="block w-full rounded-md border-0 py-1.5 text-gray-900 px-2 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
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
                  onChange={(e) => setClosingTime(e.target.value)}
                  disabled={
                    username === csOwner || csOwner === "" ? false : true
                  }
                  className="rounded-md block border-none w-full py-1.5 px-2 text-gray-900 sm:max-w-xs sm:text-sm sm:leading-6"
                >
                  {closingTime ? (
                    <option value={closingTime}>{closingTime}</option>
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
              onChange={(e) => onSelectChange("proc_ref", e)}
              disabled={username === csOwner || csOwner === "" ? false : true}
              className="block w-full rounded-md border-0 py-1.5 px-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6 chzn-select"
            >
              {procPlan ? (
                <option value={procPlan?.proc_ref}>{procPlan?.description}</option>
              ) : (
                ""
              )}
              {procPlans
                ? procPlans.map((plan) => (
                    <option value={plan.proc_ref}>{plan.description}</option>
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
              onChange={(e) => onSelectChange("currency", e)}
              disabled={username === csOwner || csOwner === "" ? false : true}
              className="block w-full rounded-md border-0 py-1.5 px-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6 chzn-select"
            >
              {currency ? (
                <option value={currency.id}>{currency.currency}</option>
              ) : (
                <option value="">Select Currency</option>
              )}
              {currencies
                ? currencies.map((currency) => (
                    <option value={currency.id}>{currency.currency}</option>
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
              value={refDate}
              onChange={(e) => setRefDate(e.target.value)}
              disabled={username === csOwner || csOwner === "" ? false : true}
              type="date"
              required
              className="block w-full rounded-md border-0 py-1.5 text-gray-900 px-2 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
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
              value={dateTenderOpened}
              onChange={(e) => setDateTenderOpened(e.target.value)}
              disabled={username === csOwner || csOwner === "" ? false : true}
              type="date"
              required
              className="block w-full rounded-md border-0 py-1.5 text-gray-900 px-2 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
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
              value={tenderAdjudicationCommitteeDate}
              onChange={(e) =>
                setTenderAdjudicationCommitteeDate(e.target.value)
              }
              disabled={username === csOwner || csOwner === "" ? false : true}
              type="date"
              required
              className="block w-full rounded-md border-0 py-1.5 text-gray-900 px-2 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
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
              onChange={(e) => onFileInputChange("advert", e)}
              disabled={username === csOwner || csOwner === "" ? false : true}
              type="file"
              id="advert"
              required
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
            <a href={advertUrl} rel="noopener noreferrer">
              View Advert Document
            </a>
          </div>
        </div>
      </div>
      <div className="flex justify-evenly mt-5  px-2 py-2 rounded-md">
        {prAttachments &&
          prAttachments?.length > 0 &&
          prAttachments?.map((attachment) => {
            return (
              <div className="flex-1 w-20 ml-1">
                <div className="mt-2">
                  <div className="rounded bg-white border border-1 shadow-lg text-center m-2">
                    <a
                      href={attachment.attachment_url}
                      className="text-center text-blue-600  p-3 sm whitespace-normal max-w-full"
                    >
                      {attachment.name}
                    </a>
                  </div>
                </div>
              </div>
            );
          })}
      </div>

      {(username === csOwner || !csid) && !approvalsComplete ? (
        <div className="flex justify-center mt-10 px-3 py-3">
          {csid ? (
            <div className="w-30 m-2">
              <button
                style={{ width: "100%" }}
                onClick={onUpdateSchedule}
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
                onClick={onSaveSchedule}
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
  );

  const additionalInfo = (
    <div className="transition-all duration-300 bg-gulf-blue-100 p-4 rounded-lg border-l-4 border-blue-600">
      <h2 className="text-base font-semibold leading-6 text-gray-900">
        Additional Information (For Procurement Admin Only)
      </h2>

      <div className="flex justify-evenly mt-5  px-2 py-2 rounded-md">
        <div className="flex-1 w-100">
          <label
            htmlFor="additionalNotes"
            className="block text-sm font-medium leading-6 text-gray-900"
          >
            Notes
          </label>
          <div className="mt-2">
            <textarea
              id="additionalNotes"
              name="additionalNotes"
              value={additionalNotes}
              disabled={requesterRole === "verify" ? false : true}
              onChange={onAdditionalNotesChange}
              className="block w-full rounded-md border-0 py-2 px-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
            ></textarea>
          </div>
        </div>
      </div>

      {requesterRole === "verify" && additionalNotes ? (
        <div className="flex justify-center mt-2 px-3 py-3">
          <div className="w-50 m-2">
            <button
              style={{ width: "100%" }}
              onClick={onAdditionalNotesSubmit}
              name="save_next"
              className="rounded-md bg-blue-700 hover:bg-blue-550 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
            >
              SUBMIT NOTES
            </button>
          </div>
        </div>
      ) : (
        ""
      )}
    </div>
  );

  const buyersInfo = (
    <div className="transition-all duration-300 bg-gulf-blue-100 p-4 rounded-lg border-l-4 border-blue-600">
      <h2 className="text-base font-semibold leading-6 text-gray-900">
        Buyer's Award Notes (For Buyers Only)
      </h2>

      <div className="flex justify-evenly mt-5  px-2 py-2 rounded-md">
        <div className="flex-1 w-100">
          <label
            htmlFor="buyersNotes"
            className="block text-sm font-medium leading-6 text-gray-900"
          >
            Notes
          </label>
          <div className="mt-2">
            <textarea
              id="buyersNotes"
              name="buyersNotes"
              value={buyersNotes}
              disabled={requesterRole === "procurement" ? false : true}
              onChange={onBuyersNotesChange}
              className="block w-full rounded-md border-0 py-2 px-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
            ></textarea>
          </div>
        </div>
      </div>

      {requesterRole === "procurement" && buyersNotes ? (
        <div className="flex justify-center mt-2 px-3 py-3">
          <div className="w-50 m-2">
            <button
              style={{ width: "100%" }}
              onClick={onBuyersNotesSubmit}
              name="save_next"
              className="rounded-md bg-blue-700 hover:bg-blue-550 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
            >
              SUBMIT NOTES
            </button>
          </div>
        </div>
      ) : (
        ""
      )}
    </div>
  );

  const committeeTableComp = (
    <div className="transition-all duration-300 bg-gulf-blue-100 p-4 rounded-lg border-l-4 border-blue-600">
      <div className="space-y-12 px-5 py-5">
        <div className="px-4 sm:px-0 mt-6 border-t border-gray-100 border-gray-900/10">
          <h2 className="text-base font-semibold leading-6 text-gray-900">
            Committee Members
          </h2>

          <div className="px-2 py-2 mt-5 rounded-md">
            <div className="grid grid-cols-3 gap-4 px-2 py-2 items-center">
              <div>
                <div className="mt-2">
                  {username === csOwner ? (
                    <select
                      onChange={(text) =>
                        onCommitteeChange("memberPosition", text)
                      }
                      id="memberPosition"
                      name="memberPosition"
                      className="block w-full rounded-md border-0 py-2 px-2 text-gray-900 shadow-sm sm:max-w-xs sm:text-sm sm:leading-6 chzn-select"
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
              <div>
                <div className="mt-2">
                  {username === csOwner ? (
                    <div>
                      {username === csOwner && (
                        <Select
                          id="memberUserName"
                          name="memberUserName"
                          className="block w-full rounded-md border-0 py-2 text-gray-900 sm:max-w-xs sm:text-sm sm:leading-6 chzn-select"
                          options={userOptions}
                          styles={customStyles}
                          onChange={(option) =>
                            onCommitteeSelect(
                              "memberUserName",
                              option?.value ?? ""
                            )
                          }
                          placeholder="Search Member Name"
                        />
                      )}
                    </div>
                  ) : (
                    ""
                  )}
                </div>
              </div>
              {username === csOwner &&
              !approvalsComplete &&
              member?.memberPosition &&
              member?.memberUserName ? (
                <div className="w-30">
                  <button
                    style={{ width: "100%" }}
                    onClick={onAddCommitteeMembers}
                    name="save_next"
                    className="rounded-md bg-blue-925 hover:bg-blue-550 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
                  >
                    ADD MEMBER
                  </button>
                </div>
              ) : (
                ""
              )}
            </div>
            <div className="grid grid-cols-3 gap-4 bg-blue-100 border before:border-blue-400 after:border-blue-700 border-blue-400 px-2 py-2 m-2 rounded-md">
              <div style={{ width: "100%" }}>
                <p className="font-medium leading-6 text-gray-900">CREATED BY</p>
                <p>{creator}</p>
              </div>
              <div style={{ width: "100%" }}>
                <p className="font-medium leading-6 text-gray-900">ACTION</p>
                <p>INITIATED</p>
              </div>
              <div style={{ width: "100%" }}>
                <p className="font-medium leading-6 text-gray-900">DATE</p>
                <p>{createdAt ? createdAt.split(".")[0] : ""}</p>
              </div>
            </div>

            {committeeMembers &&
              committeeMembers.map((member, key) => {
                return (
                  <div className={getCommitteeClassNames(member.memberApproval??"")}>
                    <div style={{ width: "100%" }}>
                      <p className="font-medium leading-6 text-gray-900">ROLE</p>
                      <p>{member?.memberPosition?.toUpperCase()}</p>
                    </div>
                    <div style={{ width: "100%" }}>
                      <p className="font-medium leading-6 text-gray-900">MEMBER</p>
                      <p>
                        {member.memberName
                          ? member.memberName
                          : member.memberUserName}
                      </p>
                    </div>
                    <div style={{ width: "100%" }}>
                      <p className="font-medium leading-6 text-gray-900">Comment</p>
                      <p>{member.committeeJustification}</p>
                    </div>
                    <div style={{ width: "100%" }}>
                      <p className="font-medium leading-6 text-gray-900">DATE</p>
                      <p>
                        {member.committeeDate
                          ? member.committeeDate.split(".")[0]
                          : ""}
                      </p>
                    </div>
                    <div style={{ width: "100%" }} className="text-center">
                      <p className="font-medium leading-6 text-gray-900">ACTION</p>
                      <p>
                        {member.memberApproval === "Approved" && "APPROVED"}
                        {member.memberApproval === "Rejected" && "REJECTED"}
                        {(member.memberApproval === "" ||
                          member.memberApproval === null) && (
                          <div style={{ width: "100%" }} className="flex justify-center">
                            {username === csOwner && !approvalsComplete ? (
                              <div style={{ width: "100%" }} className="m-1">
                                <button
                                  onClick={() =>
                                    onRemoveCommitteeMember(
                                      key,
                                      member.memberUserName
                                    )
                                  }
                                  name="save_next"
                                  className="rounded-md bg-red-600 hover:bg-red-500 px-3 py-2 text-sm font-semibold text-white shadow-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2"
                                >
                                  REMOVE
                                </button>
                              </div>
                            ) : (
                              ""
                            )}
                            {username === member.memberUserName ? (
                              <div style={{ width: "100%" }} className="flex justify-content-between">
                                <div style={{ width: "45%" }} className="m-1">
                                  <button
                                    onClick={() =>
                                      onCommitteeApprove(
                                        member.memberUserName,
                                        "Approved",
                                        ""
                                      )
                                    }
                                    name="save_next"
                                    className="rounded-md bg-blue-600 hover:bg-blue-400 px-3 py-2 text-sm font-semibold text-white shadow-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
                                  >
                                    APPROVE
                                  </button>
                                </div>
                                <div style={{ width: "45%" }} className="m-1">
                                  <button
                                    onClick={() =>
                                      onCommitteeJustificationModal(
                                        member?.memberUserName
                                      )
                                    }
                                    name="save_next"
                                    className="rounded-md bg-red-600 hover:bg-red-400 px-2 py-2 text-sm font-semibold text-white shadow-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
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
                      </p>
                    </div>
                  </div>
                );
              })}
          </div>
        </div>
      </div>
    </div>
  );

  const rankingTableComp = (
    <div className="transition-all duration-300 bg-gulf-blue-100 p-4 rounded-lg border-l-4 border-blue-600">
      <div className="space-y-12 px-5 py-5">
        <div className="px-4 sm:px-0 mt-6 border-t border-gray-100 border-gray-900/10">
          <h2 className="text-base font-semibold leading-6 text-gray-900">
            RANKING TABLE
          </h2>

          <div className="overflow-auto px-2 py-2 mt-5 rounded-md">
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
                {rankings &&
                  rankings.map((rank, key) => {
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

  return (
    <div>
      {addItemsModal && itemsModal}
      {addBidModal && bidsModal}
      {onAddSupplier && supplierModal}
      {updateBidModal && updateBidModalComp}
      {committeeJustificationModal && rejectJustification}
      {approvalsJustificationModal && rejectApprovalJustification}
      {response?.open && responseModal}
      {/* {loadingModal} */}
      <div className="space-y-12 px-5 py-5">
        <div className="px-4 sm:px-0">
            <div className="m-2">
            <button
                style={{ width: "100%" }}
                onClick={onAddSuppliersModal}
                className="rounded-md bg-nepal-950 hover:bg-nepal-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
            >
                ADD NEW SUPPLIER
            </button>
            </div>
          {fetchPR && (
            <div className="transition-all duration-300 bg-gulf-blue-100 p-4 rounded-lg border-l-4 border-blue-600 mt-5 mb-5">
              <div className="flex justify-evenly items-end mt-3 px-2 py-2">
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
                      onChange={onFetchPrNumberChange}
                      defaultValue={prNumber}
                      className="block w-full rounded-md border-0 py-2 px-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                    />
                  </div>
                </div>
                <div className="flex-1 ml-2 w-40">
                  <div className="w-30">
                    <button
                      style={{ width: "100%" }}
                      onClick={() => onFetchPR(prNumber)}
                      name="save_next"
                      className="rounded-md bg-blue-925 hover:bg-blue-550 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
                    >
                      FETCH PR
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
          {csDetailsView}
        </div>

        {username === csOwner ? (
          <div className="m-2">
            <button
              style={{ width: "100%" }}
              onClick={onAddItemsModal}
              className="rounded-md bg-nepal-950 hover:bg-nepal-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
            >
              ADD SCHEDULE ITEMS
            </button>
          </div>
        ) : (
          ""
        )}

        {bids &&
          bids.map((loopBid) => {
            return (
              <div
                id="opening_rfq"
                className="transition-all duration-300 bg-gulf-blue-100 p-4 rounded-lg border-l-4 border-blue-600 pb-12"
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
                        <p>{loopBid.supplier_name}</p>
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
                        <p>{loopBid.bid_date}</p>
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
                        <p>{loopBid?.bid_count}</p>
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
                          href={
                            loopBid?.encoded_bid_document ||
                            currentBid?.bid_document ||
                            loopBid?.bid_document ||
                            loopBid?.bid_document_url
                              ? loopBid.bid_document_url
                              : "#"
                          }
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          {loopBid?.encoded_bid_document ||
                          currentBid?.bid_document ||
                          loopBid?.bid_document ||
                          loopBid?.bid_document_url
                            ? "View Document"
                            : "NO DOCUMENT"}
                        </a>
                      </div>
                    </div>
                  </div>

                  {loopBid?.items?.map((item) => {
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
                            <p>{item.item_required}</p>
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

                {username === csOwner && !approvalsComplete ? (
                  <div className="flex justify-center mt-5 px-3 py-3">
                    <div className="m-2">
                      <button
                        onClick={() =>
                          onUpdateBidModal(loopBid?.bid_count ?? 0)
                        }
                        className="rounded-md text-gray-50 text-sm bg-blue-925 hover:bg-blue-550 px-3 py-2 font-semibold leading-6"
                      >
                        UPDATE BID
                      </button>
                    </div>
                    <div className="m-2">
                      <button
                        onClick={() =>
                          onDeleteBidModal(
                            loopBid.bid_count,
                            loopBid.supplier_name
                          )
                        }
                        type="submit"
                        className="rounded-md bg-red-600 hover:bg-red-400 text-sm font-semibold px-3 py-2 text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
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

        {(csItems?.length ?? 0 > 0) &&
        (directPurchaseLimit) &&
        username === csOwner &&
        !approvalsComplete ? (
          <div className="m-2">
            <button
              style={{ width: "100%" }}
              onClick={onAddBidModal}
              className="rounded-md bg-nepal-950 hover:bg-nepal-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
            >
              ADD BID
            </button>
          </div>
        ) : (
          ""
        )}

        {(bids?.length ?? 0 > 0) &&
        username === csOwner &&
        !approvalsComplete ? (
          <div className="m-2">
            <button
              style={{ width: "100%" }}
              onClick={onAddComplianceTable}
              className="rounded-md bg-nepal-950 hover:bg-nepal-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
            >
              ADD COMPLIANCES
            </button>
          </div>
        ) : (
          ""
        )}

        {compliance?.length ?? 0 > 0 ? complianceTableComp : ""}

        {(compliance?.length ?? 0 > 0) &&
        username === csOwner &&
        !approvalsComplete ? (
          <div className="m-2">
            <button
              style={{ width: "100%" }}
              onClick={onCloseCS}
              className="rounded-md bg-nepal-950 hover:bg-nepal-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
            >
              RANK BIDS
            </button>
          </div>
        ) : (
          ""
        )}

        {rankings?.length ?? 0 > 0 ? rankingTableComp : ""}

        {requesterRole === "verify" ? additionalInfo: ""}

        {requesterRole === "procurement" ? buyersInfo: ""}

        {rankings?.length ?? 0 > 0 ? committeeTableComp : ""}

        {(committeeMembers?.length ?? 0 > 0) &&
        username === csOwner &&
        !approvalsComplete ? (
          <div className="m-2">
            <button
              style={{ width: "100%" }}
              onClick={onSubmitCommitee}
              className="rounded-md bg-nepal-950 hover:bg-nepal-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
            >
              SUBMIT COMMITTEE
            </button>
          </div>
        ) : (
          ""
        )}
        {committeeMembers?.length ?? 0 > 2 ? approvalsTable : ""}

        <div className="flex m-2">
          <button
            style={{ width: username === csOwner ? "50%" : "100%" }}
            onClick={() => {
              console.log("going back ...");
              window.history.back();
            }}
            className="rounded-md bg-nepal-950 hover:bg-nepal-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 m-1"
          >
            GO BACK TO SCHEDULES
          </button>
          {username === csOwner && (
            <button
              style={{ width: "50%" }}
              onClick={() => {
                window.location.href = base_url + "/cancel_schedule/" + csId;
              }}
              className="rounded-md bg-red-800 hover:bg-red-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-red-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-red-600 m-1"
            >
              DELETE SCHEDULE
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
