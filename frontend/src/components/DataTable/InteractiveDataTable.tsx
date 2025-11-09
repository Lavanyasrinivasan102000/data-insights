import React, { useState, useEffect } from 'react';
import { useQuery } from 'react-query';
import { getTableData, getTableColumns } from '../../services/api';
import { useDebounce } from '../../hooks/useDebounce';

interface InteractiveDataTableProps {
  tableName: string;
  rowCount?: number;
  onTableNotFound?: () => void;
}

const InteractiveDataTable: React.FC<InteractiveDataTableProps> = ({ tableName, rowCount, onTableNotFound }) => {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState<string | null>(null);
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const debouncedSearch = useDebounce(search, 300);

  // Always show table (no row count restriction)
  const shouldShowTable = true;

  // Fetch table columns
  const { data: columnsData } = useQuery(
    ['tableColumns', tableName],
    () => getTableColumns(tableName),
    {
      enabled: shouldShowTable && !!tableName,
    }
  );

  // Fetch paginated data
  const { data, isLoading, error } = useQuery(
    ['tableData', tableName, page, pageSize, debouncedSearch, sortBy, sortOrder],
    () =>
      getTableData(tableName, {
        page,
        page_size: pageSize,
        search: debouncedSearch || undefined,
        sort_by: sortBy || undefined,
        sort_order: sortOrder,
      }),
    {
      enabled: shouldShowTable && !!tableName,
    }
  );

  // Reset to page 1 when search changes
  useEffect(() => {
    setPage(1);
  }, [debouncedSearch]);

  const handleSort = (column: string) => {
    if (sortBy === column) {
      // Toggle sort order
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortOrder('asc');
    }
    setPage(1);
  };

  // Handle errors, especially "table not found" errors
  // NOTE: This useEffect must be called BEFORE any early returns (React Hooks rule)
  useEffect(() => {
    if (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      // If table not found, it might have been deleted - clear localStorage and notify parent
      if (errorMessage.includes('not found') || errorMessage.includes('Table')) {
        // Extract userId from localStorage keys (this is a bit of a hack, but works)
        const keys = Object.keys(localStorage);
        const fileStorageKeys = keys.filter(key => key.startsWith('lastUploadedFile_'));
        fileStorageKeys.forEach(key => {
          const storedFileId = localStorage.getItem(key);
          if (storedFileId === tableName) {
            // This is the deleted file, clear its localStorage
            localStorage.removeItem(key);
            const userId = key.replace('lastUploadedFile_', '');
            localStorage.removeItem(`lastUploadedRowCount_${userId}`);
            
            // Notify parent component to clear state
            if (onTableNotFound) {
              onTableNotFound();
            }
          }
        });
      }
    }
  }, [error, tableName, onTableNotFound]);

  const columns = columnsData?.columns || data?.columns || [];
  const pagination = data?.pagination;
  const rows = data?.data || [];

  if (!shouldShowTable) {
    return null;
  }

  if (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    const isTableNotFound = errorMessage.includes('not found') || errorMessage.includes('Table');
    
    return (
      <div className="mt-6 card p-6 border-2 border-red-200 bg-red-50 animate-fade-in">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2 text-red-800">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <span className="font-semibold">Error loading data table</span>
          </div>
        </div>
        <div className="text-sm text-red-700">
          {isTableNotFound ? (
            <>
              <p>The data table for this file no longer exists. This usually happens when:</p>
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li>The file was deleted</li>
                <li>The table was removed from the database</li>
              </ul>
              <p className="mt-3 text-xs text-red-600 italic">
                The table reference has been cleared. Please upload a new file to view data.
              </p>
            </>
          ) : (
            <>
              <p>Unable to load the data table. This might be because:</p>
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li>The backend server is not running</li>
                <li>The table name is incorrect</li>
                <li>There was a network error</li>
              </ul>
            </>
          )}
          <p className="mt-2 font-mono text-xs bg-red-100 p-2 rounded">
            {errorMessage}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="mt-6 card p-6 animate-fade-in-up border-2 border-primary-200">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center">
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
              />
            </svg>
          </div>
          <h3 className="text-lg font-bold text-gray-900">Data Preview</h3>
          {pagination && (
            <span className="text-sm text-gray-500">
              ({pagination.total_rows.toLocaleString()} rows)
            </span>
          )}
        </div>
      </div>

      {/* Search and Page Size Controls */}
      <div className="mb-4 flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="relative flex-1 max-w-md">
          <input
            type="text"
            placeholder="Search across all columns..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full px-4 py-2 pl-10 border-2 border-gray-300 rounded-xl focus:border-primary-500 focus:ring-2 focus:ring-primary-200 outline-none transition-all"
          />
          <svg
            className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>
        <div className="flex items-center space-x-2">
          <label className="text-sm text-gray-600 font-medium">Rows per page:</label>
          <select
            value={pageSize}
            onChange={(e) => {
              setPageSize(Number(e.target.value));
              setPage(1);
            }}
            className="px-3 py-2 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 outline-none transition-all"
          >
            <option value={10}>10</option>
            <option value={25}>25</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-xl border-2 border-gray-200 min-h-[300px]">
        {isLoading && (!data || rows.length === 0) ? (
          <div className="p-8 text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-2 border-primary-200 border-t-primary-600"></div>
            <p className="mt-2 text-sm text-gray-600 font-medium">Loading data table...</p>
            <p className="mt-1 text-xs text-gray-500">Fetching data from server</p>
          </div>
        ) : !isLoading && rows.length === 0 && columns.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <svg className="w-12 h-12 mx-auto text-gray-400 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
            </svg>
            <p className="font-medium text-gray-700">No data available</p>
            <p className="mt-1 text-sm text-gray-500">The table is empty or could not be loaded</p>
          </div>
        ) : rows.length === 0 && !isLoading && columns.length > 0 ? (
          <div className="p-8 text-center text-gray-500">
            <p className="font-medium">No data found</p>
            {debouncedSearch && (
              <p className="mt-2 text-sm">Try adjusting your search terms</p>
            )}
          </div>
        ) : (
          <table className="w-full divide-y divide-gray-200">
            <thead className="bg-gradient-to-r from-primary-50 to-accent-50">
              <tr>
                {columns.map((column) => (
                  <th
                    key={column}
                    onClick={() => handleSort(column)}
                    className="px-4 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider cursor-pointer hover:bg-primary-100 transition-colors"
                  >
                    <div className="flex items-center space-x-1">
                      <span>{column}</span>
                      {sortBy === column && (
                        <svg
                          className={`w-4 h-4 ${sortOrder === 'asc' ? '' : 'transform rotate-180'}`}
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M5 15l7-7 7 7"
                          />
                        </svg>
                      )}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {rows.map((row, idx) => (
                <tr key={idx} className="hover:bg-gray-50 transition-colors">
                  {columns.map((column) => (
                    <td key={column} className="px-4 py-3 whitespace-nowrap text-sm text-gray-700">
                      {row[column] !== null && row[column] !== undefined
                        ? String(row[column])
                        : '-'}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination Controls */}
      {pagination && pagination.total_pages > 1 && (
        <div className="mt-4 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="text-sm text-gray-600">
            Showing {((pagination.page - 1) * pagination.page_size + 1).toLocaleString()} to{' '}
            {Math.min(pagination.page * pagination.page_size, pagination.total_rows).toLocaleString()}{' '}
            of {pagination.total_rows.toLocaleString()} rows
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setPage(1)}
              disabled={!pagination.has_previous}
              className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border-2 border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              First
            </button>
            <button
              onClick={() => setPage(page - 1)}
              disabled={!pagination.has_previous}
              className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border-2 border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Previous
            </button>
            <span className="px-4 py-1.5 text-sm font-medium text-gray-700">
              Page {pagination.page} of {pagination.total_pages}
            </span>
            <button
              onClick={() => setPage(page + 1)}
              disabled={!pagination.has_next}
              className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border-2 border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Next
            </button>
            <button
              onClick={() => setPage(pagination.total_pages)}
              disabled={!pagination.has_next}
              className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border-2 border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Last
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default InteractiveDataTable;

