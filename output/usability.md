# Campus Customs — Usability Improvements (Problem 9)

Four improvements to how the shop works: two in the website (front end) and two in the agent and backend. For each: what was added, why it helps a Campus Customs shopper or the business, and how it was checked in the running app.

*This file was written as a plan before building; each section was then updated with what was actually built and how it was checked. Status: all four built and checked in the running app (18/18 checks).*

| # | Area | Improvement |
|---|---|---|
| 1 | Front end | Shop by category, size, and price on the Products page |
| 2 | Front end | "Ask about this item" and one-tap question chips in the chat |
| 3 | Agent / backend | Size-aware search: "hoodies in my size" |
| 4 | Agent / backend | Similar in-stock items when the shopper's choice is sold out |

---

## 1. Shop by category, size, and price (front end)

**Plan:** add filters above the Products grid:
- category chips (Hoodies, Crewnecks, T-Shirts, Quarter-Zips, Jackets & Fleece, Long Sleeve)
- a size picker (XS–XXL) that hides products sold out in that size
- an "In stock only" switch
- a sort menu (featured, price low → high, price high → low, name)

The filters live in the URL, so a filtered view can be bookmarked or shared. Each card also lists its sizes in stock. The backend gives every product a clean `category`, because the database's `garment_type` has 22 inconsistent spellings.

**Why it helps:** 102 products in one long grid is hard to browse. Today a shopper looking for a medium hoodie scrolls past tees and crewnecks and opens product pages one by one to find their size. With filters, it takes two taps, and they never fall for an item they can't buy in their size. For the business, shoppers who find their size quickly are more likely to buy, and shareable links help with group orders (a residential college or team buying the same item).

## 2. "Ask about this item" + one-tap question chips (front end)

**Plan:**
- The chat panel shows suggested questions that fit the page the shopper is on. On a product page: "Is this in stock in M?", "What colors does this come in?", "Show me similar items". Elsewhere: "What hoodies do you have?", "Anything under $40?", "Show me Bulldog gear". One tap sends the question.
- Each product page gets an **Ask about this item** button that opens the chat with those product questions ready.

**Why it helps:** many shoppers don't know what the assistant can do, or don't want to type on a phone. Chips show the useful questions and answer them in one tap. The product-page button puts help right where buying decisions happen. For the business, more shoppers get size and stock answers without emailing the shop, which means fewer lost sales and fewer support questions.

## 3. Size-aware search (agent / backend)

**Plan:** `search_products` gets a `size` filter (accepting "M", "medium", "2XL", …). Results include only products in stock in that size, and each result shows how many are left in it. The prompt tells the agent to use the shopper's size whenever they've mentioned one, earlier in the chat too. The page results (Problem 7) then show only items in their size.

**Why it helps:** "Do you have hoodies in medium?" currently returns every hoodie, including ones sold out in M (145 of 612 size rows are sold out). Shoppers would have to check each one. With size-aware search the chat and the cards only show things they can actually buy. For the business, it avoids the disappointment of recommending something that turns out to be unavailable.

## 4. Similar in-stock items when sold out (agent / backend)

**Plan:** a new tool, `find_similar(product, size?)`, ranks other in-stock products by category, shared colors, shared tags, and price. It returns `SimilarItems` with the reasons each item is similar. The prompt says to offer these whenever a requested size is sold out, or when the shopper asks for "something like this".

**Why it helps:** "Sorry, L is sold out" is a dead end. Offering "the Crew Left Chest Hoodie is the same navy left-chest style and has L in stock" keeps the shopper moving. For the business, a sold-out size becomes a different sale instead of a lost one, and every item suggested really is available.

---

## What was built

### 1. Shop by category, size, and price

| Part | Where |
|---|---|
| Clean `category` for every product. Keyword rules map the 22 `garment_type` spellings into 6 shop categories, covering all 102 products: Crewnecks 29, Hoodies 27, T-Shirts 25, Quarter-Zips 11, Jackets & Fleece 8, Long Sleeve 2. | `backend/db.py` (`CATEGORIES`, `category_of`) |
| `category` and `sizes_in_stock` added to every product the API returns | `backend/models.py` (`ProductSummary`) |
| Filter bar: category chips with counts, a "My size" picker (XS–XXL), an "In stock only" switch, a sort menu, and "Clear filters". The count line reads "21 of 102 products in stock in size M". | `frontend/src/pages/Products.tsx` |
| Filters saved in the URL, e.g. `/products?category=Hoodies&size=M&sort=price-asc`. Shareable and bookmarkable, and Back/Forward work. | same |
| Each card has a size row (XS S M L XL XXL). Sold-out sizes are crossed out, and the chosen size is highlighted pink. This shows on the Products page, the Home page, and the chat results panel. | `frontend/src/components/ProductCard.tsx` |

### 2. "Ask about this item" + one-tap question chips

| Part | Where |
|---|---|
| Question chips above the chat input that change with the page. **Product page:** "Is this in stock in M?", "What colors does this come in?", "Show me similar items". **Chat results showing:** "Which of these are in stock in M?", "What's the cheapest one?", "Tell me about the first one". **Elsewhere:** "What hoodies do you have?", "Anything under $40?", and "Show me Bulldog gear" for guests or "What was I looking at last time?" for logged-in shoppers. One tap sends the question. | `frontend/src/components/ChatWidget.tsx` (`suggestedQuestions`) |
| **Ask about this item** button on every product page. It opens the chat with the product-page chips ready. | `frontend/src/pages/ProductPage.tsx` |
| **Find similar in L** link under each sold-out size on the product page. It opens the chat and asks for similar items in that size, which connects to improvement 4. | same |
| A small `openChat()` event lets any page open the chat and optionally send a question. | `frontend/src/chatEvents.ts` |

