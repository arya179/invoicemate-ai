# InvoiceMate AI 🧾

> **AI-Powered Invoice & Expense Management for Freelancers and Small Businesses**  
> Built for the **Hacktoberfest Week 2: Side Hustle Edition**.

InvoiceMate AI simplifies financial record-keeping for independent contractors, solopreneurs, and small business owners. It runs **100% locally on your machine** using Ollama and the lightweight `gemma:2b` model—keeping your financial records, client names, and billing data strictly confidential without incurring third-party cloud API costs or data leakage risks.

---

## ✨ Features

- 📊 **Polished Business Dashboard**:
  - Real-time expense metrics: **Total Expenses**, **Total Invoices**, **Top Expense Category**, and **Average Invoice Amount** with helpful tooltips.
  - Interactive **Spending by Category** bar chart.
  - **Recent Invoices** chronological feed ordered by latest invoice date (or creation date if unlisted) with high-contrast vendor names, totals, and demo vs. real badges.
  - **Guided First-Use Experience**: Clean welcome card and step-by-step visual workflow when the database is empty.
- 📄 **Multi-Format Ingestion**: Supports digital PDF documents, scanned paper receipts, and image files (`.png`, `.jpg`, `.jpeg`).
- 🔍 **Hybrid Text Extraction Pipeline**: 
  - Direct digital text extraction with **PyMuPDF**.
  - Automatic fallback to **Tesseract OCR** for scanned documents or image receipts with sparse text.
- 🤖 **Local AI Structuring (`gemma:2b` via Ollama)**:
  - Extracts Vendor Name, Invoice Number, Invoice Date, Subtotal, Tax, Total, Currency, and Expense Category into structured JSON.
  - Robust regex fallback heuristics if the document is irregular or Ollama is offline.
  - Progress indicator tracking byte reading, OCR/PyMuPDF text extraction, and local LLM inference.
- 🛡️ **Human-in-the-Loop Review & Data Validation**:
  - An editable verification form ensures you inspect and correct numbers, tax, currency, and dates before saving.
  - Accidental duplicate detection warns if an invoice from the same vendor with the same number or date and total already exists.
  - Zero unverified or automatic saves to the database.
- 🗄️ **Complete Invoice Data Management**:
  - Searchable, filterable directory with category and data-type (All / Real / Demo) filters.
  - Full details modal for inspecting individual invoice metadata and notes.
  - **Delete Selected Invoice** with explicit confirmation.
  - **Clear Demo Invoices Only** to remove synthetic test data without touching real invoices.
  - **Clear All Invoices (Full Reset)** with explicit double confirmation ("DELETE ALL" typing prompt).
  - Database deletion and dashboard statistics remain synchronized immediately.
- 📥 **Flexible CSV Export**:
  - Export filtered search subsets or export the complete database with a single click.
  - Helpful message displayed when no records exist.
- 🧪 **Built-in Synthetic Invoice Generator**:
  - Generates realistic, watermarked PDF test invoices (Cloud Hosting, SaaS, Office Supplies) for safe demonstration without revealing confidential client data.
- ❓ **Beginner-Friendly Help & About**:
  - Explains dashboard calculations, auto-rerun mechanics, local AI, and security in plain language.

---

## 🛠️ Tech Stack & Prerequisites

