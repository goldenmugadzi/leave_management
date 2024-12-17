import React, { useEffect, useRef } from 'react';
import Chart from 'chart.js/auto';

interface Dataset {
  label: string;
  data: number[];
  backgroundColor: string;
  borderColor: string;
  borderWidth: number;
  yAxisID?: string;
}

interface MultiBarChartProps {
  labels: string[];
  datasets: Dataset[];
  title: string;
  height?: number;
  width?: number;
  showLegend?: boolean;
  legendPosition?: 'top' | 'bottom' | 'left' | 'right';
}

const MultiBarChart: React.FC<MultiBarChartProps> = ({
  labels,
  datasets,
  title,
  height = 300,
  width = '100%',
  showLegend = true,
  legendPosition = 'bottom'
}) => {
  const chartRef = useRef<HTMLCanvasElement | null>(null);
  const chartInstance = useRef<Chart | null>(null);

  useEffect(() => {
    if (chartRef.current) {
      // Destroy existing chart if it exists
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }

      const ctx = chartRef.current.getContext('2d');
      if (ctx) {
        chartInstance.current = new Chart(ctx, {
          type: 'bar',
          data: {
            labels,
            datasets
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
              x: {
                grid: {
                  display: false
                }
              },
              y: {
                beginAtZero: true,
                title: {
                  display: true,
                  text: 'Count'
                }
              },
              // Add percentage scale if needed
              percentage: {
                position: 'right',
                beginAtZero: true,
                max: 100,
                title: {
                  display: true,
                  text: 'Percentage'
                },
                grid: {
                  display: false
                }
              }
            },
            plugins: {
              legend: {
                display: showLegend,
                position: legendPosition
              },
              title: {
                display: true,
                text: title
              },
              tooltip: {
                callbacks: {
                  label: function(context) {
                    let label = context.dataset.label || '';
                    if (label) {
                      label += ': ';
                    }
                    if (context.dataset.yAxisID === 'percentage') {
                      label += context.parsed.y + '%';
                    } else {
                      label += context.parsed.y;
                    }
                    return label;
                  }
                }
              }
            }
          }
        });
      }
    }

    // Cleanup function
    return () => {
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }
    };
  }, [labels, datasets, title, showLegend, legendPosition]);

  return (
    <div style={{ height, width }}>
      <canvas ref={chartRef} />
    </div>
  );
};

export default MultiBarChart;
