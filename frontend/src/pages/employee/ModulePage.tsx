import { useEffect, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";

import { Icon } from "../../components/Icon";
import { PassageText } from "../../components/PassageText";
import { ErrorPanel, LayerBadge, PriorityBadge, ProgressBadge } from "../../components/Status";
import { api } from "../../lib/api";
import { useMe } from "../../lib/auth";
import { useEmployee } from "./EmployeeLayout";

export function ModulePage() {
  const { moduleId } = useParams();
  const { hash } = useLocation();
  const me = useMe();
  const { list, markProgress } = useEmployee();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const index = list.modules.findIndex((m) => m.id === moduleId);
  const module = list.modules[index];
  const next = list.modules.slice(index + 1).find((m) => m.progress !== "completed");

  // Opening a module for the first time starts it.
  useEffect(() => {
    if (module && module.progress === "not_started") {
      api.setProgress(module.id, "in_progress").then(
        () => markProgress(module.id, "in_progress"),
        () => undefined,
      );
    }
    setError(null);
    // A review link from the final check points at one passage (#passage-<id>).
    const target = hash ? document.getElementById(hash.slice(1)) : null;
    if (target) target.scrollIntoView();
    else window.scrollTo(0, 0);
    // Only when the module or target changes, not on every progress update.
  }, [module?.id, hash]);

  if (!module) return <ErrorPanel message="This module isn't available." />;

  const complete = async () => {
    setSaving(true);
    setError(null);
    try {
      await api.setProgress(module.id, "completed");
      markProgress(module.id, "completed");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <article className="stack module-page" aria-labelledby="module-title">
      <div className="page-head">
        <div className="status-row">
          <PriorityBadge priority={module.priority} />
          <ProgressBadge status={module.progress} />
          <LayerBadge layer={module.layer} firmName={me.firm_name} />
          <span className="badge badge-neutral">{module.is_required ? "Required" : "Optional"}</span>
        </div>
        <h1 id="module-title">{module.title}</h1>
        {module.summary && <p className="lede">{module.summary}</p>}
      </div>

      {module.passages.map((p) => (
        <section
          key={p.id}
          id={`passage-${p.id}`}
          className={`passage${hash === `#passage-${p.id}` ? " highlight" : ""}`}
          aria-label={p.heading ?? undefined}
        >
          {p.overridden_by_firm && p.firm_note && (
            <div className="firm-note">
              <span className="badge badge-pending">
                <Icon name="building" size={12} />
                {p.firm_note}
              </span>
              <span className="small">This replaces the general AEC guidance on this topic.</span>
            </div>
          )}
          {p.heading && <h2>{p.heading}</h2>}
          <PassageText text={p.content} />
        </section>
      ))}

      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}

      <div className="card card-alt module-actions">
        {module.progress === "completed" ? (
          <span className="status-row">
            <Icon name="check" size={20} />
            <strong>You&rsquo;ve completed this module.</strong>
          </span>
        ) : (
          <button type="button" className="btn btn-primary" onClick={complete} disabled={saving}>
            <Icon name="check" />
            {saving ? "Saving…" : "Mark as complete"}
          </button>
        )}
        {next ? (
          <Link to={`/app/modules/${next.id}`} className="btn btn-secondary">
            Next: {next.title}
            <Icon name="arrowRight" />
          </Link>
        ) : (
          <Link to="/app" className="btn btn-secondary">
            Back to onboarding home
          </Link>
        )}
      </div>
    </article>
  );
}
