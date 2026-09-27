import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import { Icon } from "../../components/Icon";
import { PassageText } from "../../components/PassageText";
import { ErrorPanel, PriorityBadge } from "../../components/Status";
import { api } from "../../lib/api";
import { useMe } from "../../lib/auth";
import { PRIORITIES, PRIORITY_LABEL } from "../../lib/format";
import type { AdminModule as FirmModule, AdminPassage, BaselineModule, Priority } from "../../lib/types";
import { useAdmin } from "./AdminLayout";

export function AdminModule() {
  const { layer, moduleId } = useParams();
  const { firmModules, baselineModules } = useAdmin();
  const baseline = layer === "baseline" ? baselineModules.find((m) => m.id === moduleId) : undefined;
  const firm = layer === "firm" ? firmModules.find((m) => m.id === moduleId) : undefined;

  if (baseline) return <BaselineEditor key={baseline.id} module={baseline} />;
  if (firm) return <FirmEditor key={firm.id} module={firm} />;
  return <ErrorPanel message="Module not found." />;
}

// ---------------------------------------------------------------------------
// Shared pieces
// ---------------------------------------------------------------------------

function useToast(): [string | null, (message: string) => void] {
  const [toast, setToast] = useState<string | null>(null);
  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 2500);
    return () => clearTimeout(t);
  }, [toast]);
  return [toast, setToast];
}

interface Settings {
  priority: Priority;
  is_required: boolean;
  visible?: boolean; // baseline only
}

function SettingsCard({
  initial,
  showVisibility,
  onSave,
}: {
  initial: Settings;
  showVisibility: boolean;
  onSave: (s: Settings) => Promise<void>;
}) {
  const [s, setS] = useState(initial);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const dirty = s.priority !== initial.priority || s.is_required !== initial.is_required || s.visible !== initial.visible;

  const save = async () => {
    setSaving(true);
    setError(null);
    try {
      await onSave(s);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="card card-alt" aria-labelledby="settings-title">
      <div className="card-header">
        <h2 id="settings-title">Settings for your firm</h2>
        <Icon name="edit" size={20} />
      </div>
      <div className="settings-grid">
        <div className="field">
          <label htmlFor="priority">When new hires should finish it</label>
          <select id="priority" className="select" value={s.priority} onChange={(e) => setS({ ...s, priority: e.target.value as Priority })}>
            {PRIORITIES.map((p) => (
              <option key={p} value={p}>
                {PRIORITY_LABEL[p]}
              </option>
            ))}
          </select>
        </div>
        <label className="toggle-row">
          <input type="checkbox" checked={s.is_required} onChange={(e) => setS({ ...s, is_required: e.target.checked })} />
          Required before the final check
        </label>
        {showVisibility && (
          <label className="toggle-row">
            <input type="checkbox" checked={s.visible} onChange={(e) => setS({ ...s, visible: e.target.checked })} />
            Show this module to new hires
          </label>
        )}
      </div>
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}
      <div className="status-row">
        <button type="button" className="btn btn-primary" onClick={save} disabled={!dirty || saving}>
          {saving ? "Saving…" : "Save settings"}
        </button>
        {dirty && (
          <button type="button" className="btn btn-secondary" onClick={() => setS(initial)} disabled={saving}>
            Reset
          </button>
        )}
      </div>
    </section>
  );
}

function CriticalToggle({ checked, onChange }: { checked: boolean; onChange: (v: boolean) => Promise<void> }) {
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

// ---------------------------------------------------------------------------
// AEC baseline module: shared content, per-firm settings
// ---------------------------------------------------------------------------

function BaselineEditor({ module }: { module: BaselineModule }) {
  const me = useMe();
  const { replaceBaselineModule } = useAdmin();
  const [toast, showToast] = useToast();
  const [error, setError] = useState<string | null>(null);

  const saveSettings = async (s: Settings) => {
    const updated = await api.updateBaselineModule(module.id, { priority: s.priority, is_required: s.is_required, is_hidden: !s.visible });
    replaceBaselineModule(updated);
    showToast("Settings saved");
  };

  const setCritical = async (passageId: string, value: boolean) => {
    setError(null);
    try {
      await api.updatePassage(passageId, { is_critical: value });
      replaceBaselineModule({ ...module, passages: module.passages.map((p) => (p.id === passageId ? { ...p, is_critical: value } : p)) });
      showToast(value ? "Added to the final check" : "Removed from the final check");
    } catch (e) {
      setError((e as Error).message);
    }
  };

  return (
    <article className="stack module-page">
      <div className="page-head">
        <div className="status-row">
          <span className="badge badge-neutral">AEC baseline</span>
          <PriorityBadge priority={module.priority} />
          {module.is_hidden && (
            <span className="badge badge-pending">
              <Icon name="eyeOff" size={12} />
              Hidden from new hires
            </span>
          )}
        </div>
        <h1>{module.title}</h1>
        {module.summary && <p className="lede">{module.summary}</p>}
      </div>

      <SettingsCard
        initial={{ priority: module.priority, is_required: module.is_required, visible: !module.is_hidden }}
        showVisibility
        onSave={saveSettings}
      />

      <div className="card">
        <p>
          Baseline modules are general AEC practice shared by every firm, so their text can&rsquo;t be edited here. Where {me.firm_name ?? "your firm"}{" "}
          does something differently, put your rule in your firm&rsquo;s manual: FIRM FLOW proposes an override, and once you confirm it new hires see
          your version instead.
        </p>
      </div>

      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}

      {module.passages.map((p) => (
        <section key={p.id} className="passage">
          <div className="card-header">
            <h2>{p.heading ?? "Untitled section"}</h2>
            {p.overridden_by && (
              <span className="badge badge-pending">
                <Icon name="building" size={12} />
                Replaced by your firm&rsquo;s rule
              </span>
            )}
          </div>
          <PassageText text={p.content} />
          {p.overridden_by ? (
            <p className="small">New hires see your firm&rsquo;s version of this section, so it isn&rsquo;t used in the final check.</p>
          ) : (
            <CriticalToggle checked={p.is_critical} onChange={(v) => setCritical(p.id, v)} />
          )}
        </section>
      ))}

      {toast && (
        <div className="toast" role="status">
          {toast}
        </div>
      )}
    </article>
  );
}

