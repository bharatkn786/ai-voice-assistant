import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

const CallsChart = ({ summary }) => {
  if (!summary || !Array.isArray(summary) || summary.length === 0) {
    return (
      <div className="mt-12 w-full px-4">
        <div className="bg-gray-200 rounded-2xl p-6 shadow-2xl border w-full max-w-6xl mx-auto transition-transform transform hover:scale-105">
          <h3 className="text-2xl font-bold mb-6 text-center">📊 Calls Overview</h3>
          <div className="flex items-center justify-center h-64 text-gray-500">
            <p>No call data available</p>
          </div>
        </div>
      </div>
    );
  }

  const statusMap = {
    'ringing': 'Ringing',
    'answered': 'In Progress',
    'processing': 'Processing',
    'in-progress': 'In Progress',
    'completed': 'Completed',
    'failed': 'Failed',
    'busy': 'Failed',
    'no-answer': 'Failed'
  };

  const colors = {
    'Ringing': '#facc15',
    'In Progress': '#f59e0b',
    'Processing': '#f59e0b',
    'Completed': '#10b981',
    'Failed': '#ef4444'
  };

  const dataMap = {};
  summary.forEach(item => {
    const label = statusMap[item._id];
    if (label) {
      dataMap[label] = (dataMap[label] || 0) + item.count;
    }
  });

  const labels = Object.values(statusMap).filter((v, i, a) => a.indexOf(v) === i);
  const data = labels.map(label => dataMap[label] || 0);
  const backgroundColors = labels.map(label => colors[label] || '#6b7280');
  const borderColors = labels.map(label => colors[label] || '#6b7280');

  const chartData = {
    labels,
    datasets: [
      {
        label: 'Number of Calls',
        data,
        backgroundColor: backgroundColors,
        borderColor: borderColors,
        borderWidth: 1,
      },
    ],
  };

  const barOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      title: {
        display: false,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          stepSize: 1,
        },
      },
    },
  };

  return (
    <div className="mt-12 w-full px-4">
      <div className="bg-gray-200 rounded-2xl p-6 shadow-2xl border w-full max-w-7xl mx-auto transition-transform transform hover:scale-105">
        <h3 className="text-2xl font-bold mb-6 text-center">📊 Call Status Distribution</h3>
        <div className="w-full h-[700px]">
          <Bar data={chartData} options={barOptions} />
        </div>
      </div>
    </div>
  );
};

export default CallsChart;
