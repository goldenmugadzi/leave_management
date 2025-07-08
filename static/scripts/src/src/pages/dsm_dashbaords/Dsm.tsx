import { useState, useEffect } from "react";
import NetMeteringRegisterStats from "./components/NetMeteringRegisterStats";
import { NetMeteringRegisterStatsProps } from "./components/NetMeteringRegisterStats";
import NetMeterBilling from "./components/NetMeterBilling";
import DsmAuditChart from "./components/DsmAuditChart";
import DsmInitiativesOverview from './components/DsmInitiativesOverview';
import IeugBillingOverview from "./components/IeugBillingOverview";
import SolarProjectMonitoring from "./components/SolarProjectMonitoring";

export default function DSM({
  base_url,
  username,
  user_role,
}: {
  base_url: string;
  username: string;
  user_role: string;
}) {
  const [netMeteringRegisterStats, setNetMeteringRegisterStats] = useState<
    NetMeteringRegisterStatsProps[]
  >([]);

  useEffect(() => {
    console.log(
      "base_url: ",
      base_url,
      "username: ",
      username,
      "user_role: ",
      user_role
    );
    setNetMeteringRegisterStats([
      {
        title: "Net Metering Applications Quantum (KW)",
        percentage: "68% Commissioned",
        percentage_width: "68%",
        datasets: [
          {
            label: "Total Applications Quantum (KW)",
            value: "27073.08",
          },
          {
            label: "Commissioned Quantum (KW)",
            value: "18079.98",
          },
        ],
      },
      {
        title: "Net Metering Points Commissioned Applications",
        percentage: "69% Commissioned",
        percentage_width: "69%",
        datasets: [
          {
            label: "Total Applications",
            value: "375",
          },
          {
            label: "Commissioned Applications",
            value: "258",
          },
        ],
      },
      {
        title: "Exports to Import ratio after Net Metering Commissioning",
        percentage: "21.9% Export to Import Ratio",
        percentage_width: "21.9%",
        datasets: [
          {
            label: "Total Exports (KWH)",
            value: "10661462.35",
          },
          {
            label: "Total Imports (KWH)",
            value: "48719652.09",
          },
        ],
      },
      // {
      //   title: "Net Metering Register",
      //   percentage: "68%",
      //   percentage_width: "68%",
      //   datasets: [
      //     {
      //       label: "Awaiting ENM2 & Payment",
      //       value: "104",
      //     },
      //     {
      //       label: "Stores requisition in Progress",
      //       value: "230",
      //     },
      //     {
      //       label: "Awaiting Network Studies",
      //       value: "167",
      //     },
      //     {
      //       label: "Awaiting Meter Installation",
      //       value: "810",
      //     },
      //     {
      //       label: "Awaiting Commissioning",
      //       value: "1890",
      //     },
      //     {
      //       label: "Commissioned",
      //       value: "2210",
      //     },
      //     {
      //       label: "Not Yet Commissioned",
      //       value: "410",
      //     },
      //     {
      //       label: "Domestic",
      //       value: "310",
      //     },
      //   ],
      // },
    ]);
  }, []);

  return (
    <div>
      <div className="grid grid-cols-4 gap-4">
        {netMeteringRegisterStats.map((netMeteringRegisterStat, index) => (
          <NetMeteringRegisterStats key={index} {...netMeteringRegisterStat} />
        ))}
        <DsmAuditChart />
        <NetMeterBilling />
        <DsmInitiativesOverview />
        <IeugBillingOverview />
        <SolarProjectMonitoring />
      </div>
    </div>
  );
}
