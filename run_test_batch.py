"""
Test Batch Runner for WTQ 2026 Build Track
Executes Level 1 and Level 2 generation on the 10 test bills and CSV templates.
Generates:
- output/level1.csv (10 rows)
- output/level2.csv (120 rows)
Then runs packaging validation.
"""

import sys
import time
from pathlib import Path
from batch_processor import run_pipeline
from package_submission import create_submission_zip

def main():
    bills_dir = "data/test data/bills"
    l1_template = "data/test data/csv/level1.csv"
    l2_template = "data/test data/csv/level2.csv"
    output_dir = "output"

    print("=================================================================")
    print("  WTQ 2026 BUILD TRACK — TEST BATCH GENERATION")
    print("=================================================================")
    print(f"Bills directory: {bills_dir}")
    print(f"Level 1 template: {l1_template}")
    print(f"Level 2 template: {l2_template}")
    print(f"Output directory: {output_dir}")
    print("=================================================================\n")

    t0 = time.time()

    # Step 1: Run batch pipeline
    run_pipeline(
        bills_dir=bills_dir,
        level1_template=l1_template,
        level2_template=l2_template,
        output_dir=output_dir
    )

    elapsed = time.time() - t0
    print(f"\nBatch processing finished in {elapsed:.1f} seconds.")

    # Step 2: Package final submission zip
    print("\nPackaging official submission ZIP...")
    create_submission_zip()

    print("\nAll done! Please check 'output/' and 'your-submission.zip'.")

if __name__ == "__main__":
    main()
