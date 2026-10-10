
from pathlib import Path
from extractor import extract_bill_details

folder = Path("data/train data")

expected = {
    "provider", "tariff", "sanctioned_load_kw", "bill_month",
    "reading_date", "issue_date", "due_date", "previous_reading",
    "current_reading", "units_consumed", "charges", "total_charges",
    "taxes", "total_taxes", "current_bill", "arrears",
    "payable_within_due_date", "payable_after_due_date"
}

files = sorted(
    f for f in folder.iterdir()
    if f.suffix.lower() in (".jpg", ".jpeg", ".png")
)

for file in files:
    print(f"\nTEST: {file.name}", flush=True)

    try:
        result = extract_bill_details(str(file))
        missing = expected - set(result)
        extra = set(result) - expected

        print("Field count:", len(result))
        print("Missing:", sorted(missing))
        print("Extra:", sorted(extra))
        print("Provider:", result.get("provider"))
        print("Bill month:", result.get("bill_month"))
        print("Units:", result.get("units_consumed"))
        print("Current bill:", result.get("current_bill"))
    except Exception as error:
        print("ERROR:", error)
