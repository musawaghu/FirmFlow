import { useEffect, useState } from "react";

import { Icon } from "../../components/Icon";
import { PassageText } from "../../components/PassageText";
import { api } from "../../lib/api";
import type { AdminModule, AdminPassage, Issue, SourceSection } from "../../lib/types";

export function useToast(): [string | null, (message: string) => void] {
  const [toast, setToast] = useState<string | null>(null);
  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 2500);
    return () => clearTimeout(t);
  }, [toast]);
  return [toast, setToast];
}

export function Toast({ message }: { message: string | null }) {
  return message ? (
    <div className="toast" role="status">
      {message}
    </div>
  ) : null;
}

export function CriticalToggle({ checked, onChange }: { checked: boolean; onChange: (v: boolean) => Promise<void> }) {
  const [busy, setBusy] = useState(false);
  return (
    <label className="toggle-row">
      <input
        type="checkbox"
        checked={checked}
        disabled={busy}
        onChange={async (e) => {
          setBusy(true);
          try {
            await onChange(e.target.checked);
          } finally {
            setBusy(false);
          }
        }}
      />
      Critical: include in the final check
    </label>
  );
}

function pages(s: SourceSection): string {
  if (s.page_start == null) return "";
  return s.page_end && s.page_end !== s.page_start ? `pp. ${s.page_start}–${s.page_end}` : `p. ${s.page_start}`;
}

/**
 * A firm module's review controls: approve or reject, and each passage with its
 * critical toggle and text editor. With `sections`, each passage sits beside the
 * part of the original manual it came from (the side-by-side review).
 */
