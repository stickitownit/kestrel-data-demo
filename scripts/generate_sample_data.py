"""
Generate illustrative sample data for Kestrel Distributors (a FICTIONAL company).

Three source systems, each exported in its own format, the way real clients hand data over:
  1. ERP            -> data/raw/erp/*.csv          (products, customers, invoices, invoice lines)
  2. Inventory      -> data/raw/inventory/*.xlsx   (weekly stock report + goods receipts)
  3. Field-sales app-> data/raw/field_app/*.json(l)(salespeople, monthly targets, shop visits)

The script first builds a clean "truth" dataset, then writes messy exports with
deliberate data-quality issues. It also writes data/answer_key.json, computed from
the clean truth, so the pipeline and the AI assistant can be checked against it.

All names, numbers and businesses are made up. Seeded, so every run is identical.
Usage:  python scripts/generate_sample_data.py
"""
from __future__ import annotations

import json
import random
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
START = date(2025, 7, 1)
END = date(2026, 10, 23)          # data runs up to "yesterday" of the demo
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
rng = np.random.default_rng(SEED)
random.seed(SEED)

# --------------------------------------------------------------------------- #
# Reference data
# --------------------------------------------------------------------------- #
WAREHOUSES = {  # warehouse -> cities it serves
    "KHI-WH": ["Karachi", "Hyderabad"],
    "LHE-WH": ["Lahore", "Faisalabad", "Multan"],
    "ISB-WH": ["Islamabad", "Rawalpindi", "Peshawar"],
}
CITY_TO_WH = {c: wh for wh, cs in WAREHOUSES.items() for c in cs}
CITY_WEIGHT = {"Karachi": 0.26, "Hyderabad": 0.07, "Lahore": 0.22, "Faisalabad": 0.10,
               "Multan": 0.08, "Islamabad": 0.10, "Rawalpindi": 0.10, "Peshawar": 0.07}

# sku, name, category, brand, pack, price_pkr (to retailer), cost_pkr, units_per_carton, popularity
PRODUCTS = [
    ("KD-OIL-001", "Sunfield Cooking Oil 1L", "Edible Oil & Ghee", "Sunfield", "1 L", 560, 505, 12, 1.6),
    ("KD-OIL-002", "Sunfield Cooking Oil 5L", "Edible Oil & Ghee", "Sunfield", "5 L", 2720, 2470, 4, 1.0),
    ("KD-OIL-003", "Sunfield Banaspati Ghee 1kg", "Edible Oil & Ghee", "Sunfield", "1 kg", 540, 490, 12, 1.3),
    ("KD-OIL-004", "Sunfield Canola Oil 3L", "Edible Oil & Ghee", "Sunfield", "3 L", 1780, 1610, 6, 0.6),
    ("KD-RIC-001", "Rivergrain Basmati Rice 5kg", "Rice & Flour", "Rivergrain", "5 kg", 2350, 2120, 4, 0.9),
    ("KD-RIC-002", "Rivergrain Sella Rice 1kg", "Rice & Flour", "Rivergrain", "1 kg", 420, 375, 20, 1.2),
    ("KD-RIC-003", "Rivergrain Chakki Atta 10kg", "Rice & Flour", "Rivergrain", "10 kg", 1450, 1340, 2, 1.1),
    ("KD-RIC-004", "Rivergrain Besan 500g", "Rice & Flour", "Rivergrain", "500 g", 210, 185, 24, 0.7),
    ("KD-TEA-001", "Highland Black Tea 190g", "Tea & Beverages", "Highland", "190 g", 520, 470, 36, 1.5),
    ("KD-TEA-002", "Highland Black Tea 450g", "Tea & Beverages", "Highland", "450 g", 1180, 1065, 24, 1.0),
    ("KD-TEA-003", "Highland Green Tea 30 bags", "Tea & Beverages", "Highland", "30 bags", 330, 290, 48, 0.5),
    ("KD-TEA-004", "Rosewater Syrup 800ml", "Tea & Beverages", "Highland", "800 ml", 470, 420, 12, 0.6),
    ("KD-JUI-001", "Fruitara Mango Nectar 1L", "Juices & Drinks", "Fruitara", "1 L", 330, 290, 12, 1.2),
    ("KD-JUI-002", "Fruitara Apple Juice 1L", "Juices & Drinks", "Fruitara", "1 L", 340, 300, 12, 0.7),
    ("KD-JUI-003", "Fruitara Mango Nectar 200ml", "Juices & Drinks", "Fruitara", "200 ml", 70, 60, 27, 1.6),
    ("KD-JUI-004", "Fizzo Cola 1.5L", "Juices & Drinks", "Fizzo", "1.5 L", 190, 165, 6, 1.4),
    ("KD-JUI-005", "Fizzo Lemon 500ml", "Juices & Drinks", "Fizzo", "500 ml", 95, 82, 12, 0.9),
    ("KD-SNK-001", "Crunchy Bites Cream Biscuit", "Biscuits & Snacks", "Crunchy Bites", "6 pack", 180, 155, 24, 1.5),
    ("KD-SNK-002", "Crunchy Bites Salted Crackers", "Biscuits & Snacks", "Crunchy Bites", "6 pack", 160, 138, 24, 1.1),
    ("KD-SNK-003", "Crunchy Bites Chocolate Cookies", "Biscuits & Snacks", "Crunchy Bites", "family", 260, 225, 18, 0.8),
    ("KD-SNK-004", "Nimko Mix 200g", "Biscuits & Snacks", "Crunchy Bites", "200 g", 150, 128, 30, 0.9),
    ("KD-SNK-005", "Potato Chips Masala 60g", "Biscuits & Snacks", "Crunchy Bites", "60 g", 70, 58, 48, 1.3),
    ("KD-HOM-001", "Brightwash Detergent 1kg", "Home Care", "Brightwash", "1 kg", 590, 525, 12, 1.2),
    ("KD-HOM-002", "Brightwash Detergent 3kg", "Home Care", "Brightwash", "3 kg", 1650, 1480, 4, 0.6),
    ("KD-HOM-003", "Brightwash Dishwash Bar", "Home Care", "Brightwash", "1 bar", 95, 80, 48, 1.3),
    ("KD-HOM-004", "Brightwash Floor Cleaner 1L", "Home Care", "Brightwash", "1 L", 380, 335, 12, 0.6),
    ("KD-PER-001", "Petal Beauty Soap 115g", "Personal Care", "Petal", "115 g", 135, 115, 72, 1.4),
    ("KD-PER-002", "Petal Shampoo 360ml", "Personal Care", "Petal", "360 ml", 690, 610, 12, 0.8),
    ("KD-PER-003", "Petal Toothpaste 150g", "Personal Care", "Petal", "150 g", 310, 270, 36, 1.0),
    ("KD-PER-004", "Petal Hand Wash 250ml", "Personal Care", "Petal", "250 ml", 290, 252, 24, 0.6),
    ("KD-DAI-001", "Meadow UHT Milk 1L", "Dairy", "Meadow", "1 L", 290, 262, 12, 1.5),
    ("KD-DAI-002", "Meadow UHT Milk 250ml", "Dairy", "Meadow", "250 ml", 85, 75, 27, 1.0),
    ("KD-DAI-003", "Meadow Tea Whitener 1L", "Dairy", "Meadow", "1 L", 300, 268, 12, 0.9),
    ("KD-DAI-004", "Meadow Yogurt 400g", "Dairy", "Meadow", "400 g", 180, 158, 12, 0.5),
]
DISCONTINUED_SKU = ("KD-SNK-099", "Crunchy Bites Jelly Cup (discontinued)", "Biscuits & Snacks",
                    "Crunchy Bites", "cup", 40, 33, 48, 0.0)

