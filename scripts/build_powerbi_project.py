"""Generate the Power BI project (powerbi/Kestrel_Distributors.pbip + .SemanticModel + .Report + theme) from export_powerbi.SPEC.

    python scripts/build_powerbi_project.py
"""
import json, sys, uuid, shutil
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from export_powerbi import SPEC

ROOT = Path(__file__).resolve().parents[1] / "powerbi"
NAME = "Kestrel_Distributors"
SM = ROOT / f"{NAME}.SemanticModel"
RP = ROOT / f"{NAME}.Report"
for p in (SM, RP):
    shutil.rmtree(p, ignore_errors=True)
S = "https://developer.microsoft.com/json-schemas/fabric"
VC_V, PG_V, RPT_V = "2.11.0", "2.1.0", "3.3.0"


def w(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    txt = obj if isinstance(obj, str) else json.dumps(obj, indent=2, ensure_ascii=False)
    path.write_text(txt, encoding="utf-8")


def gid(seed):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "kestrel/" + seed))

# ---------------- wrapper files ----------------
w(ROOT / f"{NAME}.pbip", {
    "$schema": f"{S}/pbip/pbipProperties/1.0.0/schema.json",
    "version": "1.0",
    "artifacts": [{"report": {"path": f"{NAME}.Report"}}],
    "settings": {"enableAutoRecovery": True},
})
w(SM / ".platform", {"$schema": f"{S}/gitIntegration/platformProperties/2.0.0/schema.json",
     "metadata": {"type": "SemanticModel", "displayName": NAME},
     "config": {"version": "2.0", "logicalId": gid("sm")}})
w(RP / ".platform", {"$schema": f"{S}/gitIntegration/platformProperties/2.0.0/schema.json",
     "metadata": {"type": "Report", "displayName": NAME},
     "config": {"version": "2.0", "logicalId": gid("rp")}})
w(SM / "definition.pbism", {"$schema": f"{S}/item/semanticModel/definitionProperties/1.0.0/schema.json",
     "version": "4.2", "settings": {}})
w(RP / "definition.pbir", {"$schema": f"{S}/item/report/definitionProperties/2.0.0/schema.json",
     "version": "4.0", "datasetReference": {"byPath": {"path": f"../{NAME}.SemanticModel"}}})

