"""
Database operations for InvoiceMate AI.
Handles SQLite connection, schema migrations, parameterized CRUD operations,
and analytics queries.
"""

import sqlite3
import os
from typing import List, Dict, Any, Optional

DB_NAME = "invoices.db"


def get_connection(db_path: str = DB_NAME) -> sqlite3.Connection:
    """Returns a SQLite connection with row factory configured."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DB_NAME) -> None:
    """Initializes the database schema if tables do not exist."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vendor TEXT NOT NULL,
                invoice_number TEXT,
                invoice_date TEXT,
                subtotal REAL DEFAULT 0.0,
                tax REAL DEFAULT 0.0,
                total REAL NOT NULL,
                currency TEXT DEFAULT 'INR',
                category TEXT DEFAULT 'Other',
                raw_text TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


def insert_invoice(
    vendor: str,
    invoice_number: str,
    invoice_date: str,
    subtotal: float,
    tax: float,
    total: float,
    currency: str = "INR",
    category: str = "Other",
    raw_text: str = "",
    notes: str = "",
    db_path: str = DB_NAME,
) -> int:
    """
    Inserts a user-reviewed and confirmed invoice record.
    Uses parameterized query to prevent SQL injection.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO invoices (
                vendor, invoice_number, invoice_date, subtotal, tax, total,
                currency, category, raw_text, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                vendor.strip() if vendor else "Unknown Vendor",
                invoice_number.strip() if invoice_number else "",
                invoice_date.strip() if invoice_date else "",
                float(subtotal or 0.0),
                float(tax or 0.0),
                float(total or 0.0),
                currency.strip().upper() if currency else "INR",
                category.strip() if category else "Other",
                raw_text or "",
                notes or "",
            ),
        )
        conn.commit()
        return cursor.lastrowid


def get_all_invoices(
    search_query: str = "",
    category_filter: str = "All",
    db_path: str = DB_NAME,
) -> List[Dict[str, Any]]:
    """
    Fetches invoices matching search terms and optional category filter.
    Search spans vendor and invoice_number safely via parameterized queries.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM invoices WHERE 1=1"
        params: List[Any] = []

        if category_filter and category_filter != "All":
            query += " AND category = ?"
            params.append(category_filter)

        if search_query:
            query += " AND (vendor LIKE ? OR invoice_number LIKE ? OR notes LIKE ?)"
            term = f"%{search_query.strip()}%"
            params.extend([term, term, term])

        query += " ORDER BY id DESC"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_invoice_by_id(invoice_id: int, db_path: str = DB_NAME) -> Optional[Dict[str, Any]]:
    """Fetches a single invoice by its primary key ID."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def update_invoice(
    invoice_id: int,
    vendor: str,
    invoice_number: str,
    invoice_date: str,
    subtotal: float,
    tax: float,
    total: float,
    currency: str,
    category: str,
    notes: str,
    db_path: str = DB_NAME,
) -> bool:
    """Updates an existing invoice with parameterized values."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE invoices
            SET vendor = ?, invoice_number = ?, invoice_date = ?,
                subtotal = ?, tax = ?, total = ?, currency = ?,
                category = ?, notes = ?
            WHERE id = ?
            """,
            (
                vendor.strip(),
                invoice_number.strip(),
                invoice_date.strip(),
                float(subtotal or 0.0),
                float(tax or 0.0),
                float(total or 0.0),
                currency.strip().upper(),
                category.strip(),
                notes or "",
                invoice_id,
            ),
        )
        conn.commit()
        return cursor.rowcount > 0


def delete_invoice(invoice_id: int, db_path: str = DB_NAME) -> bool:
    """Deletes an invoice by its ID."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
        conn.commit()
        return cursor.rowcount > 0


def get_dashboard_summary(db_path: str = DB_NAME) -> Dict[str, Any]:
    """
    Computes summary metrics: total spend, total invoice count,
    spending by category, and monthly spending.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()

        # Overall counts and sums
        cursor.execute("SELECT COUNT(*), COALESCE(SUM(total), 0.0) FROM invoices")
        count, total_sum = cursor.fetchone()

        # Breakdown by category
        cursor.execute("""
            SELECT category, COUNT(*) as count, COALESCE(SUM(total), 0.0) as total_amount
            FROM invoices
            GROUP BY category
            ORDER BY total_amount DESC
        """)
        category_rows = cursor.fetchall()
        category_breakdown = [dict(row) for row in category_rows]

        # Recent 5 invoices
        cursor.execute("""
            SELECT id, vendor, invoice_number, invoice_date, total, currency, category
            FROM invoices
            ORDER BY id DESC
            LIMIT 5
        """)
        recent_invoices = [dict(row) for row in cursor.fetchall()]

        return {
            "invoice_count": count,
            "total_spend": total_sum,
            "category_breakdown": category_breakdown,
            "recent_invoices": recent_invoices,
        }
