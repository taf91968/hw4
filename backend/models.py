"""Pydantic / PydanticAI types for the Campus Customs backend.

- Product types: what the API returns to the React frontend.
- Account types: signup/login bodies and the public view of a user.
- Chat types: what the website sends to the chat route, what the agent must
  return (`AgentReply`), and what the chat route sends back (`ChatResponse`).
"""

from typing import Literal

from pydantic import BaseModel, Field

# ---------- Products ----------


class SizeStock(BaseModel):
    """Units on hand for one size of one product (from the `inventory` table)."""

    size: str = Field(description="Size label: XS, S, M, L, XL, or XXL.")
    quantity: int = Field(ge=0, description="Units in stock; 0 means sold out in this size.")


class ProductSummary(BaseModel):
    """What a product card on the Products page needs."""

    product_id: str = Field(description="Unique slug from `catalogue.product_id`.")
    name: str
    garment_type: str
    description: str
    price: float = Field(description="Price in US dollars.")
    colors: list[str]
    image_url: str = Field(description="URL the frontend can load, e.g. /media/products/<file>.jpg.")
    total_stock: int = Field(ge=0, description="Units in stock across all sizes.")
    category: str = Field(
        description="Shop category (Hoodies, Crewnecks, T-Shirts, Quarter-Zips, Jackets & Fleece, "
        "Long Sleeve), cleaned up from the inconsistent garment_type."
    )
    sizes_in_stock: list[str] = Field(description="Sizes with quantity > 0, XS → XXL.")


class ProductDetail(ProductSummary):
    """Everything the single-item page shows, including stock by size."""

    search_tags: list[str]
    inventory: list[SizeStock]


class ProductCard(BaseModel):
    """A product shown under a chat reply (the chat's product panel).

    Stored in `chat_messages.products_json`. The seed rows hold full product
    objects, which validate into this smaller shape because extra fields are ignored.
    """

    product_id: str
    name: str
    garment_type: str
    price: float
    image_url: str
    colors: list[str]
    inventory: list[SizeStock]
    total_stock: int


# ---------- Agent tool results ----------
# Each tool in tools.py returns one of these, so the model always gets the same
# well-defined fields, read straight from campus_customs.db.

StockStatus = Literal["in stock", "low stock", "sold out"]
LOW_STOCK_MAX = 5  # 1–5 units left counts as "low stock" (same as the product page)


class SizeAvailability(BaseModel):
    """Stock for one size, from `inventory.size` and `inventory.quantity`."""

    size: str = Field(description="XS, S, M, L, XL or XXL.")
    quantity: int = Field(ge=0, description="Units on hand right now.")
    status: StockStatus


class ProductHit(BaseModel):
    """One product in search results: enough to recommend it and compare prices."""

    product_id: str
    name: str
    garment_type: str
    category: str
    price: float = Field(description="US dollars, from catalogue.price.")
    colors: list[str]
    description: str
    sizes_in_stock: list[str] = Field(description="Sizes with quantity > 0.")
    size_quantity: int | None = Field(
        default=None, description="Units left in the size searched for (only when a size was given)."
    )
    matched_terms: list[str] | None = Field(
        default=None, description="Only for partial matches: which search words this product matched."
    )


class SearchResult(BaseModel):
    """Result of search_products."""

    size: str | None = Field(default=None, description="Size filter applied (as stored, e.g. 'M'), if any.")
    note: str | None = Field(default=None, description="Set when the size asked isn't one we carry.")
    query_terms: list[str] = Field(description="Search words after synonyms and stopwords.")
    match: str = Field(description="'all keywords', 'partial: …' or 'none: …'.")
    total_found: int
    products: list[ProductHit]


class ProductInfo(BaseModel):
    """Result of get_product_details: the full product record for one item."""

    product_id: str
    name: str
    garment_type: str
    description: str = Field(description="Full catalogue.description text.")
    price: float = Field(description="US dollars, from catalogue.price.")
    colors: list[str]
    tags: list[str]
    sizes: list[SizeAvailability] = Field(description="Every size, XS → XXL, with quantity and status.")
    sizes_in_stock: list[str]
    sold_out_sizes: list[str]
    total_stock: int = Field(description="Sum of quantity over all sizes.")


class StockCheck(BaseModel):
    """Result of check_stock: stock for one product, optionally one size."""

    product_id: str
    name: str
    price: float
    size_asked: str | None = Field(description="The size as the shopper said it, e.g. 'medium'.")
    size: str | None = Field(description="That size as stored in the database, e.g. 'M'.")
    quantity: int | None = Field(description="Units in that size; None when no size was asked.")
    status: StockStatus | None = Field(description="Status of that size; None when no size was asked.")
    sizes: list[SizeAvailability] = Field(description="Every size, so the agent can suggest alternatives.")
    total_stock: int
    note: str | None = Field(default=None, description="Set when the size asked isn't one we carry.")


class SimilarItem(BaseModel):
    """One in-stock alternative, with the reasons it is similar."""

    product_id: str
    name: str
    category: str
    price: float
    colors: list[str]
    sizes_in_stock: list[str]
    size_quantity: int | None = Field(default=None, description="Units left in the size asked for, if any.")
    reasons: list[str] = Field(description="Why it's similar, e.g. 'same category (Hoodies)', 'also navy'.")


class SimilarItems(BaseModel):
    """Result of find_similar."""

    source_product_id: str
    source_name: str
    size: str | None = Field(description="Only items in stock in this size (as stored), if a size was given.")
    source_in_stock_in_size: bool | None = Field(
        description="Whether the original product itself has that size in stock."
    )
    note: str | None = None
    items: list[SimilarItem] = Field(description="Best matches first; all are in stock.")


