import { useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import { Icon } from "../../components/Icon";
import { Meter } from "../../components/Meter";
import { ErrorPanel } from "../../components/Status";
import { api, ApiError } from "../../lib/api";
import { shortDate } from "../../lib/format";
import type { AnswerResult, Attempt, AttemptQuestion, SectionLink } from "../../lib/types";
import { useEmployee } from "./EmployeeLayout";

const MAX_ANSWER_CHARS = 2000; // backend services/quiz.py

export function FinalCheck() {
  const { list } = useEmployee();
  const [attempt, setAttempt] = useState<Attempt | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);

  useEffect(() => {
    api.currentAttempt().then(
      (a) => {
        setAttempt(a);
        setLoaded(true);
      },
      (e: ApiError) => {
        if (e.status !== 404) setError(e.message);
        setLoaded(true);
      },
    );
  }, []);

  if (!list.final_check_unlocked) return <Locked />;
  if (error && !attempt) return <ErrorPanel message={error} />;
  if (!loaded) return <div className="empty">Loading your final check…</div>;

  const start = async () => {
    setStarting(true);
    setError(null);
    try {
      setAttempt(await api.startAttempt());
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setStarting(false);
    }
  };

  const head = (
    <div className="page-head">
      <div className="status-row">
        <span className="badge badge-inverse">Final check</span>
      </div>
      <h1>Final onboarding check</h1>
      <p className="lede">
        A short check on the sections your firm marked as critical. If you miss a question, review the section it links to and try again. Your score counts
        first tries.
      </p>
    </div>
  );

  if (!attempt || (attempt.status === "completed" && starting)) {
    return (
      <div className="stack module-page">
        {head}
        <div className="card card-alt">
          <p>You&rsquo;ve finished every required module, so the final check is unlocked. It takes about ten minutes.</p>
          {error && (
            <p className="form-error" role="alert">
              {error}
            </p>
          )}
          <div>
            <button type="button" className="btn btn-primary" onClick={start} disabled={starting}>
              {starting ? "Starting…" : "Start the final check"}
              <Icon name="arrowRight" />
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (attempt.status === "completed") {
    return (
      <div className="stack module-page">
        {head}
        <Result attempt={attempt} />
        <div className="status-row">
          <Link to="/app" className="btn btn-secondary">
            Back to onboarding home
          </Link>
          <button type="button" className="btn btn-secondary" onClick={start} disabled={starting}>
            Take it again
          </button>
        </div>
      </div>
    );
  }

  const correct = attempt.questions.filter((q) => q.state === "correct").length;
  return (
    <div className="stack module-page">
      {head}
      <div className="card">
        <Meter label="Answered correctly" done={correct} total={attempt.questions.length} />
      </div>
      {attempt.questions.map((q, i) => (
        <QuestionCard key={q.id} attemptId={attempt.id} question={q} number={i + 1} total={attempt.questions.length} onAnswered={(r) => setAttempt(r.attempt)} />
      ))}
    </div>
  );
}

function Locked() {
  const { list } = useEmployee();
  const remaining = list.modules.filter((m) => m.is_required && m.progress !== "completed");
  return (
    <div className="stack module-page">
      <div className="page-head">
        <div className="status-row">
          <span className="badge badge-neutral">
            <Icon name="lock" size={12} />
            Locked
          </span>
        </div>
        <h1>Final onboarding check</h1>
        <p className="lede">The final check unlocks once every required module is done. You have {remaining.length} to go:</p>
      </div>
      <div className="card">
        <ul className="checklist">
        {remaining.map((m) => (
          <li key={m.id} className="check-item">
            <span className="checkbox" aria-hidden="true" />
            <span className="check-body">
              <Link to={`/app/modules/${m.id}`} className="check-title">
                {m.title}
              </Link>
            </span>
          </li>
        ))}
        </ul>
      </div>
    </div>
  );
}

function Result({ attempt }: { attempt: Attempt }) {
  const score = Math.round(attempt.score ?? 0);
  const firstTry = attempt.questions.filter((q) => q.tries === 1).length;
  return (
    <section className="card card-alt" aria-labelledby="result-title">
      <div className="card-header">
        <h2 id="result-title">You&rsquo;ve completed onboarding</h2>
        <Icon name="star" size={24} />
      </div>
      <div className="progress-hero">
        <span className="stat-value">{score}%</span>
        <span>
          right on the first try ({firstTry} of {attempt.questions.length}), finished {shortDate(attempt.completed_at)}
        </span>
      </div>
      <p>Every question is now answered correctly. Your admin can see that you&rsquo;ve finished.</p>
    </section>
  );
}

function ReviewLink({ link }: { link: SectionLink }) {
  return (
    <Link to={`/app/modules/${link.module_id}#passage-${link.passage_id}`} className="status-row">
      <Icon name="book" size={16} />
      Review &ldquo;{link.passage_heading ?? link.module_title}&rdquo; in {link.module_title}
    </Link>
  );
}

function QuestionCard({
  attemptId,
  question: q,
  number,
  total,
  onAnswered,
}: {
  attemptId: string;
  question: AttemptQuestion;
  number: number;
  total: number;
  onAnswered: (r: AnswerResult) => void;
}) {
  const [choice, setChoice] = useState<number | null>(null);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnswerResult | null>(null);
  const done = q.state === "correct";
  const scenario = q.type === "scenario";

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const r = await api.answer(attemptId, scenario ? { question_id: q.id, answer_text: text } : { question_id: q.id, selected_choice: choice ?? undefined });
      setResult(r);
      onAnswered(r);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const ready = scenario ? text.trim().length > 0 : choice !== null;
  const link = result?.link ?? q.link;

  return (
    <form className="passage question" onSubmit={submit} aria-labelledby={`q-${q.id}`}>
      <div className="card-header">
        <span className="status-row small">
          <strong>
            Question {number} of {total}
          </strong>
          · {scenario ? "Scenario: answer in your own words" : "Multiple choice"}
        </span>
        {done ? (
          <span className="badge badge-active">
            <Icon name="check" size={12} />
            Correct
          </span>
        ) : q.state === "missed" ? (
          <span className="badge badge-pending">Try again</span>
        ) : null}
      </div>
      <h2 id={`q-${q.id}`} className="question-prompt">
        {q.prompt}
      </h2>

      {!done &&
        (scenario ? (
          <div className="field">
            <label htmlFor={`a-${q.id}`}>Your answer</label>
            <textarea
              id={`a-${q.id}`}
              className="input textarea"
              rows={5}
              maxLength={MAX_ANSWER_CHARS}
              value={text}
              onChange={(e) => setText(e.target.value)}
              disabled={busy}
            />
            <span className="small">
              {text.length} / {MAX_ANSWER_CHARS}
            </span>
          </div>
        ) : (
          <fieldset className="choices" disabled={busy}>
            <legend className="sr-only">Choose one answer</legend>
            {q.choices?.map((c, i) => (
              <label key={i} className={`choice${choice === i ? " selected" : ""}`}>
                <input type="radio" name={`q-${q.id}`} checked={choice === i} onChange={() => setChoice(i)} />
                <span>{c}</span>
              </label>
            ))}
          </fieldset>
        ))}

      {result && (
        <div className={`feedback ${result.is_correct ? "feedback-correct" : "feedback-missed"}`} role="status">
          <strong>{result.is_correct ? "Correct." : "Not quite."}</strong> {result.feedback.replace(/^Not quite\.\s*/, "")}
        </div>
      )}
      {!done && link && <ReviewLink link={link} />}
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}

      {!done && (
        <div>
          <button type="submit" className="btn btn-primary" disabled={!ready || busy}>
            {busy ? (scenario ? "Grading…" : "Checking…") : q.state === "missed" ? "Check again" : "Check answer"}
          </button>
        </div>
      )}
    </form>
  );
}