SHOP_WORDS_1 = ["Madina", "Al-Noor", "Rehman", "Bismillah", "Shaheen", "Faisal", "Hamza", "Usman",
                "Al-Habib", "Ghani", "Zam Zam", "Sadiq", "Karim", "Iqbal", "Royal", "City", "New",
                "Pak", "Star", "Crescent", "Green Valley", "Sunrise", "Moon", "Haji", "Ali"]
SHOP_WORDS_2 = {"Retailer": ["General Store", "Kiryana Store", "Karyana", "Super Store", "Mart"],
                "Wholesaler": ["Traders", "Wholesale", "Enterprises", "& Sons", "Trading Co."],
                "Modern Trade": ["Hypermart", "Superstore", "Cash & Carry", "Fresh Mart", "Mega Mart"]}
AREAS = {"Karachi": ["Saddar", "Gulshan", "Clifton", "North Nazimabad", "Korangi", "Malir", "Defence"],
         "Hyderabad": ["Latifabad", "Qasimabad", "Saddar"],
         "Lahore": ["Gulberg", "Johar Town", "Model Town", "Anarkali", "Iqbal Town", "DHA", "Shadman"],
         "Faisalabad": ["D-Ground", "Madina Town", "Peoples Colony"],
         "Multan": ["Cantt", "Gulgasht", "Bosan Road"],
         "Islamabad": ["F-7", "G-9", "I-8", "E-11", "Blue Area"],
         "Rawalpindi": ["Saddar", "Satellite Town", "Bahria Town", "Chaklala"],
         "Peshawar": ["University Town", "Hayatabad", "Saddar"]}
SP_FIRST = ["Imran", "Bilal", "Asad", "Kashif", "Farhan", "Naveed", "Waqas", "Adeel", "Shahid",
            "Tariq", "Junaid", "Hassan", "Zeeshan", "Umair", "Rizwan", "Saad", "Kamran", "Noman"]
SP_LAST = ["Ahmed", "Khan", "Malik", "Qureshi", "Sheikh", "Butt", "Siddiqui", "Raza", "Chaudhry", "Mirza"]

