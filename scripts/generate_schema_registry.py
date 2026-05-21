#!/usr/bin/env python3
"""Generate schema_registry/tables/*.yaml from Jaybel PDF schema (one-time bootstrap)."""
from __future__ import annotations

import textwrap
from pathlib import Path

import yaml

PROJECT = "jaybel-dev"
DATASET = "jaybel_sales_analytics"
FQ = f"{PROJECT}.{DATASET}"
OUT = Path(__file__).resolve().parents[1] / "schema_registry" / "tables"


def tid(name: str) -> str:
    return f"{FQ}.{name}"


def col(name: str, typ: str, desc: str, samples=None, nullable=True):
    c = {"name": name, "type": typ, "description": desc, "nullable": nullable}
    if samples:
        c["sample_values"] = samples
    return c


TABLES: dict[str, dict] = {
    "fact_sales_report": {
        "layer": "fact",
        "agent_default": True,
        "routing_priority": "primary",
        "display_name": "Sales Report (Fact)",
        "description": (
            "Primary transactional fact table. One row per invoice line item with typed revenue, "
            "cost, and GP measures. Join to dim_* tables for calendar, customer, rep, product, and department."
        ),
        "business_tags": [
            "sales", "revenue", "invoice", "orders", "gp", "gross profit", "margin",
            "quantity", "line items", "transactions", "Jaybel", "Frazer", "warehouse", "territory",
        ],
        "grain": "One row represents one invoice line item (product line on an invoice).",
        "columns": [
            col("sales_key", "INT64", "Surrogate primary key"),
            col("date_key", "INT64", "FK to dim_date (YYYYMMDD surrogate)"),
            col("customer_key", "INT64", "FK to dim_sales_customer"),
            col("rep_key", "INT64", "FK to dim_sales_rep"),
            col("product_key", "INT64", "FK to dim_product"),
            col("department_key", "INT64", "FK to dim_department (1=Jaybel, 2=Frazer)"),
            col("invoice", "STRING", "Invoice number"),
            col("order_no", "STRING", "Order number"),
            col("item_code", "STRING", "Product item code"),
            col("whse", "STRING", "Warehouse code"),
            col("territory_code", "STRING", "Territory code"),
            col("orgn_rep", "STRING", "Original rep code at time of sale"),
            col("mkt", "STRING", "Market segment code"),
            col("file_id", "STRING", "Source file ID for traceability"),
            col("qty", "FLOAT64", "Quantity sold"),
            col("line_sales_ex_gst", "FLOAT64", "Line revenue excluding GST"),
            col("line_cost", "FLOAT64", "Line total cost"),
            col("line_gp_dollar", "FLOAT64", "Line gross profit dollars"),
            col("gp_percent", "FLOAT64", "Gross profit percent"),
            col("unit_sale_ex_gst", "FLOAT64", "Unit selling price ex GST"),
            col("unit_cost", "FLOAT64", "Unit cost"),
            col("unit_gp_dollar", "FLOAT64", "Unit GP dollars"),
        ],
        "relationships": [
            {"column": "date_key", "references": f"{tid('dim_date')}.date_key"},
            {"column": "customer_key", "references": f"{tid('dim_sales_customer')}.customer_key"},
            {"column": "rep_key", "references": f"{tid('dim_sales_rep')}.rep_key"},
            {"column": "product_key", "references": f"{tid('dim_product')}.product_key"},
            {"column": "department_key", "references": f"{tid('dim_department')}.department_key"},
        ],
        "common_filters": ["date_key", "department_key", "rep_key", "customer_key", "product_key", "territory_code", "whse"],
        "common_aggregations": [
            ["line_sales_ex_gst", "SUM"],
            ["line_gp_dollar", "SUM"],
            ["line_cost", "SUM"],
            ["qty", "SUM"],
            ["gp_percent", "AVG"],
            ["sales_key", "COUNT"],
        ],
        "time_columns": ["date_key"],
        "few_shot": [
            (
                "What was total sales excluding GST in fiscal year 2025-2026 for Jaybel?",
                f"""SELECT SUM(f.line_sales_ex_gst) AS total_sales_ex_gst
FROM `{tid('fact_sales_report')}` AS f
JOIN `{tid('dim_date')}` AS d ON f.date_key = d.date_key
JOIN `{tid('dim_department')}` AS dept ON f.department_key = dept.department_key
WHERE d.fy = '2025-2026' AND dept.department_name = 'Jaybel'
LIMIT 1000""",
            ),
            (
                "Show monthly sales trend for fiscal year 2024-2025",
                f"""SELECT d.fiscal_month_name, d.fiscal_month_no, SUM(f.line_sales_ex_gst) AS total_sales
FROM `{tid('fact_sales_report')}` AS f
JOIN `{tid('dim_date')}` AS d ON f.date_key = d.date_key
WHERE d.fy = '2024-2025'
GROUP BY d.fiscal_month_name, d.fiscal_month_no
ORDER BY d.fiscal_month_no
LIMIT 1000""",
            ),
            (
                "Top 10 customers by gross profit last fiscal quarter",
                f"""SELECT c.account_name, SUM(f.line_gp_dollar) AS total_gp
FROM `{tid('fact_sales_report')}` AS f
JOIN `{tid('dim_date')}` AS d ON f.date_key = d.date_key
JOIN `{tid('dim_sales_customer')}` AS c ON f.customer_key = c.customer_key
WHERE d.fy = '2025-2026' AND d.fiscal_quarter = 'Q2'
GROUP BY c.account_name
ORDER BY total_gp DESC
LIMIT 10""",
            ),
            (
                "Compare Jaybel vs Frazer total revenue this fiscal year",
                f"""SELECT dept.department_name, SUM(f.line_sales_ex_gst) AS total_sales
FROM `{tid('fact_sales_report')}` AS f
JOIN `{tid('dim_date')}` AS d ON f.date_key = d.date_key
JOIN `{tid('dim_department')}` AS dept ON f.department_key = dept.department_key
WHERE d.fy = '2025-2026'
GROUP BY dept.department_name
LIMIT 1000""",
            ),
            (
                "Sales by product main group for rep code ABC",
                f"""SELECT p.main_group_name, SUM(f.line_sales_ex_gst) AS sales
FROM `{tid('fact_sales_report')}` AS f
JOIN `{tid('dim_sales_rep')}` AS r ON f.rep_key = r.rep_key
JOIN `{tid('dim_product')}` AS p ON f.product_key = p.product_key
WHERE r.sales_rep_code = 'ABC'
GROUP BY p.main_group_name
ORDER BY sales DESC
LIMIT 1000""",
            ),
            (
                "Average GP percent by territory code in calendar year 2025",
                f"""SELECT f.territory_code, AVG(f.gp_percent) AS avg_gp_pct
FROM `{tid('fact_sales_report')}` AS f
JOIN `{tid('dim_date')}` AS d ON f.date_key = d.date_key
WHERE d.calendar_year = 2025
GROUP BY f.territory_code
LIMIT 1000""",
            ),
            (
                "How many invoice line items were sold in July 2025?",
                f"""SELECT COUNT(*) AS line_count
FROM `{tid('fact_sales_report')}` AS f
JOIN `{tid('dim_date')}` AS d ON f.date_key = d.date_key
WHERE d.date BETWEEN '2025-07-01' AND '2025-07-31'
LIMIT 1000""",
            ),
            (
                "List invoices with line sales over 10000 ex GST in Q1 fiscal 2025-2026",
                f"""SELECT f.invoice, f.order_no, f.line_sales_ex_gst, d.date
FROM `{tid('fact_sales_report')}` AS f
JOIN `{tid('dim_date')}` AS d ON f.date_key = d.date_key
WHERE d.fy = '2025-2026' AND d.fiscal_quarter = 'Q1' AND f.line_sales_ex_gst > 10000
ORDER BY f.line_sales_ex_gst DESC
LIMIT 1000""",
            ),
        ],
    },
    "fact_new_business": {
        "layer": "fact",
        "agent_default": True,
        "routing_priority": "primary",
        "display_name": "New Business (Fact)",
        "description": (
            "Frazer new-business transactions kept separate from main sales. "
            "Shares dimension keys with fact_sales_report. Use for new business / Frazer pipeline metrics."
        ),
        "business_tags": ["new business", "Frazer", "new accounts", "pipeline", "territory", "frazer link"],
        "grain": "One row represents one new-business transaction line for Frazer.",
        "columns": [
            col("new_business_key", "INT64", "Surrogate primary key"),
            col("date_key", "INT64", "FK to dim_date"),
            col("customer_key", "INT64", "FK to dim_sales_customer"),
            col("rep_key", "INT64", "FK to dim_sales_rep"),
            col("product_key", "INT64", "FK to dim_product"),
            col("department_key", "INT64", "FK to dim_department"),
            col("territory", "STRING", "Territory name"),
            col("frazer_link", "STRING", "Frazer system link identifier"),
            col("line_sales_ex_gst", "FLOAT64", "Line sales ex GST"),
            col("line_gp_dollar", "FLOAT64", "Line gross profit dollars"),
        ],
        "relationships": [
            {"column": "date_key", "references": f"{tid('dim_date')}.date_key"},
            {"column": "customer_key", "references": f"{tid('dim_sales_customer')}.customer_key"},
            {"column": "rep_key", "references": f"{tid('dim_sales_rep')}.rep_key"},
            {"column": "product_key", "references": f"{tid('dim_product')}.product_key"},
            {"column": "department_key", "references": f"{tid('dim_department')}.department_key"},
        ],
        "common_filters": ["date_key", "territory", "department_key", "rep_key"],
        "common_aggregations": [
            ["line_sales_ex_gst", "SUM"],
            ["line_gp_dollar", "SUM"],
            ["new_business_key", "COUNT"],
        ],
        "time_columns": ["date_key"],
        "few_shot": [
            (
                "Total new business sales for Frazer in fiscal 2025-2026",
                f"""SELECT SUM(f.line_sales_ex_gst) AS total_new_business_sales
FROM `{tid('fact_new_business')}` AS f
JOIN `{tid('dim_date')}` AS d ON f.date_key = d.date_key
JOIN `{tid('dim_department')}` AS dept ON f.department_key = dept.department_key
WHERE d.fy = '2025-2026' AND dept.department_name = 'Frazer'
LIMIT 1000""",
            ),
            (
                "New business GP by territory this fiscal year",
                f"""SELECT f.territory, SUM(f.line_gp_dollar) AS total_gp
FROM `{tid('fact_new_business')}` AS f
JOIN `{tid('dim_date')}` AS d ON f.date_key = d.date_key
WHERE d.fy = '2025-2026'
GROUP BY f.territory
ORDER BY total_gp DESC
LIMIT 1000""",
            ),
            (
                "Count of new business rows in Q3 fiscal 2024-2025",
                f"""SELECT COUNT(*) AS row_count
FROM `{tid('fact_new_business')}` AS f
JOIN `{tid('dim_date')}` AS d ON f.date_key = d.date_key
WHERE d.fy = '2024-2025' AND d.fiscal_quarter = 'Q3'
LIMIT 1000""",
            ),
            (
                "New business by sales rep for fiscal 2025-2026",
                f"""SELECT r.description AS rep_name, SUM(f.line_sales_ex_gst) AS sales
FROM `{tid('fact_new_business')}` AS f
JOIN `{tid('dim_date')}` AS d ON f.date_key = d.date_key
JOIN `{tid('dim_sales_rep')}` AS r ON f.rep_key = r.rep_key
WHERE d.fy = '2025-2026'
GROUP BY r.description
ORDER BY sales DESC
LIMIT 1000""",
            ),
            (
                "Monthly new business revenue trend FY 2025-2026",
                f"""SELECT d.fiscal_month_no, d.fiscal_month_name, SUM(f.line_sales_ex_gst) AS sales
FROM `{tid('fact_new_business')}` AS f
JOIN `{tid('dim_date')}` AS d ON f.date_key = d.date_key
WHERE d.fy = '2025-2026'
GROUP BY d.fiscal_month_no, d.fiscal_month_name
ORDER BY d.fiscal_month_no
LIMIT 1000""",
            ),
            (
                "Top 5 customers by new business GP",
                f"""SELECT c.account_name, SUM(f.line_gp_dollar) AS gp
FROM `{tid('fact_new_business')}` AS f
JOIN `{tid('dim_sales_customer')}` AS c ON f.customer_key = c.customer_key
GROUP BY c.account_name
ORDER BY gp DESC
LIMIT 5""",
            ),
            (
                "New business sales by product group fiscal Q4 2025-2026",
                f"""SELECT p.main_group_name, SUM(f.line_sales_ex_gst) AS sales
FROM `{tid('fact_new_business')}` AS f
JOIN `{tid('dim_date')}` AS d ON f.date_key = d.date_key
JOIN `{tid('dim_product')}` AS p ON f.product_key = p.product_key
WHERE d.fy = '2025-2026' AND d.fiscal_quarter = 'Q4'
GROUP BY p.main_group_name
LIMIT 1000""",
            ),
            (
                "Average line GP for new business in territory NSW",
                f"""SELECT AVG(f.line_gp_dollar) AS avg_line_gp
FROM `{tid('fact_new_business')}` AS f
WHERE f.territory = 'NSW'
LIMIT 1000""",
            ),
        ],
    },
    "dim_date": {
        "layer": "dimension",
        "agent_default": True,
        "routing_priority": "secondary",
        "display_name": "Date (Dimension)",
        "description": "Calendar and fiscal date dimension. July=fiscal month 1, June=12. FY label format 2025-2026.",
        "business_tags": ["date", "fiscal", "calendar", "month", "quarter", "FY", "weekday"],
        "grain": "One row per calendar date from 2018-07-01 through 2030-06-30.",
        "columns": [
            col("date_key", "INT64", "Surrogate PK YYYYMMDD"),
            col("date", "DATE", "Calendar date"),
            col("day_name", "STRING", "Full weekday name"),
            col("day_name_short", "STRING", "Short weekday name"),
            col("day_of_month", "INT64", "Day of month 1-31"),
            col("calendar_month_no", "INT64", "Calendar month 1-12"),
            col("calendar_month_name", "STRING", "Calendar month name"),
            col("calendar_year", "INT64", "Calendar year"),
            col("calendar_quarter", "INT64", "Calendar quarter 1-4"),
            col("fiscal_month_no", "INT64", "Fiscal month (July=1)"),
            col("fiscal_month_name", "STRING", "Fiscal month name"),
            col("fiscal_year", "INT64", "Fiscal year integer"),
            col("fy", "STRING", "Fiscal year label e.g. 2025-2026", ["2024-2025", "2025-2026"]),
            col("fiscal_quarter", "STRING", "Q1=Jul-Sep, Q2=Oct-Dec, Q3=Jan-Mar, Q4=Apr-Jun", ["Q1", "Q2", "Q3", "Q4"]),
            col("is_weekday", "BOOL", "True Mon-Fri"),
        ],
        "relationships": [],
        "common_filters": ["fy", "fiscal_quarter", "fiscal_month_no", "calendar_year", "date", "is_weekday"],
        "common_aggregations": [],
        "time_columns": ["date"],
        "few_shot": [
            ("How many fiscal months are in FY 2025-2026?", f"SELECT COUNT(DISTINCT fiscal_month_no) AS months FROM `{tid('dim_date')}` WHERE fy = '2025-2026' LIMIT 1000"),
            ("List fiscal quarters and their month ranges for 2025-2026", f"SELECT DISTINCT fiscal_quarter, MIN(fiscal_month_name) AS start_month, MAX(fiscal_month_name) AS end_month FROM `{tid('dim_date')}` WHERE fy = '2025-2026' GROUP BY fiscal_quarter LIMIT 1000"),
            ("Count weekdays in July 2025", f"SELECT COUNT(*) AS weekdays FROM `{tid('dim_date')}` WHERE date BETWEEN '2025-07-01' AND '2025-07-31' AND is_weekday = TRUE LIMIT 1000"),
            ("What is fiscal month number for December 2025?", f"SELECT fiscal_month_no, fiscal_month_name FROM `{tid('dim_date')}` WHERE date = '2025-12-01' LIMIT 1000"),
            ("Distinct fiscal years in the date dimension", f"SELECT DISTINCT fy FROM `{tid('dim_date')}` ORDER BY fy LIMIT 1000"),
            ("Calendar Q2 2025 date range", f"SELECT MIN(date) AS start_date, MAX(date) AS end_date FROM `{tid('dim_date')}` WHERE calendar_year = 2025 AND calendar_quarter = 2 LIMIT 1000"),
            ("Fiscal Q1 2024-2025 start and end dates", f"SELECT MIN(date) AS start_date, MAX(date) AS end_date FROM `{tid('dim_date')}` WHERE fy = '2024-2025' AND fiscal_quarter = 'Q1' LIMIT 1000"),
            ("How many days in fiscal year 2025-2026?", f"SELECT COUNT(*) AS days FROM `{tid('dim_date')}` WHERE fy = '2025-2026' LIMIT 1000"),
        ],
    },
    "dim_department": {
        "layer": "dimension",
        "agent_default": True,
        "routing_priority": "secondary",
        "display_name": "Department (Dimension)",
        "description": "Two departments only: Jaybel (key=1) and Frazer (key=2).",
        "business_tags": ["department", "company", "Jaybel", "Frazer", "division"],
        "grain": "One row per department (2 rows total).",
        "columns": [
            col("department_key", "INT64", "PK: 1=Jaybel, 2=Frazer", [1, 2]),
            col("department_name", "STRING", "Department name", ["Jaybel", "Frazer"]),
        ],
        "relationships": [],
        "common_filters": ["department_name", "department_key"],
        "common_aggregations": [],
        "time_columns": [],
        "few_shot": [
            ("List all departments", f"SELECT department_key, department_name FROM `{tid('dim_department')}` LIMIT 1000"),
            ("What is the department key for Frazer?", f"SELECT department_key FROM `{tid('dim_department')}` WHERE department_name = 'Frazer' LIMIT 1000"),
            ("Department key for Jaybel", f"SELECT department_key FROM `{tid('dim_department')}` WHERE department_name = 'Jaybel' LIMIT 1000"),
            ("Count departments", f"SELECT COUNT(*) AS dept_count FROM `{tid('dim_department')}` LIMIT 1000"),
            ("Is Frazer a valid department?", f"SELECT department_name FROM `{tid('dim_department')}` WHERE LOWER(department_name) = 'frazer' LIMIT 1000"),
            ("Department names alphabetically", f"SELECT department_name FROM `{tid('dim_department')}` ORDER BY department_name LIMIT 1000"),
            ("Map department keys to names", f"SELECT department_key, department_name FROM `{tid('dim_department')}` ORDER BY department_key LIMIT 1000"),
            ("Which department has key 1?", f"SELECT department_name FROM `{tid('dim_department')}` WHERE department_key = 1 LIMIT 1000"),
        ],
    },
    "dim_sales_customer": {
        "layer": "dimension",
        "agent_default": True,
        "routing_priority": "secondary",
        "display_name": "Sales Customer (Dimension)",
        "description": "Customer accounts with account codes, industry, and new-account flags.",
        "business_tags": ["customer", "account", "industry", "new account", "business code"],
        "grain": "One row per unique customer account.",
        "columns": [
            col("customer_key", "INT64", "Surrogate PK"),
            col("account", "STRING", "Customer account code (natural key)"),
            col("account_name", "STRING", "Customer account name"),
            col("created_date", "DATE", "Account created date"),
            col("first_created_date", "DATE", "First transaction date"),
            col("rep", "STRING", "Assigned sales rep code"),
            col("is_new_account", "BOOL", "New account in current period"),
            col("is_new_created_date_cycle", "BOOL", "New in current fiscal cycle"),
            col("industry_sub", "STRING", "Industry sub-classification"),
            col("business_code", "STRING", "Business type code"),
        ],
        "relationships": [{"column": "rep", "references": f"{tid('dim_sales_rep')}.sales_rep_code"}],
        "common_filters": ["account", "account_name", "industry_sub", "business_code", "is_new_account"],
        "common_aggregations": [["customer_key", "COUNT"]],
        "time_columns": ["created_date", "first_created_date"],
        "few_shot": [
            ("How many customer accounts are flagged as new?", f"SELECT COUNT(*) AS new_customers FROM `{tid('dim_sales_customer')}` WHERE is_new_account = TRUE LIMIT 1000"),
            ("List customers in industry sub Retail", f"SELECT account, account_name FROM `{tid('dim_sales_customer')}` WHERE industry_sub = 'Retail' LIMIT 1000"),
            ("Customers created in 2025", f"SELECT account_name, created_date FROM `{tid('dim_sales_customer')}` WHERE created_date >= '2025-01-01' ORDER BY created_date LIMIT 1000"),
            ("Count distinct business codes", f"SELECT COUNT(DISTINCT business_code) AS codes FROM `{tid('dim_sales_customer')}` LIMIT 1000"),
            ("New accounts in current fiscal cycle", f"SELECT account_name FROM `{tid('dim_sales_customer')}` WHERE is_new_created_date_cycle = TRUE LIMIT 1000"),
            ("Top 20 customers by account name", f"SELECT account, account_name FROM `{tid('dim_sales_customer')}` ORDER BY account_name LIMIT 20"),
            ("Customers assigned to rep code X01", f"SELECT account_name FROM `{tid('dim_sales_customer')}` WHERE rep = 'X01' LIMIT 1000"),
            ("Accounts with missing industry sub", f"SELECT account_name FROM `{tid('dim_sales_customer')}` WHERE industry_sub IS NULL LIMIT 1000"),
        ],
    },
    "dim_sales_rep": {
        "layer": "dimension",
        "agent_default": True,
        "routing_priority": "secondary",
        "display_name": "Sales Rep (Dimension)",
        "description": "Sales representatives with codes, names, company, and department FK.",
        "business_tags": ["sales rep", "rep", "representative", "salesperson", "frazer link"],
        "grain": "One row per sales representative.",
        "columns": [
            col("rep_key", "INT64", "Surrogate PK"),
            col("sales_rep_id", "STRING", "Source system rep ID"),
            col("sales_rep_code", "STRING", "Short rep code used in facts"),
            col("description", "STRING", "Rep full name"),
            col("frazer_link", "STRING", "Frazer link identifier"),
            col("company", "STRING", "Company rep belongs to", ["Jaybel", "Frazer"]),
            col("department_key", "INT64", "FK to dim_department"),
        ],
        "relationships": [{"column": "department_key", "references": f"{tid('dim_department')}.department_key"}],
        "common_filters": ["sales_rep_code", "company", "department_key"],
        "common_aggregations": [["rep_key", "COUNT"]],
        "time_columns": [],
        "few_shot": [
            ("List all Jaybel sales reps", f"SELECT sales_rep_code, description FROM `{tid('dim_sales_rep')}` WHERE company = 'Jaybel' LIMIT 1000"),
            ("How many reps per department?", f"SELECT department_key, COUNT(*) AS rep_count FROM `{tid('dim_sales_rep')}` GROUP BY department_key LIMIT 1000"),
            ("Find rep by code SM01", f"SELECT description, company FROM `{tid('dim_sales_rep')}` WHERE sales_rep_code = 'SM01' LIMIT 1000"),
            ("Reps with Frazer link populated", f"SELECT sales_rep_code, frazer_link FROM `{tid('dim_sales_rep')}` WHERE frazer_link IS NOT NULL LIMIT 1000"),
            ("Count sales reps", f"SELECT COUNT(*) AS total_reps FROM `{tid('dim_sales_rep')}` LIMIT 1000"),
            ("Rep names for Frazer company", f"SELECT description FROM `{tid('dim_sales_rep')}` WHERE company = 'Frazer' ORDER BY description LIMIT 1000"),
            ("Distinct companies in rep dimension", f"SELECT DISTINCT company FROM `{tid('dim_sales_rep')}` LIMIT 1000"),
            ("Reps in department key 1", f"SELECT sales_rep_code, description FROM `{tid('dim_sales_rep')}` WHERE department_key = 1 LIMIT 1000"),
        ],
    },
    "dim_product": {
        "layer": "dimension",
        "agent_default": True,
        "routing_priority": "secondary",
        "display_name": "Product Group (Dimension)",
        "description": "Main product group dimension keyed by main_group_name.",
        "business_tags": ["product", "product group", "main group", "category"],
        "grain": "One row per main product group.",
        "columns": [
            col("product_key", "INT64", "Surrogate PK"),
            col("main_group_name", "STRING", "Main product group name (natural key)"),
        ],
        "relationships": [],
        "common_filters": ["main_group_name"],
        "common_aggregations": [["product_key", "COUNT"]],
        "time_columns": [],
        "few_shot": [
            ("List all product groups", f"SELECT product_key, main_group_name FROM `{tid('dim_product')}` ORDER BY main_group_name LIMIT 1000"),
            ("How many product groups exist?", f"SELECT COUNT(*) AS group_count FROM `{tid('dim_product')}` LIMIT 1000"),
            ("Find product key for group Electrical", f"SELECT product_key FROM `{tid('dim_product')}` WHERE main_group_name = 'Electrical' LIMIT 1000"),
            ("Product groups starting with A", f"SELECT main_group_name FROM `{tid('dim_product')}` WHERE main_group_name LIKE 'A%' ORDER BY main_group_name LIMIT 1000"),
            ("Distinct main group names", f"SELECT DISTINCT main_group_name FROM `{tid('dim_product')}` LIMIT 1000"),
            ("Top 10 product groups by name", f"SELECT main_group_name FROM `{tid('dim_product')}` ORDER BY main_group_name LIMIT 10"),
            ("Product groups count by first letter", f"SELECT SUBSTR(main_group_name, 1, 1) AS letter, COUNT(*) AS cnt FROM `{tid('dim_product')}` GROUP BY letter LIMIT 1000"),
            ("Is there a product group called Plumbing?", f"SELECT product_key FROM `{tid('dim_product')}` WHERE main_group_name = 'Plumbing' LIMIT 1000"),
        ],
    },
    "stg_sales_report": {
        "layer": "staging",
        "agent_default": False,
        "routing_priority": "avoid_unless_raw",
        "display_name": "Sales Report (Staging Raw)",
        "description": "Raw RDS import of invoice line items. All columns STRING — prefer fact_sales_report for analytics.",
        "business_tags": ["raw", "staging", "source", "sales file", "untyped"],
        "grain": "One raw invoice line item row (STRING types).",
        "columns": [
            col("id", "STRING", "Record id"), col("account", "STRING", "Customer account"),
            col("trans_date", "STRING", "Transaction datetime string"), col("invoice", "STRING", "Invoice"),
            col("line_sales_ex_gst", "STRING", "Line sales ex GST as string"), col("line_gp_dollar", "STRING", "Line GP string"),
            col("rep", "STRING", "Rep code"), col("main_group_name", "STRING", "Product group"),
            col("company", "STRING", "Jaybel or Frazer"), col("fiscal_year", "STRING", "FY label"),
        ],
        "relationships": [],
        "common_filters": ["fiscal_year", "company", "account"],
        "common_aggregations": [],
        "time_columns": ["trans_date"],
        "few_shot": [
            ("Raw row count in staging sales", f"SELECT COUNT(*) AS rows FROM `{tid('stg_sales_report')}` LIMIT 1000"),
            ("Sample 5 raw sales rows", f"SELECT id, account, trans_date, line_sales_ex_gst FROM `{tid('stg_sales_report')}` LIMIT 5"),
            ("Distinct fiscal_year values in raw sales", f"SELECT DISTINCT fiscal_year FROM `{tid('stg_sales_report')}` LIMIT 1000"),
            ("Raw sales for company Jaybel", f"SELECT COUNT(*) AS cnt FROM `{tid('stg_sales_report')}` WHERE company = 'Jaybel' LIMIT 1000"),
            ("Invoices in raw staging for account ACC001", f"SELECT invoice, trans_date FROM `{tid('stg_sales_report')}` WHERE account = 'ACC001' LIMIT 1000"),
            ("Raw file_id traceability list", f"SELECT DISTINCT file_id FROM `{tid('stg_sales_report')}` LIMIT 1000"),
            ("Raw rep codes distinct", f"SELECT DISTINCT rep FROM `{tid('stg_sales_report')}` LIMIT 1000"),
            ("Raw territory codes", f"SELECT DISTINCT ter FROM `{tid('stg_sales_report')}` LIMIT 1000"),
        ],
    },
    "stg_sales_cust": {
        "layer": "staging",
        "agent_default": False,
        "routing_priority": "avoid_unless_raw",
        "display_name": "Sales Customer (Staging Raw)",
        "description": "Raw customer import. Prefer dim_sales_customer for typed customer analytics.",
        "business_tags": ["raw customer", "staging", "source"],
        "grain": "One raw customer row (STRING).",
        "columns": [
            col("id", "STRING", "Customer id"), col("account", "STRING", "Account code"),
            col("account_name", "STRING", "Account name"), col("is_new_account", "STRING", "1=new, 0=existing", ["0", "1"]),
        ],
        "relationships": [],
        "common_filters": ["account"],
        "common_aggregations": [],
        "time_columns": ["created_date"],
        "few_shot": [
            ("Count raw staging customers", f"SELECT COUNT(*) FROM `{tid('stg_sales_cust')}` LIMIT 1000"),
            ("Raw new account flag distribution", f"SELECT is_new_account, COUNT(*) AS cnt FROM `{tid('stg_sales_cust')}` GROUP BY is_new_account LIMIT 1000"),
            ("Sample raw customer names", f"SELECT account, account_name FROM `{tid('stg_sales_cust')}` LIMIT 10"),
            ("Raw customers by industry sub", f"SELECT industry_sub, COUNT(*) AS cnt FROM `{tid('stg_sales_cust')}` GROUP BY industry_sub LIMIT 1000"),
            ("Find raw account ACC99", f"SELECT * FROM `{tid('stg_sales_cust')}` WHERE account = 'ACC99' LIMIT 1000"),
            ("Distinct business codes raw", f"SELECT DISTINCT business_code FROM `{tid('stg_sales_cust')}` LIMIT 1000"),
            ("Raw customers with rep assigned", f"SELECT account_name, rep FROM `{tid('stg_sales_cust')}` WHERE rep IS NOT NULL LIMIT 1000"),
            ("Raw customer id list limit 20", f"SELECT id, account FROM `{tid('stg_sales_cust')}` LIMIT 20"),
        ],
    },
    "stg_sales_rep": {
        "layer": "staging",
        "agent_default": False,
        "routing_priority": "avoid_unless_raw",
        "display_name": "Sales Rep (Staging Raw)",
        "description": "Raw sales rep reference. Prefer dim_sales_rep.",
        "business_tags": ["raw rep", "staging"],
        "grain": "One raw rep row.",
        "columns": [
            col("sales_rep_id", "STRING", "Rep id"), col("sales_rep_code", "STRING", "Rep code"),
            col("description", "STRING", "Rep name"), col("company", "STRING", "Jaybel or Frazer"),
        ],
        "relationships": [],
        "common_filters": ["sales_rep_code", "company"],
        "common_aggregations": [],
        "time_columns": [],
        "few_shot": [
            ("Count raw reps", f"SELECT COUNT(*) FROM `{tid('stg_sales_rep')}` LIMIT 1000"),
            ("Raw rep codes for Jaybel", f"SELECT sales_rep_code, description FROM `{tid('stg_sales_rep')}` WHERE company = 'Jaybel' LIMIT 1000"),
            ("Distinct companies raw reps", f"SELECT DISTINCT company FROM `{tid('stg_sales_rep')}` LIMIT 1000"),
            ("Find raw rep by code", f"SELECT description FROM `{tid('stg_sales_rep')}` WHERE sales_rep_code = 'R01' LIMIT 1000"),
            ("Reps with frazer_link", f"SELECT sales_rep_code, frazer_link FROM `{tid('stg_sales_rep')}` WHERE frazer_link IS NOT NULL LIMIT 1000"),
            ("Sample 10 raw reps", f"SELECT sales_rep_code, description FROM `{tid('stg_sales_rep')}` LIMIT 10"),
            ("Raw rep id count", f"SELECT COUNT(DISTINCT sales_rep_id) FROM `{tid('stg_sales_rep')}` LIMIT 1000"),
            ("List raw rep descriptions A-M", f"SELECT description FROM `{tid('stg_sales_rep')}` WHERE description < 'N' ORDER BY description LIMIT 1000"),
        ],
    },
    "stg_main_product": {
        "layer": "staging",
        "agent_default": False,
        "routing_priority": "avoid_unless_raw",
        "display_name": "Main Product (Staging Raw)",
        "description": "Raw product group reference. Prefer dim_product.",
        "business_tags": ["raw product", "staging"],
        "grain": "One raw product group row.",
        "columns": [col("id", "STRING", "Product group id"), col("main_group_name", "STRING", "Group name")],
        "relationships": [],
        "common_filters": ["main_group_name"],
        "common_aggregations": [],
        "time_columns": [],
        "few_shot": [
            ("Count raw product groups", f"SELECT COUNT(*) FROM `{tid('stg_main_product')}` LIMIT 1000"),
            ("List raw main group names", f"SELECT main_group_name FROM `{tid('stg_main_product')}` ORDER BY main_group_name LIMIT 1000"),
            ("Raw product id for Electrical", f"SELECT id FROM `{tid('stg_main_product')}` WHERE main_group_name = 'Electrical' LIMIT 1000"),
            ("Sample 5 product groups raw", f"SELECT id, main_group_name FROM `{tid('stg_main_product')}` LIMIT 5"),
            ("Distinct raw product names", f"SELECT DISTINCT main_group_name FROM `{tid('stg_main_product')}` LIMIT 1000"),
            ("Product groups starting with C raw", f"SELECT main_group_name FROM `{tid('stg_main_product')}` WHERE main_group_name LIKE 'C%' LIMIT 1000"),
            ("How many distinct ids raw product", f"SELECT COUNT(DISTINCT id) FROM `{tid('stg_main_product')}` LIMIT 1000"),
            ("Check if Plumbing exists raw", f"SELECT id FROM `{tid('stg_main_product')}` WHERE main_group_name = 'Plumbing' LIMIT 1000"),
        ],
    },
    "stg_new_busin_frazer": {
        "layer": "staging",
        "agent_default": False,
        "routing_priority": "avoid_unless_raw",
        "display_name": "New Business Frazer (Staging Raw)",
        "description": "Raw Frazer new business lines. Prefer fact_new_business for metrics.",
        "business_tags": ["raw new business", "Frazer staging"],
        "grain": "One raw new business row (STRING).",
        "columns": [
            col("account", "STRING", "Account"), col("trans_date", "STRING", "Transaction date"),
            col("line_sales_ex_gst", "STRING", "Sales string"), col("territory", "STRING", "Territory"),
            col("company", "STRING", "Usually Frazer"),
        ],
        "relationships": [],
        "common_filters": ["territory", "company"],
        "common_aggregations": [],
        "time_columns": ["trans_date"],
        "few_shot": [
            ("Count raw new business rows", f"SELECT COUNT(*) FROM `{tid('stg_new_busin_frazer')}` LIMIT 1000"),
            ("Distinct territories raw new business", f"SELECT DISTINCT territory FROM `{tid('stg_new_busin_frazer')}` LIMIT 1000"),
            ("Sample raw new business", f"SELECT account, line_sales_ex_gst, territory FROM `{tid('stg_new_busin_frazer')}` LIMIT 5"),
            ("Raw new business by company", f"SELECT company, COUNT(*) FROM `{tid('stg_new_busin_frazer')}` GROUP BY company LIMIT 1000"),
            ("Raw trans dates in 2025", f"SELECT trans_date FROM `{tid('stg_new_busin_frazer')}` WHERE trans_date LIKE '2025%' LIMIT 1000"),
            ("Accounts in raw new business", f"SELECT DISTINCT account FROM `{tid('stg_new_busin_frazer')}` LIMIT 1000"),
            ("Raw frazer_link values", f"SELECT DISTINCT frazer_link FROM `{tid('stg_new_busin_frazer')}` LIMIT 1000"),
            ("Territory NSW raw rows", f"SELECT COUNT(*) FROM `{tid('stg_new_busin_frazer')}` WHERE territory = 'NSW' LIMIT 1000"),
        ],
    },
    "stg_total_working_days": {
        "layer": "staging",
        "agent_default": True,
        "routing_priority": "special_reference",
        "display_name": "Total Working Days (Reference)",
        "description": (
            "Standalone reference for working days per fiscal month/year. "
            "Not part of star schema joins — query this table alone for working-day KPIs."
        ),
        "business_tags": ["working days", "business days", "fiscal month capacity", "sales days"],
        "grain": "One row per fiscal year + month (plus yearly totals).",
        "columns": [
            col("id", "STRING", "Record id"),
            col("fiscal_year", "STRING", "FY label e.g. 2025-2026"),
            col("month", "STRING", "Month name or number"),
            col("total_working_days", "STRING", "Working days in month"),
            col("YearlyTotalWorkingDays", "STRING", "Working days in fiscal year"),
            col("Completed_days", "STRING", "Completed working days so far"),
        ],
        "relationships": [],
        "common_filters": ["fiscal_year", "month"],
        "common_aggregations": [],
        "time_columns": [],
        "few_shot": [
            ("Working days in July for fiscal 2025-2026", f"SELECT total_working_days FROM `{tid('stg_total_working_days')}` WHERE fiscal_year = '2025-2026' AND month = 'July' LIMIT 1000"),
            ("Yearly total working days FY 2025-2026", f"SELECT YearlyTotalWorkingDays FROM `{tid('stg_total_working_days')}` WHERE fiscal_year = '2025-2026' LIMIT 1"),
            ("Completed working days so far FY 2025-2026", f"SELECT Completed_days FROM `{tid('stg_total_working_days')}` WHERE fiscal_year = '2025-2026' AND month = 'Current' LIMIT 1"),
            ("List working days by month for 2024-2025", f"SELECT month, total_working_days FROM `{tid('stg_total_working_days')}` WHERE fiscal_year = '2024-2025' ORDER BY month LIMIT 1000"),
            ("How many months have working day data", f"SELECT COUNT(DISTINCT month) FROM `{tid('stg_total_working_days')}` WHERE fiscal_year = '2025-2026' LIMIT 1000"),
            ("Distinct fiscal years in working days table", f"SELECT DISTINCT fiscal_year FROM `{tid('stg_total_working_days')}` LIMIT 1000"),
            ("Working days for fiscal Q1 months", f"SELECT month, total_working_days FROM `{tid('stg_total_working_days')}` WHERE fiscal_year = '2025-2026' AND month IN ('July','August','September') LIMIT 1000"),
            ("Compare completed vs total days", f"SELECT month, Completed_days, total_working_days FROM `{tid('stg_total_working_days')}` WHERE fiscal_year = '2025-2026' LIMIT 1000"),
        ],
    },
}


def build_yaml(name: str, spec: dict) -> dict:
    shots = [{"question": q, "sql": textwrap.dedent(s).strip()} for q, s in spec["few_shot"]]
    return {
        "table_id": tid(name),
        "display_name": spec["display_name"],
        "layer": spec["layer"],
        "agent_default": spec["agent_default"],
        "routing_priority": spec["routing_priority"],
        "description": spec["description"],
        "business_tags": spec["business_tags"],
        "grain": spec["grain"],
        "columns": spec["columns"],
        "relationships": spec.get("relationships", []),
        "common_filters": spec.get("common_filters", []),
        "common_aggregations": spec.get("common_aggregations", []),
        "time_columns": spec.get("time_columns", []),
        "few_shot_examples": shots,
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, spec in TABLES.items():
        path = OUT / f"{name}.yaml"
        with path.open("w") as f:
            yaml.dump(build_yaml(name, spec), f, sort_keys=False, allow_unicode=True, default_flow_style=False)
        print("wrote", path.name)


if __name__ == "__main__":
    main()
