# summary.py
import os, csv, io, sys, textwrap, json, requests
from pathlib import Path
import pandas as pd   # add to requirements.txt

HF_TOKEN = os.getenv("HF_TOKEN")
MODEL_ID = "facebook/bart-large-cnn"
API_URL  = f"https://api-inference.huggingface.co/models/{MODEL_ID}"
HEADERS  = {"Authorization": f"Bearer {HF_TOKEN}"}

FILE_IN  = Path(sys.argv[1])           # path passed by workflow
EMAIL_OUT = Path("SUMMARY_EMAIL.txt")

def hf_summarise(text: str) -> str:
    payload = {"inputs": text, "parameters": {"max_length": 90}}
    r = requests.post(API_URL, headers=HEADERS, json=payload, timeout=60)
    r.raise_for_status()
    return r.json()[0]["summary_text"]

def load_rows(path: Path):
    if path.suffix.lower() == ".csv":
        return list(csv.DictReader(path.open()))
    else:                               # .xlsx
        return pd.read_excel(path).to_dict(orient="records")

def build_prompt(rows):
    reds = [r for r in rows if str(r.get("Status_RAG","")).lower()=="red"]
    if not reds:
        return "Good news—no red tasks today."
    parts = [f'{r["Task_Name"]}: {r["Effort_Variance_hrs"]}h over'
             for r in reds[:10]]
    return "Summarize project issues: " + "; ".join(parts)

def main():
    rows = load_rows(FILE_IN)
    summary = hf_summarise(build_prompt(rows))
    EMAIL_OUT.write_text(summary)
    print(textwrap.fill(summary, 100))

if __name__ == "__main__":
    main()
