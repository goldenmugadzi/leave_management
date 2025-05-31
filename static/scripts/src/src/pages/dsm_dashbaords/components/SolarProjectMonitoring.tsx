import React, { useState } from "react";
import { Bar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

interface ContractorData {
  contractor: string;
  installations: number;
  capacity: number;
}

const contractorData: ContractorData[] = [
  { contractor: "Solar Energy Projects", installations: 12, capacity: 492 },
  { contractor: "Min Local Government", installations: 1041, capacity: 9282 },
  { contractor: "SAMANSCO", installations: 507, capacity: 2676 },
  { contractor: "Power Speed", installations: 19, capacity: 389 },
  { contractor: "David Whitehead", installations: 1, capacity: 3500 },
  { contractor: "Department of Irrigation", installations: 24, capacity: 1321 },
];

const SolarProjectMonitoring: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);

  const chartData = {
    labels: contractorData.map((item) => item.contractor),
    datasets: [
      {
        label: "Number of Installations",
        data: contractorData.map((item) => item.installations),
        backgroundColor: "rgba(16, 185, 129, 0.7)",
        borderColor: "rgb(16, 185, 129)",
        borderWidth: 1,
        yAxisID: 'y',
      },
      {
        label: "Installed Capacity (KW)",
        data: contractorData.map((item) => item.capacity),
        backgroundColor: "rgba(59, 130, 246, 0.7)",
        borderColor: "rgb(59, 130, 246)",
        borderWidth: 1,
        yAxisID: 'y1',
      },
    ],
  };

  const options = {
    responsive: true,
    interaction: {
      intersect: false,
      mode: "index" as const,
    },
    scales: {
      y: {
        type: "linear" as const,
        display: true,
        position: "left" as const,
        title: {
          display: true,
          text: "Number of Installations",
        },
      },
      y1: {
        type: "linear" as const,
        display: true,
        position: "right" as const,
        title: {
          display: true,
          text: "Installed Capacity (KW)",
        },
        grid: {
          drawOnChartArea: false,
        },
      },
    },
    plugins: {
      legend: {
        position: "bottom" as const,
      },
      title: {
        display: true,
        text: "Solar Project Monitoring",
      },
    },
  };

  // Calculate totals
  const totalInstallations = contractorData.reduce((sum, item) => sum + item.installations, 0);
  const totalCapacity = contractorData.reduce((sum, item) => sum + item.capacity, 0);

  return (
    <div className="bg-white border border-gray-100 shadow-md shadow-black/5 p-6 rounded-md col-span-2">
      <div className="flex justify-between mb-4 items-start">
        <div className="font-medium">Solar Project Monitoring</div>
      </div>

      {/* Table Section */}
      <div className="overflow-x-auto mb-6" onClick={() => setIsOpen(true)}>
        <table className="w-full min-w-[460px]">
          <thead>
            <tr>
              <th className="text-[12px] uppercase tracking-wide font-medium text-gray-400 py-2 px-4 bg-gray-50 text-left">
                Contractor
              </th>
              <th className="text-[12px] uppercase tracking-wide font-medium text-gray-400 py-2 px-4 bg-gray-50 text-right">
                No of Installations
              </th>
              <th className="text-[12px] uppercase tracking-wide font-medium text-gray-400 py-2 px-4 bg-gray-50 text-right">
                Sum of Installed Capacity (KW)
              </th>
            </tr>
          </thead>
          <tbody>
            {contractorData.map((item, index) => (
              <tr key={index}>
                <td className="py-2 px-4 border-b border-b-gray-50">
                  {item.contractor}
                </td>
                <td className="py-2 px-4 border-b border-b-gray-50 text-right">
                  {item.installations.toLocaleString()}
                </td>
                <td className="py-2 px-4 border-b border-b-gray-50 text-right">
                  {item.capacity.toLocaleString()}
                </td>
              </tr>
            ))}
            <tr className="font-bold">
              <td className="py-2 px-4 border-b border-b-gray-50">Total</td>
              <td className="py-2 px-4 border-b border-b-gray-50 text-right">
                {totalInstallations.toLocaleString()}
              </td>
              <td className="py-2 px-4 border-b border-b-gray-50 text-right">
                {totalCapacity.toFixed(2)}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* Chart Modal */}
      {isOpen && (
        <div
          className="fixed inset-0 z-50 overflow-y-auto"
          aria-labelledby="modal-title"
          role="dialog"
          aria-modal="true"
        >
          <div className="flex items-end justify-center min-h-screen px-4 text-center md:items-center sm:block sm:p-0">
            <div
              onClick={() => setIsOpen(false)}
              className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-40"
              aria-hidden="true"
            ></div>

            <div className="inline-block w-full max-w-4xl p-8 my-20 overflow-hidden text-left transition-all transform bg-white rounded-lg shadow-xl">
              <div className="flex items-center justify-between space-x-4">
                <h1 className="text-xl font-medium text-gray-800">
                  Solar Project Monitoring
                </h1>

                <button
                  type="button"
                  onClick={() => setIsOpen(false)}
                  className="text-gray-600 focus:outline-none hover:text-gray-700"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="w-6 h-6"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                </button>
              </div>

              <div className="mt-4">
                <Bar data={chartData} options={options} />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SolarProjectMonitoring; 