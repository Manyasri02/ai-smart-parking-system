# llm_client.py
import requests
import json 
import re

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "phi3:mini"

def extract_json(text: str):
    try:
        # Remove markdown ```json ``` if present
        clean = re.sub(r"```json|```", "", text).strip()
        return json.loads(clean)
    except Exception:
        return None

def build_prompt(parking_lots):
    return f"""
You are an AI Smart Parking Decision Engine.

You are NOT a chatbot.
You do NOT give general advice.
You do NOT mention maps or real-time data.

Rules:
1. Ignore parking lots where available_slots < 20% of total_slots
2. Prefer highest available_slots
3. Choose ONLY ONE parking lot
4. Output ONLY valid JSON

Parking Data:
{parking_lots}

Output format:
{{
  "id": number,
  "reason": "short factual reason"
}}
"""

def generate_text(prompt: str):
    try:
        payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False
        }

        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=120
        )
        response.raise_for_status()

        raw_output = response.json().get("response", "")
        parsed = extract_json(raw_output)

        return parsed

    except Exception as e:
        print("Ollama error:", e)
        return None
