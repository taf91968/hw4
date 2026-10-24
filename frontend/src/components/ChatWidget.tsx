import { FormEvent, useEffect, useRef, useState } from "react";
import { Link, useLocation, useMatch } from "react-router-dom";
import { ApiError, type GuestTurn, fetchChatHistory, formatPrice, sendChat } from "../api";
import { useAuth } from "../auth";
import { onOpenChat } from "../chatEvents";
import { useChatResults } from "../chatResults";
import type { ChatTurn, PageContext, ProductCard } from "../types";
import Markdown from "./Markdown";

const MAX_CHARS = 1000; // matches MAX_MESSAGE_CHARS in backend/models.py
const GUEST_HISTORY = 12; // matches MAX_GUEST_HISTORY

/** A chat message; `local` marks greetings that only exist in the browser. */
type Message = ChatTurn & { local?: boolean };

const greeting = (firstName?: string, returning = false): Message => ({
  role: "assistant",
  content: returning
    ? `Welcome back, ${firstName}! Your earlier chat is above — pick up where you left off, or ask me anything new.`
    : `Hi${firstName ? `, ${firstName}` : ""}! I'm the Campus Customs shopping assistant. Ask me about our Yale gear — styles, colors, sizes or prices.`,
  products: [],
  local: true,
});

const PAGE_TYPES: Record<string, PageContext["page_type"]> = {
  "/": "home",
  "/products": "products",
  "/about": "about",
  "/login": "login",
  "/create-account": "create_account",
};

