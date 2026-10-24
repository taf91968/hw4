// Mirrors the Pydantic models in backend/models.py.

export interface SizeStock {
  size: string;
  quantity: number;
}

export interface ProductSummary {
  product_id: string;
  name: string;
  garment_type: string;
  description: string;
  price: number;
  colors: string[];
  image_url: string;
  total_stock: number;
  category: string;
  sizes_in_stock: string[];
}

export interface ProductDetail extends ProductSummary {
  search_tags: string[];
  inventory: SizeStock[];
}

// Chat — mirrors ProductCard, ChatTurn and ChatResponse in backend/models.py.

export interface ProductCard {
  product_id: string;
  name: string;
  garment_type: string;
  price: number;
  image_url: string;
  colors: string[];
  inventory: SizeStock[];
  total_stock: number;
}

export interface ChatTurn {
  role: "user" | "assistant";
  content: string;
  products: ProductCard[];
}

/** What the browser is showing, sent with every chat message (backend PageContext). */
export interface PageContext {
  path: string;
  page_type: "home" | "products" | "product" | "about" | "login" | "create_account" | "other";
  product_id: string | null;
  results_title: string | null;
  results_product_ids: string[];
}

/** Search results the chat puts on the page (backend/models.py PageResults). */
export interface PageResults {
  title: string;
  query: string;
  total_found: number;
  products: ProductSummary[];
}

export interface ChatResponse {
  reply: string;
  products: ProductCard[];
  page_results: PageResults | null;
}

export interface User {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
}
