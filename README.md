# AI-Driven CEO Outreach Pilot

Generate **concise, personalised emails in the CEO’s voice** for key customers minutes after a leadership news release—without sacrificing brand, tone, or security.

---

## Table of Contents
1. Project Goals  
2. Features  
3. Repository Layout  
4. Quick Start  
5. Data Schema  
6. How It Works  

---

## 1 Project Goals
* Equip Communications with an **AI assistant** that drafts 20-30 CEO-level outreach emails in < 1 week.  
* Preserve authenticity through a **persona brief + guardrails** embedded in every call.  
* Provide a lightweight, auditable workflow that Comms can review, edit, and approve before send.

---

## 2 Features
* **Prompt-efficient design** – static persona brief sent once per request, row data only 70 tokens.  
* **Strict JSON schema** (`Person_Name`, `Company`, `Suggested_Email`) using the OpenAI-compatible `response_format` flag.  
* **Robust pipeline** – retry logic, exponential back-off, UTF-8 sanitisation, environment-based secrets.  
* **Plug-and-play persona** – update `src/ceo_brief.txt` to support other executives or languages.  
* **Low run-time cost** – ≈ US $0.002 per email on “sonar-pro”.

---

## 3 Repository Layout
ai-ceo-outreach/
│
├── README.md
├── .gitignore
│
├── src/
│ ├── main_ai_mail_sender.py
│ ├── prompt.py
│ └── ceo_brief.txt
│
├── data/
│ ├── input/ → customer_list.csv
│ └── output/ → customer_emails.csv (generated)
│
├── docs/
│ ├── AI-Driven_CEO_Outreach_Pilot.pptx

## 4 Quick Start (P y C h a r m)

1. **Clone the repository**
Paste the Git URL and press **Clone**.

2. **Create or confirm a virtual environment**
* PyCharm usually creates one automatically.  
* Verify or add it:  
  `File → Settings → Python Interpreter → Gear ⚙ → Add Interpreter → New virtualenv`.

3. **Install dependencies**
* PyCharm detects `requirements.txt` and prompts “Install requirements?” → **Yes**.  
  (If you miss the prompt, right-click `requirements.txt` → **Install**.)

4. **Add your data file**
* Copy **`customer_list.csv`** into the **same folder** as `src/main_ai_mail_sender.py`.  
  The default path is:
  ```
  <project-root>/src/customer_list.csv
  ```

5. **Insert your Perplexity API key**
* Open `src/main_ai_mail_sender.py`.  
* Find the line:
  ```
  api_key = ""
  ```
* Replace the empty string with your key, e.g.:
  ```
  api_key = "pplx-xxxxxxxxxxxxxxxx"
  ```

6. **Run the script**
* Right-click `main_ai_mail_sender.py` in the Project pane → **Run 'main_ai_mail_sender'**.

7. **Review the results**
* On success, the console prints  
  `Done. Wrote N rows to customer_emails.csv`.  
* The file is written to the same directory as the script:
  ```
  <project-root>/src/customer_emails.csv
  ```
* Open it in PyCharm or Excel to check the `Suggested_Email` column.

You’re done—no terminal commands required.

## 5 Data Schema

**`data/input/customer_list.csv`**

| Name | Company | Role | Relationship Tier | Notes |
|------|---------|------|-------------------|-------|

**Output (`customer_emails.csv`)**

| Person_Name | Company | Suggested_Email |
|-------------|---------|-----------------|

---

## 6 How It Works
1. **Load** customer rows from CSV.  
2. **Build** chat messages:  
   • `system` → CEO persona brief + guardrails  
   • `user`   → tagged row data + JSON-only instruction  
3. **Call** Perplexity Chat Completions with `response_format=json_object`.  
4. **Validate** and aggregate JSON objects.  
5. **Save** results to `data/output/customer_emails.csv` for human review.
