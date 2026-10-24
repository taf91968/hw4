import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { NotFoundError, fetchProduct, formatPrice } from "../api";
import { openChat } from "../chatEvents";
import type { ProductDetail } from "../types";

const LOW_STOCK = 5;

export default function ProductPage() {
  const { productId = "" } = useParams();
  const [product, setProduct] = useState<ProductDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setProduct(null);
    setError(null);
    fetchProduct(productId)
      .then(setProduct)
      .catch((err) =>
        setError(
          err instanceof NotFoundError
            ? "We couldn't find that product."
            : "We couldn't load this product. Is the backend running?",
        ),
      );
  }, [productId]);

  if (error) {
    return (
      <>
        <p className="status status-error">{error}</p>
        <Link to="/products" className="text-link">
          ← Back to products
        </Link>
      </>
    );
  }
  if (!product) return <p className="status">Loading…</p>;

  const inStockSizes = product.inventory.filter((s) => s.quantity > 0);
  const stock =
    product.total_stock === 0
      ? { cls: "out", text: "Sold out in all sizes" }
      : inStockSizes.every((s) => s.quantity <= LOW_STOCK)
        ? { cls: "low", text: "Low stock — only a few left" }
        : { cls: "ok", text: `In stock in ${inStockSizes.length} of ${product.inventory.length} sizes` };

  return (
    <>
      <nav aria-label="Breadcrumb">
        <ol className="breadcrumbs">
          <li>
            <Link to="/">Home</Link>
          </li>
          <li>
            <Link to="/products">Products</Link>
          </li>
          <li>
            <Link to={`/products?category=${encodeURIComponent(product.category)}`}>{product.category}</Link>
          </li>
          <li aria-current="page">{product.name}</li>
        </ol>
      </nav>
      <article className="product-detail">
        <div className="product-detail-image">
          <img src={product.image_url} alt={product.name} />
        </div>
        <div className="product-detail-info">
          <p className="eyebrow">{product.garment_type}</p>
          <h1>{product.name}</h1>
          <p className="price price-large">{formatPrice(product.price)}</p>
          <p className={`stock-summary ${stock.cls}`}>{stock.text}</p>
          <p>{product.description}</p>
          <button type="button" className="button button-ghost ask-button" onClick={() => openChat()}>
            Ask about this item
          </button>

          {product.colors.length > 0 && (
            <div className="detail-block">
              <h2>Colors</h2>
              <ul className="chips">
                {product.colors.map((c) => (
                  <li key={c} className="chip">
                    {c}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {product.inventory.length > 0 && (
            <div className="detail-block">
              <h2>Sizes &amp; stock</h2>
              <ul className="sizes">
                {product.inventory.map((s) => (
                  <li
                    key={s.size}
                    className={s.quantity === 0 ? "size sold-out" : s.quantity <= LOW_STOCK ? "size low" : "size"}
                  >
                    <span className="size-label">{s.size}</span>
                    <span className="size-stock">
                      {s.quantity === 0
                        ? "Sold out"
                        : s.quantity <= LOW_STOCK
                          ? `Only ${s.quantity} left`
                          : `${s.quantity} in stock`}
                    </span>
                    {s.quantity === 0 && (
                      <button
                        type="button"
                        className="find-similar"
                        onClick={() =>
                          openChat({
                            message: `Size ${s.size} is sold out in this one. Can you show me similar items that have ${s.size} in stock?`,
                          })
                        }
                      >
                        Find similar in {s.size}
                      </button>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Only promises the site keeps. */}
          <ul className="product-assurances">
            <li>Stock shown is live, by size</li>
            <li>Questions about sizes or colors? Ask our shopping assistant</li>
          </ul>
        </div>
      </article>
    </>
  );
}
