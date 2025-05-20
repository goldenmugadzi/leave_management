import React, { useState, useCallback, useEffect } from 'react';
import { IBid, ISupplier } from '../../types/scheduleTypes';
import { useScheduleContext } from '../../context/ScheduleContext';

interface BidManagerProps {
  suppliers: ISupplier[];
  onSaveBid: (bid: IBid) => Promise<void>;
  onDeleteBid: (bid_count: number, supplier_name: string) => Promise<void>;
}

const BidManager: React.FC<BidManagerProps> = ({ 
  suppliers,
  onSaveBid,
  onDeleteBid
}) => {
  const { bids } = useScheduleContext();
  
  // State for current bid being edited
  const [currentBid, setCurrentBid] = useState<IBid>({
    bid_count: 0,
    supplier: '',
    supplier_name: '',
    bid_date: '',
    items: []
  });
  
  // State for modals
  const [showAddBidModal, setShowAddBidModal] = useState(false);
  const [showUpdateBidModal, setShowUpdateBidModal] = useState(false);
  const [showDeleteBidModal, setShowDeleteBidModal] = useState(false);
  const [bidToDelete, setBidToDelete] = useState<{bid_count?: number, supplier_name?: string}>({});

  // Open add bid modal
  const onAddBidModal = useCallback(() => {
    setCurrentBid({
      bid_count: (bids.length > 0 ? Math.max(...bids.map(b => b.bid_count || 0)) : 0) + 1,
      supplier: '',
      supplier_name: '',
      bid_date: new Date().toISOString().split('T')[0],
      items: []
    });
    setShowAddBidModal(true);
  }, [bids]);

  // Open update bid modal
  const onUpdateBidModal = useCallback((bid_count: number) => {
    const bidToUpdate = bids.find(b => b.bid_count === bid_count);
    if (bidToUpdate) {
      setCurrentBid({...bidToUpdate});
      setShowUpdateBidModal(true);
    }
  }, [bids]);

  // Close add bid modal
  const onCloseCurrentBid = useCallback(() => {
    setShowAddBidModal(false);
  }, []);

  // Close update bid modal
  const onCloseUpdateBidBid = useCallback(() => {
    setShowUpdateBidModal(false);
  }, []);

  // Handle changes to current bid
  const onCurrentBidChange = useCallback((
    name_: string,
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const { name, value } = event.target;
    setCurrentBid(prev => ({
      ...prev,
      [name]: value
    }));
  }, []);

  // Handle supplier selection
  const onCurrentBidSupplierChange = useCallback((
    name_: string,
    event: React.ChangeEvent<HTMLSelectElement>
  ) => {
    const { name, value } = event.target;
    
    // Find the supplier name
    const supplier = suppliers.find(s => s.id?.toString() === value);
    
    setCurrentBid(prev => ({
      ...prev,
      [name]: value,
      supplier_name: supplier?.supplier_name || supplier?.name || ''
    }));
  }, [suppliers]);

  // Handle bid document upload
  const onBidDocumentChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files && files.length > 0) {
      setCurrentBid(prev => ({
        ...prev,
        bid_document: files[0]
      }));
    }
  }, []);

  // Handle changes to bid items
  const onCurrentBidItemChange = useCallback((
    description: string,
    name_: string,
    event: { target: { name: string; value: string } },
    bid_no: string
  ) => {
    console.log('bid_no', bid_no, 'description', description, 'name', name_, 'event', event);
    const { name, value } = event.target;
    
    setCurrentBid(prev => {
      const items = prev.items || [];
      const itemIndex = items.findIndex(item => 
        item.item_required === description
      );
      
      if (itemIndex === -1) {
        // Item doesn't exist, create a new one
        return {
          ...prev,
          items: [
            ...items,
            {
              item_required: description,
              [name]: name === 'quantity' || name === 'unit_price' || name === 'total_price' 
                ? parseFloat(value) 
                : value
            }
          ]
        };
      } else {
        // Update existing item
        const updatedItems = [...items];
        updatedItems[itemIndex] = {
          ...updatedItems[itemIndex],
          [name]: name === 'quantity' || name === 'unit_price' || name === 'total_price' 
            ? parseFloat(value) 
            : value
        };
        
        // Calculate total price if unit price and quantity are changed
        if (name === 'unit_price' || name === 'quantity') {
          const unitPrice = name === 'unit_price' 
            ? parseFloat(value) 
            : updatedItems[itemIndex].unit_price || 0;
            
          const quantity = name === 'quantity' 
            ? parseFloat(value) 
            : updatedItems[itemIndex].quantity || 0;
            
          updatedItems[itemIndex].total_price = unitPrice * quantity;
        }
        
        return {
          ...prev,
          items: updatedItems
        };
      }
    });
  }, []);

  // Save current bid
  const onCurrentBidSave = useCallback(async () => {
    try {
      // Validation
      if (!currentBid.supplier) {
        alert('Please select a supplier');
        return;
      }
      
      if (!currentBid.bid_date) {
        alert('Please enter a bid date');
        return;
      }
      
      // Check if bid items have required fields
      if (!currentBid.items || currentBid.items.length === 0) {
        alert('Please add at least one item to the bid');
        return;
      }
      
      for (const item of currentBid.items || []) {
        if (!item.unit_price || !item.quantity) {
          alert('Please enter unit price and quantity for all items');
          return;
        }
      }
      
      // Save the bid
      await onSaveBid(currentBid);
      
      // Close modals
      setShowAddBidModal(false);
      setShowUpdateBidModal(false);
    } catch (error) {
      console.error('Error saving bid:', error);
      alert('Error saving bid');
    }
  }, [currentBid, onSaveBid]);

  // Show delete bid modal
  const onDeleteBidModal = useCallback((
    bid_count: number | undefined,
    supplier_name: string | undefined
  ) => {
    setBidToDelete({ bid_count, supplier_name });
    setShowDeleteBidModal(true);
  }, []);

  // Delete bid
  const handleDeleteBid = useCallback(async () => {
    if (bidToDelete.bid_count !== undefined && bidToDelete.supplier_name) {
      try {
        await onDeleteBid(bidToDelete.bid_count, bidToDelete.supplier_name);
        setShowDeleteBidModal(false);
      } catch (error) {
        console.error('Error deleting bid:', error);
        alert('Error deleting bid');
      }
    }
  }, [bidToDelete, onDeleteBid]);

  // Cleanup object URLs when component unmounts
  useEffect(() => {
    return () => {
      // Revoke any object URLs to prevent memory leaks
      bids.forEach(bid => {
        if (bid.bid_document_url) {
          URL.revokeObjectURL(bid.bid_document_url);
        }
      });
    };
  }, [bids]);

  return (
    <div className="mt-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-gray-800">Supplier Bids</h2>
        <button
          type="button"
          onClick={onAddBidModal}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
        >
          Add Bid
        </button>
      </div>

      {/* Bids Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Supplier
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Bid Date
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Document
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Items
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {bids.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-4 text-center text-sm text-gray-500">
                  No bids added yet
                </td>
              </tr>
            ) : (
              bids.map((bid) => (
                <tr key={bid.bid_count}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {bid.supplier_name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {bid.bid_date}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {bid.bid_document_url && (
                      <a
                        href={bid.bid_document_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-900"
                      >
                        View Document
                      </a>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {bid.items?.length || 0} items
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button
                      type="button"
                      onClick={() => bid.bid_count !== undefined && onUpdateBidModal(bid.bid_count)}
                      className="text-indigo-600 hover:text-indigo-900 mr-3"
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      onClick={() => onDeleteBidModal(bid.bid_count, bid.supplier_name)}
                      className="text-red-600 hover:text-red-900"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Add/Update Bid Modal */}
      {(showAddBidModal || showUpdateBidModal) && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 transition-opacity" aria-hidden="true">
              <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
            </div>
            <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-3xl sm:w-full">
              <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <div className="sm:flex sm:items-start">
                  <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left w-full">
                    <h3 className="text-lg leading-6 font-medium text-gray-900">
                      {showAddBidModal ? 'Add New Bid' : 'Update Bid'}
                    </h3>
                    <div className="mt-4 grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-6">
                      <div className="sm:col-span-3">
                        <label htmlFor="supplier" className="block text-sm font-medium text-gray-700">
                          Supplier
                        </label>
                        <div className="mt-1">
                          <select
                            id="supplier"
                            name="supplier"
                            value={currentBid.supplier}
                            onChange={(e) => onCurrentBidSupplierChange('supplier', e)}
                            className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md"
                          >
                            <option value="">Select a supplier</option>
                            {suppliers.map((supplier) => (
                              <option key={supplier.id} value={supplier.id}>
                                {supplier.supplier_name || supplier.name}
                              </option>
                            ))}
                          </select>
                        </div>
                      </div>

                      <div className="sm:col-span-3">
                        <label htmlFor="bid_date" className="block text-sm font-medium text-gray-700">
                          Bid Date
                        </label>
                        <div className="mt-1">
                          <input
                            type="date"
                            name="bid_date"
                            id="bid_date"
                            value={currentBid.bid_date}
                            onChange={(e) => onCurrentBidChange('bid_date', e)}
                            className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md"
                          />
                        </div>
                      </div>

                      <div className="sm:col-span-6">
                        <label htmlFor="bid_document" className="block text-sm font-medium text-gray-700">
                          Bid Document
                        </label>
                        <div className="mt-1">
                          <input
                            type="file"
                            name="bid_document"
                            id="bid_document"
                            onChange={onBidDocumentChange}
                            className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300"
                          />
                        </div>
                        {currentBid.bid_document_url && (
                          <div className="mt-2">
                            <a
                              href={currentBid.bid_document_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-blue-600 hover:text-blue-900"
                            >
                              View Current Document
                            </a>
                          </div>
                        )}
                      </div>

                      {/* Bid Items */}
                      <div className="sm:col-span-6">
                        <h4 className="text-md font-medium text-gray-700 mb-2">Bid Items</h4>
                        <table className="min-w-full divide-y divide-gray-200">
                          <thead className="bg-gray-50">
                            <tr>
                              <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Item
                              </th>
                              <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Unit of Measurement
                              </th>
                              <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Quantity
                              </th>
                              <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Unit Price
                              </th>
                              <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Total Price
                              </th>
                            </tr>
                          </thead>
                          <tbody className="bg-white divide-y divide-gray-200">
                            {/* Placeholder for item rows - would need to be populated from PR items or existing bid items */}
                            {/* Example row: */}
                            <tr>
                              <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-900">
                                Example Item
                              </td>
                              <td className="px-3 py-2 whitespace-nowrap text-sm">
                                <input
                                  type="text"
                                  name="unit_of_measurement"
                                  className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md"
                                  placeholder="e.g., Each"
                                  onChange={(e) => onCurrentBidItemChange('Example Item', 'uom', e, currentBid.bid_count?.toString() || '0')}
                                />
                              </td>
                              <td className="px-3 py-2 whitespace-nowrap text-sm">
                                <input
                                  type="number"
                                  name="quantity"
                                  className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md"
                                  placeholder="Qty"
                                  onChange={(e) => onCurrentBidItemChange('Example Item', 'quantity', e, currentBid.bid_count?.toString() || '0')}
                                />
                              </td>
                              <td className="px-3 py-2 whitespace-nowrap text-sm">
                                <input
                                  type="number"
                                  name="unit_price"
                                  className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md"
                                  placeholder="Unit price"
                                  onChange={(e) => onCurrentBidItemChange('Example Item', 'unit_price', e, currentBid.bid_count?.toString() || '0')}
                                />
                              </td>
                              <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">
                                $0.00 {/* Would be calculated */}
                              </td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                <button
                  type="button"
                  onClick={onCurrentBidSave}
                  className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:ml-3 sm:w-auto sm:text-sm"
                >
                  Save
                </button>
                <button
                  type="button"
                  onClick={showAddBidModal ? onCloseCurrentBid : onCloseUpdateBidBid}
                  className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteBidModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 transition-opacity" aria-hidden="true">
              <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
            </div>
            <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <div className="sm:flex sm:items-start">
                  <div className="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-red-100 sm:mx-0 sm:h-10 sm:w-10">
                    <svg className="h-6 w-6 text-red-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                  </div>
                  <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left">
                    <h3 className="text-lg leading-6 font-medium text-gray-900">
                      Delete Bid
                    </h3>
                    <div className="mt-2">
                      <p className="text-sm text-gray-500">
                        Are you sure you want to delete the bid from {bidToDelete.supplier_name}? This action cannot be undone.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                <button
                  type="button"
                  onClick={handleDeleteBid}
                  className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-red-600 text-base font-medium text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 sm:ml-3 sm:w-auto sm:text-sm"
                >
                  Delete
                </button>
                <button
                  type="button"
                  onClick={() => setShowDeleteBidModal(false)}
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

export default BidManager; 