export default function ChatWidget() {
  const { user, loading: authLoading } = useAuth();
  const { results, show: showResults, clear: clearResults } = useChatResults();
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([greeting()]);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const listRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const { pathname } = useLocation();
  const productMatch = useMatch("/products/:productId");

  /** What the shopper can see, so the agent can resolve "this one" / "the third one". */
  function pageContext(): PageContext {
    const productId = productMatch?.params.productId ?? null;
    return {
      path: pathname,
      page_type: productId ? "product" : (PAGE_TYPES[pathname] ?? "other"),
      product_id: productId,
      results_title: results?.title ?? null,
      results_product_ids: results?.products.map((p) => p.product_id) ?? [],
    };
  }

  // On login/logout: logged-in shoppers get their saved chat back; guests start fresh.
  useEffect(() => {
    if (authLoading) return;
    setError(null);
    clearResults(); // a different shopper shouldn't see the last one's results
    if (!user) {
      setMessages([greeting()]);
      return;
    }
    fetchChatHistory()
      .then((saved) =>
        setMessages(saved.length ? [...saved, greeting(user.first_name, true)] : [greeting(user.first_name)]),
      )
      .catch(() => setMessages([greeting(user.first_name)]));
  }, [authLoading, user?.id, user?.first_name]);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight });
  }, [messages, open, sending]);

  useEffect(() => {
    if (open) inputRef.current?.focus();
  }, [open]);

  // Other parts of the site (e.g. "Ask about this item") can open the chat
  // and send a question. A ref keeps the listener using the latest send().
  const sendRef = useRef(send);
  sendRef.current = send;
  useEffect(
    () =>
      onOpenChat(({ message }) => {
        setOpen(true);
        if (message) void sendRef.current(message);
      }),
    [],
  );

  const suggestions = suggestedQuestions(Boolean(productMatch), Boolean(results), user?.first_name);

  function submit(event: FormEvent) {
    event.preventDefault();
    void send(draft);
  }

  async function send(raw: string) {
    const text = raw.trim();
    if (!text || sending) return;

    // Guests' history lives only in the browser, so send recent turns along.
    // Logged-in shoppers' history is loaded from the database by the backend.
    // (Greetings are skipped: they aren't part of the conversation.)
    const guestHistory: GuestTurn[] = user
      ? []
      : messages
          .filter((m) => !m.local)
          .slice(-GUEST_HISTORY)
          .map((m) => ({
            role: m.role,
            content: m.content,
            product_ids: m.products.map((p) => p.product_id),
          }));

    setMessages((prev) => [...prev, { role: "user", content: text, products: [] }]);
    setDraft("");
    setError(null);
    setSending(true);
    try {
      const res = await sendChat(text, pageContext(), guestHistory);
      setMessages((prev) => [...prev, { role: "assistant", content: res.reply, products: res.products }]);
      // "What hoodies do you have?" → the matching cards appear on the page.
      if (res.page_results && res.page_results.products.length > 0) showResults(res.page_results);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "We couldn't reach the shopping assistant. Please try again.",
      );
    } finally {
      setSending(false);
      inputRef.current?.focus();
    }
  }

  return (
    <div className="chat">
      {open && (
        <section className="chat-panel" aria-label="Shopping assistant chat">
          <header className="chat-header">
            <span className="chat-avatar" aria-hidden="true">
              CC
            </span>
            <span className="chat-title">
              <strong>Campus Customs assistant</strong>
              <span>Live stock · replies in a few seconds</span>
            </span>
            <button
              type="button"
              className="chat-close"
              onClick={() => setOpen(false)}
              aria-label="Close chat"
            >
              ×
            </button>
          </header>
          <div className="chat-messages" ref={listRef} aria-live="polite">
            {messages.map((m, i) => (
              <div key={i} className={`chat-turn chat-turn-${m.role}`}>
                <div className={`chat-bubble chat-${m.role}`}>
                  {m.role === "assistant" ? <Markdown text={m.content} /> : m.content}
                </div>
                {m.products.length > 0 && (
                  <ul className="chat-cards" aria-label="Products">
                    {m.products.map((p) => (
                      <ChatProductCard key={p.product_id} product={p} />
                    ))}
                  </ul>
                )}
              </div>
            ))}
            {sending && (
              <div className="chat-bubble chat-assistant chat-typing" aria-label="Assistant is typing">
                <span />
                <span />
                <span />
              </div>
            )}
            {error && (
              <p className="chat-error" role="alert">
                {error}
              </p>
            )}
          </div>
          {!sending && (
            <div className="chat-suggestions" role="group" aria-label="Suggested questions">
              {suggestions.map((q) => (
                <button key={q} type="button" className="chat-suggestion" onClick={() => void send(q)}>
                  {q}
                </button>
              ))}
            </div>
          )}
          <form className="chat-form" onSubmit={submit}>
            <label htmlFor="chat-input" className="visually-hidden">
              Message
            </label>
            <input
              id="chat-input"
              ref={inputRef}
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              placeholder="Ask about sizes, colors, prices…"
              autoComplete="off"
              maxLength={MAX_CHARS}
            />
            <button type="submit" className="button button-small" disabled={!draft.trim() || sending}>
              Send
            </button>
          </form>
        </section>
      )}
      <button
        type="button"
        className={open ? "chat-toggle is-open" : "chat-toggle"}
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        aria-label={open ? "Close chat" : "Open chat with the shopping assistant"}
      >
        {open ? (
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" aria-hidden="true">
            <path d="M6 6l12 12M18 6 6 18" />
          </svg>
        ) : (
          <>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinejoin="round" aria-hidden="true">
              <path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12Z" />
            </svg>
            <span className="chat-toggle-label">Ask us</span>
          </>
        )}
      </button>
    </div>
  );
}

/** One-tap questions that fit the page; the agent resolves "this" from page context. */
function suggestedQuestions(onProductPage: boolean, resultsShowing: boolean, firstName?: string): string[] {
  if (onProductPage) {
    return ["Is this in stock in M?", "What colors does this come in?", "Show me similar items"];
  }
  if (resultsShowing) {
    return ["Which of these are in stock in M?", "What's the cheapest one?", "Tell me about the first one"];
  }
  return [
    "What hoodies do you have?",
    "Anything under $40?",
    firstName ? "What was I looking at last time?" : "Show me Bulldog gear",
  ];
}

function ChatProductCard({ product }: { product: ProductCard }) {
  const inStock = product.inventory.filter((s) => s.quantity > 0).map((s) => s.size);
  return (
    <li>
      <Link to={`/products/${product.product_id}`} className="chat-card">
        <img src={product.image_url} alt="" loading="lazy" />
        <span className="chat-card-text">
          <span className="chat-card-name">{product.name}</span>
          <span className="chat-card-meta">
            <span className="price">{formatPrice(product.price)}</span>
            {" · "}
            {inStock.length ? inStock.join(", ") : "Sold out"}
          </span>
        </span>
      </Link>
    </li>
  );
}
