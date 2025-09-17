import React, { useState, useCallback, useEffect, useMemo } from 'react';
import { IBid, ISupplier } from '../../types/scheduleTypes';
import { useScheduleContext } from '../../context/ScheduleContext';

interface BidManagerProps {
  suppliers: ISupplier[];
  selectedPrItems: Array<{
    id: string;
    name: string;
    quantity: number;
    unit: string;
    status: string;
    included: boolean;
  }>;
  onSaveBid: (bid: IBid) => Promise<void>;
  onDeleteBid: (bid_count: number, supplier_name: string) => Promise<void>;
}

// Searchable Supplier Dropdown Component
interface SearchableSupplierDropdownProps {
  suppliers: ISupplier[];
  selectedSupplierId: string;
  onSupplierSelect: (supplier: ISupplier | null) => void;
  placeholder?: string;
}

const SearchableSupplierDropdown: React.FC<SearchableSupplierDropdownProps> = ({
  suppliers,
  selectedSupplierId,
  onSupplierSelect,
  placeholder = "Search and select a supplier..."
}) => {
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [isDropdownOpen, setIsDropdownOpen] = useState<boolean>(false);
  const [displayValue, setDisplayValue] = useState<string>('');
  const [isSelecting, setIsSelecting] = useState<boolean>(false);

  // Filter suppliers based on search term
  const filteredSuppliers = useMemo(() => {
    if (!searchTerm.trim()) return suppliers;
    
    const term = searchTerm.toLowerCase();
    return suppliers.filter(supplier => {
      const name = (supplier.supplier_name || supplier.name || '').toLowerCase();
      return name.includes(term);
    });
  }, [suppliers, searchTerm]);

  // Update display value when selected supplier changes
  useEffect(() => {
    if (selectedSupplierId) {
      const selectedSupplier = suppliers.find(s => s.id?.toString() === selectedSupplierId);
      if (selectedSupplier) {
        const name = selectedSupplier.supplier_name || selectedSupplier.name || '';
        setDisplayValue(name);
        setSearchTerm(name);
      }
    } else {
      setDisplayValue('');
      setSearchTerm('');
    }
  }, [selectedSupplierId, suppliers]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchTerm(value);
    setDisplayValue(value);
    setIsDropdownOpen(true);
    
    // Clear selection if input is cleared
    if (!value.trim()) {
      onSupplierSelect(null);
    }
  };

  const handleSupplierSelect = (supplier: ISupplier) => {
    setIsSelecting(true);
    const name = supplier.supplier_name || supplier.name || '';
    setDisplayValue(name);
    setSearchTerm(name);
    setIsDropdownOpen(false);
    onSupplierSelect(supplier);
    setIsSelecting(false);
  };

  const handleInputFocus = () => {
    setIsDropdownOpen(true);
  };

  const handleInputBlur = () => {
    // Don't close if we're in the middle of selecting
    if (!isSelecting) {
      // Delay closing to allow clicks on dropdown items
      setTimeout(() => setIsDropdownOpen(false), 300);
    }
  };

  const handleClearSelection = () => {
    setSearchTerm('');
    setDisplayValue('');
    setIsDropdownOpen(false);
    onSupplierSelect(null);
  };

  return (
    <div className="relative">
      <div className="relative">
        <input
          type="text"
          value={displayValue}
          onChange={handleInputChange}
          onFocus={handleInputFocus}
          onBlur={handleInputBlur}
          placeholder={placeholder}
          className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md pr-10"
        />
        {selectedSupplierId && (
          <button
            type="button"
            onClick={handleClearSelection}
            className="absolute inset-y-0 right-0 pr-3 flex items-center"
          >
            <svg className="h-4 w-4 text-gray-400 hover:text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
        {!selectedSupplierId && (
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
            <svg className="h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
        )}
      </div>

      {/* Dropdown */}
      {isDropdownOpen && (
        <div className="absolute z-10 mt-1 w-full bg-white shadow-lg max-h-60 rounded-md py-1 text-base ring-1 ring-black ring-opacity-5 overflow-auto focus:outline-none sm:text-sm">
          {filteredSuppliers.length === 0 ? (
            <div className="px-3 py-2 text-sm text-gray-500">
              {searchTerm.trim() ? `No suppliers found matching "${searchTerm}"` : 'No suppliers available'}
            </div>
          ) : (
            filteredSuppliers.map((supplier) => {
              const name = supplier.supplier_name || supplier.name || '';
              const isSelected = supplier.id?.toString() === selectedSupplierId;
              
              return (
                                 <div
                   key={supplier.id}
                   onMouseDown={(e) => {
                     e.preventDefault(); // Prevent blur event
                     handleSupplierSelect(supplier);
                   }}
                   className={`cursor-pointer select-none relative py-2 pl-3 pr-9 hover:bg-blue-50 ${
                     isSelected ? 'bg-blue-100 text-blue-900' : 'text-gray-900'
                   }`}
                 >
                  <div className="flex items-center">
                    <span className={`block truncate ${isSelected ? 'font-semibold' : 'font-normal'}`}>
                      {name}
                    </span>
                  </div>
                  {isSelected && (
                    <span className="absolute inset-y-0 right-0 flex items-center pr-4 text-blue-600">
                      <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    </span>
                  )}
                </div>
              );
            })
          )}
        </div>
      )}
    </div>
  );
};

const BidManager: React.FC<BidManagerProps> = ({ 
  suppliers,
  selectedPrItems,
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

  // Helper function to calculate total price
  const calculateTotalPrice = useCallback((itemName: string) => {
    const bidItem = currentBid.items?.find(bi => bi.item_required === itemName);
    if (!bidItem) return 0;
    
    const unitPrice = Number(bidItem.unit_price) || 0;
    const quantity = Number(bidItem.quantity) || 0;
    console.log(`Calculating for ${itemName}:`, { unitPrice, quantity, bidItem });
    return unitPrice * quantity;
  }, [currentBid.items]);

  // Helper function to get current bid item value
  const getBidItemValue = useCallback((itemName: string, field: 'unit_of_measurement' | 'quantity' | 'unit_price' | 'vat') => {
    const bidItem = currentBid.items?.find(bi => bi.item_required === itemName);
    return bidItem?.[field];
  }, [currentBid.items]);
  
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
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const { name, value } = event.target;
    setCurrentBid(prev => ({
      ...prev,
      [name]: value
    }));
  }, []);

  // Handle supplier selection from searchable dropdown
  const onSupplierSelect = useCallback((supplier: ISupplier | null) => {
    setCurrentBid(prev => ({
      ...prev,
      supplier: supplier?.id?.toString() || '',
      supplier_name: supplier ? (supplier.supplier_name || supplier.name || '') : ''
    }));
  }, []);

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
    event: { target: { name: string; value: string } }
  ) => {
    console.log('🔍 BidItemChange:', { description, field: event.target.name, value: event.target.value });
    const { name, value } = event.target;
    
    setCurrentBid(prev => {
      const items = prev.items || [];
      const itemIndex = items.findIndex(item => 
        item.item_required === description
      );
      
      if (itemIndex === -1) {
        // Item doesn't exist, create a new one
        const newItem = {
          item_required: description,
          [name]: name === 'quantity' || name === 'unit_price' || name === 'total_price' 
            ? (parseFloat(value) || 0)
            : value
        };
        
        // Calculate total price for new item if both values are available
        if (name === 'unit_price' || name === 'quantity') {
          const unitPrice = name === 'unit_price' ? (parseFloat(value) || 0) : 0;
          const quantity = name === 'quantity' ? (parseFloat(value) || 0) : 0;
          newItem.total_price = unitPrice * quantity;
        }
        
        return {
          ...prev,
          items: [
            ...items,
            newItem
          ]
        };
      } else {
        // Update existing item
        const updatedItems = [...items];
        updatedItems[itemIndex] = {
          ...updatedItems[itemIndex],
          [name]: name === 'quantity' || name === 'unit_price' || name === 'total_price' 
            ? (parseFloat(value) || 0)
            : value
        };
        
        // Always recalculate total price when unit price or quantity changes
        if (name === 'unit_price' || name === 'quantity') {
          const unitPrice = name === 'unit_price' 
            ? (parseFloat(value) || 0)
            : (updatedItems[itemIndex].unit_price || 0);
            
          const quantity = name === 'quantity' 
            ? (parseFloat(value) || 0)
            : (updatedItems[itemIndex].quantity || 0);
            
          updatedItems[itemIndex].total_price = unitPrice * quantity;
        }
        
        const newState = {
          ...prev,
          items: updatedItems
        };
        
        console.log('📊 Updated currentBid state:', newState);
        return newState;
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
      
      // Check if any PR items are selected
      const selectedItems = selectedPrItems.filter(item => item.included);
      if (selectedItems.length === 0) {
        alert('Please select PR items in the PR Items tab first');
        return;
      }
      
      // Check if bid items have required fields for selected PR items
      if (!currentBid.items || currentBid.items.length === 0) {
        alert('Please enter pricing information for all items');
        return;
      }
      
      for (const prItem of selectedItems) {
        const bidItem = currentBid.items.find(bi => bi.item_required === prItem.name);
        if (!bidItem || !bidItem.unit_price || !bidItem.quantity) {
          alert(`Please enter unit price and quantity for "${prItem.name}"`);
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
  }, [currentBid, selectedPrItems, onSaveBid]);

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
          disabled={selectedPrItems.filter(item => item.included).length === 0}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
          title={selectedPrItems.filter(item => item.included).length === 0 ? 'Please select PR items first' : 'Add a new bid'}
        >
          Add Bid
        </button>
      </div>

      {/* Warning message when no PR items selected */}
      {selectedPrItems.filter(item => item.included).length === 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
          <div className="flex items-center">
            <svg className="w-6 h-6 text-yellow-600 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
            <div>
              <h3 className="text-lg font-medium text-yellow-800">No PR Items Selected</h3>
              <p className="text-yellow-700 mt-1">Please go to the "PR Items" tab and select the items you want to include in bids before adding supplier bids.</p>
            </div>
          </div>
        </div>
      )}

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
                                                     <SearchableSupplierDropdown
                             suppliers={suppliers}
                             selectedSupplierId={currentBid.supplier || ''}
                             onSupplierSelect={onSupplierSelect}
                           />
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
                            onChange={(e) => onCurrentBidChange(e)}
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
                                VAT
                              </th>
                              <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Total Price
                              </th>
                            </tr>
                          </thead>
                          <tbody className="bg-white divide-y divide-gray-200">
                            {selectedPrItems.filter(item => item.included).length === 0 ? (
                              <tr>
                                <td colSpan={6} className="px-3 py-4 text-center text-sm text-gray-500">
                                  No PR items selected. Please go to the PR Items tab and select items first.
                                </td>
                              </tr>
                            ) : (
                              selectedPrItems
                                .filter(item => item.included)
                                .map((item) => {
                                  return (
                                    <tr key={item.id}>
                                      <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-900">
                                        {item.name}
                                      </td>
                                      <td className="px-3 py-2 whitespace-nowrap text-sm">
                                        <input
                                          type="text"
                                          name="unit_of_measurement"
                                          value={getBidItemValue(item.name, 'unit_of_measurement') || item.unit}
                                          className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md"
                                          placeholder="Unit of measurement"
                                          onChange={(e) => onCurrentBidItemChange(item.name, e)}
                                        />
                                      </td>
                                      <td className="px-3 py-2 whitespace-nowrap text-sm">
                                        <input
                                          type="number"
                                          name="quantity"
                                          value={getBidItemValue(item.name, 'quantity') ?? item.quantity}
                                          className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md"
                                          placeholder="Quantity"
                                          onChange={(e) => onCurrentBidItemChange(item.name, e)}
                                        />
                                      </td>
                                      <td className="px-3 py-2 whitespace-nowrap text-sm">
                                        <input
                                          type="number"
                                          step="0.01"
                                          name="unit_price"
                                          value={getBidItemValue(item.name, 'unit_price') || ''}
                                          className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md"
                                          placeholder="Unit price"
                                          onChange={(e) => onCurrentBidItemChange(item.name, e)}
                                        />
                                      </td>
                                      <td className="px-3 py-2 whitespace-nowrap text-sm">
                                        <select
                                          name="vat"
                                          value={getBidItemValue(item.name, 'vat') || ''}
                                          className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md"
                                          onChange={(e) => onCurrentBidItemChange(item.name, e)}
                                        >
                                          <option value="">Select VAT</option>
                                          <option value="Incl.">VAT Included</option>
                                          <option value="Excl.">VAT Excluded</option>
                                        </select>
                                      </td>
                                      <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">
                                        ${calculateTotalPrice(item.name).toFixed(2)}
                                      </td>
                                    </tr>
                                  );
                                })
                            )}
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