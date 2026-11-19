"""QUANTORA UrbanKart CSV cleaning and analytics engine.

Allowed dependencies: pandas, numpy and Python standard library.
All metrics are calculated from the uploaded CSV; source SALES is ignored.
"""

import re
import numpy as np
import pandas as pd


CITY_REGION = {
    "Delhi": "North", "Jaipur": "North", "Lucknow": "North",
    "Bengaluru": "South", "Chennai": "South", "Hyderabad": "South", "Kochi": "South",
    "Kolkata": "East", "Bhubaneswar": "East", "Guwahati": "East",
    "Mumbai": "West", "Pune": "West", "Ahmedabad": "West",
}

CITY_ALIASES = {
    "delhi": "Delhi", "new delhi": "Delhi", "n delhi": "Delhi", "n. delhi": "Delhi", "delhi ncr": "Delhi",
    "jaipur": "Jaipur", "lucknow": "Lucknow", "lko": "Lucknow",
    "bengaluru": "Bengaluru", "bangalore": "Bengaluru", "blr": "Bengaluru", "b'lore": "Bengaluru", "b lore": "Bengaluru",
    "chennai": "Chennai", "madras": "Chennai",
    "hyderabad": "Hyderabad", "hyd": "Hyderabad",
    "kochi": "Kochi", "cochin": "Kochi", "ernakulam": "Kochi",
    "kolkata": "Kolkata", "calcutta": "Kolkata", "kolkatta": "Kolkata",
    "bhubaneswar": "Bhubaneswar", "bhubaneshwar": "Bhubaneswar", "bbsr": "Bhubaneswar",
    "guwahati": "Guwahati", "gauhati": "Guwahati",
    "mumbai": "Mumbai", "bombay": "Mumbai", "bom": "Mumbai",
    "pune": "Pune", "poona": "Pune",
    "ahmedabad": "Ahmedabad", "ahmadabad": "Ahmedabad", "amdavad": "Ahmedabad",
}

WORD_NUMBERS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
}

HEADER_ALIASES = {
    "orderid": ["orderid", "order id", "order number", "orderno", "order no"],
    "orderdate": ["orderdate", "order date", "date", "order_date"],
    "quantity": ["quantity", "qty", "units", "order quantity"],
    "unitprice": ["unitprice", "unit price", "price", "unit cost", "selling price"],
    "discount": ["discount", "discount percent", "discountpercent", "discount %"],
    "profit": ["profit", "net profit"],
    "orderstatus": ["orderstatus", "order status", "status"],
    "city": ["city", "town"],
}


def _header_key(value):
    return re.sub(r"[^a-z0-9]", "", str(value).strip().lower())


def standardize_headers(frame):
    df = frame.copy()
    normalized = {_header_key(col): col for col in df.columns}
    rename = {}
    for canonical, aliases in HEADER_ALIASES.items():
        for alias in aliases:
            key = _header_key(alias)
            if key in normalized:
                rename[normalized[key]] = canonical
                break
    df = df.rename(columns=rename)
    required = ["orderid", "orderdate", "quantity", "unitprice", "discount", "orderstatus", "city"]
    missing = [name for name in required if name not in df.columns]
    if missing:
        raise ValueError("Required columns not found: " + ", ".join(missing))
    # A missing Profit column is allowed; profit is optional for margin calculations.
    if "profit" not in df.columns:
        df["profit"] = np.nan
    return df


def _is_missing(value):
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except (TypeError, ValueError):
        pass
    return str(value).strip().lower() in {"", "nan", "none", "null", "na", "n/a", "nat"}


def parse_number(value):
    """Parse numeric/currency strings including 'Rs. 3,459', '₹1,200/-', '(250)' ."""
    if _is_missing(value):
        return np.nan
    if isinstance(value, (int, float, np.integer, np.floating)):
        return float(value)

    text = str(value).strip()
    if text.lower() in {"-", "—", "–", "missing"}:
        return np.nan

    is_parentheses_negative = text.startswith("(") and text.endswith(")")
    if is_parentheses_negative:
        text = text[1:-1].strip()

    # Remove currency tokens BEFORE stripping punctuation, so 'Rs. 3,459' stays 3459.
    text = re.sub(r"(?i)\b(?:inr|rs\.?|rupees?)\s*", "", text)
    text = text.replace("₹", "")
    text = re.sub(r"(?i)\s*(?:inr|rs\.?|rupees?)\s*", "", text)
    text = text.replace(",", "")
    text = re.sub(r"/\-\s*$", "", text)
    text = re.sub(r"[^0-9.\-+]", "", text)

    if text in {"", "-", "+", ".", "-.", "+."}:
        return np.nan
    try:
        number = float(text)
        return -abs(number) if is_parentheses_negative else number
    except ValueError:
        return np.nan


def parse_quantity(value):
    if _is_missing(value):
        return np.nan
    text = str(value).strip().lower()
    if text in WORD_NUMBERS:
        return float(WORD_NUMBERS[text])
    match = re.fullmatch(r"\s*(\d+)\s*(?:pcs?|units?|nos?)?\s*", text)
    return float(match.group(1)) if match else np.nan


