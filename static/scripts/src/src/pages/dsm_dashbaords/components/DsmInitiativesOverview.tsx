import React, { useState } from "react";
import { Bar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  PointElement,
} from "chart.js";

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  PointElement
);

interface IVirtualPowerStats {
  dsm_initiative: string;
  initiative_type: string;
  initiative_value: number;
  demand_curtailed: number;
}

interface DsmInitiative {
  initiative: string;
  installations: string;
  demandCurtailed: string;
}

const initiatives: DsmInitiative[] = [
  {
    initiative: "Solar PV Systems",
    installations: "1604 installations",
    demandCurtailed: "17660 KW",
  },
  {
    initiative: "Solar Thermal/solar Geysers",
    installations: "566 installations",
    demandCurtailed: "7866 KW",
  },
  {
    initiative: "Prepaymenet meters",
    installations: "344 installations",
    demandCurtailed: "200 KW",
  },
  {
    initiative: "Energy Management Audits",
    installations: "465 installations",
    demandCurtailed: "34666 KW",
  },
  {
    initiative: "Energy Management Policy",
    installations: "8456 policies",
    demandCurtailed: "7898 KW",
  },
];

const DsmInitiativesOverview: React.FC<{ virtualPowerStats: IVirtualPowerStats[] }> = ({ virtualPowerStats }) => {
  const [isOpen, setIsOpen] = useState(false);

  const chartData = {
    labels: initiatives.map((item) => item.initiative),
    datasets: [
      {
        label: "Number of Installations/Audits/Policies",
        data: virtualPowerStats.map((item) => item.initiative_value),
        backgroundColor: "rgba(16, 185, 129, 0.7)",
        borderColor: "rgb(16, 185, 129)",
        borderWidth: 1,
        order: 2,
      },
      {
        label: "Demand Curtailed (KW)",
        data: virtualPowerStats.map((item) => item.demand_curtailed),
        type: "line" as const,
        borderColor: "rgb(59, 130, 246)",
        backgroundColor: "rgba(59, 130, 246, 0.7)",
        borderWidth: 2,
        fill: false,
        tension: 0.4,
        yAxisID: "y1",
        order: 1,
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
          text: "Demand Curtailed (KW)",
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
        text: "DSM Initiatives - Installations vs Demand Curtailed",
      },
      tooltip: {
        callbacks: {
          label: function (context: any) {
            let label = context.dataset.label || "";
            if (label) {
              label += ": ";
            }
            if (context.parsed.y !== null) {
              label += context.parsed.y.toLocaleString();
            }
            return label;
          },
        },
      },
    },
  };

  return (
    <div className="bg-white border border-gray-100 shadow-md shadow-black/5 p-6 rounded-md col-span-2">
      <div className="flex justify-between mb-4 items-start">
        <div className="font-medium">DSM Initiatives Overview</div>
      </div>

      {/* Table Section */}
      <div className="overflow-x-auto mb-6" onClick={() => setIsOpen(true)}>
        <table className="w-full min-w-[460px]">
          <thead>
            <tr>
              <th className="text-[12px] uppercase tracking-wide font-medium text-gray-400 py-2 px-4 bg-gray-50 text-left">
                DSM Initiative
              </th>
              <th className="text-[12px] uppercase tracking-wide font-medium text-gray-400 py-2 px-4 bg-gray-50 text-right">
                No of installations/audits/polices
              </th>
              <th className="text-[12px] uppercase tracking-wide font-medium text-gray-400 py-2 px-4 bg-gray-50 text-right">
                Demand curtailed (KW)
              </th>
            </tr>
          </thead>
          <tbody>
            {virtualPowerStats.map((item, index) => (
              <tr key={index}>
                <td className="py-2 px-4 border-b border-b-gray-50">
                  {item.dsm_initiative}
                </td>
                <td className="py-2 px-4 border-b border-b-gray-50 text-right">
                  {item.initiative_value.toLocaleString()}
                </td>
                <td className="py-2 px-4 border-b border-b-gray-50 text-right">
                  {item.demand_curtailed.toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Chart Section */}
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
                  DSM Initiatives - Installations vs Demand Curtailed
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

              <div className="flex flex-row justify-evenly overflow-y-auto">
                <div className="col-4 p-4">
                  <h2 className="text-lg font-bold mb-2">
                    DSM Initiatives - Installations vs Demand Curtailed
                  </h2>
                  <Bar
                    data={{
                      ...chartData,
                      datasets: chartData.datasets.map((dataset) => ({
                        ...dataset,
                        type: "bar", // Ensure all datasets are of type 'bar'
                      })),
                    }}
                    options={options}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DsmInitiativesOverview;
