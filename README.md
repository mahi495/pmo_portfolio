# 🦾 AI-Powered PMO Portfolio 🚀  
*Turn raw Jira & Excel data into a living dashboard **and** auto-e-mailed AI summaries – 100 % free-tools first.*

---

## 1 · What’s inside

| Path / file | Purpose |
|-------------|---------|
| `data/` | Mock **Project_Schedule.xlsx** & **Jira_export.csv** so you can test end-to-end without corporate data. |
| `scripts/summary.py` | Reads today’s CSV → builds a bullet list of Red tasks → **tries GPT** (`gpt-3.5-turbo` or `gpt-4o-mini`) → if key missing / quota exhausted, falls back to **Hugging Face BART** → e-mails the digest → deletes the temp txt. |
| `.github/workflows/summary.yml` | Scheduled Action that runs every morning PK T, assembles an e-mail, and sends via Gmail. |
| `powerbi/PM_Dashboard.pbix` | Finished report (earned-value KPIs, slicers). |

---

## 2 · Quick start (local/free path)

```bash
# clone + venv
git clone https://github.com/mahi495/pmo_portfolio.git && cd pmo_portfolio
python -m venv .venv && . .venv/Scripts/activate          # Windows: .\.venv\Scripts\activate
pip install -r requirements.txt                          # pandas, requests, transformers

# choose ONE summariser key
set HF_TOKEN=hf_...            # 100 % free (preferred for zero cost)
# — or —
set OPENAI_API_KEY=sk-...      # pay-as-you-go (first US $5 credit free)

# optional mail creds
set EMAIL_USER=you@gmail.com
set EMAIL_PASS=16-char-app-password
set EMAIL_TO="team@example.com"

python scripts/summary.py data/Jira_export.csv

# === Summariser (pick ONE engine) ===
OPENAI_API_KEY   # first preference – GPT (pay-as-you-go)
HF_TOKEN         # fallback / free – facebook/bart-large-cnn

# === E-mail (optional) ===
EMAIL_USER       # Gmail address
EMAIL_PASS       # 16-char App-Password
EMAIL_TO         # comma-separated list

# === Tuning (optional) ===
GPT_MODEL=gpt-3.5-turbo    # 10× cheaper than 4-o-mini
LOG_LEVEL=DEBUG            # more verbose logs

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
- [ ] 🔒 Secrets → Azure Key Vault binding for Actions.
- [ ] 🌐 Multi‑language summaries (`?lang=es` query‑param).
- [ ] 📊 Embed the PBI dashboard in SharePoint PMO portal.
- [ ] 🤖 Teams slash‑command: `/pmo today` to trigger the run on demand.

---

— Built with ❤️ in Lahore PK · [LinkedIn](https://www.linkedin.com/in/hafizamahamejaz/)
