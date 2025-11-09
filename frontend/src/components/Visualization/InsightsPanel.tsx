import React from 'react';
import ReactMarkdown from 'react-markdown';

interface InsightsPanelProps {
  insightsText: string;
}

const InsightsPanel: React.FC<InsightsPanelProps> = ({ insightsText }) => {
  return (
    <div className="card p-6 animate-fade-in-up border-2 border-purple-100 bg-gradient-to-br from-purple-50/50 to-accent-50/50">
      <div className="flex items-center space-x-3 mb-6">
        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-accent-500 flex items-center justify-center shadow-lg shadow-purple-500/30">
          <svg
            className="w-6 h-6 text-white"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
            />
          </svg>
        </div>
        <div>
          <h3 className="text-xl font-display font-bold text-gray-900">Statistical Insights</h3>
          <p className="text-sm text-gray-600 mt-0.5">AI-generated data analysis</p>
        </div>
      </div>

      <div className="prose prose-sm max-w-none bg-white/60 backdrop-blur-sm rounded-xl p-6 border border-gray-200">
        <ReactMarkdown
          components={{
            h2: (props) => (
              <h2 className="text-lg font-bold text-gradient mt-6 mb-3 flex items-center" {...props} />
            ),
            h3: (props) => (
              <h3 className="text-base font-semibold text-primary-700 mt-4 mb-2" {...props} />
            ),
            ul: (props) => (
              <ul className="list-disc list-inside space-y-2 text-gray-700 my-3" {...props} />
            ),
            li: (props) => (
              <li className="text-sm leading-relaxed" {...props} />
            ),
            p: (props) => (
              <p className="text-sm text-gray-700 mb-3 leading-relaxed" {...props} />
            ),
            strong: (props) => (
              <strong className="font-bold text-primary-700" {...props} />
            ),
            code: (props) => (
              <code className="bg-primary-100 text-primary-800 px-2 py-1 rounded-lg text-xs font-mono" {...props} />
            ),
          }}
        >
          {insightsText}
        </ReactMarkdown>
      </div>
    </div>
  );
};

export default InsightsPanel;
