# Office Supplies BI — Client question catalog

Source: `Office_Supplies_BI_Analytics_Questions.pdf` (client-provided).  
These are **additional** questions the client may ask the agent, on top of the generic star-schema QA set in `docs/qa_evaluation_set.yaml` (Q001–Q060).

## How the agent should use this doc

- **Routing:** Most questions map to `fact_sales_report` + dimension joins; working-day / projection math may also use `stg_total_working_days`.
- **Product categories** (examples from the BI report): map to `dim_product.main_group_name` — e.g. `Office Supplies`, `Furniture`, `Ink & Toner`, `Kitchen & Janitorial`, `Apparel`. Confirm exact strings in live data.
- **Customer names** (examples): filter `dim_sales_customer.account_name` (e.g. `Brisbane City Council`, `Lizard Island Resort`, `Best Doors Rockhampton`, `99 BIKES`).
- **Rep-scoped questions** (“my sales”, “my GP”): require **rep context** from local `users.sales_rep_code` (Postgres) passed into Agent Engine session → filter `dim_sales_rep` / facts by `rep_key` or `sales_rep_code`.
- **Targets (v1.2):** FY goals from `config/sales_targets.yaml` (Overall $6,067,292.04, Furniture GP $387,173.20, BTS $613,099.84). SQL compares BigQuery **actuals** to these config literals — not a BQ budget table.
- **Projections (v1.2):** **Run-rate estimates** use MTD actuals + `stg_total_working_days` (`(MTD / Completed_days) × total_working_days`). This is **not** the exact Power BI “Projected Monthly Sales/GP” measure — the agent must say so.
- **BI-only forecast (Q093):** Explaining the -$1,695,009.72 Furniture projected variance requires the Power BI model; offer actuals + config target variance instead.
- **Closed accounts / embroidery:** Pattern rules in `config/account_patterns.yaml` and `config/embroidery_patterns.yaml` (no `account_status` or job_type columns in dims yet).
- **BTS target:** Program-level target in config; **no single `main_group_name` mapped yet** — confirm with business which product groups roll up to BTS.

## Categories and questions (verbatim intent, normalized spelling)

### 1. Executive & high-level KPIs

1. What is our total Sales and Gross Profit (GP$) for the current 2025-2026 financial year compared to last year?
2. What is our daily average sales amount so far this month, and are we on track to hit our projected monthly sales?
3. How far behind are we on our Overall Business Target of $6M?
4. What is our current Gross Profit margin percentage (GP%) across the business, and how does it compare to FY 24-25?

### 2. Product & category performance

5. Show me the top 10 best-selling products for the current year.
6. Which product category generated the most revenue yesterday?
7. Compare the Gross Profit percentage of 'Office Supplies' versus 'Furniture' for this year.
8. How are we performing against our specific Furniture GP Target of $387K? What is the percentage difference?
9. Show me the month-by-month sales trend for the 'Ink & Toner' category.
10. What were the total sales and GP% for Office Supplies compared to Kitchen & Janitorial this year?
11. Show me the Year-on-Year sales performance trend for the Apparel category.
12. Which specific product category is driving the highest daily average Gross Profit (GP)?
13. What is the Gross Profit percentage (GP%) for Furniture in the current year versus last year?

### 3. Customer & account management

14. Who are our top 5 customers by total sales this year?
15. Show me a list of customers who haven't placed an order since 2022.
16. What were the total sales for 'Brisbane City Council' in October compared to November?
17. Which of our accounts have a 'Closed' status but still show historical revenue?
18. Show me the customer retention performance—compare 'Previous Month Sales' to 'Current Month Sales' for our top 20 accounts.

### 4. Customer retention

19. Which customers had the largest negative difference between Previous Month Sales and Current Month Sales?
20. Show me the customer retention performance for the '99 BIKES' franchise locations.
21. How much historical revenue have we lost from accounts currently marked as '*** ACCOUNT CLOSED ***'?

### 5. Tactical & order-level inquiries

22. Show me all recent orders placed by 'Lizard Island Resort'.
23. How many units of item code 'HCL-S901S' (Allegra Bottle) were sold this month?
24. Pull the transaction date and quantity for the last order of 'Best Doors Rockhampton'.
25. List all embroidery or custom printing jobs we processed this week.

### 6. Sales representative focus

26. How do my total sales this month compare to my sales during the same month last year?
27. What is my individual Gross Profit (GP$) contribution for the 2025-2026 financial year?
28. Which of my specific accounts are showing a decline in month-over-month sales?

### 7. Targets & goal attainment

29. How are we currently performing against the Overall Business Target of $6,067,292.04?
30. What is our exact variance against the Furniture Target of $387,173.20?
31. Are we currently on track to hit the BTS Target of $613,099.84?

### 8. Projections & forecasting

32. What are our Projected Monthly Sales compared to our current Sales Month To Date?
33. Why is the Projected Furniture GP$ showing a negative variance of -$1,695,009.72?
34. What is the Projected GP$ for the entire business, and what is our percentage difference from that goal?
35. Based on the 7 completed working days this month, what is our Projected Monthly GP?

### 9. Commission & payout proxies

36. What is the total Gross Profit (GP$) I have generated for my closed deals this quarter?
37. What is the total value of closed-won sales I have achieved this month to calculate my payout?

## QA cross-reference

Each question above has a matching case **Q061–Q097** in `docs/qa_evaluation_set.yaml` (`source: office_supplies_bi_pdf`).
