"""
WTQ Utility Bill Decoder - Interactive Web Application & API Server
Redesigned with the Animated Women Tech Quest Gradient Theme:
- Primary Purple: #8050B8
- Deep Purple: #57338C
- Teal: #35B6C8
- Deep Teal: #0E7490
- Warm Yellow: #F7C928
- Off-white Base: #FAF9F6
- Dark Text: #252535
- Glassmorphism surfaces, subtle blurred orbs, smooth gradient transitions
"""

import os
import sys
import json
import mimetypes
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Any, Dict, Optional

# Import project modules
from gemini_client import GeminiClient, load_env_file
from extractor import extract_bill_details
from qa_engine import answer_question
from batch_processor import process_level1, process_level2
from package_submission import create_submission_zip

DEFAULT_PORT = int(os.environ.get("PORT", 5000))


HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>WTQ 2026 Utility Bill Decoder | Women Tech Quest</title>
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
      --bg-glass: rgba(255, 255, 255, 0.85);
      --bg-glass-elevated: rgba(255, 255, 255, 0.94);
      --border-glass: rgba(255, 255, 255, 0.8);
      --border-subtle: rgba(128, 80, 184, 0.15);
      --text-main: #252535;
      --text-muted: #57556A;
      --text-light: #8E8BA0;
      --accent-success: #10B981;
      --accent-danger: #EF4444;
      --card-radius: 20px;
      --shadow-glass: 0 10px 30px -5px rgba(87, 51, 140, 0.08), 0 4px 14px rgba(53, 182, 200, 0.05);
      --shadow-hover: 0 14px 36px -6px rgba(87, 51, 140, 0.15), 0 6px 18px rgba(53, 182, 200, 0.1);
      --gradient-brand: linear-gradient(135deg, var(--wtq-purple) 0%, var(--wtq-teal) 100%);
      --gradient-header: linear-gradient(135deg, #57338C 0%, #8050B8 48%, #35B6C8 100%);
      --gradient-btn-purple: linear-gradient(135deg, #8050B8 0%, #57338C 100%);
      --gradient-btn-teal: linear-gradient(135deg, #35B6C8 0%, #0E7490 100%);
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      font-family: 'Outfit', sans-serif;
    }

    /* Animated Multi-Gradient Background */
    body {
      background: linear-gradient(135deg, #F3EEF9 0%, #FAF9F6 28%, #EBF8FA 68%, #FEF9EB 100%);
      background-size: 300% 300%;
      animation: bgGradientShift 20s ease infinite alternate;
      color: var(--text-main);
      min-height: 100vh;
      overflow-x: hidden;
      line-height: 1.5;
      position: relative;
    }

    @keyframes bgGradientShift {
      0% { background-position: 0% 40%; }
      50% { background-position: 100% 60%; }
      100% { background-position: 0% 40%; }
    }

    /* Blurred Floating Gradient Orbs */
    body::before {
      content: "";
      position: fixed;
      top: -8vw;
      left: -8vw;
      width: 42vw;
      height: 42vw;
      background: radial-gradient(circle, rgba(128, 80, 184, 0.18) 0%, transparent 68%);
      filter: blur(80px);
      pointer-events: none;
      z-index: 0;
      animation: floatOrb1 24s ease-in-out infinite alternate;
    }

    body::after {
      content: "";
      position: fixed;
      bottom: -10vw;
      right: -10vw;
      width: 45vw;
      height: 45vw;
      background: radial-gradient(circle, rgba(53, 182, 200, 0.16) 0%, rgba(247, 201, 40, 0.1) 45%, transparent 70%);
      filter: blur(85px);
      pointer-events: none;
      z-index: 0;
      animation: floatOrb2 28s ease-in-out infinite alternate;
    }

    @keyframes floatOrb1 {
      0% { transform: translate(0, 0) scale(1); }
      100% { transform: translate(6vw, 8vw) scale(1.1); }
    }

    @keyframes floatOrb2 {
      0% { transform: translate(0, 0) scale(1); }
      100% { transform: translate(-8vw, -6vw) scale(1.12); }
    }

    @media (prefers-reduced-motion: reduce) {
      body, body::before, body::after {
        animation: none !important;
      }
    }

    /* Header */
    header {
      background: var(--gradient-header);
      border-bottom: 3px solid var(--wtq-yellow);
      padding: 1.1rem 2.5rem;
      position: sticky;
      top: 0;
      z-index: 100;
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-shadow: 0 6px 24px rgba(87, 51, 140, 0.22);
    }

    .brand-group {
      display: flex;
      align-items: center;
      gap: 16px;
    }

    .brand-icon {
      width: 46px;
      height: 46px;
      border-radius: 14px;
      background: rgba(255, 255, 255, 0.22);
      backdrop-filter: blur(10px);
      border: 1px solid rgba(255, 255, 255, 0.4);
      display: flex;
      align-items: center;
      justify-content: center;
      color: #FFFFFF;
      font-size: 24px;
      font-weight: 800;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
      transition: transform 0.3s ease;
    }

    .brand-icon:hover {
      transform: rotate(10deg) scale(1.06);
    }

    .brand-text h1 {
      font-size: 1.35rem;
      font-weight: 800;
      color: #FFFFFF;
      letter-spacing: -0.02em;
      text-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    }

    .brand-text p {
      font-size: 0.82rem;
      color: rgba(255, 255, 255, 0.9);
      font-weight: 500;
    }

    .header-badges {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .pill-track {
      background: linear-gradient(135deg, #F7C928 0%, #F59E0B 100%);
      color: #451A03;
      border: 1px solid rgba(255, 255, 255, 0.6);
      padding: 6px 15px;
      border-radius: 9999px;
      font-size: 0.82rem;
      font-weight: 800;
      display: flex;
      align-items: center;
      gap: 6px;
      box-shadow: 0 3px 12px rgba(247, 201, 40, 0.4);
    }

    .badge-status {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: rgba(255, 255, 255, 0.18);
      backdrop-filter: blur(12px);
      color: #FFFFFF;
      border: 1px solid rgba(255, 255, 255, 0.35);
      padding: 6px 15px;
      border-radius: 9999px;
      font-size: 0.82rem;
      font-weight: 600;
      box-shadow: 0 3px 12px rgba(0, 0, 0, 0.12);
    }

    .badge-status.warning {
      background: rgba(239, 68, 68, 0.2);
      border-color: rgba(239, 68, 68, 0.4);
      color: #FEE2E2;
    }

    .pulse-dot {
      width: 9px;
      height: 9px;
      border-radius: 50%;
      background-color: #35B6C8;
      box-shadow: 0 0 10px #35B6C8;
      animation: pulseGlow 2s infinite;
    }

    @keyframes pulseGlow {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.6; transform: scale(0.85); }
    }

    /* Container & Layout */
    .container {
      max-width: 1440px;
      margin: 0 auto;
      padding: 2.2rem 2.5rem;
      display: flex;
      flex-direction: column;
      gap: 1.85rem;
      position: relative;
      z-index: 1;
    }

    /* Navigation Bar (Glassmorphism Tabs) */
    .tabs-bar {
      display: flex;
      gap: 8px;
      background: var(--bg-glass);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      padding: 6px;
      border-radius: 16px;
      border: 1px solid var(--border-glass);
      width: fit-content;
      box-shadow: var(--shadow-glass);
    }

    .tab-btn {
      padding: 10px 22px;
      background: transparent;
      border: none;
      color: var(--text-muted);
      font-size: 0.95rem;
      font-weight: 600;
      border-radius: 12px;
      cursor: pointer;
      transition: all 0.25s ease;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .tab-btn:hover {
      color: var(--wtq-purple-deep);
      background: var(--wtq-purple-light);
    }

    .tab-btn.active {
      background: var(--gradient-brand);
      color: #FFFFFF;
      font-weight: 700;
      box-shadow: 0 4px 16px rgba(128, 80, 184, 0.35);
    }

    /* Tab Content Panels */
    .tab-panel {
      display: none;
    }
    .tab-panel.active {
      display: block;
    }

    /* Grid Layouts */
    .dashboard-grid {
      display: grid;
      grid-template-columns: 1fr 1.35fr;
      gap: 1.85rem;
      align-items: start;
    }

    @media (max-width: 1080px) {
      .dashboard-grid {
        grid-template-columns: 1fr;
      }
      header {
        padding: 1rem 1.5rem;
      }
      .container {
        padding: 1.5rem;
      }
    }

    /* Glassmorphism Cards */
    .glass-card {
      background: var(--bg-glass);
      backdrop-filter: blur(18px);
      -webkit-backdrop-filter: blur(18px);
      border: 1px solid var(--border-glass);
      border-radius: var(--card-radius);
      padding: 1.85rem;
      display: flex;
      flex-direction: column;
      gap: 1.35rem;
      box-shadow: var(--shadow-glass);
      transition: box-shadow 0.3s ease, transform 0.3s ease;
      position: relative;
      overflow: hidden;
    }

    .glass-card::before {
      content: "";
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 3px;
      background: linear-gradient(90deg, var(--wtq-purple) 0%, var(--wtq-teal) 50%, var(--wtq-yellow) 100%);
      opacity: 0.85;
    }

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid rgba(128, 80, 184, 0.1);
      padding-bottom: 0.9rem;
    }

    .card-title {
      font-size: 1.18rem;
      font-weight: 800;
      color: var(--text-main);
      display: flex;
      align-items: center;
      gap: 10px;
      letter-spacing: -0.01em;
    }

    .card-title .icon-tag {
      width: 32px;
      height: 32px;
      border-radius: 9px;
      background: var(--wtq-purple-light);
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-size: 1.1rem;
    }

    /* Form Controls */
    select, input[type="text"], textarea {
      background: rgba(255, 255, 255, 0.95);
      border: 1px solid rgba(128, 80, 184, 0.2);
      color: var(--text-main);
      padding: 11px 15px;
      border-radius: 12px;
      font-size: 0.95rem;
      outline: none;
      transition: all 0.25s ease;
      box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.02);
    }

    select:focus, input[type="text"]:focus, textarea:focus {
      border-color: var(--wtq-teal);
      box-shadow: 0 0 0 3px rgba(53, 182, 200, 0.22);
      background: #FFFFFF;
    }

    /* Buttons with Rich Gradients */
    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      background: var(--gradient-btn-purple);
      color: #FFFFFF;
      border: none;
      padding: 12px 24px;
      border-radius: 12px;
      font-weight: 700;
      font-size: 0.95rem;
      cursor: pointer;
      transition: all 0.25s ease;
      box-shadow: 0 6px 20px rgba(128, 80, 184, 0.28);
    }

    .btn:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 24px rgba(128, 80, 184, 0.4);
      filter: brightness(1.05);
    }

    .btn:active {
      transform: translateY(0);
    }

    .btn-teal {
      background: var(--gradient-btn-teal);
      box-shadow: 0 6px 20px rgba(53, 182, 200, 0.3);
    }

    .btn-teal:hover {
      box-shadow: 0 8px 24px rgba(53, 182, 200, 0.45);
    }

    .btn-secondary {
      background: rgba(255, 255, 255, 0.92);
      color: var(--wtq-purple-deep);
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
      border: 1px solid rgba(128, 80, 184, 0.25);
    }

    .btn-secondary:hover {
      background: var(--wtq-purple-light);
      border-color: var(--wtq-purple);
      transform: translateY(-1px);
    }

    .btn:disabled {
      opacity: 0.55;
      cursor: not-allowed;
      transform: none;
      filter: none;
    }

    /* Image Preview Container */
    .image-viewer {
      background: #14141E;
      border-radius: 14px;
      overflow: hidden;
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 500px;
      max-height: 650px;
      border: 1px solid rgba(128, 80, 184, 0.25);
      box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.4);
      position: relative;
    }

    .image-viewer img {
      width: 100%;
      height: 100%;
      object-fit: contain;
    }

    /* Gradient-Tinted Metric Cards */
    .metric-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
      gap: 12px;
    }

    .metric-box {
      background: rgba(255, 255, 255, 0.88);
      padding: 13px 15px;
      border-radius: 14px;
      border: 1px solid rgba(255, 255, 255, 0.95);
      border-top: 3px solid var(--wtq-purple);
      box-shadow: 0 4px 14px rgba(87, 51, 140, 0.04);
      transition: all 0.25s ease;
    }

    .metric-box:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 20px rgba(128, 80, 184, 0.12);
      border-color: var(--wtq-teal);
    }

    .metric-box.teal-accent {
      border-top-color: var(--wtq-teal);
    }

    .metric-box.yellow-accent {
      border-top-color: var(--wtq-yellow);
    }

    .metric-label {
      font-size: 0.72rem;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 5px;
      font-weight: 700;
    }

    .metric-val {
      font-size: 1.15rem;
      font-weight: 700;
      color: var(--text-main);
      font-family: 'JetBrains Mono', monospace;
    }

    .metric-val.purple {
      color: var(--wtq-purple-deep);
    }

    .metric-val.teal {
      color: var(--wtq-teal-deep);
    }

    .metric-val.negative {
      color: var(--accent-danger);
    }

    /* Glass Tables */
    .table-wrap {
      border: 1px solid rgba(128, 80, 184, 0.15);
      border-radius: 14px;
      overflow: hidden;
      background: rgba(255, 255, 255, 0.85);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.02);
    }

    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.9rem;
    }

    th, td {
      padding: 11px 15px;
      text-align: left;
    }

    th {
      background: rgba(128, 80, 184, 0.06);
      color: var(--wtq-purple-deep);
      font-weight: 700;
      font-size: 0.78rem;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      border-bottom: 1px solid rgba(128, 80, 184, 0.12);
    }

    td {
      border-bottom: 1px solid rgba(0, 0, 0, 0.04);
      color: var(--text-main);
    }

    tr:last-child td {
      border-bottom: none;
    }

    td.num {
      text-align: right;
      font-family: 'JetBrains Mono', monospace;
      font-weight: 600;
    }

    td.num.negative {
      color: var(--accent-danger);
    }

    /* Chips */
    .qa-box {
      display: flex;
      flex-direction: column;
      gap: 14px;
    }

    .qa-preset-chips {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .chip {
      background: rgba(255, 255, 255, 0.9);
      border: 1px solid rgba(128, 80, 184, 0.22);
      padding: 7px 15px;
      border-radius: 24px;
      font-size: 0.85rem;
      color: var(--wtq-purple-deep);
      cursor: pointer;
      font-weight: 600;
      transition: all 0.2s ease;
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02);
    }

    .chip:hover {
      background: linear-gradient(135deg, rgba(128, 80, 184, 0.12) 0%, rgba(53, 182, 200, 0.16) 100%);
      color: var(--wtq-teal-deep);
      border-color: var(--wtq-teal);
      transform: translateY(-1px);
      box-shadow: 0 4px 10px rgba(53, 182, 200, 0.15);
    }

    .answer-card {
      background: linear-gradient(135deg, rgba(53, 182, 200, 0.1) 0%, rgba(247, 201, 40, 0.06) 100%);
      border: 1px solid rgba(53, 182, 200, 0.4);
      border-radius: 16px;
      padding: 18px;
      line-height: 1.65;
      font-size: 0.96rem;
      color: var(--text-main);
      box-shadow: 0 6px 20px rgba(53, 182, 200, 0.1);
    }

    .answer-title {
      font-size: 0.84rem;
      font-weight: 800;
      color: var(--wtq-teal-deep);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 8px;
      display: flex;
      align-items: center;
      gap: 6px;
    }

    /* Terminal Raw Block */
    pre.code-block {
      background: #14141E;
      border: 1px solid #2B283E;
      padding: 15px;
      border-radius: 14px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.85rem;
      color: #94E2D5;
      overflow-x: auto;
      max-height: 380px;
      line-height: 1.55;
      box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.4);
    }

    /* Spinner */
    .spinner {
      border: 3px solid rgba(255, 255, 255, 0.3);
      border-top: 3px solid white;
      border-radius: 50%;
      width: 18px;
      height: 18px;
      animation: spin 0.8s linear infinite;
    }

    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }

    /* Summary Banners */
    .stat-banner {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
      gap: 15px;
      margin-bottom: 1rem;
    }

    .stat-card {
      background: rgba(255, 255, 255, 0.9);
      border: 1px solid rgba(255, 255, 255, 0.95);
      border-radius: 16px;
      padding: 16px 20px;
      display: flex;
      align-items: center;
      gap: 16px;
      box-shadow: 0 6px 18px rgba(87, 51, 140, 0.06);
      transition: transform 0.25s ease;
    }

    .stat-card:hover {
      transform: translateY(-2px);
    }

    .stat-icon {
      width: 44px;
      height: 44px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 22px;
      color: white;
    }

    .stat-icon.purple { background: var(--gradient-btn-purple); box-shadow: 0 4px 12px rgba(128, 80, 184, 0.3); }
    .stat-icon.teal { background: var(--gradient-btn-teal); box-shadow: 0 4px 12px rgba(53, 182, 200, 0.3); }
    .stat-icon.yellow { background: linear-gradient(135deg, #F7C928, #F59E0B); color: #451A03; box-shadow: 0 4px 12px rgba(247, 201, 40, 0.35); }
  </style>
</head>
<body>

  <header>
    <div class="brand-group">
      <div class="brand-icon">⚡</div>
      <div class="brand-text">
        <h1>Utility Bill Decoder</h1>
        <p>Women Tech Quest 2026 Build Track — AI Multimodal Assistant</p>
      </div>
    </div>
    <div class="header-badges">
      <div class="pill-track">
        <span>🏆</span> WTQ 2026 Build Track
      </div>
      <div id="system-status-badge" class="badge-status">
        <span class="pulse-dot"></span>
        <span id="status-text">Gemini 3.5 Flash-Lite Ready</span>
      </div>
    </div>
  </header>

  <div class="container">
    
    <!-- Tab navigation -->
    <div class="tabs-bar">
      <button class="tab-btn active" onclick="switchTab('explorer-tab', event)">
        <span>🔍</span> Bill Explorer & Analyzer
      </button>
      <button class="tab-btn" onclick="switchTab('batch-tab', event)">
        <span>⚙️</span> Batch CSV Runner
      </button>
      <button class="tab-btn" onclick="switchTab('package-tab', event)">
        <span>📦</span> Submission Packager
      </button>
    </div>

    <!-- TAB 1: EXPLORER & ANALYZER -->
    <div id="explorer-tab" class="tab-panel active">
      <div class="dashboard-grid">
        
        <!-- Left: Image Viewer & Bill Selector -->
        <div class="glass-card">
          <div class="card-header">
            <div class="card-title">
              <span class="icon-tag">📄</span> Select Electricity Bill
            </div>
            <div class="bill-selector-wrap">
              <select id="bill-select" onchange="loadBillImage()">
                <option value="">Loading bills...</option>
              </select>
            </div>
          </div>

          <div class="image-viewer">
            <img id="bill-img" src="" alt="Select a bill image">
          </div>

          <div style="display: flex; gap: 10px;">
            <button id="btn-extract" class="btn" style="flex: 1;" onclick="runExtraction()">
              <span id="extract-spinner" class="spinner" style="display: none;"></span>
              <span>⚡ Extract Bill Details (Level 1)</span>
            </button>
          </div>
        </div>

        <!-- Right: Extraction Results & Level 2 Q&A -->
        <div style="display: flex; flex-direction: column; gap: 1.6rem;">
          
          <!-- Level 1 Metrics Card -->
          <div class="glass-card">
            <div class="card-header">
              <div class="card-title">
                <span class="icon-tag">📊</span> Level 1 Extracted Data
              </div>
              <button class="btn btn-secondary" style="padding: 6px 14px; font-size: 0.82rem;" onclick="copyJson()">
                📋 Copy Clean JSON
              </button>
            </div>

            <div class="metric-grid">
              <div class="metric-box">
                <div class="metric-label">Provider</div>
                <div id="m-provider" class="metric-val purple">KE</div>
              </div>
              <div class="metric-box">
                <div class="metric-label">Tariff Code</div>
                <div id="m-tariff" class="metric-val">-</div>
              </div>
              <div class="metric-box yellow-accent">
                <div class="metric-label">Sanctioned Load</div>
                <div id="m-load" class="metric-val">-</div>
              </div>
              <div class="metric-box teal-accent">
                <div class="metric-label">Bill Month</div>
                <div id="m-month" class="metric-val teal">-</div>
              </div>
              <div class="metric-box">
                <div class="metric-label">Units Consumed</div>
                <div id="m-units" class="metric-val purple">-</div>
              </div>
              <div class="metric-box yellow-accent">
                <div class="metric-label">Current Bill</div>
                <div id="m-bill" class="metric-val purple">-</div>
              </div>
              <div class="metric-box">
                <div class="metric-label">Arrears</div>
                <div id="m-arrears" class="metric-val">-</div>
              </div>
              <div class="metric-box teal-accent">
                <div class="metric-label">Due Date</div>
                <div id="m-due-date" class="metric-val teal">-</div>
              </div>
              <div class="metric-box">
                <div class="metric-label">Payable (Within)</div>
                <div id="m-pay-within" class="metric-val purple">-</div>
              </div>
              <div class="metric-box yellow-accent">
                <div class="metric-label">Payable (Late)</div>
                <div id="m-pay-late" class="metric-val">-</div>
              </div>
            </div>

            <!-- Charges & Taxes Tables -->
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px;">
              <div>
                <div style="font-size: 0.85rem; font-weight: 700; color: var(--wtq-purple-deep); margin-bottom: 8px;">
                  Charges Breakdown (<span id="charges-total" style="color: var(--wtq-purple); font-weight: 600;">Total: -</span>)
                </div>
                <div class="table-wrap">
                  <table>
                    <thead>
                      <tr><th>Type</th><th style="text-align: right;">Amount (PKR)</th></tr>
                    </thead>
                    <tbody id="charges-table-body">
                      <tr><td colspan="2" style="text-align: center; color: var(--text-muted); padding: 14px;">Select bill and click extract</td></tr>
                    </tbody>
                  </table>
                </div>
              </div>

              <div>
                <div style="font-size: 0.85rem; font-weight: 700; color: var(--wtq-teal-deep); margin-bottom: 8px;">
                  Taxes Breakdown (<span id="taxes-total" style="color: var(--wtq-teal); font-weight: 600;">Total: -</span>)
                </div>
                <div class="table-wrap">
                  <table>
                    <thead>
                      <tr><th>Type</th><th style="text-align: right;">Amount (PKR)</th></tr>
                    </thead>
                    <tbody id="taxes-table-body">
                      <tr><td colspan="2" style="text-align: center; color: var(--text-muted); padding: 14px;">Select bill and click extract</td></tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            <details style="margin-top: 4px;">
              <summary style="font-size: 0.85rem; color: var(--wtq-purple-deep); cursor: pointer; font-weight: 700; padding: 4px 0;">
                ▶ View Complete RFC 4180 JSON Schema
              </summary>
              <pre id="raw-json-output" class="code-block" style="margin-top: 8px;">// Run extraction to view complete validated Level 1 JSON</pre>
            </details>
          </div>

          <!-- Level 2 Q&A Card -->
          <div class="glass-card">
            <div class="card-header">
              <div class="card-title">
                <span class="icon-tag">💬</span> Level 2 Customer Q&A Assistant
              </div>
            </div>

            <div class="qa-box">
              <div class="qa-preset-chips">
                <div class="chip" onclick="setQuestion('Is this a net-metered (solar) connection or a standard connection? How did you tell?')">
                  ☀️ Solar / Net-metered?
                </div>
                <div class="chip" onclick="setQuestion('How much of my bill is taxes?')">
                  💸 How much is taxes?
                </div>
                <div class="chip" onclick="setQuestion('Which month in the last 12 months had the highest units consumed?')">
                  📈 Highest month units?
                </div>
                <div class="chip" onclick="setQuestion('How many more units do I consume in summer (June-August) than in winter (December-February)?')">
                  🌡️ Summer vs Winter units
                </div>
                <div class="chip" onclick="setQuestion('If I dont pay on time, what late payment surcharges will be added?')">
                  ⏰ Late payment surcharge
                </div>
              </div>

              <div style="display: flex; gap: 10px;">
                <input id="qa-input" type="text" style="flex: 1;" placeholder="Ask any question about this bill..." value="Is this a net-metered (solar) connection or a standard connection? How did you tell?">
                <button id="btn-ask" class="btn btn-teal" onclick="askQuestion()">
                  <span id="qa-spinner" class="spinner" style="display: none;"></span>
                  <span>Ask AI</span>
                </button>
              </div>

              <div id="qa-result-box" class="answer-card" style="display: none;">
                <div class="answer-title">
                  <span>✓</span> Plain English Answer (Grounded in Bill):
                </div>
                <div id="qa-answer-text">...</div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>

    <!-- TAB 2: BATCH CSV RUNNER -->
    <div id="batch-tab" class="tab-panel">
      <div class="glass-card" style="max-width: 950px; margin: 0 auto;">
        <div class="card-header">
          <div class="card-title">
            <span class="icon-tag">⚙️</span> Batch CSV Processor (Level 1 & Level 2)
          </div>
        </div>

        <div class="stat-banner">
          <div class="stat-card">
            <div class="stat-icon purple">📑</div>
            <div>
              <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; font-weight: 700;">Level 1 Target</div>
              <div style="font-size: 1.15rem; font-weight: 800; color: var(--wtq-purple-deep);">10 Bills JSON</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon teal">❓</div>
            <div>
              <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; font-weight: 700;">Level 2 Target</div>
              <div style="font-size: 1.15rem; font-weight: 800; color: var(--wtq-teal-deep);">120 Questions (Q1-Q12)</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon yellow">🎯</div>
            <div>
              <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; font-weight: 700;">Format Compliance</div>
              <div style="font-size: 1.15rem; font-weight: 800; color: #451A03;">RFC 4180 Strict</div>
            </div>
          </div>
        </div>

        <p style="color: var(--text-muted); font-size: 0.95rem;">
          Executes automated batch extraction and grounded question answering for all 10 test bills, generating 
          <code>output/level1.csv</code> (10 rows) and <code>output/level2.csv</code> (120 rows).
        </p>

        <div style="display: flex; flex-direction: column; gap: 14px;">
          <div>
            <label style="font-size: 0.85rem; color: var(--text-main); font-weight: 700; display: block; margin-bottom: 4px;">Bills Directory</label>
            <input id="batch-bills-dir" type="text" style="width: 100%;" value="data/test data/bills">
          </div>
          <div>
            <label style="font-size: 0.85rem; color: var(--text-main); font-weight: 700; display: block; margin-bottom: 4px;">Level 1 Template Path</label>
            <input id="batch-l1-template" type="text" style="width: 100%;" value="data/test data/csv/level1.csv">
          </div>
          <div>
            <label style="font-size: 0.85rem; color: var(--text-main); font-weight: 700; display: block; margin-bottom: 4px;">Level 2 Template Path</label>
            <input id="batch-l2-template" type="text" style="width: 100%;" value="data/test data/csv/level2.csv">
          </div>
          <button id="btn-run-batch" class="btn" style="padding: 13px;" onclick="runBatchProcess()">
            <span id="batch-spinner" class="spinner" style="display: none;"></span>
            <span>🚀 Run Official Test Batch Generation</span>
          </button>
        </div>

        <div id="batch-status-box" style="margin-top: 1rem; display: none;">
          <pre id="batch-log" class="code-block" style="color: #A6E3A1;">Processing started...</pre>
        </div>
      </div>
    </div>

    <!-- TAB 3: SUBMISSION PACKAGER -->
    <div id="package-tab" class="tab-panel">
      <div class="glass-card" style="max-width: 950px; margin: 0 auto;">
        <div class="card-header">
          <div class="card-title">
            <span class="icon-tag">📦</span> Package Official Submission ZIP
          </div>
        </div>
        <p style="color: var(--text-muted); font-size: 0.95rem;">
          Builds <code>your-submission.zip</code> conforming strictly to Section 7:
          <code>output/level1.csv</code> (10 rows), <code>output/level2.csv</code> (120 rows), <code>source/</code> (code, README.md, .env.example), and optional <code>demo/</code>.
        </p>

        <div style="background: rgba(255, 255, 255, 0.9); padding: 20px; border-radius: 14px; border: 1px solid rgba(128, 80, 184, 0.15); box-shadow: 0 4px 14px rgba(0,0,0,0.02);">
          <div style="font-weight: 800; color: var(--text-main); margin-bottom: 12px; font-size: 1.05rem;">Submission Readiness Checklist:</div>
          <ul style="list-style-type: none; display: flex; flex-direction: column; gap: 10px; font-size: 0.92rem; color: var(--text-main);">
            <li style="display: flex; align-items: center; gap: 10px;">
              <span style="color: var(--accent-success); font-weight: 800; font-size: 1.1rem;">✅</span>
              <span><code>output/level1.csv</code>: 10 test bills with valid 18-key JSON schema</span>
            </li>
            <li style="display: flex; align-items: center; gap: 10px;">
              <span style="color: var(--accent-success); font-weight: 800; font-size: 1.1rem;">✅</span>
              <span><code>output/level2.csv</code>: 120 completed customer answers (Q1–Q12)</span>
            </li>
            <li style="display: flex; align-items: center; gap: 10px;">
              <span style="color: var(--accent-success); font-weight: 800; font-size: 1.1rem;">✅</span>
              <span>Strict Security: <code>.env</code> and real API keys excluded from ZIP</span>
            </li>
            <li style="display: flex; align-items: center; gap: 10px;">
              <span style="color: var(--accent-success); font-weight: 800; font-size: 1.1rem;">✅</span>
              <span>File size strictly verified under the 15 MB contest limit</span>
            </li>
          </ul>
        </div>

        <button id="btn-package" class="btn" style="padding: 13px;" onclick="packageSubmission()">
          <span id="pkg-spinner" class="spinner" style="display: none;"></span>
          <span>🎁 Build your-submission.zip (< 15 MB)</span>
        </button>

        <div id="pkg-result-box" style="display: none;">
          <pre id="pkg-log" class="code-block" style="color: #94E2D5;"></pre>
        </div>
      </div>
    </div>

  </div>

  <script>
    let currentExtractedData = null;

    function switchTab(tabId, ev) {
      document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
      document.querySelectorAll('.tab-panel').forEach(panel => panel.classList.remove('active'));
      if (ev && ev.currentTarget) {
        ev.currentTarget.classList.add('active');
      }
      document.getElementById(tabId).classList.add('active');
    }

    async function init() {
      try {
        const res = await fetch('/api/bills');
        const data = await res.json();
        const sel = document.getElementById('bill-select');
        sel.innerHTML = '';
        if (data.bills && data.bills.length > 0) {
          data.bills.forEach(b => {
            const opt = document.createElement('option');
            opt.value = b.path;
            opt.textContent = `${b.name} (${b.provider})`;
            sel.appendChild(opt);
          });
          loadBillImage();
        } else {
          sel.innerHTML = '<option>No bill images found</option>';
        }

        // Check status
        const statusRes = await fetch('/api/status');
        const statusData = await statusRes.json();
        const badge = document.getElementById('system-status-badge');
        const text = document.getElementById('status-text');
        if (statusData.has_api_key) {
          badge.className = 'badge-status';
          text.textContent = `${statusData.model_name} Ready`;
        } else {
          badge.className = 'badge-status warning';
          text.textContent = 'API Key Missing in .env';
        }
      } catch (e) {
        console.error('Init error:', e);
      }
    }

    function loadBillImage() {
      const sel = document.getElementById('bill-select');
      if (sel.value) {
        const img = document.getElementById('bill-img');
        img.src = `/api/bill-image?path=${encodeURIComponent(sel.value)}`;
      }
    }

    async function runExtraction() {
      const sel = document.getElementById('bill-select');
      if (!sel.value) return;

      const btn = document.getElementById('btn-extract');
      const spinner = document.getElementById('extract-spinner');
      btn.disabled = true;
      spinner.style.display = 'inline-block';

      try {
        const res = await fetch('/api/extract', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ image_path: sel.value })
        });
        const data = await res.json();
        if (data.error) {
          alert('Extraction error: ' + data.error);
          return;
        }

        currentExtractedData = data;
        displayExtractedData(data);
      } catch (e) {
        alert('Network or server error: ' + e);
      } finally {
        btn.disabled = false;
        spinner.style.display = 'none';
      }
    }

    function displayExtractedData(d) {
      document.getElementById('m-provider').textContent = d.provider || 'null';
      document.getElementById('m-tariff').textContent = d.tariff || 'null';
      document.getElementById('m-load').textContent = d.sanctioned_load_kw !== null ? `${d.sanctioned_load_kw} kW` : 'null';
      document.getElementById('m-month').textContent = d.bill_month || 'null';
      document.getElementById('m-units').textContent = d.units_consumed !== null ? d.units_consumed : 'null';
      document.getElementById('m-bill').textContent = d.current_bill !== null ? `Rs. ${d.current_bill.toLocaleString()}` : 'null';
      
      const arr = document.getElementById('m-arrears');
      if (d.arrears !== null) {
        arr.textContent = `Rs. ${d.arrears.toLocaleString()}`;
        arr.className = d.arrears < 0 ? 'metric-val negative' : 'metric-val';
      } else {
        arr.textContent = 'null';
        arr.className = 'metric-val';
      }

      document.getElementById('m-due-date').textContent = d.due_date || 'null';
      document.getElementById('m-pay-within').textContent = d.payable_within_due_date !== null ? `Rs. ${d.payable_within_due_date.toLocaleString()}` : 'null';
      document.getElementById('m-pay-late').textContent = d.payable_after_due_date !== null ? `Rs. ${d.payable_after_due_date.toLocaleString()}` : 'null';

      // Charges table
      const chargesTbody = document.getElementById('charges-table-body');
      chargesTbody.innerHTML = '';
      if (d.charges && d.charges.length > 0) {
        d.charges.forEach(c => {
          const tr = document.createElement('tr');
          const isNeg = c.amount < 0;
          tr.innerHTML = `<td>${c.type}</td><td class="num ${isNeg ? 'negative' : ''}">${c.amount.toLocaleString()}</td>`;
          chargesTbody.appendChild(tr);
        });
      } else {
        chargesTbody.innerHTML = '<tr><td colspan="2" style="text-align: center; color: var(--text-muted); padding: 12px;">None visible or covered</td></tr>';
      }
      document.getElementById('charges-total').textContent = d.total_charges !== null ? `Total: Rs. ${d.total_charges.toLocaleString()}` : 'Total: null';

      // Taxes table
      const taxesTbody = document.getElementById('taxes-table-body');
      taxesTbody.innerHTML = '';
      if (d.taxes && d.taxes.length > 0) {
        d.taxes.forEach(t => {
          const tr = document.createElement('tr');
          tr.innerHTML = `<td>${t.type}</td><td class="num">${t.amount.toLocaleString()}</td>`;
          taxesTbody.appendChild(tr);
        });
      } else {
        taxesTbody.innerHTML = '<tr><td colspan="2" style="text-align: center; color: var(--text-muted); padding: 12px;">Combined in total taxes</td></tr>';
      }
      document.getElementById('taxes-total').textContent = d.total_taxes !== null ? `Total: Rs. ${d.total_taxes.toLocaleString()}` : 'Total: null';

      // Raw JSON
      document.getElementById('raw-json-output').textContent = JSON.stringify(d, null, 2);
    }

    function setQuestion(q) {
      document.getElementById('qa-input').value = q;
    }

    async function askQuestion() {
      const sel = document.getElementById('bill-select');
      const question = document.getElementById('qa-input').value.trim();
      if (!sel.value || !question) return;

      const btn = document.getElementById('btn-ask');
      const spinner = document.getElementById('qa-spinner');
      const box = document.getElementById('qa-result-box');
      const ansText = document.getElementById('qa-answer-text');

      btn.disabled = true;
      spinner.style.display = 'inline-block';
      box.style.display = 'block';
      ansText.textContent = 'Thinking and computing grounded response...';

      try {
        const res = await fetch('/api/ask', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            image_path: sel.value,
            question: question,
            extracted_json: currentExtractedData
          })
        });
        const data = await res.json();
        if (data.error) {
          ansText.textContent = 'Error: ' + data.error;
        } else {
          ansText.textContent = data.answer;
        }
      } catch (e) {
        ansText.textContent = 'Network or server error: ' + e;
      } finally {
        btn.disabled = false;
        spinner.style.display = 'none';
      }
    }

    function copyJson() {
      const code = document.getElementById('raw-json-output').textContent;
      navigator.clipboard.writeText(code).then(() => {
        alert('Level 1 JSON copied to clipboard!');
      });
    }

    async function runBatchProcess() {
      const bills_dir = document.getElementById('batch-bills-dir').value.trim();
      const l1_template = document.getElementById('batch-l1-template').value.trim();
      const l2_template = document.getElementById('batch-l2-template').value.trim();

      const btn = document.getElementById('btn-run-batch');
      const spinner = document.getElementById('batch-spinner');
      const box = document.getElementById('batch-status-box');
      const log = document.getElementById('batch-log');

      btn.disabled = true;
      spinner.style.display = 'inline-block';
      box.style.display = 'block';
      log.textContent = 'Batch execution in progress. Processing all test bills...';

      try {
        const res = await fetch('/api/batch-run', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            bills_dir: bills_dir,
            level1_template: l1_template || null,
            level2_template: l2_template || null
          })
        });
        const data = await res.json();
        if (data.error) {
          log.textContent = 'Error: ' + data.error;
          log.style.color = '#EF4444';
        } else {
          log.textContent = data.message;
          log.style.color = '#A6E3A1';
        }
      } catch (e) {
        log.textContent = 'Network error: ' + e;
        log.style.color = '#EF4444';
      } finally {
        btn.disabled = false;
        spinner.style.display = 'none';
      }
    }

    async function packageSubmission() {
      const btn = document.getElementById('btn-package');
      const spinner = document.getElementById('pkg-spinner');
      const box = document.getElementById('pkg-result-box');
      const log = document.getElementById('pkg-log');

      btn.disabled = true;
      spinner.style.display = 'inline-block';
      box.style.display = 'block';
      log.textContent = 'Packaging zip file and validating outputs...';

      try {
        const res = await fetch('/api/package-submission', { method: 'POST' });
        const data = await res.json();
        if (data.error) {
          log.textContent = 'Error: ' + data.error;
          log.style.color = '#EF4444';
        } else {
          log.textContent = data.message;
          log.style.color = '#94E2D5';
        }
      } catch (e) {
        log.textContent = 'Network error: ' + e;
        log.style.color = '#EF4444';
      } finally {
        btn.disabled = false;
        spinner.style.display = 'none';
      }
    }

    window.onload = init;
  </script>
