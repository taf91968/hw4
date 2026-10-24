# Campus Customs — Storefront Design (Problem 10)

Goal: make the site feel like a real, trustworthy Campus Customs store, so shoppers stay longer and buy.

## What changed and why

| Area | Change | Why it helps shoppers stay and buy |
|---|---|---|
| **Font** | **Open Sans** everywhere (self-hosted through `@fontsource-variable/open-sans`, no Google request). 16 px body text, line height 1.6. | Open, very legible letters, even small on phones. Prices, sizes and stock numbers read at a glance. Self-hosting is faster and keeps shoppers' data private. |
| **Color** | Black and pink replaced with **Yale Blue `#00356B` and white**: a blue nav bar and buttons, a light gray-blue page (`#F6F8FB`), near-black navy text, and a lighter blue (`#286DC0`) for links and focus. Stock has its own colors, always paired with words: **green** in stock, **amber** low stock, **gray dashed** sold out. | Yale Blue is the color shoppers already connect with Yale gear, so the store feels official. Calm blue on white reads as stable and safe for a purchase. Stock colors answer "can I get my size?" before anyone reads a word. All main text meets WCAG AA contrast (body 16:1, prices 12:1, muted 5.9:1). |
| **Hierarchy** | One clear order on every page. **Product cards:** category label → name → price in bold blue → 2-line description → size row. **Product page:** breadcrumb → name → price (30 px) → stock summary pill ("In stock in 4 of 6 sizes") → description → **Ask about this item** → colors → sizes. Section headings at 1.65 rem, uppercase small labels for groups. | Shoppers find the price and their size in seconds, the two things that decide a purchase. Breadcrumbs (Home › Products › Hoodies › item) make it easy to keep browsing instead of leaving. |
| **Storefront presentation** | **Brand:** shield "CC" logo and wordmark (CAMPUS CUSTOMS · NEW HAVEN · YALE GEAR), plus a matching favicon. **Top bar:** "Yale gear from New Haven · Sizes XS–XXL with live stock · Ask our shopping assistant". **Home page:** a blue hero with three real product photos, a strip of 4 trust facts, **Shop by category** tiles with photos and counts, **Campus favorites**, and an "Not sure about your size?" banner that starts the chat. **Footer:** shop links by category plus help links. | It looks and works like a real store, not a demo. Category tiles put every product two clicks from the home page. Every trust claim is true: no invented shipping, returns or discounts, because a promise the shop can't keep loses trust fast. |
| **Product cards** | White cards with a soft shadow; the photo zooms slightly on hover. Badges for sold out and "Only XL & XXL left". Crossed-out sold-out sizes. Gray placeholder cards while products load. | Hover feedback says "this is clickable". Low-stock badges create honest urgency. Placeholders stop the page from jumping while it loads, which feels polished and fast. |
| **Motion** | Short and subtle (0.2–0.45 s, ease-out): pages fade up, cards appear one after another, hero photos float in, the product photo eases in. The chat button rises in, and the chat panel scales up from the corner. Every animation is switched off for shoppers who turn on "reduce motion". | Motion guides the eye to what's new (results, the opened chat) without slowing anyone down, and gives a finished, production feel. Respecting reduce-motion keeps it comfortable for everyone. |
| **Chat** | **Launcher:** a blue "Ask us" pill with a chat icon. **Header:** "CC" avatar, "Campus Customs assistant", and a green dot with "Live stock · replies in a few seconds". **Messages:** shopper bubbles in Yale Blue, assistant bubbles white with a shadow and blue bold, each fading in, with blue typing dots. Question chips styled as blue pills. Rounded input and Send button. Product cards in chat move slightly on hover. | It feels like talking to the store's own staff, not a generic bot, which builds trust. The status line sets an honest expectation (replies took 3–7 s in testing). Clear bubbles and one-tap chips make it quick to get size and stock answers, often the last step before buying. |
| **Forms** | Log in and Create account cards with a Yale Blue top border; inputs get a blue focus ring; errors in red on a light red background. | Account pages look as trustworthy as the rest of the store. Clear focus and error states make sign-up quicker, and logged-in shoppers' chats are saved. |

## Files

`frontend/src/index.css` (full restyle: design tokens, type scale, motion, reduced-motion), `components/BrandMark.tsx`, `NavBar.tsx` (announcement bar and logo), `Footer.tsx`, `pages/Home.tsx` (hero, trust strip, categories, favorites, assistant banner), `ProductCard.tsx` (badges, category label, loading placeholder), `pages/ProductPage.tsx` (breadcrumbs, stock pill, colored sizes, assurances), `ChatWidget.tsx` (launcher, header), `App.tsx` (page fade and footer), and `index.html` (favicon, theme color).

## Notes

- This overrides the black-and-pink default in `AGENTS.md`, because this problem asked for Campus Customs brand colors that feel stable and trustworthy.
- **Checked:**
  - `npm run build` passed.
  - The running dev server serves the Open Sans font file (`font/woff2`), the Yale Blue tokens (no pink left) and every new component.
  - All 8 home-page photos load.
  - Contrast was checked with the WCAG formula. The sold-out gray was darkened from 3.1:1 to 5.0:1 after that check. The crossed-out size chips on cards are intentionally faint (3.5:1); the card reads the in-stock sizes aloud to screen readers.
- **Seen on screen later (Problem 11):** headless Edge is blocked on this computer (exit code 21), so the design was first checked only through the build and the dev server. In Problem 11, Chrome driven by Playwright worked, and its screenshots (`output/app_check_images/`) showed the design working. They also turned up two layout bugs, now fixed: white gaps around the announcement bar, and a squeezed footer copyright line.