// ---------------------------------------------------------------------------
// The firm's own module: settings, critical passages, and text edits
// ---------------------------------------------------------------------------

function FirmEditor({ module }: { module: FirmModule }) {
  const { replaceFirmModule } = useAdmin();
  const [toast, showToast] = useToast();
  const [error, setError] = useState<string | null>(null);
  const [confirmFlagged, setConfirmFlagged] = useState(false);
  const [approving, setApproving] = useState(false);
  const approved = module.status === "approved";
  const flagged = module.passages.filter((p) => p.grounding_ok !== true);

  const saveSettings = async (s: Settings) => {
    const updated = await api.updateModule(module.id, { priority: s.priority, is_required: s.is_required });
    replaceFirmModule(updated);
    showToast("Settings saved");
  };

  const replacePassage = (p: AdminPassage) => replaceFirmModule({ ...module, passages: module.passages.map((x) => (x.id === p.id ? p : x)) });

  const setCritical = async (passage: AdminPassage, value: boolean) => {
    setError(null);
    try {
      replacePassage(await api.updatePassage(passage.id, { is_critical: value }));
      showToast(value ? "Added to the final check" : "Removed from the final check");
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const approve = async () => {
    setApproving(true);
    setError(null);
    try {
      replaceFirmModule(await api.updateModule(module.id, { status: "approved", confirm_flagged: confirmFlagged }));
      setConfirmFlagged(false);
      showToast("Approved: new hires can see it");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setApproving(false);
    }
  };

  return (
    <article className="stack module-page">
      <div className="page-head">
        <div className="status-row">
          <span className="badge badge-neutral">Your firm</span>
          <PriorityBadge priority={module.priority} />
          <span className={`badge ${approved ? "badge-active" : "badge-pending"}`}>{approved ? "Approved" : "Draft: hidden from new hires"}</span>
        </div>
        <h1>{module.title}</h1>
        {module.summary && <p className="lede">{module.summary}</p>}
      </div>

      <SettingsCard initial={{ priority: module.priority, is_required: module.is_required }} showVisibility={false} onSave={saveSettings} />

      {!approved && (
        <section className="card card-alt" aria-labelledby="approve-title">
          <h2 id="approve-title">Publish to new hires</h2>
          <p>This module is a draft, so new hires can&rsquo;t see it. Approve it when the text is right.</p>
          {flagged.length > 0 && (
            <label className="toggle-row">
              <input type="checkbox" checked={confirmFlagged} onChange={(e) => setConfirmFlagged(e.target.checked)} />
              {flagged.length} section{flagged.length === 1 ? " has" : "s have"} text the manual doesn&rsquo;t support, or wasn&rsquo;t checked. I&rsquo;ve
              reviewed {flagged.length === 1 ? "it" : "them"} and want to approve anyway.
            </label>
          )}
          <div>
            <button type="button" className="btn btn-primary" onClick={approve} disabled={approving || (flagged.length > 0 && !confirmFlagged)}>
              <Icon name="check" />
              {approving ? "Approving…" : "Approve module"}
            </button>
          </div>
        </section>
      )}

      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}

      {module.passages.map((p) => (
        <FirmPassage
          key={p.id}
          passage={p}
          moduleApproved={approved}
          onCritical={(v) => setCritical(p, v)}
          onSaved={(updated, moved) => {
            if (moved) replaceFirmModule({ ...module, status: "draft", passages: module.passages.map((x) => (x.id === updated.id ? updated : x)) });
            else replacePassage(updated);
            showToast(updated.grounding_ok ? "Saved. The text matches the manual." : "Saved, but some text isn't supported by the manual");
          }}
        />
      ))}

      {toast && (
        <div className="toast" role="status">
          {toast}
        </div>
      )}
    </article>
  );
}

function FirmPassage({
  passage,
  moduleApproved,
  onCritical,
  onSaved,
}: {
  passage: AdminPassage;
  moduleApproved: boolean;
  onCritical: (v: boolean) => Promise<void>;
  onSaved: (p: AdminPassage, movedToDraft: boolean) => void;
}) {
  const { firmModules } = useAdmin();
  const [editing, setEditing] = useState(false);
  const [text, setText] = useState(passage.content);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const save = async () => {
    if (
      moduleApproved &&
      !window.confirm("Editing moves this module back to draft. New hires won't see it until you approve it again. Continue?")
    ) {
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const module = firmModules.find((m) => m.passages.some((p) => p.id === passage.id));
      // The backend only accepts text edits on drafts.
      if (moduleApproved && module) await api.updateModule(module.id, { status: "draft" });
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

  const spans = passage.unsupported_spans;

  return (
    <section className="passage">
      <div className="card-header">
        <h2>{passage.heading ?? "Untitled section"}</h2>
        <div className="status-row">
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

      {spans.length > 0 && passage.grounding_ok === false && (
        <div className="form-error">
          Not found in the manual:
          <ul>
            {spans.map((s, i) => (
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
