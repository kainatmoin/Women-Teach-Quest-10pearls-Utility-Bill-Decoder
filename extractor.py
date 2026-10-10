"""
Level 1 Extractor
Extracts billing details, readings, charges, taxes, and amounts into the exact required JSON format.
Strictly conforms to WTQ Build Track rules and schema.
"""

import json
import re
from datetime import datetime
from typing import Dict, Any, Optional
from gemini_client import GeminiClient

REQUIRED_FIELDS = [
    "provider",
    "tariff",
    "sanctioned_load_kw",
    "bill_month",
    "reading_date",
    "issue_date",
    "due_date",
    "previous_reading",
    "current_reading",
    "units_consumed",
    "charges",
    "total_charges",
    "taxes",
    "total_taxes",
    "current_bill",
    "arrears",
    "payable_within_due_date",
    "payable_after_due_date"
]

ALLOWED_CHARGE_TYPES = {
    "energy", "fixed", "fpa", "quarterly_adjustment", "surcharge", "meter_rent", "subsidy", "other"
}

ALLOWED_TAX_TYPES = {
    "gst", "electricity_duty", "income_tax", "municipal_tax", "other_tax"
}

CHARGE_TYPE_MAP = {
    "energy": "energy",
    "variable": "energy",
    "variable energy": "energy",
    "cost of electricity": "energy",
    "energy charges": "energy",
    "units": "energy",
    "fixed": "fixed",
    "fixed charges": "fixed",
    "fpa": "fpa",
    "fca": "fpa",
    "fuel adjustment": "fpa",
    "fuel price adjustment": "fpa",
    "total fpa": "fpa",
    "quarterly_adjustment": "quarterly_adjustment",
    "qta": "quarterly_adjustment",
    "quarterly tariff adjustment": "quarterly_adjustment",
    "uniform quarterly adjustment": "quarterly_adjustment",
    "surcharge": "surcharge",
    "additional surcharge": "surcharge",
    "additional surcharge (phl)": "surcharge",
    "fc surcharge": "surcharge",
    "f.c surcharge": "surcharge",
    "meter_rent": "meter_rent",
    "meter rent": "meter_rent",
    "service rent": "meter_rent",
    "subsidy": "subsidy",
    "subsidies": "subsidy",
    "relief": "subsidy",
    "other": "other"
}

TAX_TYPE_MAP = {
    "gst": "gst",
    "sales tax": "gst",
    "sales_tax": "gst",
    "gst on fpa": "gst",
    "electricity_duty": "electricity_duty",
    "electricity duty": "electricity_duty",
    "ed": "electricity_duty",
    "e.d": "electricity_duty",
    "income_tax": "income_tax",
    "income tax": "income_tax",
    "municipal_tax": "municipal_tax",
    "municipal tax": "municipal_tax",
    "muct": "municipal_tax",
    "kmc": "municipal_tax",
    "muct (kmc)": "municipal_tax",
    "other_tax": "other_tax",
    "extra tax": "other_tax",
    "further tax": "other_tax",
    "tv fee": "other_tax"
}

MONTH_MAP = {
    "jan": "01", "feb": "02", "mar": "03", "apr": "04", "may": "05", "jun": "06",
    "jul": "07", "aug": "08", "sep": "09", "oct": "10", "nov": "11", "dec": "12"
}

def normalize_date(val: Any) -> Optional[str]:
    """Parse date and return in YYYY-MM-DD format."""
    if val is None:
        return None
    s = str(val).strip()
    if not s or s.lower() in ["null", "none", "n/a", "-", "not printed", "unreadable"]:
        return None

    # Already YYYY-MM-DD
    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        return s

    # Remove ordinal suffixes: 13th, 1st, 2nd, 3rd
    s_clean = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", s)

    # Match patterns like: 25 SEP 26 or 25-Sep-2026 or 25/09/2026
    m = re.search(r"(\d{1,2})[\s\-_/]+([A-Za-z]+|\d{1,2})[\s\-_/]+(\d{2,4})", s_clean)
    if m:
        day_str, mon_str, yr_str = m.groups()
        day = int(day_str)
        yr = int(yr_str)
        if yr < 100:
            yr += 2000

        if mon_str.isalpha():
            mon_key = mon_str[:3].lower()
            mon = int(MONTH_MAP.get(mon_key, "01"))
        else:
            mon = int(mon_str)

        try:
            return f"{yr:04d}-{mon:02d}-{day:02d}"
        except Exception:
            pass

    return None

