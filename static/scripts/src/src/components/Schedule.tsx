import React, { useEffect, useState } from 'react';

interface ICurrency {
    id: number;
    currency: string;
}

interface IProcPlan {
    id: number;
    plan: string;
}

interface IPRAttachment {
    id: number;
    attachment: string;
}

export default function Schedule({ base_url, username, prid, csid }: { base_url: string, username: string | null, prid: string | null, csid: string | null}) {

    const [loading, setLoading] = useState<boolean>(false);
    const [requesterRole, setRequesterRole] = useState<string>("");
    const [csId, setCsId] = useState<string>("");
    const [csOwner, setCsOwner] = useState<string>("");
    const [creator, setCreator] = useState<string>("");
    const [createdAt, setCreatedAt] = useState<string>("");
    const [committeeApprovalComplete, setCommitteeApprovalComplete] = useState<boolean>(false);
    const [planRef, setPlanRef] = useState<string>("");
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
    const [tenderAdjudicationCommitteeDate, setTenderAdjudicationCommitteeDate] = useState<string>("");
    const [advert, setAdvert] = useState(null);
    const [advertUrl, setAdvertUrl] = useState(null);
    const [bidCount, setBidCount] = useState(0);
    const [currentBid, setCurrentBid] = useState({});
    const [bids, setBids] = useState([]);
    const [addBidModal, setAddBidModal] = useState(false);
    const [updateBidModal, setUpdateBidModal] = useState(false);
    const [csItems, setCsItems] = useState([]);
    const [csItemCount, setCsItemCount] = useState(0);
    const [addItemsModal, setAddItemsModal] = useState(false);
    const [complianceTable, setComplianceTable] = useState(false);
    const [compliance, setCompliance] = useState([]);
    const [complianceRemarks, setComplianceRemarks] = useState([]);
    const [showSamples, setShowSamples] = useState("no");
    const [showSiteVisit, setShowSiteVisit] = useState("no");
    const [rankingTable, setRankingTable] = useState(false);
    const [rankings, setRankings] = useState([]);
    const [committeeTable, setCommitteeTable] = useState(false);
    const [committeeMembers, setCommitteeMembers] = useState([]);
    const [committeeJustificationModal, setCommitteeJustificationModal] = useState(false);
    const [member, setMember] = useState({
      memberName: "",
      memberUserName: "",
      memberPosition: "",
      memberApproval: "",
    });
    const [gmApproval, setGmApproval] = useState(null);
    const [fmApproval, setFmApproval] = useState(null);
    const [approvalsComplete, setApprovalsComplete] = useState(false);
    const [approvalsJustificationModal, setApprovalsJustificationModal] = useState(false);
    const [users, setUsers] = useState([]);
    const [selectUserOptions, setSelectUserOptions] = useState([
      { value: 'chairman', label: 'Chairman' },
      { value: 'finance', label: 'Finance' },
      { value: 'procurement', label: 'Procurement' },
      { value: 'user', label: 'User' },
      { value: 'other', label: 'Other' },
    ]);
    const [searchedUser, setSearchedUser] = useState<string>("");
    const [selectedUser, setSelectedUser] = useState(null);
    const [filteredUsers, setFilteredUsers] = useState([]);
    const [currentApprover, setCurrentApprover] = useState({
      username: "",
      justification: "",
      role: "",
    });
    const [prItems, setPrItems] = useState([]);
    const [suppliers, setSuppliers] = useState([]);
    const [procPlans, setProcPlans] = useState([]);
    const [uom, setUom] = useState(null);
    const [authUser, setAuthUser] = useState({});
    const [username, setUsername] = useState<string>("");
    const [fetchPR, setFetchPR] = useState(false);
    const [onAddSupplier, setOnAddSupplier] = useState(false);
    const [newSupplier, setNewSupplier] = useState({
      supplier_name: "",
      supplier_contact: "",
      supplier_email: "",
      supplier_address: "",
    });
    const [response, setResponse] = useState({
      open: false,
      message: "",
      title: "",
    });
    const [additionalNotes, setAdditionalNotes] = useState<string>("");

    console.log("csid: ", csid);
    return (
        <div>
            <h1>Schedules ghfjh: {csid}</h1>
            <p>Here is the schedule for the event. {base_url} {username} {prid}</p>
        </div>
    )
}