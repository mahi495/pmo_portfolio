import csv, os, requests, json, textwrap, sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

HF_TOKEN   = os.getenv("HF_TOKEN")        # ← Hugging Face free token
MODEL_ID   = "facebook/bart-large-cnn"
API_URL    = f"https://api-inference.huggingface.co/models/{MODEL_ID}"
HEADERS    = {"Authorization": f"Bearer {HF_TOKEN}"}

CSV_PATH   = Path(sys.argv[1])
EMAIL_FILE = Path("SUMMARY_EMAIL.txt")

def hf_summary(text: str) -> str:
    payload = {"inputs": text, "parameters": {"max_length": 90}}
    r = requests.post(API_URL, headers=HEADERS, json=payload, timeout=60)
    r.raise_for_status()
    return r.json()[0]["summary_text"]

def build_prompt(rows):
    reds = [r for r in rows if r["Status_RAG"].lower() == "red"]
    if not reds:
        return "Good news—no red tasks today."
    parts = [f'{r["Task_Name"]}: {r["Effort_Variance_hrs"]} h over'
             for r in reds[:10]]
    return "Summarize project issues: " + "; ".join(parts)

def main(csv_path: Path):
    rows = list(csv.DictReader(csv_path.open()))
    summary = hf_summary(build_prompt(rows))
    EMAIL_FILE.write_text(summary)
    print("SUMMARY:\n", textwrap.fill(summary, 100))

if __name__ == "__main__":
    main(CSV_PATH)
