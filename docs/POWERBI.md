# Power BI dashboard

`powerbi/Kestrel_Distributors.pbip` is a Power BI project (text format, reviewable in Git). `powerbi/Kestrel_Distributors.pbix` is the same report as a single file.

## Open it

1. Export the dashboard tables: `python run.py powerbi` (writes `powerbi/data/*.csv`; the last line should show total net sales of Rs 2,533,032,735.60).
2. Open `powerbi/Kestrel_Distributors.pbip` in Power BI Desktop and click **Refresh**.
3. If the repo is not in the default location, open **Transform data → Manage parameters** and set `DataFolder` to your `powerbi/data` folder.

## Pages

| Page | Shows |
|---|---|
| Actions | Four problems found in the data, each priced in rupees, with an owner |
| Overview | Last full month vs previous month and last year, monthly trend, city map, categories, lost customers |
| Products | Seasonality-adjusted index by product and city; biggest gaps ranked by rupees |
| Sales team | Attainment over the last 3 full months; month-by-month detail |
| Stock | Days of cover by warehouse and item; status follows the warehouse filter |
| Data quality | Every issue found in the source files and how it was handled |

Screenshots: `docs/screenshots/`.

## Regenerate

`python scripts/build_powerbi_project.py` rebuilds the model (tables, relationships, measures) and all report pages from code, so changes are reviewable and repeatable.