# ---------------- semantic model (TMDL) ----------------
T = "\t"
DT = {"text": "string", "date": "dateTime", "int": "int64", "decimal": "decimal", "double": "double", "bool": "boolean"}
MT = {"text": "type text", "date": "type date", "int": "Int64.Type", "decimal": "Currency.Type", "double": "type number", "bool": "type logical"}
FMT = {"date": "yyyy-mm-dd", "decimal": "#,0", "int": "#,0"}
NO_SUM = {"year", "month", "day_of_month", "sort_order", "slowdown_rank_in_city", "days_since_last_order"}
RS = "\\R\\s\\ #,0"
MEAS = {
    "rpt_sales_overview": [
        ("Net Sales", "SUM(rpt_sales_overview[net_amount_pkr])", RS),
        ("Returns", "-SUM(rpt_sales_overview[returns_amount_pkr])", RS),
        ("Returns %", "DIVIDE([Returns], [Net Sales] + [Returns])", "0.0%"),
        ("Active Customers", "CALCULATE(DISTINCTCOUNT(rpt_sales_overview[customer_id]), rpt_sales_overview[is_return] = FALSE())", "#,0"),
        ("Gross Margin %", "DIVIDE([Net Sales] - SUM(rpt_sales_overview[cost_amount_pkr]), [Net Sales])", "0.0%"),
        ("Net Sales PM", "CALCULATE([Net Sales], DATEADD(dim_date[date_day], -1, MONTH))", RS),
        ("MoM %", "DIVIDE([Net Sales] - [Net Sales PM], [Net Sales PM])", "+0.0%;-0.0%;0.0%"),
        ("Net Sales LY", "CALCULATE([Net Sales], SAMEPERIODLASTYEAR(dim_date[date_day]))", RS),
        ("YoY %", "DIVIDE([Net Sales] - [Net Sales LY], [Net Sales LY])", "+0.0%;-0.0%;0.0%"),
        ("Data Label", '"Illustrative data — fictional company"', None),
        ('Net Sales Cr', '[Net Sales] / 10000000', '\\R\\s 0.0 \\C\\r'),
        ('Net Sales LY Cr', '[Net Sales LY] / 10000000', '\\R\\s 0.0 \\C\\r'),
        ('Sales at Stake Text', 'VAR v = [Lost Sales per Month] + [Churned Sales per Month] + [Target Shortfall 3M] / 3 RETURN IF(ISBLANK(v), BLANK(), IF(ABS(v) >= 10000000, "Rs " & FORMAT(v / 10000000, "0.0") & " Cr", "Rs " & FORMAT(v / 100000, "0.0") & " lakh"))', None),
    ],
    "mart_product_city_trend": [
        ("Seasonality Index", "AVERAGE(mart_product_city_trend[seasonality_adjusted_index])", "0.00"),
        ("Slowing Products", "CALCULATE(COUNTROWS(mart_product_city_trend), mart_product_city_trend[is_slowing] = TRUE())", "#,0"),
        ('Lost Sales per Month', 'SUMX(FILTER(mart_product_city_trend, mart_product_city_trend[is_slowing]), VAR sku = mart_product_city_trend[product_sku] VAR price = CALCULATE(DIVIDE(SUM(rpt_sales_overview[net_amount_pkr]), SUM(rpt_sales_overview[quantity])), REMOVEFILTERS(rpt_sales_overview), REMOVEFILTERS(dim_date), rpt_sales_overview[product_sku] = sku, rpt_sales_overview[is_return] = FALSE()) VAR gap = mart_product_city_trend[daily_units_base] * mart_product_city_trend[rest_of_country_change] - mart_product_city_trend[daily_units_cur] RETURN MAX(0, gap) * 30 * price)', '#,0'),
        ('Lost Sales Text', 'VAR v = [Lost Sales per Month] RETURN IF(ISBLANK(v), BLANK(), IF(ABS(v) >= 10000000, "Rs " & FORMAT(v / 10000000, "0.0") & " Cr", "Rs " & FORMAT(v / 100000, "0.0") & " lakh"))', None),
        ('Slowdown Detail', 'VAR t = TOPN(2, FILTER(mart_product_city_trend, mart_product_city_trend[is_slowing]), mart_product_city_trend[seasonality_adjusted_index], ASC) RETURN CONCATENATEX(t, mart_product_city_trend[product_name], " & ") & " · " & MAXX(t, mart_product_city_trend[city])', None),
    ],
    "mart_salesperson_attainment": [
        ("Attainment %", "DIVIDE(SUM(mart_salesperson_attainment[actual_pkr]), SUM(mart_salesperson_attainment[target_pkr]))", "0%"),
        ("Target Line", "1", "0%"),
        ("Visit to Order %", "DIVIDE(SUM(mart_salesperson_attainment[order_visits]), SUM(mart_salesperson_attainment[visits]))", "0%"),
        ("Reps Below 85% x3", "CALCULATE(DISTINCTCOUNT(mart_salesperson_attainment[salesperson_id]), mart_salesperson_attainment[is_below_85_three_months_running] = TRUE())", "#,0"),
        ("Target PKR", "SUM(mart_salesperson_attainment[target_pkr])", RS),
        ('Target Shortfall 3M', 'VAR latest = CALCULATE(MAX(mart_salesperson_attainment[month_start]), REMOVEFILTERS(mart_salesperson_attainment), mart_salesperson_attainment[is_month_to_date] = FALSE()) VAR reps = CALCULATETABLE(VALUES(mart_salesperson_attainment[salesperson_id]), REMOVEFILTERS(mart_salesperson_attainment), mart_salesperson_attainment[is_below_85_three_months_running] = TRUE()) RETURN CALCULATE(SUM(mart_salesperson_attainment[target_pkr]) - SUM(mart_salesperson_attainment[actual_pkr]), REMOVEFILTERS(mart_salesperson_attainment), mart_salesperson_attainment[salesperson_id] IN reps, mart_salesperson_attainment[is_month_to_date] = FALSE(), mart_salesperson_attainment[month_start] > EDATE(latest, -3))', '#,0'),
        ('Shortfall Text', 'VAR v = [Target Shortfall 3M] RETURN IF(ISBLANK(v), BLANK(), IF(ABS(v) >= 10000000, "Rs " & FORMAT(v / 10000000, "0.0") & " Cr", "Rs " & FORMAT(v / 100000, "0.0") & " lakh"))', None),
        ('Rep Detail', 'VAR r = CALCULATETABLE(VALUES(mart_salesperson_attainment[salesperson_name]), REMOVEFILTERS(mart_salesperson_attainment), mart_salesperson_attainment[is_below_85_three_months_running] = TRUE()) RETURN CONCATENATEX(r, mart_salesperson_attainment[salesperson_name], ", ") & " · below 85% for 3 months"', None),
        ("Actual PKR", "SUM(mart_salesperson_attainment[actual_pkr])", RS),
    ],
    "mart_stock_cover": [
        ("Days of Cover", "MIN(mart_stock_cover[days_of_cover])", "0.0"),
        ("Low Stock Items", "CALCULATE(COUNTROWS(mart_stock_cover), mart_stock_cover[is_low_stock] = TRUE())", "#,0"),
        ('Sales at Risk per Day', 'SUMX(FILTER(mart_stock_cover, mart_stock_cover[is_low_stock]), VAR sku = mart_stock_cover[product_sku] VAR price = CALCULATE(DIVIDE(SUM(rpt_sales_overview[net_amount_pkr]), SUM(rpt_sales_overview[quantity])), REMOVEFILTERS(rpt_sales_overview), REMOVEFILTERS(dim_date), rpt_sales_overview[product_sku] = sku, rpt_sales_overview[is_return] = FALSE()) RETURN mart_stock_cover[avg_units_per_day_28d] * price)', '#,0'),
        ('Stock Risk Text', 'VAR v = [Sales at Risk per Day] RETURN IF(ISBLANK(v), BLANK(), IF(ABS(v) >= 10000000, "Rs " & FORMAT(v / 10000000, "0.0") & " Cr", "Rs " & FORMAT(v / 100000, "0.0") & " lakh")) & " / day"', None),
        ('Stock Detail', 'VAR t = TOPN(1, FILTER(mart_stock_cover, NOT ISBLANK(mart_stock_cover[days_of_cover])), mart_stock_cover[days_of_cover], ASC) RETURN MAXX(t, mart_stock_cover[product_name]) & " · " & MAXX(t, mart_stock_cover[warehouse_id]) & " · " & FORMAT(MAXX(t, mart_stock_cover[days_of_cover]), "0.0") & " days left"', None),
    ],
    "mart_customer_activity": [
        ("Churned Customers", "CALCULATE(COUNTROWS(mart_customer_activity), mart_customer_activity[is_churned] = TRUE())", "#,0"),
        ('Churned Sales per Month', 'SUMX(FILTER(mart_customer_activity, mart_customer_activity[is_churned]), DIVIDE(mart_customer_activity[lifetime_net_pkr], MAX(1, DATEDIFF(mart_customer_activity[first_order_date], mart_customer_activity[last_order_date], MONTH) + 1)))', '#,0'),
        ('Churn Text', 'VAR v = [Churned Sales per Month] RETURN IF(ISBLANK(v), BLANK(), IF(ABS(v) >= 10000000, "Rs " & FORMAT(v / 10000000, "0.0") & " Cr", "Rs " & FORMAT(v / 100000, "0.0") & " lakh"))', None),
        ('Churn Detail', 'VAR byCity = ADDCOLUMNS(VALUES(mart_customer_activity[city]), "n", CALCULATE(COUNTROWS(mart_customer_activity), mart_customer_activity[is_churned] = TRUE())) VAR top = TOPN(1, byCity, [n], DESC) RETURN FORMAT([Churned Customers], "0") & " retailers stopped ordering · " & MAXX(top, [n]) & " in " & MAXX(top, mart_customer_activity[city])', None),
        ("At-Risk Customers", "CALCULATE(COUNTROWS(mart_customer_activity), mart_customer_activity[is_at_risk] = TRUE())", "#,0"),
    ],
    "mart_data_quality": [("Rows Affected", "SUM(mart_data_quality[affected_count])", "#,0")],
}

# ---- Business measures (owner-facing, values in lakh / crore) ----
def _lak(expr):
    return (f'VAR v = {expr} RETURN IF(ISBLANK(v), BLANK(), IF(ABS(v) >= 10000000, "Rs " & FORMAT(v / 10000000, "0.0") & " Cr", '
            f'"Rs " & FORMAT(v / 100000, "0.0") & " lakh"))')


def _set(table, name, expr, fmt, new_name=None):
    lst = MEAS[table]
    for i, m in enumerate(lst):
        if m[0] == name:
            lst[i] = (new_name or name, expr, fmt)
            return
    lst.append((new_name or name, expr, fmt))


_LM = ('VAR maxd = CALCULATE(MAX(rpt_sales_overview[invoice_date]), REMOVEFILTERS()) '
       'VAR b = EOMONTH(maxd, -2) + 1 ')