def normalize_month(val: Any) -> Optional[str]:
    """Parse billing month and return in YYYY-MM format."""
    if val is None:
        return None
    s = str(val).strip()
    if not s or s.lower() in ["null", "none", "n/a", "-", "unreadable"]:
        return None

    # Already YYYY-MM
    if re.match(r"^\d{4}-\d{2}$", s):
        return s

    # Match: SEP 26, SEP 2026, Jun-26, 09/2026
    m = re.search(r"([A-Za-z]+|\d{1,2})[\s\-_/]+(\d{2,4})", s)
    if m:
        mon_str, yr_str = m.groups()
        yr = int(yr_str)
        if yr < 100:
            yr += 2000

        if mon_str.isalpha():
            mon_key = mon_str[:3].lower()
            mon = int(MONTH_MAP.get(mon_key, "01"))
        else:
            mon = int(mon_str)

        return f"{yr:04d}-{mon:02d}"

    return None

EXTRACTION_SYSTEM_PROMPT = """You are an expert AI assistant specialized in analyzing Pakistani electricity bills from K-Electric (KE), LESCO, and IESCO for the WTQ Build Track competition.

Your task is to accurately extract non-identifying billing details from the provided bill image into a single JSON object.

CRITICAL RULES:
1. OUTPUT FORMAT: Return ONLY valid JSON. No conversational text, no markdown outside of a json codeblock.
2. NUMERIC FIELDS: Must be numbers (integers or floats), NEVER quoted strings, currency symbols ('Rs.', 'PKR'), or commas. Example: Rs. 19,964 -> 19964.
3. CREDITS & SUBSIDIES ARE NEGATIVE:
   - Any credit marked with 'CR' or '-' must be negative (e.g., '38209CR' -> -38209, '-0.53' -> -0.53, '54770CR' -> -54770).
   - Any subsidy or relief amount must be recorded as negative (e.g., subsidy of 3332 -> -3332).
4. DATE FORMATS:
   - bill_month MUST be 'YYYY-MM' (e.g., 'SEP 26' or 'Sep-2026' -> '2026-09', 'Jun-26' -> '2026-06').
   - reading_date, issue_date, due_date MUST be 'YYYY-MM-DD' (e.g., '25 SEP 26' -> '2026-09-25', '13th Jul 2026' -> '2026-07-13').
5. NULL VALUES:
   - Use null (not 'null' string, not 0) for unavailable values: not printed, blank, covered by a grey box, unreadable, or not applicable (e.g. 'NOT TO BE PAID').
   - A correct null is scored as correct. Do NOT guess or hallucinate.
6. NO PERSONAL IDENTIFIERS:
   - Do NOT extract or include names, addresses, CNIC, account numbers, reference numbers, consumer numbers, or meter numbers.
7. PROVIDER:
   - MUST be exactly one of: "KE", "LESCO", "IESCO".
   - Note: Even if filename is KESC_*, provider in JSON is "KE".
8. TARIFF:
   - Extract tariff code exactly as printed (e.g., "A1-R", "A-1a(01)", "A-1b(03)T", "A-2a(04)").
9. SANCTIONED LOAD:
   - Extract numeric kW value labelled 'Sanc Load', 'S.Load', or 'San Load'.
10. CHARGES:
    - One entry per line in the charges section. Skip blank lines and lines printed as 0.
    - Each item: {"type": "<type>", "amount": <number>}.
    - Allowed types: "energy", "fixed", "fpa", "quarterly_adjustment", "surcharge", "meter_rent", "subsidy", "other".
    - "energy": Cost of units used, Variable Upto ... Units, Cost of Electricity, Energy Charges.
    - "fixed": Fixed charges.
    - "fpa": Fuel price adjustment (FPA, FCA).
    - "quarterly_adjustment": QTA, Uniform Quarterly Adjustment, Quarterly Tariff Adjustment.
    - "surcharge": Surcharges, Additional Surcharge (PHL), F.C Surcharge.
    - "meter_rent": Meter rent or service rent.
    - "subsidy": Government subsidy or relief lines (AMOUNT MUST BE NEGATIVE).
    - "other": Any other charge line.
    - If detailed charges table is covered by a grey box (as often in LESCO/IESCO), include only visible charge lines (like Subsidies or Total FPA), or [] if none visible.
11. TOTAL_CHARGES:
    - The printed charges subtotal, or null if no subtotal is printed.
12. TAXES:
    - One entry per line in the tax or government section.
    - Allowed types: "gst", "electricity_duty", "income_tax", "municipal_tax", "other_tax".
    - "gst": Sales tax, GST, GST on FPA.
    - "electricity_duty": Electricity duty, ED.
    - "income_tax": Income tax.
    - "municipal_tax": Municipal or local charges printed under taxes (e.g. KE MUCT (KMC)).
    - "other_tax": Extra tax, further tax, TV fee.
    - IMPORTANT: If only a combined tax amount is printed (or detailed taxes are under a grey box), return [] for taxes and put the combined amount in total_taxes.
13. TOTAL_TAXES:
    - The printed tax subtotal, or null if no subtotal is printed.
14. CURRENT_BILL:
    - The printed amount for this month's bill.
15. ARREARS:
    - Previous dues carried forward. Keep printed sign (-0.53, -75496, 39411). Return null if blank.
16. PAYABLE_WITHIN_DUE_DATE:
    - The amount payable by the due date. Negative if CR (e.g., -54770).
17. PAYABLE_AFTER_DUE_DATE:
    - The amount payable after the due date.
    - If several late-payment amounts are shown (e.g., 'Till 12-OCT: 3674' and 'After 12-OCT: 3812'), USE THE HIGHEST (3812).
    - If marked 'NOT TO BE PAID' or blank, use null.

WORKED EXAMPLE (KE Bill KESC_0008):
{
  "provider": "KE",
  "tariff": "A1-R",
  "sanctioned_load_kw": 3,
  "bill_month": "2026-04",
  "reading_date": "2026-04-03",
  "issue_date": "2026-04-07",
  "due_date": "2026-04-21",
  "previous_reading": 8819,
  "current_reading": 8970,
  "units_consumed": 151,
  "charges": [
    {"type": "fixed", "amount": 900},
    {"type": "energy", "amount": 1054},
    {"type": "energy", "amount": 663.51},
    {"type": "quarterly_adjustment", "amount": 52.91},
    {"type": "fpa", "amount": 125.27},
    {"type": "surcharge", "amount": 64.93}
  ],
  "total_charges": 2860.62,
  "taxes": [
    {"type": "electricity_duty", "amount": 29.41},
    {"type": "gst", "amount": 520.21},
    {"type": "municipal_tax", "amount": 20}
  ],
  "total_taxes": 569.62,
  "current_bill": 3430.24,
  "arrears": -0.53,
  "payable_within_due_date": 3430,
  "payable_after_due_date": 3716
}
"""

