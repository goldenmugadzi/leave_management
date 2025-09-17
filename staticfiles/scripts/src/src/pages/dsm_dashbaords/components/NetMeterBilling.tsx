import { useState } from "react";
import MultiBarChart from "./MultiBarChart";

interface INetMeterBillingProp {
  region: string;
  commissionedPoints: number;
  totalBilled: number;
  percentageBilled: number;
}
  

export default function NetMeterBilling({ netMeteringBilling }: { netMeteringBilling: INetMeterBillingProp[] }) {

    const [netMeterBillingOpen, setNetMeterBillingOpen] = useState<boolean>(false);
    const title = "Regional Net Metering Statistics Comparison";

  const RegionalStats = () => {
    const labels = [
      "ZETDC",
      "Harare",
      "Southern",
      "Eastern",
      "Western",
      "Northern",
    ];

    const datasets = [
      {
        label: "Commissioned Net Metering Points",
        data: netMeteringBilling?.map((item: INetMeterBillingProp) => item.commissionedPoints),
        backgroundColor: "rgba(16, 185, 129, 0.7)",
        borderColor: "rgb(16, 185, 129)",
        borderWidth: 1,
      },
      {
        label: "Total Billed",
        data: netMeteringBilling?.map((item: INetMeterBillingProp) => item.totalBilled),
        backgroundColor: "rgba(59, 130, 246, 0.7)",
        borderColor: "rgb(59, 130, 246)",
        borderWidth: 1,
      },
      {
        label: "% Billed",
        data: netMeteringBilling?.map((item: INetMeterBillingProp) => item.percentageBilled),
        backgroundColor: "rgba(245, 158, 11, 0.7)",
        borderColor: "rgb(245, 158, 11)",
        borderWidth: 1,
        yAxisID: "percentage",
      },
    ];

    return (
      <MultiBarChart
        labels={labels}
        datasets={datasets}
        title="Regional Net Metering Statistics Comparison"
        height={400}
        showLegend={true}
        legendPosition="bottom"
      />
    );
  };

  return (
    <>
      <div className="bg-white rounded-lg shadow-md p-4 col-span-2">
        <div className="flex justify-between mb-4 items-start">
          <div className="font-medium">Regional Net Metering Statistics</div>
        </div>
        <div className="overflow-x-auto" onClick={() => setNetMeterBillingOpen(true)}>
          <table className="w-full min-w-[460px]">
            <thead>
              <tr>
                <th className="text-[12px] uppercase tracking-wide font-medium text-gray-400 py-2 px-4 bg-gray-50 text-left rounded-tl-md rounded-bl-md">
                  Region
                </th>
                <th className="text-[12px] uppercase tracking-wide font-medium text-gray-400 py-2 px-4 bg-gray-50 text-left">
                  Commissioned Points
                </th>
                <th className="text-[12px] uppercase tracking-wide font-medium text-gray-400 py-2 px-4 bg-gray-50 text-left">
                  Total Billed
                </th>
                <th className="text-[12px] uppercase tracking-wide font-medium text-gray-400 py-2 px-4 bg-gray-50 text-left">
                  % Billed
                </th>
              </tr>
            </thead>
            <tbody>
              {netMeteringBilling?.map((item, index) => (
                <tr key={index}>
                  <td className="py-2 px-4 border-b border-b-gray-50">
                    <div className="flex items-center">
                      <span className="text-gray-600 text-sm font-medium">
                        {item.region}
                      </span>
                    </div>
                </td>
                <td className="py-2 px-4 border-b border-b-gray-50">
                  <span className="text-[13px] font-medium text-emerald-500">
                    {item.commissionedPoints}
                  </span>
                </td>
                <td className="py-2 px-4 border-b border-b-gray-50">
                  <span className="text-[13px] font-medium text-blue-500">
                    {item.totalBilled}
                  </span>
                </td>
                <td className="py-2 px-4 border-b border-b-gray-50">
                  <span className="text-[13px] font-medium text-blue-700 p-1 rounded-md bg-blue-100">
                    {item.percentageBilled}%
                  </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {netMeterBillingOpen && (
          <div
            className="fixed inset-0 z-50 overflow-y-auto"
            aria-labelledby="modal-title"
            role="dialog"
            aria-modal="true"
          >
            <div className="flex items-end justify-center min-h-screen px-4 text-center md:items-center sm:block sm:p-0">
              <div
                onClick={() => setNetMeterBillingOpen(false)}
                className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-40"
                aria-hidden="true"
              ></div>

              <div className="inline-block w-full max-w-4xl p-8 my-20 overflow-hidden text-left transition-all transform bg-white rounded-lg shadow-xl">
                <div className="flex items-center justify-between space-x-4">
                  <h1 className="text-xl font-medium text-gray-800">{title}</h1>

                  <button
                    type="button"
                    onClick={() => setNetMeterBillingOpen(false)}
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
                    <h2 className="text-lg font-bold mb-2">{title}</h2>
                    <RegionalStats />
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