def _month(shift):
    return (_LM + f'RETURN CALCULATE([Net Sales], REMOVEFILTERS(dim_date), dim_date[date_day] >= EDATE(b, {shift}), '
            f'dim_date[date_day] <= EOMONTH(EDATE(b, {shift}), 0))')


SR = "rpt_sales_overview"; TR = "mart_product_city_trend"; AT = "mart_salesperson_attainment"
ST = "mart_stock_cover"; CU = "mart_customer_activity"; DQT = "mart_data_quality"
_set(SR, "Net Sales Last Month", _month(0), "#,0")
_set(SR, "Net Sales Last Month Text", _lak("[Net Sales Last Month]"), None)
_set(SR, "Net Sales PM", _month(-1), "#,0")
_set(SR, "Net Sales LY", _month(-12), "#,0")
_set(SR, "MoM %", "DIVIDE([Net Sales Last Month] - [Net Sales PM], [Net Sales PM])", "+0.0%;-0.0%;0.0%")
_set(SR, "YoY %", "DIVIDE([Net Sales Last Month] - [Net Sales LY], [Net Sales LY])", "+0.0%;-0.0%;0.0%")
_set(SR, "Net Sales LY Cr", _LM + 'RETURN FORMAT(b, "mmmm yyyy")', None, "Last Full Month")
_set(SR, "Net Sales Text", _lak("[Net Sales]"), None)

_set(TR, "Lost Sales per Month", f"CALCULATE(SUM({TR}[lost_sales_per_month]), {TR}[lost_sales_per_month] >= 200000)", "#,0")
_set(TR, "Slowing Products", f"CALCULATE(COUNTROWS({TR}), {TR}[lost_sales_per_month] >= 200000)", "#,0")
_set(TR, "Slowdown Detail",
     f'VAR t = TOPN(1, {TR}, {TR}[lost_sales_per_month], DESC) RETURN [Slowing Products] & " pairs · biggest: " & '
     f'MAXX(t, {TR}[product_name]) & " (" & MAXX(t, {TR}[city]) & ")"', None)

_LATEST = (f'VAR latest = CALCULATE(MAX({AT}[month_start]), REMOVEFILTERS({AT}), {AT}[is_month_to_date] = FALSE()) ')
_REPS = (f'VAR reps = CALCULATETABLE(VALUES({AT}[salesperson_id]), REMOVEFILTERS({AT}), '
         f'{AT}[is_below_85_three_months_running] = TRUE(), {AT}[month_start] = latest) ')
_set(AT, "Reps Below 85% x3", _LATEST + f'RETURN CALCULATE(DISTINCTCOUNT({AT}[salesperson_id]), REMOVEFILTERS({AT}), '
     f'{AT}[is_below_85_three_months_running] = TRUE(), {AT}[month_start] = latest)', "#,0")
_set(AT, "Target Shortfall 3M", _LATEST + _REPS + f'RETURN CALCULATE(SUM({AT}[target_pkr]) - SUM({AT}[actual_pkr]), '
     f'REMOVEFILTERS({AT}), {AT}[salesperson_id] IN reps, {AT}[is_last_3_months] = TRUE())', "#,0")
_set(AT, "Rep Detail", _LATEST + _REPS + f'VAR r = CALCULATETABLE({AT}, REMOVEFILTERS({AT}), {AT}[salesperson_id] IN reps, '
     f'{AT}[is_last_3_months] = TRUE()) RETURN CONCATENATEX(SUMMARIZE(r, {AT}[salesperson_name]), {AT}[salesperson_name], ", ") '
     f'& " · " & FORMAT(MINX(r, {AT}[attainment]), "0%") & "–" & FORMAT(MAXX(r, {AT}[attainment]), "0%") & " of target"', None)

_set(CU, "Churned Sales per Month", f"CALCULATE(SUM({CU}[monthly_value]), {CU}[is_churned] = TRUE())", "#,0")
_set(CU, "Churn Detail",
     f'VAR n = [Churned Customers] VAR t = TOPN(1, ADDCOLUMNS(VALUES({CU}[city]), "@n", CALCULATE(COUNTROWS({CU}), '
     f'{CU}[is_churned] = TRUE())), [@n], DESC) VAR c = MAXX(t, [@n]) RETURN n & " retailers stopped ordering · " & '
     f'IF(c = n, "all in ", "most in ") & MAXX(t, {CU}[city])', None)
_set(CU, "Customer Monthly Value", f"SUM({CU}[monthly_value])", "\\R\\s #,0")
_set(ST, "Stock Risk Text", _lak("[Sales at Risk per Day]"), None)
_set(DQT, "Rows Affected", f"COUNTROWS({DQT})", "#,0", "Issues Found")

_PRICE = ('CALCULATE(DIVIDE(SUM(rpt_sales_overview[net_amount_pkr]), SUM(rpt_sales_overview[quantity])), REMOVEFILTERS(), '
          'rpt_sales_overview[product_sku] = sku, rpt_sales_overview[is_return] = FALSE())')
CALC = {
    TR: [("lost_sales_per_month",
          f"IF({TR}[is_slowing], VAR sku = {TR}[product_sku] VAR price = {_PRICE} VAR gap = {TR}[daily_units_base] * "
          f"{TR}[rest_of_country_change] - {TR}[daily_units_cur] RETURN MAX(0, gap) * 30 * price, 0)", "double", "\\R\\s #,0")],
    AT: [("is_last_3_months",
          f"VAR latest = MAXX(FILTER(ALL({AT}), NOT {AT}[is_month_to_date]), {AT}[month_start]) "
          f"RETURN {AT}[is_month_to_date] = FALSE() && {AT}[month_start] > EDATE(latest, -3)", "boolean", None)],
    CU: [("monthly_value",
          f"IF(ISBLANK({CU}[first_order_date]), 0, DIVIDE({CU}[lifetime_net_pkr], MAX(1, DATEDIFF({CU}[first_order_date], "
          f"{CU}[last_order_date], MONTH) + 1)))", "double", "\\R\\s #,0")],
    "dim_date": [("is_complete_month",
                  "dim_date[month_start] <= EOMONTH(MAX(rpt_sales_overview[invoice_date]), -2) + 1 "
                  "&& dim_date[month_start] >= MIN(rpt_sales_overview[invoice_month])",
                  "boolean", None)],
}

