import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { getCatalogs, getFileCatalog, deleteFile } from '../../services/api';

interface FileListProps {
  userId: string;
}

const FileList: React.FC<FileListProps> = ({ userId }) => {
  const [expandedFileId, setExpandedFileId] = useState<string | null>(null);
  const [deletingFileId, setDeletingFileId] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const { data: catalogs, isLoading, error } = useQuery(
    ['catalogs', userId],
    () => getCatalogs(userId),
    {
      enabled: !!userId,
      refetchInterval: 5000, // Refetch every 5 seconds
    }
  );

  const deleteMutation = useMutation(
    (fileId: string) => deleteFile(fileId),
    {
      onSuccess: (_, deletedFileId) => {
        // Invalidate and refetch the catalogs
        queryClient.invalidateQueries(['catalogs', userId]);
        setDeletingFileId(null);
        
        // Clear localStorage if the deleted file was the one stored there
        const storedFileId = localStorage.getItem(`lastUploadedFile_${userId}`);
        if (storedFileId === deletedFileId) {
          localStorage.removeItem(`lastUploadedFile_${userId}`);
          localStorage.removeItem(`lastUploadedRowCount_${userId}`);
          console.log('Cleared localStorage for deleted file:', deletedFileId);
        }
      },
      onError: (error) => {
        console.error('Error deleting file:', error);
        alert('Failed to delete file. Please try again.');
        setDeletingFileId(null);
      }
    }
  );

  const { data: fullCatalog } = useQuery(
    ['catalog', expandedFileId],
    () => getFileCatalog(expandedFileId!),
    {
      enabled: !!expandedFileId,
    }
  );

  const handleDelete = (fileId: string) => {
    if (window.confirm(`Are you sure you want to delete this file? This action cannot be undone.`)) {
      setDeletingFileId(fileId);
      deleteMutation.mutate(fileId);
    }
  };

  if (isLoading) {
    return (
      <div className="card p-8 animate-fade-in-up">
        <div className="flex items-center space-x-3 mb-6">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center shadow-lg shadow-primary-500/30">
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <div>
            <h2 className="text-2xl font-display font-bold text-gray-900">Uploaded Files</h2>
            <p className="text-sm text-gray-500 mt-0.5">Your uploaded data files</p>
          </div>
        </div>
        <div className="text-center py-12">
          <div className="relative inline-block">
            <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-200 border-t-primary-600 mx-auto"></div>
            <div className="absolute inset-0 animate-pulse-slow">
              <div className="rounded-full h-12 w-12 bg-primary-400/20 mx-auto"></div>
            </div>
          </div>
          <p className="mt-4 text-gray-600 font-medium">Loading files...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card p-8 animate-fade-in-up">
        <div className="flex items-center space-x-3 mb-6">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-red-500 to-red-600 flex items-center justify-center shadow-lg shadow-red-500/30">
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <h2 className="text-2xl font-display font-bold text-gray-900">Uploaded Files</h2>
            <p className="text-sm text-gray-500 mt-0.5">Your uploaded data files</p>
          </div>
        </div>
        <div className="p-4 bg-red-50 border-2 border-red-200 rounded-xl text-red-800">
          <div className="flex items-center space-x-2">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="font-semibold">Error loading files</span>
          </div>
        </div>
      </div>
    );
  }

  if (!catalogs || catalogs.length === 0) {
    return (
      <div className="card p-8 animate-fade-in-up">
        <div className="flex items-center space-x-3 mb-6">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center shadow-lg shadow-primary-500/30">
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <div>
            <h2 className="text-2xl font-display font-bold text-gray-900">Uploaded Files</h2>
            <p className="text-sm text-gray-500 mt-0.5">Your uploaded data files</p>
          </div>
        </div>
        <div className="text-center py-12">
          <div className="w-20 h-20 mx-auto rounded-2xl bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center mb-4">
            <svg className="w-10 h-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <p className="text-gray-500 font-medium">No files uploaded yet</p>
          <p className="text-sm text-gray-400 mt-1">Upload a file to get started</p>
        </div>
      </div>
    );
  }

  return (
    <div className="card p-8 animate-fade-in-up">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center shadow-lg shadow-primary-500/30">
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <div>
            <h2 className="text-2xl font-display font-bold text-gray-900">Uploaded Files</h2>
            <p className="text-sm text-gray-500 mt-0.5">
              {catalogs.length} file{catalogs.length !== 1 ? 's' : ''} uploaded
            </p>
          </div>
        </div>
      </div>
      <div className="space-y-4">
        {catalogs.map((catalog, index) => {
          const isExpanded = expandedFileId === catalog.file_id;
          const displaySummary = isExpanded && fullCatalog 
            ? fullCatalog.summary 
            : catalog.summary;

          return (
            <div
              key={catalog.file_id}
              className="group relative bg-gradient-to-br from-white to-gray-50 border-2 border-gray-200 rounded-2xl p-6 hover:border-primary-300 hover:shadow-lg transition-all duration-300 animate-fade-in-up"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-3 mb-3">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-400 to-accent-400 flex items-center justify-center flex-shrink-0 shadow-md">
                      <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-bold text-gray-900 truncate">{catalog.file_id}</h3>
                    </div>
                  </div>
                  
                  <div className="mt-4">
                    {isExpanded ? (
                      <div className="animate-fade-in">
                        <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl p-4 border border-gray-200">
                          <pre className="whitespace-pre-wrap text-sm text-gray-700 font-sans leading-relaxed scrollbar-thin max-h-96 overflow-y-auto">
                            {displaySummary}
                          </pre>
                        </div>
                      </div>
                    ) : (
                      <p className="text-sm text-gray-600 line-clamp-3 leading-relaxed">
                        {catalog.summary.substring(0, 300)}
                        {catalog.summary.length > 300 && '...'}
                      </p>
                    )}
                  </div>
                </div>
              </div>
              
              <div className="flex items-center justify-end gap-2 mt-4 pt-4 border-t border-gray-200">
                <button
                  onClick={() => setExpandedFileId(isExpanded ? null : catalog.file_id)}
                  className="px-4 py-2 text-sm font-semibold rounded-lg bg-primary-50 text-primary-700 hover:bg-primary-100 hover:text-primary-800 transition-all duration-200 flex items-center space-x-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={isExpanded ? "M5 15l7-7 7 7" : "M19 9l-7 7-7-7"} />
                  </svg>
                  <span>{isExpanded ? 'Hide Summary' : 'Show Full Summary'}</span>
                </button>
                <button
                  onClick={() => handleDelete(catalog.file_id)}
                  disabled={deleteMutation.isLoading}
                  className="px-4 py-2 text-sm font-semibold rounded-lg bg-red-50 text-red-700 hover:bg-red-100 hover:text-red-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center space-x-2"
                >
                  {deleteMutation.isLoading && deletingFileId === catalog.file_id ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-2 border-red-300 border-t-red-600"></div>
                      <span>Deleting...</span>
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                      <span>Delete</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default FileList;