TYPE_MIX = {"Retailer": 0.70, "Wholesaler": 0.18, "Modern Trade": 0.12}
ORDER_PROB = {"Retailer": 0.085, "Wholesaler": 0.16, "Modern Trade": 0.15}   # per working day
QTY_MULT = {"Retailer": 1.0, "Wholesaler": 6.0, "Modern Trade": 3.5}
LINES = {"Retailer": (2, 6), "Wholesaler": (5, 12), "Modern Trade": (6, 14)}
DISCOUNT = {"Retailer": 0.0, "Wholesaler": 0.03, "Modern Trade": 0.02}

# Approximate calendar events (good enough for illustrative data)
RAMADAN = (date(2026, 2, 18), date(2026, 3, 19))
EID_FITR = date(2026, 3, 20)
EID_ADHA = date(2026, 5, 27)

# Planted signals (the "story" the demo should surface)
SLOWDOWN = {  # sku -> (city, start, multiplier)
    "KD-JUI-001": ("Karachi", date(2026, 9, 25), 0.40),
    "KD-HOM-001": ("Karachi", date(2026, 10, 1), 0.50),
}
UHT_GROWTH_CITIES = ["Islamabad", "Rawalpindi"]
UHT_GROWTH_START = date(2026, 6, 1)
UNDERPERFORMER = "SP-07"            # a Lahore order booker
UNDERPERF_START = date(2026, 7, 1)
CHURN_CITY, CHURN_N, CHURN_START = "Multan", 9, date(2026, 8, 1)
LOW_STOCK = ("LHE-WH", "KD-OIL-002", date(2026, 9, 21))   # supplier stops delivering from this date


def seasonal(cat: str, d: date) -> float:
    m = 1.0
    if RAMADAN[0] <= d <= RAMADAN[1]:
        m *= {"Edible Oil & Ghee": 1.45, "Rice & Flour": 1.4, "Tea & Beverages": 1.35,
              "Juices & Drinks": 1.3, "Dairy": 1.2}.get(cat, 1.0)
    if EID_FITR - timedelta(days=10) <= d < EID_FITR:
        m *= {"Personal Care": 1.35, "Biscuits & Snacks": 1.3}.get(cat, 1.0)
    if EID_ADHA - timedelta(days=7) <= d < EID_ADHA:
        m *= {"Edible Oil & Ghee": 1.25, "Rice & Flour": 1.2}.get(cat, 1.0)
    if d.month in (5, 6, 7, 8):
        m *= {"Juices & Drinks": 1.6, "Tea & Beverages": 0.85}.get(cat, 1.0)
    if d.month in (11, 12, 1, 2):
        m *= {"Tea & Beverages": 1.25, "Juices & Drinks": 0.75}.get(cat, 1.0)
    return m


def build_reference():
    products = pd.DataFrame(PRODUCTS, columns=["sku", "product_name", "category", "brand", "pack_size",
                                               "unit_price_pkr", "unit_cost_pkr", "units_per_carton",
                                               "popularity"])
    # salespeople: 2 per city, 3 in Karachi and Lahore
    sp_rows, n = [], 1
    for city in CITY_WEIGHT:
        for _ in range(3 if city in ("Karachi", "Lahore") else 2):
            sp_rows.append({"salesperson_id": f"SP-{n:02d}",
                            "name": f"{SP_FIRST[n % len(SP_FIRST)]} {SP_LAST[(n * 3) % len(SP_LAST)]}",
                            "city": city, "joined_on": str(date(2023, 1, 1) + timedelta(days=int(rng.integers(0, 800))))})
            n += 1
    salespeople = pd.DataFrame(sp_rows)
    assert salespeople.loc[salespeople.salesperson_id == UNDERPERFORMER, "city"].item() == "Lahore"

    cust_rows, used = [], set()
    n_cust = 360
    cities = rng.choice(list(CITY_WEIGHT), size=n_cust, p=list(CITY_WEIGHT.values()))
    types = rng.choice(list(TYPE_MIX), size=n_cust, p=list(TYPE_MIX.values()))
    for i, (city, ctype) in enumerate(zip(cities, types), start=1):
        while True:
            name = f"{random.choice(SHOP_WORDS_1)} {random.choice(SHOP_WORDS_2[ctype])}"
            if (name, city) not in used:
                used.add((name, city)); break
        sps = salespeople.loc[salespeople.city == city, "salesperson_id"].tolist()
        cust_rows.append({"customer_id": f"C{i:04d}", "customer_name": name, "customer_type": ctype,
                          "city": city, "area": random.choice(AREAS[city]),
                          "salesperson_id": sps[i % len(sps)],
                          "credit_days": {"Retailer": 7, "Wholesaler": 30, "Modern Trade": 45}[ctype],
                          "created_on": START - timedelta(days=int(rng.integers(30, 1500))),
                          "size_factor": float(rng.lognormal(0, 0.35))})
    customers = pd.DataFrame(cust_rows)
    # new modern-trade outlets in Islamabad/Rawalpindi from June 2026 (drives UHT growth)
    extra = []
    for k in range(6):
        city = UHT_GROWTH_CITIES[k % 2]
        sps = salespeople.loc[salespeople.city == city, "salesperson_id"].tolist()
        extra.append({"customer_id": f"C{n_cust + k + 1:04d}",
                      "customer_name": f"FreshCart {['Express', 'Hypermart', 'Fresh Mart'][k % 3]} {random.choice(AREAS[city])}",
                      "customer_type": "Modern Trade", "city": city, "area": random.choice(AREAS[city]),
                      "salesperson_id": sps[k % len(sps)], "credit_days": 45,
                      "created_on": UHT_GROWTH_START + timedelta(days=int(rng.integers(0, 40))),
                      "size_factor": 1.3})
    customers = pd.concat([customers, pd.DataFrame(extra)], ignore_index=True)
    churned = customers[(customers.city == CHURN_CITY) & (customers.customer_type == "Retailer")] \
        .sample(CHURN_N, random_state=SEED).customer_id.tolist()
    return products, salespeople, customers, churned


