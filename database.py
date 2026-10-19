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
    """Initializes the database schema if tables do not exist and applies migrations."""
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
        # Safe migration: add is_demo column if not present
        cursor.execute("PRAGMA table_info(invoices)")
        columns = [col[1] for col in cursor.fetchall()]
        if "is_demo" not in columns:
            cursor.execute("ALTER TABLE invoices ADD COLUMN is_demo INTEGER DEFAULT 0")
        conn.commit()


def check_duplicate_invoice(
    vendor: str,
    invoice_number: str,
    invoice_date: str,
    total: float,
    db_path: str = DB_NAME,
) -> Optional[Dict[str, Any]]:
    """
    Checks if a potential duplicate invoice already exists in the database.
    Matches either identical vendor + invoice_number (if invoice_number is non-empty)
    OR vendor + invoice_date + total.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        v_clean = vendor.strip()
        num_clean = invoice_number.strip()
        date_clean = invoice_date.strip()

        if num_clean:
            cursor.execute(
                """
                SELECT id, vendor, invoice_number, invoice_date, total, is_demo
                FROM invoices
                WHERE LOWER(vendor) = LOWER(?) AND LOWER(invoice_number) = LOWER(?)
                LIMIT 1
                """,
                (v_clean, num_clean),
            )
            row = cursor.fetchone()
            if row:
                return dict(row)

        if date_clean and total > 0:
            cursor.execute(
                """
                SELECT id, vendor, invoice_number, invoice_date, total, is_demo
                FROM invoices
                WHERE LOWER(vendor) = LOWER(?) AND invoice_date = ? AND ABS(total - ?) < 0.01
                LIMIT 1
                """,
                (v_clean, date_clean, float(total)),
            )
            row = cursor.fetchone()
            if row:
                return dict(row)

        return None


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
    is_demo: int = 0,
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
                currency, category, raw_text, notes, is_demo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                1 if is_demo else 0,
            ),
        )
        conn.commit()
        return cursor.lastrowid


def get_all_invoices(
    search_query: str = "",
    category_filter: str = "All",
    data_type_filter: str = "All",
    db_path: str = DB_NAME,
) -> List[Dict[str, Any]]:
    """
    Fetches invoices matching search terms and optional filters.
    data_type_filter can be 'All', 'Real Only', or 'Demo Only'.
    Search spans vendor and invoice_number safely via parameterized queries.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM invoices WHERE 1=1"
        params: List[Any] = []

        if category_filter and category_filter != "All":
            query += " AND category = ?"
            params.append(category_filter)

        if data_type_filter == "Real Only":
            query += " AND (is_demo = 0 OR is_demo IS NULL)"
        elif data_type_filter == "Demo Only":
            query += " AND is_demo = 1"

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
    is_demo: Optional[int] = None,
    db_path: str = DB_NAME,
) -> bool:
    """Updates an existing invoice with parameterized values."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        if is_demo is not None:
            cursor.execute(
                """
                UPDATE invoices
                SET vendor = ?, invoice_number = ?, invoice_date = ?,
                    subtotal = ?, tax = ?, total = ?, currency = ?,
                    category = ?, notes = ?, is_demo = ?
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
                    1 if is_demo else 0,
                    invoice_id,
                ),
            )
        else:
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


def clear_all_invoices(db_path: str = DB_NAME) -> int:
    """
    Deletes ALL invoice records from the database table.
    Does not delete the database file itself or unrelated tables.
    Returns the number of deleted records.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM invoices")
        deleted_count = cursor.rowcount
        conn.commit()
        # Vacuum to release disk space cleanly
        cursor.execute("VACUUM")
        return deleted_count


def clear_demo_invoices(db_path: str = DB_NAME) -> int:
    """
    Deletes only synthetic demo invoice records (where is_demo = 1).
    Guarantees that real, user-uploaded invoices are never touched.
    Returns the number of deleted records.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM invoices WHERE is_demo = 1")
        deleted_count = cursor.rowcount
        conn.commit()
        return deleted_count


def count_invoices(db_path: str = DB_NAME) -> Dict[str, int]:
    """Returns total, real, and demo invoice counts."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM invoices")
        total_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM invoices WHERE is_demo = 1")
        demo_count = cursor.fetchone()[0]

        real_count = total_count - demo_count
        return {
            "total": total_count,
            "demo": demo_count,
            "real": real_count,
        }


def get_dashboard_summary(db_path: str = DB_NAME) -> Dict[str, Any]:
    """
    Computes summary metrics: total spend, total invoice count,
    spending by category, and recent invoices.
    Recent invoices are ordered by invoice_date DESC, id DESC to prioritize latest business date.
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

        # Recent 5 invoices ordered by invoice_date (latest first), then ID desc
        cursor.execute("""
            SELECT id, vendor, invoice_number, invoice_date, total, currency, category, is_demo, created_at
            FROM invoices
            ORDER BY invoice_date DESC, id DESC
            LIMIT 5
        """)
        recent_invoices = [dict(row) for row in cursor.fetchall()]

        cursor.execute("SELECT COUNT(*) FROM invoices WHERE is_demo = 1")
        demo_count = cursor.fetchone()[0]

        return {
            "invoice_count": count,
            "total_spend": total_sum,
            "category_breakdown": category_breakdown,
            "recent_invoices": recent_invoices,
            "demo_count": demo_count,
            "real_count": count - demo_count,
        }
