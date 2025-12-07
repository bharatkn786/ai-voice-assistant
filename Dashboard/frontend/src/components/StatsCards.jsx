import React from 'react';

const StatsCards = ({ summary, loading, onCardClick }) => {
  const getStatValue = (status) => {
    if (!summary || !Array.isArray(summary)) return 0;
    const stat = summary.find(item => item._id === status);
    return stat ? stat.count : 0;
  };

  const totalCalls = summary ? summary.reduce((sum, item) => sum + item.count, 0) : 0;
  const callingCalls = getStatValue('calling');
  const inProgressCalls = getStatValue('processing') + getStatValue('in-progress');
  const completedCalls = getStatValue('completed');
  const failedCalls = getStatValue('failed') + getStatValue('busy') + getStatValue('no-answer');

  const stats = [
    {
      title: 'Total Calls',
      value: totalCalls,
      icon: '📞',
      bgColor: 'bg-gray-200',
      textColor: 'text-gray-800',
      status: 'total'
    },
    {
      title: 'Calling',
      value: callingCalls,
      icon: '🕰️',
      bgColor: 'bg-yellow-200',
      textColor: 'text-yellow-800',
      status: 'initialized'
    },
    {
      title: 'In Progress',
      value: inProgressCalls,
      icon: '⚠️',
      bgColor: 'bg-blue-200',
      textColor: 'text-blue-800',
      status: 'in-progress'
    },
    {
      title: 'Completed',
      value: completedCalls,
      icon: '✅',
      bgColor: 'bg-green-200',
      textColor: 'text-green-800',
      status: 'completed'
    },
    {
      title: 'Failed/Not-Answered',
      value: failedCalls,
      icon: '🚨',
      bgColor: 'bg-red-200',
      textColor: 'text-red-800',
      status: 'failed'
    }
  ];

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-10 mx-4 mb 12">
        {[1, 2, 3, 4, 5].map((index) => (
          <div key={index} className="bg-white rounded-xl p-10 shadow-sm border animate-pulse min-h-[170px]"></div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-10 mx-4 mb-12">
      {stats.map((stat, index) => (
        <div
          key={index}
          onClick={() => onCardClick && onCardClick(stat.status)}
          className={`
            bg-white rounded-2xl p-7 shadow-md border transition-all duration-200 
            min-h-[180px]
            flex flex-col justify-between
            ${onCardClick ? 'cursor-pointer hover:scale-[1.05]' : ''}
          `}
        >
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-semibold text-gray-700">{stat.title}</h3>

            {/* 🔵 Updated ICON Styling */}
            <span
              className={`
                w-35 h-35 rounded-full flex items-center justify-center 
                text-6xl font-bold shadow-sm ${stat.bgColor}
              `}
            >
              {stat.icon}
            </span>
          </div>

          <p className={`text-5xl font-bold mt-6 ${stat.textColor}`}>
            {stat.value}
          </p>
        </div>
      ))}
    </div>
  );
};

export default StatsCards;