import { createContext, ReactNode, useCallback, useContext, useEffect, useState } from "react";
import * as api from "./api";
import type { User } from "./types";

interface AuthState {
  user: User | null;
  /** True until the first "am I logged in?" check finishes. */
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (fields: api.SignupFields) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // The session lives in an HttpOnly cookie, so ask the backend who we are.
  useEffect(() => {
    api
      .fetchMe()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    setUser(await api.login(email, password));
  }, []);

  const signup = useCallback(async (fields: api.SignupFields) => {
    setUser(await api.signup(fields));
  }, []);

  const logout = useCallback(async () => {
    await api.logout();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