def simulate_sales(products, customers, churned):
    prod = products.set_index("sku")
    skus = products.sku.to_numpy()
    base_pop = products.popularity.to_numpy()
    cats = products.category.to_numpy()
    days = pd.date_range(START, END, freq="D").date
    inv_rows, line_rows, inv_no = [], [], 100000
    for d in days:
        dow = d.weekday()
        day_mult = 0.12 if dow == 6 else (0.8 if dow == 4 else 1.0)    # Sunday mostly off, Friday lighter
        season = np.array([seasonal(c, d) for c in cats])
        for c in customers.itertuples(index=False):
            if c.created_on > d:
                continue
            if c.customer_id in churned and d >= CHURN_START:
                continue
            p = ORDER_PROB[c.customer_type] * day_mult
            if c.salesperson_id == UNDERPERFORMER and d >= UNDERPERF_START:
                p *= 0.55
            if rng.random() >= p:
                continue
            weights = base_pop * season
            for sku, (city, start, mult) in SLOWDOWN.items():
                if c.city == city and d >= start:
                    weights = weights * np.where(skus == sku, mult, 1.0)
            if c.city in UHT_GROWTH_CITIES and d >= UHT_GROWTH_START:
                months_in = (d.year - UHT_GROWTH_START.year) * 12 + d.month - UHT_GROWTH_START.month
                weights = weights * np.where(np.char.startswith(skus.astype(str), "KD-DAI-00") & (skus != "KD-DAI-004"),
                                             1.25 + 0.15 * months_in, 1.0)
            lo, hi = LINES[c.customer_type]
            k = int(rng.integers(lo, hi + 1))
            chosen = rng.choice(len(skus), size=min(k, len(skus)), replace=False, p=weights / weights.sum())
            inv_no += 1
            inv_id = f"INV-{inv_no}"
            inv_rows.append({"invoice_id": inv_id, "invoice_date": d, "customer_id": c.customer_id,
                             "salesperson_id": c.salesperson_id, "doc_type": "INV"})
            # A bigger basket weight raises quantity; seasonality and slowdowns also shift quantity
            for line_no, j in enumerate(chosen, start=1):
                sku = skus[j]
                upc = prod.at[sku, "units_per_carton"]
                lam = max(0.3, QTY_MULT[c.customer_type] * c.size_factor * season[j] * 0.9)
                for s, (city, start, mult) in SLOWDOWN.items():
                    if s == sku and c.city == city and d >= start:
                        lam *= mult
                cartons = rng.poisson(lam)
                qty = int(cartons * upc + (rng.integers(1, upc) if cartons == 0 or rng.random() < 0.3 else 0))
                line_rows.append({"invoice_id": inv_id, "line_no": line_no, "sku": sku, "quantity": qty,
                                  "unit_price_pkr": float(prod.at[sku, "unit_price_pkr"]),
                                  "discount_pct": DISCOUNT[c.customer_type]})
            # discontinued SKU still sold off in early months (not in product master later)
            if d < date(2025, 10, 1) and rng.random() < 0.02:
                line_rows.append({"invoice_id": inv_id, "line_no": len(chosen) + 1, "sku": DISCONTINUED_SKU[0],
                                  "quantity": int(rng.integers(12, 96)), "unit_price_pkr": float(DISCONTINUED_SKU[5]),
                                  "discount_pct": DISCOUNT[c.customer_type]})
    invoices = pd.DataFrame(inv_rows)
    lines = pd.DataFrame(line_rows)

    # returns: ~1.5% of invoices get a partial return a few days later
    ret_inv, ret_lines = [], []
    sample = invoices.sample(frac=0.015, random_state=SEED)
    for r in sample.itertuples(index=False):
        rd = r.invoice_date + timedelta(days=int(rng.integers(2, 10)))
        if rd > END:
            continue
        src = lines[lines.invoice_id == r.invoice_id].sample(1, random_state=int(rng.integers(0, 1e6))).iloc[0]
        inv_no += 1
        rid = f"RET-{inv_no}"
        ret_inv.append({"invoice_id": rid, "invoice_date": rd, "customer_id": r.customer_id,
                        "salesperson_id": r.salesperson_id, "doc_type": "RET"})
        ret_lines.append({"invoice_id": rid, "line_no": 1, "sku": src.sku,
                          "quantity": -max(1, int(src.quantity * rng.uniform(0.1, 0.5))),
                          "unit_price_pkr": src.unit_price_pkr, "discount_pct": src.discount_pct})
    invoices = pd.concat([invoices, pd.DataFrame(ret_inv)], ignore_index=True)
    lines = pd.concat([lines, pd.DataFrame(ret_lines)], ignore_index=True)
    lines["net_amount_pkr"] = (lines.quantity * lines.unit_price_pkr * (1 - lines.discount_pct)).round(2)
    return invoices, lines


