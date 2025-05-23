import React, { useState, useCallback } from 'react';
import { useScheduleContext } from '../../context/ScheduleContext';

interface ApprovalWorkflowProps {
  onApprove: (role: string, username: string, approval: string, justification: string) => Promise<void>;
}

const ApprovalWorkflow: React.FC<ApprovalWorkflowProps> = ({ 
  onApprove
}) => {
  const { currentApprover, username } = useScheduleContext();
  
  // State for justification
  const [justification, setJustification] = useState('');
  const [showJustificationModal, setShowJustificationModal] = useState(false);
  const [approvalAction, setApprovalAction] = useState<'approve' | 'reject'>('approve');
  
  // Open justification modal
  const onApprovalJustificationModal = useCallback((action: 'approve' | 'reject') => {
    if (!currentApprover || !currentApprover.username) {
      alert('No current approver information available');
      return;
    }
    
    if (currentApprover.username !== username) {
      alert('You are not the current approver');
      return;
    }
    
    setApprovalAction(action);
    setJustification('');
    setShowJustificationModal(true);
  }, [currentApprover, username]);
  
  // Close justification modal
  const onApprovalJustificationModalClose = useCallback(() => {
    setShowJustificationModal(false);
  }, []);
  
  // Handle justification change
  const onApprovalJustificationChange = useCallback((event: {
    target: { value: string };
  }) => {
    setJustification(event.target.value);
  }, []);
  
  // Handle approval action
  const handleApprove = useCallback(async () => {
    if (!currentApprover || !currentApprover.role || !currentApprover.username) {
      alert('No current approver information available');
      return;
    }
    
    try {
      const approval = approvalAction === 'approve' ? 'Approved' : 'Rejected';
      await onApprove(currentApprover.role, currentApprover.username, approval, justification);
      setShowJustificationModal(false);
    } catch (error) {
      console.error('Error during approval:', error);
      alert('Error during approval');
    }
  }, [currentApprover, approvalAction, justification, onApprove]);

  // If no current approver, show nothing
  if (!currentApprover) {
    return null;
  }

  return (
    <div className="mt-8">
      <div className="bg-white shadow overflow-hidden sm:rounded-lg">
        <div className="px-4 py-5 sm:px-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900">Approval Workflow</h3>
          <p className="mt-1 max-w-2xl text-sm text-gray-500">
            Current approval stage details.
          </p>
        </div>
        <div className="border-t border-gray-200">
          <dl>
            <div className="bg-gray-50 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
              <dt className="text-sm font-medium text-gray-500">Current Approver</dt>
              <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                {currentApprover.username || 'N/A'}
              </dd>
            </div>
            <div className="bg-white px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
              <dt className="text-sm font-medium text-gray-500">Role</dt>
              <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                {currentApprover.role || 'N/A'}
              </dd>
            </div>
            
            {/* Only show actions if the current user is the approver */}
            {currentApprover.username === username && (
              <div className="bg-gray-50 px-4 py-5 sm:px-6">
                <div className="flex justify-end space-x-4">
                  <button
                    type="button"
                    onClick={() => onApprovalJustificationModal('approve')}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700"
                  >
                    Approve
                  </button>
                  <button
                    type="button"
                    onClick={() => onApprovalJustificationModal('reject')}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-red-600 hover:bg-red-700"
                  >
                    Reject
                  </button>
                </div>
              </div>
            )}
          </dl>
        </div>
      </div>

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
                      {approvalAction === 'approve' ? 'Approval' : 'Rejection'} Justification
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
                          onChange={onApprovalJustificationChange}
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
                  onClick={handleApprove}
                  className={`w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 text-base font-medium text-white focus:outline-none focus:ring-2 focus:ring-offset-2 sm:ml-3 sm:w-auto sm:text-sm ${
                    approvalAction === 'approve' 
                      ? 'bg-green-600 hover:bg-green-700 focus:ring-green-500' 
                      : 'bg-red-600 hover:bg-red-700 focus:ring-red-500'
                  }`}
                >
                  {approvalAction === 'approve' ? 'Approve' : 'Reject'}
                </button>
                <button
                  type="button"
                  onClick={onApprovalJustificationModalClose}
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

export default ApprovalWorkflow; 