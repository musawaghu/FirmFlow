import { Link } from "react-router-dom";

import { Icon } from "../../components/Icon";
import { Meter } from "../../components/Meter";
import { LayerBadge, ProgressBadge } from "../../components/Status";
import { useMe } from "../../lib/auth";
import { PRIORITIES, PRIORITY_LABEL, percent } from "../../lib/format";
import type { EmployeeModule, Priority } from "../../lib/types";
import { useEmployee } from "./EmployeeLayout";

const PHASE_HINT: Record<Priority, string> = {
  day_1: "Get set up and find your way around.",
  week_1: "Learn how the studio works day to day.",
  later: "Round out the details before your final check.",
};

function nextModule(modules: EmployeeModule[]): EmployeeModule | undefined {
  // The modules arrive in onboarding order (Day 1 first). Continue what's started, else start the next.
  return modules.find((m) => m.progress === "in_progress") ?? modules.find((m) => m.progress !== "completed");
}

export function EmployeeHome() {
  const me = useMe();
  const { list } = useEmployee();
  const firstName = list.full_name.split(" ")[0];
  const pct = percent(list.completed_required, list.required_modules);
  const next = nextModule(list.modules);
  const phases = PRIORITIES.map((p) => {
    const modules = list.modules.filter((m) => m.priority === p);
    return { priority: p, modules, done: modules.filter((m) => m.progress === "completed").length };
  });

  return (
    <>
      <div className="page-head">
        <div className="status-row">
          <span className="badge badge-neutral">{me.firm_name ?? "Your firm"} onboarding</span>
        </div>
        <h1>Welcome, {firstName}.</h1>
        <p className="lede">
          Everything you need for your first month is here, in the order you&rsquo;ll need it. Work through the checklist, and once the required modules
          are done you can take the final check.
        </p>
      </div>

      <div className="row">
        <section className="card grow" aria-labelledby="progress-title">
          <div className="card-header">
            <h2 id="progress-title">Your progress</h2>
            <Icon name="chart" size={22} />
          </div>
          <div className="progress-hero">
            <span className="stat-value">{pct}%</span>
            <span>
              of required modules complete ({list.completed_required} of {list.required_modules})
            </span>
          </div>
          <Meter label="Required modules" done={list.completed_required} total={list.required_modules} />
          <div className="stack" style={{ gap: "0.75rem" }}>
            {phases
              .filter((p) => p.modules.length > 0)
              .map((p) => (
                <Meter key={p.priority} size="sm" label={PRIORITY_LABEL[p.priority]} done={p.done} total={p.modules.length} />
              ))}
          </div>
        </section>

        <section className="card card-alt grow" aria-labelledby="next-title">
          <div className="card-header">
            <h2 id="next-title">{next ? "Up next" : "All modules done"}</h2>
            <Icon name="arrowRight" size={22} />
          </div>
          {next ? (
            <>
              <div className="status-row">
                <ProgressBadge status={next.progress} />
                <LayerBadge layer={next.layer} firmName={me.firm_name} />
              </div>
              <h3>{next.title}</h3>
              {next.summary && <p>{next.summary}</p>}
              <div>
                <Link to={`/app/modules/${next.id}`} className="btn btn-primary">
                  {next.progress === "in_progress" ? "Continue" : "Start"} module
                  <Icon name="arrowRight" />
                </Link>
              </div>
            </>
          ) : (
            <p>You&rsquo;ve completed every module. Nice work.</p>
          )}
          <FinalCheckNote unlocked={list.final_check_unlocked} />
        </section>
      </div>

      <section className="stack" aria-labelledby="checklist-title">
        <div className="page-head">
          <h2 id="checklist-title">Onboarding checklist</h2>
          <p>What to finish on your first day, by the end of your first week, and within your first month.</p>
        </div>
        <div className="grid-cards checklist-grid">
          {phases.map((p) => (
            <article key={p.priority} className="card" aria-labelledby={`phase-${p.priority}`}>
              <div className="card-header">
                <h3 id={`phase-${p.priority}`}>{PRIORITY_LABEL[p.priority]}</h3>
                <span className={`badge ${p.modules.length > 0 && p.done === p.modules.length ? "badge-active" : "badge-neutral"}`}>
                  {p.done}/{p.modules.length}
                </span>
              </div>
              <p className="small">{PHASE_HINT[p.priority]}</p>
              <ul className="checklist">
                {p.modules.map((m) => (
                  <ChecklistItem key={m.id} module={m} />
                ))}
                {p.priority === "later" && (
                  <li className="check-item">
                    <span className="checkbox" aria-hidden="true">
                      {!list.final_check_unlocked && <Icon name="lock" size={12} />}
                    </span>
                    <span className="check-body">
                      <Link to="/app/final-check" className="check-title">
                        Pass the final check
                      </Link>
                      <span className="small">
                        {list.final_check_unlocked ? "Unlocked: every required module is done." : "Unlocks when every required module is done."}
                      </span>
                    </span>
                  </li>
                )}
                {p.modules.length === 0 && p.priority !== "later" && <li className="check-item small">Nothing scheduled here.</li>}
              </ul>
            </article>
          ))}
        </div>
      </section>
    </>
  );
}

function ChecklistItem({ module: m }: { module: EmployeeModule }) {
  const done = m.progress === "completed";
  return (
    <li className={`check-item${done ? " done" : ""}`}>
      <span className={`checkbox${done ? " checked" : ""}`} aria-hidden="true">
        {done && <Icon name="check" size={14} />}
      </span>
      <span className="check-body">
        <Link to={`/app/modules/${m.id}`} className="check-title">
          {m.title}
          <span className="sr-only">{done ? " (done)" : " (to do)"}</span>
        </Link>
        <span className="small">
          {m.is_required ? "Required" : "Optional"}
          {m.progress === "in_progress" ? " · In progress" : ""}
        </span>
      </span>
    </li>
  );
}

function FinalCheckNote({ unlocked }: { unlocked: boolean }) {
  return (
    <div className="status-row small">
      <Icon name={unlocked ? "star" : "lock"} size={16} />
      {unlocked ? (
        <Link to="/app/final-check">Your final check is unlocked. Take it now.</Link>
      ) : (
        "The final check unlocks when every required module is done."
      )}
    </div>
  );
}
