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

interface IeugCustomer {
  customer: string;
  monthlyEnergyBill: number;
  monthlyDemand: number;
  monthlyBill: number;
  scheduledPower: number;
  dateOfRelease: Date;
}

const customers: IeugCustomer[] = [
  {
    customer: "How mine",
    monthlyEnergyBill: 4496849.13,
    monthlyDemand: 10130.86,
    monthlyBill: 203137.36,
    scheduledPower: 192558.21,
    dateOfRelease: new Date("2024-01-01"),
  },
  {
    customer: "Renco mine",
    monthlyEnergyBill: 4496849.13,
    monthlyDemand: 8145.18,
    monthlyBill: 566949.28,
    scheduledPower: 566532.66,
    dateOfRelease: new Date("2024-01-01"),
  },
];

const IeugBillingOverview: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);

  const chartData = {
    labels: customers.map((item) => item.customer),
    datasets: [
      {
        label: "Monthly Energy Bill (kWh)",
        data: customers.map((item) => item.monthlyEnergyBill),
        backgroundColor: "rgba(16, 185, 129, 0.7)",
        borderColor: "rgb(16, 185, 129)",
        borderWidth: 1,
        order: 1,
      },
      {
        label: "Monthly Demand (kVA)",
        data: customers.map((item) => item.monthlyDemand),
        backgroundColor: "rgba(59, 130, 246, 0.7)",
        borderColor: "rgb(59, 130, 246)",
        borderWidth: 1,
        order: 2,
      },
      {
        label: "Monthly Bill (USD)",
        data: customers.map((item) => item.monthlyBill),
        backgroundColor: "rgba(245, 158, 11, 0.7)",
        borderColor: "rgb(245, 158, 11)",
        borderWidth: 1,
        order: 3,
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
          text: "Amount",
        },
      },
    },
    plugins: {
      legend: {
        position: "bottom" as const,
      },
      title: {
        display: true,
        text: "IEUG Customers Billing Statistics",
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
        <div className="font-medium">IEUG Customers Billing Statistics</div>
      </div>

      {/* Table Section */}
      <div className="overflow-x-auto mb-6" onClick={() => setIsOpen(true)}>
        <table className="w-full min-w-[460px]">
          <thead>
            <tr>
              <th className="text-[12px] uppercase tracking-wide font-medium text-gray-400 py-2 px-4 bg-gray-50 text-left">
                Customer
              </th>
              <th className="text-[12px] uppercase tracking-wide font-medium text-gray-400 py-2 px-4 bg-gray-50 text-right">
                Monthly Energy Bill (kWh)
              </th>
              <th className="text-[12px] uppercase tracking-wide font-medium text-gray-400 py-2 px-4 bg-gray-50 text-right">
                Monthly Demand (kVA)
              </th>
              <th className="text-[12px] uppercase tracking-wide font-medium text-gray-400 py-2 px-4 bg-gray-50 text-right">
                Monthly Bill (USD)
              </th>
              <th className="text-[12px] uppercase tracking-wide font-medium text-gray-400 py-2 px-4 bg-gray-50 text-right">
                Scheduled Power
              </th>
              <th className="text-[12px] uppercase tracking-wide font-medium text-gray-400 py-2 px-4 bg-gray-50 text-right">
                Date of Release
              </th>
            </tr>
          </thead>
          <tbody>
            {customers.map((item, index) => (
              <tr key={index}>
                <td className="py-2 px-4 border-b border-b-gray-50">
                  {item.customer}
                </td>
                <td className="py-2 px-4 border-b border-b-gray-50 text-right">
                  {item.monthlyEnergyBill.toLocaleString()}
                </td>
                <td className="py-2 px-4 border-b border-b-gray-50 text-right">
                  {item.monthlyDemand.toLocaleString()}
                </td>
                <td className="py-2 px-4 border-b border-b-gray-50 text-right">
                  {item.monthlyBill.toLocaleString()}
                </td>
                <td className="py-2 px-4 border-b border-b-gray-50 text-right">
                  {item.scheduledPower.toLocaleString()}
                </td>
                <td className="py-2 px-4 border-b border-b-gray-50 text-right">
                  {item.dateOfRelease.toLocaleString()}
                </td>
              </tr>
            ))}
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
                  IEUG Customers Billing Statistics
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
                  <Bar data={chartData} options={options} />
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default IeugBillingOverview; 