def simulate_inventory(products, invoices, lines, customers):
    """Daily stock per warehouse x SKU; weekly receipts (order-up-to 28 days cover)."""
    df = lines.merge(invoices[["invoice_id", "invoice_date", "customer_id"]], on="invoice_id") \
              .merge(customers[["customer_id", "city"]], on="customer_id")
    df["warehouse"] = df.city.map(CITY_TO_WH)
    daily = df.groupby(["warehouse", "sku", "invoice_date"]).quantity.sum()
    days = pd.date_range(START, END, freq="D").date
    receipts, snaps = [], []
    grn = 5000
    for wh in WAREHOUSES:
        for sku in list(products.sku) + [DISCONTINUED_SKU[0]]:
            try:
                s = daily.loc[(wh, sku)].reindex(days, fill_value=0)
            except KeyError:
                s = pd.Series(0, index=days)
            avg = max(1.0, s.iloc[:28].mean())
            stock = int(avg * 21) + 50
            if sku == DISCONTINUED_SKU[0]:                            # old stock being sold off
                stock = int(s.sum()) + 40
            for i, d in enumerate(days):
                if d.weekday() == 0 and sku != DISCONTINUED_SKU[0]:   # Monday receipt
                    trailing = max(s.iloc[max(0, i - 28):i].mean(), s.iloc[max(0, i - 7):i].mean()) if i else avg
                    need = int(max(0, trailing * 35 - stock))
                    if (wh, sku) == LOW_STOCK[:2] and d >= LOW_STOCK[2]:
                        need = 0                                      # supplier stopped delivering
                    if need > 0:
                        grn += 1
                        receipts.append({"grn_no": f"GRN-{grn}", "receipt_date": d, "warehouse": wh,
                                         "sku": sku, "qty_received": need, "supplier": f"{products.set_index('sku').brand.get(sku, 'Unknown')} Pvt Ltd (fictional)"})
                        stock += need
                stock -= int(s.iloc[i])
                if d.weekday() == 6:                                   # Sunday week-end snapshot
                    snaps.append({"week_ending": d, "warehouse": wh, "sku": sku, "closing_qty": stock})
    snaps = pd.DataFrame(snaps)
    assert (snaps.closing_qty >= 0).all(), snaps[snaps.closing_qty < 0].head()
    return pd.DataFrame(receipts), snaps


def build_targets(invoices, lines, salespeople):
    df = lines.merge(invoices[["invoice_id", "invoice_date", "salesperson_id"]], on="invoice_id")
    df["month"] = pd.to_datetime(df.invoice_date).dt.to_period("M")
    act = df.groupby(["salesperson_id", "month"]).net_amount_pkr.sum().unstack(fill_value=0)
    rows = []
    for sp in salespeople.salesperson_id:
        series = act.loc[sp]
        for idx, m in enumerate(series.index):
            if idx < 3:
                base = series.iloc[idx] * rng.uniform(1.0, 1.1)
            elif sp == UNDERPERFORMER and m >= pd.Period(UNDERPERF_START, "M"):
                base = series.loc[pd.Period("2026-04", "M"):pd.Period("2026-06", "M")].mean() * 1.05  # target not lowered
            else:
                base = series.iloc[idx - 3:idx].mean() * 1.08
            rows.append({"salesperson_id": sp, "month": str(m), "target_pkr": int(round(base, -4))})
    return pd.DataFrame(rows)


