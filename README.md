# WTQ 2026 Utility Bill Decoder

[![Women Tech Quest 2026](https://img.shields.io/badge/WTQ%202026-Build%20Track-8050B8)](https://womentechquest.10pearls.com/)
[![Organized by 10Pearls](https://img.shields.io/badge/Organized%20By-10Pearls-35B6C8)](https://10pearls.com/)
[![Python Version](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-F7C928)](https://www.python.org/)
[![Streamlit Cloud](https://img.shields.io/badge/Streamlit-Community%20Cloud-FF4B4B)](https://share.streamlit.io/)
[![Model](https://img.shields.io/badge/Gemini-3.5--flash--lite-0E7490)](https://aistudio.google.com/)
[![License](https://img.shields.io/badge/License-MIT-gray.svg)](LICENSE)

An AI-powered multimodal electricity bill decoder built for **Women Tech Quest 2026 (Build Track)**, organized by **10Pearls**. Extracts structured billing data from Pakistani electricity bills (K-Electric, LESCO, IESCO) and answers customer questions with grounded, plain-English explanations using Google Gemini.

---

## 1. Project Overview & Architecture

Pakistani utility bills feature dense visual layouts, bilingual terminology (English & Urdu), greyed-out PII boxes, tiered tariff slabs, and complex surcharges (FPA, QTA, electricity duty, sales tax).

This solution implements a complete end-to-end processing pipeline:

```
                  +--------------------------------+
                  |  Utility Bill Image (PNG/JPG)  |
                  |  (K-Electric / LESCO / IESCO)  |
                  +---------------+----------------+
                                  |
                                  v
                  +--------------------------------+
                  |     GeminiClient (urllib)      |
                  |  Google Gemini 3.5 Flash-Lite  |
                  +---------------+----------------+
                                  |
         +------------------------+------------------------+
         |                                                 |
         v                                                 v
+-------------------------------+       +-----------------------------------+
|  Level 1 Extractor            |       |  Level 2 QA Engine                |
|  - 18 Required Schema Keys    |       |  - Grounded Plain English Answers |
|  - Date & Number Coercion     |       |  - On-Bill Calculations           |
|  - PII Whitelist Filtering    |       |  - Regex PII Scrubber Redaction   |
+---------------+---------------+       +-----------------+-----------------+
                |                                         |
                v                                         v
        output/level1.csv                         output/level2.csv
      (10 bills, RFC 4180)                     (120 Q&A pairs, RFC 4180)
         \                                                /
          +-----------------------+----------------------+
                                  |
                                  v
              +----------------------------------------+
              |           Interfaces & Tools           |
              |  - Responsive Streamlit App            |
              |    (streamlit_app.py)                  |
              |  - Original Standalone HTTP Server     |
              |    (app.py)                            |
              |  - Batch CLI (batch_processor.py)      |
              |  - Submission Packager (< 15 MB ZIP)   |
              +----------------------------------------+
```

### Key Capabilities
- **Level 1 (Structured Extraction)**: Extracts exactly the 18 required schema fields into clean, single-line RFC 4180 JSON. Enforces date normalization (`YYYY-MM-DD`, `YYYY-MM`), numeric parsing, and negative signs for subsidies and credits.
- **Level 2 (Bill-Grounded Q&A)**: Answers customer questions (Q1–Q12) strictly grounded in the bill image and extracted data. Computes math (historical averages, summer vs. winter differences, late surcharges) without hallucinating external rates.
- **Privacy & PII Protection**: Strict key whitelisting and regex-based redaction ensure customer names, addresses, CNICs (`\d{5}-\d{7}-\d`), and 14-digit reference numbers are never exposed.
- **Responsive Streamlit Dashboard** (`streamlit_app.py`): Recreates the official Women Tech Quest glassmorphism theme (Purple `#8050B8`, Teal `#35B6C8`, Yellow `#F7C928`). Fully responsive across mobile (320px–430px) and desktop viewports, with metric cards, breakdown tables, quick question chips, and one-click downloads.
- **Original Standalone HTTP Server** (`app.py`): Preserved zero-dependency Python `http.server` with embedded SPA dashboard.
- **Automated Batch Processing & Submission Packaging**: Generates compliant deliverables and packages `your-submission.zip` (< 15 MB) with pre-flight validation.

---

## 2. Technology Stack

| Component | Technology | Rationale |
| :--- | :--- | :--- |
| **Language** | Python 3.11+ (Tested on 3.13) | Modern standard runtime |
| **Web Framework (Cloud & Primary)** | Streamlit (`streamlit>=1.35.0`) | Interactive data dashboard, mobile-responsive, native Streamlit Community Cloud support |
| **Web Framework (Original Standalone)** | Python Standard Library (`http.server`) | Lightweight zero-dependency HTTP server, completely preserved in `app.py` |
| **Multimodal LLM** | Gemini 3.5 Flash-Lite (`gemini-3.5-flash-lite`) | High accuracy, fast vision inference, competition-approved |
| **API Client** | Native Standard Library (`urllib.request`) | Zero external dependency, exponential backoff on HTTP 429/503 |
| **Styling & Theme** | Custom CSS3 + Glassmorphism | WTQ Purple/Teal/Yellow visual identity, mobile-responsive layout |
| **Packaging & CI** | `zipfile`, `csv`, `json`, Dockerfile, Procfile | Automated validation and multi-platform deployment readiness |

---

## 3. Project Directory Structure

```
Women-Teach-Quest-10pearls-Utility-Bill-Decoder/
├── streamlit_app.py         # Primary Streamlit web application (Cloud & Local)
├── app.py                   # Original standalone HTTP server & REST API
├── batch_processor.py       # Automated batch CLI for Level 1 & Level 2 CSVs
├── check_bills.py           # Quick utility script to inspect bill extractions
├── extractor.py             # Level 1 bill extraction engine & schema validator
├── gemini_client.py         # Resilient Gemini multimodal API client
├── package_submission.py    # Official submission packager & ZIP validator
├── qa_engine.py             # Level 2 grounded question-answering engine
├── test_solution.py         # End-to-end verification test suite
├── run_streamlit.bat        # Windows one-click launcher for Streamlit app
├── run_dashboard.bat        # Windows one-click launcher for original app.py
├── run_test_batch.bat       # Windows one-click launcher for batch processing
├── run_test_batch.py        # Pipeline orchestrator for test data
├── Dockerfile               # Container specification
├── Procfile                 # Cloud web command (web: python app.py)
├── requirements.txt         # Minimal Python dependencies
├── .env.example             # Template for required environment variables
├── .gitignore               # Excludes secrets (.env), venv, caches, and archives
├── .streamlit/
│   └── config.toml          # Streamlit theme configuration (WTQ colors)
├── data/                    # Dataset directory
│   ├── test data/           # Official test dataset (10 bills & template CSVs)
│   └── train data/          # Reference training bills
└── output/                  # Generated competition deliverables
    ├── level1.csv           # 10 rows of extracted JSON
    └── level2.csv           # 120 rows of grounded Q&A
```

---

## 4. Local Setup Instructions (Windows)

Follow these exact steps to clone, configure, and run the project locally on Windows:

```powershell
# 1. Clone the repository
git clone https://github.com/kainatmoin/Women-Teach-Quest-10pearls-Utility-Bill-Decoder.git

# 2. Enter the project directory
cd Women-Teach-Quest-10pearls-Utility-Bill-Decoder

# 3. Create a virtual environment
python -m venv .venv

# 4. Activate the virtual environment
.venv\Scripts\Activate.ps1

# 5. Install dependencies
python -m pip install -r requirements.txt

# 6. Configure environment credentials
copy .env.example .env
```

Open `.env` in any text editor and insert your Google AI Studio API key:
```env
MODEL_PROVIDER=google
MODEL_NAME=gemini-3.5-flash-lite
API_KEY=your_actual_google_ai_studio_api_key_here
PORT=5000
HOST=127.0.0.1
```

> [!WARNING]
> Never commit your `.env` file or publish your API keys. The `.gitignore` file is pre-configured to strictly exclude `.env` and local secrets from version control.

### Run the Streamlit Application (Recommended)
```powershell
streamlit run streamlit_app.py
```
*Or double-click `run_streamlit.bat` on Windows.* Open your web browser at: **`http://localhost:8501`**

### Run the Original Standalone Application
```powershell
python app.py
```
*Or double-click `run_dashboard.bat` on Windows.* Open your web browser at: **`http://127.0.0.1:5000`**

---

## 5. Streamlit Community Cloud Deployment

The repository is configured for one-click deployment on **[Streamlit Community Cloud](https://share.streamlit.io/)**:

1. Sign in to **[share.streamlit.io](https://share.streamlit.io/)** with your GitHub account.
2. Click **New app**.
3. Configure the app settings:
   - **Repository**: `kainatmoin/Women-Teach-Quest-10pearls-Utility-Bill-Decoder`
   - **Branch**: `main`
   - **Main file path**: `streamlit_app.py`
4. Click **Advanced settings...** and configure your secrets in **Secrets (TOML)** format:
   ```toml
   # Google AI Studio API Key (Required)
   API_KEY = "your_actual_google_ai_studio_api_key_here"

   # Model Settings (Optional, defaults to gemini-3.5-flash-lite)
   MODEL_NAME = "gemini-3.5-flash-lite"
   MODEL_PROVIDER = "google"
   ```
   *(Note: `GEMINI_API_KEY` is also supported as an alternative key name).*
5. Click **Deploy!**

> [!IMPORTANT]
> API keys belong exclusively in **Streamlit Cloud Secrets** or local `.env` files. They must **never** be committed to GitHub.

---

## 6. Batch Processing & Testing

### 1. Run Automated Test Suite
To validate schema parsing, CSV RFC 4180 formatting, deliverables integrity, and submission packaging:
```powershell
python test_solution.py
```

Expected output:
```text
Test 1: Validating schema parsing on KESC_0008 reference JSON...
  [PASS] Schema validation passed!
Test 2: Verifying CSV quoting and single-line JSON format...
  [PASS] CSV formatting test passed!
Test 3: Validating competition deliverables in output/ folder...
  [PASS] output/level1.csv verified (exactly 10 bills, valid 18-key JSON)
  [PASS] output/level2.csv verified (exactly 120 rows, 0 empty answers)
Test 4: Packaging and validating your-submission.zip...
  Added output/level1.csv
  Added output/level2.csv
  Added source/app.py
  Added source/streamlit_app.py
  Added source/batch_processor.py
  Added source/extractor.py
  Added source/qa_engine.py
  Added source/gemini_client.py
  Added source/package_submission.py
  Added source/README.md
  Added source/.env.example
  Added source/requirements.txt
  [PASS] Size check: Archive is strictly under 15 MB (0.05 MB).
  [PASS] your-submission.zip verified (0.05 MB, perfect archive structure, 0 secret leaks)

=======================================================
  ALL VERIFICATION TESTS PASSED SUCCESSFULLY!
=======================================================
```

### 2. Run Batch CSV Processing via CLI
To process all test bills and generate `output/level1.csv` and `output/level2.csv`:
```powershell
python run_test_batch.py
```
*Or double-click `run_test_batch.bat` on Windows.*

Alternatively, run `batch_processor.py` with custom paths:
```powershell
python batch_processor.py \
  --bills "data/test data/bills" \
  --l1-template "data/test data/csv/level1.csv" \
  --l2-template "data/test data/csv/level2.csv" \
  --output-dir "output"
```

### 3. Package Official Submission ZIP
```powershell
python package_submission.py
```
Validates deliverables and generates `your-submission.zip` (< 15 MB) containing:
- `output/level1.csv` (10 rows)
- `output/level2.csv` (120 rows)
- `source/` (`streamlit_app.py`, `app.py`, `extractor.py`, `qa_engine.py`, `gemini_client.py`, `batch_processor.py`, `package_submission.py`, `README.md`, `.env.example`, `requirements.txt`)
- `demo/` (optional demo video)

---

## 7. Expected Output Schemas

### Level 1 Output (`output/level1.csv`)
- **Row Count**: Exactly 10 rows (1 row per test bill)
- **Columns**: `bill_id,json`
- **JSON Schema** (Strict 18 Keys):
  ```json
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
      {"type": "energy", "amount": 1054}
    ],
    "total_charges": 2860.62,
    "taxes": [
      {"type": "electricity_duty", "amount": 29.41},
      {"type": "gst", "amount": 520.21}
    ],
    "total_taxes": 569.62,
    "current_bill": 3430.24,
    "arrears": -0.53,
    "payable_within_due_date": 3430,
    "payable_after_due_date": 3716
  }
  ```
- **Formatting**: Encoded as a single-line string with double quotation marks escaping (`""`) per RFC 4180.

### Level 2 Output (`output/level2.csv`)
- **Row Count**: Exactly 120 rows (10 bills × 12 questions Q1–Q12)
- **Columns**: `bill_id,question_id,question,answer`
- **Answers**: Plain-English, grounded directly in the bill image. Numerical answers state exact values in `PKR` or `units` (kWh). Projections (Q10, Q11, Q12) are labeled as estimates.

---

## 8. AI Usage & Compliance Disclosure

In compliance with competition guidelines:

1. **Multimodal LLM**: Google Gemini 3.5 Flash-Lite (`gemini-3.5-flash-lite`) accessed via the official Google AI Studio REST endpoint (`https://generativelanguage.googleapis.com/v1beta/models/...:generateContent`).
2. **Third-Party Extraction Services**: No commercial invoice or document extraction APIs (such as AWS Textract, Azure Document Intelligence, Mindee, or Google Document AI) were used.
3. **Local OCR Libraries**: No local optical character recognition libraries (such as Tesseract or EasyOCR) were utilized; all extraction is handled end-to-end multimodally by Gemini.
4. **Development Assistants**: Antigravity AI coding assistant was used during development for codebase auditing, architecture planning, error-handling logic, and UI theme design.

---

## 9. Security, Privacy & Limitations

### Security & Privacy
- **Zero API Key Leaks**: Credentials are read strictly from Streamlit Cloud Secrets, `.env`, or system environment variables, and are excluded from Git commits via `.gitignore`.
- **Pre-flight Archive Guard**: `package_submission.py` checks archive contents before creation and raises an exception if any secret file or real `.env` is detected.
- **PII Redaction**:
  - Whitelist schema filtering ensures personal names, addresses, and consumer numbers are not stored in `level1.csv`.
  - Regex sanitization (`scrub_pii`) in `qa_engine.py` removes CNIC numbers (`\d{5}-\d{7}-\d`) and 14-digit account references from responses.

### Limitations
- **Image Quality Dependence**: Low-resolution, blurred, or obscured bill scans can impact multimodal token recognition. When values are concealed behind grey security boxes, the engine explicitly reports them as unavailable.
- **Historical Billing Context**: Answers to multi-month questions (e.g., Q2, Q5, Q7, Q9) rely exclusively on the printed 12/13-month billing history table and chart on the bill.
- **Evaluation Benchmark**: Accuracy should be measured against ground-truth contest evaluation benchmarks rather than ungrounded estimates.

---

## 10. Acknowledgments

Developed for the **Women Tech Quest 2026** competition organized by **10Pearls**. Special thanks to the 10Pearls team for organizing WTQ and empowering women in technology and AI innovation.
