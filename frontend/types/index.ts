export type UIEventType =
  | "status"
  | "table_name"
  | "sql"
  | "results"
  | "token"
  | "chart_spec"
  | "cost_warning"
  | "done"
  | "error";

export interface UIEvent {
  type: UIEventType;
  message?: string;
  table?: string;
  display?: string;
  sql?: string;
  rows?: Record<string, unknown>[];
  row_count?: number;
  columns?: string[];
  text?: string;
  code?: string;
  bytes_scanned?: number;
  session_id?: string;
  query_id?: string;
  turn_id?: string;
  [key: string]: unknown;
}

export interface ChartSpec {
  chart_type?: "line" | "bar" | "pie" | string;
  x?: string;
  y?: string;
  title?: string;
  [key: string]: unknown;
}

export interface ChatSession {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ChatTurn {
  id: string;
  query_id: string;
  question: string;
  intent?: string | null;
  table_id?: string | null;
  sql?: string | null;
  answer?: string | null;
  row_count?: number;
  chart_spec?: ChartSpec | null;
  results_sample?: Record<string, unknown>[] | null;
  events?: UIEvent[] | null;
  starter_id?: string | null;
  category_id?: string | null;
  feedback_rating?: number | null;
  created_at: string;
}

export interface ChatSendMeta {
  starter_id?: string;
  category_id?: string;
}

export interface AppUser {
  id: string;
  email: string | null;
  display_name: string;
  sales_rep_code: string | null;
}

export interface ChatMessage {
  id: string;
  role: "user" | "agent";
  content: string;
  createdAt?: string;
  status?: string;
  tableDisplay?: string;
  sql?: string;
  rows?: Record<string, unknown>[];
  columns?: string[];
  rowCount?: number;
  chartSpec?: ChartSpec | null;
  costWarningBytes?: number;
  queryId?: string;
  question?: string;
  turnId?: string;
  starterId?: string;
  categoryId?: string;
  feedbackRating?: number | null;
  streaming?: boolean;
  error?: string;
}
