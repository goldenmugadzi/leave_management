import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js';
import { Bar } from 'react-chartjs-2';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

interface BarChartProps {
    labels: string[];
    data: number[];
    labelTitle: string;
}

export const BarChart: React.FC<BarChartProps> = ({ labels, data, labelTitle }) => {
  const chartData = {
    labels: labels,
    datasets: [
      {
        label: labelTitle,
        data: data,
        backgroundColor: [
          'rgba(16, 185, 129, 0.7)', // Emerald for exports
          'rgba(244, 63, 94, 0.7)',   // Rose for imports
        ],
        borderColor: [
          'rgb(16, 185, 129)',
          'rgb(244, 63, 94)',
        ],
        borderWidth: 1,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  };

  return (
    <div style={{ height: '500px' }}>
      <Bar data={chartData} options={options} />
    </div>
  );
};

export default BarChart;
