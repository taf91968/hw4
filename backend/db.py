"""Access to the Campus Customs SQLite database.

The FastAPI routes and the agent's tools both use these helpers, so the website
and the chatbot always show the same products, prices, and stock.
"""

import json
import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from models import ChatTurn, ProductCard, ProductDetail, ProductSummary, SizeStock

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
# CC_DB_PATH lets tests run against a copy instead of the real database.
DB_PATH = Path(os.getenv("CC_DB_PATH") or DATA_DIR / "campus_customs.db")
PRODUCTS_DIR = DATA_DIR / "products"

# Sizes sort in shop order rather than alphabetically.
SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]

# Shop categories, in the order the website shows them. `garment_type` has 22
# inconsistent spellings ("short-sleeve T-shirt", "t-shirt", "hoodie",
# "pullover hoodie", …), so products are grouped by keywords instead.
CATEGORIES = ["Hoodies", "Crewnecks", "T-Shirts", "Quarter-Zips", "Jackets & Fleece", "Long Sleeve"]


def category_of(garment_type: str, name: str) -> str:
    """Map a product to one shop category (checked in this order; covers all 102)."""
    text = f" {garment_type} {name} ".lower()
    if "quarter-zip" in text or " 1 4 zip" in text:
        return "Quarter-Zips"
    if "hood" in text:
        return "Hoodies"
    if "jacket" in text or "fleece" in text:
        return "Jackets & Fleece"
    if "long-sleeve" in text or "long sleeve" in text or "performance" in text:
        return "Long Sleeve"
    if "t-shirt" in text or " t shirt" in text or " tee" in text:
        return "T-Shirts"
    return "Crewnecks"  # crewneck, mockneck, and raglan sweatshirts


@contextmanager
def connect(writable: bool = False) -> Iterator[sqlite3.Connection]:
    """Open the database with foreign keys enforced; commit and close when done.

    Read-only by default. Only account signup and saving chat messages open it
    writable.
    """
    mode = "rw" if writable else "ro"
    conn = sqlite3.connect(f"file:{DB_PATH.as_posix()}?mode={mode}", uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def image_url(image_file_path: str) -> str:
    """Turn `products/x.jpg` from the catalogue into the URL served at /media."""
    return f"/media/{image_file_path}"


# ---------- Products ----------

def _sort_sizes(sizes: list[SizeStock]) -> None:
    sizes.sort(key=lambda s: SIZE_ORDER.index(s.size) if s.size in SIZE_ORDER else len(SIZE_ORDER))


def _stock_by_product(conn: sqlite3.Connection) -> dict[str, list[SizeStock]]:
    stock: dict[str, list[SizeStock]] = {}
    for row in conn.execute("SELECT product_id, size, quantity FROM inventory"):
        stock.setdefault(row["product_id"], []).append(
            SizeStock(size=row["size"], quantity=row["quantity"])
        )
    for sizes in stock.values():
        _sort_sizes(sizes)
    return stock


def _summary(row: sqlite3.Row, sizes: list[SizeStock]) -> ProductSummary:
    return ProductSummary(
        product_id=row["product_id"],
        name=row["name"],
        garment_type=row["garment_type"],
        description=row["description"],
        price=row["price"],
        colors=json.loads(row["colors"]),
        image_url=image_url(row["image_file_path"]),
        total_stock=sum(s.quantity for s in sizes),
        category=category_of(row["garment_type"], row["name"]),
        sizes_in_stock=[s.size for s in sizes if s.quantity > 0],
    )


def _detail(row: sqlite3.Row, sizes: list[SizeStock]) -> ProductDetail:
    return ProductDetail(
        **_summary(row, sizes).model_dump(),
        search_tags=json.loads(row["search_tags"]),
        inventory=sizes,
    )


def list_products() -> list[ProductSummary]:
    """All products, sorted by name."""
    with connect() as conn:
        stock = _stock_by_product(conn)
        rows = conn.execute("SELECT * FROM catalogue ORDER BY name").fetchall()
    return [_summary(row, stock.get(row["product_id"], [])) for row in rows]


def list_product_details() -> list[ProductDetail]:
    """All products with tags and stock by size (used by the agent's search)."""
    with connect() as conn:
        stock = _stock_by_product(conn)
        rows = conn.execute("SELECT * FROM catalogue ORDER BY name").fetchall()
    return [_detail(row, stock.get(row["product_id"], [])) for row in rows]


def get_product(product_id: str) -> ProductDetail | None:
    """One product with its stock by size, or None if the ID is unknown."""
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM catalogue WHERE product_id = ?", (product_id,)
        ).fetchone()
        if row is None:
            return None
        sizes = [
            SizeStock(size=r["size"], quantity=r["quantity"])
            for r in conn.execute(
                "SELECT size, quantity FROM inventory WHERE product_id = ?", (product_id,)
            )
        ]
    _sort_sizes(sizes)
    return _detail(row, sizes)


def get_products(product_ids: list[str]) -> list[ProductDetail]:
    """Products for the given IDs, in the same order; unknown IDs are skipped."""
    found = []
    for pid in dict.fromkeys(product_ids):  # drop duplicates, keep order
        item = get_product(pid)
        if item is not None:
            found.append(item)
    return found


# ---------- Chat history ----------

def _cards(products_json: str | None) -> list[ProductCard]:
    if not products_json:
        return []
    try:
        return [ProductCard.model_validate(p) for p in json.loads(products_json)]
    except (ValueError, TypeError):
        return []


def load_chat(user_id: int, limit: int = 30) -> list[ChatTurn]:
    """The user's most recent chat messages, oldest first."""
    with connect() as conn:
        rows = conn.execute(
            "SELECT role, content, products_json FROM chat_messages "
            "WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return [
        ChatTurn(role=r["role"], content=r["content"], products=_cards(r["products_json"]))
        for r in reversed(rows)
    ]


def shopper_stats(user_id: int) -> tuple[str | None, int]:
    """(account created_at, number of saved chat messages) for one user."""
    with connect() as conn:
        row = conn.execute("SELECT created_at FROM users WHERE id = ?", (user_id,)).fetchone()
        count = conn.execute(
            "SELECT COUNT(*) FROM chat_messages WHERE user_id = ?", (user_id,)
        ).fetchone()[0]
    return (row["created_at"] if row else None), count


def save_chat_turn(user_id: int, message: str, reply: str, products: list[ProductDetail]) -> None:
    """Save the shopper's message and the agent's reply.

    Products are stored as full product objects, the same shape as the seed
    rows in `chat_messages.products_json`.
    """
    products_json = json.dumps([p.model_dump() for p in products]) if products else None
    with connect(writable=True) as conn:
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content) VALUES (?, 'user', ?)",
            (user_id, message),
        )
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content, products_json) "
            "VALUES (?, 'assistant', ?, ?)",
            (user_id, reply, products_json),
        )
