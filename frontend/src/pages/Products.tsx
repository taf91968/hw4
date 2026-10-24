import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { fetchProducts } from "../api";
import ProductCard, { ProductCardSkeleton } from "../components/ProductCard";
import type { ProductSummary } from "../types";

// Same order as CATEGORIES in backend/db.py.
const CATEGORIES = ["Hoodies", "Crewnecks", "T-Shirts", "Quarter-Zips", "Jackets & Fleece", "Long Sleeve"];
const SIZES = ["XS", "S", "M", "L", "XL", "XXL"];
const SORTS = {
  featured: "Featured",
  "price-asc": "Price: low to high",
  "price-desc": "Price: high to low",
  name: "Name A–Z",
} as const;
type SortKey = keyof typeof SORTS;

/**
 * Products page with filters. Every filter lives in the URL
 * (/products?category=Hoodies&size=M&instock=1&sort=price-asc), so a filtered
 * view can be bookmarked or shared, and Back/Forward work.
 */
export default function Products() {
  const [products, setProducts] = useState<ProductSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [params, setParams] = useSearchParams();

  const query = params.get("q") ?? "";
  const category = params.get("category");
  const size = params.get("size");
  const inStockOnly = params.get("instock") === "1";
  const sort = (params.get("sort") as SortKey) in SORTS ? (params.get("sort") as SortKey) : "featured";

  function update(key: string, value: string | null) {
    const next = new URLSearchParams(params);
    if (value === null || value === "") next.delete(key);
    else next.set(key, value);
    setParams(next, { replace: key === "q" }); // typing shouldn't add a history entry per letter
  }

  useEffect(() => {
    fetchProducts()
      .then(setProducts)
      .catch(() => setError("We couldn't load the products. Is the backend running?"));
  }, []);

  const counts = useMemo(() => {
    const c: Record<string, number> = {};
    for (const p of products ?? []) c[p.category] = (c[p.category] ?? 0) + 1;
    return c;
  }, [products]);

  const shown = useMemo(() => {
    if (!products) return [];
    const q = query.trim().toLowerCase();
    const list = products.filter(
      (p) =>
        (!category || p.category === category) &&
        (!size || p.sizes_in_stock.includes(size)) &&
        (!inStockOnly || p.total_stock > 0) &&
        (!q || [p.name, p.garment_type, p.description, ...p.colors].join(" ").toLowerCase().includes(q)),
    );
    if (sort === "price-asc") list.sort((a, b) => a.price - b.price || a.name.localeCompare(b.name));
    if (sort === "price-desc") list.sort((a, b) => b.price - a.price || a.name.localeCompare(b.name));
    if (sort === "name") list.sort((a, b) => a.name.localeCompare(b.name));
    return list;
  }, [products, query, category, size, inStockOnly, sort]);

  const filtersOn = Boolean(query || category || size || inStockOnly || sort !== "featured");

  return (
    <>
      <div className="section-heading">
        <h1>Products</h1>
        <label className="search">
          <span className="visually-hidden">Search products</span>
          <input
            type="search"
            value={query}
            onChange={(e) => update("q", e.target.value)}
            placeholder="Search hoodies, colleges, colors…"
          />
        </label>
      </div>

      <div className="filters" role="group" aria-label="Filter products">
        <div className="filter-row" role="group" aria-label="Category">
          <button
            type="button"
            className={!category ? "filter-chip active" : "filter-chip"}
            aria-pressed={!category}
            onClick={() => update("category", null)}
          >
            All <span className="filter-count">{products?.length ?? ""}</span>
          </button>
          {CATEGORIES.map((c) => (
            <button
              key={c}
              type="button"
              className={category === c ? "filter-chip active" : "filter-chip"}
              aria-pressed={category === c}
              onClick={() => update("category", category === c ? null : c)}
            >
              {c} <span className="filter-count">{counts[c] ?? ""}</span>
            </button>
          ))}
        </div>

        <div className="filter-row">
          <span className="filter-label" id="size-label">
            My size
          </span>
          <div className="size-picker" role="group" aria-labelledby="size-label">
            {SIZES.map((s) => (
              <button
                key={s}
                type="button"
                className={size === s ? "size-chip active" : "size-chip"}
                aria-pressed={size === s}
                onClick={() => update("size", size === s ? null : s)}
              >
                {s}
              </button>
            ))}
          </div>

          <label className="toggle">
            <input
              type="checkbox"
              checked={inStockOnly}
              onChange={(e) => update("instock", e.target.checked ? "1" : null)}
            />
            In stock only
          </label>

          <label className="sort">
            <span>Sort</span>
            <select value={sort} onChange={(e) => update("sort", e.target.value === "featured" ? null : e.target.value)}>
              {Object.entries(SORTS).map(([key, label]) => (
                <option key={key} value={key}>
                  {label}
                </option>
              ))}
            </select>
          </label>

          {filtersOn && (
            <button type="button" className="text-link clear-filters" onClick={() => setParams(new URLSearchParams())}>
              Clear filters
            </button>
          )}
        </div>
      </div>

      {error && <p className="status status-error">{error}</p>}
      {!error && !products && (
        <div className="product-grid" aria-busy="true" aria-label="Loading products">
          {Array.from({ length: 8 }, (_, i) => (
            <ProductCardSkeleton key={i} />
          ))}
        </div>
      )}
      {products && (
        <>
          <p className="status" aria-live="polite">
            {shown.length} of {products.length} products
            {size && <> in stock in size {size}</>}
          </p>
          {shown.length === 0 ? (
            <p className="status">
              Nothing matches these filters. Try another size or category, or ask the shopping assistant.
            </p>
          ) : (
            <div className="product-grid">
              {shown.map((p, i) => (
                <ProductCard key={p.product_id} product={p} highlightSize={size} index={i} />
              ))}
            </div>
          )}
        </>
      )}
    </>
  );
}
