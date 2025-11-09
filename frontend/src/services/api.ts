import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || process.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000, // 60 second timeout for file uploads
});

// Add request interceptor for debugging
api.interceptors.request.use(
  (config) => {
    console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('[API] Request error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for better error handling
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.code === 'ECONNABORTED') {
      console.error('[API] Request timeout:', error);
      error.message = 'Request timeout. The server is taking too long to respond.';
    } else if (error.code === 'ERR_NETWORK') {
      console.error('[API] Network error:', error);
      error.message = `Network error: Unable to connect to the server at ${API_URL}. Please make sure the backend server is running.`;
    } else if (error.response) {
      // Server responded with error status
      console.error('[API] Server error:', error.response.status, error.response.data);
      error.message = error.response.data?.detail || error.response.data?.message || `Server error: ${error.response.status}`;
    } else if (error.request) {
      // Request was made but no response received
      console.error('[API] No response received:', error.request);
      error.message = `No response from server at ${API_URL}. Please check if the backend is running.`;
    } else {
      // Something else happened
      console.error('[API] Error:', error.message);
      error.message = error.message || 'An unexpected error occurred';
    }
    return Promise.reject(error);
  }
);

export interface SignInResponse {
  user_id: string;
}

export interface UploadResponse {
  file_id: string;
  filename: string;
  status: string;
  row_count: number;
}

export interface CatalogSummary {
  file_id: string;
  summary: string;
}

export interface ChatMessageRequest {
  user_id: string;
  message: string;
  session_id?: string;
}

export interface VisualizationConfig {
  type: string;
  show_bar_chart: boolean;
  input_data?: Array<Record<string, any>>;
}

export interface ChatMessageResponse {
  message: string;
  data?: {
    rows: Array<Record<string, any>>;
    columns: string[];
    sql_query?: string;
    file_id?: string;
  };
  visualization?: VisualizationConfig;
  session_id: string;
}

// Auth API
export const signIn = async (): Promise<SignInResponse> => {
  const response = await api.post<SignInResponse>('/api/auth/signin');
  return response.data;
};

// Upload API
export const uploadFile = async (
  userId: string,
  file: File
): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('user_id', userId);

  const response = await api.post<UploadResponse>(
    '/api/upload/',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );
  return response.data;
};

export const getFileInfo = async (fileId: string) => {
  const response = await api.get(`/api/upload/${fileId}`);
  return response.data;
};

export const deleteFile = async (fileId: string) => {
  const response = await api.delete(`/api/upload/${fileId}`);
  return response.data;
};

// Catalog API
export const getCatalogs = async (userId: string): Promise<CatalogSummary[]> => {
  const response = await api.get<CatalogSummary[]>(`/api/catalog/${userId}`);
  return response.data;
};

export const getFileCatalog = async (fileId: string) => {
  const response = await api.get(`/api/catalog/file/${fileId}`);
  return response.data;
};

// Chat API
export const sendMessage = async (
  request: ChatMessageRequest
): Promise<ChatMessageResponse> => {
  const response = await api.post<ChatMessageResponse>(
    '/api/chat/message',
    request
  );
  return response.data;
};

export const getChatSessions = async (userId: string) => {
  const response = await api.get(`/api/chat/sessions/${userId}`);
  return response.data;
};

export const executeSQL = async (table: string, sql: string) => {
  const response = await api.post('/api/chat/sql/execute', null, {
    params: { table, sql },
  });
  return response.data;
};

// Data Edit API
export interface UpdateRowRequest {
  table_name: string;
  row_id: number;
  updates: Record<string, any>;
}

export interface InsertRowRequest {
  table_name: string;
  data: Record<string, any>;
}

export interface DeleteRowRequest {
  table_name: string;
  row_id: number;
}

export interface AIBatchEditRequest {
  table_name: string;
  instruction: string;
  user_id: string;
}

export interface DataEditResponse {
  success: boolean;
  message?: string;
  rows_affected?: number;
  sql_executed?: string;
  error?: string;
}

export const updateRow = async (request: UpdateRowRequest): Promise<DataEditResponse> => {
  const response = await api.post<DataEditResponse>('/api/data/update-row', request);
  return response.data;
};

export const insertRow = async (request: InsertRowRequest): Promise<DataEditResponse> => {
  const response = await api.post<DataEditResponse>('/api/data/insert-row', request);
  return response.data;
};

export const deleteRow = async (request: DeleteRowRequest): Promise<DataEditResponse> => {
  const response = await api.post<DataEditResponse>('/api/data/delete-row', request);
  return response.data;
};

export const aiBatchEdit = async (request: AIBatchEditRequest): Promise<DataEditResponse> => {
  const response = await api.post<DataEditResponse>('/api/data/ai-batch-edit', request);
  return response.data;
};

// Data Table API
export interface PaginatedDataParams {
  page?: number;
  page_size?: number;
  search?: string;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface PaginatedDataResponse {
  data: Array<Record<string, any>>;
  columns: string[];
  pagination: {
    page: number;
    page_size: number;
    total_rows: number;
    total_pages: number;
    has_next: boolean;
    has_previous: boolean;
  };
}

export interface TableColumnsResponse {
  columns: string[];
  column_types: Record<string, string>;
}

export const getTableData = async (
  tableName: string,
  params: PaginatedDataParams = {}
): Promise<PaginatedDataResponse> => {
  const response = await api.get<PaginatedDataResponse>(`/api/data/table/${tableName}`, {
    params,
  });
  return response.data;
};

export const getTableColumns = async (tableName: string): Promise<TableColumnsResponse> => {
  const response = await api.get<TableColumnsResponse>(`/api/data/table/${tableName}/columns`);
  return response.data;
};

