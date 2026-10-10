"""
Submission Packager for WTQ Build Track
Creates your-submission.zip matching the exact specification:
- output/level1.csv (10 rows, valid JSON strings, no empty cells)
- output/level2.csv (120 rows, answers grounded in bills, no empty cells)
- source/ (code files, README.md, .env.example, requirements.txt, strictly NO .env or secrets)
- demo/ (optional demo.mp4 if present)
Ensures total archive is under 15 MB.
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

REQUIRED_SOURCE_FILES = [
    "app.py",
    "batch_processor.py",
    "extractor.py",
    "qa_engine.py",
    "gemini_client.py",
    "package_submission.py",
    "README.md",
    ".env.example",
    "requirements.txt"
]

def validate_csv_outputs(ws: Path):
    """Validate level1.csv and level2.csv before packaging."""
    l1_path = ws / "output" / "level1.csv"
    l2_path = ws / "output" / "level2.csv"

    warnings = []

    if not l1_path.exists():
        warnings.append("output/level1.csv is missing!")
    else:
        with open(l1_path, "r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            print(f"  [Check] output/level1.csv row count: {len(reader)}")
            if len(reader) != 10:
                warnings.append(f"output/level1.csv has {len(reader)} rows (expected 10 test rows).")
            for idx, r in enumerate(reader, 1):
                b_id = r.get("bill_id", "").strip()
                j_str = r.get("json", "").strip()
                if not b_id or not j_str:
                    warnings.append(f"output/level1.csv row {idx} has empty bill_id or json!")
                else:
                    try:
                        d = json.loads(j_str)
                        if "provider" not in d or "current_bill" not in d:
                            warnings.append(f"output/level1.csv row {idx} ({b_id}) JSON missing core fields.")
                    except Exception as e:
                        warnings.append(f"output/level1.csv row {idx} ({b_id}) contains invalid JSON: {e}")

    if not l2_path.exists():
        warnings.append("output/level2.csv is missing!")
    else:
        with open(l2_path, "r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            print(f"  [Check] output/level2.csv row count: {len(reader)}")
            if len(reader) != 120:
                warnings.append(f"output/level2.csv has {len(reader)} rows (expected 120 test rows).")
            empty_answers = sum(1 for r in reader if not r.get("answer", "").strip())
            if empty_answers > 0:
                warnings.append(f"output/level2.csv has {empty_answers} empty answers!")

    if warnings:
        print("\n  [WARNING] PRE-FLIGHT CSV VALIDATION WARNINGS:")
        for w in warnings:
            print(f"    - {w}")
    else:
        print("  [OK] All output CSVs passed pre-flight integrity checks!")

def create_submission_zip(
    workspace_dir: str = ".",
    output_zip_path: str = "your-submission.zip"
) -> str:
    ws = Path(workspace_dir).resolve()
    zip_out = ws / output_zip_path

    print(f"\nCreating submission package: {zip_out}...")
    validate_csv_outputs(ws)

    with zipfile.ZipFile(zip_out, "w", zipfile.ZIP_DEFLATED) as zf:
        # 1. Output folder
        output_dir = ws / "output"
        if output_dir.exists():
            for f in output_dir.glob("*.csv"):
                zf.write(f, arcname=f"output/{f.name}")
                print(f"  Added output/{f.name}")
        else:
            print("  WARNING: output/ directory not found!")

        # 2. Source folder
        for sf_name in REQUIRED_SOURCE_FILES:
            sf_path = ws / sf_name
            if sf_path.exists():
                zf.write(sf_path, arcname=f"source/{sf_name}")
                print(f"  Added source/{sf_name}")
            else:
                print(f"  WARNING: {sf_name} not found in workspace!")

        # 3. Demo folder (optional)
        demo_dir = ws / "demo"
        if demo_dir.exists():
            for df in demo_dir.iterdir():
                if df.suffix.lower() in [".mp4", ".mov", ".webm"]:
                    zf.write(df, arcname=f"demo/{df.name}")
                    print(f"  Added demo/{df.name}")

        # Security check: ensure .env is NOT in zip
        for member in zf.namelist():
            if ".env" in member and not member.endswith(".env.example"):
                raise RuntimeError(f"SECURITY ALERT: Found forbidden secret file '{member}' in ZIP archive!")

    size_mb = zip_out.stat().st_size / (1024 * 1024)
    print(f"\n=======================================================")
    print(f"  Created {output_zip_path} ({size_mb:.2f} MB)")
    if size_mb > 15.0:
        print("  [ERROR] Archive exceeds 15 MB limit!")
    else:
        print("  [PASS] Size check: Archive is strictly under 15 MB.")
    print(f"=======================================================\n")

    return str(zip_out)

if __name__ == "__main__":
    create_submission_zip()