_set(SR, "Active Customers LM", _LM + 'RETURN CALCULATE(DISTINCTCOUNT(rpt_sales_overview[customer_id]), REMOVEFILTERS(dim_date), dim_date[date_day] >= b, dim_date[date_day] <= EOMONTH(b, 0), rpt_sales_overview[is_return] = FALSE())', "#,0")
_set(SR, "Gross Margin LM", _LM + 'RETURN CALCULATE([Gross Margin %], REMOVEFILTERS(dim_date), dim_date[date_day] >= b, dim_date[date_day] <= EOMONTH(b, 0))', "0.0%")
_set(TR, "Slowdown Detail", f'VAR t = TOPN(1, {TR}, {TR}[lost_sales_per_month], DESC) RETURN [Slowing Products] & " slowdowns · biggest: " & MAXX(t, {TR}[product_name]) & " (" & MAXX(t, {TR}[city]) & ")"', None)
CALC[TR].append(("lost_lakh", f"{TR}[lost_sales_per_month] / 100000", "double", "\\R\\s 0.0 \\l\\a\\k\\h"))

_set(ST, "Stock Risk Text", 'VAR v = [Sales at Risk per Day] RETURN IF(ISBLANK(v) || v = 0, "Rs 0", IF(v >= 10000000, "Rs " & FORMAT(v / 10000000, "0.0") & " Cr", "Rs " & FORMAT(v / 100000, "0.0") & " lakh"))', None)
CALC.setdefault(SR, []).append(("city_location", 'rpt_sales_overview[city] & ", Pakistan"', "string", None))

_set(ST, "Stock Status", f'VAR lowN = [Low Stock Items] VAR t = TOPN(1, FILTER({ST}, NOT ISBLANK({ST}[days_of_cover])), {ST}[days_of_cover], ASC) VAR p = MAXX(t, {ST}[product_name]) VAR w = MAXX(t, {ST}[warehouse_id]) VAR d = FORMAT(MAXX(t, {ST}[days_of_cover]), "0.0") RETURN IF(lowN > 0, p & " at " & w & " has " & d & " days of stock left. Reorder now: running out costs about " & [Stock Risk Text] & " of sales a day.", "Nothing below 7 days here. Lowest cover: " & p & " at " & w & ", " & d & " days.")', None)

_set(ST, "Sales at Risk Value", "COALESCE([Sales at Risk per Day], 0)", "#,0")
_set(SR, "MoM %", "DIVIDE([Net Sales Last Month] - [Net Sales PM], [Net Sales PM])", "▲ +0.0%;▼ -0.0%;0.0%")
_set(SR, "YoY %", "DIVIDE([Net Sales Last Month] - [Net Sales LY], [Net Sales LY])", "▲ +0.0%;▼ -0.0%;0.0%")

DATA_FOLDER = "D:\\Projects\\kestrel-demo\\powerbi\\data"

w(SM / "definition/database.tmdl", "database\n\tcompatibilityLevel: 1600\n")
model = ["model Model", f"{T}culture: en-US", f"{T}defaultPowerBIDataSourceVersion: powerBI_V3",
         f"{T}sourceQueryCulture: en-US", f"{T}dataAccessOptions", f"{T*2}legacyRedirects",
         f"{T*2}returnErrorValuesAsNull", "", f"{T}annotation __PBI_TimeIntelligenceEnabled = 0", ""]
model += [f"ref table {t}" for t in SPEC] + [""]
w(SM / "definition/model.tmdl", "\n".join(model))
w(SM / "definition/expressions.tmdl",
  f'expression DataFolder = "{DATA_FOLDER}" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]\n'
  f"{T}lineageTag: {gid('expr')}\n\n{T}annotation PBI_ResultType = Text\n")
for t, cols in SPEC.items():
    L = [f"table {t}", f"{T}lineageTag: {gid(t)}"]
    if t == "dim_date":
        L.append(f"{T}dataCategory: Time")
    L.append("")
    for name, expr, fmt in MEAS.get(t, []):
        L.append(f"{T}measure '{name}' = {expr}")
        if fmt:
            L.append(f"{T*2}formatString: {fmt}")
        L.append(f"{T*2}lineageTag: {gid(t + '/m/' + name)}")
        L.append("")
    for c, ty in cols:
        L.append(f"{T}column {c}")
        L.append(f"{T*2}dataType: {DT[ty]}")
        if t == "dim_date" and c == "date_day":
            L.append(f"{T*2}isKey")
        if c in ("month_start", "invoice_month", "week_start"):
            L.append(f"{T*2}formatString: mmm yyyy")
        elif c in ("avg_units_per_day_28d", "units_sold_28d", "units_cur", "units_base"):
            L.append(f"{T*2}formatString: #,0")
        elif ty in FMT:
            L.append(f"{T*2}formatString: {FMT[ty]}")
        L.append(f"{T*2}lineageTag: {gid(t + '/c/' + c)}")
        L.append(f"{T*2}summarizeBy: {'sum' if ty in ('decimal', 'double', 'int') and c not in NO_SUM else 'none'}")
        L.append(f"{T*2}sourceColumn: {c}")
        L.append("")
    for c, expr, dt_, fmt in CALC.get(t, []):
        L.append(f"{T}column {c} = {expr}")
        L.append(f"{T*2}dataType: {dt_}")
        if c == "city_location":
            L.append(f"{T*2}dataCategory: Place")
        if fmt:
            L.append(f"{T*2}formatString: {fmt}")
        L.append(f"{T*2}lineageTag: {gid(t + '/cc/' + c)}")
        L.append(f"{T*2}summarizeBy: {'sum' if dt_ == 'double' else 'none'}")
        L.append("")
    types = ", ".join('{"%s", %s}' % (c, MT[ty]) for c, ty in cols)
    L += [f"{T}partition {t} = m", f"{T*2}mode: import", f"{T*2}source =",
          f"{T*4}let",
          f'{T*5}Source = Csv.Document(File.Contents(DataFolder & "\\{t}.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
          f"{T*5}Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),",
          f'{T*5}Typed = Table.TransformColumnTypes(Promoted, {{{types}}}, "en-US")',
          f"{T*4}in", f"{T*5}Typed", ""]
    w(SM / f"definition/tables/{t}.tmdl", "\n".join(L))
w(SM / "definition/relationships.tmdl",
  f"relationship {gid('rel1')}\n{T}fromColumn: rpt_sales_overview.invoice_date\n{T}toColumn: dim_date.date_day\n")

