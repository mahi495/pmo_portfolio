# AI‑Powered PMO Portfolio 

*Turn raw Jira & Excel data into a living dashboard **and** auto‑e‑mailed GPT summaries – in one repo.*

---

## 1 · What’s inside

| Folder / file | What it does |
|---------------|-------------|
| `data/` | Tiny mock *Project_Schedule.xlsx* + *Jira_export.csv* so you can test end‑to‑end without corporate data. |
| `scripts/summary.py` | Reads today’s CSV → builds a bullet list → **tries GPT‑4o‑mini** → if that fails, falls back to **BART‑CNN** on Hugging Face → e‑mails the digest → deletes the temp txt. |
| `.github/workflows/summary.yml` | A scheduled Action that runs the script every morning PKT, assembles an HTML‑ish e‑mail, and sends it via Gmail. |
| `powerbi/PM_Dashboard.pbix` | Finished report (earned‑value KPIs, slicers). |

---

## 2 · Quick start (local)
```bash
# clone + set up venv
$ git clone https://github.com/mahi495/pmo_portfolio.git && cd pmo_portfolio
$ python -m venv .venv && source .venv/bin/activate
$ pip install -r requirements.txt

# one of the TWO summariser keys is enough
$ export OPENAI_API_KEY=sk‑...
# OR
$ export HF_TOKEN=hf_...

# optional mail creds
$ export EMAIL_USER=you@gmail.com EMAIL_PASS=16‑char‑app‑pwd EMAIL_TO="team@example.com"

# optional: more verbose logs
set LOG_LEVEL=DEBUG

# run it
$ python scripts/summary.py data/Jira_export.csv
```
You should see a 60‑‑90‑word executive summary in the console; if mail creds are set you’ll get an e‑mail too.

---

## 3 · GitHub Actions daily run
The included workflow triggers on **push**, on a **Run workflow** button, and **every day at 05:00 UTC** (10:00 PKT).

Add these four secrets in **Settings → Secrets → Actions**:
| Secret | Needed for |
|--------|------------|
| `OPENAI_API_KEY` *or* `HF_TOKEN` | Summariser (set at least one) |
| `EMAIL_USER` | Gmail address (SMTP user) |
| `EMAIL_PASS` | 16‑char App Password (not your real password!) |
| `EMAIL_TO` | `alice@x.com,bob@y.com` |

> **Tip:** If you don’t want e‑mail, skip the last three secrets – the job will still pass and upload the summary as an artifact.

---

## 4 · Environment variables (recap)
```text
# === Summariser (choose ONE engine) ===
OPENAI_API_KEY   # first preference – GPT‑4o‑mini
HF_TOKEN         # fallback – facebook/bart‑large‑cnn

# === E‑mail (optional) ===
EMAIL_USER       # e.g. you@gmail.com
EMAIL_PASS       # Gmail App‑Password (16 chars)
EMAIL_TO         # comma‑separated list

# === Logging/tuning (optional) ===
LOG_LEVEL=DEBUG          # INFO by default; DEBUG for full stack traces
GPT_MODEL=gpt-3.5-turbo  # 10× cheaper than gpt-4o-mini
```
If both keys are present, the script **tries OpenAI first** – on any error, it logs a warning and falls back to Hugging Face.

---

## 5 · Getting a free OpenAI key
1. Sign up at <https://platform.openai.com/> (verify e‑mail + phone).  
2. Go to **⚙️ Settings → API keys → Create new secret key**.  
3. Copy the string (starts with `sk‑`). Paste it into your local shell or GitHub secret.

New accounts receive **US$5 free credit** (enough for ±10,000 summaries) valid for 3 months. After that, add a payment method or swap to the free Hugging Face tier.

---

## 6 · Dashboard refresh loop
```
Jira → CSV ─┐                     ┌─▶ Power BI Service (auto‑refresh)
            │ Power Query (merge) │
Excel plan ─┘                     └─▶ KPIs: Var %, CPI, Status_RAG
                                        ▲
summary.py ◀──── GitHub Actions / Flow ──┘
                 (daily 05:00 UTC)
```
* **Office Scripts** (optional) adds the `Status_RAG` column inside Excel.  
* **Power Automate** version: use the flow zip if you live in M365.

---

## 7 · Roadmap
- [ ] Secrets → Azure Key Vault binding for Actions.
- [ ] Multi‑language summaries (`?lang=es` query‑param).
- [ ] Embed the PBI dashboard in SharePoint PMO portal.
- [ ] Teams slash‑command: `/pmo today` to trigger the run on demand.

---

— Built with ❤️ in Lahore PK · [LinkedIn](https://www.linkedin.com/in/hafizamahamejaz/)
