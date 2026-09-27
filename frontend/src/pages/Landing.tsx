import { TopNav } from "../components/TopNav";
import { Icon, type IconName } from "../components/Icon";

// What went wrong in a real architect's first weeks (from the team's architect).
const PROBLEMS: { title: string; body: string; icon: IconName }[] = [
  { title: "Logins that don't work", body: "Day one goes to chasing software licenses and access instead of project work.", icon: "lock" },
  { title: "Help is always in a meeting", body: "The people who know the answer are booked solid, so new hires wait or guess.", icon: "users" },
  { title: "No idea who to ask", body: "Nobody tells you who owns payroll, IT, or the drawing standards.", icon: "question" },
  { title: "Knowledge is scattered", body: "Critical information lives in folders, old emails, and a long handbook nobody reads.", icon: "layers" },
  { title: "Standards needed on day one", body: "You're expected to follow firm drawing standards immediately, but can't find them.", icon: "alert" },
];

const SOLUTIONS: { title: string; body: string; icon: IconName }[] = [
  {
    title: "Your manual, as short modules",
    body: "The firm handbook becomes focused modules ordered by what a new hire needs on Day 1, in Week 1, and in the first month.",
    icon: "book",
  },
  {
    title: "AEC basics plus your firm's way",
    body: "A shared baseline covers practice common to every architecture firm. Where your firm does it differently, your version wins, and employees see a note saying so.",
    icon: "building",
  },
  {
    title: "“Who do I ask?”",
    body: "An assistant answers where-is and who-can-help questions with the right module and a contact card, including a backup when someone is out.",
    icon: "users",
  },
  {
    title: "A final check that teaches",
    body: "A short quiz on the passages you marked critical. A missed question links straight back to the section to review.",
    icon: "check",
  },
  {
    title: "A dashboard for the firm",
    body: "See who has finished, who is stuck, and which sections people miss most, so you can fix the material, not just chase people.",
    icon: "chart",
  },
];

const STEPS: { title: string; body: string }[] = [
  { title: "Upload your manual", body: "An admin uploads the firm handbook as a PDF or Word file." },
  {
    title: "Claude drafts the modules",
    body: "Claude rewrites the manual into clear modules and flags gaps, contradictions, and outdated references. It edits for clarity and never adds facts of its own.",
  },
  {
    title: "Every sentence is checked",
    body: "Each passage is checked against the section of the manual it came from. Anything the source doesn't support is flagged before a person sees it.",
  },
  { title: "An admin approves", body: "Nothing reaches employees until an admin reviews it side by side with the original and approves it." },
  { title: "New hires onboard", body: "Employees follow their checklist, ask the assistant, and pass the final check. The dashboard shows how it's going." },
];

export function Landing() {
  return (
    <>
      <TopNav showPortalLink />
      <main>
        <section className="section section-inverse" aria-labelledby="hero-title">
          <div className="section-inner">
            <span className="eyebrow">Onboarding for architecture firms</span>
            <h1 id="hero-title">New hires productive on day one.</h1>
            <p className="lede">
              FIRM FLOW turns your firm&rsquo;s manual into a guided onboarding path, answers &ldquo;who do I ask?&rdquo; in seconds, and shows you where new
              hires get stuck.
            </p>
            <div className="status-row">
              <a href="#how" className="btn btn-primary">
                See how it works
                <Icon name="arrowRight" />
              </a>
            </div>
          </div>
        </section>

        <section className="section" aria-labelledby="problem-title">
          <div className="section-inner">
            <span className="eyebrow">
              <span className="eyebrow-num">01</span>The problem
            </span>
            <h2 id="problem-title">The first weeks at a design firm are lost to searching.</h2>
            <p className="lede">
              Projects move fast and senior staff are busy. What a new hire needs is spread across servers, systems, and people. These are the problems
              an architect on our team hit in his own onboarding:
            </p>
            <div className="grid-cards">
              {PROBLEMS.map((p) => (
                <article key={p.title} className="card">
                  <span className="card-title">
                    <Icon name={p.icon} size={22} />
                    <h3>{p.title}</h3>
                  </span>
                  <p>{p.body}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="section section-alt" aria-labelledby="solution-title">
          <div className="section-inner">
            <span className="eyebrow">
              <span className="eyebrow-num">02</span>How FIRM FLOW solves it
            </span>
            <h2 id="solution-title">One place for everything a new hire needs.</h2>
            <div className="grid-cards">
              {SOLUTIONS.map((s) => (
                <article key={s.title} className="card">
                  <span className="card-title">
                    <Icon name={s.icon} size={22} />
                    <h3>{s.title}</h3>
                  </span>
                  <p>{s.body}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="section" id="how" aria-labelledby="how-title">
          <div className="section-inner">
            <span className="eyebrow">
              <span className="eyebrow-num">03</span>How we do it
            </span>
            <h2 id="how-title">From handbook to onboarding path, with a person in charge.</h2>
            <ol className="steps">
              {STEPS.map((s, i) => (
                <li key={s.title} className="step">
                  <span className="step-num">{i + 1}</span>
                  <div className="stack" style={{ gap: "0.25rem" }}>
                    <h3>{s.title}</h3>
                    <p>{s.body}</p>
                  </div>
                </li>
              ))}
            </ol>
          </div>
        </section>

        <section className="section section-alt" aria-labelledby="trust-title">
          <div className="section-inner">
            <h2 id="trust-title">The AI never invents your policies.</h2>
            <p className="lede">
              Every passage an employee reads cites the section of your manual it came from and is checked against it, and an admin approves it before anyone sees it. General AEC guidance is
              written once, reviewed by a licensed architect, and always gives way to your firm&rsquo;s own rules.
            </p>
          </div>
        </section>
      </main>
      <footer className="section section-inverse footer">
        <div className="section-inner">
          <span className="small">FIRM FLOW · Built for architecture and engineering firms</span>
        </div>
      </footer>
    </>
  );
}
