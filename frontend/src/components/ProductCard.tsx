import type { CSSProperties } from "react";
import { Link } from "react-router-dom";
import { formatPrice } from "../api";
import type { ProductSummary } from "../types";

const SIZES = ["XS", "S", "M", "L", "XL", "XXL"];
const FEW_SIZES = 2; // "Low stock" badge when only this many sizes are left

export default function ProductCard({
  product,
  highlightSize = null,
  index = 0,
}: {
  product: ProductSummary;
  /** The shopper's chosen size filter, shown highlighted in the size row. */
  highlightSize?: string | null;
  /** Position in the grid, used to stagger the entrance animation. */
  index?: number;
}) {
  const inStock = new Set(product.sizes_in_stock);
  const soldOut = product.total_stock === 0;
  const fewSizes = !soldOut && product.sizes_in_stock.length <= FEW_SIZES;

  return (
    <Link
      to={`/products/${product.product_id}`}
      className="product-card"
      style={{ "--i": index } as CSSProperties}
    >
      {soldOut && <span className="card-badge out">Sold out</span>}
      {fewSizes && <span className="card-badge low">Only {product.sizes_in_stock.join(" & ")} left</span>}
      <div className="product-card-image">
        <img src={product.image_url} alt={product.name} loading="lazy" />
      </div>
      <div className="product-card-body">
        <p className="product-card-type">{product.category}</p>
        <h3>{product.name}</h3>
        <p className="price">{formatPrice(product.price)}</p>
        <p className="product-card-description">{product.description}</p>
        {!soldOut && (
          <p className="card-sizes" aria-label={`Sizes in stock: ${product.sizes_in_stock.join(", ")}`}>
            {SIZES.map((s) => (
              <span
                key={s}
                className={["card-size", inStock.has(s) ? "" : "out", s === highlightSize ? "picked" : ""].join(" ")}
                aria-hidden="true"
              >
                {s}
              </span>
            ))}
          </p>
        )}
      </div>
    </Link>
  );
}

/** Placeholder card shown while products load, so the layout doesn't jump. */
export function ProductCardSkeleton() {
  return (
    <div className="product-card skeleton" aria-hidden="true">
      <div className="product-card-image" />
      <div className="product-card-body">
        <div className="skeleton-line short" />
        <div className="skeleton-line" />
        <div className="skeleton-line short" />
      </div>
    </div>
  );
}
