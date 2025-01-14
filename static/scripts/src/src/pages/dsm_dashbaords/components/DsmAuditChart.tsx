import React, { useEffect, useRef, useState } from "react";
import Chart from "chart.js/auto";
import PieChart from "./PieChart";

interface DsmAuditData {
  region: string;
  audits: number;
}

const DsmAuditChart: React.FC<{ dsmAudits: DsmAuditData[] }> = ({ dsmAudits }) => {
  const chartRef = useRef<HTMLCanvasElement>(null);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    if (chartRef.current) {
      // Destroy existing chart if it exists
      const chartInstance = Chart.getChart(chartRef.current);
      if (chartInstance) {
        chartInstance.destroy();
      }

      // Create new chart
      new Chart(chartRef.current, {
        type: "pie",
        data: {
          labels: dsmAudits.map(audit => audit?.region),
          datasets: [
            {
              data: dsmAudits?.map(audit => audit?.audits),
              backgroundColor: [
                "rgba(16, 185, 129, 0.7)", // Emerald
                "rgba(59, 130, 246, 0.7)", // Blue
                "rgba(245, 158, 11, 0.7)", // Amber
                "rgba(99, 102, 241, 0.7)", // Indigo
                "rgba(236, 72, 153, 0.7)", // Pink
              ],
              borderColor: [
                "rgb(16, 185, 129)",
                "rgb(59, 130, 246)",
                "rgb(245, 158, 11)",
                "rgb(99, 102, 241)",
                "rgb(236, 72, 153)",
              ],
              borderWidth: 1,
            },
          ],
        },
        options: {
          responsive: true,
          plugins: {
            legend: {
              position: "bottom",
            },
            title: {
              display: true,
              text: "DSM Audits by Region",
            },
            tooltip: {
              callbacks: {
                label: function (context) {
                  const label = context.label || "";
                  const value = context.raw as number;
                  const total = (context.dataset.data as number[]).reduce(
                    (a, b) => a + b,
                    0
                  );
                  const percentage = ((value / total) * 100).toFixed(1);
                  return `${label}: ${value} (${percentage}%)`;
                },
              },
            },
          },
        },
      });
    }
  }, []);

  return (
    <>
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
                DSM Audits Distribution by Region
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
                  DSM Audits Distribution by Region
                </h2>
                <div className="mt-4">
                  <PieChart
                    labels={["Harare", "Southern", "Eastern", "Western", "Northern"]}
                    data={[8, 1, 0, 0, 0]}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
        </div>
      )}

      <div className="bg-white border border-gray-100 shadow-md shadow-black/5 p-6 rounded-md">
        <div className="flex justify-between mb-4 items-start">
          <div className="font-medium">DSM Audits Client List</div>
        </div>
        <div className="overflow-x-auto" onClick={() => setIsOpen(true)}>
          <table className="w-full min-w-[460px]">
            <thead>
              <tr>
                <th className="text-[12px] uppercase tracking-wide font-medium text-gray-400 py-2 px-4 bg-gray-50 text-left">
                  Region
                </th>
                <th className="text-[12px] uppercase tracking-wide font-medium text-gray-400 py-2 px-4 bg-gray-50 text-left">
                  Number of Audits
                </th>
              </tr>
            </thead>
            <tbody>
              {dsmAudits?.map((item, index) => (
                <tr key={index}>
                  <td className="py-2 px-4 border-b border-b-gray-50">
                    {item.region}
                  </td>
                  <td className="py-2 px-4 border-b border-b-gray-50">
                    {item.audits}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
};

export default DsmAuditChart;
