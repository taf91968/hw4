"""Tools the Campus Customs agent can call.

Each tool reads the shop database (campus_customs.db) through `db.py`, the
same code the website uses, so the chatbot can only quote real descriptions,
prices and stock. Every tool returns a Pydantic model from `models.py`, so the
model always gets the same well-defined fields.

| Tool                | Looks up                          | Returns          |
|---------------------|-----------------------------------|------------------|
| search_products     | keywords, max price, in stock     | SearchResult     |
| get_product_details | one product (ID or name)          | ProductInfo      |
| check_stock         | one product (+ optional size)     | StockCheck       |
| find_similar        | one product (+ optional size)     | SimilarItems     |
| list_categories     | —                                 | CategoryOverview |
| get_shopper         | the logged-in user (from deps)    | ShopperProfile   |
| get_current_page    | the shopper's screen (from deps)  | PageInfo         |
"""

import re
from dataclasses import dataclass, field

from pydantic_ai import ModelRetry, RunContext

import db
from audit import audited
from models import (
    LOW_STOCK_MAX,
    CategoryOverview,
    CategorySummary,
    PageContext,
    PageInfo,
    PageProduct,
    ProductDetail,
    ProductHit,
    ProductInfo,
    PublicUser,
    SearchResult,
    ShopperProfile,
    SimilarItem,
    SimilarItems,
    SizeAvailability,
    StockCheck,
    StockStatus,
)


@dataclass
class LastSearch:
    """The most recent search_products call in this run (for page results)."""

    query: str
    ranked_ids: list[str]  # every match, in result order, not just the `limit` sent to the model


@dataclass
class ShopDeps:
    """Per-request state the agent and its tools can see.

    Built fresh for every chat message in agent.run_chat().
    """

    run_id: str | None = None  # ties this message's audit-trail records together
    user: PublicUser | None = None  # logged-in shopper (id, first/last name, email), None for guests
    page: PageContext = field(default_factory=PageContext)  # what the browser is showing
    products_on_screen: list[str] = field(default_factory=list)  # cards under the last reply
    seen_product_ids: set[str] = field(default_factory=set)  # every ID a tool returned this run
    last_search: LastSearch | None = None
    last_similar_ids: list[str] = field(default_factory=list)  # most recent find_similar results

    @property
    def current_product_id(self) -> str | None:
        """Product page the shopper is viewing, if any."""
        return self.page.product_id


# ---------- Shared helpers ----------

def _status(quantity: int) -> StockStatus:
    if quantity == 0:
        return "sold out"
    return "low stock" if quantity <= LOW_STOCK_MAX else "in stock"


def _sizes(p: ProductDetail) -> list[SizeAvailability]:
    return [SizeAvailability(size=s.size, quantity=s.quantity, status=_status(s.quantity)) for s in p.inventory]


def _sizes_in_stock(p: ProductDetail) -> list[str]:
    return [s.size for s in p.inventory if s.quantity > 0]


def _resolve(ctx: RunContext[ShopDeps], product: str) -> ProductDetail:
    """Find one product by product_id, or by its exact name (any letter case).

    Raises ModelRetry with suggestions so the model can correct itself.
    """
    key = product.strip()
    p = db.get_product(key) or db.get_product(key.lower().replace(" ", "-"))
    if p is None:
        by_name = [d for d in db.list_product_details() if d.name.lower() == key.lower()]
        p = by_name[0] if len(by_name) == 1 else None
    if p is None:
        shopper_search = ctx.deps.last_search  # suggestions mustn't replace the page results
        close = search_products(ctx, key, in_stock_only=False, limit=3).products
        ctx.deps.last_search = shopper_search
        hint = ", ".join(f"{h.name} ({h.product_id})" for h in close) or "none"
        raise ModelRetry(
            f"No product matches '{product}'. Closest matches: {hint}. "
            "Use one of those product_id values, or call search_products."
        )
    ctx.deps.seen_product_ids.add(p.product_id)
    return p


# ---------- Search ----------

# Common shopper words mapped to the words the catalogue actually uses.
SYNONYMS = {
    "tee": "t-shirt", "tees": "t-shirt", "tshirt": "t-shirt", "tshirts": "t-shirt",
    "hoody": "hoodie", "hoodies": "hoodie", "hooded": "hoodie", "hood": "hoodie",
    "sweatshirts": "sweatshirt", "crew": "crewneck", "crewnecks": "crewneck",
    "quarterzip": "quarter-zip", "1/4": "quarter-zip", "¼": "quarter-zip",
    "fleeces": "fleece", "jackets": "jacket", "grey": "gray",
    "bulldogs": "bulldog", "dan": "bulldog",
}

