export interface SalesPerformance {
  current_fy: string;
  prior_fy: string;
  current_sales: number;
  prior_sales: number;
  yoy_pct: number;
}

export interface GrossProfitSummary {
  current_gp: number;
  prior_gp: number;
  current_gp_pct: number;
  prior_gp_pct: number;
  gp_variance_dollars: number;
}

export interface MonthlyOnTrack {
  daily_avg_mtd: number;
  days_completed: number;
  daily_avg_needed: number;
  days_remaining: number;
  monthly_target: number;
  closed_mtd: number;
  closed_mtd_pct: number;
  projected_close: number;
  projected_pct: number;
}

export interface YesterdaySales {
  sales: number;
  gp_dollar: number;
  gp_pct: number;
  fy_avg_gp_pct: number;
  sales_status: string;
  gp_status: string;
}

export interface DailyBusinessSummary {
  as_of_date: string;
  yesterday_date: string;
  disclaimer: string;
  sales_performance: SalesPerformance;
  gross_profit: GrossProfitSummary;
  monthly_on_track: MonthlyOnTrack;
  yesterday: YesterdaySales;
}