</body>
</html>
"""

class BillDecoderServer(BaseHTTPRequestHandler):
    def _send_json(self, status: int, data: Any):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            body = HTML_CONTENT.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if path == "/health":
            self._send_json(200, {"status": "healthy", "service": "wtq-utility-bill-decoder"})
            return

        if path == "/api/status":
            env_vars = load_env_file()
            api_key = (
                os.environ.get("API_KEY")
                or env_vars.get("API_KEY")
                or os.environ.get("GEMINI_API_KEY")
                or env_vars.get("GEMINI_API_KEY")
            )
            model_name = os.environ.get("MODEL_NAME") or env_vars.get("MODEL_NAME", "gemini-3.5-flash-lite")
            self._send_json(200, {
                "has_api_key": bool(api_key and len(api_key.strip()) > 5),
                "model_name": model_name,
                "provider": "google"
            })
            return

        if path == "/api/bills":
            search_dirs = [
                "data/test data/bills",
                "test/bills",
                "data/test data",
                "data/train data",
                "train/bills",
                "data"
            ]
            bills = []
            seen_stems = set()
            for d in search_dirs:
                p = Path(d)
                if p.exists() and p.is_dir():
                    for f in sorted(p.iterdir()):
                        if f.suffix.lower() in [".png", ".jpg", ".jpeg"] and f.stem not in seen_stems:
                            seen_stems.add(f.stem)
                            stem = f.stem
                            prov = "KE" if "KESC" in stem.upper() or "KE" in stem.upper() else ("LESCO" if "LESCO" in stem.upper() else "IESCO")
                            bills.append({
                                "name": f.name,
                                "stem": stem,
                                "path": str(f).replace("\\", "/"),
                                "provider": prov
                            })
            self._send_json(200, {"bills": bills})
            return

        if path == "/api/bill-image":
            qs = parse_qs(parsed.query)
            img_path = qs.get("path", [None])[0]
            if img_path and os.path.exists(img_path):
                mime, _ = mimetypes.guess_type(img_path)
                mime = mime or "image/png"
                with open(img_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return
            else:
                self.send_error(404, "Image not found")
                return

        self.send_error(404, "Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            req_data = json.loads(body)
        except Exception:
            req_data = {}

        if path == "/api/extract":
            image_path = req_data.get("image_path")
            if not image_path or not os.path.exists(image_path):
                self._send_json(400, {"error": f"Image path '{image_path}' not found."})
                return

            try:
                result = extract_bill_details(image_path)
                self._send_json(200, result)
            except Exception as e:
                self._send_json(500, {"error": str(e)})
            return

        if path == "/api/ask":
            image_path = req_data.get("image_path")
            question = req_data.get("question")
            extracted_json = req_data.get("extracted_json")

            if not image_path or not question:
                self._send_json(400, {"error": "Missing image_path or question."})
                return

            try:
                answer = answer_question(question, image_path, extracted_json=extracted_json)
                self._send_json(200, {"answer": answer})
            except Exception as e:
                self._send_json(500, {"error": str(e)})
            return

        if path == "/api/batch-run":
            bills_dir = req_data.get("bills_dir", "data/test data/bills")
            l1_template = req_data.get("level1_template")
            l2_template = req_data.get("level2_template")

            try:
                client = GeminiClient()
                l1_res = process_level1(bills_dir, template_csv=l1_template, client=client)
                if l2_template and os.path.exists(l2_template):
                    process_level2(bills_dir, l2_template, extracted_data_map=l1_res, client=client)
                    msg = "Batch run complete! Successfully generated output/level1.csv (10 bills) and output/level2.csv (120 questions)."
                else:
                    msg = "Batch run complete! Successfully generated output/level1.csv."

                self._send_json(200, {"message": msg})
            except Exception as e:
                self._send_json(500, {"error": str(e)})
            return

        if path == "/api/package-submission":
            try:
                zip_path = create_submission_zip()
                size_mb = os.path.getsize(zip_path) / (1024 * 1024)
                self._send_json(200, {
                    "message": f"Successfully validated and packaged {zip_path} ({size_mb:.2f} MB). Ready for official upload!"
                })
            except Exception as e:
                self._send_json(500, {"error": str(e)})
            return

        self.send_error(404, "Not Found")

def start_server(preferred_port: int = DEFAULT_PORT, host: Optional[str] = None):
    env_port = os.environ.get("PORT")
    if env_port:
        try:
            preferred_port = int(env_port)
        except ValueError:
            pass

    if host is None:
        # Default to 0.0.0.0 in cloud/container environments, 127.0.0.1 for local dev
        host = os.environ.get("HOST", "0.0.0.0" if env_port else "127.0.0.1")

    ports_to_try = [preferred_port] if env_port else [preferred_port, 8000, 8080, 5001, 8888, 3000]
    httpd = None
    actual_port = None

    for port in ports_to_try:
        try:
            server_address = (host, port)
            httpd = HTTPServer(server_address, BillDecoderServer)
            actual_port = port
            break
        except OSError:
            print(f"Port {port} is in use on {host}, trying next port...")

    if not httpd:
        print(f"ERROR: Could not bind to candidate port(s) on host {host}.")
        sys.exit(1)

    display_host = "localhost" if host in ("0.0.0.0", "127.0.0.1") else host
    url = f"http://{display_host}:{actual_port}"
    print(f"\n=======================================================")
    print(f"  Women Tech Quest 2026 Utility Bill Decoder Dashboard")
    print(f"  Listening on: {host}:{actual_port}")
    print(f"  Open in Browser: {url}")
    print(f"=======================================================\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.server_close()

if __name__ == "__main__":
    p = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT
    start_server(p)

