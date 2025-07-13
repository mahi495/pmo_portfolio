# summary.py
import os, csv, sys, textwrap, requests
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")
MODEL_ID = "facebook/bart-large-cnn"
API_URL  = f"https://api-inference.huggingface.co/models/{MODEL_ID}"
HEADERS  = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}

FILE_IN   = Path(sys.argv[1])           # path passed by workflow or CLI
EMAIL_OUT = Path("SUMMARY_EMAIL.txt")

# ---------------------------------------------------------------------
def hf_summarise(text: str) -> str:
    if not HF_TOKEN:
        sys.exit("ERROR: HF_TOKEN environment variable is missing. "
                 "Set it locally or add it as a GitHub secret.")

    payload = {"inputs": text, "parameters": {"max_length": 90}}
    try:
        r = requests.post(API_URL, headers=HEADERS, json=payload, timeout=60)
        if r.status_code == 401:
            sys.exit("ERROR: Hugging Face returned 401 – invalid or expired HF_TOKEN.")
        r.raise_for_status()
        return r.json()[0]["summary_text"]
    except requests.exceptions.RequestException as e:
        sys.exit(f"ERROR: Request to Hugging Face failed → {e}")

# ---------------------------------------------------------------------
def load_rows(path: Path):
    if path.suffix.lower() == ".csv":
        import csv
        return list(csv.DictReader(path.open()))
    else:                                # .xlsx
        return pd.read_excel(path).to_dict(orient="records")

def build_prompt(rows):
    reds = [r for r in rows if str(r.get("Status_RAG", "")).lower() == "red"]
    if not reds:
        return "Good news—no red tasks today."

    # find a key that looks like effort variance hours
    effort_key = next(
        (k for k in rows[0].keys()
         if "effort" in k.lower() and "var" in k.lower() and "hr" in k.lower()),
        None
    )

    parts = []
    for r in reds[:10]:
        effort = r.get(effort_key, "?") if effort_key else "?"
        parts.append(f'{r.get("Task_Name", "(no name)")}: {effort}h over')
    return "Summarize project issues: " + "; ".join(parts)

# ---------------------------------------------------------------------
def main():
    rows = load_rows(FILE_IN)
    summary = hf_summarise(build_prompt(rows))
    EMAIL_OUT.write_text(summary)
    print(textwrap.fill(summary, 100))

if __name__ == "__main__":
    main()