def build_visits(invoices, customers):
    rows, vid = [], 700000
    inv = invoices[invoices.doc_type == "INV"]
    for r in inv.itertuples(index=False):
        vid += 1
        local = datetime.combine(r.invoice_date, datetime.min.time()) + timedelta(hours=int(rng.integers(9, 19)), minutes=int(rng.integers(0, 60)))
        rows.append({"visit_id": f"V{vid}", "salesperson_id": r.salesperson_id, "customer_id": r.customer_id,
                     "visited_at_utc": (local - timedelta(hours=5)).replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
                     "outcome": "order", "order_ref": r.invoice_id})
    # no-order visits (about 1 per 2.5 orders)
    n_extra = int(len(inv) / 2.5)
    pick = customers.sample(n_extra, replace=True, random_state=SEED)
    dts = rng.integers(0, (END - START).days + 1, n_extra)
    for c, off in zip(pick.itertuples(index=False), dts):
        d = START + timedelta(days=int(off))
        if d.weekday() == 6 or c.created_on > d:
            continue
        vid += 1
        local = datetime.combine(d, datetime.min.time()) + timedelta(hours=int(rng.integers(9, 21)), minutes=int(rng.integers(0, 60)))
        rows.append({"visit_id": f"V{vid}", "salesperson_id": c.salesperson_id, "customer_id": c.customer_id,
                     "visited_at_utc": (local - timedelta(hours=5)).replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
                     "outcome": rng.choice(["no_order", "shop_closed", "owner_absent"], p=[0.7, 0.15, 0.15]),
                     "order_ref": None})
    v = pd.DataFrame(rows).sort_values("visited_at_utc").reset_index(drop=True)
    return v


# --------------------------------------------------------------------------- #
# Messy exports (deliberate data-quality issues, all counted in the answer key)
# --------------------------------------------------------------------------- #
def write_erp(products, customers, invoices, lines, issues):
    out = RAW / "erp"; out.mkdir(parents=True, exist_ok=True)
    products.drop(columns="popularity").assign(is_active="Y").to_csv(out / "products.csv", index=False)

    cust = customers.drop(columns=["size_factor"]).copy()
    variants = {"Karachi": ["KHI", "karachi ", "Krachi"], "Rawalpindi": ["Pindi", "rawalpindi"],
                "Islamabad": ["ISB", "Islamabad "], "Lahore": ["LHR", "lahore"], "Faisalabad": ["Fsd"]}
    idx = cust[cust.city.isin(variants)].sample(frac=0.12, random_state=SEED).index
    for i in idx:
        cust.at[i, "city"] = random.choice(variants[cust.at[i, "city"]])
    issues["customers_city_misspelt"] = len(idx)
    miss = cust.sample(frac=0.03, random_state=SEED + 1).index
    cust.loc[miss, "salesperson_id"] = ""
    issues["customers_missing_salesperson"] = len(miss)
    cust["created_on"] = pd.to_datetime(cust.created_on).dt.strftime("%d/%m/%Y")
    cust.to_csv(out / "customers.csv", index=False)

    tot = lines.groupby("invoice_id").net_amount_pkr.sum().round(2)
    hdr = invoices.copy()
    hdr["total_amount_pkr"] = hdr.invoice_id.map(tot)
    bad = hdr.sample(frac=0.005, random_state=SEED + 2).index           # manual header edits
    hdr.loc[bad, "total_amount_pkr"] = (hdr.loc[bad, "total_amount_pkr"] * rng.uniform(0.9, 0.98, len(bad))).round(-1)
    issues["invoice_header_total_mismatch"] = len(bad)
    hdr["total_amount_pkr"] = hdr.total_amount_pkr.map(lambda x: f"{x:,.2f}")   # "12,345.00" as text
    hdr["invoice_date"] = pd.to_datetime(hdr.invoice_date).dt.strftime("%d/%m/%Y")
    hdr.drop(columns=[]).to_csv(out / "sales_invoices.csv", index=False)

    ln = lines.drop(columns=["net_amount_pkr"]).copy()
    messy = ln.sample(frac=0.01, random_state=SEED + 3).index
    ln.loc[messy, "sku"] = ln.loc[messy, "sku"].str.lower() + " "
    issues["invoice_lines_sku_bad_case_or_space"] = len(messy)
    dup = ln.sample(frac=0.004, random_state=SEED + 4)
    ln = pd.concat([ln, dup]).sort_values(["invoice_id", "line_no"], kind="stable")
    issues["invoice_lines_exact_duplicates"] = len(dup)
    issues["invoice_lines_unknown_sku"] = int((lines.sku == DISCONTINUED_SKU[0]).sum())
    ln.to_csv(out / "sales_invoice_lines.csv", index=False)


