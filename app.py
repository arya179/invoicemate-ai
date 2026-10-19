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
    }
    .metric-value {
        font-size: 1.85rem;
        font-weight: 700;
        color: #0F2042;
    }
    .metric-subtext {
        font-size: 0.8rem;
        color: #10B981;
        margin-top: 4px;
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

    /* Status badge */
    .badge-pill {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 600;
        background-color: #E2E8F0;
        color: #334155;
    }

    /* Invoice Cards */
    .invoice-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 8px;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
    }
    .invoice-card-vendor {
        font-weight: 700;
        color: #172554 !important;
    }
    .invoice-card-total {
        font-weight: 700;
        color: #172554 !important;
    }
    .invoice-card-meta {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.82rem;
        color: #64748B !important;
        margin-top: 4px;
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
    if currency == "INR":
        # Indian numbering format (Lakhs / Crores)
        s = f"{amount:,.2f}"
        return f"₹ {s}"
    elif currency == "USD":
        return f"$ {amount:,.2f}"
    elif currency == "EUR":
        return f"€ {amount:,.2f}"
    elif currency == "GBP":
        return f"£ {amount:,.2f}"
    else:
        return f"{currency} {amount:,.2f}"


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

    # Document text layout
    lines = [
        "TAX INVOICE / EXPENSE RECEIPT",
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
    ["📊 Dashboard", "📤 Upload & Parse", "📑 All Invoices", "🧪 Sample Generator"],
    index=0,
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    **Privacy & Security First:**
    - 🔒 100% Local Inference (`gemma:2b`)
    - 🚫 No cloud APIs or external data transfers
    - 🛡️ Parameterized SQLite storage
    - 👁️ User-reviewed data validation
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

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Total Expenses</div>
                <div class="metric-value">{format_currency(total_spend, 'INR')}</div>
                <div class="metric-subtext">Across all records</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Total Invoices</div>
                <div class="metric-value">{inv_count}</div>
                <div class="metric-subtext">Processed & confirmed</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        top_cat = categories[0]["category"] if categories else "None"
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Top Expense Category</div>
                <div class="metric-value" style="font-size: 1.3rem;">{top_cat}</div>
                <div class="metric-subtext">Largest allocation</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col4:
        avg_inv = (total_spend / inv_count) if inv_count > 0 else 0.0
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Avg. Invoice Size</div>
                <div class="metric-value">{format_currency(avg_inv, 'INR')}</div>
                <div class="metric-subtext">Per transaction</div>
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
            st.info("No invoice data available yet. Upload your first invoice to see category insights!")

    with col_recent:
        st.subheader("Recent Invoices")
        if recent:
            for inv in recent:
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
                                <span class="badge-pill">{inv['category']}</span>
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

                parse_button = st.button("🚀 Process Invoice with Gemma 2B", type="primary")

            if parse_button or "parsed_draft" in st.session_state:
                if parse_button:
                    with st.spinner("Extracting text and running local AI inference..."):
                        # Step 1: Text extraction
                        raw_text, doc_type, used_ocr = parser.extract_document_text(
                            file_bytes, uploaded_file.name
                        )
                        st.session_state["raw_text"] = raw_text
                        st.session_state["used_ocr"] = used_ocr

                        if not raw_text.strip():
                            st.error("Could not extract any readable text from this document. Please verify the image/PDF is legible.")
                        else:
                            # Step 2: LLM parsing
                            draft_data, warn = parser.parse_invoice_with_llm(raw_text)
                            st.session_state["parsed_draft"] = draft_data
                            st.session_state["parse_warning"] = warn

                if "parsed_draft" in st.session_state:
                    draft = st.session_state["parsed_draft"]
                    warn = st.session_state.get("parse_warning")

                    if warn:
                        st.warning(warn)

                    if st.session_state.get("used_ocr"):
                        st.info("ℹ️ Scanned document detected: Tesseract OCR was utilized for text extraction.")

                    # Review & Edit Form
                    st.markdown("---")
                    st.subheader("📝 Review & Edit Invoice Before Saving")
                    st.write("Confirm all numbers and categories. Only confirmed data is saved to SQLite.")

                    with st.form("invoice_review_form"):
                        f_col1, f_col2 = st.columns(2)

                        with f_col1:
                            vendor = st.text_input("Vendor Name", value=draft.get("vendor", ""))
                            invoice_number = st.text_input("Invoice Number", value=draft.get("invoice_number", ""))
                            invoice_date = st.text_input(
                                "Invoice Date (YYYY-MM-DD)",
                                value=draft.get("invoice_date", str(datetime.date.today())),
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
                                "Grand Total (Required)",
                                value=float(draft.get("total", subtotal + tax)),
                                min_value=0.0,
                                step=10.0,
                                format="%.2f",
                            )

                        notes = st.text_area("Optional Notes", value="", placeholder="e.g. Project-specific expense, client reimbursement")

                        save_submitted = st.form_submit_button("💾 Save Confirmed Invoice", type="primary")

                        if save_submitted:
                            if not vendor.strip():
                                st.error("Vendor name cannot be empty.")
                            elif total <= 0:
                                st.error("Total amount must be greater than 0.")
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
                                )
                                st.success(f"Invoice saved successfully! (Record ID #{new_id})")
                                # Clean session state
                                del st.session_state["parsed_draft"]
                                if "raw_text" in st.session_state:
                                    del st.session_state["raw_text"]
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
    st.markdown("Search, filter, view details, and export your expense records.")

    search_col, filter_col = st.columns([2, 1])

    with search_col:
        search_query = st.text_input("🔍 Search invoices", placeholder="Filter by vendor, invoice #, or notes...")
    with filter_col:
        category_options = ["All"] + parser.VALID_CATEGORIES
        selected_category = st.selectbox("Filter Category", category_options)

    invoices = db.get_all_invoices(search_query=search_query, category_filter=selected_category)

    if invoices:
        df = pd.DataFrame(invoices)
        
        # Display summary counts
        st.write(f"Showing **{len(invoices)}** matching invoice(s).")

        # Table view for quick glance
        display_df = df[
            ["id", "vendor", "invoice_number", "invoice_date", "category", "currency", "subtotal", "tax", "total", "notes"]
        ].copy()
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
            },
            inplace=True,
        )

        st.dataframe(display_df, width="stretch")

        # CSV Export action
        csv_data = display_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Export Report as CSV",
            data=csv_data,
            file_name=f"invoices_report_{datetime.date.today()}.csv",
            mime="text/csv",
        )

        st.markdown("---")
        st.subheader("Manage Records")

        # Edit and delete accordion
        selected_id = st.selectbox(
            "Select Invoice ID to Edit or Delete",
            [inv["id"] for inv in invoices],
            format_func=lambda x: f"ID #{x} - {next((i['vendor'] for i in invoices if i['id'] == x), '')} ({next((i['currency'] + ' ' + str(i['total']) for i in invoices if i['id'] == x), '')})",
        )

        curr_inv = next((i for i in invoices if i["id"] == selected_id), None)
        if curr_inv:
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

                    col_save_btn, col_del_btn = st.columns([1, 1])
                    with col_save_btn:
                        update_submit = st.form_submit_button("Update Invoice", type="primary")
                    with col_del_btn:
                        delete_submit = st.form_submit_button("Delete Invoice")

                    if update_submit:
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
                        )
                        st.success("Invoice updated successfully!")
                        st.rerun()

                    if delete_submit:
                        db.delete_invoice(selected_id)
                        st.warning(f"Invoice #{selected_id} deleted.")
                        st.rerun()

    else:
        st.info("No matching invoices found in your database. Upload invoices or adjust your search filter.")


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
