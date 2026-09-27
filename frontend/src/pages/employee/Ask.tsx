import { useEffect, useRef, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import { Icon } from "../../components/Icon";
import { PassageText } from "../../components/PassageText";
import { api } from "../../lib/api";
import { useMe } from "../../lib/auth";
import { shortDate } from "../../lib/format";
import type { ChatReply, ContactCard } from "../../lib/types";

const MAX_QUESTION_CHARS = 500; // backend routers/chat.py

const SUGGESTIONS = [
  "My Revit license isn't working. Who do I ask?",
  "Where are the drawing standards?",
  "Who handles payroll?",
  "How do I submit my timesheet?",
  "Who can I talk to about benefits?",
];

interface Turn {
  question: string;
  reply: ChatReply | null; // null while waiting
  error?: string;
}

// The conversation survives moving between pages in this tab.
function storageKey(userId: string) {
  return `firmflow.ask.${userId}`;
}

function loadTurns(userId: string): Turn[] {
  try {
    const raw = sessionStorage.getItem(storageKey(userId));
    return raw ? (JSON.parse(raw) as Turn[]).filter((t) => t.reply) : [];
  } catch {
    return [];
  }
}

export function Ask() {
  const me = useMe();
  const [turns, setTurns] = useState<Turn[]>(() => loadTurns(me.id));
  const [question, setQuestion] = useState("");
  const busy = turns.some((t) => t.reply === null && !t.error);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    try {
      sessionStorage.setItem(storageKey(me.id), JSON.stringify(turns.filter((t) => t.reply)));
    } catch {
      // Storage can be unavailable (private mode); the conversation just won't persist.
    }
    endRef.current?.scrollIntoView({ block: "end" });
  }, [turns, me.id]);

  const ask = async (text: string) => {
    const q = text.trim();
    if (!q || busy) return;
    setQuestion("");
    setTurns((t) => [...t, { question: q, reply: null }]);
    try {
      const reply = await api.ask(q);
      setTurns((t) => t.map((turn, i) => (i === t.length - 1 ? { ...turn, reply } : turn)));
    } catch (e) {
      setTurns((t) => t.map((turn, i) => (i === t.length - 1 ? { ...turn, error: (e as Error).message } : turn)));
    }
  };

  const submit = (e: FormEvent) => {
    e.preventDefault();
    void ask(question);
  };

  return (
    <div className="stack module-page">
      <div className="page-head">
        <div className="status-row">
          <span className="badge badge-inverse">Assistant</span>
        </div>
        <h1>Who do I ask?</h1>
        <p className="lede">
          Ask where something is or who can help. You&rsquo;ll get the right section of your onboarding and a contact card, with a backup when someone is
          out.
        </p>
      </div>

      {turns.length === 0 && (
        <div className="card card-alt">
          <span className="label">Try asking</span>
          <div className="status-row">
            {SUGGESTIONS.map((s) => (
              <button key={s} type="button" className="btn btn-secondary btn-small" onClick={() => ask(s)}>
                {s}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="stack" aria-live="polite">
        {turns.map((t, i) => (
          <div key={i} className="stack turn">
            <div className="you-asked">
              <span className="label">You asked</span>
              <p>{t.question}</p>
            </div>
            {t.error ? (
              <p className="form-error" role="alert">
                {t.error}
              </p>
            ) : t.reply ? (
              <Answer reply={t.reply} />
            ) : (
              <div className="card">Looking through your onboarding and the staff directory…</div>
            )}
          </div>
        ))}
        <div ref={endRef} />
      </div>

      <form className="card ask-form" onSubmit={submit}>
        <label htmlFor="ask-input" className="label">
          Your question
        </label>
        <div className="ask-row">
          <input
            id="ask-input"
            className="input"
            placeholder="e.g. Who do I ask about a plotter that won't print?"
            maxLength={MAX_QUESTION_CHARS}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            disabled={busy}
            autoComplete="off"
          />
          <button type="submit" className="btn btn-primary" disabled={busy || !question.trim()}>
            {busy ? "Asking…" : "Ask"}
          </button>
        </div>
        {turns.length > 0 && (
          <button type="button" className="btn btn-secondary btn-small ask-clear" onClick={() => setTurns([])} disabled={busy}>
            Clear conversation
          </button>
        )}
      </form>
    </div>
  );
}

function Answer({ reply }: { reply: ChatReply }) {
  return (
    <section className="card answer">
      {reply.used_fallback && (
        <div className="status-row small">
          <Icon name="question" size={16} />I couldn&rsquo;t find this in your onboarding material, so here&rsquo;s who can help.
        </div>
      )}
      <PassageText text={reply.answer} />
      {reply.links.length > 0 && (
        <div className="stack" style={{ gap: "0.375rem" }}>
          <span className="label">In your onboarding</span>
          {reply.links.map((l) => (
            <Link key={l.passage_id} to={`/app/modules/${l.module_id}#passage-${l.passage_id}`} className="status-row">
              <Icon name="book" size={16} />
              {l.passage_heading ? `${l.passage_heading} · ` : ""}
              {l.module_title}
            </Link>
          ))}
        </div>
      )}
      {reply.contacts.length > 0 && (
        <div className="grid-cards contacts">
          {reply.contacts.map((c) => (
            <Contact key={c.person_id} contact={c} />
          ))}
        </div>
      )}
    </section>
  );
}

function Contact({ contact: c, isBackup = false }: { contact: ContactCard; isBackup?: boolean }) {
  const first = c.name.split(" ")[0];
  return (
    <article className={`card contact${isBackup ? " card-alt" : ""}`}>
      <div className="card-header">
        <div>
          {isBackup && <span className="label">Backup</span>}
          <h3>{c.name}</h3>
          <span className="small">
            {c.title} · {c.department}
          </span>
        </div>
        {c.is_in_today ? (
          <span className="badge badge-active">In today</span>
        ) : (
          <span className="badge badge-pending">{c.out_of_office_until ? `Out until ${shortDate(c.out_of_office_until)}` : "Not in today"}</span>
        )}
      </div>
      <p>{c.reason}</p>
      <dl className="contact-meta small">
        <div>
          <dt>Hours</dt>
          <dd>{c.working_hours}</dd>
        </div>
        {c.phone_ext && (
          <div>
            <dt>Ext.</dt>
            <dd>{c.phone_ext}</dd>
          </div>
        )}
        <div>
          <dt>Email</dt>
          <dd>{c.email}</dd>
        </div>
      </dl>
      <div>
        <a className="btn btn-primary btn-small" href={c.mailto}>
          Email {first}
        </a>
      </div>
      <span className="small">Opens a drafted email you can edit before sending.</span>
      {c.backup && (
        <>
          <span className="small">
            <strong>{first} is out today.</strong> Try their backup:
          </span>
          <Contact contact={c.backup} isBackup />
        </>
      )}
    </article>
  );
}
