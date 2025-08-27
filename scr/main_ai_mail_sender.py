#!/usr/bin/env python3
"""
run_perplexity.py

Reads customer_list.csv (Name,Company,Role,Relationship,Notes),
builds a tailored prompt via prompt.get_prompt(...),
calls Perplexity's Chat Completions API once per row,
expects a JSON response with:
  {
    "Person_Name": "...",
    "Company": "...",
    "Suggested_Email": "..."
  }
and writes aggregated results to customer_emails.csv.

Environment:
  PPLX_API_KEY=<your api key>

Usage:
  python run_perplexity.py
"""

import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

import requests

def clean_text(s: str) -> str:
    if not s:
        return s
    # Fix common UTF-8/Latin1 issues
    return s.encode("latin1", errors="ignore").decode("utf-8", errors="ignore")

# ---- Import your prompt builder ----
try:
    from prompt import build_messages
except ImportError as e:
    print("Error: could not import get_prompt from prompt.py. Make sure this file is in the same directory.")
    raise e

PPLX_API_URL = "https://api.perplexity.ai/chat/completions"
OUTPUT_CSV = "customer_emails.csv"
INPUT_CSV = "customer_list.csv"
MODEL = "sonar-pro"  # adjust if you use a different model

# ---------- Add response_format ----------
MAX_TOKENS = 300          # plenty for 3-key JSON + ≤200-word email
TEMPERATURE = 0.2
TIMEOUT_SECS = 60
MAX_RETRIES = 5
RETRY_BACKOFF_BASE = 2.0  # exponential backoff factor

def call_perplexity(api_key: str, messages: List[Dict[str, str]], timeout: int = TIMEOUT_SECS):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
        #"response_format": {"type": "json_object"},   # <= OFFICIAL FLAG
    }

    attempt = 0
    while True:
        attempt += 1
        try:
            resp = requests.post(PPLX_API_URL, headers=headers, json=payload, timeout=timeout)
            # Retry on rate limits or transient server errors
            if resp.status_code in (429, 500, 502, 503, 504):
                if attempt >= MAX_RETRIES:
                    resp.raise_for_status()
                sleep_s = (RETRY_BACKOFF_BASE ** (attempt - 1))
                time.sleep(sleep_s)
                continue

            resp.raise_for_status()
            data = resp.json()
            # Perplexity returns OpenAI-like structure:
            content = data["choices"][0]["message"]["content"]
            # content should be a JSON string per response_format=json_object
            return json.loads(content)

        except (requests.RequestException, ValueError, KeyError, json.JSONDecodeError) as e:
            if attempt >= MAX_RETRIES:
                raise
            sleep_s = (RETRY_BACKOFF_BASE ** (attempt - 1))
            time.sleep(sleep_s)


def validate_output(obj: Dict[str, Any], fallback_name: str, fallback_company: str) -> Dict[str, str]:
    """
    Ensure we have the three keys; fall back to input name/company if missing.
    """
    out = {
        "Person_Name": str(obj.get("Person_Name", fallback_name)).strip(),
        "Company": str(obj.get("Company", fallback_company)).strip(),
        "Suggested_Email": str(obj.get("Suggested_Email", "")).strip(),
    }
    print(out)
    return out


def read_rows(csv_path: Path) -> List[Dict[str, str]]:
    """
    Read input CSV with required columns.
    """
    required = {"Name", "Company", "Role", "Relationship Tier", "Notes"}
    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        header = set(reader.fieldnames or [])
        missing = required - header
        if missing:
            raise ValueError(f"Input CSV missing required columns: {', '.join(sorted(missing))}")
        return [ {k: (row.get(k) or "").strip() for k in reader.fieldnames} for row in reader ]


def write_rows(csv_path: Path, rows: List[Dict[str, str]]) -> None:
    """
    Write output CSV.
    """
    fieldnames = ["Person_Name", "Company", "Suggested_Email"]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def main() -> int:
    api_key = ""
    if not api_key:
        print("Error: PPLX_API_KEY environment variable is not set.", file=sys.stderr)
        return 1

    input_path = Path(INPUT_CSV)
    if not input_path.exists():
        print(f"Error: '{INPUT_CSV}' not found in current directory.", file=sys.stderr)
        return 1

    try:
        rows = read_rows(input_path)
    except Exception as e:
        print(f"Error reading input CSV: {e}", file=sys.stderr)
        return 1

    outputs: List[Dict[str, str]] = []
    for idx, row in enumerate(rows, start=1):
        messages = build_messages(
            person_name=row.get("Name", ""),
            company=row.get("Company", ""),
            role=row.get("Role", ""),
            relationship=row.get("Relationship Tier", ""),
            notes=row.get("Notes", "")
        )

        try:
            result_obj = call_perplexity(api_key, messages)
            validated = validate_output(result_obj,
                                        fallback_name=row.get("Name", ""),
                                        fallback_company=row.get("Company", ""))
        except Exception as e:
            validated = {
                "Person_Name": row.get("Name", ""),
                "Company": row.get("Company", ""),
                "Suggested_Email": f"[ERROR] {type(e).__name__}: {e}",
            }

        outputs.append({k: clean_text(v) for k, v in validated.items()})

    write_rows(Path(OUTPUT_CSV), outputs)
    print(f"Done. Wrote {len(outputs)} rows to {OUTPUT_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
