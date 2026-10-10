"""
Gemini API Multimodal Client
Uses Python's standard library (urllib.request) for zero-dependency, reliable communication
with Google AI Studio (Gemini 3.5 Flash-Lite / Gemini 3.1 Flash-Lite).
"""

import os
import json
import time
import base64
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, Optional

ALLOWED_MODELS = {
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "claude-haiku-4-5",
    "gpt-4.1-mini",
    "gpt-5-mini"
}

def load_env_file(env_path: str = ".env") -> Dict[str, str]:
    """Load simple key=value pairs from a .env file."""
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    env_vars[key.strip()] = val.strip().strip('"').strip("'")
    return env_vars

class GeminiClient:
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        env_vars = load_env_file()
        self.api_key = api_key or os.environ.get("API_KEY") or env_vars.get("API_KEY")
        self.model_name = model_name or os.environ.get("MODEL_NAME") or env_vars.get("MODEL_NAME", "gemini-3.5-flash-lite")
        self.provider = os.environ.get("MODEL_PROVIDER") or env_vars.get("MODEL_PROVIDER", "google")
        
        # Enforce approved competition models
        if self.model_name not in ALLOWED_MODELS:
            raise ValueError(
                f"Model '{self.model_name}' is not in the approved competition model list: {sorted(ALLOWED_MODELS)}"
            )

        if not self.api_key:
            self.api_key = os.environ.get("GEMINI_API_KEY") or env_vars.get("GEMINI_API_KEY")

    def call_gemini(
        self,
        prompt: str,
        image_path: Optional[str] = None,
        system_instruction: Optional[str] = None,
        json_mode: bool = False,
        max_retries: int = 5,
        temperature: float = 0.1
    ) -> str:
        """
        Call Gemini generateContent API with text prompt and optional image.
        Handles retry with exponential backoff on 429 / 503 errors.
        """
        if not self.api_key:
            raise ValueError("Google API key is missing. Please set API_KEY in .env file.")

        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"

        parts = []

        # Add image part if provided
        if image_path:
            p = Path(image_path)
            if not p.exists():
                raise FileNotFoundError(f"Image not found at {image_path}")

            ext = p.suffix.lower().replace(".", "")
            mime_type = "image/jpeg" if ext in ["jpg", "jpeg"] else "image/png"

            with open(p, "rb") as img_file:
                b64_data = base64.b64encode(img_file.read()).decode("utf-8")

            parts.append({
                "inline_data": {
                    "mime_type": mime_type,
                    "data": b64_data
                }
            })

        # Add prompt text part
        parts.append({"text": prompt})

        contents = [{"parts": parts}]

        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "topP": 0.95,
                "maxOutputTokens": 4096
            }
        }

        if json_mode:
            payload["generationConfig"]["responseMimeType"] = "application/json"

        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        req_data = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}

        delay = 3
        last_error = None

        for attempt in range(max_retries):
            try:
                req = urllib.request.Request(endpoint, data=req_data, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=90) as response:
                    res_body = response.read().decode("utf-8")
                    data = json.loads(res_body)

                    candidates = data.get("candidates", [])
                    if not candidates:
                        raise ValueError(f"Gemini returned no candidates: {data}")

                    content = candidates[0].get("content", {})
                    out_parts = content.get("parts", [])
                    text_out = "".join(part.get("text", "") for part in out_parts)
                    return text_out

            except urllib.error.HTTPError as e:
                err_content = e.read().decode("utf-8", errors="replace")
                last_error = f"HTTP {e.code}: {err_content}"
                if e.code in [429, 500, 503]:
                    print(f"[GeminiClient] Rate limit or transient error (HTTP {e.code}), retrying in {delay}s...")
                    time.sleep(delay)
                    delay *= 2
                else:
                    raise RuntimeError(f"Gemini API request failed: {last_error}") from e
            except Exception as e:
                last_error = str(e)
                print(f"[GeminiClient] Request error: {e}, retrying in {delay}s...")
                time.sleep(delay)
                delay *= 2

        raise RuntimeError(f"Gemini API failed after {max_retries} retries: {last_error}")