def parse_discount(value):
    if _is_missing(value) or str(value).strip().lower() in {"no discount", "no-discount", "nil", "none", "-"}:
        return 0.0
    text = str(value).strip()
    percent_marked = "%" in text
    number = parse_number(text)
    if pd.isna(number):
        return np.nan
    if percent_marked or number > 1:
        number /= 100.0
    return float(number)


def parse_order_date(value):
    """Parse supported date forms without swapping day/month for slash or dot dates."""
    if _is_missing(value):
        return pd.NaT

    if isinstance(value, (int, float, np.integer, np.floating)):
        number = float(value)
        if 20000 <= number <= 80000:  # Excel serial date
            return pd.Timestamp("1899-12-30") + pd.to_timedelta(number, unit="D")
        if number.is_integer() and 19000101 <= number <= 21001231:
            return pd.to_datetime(str(int(number)), format="%Y%m%d", errors="coerce")
        return pd.NaT

    text = str(value).strip()

    # YYYYMMDD, often imported as a numeric-looking string.
    if re.fullmatch(r"\d{8}", text):
        return pd.to_datetime(text, format="%Y%m%d", errors="coerce")

    # Slash/dot date formats are DD/MM/YYYY or DD.MM.YYYY.
    if re.fullmatch(r"\d{1,2}[/.]\d{1,2}[/.]\d{4}", text):
        return pd.to_datetime(text.replace(".", "/"), format="%d/%m/%Y", errors="coerce")

    # ISO and year-first formats.
    if re.fullmatch(r"\d{4}[-/]\d{1,2}[-/]\d{1,2}(?:[ T].*)?", text):
        parsed = pd.to_datetime(text, yearfirst=True, errors="coerce")
        if not pd.isna(parsed):
            return parsed

    # Excel serial date stored as text.
    if re.fullmatch(r"\d{4,5}(?:\.0+)?", text):
        number = float(text)
        if 20000 <= number <= 80000:
            return pd.Timestamp("1899-12-30") + pd.to_timedelta(number, unit="D")

    for fmt in (
        "%d-%b-%Y", "%d-%B-%Y", "%B %d, %Y", "%b %d, %Y",
        "%d %b %Y", "%d %B %Y", "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
    ):
        parsed = pd.to_datetime(text, format=fmt, errors="coerce")
        if not pd.isna(parsed):
            return parsed

    return pd.to_datetime(text, errors="coerce", dayfirst=True)


def standardize_city(value):
    if _is_missing(value):
        return np.nan
    key = re.sub(r"\s+", " ", str(value).strip().lower())
    key = re.sub(r"\s*,\s*(ka|mh|ts|tn|dl|rj|up|wb|od|as|gj)$", "", key)
    return CITY_ALIASES.get(key, np.nan)


def _status_is_cancelled(value):
    if _is_missing(value):
        return False
    normalized = re.sub(r"[^a-z]", "", str(value).lower())
    return normalized in {"cancelled", "canceled", "cancel", "cxl"} or normalized.startswith("cancel")


def clean_urbankart(raw_df):
    if raw_df is None or not isinstance(raw_df, pd.DataFrame):
        raise ValueError("Please upload a valid CSV dataset.")
    if raw_df.empty:
        raise ValueError("The uploaded CSV is empty.")

    raw = raw_df.copy()
    raw_rows = len(raw)
    missing_before = {str(col): int(raw[col].apply(_is_missing).sum()) for col in raw.columns}
    df = standardize_headers(raw)

    # Validate IDs case/space-insensitively and retain the first occurrence.
    id_text = df["orderid"].fillna("").astype(str).str.upper()
    id_key = id_text.str.replace(r"\s+", "", regex=True)
    valid_id = id_key.str.fullmatch(r"UK-\d{4}-\d{6}")
    junk_rows = int((~valid_id).sum())
    df = df.loc[valid_id].copy()
    df["_order_key"] = id_key.loc[valid_id]
    before_dedup = len(df)
    df = df.drop_duplicates(subset="_order_key", keep="first").copy()
    duplicate_orders = before_dedup - len(df)

    df["_date"] = df["orderdate"].apply(parse_order_date)
    df["_quantity"] = df["quantity"].apply(parse_quantity)
    df["_unit_price"] = df["unitprice"].apply(parse_number)
    df["_discount"] = df["discount"].apply(parse_discount)
    df["_profit"] = df["profit"].apply(parse_number)

    valid_rows = (
        df["_date"].notna()
        & df["_quantity"].between(1, 50, inclusive="both")
        & df["_unit_price"].notna()
        & (df["_unit_price"] > 0)
    )
    invalid_rows = int((~valid_rows).sum())
    df = df.loc[valid_rows].copy()

    # Keep these column names for compatibility with the QUANTORA dashboard.
    df["order_id_clean"] = df["_order_key"]
    df["order_date_clean"] = df["_date"]
    df["quantity_clean"] = df["_quantity"]
    df["unit_price_clean"] = df["_unit_price"]
    df["discount_clean"] = df["_discount"].fillna(0.0)
    df["profit_clean"] = df["_profit"]
    df["order_status_clean"] = df["orderstatus"].astype(str).str.strip()
    df["city_clean"] = df["city"].apply(standardize_city)
    df["region_clean"] = df["city_clean"].map(CITY_REGION)
    df["net_sales"] = df["quantity_clean"] * df["unit_price_clean"] * (1.0 - df["discount_clean"])
    df["month_period"] = df["order_date_clean"].dt.to_period("M")
    df["month_start"] = df["month_period"].dt.to_timestamp()
    df["_cancelled"] = df["orderstatus"].apply(_status_is_cancelled)

    report = {
        "raw_rows": int(raw_rows),
        "junk_rows_removed": int(junk_rows),
        "duplicate_orders_removed": int(duplicate_orders),
        "invalid_rows_removed": int(invalid_rows),
        "clean_rows": int(len(df)),
        "missing_before": missing_before,
    }
    return df, report


