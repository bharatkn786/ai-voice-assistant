import React, { useState } from 'react';

const ActiveCallsTable = ({ calls, loading, onCallClick }) => {
  const [statusFilter, setStatusFilter] = useState('All Active');
  const [currentPage, setCurrentPage] = useState(1);
  const callsPerPage = 10;

  // Filter calls based on status
  const filteredCalls = calls.filter(call => {
    if (statusFilter === 'All Active') {
      // Show only active calls (not completed/failed/no-answer/busy)
      const activeStatuses = ['initiated', 'calling', 'queued', 'ringing', 'in-progress'];
      return activeStatuses.includes(call.status);
    }
    
    // Match against the specific filter value
    return call.status === statusFilter;
  });

  // Sort by created_at in descending order (latest first)
  const sortedCalls = [...filteredCalls].sort((a, b) => {
    const dateA = new Date(a.created_at);
    const dateB = new Date(b.created_at);
    return dateB - dateA; // Descending order (newest first)
  });

  // Pagination logic
  const totalPages = Math.ceil(sortedCalls.length / callsPerPage);
  const indexOfLastCall = currentPage * callsPerPage;
  const indexOfFirstCall = indexOfLastCall - callsPerPage;
  const currentCalls = sortedCalls.slice(indexOfFirstCall, indexOfLastCall);

  const handleNextPage = () => {
    if (currentPage < totalPages) {
      setCurrentPage(currentPage + 1);
    }
  };

  const handlePrevPage = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1);
    }
  };

  // Reset to page 1 when filter changes
  React.useEffect(() => {
    setCurrentPage(1);
  }, [statusFilter]);

  const getStatusBadge = (status) => {
    const statusMap = {
      'initiated': { color: 'bg-blue-100 text-blue-800', label: 'Initialized' },
      'queued': { color: 'bg-blue-100 text-blue-800', label: 'Queued' },
      'ringing': { color: 'bg-yellow-100 text-yellow-800', label: 'Ringing' },
      'answered': { color: 'bg-green-100 text-green-800', label: 'Answered' },
      'processing': { color: 'bg-yellow-100 text-yellow-800', label: 'Processing' },
      'in-progress': { color: 'bg-yellow-100 text-yellow-800', label: 'In Progress' },
      'completed': { color: 'bg-green-100 text-green-800', label: 'Completed' },
      'failed': { color: 'bg-red-100 text-red-800', label: 'Failed' },
      'busy': { color: 'bg-red-100 text-red-800', label: 'Busy' },
      'no-answer': { color: 'bg-red-100 text-red-800', label: 'No Answer' }
    };

    const config = statusMap[status] || { color: 'bg-gray-100 text-gray-800', label: status };
    return (
      <span className={`px-3 py-1 rounded-full text-lg font-medium ${config.color}`}>
        {config.label}
      </span>
    );
  };

  const formatDateTime = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  const formatDuration = (call) => {
    if (!call.created_at) return 'N/A';
    
    const start = new Date(call.created_at);
    // Always use updated_at (or created_at if not updated yet)
    const end = call.updated_at ? new Date(call.updated_at) : start;
    
    const diffMs = end - start;
    const minutes = Math.floor(diffMs / 60000);
    const seconds = Math.floor((diffMs % 60000) / 1000);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="p-8">
          <h2 className="text-4xl font-extrabold mb-6 text-blue-700">🔄 Active Calls</h2>
          <div className="animate-pulse">
            <div className="h-14 bg-gray-200 rounded mb-6"></div>
            {[1, 2, 3].map(i => (
              <div key={i} className="h-24 bg-gray-100 rounded mb-3"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border">
      {/* Header with Status Filter */}
      <div className="p-8 border-b flex flex-col sm:flex-row justify-between items-center gap-6">
        <h2 className="text-3xl font-extrabold text-blue-700">🔄 Active Calls</h2>
        <div>
          {/* Status Filter */}
          <select
            className="px-5 py-4 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-2xl"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="All Active">All Active</option>
            <option value="in-progress">In Progress</option>
            <option value="calling">Calling</option>
           
            <option value="completed">Completed</option>
            
                 <option value="no-answer">No Answer</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-8 py-4 text-left text-2xl font-medium text-gray-500 uppercase tracking-wider">
                Caller
              </th>
              <th className="px-8 py-4 text-left text-2xl font-medium text-gray-500 uppercase tracking-wider">
                Phone Number
              </th>
              <th className="px-8 py-4 text-left text-2xl font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-8 py-4 text-left text-2xl font-medium text-gray-500 uppercase tracking-wider">
                Duration
              </th>
              <th className="px-8 py-4 text-left text-2xl font-medium text-gray-500 uppercase tracking-wider">
                Started
              </th>
              <th className="px-8 py-4 text-left text-2xl font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {currentCalls.length === 0 ? (
              <tr>
                <td colSpan="6" className="px-8 py-12 text-center text-gray-500 text-2xl">
                  {calls.length === 0 ? 'No active calls found.' : 'No calls match your criteria.'}
                </td>
              </tr>
            ) : (
              currentCalls.map((call) => (
                <tr
                  key={call.call_sid}
                  className="hover:bg-gray-50 cursor-pointer"
                  onClick={() => onCallClick && onCallClick(call)}
                >
                  <td className="px-8 py-6 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="flex-shrink-0 h-14 w-14">
                        <div className="h-14 w-14 rounded-full bg-blue-100 flex items-center justify-center">
                          <span className="text-blue-600 font-bold text-xl">
                            {call.caller_name?.charAt(0).toUpperCase() || '?'}
                          </span>
                        </div>
                      </div>
                      <div className="ml-5">
                        <div className="text-2xl font-bold text-gray-900">
                          {call.caller_name || 'Unknown'}
                        </div>
                        <div className="text-lg text-gray-500">
                          Call ID: {call.call_sid?.substring(0, 8)}...
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-8 py-6 whitespace-nowrap text-2xl text-gray-900">
                    {call.phone_number || 'N/A'}
                  </td>
                  <td className="px-8 py-6 whitespace-nowrap">
                    {getStatusBadge(call.status)}
                  </td>
                  <td className="px-8 py-6 whitespace-nowrap text-2xl text-gray-900">
                    {formatDuration(call)}
                  </td>
                  <td className="px-8 py-6 whitespace-nowrap text-2xl text-gray-900">
                    {formatDateTime(call.created_at)}
                  </td>
                  <td className="px-8 py-6 whitespace-nowrap text-2xl font-medium">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onCallClick && onCallClick(call);
                      }}
                      className="text-blue-600 hover:text-blue-900 transition-colors text-2xl font-bold"
                    >
                      View Details
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div className="px-8 py-4 bg-gray-50 border-t flex items-center justify-between">
        <div className="text-lg text-gray-500">
          Showing {indexOfFirstCall + 1}-{Math.min(indexOfLastCall, sortedCalls.length)} of {sortedCalls.length} calls
          {sortedCalls.length !== calls.length && ` (filtered)`}
        </div>
        
        {totalPages > 1 && (
          <div className="flex items-center gap-4">
            <button
              onClick={handlePrevPage}
              disabled={currentPage === 1}
              className={`px-6 py-3 rounded-lg text-xl font-semibold transition-all ${
                currentPage === 1
                  ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700 shadow-md'
              }`}
            >
              ← Previous
            </button>
            
            <span className="text-xl font-medium text-gray-700">
              Page {currentPage} of {totalPages}
            </span>
            
            <button
              onClick={handleNextPage}
              disabled={currentPage === totalPages}
              className={`px-6 py-3 rounded-lg text-xl font-semibold transition-all ${
                currentPage === totalPages
                  ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700 shadow-md'
              }`}
            >
              Next →
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default ActiveCallsTable;
