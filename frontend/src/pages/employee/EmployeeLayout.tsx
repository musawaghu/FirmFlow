import { NavLink, Outlet, useOutletContext } from "react-router-dom";

import { Icon } from "../../components/Icon";
import { ErrorPanel } from "../../components/Status";
import { TopNav } from "../../components/TopNav";
import { api } from "../../lib/api";
import { PRIORITIES, PRIORITY_LABEL, PROGRESS_LABEL } from "../../lib/format";
import type { EmployeeModule, ModuleList, ProgressStatus } from "../../lib/types";
import { useLoad } from "../../lib/useLoad";

export interface EmployeeContext {
  list: ModuleList;
  /** Apply a progress change the server has accepted. Completed never goes back. */
  markProgress: (moduleId: string, status: ProgressStatus) => void;
}

export function useEmployee(): EmployeeContext {
  return useOutletContext<EmployeeContext>();
}

function StatusMark({ status }: { status: ProgressStatus }) {
  return (
    <span className={`mark mark-${status}`} title={PROGRESS_LABEL[status]}>
      {status === "completed" && <Icon name="check" size={12} />}
      <span className="sr-only">{PROGRESS_LABEL[status]}</span>
    </span>
  );
}

export function EmployeeLayout() {
  const { data, error, loading, reload, setData } = useLoad(api.modules);

  // Recount locally with the backend's rules (services/progress.py) instead of refetching,
  // so two quick updates can't land out of order and show stale counts.
  const markProgress = (moduleId: string, status: ProgressStatus) => {
    setData((d) => {
      if (!d) return d;
      const modules = d.modules.map((m) => (m.id === moduleId && m.progress !== "completed" ? { ...m, progress: status } : m));
      const required = modules.filter((m) => m.is_required);
      const completed = required.filter((m) => m.progress === "completed").length;
      return {
        ...d,
        modules,
        required_modules: required.length,
        completed_required: completed,
        final_check_unlocked: required.length > 0 && completed === required.length,
      };
    });
  };

  const byPriority = (modules: EmployeeModule[]) => PRIORITIES.map((p) => ({ priority: p, modules: modules.filter((m) => m.priority === p) }));

  return (
    <>
      <TopNav />
      <div className="shell">
        <nav className="sidebar" aria-label="Onboarding modules">
          <div className="sidebar-group">
            <NavLink to="/app" end className="sidebar-link">
              <span className="status-row">
                <Icon name="home" />
                Onboarding home
              </span>
            </NavLink>
          </div>
          {data &&
            byPriority(data.modules).map(
              (g) =>
                g.modules.length > 0 && (
                  <div className="sidebar-group" key={g.priority}>
                    <span className="sidebar-heading">{PRIORITY_LABEL[g.priority]}</span>
                    {g.modules.map((m) => (
                      <NavLink key={m.id} to={`/app/modules/${m.id}`} className="sidebar-link">
                        <span>{m.title}</span>
                        <StatusMark status={m.progress} />
                      </NavLink>
                    ))}
                  </div>
                ),
            )}
        </nav>
        <main className="main">
          {error ? (
            <ErrorPanel message={error} onRetry={reload} />
          ) : !data ? (
            <div className="empty">{loading ? "Loading your onboarding…" : null}</div>
          ) : (
            <Outlet context={{ list: data, markProgress } satisfies EmployeeContext} />
          )}
        </main>
      </div>
    </>
  );
}