# ---------------- report (PBIR) ----------------
NAVY, ACCENT, SLATE, INK = "#1E2A44", "#2A78D6", "#64748B", "#0F172A"
ATTN, NEUTRAL, UP, DOWN, HEAD = "#E8833A", "#A9BCD3", "#1E8E5A", "#C2413B", "#1D4ED8"
RED, AMBER, GREEN = "#DC2626", "#F59E0B", "#16A34A"
THEME = {
    "name": "Kestrel Demo",
    "dataColors": ["#2A78D6", "#EB6834", "#1BAF7A", "#EDA100", "#E87BA4", "#008300", "#6250D6"],
    "background": "#FFFFFF", "foreground": INK, "tableAccent": ACCENT,
    "good": GREEN, "neutral": AMBER, "bad": RED, "maximum": GREEN, "center": "#FFFFFF", "minimum": RED,
    "textClasses": {
        "title": {"fontFace": "Segoe UI Semibold", "fontSize": 12, "color": INK},
        "header": {"fontFace": "Segoe UI Semibold", "fontSize": 11, "color": INK},
        "label": {"fontFace": "Segoe UI", "fontSize": 10, "color": "#475569"},
        "callout": {"fontFace": "Segoe UI Semibold", "fontSize": 24, "color": INK},
    },
    "visualStyles": {
        "*": {"*": {
            "background": [{"show": True, "color": {"solid": {"color": "#FFFFFF"}}, "transparency": 0}],
            "border": [{"show": True, "color": {"solid": {"color": "#E2E8F0"}}, "radius": 10, "width": 1}],
            "dropShadow": [{"show": True, "color": {"solid": {"color": "#0F172A"}}, "transparency": 90,
                            "position": "Outer", "preset": "BottomRight"}],
            "padding": [{"top": 8, "bottom": 8, "left": 12, "right": 12}],
            "title": [{"show": True, "fontColor": {"solid": {"color": INK}}, "fontSize": 11, "bold": True}],
            "visualHeader": [{"show": False}],
        }},
        "page": {"*": {
            "background": [{"color": {"solid": {"color": "#F1F5F9"}}, "transparency": 0}],
            "outspace": [{"color": {"solid": {"color": "#F1F5F9"}}, "transparency": 0}],
        }},
        "textbox": {"*": {"background": [{"show": False}], "border": [{"show": False}], "dropShadow": [{"show": False}]}},
        "shape": {"*": {"background": [{"show": False}], "border": [{"show": False}], "dropShadow": [{"show": False}],
                        "title": [{"show": False}]}},
        "pageNavigator": {"*": {"background": [{"show": False}], "border": [{"show": False}],
                                "dropShadow": [{"show": False}], "title": [{"show": False}]}},
        "tableEx": {"*": {"grid": [{"gridHorizontal": True, "gridHorizontalColor": {"solid": {"color": "#EEF2F7"}},
                                    "gridVertical": False, "rowPadding": 4}],
                          "columnHeaders": [{"backColor": {"solid": {"color": "#F8FAFC"}}, "bold": True,
                                             "fontColor": {"solid": {"color": "#334155"}}}]}},
        "pivotTable": {"*": {"columnHeaders": [{"backColor": {"solid": {"color": "#F8FAFC"}}, "bold": True}],
                             "rowHeaders": [{"backColor": {"solid": {"color": "#FFFFFF"}}}]}},
    },
}
(RP / "StaticResources/RegisteredResources").mkdir(parents=True, exist_ok=True)
w(RP / "StaticResources/RegisteredResources/KestrelDemo.json", THEME)
w(ROOT / "kestrel_theme.json", THEME)

D = RP / "definition"
VER = {"visual": "2.11.0", "report": "3.4.0", "page": "2.3.1"}
w(D / "version.json", {"$schema": f"{S}/item/report/definition/versionMetadata/1.0.0/schema.json", "version": "2.0.0"})
w(D / "report.json", {
    "$schema": f"{S}/item/report/definition/report/{RPT_V}/schema.json",
    "themeCollection": {"baseTheme": {"name": "CY26SU07", "reportVersionAtImport": VER, "type": "SharedResources"},
                        "customTheme": {"name": "KestrelDemo.json", "reportVersionAtImport": VER,
                                        "type": "RegisteredResources"}},
    "objects": {"section": [{"properties": {"verticalAlignment": {"expr": {"Literal": {"Value": "'Top'"}}}}}],
                "outspacePane": [{"properties": {"expanded": {"expr": {"Literal": {"Value": "false"}}}}}]},
    "resourcePackages": [{"name": "RegisteredResources", "type": "RegisteredResources",
                          "items": [{"name": "KestrelDemo.json", "path": "KestrelDemo.json", "type": "CustomTheme"}]}],
    "settings": {"useStylableVisualContainerHeader": True, "exportDataMode": "AllowSummarized",
                 "defaultDrillFilterOtherVisuals": True, "allowChangeFilterTypes": True, "useEnhancedTooltips": True,
                 "useDefaultAggregateDisplayName": True},
})


def col(t, c):
    return {"Column": {"Expression": {"SourceRef": {"Entity": t}}, "Property": c}}


def mea(t, m):
    return {"Measure": {"Expression": {"SourceRef": {"Entity": t}}, "Property": m}}


def proj(f):
    label = None
    if isinstance(f, tuple):
        f, label = f
    k = "Column" if "Column" in f else "Measure"
    t = f[k]["Expression"]["SourceRef"]["Entity"]; p = f[k]["Property"]
    out = {"field": f, "queryRef": f"{t}.{p}", "nativeQueryRef": p}
    if label:
        out["displayName"] = label
    return out


def L(v):
    return {"expr": {"Literal": {"Value": v}}}


def color(hexv):
    return {"solid": {"color": L(f"'{hexv}'")}}


def s(text):
    return L("'" + text.replace("'", "''") + "'")


def gradient(field, lo, mid, hi):
    """3-colour gradient conditional colour. lo/mid/hi = (value, hex)."""
    def stop(v, c):
        return {"color": {"Literal": {"Value": f"'{c}'"}}, "value": {"Literal": {"Value": f"{v}D"}}}
    return {"solid": {"color": {"expr": {"FillRule": {"Input": field, "FillRule": {"linearGradient3": {
        "min": stop(*lo), "mid": stop(*mid), "max": stop(*hi),
        "nullColoringStrategy": {"strategy": {"Literal": {"Value": "'asZero'"}}}}}}}}}}


def bands(field, cuts):
    """Firm colour bands: cuts = [(upper_bound, hex), ...] ascending, last entry = default colour."""
    cases = [{"Condition": {"Comparison": {"ComparisonKind": 3, "Left": field,
                                           "Right": {"Literal": {"Value": f"{ub}D"}}}},
              "Value": {"Literal": {"Value": f"'{c}'"}}} for ub, c in cuts[:-1]]
    return {"solid": {"color": {"expr": {"Conditional": {"Cases": cases,
            "DefaultValue": {"Literal": {"Value": f"'{cuts[-1][1]}'"}}}}}}}


ALL_POINTS = {"data": [{"dataViewWildcard": {"matchingOption": 1}}]}


def bool_filter(name, t, c, value=True):
    return {"name": name, "field": col(t, c), "type": "Categorical",
            "filter": {"Version": 2, "From": [{"Name": "x", "Entity": t, "Type": 0}],
                       "Where": [{"Condition": {"In": {
                           "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "x"}}, "Property": c}}],
                           "Values": [[{"Literal": {"Value": "true" if value else "false"}}]]}}}]}}


