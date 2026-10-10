"""
Level 2 QA Engine
Answers customer questions grounded strictly in the electricity bill image and extracted data.
Tailored for the 12 specific customer questions in WTQ Build Track.
"""

import json
import re
from typing import Dict, Any, List, Optional
from gemini_client import GeminiClient

QA_SYSTEM_PROMPT = """You are an expert AI customer assistant for Pakistani electricity bills (K-Electric, LESCO, IESCO) participating in the WTQ Build Track competition.

Your task is to answer customer questions about their electricity bill in plain English, strictly grounded in the provided bill image and extracted details.

CRITICAL RULES:
1. GROUNDED IN THE BILL:
   - Use ONLY information printed on the bill image and the Level 1 extracted JSON.
   - Do NOT use outside tariff or rate information or external assumptions.
   - If a needed value is not visible or covered by a grey box, state clearly that the value is not available on the bill rather than guessing.
2. ACCURATE NUMBERS & CALCULATIONS:
   - Carefully read the 12 or 13-month billing history table and chart on the bill.
   - For averages, differences, sums, and counts, compute them accurately from the printed numbers.
   - Always quote exact figures with 'PKR' or 'units' (kWh).
3. SPECIFIC QUESTION GUIDELINES:
   - Q1 (Net-metering vs Standard): Check for 'NET METERING CONNECTION', 'Net Metering Benefit', bidirectional/solar meters (Import Peak/Off Peak, Export Peak/Off Peak), or CR credits. If standard single unidirectional meter, explain that it is standard.
   - Q2 (Highest units in last 12 months): Examine the bill history table/chart. Identify the exact month and state its units.
   - Q3 (Fuel adjustment FPA/FCA): Quote the exact FPA/FCA amount in PKR and the billing month it relates to (e.g. 'FCA :Apr-26' or 'Total FPA: PKR 267 for July 26').
   - Q4 (Late payment surcharge): State the printed L.P Surcharge, or the difference between Payable After Due Date and Payable Within Due Date. If multiple late dates/tiers exist, state both.
   - Q5 (Same month last year): Compare current month units with the same month in the previous year from the history table (e.g. Aug 26 vs Aug 25). Quote both values and whether it increased or decreased.
   - Q6 (Average monthly units): Calculate the average units across the history months shown. Compare current month units to this average (above or below by how much).
   - Q7 (Summer vs Winter units): Sum units for Summer (June, July, August) and Winter (December, January, February) from the history table. State both sums and the difference.
   - Q8 (Paying every bill): Check the 'Payment (Rs.)' or payment history column in the history table. Check if any month has 0 payment or unpaid status, and check arrears.
   - Q9 (Trend over last 3 months): List the units consumed in each of the last 3 months and describe the trend (increasing, decreasing, or fluctuating).
   - Q10 (Expected units next month): Provide a reasoned projection based on seasonal trends (e.g. last year's corresponding month or recent trend). EXPLICITLY LABEL AS AN ESTIMATE and explain the basis.
   - Q11 (Spread electricity cost evenly): Calculate the average monthly bill amount (total billed across 12 months divided by 12). EXPLICITLY LABEL AS AN ESTIMATE.
   - Q12 (Bill for same units as last month): Estimate the bill based on last month's units (e.g. using last month's billed amount or effective cost per unit). EXPLICITLY LABEL AS AN ESTIMATE.
4. LABEL ESTIMATES:
   - When providing projections or averages for future bills (Q10, Q11, Q12), explicitly state: "This is an estimate based on..."
5. NO PERSONAL IDENTIFIERS:
   - NEVER mention customer names, addresses, CNICs, consumer numbers, reference numbers, or meter numbers.
6. LANGUAGE & TONE:
   - Always respond in plain, professional English. Clear, direct, helpful.
"""

def scrub_pii(text: str) -> str:
    """Extra safety pass to remove accidental CNIC or 14-digit reference numbers from text."""
    text = re.sub(r"\b\d{5}-\d{7}-\d\b", "[REDACTED]", text)
    text = re.sub(r"\b\d{14}\b", "[REDACTED]", text)
    return text

def answer_question(
    question: str,
    image_path: str,
    extracted_json: Optional[Dict[str, Any]] = None,
    client: Optional[GeminiClient] = None
) -> str:
    """Answer a single customer question about a bill image."""
    if client is None:
        client = GeminiClient()

    context_str = ""
    if extracted_json:
        context_str = f"\nExtracted Level 1 Bill Details (JSON):\n{json.dumps(extracted_json, indent=2)}\n"

    user_prompt = f"""Customer Question: {question}
{context_str}
Instructions:
- Look carefully at the bill image (including billing history table/chart, charges breakdown, and meter info) and the extracted details.
- Answer the customer's question directly, accurately, and concisely in plain English following all rules.
- Quote exact figures in PKR and units (kWh) where applicable.
- If information is not visible or covered by grey boxes, state that clearly.
"""

    answer = client.call_gemini(
        prompt=user_prompt,
        image_path=image_path,
        system_instruction=QA_SYSTEM_PROMPT,
        temperature=0.1
    )

    return scrub_pii(answer.strip())

def answer_questions_batch(
    questions: List[Dict[str, str]],
    image_path: str,
    extracted_json: Optional[Dict[str, Any]] = None,
    client: Optional[GeminiClient] = None
) -> Dict[str, str]:
    """
    Answers a list of questions for a single bill image in a single call.
    questions format: [{"question_id": "Q1", "question": "..."}, ...]
    Returns dict: {"Q1": "...", "Q2": "..."}
    """
    if client is None:
        client = GeminiClient()

    q_text = "\n".join([f"- ID: {q['question_id']} | Question: {q['question']}" for q in questions])
    context_str = ""
    if extracted_json:
        context_str = f"\nExtracted Level 1 Bill Details (JSON):\n{json.dumps(extracted_json, indent=2)}\n"

    prompt = f"""You are asked to answer the following {len(questions)} customer questions about this electricity bill image:
{q_text}
{context_str}
INSTRUCTIONS:
- Carefully inspect the bill image (including the 12-month billing history table and chart, meter info, charges, and taxes) and extracted Level 1 details.
- Answer every question thoroughly, accurately, and grounded strictly in the bill.
- Follow all answer rules (accurate numbers, summer vs winter sums, averages, labels for estimates in Q10/Q11/Q12, no personal identifiers, plain English).
- Return your output as a single JSON object where the keys are the question IDs (e.g. "Q1", "Q2") and values are your plain English answers.
Format:
{{
  "Q1": "answer text",
  "Q2": "answer text",
  ...
  "Q12": "answer text"
}}
"""

    try:
        raw_res = client.call_gemini(
            prompt=prompt,
            image_path=image_path,
            system_instruction=QA_SYSTEM_PROMPT,
            json_mode=True,
            temperature=0.1
        )
        text = raw_res.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
            text = re.sub(r"\s*```$", "", text, flags=re.MULTILINE).strip()
        batch_answers = json.loads(text)
        return {k: scrub_pii(str(v).strip()) for k, v in batch_answers.items()}
    except Exception as e:
        print(f"Batch QA call failed ({e}), falling back to individual calls...")
        fallback_answers = {}
        for q in questions:
            qid = q["question_id"]
            fallback_answers[qid] = answer_question(
                q["question"],
                image_path=image_path,
                extracted_json=extracted_json,
                client=client
            )
        return fallback_answers