def _margin(profit, revenue):
    if pd.isna(revenue) or revenue == 0:
        return np.nan
    return float(profit / revenue * 100.0)


def calculate_business_results(clean_df):
    if clean_df is None or clean_df.empty:
        raise ValueError("No valid cleaned records are available for analysis.")

    # Cancelled orders are excluded from all business KPIs.
    active = clean_df.loc[~clean_df["_cancelled"]].copy()
    if active.empty:
        raise ValueError("No active orders remain after excluding cancelled orders.")

    net_revenue = float(active["net_sales"].sum())
    known_profit = active.loc[active["profit_clean"].notna()].copy()
    total_profit = float(known_profit["profit_clean"].sum()) if not known_profit.empty else np.nan
    profit_margin = _margin(known_profit["profit_clean"].sum(), known_profit["net_sales"].sum()) if not known_profit.empty else np.nan
    order_count = int(active["order_id_clean"].nunique())
    average_order_value = net_revenue / order_count if order_count else np.nan

    monthly = active.groupby("month_start", dropna=True)["net_sales"].sum().sort_index()
    monthly_trend = [
        {"month": month.strftime("%b %Y"), "net_revenue": float(revenue)}
        for month, revenue in monthly.items()
    ]
    best_month = monthly.idxmax().strftime("%B %Y") if not monthly.empty else "N/A"
    worst_month = monthly.idxmin().strftime("%B %Y") if not monthly.empty else "N/A"
    worst_month_revenue = float(monthly.min()) if not monthly.empty else np.nan

    city_sales = active.dropna(subset=["city_clean"]).groupby("city_clean")["net_sales"].sum().sort_values(ascending=False)
    top_5_cities = [
        {"city": str(city), "net_revenue": float(revenue)}
        for city, revenue in city_sales.head(5).items()
    ]

    region_sales = active.dropna(subset=["region_clean"]).groupby("region_clean")["net_sales"].sum().sort_values(ascending=False)
    region_shares = [
        {
            "region": str(region),
            "net_revenue": float(revenue),
            "share_pct": float(revenue / net_revenue * 100.0) if net_revenue else np.nan,
        }
        for region, revenue in region_sales.items()
    ]
    top_region = str(region_sales.index[0]) if not region_sales.empty else "N/A"

    discount_bands = [
        ("0%", 0.0, 0.0),
        ("1–10%", 0.0, 0.10),
        ("11–20%", 0.10, 0.20),
        ("21–30%", 0.20, 0.30),
        ("Above 30%", 0.30, float("inf")),
    ]
    discount_impact = []
    for label, low, high in discount_bands:
        if label == "0%":
            band = active.loc[active["discount_clean"] == 0.0]
        else:
            band = active.loc[(active["discount_clean"] > low) & (active["discount_clean"] <= high)]
        band_known = band.loc[band["profit_clean"].notna()]
        band_margin = _margin(band_known["profit_clean"].sum(), band_known["net_sales"].sum()) if not band_known.empty else np.nan
        discount_impact.append({
            "band": label,
            "profit_margin_pct": band_margin,
            "orders": int(band["order_id_clean"].nunique()),
        })

    first_negative = next(
        (item["band"] for item in discount_impact
         if not pd.isna(item["profit_margin_pct"]) and item["profit_margin_pct"] < 0),
        "None",
    )

    return {
        "net_revenue": net_revenue,
        "total_profit": total_profit,
        "number_of_orders": order_count,
        "average_order_value": average_order_value,
        "profit_margin_pct": profit_margin,
        "monthly_trend": monthly_trend,
        "best_month": best_month,
        "worst_month": worst_month,
        "worst_month_revenue": worst_month_revenue,
        "top_5_cities": top_5_cities,
        "region_shares": region_shares,
        "top_region": top_region,
        "discount_impact": discount_impact,
        "first_negative_discount_band": first_negative,
    }
