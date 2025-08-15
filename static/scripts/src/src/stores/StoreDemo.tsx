import React from 'react';
import { useScheduleStore, useScheduleSelector } from './scheduleStore';

const StoreDemo: React.FC = () => {
  // Get store actions
  const {
    setCsId,
    setUsername,
    setPrData,
    addBid,
    resetSchedule,
    isCreator
  } = useScheduleStore();

  // Get store state using selectors
  const { csId, username, prData } = useScheduleSelector(state => ({
    csId: state.csId,
    username: state.username,
    prData: state.prData
  }));

  const { bids, bidCount } = useScheduleSelector(state => ({
    bids: state.bids,
    bidCount: state.bidCount
  }));

  const handleSetCsId = () => {
    setCsId('CS-' + Date.now());
  };

  const handleSetUsername = () => {
    setUsername('user-' + Date.now());
  };

  const handleSetPrData = () => {
    setPrData({
      pr_number: 'PR-' + Date.now(),
      scope_of_work: 'Demo scope ' + Date.now()
    });
  };

  const handleAddBid = () => {
    addBid({
      bid_count: bidCount + 1,
      supplier_name: 'Supplier ' + (bidCount + 1),
      items: []
    });
  };

  const handleReset = () => {
    resetSchedule();
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Zustand Store Demo</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Store State Display */}
        <div className="bg-white p-4 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-4">Current Store State</h2>
          <div className="space-y-2 text-sm">
            <div><strong>CS ID:</strong> {csId || 'Not set'}</div>
            <div><strong>Username:</strong> {username || 'Not set'}</div>
            <div><strong>PR Number:</strong> {prData.pr_number || 'Not set'}</div>
            <div><strong>Scope of Work:</strong> {prData.scope_of_work || 'Not set'}</div>
            <div><strong>Bid Count:</strong> {bidCount}</div>
            <div><strong>Is Creator:</strong> {isCreator() ? 'Yes' : 'No'}</div>
          </div>
        </div>

        {/* Actions */}
        <div className="bg-white p-4 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-4">Actions</h2>
          <div className="space-y-3">
            <button
              onClick={handleSetCsId}
              className="w-full bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
            >
              Set Random CS ID
            </button>
            <button
              onClick={handleSetUsername}
              className="w-full bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
            >
              Set Random Username
            </button>
            <button
              onClick={handleSetPrData}
              className="w-full bg-purple-500 text-white px-4 py-2 rounded hover:bg-purple-600"
            >
              Set Random PR Data
            </button>
            <button
              onClick={handleAddBid}
              className="w-full bg-orange-500 text-white px-4 py-2 rounded hover:bg-orange-600"
            >
              Add Bid
            </button>
            <button
              onClick={handleReset}
              className="w-full bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
            >
              Reset Store
            </button>
          </div>
        </div>
      </div>

      {/* Bids Display */}
      {bids.length > 0 && (
        <div className="mt-6 bg-white p-4 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-4">Current Bids</h2>
          <div className="space-y-2">
            {bids.map((bid, index) => (
              <div key={index} className="p-3 bg-gray-50 rounded">
                <strong>Bid #{bid.bid_count}</strong> - {bid.supplier_name}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Store Info */}
      <div className="mt-6 bg-gray-100 p-4 rounded-lg">
        <h2 className="text-lg font-semibold mb-2">Store Information</h2>
        <p className="text-sm text-gray-600">
          This demo shows the Zustand store in action. The store manages all schedule-related state
          and provides actions to modify it. Notice how components automatically re-render when
          their selected state changes.
        </p>
      </div>
    </div>
  );
};

export default StoreDemo;