def write_inventory(products, receipts, snaps, issues):
    out = RAW / "inventory"; out.mkdir(parents=True, exist_ok=True)
    names = products.set_index("sku").product_name.to_dict()
    names[DISCONTINUED_SKU[0]] = DISCONTINUED_SKU[1]
    path = out / "weekly_stock_report.xlsx"
    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        nodash = 0
        for wh in WAREHOUSES:
            s = snaps[snaps.warehouse == wh].copy()
            if wh == "ISB-WH":                       # this warehouse's sheet uses codes without dashes
                s["sku"] = s.sku.str.replace("-", "", regex=False); nodash = len(s)
            s = s.assign(item_description=s.sku.map(lambda k: names.get(k, names.get(k[:2] + "-" + k[2:5] + "-" + k[5:], ""))))
            s = s.rename(columns={"week_ending": "Week Ending", "sku": "Item Code",
                                  "item_description": "Item Description", "closing_qty": "Closing Qty"})
            s = s[["Week Ending", "Item Code", "Item Description", "Closing Qty"]]
            # 3 title rows above the real header, like a typical exported Excel report
            pd.DataFrame([[f"Kestrel Distributors (fictional) - Stock Report - {wh}"], ["Generated by WMS v2.1"], [""]]) \
                .to_excel(xw, sheet_name=wh, index=False, header=False)
            s.to_excel(xw, sheet_name=wh, index=False, startrow=3)
        r = receipts.rename(columns={"grn_no": "GRN No", "receipt_date": "Receipt Date", "warehouse": "Warehouse",
                                     "sku": "Item Code", "qty_received": "Qty Received", "supplier": "Supplier"})
        r.to_excel(xw, sheet_name="Goods Receipts", index=False)
    issues["stock_rows_sku_without_dashes_ISB"] = nodash
    issues["stock_sheets_with_title_rows"] = len(WAREHOUSES)


def write_field_app(salespeople, targets, visits, issues):
    out = RAW / "field_app"; out.mkdir(parents=True, exist_ok=True)
    (out / "salespeople.json").write_text(json.dumps({"data": salespeople.to_dict("records"), "exported_at": "2026-10-23T22:00:00Z"}, indent=1))
    (out / "monthly_targets.json").write_text(json.dumps({"data": targets.to_dict("records")}, indent=1))
    dup = visits.sample(frac=0.006, random_state=SEED + 5)            # app sync retries
    v = pd.concat([visits, dup]).sort_values("visited_at_utc", kind="stable")
    with open(out / "visits.jsonl", "w") as f:
        for rec in v.to_dict("records"):
            f.write(json.dumps({k: (None if (isinstance(x, float) and np.isnan(x)) else x) for k, x in rec.items()}) + "\n")
    issues["visits_duplicate_visit_id"] = len(dup)
    issues["visits_timestamps_in_utc_not_pkt"] = "all"


