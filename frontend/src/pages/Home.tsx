import { type CSSProperties, type ReactNode, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchProducts } from "../api";
import { openChat } from "../chatEvents";
import ProductCard from "../components/ProductCard";
import type { ProductSummary } from "../types";

// One real product photo per category (same order as backend/db.py CATEGORIES).
const CATEGORY_TILES = [
  { name: "Hoodies", image: "champion-reverse-weave-hoodie-1" },
  { name: "Crewnecks", image: "champion-reverse-weave-crewneck" },
  { name: "T-Shirts", image: "boola-boola-t-shirt" },
  { name: "Quarter-Zips", image: "branford-1-4-zip" },
  { name: "Jackets & Fleece", image: "benjamin-franklin-fleece-jacket" },
  { name: "Long Sleeve", image: "dry-zone-long-sleeve" },
];

const HERO_IMAGES = ["basic-hoodie-big-yale", "branford-1-4-zip", "2025-yale-vs-harvard-t-shirt"];
const FEATURED = ["basic-hoodie-big-yale", "2025-yale-vs-harvard-t-shirt", "branford-1-4-zip", "benjamin-franklin-fleece-jacket"];

const icon = (path: ReactNode) => (
  <span className="trust-icon" aria-hidden="true">
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      {path}
    </svg>
  </span>
);

export default function Home() {
  const [products, setProducts] = useState<ProductSummary[]>([]);

  useEffect(() => {
    fetchProducts()
      .then(setProducts)
      .catch(() => setProducts([]));
  }, []);

  const count = (c: string) => products.filter((p) => p.category === c).length;
  const featured = FEATURED.map((id) => products.find((p) => p.product_id === id)).filter(
    (p): p is ProductSummary => Boolean(p && p.total_stock > 0),
  );

  return (
    <>
      <section className="hero">
        <div>
          <p className="eyebrow">Campus Customs · New Haven</p>
          <h1>Wear your Yale pride.</h1>
          <p className="hero-text">
            Hoodies, crewnecks, tees, quarter-zips and jackets for students, families and alumni — from residential
            college crests to Bulldogs classics.
          </p>
          <div className="hero-actions">
            <Link to="/products" className="button button-light">
              Shop all {products.length || ""} styles
            </Link>
            <button type="button" className="button button-outline-light" onClick={() => openChat()}>
              Ask our assistant
            </button>
          </div>
        </div>
        <div className="hero-gallery" aria-hidden="true">
          {HERO_IMAGES.map((id) => (
            <img key={id} src={`/media/products/${id}.jpg`} alt="" />
          ))}
        </div>
      </section>

      {/* Facts the site actually delivers, to build trust without overpromising. */}
      <ul className="trust-strip" aria-label="Why shop Campus Customs">
        <li>
          {icon(<path d="M20 7 9 18l-5-5" />)}
          <span>
            <strong>{products.length || 102} Yale styles</strong>Colleges, sports, The Game
          </span>
        </li>
        <li>
          {icon(<><path d="M3 6h18" /><path d="M3 12h18" /><path d="M3 18h12" /></>)}
          <span>
            <strong>Sizes XS–XXL</strong>Filter to your size
          </span>
        </li>
        <li>
          {icon(<><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></>)}
          <span>
            <strong>Live stock by size</strong>See exactly what's left
          </span>
        </li>
        <li>
          {icon(<path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12Z" />)}
          <span>
            <strong>Help in seconds</strong>Ask our shopping assistant
          </span>
        </li>
      </ul>

      <section className="section" aria-labelledby="shop-by-category">
        <div className="section-heading">
          <h2 id="shop-by-category">Shop by category</h2>
          <Link to="/products" className="text-link">
            View all →
          </Link>
        </div>
        <div className="category-grid">
          {CATEGORY_TILES.map((c, i) => (
            <Link
              key={c.name}
              to={`/products?category=${encodeURIComponent(c.name)}`}
              className="category-tile"
              style={{ "--i": i } as CSSProperties}
            >
              <img src={`/media/products/${c.image}.jpg`} alt="" loading="lazy" />
              <span className="category-name">{c.name}</span>
              <span className="category-count">{count(c.name) ? `${count(c.name)} styles` : " "}</span>
            </Link>
          ))}
        </div>
      </section>

      {featured.length > 0 && (
        <section className="section" aria-labelledby="featured">
          <div className="section-heading">
            <h2 id="featured">Campus favorites</h2>
            <Link to="/products" className="text-link">
              Shop all →
            </Link>
          </div>
          <div className="product-grid">
            {featured.map((p, i) => (
              <ProductCard key={p.product_id} product={p} index={i} />
            ))}
          </div>
        </section>
      )}

      <section className="section assist-banner" aria-labelledby="assist">
        <div>
          <h2 id="assist">Not sure about your size?</h2>
          <p>Our shopping assistant checks live stock by size and finds similar styles when one sells out.</p>
        </div>
        <button type="button" className="button" onClick={() => openChat({ message: "What hoodies do you have?" })}>
          Try "What hoodies do you have?"
        </button>
      </section>
    </>
  );
}
