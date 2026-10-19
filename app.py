"""
InvoiceMate AI - Web Application
Streamlit UI for AI-powered invoice and expense management.
Designed for freelancers and small businesses (Hacktoberfest Week 2 Side Hustle).
"""

import io
import os
import datetime
import pandas as pd
import streamlit as st
import pymupdf as fitz
from PIL import Image

import database as db
import invoice_parser as parser

# Page configuration
st.set_page_config(
    page_title="InvoiceMate AI | Smart Expense Tracker",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize database
db.init_db()

# Custom CSS for modern business styling
st.markdown(
    """
    <style>
    /* Global container styling */
    .main {
        background-color: #F8FAFC;
        color: #0F172A;
    }
    
    /* Typography */
    h1, h2, h3, h4 {
        color: #0F2042;
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    
    /* Metric Cards */
    .metric-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.08);
    }
    .metric-label {
        font-size: 0.85rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .metric-value {
        font-size: 1.85rem;
        font-weight: 700;
        color: #0F2042;
    }
    .metric-subtext {
        font-size: 0.8rem;
        color: #64748B;
        margin-top: 6px;
    }

    /* Disclaimer banner */
    .disclaimer-banner {
        background-color: #EFF6FF;
        border-left: 4px solid #2563EB;
        padding: 12px 16px;
        border-radius: 0 8px 8px 0;
        font-size: 0.88rem;
        color: #1E40AF;
        margin-bottom: 20px;
    }

    /* Status badges */
    .badge-pill {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 600;
        background-color: #E2E8F0;
        color: #334155;
    }
    .badge-demo {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 9999px;
        font-size: 0.72rem;
        font-weight: 700;
        background-color: #FEF3C7;
        color: #92400E;
        border: 1px solid #FCD34D;
    }
    .badge-real {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 9999px;
        font-size: 0.72rem;
        font-weight: 700;
        background-color: #DCFCE7;
        color: #166534;
        border: 1px solid #86EFAC;
    }

    /* Invoice Cards */
    .invoice-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        padding: 14px;
        border-radius: 8px;
        margin-bottom: 10px;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
    }
    .invoice-card-vendor {
        font-weight: 700;
        color: #172554 !important;
        font-size: 0.98rem;
    }
    .invoice-card-total {
        font-weight: 700;
        color: #172554 !important;
        font-size: 1.05rem;
    }
    .invoice-card-meta {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.82rem;
        color: #64748B !important;
        margin-top: 6px;
    }

    /* Welcome / Empty State Card */
    .welcome-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 28px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
        margin-bottom: 24px;
    }
    .step-box {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 16px;
        height: 100%;
    }
    .step-number {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 28px;
        height: 28px;
        border-radius: 50%;
        background-color: #2563EB;
        color: #FFFFFF;
        font-weight: 700;
        font-size: 0.85rem;
        margin-bottom: 8px;
    }
    .step-title {
        font-weight: 600;
        color: #0F2042;
        font-size: 0.95rem;
        margin-bottom: 4px;
    }
    .step-desc {
        font-size: 0.82rem;
        color: #64748B;
        line-height: 1.4;
    }

    /* Danger confirmation box */
    .danger-box {
        background: #FEF2F2;
        border: 1px solid #FCA5A5;
        border-radius: 8px;
        padding: 16px;
        margin-top: 12px;
        margin-bottom: 12px;
        color: #991B1B;
    }

    /* Sidebar tweaks */
    .sidebar-section {
        margin-bottom: 1.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def format_currency(amount: float, currency: str = "INR") -> str:
    """Formats amount with appropriate currency symbols and locale convention."""
    if amount is None:
        amount = 0.0
    c = (currency or "INR").strip().upper()
    if c == "INR":
        return f"₹ {amount:,.2f}"
    elif c == "USD":
        return f"$ {amount:,.2f}"
    elif c == "EUR":
        return f"€ {amount:,.2f}"
    elif c == "GBP":
        return f"£ {amount:,.2f}"
    elif c == "CAD":
        return f"CA$ {amount:,.2f}"
    elif c == "AUD":
        return f"AU$ {amount:,.2f}"
    elif c == "SGD":
        return f"SG$ {amount:,.2f}"
    elif c == "AED":
        return f"AED {amount:,.2f}"
    else:
        return f"{c} {amount:,.2f}"


def generate_synthetic_invoice_pdf(
    vendor: str,
    invoice_number: str,
    date_str: str,
    items: list,
    currency: str = "INR",
    tax_rate: float = 0.18,
) -> bytes:
    """Generates a clean, synthetic PDF invoice for offline testing and demos."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4 size

    # Calculate totals
    subtotal = sum(item["qty"] * item["price"] for item in items)
    tax = round(subtotal * tax_rate, 2)
    total = round(subtotal + tax, 2)

    # Document text layout with explicit synthetic demo indicator
    lines = [
        "SYNTHETIC TEST INVOICE / EXPENSE RECEIPT",
        "*** DEMO DATA FOR TESTING & EVALUATION ONLY ***",
        "=" * 45,
        f"Vendor / Issuer: {vendor}",
        f"GSTIN / Tax ID: 27AABCA{invoice_number[-4:]}F1Z5",
        f"Invoice Number: {invoice_number}",
        f"Date: {date_str}",
        "",
        "Billed To:",
        "  Client Name: Freelance Creative Studio",
        "  Address: Tech Park, Koramangala, Bengaluru, India",
        "",
        "Line Items:",
        "-" * 55,
    ]
    for item in items:
        line_total = item["qty"] * item["price"]
        lines.append(f"• {item['desc']} (x{item['qty']}) - {currency} {line_total:,.2f}")

    lines.extend([
        "-" * 55,
        f"Subtotal: {currency} {subtotal:,.2f}",
        f"Tax (GST {int(tax_rate*100)}%): {currency} {tax:,.2f}",
        f"Grand Total: {currency} {total:,.2f}",
        "=" * 45,
        "",
        "Note: Thank you for your business! This is a synthetic invoice generated for testing.",
    ])

    full_text = "\n".join(lines)
    page.insert_text((45, 60), full_text, fontsize=11, fontname="helv")
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


# ----------------------------------------------------
# Sidebar Navigation & System Health Check
# ----------------------------------------------------
st.sidebar.markdown(
    """
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
        <span style="font-size: 2rem;">🧾</span>
        <div>
            <div style="font-size: 1.25rem; font-weight: 700; color: #0F2042;">InvoiceMate AI</div>
            <div style="font-size: 0.78rem; color: #64748B;">Hacktoberfest Week 2 Edition</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Check Ollama status
ollama_ready, ollama_msg = parser.check_ollama_availability("gemma:2b")
if ollama_ready:
    st.sidebar.success("🟢 Local AI: Gemma 2B Ready")
else:
    st.sidebar.warning(f"🟡 AI Status: {ollama_msg}")

nav = st.sidebar.radio(
    "Navigation",
    [
        "📊 Dashboard",
        "📤 Upload & Parse",
        "📑 All Invoices",
        "🧪 Sample Generator",
        "❓ Help & About",
    ],
    index=0,
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    **Privacy & Local Storage:**
    - 🔒 **100% Local Inference** (`gemma:2b` via Ollama)
    - 🚫 **No cloud APIs** or remote data telemetry
    - 🗄️ **Local SQLite Database** (`invoices.db`)
    - 🛡️ **Zero Unverified Saves** (human-in-the-loop review)
    """
)


# ----------------------------------------------------
# 1. Dashboard View
# ----------------------------------------------------
if nav == "📊 Dashboard":
    st.title("Expense & Invoice Dashboard")
    st.markdown(
        "Monitor your business expenses, track incoming invoices, and analyze spending patterns."
    )

    summary = db.get_dashboard_summary()
    total_spend = summary["total_spend"]
    inv_count = summary["invoice_count"]
    categories = summary["category_breakdown"]
    recent = summary["recent_invoices"]
    demo_count = summary.get("demo_count", 0)
    real_count = summary.get("real_count", 0)

    # Empty Database State: Guided First-Use Experience
    if inv_count == 0:
        st.markdown(
            """
            <div class="welcome-card">
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                    <span style="font-size: 2.2rem;">👋</span>
                    <div>
                        <h3 style="margin: 0; color: #0F2042;">Welcome to InvoiceMate AI!</h3>
                        <p style="margin: 0; color: #64748B; font-size: 0.95rem;">
                            Your database is currently empty. Get started in minutes with our guided workflow.
                        </p>
                    </div>
                </div>
                <div style="background: #EFF6FF; border-left: 4px solid #2563EB; padding: 12px 16px; border-radius: 0 8px 8px 0; font-size: 0.88rem; color: #1E40AF; margin-bottom: 20px;">
                    InvoiceMate runs <strong>100% locally</strong> on your machine. Your invoices, client names, and financial data are never sent to external cloud servers.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.subheader("🚀 Guided 6-Step Workflow")
        w_col1, w_col2, w_col3 = st.columns(3)
        with w_col1:
            st.markdown(
                """
                <div class="step-box">
                    <div class="step-number">1</div>
                    <div class="step-title">Upload Invoice</div>
                    <div class="step-desc">Upload a PDF invoice or receipt image (PNG, JPG).</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(
                """
                <div class="step-box">
                    <div class="step-number">4</div>
                    <div class="step-title">Review & Correct</div>
                    <div class="step-desc">Inspect numbers, tax, currency, and category in the review form.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with w_col2:
            st.markdown(
                """
                <div class="step-box">
                    <div class="step-number">2</div>
                    <div class="step-title">Extract Text</div>
                    <div class="step-desc">PyMuPDF extracts text, with automatic Tesseract OCR for scanned docs.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(
                """
                <div class="step-box">
                    <div class="step-number">5</div>
                    <div class="step-title">Save to SQLite</div>
                    <div class="step-desc">Save verified data directly into your local database.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with w_col3:
            st.markdown(
                """
                <div class="step-box">
                    <div class="step-number">3</div>
                    <div class="step-title">AI Identification</div>
                    <div class="step-desc">Local Gemma 2B identifies vendor, date, total, and tax into JSON.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(
                """
                <div class="step-box">
                    <div class="step-number">6</div>
                    <div class="step-title">Dashboard & Export</div>
                    <div class="step-desc">Track category spending and export clean CSV reports anytime.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)
        btn_col1, btn_col2 = st.columns([1, 1])
        with btn_col1:
            st.info("💡 **Ready to upload an invoice?** Navigate to the **'📤 Upload & Parse'** section from the sidebar.")
        with btn_col2:
            st.info("🧪 **Don't have an invoice handy?** Visit **'🧪 Sample Generator'** to download a realistic synthetic PDF.")

    else:
        # Metrics row
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div>
                        <div class="metric-label" title="Sum of all invoice amounts stored in the database">
                            💰 Total Expenses
                        </div>
                        <div class="metric-value">{format_currency(total_spend, 'INR')}</div>
                    </div>
                    <div class="metric-subtext">Sum of all {inv_count} stored record(s)</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col2:
            demo_badge_str = f" • <span class='badge-demo'>{demo_count} demo</span>" if demo_count > 0 else ""
            st.markdown(
                f"""
                <div class="metric-card">
                    <div>
                        <div class="metric-label" title="Total count of confirmed invoice records currently stored in SQLite">
                            📄 Total Invoices
                        </div>
                        <div class="metric-value">{inv_count}</div>
                    </div>
                    <div class="metric-subtext">{real_count} real{demo_badge_str}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col3:
            top_cat = categories[0]["category"] if categories else "None"
            top_cat_spend = categories[0]["total_amount"] if categories else 0.0
            st.markdown(
                f"""
                <div class="metric-card">
                    <div>
                        <div class="metric-label" title="The expense category with the highest cumulative spending">
                            🏷️ Top Expense Category
                        </div>
                        <div class="metric-value" style="font-size: 1.3rem;">{top_cat}</div>
                    </div>
                    <div class="metric-subtext">{format_currency(top_cat_spend, 'INR')} allocated</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col4:
            avg_inv = (total_spend / inv_count) if inv_count > 0 else 0.0
            st.markdown(
                f"""
                <div class="metric-card">
                    <div>
                        <div class="metric-label" title="Average amount per stored invoice (Total Expenses ÷ Total Invoices)">
                            📊 Average Invoice Amount
                        </div>
                        <div class="metric-value">{format_currency(avg_inv, 'INR')}</div>
                    </div>
                    <div class="metric-subtext">Per stored transaction</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Visualizations & Recent Invoices
        col_chart, col_recent = st.columns([1.2, 1])

        with col_chart:
            st.subheader("Spending by Category")
            if categories:
                df_cat = pd.DataFrame(categories)
                df_cat.columns = ["Category", "Invoices", "Total Spend"]
                st.bar_chart(
                    data=df_cat,
                    x="Category",
                    y="Total Spend",
                    color="#2563EB",
                    width="stretch",
                )
            else:
                st.info("No category data available yet.")

        with col_recent:
            st.subheader("Recent Invoices")
            st.caption("Ordered by latest invoice date (or creation date if date is unlisted).")
            if recent:
                for inv in recent:
                    is_demo_tag = (
                        '<span class="badge-demo">DEMO</span>'
                        if inv.get("is_demo")
                        else '<span class="badge-real">REAL</span>'
                    )
                    with st.container():
                        st.markdown(
                            f"""
                            <div class="invoice-card" style="background-color: #FFFFFF; border: 1px solid #E2E8F0; padding: 12px; border-radius: 8px; margin-bottom: 8px;">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <strong class="invoice-card-vendor" style="color: #172554;">{inv['vendor']}</strong>
                                    <span class="invoice-card-total" style="font-weight: 700; color: #172554;">{format_currency(inv['total'], inv['currency'])}</span>
                                </div>
                                <div class="invoice-card-meta" style="display: flex; justify-content: space-between; align-items: center; font-size: 0.82rem; color: #64748B; margin-top: 4px;">
                                    <span style="color: #64748B;">#{inv['invoice_number'] or 'N/A'} • {inv['invoice_date'] or 'No date'}</span>
                                    <div style="display: flex; gap: 4px; align-items: center;">
                                        {is_demo_tag}
                                        <span class="badge-pill">{inv['category']}</span>
                                    </div>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
            else:
                st.write("No recent invoices recorded.")


# ----------------------------------------------------
# 2. Upload & Parse View
# ----------------------------------------------------
elif nav == "📤 Upload & Parse":
    st.title("Upload & Extract Invoice")
    
    st.markdown(
        """
        <div class="disclaimer-banner">
            ⚠️ <strong>Verification Notice:</strong> AI extracts key fields to save you time. 
            AI values are estimations and have NOT been verified by an accountant or tax professional. 
            Always review and verify extracted values before saving.
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Choose an invoice file (PDF, PNG, JPG, JPEG)",
        type=["pdf", "png", "jpg", "jpeg"],
        help="Maximum file size limit: 10MB.",
    )

    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        file_size_mb = len(file_bytes) / (1024 * 1024)

        if file_size_mb > 10.0:
            st.error("File is too large! Please upload files under 10MB.")
        else:
            st.success(f"Uploaded: **{uploaded_file.name}** ({file_size_mb:.2f} MB)")

            # Document preview and parsing trigger
            preview_col, action_col = st.columns([1, 1])

            with preview_col:
                st.subheader("Document Preview")
                file_ext = os.path.splitext(uploaded_file.name)[1].lower()
                if file_ext in [".png", ".jpg", ".jpeg"]:
                    st.image(file_bytes, caption="Uploaded Image", width="stretch")
                elif file_ext == ".pdf":
                    try:
                        doc = fitz.open(stream=file_bytes, filetype="pdf")
                        if len(doc) > 0:
                            pix = doc[0].get_pixmap(dpi=150)
                            img = Image.open(io.BytesIO(pix.tobytes("png")))
                            st.image(img, caption=f"PDF Page 1 of {len(doc)}", width="stretch")
                        doc.close()
                    except Exception as e:
                        st.warning(f"Could not render PDF preview: {e}")

            with action_col:
                st.subheader("AI Extraction Pipeline")
                st.write("Extract text using PyMuPDF & Tesseract OCR, then parse with local `gemma:2b`.")

                # Mark whether this is synthetic demo data
                is_demo_upload = st.checkbox(
                    "Tag as synthetic demo invoice (allows removing via demo-only cleanup)",
                    value="sample_" in uploaded_file.name.lower() or "demo" in uploaded_file.name.lower(),
                    help="Demo records can be cleared separately without deleting your real invoices.",
                )

                parse_button = st.button("🚀 Process Invoice with Gemma 2B", type="primary")

            if parse_button or "parsed_draft" in st.session_state:
                if parse_button:
                    progress_bar = st.progress(10, text="Step 1/3: Reading document bytes...")
                    # Step 1: Text extraction
                    progress_bar.progress(35, text="Step 2/3: Extracting document text (PyMuPDF & Tesseract OCR)...")
                    raw_text, doc_type, used_ocr = parser.extract_document_text(
                        file_bytes, uploaded_file.name
                    )
                    st.session_state["raw_text"] = raw_text
                    st.session_state["used_ocr"] = used_ocr
                    st.session_state["is_demo_flag"] = is_demo_upload

                    if not raw_text.strip():
                        progress_bar.progress(100, text="Extraction completed.")
                        st.error(
                            "Could not extract readable text from this document. "
                            "If this is a scanned document, please ensure Tesseract OCR is installed on your system (`sudo apt-get install tesseract-ocr`)."
                        )
                    else:
                        # Step 2: LLM parsing
                        progress_bar.progress(70, text="Step 3/3: Running local Gemma 2B inference via Ollama...")
                        draft_data, warn = parser.parse_invoice_with_llm(raw_text)
                        progress_bar.progress(100, text="Extraction pipeline finished!")
                        st.session_state["parsed_draft"] = draft_data
                        st.session_state["parse_warning"] = warn

                if "parsed_draft" in st.session_state:
                    draft = st.session_state["parsed_draft"]
                    warn = st.session_state.get("parse_warning")

                    if warn:
                        st.warning(warn)

                    if st.session_state.get("used_ocr"):
                        st.info("ℹ️ Scanned document or sparse page detected: Tesseract OCR was utilized for optical character recognition.")

                    # Review & Edit Form
                    st.markdown("---")
                    st.subheader("📝 Review & Edit Invoice Before Saving")
                    st.write(
                        "Please verify all numbers, dates, and categories. "
                        "**Human verification is required** before records are committed to SQLite."
                    )

                    with st.form("invoice_review_form"):
                        f_col1, f_col2 = st.columns(2)

                        with f_col1:
                            vendor = st.text_input("Vendor Name (Required)", value=draft.get("vendor", ""))
                            invoice_number = st.text_input("Invoice Number", value=draft.get("invoice_number", ""))
                            invoice_date = st.text_input(
                                "Invoice Date (YYYY-MM-DD)",
                                value=draft.get("invoice_date", str(datetime.date.today())),
                                help="Format: YYYY-MM-DD or standard date format.",
                            )
                            # Category selector
                            cat_index = 0
                            if draft.get("category") in parser.VALID_CATEGORIES:
                                cat_index = parser.VALID_CATEGORIES.index(draft.get("category"))
                            category = st.selectbox(
                                "Expense Category",
                                parser.VALID_CATEGORIES,
                                index=cat_index,
                            )

                        with f_col2:
                            curr_index = 0
                            if draft.get("currency") in parser.DEFAULT_CURRENCIES:
                                curr_index = parser.DEFAULT_CURRENCIES.index(draft.get("currency"))
                            currency = st.selectbox(
                                "Currency",
                                parser.DEFAULT_CURRENCIES,
                                index=curr_index,
                            )
                            subtotal = st.number_input(
                                "Subtotal",
                                value=float(draft.get("subtotal", 0.0)),
                                min_value=0.0,
                                step=10.0,
                                format="%.2f",
                            )
                            tax = st.number_input(
                                "Tax / GST / VAT",
                                value=float(draft.get("tax", 0.0)),
                                min_value=0.0,
                                step=5.0,
                                format="%.2f",
                            )
                            total = st.number_input(
                                "Grand Total (Required, > 0)",
                                value=float(draft.get("total", subtotal + tax)),
                                min_value=0.0,
                                step=10.0,
                                format="%.2f",
                            )

                        notes = st.text_area(
                            "Optional Notes",
                            value="",
                            placeholder="e.g., Project-specific expense, client reimbursement, hardware purchase",
                        )

                        form_demo = st.checkbox(
                            "Save as synthetic demo invoice",
                            value=st.session_state.get("is_demo_flag", False),
                        )

                        # Accidental duplicate check warning
                        duplicate_match = db.check_duplicate_invoice(
                            vendor=vendor,
                            invoice_number=invoice_number,
                            invoice_date=invoice_date,
                            total=total,
                        )
                        if duplicate_match:
                            st.warning(
                                f"⚠️ Potential duplicate detected! Existing Record ID #{duplicate_match['id']} "
                                f"has matching vendor '{duplicate_match['vendor']}' and invoice #{duplicate_match['invoice_number']} "
                                f"({duplicate_match['total']}). Check the box below if you intend to save this anyway."
                            )
                            allow_duplicate = st.checkbox("Confirm: I know this may be a duplicate and want to save it anyway.")
                        else:
                            allow_duplicate = True

                        save_submitted = st.form_submit_button("💾 Save Confirmed Invoice", type="primary")

                        if save_submitted:
                            # Validation checks
                            date_valid = bool(re.match(r"^\d{4}-\d{2}-\d{2}$", invoice_date.strip())) or bool(invoice_date.strip())
                            if not vendor.strip():
                                st.error("Validation Error: Vendor name is required and cannot be empty.")
                            elif total <= 0:
                                st.error("Validation Error: Grand total must be a positive number greater than 0.")
                            elif duplicate_match and not allow_duplicate:
                                st.error("Save blocked: Please confirm duplicate override before saving.")
                            else:
                                new_id = db.insert_invoice(
                                    vendor=vendor,
                                    invoice_number=invoice_number,
                                    invoice_date=invoice_date,
                                    subtotal=subtotal,
                                    tax=tax,
                                    total=total,
                                    currency=currency,
                                    category=category,
                                    raw_text=st.session_state.get("raw_text", ""),
                                    notes=notes,
                                    is_demo=1 if form_demo else 0,
                                )
                                st.success(f"Invoice saved successfully! (Record ID #{new_id})")
                                # Clean session state
                                if "parsed_draft" in st.session_state:
                                    del st.session_state["parsed_draft"]
                                if "raw_text" in st.session_state:
                                    del st.session_state["raw_text"]
                                if "is_demo_flag" in st.session_state:
                                    del st.session_state["is_demo_flag"]
                                st.rerun()

                    # Raw text inspect expander
                    with st.expander("🔍 Inspect Extracted Raw Document Text"):
                        st.text_area(
                            "Document Raw Text",
                            value=st.session_state.get("raw_text", ""),
                            height=200,
                            disabled=True,
                        )


# ----------------------------------------------------
# 3. All Invoices & Reports View
# ----------------------------------------------------
elif nav == "📑 All Invoices":
    st.title("Invoice Directory & Export")
    st.markdown("Search, filter, view full details, manage records, and export CSV reports.")

    counts = db.count_invoices()
    total_stored = counts["total"]

    if total_stored == 0:
        st.info("ℹ️ Your invoice database is currently empty. There are no records to display or export.")
        st.markdown(
            "Upload an invoice via the **'📤 Upload & Parse'** tab or generate a sample PDF using **'🧪 Sample Generator'**."
        )
    else:
        search_col, filter_col, type_col = st.columns([2, 1, 1])

        with search_col:
            search_query = st.text_input("🔍 Search invoices", placeholder="Filter by vendor, invoice #, or notes...")
        with filter_col:
            category_options = ["All"] + parser.VALID_CATEGORIES
            selected_category = st.selectbox("Filter Category", category_options)
        with type_col:
            selected_type = st.selectbox("Data Type", ["All", "Real Only", "Demo Only"])

        invoices = db.get_all_invoices(
            search_query=search_query,
            category_filter=selected_category,
            data_type_filter=selected_type,
        )

        if invoices:
            df = pd.DataFrame(invoices)
            
            # Display summary counts
            st.write(f"Showing **{len(invoices)}** matching invoice(s) (out of {total_stored} total stored).")

            # Table view for quick glance
            display_cols = ["id", "vendor", "invoice_number", "invoice_date", "category", "currency", "subtotal", "tax", "total", "notes", "is_demo"]
            available_cols = [c for c in display_cols if c in df.columns]
            display_df = df[available_cols].copy()
            if "is_demo" in display_df.columns:
                display_df["is_demo"] = display_df["is_demo"].apply(lambda x: "DEMO" if x == 1 else "REAL")
            
            display_df.rename(
                columns={
                    "id": "ID",
                    "vendor": "Vendor",
                    "invoice_number": "Invoice #",
                    "invoice_date": "Date",
                    "category": "Category",
                    "currency": "Currency",
                    "subtotal": "Subtotal",
                    "tax": "Tax",
                    "total": "Total",
                    "notes": "Notes",
                    "is_demo": "Type",
                },
                inplace=True,
            )

            st.dataframe(display_df, width="stretch")

            # CSV Export action
            csv_exp_col1, csv_exp_col2 = st.columns([1, 1])
            with csv_exp_col1:
                # Export currently filtered subset
                filtered_csv_data = display_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label=f"📥 Export Filtered ({len(display_df)} records) as CSV",
                    data=filtered_csv_data,
                    file_name=f"invoices_filtered_{datetime.date.today()}.csv",
                    mime="text/csv",
                    help="Exports only the records currently matching the active search and category filters.",
                )
            with csv_exp_col2:
                # Export all stored records
                all_records = db.get_all_invoices(search_query="", category_filter="All", data_type_filter="All")
                all_df = pd.DataFrame(all_records)
                if "is_demo" in all_df.columns:
                    all_df["Type"] = all_df["is_demo"].apply(lambda x: "DEMO" if x == 1 else "REAL")
                all_csv_data = all_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label=f"📥 Export Complete Database ({total_stored} records) as CSV",
                    data=all_csv_data,
                    file_name=f"invoices_complete_database_{datetime.date.today()}.csv",
                    mime="text/csv",
                    help="Exports every invoice in the SQLite database regardless of active filters.",
                )

            st.markdown("---")

            # Invoice Full Details & Management Tabs
            st.subheader("Manage Records & View Details")
            manage_tab1, manage_tab2, manage_tab3 = st.tabs([
                "🔍 View Full Details & Edit",
                "🗑️ Delete Single Invoice",
                "⚠️ Clear All / Demo Invoices",
            ])

            with manage_tab1:
                selected_id = st.selectbox(
                    "Select Invoice to View Full Details or Edit",
                    [inv["id"] for inv in invoices],
                    format_func=lambda x: f"ID #{x} - {next((i['vendor'] for i in invoices if i['id'] == x), '')} ({next((i['currency'] + ' ' + str(i['total']) for i in invoices if i['id'] == x), '')})",
                    key="view_details_selectbox",
                )

                curr_inv = db.get_invoice_by_id(selected_id)
                if curr_inv:
                    st.markdown("#### Full Invoice Details")
                    d_col1, d_col2 = st.columns(2)
                    with d_col1:
                        st.markdown(f"**Record ID:** `{curr_inv['id']}`")
                        st.markdown(f"**Vendor Name:** {curr_inv['vendor']}")
                        st.markdown(f"**Invoice Number:** {curr_inv['invoice_number'] or 'N/A'}")
                        st.markdown(f"**Invoice Date:** {curr_inv['invoice_date'] or 'N/A'}")
                        st.markdown(f"**Category:** {curr_inv['category']}")
                    with d_col2:
                        st.markdown(f"**Currency:** {curr_inv['currency']}")
                        st.markdown(f"**Subtotal:** {format_currency(curr_inv['subtotal'], curr_inv['currency'])}")
                        st.markdown(f"**Tax:** {format_currency(curr_inv['tax'], curr_inv['currency'])}")
                        st.markdown(f"**Total Amount:** **{format_currency(curr_inv['total'], curr_inv['currency'])}**")
                        tag_str = "🟡 Synthetic Demo Invoice" if curr_inv.get("is_demo") == 1 else "🟢 Real Business Invoice"
                        st.markdown(f"**Record Type:** {tag_str}")
                    
                    if curr_inv.get("notes"):
                        st.info(f"**Notes:** {curr_inv['notes']}")

                    with st.expander(f"✏️ Edit Record #{selected_id} ({curr_inv['vendor']})"):
                        with st.form(f"edit_form_{selected_id}"):
                            e_col1, e_col2 = st.columns(2)
                            with e_col1:
                                e_vendor = st.text_input("Vendor", value=curr_inv["vendor"])
                                e_inv_num = st.text_input("Invoice #", value=curr_inv["invoice_number"])
                                e_date = st.text_input("Date", value=curr_inv["invoice_date"])
                                e_cat_idx = parser.VALID_CATEGORIES.index(curr_inv["category"]) if curr_inv["category"] in parser.VALID_CATEGORIES else 0
                                e_cat = st.selectbox("Category", parser.VALID_CATEGORIES, index=e_cat_idx)
                            with e_col2:
                                e_curr_idx = parser.DEFAULT_CURRENCIES.index(curr_inv["currency"]) if curr_inv["currency"] in parser.DEFAULT_CURRENCIES else 0
                                e_curr = st.selectbox("Currency", parser.DEFAULT_CURRENCIES, index=e_curr_idx)
                                e_subtotal = st.number_input("Subtotal", value=float(curr_inv["subtotal"]), format="%.2f")
                                e_tax = st.number_input("Tax", value=float(curr_inv["tax"]), format="%.2f")
                                e_total = st.number_input("Total", value=float(curr_inv["total"]), format="%.2f")
                            
                            e_notes = st.text_area("Notes", value=curr_inv["notes"] or "")
                            e_is_demo = st.checkbox("Is Synthetic Demo Invoice", value=bool(curr_inv.get("is_demo", 0)))

                            update_submit = st.form_submit_button("💾 Update Invoice", type="primary")

                            if update_submit:
                                if not e_vendor.strip():
                                    st.error("Vendor name cannot be empty.")
                                elif e_total <= 0:
                                    st.error("Total amount must be greater than 0.")
                                else:
                                    db.update_invoice(
                                        invoice_id=selected_id,
                                        vendor=e_vendor,
                                        invoice_number=e_inv_num,
                                        invoice_date=e_date,
                                        subtotal=e_subtotal,
                                        tax=e_tax,
                                        total=e_total,
                                        currency=e_curr,
                                        category=e_cat,
                                        notes=e_notes,
                                        is_demo=1 if e_is_demo else 0,
                                    )
                                    st.success(f"Invoice #{selected_id} updated successfully!")
                                    st.rerun()

            with manage_tab2:
                del_target_id = st.selectbox(
                    "Select Invoice to Delete",
                    [inv["id"] for inv in invoices],
                    format_func=lambda x: f"ID #{x} - {next((i['vendor'] for i in invoices if i['id'] == x), '')} ({next((i['currency'] + ' ' + str(i['total']) for i in invoices if i['id'] == x), '')})",
                    key="delete_single_selectbox",
                )
                del_item = db.get_invoice_by_id(del_target_id)
                if del_item:
                    st.markdown(
                        f"""
                        <div class="danger-box">
                            <strong>⚠️ Confirm Deletion for Record #{del_item['id']}</strong><br>
                            Vendor: <strong>{del_item['vendor']}</strong> | Invoice #: <strong>{del_item['invoice_number'] or 'N/A'}</strong> | Total: <strong>{format_currency(del_item['total'], del_item['currency'])}</strong><br>
                            This record will be permanently deleted from the SQLite database. This action cannot be undone.
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    confirm_single_del = st.checkbox(
                        f"Yes, permanently delete Record #{del_item['id']} ({del_item['vendor']})",
                        key=f"confirm_del_{del_item['id']}",
                    )
                    if st.button("🗑️ Delete Selected Invoice", type="primary", disabled=not confirm_single_del):
                        deleted = db.delete_invoice(del_target_id)
                        if deleted:
                            st.success(f"Record #{del_target_id} was permanently deleted.")
                            st.rerun()
                        else:
                            st.error("Record could not be deleted or was already removed.")

            with manage_tab3:
                st.markdown("#### Database Bulk Deletion Options")
                st.markdown(
                    "Manage your stored data safely. You can clean up synthetic demo test data without affecting your real business invoices, or clear all records."
                )

                demo_in_db = counts["demo"]
                st.markdown("---")
                st.markdown(f"##### Option A: Remove Synthetic Demo Invoices (`{demo_in_db}` records)")
                st.write(
                    "Deletes only records tagged as demo data (`is_demo = 1`). Real uploaded invoices will **never** be deleted by this action."
                )
                if demo_in_db == 0:
                    st.info("No synthetic demo invoices found in database.")
                else:
                    confirm_demo_del = st.checkbox("Confirm: Delete all synthetic demo invoices only.", key="confirm_demo_del")
                    if st.button("🧹 Clear Demo Invoices Only", disabled=not confirm_demo_del):
                        c = db.clear_demo_invoices()
                        st.success(f"Removed {c} synthetic demo invoice record(s). Real invoices were preserved.")
                        st.rerun()

                st.markdown("---")
                st.markdown("##### Option B: Clear All Invoices (Full Reset)")
                st.markdown(
                    """
                    <div class="danger-box">
                        <strong>⚠️ Danger Zone: Clear All Records</strong><br>
                        This will permanently delete <strong>ALL invoice records</strong> from the database table. 
                        <strong>This action cannot be undone!</strong> The SQLite database file itself will be preserved and vacuumed, but all stored invoices will be deleted.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                confirm_all_del = st.checkbox(
                    f"I understand that deleting all {total_stored} records is permanent and cannot be undone.",
                    key="confirm_all_del",
                )
                type_confirm = st.text_input("Type 'DELETE ALL' to confirm destructive action:", key="type_confirm_clear_all")

                if st.button("💥 Permanently Clear All Records", type="primary", disabled=not (confirm_all_del and type_confirm.strip() == "DELETE ALL")):
                    c = db.clear_all_invoices()
                    st.success(f"Cleared {c} record(s). Database is now completely reset and vacuumed.")
                    st.rerun()

        else:
            st.info("No matching invoices found for the current search/filter criteria.")
            # Still provide CSV export option for all records if any exist in the database
            all_records = db.get_all_invoices(search_query="", category_filter="All", data_type_filter="All")
            all_df = pd.DataFrame(all_records)
            if not all_df.empty:
                all_csv_data = all_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label=f"📥 Export Complete Database ({len(all_df)} records) as CSV",
                    data=all_csv_data,
                    file_name=f"invoices_complete_database_{datetime.date.today()}.csv",
                    mime="text/csv",
                )


# ----------------------------------------------------
# 4. Sample Invoice Generator View
# ----------------------------------------------------
elif nav == "🧪 Sample Generator":
    st.title("Synthetic Sample Invoice Generator")
    st.markdown(
        "Generate and download realistic synthetic PDF invoices to test OCR and AI extraction without exposing confidential client data."
    )

    templates = {
        "Cloud Hosting (Digital Ocean / AWS)": {
            "vendor": "Apex Cloud Technologies Pvt Ltd",
            "invoice_num": "ACT-2026-4401",
            "category": "Cloud & Hosting",
            "items": [
                {"desc": "High CPU VPS Instance (2 vCPU, 4GB RAM)", "qty": 1, "price": 1800.0},
                {"desc": "NVMe Block Storage (250 GB)", "qty": 1, "price": 1200.0},
                {"desc": "Automated Daily Snapshots", "qty": 1, "price": 500.0},
            ],
            "currency": "INR",
            "tax_rate": 0.18,
        },
        "Software Subscription (Design Tool)": {
            "vendor": "DesignFlow Labs Inc.",
            "invoice_num": "DF-998231",
            "category": "Software & SaaS",
            "items": [
                {"desc": "DesignFlow Pro Annual Subscription", "qty": 1, "price": 149.00},
                {"desc": "Team Cloud Storage Addon", "qty": 1, "price": 29.00},
            ],
            "currency": "USD",
            "tax_rate": 0.08,
        },
        "Office Stationery & Gear": {
            "vendor": "Kalam & Kagaz Enterprise",
            "invoice_num": "KK-BLR-1092",
            "category": "Office Supplies",
            "items": [
                {"desc": "Ergonomic Mesh Desk Chair", "qty": 1, "price": 6500.0},
                {"desc": "Notebooks & Gel Pen Pack", "qty": 4, "price": 250.0},
            ],
            "currency": "INR",
            "tax_rate": 0.12,
        },
    }

    choice = st.selectbox("Choose a sample scenario", list(templates.keys()))
    sample_config = templates[choice]

    col_details, col_gen = st.columns([1.2, 1])

    with col_details:
        st.subheader("Invoice Metadata Preview")
        st.write(f"**Vendor:** {sample_config['vendor']}")
        st.write(f"**Invoice Number:** {sample_config['invoice_num']}")
        st.write(f"**Suggested Category:** {sample_config['category']}")
        st.write(f"**Currency:** {sample_config['currency']}")

        st.write("**Line Items:**")
        sample_df = pd.DataFrame(sample_config["items"])
        st.table(sample_df)

    with col_gen:
        st.subheader("Generate PDF")
        st.write("Click below to build the PDF document and download it for testing:")

        today_str = datetime.date.today().strftime("%Y-%m-%d")
        pdf_bytes = generate_synthetic_invoice_pdf(
            vendor=sample_config["vendor"],
            invoice_number=sample_config["invoice_num"],
            date_str=today_str,
            items=sample_config["items"],
            currency=sample_config["currency"],
            tax_rate=sample_config["tax_rate"],
        )

        st.download_button(
            label=f"📥 Download {sample_config['invoice_num']}.pdf",
            data=pdf_bytes,
            file_name=f"sample_{sample_config['invoice_num']}.pdf",
            mime="application/pdf",
            type="primary",
        )

        st.markdown("<br>", unsafe_allow_html=True)
        st.info("💡 Once downloaded, switch to the **'Upload & Parse'** tab and upload this PDF to test the complete extraction workflow!")


# ----------------------------------------------------
# 5. Help & About View (Beginner Friendly)
# ----------------------------------------------------
elif nav == "❓ Help & About":
    st.title("Help & Beginner's Guide")
    st.markdown(
        "Welcome to **InvoiceMate AI**! This section explains the key metrics, how the application works, and common terms in plain, simple English."
    )

    st.subheader("📖 Dashboard Metrics Explained")
    m_exp1, m_exp2 = st.columns(2)
    with m_exp1:
        st.markdown(
            """
            - **Total Expenses:** The cumulative sum of all invoice amounts stored in your local database. It gives an immediate overview of total business outlays.
            - **Total Invoices:** The total count of confirmed invoice records currently stored in your database.
            - **Average Invoice Amount:** The average monetary amount per stored invoice. It is calculated by dividing **Total Expenses** by **Total Invoices**.
            """
        )
    with m_exp2:
        st.markdown(
            """
            - **Top Expense Category:** The business category (e.g., *Cloud & Hosting*, *Office Supplies*, *Software & SaaS*) with the highest total financial allocation.
            - **Recent Invoices:** The latest invoice records based primarily on the printed **Invoice Date** (or creation timestamp if no invoice date was provided).
            """
        )

    st.markdown("---")
    st.subheader("⚙️ How Streamlit & Local AI Work")

    st.markdown(
        """
        - 🔄 **What is 'Auto Rerun'?**  
          Streamlit is designed as an interactive reactive framework. Whenever you interact with a button, checkbox, slider, or text field, Streamlit automatically reruns the Python script to update the screen.  
          **This is completely normal!** It does *not* mean your invoice is being uploaded or re-processed by the AI every time you click a widget. Processing only happens when you explicitly click the action buttons.

        - 🤖 **What is 'Local AI'?**  
          Instead of sending your financial documents to expensive, privacy-invasive cloud APIs, InvoiceMate runs Google's compact **Gemma 2B** language model through **Ollama** directly on your own machine.
          - Your invoices stay on your computer.
          - No data transfer fees or API token limits.
          - If Ollama is not installed or running, InvoiceMate will automatically use intelligent regex pattern-matching heuristics so you can still work uninterrupted.
        
        - 🛡️ **Why 'Human-in-the-Loop' Review?**  
          AI models are helpful assistants, but they can occasionally misread small print or handwritten receipts. InvoiceMate *never* writes data directly to your records without your confirmation. You always inspect and confirm the numbers first.
        """
    )

    st.markdown("---")
    st.subheader("🔒 Privacy, Storage & Security")
    st.markdown(
        """
        1. **Local SQLite Database:** All records are saved in `invoices.db` located in the application directory.
        2. **Safe SQL Operations:** All database queries utilize parameterized queries (`?`) to guarantee safety against SQL injection.
        3. **Git Hygiene:** Your local database file (`invoices.db`), any `.env` secrets, uploaded files, and Python virtual environments are ignored in `.gitignore`.
        4. **Synthetic Test Data:** The built-in generator produces synthetic mock invoices clearly marked as test documents so you can demo the tool safely.
        """
    )
