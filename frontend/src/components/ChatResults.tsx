import { useEffect, useRef } from "react";
import { useLocation } from "react-router-dom";
import { useChatResults } from "../chatResults";
import ProductCard from "./ProductCard";

/**
 * "From the shopping assistant" panel at the top of every page.
 *
 * Shows the cards from the chat's latest search. It reuses the Products page
 * ProductCard, so each card is the same link to /products/:id and opens the
 * same single-item page.
 */
export default function ChatResults() {
  const { results, collapsed, setCollapsed, clear } = useChatResults();
  const { pathname } = useLocation();
  const sectionRef = useRef<HTMLElement>(null);

  // Opening a product (from these cards or anywhere else) folds the panel
  // down to its header, so the single-item page is front and center.
  useEffect(() => {
    if (pathname.startsWith("/products/")) setCollapsed(true);
  }, [pathname, setCollapsed]);

  // New results: bring the panel into view.
  useEffect(() => {
    if (results) sectionRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [results]);

  if (!results) return null;

  const { title, total_found, products } = results;
  const count =
    total_found > products.length
      ? `Showing ${products.length} of ${total_found}`
      : `${total_found} ${total_found === 1 ? "item" : "items"}`;

  return (
    <section className="chat-results" ref={sectionRef} aria-labelledby="chat-results-title">
      <div className="chat-results-header">
        <div>
          <p className="eyebrow">From the shopping assistant</p>
          <h2 id="chat-results-title">
            {title} <span className="chat-results-count">· {count}</span>
          </h2>
        </div>
        <div className="chat-results-actions">
          <button
            type="button"
            className="button button-small button-ghost"
            onClick={() => setCollapsed(!collapsed)}
            aria-expanded={!collapsed}
            aria-controls="chat-results-grid"
          >
            {collapsed ? "Show results" : "Hide"}
          </button>
          <button type="button" className="button button-small button-ghost" onClick={clear}>
            Clear
          </button>
        </div>
      </div>
      {!collapsed && (
        <div className="product-grid" id="chat-results-grid">
          {products.map((p, i) => (
            <ProductCard key={p.product_id} product={p} index={i} />
          ))}
        </div>
      )}
    </section>
  );
}
