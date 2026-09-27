import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";

import { useAuth } from "../lib/auth";
import type { Role } from "../lib/types";

/** Signed-out visitors go to the landing page; the wrong role goes to its own portal. */
export function RequireRole({ role, children }: { role: Role; children: ReactNode }) {
  const { state } = useAuth();
  if (state.status === "loading") {
    return (
      <div className="empty" aria-live="polite">
        Loading…
      </div>
    );
  }
  if (state.status === "signed_out") return <Navigate to="/" replace />;
  if (state.me.role !== role) return <Navigate to={state.me.role === "admin" ? "/admin" : "/app"} replace />;
  return <>{children}</>;
}
