"""
StationerySort — SQLite Database Layer
Handles database schema creation, initial sample data seeding, and CRUD operations.
"""

import sqlite3
import os
from typing import List, Dict, Any, Optional

DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "stationery.db")

SAMPLE_ITEMS = [
    {
        "name": "Blue Gel Pens (0.5mm)",
        "category": "Writing",
        "quantity": 2,
        "min_stock_level": 5,
        "unit": "pcs",
        "location": "Pencil Case",
        "notes": "Quick-drying blue ink for daily lecture notes"
    },
    {
        "name": "Pastel Sticky Notes (3x3 in)",
        "category": "Paper & Notes",
        "quantity": 1,
        "min_stock_level": 3,
        "unit": "pads",
        "location": "Desk Top",
        "notes": "Used for textbook annotations and quick reminders"
    },
    {
        "name": "A5 Spiral Grid Notebooks",
        "category": "Paper & Notes",
        "quantity": 4,
        "min_stock_level": 2,
        "unit": "pcs",
        "location": "Bookshelf",
        "notes": "100gsm paper for math and physics diagrams"
    },
    {
        "name": "Pastel Highlighters (6-Color Set)",
        "category": "Writing",
        "quantity": 1,
        "min_stock_level": 2,
        "unit": "pack",
        "location": "Desk Organizer",
        "notes": "Mildliner style soft colors"
    },
    {
        "name": "Wooden HB Graphite Pencils",
        "category": "Writing",
        "quantity": 12,
        "min_stock_level": 4,
        "unit": "pcs",
        "location": "Desk Drawer",
        "notes": "Pre-sharpened with latex-free erasers"
    },
    {
        "name": "Dust-Free Soft Vinyl Erasers",
        "category": "Correction & Tools",
        "quantity": 3,
        "min_stock_level": 2,
        "unit": "pcs",
        "location": "Pencil Case",
        "notes": "Non-abrasive, leaves minimal residue"
    },
    {
        "name": "Correction Tape Dispensers (5mm x 6m)",
        "category": "Correction & Tools",
        "quantity": 1,
        "min_stock_level": 2,
        "unit": "pcs",
        "location": "Pencil Case",
        "notes": "Tear-resistant white tape for pen corrections"
    },
    {
        "name": "Medium Binder Clips (19mm / 3/4-in)",
        "category": "Fasteners & Clips",
        "quantity": 24,
        "min_stock_level": 10,
        "unit": "pcs",
        "location": "Clip Dish",
        "notes": "Holds up to 50 sheets of homework papers"
    },
    {
        "name": "Transparent Index Tabs (120 Tabs)",
        "category": "Paper & Notes",
        "quantity": 5,
        "min_stock_level": 2,
        "unit": "packs",
        "location": "Backpack",
        "notes": "Repositionable PET index page flags"
    },
    {
        "name": "Standard Staples (No. 10 Box)",
        "category": "Fasteners & Clips",
        "quantity": 1,
        "min_stock_level": 2,
        "unit": "box",
        "location": "Desk Drawer",
        "notes": "1,000 staples per box"
    },
    {
        "name": "Washable Glue Stick (21g)",
        "category": "Adhesives",
        "quantity": 3,
        "min_stock_level": 1,
        "unit": "pcs",
        "location": "Desk Organizer",
        "notes": "Goes on purple, dries clear"
    },
    {
        "name": "Stainless Steel Ruler (15cm / 6-in)",
        "category": "Correction & Tools",
        "quantity": 1,
        "min_stock_level": 1,
        "unit": "pcs",
        "location": "Backpack",
        "notes": "Etched metric and imperial graduations"
    }
]

def get_db_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Return a connection with Row factory enabled for dictionary-like access."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: str = DEFAULT_DB_PATH) -> None:
    """Initialize database tables and indexes."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stationery_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 0,
            min_stock_level INTEGER NOT NULL DEFAULT 1,
            unit TEXT DEFAULT 'pcs',
            location TEXT DEFAULT 'Desk',
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_items_category ON stationery_items (category)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_items_name ON stationery_items (name)
    """)
    conn.commit()

    # Seed sample items if table is empty
    cursor.execute("SELECT COUNT(*) AS count FROM stationery_items")
    row = cursor.fetchone()
    if row["count"] == 0:
        seed_sample_data(db_path, force=True)
    conn.close()

def seed_sample_data(db_path: str = DEFAULT_DB_PATH, force: bool = False) -> int:
    """Populate sample stationery inventory items."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    if force:
        cursor.execute("DELETE FROM stationery_items")
    
    for item in SAMPLE_ITEMS:
        cursor.execute("""
            INSERT INTO stationery_items (name, category, quantity, min_stock_level, unit, location, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            item["name"],
            item["category"],
            item["quantity"],
            item["min_stock_level"],
            item.get("unit", "pcs"),
            item.get("location", "Desk"),
            item.get("notes", "")
        ))
    conn.commit()
    inserted = len(SAMPLE_ITEMS)
    conn.close()
    return inserted

