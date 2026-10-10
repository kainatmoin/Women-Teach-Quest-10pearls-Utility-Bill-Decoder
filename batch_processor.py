"""
Batch Processor for WTQ Utility Bill Decoder
Processes test bills and templates to generate output/level1.csv and output/level2.csv.
"""

import os
import csv
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
from gemini_client import GeminiClient
from extractor import extract_bill_details, REQUIRED_FIELDS
from qa_engine import answer_questions_batch, answer_question

EMPTY_FALLBACK_BILL = {
    "provider": "KE",
    "tariff": None,
    "sanctioned_load_kw": None,
    "bill_month": None,
    "reading_date": None,
    "issue_date": None,
    "due_date": None,
    "previous_reading": None,
    "current_reading": None,
    "units_consumed": None,
    "charges": [],
    "total_charges": None,
    "taxes": [],
    "total_taxes": None,
    "current_bill": None,
    "arrears": None,
    "payable_within_due_date": None,
    "payable_after_due_date": None
}

def get_fallback_record(bill_id: str) -> Dict[str, Any]:
    rec = dict(EMPTY_FALLBACK_BILL)
    u_id = bill_id.upper()
    if "KESC" in u_id or "KE" in u_id:
        rec["provider"] = "KE"
    elif "LESCO" in u_id:
        rec["provider"] = "LESCO"
    elif "IESCO" in u_id:
        rec["provider"] = "IESCO"
    return rec

def find_image_for_bill_id(bills_dir: Path, bill_id: str) -> Optional[Path]:
    """Find the image file matching bill_id regardless of extension (.png, .jpg, .jpeg)."""
    for ext in [".png", ".jpg", ".jpeg", ".PNG", ".JPG", ".JPEG"]:
        p = bills_dir / f"{bill_id}{ext}"
        if p.exists():
            return p
    for p in bills_dir.iterdir():
        if p.stem.lower() == bill_id.lower() and p.suffix.lower() in [".png", ".jpg", ".jpeg"]:
            return p
    return None