class Page:
    def __init__(self, pid, title, subtitle):
        self.pid, self.title, self.vis, self.n, self.filters = pid, title, [], 0, []
        self.add("textbox", 0, 0, 1280, 76, objects={"general": [{"properties": {
            "paragraphs": [{"textRuns": [{"value": " "}]}]}}]},
            vco={"background": [{"properties": {"show": L("true"), "color": color(NAVY), "transparency": L("0D")}}],
                 "border": [{"properties": {"show": L("false")}}],
                 "dropShadow": [{"properties": {"show": L("false")}}]})
        self.text(16, 0, 580, 46, title, "15pt", color="#FFFFFF")
        self.text(16, 38, 580, 36, subtitle + "  ·  Illustrative data, fictional company", "9pt",
                  bold=False, color="#DBEAFE")
        self.add("pageNavigator", 600, 18, 664, 42, objects={
            "fill": [{"properties": {"show": L("true")}},
                     {"properties": {"fillColor": color("#34466A")}, "selector": {"id": "default"}}],
            "outline": [{"properties": {"show": L("false")}}],
            "glow": [{"properties": {"show": L("false")}}],
            "accentBar": [{"properties": {"show": L("false")}}, ],
            "shape": [{"properties": {"roundEdge": L("8L"), "tileShape": s("rectangleRounded")}, "selector": {"id": "default"}}],
            "text": [{"properties": {"fontColor": color("#FFFFFF"), "fontSize": L("9D")}, "selector": {"id": "default"}}]})

    def add(self, vtype, x, y, wd, ht, roles=None, title=None, sort=None, filters=None, objects=None, vco=None):
        self.n += 1
        name = f"{self.pid}_v{self.n:02d}"
        visual = {"visualType": vtype}
        if roles:
            visual["query"] = {"queryState": {r: {"projections": [proj(f) for f in fs]} for r, fs in roles.items()}}
            if sort:
                f, d = sort
                visual["query"]["sortDefinition"] = {"sort": [{"field": f, "direction": d}], "isDefaultSort": False}
        if objects:
            visual["objects"] = objects
        c = dict(vco or {})
        if title:
            c["title"] = [{"properties": {"show": L("true"), "text": s(title)}}]
        if c:
            visual["visualContainerObjects"] = c
        vc = {"$schema": f"{S}/item/report/definition/visualContainer/{VC_V}/schema.json", "name": name,
              "position": {"x": x, "y": y, "z": self.n * 1000, "width": wd, "height": ht, "tabOrder": self.n * 1000},
              "visual": visual}
        if filters:
            vc["filterConfig"] = {"filters": filters}
        self.vis.append(vc)

    def text(self, x, y, wd, ht, text, size="20pt", bold=True, color=None):
        style = {"fontSize": size}
        if bold:
            style["fontWeight"] = "bold"
        if color:
            style["color"] = color
        self.add("textbox", x, y, wd, ht, objects={"general": [{"properties": {
            "paragraphs": [{"textRuns": [{"value": text, "textStyle": style}]}]}}]})

    def insight(self, x, y, wd, ht, heading, body, tone=None):
        tone = HEAD
        self.add("textbox", x, y, wd, ht, objects={"general": [{"properties": {"paragraphs": [
            {"textRuns": [{"value": heading, "textStyle": {"fontSize": "11pt", "fontWeight": "bold", "color": tone}}]},
            {"textRuns": [{"value": body, "textStyle": {"fontSize": "10pt", "color": "#334155"}}]}]}}]},
            vco={"background": [{"properties": {"show": L("true"), "color": color("#EFF6FF"), "transparency": L("0D")}}],
                 "border": [{"properties": {"show": L("true"), "color": color("#BFDBFE"), "radius": L("10D")}}],
                 "padding": [{"properties": {"top": L("12D"), "left": L("14D"), "right": L("14D")}}]})

    def kpi(self, x, y, wd, ht, field, label, colour_rule=None, size=None, accent=ACCENT):
        props = {"fontColor": colour_rule or color(INK)}
        if size:
            props["fontSize"] = L(f"{size}D")
        obj = {"value": [{"properties": props, "selector": {"id": "default"}}],
               "outline": [{"properties": {"show": L("false")}, "selector": {"id": "default"}}],
               "accentBar": [{"properties": {"show": L("true"), "color": color(accent), "width": L("4D")},
                              "selector": {"id": "default"}}]}
        self.add("cardVisual", x, y, wd, ht, {"Data": [(field, label)]}, objects=obj)

    def note(self, x, y, wd, ht, field, label):
        """Classic card for a sentence-length text measure, word-wrapped."""
        self.add("card", x, y, wd, ht, {"Values": [(field, label)]}, objects={
            "labels": [{"properties": {"fontSize": L("11D"), "color": color(INK)}}],
            "wordWrap": [{"properties": {"show": L("true")}}],
            "categoryLabels": [{"properties": {"show": L("true"), "fontSize": L("9D")}}]})

    def table(self, x, y, wd, ht, cols, title, sort=None, filters=None):
        self.add("tableEx", x, y, wd, ht, {"Values": cols}, title=title, sort=sort, filters=filters,
                 objects={"total": [{"properties": {"totals": L("false")}}]})

    def slicer(self, x, y, wd, ht, field, title):
        self.add("slicer", x, y, wd, ht, {"Values": [(field, title)]},
                 objects={"data": [{"properties": {"mode": s("Dropdown")}}]})


def bar_objects(field=None, rule=None, ref=None, ref_label=None, inside=False, label_bg=False):
    lab = {"show": L("true"), "fontSize": L("9D")}
    if inside:
        lab.update({"labelPosition": s("InsideEnd"), "color": color("#FFFFFF")})
    if label_bg:
        lab.update({"enableBackground": L("true"), "backgroundColor": color("#FFFFFF"), "backgroundTransparency": L("0D")})
    o = {"labels": [{"properties": lab}],
         "legend": [{"properties": {"show": L("false")}}],
         "valueAxis": [{"properties": {"show": L("false")}}],
         "categoryAxis": [{"properties": {"showAxisTitle": L("false"), "maxMarginFactor": L("45D")}}]}
    if rule:
        o["dataPoint"] = [{"properties": {"fill": rule}, "selector": ALL_POINTS}]
    if ref is not None:
        o["y1AxisReferenceLine"] = [{"properties": {"show": L("true"), "value": L(f"{ref}D"),
                                                    "lineColor": color("#0F172A"), "style": s("dashed"),
                                                    "transparency": L("20D"), "displayName": s(ref_label), "position": s("Behind"),
                                                    "dataLabelShow": L("false")}, "selector": {"id": "1"}}]
    return o



