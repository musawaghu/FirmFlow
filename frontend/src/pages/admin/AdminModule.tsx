import { useState } from "react";
import { useParams } from "react-router-dom";

import { Icon } from "../../components/Icon";
import { PassageText } from "../../components/PassageText";
import { ErrorPanel, PriorityBadge } from "../../components/Status";
import { api } from "../../lib/api";
import { useMe } from "../../lib/auth";
import { PRIORITIES, PRIORITY_LABEL } from "../../lib/format";
import type { AdminModule as FirmModule, BaselineModule, Priority } from "../../lib/types";
import { useAdmin } from "./AdminLayout";
import { CriticalToggle, FirmModuleBody, Toast, useToast } from "./FirmModuleBody";

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

      <Toast message={toast} />
    </article>
  );
}

// ---------------------------------------------------------------------------
// The firm's own module: settings, critical passages, and text edits
// ---------------------------------------------------------------------------

function FirmEditor({ module }: { module: FirmModule }) {
  const { replaceFirmModule } = useAdmin();
  const [toast, showToast] = useToast();
  const approved = module.status === "approved";

  const saveSettings = async (s: Settings) => {
    replaceFirmModule(await api.updateModule(module.id, { priority: s.priority, is_required: s.is_required }));
    showToast("Settings saved");
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
      <FirmModuleBody module={module} onChange={replaceFirmModule} />
      <Toast message={toast} />
    </article>
  );
}
