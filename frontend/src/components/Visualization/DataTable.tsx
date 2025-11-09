import React from 'react';

interface DataTableProps {
  rows: Array<Record<string, any>>;
  columns: string[];
}

const DataTable: React.FC<DataTableProps> = ({ rows, columns }) => {
  if (rows.length === 0) {
    return (
      <div className="bg-white border rounded-lg p-4 text-center text-gray-500">
        No data to display
      </div>
    );
  }

  const displayColumns = columns.length > 0 ? columns : Object.keys(rows[0] || {});
  const displayRows = rows.slice(0, 10); // Only show first 10 rows initially
  const hasMore = rows.length > 10;

  return (
    <div className="card overflow-hidden animate-fade-in-up border-2 border-gray-100">
      <div className="px-6 py-4 bg-gradient-to-r from-primary-50 to-accent-50 border-b border-gray-200 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center">
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
          </div>
          <div>
            <h3 className="text-lg font-bold text-gray-900">Data Table</h3>
            <p className="text-xs text-gray-600">Showing {displayRows.length} of {rows.length} rows</p>
          </div>
        </div>
      </div>
      <div className="overflow-x-auto max-h-96 overflow-y-auto scrollbar-thin">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gradient-to-r from-gray-50 to-gray-100 sticky top-0 z-10">
            <tr>
              {displayColumns.map((col) => (
                <th
                  key={col}
                  className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider border-r border-gray-200 last:border-r-0"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {displayRows.map((row, index) => (
              <tr 
                key={index} 
                className="hover:bg-gradient-to-r hover:from-primary-50/50 hover:to-accent-50/50 transition-colors duration-150"
              >
                {displayColumns.map((col) => (
                  <td
                    key={col}
                    className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-medium border-r border-gray-100 last:border-r-0"
                  >
                    {row[col] !== null && row[col] !== undefined
                      ? String(row[col])
                      : <span className="text-gray-400">-</span>}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {hasMore && (
        <div className="px-6 py-3 bg-gray-50 border-t border-gray-200 text-center">
          <p className="text-xs text-gray-600 font-medium">
            Scroll to view more rows or refine your query for better results
          </p>
        </div>
      )}
      <div className="px-6 py-4 bg-gradient-to-r from-primary-50 to-accent-50 border-t border-gray-200 flex items-center justify-center gap-2">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-400 to-accent-400 flex items-center justify-center">
          <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
          </svg>
        </div>
        <span className="text-sm font-semibold text-primary-700">You can edit this data! Try editing with natural language.</span>
      </div>
    </div>
  );
};

export default DataTable;