# --------------------------------------------------------------------------- #
# Answer key (from clean truth)
# --------------------------------------------------------------------------- #
def answer_key(products, customers, invoices, lines, snaps, targets, churned, issues):
    df = lines.merge(invoices[["invoice_id", "invoice_date", "customer_id", "salesperson_id", "doc_type"]], on="invoice_id") \
              .merge(customers[["customer_id", "city"]], on="customer_id") \
              .merge(products[["sku", "product_name", "category"]], on="sku", how="left")
    df["month"] = pd.to_datetime(df.invoice_date).dt.to_period("M").astype(str)
    monthly = df.groupby("month").net_amount_pkr.sum().round(0)

    def sku_city(sku, city):
        x = df[(df.sku == sku) & (df.city == city) & (df.doc_type == "INV")]
        g = x.groupby("month").quantity.sum()
        return {m: int(g.get(m, 0)) for m in ["2026-07", "2026-08", "2026-09", "2026-10"]}

    # month-to-date (1-23 Oct) vs same days in Jul-Sep, per city, to show the Karachi drop is local
    def mtd_index(sku):
        out = {}
        for city in CITY_WEIGHT:
            x = df[(df.sku == sku) & (df.city == city) & (df.doc_type == "INV")]
            dd = pd.to_datetime(x.invoice_date)
            oct_ = x[(dd >= "2026-10-01") & (dd <= "2026-10-23")].quantity.sum()
            prior = np.mean([x[(dd >= f"2026-{m:02d}-01") & (dd <= f"2026-{m:02d}-23")].quantity.sum() for m in (7, 8, 9)])
            out[city] = round(float(oct_ / prior), 2) if prior else None
        return out

    def karachi_relative_ranking():
        """Daily rate 1-23 Oct vs Jul-Sep, Karachi divided by rest of country (removes seasonality)."""
        x = df[df.doc_type == "INV"].copy()
        x["d"] = pd.to_datetime(x.invoice_date)
        x["khi"] = x.city == "Karachi"
        cur = x[(x.d >= "2026-10-01") & (x.d <= "2026-10-23")].groupby(["sku", "khi"]).quantity.sum() / 23
        base = x[(x.d >= "2026-07-01") & (x.d <= "2026-09-30")].groupby(["sku", "khi"]).quantity.sum() / 92
        r = (cur / base).unstack()
        rel = (r[True] / r[False]).dropna().sort_values().round(2)
        return {k: float(v) for k, v in rel.head(5).items()}

    sp = df.groupby(["salesperson_id", "month"]).net_amount_pkr.sum().reset_index() \
           .merge(targets, on=["salesperson_id", "month"])
    sp["attainment"] = (sp.net_amount_pkr / sp.target_pkr).round(2)
    under = sp[(sp.salesperson_id == UNDERPERFORMER) & (sp.month >= "2026-07")][["month", "net_amount_pkr", "target_pkr", "attainment"]]

    last = snaps.week_ending.max()
    ls = snaps[(snaps.week_ending == last) & (snaps.warehouse == LOW_STOCK[0]) & (snaps.sku == LOW_STOCK[1])].closing_qty.item()
    wh_lines = df[df.city.isin(WAREHOUSES[LOW_STOCK[0]]) & (df.sku == LOW_STOCK[1])]
    dd = pd.to_datetime(wh_lines.invoice_date)
    per_day = wh_lines[(dd > pd.Timestamp(last) - pd.Timedelta(days=28)) & (dd <= pd.Timestamp(last))].quantity.sum() / 28

    uht = df[df.city.isin(UHT_GROWTH_CITIES) & df.sku.isin(["KD-DAI-001", "KD-DAI-002"])].groupby("month").quantity.sum()

    key = {
        "_note": "Computed from the clean truth data BEFORE data-quality issues were added. All data is fictional.",
        "period": {"start": str(START), "end": str(END)},
        "row_counts_clean": {"products": len(products), "customers": len(customers),
                             "invoices_and_returns": len(invoices), "invoice_lines": len(lines)},
        "net_sales_pkr_total": round(float(lines.net_amount_pkr.sum()), 2),
        "net_sales_pkr_by_month": {k: float(v) for k, v in monthly.items()},
        "returns_pkr_total": round(float(df[df.doc_type == "RET"].net_amount_pkr.sum()), 2),
        "planted_signals": {
            "1_karachi_slowdown": {
                "question": "Which products are slowing down in Karachi this month?",
                "expected_answer": ["KD-JUI-001 Fruitara Mango Nectar 1L", "KD-HOM-001 Brightwash Detergent 1kg"],
                "units_by_month_karachi": {"KD-JUI-001": sku_city("KD-JUI-001", "Karachi"),
                                           "KD-HOM-001": sku_city("KD-HOM-001", "Karachi")},
                "oct_1_23_vs_avg_jul_sep_same_days_by_city": {"KD-JUI-001": mtd_index("KD-JUI-001"),
                                                              "KD-HOM-001": mtd_index("KD-HOM-001")},
                "seasonality_adjusted_bottom5_karachi": karachi_relative_ranking(),
                "method": "Karachi daily-rate change (1-23 Oct vs Jul-Sep) divided by rest-of-country change; 1.0 = same trend as the rest of the country",
            },
            "2_salesperson_below_target": {
                "question": "Which salesperson has been below 85% of target three months running?",
                "expected_answer": UNDERPERFORMER,
                "monthly": under.to_dict("records"),
                "note": "October is month-to-date (to 23 Oct) against a full-month target. Other order bookers sit just under 100% some months (targets are set at +8%); only this one is below 85%.",
            },
            "3_low_stock": {
                "question": "Which items are about to run out?",
                "expected_answer": f"{LOW_STOCK[1]} at {LOW_STOCK[0]}",
                "snapshot_week_ending": str(last), "closing_qty": int(ls),
                "avg_units_per_day_last_28d": round(float(per_day), 1),
                "days_of_cover": round(float(ls / per_day), 1) if per_day else None,
            },
            "4_uht_growth_islamabad_rawalpindi": {
                "question": "Where is UHT milk growing?",
                "expected_answer": "Islamabad and Rawalpindi, stepping up from July 2026 (new modern-trade outlets opened June-July)",
                "units_by_month": {k: int(v) for k, v in uht.items() if k >= "2026-03"},
            },
            "5_churned_customers": {
                "question": "Which customers stopped ordering?",
                "expected_answer": f"{len(churned)} {CHURN_CITY} retailers, no orders since {CHURN_START}",
                "customer_ids": sorted(churned),
            },
        },
        "data_quality_issues_planted": issues,
    }
    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "data" / "answer_key.json").write_text(json.dumps(key, indent=2, default=str))
    return key


def main():
    issues: dict = {}
    products, salespeople, customers, churned = build_reference()
    invoices, lines = simulate_sales(products, customers, churned)
    receipts, snaps = simulate_inventory(products, invoices, lines, customers)
    targets = build_targets(invoices, lines, salespeople)
    visits = build_visits(invoices, customers)
    write_erp(products, customers, invoices, lines, issues)
    write_inventory(products, receipts, snaps, issues)
    write_field_app(salespeople, targets, visits, issues)
    key = answer_key(products, customers, invoices, lines, snaps, targets, churned, issues)
    print(json.dumps({k: key[k] for k in ("row_counts_clean", "net_sales_pkr_total")}, indent=2))


if __name__ == "__main__":
    main()
