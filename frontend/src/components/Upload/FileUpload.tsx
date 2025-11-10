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
  const [justUploadedFileId, setJustUploadedFileId] = useState<string | null>(null); // Track recently uploaded files
  const queryClient = useQueryClient();

  // Restore uploadedFileId from localStorage on mount
  // IMPORTANT: Restore immediately, verify file exists asynchronously
  // This prevents the table from disappearing during catalog verification
  useEffect(() => {
    // Always check localStorage on mount - restore immediately if available
    const storedFileId = localStorage.getItem(`lastUploadedFile_${userId}`);
    if (storedFileId && !uploadedFileId) {
      console.log('Restoring uploadedFileId from localStorage:', storedFileId);
      // Restore state immediately (optimistic restoration)
      setUploadedFileId(storedFileId);
      const storedRowCount = localStorage.getItem(`lastUploadedRowCount_${userId}`);
      if (storedRowCount) {
        setUploadedRowCount(parseInt(storedRowCount, 10));
      }
      
      // Verify file exists asynchronously (don't block table rendering)
      // If file doesn't exist, it will be cleared by the catalog subscription check
      queryClient.fetchQuery(['catalogs', userId]).then((catalogs: any) => {
        const fileExists = catalogs?.some((cat: any) => cat.file_id === storedFileId);
        if (!fileExists) {
          console.log('File not found in catalogs after verification, clearing state');
          // File was deleted, clear state and localStorage
          setUploadedFileId(null);
          setUploadedRowCount(null);
          localStorage.removeItem(`lastUploadedFile_${userId}`);
          localStorage.removeItem(`lastUploadedRowCount_${userId}`);
        } else {
          console.log('File verified in catalogs, table should be visible');
        }
      }).catch((error) => {
        console.error('Error fetching catalogs for verification:', error);
        // Don't clear state on error - might be a transient network issue
        // The table will show an error if the file truly doesn't exist
        console.warn('Catalog verification failed, but keeping table visible (might be transient error)');
      });
    } else if (!storedFileId) {
      console.log('No stored fileId found in localStorage');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]); // Only run on mount and when userId changes

  // Save to localStorage when file is successfully uploaded
  // Only save, never clear - this ensures table persists across refreshes and tab switches
  // Added try-catch for Edge compatibility
  useEffect(() => {
    if (uploadedFileId) {
      try {
        localStorage.setItem(`lastUploadedFile_${userId}`, uploadedFileId);
        if (uploadedRowCount !== null) {
          localStorage.setItem(`lastUploadedRowCount_${userId}`, uploadedRowCount.toString());
        }
        console.log('Saved uploadedFileId to localStorage in useEffect:', uploadedFileId);
      } catch (e) {
        console.error('Error saving to localStorage in useEffect:', e);
      }
    }
    // Note: We don't clear localStorage here - we want the table to persist even after refresh
  }, [uploadedFileId, uploadedRowCount, userId]);

  // Subscribe to catalog changes to detect when current file is deleted
  // IMPORTANT: Always enable when userId exists (not just when uploadedFileId exists)
  // This ensures catalog refetches after upload to include the new file
  const { data: catalogsForCheck } = useQuery(
    ['catalogs', userId],
    () => getCatalogs(userId),
    {
      enabled: !!userId, // Always enable when userId exists (Edge compatibility)
      refetchInterval: false,
      // Refetch when catalogs are invalidated (after upload)
      staleTime: 0, // Consider data stale immediately to allow refetch after upload
    }
  );

  // Only clear state if catalogs are loaded AND file doesn't exist
  // IMPORTANT: Don't clear state if file was just uploaded (race condition fix for Edge)
  useEffect(() => {
    if (uploadedFileId && catalogsForCheck && catalogsForCheck.length > 0) {
      // Don't check if this file was just uploaded (wait for catalog to update)
      if (justUploadedFileId === uploadedFileId) {
        console.log('File was just uploaded, skipping catalog check (waiting for catalog update)');
        return;
      }
      
      const fileExists = catalogsForCheck.some((cat) => cat.file_id === uploadedFileId);
      if (!fileExists) {
        console.log('File no longer exists in catalogs, clearing state');
        // File was deleted, clear state and localStorage
        setUploadedFileId(null);
        setUploadedRowCount(null);
        localStorage.removeItem(`lastUploadedFile_${userId}`);
        localStorage.removeItem(`lastUploadedRowCount_${userId}`);
      }
    }
    // Only run this check after catalogs are loaded, not during loading
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [catalogsForCheck, uploadedFileId, userId, justUploadedFileId]); // Only when catalogs or uploadedFileId changes

  // Clear justUploadedFileId flag after catalog includes the file (Edge compatibility)
  // This ensures we don't clear state before the backend adds the file to the catalog
  useEffect(() => {
    if (!justUploadedFileId) return;

    // Check if file exists in catalog
    if (catalogsForCheck) {
      const fileExistsInCatalog = catalogsForCheck.some((cat) => cat.file_id === justUploadedFileId);
      if (fileExistsInCatalog) {
        console.log('File found in catalog, clearing justUploadedFileId flag');
        setJustUploadedFileId(null);
        return;
      }
    }

    // File not in catalog yet, set a timer to clear flag after delay (safety fallback)
    // This prevents the flag from staying set forever if catalog never updates
    const timer = setTimeout(() => {
      console.log('Clearing justUploadedFileId flag after timeout (catalog may have updated)');
      setJustUploadedFileId(null);
    }, 5000); // Wait 5 seconds max for catalog to update

    return () => clearTimeout(timer);
  }, [justUploadedFileId, catalogsForCheck]);

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
          console.log('File uploaded successfully, setting uploadedFileId:', lastFileId);
          // Set flag to prevent catalog check from clearing state immediately (Edge fix)
          setJustUploadedFileId(lastFileId);
          // Update state - use functional updates to ensure state persistence in Edge
          setUploadedFileId((prev) => {
            console.log('Setting uploadedFileId state:', lastFileId, 'Previous:', prev);
            return lastFileId;
          });
          setUploadedRowCount((prev) => {
            console.log('Setting uploadedRowCount state:', lastRowCount, 'Previous:', prev);
            return lastRowCount;
          });
          
          // Force save to localStorage immediately (Edge compatibility)
          try {
            localStorage.setItem(`lastUploadedFile_${userId}`, lastFileId);
            if (lastRowCount !== null) {
              localStorage.setItem(`lastUploadedRowCount_${userId}`, lastRowCount.toString());
            }
            console.log('Saved to localStorage:', lastFileId);
          } catch (e) {
            console.error('Error saving to localStorage:', e);
          }
        }
        setUploadStatus(`Successfully uploaded ${acceptedFiles.length} file(s)`);
        // Invalidate and refetch queries to refresh file list
        // Use setTimeout to ensure state is set before catalog refetch (Edge compatibility)
        setTimeout(() => {
          queryClient.invalidateQueries(['files', userId]);
          // Force refetch catalog to include the newly uploaded file
          queryClient.refetchQueries(['catalogs', userId], { active: true });
        }, 100);
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
      {uploadedFileId ? (
        <div className="mt-6">
          <InteractiveDataTable 
            tableName={uploadedFileId} 
            rowCount={uploadedRowCount || undefined}
            onTableNotFound={() => {
              console.log('Table not found, clearing state');
              // Clear state and localStorage when table is not found (file was deleted)
              setUploadedFileId(null);
              setUploadedRowCount(null);
              setJustUploadedFileId(null);
              try {
                localStorage.removeItem(`lastUploadedFile_${userId}`);
                localStorage.removeItem(`lastUploadedRowCount_${userId}`);
              } catch (e) {
                console.error('Error removing from localStorage:', e);
              }
            }}
          />
        </div>
      ) : (
        <div className="mt-6 text-sm text-gray-500 text-center py-4">
          {/* Debug info - only show in development */}
          {process.env.NODE_ENV === 'development' && (
            <div className="text-xs text-gray-400 space-y-1">
              <p>No file uploaded yet. Upload a file to see the data table.</p>
              <p className="text-xs text-gray-300 mt-2">
                Debug: uploadedFileId = {uploadedFileId || 'null'}, 
                justUploaded = {justUploadedFileId || 'null'}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default FileUpload;
