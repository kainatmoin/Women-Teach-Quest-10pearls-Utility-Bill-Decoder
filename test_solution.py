"""
Test Suite for WTQ Utility Bill Decoder
Tests:
1. Clean and validate schema logic against Section 5.7 worked example.
2. CSV format compliance (RFC 4180 double-quoting, single-line JSON).
3. Deliverables validation: output/level1.csv (10 rows) and output/level2.csv (120 rows).
4. Package validation: builds your-submission.zip, validates structure, size < 15MB, strictly no .env leak.
"""

import os
import sys
import csv
import json
import zipfile
from pathlib import Path

# Safe encoding for Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from extractor import clean_and_validate_json, REQUIRED_FIELDS
from package_submission import create_submission_zip

SAMPLE_KESC_0008_JSON = """{
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
}"""

def test_schema_validation():
    print("Test 1: Validating schema parsing on KESC_0008 reference JSON...")
    data = clean_and_validate_json(SAMPLE_KESC_0008_JSON)

    for field in REQUIRED_FIELDS:
        assert field in data, f"Missing required field {field}"

    assert data["provider"] == "KE"
    assert data["units_consumed"] == 151
    assert data["arrears"] == -0.53
    assert data["total_charges"] == 2860.62
    assert data["total_taxes"] == 569.62
    assert data["payable_after_due_date"] == 3716
    print("  [PASS] Schema validation passed!")

def test_csv_formatting():
    print("Test 2: Verifying CSV quoting and single-line JSON format...")
    test_csv = "test_output.csv"
    data = clean_and_validate_json(SAMPLE_KESC_0008_JSON)
    json_str = json.dumps(data, separators=(",", ":"))

    with open(test_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["bill_id", "json"])
        writer.writeheader()
        writer.writerow({"bill_id": "KESC_0008", "json": json_str})

    with open(test_csv, "r", encoding="utf-8") as f:
        content = f.read()

    assert '"{""provider"":""KE""' in content or ',"{""provider"":""KE""' in content
    lines = [l for l in content.splitlines() if l.strip()]
    assert len(lines) == 2, f"Expected 2 lines, got {len(lines)}"

    if os.path.exists(test_csv):
        os.remove(test_csv)
    print("  [PASS] CSV formatting test passed!")

def test_output_csv_deliverables():
    print("Test 3: Validating competition deliverables in output/ folder...")
    l1_path = Path("output/level1.csv")
    l2_path = Path("output/level2.csv")

    assert l1_path.exists(), "output/level1.csv does not exist!"
    assert l2_path.exists(), "output/level2.csv does not exist!"

    # Validate level1.csv
    with open(l1_path, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        assert len(reader) == 10, f"Expected exactly 10 rows in level1.csv, got {len(reader)}"
        for idx, r in enumerate(reader, 1):
            assert "bill_id" in r and "json" in r, f"Row {idx} missing bill_id or json"
            j_data = json.loads(r["json"])
            for req_k in REQUIRED_FIELDS:
                assert req_k in j_data, f"Row {idx} ({r['bill_id']}) JSON missing required key: {req_k}"
            assert j_data["provider"] in ["KE", "LESCO", "IESCO"], f"Invalid provider: {j_data['provider']}"
    print("  [PASS] output/level1.csv verified (exactly 10 bills, valid 18-key JSON)")

    # Validate level2.csv
    with open(l2_path, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        assert len(reader) == 120, f"Expected exactly 120 rows in level2.csv, got {len(reader)}"
        empty_answers = 0
        for idx, r in enumerate(reader, 1):
            assert "bill_id" in r and "question_id" in r and "question" in r and "answer" in r
            if not r["answer"] or not r["answer"].strip():
                empty_answers += 1
        assert empty_answers == 0, f"Found {empty_answers} empty answers in level2.csv"
    print("  [PASS] output/level2.csv verified (exactly 120 rows, 0 empty answers)")

def test_submission_archive():
    print("Test 4: Packaging and validating your-submission.zip...")
    create_submission_zip()
    zip_path = Path("your-submission.zip")
    assert zip_path.exists(), "your-submission.zip was not created!"

    size_mb = zip_path.stat().st_size / (1024 * 1024)
    assert size_mb < 15.0, f"Zip archive exceeds 15 MB: {size_mb:.2f} MB"

    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()
        assert "output/level1.csv" in names, "Missing output/level1.csv in zip"
        assert "output/level2.csv" in names, "Missing output/level2.csv in zip"
        assert "source/README.md" in names, "Missing source/README.md in zip"
        assert "source/.env.example" in names, "Missing source/.env.example in zip"
        assert "source/app.py" in names, "Missing source/app.py in zip"

        # Security assertion: ensure real .env is NOT packaged
        for n in names:
            # Must strictly reject any real .env file while allowing .env.example
            is_secret_env = (n == ".env" or n == "source/.env" or n.endswith("/.env") or n.endswith("\\.env"))
            assert not is_secret_env, f"SECURITY VIOLATION: secret .env packaged in {n}"

    print(f"  [PASS] your-submission.zip verified ({size_mb:.2f} MB, perfect archive structure, 0 secret leaks)")

if __name__ == "__main__":
    test_schema_validation()
    test_csv_formatting()
    test_output_csv_deliverables()
    test_submission_archive()
    print("\n=======================================================")
    print("  ALL VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=======================================================\n")