S_ = "rpt_sales_overview"; PT = "mart_product_city_trend"; SA = "mart_salesperson_attainment"
SC = "mart_stock_cover"; CA = "mart_customer_activity"; DQ = "mart_data_quality"
pct_rule = lambda f: bands(f, [(0, DOWN), (None, UP)])
pages = []

# 0 Action summary ---------------------------------------------------------
p = Page("actions", "Kestrel Distributors · What to do this week", "Four problems found in the data, each priced in rupees")
pages.append(p)
p.kpi(20, 88, 380, 124, mea(S_, "Sales at Stake Text"), "Sales to recover per month (estimate)", color(NAVY), 30, accent=ATTN)
p.insight(412, 88, 848, 124, "How to read this page",
          "Each column is one problem, what it costs and who should act. Every rupee figure is calculated from the "
          "invoices, stock counts and targets behind the other pages. Use the tabs above to see the detail.")
ACTIONS = [
    ("1 · Win back lost retailers", "Owner: Multan sales manager", mea(CA, "Churn Text"), "Sales lost per month",
     mea(CA, "Churn Detail")),
    ("2 · Fix the biggest slowdowns", "Owner: Trade marketing", mea(PT, "Lost Sales Text"),
     "Gap per month vs trend", mea(PT, "Slowdown Detail")),
    ("3 · Coach the rep below target", "Owner: Lahore sales manager", mea(SA, "Shortfall Text"),
     "Target missed, 3 months", mea(SA, "Rep Detail")),
    ("4 · Reorder before stock-out", "Owner: Purchasing, LHE warehouse", mea(SC, "Stock Risk Text"),
     "Sales at risk per day", mea(SC, "Stock Detail")),
]
for i, (head, owner, impact, impact_label, detail) in enumerate(ACTIONS):
    x = 20 + i * 312
    p.insight(x, 224, 302, 70, head, owner, ACCENT)
    p.kpi(x, 302, 302, 118, impact, impact_label, color(INK), 24, accent=ATTN)
    p.note(x, 428, 302, 112, detail, "What the data shows")
p.kpi(20, 552, 302, 152, mea(S_, "Net Sales Text"), "Net sales, Jul 2025 – Oct 2026")
p.kpi(332, 552, 302, 152, mea(S_, "YoY %"), "Last full month vs a year earlier", pct_rule(mea(S_, "YoY %")))
p.kpi(644, 552, 302, 152, mea(S_, "Active Customers LM"), "Active customers, last month")
p.insight(956, 552, 304, 152, "Numbers you can check",
          "Net sales reconcile to the source invoices to the rupee. Every data problem found was fixed and is "
          "listed on the Data quality page.")

# 1 Overview ----------------------------------------------------------------
p = Page("overview", "Sales overview", "Last full month at a glance, then the trend since July 2025"); pages.append(p)
p.slicer(20, 88, 300, 72, col(S_, "city"), "City")
p.slicer(332, 88, 300, 72, col(S_, "category"), "Category")
p.note(644, 88, 616, 72, mea(S_, "Last Full Month"), "Last full month (cards below)")
p.kpi(20, 172, 302, 104, mea(S_, "Net Sales Last Month Text"), "Net sales, last full month")
p.kpi(332, 172, 302, 104, mea(S_, "MoM %"), "vs previous month", pct_rule(mea(S_, "MoM %")))
p.kpi(644, 172, 302, 104, mea(S_, "YoY %"), "vs same month last year", pct_rule(mea(S_, "YoY %")))
p.kpi(956, 172, 304, 104, mea(S_, "Gross Margin LM"), "Gross margin, last full month")
p.add("lineChart", 20, 288, 620, 206, {"Category": [(col("dim_date", "month_start"), "Month")],
      "Y": [(mea(S_, "Net Sales Cr"), "Net sales (Rs Cr)")]}, title="Net sales by month, Rs crore (full months only)",
      filters=[bool_filter("f_full", "dim_date", "is_complete_month")],
      objects={"valueAxis": [{"properties": {"show": L("true"), "showAxisTitle": L("false"), "start": L("0D")}}],
               "categoryAxis": [{"properties": {"showAxisTitle": L("false")}}],
               "labels": [{"properties": {"show": L("false")}}]})
p.table(20, 506, 620, 198, [(col(CA, "customer_name"), "Customer"), (col(CA, "city"), "City"),
        (col(CA, "last_order_date"), "Last order"), (col(CA, "days_since_last_order"), "Days since"),
        (mea(CA, "Customer Monthly Value"), "Usual monthly sales")],
        "Stopped ordering (all cities): 9 in Multan, about Rs 7 lakh a month", sort=(mea(CA, "Customer Monthly Value"), "Descending"),
        filters=[bool_filter("f_churn", CA, "is_churned")])
p.add("map", 652, 288, 300, 416, {"Category": [(col(S_, "city_location"), "City")],
      "Size": [(mea(S_, "Net Sales Cr"), "Net sales (Rs Cr)")],
      "Tooltips": [(mea(S_, "Net Sales Last Month Text"), "Net sales, last full month"), (mea(S_, "YoY %"), "vs a year earlier")]},
      title="Cities vs last year: blue up, orange down",
      objects={"bubbles": [{"properties": {"bubbleSize": L("12L")}}],
               "categoryLabels": [{"properties": {"show": L("false")}}],
               "heatMap": [{"properties": {"show": L("false")}}],
               "dataPoint": [{"properties": {"fill": bands(mea(S_, "YoY %"), [(0, ATTN), (None, ACCENT)])},
                              "selector": ALL_POINTS}]})
p.add("clusteredBarChart", 964, 288, 296, 416, {"Category": [(col(S_, "category"), "Category")],
      "Y": [(mea(S_, "Net Sales Cr"), "Net sales (Rs Cr)")]},
      title="By category, Jul 2025 – Oct 2026 (Rs Cr)", sort=(mea(S_, "Net Sales Cr"), "Descending"), objects=bar_objects())

# 2 Products & cities -------------------------------------------------------
p = Page("products", "Products & cities", "Each city's trend this month vs the rest of Pakistan, after seasonality")
pages.append(p)
p.kpi(20, 88, 300, 124, mea(PT, "Lost Sales Text"), "Gap per month vs trend", color(INK), 24, accent=ATTN)
p.insight(332, 88, 928, 124, "What stands out",
          "Biggest rupee loss: Highland Black Tea 450g in Rawalpindi (Rs 13 lakh a month). Sharpest city-specific drop: "
          "Brightwash Detergent 1kg and Fruitara Mango Nectar 1L in Karachi, at a quarter of the national trend on high "
          "volumes. Only losses over Rs 2 lakh a month are counted.")
