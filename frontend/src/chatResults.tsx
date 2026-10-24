import { createContext, ReactNode, useCallback, useContext, useState } from "react";
import type { PageResults } from "./types";

/**
 * Shares the chat's latest search results between the chat widget (which
 * receives them from POST /api/chat) and the results panel at the top of
 * every page (which shows them as product cards).
 */
interface ChatResultsState {
  results: PageResults | null;
  collapsed: boolean;
  show: (results: PageResults) => void;
  setCollapsed: (collapsed: boolean) => void;
  clear: () => void;
}

const ChatResultsContext = createContext<ChatResultsState | null>(null);

export function ChatResultsProvider({ children }: { children: ReactNode }) {
  const [results, setResults] = useState<PageResults | null>(null);
  const [collapsed, setCollapsed] = useState(false);

  const show = useCallback((next: PageResults) => {
    setResults(next);
    setCollapsed(false);
  }, []);

  const clear = useCallback(() => setResults(null), []);

  return (
    <ChatResultsContext.Provider value={{ results, collapsed, show, setCollapsed, clear }}>
      {children}
    </ChatResultsContext.Provider>
  );
}

export function useChatResults(): ChatResultsState {
  const ctx = useContext(ChatResultsContext);
  if (!ctx) throw new Error("useChatResults must be used inside <ChatResultsProvider>");
  return ctx;
}
