import type { ChatResponse, ChatTurn, PageContext, ProductDetail, ProductSummary, User } from "./types";

export class NotFoundError extends Error {}

/** An error whose message comes from the backend and is safe to show. */
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}

async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (res.status === 404) throw new NotFoundError("Not found");
  if (!res.ok) throw new Error(`Request failed (${res.status})`);
  return res.json() as Promise<T>;
}

async function postJson<T>(url: string, body?: unknown): Promise<T> {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => null);
    const detail = typeof data?.detail === "string" ? data.detail : null;
    throw new ApiError(detail ?? "Something went wrong. Please try again.", res.status);
  }
  return (res.status === 204 ? undefined : await res.json()) as T;
}

export function fetchProducts(): Promise<ProductSummary[]> {
  return getJson("/api/products");
}

export function fetchProduct(productId: string): Promise<ProductDetail> {
  return getJson(`/api/products/${encodeURIComponent(productId)}`);
}

export async function fetchMe(): Promise<User | null> {
  const res = await fetch("/api/auth/me");
  return res.ok ? ((await res.json()) as User) : null;
}

export function login(email: string, password: string): Promise<User> {
  return postJson("/api/auth/login", { email, password });
}

export interface SignupFields {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
}

export function signup(fields: SignupFields): Promise<User> {
  return postJson("/api/auth/signup", fields);
}

export function logout(): Promise<void> {
  return postJson("/api/auth/logout");
}

export function fetchChatHistory(): Promise<ChatTurn[]> {
  return getJson("/api/chat/history");
}

export interface GuestTurn {
  role: "user" | "assistant";
  content: string;
  product_ids: string[];
}

export function sendChat(message: string, page: PageContext, history: GuestTurn[]): Promise<ChatResponse> {
  return postJson("/api/chat", { message, page, history });
}

export function formatPrice(price: number): string {
  return `$${price.toFixed(2)}`;
}
