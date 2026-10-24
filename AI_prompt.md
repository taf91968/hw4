# AI Prompt Log — Homework 4

This file records the instructions I type to the AI while completing Homework 4. It is a log of vibe-coding requests and is not a runtime prompt file for scripts.

## Instructions

### 1. Initial assignment instruction

- Prompt typed in my own words: Starting Homework 4 - don't forget AI_prompt.md before starting the assignment
- AI instructions requested: Set up a Homework 4 folder with its own `AI_prompt.md` log and record each prompt I type as I work through the assignment. Do not begin Problem 1 until I explain in my own words what I want done.
- What was lacking after the first prompt: Not applicable; this is the first prompt for Homework 4.

### 2. Homework 4 project and data files

- Prompt typed in my own words: I will be creating a real customer website for Campus Customs . I will be building a react +Vite TypeScript  front end  and a Python Fast API  backend whose brain is a PydanticAI agent. https://zlisto.github.io/mgt_409_fa26/data/hw4/data.zip here is the data file for this
- AI instructions requested: Download the Homework 4 data and add it to the homework folder. The project will be a Campus Customs customer website with a React + Vite + TypeScript frontend and a Python FastAPI backend powered by a PydanticAI agent. The zip was extracted to `hw4/data/` and contains `products/` (102 product photos) and `campus_customs.db`, a SQLite database with four tables: `catalogue` (102 products with name, garment type, description, colors, search tags, image path, and price), `inventory` (612 rows of stock by product and size, XS–XXL), `users` (3 accounts with hashed passwords), and `chat_messages` (22 saved chat turns, including the products shown with each answer).
- What was lacking after the first prompt: Not applicable.

## Problem-by-Problem Log

Complete one section for each problem. Record the problem title, the prompt typed in my own words, the AI instructions requested, and, when applicable, one sentence describing what was missing after the first prompt.

### Problem 1: Create the AI prompt log

