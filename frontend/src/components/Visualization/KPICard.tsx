import React from 'react';

interface KPICardProps {
  data: Record<string, any>;
}

const KPICard: React.FC<KPICardProps> = ({ data }) => {
  const value = data.value || data[Object.keys(data)[0]] || 0;
  const label = data.label || 'Value';

  // Format number
  const formattedValue =
    typeof value === 'number'
      ? value.toLocaleString('en-US', {
          maximumFractionDigits: 2,
        })
      : value;

  return (
    <div className="card-gradient p-8 text-white shadow-premium animate-scale-in relative overflow-hidden">
      {/* Animated background pattern */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute inset-0" style={{
          backgroundImage: `radial-gradient(circle at 2px 2px, white 1px, transparent 0)`,
          backgroundSize: '40px 40px'
        }}></div>
      </div>
      
      {/* Glow effect */}
      <div className="absolute -inset-1 bg-gradient-to-r from-primary-600 to-accent-500 rounded-2xl blur-xl opacity-50"></div>
      
      <div className="relative z-10">
        <div className="flex items-center justify-between mb-4">
          <div className="text-sm font-semibold opacity-90 uppercase tracking-wider">{label}</div>
          <div className="w-12 h-12 rounded-xl bg-white/20 backdrop-blur-sm flex items-center justify-center">
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
          </div>
        </div>
        <div className="text-5xl font-bold mb-2">{formattedValue}</div>
        <div className="flex items-center space-x-2 text-sm opacity-75">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>Key Performance Indicator</span>
        </div>
      </div>
    </div>
  );
};

export default KPICard;

