export type DataAvailability =
  | "full"
  | "full_with_config_target"
  | "partial_run_rate"
  | "partial_pattern"
  | "requires_rep_context"
  | "not_in_bq_forecast"
  | "partial"
  | "requires_target_table"
  | "target_not_in_bq";

export interface QuestionCategory {
  id: string;
  label: string;
  description: string;
  icon: string;
  order: number;
  starter_count?: number;
  requires_rep_code?: boolean;
}

export interface StarterQuestion {
  id: string;
  category_id: string;
  text: string;
  data_availability: DataAvailability;
  intent: string;
  expected_table_id?: string | null;
  join_pattern?: string | null;
  source?: string | null;
}

export interface FollowUpQuestion {
  id: string;
  text: string;
  data_availability?: DataAvailability;
  intent?: string | null;
}

export interface FollowUpsResponse {
  follow_ups: FollowUpQuestion[];
  source: string;
}
