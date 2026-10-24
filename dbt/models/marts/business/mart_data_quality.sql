-- One row per data-quality issue, with how many rows it affected and how the
-- pipeline handled it. Feeds the dashboard's Data quality page.

with checks as (
    select 1 as sort_order, 'City spelling variants' as issue, 'ERP customers' as source_system,
           (select count(*) from {{ ref('stg_erp__customers') }} where is_city_corrected) as affected_count,
           'Mapped to canonical city with a seed table' as handling
    union all
    select 2, 'Customers with no salesperson', 'ERP customers',
           (select count(*) from {{ ref('stg_erp__customers') }} where is_salesperson_missing),
           'Kept, shown as Unassigned'
    union all
    select 3, 'Invoice header total differs from its lines', 'ERP invoices',
           (select count(*) from {{ ref('int_invoice_reconciliation') }} where is_mismatch),
           'Lines used as the source of truth'
    union all
    select 4, 'SKU in lower case or with spaces', 'ERP invoice lines',
           (select count(*) from {{ ref('stg_erp__invoice_lines') }} where is_sku_cleaned),
           'Trimmed and upper-cased'
    union all
    select 5, 'Exact duplicate invoice lines', 'ERP invoice lines',
           (select count(*) from {{ source('erp', 'sales_invoice_lines') }})
             - (select count(*) from {{ ref('stg_erp__invoice_lines') }}),
           'Removed'
    union all
    select 6, 'SKU missing from product master', 'ERP invoice lines',
           (select count(*) from {{ ref('fct_sales_lines') }} where is_unknown_product),
           'Kept as Unknown product and flagged for review'
    union all
    select 7, 'Stock item codes without dashes (ISB-WH)', 'Inventory workbook',
           (select count(*) from {{ ref('stg_inv__stock_snapshots') }} where is_sku_cleaned),
           'Dashes restored'
    union all
    select 8, 'Stock sheets with title rows above the header', 'Inventory workbook',
           (select count(distinct warehouse_id) from {{ ref('stg_inv__stock_snapshots') }}),
           'Title rows skipped, header row checked'
    union all
    select 9, 'Duplicate visit records (sync retries)', 'Field-sales app',
           (select count(*) from {{ source('field_app', 'visits') }})
             - (select count(*) from {{ ref('stg_app__visits') }}),
           'First copy kept'
    union all
    select 10, 'Visit times in UTC, not Pakistan time', 'Field-sales app',
           (select count(*) from {{ ref('stg_app__visits') }}),
           'Converted to Asia/Karachi'
)

select * from checks
