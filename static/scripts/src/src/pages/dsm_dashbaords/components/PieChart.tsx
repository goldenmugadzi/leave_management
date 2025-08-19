import { Chart as ChartJS, ArcElement, Tooltip, Legend, Title } from 'chart.js';
import { Pie } from 'react-chartjs-2';

ChartJS.register(ArcElement, Tooltip, Legend, Title);

interface PieChartProps {
  labels: string[];
  data: number[];
  title?: string;
  height?: number;
  width?: number;
  showLegend?: boolean;
  legendPosition?: 'top' | 'bottom' | 'left' | 'right';
  colors?: {
    backgroundColor: string[];
    borderColor: string[];
  };
}

export default function PieChart({
  labels,
  data,
  title = '',
  height = 400,
  width,
  showLegend = true,
  legendPosition = 'bottom',
  colors = {
    backgroundColor: [
      "rgba(16, 185, 129, 0.7)",  // Emerald
      "rgba(59, 130, 246, 0.7)",  // Blue
      "rgba(245, 158, 11, 0.7)",  // Amber
      "rgba(99, 102, 241, 0.7)",  // Indigo
      "rgba(236, 72, 153, 0.7)",  // Pink
    ],
    borderColor: [
      "rgb(16, 185, 129)",
      "rgb(59, 130, 246)",
      "rgb(245, 158, 11)",
      "rgb(99, 102, 241)",
      "rgb(236, 72, 153)",
    ],
  },
}: PieChartProps) {
  const chartData = {
    labels: labels,
    datasets: [
      {
        data: data,
        backgroundColor: colors.backgroundColor,
        borderColor: colors.borderColor,
        borderWidth: 1,
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: {
      legend: {
        display: showLegend,
        position: legendPosition,
      },
      title: {
        display: !!title,
        text: title,
      },
      tooltip: {
        callbacks: {
          label: function (context: any) {
            const label = context.label || "";
            const value = context.raw as number;
            const total = (context.dataset.data as number[]).reduce(
              (a: number, b: number) => a + b,
              0
            );
            const percentage = ((value / total) * 100).toFixed(1);
            return `${label}: ${value} (${percentage}%)`;
          },
        },
      },
    },
  };

  return (
    <div style={{ height, width: width || '100%' }}>
      <Pie data={chartData} options={options} />
    </div>
  );
}
