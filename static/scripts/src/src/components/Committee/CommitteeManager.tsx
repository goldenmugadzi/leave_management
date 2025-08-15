import React, { useState, useCallback, useEffect } from 'react';
import { useScheduleContext } from '../../context/ScheduleContext';
import { ICommittee, IUser } from '../../types/scheduleTypes';
import { buildApiUrl, getApiEndpoints, getCurrentModule, API_MODULES, MODULE_CONFIG } from '../../config/apiEndpoints';

// Helper function to get CSRF token from cookies
const getCookie = (name: string) => {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop()?.split(';').shift();
  return null;
};

interface IUserOption {
  value: string;
  label: string;
}

interface CommitteeManagerProps {
  users: IUser[];
  committeeMembers: ICommittee[];
  onSaveCommittee: (committee: ICommittee[]) => Promise<void>;
  isCreator?: boolean; // Add isCreator prop
  csrfToken?: string; // Add CSRF token prop
}

const CommitteeManager: React.FC<CommitteeManagerProps> = ({ 
  users,
  committeeMembers: committee,
  onSaveCommittee,
  isCreator = false, // Default to false for safety
  csrfToken = "" // Default to empty string
}) => {
  const { username, csId, base_url } = useScheduleContext();
  
  // Local state for committee management
  const [localCommitteeMembers, setLocalCommitteeMembers] = useState<ICommittee[]>(committee);
  
  // Update committee members locally
  const updateCommitteeMembers = useCallback((members: ICommittee[]) => {
    setLocalCommitteeMembers(members);
  }, []);
  
  // Clear committee cache
  const clearCommitteeCache = useCallback(() => {
    setLocalCommitteeMembers([]);
  }, []);
  
  // Use local committee members
  const currentCommittee = localCommitteeMembers;

  // State for user justification
  const [justification, setJustification] = useState('');
  const [showJustificationModal, setShowJustificationModal] = useState(false);
  const [currentMember, setCurrentMember] = useState<string>('');
  
  // State for tracking if add committee modal is shown
  const [showAddCommitteeModal, setShowAddCommitteeModal] = useState(false);
  
  // State for search term with debouncing
  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<IUserOption[]>([]);
  
  // State for add member modal
  const [selectedUser, setSelectedUser] = useState<IUserOption | null>(null);
  const [selectedPosition, setSelectedPosition] = useState<string>("");
  const [showUserDropdown, setShowUserDropdown] = useState(false);
  const positionOptions = [
    { value: "CHAIRMAN", label: "Chairman" },
    { value: "USER", label: "User" },
    { value: "PROCUREMENT ADMIN", label: "Procurement Admin" },
    { value: "FINANCE", label: "Finance" },
  ];
  
  // Debounce search term with reduced delay and loading state
  useEffect(() => {
    setIsSearching(true);
    const timer = setTimeout(() => {
      setDebouncedSearchTerm(searchTerm);
      setIsSearching(false);
    }, 300); // Optimized for reduced API calls while typing
    
    return () => {
      clearTimeout(timer);
      setIsSearching(false);
    };
  }, [searchTerm]);

  // Committee data is passed from parent component
  // No need for redundant API calls here

  // Server-side search for users
  const searchUsers = useCallback(async (searchQuery: string) => {
    if (!searchQuery || searchQuery.length < 2) {
      setSearchResults([]);
      return;
    }

    setIsSearching(true);
    try {
      // Get the current module to construct the correct API endpoint
      const currentModule = getCurrentModule();
      
      // Use the centralized MODULE_CONFIG to get the correct users endpoint
      let usersEndpoint = '';
      if (currentModule === API_MODULES.COMPARATIVE_SCHEDULES) {
        usersEndpoint = MODULE_CONFIG.comparativeSchedules.users;
      } else if (currentModule === API_MODULES.DIRECT_PURCHASE) {
        usersEndpoint = MODULE_CONFIG.directPurchase.users;
      } else if (currentModule === API_MODULES.RESTRICTED_BIDDING) {
        usersEndpoint = MODULE_CONFIG.restrictedBidding.users;
      } else {
        // Fallback to comparative schedules
        usersEndpoint = MODULE_CONFIG.comparativeSchedules.users;
      }
      
      const url = buildApiUrl(base_url, `${usersEndpoint}?search=${encodeURIComponent(searchQuery)}&limit=20`);
      const response = await fetch(url);
      const data = await response.json();
      
      if (data.users) {
        const userOptions = data.users.map((user: IUser) => ({
          value: user.username,
          label: `${user.first_name} ${user.last_name} (${user.username})${user.is_active === false ? ' [INACTIVE]' : ''}`
        }));
        setSearchResults(userOptions);
      }
    } catch (error) {
      console.error('Error searching users:', error);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  }, [base_url]);

  // Trigger search when debounced search term changes
  useEffect(() => {
    searchUsers(debouncedSearchTerm);
  }, [debouncedSearchTerm, searchUsers]);

  // Get users to display in dropdown
  const getUsersToDisplay = useCallback(() => {
    if (!debouncedSearchTerm || debouncedSearchTerm.length < 2) {
      // Show limited default users for better performance
      return users.slice(0, 20).map(user => ({
        value: user.username,
        label: `${user.first_name} ${user.last_name} (${user.username})${user.is_active === false ? ' [INACTIVE]' : ''}`
      }));
    }
    return searchResults;
  }, [debouncedSearchTerm, searchResults, users]);

  // Add committee members modal
  const onAddCommitteeMembers = useCallback(() => {
    setSearchTerm(''); // Reset search when opening modal
    setDebouncedSearchTerm(''); // Also reset debounced term
    setSelectedUser(null); // Clear any selected user
    setSelectedPosition(''); // Clear any selected position
    setShowUserDropdown(false); // Hide dropdown
    setShowAddCommitteeModal(true);
  }, []);
  
  // Handle committee member selection from dropdown
  const onSelectUserFromDropdown = useCallback((userOption: IUserOption) => {
    setSelectedUser(userOption);
    setSearchTerm(userOption.label.split(' (')[0]); // Set search term to user's name
    setShowUserDropdown(false);
  }, []);

  // Handle search input focus and changes
  const onSearchInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchTerm(value);
    setShowUserDropdown(value.length >= 2); // Show dropdown when search has 2+ characters
    if (value.length < 2) {
      setSelectedUser(null); // Clear selection if search is too short
    }
  }, []);

  const onSearchInputFocus = useCallback(() => {
    if (searchTerm.length >= 2) {
      setShowUserDropdown(true);
    }
  }, [searchTerm]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Element;
      if (!target.closest('.user-search-container')) {
        setShowUserDropdown(false);
      }
    };

    if (showUserDropdown) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showUserDropdown]);

  // Add committee member from modal
  const onAddCommitteeMemberModal = useCallback(() => {
    if (!selectedUser || !selectedPosition) {
      alert("Please select both a user and a position.");
      return;
    }
    const username = selectedUser.value;
    const memberName = selectedUser.label.split(' (')[0];
    // Check if member already exists
    const memberExists = currentCommittee.some(m => m.memberUserName === username);
    if (memberExists) {
      alert('This member is already in the committee');
      return;
    }
    // Check if position already taken
    const positionExists = currentCommittee.some(m => m.memberPosition === selectedPosition);
    if (positionExists) {
      alert('This position is already assigned to another member');
      return;
    }
    const newCommittee = [
      ...currentCommittee,
      {
        memberUserName: username,
        memberName,
        memberPosition: selectedPosition,
        committeeStatus: 'Pending',
        memberApproval: 'Pending',
        committeeJustification: '',
        committeeDate: new Date().toISOString().split('T')[0]
      }
    ];
    updateCommitteeMembers(newCommittee);
    setShowAddCommitteeModal(false);
    setSearchTerm("");
    setDebouncedSearchTerm("");
    setSelectedUser(null);
    setSelectedPosition("");
    setShowUserDropdown(false);
  }, [committee, updateCommitteeMembers, selectedUser, selectedPosition]);
  
  // Delete committee member from backend
  const deleteCommitteeMember = useCallback(async (username_: string) => {
    try {
      const token = csrfToken || getCookie("csrftoken") || "";
      const formData = new FormData();
      formData.append("cs_id", csId || "");
      formData.append("username", username_);
      formData.append("csrfmiddlewaretoken", token);

      const requestOptions = {
        method: "POST",
        headers: {
          "X-CSRFToken": token,
        },
        body: formData,
      };

      const response = await fetch(buildApiUrl(base_url, getApiEndpoints().CS_DELETE_COMMITTEE_MEMBER), requestOptions);
      const data = await response.json();

      if (data.success) {
        return true;
      } else {
        console.error("❌ Failed to delete committee member:", data.message);
        return false;
      }
    } catch (error) {
      console.error("❌ Error deleting committee member:", error);
      return false;
    }
  }, [csrfToken, csId, base_url]);

  // Clear all committee members from backend
  const clearAllCommitteeMembers = useCallback(async () => {
    try {
      // Delete each committee member one by one
      const deletePromises = currentCommittee.map(member => 
        deleteCommitteeMember(member.memberUserName)
      );
      
      const results = await Promise.all(deletePromises);
      const successCount = results.filter(result => result).length;
      const failureCount = results.filter(result => !result).length;
      
      if (failureCount > 0) {
        console.warn(`⚠️ ${failureCount} committee members failed to delete from backend`);
        alert(`Warning: ${failureCount} committee members failed to delete from server. Some changes may not persist.`);
      }
      
      // Always clear local state regardless of backend results
      clearCommitteeCache();
      
      return successCount === currentCommittee.length;
    } catch (error) {
      console.error("❌ Error clearing committee members:", error);
      alert("Error clearing committee members. Please try again.");
      return false;
    }
  }, [committee, deleteCommitteeMember, clearCommitteeCache]);

  // Handle committee member removal
  const onRemoveCommitteeMember = useCallback(async (index: number, username_: string) => {
    // First, try to delete from backend
    const deleteSuccess = await deleteCommitteeMember(username_);
    
    if (deleteSuccess) {
          // If backend deletion was successful, update local state
    const updated = [...currentCommittee];
    updated.splice(index, 1);
    updateCommitteeMembers(updated);
  } else {
    // If backend deletion failed, show error but still update local state
    console.warn("⚠️ Backend deletion failed, but updating local state");
    alert("Warning: Failed to delete committee member from server. The change may not persist.");
    const updated = [...currentCommittee];
    updated.splice(index, 1);
    updateCommitteeMembers(updated);
  }
  }, [currentCommittee, updateCommitteeMembers, deleteCommitteeMember]);
  
  // Open justification modal
  const onOpenJustificationModal = useCallback((username_: string) => {
    setCurrentMember(username_);
    setShowJustificationModal(true);
  }, []);
  
  // Submit justification
  const onSubmitJustification = useCallback((
    username_: string,
    approval_: string,
    justification_: string
  ) => {
    const updated = committee.map(member => {
      if (member.memberUserName === username_) {
        return {
          ...member,
          memberApproval: approval_,
          committeeJustification: justification_
        };
      }
      return member;
    });
    updateCommitteeMembers(updated);
    
    setShowJustificationModal(false);
  }, [committee, updateCommitteeMembers]);
  
  // Submit committee
  const onSubmitCommittee = useCallback(async () => {
    try {
      // Validation
      if (currentCommittee.length === 0) {
        alert('Please add at least one committee member');
        return;
      }
      
      await onSaveCommittee(currentCommittee);
    } catch (error) {
      console.error('Error saving committee:', error);
      alert('Error saving committee');
    }
  }, [currentCommittee, onSaveCommittee]);
  
  // Helper function to get style classes for approval status
  const getCommitteeClassNames = useCallback((approvalStatus: string) => {
    switch (approvalStatus) {
      case "Approved":
        return "bg-green-100 text-green-800";
      case "Rejected":
        return "bg-red-100 text-red-800";
      default:
        return "bg-yellow-100 text-yellow-800";
    }
  }, []);

  return (
    <div className="mt-8">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-gray-800">Committee Members</h2>
        <div className="flex space-x-2">
          {/* Only show Add Committee Member button if user is creator */}
          {isCreator && (
            <button
              type="button"
              onClick={onAddCommitteeMembers}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
            >
              Add Committee Member
            </button>
          )}
          
          {/* Only show Clear Committee button if user is creator */}
          {isCreator && currentCommittee.length > 0 && (
            <button
              type="button"
              onClick={async () => {
                if (confirm('Are you sure you want to clear all committee members?')) {
                  await clearAllCommitteeMembers();
                }
              }}
              className="inline-flex items-center px-4 py-2 border border-red-300 text-sm font-medium rounded-md shadow-sm text-red-700 bg-white hover:bg-red-50"
            >
              Clear Committee
            </button>
          )}

        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Name
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Position
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Date
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {currentCommittee.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-4 text-center text-sm text-gray-500">
                  No committee members added yet.
                  {!isCreator && (
                    <div className="mt-2 text-xs text-gray-400">
                      Only the creator can add committee members.
                    </div>
                  )}
                </td>
              </tr>
            ) : (
              currentCommittee.map((member, index) => (
                <tr key={member.memberUserName} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="flex-shrink-0 h-10 w-10">
                        <div className="h-10 w-10 rounded-full bg-indigo-100 flex items-center justify-center">
                          <span className="text-sm font-medium text-indigo-600">
                            {member.memberName.split(' ').map(n => n[0]).join('').toUpperCase()}
                          </span>
                        </div>
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">{member.memberName}</div>
                        <div className="text-sm text-gray-500">@{member.memberUserName}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {member.memberPosition || 'Not specified'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getCommitteeClassNames(member.memberApproval || 'Pending')}`}>
                      {member.memberApproval || 'Pending'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {member.committeeDate ? new Date(member.committeeDate).toLocaleDateString() : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    {member.memberUserName === username ? (
                      <>
                        <button
                          type="button"
                          onClick={() => onOpenJustificationModal(member.memberUserName)}
                          className="text-indigo-600 hover:text-indigo-900 mr-3"
                          disabled={member.memberApproval !== 'Pending'}
                        >
                          Approve
                        </button>
                        <button
                          type="button"
                          onClick={() => onOpenJustificationModal(member.memberUserName)}
                          className="text-red-600 hover:text-red-900 mr-3"
                          disabled={member.memberApproval !== 'Pending'}
                        >
                          Reject
                        </button>
                      </>
                    ) : isCreator ? (
                      <button
                        type="button"
                        onClick={() => onRemoveCommitteeMember(index, member.memberUserName)}
                        className="text-red-600 hover:text-red-900"
                      >
                        Remove
                      </button>
                    ) : (
                      <span className="text-gray-400">No actions available</span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Only show Save Committee button if user is creator and there are committee members */}
      {isCreator && currentCommittee.length > 0 && (
        <div className="mt-6 flex justify-end">
          <button
            type="button"
            onClick={onSubmitCommittee}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
          >
            Save Committee
          </button>
        </div>
      )}

      {/* Add Committee Member Modal */}
      {showAddCommitteeModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 transition-opacity" aria-hidden="true">
              <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
            </div>
            <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <div className="sm:flex sm:items-start">
                  <div className="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-blue-100 sm:mx-0 sm:h-10 sm:w-10">
                    <svg className="h-6 w-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                    </svg>
                  </div>
                  <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left w-full">
                    <h3 className="text-lg leading-6 font-medium text-gray-900">
                      Add Committee Member
                    </h3>
                    <div className="mt-4 space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Search and Select User
                        </label>
                        <div className="relative user-search-container">
                          <input
                            type="text"
                            value={searchTerm}
                            onChange={onSearchInputChange}
                            onFocus={onSearchInputFocus}
                            placeholder="Search by name or username... (min 2 characters)"
                            className="w-full px-3 py-2 pr-8 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          />
                          {isSearching && (
                            <div className="absolute right-2 top-2.5">
                              <div className="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
                            </div>
                          )}
                          {showUserDropdown && getUsersToDisplay().length > 0 && (
                            <div className="absolute z-10 mt-1 w-full bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto">
                              {getUsersToDisplay().map((userOption: IUserOption) => (
                                <div
                                  key={userOption.value}
                                  onClick={() => onSelectUserFromDropdown(userOption)}
                                  className="px-3 py-2 hover:bg-blue-50 cursor-pointer text-sm border-b border-gray-100 last:border-b-0"
                                >
                                  <div className="font-medium text-gray-900">
                                    {userOption.label.split(' (')[0]}
                                  </div>
                                  <div className="text-gray-500 text-xs">
                                    @{userOption.value}
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                        <p className="text-xs text-gray-500 mt-1">
                          {searchTerm.length > 0 && searchTerm.length < 2 ? 
                            `Type ${2 - searchTerm.length} more character${2 - searchTerm.length === 1 ? '' : 's'} to search` :
                            `${getUsersToDisplay().length} user${getUsersToDisplay().length === 1 ? '' : 's'} found`
                          }
                        </p>
                        {selectedUser && (
                          <div className="mt-2 p-2 bg-blue-50 border border-blue-200 rounded-md">
                            <div className="text-sm font-medium text-blue-900">Selected:</div>
                            <div className="text-sm text-blue-700">{selectedUser.label}</div>
                          </div>
                        )}
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Position
                        </label>
                        <select
                          value={selectedPosition}
                          onChange={(e) => setSelectedPosition(e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                          <option value="">Select a position...</option>
                          {positionOptions.map(option => (
                            <option key={option.value} value={option.value}>
                              {option.label}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                <button
                  type="button"
                  onClick={onAddCommitteeMemberModal}
                  className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:ml-3 sm:w-auto sm:text-sm"
                >
                  Add Member
                </button>
                <button
                  type="button"
                  onClick={() => { 
                    setShowAddCommitteeModal(false); 
                    setSelectedUser(null); 
                    setSelectedPosition(""); 
                    setSearchTerm('');
                    setDebouncedSearchTerm('');
                    setShowUserDropdown(false);
                  }}
                  className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Justification Modal */}
      {showJustificationModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 transition-opacity" aria-hidden="true">
              <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
            </div>
            <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <div className="sm:flex sm:items-start">
                  <div className="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-yellow-100 sm:mx-0 sm:h-10 sm:w-10">
                    <svg className="h-6 w-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                    </svg>
                  </div>
                  <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left w-full">
                    <h3 className="text-lg leading-6 font-medium text-gray-900">
                      Committee Approval
                    </h3>
                    <div className="mt-4">
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Justification
                      </label>
                      <textarea
                        value={justification}
                        onChange={(e) => setJustification(e.target.value)}
                        rows={3}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="Enter your justification for the approval..."
                      />
                    </div>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                <button
                  type="button"
                  onClick={() => onSubmitJustification(currentMember, 'Approved', justification)}
                  className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-green-600 text-base font-medium text-white hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 sm:ml-3 sm:w-auto sm:text-sm"
                >
                  Approve
                </button>
                <button
                  type="button"
                  onClick={() => onSubmitJustification(currentMember, 'Rejected', justification)}
                  className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-red-600 text-base font-medium text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 sm:ml-3 sm:w-auto sm:text-sm"
                >
                  Reject
                </button>
                <button
                  type="button"
                  onClick={() => { setShowJustificationModal(false); setJustification(''); }}
                  className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CommitteeManager; 