export function FirmModuleBody({
  module,
  onChange,
  sections,
  issues = [],
}: {
  module: AdminModule;
  onChange: (m: AdminModule) => void;
  sections?: Map<string, SourceSection>;
  issues?: Issue[];
}) {
  const [toast, showToast] = useToast();
  const [error, setError] = useState<string | null>(null);
  const [confirmFlagged, setConfirmFlagged] = useState(false);
  const [busy, setBusy] = useState(false);
  const approved = module.status === "approved";
  const flagged = module.passages.filter((p) => p.grounding_ok !== true);

  const replacePassage = (p: AdminPassage, status = module.status) =>
    onChange({ ...module, status, passages: module.passages.map((x) => (x.id === p.id ? p : x)) });

  const setStatus = async (status: "approved" | "rejected" | "draft") => {
    setBusy(true);
    setError(null);
    try {
      onChange(await api.updateModule(module.id, { status, confirm_flagged: status === "approved" ? confirmFlagged : undefined }));
      setConfirmFlagged(false);
      showToast(status === "approved" ? "Approved: new hires can see it" : status === "rejected" ? "Rejected" : "Moved back to draft");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const setCritical = async (passage: AdminPassage, value: boolean) => {
    setError(null);
    try {
      replacePassage(await api.updatePassage(passage.id, { is_critical: value }));
      showToast(value ? "Added to the final check" : "Removed from the final check");
    } catch (e) {
      setError((e as Error).message);
    }
  };

  return (
    <>
      {module.status === "rejected" ? (
        <section className="card card-alt">
          <p>This module was rejected, so new hires won&rsquo;t see it.</p>
          <div>
            <button type="button" className="btn btn-secondary" onClick={() => setStatus("draft")} disabled={busy}>
              Move back to draft
            </button>
          </div>
        </section>
      ) : (
        !approved && (
          <section className="card card-alt" aria-labelledby={`approve-${module.id}`}>
            <h2 id={`approve-${module.id}`}>Publish to new hires</h2>
            <p>This module is a draft, so new hires can&rsquo;t see it. Approve it when the text is right.</p>
            {flagged.length > 0 && (
              <label className="toggle-row">
                <input type="checkbox" checked={confirmFlagged} onChange={(e) => setConfirmFlagged(e.target.checked)} />
                {flagged.length} section{flagged.length === 1 ? " has" : "s have"} text the manual doesn&rsquo;t support, or wasn&rsquo;t checked.
                I&rsquo;ve reviewed {flagged.length === 1 ? "it" : "them"} and want to approve anyway.
              </label>
            )}
            <div className="status-row">
              <button type="button" className="btn btn-primary" onClick={() => setStatus("approved")} disabled={busy || (flagged.length > 0 && !confirmFlagged)}>
                <Icon name="check" />
                {busy ? "Saving…" : "Approve module"}
              </button>
              <button type="button" className="btn btn-secondary" onClick={() => setStatus("rejected")} disabled={busy}>
                Reject
              </button>
            </div>
          </section>
        )
      )}

      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}

      {module.passages.map((p) => {
        const source = sections?.get(p.source_section_id);
        const passage = (
          <FirmPassage
            key={p.id}
            moduleId={module.id}
            passage={p}
            moduleApproved={approved}
            onCritical={(v) => setCritical(p, v)}
            onSaved={(updated, moved) => {
              replacePassage(updated, moved ? "draft" : module.status);
              showToast(updated.grounding_ok ? "Saved. The text matches the manual." : "Saved, but some text isn't supported by the manual");
            }}
          />
        );
        if (!sections) return passage;
        const sectionIssues = issues.filter((i) => i.source_section_id === p.source_section_id);
        return (
          <div key={p.id} className="side-by-side">
            <section className="source" aria-label="Original manual">
              <div className="card-header">
                <span className="label">Original manual{source ? ` · ${pages(source)}` : ""}</span>
              </div>
              {source ? (
                <>
                  {source.heading && <h3>{source.heading}</h3>}
                  <PassageText text={source.content} />
                </>
              ) : (
                <p className="small">Source section not found.</p>
              )}
              {sectionIssues.map((i) => (
                <div key={i.id} className="issue">
                  <span className="badge badge-pending">
                    <Icon name="alert" size={12} />
                    {i.type.replace(/_/g, " ")}
                  </span>
                  <p>{i.description}</p>
                  {i.excerpt && <p className="small">&ldquo;{i.excerpt}&rdquo;</p>}
                </div>
              ))}
            </section>
            {passage}
          </div>
        );
      })}

      <Toast message={toast} />
    </>
  );
}

function FirmPassage({
  moduleId,
  passage,
  moduleApproved,
  onCritical,
  onSaved,
}: {
  moduleId: string;
  passage: AdminPassage;
  moduleApproved: boolean;
  onCritical: (v: boolean) => Promise<void>;
  onSaved: (p: AdminPassage, movedToDraft: boolean) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [text, setText] = useState(passage.content);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const save = async () => {
    if (moduleApproved && !window.confirm("Editing moves this module back to draft. New hires won't see it until you approve it again. Continue?")) {
      return;
    }
    setSaving(true);
    setError(null);
    try {
      // The backend only accepts text edits on drafts.
      if (moduleApproved) await api.updateModule(moduleId, { status: "draft" });
      const updated = await api.updatePassage(passage.id, { content: text });
      setEditing(false);
      if (updated.grounding_error) setError(`Saved, but the check against the manual couldn't run: ${updated.grounding_error}`);
      onSaved(updated, moduleApproved);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="passage">
      <div className="card-header">
        <h2>{passage.heading ?? "Untitled section"}</h2>
        <div className="status-row">
          {passage.grounding_ok === true && (
            <span className="badge badge-neutral">
              <Icon name="check" size={12} />
              Matches the manual
            </span>
          )}
          {passage.grounding_ok === false && (
            <span className="badge badge-pending">
              <Icon name="alert" size={12} />
              Not supported by the manual
            </span>
          )}
          {passage.grounding_ok === null && <span className="badge badge-neutral">Not checked</span>}
          {!editing && (
            <button type="button" className="btn btn-secondary btn-small" onClick={() => setEditing(true)}>
              <Icon name="edit" size={14} />
              Edit text
            </button>
          )}
        </div>
      </div>

      {editing ? (
        <div className="stack">
          <label className="sr-only" htmlFor={`edit-${passage.id}`}>
            Section text
          </label>
          <textarea id={`edit-${passage.id}`} className="input textarea" value={text} onChange={(e) => setText(e.target.value)} rows={10} />
          <p className="small">Saving checks the new text against the section of the manual it came from. Edit for clarity; don&rsquo;t add new facts.</p>
          <div className="status-row">
            <button type="button" className="btn btn-primary" onClick={save} disabled={saving || !text.trim() || text === passage.content}>
              {saving ? "Saving and checking…" : "Save"}
            </button>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => {
                setEditing(false);
                setText(passage.content);
              }}
              disabled={saving}
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <PassageText text={passage.content} />
      )}

      {passage.grounding_ok === false && passage.unsupported_spans.length > 0 && (
        <div className="form-error">
          Not found in the manual:
          <ul>
            {passage.unsupported_spans.map((s, i) => (
              <li key={i}>&ldquo;{s.text}&rdquo;</li>
            ))}
          </ul>
        </div>
      )}
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}
      <CriticalToggle checked={passage.is_critical} onChange={onCritical} />
    </section>
  );
}
