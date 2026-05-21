# Schema registry (Jaybel)

Single source of truth for NL-to-SQL routing and validation.

## Layout

- `tables/*.yaml` — one file per BigQuery table (13 tables)
- `join_allowlist.yaml` — approved `fact_*` + `dim_*` join patterns
- Regenerate table YAMLs: `python scripts/generate_schema_registry.py` (after editing script data)

## Table inventory

| File | Layer | Agent default |
|------|-------|---------------|
| `fact_sales_report.yaml` | fact | yes (primary) |
| `fact_new_business_frazer.yaml` | fact | yes (primary) |
| `dim_date.yaml` | dimension | yes |
| `dim_department.yaml` | dimension | yes |
| `dim_sales_customer.yaml` | dimension | yes |
| `dim_sales_rep.yaml` | dimension | yes |
| `dim_product.yaml` | dimension | yes |
| `stg_total_working_days.yaml` | staging | yes (special reference) |
| `stg_sales_report.yaml` | staging | no (raw) |
| `stg_sales_cust.yaml` | staging | no |
| `stg_sales_rep.yaml` | staging | no |
| `stg_main_product.yaml` | staging | no |
| `stg_new_busin_frazer.yaml` | staging | no |

Fully qualified prefix: `jaybel-dev.jaybel_sales_analytics.<table_name>`
