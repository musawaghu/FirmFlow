import { useCallback, useEffect, useState } from "react";
import { NavLink, Outlet, useOutletContext } from "react-router-dom";

import { Icon } from "../../components/Icon";
import { ErrorPanel } from "../../components/Status";
import { TopNav } from "../../components/TopNav";
import { api } from "../../lib/api";
import { useMe } from "../../lib/auth";
import { PRIORITY_LABEL } from "../../lib/format";
import { sortModules } from "../../lib/modules";
import type { AdminModule, BaselineModule } from "../../lib/types";

export interface AdminContext {
  firmModules: AdminModule[];
  baselineModules: BaselineModule[];
  replaceFirmModule: (m: AdminModule) => void;
  replaceBaselineModule: (m: BaselineModule) => void;
  /** Refetch everything, e.g. after a manual is processed or a new module is approved. */
  reload: () => Promise<void>;
}

export function useAdmin(): AdminContext {
  return useOutletContext<AdminContext>();
}

/** The firm's own modules come from its processed manuals (rejected ones are left out). */
async function loadFirmModules(): Promise<AdminModule[]> {
  const manuals = (await api.manuals()).filter((m) => m.status === "processed");
  const reviews = await Promise.all(manuals.map((m) => api.review(m.id)));
  return sortModules(reviews.flatMap((r) => r.modules).filter((m) => m.status !== "rejected"));
}

export function AdminLayout() {
  const me = useMe();
  const [firmModules, setFirmModules] = useState<AdminModule[] | null>(null);
  const [baselineModules, setBaselineModules] = useState<BaselineModule[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const [firm, baseline] = await Promise.all([loadFirmModules(), api.baselineModules()]);
      setFirmModules(firm);
      setBaselineModules(baseline);
    } catch (e) {
      setError((e as Error).message);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const ready = firmModules !== null && baselineModules !== null;
  const context: AdminContext | null = ready
    ? {
        firmModules,
        baselineModules,
        replaceFirmModule: (m) => setFirmModules((list) => sortModules((list ?? []).map((x) => (x.id === m.id ? m : x)))),
        replaceBaselineModule: (m) => setBaselineModules((list) => sortModules((list ?? []).map((x) => (x.id === m.id ? m : x)))),
        reload: load,
      }
    : null;

  return (
    <>
      <TopNav />
      <div className="shell">
        <nav className="sidebar" aria-label="Admin">
          <div className="sidebar-group">
            <NavLink to="/admin" end className="sidebar-link">
              <span className="status-row">
                <Icon name="chart" />
                Dashboard
              </span>
            </NavLink>
            <NavLink to="/admin/manuals" className="sidebar-link">
              <span className="status-row">
                <Icon name="book" />
                Manuals and review
              </span>
            </NavLink>
          </div>
          {ready && (
            <>
              <div className="sidebar-group">
                <span className="sidebar-heading">{me.firm_name ?? "Firm"} modules</span>
                {firmModules.length === 0 && <span className="sidebar-link small">No firm modules yet.</span>}
                {firmModules.map((m) => (
                  <NavLink key={m.id} to={`/admin/modules/firm/${m.id}`} className="sidebar-link">
                    <span>{m.title}</span>
                    <span className="small">{m.status === "approved" ? PRIORITY_LABEL[m.priority] : "Draft"}</span>
                  </NavLink>
                ))}
              </div>
              <div className="sidebar-group">
                <span className="sidebar-heading">AEC baseline modules</span>
                {baselineModules.map((m) => (
                  <NavLink key={m.id} to={`/admin/modules/baseline/${m.id}`} className="sidebar-link">
                    <span>{m.title}</span>
                    <span className="small">{m.is_hidden ? "Hidden" : PRIORITY_LABEL[m.priority]}</span>
                  </NavLink>
                ))}
              </div>
            </>
          )}
        </nav>
        <main className="main">
          {error ? (
            <ErrorPanel message={error} onRetry={load} />
          ) : context ? (
            <Outlet context={context} />
          ) : (
            <div className="empty">Loading…</div>
          )}
        </main>
      </div>
    </>
  );
}
