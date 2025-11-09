export interface Message {
  role: 'user' | 'assistant';
  content: string;
  data?: {
    rows: Array<Record<string, any>>;
    columns: string[];
    sql_query?: string;
  };
  visualization?: VisualizationConfig;
  timestamp: Date;
}

export interface VisualizationConfig {
  type: 'bar_chart' | 'line_chart' | 'kpi' | 'table';
  show_bar_chart: boolean;
  input_data?: Array<Record<string, any>>;
}

export interface FileInfo {
  file_id: string;
  filename: string;
  file_type: string;
  row_count: number;
  created_at: string;
}

