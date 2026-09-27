import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { BarList, type Bar } from "../../components/BarList";
import { Icon } from "../../components/Icon";
import { Meter } from "../../components/Meter";
import { ErrorPanel } from "../../components/Status";
import { api } from "../../lib/api";
import { useMe } from "../../lib/auth";
import { shortDate } from "../../lib/format";
import type { AdminProgress, EmployeeProgress, FailedQuestion } from "../../lib/types";
import { useAdmin } from "./AdminLayout";

const STAGE: Record<EmployeeProgress["stage"], { label: string; cls: string }> = {
  complete: { label: "Finished", cls: "badge-active" },
  modules_done: { label: "Modules done", cls: "badge-pending" },
  in_progress: { label: "In progress", cls: "badge-pending" },
  not_started: { label: "Not started", cls: "badge-neutral" },
};

const FINAL_CHECK: Record<EmployeeProgress["final_check"]["status"], string> = {
  completed: "Passed",
  in_progress: "In progress",
  not_started: "Unlocked",
  locked: "Locked",
};

interface Struggle {
  key: string;
  moduleId: string;
  moduleTitle: string;
  section: string;
  firstTries: number;
  misses: number;
  questions: number;
}

/** Group first-try results by the module section each question was written from. */
function struggles(questions: FailedQuestion[]): Struggle[] {
  const bySection = new Map<string, Struggle>();
  for (const q of questions) {
    if (!q.link) continue;
    const key = q.link.passage_id;
    const s = bySection.get(key) ?? {
      key,
      moduleId: q.link.module_id,
      moduleTitle: q.link.module_title,
      section: q.link.passage_heading ?? q.link.module_title,
      firstTries: 0,
      misses: 0,
      questions: 0,
    };
    s.firstTries += q.first_tries;
    s.misses += q.first_try_misses;
    s.questions += 1;
    bySection.set(key, s);
  }
  return [...bySection.values()].filter((s) => s.misses > 0).sort((a, b) => b.misses / b.firstTries - a.misses / a.firstTries || b.misses - a.misses);
}

export function AdminDashboard() {
  const me = useMe();
  const { firmModules, baselineModules } = useAdmin();
  const [progress, setProgress] = useState<AdminProgress | null>(null);
  const [failed, setFailed] = useState<FailedQuestion[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    setError(null);
    Promise.all([api.adminProgress(), api.failedQuestions()]).then(
      ([p, f]) => {
        setProgress(p);
        setFailed(f);
      },
      (e: Error) => setError(e.message),
    );
  };
  useEffect(load, []);

  if (error) return <ErrorPanel message={error} onRetry={load} />;
  if (!progress || !failed) return <div className="empty">Loading the dashboard…</div>;

  const employees = progress.employees;
  const count = (stage: EmployeeProgress["stage"]) => employees.filter((e) => e.stage === stage).length;
  const finished = count("complete");
  const scores = employees.map((e) => e.final_check.score).filter((s): s is number => s !== null);
  const avgScore = scores.length ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : null;
  const moduleDone = employees.reduce((a, e) => a + e.completed_required, 0);
  const moduleTotal = employees.reduce((a, e) => a + e.required_modules, 0);

  const sections = struggles(failed);
  const moduleIds = new Set(firmModules.map((m) => m.id));
  const layerOf = (moduleId: string) => (moduleIds.has(moduleId) ? "firm" : "baseline");
  const bars: Bar[] = sections.slice(0, 8).map((s) => ({
    key: s.key,
    label: s.section,
    sublabel: s.moduleTitle,
    value: s.misses / s.firstTries,
    detail: `${s.misses} of ${s.firstTries} first tries missed across ${s.questions} question${s.questions === 1 ? "" : "s"}`,
  }));

  return (
    <>
      <div className="page-head">
        <div className="status-row">
          <span className="badge badge-neutral">{me.firm_name ?? "Your firm"}</span>
        </div>
        <h1>Onboarding overview</h1>
        <p className="lede">Who has finished onboarding, who is still working through it, and which sections new hires find hardest.</p>
      </div>

      <div className="stat-row" role="list">
        <Stat label="New hires" value={employees.length} />
        <Stat label="Finished" value={finished} />
        <Stat label="In progress" value={count("in_progress") + count("modules_done")} />
        <Stat label="Not started" value={count("not_started")} />
        <Stat label="Avg final check" value={avgScore === null ? "—" : `${avgScore}%`} />
      </div>

      <section className="card" aria-labelledby="overall-title">
        <div className="card-header">
          <h2 id="overall-title">Overall progress</h2>
          <span className="small">
            {progress.required_modules} required modules ({firmModules.filter((m) => m.status === "approved").length} firm,{" "}
            {baselineModules.filter((m) => !m.is_hidden).length} AEC baseline shown)
          </span>
        </div>
        <Meter label="New hires who finished onboarding" done={finished} total={employees.length} />
        <Meter label="Required modules completed, all new hires" done={moduleDone} total={moduleTotal} />
      </section>

      <section className="stack" aria-labelledby="employees-title">
        <h2 id="employees-title">New hires</h2>
        {employees.length === 0 ? (
          <div className="card empty">
            <Icon name="users" size={28} />
            <p>No employees yet. New hires appear here once they have a FIRM FLOW login.</p>
          </div>
        ) : (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th scope="col">Name</th>
                  <th scope="col">Started</th>
                  <th scope="col">Status</th>
                  <th scope="col" style={{ minWidth: "12rem" }}>
                    Required modules
                  </th>
                  <th scope="col">Final check</th>
                  <th scope="col">Last active</th>
                </tr>
              </thead>
              <tbody>
                {employees.map((e) => (
                  <tr key={e.profile_id}>
                    <td>
                      <strong>{e.full_name}</strong>
                      <div className="small">{e.email}</div>
                    </td>
                    <td>{shortDate(e.start_date)}</td>
                    <td>
                      <span className={`badge ${STAGE[e.stage].cls}`}>
                        {e.stage === "complete" && <Icon name="check" size={12} />}
                        {STAGE[e.stage].label}
                      </span>
                    </td>
                    <td>
                      <Meter size="sm" label="Done" done={e.completed_required} total={e.required_modules} />
                    </td>
                    <td>
                      {FINAL_CHECK[e.final_check.status]}
                      {e.final_check.score !== null && <div className="small">Score {Math.round(e.final_check.score)}%</div>}
                    </td>
                    <td>{shortDate(e.last_activity_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="card" aria-labelledby="struggle-title">
        <div className="card-header">
          <h2 id="struggle-title">Where new hires struggle</h2>
          <Icon name="alert" size={22} />
        </div>
        {bars.length === 0 ? (
          <div className="empty">
            <p>No missed final check questions yet. Sections appear here once new hires start answering.</p>
          </div>
        ) : (
          <>
            <BarList bars={bars} valueLabel="First-try miss rate" caption="Final check questions missed on the first try, by the module section they test." />
            <div className="status-row small">
              Review a section:
              {sections.slice(0, 8).map((s) => (
                <Link key={s.key} to={`/admin/modules/${layerOf(s.moduleId)}/${s.moduleId}`}>
                  {s.section}
                </Link>
              ))}
            </div>
          </>
        )}
      </section>
    </>
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
