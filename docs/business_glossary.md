# Jaybel Sales Analytics — Business Glossary

Derived from `Jaybel_Sales_Analytics_Detailed_Schema.pdf` and star-schema design. Used by L1 routing and answer generation.

**Column aliases** for SQL generation (NL → registry column names) live in `config/column_aliases.yaml` — edit that file when the model hallucinates column names; redeploy once and re-run the SQL regression suite.

## Companies & departments

| Term | Meaning | Data location |
|------|---------|---------------|
| **Jaybel** | Primary operating company / department | `dim_department.department_name = 'Jaybel'`, `department_key = 1`; also `company` on facts/staging |
| **Frazer** | Sister company / department; new-business focus | `dim_department.department_name = 'Frazer'`, `department_key = 2` |
| **Department** | Legal entity split for reporting | `dim_department` (2 rows only) |

## Time & fiscal calendar

| Term | Meaning | Data location |
|------|---------|---------------|
| **Fiscal year (FY)** | July → June; label **2025-2026** (not FY2026) | `dim_date.fy`, `stg_*.fiscal_year` |
| **Fiscal month** | July = month 1, June = month 12 | `dim_date.fiscal_month_no`, `fiscal_month_name` |
| **Fiscal quarter** | Q1 Jul–Sep, Q2 Oct–Dec, Q3 Jan–Mar, Q4 Apr–Jun | `dim_date.fiscal_quarter` |
| **Calendar year / quarter** | Standard Jan–Dec calendar | `dim_date.calendar_year`, `calendar_quarter` |
| **Last month** | Previous **calendar** month in **`Australia/Sydney`** (confirmed) | `dim_date.date` between computed start/end |
| **This quarter** (default) | Current **calendar** quarter in Sydney time | `dim_date.calendar_quarter` + `calendar_year` |
| **Last fiscal month / fiscal quarter** | Only when user says **fiscal** | `dim_date.fiscal_month_no` / `fiscal_quarter` + `fy` |
| **Working days** | Business days available per fiscal month | **`stg_total_working_days`** only (not joined to facts) |
| **Completed days** | Working days elapsed in period | `stg_total_working_days.Completed_days` |

## Sales & revenue metrics

| Term | Meaning | Column(s) | Preferred table |
|------|---------|-----------|-----------------|
| **Sales / revenue** | Line revenue excluding GST | `line_sales_ex_gst` | `fact_sales_report` |
| **Bookings** | *(User synonym)* → treat as **confirmed line sales** unless defined otherwise | `line_sales_ex_gst` | `fact_sales_report` |
| **Cost** | Line cost | `line_cost` | `fact_sales_report` |
| **GP / gross profit** | Line GP dollars | `line_gp_dollar` | `fact_sales_report` or `fact_new_business_frazer` |
| **Margin / GP %** | Gross profit percent | `gp_percent` | `fact_sales_report` |
| **Quantity / units** | Units sold on line | `qty` | `fact_sales_report` |
| **Unit price** | Unit sell ex GST | `unit_sale_ex_gst` | `fact_sales_report` |
| **Unit cost** | Unit cost | `unit_cost` | `fact_sales_report` |
| **Invoice / order** | Document identifiers | `invoice`, `order_no` | `fact_sales_report` |
| **Line item** | One product line on an invoice | grain of `fact_sales_report` | `fact_sales_report` |

## New business (Frazer)

| Term | Meaning | Preferred table |
|------|---------|-----------------|
| **New business** | Frazer pipeline transactions (separate from main sales fact) | `fact_new_business_frazer` |
| **New business sales** | Revenue on new-business lines | `fact_new_business_frazer.line_sales_ex_gst` |
| **Frazer link** | External Frazer system identifier | `fact_new_business_frazer.frazer_link`, `dim_sales_rep.frazer_link` |

## Customers & accounts

| Term | Meaning | Preferred table |
|------|---------|-----------------|
| **Customer / account** | B2B customer | `dim_sales_customer`; join via `customer_key` |
| **Account code** | Natural key | `dim_sales_customer.account` |
| **New account** | Flag for new customer | `dim_sales_customer.is_new_account` |
| **New in fiscal cycle** | New within current FY cycle | `dim_sales_customer.is_new_created_date_cycle` |
| **Industry / business type** | Segmentation | `industry_sub`, `business_code` |

## Sales organization

| Term | Meaning | Preferred table |
|------|---------|-----------------|
| **Rep / salesperson** | Sales representative | `dim_sales_rep`; join via `rep_key` |
| **Rep code** | Short code on transactions | `dim_sales_rep.sales_rep_code` |
| **Original rep** | Rep at time of sale | `fact_sales_report.orgn_rep` |
| **Territory** | Sales territory | `fact_sales_report.territory_code` or `fact_new_business_frazer.territory` |
| **Warehouse** | Warehouse code | `fact_sales_report.whse` |
| **Market segment** | Market code | `fact_sales_report.mkt` |

## Products

| Term | Meaning | Preferred table |
|------|---------|-----------------|
| **Product name** | Human-readable product on invoice line | `fact_sales_report.description` (join `dim_product` for group) |
| **Product group / category** | Main product group (Office Supplies, Furniture, …) | `dim_product.main_group_name` |
| **Item / SKU** | Product item on line | `fact_sales_report.item_code` |
| **Brand / manufacturer** | In raw staging only | `stg_sales_report.brand_manuf` |

## Data layers (routing hints)

