import React, { useState, useCallback } from 'react';
import Select from 'react-select';
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
  
  // State for user justification
  const [justification, setJustification] = useState('');
  const [showJustificationModal, setShowJustificationModal] = useState(false);
  const [currentMember, setCurrentMember] = useState<string>('');
  
  // State for tracking if add committee modal is shown
  const [showAddCommitteeModal, setShowAddCommitteeModal] = useState(false);
  
  // Convert users to select options
  const userOptions = users.map(user => ({
    value: user.username,
    label: `${user.first_name} ${user.last_name}`
  }));
  
  // Add committee members modal
  const onAddCommitteeMembers = useCallback(() => {
    setShowAddCommitteeModal(true);
  }, []);
  
  // Handle committee member selection
  const onCommitteeSelect = useCallback((name_: string, selectedOption: IUserOption | null) => {
    if (!selectedOption) return;
    
    const username = selectedOption.value;
    const memberName = selectedOption.label;
    
    // Check if member already exists
    const memberExists = committee.some(m => m.memberUserName === username);
    if (memberExists) {
      alert('This member is already in the committee');
      return;
    }
    
    // Add new member
    setCommittee(prev => [
      ...prev,
      {
        memberUserName: username,
        memberName,
        memberPosition: '',
        committeeStatus: 'Pending',
        memberApproval: 'Pending',
        committeeJustification: '',
        committeeDate: new Date().toISOString().split('T')[0]
      }
    ]);
    
    setShowAddCommitteeModal(false);
  }, [committee, setCommittee]);
  
  // Handle committee member removal
  const onRemoveCommitteeMember = useCallback((index: number, username_: string) => {
    console.log('index', index, 'username_', username_);
    setCommittee(prev => {
      const updated = [...prev];
      updated.splice(index, 1);
      return updated;
    });
  }, [setCommittee]);
  
  // Handle changes to committee members
  const onCommitteeChange = useCallback((
    name_: string,
    event: { target: { name: string; value: string } }
  ) => {
    const { name, value } = event.target;
    
    setCommittee(prev => {
      const index = prev.findIndex(member => member.memberUserName === name_);
      if (index === -1) return prev;
      
      const updated = [...prev];
      updated[index] = {
        ...updated[index],
        [name]: value
      };
      
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
                    <input
                      type="text"
                      name="memberPosition"
                      value={member.memberPosition || ''}
                      onChange={(e) => onCommitteeChange(member.memberUserName, e)}
                      className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md"
                      placeholder="Position"
                    />
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
                        <Select
                          name="memberUserName"
                          className="block w-full rounded-md border-0 py-2 text-gray-900 sm:max-w-xs sm:text-sm sm:leading-6"
                          options={userOptions}
                          onChange={(option) => onCommitteeSelect('memberUserName', option)}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                <button
                  type="button"
                  onClick={() => setShowAddCommitteeModal(false)}
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