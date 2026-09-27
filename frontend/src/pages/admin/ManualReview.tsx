import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { Icon } from "../../components/Icon";
import { PriorityBadge } from "../../components/Status";
import { api } from "../../lib/api";
import type { AdminModule, Issue, Manual, Override, Review, SourceSection } from "../../lib/types";
import { useAdmin } from "./AdminLayout";
import { FirmModuleBody } from "./FirmModuleBody";
import { MANUAL_STATUS } from "./Manuals";

const POLL_MS = 5000;

const MODULE_STATUS: Record<string, { label: string; cls: string }> = {
  approved: { label: "Approved", cls: "badge-active" },
  draft: { label: "Draft", cls: "badge-pending" },
  rejected: { label: "Rejected", cls: "badge-neutral" },
};

export function ManualReview() {
  const { manualId = "" } = useParams();
  const [manual, setManual] = useState<Manual | null>(null);
  const [review, setReview] = useState<Review | null>(null);
  const [issues, setIssues] = useState<Issue[]>([]);
  const [error, setError] = useState<string | null>(null);

  const loadReview = useCallback(async () => {
    const [r, i] = await Promise.all([api.review(manualId), api.issues(manualId)]);
    setReview(r);
    setIssues(i);
  }, [manualId]);

  useEffect(() => {
    setManual(null);
    setReview(null);
    api.manual(manualId).then(
      (m) => {
        setManual(m);
        if (m.status === "processed") loadReview().catch((e: Error) => setError(e.message));
      },
      (e: Error) => setError(e.message),
    );
  }, [manualId, loadReview]);

  // While Claude works, check back every few seconds.
  useEffect(() => {
    if (manual?.status !== "processing") return;
    const t = setInterval(async () => {
      try {
        const m = await api.manual(manualId);
        if (m.status !== "processing") {
          setManual(m);
          if (m.status === "processed") await loadReview();
        }
      } catch {
        // A missed poll is fine; the next one tries again.
      }
    }, POLL_MS);
    return () => clearInterval(t);
  }, [manual?.status, manualId, loadReview]);

  if (error) {
    return (
      <div className="card empty">
        <p>{error}</p>
        <Link to="/admin/manuals">Back to manuals</Link>
      </div>
    );
  }
  if (!manual) return <div className="empty">Loading…</div>;

  return (
    <div className="stack">
      <div className="page-head">
        <div className="status-row">
          <Link to="/admin/manuals" className="small">
            Manuals
          </Link>
          <span className={`badge ${MANUAL_STATUS[manual.status].cls}`}>{MANUAL_STATUS[manual.status].label}</span>
          <span className="badge badge-neutral">
            {manual.file_type.toUpperCase()}
            {manual.page_count ? `, ${manual.page_count} pages` : ""}
          </span>
        </div>
        <h1>{manual.title}</h1>
      </div>

      {manual.status === "processed" ? (
        review ? (
          <ReviewBody review={review} issues={issues} onReview={setReview} />
        ) : (
          <div className="empty">Loading the review…</div>
        )
      ) : (
        <ProcessCard manual={manual} onStarted={setManual} />
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Before review: start processing and wait
// ---------------------------------------------------------------------------

function ProcessCard({ manual, onStarted }: { manual: Manual; onStarted: (m: Manual) => void }) {
  const [topics, setTopics] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (manual.status === "processing") {
    return (
      <section className="card card-alt empty" aria-live="polite">
        <Icon name="layers" size={32} />
        <h2>Claude is drafting your modules</h2>
        <p>
          It rewrites the manual into modules, flags problems in it, and checks every passage against the original. This usually takes 5 to 15 minutes.
          You can leave this page; it keeps going.
        </p>
      </section>
    );
  }

  const start = async () => {
    setBusy(true);
    setError(null);
    try {
      const list = topics
        .split("\n")
        .map((t) => t.trim())
        .filter(Boolean);
      onStarted(await api.processManual(manual.id, list));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="card card-alt" aria-labelledby="process-title">
      <h2 id="process-title">{manual.status === "failed" ? "Processing failed" : "Turn it into modules"}</h2>
      {manual.status === "failed" && manual.error && <p className="form-error">{manual.error}</p>}
      <p>
        The file has been read. Claude will now draft onboarding modules from it and flag gaps, contradictions, and outdated references. Nothing reaches new
        hires until you approve it.
      </p>
      <div className="field">
        <label htmlFor="topics">Modules you want (optional, one per line)</label>
        <textarea
          id="topics"
          className="input textarea"
          rows={5}
          value={topics}
          onChange={(e) => setTopics(e.target.value)}
          placeholder={"Welcome and general onboarding\nTechnology guide: BIM standards, file naming, folders\nOperations: timesheets, expenses, billing hours"}
        />
        <span className="small">Leave it empty and Claude picks the modules from the manual&rsquo;s structure.</span>
      </div>
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}
      <div>
        <button type="button" className="btn btn-primary" onClick={start} disabled={busy}>
          {busy ? "Starting…" : manual.status === "failed" ? "Try again" : "Process with Claude"}
        </button>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// The side-by-side review
// ---------------------------------------------------------------------------

function ReviewBody({ review, issues, onReview }: { review: Review; issues: Issue[]; onReview: (r: Review) => void }) {
  const { firmModules, replaceFirmModule, reload } = useAdmin();
  const [selected, setSelected] = useState<string | null>(review.modules[0]?.id ?? null);
  const sections = useMemo(() => new Map<string, SourceSection>(review.sections.map((s) => [s.id, s])), [review.sections]);
  const module = review.modules.find((m) => m.id === selected);

  const onModuleChange = (m: AdminModule) => {
    const before = review.modules.find((x) => x.id === m.id);
    onReview({ ...review, modules: review.modules.map((x) => (x.id === m.id ? m : x)) });
    // Keep the sidebar in step: a newly approved or rejected module adds or removes an entry.
    if (firmModules.some((x) => x.id === m.id) && m.status !== "rejected") replaceFirmModule(m);
    else if (before?.status !== m.status) void reload();
  };

  const counts = {
    approved: review.modules.filter((m) => m.status === "approved").length,
    flagged: review.modules.flatMap((m) => m.passages).filter((p) => p.grounding_ok !== true).length,
    openIssues: issues.filter((i) => i.status === "open").length,
    proposed: review.overrides.filter((o) => o.status === "proposed").length,
  };
  const passageSections = new Set(review.modules.flatMap((m) => m.passages.map((p) => p.source_section_id)));
  const otherIssues = issues.filter((i) => !i.source_section_id || !passageSections.has(i.source_section_id));
  const warnings = review.manual.processing_notes.warnings ?? [];

  return (
    <>
      <div className="stat-row" role="list">
        <Stat label="Modules approved" value={`${counts.approved} / ${review.modules.length}`} />
        <Stat label="Passages flagged" value={counts.flagged} />
        <Stat label="Issues in the manual" value={counts.openIssues} />
        <Stat label="Baseline overrides to confirm" value={counts.proposed} />
      </div>

      {warnings.length > 0 && (
        <details className="card">
          <summary className="label">
            {warnings.length} processing note{warnings.length === 1 ? "" : "s"}
          </summary>
          <ul className="small">
            {warnings.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </details>
      )}

      {review.overrides.length > 0 && <Overrides overrides={review.overrides} onChange={(o) => onReview({ ...review, overrides: o })} />}

      <section className="stack" aria-labelledby="modules-title">
        <div className="page-head">
          <h2 id="modules-title">Review each module</h2>
          <p>The original manual is on the left and Claude&rsquo;s version on the right. Edit anything that isn&rsquo;t right, then approve the module.</p>
        </div>
        <div className="tabs" role="tablist" aria-label="Modules">
          {review.modules.map((m) => (
            <button
              key={m.id}
              type="button"
              role="tab"
              className="tab"
              aria-selected={m.id === selected}
              onClick={() => setSelected(m.id)}
            >
              {m.status === "approved" && <Icon name="check" size={14} />} {m.title}
            </button>
          ))}
        </div>
        {module ? (
          <div className="tab-panel" role="tabpanel">
            <div className="card-header">
              <div className="stack" style={{ gap: "0.25rem" }}>
                <div className="status-row">
                  <PriorityBadge priority={module.priority} />
                  <span className={`badge ${MODULE_STATUS[module.status]?.cls ?? "badge-neutral"}`}>{MODULE_STATUS[module.status]?.label ?? module.status}</span>
                  <span className="badge badge-neutral">{module.is_required ? "Required" : "Optional"}</span>
                </div>
                <h2>{module.title}</h2>
                {module.summary && <p>{module.summary}</p>}
              </div>
              {module.status !== "rejected" && (
                <Link to={`/admin/modules/firm/${module.id}`} className="small">
                  Due date and settings
                </Link>
              )}
            </div>
            <FirmModuleBody key={module.id} module={module} onChange={onModuleChange} sections={sections} issues={issues} />
          </div>
        ) : (
          <div className="card empty">
            <p>Claude didn&rsquo;t produce any modules from this manual.</p>
          </div>
        )}
      </section>

      {otherIssues.length > 0 && (
        <section className="card" aria-labelledby="other-issues-title">
          <h2 id="other-issues-title">Other problems flagged in the manual</h2>
          <ul className="checklist">
            {otherIssues.map((i) => (
              <li key={i.id} className="check-item">
                <Icon name="alert" size={16} />
                <span className="check-body">
                  <strong>{i.type.replace(/_/g, " ")}</strong>
                  <span>{i.description}</span>
                  {(i.section_heading || i.pages) && (
                    <span className="small">
                      {i.section_heading}
                      {i.pages ? ` · ${i.pages}` : ""}
                    </span>
                  )}
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </>
  );
}

function Overrides({ overrides, onChange }: { overrides: Override[]; onChange: (o: Override[]) => void }) {
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const decide = async (o: Override, status: Override["status"]) => {
    setBusy(o.id);
    setError(null);
    try {
      const updated = await api.updateOverride(o.id, status);
      onChange(overrides.map((x) => (x.id === o.id ? updated : x)));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(null);
    }
  };

  return (
    <section className="card" aria-labelledby="overrides-title">
      <div className="card-header">
        <h2 id="overrides-title">Where your firm differs from the AEC baseline</h2>
        <Icon name="building" size={22} />
      </div>
      <p>
        Your manual states a different practice than the general AEC guidance. Confirm an override and new hires see your version, with a note that your
        firm does this differently.
      </p>
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}
      {overrides.map((o) => (
        <article key={o.id} className="override">
          <div className="card-header">
            <strong>{o.difference}</strong>
            <span className={`badge ${o.status === "confirmed" ? "badge-active" : o.status === "proposed" ? "badge-pending" : "badge-neutral"}`}>
              {o.status === "confirmed" ? "Confirmed" : o.status === "proposed" ? "Needs a decision" : "Dismissed"}
            </span>
          </div>
          <div className="side-by-side">
            <div className="source">
              <span className="label">AEC baseline · {o.baseline_passage.module_title}</span>
              <blockquote>{o.baseline_excerpt}</blockquote>
            </div>
            <div className="passage">
              <span className="label">Your manual · {o.firm_passage.module_title}</span>
              <blockquote>{o.firm_excerpt}</blockquote>
            </div>
          </div>
          <div className="status-row">
            {o.status !== "confirmed" && (
              <button type="button" className="btn btn-primary btn-small" onClick={() => decide(o, "confirmed")} disabled={busy === o.id}>
                Use our version
              </button>
            )}
            {o.status !== "dismissed" && (
              <button type="button" className="btn btn-secondary btn-small" onClick={() => decide(o, "dismissed")} disabled={busy === o.id}>
                {o.status === "confirmed" ? "Stop overriding" : "Dismiss"}
              </button>
            )}
          </div>
        </article>
      ))}
    </section>
  );
}

function Stat({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="stat" role="listitem">
      <span className="stat-label">{label}</span>
      <span className="stat-value">{value}</span>
    </div>
  );
}
