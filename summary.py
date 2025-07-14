"""
summary.py  –  Generate a concise effort-variance summary and (optionally) e-mail it.

Preference order
----------------
1️⃣  OpenAI GPT-4o-mini  ........  needs  OPENAI_API_KEY
2️⃣  Hugging Face BART  .........  needs  HF_TOKEN      (used if GPT key absent *or* GPT call fails)

If neither key is present the script exits with code 1.

Optional mail:
  EMAIL_USER, EMAIL_PASS, EMAIL_TO   →  sent via smtp.gmail.com:465
  (skips SMTP gracefully if any of the three is missing)

Usage:
  python summary.py <csv_or_xlsx_file>
"""

from __future__ import annotations

import csv
import logging
import os
import re
import smtplib
import sys
import textwrap
from email.message import EmailMessage
from pathlib import Path
from typing import List

import pandas as pd
import requests
from dotenv import load_dotenv

# ────────────────────────────────  env & logging  ──────────────────────────────
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
HF_TOKEN       = os.getenv("HF_TOKEN")

SMTP_USER = os.getenv("EMAIL_USER", "")
SMTP_PASS = os.getenv("EMAIL_PASS", "")
SMTP_TO   = [a.strip() for a in os.getenv("EMAIL_TO", "").split(",") if a.strip()]

GPT_MODEL   = os.getenv("GPT_MODEL", "gpt-4o-mini")
HF_MODEL_ID = "facebook/bart-large-cnn"
HF_API_URL  = f"https://api-inference.huggingface.co/models/{HF_MODEL_ID}"
HF_HEADERS  = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}

EMAIL_TMP = Path("SUMMARY_EMAIL.txt")

LOG_LEVEL  = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL, format="%(levelname)s  %(message)s")

# ────────────────────────────────  summariser  ────────────────────────────────
def gpt_summarise(bullets: str) -> str:
    """Summarise using OpenAI ChatCompletion (GPT-4o-mini)."""
    import openai
    logging.info("🔮  Trying OpenAI GPT (%s)", GPT_MODEL)
    openai.api_key = OPENAI_API_KEY

    prompt = (
        "Summarise the following project issues in ≤90 words of plain English, "
        "group similar items, end with an overall RAG if obvious.\n\n"
        f"Issues: {bullets}"
    )

    response = openai.ChatCompletion.create(
        model=GPT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return response.choices[0].message["content"].strip()


def hf_summarise(bullets: str) -> str:
    """Summarise using Hugging Face BART (free inference endpoint)."""
    logging.info("🤖  Falling back to Hugging Face BART")
    payload = {"inputs": bullets, "parameters": {"max_length": 90}}
    try:
        r = requests.post(HF_API_URL, headers=HF_HEADERS, json=payload, timeout=60)
        if r.status_code == 401:
            sys.exit("ERROR 401 – invalid HF_TOKEN")
        r.raise_for_status()
        return r.json()[0]["summary_text"]
    except requests.exceptions.RequestException as e:
        sys.exit(f"ERROR: Hugging Face request failed → {e}")


def summarise(bullets: str) -> str:
    """
    Try GPT first; if GPT key missing *or* any GPT error occurs, try Hugging Face.
    Exit if both engines are unavailable.
    """
    if OPENAI_API_KEY:
        try:
            return gpt_summarise(bullets)
        except Exception as err:
            logging.warning("⚠️  GPT call failed – %s", err)

    if HF_TOKEN:
        return hf_summarise(bullets)

    sys.exit("No OPENAI_API_KEY or HF_TOKEN supplied – cannot summarise.")

# ────────────────────────────────  helpers  ───────────────────────────────────
def load_rows(path: Path) -> List[dict]:
    if path.suffix.lower() == ".csv":
        return list(csv.DictReader(path.open()))
    return pd.read_excel(path).to_dict(orient="records")


def build_bullets(rows: List[dict]) -> List[str]:
    """Return list of unique Red-status bullets (max 10)."""
    reds = [r for r in rows if str(r.get("Status_RAG", "")).lower().startswith("red")]
    if not reds:
        return ["All tasks green today – great job! 🎉"]

    effort_key = next((k for k in rows[0] if re.search(r"var.*h", k, re.I)), None)

    seen, bullets = set(), []
    for r in reds:
        task = (
            r.get("Task_Name")
            or r.get("Task")
            or r.get("Work_Package")
            or "(no name)"
        ).strip()
        norm = re.sub(r"\s+", " ", task).lower()
        if norm in seen:
            continue  # de-dupe
        seen.add(norm)

        hrs = r.get(effort_key, "?") if effort_key else "?"
        bullets.append(f"{task}: {hrs}h over")
        if len(bullets) == 10:
            break

    return bullets


def craft_email(summary: str) -> EmailMessage:
    body = textwrap.dedent(
        f"""\
        Hello Team,

        Below is today’s effort-variance snapshot generated automatically.

        {summary}

        Next steps
        • Review items above and confirm root causes.
        • Add recovery actions or updated ETAs to the tracker before 17:00 PKT.

        Thanks,
        Hafiza Maham
        """
    )
    msg = EmailMessage()
    msg["Subject"] = "Daily PMO Effort-Variance Snapshot"
    msg["From"]    = SMTP_USER or "pmo-bot@example.com"
    msg["To"]      = ", ".join(SMTP_TO) or SMTP_USER
    msg.set_content(body)
    return msg


def send_mail(msg: EmailMessage) -> None:
    if not (SMTP_USER and SMTP_PASS and (SMTP_TO or SMTP_USER)):
        logging.warning("📭  Mail creds missing – skipping SMTP send.")
        return
    logging.info("📧  Sending e-mail to %s", ", ".join(SMTP_TO) or SMTP_USER)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(SMTP_USER, SMTP_PASS)
        s.send_message(msg)

# ────────────────────────────────  main  ──────────────────────────────────────
def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("Usage: python summary.py <csv_or_xlsx_file>")

    file_in = Path(sys.argv[1])
    if not file_in.exists():
        sys.exit(f"Input file not found: {file_in}")

    logging.info("📂  Loading data from %s", file_in)
    rows    = load_rows(file_in)
    bullets = build_bullets(rows)
    summary = summarise("; ".join(bullets))

    EMAIL_TMP.write_text(summary, encoding="utf-8")
    print("\n" + textwrap.fill(summary, 100) + "\n")

    send_mail(craft_email(summary))

    try:
        EMAIL_TMP.unlink()
        logging.debug("🗑️  Deleted %s", EMAIL_TMP)
    except FileNotFoundError:
        pass

    logging.info("✅  Done.")
    sys.exit(0)


if __name__ == "__main__":
    main()
