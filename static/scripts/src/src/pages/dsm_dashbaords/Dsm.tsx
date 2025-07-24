import { useState, useEffect } from "react";
import NetMeteringRegisterStats from "./components/NetMeteringRegisterStats";
import { NetMeteringRegisterStatsProps } from "./components/NetMeteringRegisterStats";
import NetMeterBilling from "./components/NetMeterBilling";
import DsmAuditChart from "./components/DsmAuditChart";
import DsmInitiativesOverview from './components/DsmInitiativesOverview';
import IeugBillingOverview from "./components/IeugBillingOverview";
import SolarProjectMonitoring from "./components/SolarProjectMonitoring";
import BarChart from "./components/BarChart";

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
  const [dsmAudits, setDsmAudits] = useState<[]>([]);
  const [netMeteringBilling, setNetMeteringBilling] = useState<[]>([]);
  const [virtualPowerStats, setVirtualPowerStats] = useState<[]>([]);

  useEffect(() => {
    console.log(
      "base_url: ",
      base_url,
      "username: ",
      username,
      "user_role: ",
      user_role
    );
    fetchNetMeteringRegister();
    fetchDsmAudits();
    fetchNetMeteringBilling();
    fetchVirtualPowerStats();
    // setNetMeteringRegisterStats([
    //   {
    //     title: "Net Metering Applications Quantum (KW)",
    //     percentage: "68% Commissioned",
    //     percentage_width: "68%",
    //     datasets: [
    //       {
    //         label: "Total Applications Quantum (KW)",
    //         value: "27073.08",
    //       },
    //       {
    //         label: "Commissioned Quantum (KW)",
    //         value: "18079.98",
    //       },
    //     ],
    //   },
    //   {
    //     title: "Net Metering Points Commissioned Applications",
    //     percentage: "69% Commissioned",
    //     percentage_width: "69%",
    //     datasets: [
    //       {
    //         label: "Total Applications",
    //         value: "375",
    //       },
    //       {
    //         label: "Commissioned Applications",
    //         value: "258",
    //       },
    //     ],
    //   },
    //   {
    //     title: "Exports to Import ratio after Net Metering Commissioning",
    //     percentage: "21.9% Export to Import Ratio",
    //     percentage_width: "21.9%",
    //     datasets: [
    //       {
    //         label: "Total Exports (KWH)",
    //         value: "10661462.35",
    //       },
    //       {
    //         label: "Total Imports (KWH)",
    //         value: "48719652.09",
    //       },
    //     ],
    //   },
    // ]);
  }, []);

  const fetchNetMeteringRegister = async () => {
    const response = await fetch(`${base_url}/dashboards/dsm/get_net_metering_register`);
    const data = await response.json();
    console.log("data: ", data);
    setNetMeteringRegisterStats(data?.net_metering_stats);
  };

  const fetchDsmAudits = async () => {
    const response = await fetch(`${base_url}/dashboards/dsm/get_dsm_audits`);
    const data = await response.json();
    console.log("data: ", data);
    setDsmAudits(data);
  };

  const fetchNetMeteringBilling = async () => {
    const response = await fetch(`${base_url}/dashboards/dsm/get_net_metering_billing`);
    const data = await response.json();
    console.log("data: ", data);
    setNetMeteringBilling(data);
  };

  const fetchVirtualPowerStats = async () => {
    const response = await fetch(`${base_url}/dashboards/dsm/get_virtual_power_stats`);
    const data = await response.json();
    console.log("data: ", data);
    setVirtualPowerStats(data);
  };

  return (
    <div>
      <div className="grid grid-cols-4 gap-4">
        {netMeteringRegisterStats.map((netMeteringRegisterStat, index) => (
          <NetMeteringRegisterStats key={index} {...netMeteringRegisterStat} />
        ))}
        <DsmAuditChart dsmAudits={dsmAudits} />
        <BarChart 
            labels={["January", "February", "March", "April", "May"]}
            data={[65, 59, 80, 81, 56]} 
            labelTitle="Monthly Data"  
          />
        <NetMeterBilling netMeteringBilling={netMeteringBilling} />
        <DsmInitiativesOverview virtualPowerStats={virtualPowerStats} />
        <IeugBillingOverview />
        <SolarProjectMonitoring />
      </div>
    </div>
  );
}