STOPWORDS = {
    "a", "an", "and", "any", "anything", "are", "do", "for", "got", "have", "i", "im",
    "in", "is", "it", "me", "of", "on", "or", "show", "some", "something", "that",
    "the", "there", "with", "you", "your", "u", "what", "whats", "which", "looking",
    "want", "need", "item", "items", "stuff", "gear", "one", "ones", "please",
}

# Words whose singular means something else in the catalogue ("short" is in "short-sleeve").
NO_SINGULAR = {"shorts", "pants", "sweatpants", "joggers", "leggings", "socks", "glasses"}


def _terms(query: str) -> list[str]:
    query = query.lower().replace("quarter zip", "quarter-zip").replace("t shirt", "t-shirt")
    words = re.findall(r"[a-z0-9¼/'-]+", query)
    terms = []
    for w in words:
        w = SYNONYMS.get(w, w.strip("'"))
        if w and w not in STOPWORDS:
            terms.append(w)
    return list(dict.fromkeys(terms))


def _text(p: ProductDetail) -> str:
    return " ".join([p.name, p.garment_type, p.description, *p.colors, *p.search_tags]).lower()


def _matches(term: str, text: str) -> bool:
    # Match at the start of a word: "hoodie" matches "hoodies", "zip" matches
    # "full-zip", but "art" doesn't match "smart". "hats" also tries "hat".
    def at_word_start(t: str) -> bool:
        return re.search(r"(?<![a-z0-9])" + re.escape(t), text) is not None

    if at_word_start(term):
        return True
    return term.endswith("s") and term not in NO_SINGULAR and len(term) > 3 and at_word_start(term[:-1])


def _qty(p: ProductDetail, size: str | None) -> int | None:
    if size is None:
        return None
    return next((s.quantity for s in p.inventory if s.size == size), 0)


def search_products(
    ctx: RunContext[ShopDeps],
    query: str,
    max_price: float | None = None,
    in_stock_only: bool = True,
    size: str | None = None,
    limit: int = 8,
) -> SearchResult:
    """Search the Campus Customs catalogue by keywords. Use it to find products and compare prices.

    Matches words against each product's name, garment type, description,
    colors and tags. Products matching every word rank first (cheapest first);
    if none match every word, products matching the most words are returned.

    Args:
        query: Keywords, e.g. "navy hoodie", "bulldog", "fleece", "Branford", "Harvard".
        max_price: Only return products at or below this price in US dollars ("under $60").
        in_stock_only: Skip products with no stock in any size.
        size: Only return products in stock in this size. Pass the shopper's size whenever
            they have mentioned one: XS, S, M, L, XL, XXL, or words like "medium", "2XL".
        limit: Maximum number of products to return (1-10).
    """
    limit = max(1, min(limit, 10))
    terms = _terms(query)
    products = db.list_product_details()
    size_label, note = None, None
    if size:
        size_label = normalize_size(size)
        if size_label is None:
            note = f"'{size}' isn't a size Campus Customs carries (XS–XXL), so no size filter was applied."
    if max_price is not None:
        products = [p for p in products if p.price <= max_price]
    if size_label:
        products = [p for p in products if (_qty(p, size_label) or 0) > 0]
    elif in_stock_only:
        products = [p for p in products if p.total_stock > 0]

    matched: dict[str, list[str]] = {}
    if not terms:
        ranked = sorted(products, key=lambda p: (p.price, p.name))
        match = "no keywords given; showing products"
    else:
        scored = []
        for p in products:
            text = _text(p)
            hit_terms = [t for t in terms if _matches(t, text)]
            if hit_terms:
                matched[p.product_id] = hit_terms
                scored.append((len(hit_terms), p))
        scored.sort(key=lambda sp: (-sp[0], sp[1].price, sp[1].name))
        full = [p for s, p in scored if s == len(terms)]
        ranked = full or [p for _, p in scored]
        match = (
            "all keywords"
            if full
            else "partial: no product matches every keyword, so these only match some of them"
            if ranked
            else "none: nothing in the catalogue matches"
        )

    hits = ranked[:limit]
    ctx.deps.seen_product_ids.update(p.product_id for p in hits)
    ctx.deps.last_search = LastSearch(query=query, ranked_ids=[p.product_id for p in ranked])
    partial = match.startswith("partial")
    return SearchResult(
        size=size_label,
        note=note,
        query_terms=terms,
        match=match,
        total_found=len(ranked),
        products=[
            ProductHit(
                product_id=p.product_id,
                name=p.name,
                garment_type=p.garment_type,
                category=p.category,
                price=p.price,
                colors=p.colors,
                description=p.description,
                sizes_in_stock=_sizes_in_stock(p),
                size_quantity=_qty(p, size_label),
                matched_terms=matched.get(p.product_id) if partial else None,
            )
            for p in hits
        ],
    )


