import React from 'react';
import { LineChart as RechartsLineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface LineChartProps {
  data: Array<Record<string, any>>;
}

const LineChart: React.FC<LineChartProps> = ({ data }) => {
  // Extract columns (assuming first is x-axis, rest are y-axis)
  const columns = data.length > 0 ? Object.keys(data[0]) : [];
  const xAxisKey = columns[0] || 'label';
  const yAxisKeys = columns.slice(1);

  const colors = [
    { stroke: '#6366f1', fill: 'rgba(99, 102, 241, 0.1)' },
    { stroke: '#8b5cf6', fill: 'rgba(139, 92, 246, 0.1)' },
    { stroke: '#ec4899', fill: 'rgba(236, 72, 153, 0.1)' },
    { stroke: '#f59e0b', fill: 'rgba(245, 158, 11, 0.1)' },
    { stroke: '#10b981', fill: 'rgba(16, 185, 129, 0.1)' },
  ];

  return (
    <div className="card p-6 animate-fade-in-up border-2 border-purple-100">
      <div className="flex items-center space-x-2 mb-4">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-accent-500 flex items-center justify-center">
          <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
          </svg>
        </div>
        <h3 className="text-lg font-bold text-gray-900">Line Chart</h3>
      </div>
      <ResponsiveContainer width="100%" height={350}>
        <RechartsLineChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <defs>
            {yAxisKeys.map((key, index) => (
              <linearGradient key={key} id={`lineGradient${index}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={colors[index % colors.length].stroke} stopOpacity={0.3} />
                <stop offset="100%" stopColor={colors[index % colors.length].stroke} stopOpacity={0} />
              </linearGradient>
            ))}
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" opacity={0.5} />
          <XAxis 
            dataKey={xAxisKey} 
            stroke="#6b7280"
            tick={{ fill: '#6b7280', fontSize: 12 }}
            angle={-45}
            textAnchor="end"
            height={80}
          />
          <YAxis 
            stroke="#6b7280"
            tick={{ fill: '#6b7280', fontSize: 12 }}
          />
          <Tooltip 
            contentStyle={{
              backgroundColor: 'white',
              border: '2px solid #e5e7eb',
              borderRadius: '12px',
              boxShadow: '0 10px 40px -10px rgba(0, 0, 0, 0.1)'
            }}
            cursor={{ stroke: '#6366f1', strokeWidth: 1, strokeDasharray: '5 5' }}
          />
          <Legend wrapperStyle={{ paddingTop: '20px' }} />
          {yAxisKeys.map((key, index) => (
            <Line
              key={key}
              type="monotone"
              dataKey={key}
              stroke={colors[index % colors.length].stroke}
              strokeWidth={3}
              dot={{ fill: colors[index % colors.length].stroke, r: 5 }}
              activeDot={{ r: 7, fill: colors[index % colors.length].stroke }}
              fill={`url(#lineGradient${index})`}
            />
          ))}
        </RechartsLineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default LineChart;