class ShopperProfile(BaseModel):
    """Result of get_shopper: who is chatting (from the `users` table)."""

    logged_in: bool
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    member_since: str | None = Field(default=None, description="Account creation date, YYYY-MM-DD.")
    saved_chat_messages: int = Field(default=0, description="Messages already saved for this shopper.")


class PageProduct(BaseModel):
    """A product the shopper can see on their screen."""

    position: int = Field(description="1-based position as shown, so 'the third one' = 3.")
    product_id: str
    name: str
    price: float
    colors: list[str]


class PageInfo(BaseModel):
    """Result of get_current_page: what is on the shopper's screen right now."""

    path: str
    page_type: str
    viewing_product: ProductInfo | None = Field(
        default=None, description="Full record of the product page that is open, if any."
    )
    results_title: str | None = None
    results_on_page: list[PageProduct] = Field(
        default_factory=list, description="Chat results panel cards, in on-screen order."
    )
    last_reply_cards: list[PageProduct] = Field(
        default_factory=list, description="Product cards under your last chat reply."
    )


class CategorySummary(BaseModel):
    garment_type: str
    count: int
    min_price: float
    max_price: float


class CategoryOverview(BaseModel):
    """Result of list_categories."""

    total_products: int
    categories: list[CategorySummary]


# ---------- Accounts ----------


class SignupRequest(BaseModel):
    """Create-account form. Confirm-password is checked in the browser only."""

    first_name: str = Field(max_length=60)
    last_name: str = Field(max_length=60)
    email: str = Field(max_length=254)
    password: str = Field(max_length=128)


class LoginRequest(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(max_length=128)


class PublicUser(BaseModel):
    """The logged-in shopper as the frontend and the agent see them.

    Never includes `password_hash`.
    """

    id: int
    first_name: str
    last_name: str
    email: str


# ---------- Chat ----------

MAX_MESSAGE_CHARS = 1000
MAX_GUEST_HISTORY = 12
MAX_PRODUCT_CARDS = 8
MAX_PAGE_RESULTS = 24


class GuestTurn(BaseModel):
    """One earlier message, sent by the browser for shoppers who aren't logged in.

    Logged-in shoppers' history comes from the database instead.
    """

    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)
    product_ids: list[str] = Field(default_factory=list, max_length=MAX_PRODUCT_CARDS)


PageType = Literal["home", "products", "product", "about", "login", "create_account", "other"]


class PageContext(BaseModel):
    """What the shopper's browser is showing when they send a chat message.

    Sent by the chat widget with every message, so "do you have this in pink?"
    on a product page, or "the third one" under chat results, can be resolved.
    Only IDs are sent; the backend looks the products up in the database itself.
    """

    path: str = Field(default="/", max_length=300, description="URL path, e.g. /products/basic-hoodie-big-yale.")
    page_type: PageType = "other"
    product_id: str | None = Field(
        default=None, max_length=200, description="Product whose single-item page is open, if any."
    )
    results_title: str | None = Field(
        default=None, max_length=60, description="Heading of the chat results panel on the page, if showing."
    )
    results_product_ids: list[str] = Field(
        default_factory=list,
        max_length=MAX_PAGE_RESULTS,
        description="Product IDs in the chat results panel, in the order shown.",
    )


class ChatRequest(BaseModel):
    """Body of POST /api/chat."""

    message: str = Field(min_length=1, max_length=MAX_MESSAGE_CHARS)
    page: PageContext = Field(default_factory=PageContext)
    current_product_id: str | None = Field(
        default=None, max_length=200, description="Older form of page.product_id; still accepted."
    )
    history: list[GuestTurn] = Field(default_factory=list, max_length=MAX_GUEST_HISTORY)


class AgentReply(BaseModel):
    """Structured output the PydanticAI agent must return."""

    reply: str = Field(
        description="What to say to the shopper, in Campus Customs voice. Markdown allowed: "
        "**bold** and '- ' bullet lists."
    )
    product_ids: list[str] = Field(
        default_factory=list,
        max_length=MAX_PRODUCT_CARDS,
        description="product_id values (from tool results only) to show as product cards "
        "under the reply, most relevant first. Empty if no products fit.",
    )
    page_title: str | None = Field(
        default=None,
        max_length=60,
        description="Set ONLY when the shopper is browsing a type or group of items "
        "(e.g. 'Hoodies', 'Bulldog gear', 'Tees under $40'). The website then shows every "
        "result of your most recent search_products call as product cards on the page, "
        "under this title. Leave null for questions about one product (price, stock, sizes) "
        "and for small talk, so the page stays as it is.",
    )


class ChatTurn(BaseModel):
    """One message in a chat, as the chat widget shows it."""

    role: Literal["user", "assistant"]
    content: str
    products: list[ProductCard] = Field(default_factory=list)


class PageResults(BaseModel):
    """Search results the website shows as product cards on the page itself.

    Built by the backend from the agent's most recent search_products call
    (not from the model's text), so the cards always match the catalogue.
    """

    title: str = Field(description="Heading from the agent, e.g. 'Hoodies'.")
    query: str = Field(description="The search_products query that produced these results.")
    total_found: int = Field(description="How many products matched in total.")
    products: list[ProductSummary] = Field(
        description=f"Up to {MAX_PAGE_RESULTS} matches in search order: image, name, price, description."
    )


class ChatResponse(BaseModel):
    """Response of POST /api/chat: the agent's reply, product cards, and optional page results."""

    reply: str
    products: list[ProductCard]
    page_results: PageResults | None = None
