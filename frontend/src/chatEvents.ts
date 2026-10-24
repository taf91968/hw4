/**
 * Lets any page open the chat widget, optionally sending a question right away
 * (e.g. the "Ask about this item" button on product pages).
 */
const OPEN_CHAT = "cc:open-chat";

export interface OpenChatDetail {
  /** Send this message as soon as the chat opens. */
  message?: string;
}

export function openChat(detail: OpenChatDetail = {}): void {
  window.dispatchEvent(new CustomEvent<OpenChatDetail>(OPEN_CHAT, { detail }));
}

export function onOpenChat(handler: (detail: OpenChatDetail) => void): () => void {
  const listener = (e: Event) => handler((e as CustomEvent<OpenChatDetail>).detail ?? {});
  window.addEventListener(OPEN_CHAT, listener);
  return () => window.removeEventListener(OPEN_CHAT, listener);
}