| Term | Meaning | Agent behavior |
|------|---------|----------------|
| **Analytics / KPI / trend** | Typed measures | Route to **`fact_*`** + join **`dim_*`** |
| **Customer list / rep list** | Dimension-only questions | Route to relevant **`dim_*`** |
| **Working days** | Capacity calendar | Route to **`stg_total_working_days`** |
| **Raw / source / untyped** | STRING staging imports | Route to **`stg_*`** only when user asks for raw/source |

## Office Supplies BI report (client terminology)

From `Office_Supplies_BI_Analytics_Questions.pdf`. Full list: `docs/office_supplies_client_questions.md`.

| Term | Meaning | BigQuery mapping / notes |
|------|---------|---------------------------|
| **Sales** | Revenue ex GST | `fact_sales_report.line_sales_ex_gst` |
| **GP$ / Gross Profit** | Line GP dollars | `line_gp_dollar` |
| **GP% / margin** | Gross profit % | `gp_percent` (line-level; use AVG or weighted logic as appropriate) |
| **Office Supplies, Furniture, Ink & Toner, Kitchen & Janitorial, Apparel** | Product **categories** in the BI report | `dim_product.main_group_name` — verify exact spelling in data |
| **Best-selling / top products** | By product name | `GROUP BY fact_sales_report.description`, include `main_group_name` in results |
| **Best product group / category** | By category only | `GROUP BY dim_product.main_group_name` |
| **SKU / item code** | Product code | `fact_sales_report.item_code` |
| **Financial year 2025-2026 / FY 24-25** | Fiscal year labels | `dim_date.fy` = `'2025-2026'`, `'2024-2025'` |
| **Yesterday / this month** | Relative dates | Resolve in **`Australia/Sydney`** (calendar month/day) |
| **This year / last year / YTD** | Relative dates | **Fiscal year** (Jul–Jun, `dim_date.fy`) unless user says **calendar year** |
| **Daily average sales** | MTD sales ÷ elapsed days (or working days) | Aggregate facts + date filter; working days from `stg_total_working_days` if needed |
| **Top customers** | By total sales | `fact_sales_report` + `dim_sales_customer`; `ORDER BY SUM(line_sales_ex_gst) DESC` |
| **No order since 2022** | Inactive accounts | Customers with no `fact_sales_report` rows after 2022-12-31 (anti-join or `MAX(d.date)` filter) |
| **Brisbane City Council, Lizard Island Resort, Best Doors Rockhampton** | Named accounts | `dim_sales_customer.account_name` |
| **99 BIKES** | Franchise account family | `account_name LIKE '%99 BIKES%'` (confirm pattern in data) |
| **Closed / \*\*\* ACCOUNT CLOSED \*\*\*** | Closed account indicator | Likely embedded in `account_name` or account status in source; **not a dedicated column in current dim** — search `account_name` patterns |
| **Previous Month vs Current Month Sales** | MoM retention | Two-period aggregation per `customer_key` on `fact_sales_report` + `dim_date` |
| **Item code HCL-S901S** | SKU / product line | `fact_sales_report.item_code` |
| **Embroidery / custom printing** | Job type | Filter `item_code`, `description` (staging), or product group — confirm with business which field encodes job type |
| **My / our sales / GP / accounts** | Company-wide | No rep filter; "my" is treated as "our" |
| **My commission / payout / closed deals** | Rep-scoped | Filter by `dim_sales_rep.sales_rep_code` (sidebar Settings) |
| **Overall Business Target ($6M / $6,067,292.04)** | FY sales goal from BI | **v1.2:** `config/sales_targets.yaml` — compare `SUM(line_sales_ex_gst)` actuals to literal target in SQL |
| **Furniture GP Target ($387K / $387,173.20)** | Category GP goal | **v1.2:** config target `387173.20` vs `SUM(line_gp_dollar)` where `main_group_name = 'Furniture'` |
| **BTS Target ($613,099.84)** | Category/segment goal | **v1.2:** config target amount; `category_main_group` TBD — filter pending business confirmation |
| **Projected Monthly Sales / Projected GP$** | Forecast from BI model | **Run-rate estimate (v1.2):** `(MTD / Completed_days) × total_working_days` — **not** exact Power BI forecast |
| **BI Furniture projected variance (-$1,695,009.72)** | Power BI forecast only | **not_in_bq_forecast** — explain BI model; offer actuals + config target |
| **Sales Month To Date (MTD)** | Month-to-date sales | `fact_sales_report` + `dim_date` current calendar month (Sydney) |
| **Completed working days** | Days elapsed in month | `stg_total_working_days.Completed_days` |
| **Closed deals / closed-won / payout** | Commission proxy | Map to closed invoices or rep-attributed `line_sales_ex_gst` / `line_gp_dollar` for period; define “closed” with business if unclear |

## Common question → primary table

| Question pattern | Primary `table_id` | Join pattern |
|------------------|-------------------|--------------|
| Revenue, GP, qty, invoices, trends by time/rep/product/customer | `fact_sales_report` | `fact_sales_with_dims` |
| New business, Frazer pipeline | `fact_new_business_frazer` | `fact_new_business_frazer_with_dims` |
| FY labels, fiscal months, quarters | `dim_date` | single table |
| Jaybel vs Frazer entity list | `dim_department` | single table |
| Customer attributes without measures | `dim_sales_customer` | single table |
| Rep roster | `dim_sales_rep` | single table |
| Product group list | `dim_product` | single table |
| Working days per month | `stg_total_working_days` | single table |
