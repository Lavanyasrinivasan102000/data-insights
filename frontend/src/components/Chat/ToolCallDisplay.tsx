import React, { useState } from 'react';

interface ToolCallDisplayProps {
  sqlQuery?: string;
  fileId?: string;
  rowCount?: number;
}

const ToolCallDisplay: React.FC<ToolCallDisplayProps> = ({ 
  sqlQuery, 
  fileId, 
  rowCount 
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!sqlQuery && !fileId) {
    return null;
  }

  return (
    <div className="mt-3 ml-14 bg-gradient-to-r from-primary-50 to-purple-50 border-2 border-primary-200 rounded-xl p-4 animate-fade-in shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-primary-500 to-purple-500 flex items-center justify-center">
            <svg
              className="w-4 h-4 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"
              />
            </svg>
          </div>
          <span className="text-xs font-bold text-primary-700 uppercase tracking-wider">
            Tool Call
          </span>
        </div>
        {sqlQuery && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="px-3 py-1 text-xs font-semibold text-primary-700 bg-primary-100 hover:bg-primary-200 rounded-lg transition-colors"
          >
            {isExpanded ? 'Hide SQL' : 'Show SQL'}
          </button>
        )}
      </div>
      
      <div className="space-y-2">
        {fileId && (
          <div className="flex items-center space-x-2 text-xs">
            <svg className="w-4 h-4 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <span className="font-semibold text-gray-700">Data Source:</span>
            <span className="text-gray-600 font-mono">{fileId}</span>
          </div>
        )}
        
        {rowCount !== undefined && (
          <div className="flex items-center space-x-2 text-xs">
            <svg className="w-4 h-4 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
            </svg>
            <span className="font-semibold text-gray-700">Rows Returned:</span>
            <span className="text-primary-700 font-bold">{rowCount}</span>
          </div>
        )}
      </div>

      {sqlQuery && isExpanded && (
        <div className="mt-3 bg-white rounded-xl border-2 border-primary-200 p-4 animate-fade-in">
          <div className="flex items-center space-x-2 mb-2">
            <svg className="w-4 h-4 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <span className="text-xs font-bold text-gray-700 uppercase tracking-wider">SQL Query</span>
          </div>
          <pre className="text-xs text-gray-800 overflow-x-auto font-mono bg-gray-50 p-3 rounded-lg border border-gray-200 scrollbar-thin">
            {sqlQuery}
          </pre>
        </div>
      )}
    </div>
  );
};

export default ToolCallDisplay;