The chips say "this" and the agent works out which product from the page context (Problem 8). The same short chips work on every product page.

### 3. Size-aware search

| Part | Where |
|---|---|
| `search_products(…, size=)` accepts "M", "medium", "2XL" and so on. It returns only products in stock in that size, and each result's `size_quantity` shows how many are left in that size. `SearchResult.size` and `note` (for sizes we don't carry). | `backend/tools.py`, `backend/models.py` (`ProductHit`, `SearchResult`) |
| The page results panel (Problem 7) uses the same filtered search, so the cards on the page are only items in the shopper's size. | automatic, via `last_search` |
| Prompt: pass the shopper's size whenever they've mentioned one (in this message or earlier), and say the size in the reply. | `backend/prompts/prompt.md` ("Shopping by size") |

### 4. Similar in-stock items when sold out

| Part | Where |
|---|---|
| New tool `find_similar(product, size?, limit)`. It scores other in-stock products: same category +3, each shared color +1 ("navy" = "navy blue"), each shared style tag +0.5 (ignoring tags nearly every product has, like "Yale"), and price within 15% +1. With a size, only items in stock in that size are included. | `backend/tools.py` |
| Returns `SimilarItems {source_product_id, source_name, size, source_in_stock_in_size, items: SimilarItem[]}`. Each item has `reasons` like "same category (Hoodies)", "also navy", "similar style: drawstring hood, kangaroo pocket", "same price". | `backend/models.py` |
| Prompt: when a size is sold out, or they ask for "something like this", call `find_similar` and offer 2–3 items with reasons. Never claim an alternative is in stock unless a tool returned it. | `backend/prompts/prompt.md` |
| **Safety net (added after testing):** if the agent offers alternatives but forgets to attach them as cards, the backend attaches the `find_similar` results, so the shopper can always click through. | `backend/agent.py` (`run_chat`) |

---

## Checks in the running app

All checks ran against the live site at `localhost:5173`: the Vite dev server, plus the backend started with `uvicorn main:app --reload --port 8000` from `backend/`. Chats ran as a guest, so nothing was saved. Final run: **18/18 passed.**

| # | Check | Result |
|---|---|---|
| 1 | `/api/products`: every product has `category` (6 categories, 102 total) and `sizes_in_stock` | ✓ |
| 1 | Hoodies in stock in M (what `/products?category=Hoodies&size=M` shows) | 21 |
| 1 | The running dev server serves the new filter UI ("My size", "In stock only", "Price: low to high", "Jackets & Fleece"), and the filtered URL loads the app | ✓ ✓ |
| 2 | The running chat widget has the page-aware chips; the product page has "Ask about this item" and "Find similar in …" | ✓ ✓ |
| 2 | Chip "Is this in stock in M?" on the Basic Hoodie page | "Yes — we have **M** in stock, with **only 5 left**…" (database: M = 5) ✓ |
| 2 | Chip "What colors does this come in?" on the Branford page | "heather gray, green, yellow, blue, and white" ✓ |
| 3 | "do you have hoodies in medium?" | "We have **21 hoodies in stock in M** — they're on the page now…" The page panel has 21 cards, every one in stock in M ✓✓✓✓ |
| 3 | "I'm an XL. any quarter-zips?" | "**9 quarter-zips in stock in XL**…" All page cards have XL ✓ |
| 4 | "is this in stock in large?" on the Fencing hoodie page (L sold out) | "Sorry, **L is sold out**… Similar navy hoodies with L in stock: Crew Left Chest Hoodie, 8 left in L; Squash Left Chest Hoodie, 25 left; The Forest School Hoodie, only 2 left". 3 cards, each confirmed to have L in stock through `/api/products/<id>` ✓✓✓ |
| 4 | The "Find similar in S" button's message on the Morse tee page (S sold out) | 4 college logo tees, all confirmed to have S in stock ✓ |
| 4 | Chip "Show me similar items" on the Branford quarter-zip page | 4 other college quarter-zips ($72) ✓ |

**What testing turned up:**
- **First run, 16/18.** For the Fencing hoodie, the agent named the right alternatives in its text but left `product_ids` empty, so no cards appeared. The backend safety net in improvement 4 fixed it, and the re-run passed 18/18.
- **Second run answered in about 1 second** (the first took 4–6 seconds) with word-for-word the same replies. This suggests Portkey returned cached model responses for identical requests. The tools still ran on our side each time; that's how the safety net found the `find_similar` results. A change in stock would change the tool results and so the request, which would get a fresh answer.
- **Build:** `npm run build` (type-check plus production build) passed.

**Not checked on screen:** clicking the new filters, chips and buttons in a real browser. The Chrome extension was not connected. The running dev server was confirmed to serve the new components, and every chat path they trigger was tested through the live API above. To see them: open `http://localhost:5173/products`, choose **Hoodies** and **M**; then open the Fencing Left Chest Hoodie and click **Find similar in L**.