def get_all_items(
    db_path: str = DEFAULT_DB_PATH,
    search: str = "",
    category: str = "",
    status: str = ""
) -> List[Dict[str, Any]]:
    """Retrieve all stationery items with optional search and filters."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    query = "SELECT * FROM stationery_items WHERE 1=1"
    params: List[Any] = []

    if search.strip():
        search_term = f"%{search.strip().lower()}%"
        query += " AND (LOWER(name) LIKE ? OR LOWER(notes) LIKE ? OR LOWER(location) LIKE ?)"
        params.extend([search_term, search_term, search_term])

    if category.strip() and category.strip() != "all":
        query += " AND category = ?"
        params.append(category.strip())

    if status == "low_stock":
        query += " AND quantity <= min_stock_level"
    elif status == "in_stock":
        query += " AND quantity > min_stock_level"

    query += " ORDER BY (quantity <= min_stock_level) DESC, category ASC, name ASC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    items = []
    for r in rows:
        d = dict(r)
        d["is_low_stock"] = d["quantity"] <= d["min_stock_level"]
        d["is_out_of_stock"] = d["quantity"] == 0
        items.append(d)
    conn.close()
    return items

def get_item_by_id(item_id: int, db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """Retrieve a single item by primary key."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM stationery_items WHERE id = ?", (item_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["is_low_stock"] = d["quantity"] <= d["min_stock_level"]
    d["is_out_of_stock"] = d["quantity"] == 0
    return d

def create_item(data: Dict[str, Any], db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    """Create a new stationery item."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO stationery_items (name, category, quantity, min_stock_level, unit, location, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("name", "").strip(),
        data.get("category", "General").strip(),
        max(0, int(data.get("quantity", 0))),
        max(0, int(data.get("min_stock_level", 1))),
        data.get("unit", "pcs").strip() or "pcs",
        data.get("location", "Desk").strip() or "Desk",
        data.get("notes", "").strip()
    ))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return get_item_by_id(new_id, db_path)

def update_item(item_id: int, data: Dict[str, Any], db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """Update an existing stationery item."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE stationery_items
        SET name = ?,
            category = ?,
            quantity = ?,
            min_stock_level = ?,
            unit = ?,
            location = ?,
            notes = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        data.get("name", "").strip(),
        data.get("category", "General").strip(),
        max(0, int(data.get("quantity", 0))),
        max(0, int(data.get("min_stock_level", 1))),
        data.get("unit", "pcs").strip() or "pcs",
        data.get("location", "Desk").strip() or "Desk",
        data.get("notes", "").strip(),
        item_id
    ))
    conn.commit()
    conn.close()
    return get_item_by_id(item_id, db_path)

def adjust_item_quantity(
    item_id: int,
    delta: Optional[int] = None,
    new_quantity: Optional[int] = None,
    db_path: str = DEFAULT_DB_PATH
) -> Optional[Dict[str, Any]]:
    """Increment/decrement or set the quantity of an item."""
    item = get_item_by_id(item_id, db_path)
    if not item:
        return None

    if new_quantity is not None:
        final_qty = max(0, int(new_quantity))
    elif delta is not None:
        final_qty = max(0, item["quantity"] + int(delta))
    else:
        final_qty = item["quantity"]

    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE stationery_items
        SET quantity = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (final_qty, item_id))
    conn.commit()
    conn.close()
    return get_item_by_id(item_id, db_path)

def delete_item(item_id: int, db_path: str = DEFAULT_DB_PATH) -> bool:
    """Delete an item by id."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM stationery_items WHERE id = ?", (item_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def get_categories(db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Return list of distinct categories with item counts."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT category, COUNT(*) as count, SUM(quantity) as total_units,
               SUM(CASE WHEN quantity <= min_stock_level THEN 1 ELSE 0 END) as low_stock_count
        FROM stationery_items
        GROUP BY category
        ORDER BY count DESC, category ASC
    """)
    rows = cursor.fetchall()
    categories = [dict(r) for r in rows]
    conn.close()
    return categories

def get_stats(db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    """Return dashboard summary stats."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            COUNT(*) as total_items,
            COALESCE(SUM(quantity), 0) as total_units,
            SUM(CASE WHEN quantity <= min_stock_level THEN 1 ELSE 0 END) as low_stock_count,
            SUM(CASE WHEN quantity = 0 THEN 1 ELSE 0 END) as out_of_stock_count,
            COUNT(DISTINCT category) as total_categories
        FROM stationery_items
    """)
    stats = dict(cursor.fetchone())
    conn.close()
    return stats
