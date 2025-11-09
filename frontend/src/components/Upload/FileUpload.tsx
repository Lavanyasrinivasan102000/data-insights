import React, { useState, useCallback, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { uploadFile, getCatalogs } from '../../services/api';
import { useQueryClient, useQuery } from 'react-query';
import InteractiveDataTable from '../DataTable/InteractiveDataTable';

interface FileUploadProps {
  userId: string;
}

const FileUpload: React.FC<FileUploadProps> = ({ userId }) => {
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const [uploadedFileId, setUploadedFileId] = useState<string | null>(null);
  const [uploadedRowCount, setUploadedRowCount] = useState<number | null>(null);
  const queryClient = useQueryClient();

  // Restore uploadedFileId from localStorage on mount, but verify file still exists
  // This ensures the table persists across page refreshes and tab switches
  useEffect(() => {
    // Always check localStorage on mount - restore if available and state is empty
    if (!uploadedFileId) {
      const storedFileId = localStorage.getItem(`lastUploadedFile_${userId}`);
      if (storedFileId) {
        // Verify the file still exists by checking the catalogs
        queryClient.fetchQuery(['catalogs', userId]).then((catalogs: any) => {
          const fileExists = catalogs?.some((cat: any) => cat.file_id === storedFileId);
          if (fileExists) {
            setUploadedFileId(storedFileId);
            // Try to get row count from storage if available
            const storedRowCount = localStorage.getItem(`lastUploadedRowCount_${userId}`);
            if (storedRowCount) {
              setUploadedRowCount(parseInt(storedRowCount, 10));
            }
          } else {
            // File was deleted, clear localStorage
            localStorage.removeItem(`lastUploadedFile_${userId}`);
            localStorage.removeItem(`lastUploadedRowCount_${userId}`);
          }
        }).catch(() => {
          // If query fails, clear localStorage to be safe
          localStorage.removeItem(`lastUploadedFile_${userId}`);
          localStorage.removeItem(`lastUploadedRowCount_${userId}`);
        });
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]); // Only run on mount and when userId changes

  // Save to localStorage when file is successfully uploaded
  // Only save, never clear - this ensures table persists across refreshes and tab switches
  useEffect(() => {
    if (uploadedFileId) {
      localStorage.setItem(`lastUploadedFile_${userId}`, uploadedFileId);
      if (uploadedRowCount !== null) {
        localStorage.setItem(`lastUploadedRowCount_${userId}`, uploadedRowCount.toString());
      }
    }
    // Note: We don't clear localStorage here - we want the table to persist even after refresh
  }, [uploadedFileId, uploadedRowCount, userId]);

  // Subscribe to catalog changes to detect when current file is deleted
  useQuery(
    ['catalogs', userId],
    () => getCatalogs(userId),
    {
      enabled: !!userId && !!uploadedFileId,
      refetchInterval: false,
      onSuccess: (catalogs) => {
        // Check if current uploadedFileId still exists
        if (uploadedFileId && catalogs) {
          const fileExists = catalogs.some((cat) => cat.file_id === uploadedFileId);
          if (!fileExists) {
            // File was deleted, clear state and localStorage
            setUploadedFileId(null);
            setUploadedRowCount(null);
            localStorage.removeItem(`lastUploadedFile_${userId}`);
            localStorage.removeItem(`lastUploadedRowCount_${userId}`);
          }
        }
      }
    }
  );

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      if (acceptedFiles.length === 0) return;

      setUploading(true);
      setUploadStatus(null);
      // Don't clear uploadedFileId - keep the table visible during upload
      // It will be updated with the new file ID after upload completes

      try {
        // Process files and update state
        let lastFileId: string | null = null;
        let lastRowCount: number | null = null;
        for (const file of acceptedFiles) {
          const response = await uploadFile(userId, file);
          lastFileId = response.file_id;
          lastRowCount = response.row_count;
        }
        // Update state after all files are processed
        // This will automatically save to localStorage and update the table
        if (lastFileId) {
          setUploadedFileId(lastFileId);
          setUploadedRowCount(lastRowCount);
        }
        setUploadStatus(`Successfully uploaded ${acceptedFiles.length} file(s)`);
        // Invalidate queries to refresh file list
        queryClient.invalidateQueries(['files', userId]);
        queryClient.invalidateQueries(['catalogs', userId]);
      } catch (error: any) {
        console.error('Upload error:', error);
        // Extract error message - check multiple possible locations
        let errorMessage = 'Unknown error occurred';
        
        if (error.message) {
          errorMessage = error.message;
        } else if (error.response?.data?.detail) {
          errorMessage = error.response.data.detail;
        } else if (error.response?.data?.message) {
          errorMessage = error.response.data.message;
        } else if (error.response?.status) {
          errorMessage = `Server error (${error.response.status})`;
        }
        
        setUploadStatus(`Error uploading file: ${errorMessage}`);
      } finally {
        setUploading(false);
      }
    },
    [userId, queryClient]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/json': ['.json'],
    },
    maxSize: 10 * 1024 * 1024, // 10MB
  });

  return (
    <div className="card p-8 animate-fade-in-up">
      <div className="flex items-center space-x-3 mb-6">
        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center shadow-lg shadow-primary-500/30">
          <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
        </div>
        <div>
          <h2 className="text-2xl font-display font-bold text-gray-900">Upload Files</h2>
          <p className="text-sm text-gray-500 mt-0.5">Upload your data files to get started</p>
        </div>
      </div>
      
      <div
        {...getRootProps()}
        className={`relative border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all duration-300 overflow-hidden group ${
          isDragActive
            ? 'border-primary-500 bg-gradient-to-br from-primary-50 to-accent-50 scale-105 shadow-premium'
            : 'border-gray-300 hover:border-primary-400 hover:bg-gradient-to-br hover:from-primary-50/50 hover:to-accent-50/50 hover:shadow-lg'
        }`}
      >
        <input {...getInputProps()} />
        
        {/* Animated background gradient on hover */}
        <div className="absolute inset-0 opacity-0 group-hover:opacity-5 transition-opacity duration-300 bg-gradient-to-br from-primary-600 via-purple-600 to-accent-600"></div>
        
        <div className="relative space-y-4">
          <div className="relative inline-block">
            <div className={`w-20 h-20 mx-auto rounded-2xl flex items-center justify-center transition-all duration-300 ${
              isDragActive 
                ? 'bg-gradient-to-br from-primary-500 to-accent-500 scale-110 shadow-lg shadow-primary-500/50' 
                : 'bg-gradient-to-br from-primary-100 to-accent-100 group-hover:scale-110 group-hover:shadow-lg'
            }`}>
              <svg
                className={`w-10 h-10 transition-colors duration-300 ${
                  isDragActive ? 'text-white' : 'text-primary-600'
                }`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                />
              </svg>
            </div>
            {isDragActive && (
              <div className="absolute -inset-2 bg-primary-400/20 rounded-2xl animate-pulse"></div>
            )}
          </div>
          
          {isDragActive ? (
            <div className="space-y-2 animate-scale-in">
              <p className="text-lg font-semibold text-primary-700">Drop the files here...</p>
              <p className="text-sm text-primary-600">Release to upload</p>
            </div>
          ) : (
            <div className="space-y-2">
              <p className="text-lg font-semibold text-gray-700 group-hover:text-primary-700 transition-colors">
                Drag & drop files here
              </p>
              <p className="text-sm text-gray-500 group-hover:text-primary-600 transition-colors">
                or <span className="font-semibold text-primary-600 underline">click to browse</span>
              </p>
              <div className="flex items-center justify-center space-x-4 mt-4 pt-4 border-t border-gray-200">
                <div className="flex items-center space-x-2 text-xs text-gray-500">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <span>CSV, JSON</span>
                </div>
                <div className="flex items-center space-x-2 text-xs text-gray-500">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
                  </svg>
                  <span>Max 10MB</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {uploading && (
        <div className="mt-6 flex items-center justify-center space-x-3 p-4 bg-gradient-to-r from-primary-50 to-accent-50 rounded-xl border border-primary-200 animate-fade-in">
          <div className="relative">
            <div className="animate-spin rounded-full h-6 w-6 border-2 border-primary-200 border-t-primary-600"></div>
            <div className="absolute inset-0 animate-ping rounded-full h-6 w-6 border-2 border-primary-400 opacity-20"></div>
          </div>
          <span className="text-sm font-semibold text-primary-700">Uploading and processing...</span>
        </div>
      )}

      {uploadStatus && (
        <div
          className={`mt-6 p-4 rounded-xl border-2 animate-fade-in ${
            uploadStatus.includes('Error')
              ? 'bg-red-50 border-red-200 text-red-800'
              : 'bg-green-50 border-green-200 text-green-800'
          }`}
        >
          <div className="flex items-center space-x-2">
            {uploadStatus.includes('Error') ? (
              <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            ) : (
              <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            )}
            <span className="font-semibold">{uploadStatus}</span>
          </div>
        </div>
      )}

      {/* Interactive Data Table - show immediately after upload */}
      {uploadedFileId && (
        <InteractiveDataTable 
          tableName={uploadedFileId} 
          rowCount={uploadedRowCount || undefined}
          onTableNotFound={() => {
            // Clear state and localStorage when table is not found (file was deleted)
            setUploadedFileId(null);
            setUploadedRowCount(null);
            localStorage.removeItem(`lastUploadedFile_${userId}`);
            localStorage.removeItem(`lastUploadedRowCount_${userId}`);
          }}
        />
      )}
    </div>
  );
};

export default FileUpload;
