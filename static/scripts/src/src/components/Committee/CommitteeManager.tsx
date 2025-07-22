import React, { useState, useCallback, useMemo, useEffect } from 'react';
import Select, { StylesConfig, InputActionMeta } from 'react-select';
import { ICommittee, IUser } from '../../types/scheduleTypes';
import { useScheduleContext } from '../../context/ScheduleContext';

interface IUserOption {
  value: string;
  label: string;
}

interface CommitteeManagerProps {
  users: IUser[];
  onSaveCommittee: (committee: ICommittee[]) => Promise<void>;
}

const CommitteeManager: React.FC<CommitteeManagerProps> = ({ 
  users,
  onSaveCommittee
}) => {
  const { committee, setCommittee, username } = useScheduleContext();
  
  // Log props on every render to debug
  console.log('🔍 CommitteeManager rendered with:', {
    usersCount: users?.length || 0,
    usersData: users?.slice(0, 3), // Show first 3 users for debugging
    committeeCount: committee?.length || 0,
    currentUsername: username
  });
  
  // State for user justification
  const [justification, setJustification] = useState('');
  const [showJustificationModal, setShowJustificationModal] = useState(false);
  const [currentMember, setCurrentMember] = useState<string>('');
  
  // State for tracking if add committee modal is shown
  const [showAddCommitteeModal, setShowAddCommitteeModal] = useState(false);
  
  // State for search term with debouncing
  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState('');
  
  // State for add member modal
  const [selectedUser, setSelectedUser] = useState<IUserOption | null>(null);
  const [selectedPosition, setSelectedPosition] = useState<string>("");
  const positionOptions = [
    { value: "CHAIRMAN", label: "Chairman" },
    { value: "USER", label: "User" },
    { value: "PROCUREMENT ADMIN", label: "Procurement Admin" },
    { value: "FINANCE", label: "Finance" },
  ];
  
  // Debounce search term
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchTerm(searchTerm);
    }, 300);
    
    return () => clearTimeout(timer);
  }, [searchTerm]);
  
  // Memoized user options with search filtering
  const userOptions = useMemo(() => {
    if (!users || users.length === 0) {
      console.log('🔍 No users available');
      return [];
    }
    
    console.log('🔍 Total users:', users.length);
    console.log('🔍 Search term:', debouncedSearchTerm);
    console.log('🔍 Current committee members:', committee.map(m => m.memberUserName));
    
    // Debug: Log first few users to see their structure
    console.log('🔍 First 3 users structure:', users.slice(0, 3).map(user => ({
      first_name: user.first_name,
      last_name: user.last_name,
      username: user.username,
      types: typeof user.first_name + ' ' + typeof user.last_name + ' ' + typeof user.username
    })));
    
    // Filter users based on search term (if any)
    let filteredUsers = users;
    
    if (debouncedSearchTerm.length >= 1) {
      console.log('🔍 Starting search with term:', debouncedSearchTerm);
      
      filteredUsers = users.filter(user => {
        // Handle potential null/undefined values
        const firstName = (user.first_name || '').toLowerCase().trim();
        const lastName = (user.last_name || '').toLowerCase().trim();
        const username = (user.username || '').toLowerCase().trim();
        const fullName = `${firstName} ${lastName}`.trim();
        const search = debouncedSearchTerm.toLowerCase().trim();
        
        // Debug each user during search
        console.log('🔍 Checking user:', {
          user: user.username,
          firstName,
          lastName,
          fullName,
          searchTerm: search,
          firstNameMatch: firstName.includes(search),
          lastNameMatch: lastName.includes(search),
          usernameMatch: username.includes(search),
          fullNameMatch: fullName.includes(search)
        });
        
        const matches = fullName.includes(search) || 
                       username.includes(search) ||
                       firstName.includes(search) ||
                       lastName.includes(search);
        
        if (matches) {
          console.log('🔍 ✅ Match found:', fullName, username);
        }
        return matches;
      });
      console.log('🔍 Filtered by search:', filteredUsers.length, 'users');
    } else {
      // Show first 50 users if no search
      filteredUsers = users.slice(0, 50);
      console.log('🔍 No search term, showing first 50 users');
    }
    
    // Filter out already selected users
    const availableUsers = filteredUsers.filter(user => 
      !committee.some(member => member.memberUserName === user.username)
    );
    
    console.log('🔍 Available users after filtering committee:', availableUsers.length);
    
    const options = availableUsers.map(user => ({
      value: user.username,
      label: `${user.first_name || ''} ${user.last_name || ''}`.trim() + ` (${user.username})`
    }));
    
    console.log('🔍 Final options:', options.length, options.slice(0, 3));
    return options;
  }, [users, debouncedSearchTerm, committee]);

  // Custom styles for react-select to handle modal and performance
  const selectStyles: StylesConfig<IUserOption, false> = useMemo(() => ({
    control: (provided) => ({
      ...provided,
      minHeight: '40px',
      backgroundColor: 'white',
      borderColor: '#d1d5db',
      '&:hover': {
        borderColor: '#9ca3af'
      },
      '&:focus-within': {
        borderColor: '#3b82f6',
        boxShadow: '0 0 0 1px #3b82f6'
      }
    }),
    menu: (provided) => ({
      ...provided,
      zIndex: 9999,
      position: 'absolute',
      maxHeight: '200px',
    }),
    menuPortal: (provided) => ({
      ...provided,
      zIndex: 9999,
    }),
    option: (provided, state) => ({
      ...provided,
      backgroundColor: state.isSelected 
        ? '#3b82f6' 
        : state.isFocused 
        ? '#eff6ff' 
        : 'white',
      color: state.isSelected ? 'white' : '#1f2937',
      '&:hover': {
        backgroundColor: state.isSelected ? '#3b82f6' : '#eff6ff'
      }
    }),
    placeholder: (provided) => ({
      ...provided,
      color: '#9ca3af'
    }),
    noOptionsMessage: (provided) => ({
      ...provided,
      color: '#6b7280',
      fontSize: '14px'
    })
  }), []);
  
  // Handle search input change
  const handleInputChange = useCallback((inputValue: string, actionMeta: InputActionMeta) => {
    console.log('🔍 Input change:', { inputValue, action: actionMeta.action });
    if (actionMeta.action === 'input-change') {
      setSearchTerm(inputValue);
    }
    return inputValue;
  }, []);

  // Add committee members modal
  const onAddCommitteeMembers = useCallback(() => {
    setSearchTerm(''); // Reset search when opening modal
    setShowAddCommitteeModal(true);
  }, []);
  
  // Handle committee member selection in modal
  const onCommitteeSelect = useCallback((selectedOption: IUserOption | null) => {
    setSelectedUser(selectedOption);
  }, []);

  // Add committee member from modal
  const onAddCommitteeMemberModal = useCallback(() => {
    if (!selectedUser || !selectedPosition) {
      alert("Please select both a user and a position.");
      return;
    }
    const username = selectedUser.value;
    const memberName = selectedUser.label.split(' (')[0];
    // Check if member already exists
    const memberExists = committee.some(m => m.memberUserName === username);
    if (memberExists) {
      alert('This member is already in the committee');
      return;
    }
    // Check if position already taken
    const positionExists = committee.some(m => m.memberPosition === selectedPosition);
    if (positionExists) {
      alert('This position is already assigned to another member');
      return;
    }
    setCommittee(prev => [
      ...prev,
      {
        memberUserName: username,
        memberName,
        memberPosition: selectedPosition,
        committeeStatus: 'Pending',
        memberApproval: 'Pending',
        committeeJustification: '',
        committeeDate: new Date().toISOString().split('T')[0]
      }
    ]);
    setShowAddCommitteeModal(false);
    setSearchTerm("");
    setSelectedUser(null);
    setSelectedPosition("");
  }, [committee, setCommittee, selectedUser, selectedPosition]);
  
  // Handle committee member removal
  const onRemoveCommitteeMember = useCallback((index: number, username_: string) => {
    console.log('index', index, 'username_', username_);
    setCommittee(prev => {
      const updated = [...prev];
      updated.splice(index, 1);
      return updated;
    });
  }, [setCommittee]);
  
  // Open justification modal
  const onCommitteeJustificationModal = useCallback((username_: string) => {
    setCurrentMember(username_);
    setJustification('');
    setShowJustificationModal(true);
  }, []);
  
  // Close justification modal
  const onCommitteeJustificationModalClose = useCallback(() => {
    setShowJustificationModal(false);
  }, []);
  
  // Handle justification change
  const onCommitteeJustificationChange = useCallback((event: {
    target: { value: string };
  }) => {
    setJustification(event.target.value);
  }, []);
  
  // Handle committee approval
  const onCommitteeApprove = useCallback((
    username_: string,
    approval: string,
    justification_: string
  ) => {
    setCommittee(prev => {
      const index = prev.findIndex(member => member.memberUserName === username_);
      if (index === -1) return prev;
      
      const updated = [...prev];
      updated[index] = {
        ...updated[index],
        memberApproval: approval,
        committeeJustification: justification_,
        committeeDate: new Date().toISOString().split('T')[0]
      };
      
      return updated;
    });
    
    setShowJustificationModal(false);
  }, [setCommittee]);
  
  // Submit committee
  const onSubmitCommittee = useCallback(async () => {
    try {
      // Validation
      if (committee.length === 0) {
        alert('Please add at least one committee member');
        return;
      }
      
      await onSaveCommittee(committee);
    } catch (error) {
      console.error('Error saving committee:', error);
      alert('Error saving committee');
    }
  }, [committee, onSaveCommittee]);
  
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
      {/* Temporary Debug Panel - Remove after fixing */}

      
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-gray-800">Committee Members</h2>
        <button
          type="button"
          onClick={onAddCommitteeMembers}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
        >
          Add Committee Member
        </button>
      </div>

      {/* Committee Members Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Name
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Position
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Date
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {committee.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-4 text-center text-sm text-gray-500">
                  No committee members added yet
                </td>
              </tr>
            ) : (
              committee.map((member, index) => (
                <tr key={member.memberUserName}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {member.memberName}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {member.memberPosition}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getCommitteeClassNames(member.memberApproval || 'Pending')}`}>
                      {member.memberApproval || 'Pending'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {member.committeeDate || ''}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    {member.memberUserName === username ? (
                      <>
                        <button
                          type="button"
                          onClick={() => onCommitteeJustificationModal(member.memberUserName)}
                          className="text-indigo-600 hover:text-indigo-900 mr-3"
                          disabled={member.memberApproval !== 'Pending'}
                        >
                          Approve
                        </button>
                        <button
                          type="button"
                          onClick={() => onCommitteeJustificationModal(member.memberUserName)}
                          className="text-red-600 hover:text-red-900 mr-3"
                          disabled={member.memberApproval !== 'Pending'}
                        >
                          Reject
                        </button>
                      </>
                    ) : (
                      <button
                        type="button"
                        onClick={() => onRemoveCommitteeMember(index, member.memberUserName)}
                        className="text-red-600 hover:text-red-900"
                      >
                        Remove
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {committee.length > 0 && (
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
                  <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left w-full">
                    <h3 className="text-lg leading-6 font-medium text-gray-900">
                      Add Committee Member
                    </h3>
                    <div className="mt-4">
                      <label htmlFor="memberUserName" className="block text-sm font-medium text-gray-700">
                        Select User
                      </label>
                      <div className="mt-1">
                        {!users || users.length === 0 ? (
                          <div className="bg-yellow-50 border border-yellow-200 rounded p-3">
                            <p className="text-yellow-800 text-sm">
                              {!users ? "Loading users..." : "No users available"}
                            </p>
                          </div>
                        ) : (
                          <Select
                            name="memberUserName"
                            className="block w-full rounded-md border-0 py-2 text-gray-900 sm:max-w-xs sm:text-sm sm:leading-6"
                            options={userOptions}
                            value={selectedUser}
                            onChange={onCommitteeSelect}
                            onInputChange={handleInputChange}
                            styles={selectStyles}
                            placeholder="Search users..."
                            isClearable
                            isSearchable
                            isLoading={!users || users.length === 0}
                            noOptionsMessage={() => searchTerm.length < 1 ? "Start typing to search users" : `No users found for "${searchTerm}"`}
                            menuPortalTarget={document.body}
                            menuPosition="fixed"
                            loadingMessage={() => "Loading users..."}
                          />
                        )}
                      </div>
                    </div>
                    <div className="mt-4">
                      <label htmlFor="memberPosition" className="block text-sm font-medium text-gray-700">
                        Select Position
                      </label>
                      <div className="mt-1">
                        <select
                          id="memberPosition"
                          name="memberPosition"
                          className="block w-full rounded-md border-0 text-gray-900 sm:max-w-xs sm:text-sm sm:leading-6 p-2"
                          value={selectedPosition}
                          onChange={e => setSelectedPosition(e.target.value)}
                        >
                          <option value="">Select Position</option>
                          {positionOptions.map(opt => (
                            <option key={opt.value} value={opt.value}>{opt.label}</option>
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
                  onClick={() => { setShowAddCommitteeModal(false); setSelectedUser(null); setSelectedPosition(""); }}
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
                  <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left w-full">
                    <h3 className="text-lg leading-6 font-medium text-gray-900">
                      Committee Justification
                    </h3>
                    <div className="mt-4">
                      <label htmlFor="justification" className="block text-sm font-medium text-gray-700">
                        Justification
                      </label>
                      <div className="mt-1">
                        <textarea
                          id="justification"
                          name="justification"
                          rows={4}
                          value={justification}
                          onChange={onCommitteeJustificationChange}
                          className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md"
                          placeholder="Enter your justification..."
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                <button
                  type="button"
                  onClick={() => onCommitteeApprove(currentMember, 'Approved', justification)}
                  className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-green-600 text-base font-medium text-white hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 sm:ml-3 sm:w-auto sm:text-sm"
                >
                  Approve
                </button>
                <button
                  type="button"
                  onClick={() => onCommitteeApprove(currentMember, 'Rejected', justification)}
                  className="mt-3 w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-red-600 text-base font-medium text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                >
                  Reject
                </button>
                <button
                  type="button"
                  onClick={onCommitteeJustificationModalClose}
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