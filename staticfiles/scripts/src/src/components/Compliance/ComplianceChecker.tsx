import React, { useState, useCallback } from 'react';
import { ICompliance, IComplianceRemark } from '../../types/scheduleTypes';
import { useScheduleContext } from '../../context/ScheduleContext';

interface ComplianceCheckerProps {
  onSaveCompliance: (compliance: ICompliance[], remarks: IComplianceRemark[]) => Promise<void>;
}

const ComplianceChecker: React.FC<ComplianceCheckerProps> = ({ 
  onSaveCompliance
}) => {
  const { bids, compliance, setCompliance, complianceRemarks, setComplianceRemarks } = useScheduleContext();
  
  // State for tracking if compliance table is shown
  const [showComplianceTable, setShowComplianceTable] = useState(false);
  
  // Add compliance table
  const onAddComplianceTable = useCallback(() => {
    // Initialize compliance objects for each bid if not already done
    if (compliance.length === 0 && bids.length > 0) {
      const initialCompliance = bids.map(bid => ({
        supplier_name: bid.supplier_name,
        supplier: bid.supplier,
        bid_no: bid.bid_count,
        payment_terms: false,
        bid_validity: false,
        delivery_period: false,
        technical_specifications: false,
        valid_tax_clearance: false,
        registered_with_praz: false,
        site_visit: false,
        samples_required: false,
        decision: false,
        reject: false
      }));
      
      setCompliance(initialCompliance);

      // Initialize remarks for each supplier
      const initialRemarks = bids.map(bid => ({
        supplier_name: bid.supplier_name,
        bid_no: bid.bid_count,
        remarks: ''
      }));
      
      setComplianceRemarks(initialRemarks);
    }
    
    setShowComplianceTable(true);
  }, [bids, compliance, setCompliance, complianceRemarks, setComplianceRemarks]);

  // Handle changes to compliance checkbox fields
  const onComplianceChange = useCallback((
    index: number,
    event: { target: { name: string; checked: boolean } }
  ) => {
    const { name, checked } = event.target;
    
    setCompliance(prev => {
      const updated = [...prev];
      updated[index] = {
        ...updated[index],
        [name]: checked
      };
      return updated;
    });
  }, [setCompliance]);

  // Handle changes to compliance remarks
  const onComplianceRemarksChange = useCallback((
    supplier_name: string,
    event: { target: { name: string; value: string } }
  ) => {
    const { name, value } = event.target;
    
    setComplianceRemarks(prev => {
      const index = prev.findIndex(
        (item) => item.supplier_name === supplier_name
      );
      
      if (index === -1) return prev;
      
      const updated = [...prev];
      updated[index] = {
        ...updated[index],
        [name]: value
      };
      
      return updated;
    });
  }, [setComplianceRemarks]);

  // Save compliance
  const handleSaveCompliance = useCallback(async () => {
    try {
      // Validation
      if (compliance.length === 0) {
        alert('No compliance data to save');
        return;
      }
      
      await onSaveCompliance(compliance, complianceRemarks);
    } catch (error) {
      console.error('Error saving compliance:', error);
      alert('Error saving compliance');
    }
  }, [compliance, complianceRemarks, onSaveCompliance]);

  return (
    <div className="mt-8">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-gray-800">Compliance Checking</h2>
        {!showComplianceTable && (
          <button
            type="button"
            onClick={onAddComplianceTable}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
            disabled={bids.length === 0}
          >
            Add Compliance Table
          </button>
        )}
      </div>

      {showComplianceTable && (
        <>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Criteria / Supplier
                  </th>
                  {compliance.map((item) => (
                    <th 
                      key={`${item.supplier_name}-${item.bid_no}`} 
                      scope="col" 
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                    >
                      {item.supplier_name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {/* Payment Terms */}
                <tr>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    Payment Terms
                  </td>
                  {compliance.map((item, index) => (
                    <td 
                      key={`payment-${item.supplier_name}-${item.bid_no}`} 
                      className="px-6 py-4 whitespace-nowrap text-sm text-gray-500"
                    >
                      <input
                        type="checkbox"
                        name="payment_terms"
                        checked={item.payment_terms || false}
                        onChange={(e) => onComplianceChange(index, e)}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                    </td>
                  ))}
                </tr>
                
                {/* Bid Validity */}
                <tr>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    Bid Validity
                  </td>
                  {compliance.map((item, index) => (
                    <td 
                      key={`validity-${item.supplier_name}-${item.bid_no}`} 
                      className="px-6 py-4 whitespace-nowrap text-sm text-gray-500"
                    >
                      <input
                        type="checkbox"
                        name="bid_validity"
                        checked={item.bid_validity || false}
                        onChange={(e) => onComplianceChange(index, e)}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                    </td>
                  ))}
                </tr>
                
                {/* Delivery Period */}
                <tr>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    Delivery Period
                  </td>
                  {compliance.map((item, index) => (
                    <td 
                      key={`delivery-${item.supplier_name}-${item.bid_no}`} 
                      className="px-6 py-4 whitespace-nowrap text-sm text-gray-500"
                    >
                      <input
                        type="checkbox"
                        name="delivery_period"
                        checked={item.delivery_period || false}
                        onChange={(e) => onComplianceChange(index, e)}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                    </td>
                  ))}
                </tr>
                
                {/* Technical Specifications */}
                <tr>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    Technical Specifications
                  </td>
                  {compliance.map((item, index) => (
                    <td 
                      key={`tech-${item.supplier_name}-${item.bid_no}`} 
                      className="px-6 py-4 whitespace-nowrap text-sm text-gray-500"
                    >
                      <input
                        type="checkbox"
                        name="technical_specifications"
                        checked={item.technical_specifications || false}
                        onChange={(e) => onComplianceChange(index, e)}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                    </td>
                  ))}
                </tr>
                
                {/* Valid Tax Clearance */}
                <tr>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    Valid Tax Clearance
                  </td>
                  {compliance.map((item, index) => (
                    <td 
                      key={`tax-${item.supplier_name}-${item.bid_no}`} 
                      className="px-6 py-4 whitespace-nowrap text-sm text-gray-500"
                    >
                      <input
                        type="checkbox"
                        name="valid_tax_clearance"
                        checked={item.valid_tax_clearance || false}
                        onChange={(e) => onComplianceChange(index, e)}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                    </td>
                  ))}
                </tr>
                
                {/* Registered with PRAZ */}
                <tr>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    Registered with PRAZ
                  </td>
                  {compliance.map((item, index) => (
                    <td 
                      key={`praz-${item.supplier_name}-${item.bid_no}`} 
                      className="px-6 py-4 whitespace-nowrap text-sm text-gray-500"
                    >
                      <input
                        type="checkbox"
                        name="registered_with_praz"
                        checked={item.registered_with_praz || false}
                        onChange={(e) => onComplianceChange(index, e)}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                    </td>
                  ))}
                </tr>
                
                {/* Site Visit */}
                <tr>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    Site Visit
                  </td>
                  {compliance.map((item, index) => (
                    <td 
                      key={`site-${item.supplier_name}-${item.bid_no}`} 
                      className="px-6 py-4 whitespace-nowrap text-sm text-gray-500"
                    >
                      <input
                        type="checkbox"
                        name="site_visit"
                        checked={item.site_visit || false}
                        onChange={(e) => onComplianceChange(index, e)}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                    </td>
                  ))}
                </tr>
                
                {/* Samples Required */}
                <tr>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    Samples Required
                  </td>
                  {compliance.map((item, index) => (
                    <td 
                      key={`samples-${item.supplier_name}-${item.bid_no}`} 
                      className="px-6 py-4 whitespace-nowrap text-sm text-gray-500"
                    >
                      <input
                        type="checkbox"
                        name="samples_required"
                        checked={item.samples_required || false}
                        onChange={(e) => onComplianceChange(index, e)}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                    </td>
                  ))}
                </tr>
                
                {/* Decision */}
                <tr className="bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    Compliance
                  </td>
                  {compliance.map((item, index) => (
                    <td 
                      key={`decision-${item.supplier_name}-${item.bid_no}`} 
                      className="px-6 py-4 whitespace-nowrap text-sm text-gray-500"
                    >
                      <input
                        type="checkbox"
                        name="decision"
                        checked={item.decision || false}
                        onChange={(e) => onComplianceChange(index, e)}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                    </td>
                  ))}
                </tr>
                
                {/* Reject */}
                <tr className="bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    Reject
                  </td>
                  {compliance.map((item, index) => (
                    <td 
                      key={`reject-${item.supplier_name}-${item.bid_no}`} 
                      className="px-6 py-4 whitespace-nowrap text-sm text-gray-500"
                    >
                      <input
                        type="checkbox"
                        name="reject"
                        checked={item.reject || false}
                        onChange={(e) => onComplianceChange(index, e)}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>
          </div>

          {/* Remarks */}
          <div className="mt-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Remarks</h3>
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {complianceRemarks.map((remark) => (
                <div 
                  key={`remarks-${remark.supplier_name}-${remark.bid_no}`}
                  className="bg-white shadow overflow-hidden sm:rounded-lg"
                >
                  <div className="px-4 py-3 border-b border-gray-200 sm:px-6">
                    <h3 className="text-sm font-medium text-gray-900">
                      {remark.supplier_name}
                    </h3>
                  </div>
                  <div className="px-4 py-3 sm:px-6">
                    <textarea
                      name="remarks"
                      rows={4}
                      value={remark.remarks || ''}
                      onChange={(e) => onComplianceRemarksChange(remark.supplier_name || '', e)}
                      className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md"
                      placeholder="Enter remarks..."
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-6 flex justify-end">
            <button
              type="button"
              onClick={handleSaveCompliance}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
            >
              Save Compliance
            </button>
          </div>
        </>
      )}
    </div>
  );
};

export default ComplianceChecker; 