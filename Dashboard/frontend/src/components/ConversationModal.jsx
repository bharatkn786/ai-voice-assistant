import React from 'react';

const ConversationModal = ({ call, isOpen, onClose }) => {
  if (!isOpen || !call) return null;

  const formatDateTime = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

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
      <span className={`px-3 py-1 rounded-full text-base font-semibold ${config.color}`}>
        {config.label}
      </span>
    );
  };

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity z-40"
        onClick={onClose}
      ></div>

      {/* Modal */}
      <div className="fixed inset-0 z-50 overflow-y-auto">
        <div className="flex items-center justify-center min-h-full p-6">
          <div className="bg-white rounded-xl shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">

            {/* Header */}
            <div className="flex items-center justify-between p-8 border-b">
              <div className="flex items-center space-x-5">
                <div className="h-14 w-14 rounded-full bg-blue-100 flex items-center justify-center">
                  <span className="text-blue-600 font-bold text-2xl">
                    {call.caller_name?.charAt(0).toUpperCase() || '?'}
                  </span>
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">
                    {call.caller_name || 'Unknown Caller'}
                  </h2>
                  <p className="text-lg text-gray-500">{call.phone_number}</p>
                </div>
              </div>

              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Content */}
            <div className="p-8 max-h-[70vh] overflow-y-auto">

              {/* Call Details */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
                <div className="bg-gray-50 rounded-lg p-5">
                  <h3 className="text-lg font-medium text-gray-500 mb-2">Call Status</h3>
                  {getStatusBadge(call.status)}
                </div>
                <div className="bg-gray-50 rounded-lg p-5">
                  <h3 className="text-lg font-medium text-gray-500 mb-2">Call ID</h3>
                  <p className="text-lg font-mono text-gray-900 break-all">{call.call_sid}</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-5">
                  <h3 className="text-lg font-medium text-gray-500 mb-2">Started At</h3>
                  <p className="text-lg text-gray-900">{formatDateTime(call.created_at)}</p>
                </div>
              </div>

              {/* Conversation */}
              <div>
                <h3 className="text-2xl font-semibold text-gray-900 mb-6 flex items-center">
                  💬 Conversation History
                  {call.conversation?.length > 0 && (
                    <span className="ml-3 text-base bg-blue-100 text-blue-800 px-3 py-1 rounded-full">
                      {call.conversation.length} messages
                    </span>
                  )}
                </h3>

                {call.conversation?.length > 0 ? (
                  <div className="space-y-6 max-h-96 overflow-y-auto pr-2">

                    {call.conversation.map((message, index) => (
                      <div key={index} className="bg-gray-50 rounded-xl p-5">

                        {/* User */}
                        {message.question && (
                          <div className="mb-5">
                            <div className="flex items-start space-x-4">
                              <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center">
                                <span className="text-blue-600 text-xl">👤</span>
                              </div>
                              <div>
                                <p className="text-lg font-bold text-gray-900 mb-1">User</p>
                                <p className="text-lg text-gray-700 leading-relaxed">
                                  {message.question}
                                </p>
                              </div>
                            </div>
                          </div>
                        )}

                        {/* Bot */}
                        {message.answer && (
                          <div className="mb-5">
                            <div className="flex items-start space-x-4">
                              <div className="h-10 w-10 rounded-full bg-green-100 flex items-center justify-center">
                                <span className="text-green-600 text-xl">🤖</span>
                              </div>
                              <div>
                                <p className="text-lg font-bold text-gray-900 mb-1">AI Agent</p>
                                <p className="text-lg text-gray-700 leading-relaxed">
                                  {message.answer}
                                </p>
                              </div>
                            </div>
                          </div>
                        )}

                        {/* Timestamp */}
                        {message.timestamp && (
                          <div className="text-base text-gray-500 text-right">
                            {formatDateTime(message.timestamp)}
                          </div>
                        )}
                      </div>
                    ))}

                  </div>
                ) : (
                  <div className="text-center py-14 text-gray-500">
                    <div className="text-5xl mb-4">💭</div>
                    <p className="text-xl">No conversation history available.</p>
                    <p className="text-lg mt-2">The conversation may not have started yet.</p>
                  </div>
                )}
              </div>
            </div>

            {/* Footer */}
            <div className="flex justify-end space-x-4 px-8 py-6 border-t bg-gray-50">
              <button
                onClick={onClose}
                className="px-5 py-3 text-lg text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-100"
              >
                Close
              </button>
              {call.conversation?.length > 0 && (
                <button
                  onClick={() => {
                    const data = JSON.stringify(call.conversation, null, 2);
                    const blob = new Blob([data], { type: 'application/json' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `conversation-${call.call_sid}.json`;
                    a.click();
                  }}
                  className="px-5 py-3 text-lg bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  Export Conversation
                </button>
              )}
            </div>

          </div>
        </div>
      </div>
    </>
  );
};

export default ConversationModal;