- **Operating System**: Ubuntu Linux (or any modern Linux, macOS, or Windows WSL2)
- **Language**: Python 3.10+
- **Frontend / Web UI**: [Streamlit](https://streamlit.io/)
- **Local AI Engine**: [Ollama](https://ollama.ai/) with `gemma:2b`
- **PDF Extraction**: [PyMuPDF](https://pymupdf.readthedocs.io/)
- **OCR Engine**: Tesseract OCR (`tesseract-ocr` system package & `pytesseract`)
- **Database**: SQLite3 (`invoices.db`)
- **Data Manipulation**: Pandas

---

## 🚀 Step-by-Step Installation & Setup (Ubuntu Linux)

### 1. Install System Dependencies (Tesseract OCR)
Ensure system packages for optical character recognition are installed:
```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr python3-venv python3-pip
```

### 2. Set Up & Run Ollama with Gemma 2B
Install and start Ollama on your local machine:
```bash
# 1. Install Ollama (if not already installed)
curl -fsSL https://ollama.com/install.sh | sh

# 2. Start the Ollama background daemon (if not running as a systemd service)
ollama serve

# 3. In another terminal, download and run the Gemma 2B model
ollama pull gemma:2b

# 4. Verify the model is available
ollama list
```

### 3. Create & Activate Python Virtual Environment
Navigate to your project directory, create a dedicated `venv`, and activate it:
```bash
cd /home/bisagn/hackoberfest/week_2

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip and install Python packages
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Launch the Streamlit Application
```bash
streamlit run app.py
```
Open your browser and navigate to:
```
http://localhost:8501
```

---

## 🧭 Using the Navigation Sections

### 1. 📊 Dashboard
- **Metric Cards**: View your **Total Expenses**, **Total Invoices** (with breakdown of real vs. demo), **Top Expense Category**, and **Average Invoice Amount**.
- **Category Chart**: Visualizes spending distribution across business categories (*Cloud & Hosting*, *Software & SaaS*, *Office Supplies*, etc.).
- **Recent Invoices**: Displays the latest 5 transactions ordered by invoice date, clearly marked with dark navy text contrast and `REAL` vs. `DEMO` status pills.
- **Empty State**: When no invoices exist in the database, a guided 6-step walkthrough appears to orient first-time users.

### 2. 📤 Upload & Parse
- **Upload File**: Drag-and-drop or browse for PDF, PNG, JPG, or JPEG files (up to 10MB).
- **Document Preview**: Visual preview of your uploaded image or page 1 of your PDF.
- **Demo Tag**: Check the demo checkbox if uploading synthetic test data to facilitate one-click cleanup later.
- **Process Invoice with Gemma 2B**: Triggers text extraction and Ollama local LLM inference with a live step-by-step progress bar.
- **Review & Edit Form**: Inspect the extracted vendor, invoice number, date, category, currency, subtotal, tax, and total. Modify any field if necessary, view duplicate warnings if applicable, and click **Save Confirmed Invoice**.

### 3. 📑 All Invoices
- **Search & Filter**: Filter records by text keyword (vendor name, invoice number, or notes), expense category, or record type (*All*, *Real Only*, *Demo Only*).
- **Interactive Table**: Clean overview table with all columns formatted.
- **CSV Export**: Click **Export Filtered as CSV** to download currently visible results, or **Export Complete Database as CSV** to download all records.
- **View Full Details & Edit**: Select an invoice from the dropdown to review its full details or update fields.
- **Delete Single Invoice**: Select an invoice ID, check the confirmation box, and permanently delete it from SQLite.
- **Clear Demo / All Invoices**:
  - **Option A (Clear Demo Invoices Only)**: Safely purges mock demo records while preserving all your real invoices.
  - **Option B (Clear All Records)**: Requires typing `DELETE ALL` and checking the acknowledgement box before executing a full database wipe and vacuum.

### 4. 🧪 Sample Generator
- Select from predefined templates (*Cloud Hosting*, *Software Subscription*, *Office Stationery*).
- Click **Download PDF** to generate an offline, synthetic test invoice with clear watermark disclaimers.
- Test the full OCR and AI pipeline by uploading the downloaded sample invoice in the **Upload & Parse** view.

### 5. ❓ Help & About
- Simple explanations of all business metrics and terminology.
- Clarification on **Streamlit Auto Rerun** (widget interactions re-execute the script locally for UI updates, not re-processing or re-uploading invoices).
- Explanation of **Local AI**, **Tesseract OCR**, and security policies.

---

## 🔒 Privacy, Security & Git Hygiene

- **100% Local Inference**: Your invoices, financial sums, vendor names, and client details never leave your machine.
- **Parameterized SQL**: All SQLite database queries use parameterized placeholders (`?`) to prevent SQL injection vulnerabilities.
- **Git Protection**: Sensitive and generated artifacts are strictly ignored in `.gitignore`:
  - `invoices.db` and `*.db`
  - `.venv/` and `venv/`
  - `.env` and `.streamlit/secrets.toml`
  - `uploads/`
- **Synthetic Test Data**: The built-in test generator produces synthetic data with explicit evaluation labels to avoid confusion with real accounting records.

---

## 🔧 Troubleshooting

| Symptom | Cause | Solution |
| :--- | :--- | :--- |
| `🟡 AI Status: Cannot connect to local Ollama service` | Ollama daemon is not running | Run `ollama serve` in a terminal or verify `systemctl status ollama`. |
| `🟡 AI Status: Model 'gemma:2b' was not found` | Model has not been pulled | Run `ollama pull gemma:2b` in your terminal. |
| Scanned PDF extraction returns no text | Missing system Tesseract OCR | Run `sudo apt-get install tesseract-ocr`. |
| Deprecation warning for `use_container_width` | Older Streamlit parameter syntax | Replaced across all widgets with `width="stretch"` or `width="content"`. |
| Text contrast in invoice cards | Dark theme inversion | Addressed with high-contrast navy `#172554` and slate `#64748B` styling. |

---

## 📜 License & Acknowledgements
Developed for **Hacktoberfest Week 2: Side Hustle Edition**. Built with open-source tools including Streamlit, Ollama, Google Gemma 2B, PyMuPDF, Tesseract OCR, and SQLite.

