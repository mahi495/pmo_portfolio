"""
summary.py – Generate a concise effort-variance summary and (optionally) e-mail it.

**Preference order**
1. **OpenAI GPT** (set `OPENAI_API_KEY` – first choice)
2. **Hugging Face BART** (set `HF_TOKEN` – automatic fallback if GPT absent *or* fails)

Usage:
    python summary.py <csv_or_xlsx_file>

Environment variables:
  # === Summariser (set at least one) ===
  OPENAI_API_KEY   – OpenAI key (uses gpt-4o-mini)
  HF_TOKEN         – Hugging Face token (facebook/bart-large-cnn)

  # === E-mail (all optional) ===
  EMAIL_USER       – SMTP user (e.g., Gmail address)
  EMAIL_PASS       – SMTP password / App Password
  EMAIL_TO         – Comma-separated recipients

If neither key is present, the script exits.  If both keys are present it
**tries GPT first**; on any GPT error it logs a warning and falls back to BART.
The generated SUMMARY_EMAIL.txt is deleted at the end so the file never ends
up in the repo.
"""

from __future__ import annotations

import csv
import os
import re
import smtplib
import sys
import textwrap
from email.message import EmailMessage
from pathlib import Path
from typing import List
import logging
import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────────────────────────────────────────────
# Environment & constants
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")

SMTP_USER = os.getenv("EMAIL_USER", "")
SMTP_PASS = os.getenv("EMAIL_PASS", "")
SMTP_TO = [addr.strip() for addr in os.getenv("EMAIL_TO", "").split(",") if addr.strip()]

GPT_MODEL = os.getenv("GPT_MODEL", "gpt-4o-mini")
MODEL_ID = "facebook/bart-large-cnn"
HF_API_URL = f"https://api-inference.huggingface.co/models/{MODEL_ID}"
HF_HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}

EMAIL_TMP = Path("SUMMARY_EMAIL.txt")
FILE_IN = Path(sys.argv[1]) if len(sys.argv) > 1 else None
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")

# ──────────────────────────────────────────────────────────────────────
# Summariser functions

def hf_summarise(bullets: str) -> str:
    """ Summarise text using Hugging Face BART."""
    logging.info("Using Hugging Face BART-CNN")
    payload = {"inputs": bullets, "parameters": {"max_length": 90}}
    try:
        r = requests.post(HF_API_URL, headers=HF_HEADERS, json=payload, timeout=60)
        if r.status_code == 401:
            sys.exit("ERROR: Hugging Face 401 – bad HF_TOKEN.")
        r.raise_for_status()
        return r.json()[0]["summary_text"]
    except requests.exceptions.RequestException as e:
        sys.exit(f"ERROR: HF request failed → {e}")


def gpt_summarise(bullets: str) -> str:
    """Summarise text using OpenAI ChatCompletion."""
    import openai  # import only when actually needed
    logging.info("Using OpenAI GPT-4o-mini")
    openai.api_key = OPENAI_API_KEY
    prompt = (
        "Summarise the following project issues in ≤ 90 words, plain English."
        "grouping similar items and ending with an overall RAG if obvious.\n\n"
        f"Issues: {bullets}"
    )
    resp = openai.ChatCompletion.create(
        model=GPT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return resp.choices[0].message["content"].strip()


def summarise(bullets: str) -> str:
    """Try GPT first; if it fails, fall back to HF if available."""
    if OPENAI_API_KEY:                              # first choice
    try:
        summary = gpt_summarise(text)
    except Exception as err:
        logging.warning("GPT failed → %s", err)
        if HF_TOKEN:                            # fallback
            summary = hf_summarise(text)
        else:
            sys.exit("No working GPT and no HF_TOKEN – aborting.")
    elif HF_TOKEN:                                  # no GPT key, but HF exists
        summary = hf_summarise(text)
    else:                                           # neither key is set
        sys.exit("Set OPENAI_API_KEY or HF_TOKEN in your env/secrets.")


# ──────────────────────────────────────────────────────────────────────
# Helper functions

def load_rows(path: Path):
    if path.suffix.lower() == ".csv":
        return list(csv.DictReader(path.open()))
    return pd.read_excel(path).to_dict(orient="records")


def build_bullets(rows: List[dict]) -> List[str]:
    """Return list of unique Red-task bullet strings limited to 10 items."""
    reds = [r for r in rows if str(r.get("Status_RAG", "")).lower().startswith("red")]
    if not reds:
        return ["All tasks green today – great job! 🎉"]

    effort_key = next((k for k in rows[0].keys() if re.search(r"var.*h", k, re.I)), None)
    seen, bullets = set(), []
    for r in reds:
        task = (
            r.get("Task_Name")
            or r.get("Task")
            or r.get("Work_Package")
            or "(no name)"
        ).strip()
        task = re.sub(r"\s+", " ", task)
        key = task.lower()
        if key in seen:
            continue  # de-dupe
        seen.add(key)
        hrs = r.get(effort_key, "?") if effort_key else "?"
        bullets.append(f"{task}: {hrs}h over")
        if len(bullets) == 10:
            break
    return bullets


def craft_email(summary: str) -> EmailMessage:
    body = textwrap.dedent(
        f"""\
        Hello Team,

        Below is today’s effort-variance snapshot generated by the PMO pipeline.

        {summary}

        Next steps
        • Review the items above and confirm root causes.
        • Add recovery actions or updated ETAs to the project tracker before 17:00 PKT today.

        Thanks,
        Hafiza Maham
        """
    )
    msg = EmailMessage()
    msg["Subject"] = "Daily PMO Effort-Variance Snapshot"
    msg["From"] = SMTP_USER or "pmo-bot@example.com"
    msg["To"] = ", ".join(SMTP_TO) or SMTP_USER
    msg.set_content(body)
    return msg


def send_mail(msg: EmailMessage) -> None:
    if not (SMTP_USER and SMTP_PASS and (SMTP_TO or SMTP_USER)):
        print("[warn] Mail creds missing – skipping SMTP send.")
        return
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(SMTP_USER, SMTP_PASS)
        s.send_message(msg)

# ──────────────────────────────────────────────────────────────────────
# Main

def main():
    if not FILE_IN or not FILE_IN.exists():
        sys.exit("Usage: python summary.py <csv_or_xlsx_file>")

    rows = load_rows(FILE_IN)
    bullets = build_bullets(rows)
    summary_text = summarise("; ".join(bullets))

    EMAIL_TMP.write_text(summary_text, encoding="utf-8")
    print("\n" + textwrap.fill(summary_text, 100) + "\n")

    send_mail(craft_email(summary_text))

    try:
        EMAIL_TMP.unlink()
    except FileNotFoundError:
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
