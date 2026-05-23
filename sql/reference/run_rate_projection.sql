-- Reference: run-rate monthly projection (v1.2 — NOT Power BI forecast)
-- Timezone: Australia/Sydney calendar month for MTD facts
-- Working days: stg_total_working_days month = 'Current'

-- Projected month sales
WITH mtd AS (
  SELECT SUM(f.line_sales_ex_gst) AS mtd_sales
  FROM `jaybel-dev.jaybel_sales_analytics.fact_sales_report` AS f
  JOIN `jaybel-dev.jaybel_sales_analytics.dim_date` AS d ON f.date_key = d.date_key
  WHERE d.date >= DATE_TRUNC(CURRENT_DATE('Australia/Sydney'), MONTH)
    AND d.date <= CURRENT_DATE('Australia/Sydney')
),
wd AS (
  SELECT
    CAST(Completed_days AS INT64) AS completed_days,
    CAST(total_working_days AS INT64) AS total_working_days
  FROM `jaybel-dev.jaybel_sales_analytics.stg_total_working_days`
  WHERE fiscal_year = '2025-2026' AND month = 'Current'
  LIMIT 1
)
SELECT
  mtd.mtd_sales,
  wd.completed_days,
  wd.total_working_days,
  SAFE_DIVIDE(mtd.mtd_sales, wd.completed_days) * wd.total_working_days AS projected_month_sales
FROM mtd, wd
LIMIT 1000;