# ---------- One product: description, price, stock ----------

def _info(p: ProductDetail) -> ProductInfo:
    sizes = _sizes(p)
    return ProductInfo(
        product_id=p.product_id,
        name=p.name,
        garment_type=p.garment_type,
        description=p.description,
        price=p.price,
        colors=p.colors,
        tags=p.search_tags,
        sizes=sizes,
        sizes_in_stock=[s.size for s in sizes if s.quantity > 0],
        sold_out_sizes=[s.size for s in sizes if s.quantity == 0],
        total_stock=p.total_stock,
    )


def get_product_details(ctx: RunContext[ShopDeps], product: str) -> ProductInfo:
    """Full record for one product: description, price, colors, and stock for every size.

    Call this for any question about a specific product's description, price
    or availability. Always call it again rather than reusing numbers from
    earlier in the chat: prices and stock can change.

    Args:
        product: The product_id (best), or the product's exact name.
    """
    return _info(_resolve(ctx, product))


# Shopper words for sizes → the labels stored in inventory.size.
SIZE_WORDS = {
    "xs": "XS", "extra small": "XS", "extra-small": "XS", "x-small": "XS", "xsmall": "XS",
    "s": "S", "small": "S", "sm": "S",
    "m": "M", "medium": "M", "med": "M", "md": "M",
    "l": "L", "large": "L", "lg": "L",
    "xl": "XL", "extra large": "XL", "extra-large": "XL", "x-large": "XL", "xlarge": "XL",
    "xxl": "XXL", "2xl": "XXL", "xx-large": "XXL", "xxlarge": "XXL", "2x": "XXL",
    "double xl": "XXL", "extra extra large": "XXL",
}


def normalize_size(size: str) -> str | None:
    return SIZE_WORDS.get(size.strip().lower().rstrip("."))


def check_stock(ctx: RunContext[ShopDeps], product: str, size: str | None = None) -> StockCheck:
    """How many of a product are in stock, for one size or all sizes.

    Use for "do you have it in medium?", "how many XL are left?", "is it sold out?".

    Args:
        product: The product_id (best), or the product's exact name.
        size: Optional size as the shopper said it: XS, S, M, L, XL, XXL, or words
            like "small", "medium", "large", "extra large", "2XL". Leave empty for all sizes.
    """
    p = _resolve(ctx, product)
    sizes = _sizes(p)
    label = normalize_size(size) if size else None
    note = None
    if size and label is None:
        # Not an error: tell the model so it can explain we carry XS–XXL.
        note = f"'{size}' isn't a size Campus Customs carries. Sizes are XS, S, M, L, XL and XXL."
    chosen = next((s for s in sizes if s.size == label), None)
    return StockCheck(
        product_id=p.product_id,
        name=p.name,
        price=p.price,
        size_asked=size,
        size=label,
        quantity=chosen.quantity if chosen else None,
        status=chosen.status if chosen else None,
        sizes=sizes,
        total_stock=p.total_stock,
        note=note,
    )


# ---------- Alternatives ----------

# Tags almost every product has; sharing them says nothing about similarity.
GENERIC_TAGS = {
    "yale", "campus customs", "college apparel", "college merch", "yale merch",
    "yale apparel", "collegiate", "university apparel", "yale university",
}


def _color_words(colors: list[str]) -> set[str]:
    # "navy blue" and "navy" should count as the same color.
    skip = {"heather", "dark", "light", "dusty", "blue"}
    words = {w for c in colors for w in c.lower().split() if w not in skip}
    return words or {c.lower() for c in colors}


