import { useState } from "react";
import BarChart from './BarChart';

interface NetMeteringRegisterStatsProps {
  title: string;
  percentage: string;
  percentage_width: string;
  datasets: {
    label: string;
    value: string;
  }[];
}

export type { NetMeteringRegisterStatsProps };

export default function NetMeteringRegisterStats({
  title,
  percentage,
  percentage_width,
  datasets
}: NetMeteringRegisterStatsProps) {

  const [quantumsOpen, setQuantumsOpen] = useState<boolean>(false);

  return (
    <div>
      <div className="bg-white border border-gray-100 shadow-md shadow-black/5 p-6 rounded-md">
        <h2 className="text-lg font-bold mb-2">{title}</h2>
        <div
          onClick={() => setQuantumsOpen(!quantumsOpen)}
          className="flex items-center py-3"
        >
          <div className="space-y-3 flex-1">
            <div className="flex items-center">
              <span className="px-2 py-1 rounded-lg bg-blue-100 text-blue-800 text-sm">
                {percentage}
              </span>
            </div>
            <div className="overflow-hidden bg-blue-50 h-1.5 rounded-full w-full">
              <span
                className="h-full bg-blue-500 w-full block rounded-full"
                style={{ width: `${percentage_width}` }}
              ></span>
            </div>
          </div>
        </div>

        <div id="net_metering_register_statistics">
          <div>
            {datasets.map((dataset) => (
              <div className="flex justify-between py-3">
                <div>{dataset.label}</div>
              <div>
                <div className="center relative inline-block select-none whitespace-nowrap rounded-lg bg-blue-100 py-2 px-3.5 align-baseline font-sans text-xs font-bold uppercase leading-none text-white">
                  <div className="mt-px text-blue-800">{dataset.value}</div>
                </div>
              </div>
              </div>
            ))}
          </div>
        </div>

        {quantumsOpen && (
          <div
            className="fixed inset-0 z-50 overflow-y-auto"
            aria-labelledby="modal-title"
            role="dialog"
            aria-modal="true"
          >
            <div className="flex items-end justify-center min-h-screen px-4 text-center md:items-center sm:block sm:p-0">
              <div
                onClick={() => setQuantumsOpen(false)}
                className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-40"
                aria-hidden="true"
              ></div>

              <div className="inline-block w-full max-w-4xl p-8 my-20 overflow-hidden text-left transition-all transform bg-white rounded-lg shadow-xl">
                <div className="flex items-center justify-between space-x-4">
                  <h1 className="text-xl font-medium text-gray-800">
                    {title}
                  </h1>

                  <button
                    type="button"
                    onClick={() => setQuantumsOpen(false)}
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
                      {title}
                    </h2>
                    <BarChart 
                      labels={datasets.map((dataset) => dataset.label)}
                      data={datasets.map((dataset) => Number(dataset.value))}
                      labelTitle={title}
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