- Prompt typed in my own words: For problem 1 you created the AI_prompt.md at the start which is what you did
- AI instructions requested: Count the `AI_prompt.md` set up at the start of Homework 4 (Instructions #1) as the Problem 1 deliverable. The log records every prompt I type in my own words, the AI instructions requested, and what was lacking after the first prompt, and it will be kept up to date for every later problem.
- What was lacking after the first prompt: Not applicable; the log was already created by the first Homework 4 prompt.

Output evidence: `AI_prompt.md`

### Problem 2: Understand the database and start the harness

- Prompt typed in my own words: Problem 2 is to look at the database data/campus_customs.db  and understand each table which i did and start the file output/harness.md -  I see you already wrote down each table and its fields including why each field matters for the shop or the chatbot
- AI instructions requested: Study each table in `data/campus_customs.db` and start `output/harness.md` with every table and field, including why each field matters for the shop or the chatbot. The AI had only summarized the tables in chat, not written the field-by-field reasons, so it wrote them in `output/harness.md` Part 1: the four tables (`catalogue`, `inventory`, `users`, `chat_messages`) plus `sqlite_sequence`, how the tables link, a table per field with type, example, and shop and chatbot reasons, and what the 22 saved chats show the agent must do. Data issues noted for later problems: `garment_type` values are inconsistent (22 variants), `colors` and `search_tags` are stored as JSON text, 145 of 612 size rows are sold out, foreign keys are not enforced by default, and password hashes use PBKDF2-SHA256 and must never reach the agent or frontend.
- What was lacking after the first prompt: The earlier chat summary listed the tables and row counts but did not explain each field or why it matters, and it was not saved to `output/harness.md`.

Output evidence: `output/harness.md` (Part 1)

### Problem 3: Scaffold the website frontend and product backend

- Prompt typed in my own words: Problem 3  I need you to scaffold a React + Vite + TypeScript front end for Campus Customs with a nav bar at the top that links to the main pages: Home, Products, About Us, Log in and Create account. On the product page show product images from the catalog (use image paths in the database) with basic product info (name, price, short description)  - Each product open a single-item page (large image on one side, full product text on the other - description, price, sizes/stock when its there) Clicking a card on Products should take the shopper there. - add a chat interface inthe bottom right of the site. ( a floating chat panel is fine) It doesnt need to talk to an agent yet. - start a fastAPI app in backendd/main.py just to serve products and images, then grow it into the agent backend in Problem 5
- AI instructions requested: Build a React + Vite + TypeScript frontend in `frontend/` with a top nav bar (Home, Products, About Us, Log in, Create account). The Products page shows each catalogue photo, using the database's image path, with name, price, and a short description. Clicking a card opens a single-item page with a large image on one side and the full description, price, colors, and sizes/stock on the other. Add a floating chat panel in the bottom right that does not call an agent yet. Start a FastAPI app in `backend/main.py` (the AI used `backend/`, correcting the "backendd" typo) that serves products and photos only, to grow into the agent backend in Problem 5. The AI split the backend into `main.py` (routes), `db.py` (read-only database helpers the agent can reuse), and `models.py` (Pydantic `SizeStock`, `ProductSummary`, `ProductDetail`). It served only `data/products/` so the database file can't be downloaded, used the black-and-pink style from `AGENTS.md`, added a product search box and simple Log in / Create account forms (not connected yet), and documented it all in `output/harness.md` Part 2.
- What was lacking after the first prompt: Not applicable.

Code evidence: `backend/main.py`, `backend/db.py`, `backend/models.py`, `frontend/src/`
Output evidence: `output/harness.md` (Part 2)

### Problem 4: Create account and log in

- Prompt typed in my own words: Problem 4 - now will build a create-account  (first name, last name, email, password( confirm password is a nice touch)  and log in (email and password) - seed database has a test user available to use while building: Email: Test@campuscustoms.yale.edu, Password: password, Hash function: PBKDF2-HMAC-SHA256, 120,000 iterations (stored as pbkdf2_sha256$salt$hash)
- AI instructions requested: Build a working Create account page (first name, last name, email, password, confirm password) and Log in page (email, password) backed by the `users` table. Hash new passwords with PBKDF2-HMAC-SHA256 at 120,000 iterations, stored as `pbkdf2_sha256$salt$hash` to match the seed data, and test with the seed test user. The AI first recomputed the test user's stored hash to confirm the format (salt used as text), then added `backend/auth.py` and four routes (`signup`, `login`, `logout`, `me`), with an HttpOnly signed session cookie, emails lowercased so `Test@...` matches the stored `test@...`, the same error for wrong email and wrong password, and a 5-failure lockout. On the frontend it added shared login state, real forms with error messages and a live password-match check, a nav bar showing "Hi, first name" and Log out, and a chat greeting by name. It backed up the original database to `data/campus_customs.seed.db`, added `SESSION_SECRET` to `.env.example`, ran 21 account tests on a copy of the database (all passed), and documented it in `output/harness.md` Part 3.
- What was lacking after the first prompt: Not applicable.

Code evidence: `backend/auth.py`, `backend/main.py`, `backend/models.py`, `frontend/src/auth.tsx`, `frontend/src/pages/Login.tsx`, `frontend/src/pages/CreateAccount.tsx`
Output evidence: `output/harness.md` (Part 3)

### Problem 4 follow-up: How login checks a password, and the live login check

- Prompt typed in my own words: How login checks a password: YOu never un-hash the stored value. You re-hash what the user typed and compare, read the salt out of the stored string - do not make a new one at login, Hash the typed password with that same salt, then ompared to the stored hash. Use a constant-time compare. signup and login must the same hash settings. If they are different, even the right password will not match. Surest check: log in as the seeded test user and as a brand-new account you just created in your app. confirm you can log in as that user and that a brand new account you just created also works.
- AI instructions requested: Confirm that login re-hashes the typed password with the salt read from the stored string (no new salt at login), compares with a constant-time compare, and uses the same hash settings as signup. Then prove it on the live app by logging in as the seeded test user and as a brand-new account created in the app. The AI showed the code already worked this way: one shared `hash_password` function with `ITERATIONS = 120_000` for both signup and login, the salt split out of the stored string, and `hmac.compare_digest`. It added these steps to `output/harness.md`. It then ran the check through the website on the real database. The test user logged in. A new account (`newshopper.check@campuscustoms.yale.edu`) was created, logged out, and logged back in. Wrong passwords failed for both, and re-hashing each password by hand with its stored salt matched. The new account was left in the database as evidence.
- What was lacking after the first prompt: The first Problem 4 tests created the new account on a copy of the database, not in the running app, and the harness did not spell out the steps login uses to check a password.

Output evidence: `output/harness.md` (Part 3.3 and 3.6)

### Problem 4 follow-up: Document how auth works

- Prompt typed in my own words: Update  output/harness.md with how auth works ( what is stored for a user and how passwords are protected)
- AI instructions requested: Rewrite `output/harness.md` section 3.3 as one "How auth works" section. It shows what is stored for a user, using the real stored row of the new account (user 4) column by column. It lists what is never stored (the password, confirm password, and sessions) and what leaves the backend (`PublicUser` only, never the hash). It explains how passwords are protected: signup steps (length check, a new random salt per account, PBKDF2-HMAC-SHA256 × 120,000, stored format), login steps (read the salt from the stored string, re-hash, constant-time compare), and a table of the other protections and what each stops, including that HTTPS is still needed before deployment. The earlier scattered password bullets were merged into this section.
- What was lacking after the first prompt: The earlier harness explained the password check but had no single place showing what is stored for a user, what is never stored, and why each protection exists.

Output evidence: `output/harness.md` (Part 3.3)

### Problem 5: Shop chatbot as a PydanticAI agent behind FastAPI

- Prompt typed in my own words: Problem 5 - Build the shop chatbot as a PydanticAI agent behind FastAPI, plugged into your front-end chat widget. put the API app in backend/main.py - that is the file run with Uvicorn. Keep the agent as these 4 files next to it: Backend/prompts/prompt.md - system prompt, backend/agent.py - agent entry/wiring, backend/tools.py - tools the agent can call, backend/models.py - pydantic/PydanticAI structured types. In main.py expose a chat route so a message from the website returns a reply from the agent.- need AI model API key for the agent . Put Campus Customs voice and safety basics into prompts/prompt.md  - start or update types in models.py for chat replies/product cards as needed. in output/harness.md, note how the front end talks to FastAPI and how the agent is loaded (prompt file + model) , make sure the backend runs from the backend/ folder like this: uvicorn main:app  --reload --port 8000
- AI instructions requested: Build the shop chatbot as a PydanticAI agent behind FastAPI and connect it to the website's chat widget. Use `backend/main.py` as the Uvicorn app with a chat route, and keep the agent in four files: `backend/prompts/prompt.md` (system prompt with Campus Customs voice and safety basics), `backend/agent.py` (wiring), `backend/tools.py` (tools), and `backend/models.py` (types for chat replies and product cards). Use an AI model API key. Document in `output/harness.md` how the frontend talks to FastAPI and how the agent is loaded. Make the backend run from `backend/` with `uvicorn main:app --reload --port 8000`. What the AI did:
  - Found `PORTKEY_API_KEY` already set as a Windows user environment variable (no `.env` existed) and used it with `gpt-5.6-luna` through Portkey, the same setup as Homework 3. The key was never printed.
  - Switched the backend files to plain imports so Uvicorn can run from `backend/`.
  - Added three tools: keyword search with shopper-word synonyms and partial-match flags, product details with stock by size, and a category overview.
  - Added `POST /api/chat` and `GET /api/chat/history`. Logged-in chats are saved to `chat_messages` with the products shown; guest history stays in the browser.
  - Only products a tool actually returned can become cards, and cards are rebuilt from the database, so prices can't be made up. Each message is capped at 6 model calls.
  - Built the chat widget with Markdown replies, mini product cards linking to product pages, typing dots, and error messages, and sent the current product page to the agent.
  - Tested 15 conversations with the real agent. Fixed two problems: "gym shorts" was matching "short-sleeve" tees, and Azure's content filter turned a jailbreak message into a 502 error (now a polite decline).
- What was lacking after the first prompt: Not applicable.

Prompt evidence: `backend/prompts/prompt.md`
Code evidence: `backend/main.py`, `backend/agent.py`, `backend/tools.py`, `backend/models.py`, `backend/db.py`, `frontend/src/components/ChatWidget.tsx`, `frontend/src/components/Markdown.tsx`
Output evidence: `output/harness.md` (Part 4)

### Problem 6: Real lookups for description, price and stock

- Prompt typed in my own words: Problem  6 Look up real information from Campus_custom.db - Product description, Price and How many are in stock  (by size when the customer asks) Expand prompts/prompt.md - call tools for price and stock quesions. Add or update return types in models.py - List each tool and explain which models fields for look up, results and why in output/harness.md
- AI instructions requested: Make the agent look up real product descriptions, prices, and stock (by size when asked) from `campus_customs.db`. Expand `prompts/prompt.md` so it calls tools for price and stock questions. Add or update return types in `models.py`. In `output/harness.md`, list each tool with its lookup fields, result model fields, and why. What the AI did:
  - Added typed tool results to `models.py`: `SizeAvailability` (size, quantity, and in stock / low stock / sold out), `ProductHit`, `SearchResult`, `ProductInfo`, `StockCheck`, `CategorySummary`, and `CategoryOverview`.
  - Rewrote `tools.py` so every tool returns one of these models.
  - Added a new `check_stock` tool that understands shopper sizes ("medium", "2XL", "extra small") and returns a note, not an error, for sizes we don't carry like 3XL.
  - Let tools accept an exact product name as well as an ID, and suggest the 3 closest matches when nothing matches.
  - Added a "Looking up descriptions, prices and stock" section to the prompt: a question → tool table, re-check stock and prices every time, exact prices, size-first stock answers, and no made-up fabric or fit details.
  - Tested 11 questions with the real agent. A lookup tool was called every time and every number matched the database. The one failed text check was the test's own pattern, not a wrong answer.
- What was lacking after the first prompt: Not applicable.

Prompt evidence: `backend/prompts/prompt.md` (Looking up descriptions, prices and stock)
Code evidence: `backend/tools.py`, `backend/models.py`
Output evidence: `output/harness.md` (Part 5)

### Problem 7: Chat search results appear on the page as product cards

- Prompt typed in my own words: Problem 7 - add a neat feature to the site - when a customer askes about a type of item  - for example " what hoodies do you have?' the agent should search the catalog and the website should dynamically show those matching items as product cards.( image,name price and short info) . After the dynamic product cards are loaded by your new feature make sure the same single-item page behavior you build in problem 3 still works: each product card - including the ones chat just put on the page - should still open the detail view ( large image + full info) when clicked.  update prompts/prompt.md and output/harness.md so its clear how search results reach the page
- AI instructions requested: When a shopper asks about a type of item, have the agent search the catalogue and have the website show the matches as product cards (image, name, price, short info) on the page. Keep the Problem 3 behavior: every card, including the ones the chat adds, opens the single-item page with a large image and full info. Update `prompts/prompt.md` and `output/harness.md` to explain how search results reach the page. What the AI did:
  - **Model fields:** added `page_title` to the agent's output; the agent sets it only when the shopper is browsing.
  - **Search memory:** `search_products` now saves every match from the latest search, not just the 8 the model sees.
  - **Page results:** `PageResults` is built from that search straight from the database (up to 24) and returned in `ChatResponse`. The model chooses whether to show results; the database decides which cards appear.
  - **Website:** a shared results context and a "From the shopping assistant" panel at the top of every page. The panel uses the same `ProductCard` component as the Products page, so clicks open the same single-item page.
  - **On the detail page:** the panel folds to its header so the large image comes first, and each page starts at the top.
  - **Prompt:** added a section on when to set `page_title`, what to write in the reply, and when to leave the page alone.
  - **Tests:** 9 of 9 checks passed on the live site. All 35 chat-added cards were checked to open a working single-item page with matching data and photos.
- What was lacking after the first prompt: Not applicable.

Prompt evidence: `backend/prompts/prompt.md` (Showing search results on the page)
Code evidence: `backend/models.py`, `backend/tools.py`, `backend/agent.py`, `frontend/src/chatResults.tsx`, `frontend/src/components/ChatResults.tsx`, `frontend/src/components/ChatWidget.tsx`
Output evidence: `output/harness.md` (Part 6)

### Problem 8: Saved chat history, who is chatting, and page context

- Prompt typed in my own words: Problem 8 - when a shopper is logged in , save their chat history in the database in an appropriate table and reload it when they return. the agent should know who is chatting  (name, email) put that in agent deps, and/or tools the agent can call.- pass enough page content that if someone is on a product page  and asks " do you have this in pink?" the agent knows which item they mean. - can put code in agent context . GUests can still chat, but history only needs to presist for logged in users. Document in outputs/harness.md: how user chat history is stored, what customer field the agent sees, and how page context is passed
- AI instructions requested: Save logged-in shoppers' chat history in a suitable database table and reload it when they return. Make the agent know who is chatting (name and email) through deps and/or tools. Send enough page content that "do you have this in pink?" on a product page refers to the right item. Guests can still chat without saved history. Document how history is stored, which customer fields the agent sees, and how page context is passed. What the AI did:
  - **History:** kept using the seed database's `chat_messages` table, which already had user, role, text, products shown, and time. On return, the widget shows the saved chat followed by a "Welcome back" greeting.
  - **Who is chatting:** the agent's per-message context now includes the shopper's full name and email (it previously had only the first name). Added a `get_shopper` tool (name, email, member since, saved message count). The ID stays in code only, and the password hash never reaches the agent.
  - **Page context:** the chat widget now sends a `PageContext` (path, page type, open product, results panel title and product IDs) instead of just a product ID. The backend looks each product up and writes it into the agent's context with price and colors, in numbered order. Added a `get_current_page` tool.
  - **Prompt:** added rules for using the shopper's details, resolving "this" and "the third one", and naming near-match colors honestly ("dusty coral", not pink).
  - **Tests:** 13 of 13 checks passed on a copy of the database. A live guest test worked. The documentation went in `output/harness.md`, the existing file, not a new `outputs/` folder.
- What was lacking after the first prompt: Not applicable.

Prompt evidence: `backend/prompts/prompt.md` (Who you're talking to and what's on their screen)
Code evidence: `backend/agent.py`, `backend/tools.py`, `backend/models.py`, `backend/db.py`, `backend/main.py`, `frontend/src/components/ChatWidget.tsx`
Output evidence: `output/harness.md` (Part 7)

### Problem 9: Usability improvements

- Prompt typed in my own words: Problem 9 lets improve core shop works. choose and implement : 2 front-end usability improvements, 2 agent/backend usability improvements - write output/usability.md before or as you build. for each of the improvements say what you added and why it helps a Campus Customs shopper or the business - makes sure all improvements actually show up in the running app.
- AI instructions requested: Choose and build two front-end and two agent/backend usability improvements. Write `output/usability.md` before or while building, saying for each what was added and why it helps a Campus Customs shopper or the business. Make sure all four show up in the running app. The AI wrote `output/usability.md` as a plan first, then built:
  1. **Front end — shop by category, size, and price:** a filter bar on the Products page with 6 clean categories (mapped from the 22 inconsistent `garment_type` spellings), a "My size" picker, an in-stock switch, and sort. Filters are kept in the URL, and each card has a size row.
  2. **Front end — question chips and "Ask about this item":** suggested questions in the chat that change with the page, an "Ask about this item" button, and "Find similar in [size]" links under sold-out sizes.
  3. **Agent/backend — size-aware search:** `search_products(size=…)` returns only items in stock in the shopper's size, and the page results follow the same filter.
  4. **Agent/backend — similar in-stock items:** a new `find_similar` tool that scores items by category, color, style, and price, and gives the reasons for each match.

  Testing against the running app passed 16/18 at first. The agent once listed alternatives without attaching cards, so the AI added a backend safety net that attaches them, and the re-run passed 18/18. It also noted that Portkey seems to cache identical requests, and that the new controls could not be clicked on screen because the Chrome extension was not connected.
- What was lacking after the first prompt: Not applicable.

Prompt evidence: `backend/prompts/prompt.md` (Shopping by size; When something is sold out, offer alternatives)
Code evidence: `frontend/src/pages/Products.tsx`, `frontend/src/components/ProductCard.tsx`, `frontend/src/components/ChatWidget.tsx`, `frontend/src/pages/ProductPage.tsx`, `frontend/src/chatEvents.ts`, `backend/tools.py`, `backend/models.py`, `backend/db.py`, `backend/agent.py`
Output evidence: `output/usability.md`, `output/harness.md` (Part 8)

### Problem 10: Storefront design

- Prompt typed in my own words: Problem 10 add creative design so the site feels like a real Campus Customs Storefront - use font that is easily readable, high clarity  like Open Sans and Color should be in Campus Customs brand colors but feel stable and trustworthy, heirarchy, motion production presentation and chat feel.  write output/design.md - what you changed and why it should help customs stick around and buy. Keep it concrete and short
- AI instructions requested: Redesign the site so it feels like a real Campus Customs storefront. Use a clear, readable font like Open Sans and Campus Customs brand colors that feel stable and trustworthy, and work on hierarchy, motion, presentation, and how the chat feels. Write a short, concrete `output/design.md` on what changed and why it should help customers stay and buy. What the AI did:
  - **Font:** self-hosted Open Sans with `@fontsource-variable/open-sans`, installed with OneDrive paused.
  - **Colors:** replaced black and pink with Yale Blue `#00356B` and white, plus green, amber, and gray for in stock, low stock, and sold out (always with words). This overrides the `AGENTS.md` default because the prompt asked for brand colors.
  - **Brand and layout:** a "CC" shield logo, favicon, announcement bar, and footer. A new home page with a hero of real product photos, a strip of true trust facts, category tiles, Campus favorites, and an assistant banner.
  - **Product pages and cards:** breadcrumbs, a stock summary pill, and color-coded sizes on product pages. Badges, category labels, and loading placeholders on cards.
  - **Motion:** subtle animations, all switched off when the shopper has "reduce motion" turned on.
  - **Chat:** a restyled panel with an "Ask us" launcher, assistant header, Yale Blue bubbles, and blue question chips.
  - **Accuracy:** removed two product-page lines that promised more than the shop can back up.
  - **Checks:** contrast checked with the WCAG formula, and the sold-out gray darkened to pass. The build passed, and the running dev server was confirmed to serve the font, colors, components, and photos. Screenshots weren't possible because headless Edge is blocked on this computer and the Chrome extension wasn't connected.
- What was lacking after the first prompt: Not applicable.

Code evidence: `frontend/src/index.css`, `frontend/src/components/BrandMark.tsx`, `frontend/src/components/NavBar.tsx`, `frontend/src/components/Footer.tsx`, `frontend/src/pages/Home.tsx`, `frontend/src/components/ProductCard.tsx`, `frontend/src/pages/ProductPage.tsx`, `frontend/src/components/ChatWidget.tsx`
Output evidence: `output/design.md`

### Problem 11: Test the live site and document it in app_check.html

- Prompt typed in my own words: Problem 11 - Test the live site and document it in output/app_check.html. (a page you can double click) - include clear screenshots and short captions for: 1. Chat checking the inventory level of an item ( honest stock /price from the DB) 2. The dynamic search-result cards appearing after a category question 3. one of the usability features you added in problem 9 . Make the HTML easy to grade: heading for each check, screenshot one or two sentences on what the screenshot proves. - put the screenshot images file in output/app_check_images/ and link them from app_check.html with relative paths (for example app_check_images/inventory.png)
- AI instructions requested: Test the live site and document it in `output/app_check.html`, a page that opens with a double-click. Include clear screenshots with short captions for three checks: the chat checking an item's inventory honestly against the database, the dynamic search-result cards after a category question, and one Problem 9 usability feature. Give each check a heading and one or two sentences on what its screenshot proves. Save the images in `output/app_check_images/` and link them with relative paths. What the AI did:
  - **Screenshot tool:** headless Edge and plain headless Chrome screenshots didn't work on this computer, so the AI installed Playwright in a temporary environment outside the project and used it to drive the installed Chrome. The script is saved as `scripts/app_check_shots.py`.
  - **Testing:** the script used the running site like a guest shopper (clicking, typing, and waiting for real agent replies) and compared each result with the database.
    - **Inventory:** the chat said 5 left in M at $68; the database had M = 5 and $68.
    - **Search cards:** "Hoodies · Showing 24 of 27", all hoodies, and the clicked card opened its single-item page.
    - **Size filter:** exactly the 21 hoodies the database has in stock in M.
    - **Bonus:** "Find similar in L" returned four alternatives, each confirmed to have L in stock.
  - **Bugs found and fixed:** the screenshots showed two layout bugs (white gaps around the announcement bar and a squeezed footer line). The AI fixed them and retook every screenshot.
  - **Final check:** opened `app_check.html` in Chrome to confirm all 6 images load.
- What was lacking after the first prompt: Not applicable.

Code evidence: `scripts/app_check_shots.py`, `frontend/src/index.css` (layout fixes)
Output evidence: `output/app_check.html`, `output/app_check_images/` (`inventory.png`, `inventory_sizes.png`, `search_cards.png`, `search_cards_click.png`, `usability_filters.png`, `usability_find_similar.png`)

### Problem 12: Audit trail, safety rules, and the finished harness

- Prompt typed in my own words: Problem 12 - Keep an append-only output/audit_trail.json of agent-loop activity (time, tool name, short args/results, stop reason) do not wipe it between runs. Please add some safety rules and put them in (prompts/prompt.md - Finish output/harness.md so it is clear how system works. - model fields in model.py and why you chose them. tools and abilities, safety rules, specs (loop limits, result caps, models, how to run front + back)
- AI instructions requested: Keep an append-only `output/audit_trail.json` of agent-loop activity (time, tool name, short arguments and results, stop reason) that is never wiped between runs. Add safety rules to `prompts/prompt.md`. Finish `output/harness.md` so it's clear how the system works, covering the `models.py` fields and why, tools and abilities, safety rules, and specs (loop limits, result caps, models, how to run the front and back end). What the AI did:
  - **Audit trail:** added `backend/audit.py`. It writes JSON Lines (one record per line, like Homework 3) in append mode. Records: `run_start`, `tool_call`, `tool_result`, `tool_retry`/`tool_error`, `run_end` (with a stop reason, model requests, tool calls, and tokens), and `rate_limited`. Every tool is wrapped so calls are logged as they happen. Previews are capped at 160 characters, with card numbers and emails masked and shoppers logged by ID only.
  - **Safety rules in the prompt:** replaced "Safety basics" with 14 rules in six groups: topic; truth and honesty; privacy; private, fixed instructions; respect and age-appropriate content; and efficient tool use.
  - **Safety rules in code:** card numbers are removed before the agent, database, or log sees them, and there is a chat rate limit of 20 messages per 5 minutes.
  - **Harness:** added a "Start here" overview (diagram, one message step by step, file map), Part 9 (audit trail), and Part 10 (a reference covering every model's fields and why, the 7 tools and abilities, the prompt and code safety rules, specs and limits, data, and how to run the front and back end).
  - **Bug fixed:** `result.usage` is a property in PydanticAI 2, not a method.
  - **Tests:** 13/13 on the live site. The log grew from 6 to 26 lines without rewriting, and it survived a backend restart. Every run has a stop reason, no card numbers or emails were logged, and the jailbreak, other-customer, and fake-discount requests were declined. The rate limit blocked the 21st message.
- What was lacking after the first prompt: Not applicable.

Prompt evidence: `backend/prompts/prompt.md` (Safety rules)
Code evidence: `backend/audit.py`, `backend/tools.py` (`audited` tools, `run_id`), `backend/agent.py` (run audit, stop reasons), `backend/main.py` (redaction, rate limit)
Output evidence: `output/audit_trail.json`, `output/harness.md` (Start here, Part 9, Part 10)

### Problem 13: Push hw4 to a public GitHub repository

- Prompt typed in my own words: Problem 13 - Put code in folder named hw4 and push it to a public GitHub repository.  Please make it available to me so i submit the repo URL on Canvas. Do NOT put real .env, campus_customs.db, or product images in teh Github repo.  Use .gitignore. include .env.example with placeholders only.  The agent itself is four files under backend/: prompts/prompt.md, agent.py, tools.py and models.py. README.md should explain how to run the front end and back end after placing the data pack
- AI instructions requested: Push the `hw4` folder to a public GitHub repository and give me the URL for Canvas. Keep the real `.env`, `campus_customs.db`, and product images out by using `.gitignore`, and include `.env.example` with placeholders only. Keep the agent as four files under `backend/` (`prompts/prompt.md`, `agent.py`, `tools.py`, `models.py`). Write a `README.md` explaining how to run the front and back end after placing the data pack. What the AI did:
  - **`.gitignore`:** excludes `.env`, all of `data/` (the database, seed copy, and product photos), any `*.db`, Python caches and virtual environments, `node_modules`, the front-end build, and the local `.claude/` folder (it holds machine-specific paths).
  - **`.env.example`:** rewritten with placeholders only.
  - **`README.md`:** what's in the repo, the four agent files, how to download and place the data pack, `.env` setup, how to run the back end (`uvicorn main:app --reload --port 8000` from `backend/`) and the front end (`npm install`, `npm run dev`), the test account, things to try, troubleshooting, and where the documentation is.
  - **Checks before pushing:** reviewed every staged file (53, none forbidden) and scanned their contents for the real Portkey key, token patterns, and full password hashes (0 hits).
  - **Push:** created the public repository `hw4` on the GitHub account `taf91968` and pushed the `main` branch.
- What was lacking after the first prompt: Not applicable.

Output evidence: GitHub repository `hw4` (public), `README.md`, `.gitignore`, `.env.example`