def find_similar(
    ctx: RunContext[ShopDeps], product: str, size: str | None = None, limit: int = 4
) -> SimilarItems:
    """In-stock alternatives to a product: same category, similar colors, style and price.

    Use when a size the shopper wants is sold out ("L is sold out — here are similar
    hoodies with L in stock"), or when they ask for "something like this".

    Args:
        product: The product_id (best), or the product's exact name.
        size: Only suggest items in stock in this size (the shopper's size), e.g. "L", "large".
        limit: How many alternatives to return (1-6).
    """
    limit = max(1, min(limit, 6))
    src = _resolve(ctx, product)
    label = normalize_size(size) if size else None
    note = None
    if size and label is None:
        note = f"'{size}' isn't a size Campus Customs carries (XS–XXL), so no size filter was applied."

    src_colors = _color_words(src.colors)
    src_tags = {t.lower() for t in src.search_tags} - GENERIC_TAGS
    scored = []
    for p in db.list_product_details():
        if p.product_id == src.product_id or p.total_stock == 0:
            continue
        if label and (_qty(p, label) or 0) == 0:
            continue
        score, reasons = 0.0, []
        if p.category == src.category:
            score += 3
            reasons.append(f"same category ({p.category})")
        shared_colors = sorted(src_colors & _color_words(p.colors))
        if shared_colors:
            score += len(shared_colors)
            reasons.append("also " + "/".join(shared_colors))
        shared_tags = sorted(src_tags & ({t.lower() for t in p.search_tags} - GENERIC_TAGS))
        if shared_tags:
            score += 0.5 * len(shared_tags)
            reasons.append("similar style: " + ", ".join(shared_tags[:3]))
        if abs(p.price - src.price) <= 0.15 * src.price:
            score += 1
            reasons.append("similar price" if p.price != src.price else "same price")
        if score >= 3:  # at least the same category, or several other things in common
            scored.append((score, p, reasons))
    scored.sort(key=lambda x: (-x[0], abs(x[1].price - src.price), x[1].name))

    items = [
        SimilarItem(
            product_id=p.product_id,
            name=p.name,
            category=p.category,
            price=p.price,
            colors=p.colors,
            sizes_in_stock=_sizes_in_stock(p),
            size_quantity=_qty(p, label),
            reasons=reasons,
        )
        for _, p, reasons in scored[:limit]
    ]
    ctx.deps.seen_product_ids.update(i.product_id for i in items)
    ctx.deps.last_similar_ids = [i.product_id for i in items]
    return SimilarItems(
        source_product_id=src.product_id,
        source_name=src.name,
        size=label,
        source_in_stock_in_size=((_qty(src, label) or 0) > 0) if label else None,
        note=note,
        items=items,
    )


# ---------- Who is chatting, and what is on their screen ----------

def get_shopper(ctx: RunContext[ShopDeps]) -> ShopperProfile:
    """Who is chatting: the logged-in shopper's name, email and account details.

    Use when the shopper asks about themselves ("what's my email?", "am I logged
    in?") or when you need their details. Guests get logged_in=false.
    """
    user = ctx.deps.user
    if user is None:
        return ShopperProfile(logged_in=False)
    created_at, saved = db.shopper_stats(user.id)
    return ShopperProfile(
        logged_in=True,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        member_since=created_at[:10] if created_at else None,
        saved_chat_messages=saved,
    )


def _page_products(ids: list[str]) -> list[PageProduct]:
    return [
        PageProduct(position=i, product_id=p.product_id, name=p.name, price=p.price, colors=p.colors)
        for i, p in enumerate(db.get_products(ids), start=1)
    ]


def get_current_page(ctx: RunContext[ShopDeps]) -> PageInfo:
    """What the shopper is looking at right now: the open product page (full record),
    the chat results panel cards in on-screen order, and the cards under your last reply.

    Use it to work out what "this", "it", "this one" or "the third one" means.
    """
    page = ctx.deps.page
    viewing = None
    if page.product_id:
        p = db.get_product(page.product_id)
        if p is not None:
            ctx.deps.seen_product_ids.add(p.product_id)
            viewing = _info(p)
    results = _page_products(page.results_product_ids)
    last_cards = _page_products(ctx.deps.products_on_screen)
    ctx.deps.seen_product_ids.update(r.product_id for r in results + last_cards)
    return PageInfo(
        path=page.path,
        page_type=page.page_type,
        viewing_product=viewing,
        results_title=page.results_title,
        results_on_page=results,
        last_reply_cards=last_cards,
    )


# ---------- Overview ----------

def list_categories(ctx: RunContext[ShopDeps]) -> CategoryOverview:
    """Overview of what Campus Customs sells: garment types with counts and price ranges."""
    groups: dict[str, list[float]] = {}
    for p in db.list_product_details():
        groups.setdefault(p.garment_type.lower(), []).append(p.price)
    return CategoryOverview(
        total_products=sum(len(v) for v in groups.values()),
        categories=[
            CategorySummary(garment_type=g, count=len(prices), min_price=min(prices), max_price=max(prices))
            for g, prices in sorted(groups.items(), key=lambda kv: -len(kv[1]))
        ],
    )


# Every tool the agent can call, each wrapped so its calls, results and retries
# are appended to output/audit_trail.json (see audit.py).
TOOLS = [
    audited(t)
    for t in [
        search_products,
        get_product_details,
        check_stock,
        find_similar,
        list_categories,
        get_shopper,
        get_current_page,
    ]
]
