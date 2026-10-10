# WTQ Utility Bill Decoder

[![Women Tech Quest 2026](https://img.shields.io/badge/WTQ%202026-Build%20Track-8050B8)](https://womentechquest.10pearls.com/)
[![Organized by 10Pearls](https://img.shields.io/badge/Organized%20By-10Pearls-35B6C8)](https://10pearls.com/)
[![Python Version](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-F7C928)](https://www.python.org/)
[![Model](https://img.shields.io/badge/Gemini-3.5--flash--lite-0E7490)](https://aistudio.google.com/)
[![License](https://img.shields.io/badge/License-MIT-gray.svg)](LICENSE)

An AI-powered electricity bill decoder built for **Women Tech Quest 2026 (Build Track)**, organized by **10Pearls**. Extracts structured billing data from Pakistani electricity bills (K-Electric, LESCO, IESCO) and provides grounded, plain-English answers to customer questions using multimodal Google Gemini.

---

## 1. Project Overview & Architecture

Pakistani utility bills feature dense visual layouts, varying bilingual terminology (English & Urdu), greyed-out PII boxes, multi-tiered tariff slabs, and complex surcharges (FPA, QTA, electricity duty, sales tax).

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
              |  - Interactive Web Dashboard (app.py)  |
              |  - Batch CLI (batch_processor.py)      |
              |  - Submission Packager (< 15 MB ZIP)   |
              +----------------------------------------+
```

### Key Capabilities
- **Level 1 (Structured Extraction)**: Extracts exactly the 18 required schema fields into clean, single-line RFC 4180 JSON. Enforces date normalization (`YYYY-MM-DD`, `YYYY-MM`), numeric parsing, and negative signs for subsidies.
- **Level 2 (Bill-Grounded Q&A)**: Answers customer questions (Q1–Q12) strictly grounded in the bill image and extracted data. Computes math (historical averages, summer vs. winter differences, late surcharges) without hallucinating external rates.
- **Privacy & PII Protection**: Strict key whitelisting and regex-based redaction ensure customer names, addresses, CNICs, and 14-digit reference numbers are never exposed.
- **Interactive Web Dashboard**: Built with Python's standard library `http.server` and a responsive glassmorphism UI styled in the official Women Tech Quest palette (Purple `#8050B8`, Teal `#35B6C8`, Yellow `#F7C928`).
- **Pre-flight Submission Validator**: Automatically validates row counts, schemas, and archive size before bundling `your-submission.zip` (< 15 MB limit).

---

## 2. Technology Stack

| Component | Technology | Rationale |
| :--- | :--- | :--- |
| **Language** | Python 3.11+ (Tested on 3.13) | Modern standard runtime |
| **Web Framework** | Python Standard Library (`http.server`) | Lightweight, portable, zero heavy web framework dependencies |
| **Multimodal LLM** | Gemini 3.5 Flash-Lite (`gemini-3.5-flash-lite`) | High accuracy, fast vision inference, competition-approved |
| **API Client** | Native Standard Library (`urllib.request`) | Zero dependency, exponential backoff on HTTP 429/503 |
| **Frontend** | Vanilla HTML5 / CSS3 / JavaScript | Modern glassmorphism UI, zero node/npm build overhead |
| **Deployment** | Standalone Python Process / Procfile / Docker | Container and cloud-platform ready (Render, Railway, Fly.io, etc.) |

---

## 3. Project Directory Structure

```
wtq-utility-bill-decoder/
├── app.py                   # Web dashboard & REST API server (Python http.server)
├── batch_processor.py       # Automated batch CLI for Level 1 & Level 2 CSVs
├── check_bills.py           # Quick utility script to inspect bill extractions
├── extractor.py             # Level 1 bill extraction engine & schema validator
├── gemini_client.py         # Resilient Gemini multimodal API client
├── package_submission.py    # Official submission packager & ZIP validator
├── qa_engine.py             # Level 2 grounded question-answering engine
├── run_dashboard.bat        # Windows one-click launcher for web dashboard
├── run_test_batch.bat       # Windows one-click launcher for batch processing
├── run_test_batch.py        # Pipeline orchestrator for test data
├── test_solution.py         # End-to-end verification test suite
├── Dockerfile               # Production container definition
├── Procfile                 # Cloud deployment start command (web: python app.py)
├── requirements.txt         # Minimal Python dependencies
├── .env.example             # Template for required environment variables
├── .gitignore               # Excludes secrets (.env), venv, caches, and archives
├── data/                    # Dataset directory
│   ├── test data/           # Official test dataset (10 bills & template CSVs)
│   └── train data/          # Reference training bills
└── output/                  # Generated competition deliverables
    ├── level1.csv           # 10 rows of extracted JSON
    └── level2.csv           # 120 rows of grounded Q&A
```

---

## 4. Installation & Setup

### Prerequisites
- Python 3.11 or later (compatible with Python 3.12 and 3.13)
- Windows PowerShell, Command Prompt, or Linux/macOS terminal
- Google AI Studio API Key ([Get an API Key](https://aistudio.google.com/app/apikey))

### Step 1: Clone the Repository
```bash
git clone https://github.com/your-username/wtq-utility-bill-decoder.git
cd wtq-utility-bill-decoder
```

### Step 2: Set Up Virtual Environment (Windows)
```powershell
# Create virtual environment
python -m venv .venv

# Activate in PowerShell
.venv\Scripts\Activate.ps1

# (Or in Command Prompt)
# .venv\Scripts\activate.bat
```

*(On Linux / macOS)*:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies
The core pipeline runs on Python standard libraries. Helper packages can be installed via:
```powershell
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Copy `.env.example` to create your local `.env`:
```powershell
copy .env.example .env     # Windows
# cp .env.example .env     # Linux / macOS
```

Open `.env` and set your Google AI Studio API key:
```env
MODEL_PROVIDER=google
MODEL_NAME=gemini-3.5-flash-lite
API_KEY=your_actual_google_ai_studio_api_key_here
PORT=5000
HOST=127.0.0.1
```

> [!WARNING]
> Never commit your `.env` file or publish your API keys. The `.gitignore` file is pre-configured to keep your credentials safe.

---

## 5. Usage & Execution

### 1. Launch the Interactive Web Dashboard

#### Option A: Streamlit Edition (Recommended for Streamlit Cloud & Modern UI)
```powershell
streamlit run streamlit_app.py
```
*Or double-click `run_streamlit.bat` on Windows.*
Open your web browser at: **`http://localhost:8501`**

#### Option B: Native Python HTTP Server
```powershell
python app.py
```
*Or double-click `run_dashboard.bat` on Windows.*
Open your web browser at: **`http://127.0.0.1:5000`**

**Dashboard Features:**
- **Bill Explorer**: Browse test bills or upload new bills, run Level 1 extraction with metric cards and tables, and ask grounded questions in real time.
- **Batch Processor**: Trigger batch processing of test bills directly from the browser with CSV download buttons.
- **Submission Packager**: Run pre-flight checks and package your submission ZIP with one-click download.

---


### 2. Run Batch Processing via CLI
To process all test bills and generate `output/level1.csv` and `output/level2.csv`:
```powershell
python run_test_batch.py
```
*Or double-click `run_test_batch.bat` on Windows.*

You can also run `batch_processor.py` with custom arguments:
```powershell
python batch_processor.py \
  --bills "data/test data/bills" \
  --l1-template "data/test data/csv/level1.csv" \
  --l2-template "data/test data/csv/level2.csv" \
  --output-dir "output"
```

---

### 3. Run the Automated Test Suite
To validate schema parsing, CSV formatting compliance, output deliverables, and archive packaging:
```powershell
python test_solution.py
```

Expected test suite output:
```
Test 1: Validating schema parsing on KESC_0008 reference JSON...
  [PASS] Schema validation passed!
Test 2: Verifying CSV quoting and single-line JSON format...
  [PASS] CSV formatting test passed!
Test 3: Validating competition deliverables in output/ folder...
  [PASS] output/level1.csv verified (exactly 10 bills, valid 18-key JSON)
  [PASS] output/level2.csv verified (exactly 120 rows, 0 empty answers)
Test 4: Packaging and validating your-submission.zip...
  [PASS] Size check: Archive is strictly under 15 MB.
  [PASS] your-submission.zip verified (0.04 MB, perfect archive structure, 0 secret leaks)

=======================================================
  ALL VERIFICATION TESTS PASSED SUCCESSFULLY!
=======================================================
```

---

### 4. Package Official Submission ZIP
```powershell
python package_submission.py
```
Validates the CSV files and generates `your-submission.zip` matching the required structure:
- `output/level1.csv`
- `output/level2.csv`
- `source/` (all core `.py` scripts, `README.md`, `.env.example`, `requirements.txt`)
- `demo/` (optional demo video)

---

## 6. Expected Output Schemas

### Level 1 Output (`output/level1.csv`)
- **Row Count**: 10 rows (1 per test bill)
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
- **Row Count**: 120 rows (10 bills × 12 questions Q1–Q12)
- **Columns**: `bill_id,question_id,question,answer`
- **Answers**: Plain-English, grounded directly in the bill image. Numerical answers state exact values in `PKR` or `units` (kWh). Projections (Q10, Q11, Q12) are labeled as estimates.

---

## 7. Cloud Deployment Guide

The application can be deployed via **Streamlit Community Cloud** (recommended) or as a container / standalone web service.

### Option A: Streamlit Community Cloud (Recommended)
1. Sign in to [share.streamlit.io](https://share.streamlit.io/) with your GitHub account.
2. Click **New app**.
3. Select your repository: `kainatmoin/Women-Teach-Quest-10pearls-Utility-Bill-Decoder`
4. Set **Branch**: `main`
5. Set **Main file path**: `streamlit_app.py`
6. Click **Advanced settings...** and add your secrets:
   ```toml
   API_KEY = "your_actual_google_ai_studio_api_key"
   MODEL_NAME = "gemini-3.5-flash-lite"
   MODEL_PROVIDER = "google"
   ```
7. Click **Deploy!** Your interactive app will be live with full functionality.

### Option B: Render / Railway / Heroku
To deploy the native HTTP server (`app.py`):
1. Connect your repository to Render, Railway, or Heroku (the included `Procfile` specifies `web: python app.py`).
2. Set environment variables in the dashboard:
   - `API_KEY` = *your_google_ai_studio_api_key*
   - `MODEL_NAME` = `gemini-3.5-flash-lite`
   - `MODEL_PROVIDER` = `google`
3. Deploy service and verify the `/health` endpoint.


### Option C: Docker Container
Build and run locally or on any cloud container engine:
```bash
# Build Docker image
docker build -t wtq-utility-bill-decoder .

# Run container with API key
docker run -d -p 5000:5000 \
  -e API_KEY="your_actual_api_key_here" \
  wtq-utility-bill-decoder
```
Test health check:
```bash
curl http://localhost:5000/health
```

> [!NOTE]
> No live cloud deployment URL is currently active. The steps above describe the exact procedure to launch an instance on demand.

---

## 8. AI Usage & Compliance Disclosure

In compliance with competition guidelines:

1. **Multimodal LLM**: Google Gemini 3.5 Flash-Lite (`gemini-3.5-flash-lite`) accessed via the official Google AI Studio REST endpoint (`https://generativelanguage.googleapis.com/v1beta/models/...:generateContent`).
2. **Third-Party Extraction Services**: No commercial invoice or document extraction APIs (such as AWS Textract, Azure Document Intelligence, Mindee, or Google Document AI) were used.
3. **Local OCR Libraries**: No local optical character recognition libraries (such as Tesseract or EasyOCR) were utilized; all extraction is handled end-to-end multimodally by Gemini.
4. **Development Assistants**: Antigravity AI coding assistant was used during development for codebase auditing, architecture planning, error-handling logic, and UI styling.

---

## 9. Security, Privacy & Limitations

### Security & Privacy
- **Zero API Key Leaks**: Credentials are read strictly from `.env` or system environment variables and are excluded from Git commits via `.gitignore`.
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

Developed for the **Women Tech Quest 2026** competition organized by **10Pearls**. Special thanks to the 10Pearls team for organizing WTQ and fostering women's talent in technology and AI innovation.
