"""
=============================================================================
WTQ 2026 Utility Bill Decoder — Streamlit Edition
Women Tech Quest 2026 | Build Track | Organized by 10Pearls
=============================================================================
Recreates the Women Tech Quest visual identity in Streamlit:
- Primary Purple: #8050B8
- Deep Purple: #57338C
- Teal: #35B6C8
- Deep Teal: #0E7490
- Warm Yellow: #F7C928
- Glassmorphism cards, blurred floating gradient orbs, animated transitions
=============================================================================
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional

import streamlit as st

# Import core business-logic modules (zero duplication)
from gemini_client import GeminiClient, load_env_file, ALLOWED_MODELS
from extractor import extract_bill_details, REQUIRED_FIELDS
from qa_engine import answer_question
from batch_processor import process_level1, process_level2
from package_submission import create_submission_zip

# ---------------------------------------------------------------------------
# Streamlit Community Cloud Secret Synchronization
# ---------------------------------------------------------------------------
def sync_secrets():
    """Ensure Streamlit Cloud secrets are available in os.environ for GeminiClient."""
    try:
        if hasattr(st, "secrets"):
            for key in ["API_KEY", "GEMINI_API_KEY", "MODEL_NAME", "MODEL_PROVIDER"]:
                if key in st.secrets and key not in os.environ:
                    os.environ[key] = str(st.secrets[key])
    except Exception:
        pass

sync_secrets()

# ---------------------------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="WTQ 2026 Utility Bill Decoder",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------------------------
# Custom CSS — WTQ 2026 Glassmorphism & Animated Theme
# ---------------------------------------------------------------------------
WTQ_CUSTOM_CSS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">

<style>
  :root {
    --wtq-purple: #8050B8;
    --wtq-purple-deep: #57338C;
    --wtq-purple-light: rgba(128, 80, 184, 0.1);
    --wtq-teal: #35B6C8;
    --wtq-teal-deep: #0E7490;
    --wtq-teal-light: rgba(53, 182, 200, 0.12);
    --wtq-yellow: #F7C928;
    --wtq-yellow-deep: #B45309;
    --wtq-yellow-light: rgba(247, 201, 40, 0.2);
    --bg-base: #FAF9F6;
    --bg-glass: rgba(255, 255, 255, 0.88);
    --bg-glass-elevated: rgba(255, 255, 255, 0.95);
    --border-glass: rgba(255, 255, 255, 0.8);
    --border-subtle: rgba(128, 80, 184, 0.15);
    --text-main: #252535;
    --text-muted: #57556A;
    --text-light: #8E8BA0;
    --accent-success: #10B981;
    --accent-danger: #EF4444;
    --card-radius: 18px;
    --shadow-glass: 0 10px 30px -5px rgba(87, 51, 140, 0.08), 0 4px 14px rgba(53, 182, 200, 0.05);
  }

  /* Global Typography */
  html, body, [class*="css"], [class*="st-"] {
    font-family: 'Outfit', sans-serif !important;
    color: var(--text-main);
  }

  /* Animated Multi-Gradient Background */
  .stApp {
    background: linear-gradient(135deg, #F3EEF9 0%, #FAF9F6 28%, #EBF8FA 68%, #FEF9EB 100%) !important;
    background-size: 300% 300% !important;
    animation: bgGradientShift 20s ease infinite alternate !important;
  }

  @keyframes bgGradientShift {
    0% { background-position: 0% 40%; }
    50% { background-position: 100% 60%; }
    100% { background-position: 0% 40%; }
  }

  /* Header Branding Banner */
  .wtq-banner {
    background: linear-gradient(135deg, #57338C 0%, #8050B8 48%, #35B6C8 100%);
    border-bottom: 3.5px solid var(--wtq-yellow);
    border-radius: 16px;
    padding: 1.4rem 2rem;
    margin-bottom: 1.8rem;
    box-shadow: 0 10px 28px rgba(87, 51, 140, 0.22);
    display: flex;
    justify-content: space-between;
    align-items: center;
    color: white;
  }
  .wtq-title-wrap {
    display: flex;
    align-items: center;
    gap: 16px;
  }
  .wtq-logo-icon {
    width: 52px;
    height: 52px;
    background: rgba(255, 255, 255, 0.2);
    border: 1.5px solid rgba(255, 255, 255, 0.45);
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 26px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.15);
  }
  .wtq-header-title {
    font-size: 1.65rem;
    font-weight: 800;
    line-height: 1.2;
    color: #FFFFFF !important;
    margin: 0;
  }
  .wtq-header-subtitle {
    font-size: 0.95rem;
    color: rgba(255, 255, 255, 0.92);
    margin: 3px 0 0 0;
  }
  .wtq-badge-event {
    background: rgba(247, 201, 40, 0.25);
    border: 1px solid var(--wtq-yellow);
    color: #FFFDF0;
    padding: 6px 14px;
    border-radius: 30px;
    font-size: 0.82rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  /* Glassmorphism Cards */
  .glass-card {
    background: var(--bg-glass);
    backdrop-filter: blur(14px);
    border: 1px solid var(--border-subtle);
    border-radius: var(--card-radius);
    padding: 1.5rem;
    margin-bottom: 1.3rem;
    box-shadow: var(--shadow-glass);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
  }
  .glass-card:hover {
    box-shadow: 0 14px 34px -5px rgba(87, 51, 140, 0.12);
  }

  /* Section Titles */
  .section-title {
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--wtq-purple-deep);
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 1rem;
  }

  /* Metric Card Grid */
  .metric-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 12px;
    margin-bottom: 1.2rem;
  }
  .metric-card {
    background: rgba(255, 255, 255, 0.85);
    border: 1px solid rgba(128, 80, 184, 0.14);
    border-radius: 14px;
    padding: 12px 14px;
    box-shadow: 0 4px 12px rgba(87, 51, 140, 0.04);
  }
  .metric-label {
    font-size: 0.76rem;
    text-transform: uppercase;
    font-weight: 700;
    letter-spacing: 0.4px;
    color: var(--text-muted);
    margin-bottom: 4px;
  }
  .metric-value {
    font-size: 1.25rem;
    font-weight: 800;
    color: var(--wtq-purple-deep);
    font-family: 'JetBrains Mono', monospace !important;
  }
  .metric-value.highlight-teal {
    color: var(--wtq-teal-deep);
  }
  .metric-value.highlight-red {
    color: var(--accent-danger);
  }
  .metric-value.highlight-green {
    color: var(--accent-success);
  }

  /* Breakdown Tables */
  .styled-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.88rem;
    margin-top: 6px;
    background: rgba(255, 255, 255, 0.7);
    border-radius: 10px;
    overflow: hidden;
  }
  .styled-table th {
    background: var(--wtq-purple-light);
    color: var(--wtq-purple-deep);
    font-weight: 700;
    text-align: left;
    padding: 8px 12px;
  }
  .styled-table td {
    padding: 8px 12px;
    border-top: 1px solid rgba(128, 80, 184, 0.08);
  }
  .styled-table tr:hover {
    background: rgba(53, 182, 200, 0.06);
  }
  .table-num {
    font-family: 'JetBrains Mono', monospace !important;
    text-align: right;
    font-weight: 600;
  }

  /* Answer Card */
  .answer-card {
    background: linear-gradient(135deg, rgba(235, 248, 250, 0.95) 0%, rgba(243, 238, 249, 0.95) 100%);
    border-left: 5px solid var(--wtq-teal);
    border-radius: 14px;
    padding: 1.3rem;
    margin-top: 1rem;
    box-shadow: 0 6px 20px rgba(53, 182, 200, 0.1);
  }
  .answer-title {
    font-weight: 800;
    color: var(--wtq-teal-deep);
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 1.02rem;
  }
  .answer-body {
    font-size: 1rem;
    line-height: 1.6;
    color: var(--text-main);
  }

  /* Streamlit Button Styling */
  div.stButton > button:first-child {
    background: linear-gradient(135deg, #8050B8 0%, #57338C 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.55rem 1.4rem !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    box-shadow: 0 4px 14px rgba(128, 80, 184, 0.3) !important;
    transition: all 0.2s ease !important;
  }
  div.stButton > button:first-child:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(87, 51, 140, 0.4) !important;
  }

  /* Secondary / Teal action buttons */
  .btn-teal div.stButton > button:first-child {
    background: linear-gradient(135deg, #35B6C8 0%, #0E7490 100%) !important;
    box-shadow: 0 4px 14px rgba(53, 182, 200, 0.3) !important;
  }

  /* Tab Header Styling */
  .stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    border-bottom: 2px solid rgba(128, 80, 184, 0.15);
    padding-bottom: 4px;
  }
  .stTabs [data-baseweb="tab"] {
    background: rgba(255, 255, 255, 0.7);
    border-radius: 10px 10px 0 0;
    padding: 8px 18px;
    font-weight: 600;
    color: var(--text-muted);
    border: 1px solid rgba(128, 80, 184, 0.1);
    border-bottom: none;
  }
  .stTabs [aria-selected="true"] {
    background: white !important;
    color: var(--wtq-purple-deep) !important;
    font-weight: 800 !important;
    border-top: 3px solid var(--wtq-purple) !important;
  }

  /* Code block styling */
  pre, code {
    font-family: 'JetBrains Mono', monospace !important;
  }
</style>
"""