def process_level1(
    bills_dir: str,
    template_csv: Optional[str] = None,
    output_csv: str = "output/level1.csv",
    client: Optional[GeminiClient] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Process bills for Level 1 and generate level1.csv.
    Returns mapping of bill_id -> extracted_json.
    """
    bills_path = Path(bills_dir)
    os.makedirs(Path(output_csv).parent, exist_ok=True)
    
    # Determine bills to process
    bill_ids: List[str] = []
    if template_csv and os.path.exists(template_csv):
        with open(template_csv, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                b_id = row.get("bill_id", "").strip()
                if b_id:
                    bill_ids.append(b_id)
    else:
        for p in sorted(bills_path.iterdir()):
            if p.suffix.lower() in [".png", ".jpg", ".jpeg"]:
                bill_ids.append(p.stem)

    results: Dict[str, Dict[str, Any]] = {}
    rows_to_write = []

    print(f"\n--- Starting Level 1 Processing ({len(bill_ids)} bills) ---")
    for idx, bill_id in enumerate(bill_ids, 1):
        img_path = find_image_for_bill_id(bills_path, bill_id)
        if not img_path:
            print(f"[{idx}/{len(bill_ids)}] WARNING: Image for bill {bill_id} not found in {bills_dir}!")
            data = get_fallback_record(bill_id)
        else:
            print(f"[{idx}/{len(bill_ids)}] Extracting Level 1 details for {bill_id} ({img_path.name})...")
            try:
                data = extract_bill_details(str(img_path), client=client)
            except Exception as e:
                print(f"  Error processing {bill_id}: {e}")
                data = get_fallback_record(bill_id)

        results[bill_id] = data
        json_str = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
        rows_to_write.append({"bill_id": bill_id, "json": json_str})

    # Write output/level1.csv
    with open(output_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["bill_id", "json"])
        writer.writeheader()
        for r in rows_to_write:
            writer.writerow(r)

    print(f"Level 1 complete! Saved {len(rows_to_write)} rows to {output_csv}\n")
    return results

def process_level2(
    bills_dir: str,
    template_csv: str,
    output_csv: str = "output/level2.csv",
    extracted_data_map: Optional[Dict[str, Dict[str, Any]]] = None,
    client: Optional[GeminiClient] = None
):
    """
    Process bills for Level 2 and generate level2.csv.
    Groups questions per bill for high speed and rate-limit safety.
    """
    bills_path = Path(bills_dir)
    os.makedirs(Path(output_csv).parent, exist_ok=True)

    if not os.path.exists(template_csv):
        print(f"Level 2 template {template_csv} not found. Skipping Level 2 batch.")
        return

    extracted_data_map = extracted_data_map or {}

    rows_to_process = []
    with open(template_csv, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows_to_process.append(row)

    print(f"\n--- Starting Level 2 Processing ({len(rows_to_process)} questions total) ---")

    # Group questions by bill_id
    bill_questions_map: Dict[str, List[Dict[str, str]]] = {}
    for row in rows_to_process:
        bid = row["bill_id"].strip()
        if bid not in bill_questions_map:
            bill_questions_map[bid] = []
        bill_questions_map[bid].append(row)

    answers_cache: Dict[str, Dict[str, str]] = {}

    for idx, (bill_id, q_rows) in enumerate(bill_questions_map.items(), 1):
        img_path = find_image_for_bill_id(bills_path, bill_id)
        bill_data = extracted_data_map.get(bill_id)

        print(f"[{idx}/{len(bill_questions_map)}] Answering {len(q_rows)} questions for bill {bill_id}...")
        if img_path:
            q_list = [{"question_id": r.get("question_id", ""), "question": r.get("question", "")} for r in q_rows]
            ans_map = answer_questions_batch(q_list, str(img_path), extracted_json=bill_data, client=client)
            answers_cache[bill_id] = ans_map
        else:
            answers_cache[bill_id] = {r.get("question_id", ""): "Bill image not available to answer question." for r in q_rows}

    # Assemble completed rows strictly preserving the template row order
    completed_rows = []
    for row in rows_to_process:
        bill_id = row["bill_id"].strip()
        qid = row.get("question_id", "").strip()
        ans = answers_cache.get(bill_id, {}).get(qid, "No answer generated.")
        completed_rows.append({
            "bill_id": bill_id,
            "question_id": qid,
            "question": row.get("question", "").strip(),
            "answer": ans
        })

    # Write output/level2.csv
    with open(output_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["bill_id", "question_id", "question", "answer"])
        writer.writeheader()
        for r in completed_rows:
            writer.writerow(r)

    print(f"Level 2 complete! Saved {len(completed_rows)} rows to {output_csv}\n")

def auto_detect_bills_dir() -> str:
    candidates = [
        "data/test data/bills",
        "test/bills",
        "data/test data",
        "data/train data",
        "train/bills"
    ]
    for c in candidates:
        if os.path.exists(c) and any(Path(c).glob("*.png")):
            return c
    return "data/train data"

def auto_detect_templates() -> tuple[Optional[str], Optional[str]]:
    l1_candidates = [
        "data/test data/csv/level1.csv",
        "test/csv/level1.csv",
        "csv/level1.csv",
        "test/level1.csv",
        "level1.csv"
    ]
    l2_candidates = [
        "data/test data/csv/level2.csv",
        "test/csv/level2.csv",
        "csv/level2.csv",
        "test/level2.csv",
        "level2.csv"
    ]
    l1 = next((p for p in l1_candidates if os.path.exists(p)), None)
    l2 = next((p for p in l2_candidates if os.path.exists(p)), None)
    return l1, l2

def run_pipeline(
    bills_dir: Optional[str] = None,
    level1_template: Optional[str] = None,
    level2_template: Optional[str] = None,
    output_dir: str = "output"
):
    """Run end-to-end pipeline."""
    client = GeminiClient()
    os.makedirs(output_dir, exist_ok=True)

    bills_dir = bills_dir or auto_detect_bills_dir()
    det_l1, det_l2 = auto_detect_templates()
    level1_template = level1_template or det_l1
    level2_template = level2_template or det_l2

    print(f"Using bills directory: {bills_dir}")
    print(f"Level 1 template: {level1_template}")
    print(f"Level 2 template: {level2_template}")

    l1_out = os.path.join(output_dir, "level1.csv")
    l2_out = os.path.join(output_dir, "level2.csv")

    # Step 1: Level 1
    extracted_map = process_level1(
        bills_dir=bills_dir,
        template_csv=level1_template,
        output_csv=l1_out,
        client=client
    )

    # Step 2: Level 2
    if level2_template and os.path.exists(level2_template):
        process_level2(
            bills_dir=bills_dir,
            template_csv=level2_template,
            output_csv=l2_out,
            extracted_data_map=extracted_map,
            client=client
        )
    else:
        print(f"Level 2 template not provided or not found. Only Level 1 generated.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WTQ Utility Bill Decoder Batch Runner")
    parser.add_argument("--bills", default=None, help="Directory containing bill images")
    parser.add_argument("--l1-template", default=None, help="Path to level1.csv template")
    parser.add_argument("--l2-template", default=None, help="Path to level2.csv template")
    parser.add_argument("--output-dir", default="output", help="Output directory for generated CSVs")
    args = parser.parse_args()

    run_pipeline(
        bills_dir=args.bills,
        level1_template=args.l1_template,
        level2_template=args.l2_template,
        output_dir=args.output_dir
    )
