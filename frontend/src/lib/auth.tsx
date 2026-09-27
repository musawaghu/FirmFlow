import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import { api, ApiError } from "./api";
import { supabase } from "./supabase";
import type { Me, Role } from "./types";

type AuthState =
  | { status: "loading" }
  | { status: "signed_out" }
  | { status: "signed_in"; me: Me };

interface AuthContextValue {
  state: AuthState;
  /** Signs in and checks the account matches the chosen role. Throws a readable Error otherwise. */
  signIn: (email: string, password: string, role: Role) => Promise<Me>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const ROLE_LABEL: Record<Role, string> = { admin: "an admin", employee: "an employee" };

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({ status: "loading" });

  useEffect(() => {
    if (!supabase) {
      setState({ status: "signed_out" });
      return;
    }
    let cancelled = false;
    supabase.auth.getSession().then(async ({ data }) => {
      if (!data.session) {
        if (!cancelled) setState({ status: "signed_out" });
        return;
      }
      try {
        const me = await api.me();
        if (!cancelled) setState({ status: "signed_in", me });
      } catch {
        await supabase?.auth.signOut();
        if (!cancelled) setState({ status: "signed_out" });
      }
    });
    const { data } = supabase.auth.onAuthStateChange((event) => {
      if (event === "SIGNED_OUT") setState({ status: "signed_out" });
    });
    return () => {
      cancelled = true;
      data.subscription.unsubscribe();
    };
  }, []);

  const signIn = useCallback(async (email: string, password: string, role: Role) => {
    if (!supabase) {
      throw new Error("Sign-in isn't configured. Add VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY to frontend/.env.");
    }
    const { error } = await supabase.auth.signInWithPassword({ email: email.trim(), password });
    if (error) throw new Error(error.message === "Invalid login credentials" ? "Wrong email or password." : error.message);
    let me: Me;
    try {
      me = await api.me();
    } catch (e) {
      await supabase.auth.signOut();
      throw new Error(e instanceof ApiError && e.status === 403 ? "This login has no FIRM FLOW profile." : (e as Error).message);
    }
    if (me.role !== role) {
      await supabase.auth.signOut();
      throw new Error(`This is ${ROLE_LABEL[me.role]} account. Choose "${me.role === "admin" ? "Admin" : "Employee"}" to sign in.`);
    }
    setState({ status: "signed_in", me });
    return me;
  }, []);

  const signOut = useCallback(async () => {
    await supabase?.auth.signOut();
    setState({ status: "signed_out" });
  }, []);

  const value = useMemo(() => ({ state, signIn, signOut }), [state, signIn, signOut]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}

/** The signed-in profile. Only call inside a route guarded by RequireRole. */
export function useMe(): Me {
  const { state } = useAuth();
  if (state.status !== "signed_in") throw new Error("useMe needs a signed-in user");
  return state.me;
}
