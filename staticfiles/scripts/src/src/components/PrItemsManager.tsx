import React, { useState, useEffect } from 'react';

interface PrItem {
  id: string;
  item_required: string;
  quantity: number;
  unit_of_measurement: string;
  status: string;
  included: boolean;
}

interface PrItemsData {
  success: boolean;
  pr_id: string;
  pr_number: string;
  pr_items: PrItem[];
  message?: string;
}

interface PrItemsManagerProps {
  csId: string | null;
  enabled: boolean;
  onItemsUpdated?: (items: PrItem[]) => void;
}

// Skeleton loading components for smooth transitions
const ItemSkeleton = () => (
  <div className="animate-pulse bg-white border border-gray-200 rounded-lg p-4 mb-3">
    <div className="flex items-center justify-between">
      <div className="flex items-center space-x-3 flex-1">
        <div className="w-5 h-5 bg-gray-200 rounded"></div>
        <div className="flex-1">
          <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
          <div className="h-3 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
      <div className="flex items-center space-x-3">
        <div className="h-3 bg-gray-200 rounded w-16"></div>
        <div className="h-6 bg-gray-200 rounded w-20"></div>
      </div>
    </div>
  </div>
);

const SkeletonLoader = () => (
  <div className="pr-items-skeleton">
    <div className="animate-pulse">
      {/* Header skeleton */}
      <div className="flex justify-between items-center mb-6">
        <div className="h-6 bg-gray-200 rounded w-48"></div>
        <div className="h-8 bg-gray-200 rounded w-32"></div>
      </div>
      
      {/* Stats skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-gray-50 p-4 rounded-lg">
            <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
            <div className="h-8 bg-gray-200 rounded w-1/2"></div>
          </div>
        ))}
      </div>
      
      {/* Items skeleton */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="p-4 border-b border-gray-200">
          <div className="h-5 bg-gray-200 rounded w-32"></div>
        </div>
        <div className="p-4 space-y-3">
          {[...Array(5)].map((_, i) => (
            <ItemSkeleton key={i} />
          ))}
        </div>
      </div>
    </div>
  </div>
);

const PrItemsManager: React.FC<PrItemsManagerProps> = ({ 
  csId, 
  enabled, 
  onItemsUpdated 
}) => {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [data, setData] = useState<PrItemsData | null>(null);
  const [error, setError] = useState<string>('');
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set());
  const [isInitialLoad, setIsInitialLoad] = useState(true);
  const [fadeIn, setFadeIn] = useState(false);

  useEffect(() => {
    if (enabled && csId) {
      loadPrItemsData();
    }
  }, [enabled, csId]);

  // Trigger fade-in animation when data loads
  useEffect(() => {
    if (data && !loading) {
      setFadeIn(true);
    }
  }, [data, loading]);

  const loadPrItemsData = async () => {
    setLoading(true);
    setError('');
    setFadeIn(false);
    
    try {
      // Add small delay for initial load to show skeleton nicely
      if (isInitialLoad) {
        await new Promise(resolve => setTimeout(resolve, 300));
      }
      
      const response = await fetch(`/comperative_schedule/api/cs-pr-items-management/${csId}/`);
      const result = await response.json();
      
      if (result.success) {
        setData(result);
        // Initialize selected items based on current status
        const selected = new Set<string>(
          result.pr_items
            .filter((item: PrItem) => item.included || item.status === 'selected_for_this_cs')
            .map((item: PrItem) => item.id)
        );
        setSelectedItems(selected);
      } else {
        setError(result.message || 'Failed to load PR items data');
      }
    } catch (err) {
      setError('Error loading PR items data: ' + (err as Error).message);
    } finally {
      setLoading(false);
      setIsInitialLoad(false);
    }
  };

  const handleItemToggle = (itemId: string, item: PrItem) => {
    if (item.status === 'used_in_other_schedule') {
      return; // Cannot modify items used in other schedules
    }

    const newSelected = new Set(selectedItems);
    if (newSelected.has(itemId)) {
      newSelected.delete(itemId);
    } else {
      newSelected.add(itemId);
    }
    setSelectedItems(newSelected);
  };

  const handleSelectAll = () => {
    const availableItems = data?.pr_items.filter(item => 
      item.status !== 'used_in_other_schedule'
    ) || [];
    
    const allSelected = availableItems.every(item => selectedItems.has(item.id));
    const newSelected = new Set(selectedItems);
    
    if (allSelected) {
      // Deselect all available items
      availableItems.forEach(item => newSelected.delete(item.id));
    } else {
      // Select all available items
      availableItems.forEach(item => newSelected.add(item.id));
    }
    
    setSelectedItems(newSelected);
  };

  const handleSave = async () => {
    if (!data || !csId) return;
    
    setSaving(true);
    try {
      const response = await fetch(`/comperative_schedule/api/cs-pr-items-update/${csId}/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.getAttribute('value') || '',
        },
        body: JSON.stringify({
          selected_items: Array.from(selectedItems)
        }),
      });

      const result = await response.json();
      
      if (result.success) {
        // Update the data with new status
        setData(prevData => {
          if (!prevData) return prevData;
          
          const updatedItems = prevData.pr_items.map(item => ({
            ...item,
            status: selectedItems.has(item.id) ? 'selected_for_this_cs' : 
                   (item.status === 'selected_for_this_cs' ? 'available' : item.status),
            included: selectedItems.has(item.id)
          }));
          
          const updatedData = { ...prevData, pr_items: updatedItems };
          
          // Notify parent component
          if (onItemsUpdated) {
            onItemsUpdated(updatedItems);
          }
          
          return updatedData;
        });
        
        // Show success message briefly
        const successEl = document.createElement('div');
        successEl.className = 'fixed top-4 right-4 bg-green-500 text-white px-4 py-2 rounded-md shadow-lg z-50 transition-all duration-300';
        successEl.textContent = 'PR items updated successfully!';
        document.body.appendChild(successEl);
        
        setTimeout(() => {
          successEl.style.opacity = '0';
          setTimeout(() => document.body.removeChild(successEl), 300);
        }, 2000);
        
      } else {
        setError(result.message || 'Failed to save PR items');
      }
    } catch (err) {
      setError('Error saving PR items: ' + (err as Error).message);
    } finally {
      setSaving(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'selected_for_this_cs':
        return '#52c41a'; // Green
      case 'used_in_other_schedule':
        return '#fa8c16'; // Orange
      case 'available':
        return '#1890ff'; // Blue
      default:
        return '#666666'; // Gray
    }
  };

  const getStatusText = (status: string) => {
    return status.replace(/_/g, ' ').toUpperCase();
  };

  if (!enabled) {
    return (
      <div className="pr-items-manager transition-all duration-300 ease-in-out">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 text-center">
          <div className="text-blue-600 mb-2">
            <svg className="w-12 h-12 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h4 className="text-lg font-semibold text-gray-900 mb-2">Schedule Details Required</h4>
          <p className="text-gray-600">Please save the schedule details first before managing PR items.</p>
        </div>
      </div>
    );
  }

  if (loading && isInitialLoad) {
    return (
      <div className="pr-items-manager">
        <SkeletonLoader />
      </div>
    );
  }

  if (error) {
    return (
      <div className="pr-items-manager transition-all duration-300 ease-in-out">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <svg className="w-6 h-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="ml-3 flex-1">
              <h4 className="text-lg font-semibold text-red-800 mb-2">Error Loading PR Items</h4>
              <p className="text-red-700 mb-4">{error}</p>
              <button 
                className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md transition-colors duration-200" 
                onClick={loadPrItemsData}
              >
                Try Again
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="pr-items-manager transition-all duration-300 ease-in-out">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
          <div className="text-yellow-600 mb-2">
            <svg className="w-12 h-12 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2 2v-5m16 0h-2a2 2 0 00-2 2v3a2 2 0 002 2h2z" />
            </svg>
          </div>
          <h4 className="text-lg font-semibold text-gray-900 mb-2">No Data Available</h4>
          <p className="text-gray-600">No PR items data available for this schedule.</p>
        </div>
      </div>
    );
  }

  // Calculate statistics
  const totalItems = data.pr_items.length;
  const selectedCount = selectedItems.size;
  const availableCount = data.pr_items.filter(item => item.status === 'available').length;
  const usedInOtherCount = data.pr_items.filter(item => item.status === 'used_in_other_schedule').length;

  return (
    <div className={`pr-items-manager transition-all duration-500 ease-in-out ${fadeIn ? 'opacity-100' : 'opacity-0'}`}>
      {/* Loading overlay for save operation */}
      {saving && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 transition-opacity duration-300">
          <div className="bg-white rounded-lg p-6 flex items-center space-x-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="text-gray-700 font-medium">Saving changes...</span>
          </div>
        </div>
      )}

      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h3 className="text-xl font-semibold text-gray-900">PR Items Management</h3>
            <p className="text-gray-600 mt-1">Select items to include in this comparative schedule</p>
          </div>
          <button
            onClick={loadPrItemsData}
            disabled={loading}
            className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-md transition-colors duration-200 disabled:opacity-50"
          >
            {loading ? (
              <div className="flex items-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600"></div>
                <span>Refreshing...</span>
              </div>
            ) : (
              'Refresh'
            )}
          </button>
        </div>

        {/* Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 transition-all duration-200 hover:shadow-md">
            <div className="text-sm font-medium text-blue-600 mb-1">Total Items</div>
            <div className="text-2xl font-bold text-blue-900">{totalItems}</div>
          </div>
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 transition-all duration-200 hover:shadow-md">
            <div className="text-sm font-medium text-green-600 mb-1">Selected</div>
            <div className="text-2xl font-bold text-green-900">{selectedCount}</div>
          </div>
          <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4 transition-all duration-200 hover:shadow-md">
            <div className="text-sm font-medium text-indigo-600 mb-1">Available</div>
            <div className="text-2xl font-bold text-indigo-900">{availableCount}</div>
          </div>
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 transition-all duration-200 hover:shadow-md">
            <div className="text-sm font-medium text-orange-600 mb-1">Used Elsewhere</div>
            <div className="text-2xl font-bold text-orange-900">{usedInOtherCount}</div>
          </div>
        </div>

        {/* Items List */}
        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm">
          <div className="p-4 border-b border-gray-200 bg-gray-50">
            <div className="flex justify-between items-center">
              <h4 className="text-lg font-medium text-gray-900">PR Items ({data.pr_number})</h4>
              <button
                onClick={handleSelectAll}
                className="text-blue-600 hover:text-blue-800 font-medium transition-colors duration-200"
              >
                {data.pr_items.filter(item => item.status !== 'used_in_other_schedule').every(item => selectedItems.has(item.id)) 
                  ? 'Deselect All' : 'Select All Available'}
              </button>
            </div>
          </div>
          
          <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
            {data.pr_items.map((item, index) => (
              <div 
                key={item.id} 
                className={`p-4 hover:bg-gray-50 transition-all duration-200 ${
                  selectedItems.has(item.id) ? 'bg-blue-50 border-l-4 border-blue-500' : ''
                }`}
                style={{
                  animationDelay: `${index * 50}ms`,
                  animation: fadeIn ? 'slideInUp 0.3s ease-out forwards' : 'none'
                }}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3 flex-1">
                    <input
                      type="checkbox"
                      checked={selectedItems.has(item.id)}
                      onChange={() => handleItemToggle(item.id, item)}
                      disabled={item.status === 'used_in_other_schedule'}
                      className="h-5 w-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500 transition-colors duration-200"
                    />
                    <div className="flex-1">
                      <div className="text-sm font-medium text-gray-900">{item.item_required}</div>
                      <div className="text-sm text-gray-500">
                        Quantity: {item.quantity} {item.unit_of_measurement}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    <span 
                      className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium transition-colors duration-200"
                      style={{
                        backgroundColor: `${getStatusColor(item.status)}20`,
                        color: getStatusColor(item.status)
                      }}
                    >
                      {getStatusText(item.status)}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Save Button */}
        <div className="flex justify-end">
          <button
            onClick={handleSave}
            disabled={saving || loading}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-6 py-2 rounded-md font-medium transition-all duration-200 transform hover:scale-105 disabled:scale-100"
          >
            {saving ? (
              <div className="flex items-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                <span>Saving...</span>
              </div>
            ) : (
              'Save Changes'
            )}
          </button>
        </div>
      </div>

      <style>{`
        @keyframes slideInUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        .animate-pulse {
          animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }
        
        @keyframes pulse {
          0%, 100% {
            opacity: 1;
          }
          50% {
            opacity: .5;
          }
        }
      `}</style>
    </div>
  );
};

export default PrItemsManager; 