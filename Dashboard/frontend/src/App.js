import React, { useState, useEffect } from "react";
import StatsCards from "./components/StatsCards";
import CallsChart from "./components/CallsChart";
import ActiveCallsTable from "./components/ActiveCallsTable";
import ConversationModal from "./components/ConversationModal";
import UploadDocument from "./components/UploadDocument";
import { fetchSummary, fetchCalls } from "./api";

function App() {  
  const [activeCalls, setActiveCalls] = useState([]);
  const [summary, setSummary] = useState([]);
  const [selectedCall, setSelectedCall] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [showUploadDialog, setShowUploadDialog] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);

      const summaryResponse = await fetchSummary();
      if (summaryResponse.success) setSummary(summaryResponse.data);

      // Fetch ALL calls instead of just active ones
      const allCallsResponse = await fetchCalls();
      if (allCallsResponse.success) setActiveCalls(allCallsResponse.data);

    } catch (error) {
      console.error("Error loading data:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleCallClick = (call) => {
    setSelectedCall(call);
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setSelectedCall(null);
  };

  return (
    <div className="min-h-screen bg-gray-100">

      {/* 🔵 Modern Navigation Bar */}
      <header className="bg-white shadow-md border-b">
  <div className="max-w-7xl mx-auto px-8 py-5 flex items-center justify-between">

    {/* LEFT — Logo + Title */}
    <div className="flex items-center gap-5 flex-shrink-0 ml-[-200px]">
      <div className="w-14 h-14 bg-blue-600 rounded-2xl flex items-center justify-center shadow">
        <span className="text-white font-bold text-3xl">🤖</span>
      </div>

      <div className="ml-2">
        <h1 className="text-4xl font-bold text-gray-900 tracking-tight">
          AI Calling Dashboard
        </h1>
        <p className="text-gray-500 text-lg">Monitor • Manage • Analyze</p>
      </div>
    </div>

    {/* CENTER — Dashboard + Refresh + Upload */}
    <div className="flex-1 flex items-center justify-center gap-10">
      <button 
        className="text-blue-600 text-2xl font-semibold transition flex items-center gap-2"
      >
        📊 <span>Dashboard</span>
      </button>

      <button
        onClick={loadData}
        disabled={loading}
        className="text-gray-700 hover:text-blue-600 text-2xl font-semibold transition flex items-center gap-2"
      >
        🔄 <span>{loading ? "Refreshing..." : "Refresh"}</span>
      </button>

      <button
        onClick={() => setShowUploadDialog(!showUploadDialog)}
        className={`text-2xl font-semibold transition flex items-center gap-2 ${showUploadDialog ? 'text-blue-600' : 'text-gray-700 hover:text-blue-600'}`}
      >
        📤 <span>Upload Docs</span>
      </button>
    </div>

    {/* RIGHT — Profile */}
    <div className="flex items-center justify-end flex-shrink-0 mr-[-50px]">
      <div className="w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center shadow">
        <span className="text-white text-2xl font-bold">A</span>
      </div>
    </div>

  </div>
</header>

{/* 🔵 Banner */}
<section className="bg-blue-600 text-white min-h-[250px] flex items-center">
  <div className="max-w-7xl mx-auto px-6 flex justify-between items-center w-full">
    
    {/* Left content */}
    <div className="flex flex-col justify-center -ml-40 ">
      <h1 className="text-6xl font-bold mb-4">Calls Dashboard</h1>
      <p className="text-blue-200 text-2xl">
        Live analytics & monitoring for your AI-powered calls
      </p>
    </div>

    {/* Button */}
    <button
      onClick={loadData}
      disabled={loading}
      className="bg-blue-500 hover:bg-blue-400 px-6 py-3 rounded-xl font-medium text-xl transition"
    >
      {loading ? "Refreshing..." : "View Analytics"}
    </button>

  </div>
</section>


      {/* Upload Dialog - Floating */}
      {showUploadDialog && (
        <div className="fixed top-20 right-8 z-50">
          <div className="bg-white rounded-lg shadow-2xl border-2 border-blue-500 p-6 w-96">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-bold text-gray-800">📤 Upload Document</h3>
              <button 
                onClick={() => setShowUploadDialog(false)}
                className="text-gray-400 hover:text-gray-600 text-2xl font-bold"
              >
                ×
              </button>
            </div>
            <UploadDocument onClose={() => setShowUploadDialog(false)} />
          </div>
        </div>
      )}

      {/* 🔵 Main Content */}
      <main className="max-w-7.1xl mx-auto px-9 py-10 -mt 20">

        <StatsCards summary={summary} loading={loading} />

        {/* Search + Filters */}
        <div className="mb-11">
          <div className="flex items-center mb-4">
            <span className="text-4xl mr-3">🔍</span>
            <h2 className="text-3xl font-semibold text-gray-800">
              Filters & Search
            </h2>
          </div>

          <div className="flex flex-col lg:flex-row gap-4 bg-white rounded-lg p-6 shadow border">

            <input
              type="text"
              placeholder="Search calls..."
              className="flex-1 px-5 py-4 text-2xl border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />

            <select className="px-5 py-4 text-2xl border border-gray-300 rounded-lg">
              <option>All Active</option>
              <option>In Progress</option>
              <option>Completed</option>
              <option>Failed</option>
            </select>

            <select className="px-5 py-4 text-2xl border border-gray-300 rounded-lg">
              <option>All Categories</option>
              <option>Voice Calls</option>
              <option>AI Calls</option>
            </select>

          </div>
        </div>

        {/* Active Calls Table */}
        <ActiveCallsTable
          calls={activeCalls}
          loading={loading}
          onCallClick={handleCallClick}
        />

        {/* Calls Chart */}
        <CallsChart summary={summary} />
      </main>

      {/* Modal */}
      <ConversationModal
        call={selectedCall}
        isOpen={isModalOpen}
        onClose={closeModal}
      />
    </div>
  );
}

export default App;