idx = mea(PT, "Seasonality Index")
p.add("pivotTable", 20, 224, 820, 480, {"Rows": [(col(PT, "product_name"), "Product")], "Columns": [(col(PT, "city"), "City")],
      "Values": [(idx, "Index")]}, title="Index by product and city · orange = slower than the national trend, blue = faster",
      objects={"values": [{"properties": {"backColor": gradient(idx, (0.25, "#F4A582"), (1, "#FFFFFF"), (1.75, "#92C5DE")),
                                          "fontSize": L("9D")},
                           "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}],
                                        "metadata": f"{PT}.Seasonality Index"}}],
               "columnHeaders": [{"properties": {"fontSize": L("9D")}}],
               "rowHeaders": [{"properties": {"fontSize": L("9D")}}],
               "subTotals": [{"properties": {"rowSubtotals": L("false"), "columnSubtotals": L("false")}}]})
p.table(852, 224, 408, 480, [(col(PT, "product_name"), "Product"), (col(PT, "city"), "City"),
        (col(PT, "lost_lakh"), "Gap")],
        "Biggest gaps, ranked by rupees", sort=(col(PT, "lost_lakh"), "Descending"),
        filters=[bool_filter("f_slow", PT, "is_slowing")])

# 3 Sales team --------------------------------------------------------------
p = Page("sales_team", "Sales team", "Attainment vs target over the last 3 full months (Jul – Sep 2026)")
pages.append(p)
p.filters = [bool_filter("f_l3m", SA, "is_last_3_months")]
att = mea(SA, "Attainment %")
p.kpi(20, 88, 236, 124, att, "Attainment, 3 months", bands(att, [(0.85, ATTN), (None, INK)]))
p.kpi(268, 88, 236, 124, mea(SA, "Visit to Order %"), "Visits → orders")
p.kpi(516, 88, 236, 124, mea(SA, "Shortfall Text"), "Gap for reps under 85%", color(INK), accent=ATTN)
p.insight(764, 88, 496, 124, "What stands out",
          "Only Adeel Khan (SP-07, Lahore) was under 85% in all three months: 55%, 64%, 53%. Lahore sales are down 25% on last September, and his customers account for about two-thirds of that drop (Rs 137 lakh down to Rs 79 lakh).")
p.add("clusteredBarChart", 20, 224, 560, 480, {"Category": [(col(SA, "salesperson_name"), "Salesperson")],
      "Y": [(att, "Attainment")]}, title="Attainment by salesperson (dashed line = 100% of target)",
      sort=(att, "Ascending"),
      objects=bar_objects(att, bands(att, [(0.85, ATTN), (1.0, NEUTRAL), (None, ACCENT)]), 1, "Target"))
p.table(592, 224, 668, 480, [(col(SA, "salesperson_name"), "Salesperson"), (col(SA, "month_start"), "Month"),
        (mea(SA, "Target PKR"), "Target"), (mea(SA, "Actual PKR"), "Actual"), (att, "Attainment"),
        (mea(SA, "Visit to Order %"), "Visit → order")], "Month by month", sort=(att, "Ascending"))

# 4 Stock -------------------------------------------------------------------
p = Page("stock", "Stock", "Days of cover at the latest count · under 7 = reorder")
pages.append(p)
p.slicer(20, 88, 300, 72, col(SC, "warehouse_id"), "Warehouse")
p.kpi(332, 88, 300, 124, mea(SC, "Stock Risk Text"), "Sales at risk per day", bands(mea(SC, "Sales at Risk Value"), [(1, INK), (None, ATTN)]), accent=ATTN)
p.note(644, 88, 616, 124, mea(SC, "Stock Status"), "Status for the selected warehouse")
doc = mea(SC, "Days of Cover")
p.add("clusteredBarChart", 20, 224, 560, 480, {"Category": [(col(SC, "product_name"), "Product")],
      "Y": [(doc, "Days of cover")]}, title="Lowest days of cover (dashed line = 7 days)", sort=(doc, "Ascending"),
      objects=bar_objects(doc, bands(doc, [(7, ATTN), (None, NEUTRAL)]), 7, "Reorder line", label_bg=True))
p.table(592, 224, 668, 480, [(col(SC, "warehouse_id"), "Warehouse"), (col(SC, "product_name"), "Product"),
        (col(SC, "closing_qty"), "In stock"), (col(SC, "avg_units_per_day_28d"), "Sold per day"),
        (doc, "Days of cover")], "Every item, lowest cover first", sort=(doc, "Ascending"))

# 5 Data quality ------------------------------------------------------------
p = Page("data_quality", "Data quality", "What was wrong in the source files and how it was fixed")
pages.append(p)
p.kpi(20, 88, 300, 124, mea(DQ, "Issues Found"), "Data problems found and fixed")
p.insight(332, 88, 928, 124, "Why this matters",
          "Net sales on every page reconcile to the source invoices to the rupee (Rs 253.3 Cr). Your own exports "
          "almost certainly have issues like these. A Data & AI Readiness Audit finds them and produces this page "
          "for your business.")
p.table(20, 224, 892, 480, [(col(DQ, "sort_order"), "#"), (col(DQ, "issue"), "Problem"),
        (col(DQ, "source_system"), "Source"), (col(DQ, "affected_count"), "Rows affected"),
        (col(DQ, "handling"), "How it was fixed")], "Problems found in the source data",
        sort=(col(DQ, "sort_order"), "Ascending"))
p.insight(924, 224, 336, 480, "Checked on every refresh",
          "132 automated checks run each time the data is reloaded: every ID is unique, every sale links to a real "
          "customer, unknown products are flagged, stock is never negative, and total net sales must match the "
          "source invoices to the rupee. If a critical check fails, the update stops before a wrong number reaches "
          "this report.")

NAMES = {"actions": "Actions", "overview": "Overview", "products": "Products"}
for pg in pages:
    pd = {"$schema": f"{S}/item/report/definition/page/{PG_V}/schema.json", "name": pg.pid,
          "displayName": NAMES.get(pg.pid, pg.title), "displayOption": "FitToPage", "height": 720, "width": 1280}
    if pg.filters:
        pd["filterConfig"] = {"filters": pg.filters}
    w(D / f"pages/{pg.pid}/page.json", pd)
    for v in pg.vis:
        w(D / f"pages/{pg.pid}/visuals/{v['name']}/visual.json", v)
w(D / "pages/pages.json", {"$schema": f"{S}/item/report/definition/pagesMetadata/1.1.0/schema.json",
                           "pageOrder": [p.pid for p in pages], "activePageName": pages[0].pid})
print("pages", len(pages), "visuals", sum(len(p.vis) for p in pages))