EXTRACTION_USER_PROMPT = """Analyze this Pakistani electricity bill image carefully and extract all billing details according to the required schema.

Make sure:
1. Provider is strictly one of KE, LESCO, IESCO.
2. All date fields follow YYYY-MM or YYYY-MM-DD.
3. Numbers are actual numeric types without commas or currency marks.
4. If payable after due date has multiple tiers, pick the HIGHEST amount.
5. All negative credits / subsidies have negative numbers.
6. Null for any covered, blank, or unreadable values.
7. Return strictly the single JSON object matching all schema fields.
"""

def clean_and_validate_json(raw_text: str) -> Dict[str, Any]:
    """Parse JSON and normalize values according to competition rules."""
    text = raw_text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
        text = re.sub(r"\s*```$", "", text, flags=re.MULTILINE).strip()

    data = json.loads(text)

    # 1. Provider normalization
    prov = str(data.get("provider", "")).upper().strip()
    if "KESC" in prov or "K-ELECTRIC" in prov or prov == "KE":
        data["provider"] = "KE"
    elif "LESCO" in prov:
        data["provider"] = "LESCO"
    elif "IESCO" in prov:
        data["provider"] = "IESCO"
    else:
        data["provider"] = "KE" if "KE" in prov else ("LESCO" if "LESCO" in prov else "IESCO")

    # 2. Tariff normalization
    tariff = data.get("tariff")
    if tariff is not None:
        t_str = str(tariff).strip()
        if not t_str or t_str.lower() in ["null", "none", "n/a", "unreadable"]:
            data["tariff"] = None
        else:
            data["tariff"] = t_str
    else:
        data["tariff"] = None

    # 3. Date normalization
    data["bill_month"] = normalize_month(data.get("bill_month"))
    data["reading_date"] = normalize_date(data.get("reading_date"))
    data["issue_date"] = normalize_date(data.get("issue_date"))
    data["due_date"] = normalize_date(data.get("due_date"))

    # 4. Numeric conversions for root numeric fields
    numeric_fields = [
        "sanctioned_load_kw", "previous_reading", "current_reading", "units_consumed",
        "total_charges", "total_taxes", "current_bill", "arrears",
        "payable_within_due_date", "payable_after_due_date"
    ]

    for field in numeric_fields:
        val = data.get(field)
        if val is not None:
            if isinstance(val, str):
                v_clean = val.replace(",", "").replace("Rs.", "").replace("PKR", "").strip()
                if v_clean.lower() in ["null", "none", "n/a", "-", "not to be paid"]:
                    data[field] = None
                    continue
                is_credit = "CR" in v_clean.upper() or v_clean.startswith("-")
                v_clean = re.sub(r"[^\d.]", "", v_clean)
                if v_clean:
                    num = float(v_clean) if "." in v_clean else int(v_clean)
                    data[field] = -num if is_credit else num
                else:
                    data[field] = None
            elif isinstance(val, (int, float)):
                data[field] = val
        else:
            data[field] = None

    # 5. Validate and map charges
    charges = data.get("charges")
    if isinstance(charges, list):
        clean_charges = []
        for item in charges:
            if isinstance(item, dict) and "type" in item and "amount" in item:
                raw_type = str(item["type"]).lower().strip()
                c_type = CHARGE_TYPE_MAP.get(raw_type, "other")
                if c_type not in ALLOWED_CHARGE_TYPES:
                    c_type = "other"

                amt = item["amount"]
                if isinstance(amt, str):
                    is_neg = "CR" in amt.upper() or "-" in amt
                    c_clean = re.sub(r"[^\d.]", "", amt)
                    amt = float(c_clean) if "." in c_clean else (int(c_clean) if c_clean else 0)
                    if is_neg:
                        amt = -amt
                # Subsidy must be negative
                if c_type == "subsidy" and amt is not None and amt > 0:
                    amt = -amt
                if amt != 0 and amt is not None:
                    clean_charges.append({"type": c_type, "amount": amt})
        data["charges"] = clean_charges
    else:
        data["charges"] = []

    # 6. Validate and map taxes
    taxes = data.get("taxes")
    if isinstance(taxes, list):
        clean_taxes = []
        for item in taxes:
            if isinstance(item, dict) and "type" in item and "amount" in item:
                raw_type = str(item["type"]).lower().strip()
                t_type = TAX_TYPE_MAP.get(raw_type, "other_tax")
                if t_type not in ALLOWED_TAX_TYPES:
                    t_type = "other_tax"

                amt = item["amount"]
                if isinstance(amt, str):
                    c_clean = re.sub(r"[^\d.]", "", amt)
                    amt = float(c_clean) if "." in c_clean else (int(c_clean) if c_clean else 0)
                if amt != 0 and amt is not None:
                    clean_taxes.append({"type": t_type, "amount": amt})
        data["taxes"] = clean_taxes
    else:
        data["taxes"] = []

    # 7. Strict whitelist filter to strictly the 18 required keys (excludes any PII or extra keys)
    final_output = {}
    for k in REQUIRED_FIELDS:
        final_output[k] = data.get(k, None)

    return final_output


def extract_bill_details(image_path: str, client: Optional[GeminiClient] = None) -> Dict[str, Any]:
    """Run Level 1 extraction on a bill image."""
    if client is None:
        client = GeminiClient()

    raw_response = client.call_gemini(
        prompt=EXTRACTION_USER_PROMPT,
        image_path=image_path,
        system_instruction=EXTRACTION_SYSTEM_PROMPT,
        json_mode=True
    )

    return clean_and_validate_json(raw_response)