st.markdown(WTQ_CUSTOM_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Helper: Scan Available Bills
# ---------------------------------------------------------------------------
def get_available_bills() -> Dict[str, str]:
    """Find sample bill images in project directories."""
    candidates = [
        "data/test data/bills",
        "data/train data",
        "test/bills",
        "data"
    ]
    bills = {}
    for d in candidates:
        p = Path(d)
        if p.exists() and p.is_dir():
            for f in sorted(p.iterdir()):
                if f.suffix.lower() in [".png", ".jpg", ".jpeg"]:
                    provider = "KE" if "KESC" in f.stem.upper() or "KE" in f.stem.upper() else ("LESCO" if "LESCO" in f.stem.upper() else "IESCO")
                    label = f"{f.stem} ({provider} - {f.parent.name})"
                    if label not in bills:
                        bills[label] = str(f)
    return bills

# ---------------------------------------------------------------------------
# Sidebar: System Status & API Configuration
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 10px 0 15px 0;">
      <div style="font-size: 32px;">⚡</div>
      <div style="font-size: 1.25rem; font-weight: 800; color: #57338C;">Women Tech Quest 2026</div>
      <div style="font-size: 0.85rem; color: #57556A; font-weight: 600;">10Pearls Build Track</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🔌 System Status")

    env_vars = load_env_file()
    active_api_key = (
        os.environ.get("API_KEY")
        or env_vars.get("API_KEY")
        or os.environ.get("GEMINI_API_KEY")
        or env_vars.get("GEMINI_API_KEY")
    )
    active_model = os.environ.get("MODEL_NAME") or env_vars.get("MODEL_NAME", "gemini-3.5-flash-lite")

    if active_api_key and len(active_api_key.strip()) > 5:
        st.success(f"✓ Gemini API Key Loaded\n\n**Model**: `{active_model}`")
    else:
        st.warning("⚠️ API Key not detected in `.env` or Streamlit Secrets.")
        user_key = st.text_input("Enter Google AI Studio Key:", type="password", key="sidebar_key_input")
        if user_key:
            os.environ["API_KEY"] = user_key.strip()
            st.rerun()

    st.markdown("---")
    st.markdown("""
    **Quick Reference:**
    - **Level 1**: 18-key RFC 4180 JSON
    - **Level 2**: 12 grounded answers (Q1–Q12)
    - **Utilities**: K-Electric, LESCO, IESCO
    - **Theme**: Official WTQ Purple / Teal / Gold
    """)

    st.markdown("---")
    st.caption("Organized by 10Pearls for WTQ 2026. Multimodal vision with Gemini 3.5 Flash-Lite.")

# ---------------------------------------------------------------------------
# Header Banner
# ---------------------------------------------------------------------------
st.markdown("""
<div class="wtq-banner">
  <div class="wtq-title-wrap">
    <div class="wtq-logo-icon">⚡</div>
    <div>
      <h1 class="wtq-header-title">WTQ 2026 Utility Bill Decoder</h1>
      <p class="wtq-header-subtitle">AI-Powered Electricity Bill Extraction & Grounded Customer Q&A Dashboard</p>
    </div>
  </div>
  <div class="wtq-badge-event">Women Tech Quest 2026</div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Navigation Tabs
# ---------------------------------------------------------------------------
tab_explorer, tab_batch, tab_packager = st.tabs([
    "🔍 Bill Explorer & Analyzer",
    "⚙️ Batch CSV Processor",
    "📦 Submission Packager"
])

# Initialize session state for analysis results
if "extracted_data" not in st.session_state:
    st.session_state.extracted_data = None
if "current_image_path" not in st.session_state:
    st.session_state.current_image_path = None
if "qa_answer" not in st.session_state:
    st.session_state.qa_answer = None
if "qa_question" not in st.session_state:
    st.session_state.qa_question = "Is this a net-metered (solar) connection or a standard connection? How did you tell?"


# ===========================================================================
# TAB 1: BILL EXPLORER & ANALYZER
# ===========================================================================
with tab_explorer:
    col_input, col_view = st.columns([1, 1], gap="medium")

    # --- Left Column: Bill Selection & Image Preview ---
    with col_input:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title"><span>📑</span> Select or Upload Utility Bill</div>', unsafe_allow_html=True)

        source_mode = st.radio(
            "Bill Source",
            ["Sample Competition Bills", "Upload New Bill Image"],
            horizontal=True,
            label_visibility="collapsed"
        )

        chosen_path = None
        available_bills = get_available_bills()

        if source_mode == "Sample Competition Bills":
            if available_bills:
                selected_label = st.selectbox(
                    "Choose a test bill:",
                    list(available_bills.keys()),
                    index=0
                )
                chosen_path = available_bills[selected_label]
            else:
                st.warning("No sample bills found in `data/test data/bills`.")
        else:
            uploaded_file = st.file_uploader(
                "Upload a Pakistani Electricity Bill (PNG, JPG, JPEG):",
                type=["png", "jpg", "jpeg"]
            )
            if uploaded_file:
                # Save to temporary scratch location
                temp_dir = Path("scratch")
                temp_dir.mkdir(exist_ok=True)
                temp_path = temp_dir / uploaded_file.name
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                chosen_path = str(temp_path)

        if chosen_path and os.path.exists(chosen_path):
            st.session_state.current_image_path = chosen_path
            st.image(chosen_path, caption=f"Selected: {Path(chosen_path).name}", use_container_width=True)

            if st.button("⚡ Extract Level 1 Bill Details", use_container_width=True):
                with st.spinner("Extracting Level 1 fields via Gemini Multimodal..."):
                    try:
                        client = GeminiClient()
                        data = extract_bill_details(chosen_path, client=client)
                        st.session_state.extracted_data = data
                        st.success("Extraction complete!")
                    except Exception as e:
                        st.error(f"Extraction error: {e}")

        st.markdown('</div>', unsafe_allow_html=True)

    # --- Right Column: Extraction Results & Grounded Q&A ---
    with col_view:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title"><span>📊</span> Extracted Bill Metrics (Level 1)</div>', unsafe_allow_html=True)

        d = st.session_state.extracted_data

        if d:
            # Metric Cards
            p_val = d.get('provider') or 'null'
            t_val = d.get('tariff') or 'null'
            load_val = f"{d.get('sanctioned_load_kw')} kW" if d.get('sanctioned_load_kw') is not None else 'null'
            m_val = d.get('bill_month') or 'null'
            units_val = f"{d.get('units_consumed')}" if d.get('units_consumed') is not None else 'null'
            bill_val = f"Rs. {d.get('current_bill'):,}" if d.get('current_bill') is not None else 'null'

            arr = d.get('arrears')
            if arr is not None:
                arr_cls = "highlight-green" if arr < 0 else "highlight-red" if arr > 0 else ""
                arr_val = f"Rs. {arr:,}"
            else:
                arr_cls = ""
                arr_val = "null"

            due_val = d.get('due_date') or 'null'
            p_within = f"Rs. {d.get('payable_within_due_date'):,}" if d.get('payable_within_due_date') is not None else 'null'
            p_after = f"Rs. {d.get('payable_after_due_date'):,}" if d.get('payable_after_due_date') is not None else 'null'

            st.markdown(f"""
            <div class="metric-grid">
              <div class="metric-card">
                <div class="metric-label">Provider</div>
                <div class="metric-value">{p_val}</div>
              </div>
              <div class="metric-card">
                <div class="metric-label">Tariff</div>
                <div class="metric-value">{t_val}</div>
              </div>
              <div class="metric-card">
                <div class="metric-label">Sanctioned Load</div>
                <div class="metric-value">{load_val}</div>
              </div>
              <div class="metric-card">
                <div class="metric-label">Billing Month</div>
                <div class="metric-value">{m_val}</div>
              </div>
              <div class="metric-card">
                <div class="metric-label">Units Consumed</div>
                <div class="metric-value highlight-teal">{units_val}</div>
              </div>
              <div class="metric-card">
                <div class="metric-label">Current Bill</div>
                <div class="metric-value">{bill_val}</div>
              </div>
              <div class="metric-card">
                <div class="metric-label">Arrears / Credit</div>
                <div class="metric-value {arr_cls}">{arr_val}</div>
              </div>
              <div class="metric-card">
                <div class="metric-label">Due Date</div>
                <div class="metric-value">{due_val}</div>
              </div>
              <div class="metric-card">
                <div class="metric-label">Within Due Date</div>
                <div class="metric-value highlight-teal">{p_within}</div>
              </div>
              <div class="metric-card">
                <div class="metric-label">After Due Date</div>
                <div class="metric-value highlight-red">{p_after}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            # Charges & Taxes Breakdowns
            sub_col1, sub_col2 = st.columns(2)

            with sub_col1:
                st.markdown("**Charges Breakdown:**")
                charges = d.get("charges", [])
                if charges:
                    rows_html = "".join([
                        f"<tr><td>{c.get('type')}</td><td class='table-num {'highlight-green' if c.get('amount', 0) < 0 else ''}'>{c.get('amount', 0):,}</td></tr>"
                        for c in charges
                    ])
                    tot_charges = f"Rs. {d.get('total_charges'):,}" if d.get('total_charges') is not None else "null"
                    st.markdown(f"""
                    <table class="styled-table">
                      <thead><tr><th>Charge Type</th><th style="text-align: right;">Amount (PKR)</th></tr></thead>
                      <tbody>{rows_html}</tbody>
                      <tfoot><tr><th colspan="2" style="text-align: right;">Total: {tot_charges}</th></tr></tfoot>
                    </table>
                    """, unsafe_allow_html=True)
                else:
                    st.caption("No itemized charges visible or covered by security box.")

            with sub_col2:
                st.markdown("**Taxes Breakdown:**")
                taxes = d.get("taxes", [])
                if taxes:
                    rows_html = "".join([
                        f"<tr><td>{t.get('type')}</td><td class='table-num'>{t.get('amount', 0):,}</td></tr>"
                        for t in taxes
                    ])
                    tot_taxes = f"Rs. {d.get('total_taxes'):,}" if d.get('total_taxes') is not None else "null"
                    st.markdown(f"""
                    <table class="styled-table">
                      <thead><tr><th>Tax Type</th><th style="text-align: right;">Amount (PKR)</th></tr></thead>
                      <tbody>{rows_html}</tbody>
                      <tfoot><tr><th colspan="2" style="text-align: right;">Total: {tot_taxes}</th></tr></tfoot>
                    </table>
                    """, unsafe_allow_html=True)
                else:
                    st.caption("Combined in total taxes or not visible.")

            # Raw JSON Expander
            with st.expander("📄 View & Download Raw Level 1 JSON"):
                json_str = json.dumps(d, indent=2)
                st.code(json_str, language="json")
                st.download_button(
                    "💾 Download JSON File",
                    data=json_str,
                    file_name=f"{Path(st.session_state.current_image_path).stem}_level1.json",
                    mime="application/json"
                )

        else:
            st.info("Select a bill image and click **Extract Level 1 Bill Details** to populate structured metrics.")

        st.markdown('</div>', unsafe_allow_html=True)

    # --- Grounded Q&A Assistant (Full Width) ---
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title"><span>💬</span> Ask Bill-Grounded Question (Level 2)</div>', unsafe_allow_html=True)

    st.markdown("**Quick Preset Questions:**")
    quick_questions = [
        ("☀️ Net-metering?", "Is this a net-metered (solar) connection or a standard connection? How did you tell?"),
        ("💸 Total taxes?", "How much total tax is charged on this bill, and what is the breakdown of electricity duty vs GST?"),
        ("📈 Peak usage month?", "Which month in the last 12 months had the highest units consumed?"),
        ("🌡️ Summer vs Winter?", "How many more units do I consume in summer (June-August) than in winter (December-February)?"),
        ("⏰ Late surcharge?", "If I dont pay on time, what late payment surcharges will be added?"),
    ]

    q_cols = st.columns(len(quick_questions))
    for idx, (label, text) in enumerate(quick_questions):
        if q_cols[idx].button(label, key=f"btn_chip_{idx}", use_container_width=True):
            st.session_state.qa_question = text

    user_q = st.text_input(
        "Question about the bill:",
        value=st.session_state.qa_question,
        placeholder="Ask anything about rates, taxes, or history..."
    )

    if st.button("🤖 Ask AI Assistant", use_container_width=True):
        if not st.session_state.current_image_path:
            st.warning("Please select or upload a bill image first.")
        elif not user_q.strip():
            st.warning("Please enter a question.")
        else:
            with st.spinner("Analyzing bill image and generating grounded calculation..."):
                try:
                    client = GeminiClient()
                    ans = answer_question(
                        question=user_q.strip(),
                        image_path=st.session_state.current_image_path,
                        extracted_json=st.session_state.extracted_data,
                        client=client
                    )
                    st.session_state.qa_answer = ans
                except Exception as e:
                    st.error(f"Error answering question: {e}")

    if st.session_state.qa_answer:
        st.markdown(f"""
        <div class="answer-card">
          <div class="answer-title">
            <span>✓</span> Plain English Answer (Grounded in Bill):
          </div>
          <div class="answer-body">{st.session_state.qa_answer}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ===========================================================================
# TAB 2: BATCH CSV PROCESSOR
# ===========================================================================
with tab_batch:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title"><span>⚙️</span> Batch CSV Processor (Level 1 & Level 2)</div>', unsafe_allow_html=True)

    st.markdown("""
    Executes automated batch extraction and grounded question answering across test bills,
    generating **`output/level1.csv`** (10 bills) and **`output/level2.csv`** (120 questions) conforming strictly to RFC 4180.
    """)

    b_col1, b_col2, b_col3 = st.columns(3)
    b_col1.metric("Level 1 Target", "10 Bills", "18 Keys RFC 4180")
    b_col2.metric("Level 2 Target", "120 Questions", "Q1 – Q12 Grounded")
    b_col3.metric("Format Compliance", "Double Quoted", "Single-line JSON")

    st.markdown("---")
    bills_dir_input = st.text_input("Bills Directory:", value="data/test data/bills")
    l1_temp_input = st.text_input("Level 1 Template CSV:", value="data/test data/csv/level1.csv")
    l2_temp_input = st.text_input("Level 2 Template CSV:", value="data/test data/csv/level2.csv")

    if st.button("🚀 Run Official Test Batch Generation", use_container_width=True):
        status_box = st.empty()
        status_box.info("Starting batch processing pipeline...")
        try:
            client = GeminiClient()
            t0 = time.time()
            l1_res = process_level1(
                bills_dir=bills_dir_input,
                template_csv=l1_temp_input if os.path.exists(l1_temp_input) else None,
                output_csv="output/level1.csv",
                client=client
            )
            if os.path.exists(l2_temp_input):
                process_level2(
                    bills_dir=bills_dir_input,
                    template_csv=l2_temp_input,
                    output_csv="output/level2.csv",
                    extracted_data_map=l1_res,
                    client=client
                )
            elapsed = time.time() - t0
            status_box.success(f"Batch processing completed successfully in {elapsed:.1f}s!")
        except Exception as e:
            status_box.error(f"Batch process error: {e}")

    # Download Deliverables
    st.markdown("### 📥 Generated Deliverables")
    d_col1, d_col2 = st.columns(2)

    l1_path = Path("output/level1.csv")
    if l1_path.exists():
        with open(l1_path, "r", encoding="utf-8") as f:
            d_col1.download_button(
                "📥 Download output/level1.csv",
                data=f.read(),
                file_name="level1.csv",
                mime="text/csv",
                use_container_width=True
            )
    else:
        d_col1.caption("level1.csv not yet generated.")

    l2_path = Path("output/level2.csv")
    if l2_path.exists():
        with open(l2_path, "r", encoding="utf-8") as f:
            d_col2.download_button(
                "📥 Download output/level2.csv",
                data=f.read(),
                file_name="level2.csv",
                mime="text/csv",
                use_container_width=True
            )
    else:
        d_col2.caption("level2.csv not yet generated.")

    st.markdown('</div>', unsafe_allow_html=True)


# ===========================================================================
# TAB 3: SUBMISSION PACKAGER
# ===========================================================================
with tab_packager:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title"><span>📦</span> Build Competition Submission ZIP</div>', unsafe_allow_html=True)

    st.markdown("""
    Builds **`your-submission.zip`** conforming strictly to competition guidelines:
    - `output/level1.csv` (10 rows)
    - `output/level2.csv` (120 rows)
    - `source/` (`app.py`, `streamlit_app.py`, `extractor.py`, `qa_engine.py`, `gemini_client.py`, `README.md`, etc.)
    - Excludes secret `.env` and enforces < 15 MB size constraint.
    """)

    st.markdown("""
    **Readiness Checklist:**
    - ✅ `output/level1.csv`: 10 test bills with 18 required JSON keys
    - ✅ `output/level2.csv`: 120 customer questions answered with grounded facts
    - ✅ Zero Credential Leaks: `.env` excluded by security validation
    - ✅ Size Guarantee: strictly verified under the 15 MB limit
    """)

    if st.button("🎁 Validate & Package your-submission.zip", use_container_width=True):
        with st.spinner("Running pre-flight checks and packaging ZIP archive..."):
            try:
                zip_path = create_submission_zip()
                size_mb = os.path.getsize(zip_path) / (1024 * 1024)
                st.success(f"Successfully packaged {zip_path} ({size_mb:.2f} MB)! Ready for submission.")

                with open(zip_path, "rb") as f:
                    st.download_button(
                        "💾 Download your-submission.zip",
                        data=f.read(),
                        file_name="your-submission.zip",
                        mime="application/zip",
                        use_container_width=True
                    )
            except Exception as e:
                st.error(f"Packaging error: {e}")

    st.markdown('</div>', unsafe_allow_html=True)
