import React, { useState, useEffect } from 'react';

interface PrItem {
  id: string;
  item_required: string;
  quantity: number;
  unit_of_measurement: string;
  status: 'selected_for_this_cs' | 'available' | 'used_in_other_schedule';
  included: boolean;
  source: string;
}

interface PrItemsData {
  success: boolean;
  cs_id: string;
  pr_id: string;
  pr_number: string;
  scope_of_work: string;
  pr_items: PrItem[];
  pr_attachments: Array<{
    id: string;
    file: string;
    name: string;
  }>;
  uom: Array<{
    unit: string;
    name: string;
  }>;
  can_modify: boolean;
  total_items: number;
  selected_items: number;
  available_items: number;
}

interface PrItemsManagerProps {
  csId: string;
  enabled: boolean;
  onItemsUpdated?: (stats: { added: number; removed: number; total: number }) => void;
}

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

  useEffect(() => {
    if (enabled && csId) {
      loadPrItemsData();
    }
  }, [enabled, csId]);

  const loadPrItemsData = async () => {
    setLoading(true);
    setError('');
    
    try {
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

  const handleSave = async () => {
    if (!data) return;

    setSaving(true);
    setError('');

    try {
      // Prepare items data with updated included status
      const updatedItems = data.pr_items.map(item => ({
        ...item,
        included: selectedItems.has(item.id)
      }));

      const response = await fetch(`/comperative_schedule/api/cs-pr-items-update/${csId}/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken(),
        },
        body: JSON.stringify({
          cs_items: updatedItems,
          pr_id: data.pr_id,
        }),
      });

      const result = await response.json();
      
      if (result.success) {
        // Reload data to reflect changes
        await loadPrItemsData();
        
        // Notify parent component
        if (onItemsUpdated) {
          onItemsUpdated({
            added: result.stats.added_items,
            removed: result.stats.removed_items,
            total: result.stats.total_selected
          });
        }

        // Show success message
        alert('PR items updated successfully!');
      } else {
        setError(result.message || 'Failed to update PR items');
      }
    } catch (err) {
      setError('Error updating PR items: ' + (err as Error).message);
    } finally {
      setSaving(false);
    }
  };

     const getCsrfToken = () => {
     const cookies = document.cookie.split(';');
     for (const cookie of cookies) {
       const [name, value] = cookie.trim().split('=');
       if (name === 'csrftoken') {
         return value;
       }
     }
     return '';
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
      <div className="pr-items-manager">
        <div className="alert alert-info">
          <h4>Schedule Details Required</h4>
          <p>Please save the schedule details first before managing PR items.</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="pr-items-manager">
        <div className="text-center py-4">
          <div className="spinner-border" role="status">
            <span className="sr-only">Loading...</span>
          </div>
          <p className="mt-2">Loading PR items...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="pr-items-manager">
        <div className="alert alert-danger">
          <h4>Error</h4>
          <p>{error}</p>
          <button 
            className="btn btn-outline-danger btn-sm" 
            onClick={loadPrItemsData}
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="pr-items-manager">
        <div className="alert alert-warning">
          <h4>No Data</h4>
          <p>No PR items data available.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="pr-items-manager">
      <div className="card">
        <div className="card-header d-flex justify-content-between align-items-center">
          <h5 className="mb-0">PR Items Management</h5>
          <div className="text-sm text-muted">
            CS: {data.cs_id} | PR: {data.pr_number}
          </div>
        </div>
        
        <div className="card-body">
          {/* Summary */}
          <div className="row mb-3">
            <div className="col-md-12">
              <div className="alert alert-info">
                <strong>Summary:</strong> {data.selected_items} selected, {data.available_items} available, {data.total_items} total items
              </div>
            </div>
          </div>

          {/* Save Button */}
          <div className="row mb-3">
            <div className="col-md-12">
              <button 
                className="btn btn-primary"
                onClick={handleSave}
                disabled={saving || !data.can_modify}
              >
                {saving ? (
                  <>
                    <span className="spinner-border spinner-border-sm me-2" role="status"></span>
                    Saving...
                  </>
                ) : (
                  'Save PR Items Selection'
                )}
              </button>
              {!data.can_modify && (
                <small className="text-muted ms-2">
                  Items cannot be modified in current status
                </small>
              )}
            </div>
          </div>

          {/* Items List */}
          <div className="row">
            <div className="col-md-12">
              <div className="table-responsive">
                <table className="table table-striped">
                                     <thead>
                     <tr>
                       <th style={{width: "50px"}}>Select</th>
                       <th>Item Description</th>
                       <th style={{width: "100px"}}>Quantity</th>
                       <th style={{width: "100px"}}>Unit</th>
                       <th style={{width: "150px"}}>Status</th>
                     </tr>
                   </thead>
                  <tbody>
                    {data.pr_items.map((item) => (
                      <tr 
                        key={item.id}
                        style={{
                          backgroundColor: item.status === 'selected_for_this_cs' ? '#f6ffed' : 
                                         item.status === 'used_in_other_schedule' ? '#fff2e8' : '#ffffff'
                        }}
                      >
                        <td>
                          <input
                            type="checkbox"
                            className="form-check-input"
                            checked={selectedItems.has(item.id)}
                            disabled={item.status === 'used_in_other_schedule' || !data.can_modify}
                            onChange={() => handleItemToggle(item.id, item)}
                          />
                        </td>
                        <td>{item.item_required}</td>
                        <td>{item.quantity}</td>
                        <td>{item.unit_of_measurement}</td>
                        <td>
                          <span 
                            className="badge"
                            style={{ 
                              backgroundColor: getStatusColor(item.status),
                              color: 'white'
                            }}
                          >
                            {getStatusText(item.status)}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* PR Attachments */}
          {data.pr_attachments && data.pr_attachments.length > 0 && (
            <div className="row mt-4">
              <div className="col-md-12">
                <h6>PR Attachments</h6>
                <div className="list-group">
                  {data.pr_attachments.map((attachment) => (
                    <div key={attachment.id} className="list-group-item">
                      <div className="d-flex justify-content-between align-items-center">
                        <span>{attachment.name}</span>
                        <button 
                          className="btn btn-outline-primary btn-sm"
                          onClick={() => {
                            // Download attachment
                            const link = document.createElement('a');
                            link.href = `data:application/octet-stream;base64,${attachment.file}`;
                            link.download = attachment.name;
                            link.click();
                          }}
                        >
                          Download
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PrItemsManager; 