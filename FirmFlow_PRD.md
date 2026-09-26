# FIRM FLOW — Product Requirements Document

Sep 26, 2026 · Musa

## Overview

FIRM FLOW is an AI onboarding platform for architecture firms. Firms upload the onboarding material they already have, and FIRM FLOW turns it into clear, interactive modules, a short final check, and an assistant that connects new hires to the right person.

The core promise: the AI never invents anything. It improves what the firm gave it, tests only on approved content, and routes people to real humans from the firm's own directory.

FIRM FLOW has a general AEC baseline that every firm shares, and each firm customizes it with its own policies, standards, projects, and people.

## Problem

Onboarding at architecture firms is static, scattered, and hard to trust, so new hires lose weeks and interrupt senior staff with basic questions. The team's architect member experienced this firsthand. Pain points from the team's research:

- **No sense of importance:** nothing separates what you need on Day 1 from what you need later.
- **Unorganized and unclear:** information lives across an intranet, PDFs, Slack, and people's heads.
- **Corrupted links:** documents point to files and pages that no longer exist.
- **Not interactive:** long static manuals, so engagement drops.
- **Not trackable:** neither the new hire nor the admin can see progress.
- **Tacit BIM knowledge is never taught:** interns aren't shown how to copy Revit files safely, read keynotes, or follow model practices until something breaks.
- **Hard to find the right person:** new hires don't know who handles payroll, PTO, or who leads a given project.

## Goals and non-goals

The hackathon build proves three AI features end to end for one realistic demo firm.

**Goals**

- Turn a messy existing onboarding manual into clean, approved modules without adding content.
- Verify understanding with one short final check at the end of onboarding.
- Answer "where is" and "who can help" questions with real links and real people.
- Let new hires see their own progress and let admins see everyone's progress.

**Non-goals for the hackathon (roadmap)**

- ADP or Paycor integration, paycheck info, i9/w2 forms, clock in/out.
- Mentor/mentee matching and Slack scraping.
- Real multi-tenant accounts for many firms (one demo firm is enough).
- Live calendar availability (static working hours and an out-of-office flag instead).
- A Revit plugin.

## Users

| User | Who they are | What they need | Main flow |
| --- | --- | --- | --- |
| Admin | HR lead, office manager, or BIM manager | Get existing material into usable shape fast, trust it's accurate, see who's stuck | Login → upload manual → review and approve modules → approve quiz → track progress and failed questions |
| New employee | Intern or new architect/designer | Know what matters first, learn firm practices, find answers and people without bothering seniors | Login → dashboard ("Hello {name}", progress) → modules → final check → ask the assistant anytime |

## Feature 1: Manual Enhancer

An admin uploads the firm's old onboarding manual, and FIRM FLOW improves, restructures, and fixes it into modules without adding new content.

**Requirements**

1. Admin can upload a PDF or DOCX manual (demo target: up to about 80 pages).
2. The system extracts the text and splits it into source sections, keeping page numbers.
3. The AI proposes modules using only allowed edits:
    - reorder and group content into modules
    - rewrite for clarity and plain language
    - turn procedures into numbered steps or checklists
    - add headings and short summaries drawn from the text
4. Every enhanced passage links to the source section it came from.
5. A grounding check compares each passage to its source and highlights unsupported text in red.
6. The AI flags issues instead of fixing them: broken links, outdated software versions, contradictions between sections, and missing steps.
7. Admin reviews each module side by side with the original and can approve, edit, or reject it.
8. Admin marks each module's priority (Day 1, Week 1, Later) and marks which sections are critical for the final check.
9. Only approved modules are visible to employees.

**Acceptance criteria**

- No approved module contains a fact, number, or policy absent from the source.
- Every flagged broken link appears in the admin's issue list.
- An admin can go from upload to one approved module in under 5 minutes.

## Feature 2: Final Onboarding Check

One short check at the end of all onboarding: 5 to 7 questions, under 5 minutes, focused on what matters most.

**Requirements**

1. The check unlocks only after all required modules are complete.
2. Questions come only from sections the admin marked critical in approved modules.
3. Mix: 2 to 3 short scenario questions answered in free text, the rest multiple choice.
4. The AI grades free-text answers against a rubric built from the source section.
5. After each answer, the employee sees instant feedback and a link to the exact module section.
6. Employees retry only the questions they missed.
7. Admin approves the question bank once before any employee sees it.
8. Admin sees a summary of the most-failed questions across employees.

**Example scenario**

You need a copy of the project's central Revit model to test a design option. What do you do? A correct answer follows the firm's worksharing rule, such as opening with "Detach from Central" instead of copying the file in File Explorer.

**Acceptance criteria**

- A new hire finishes the check in under 5 minutes.
- Every question traces to an approved, critical section.
- A missed question always links back to the right module section.

## Feature 3: Who Do I Ask? Assistant

A chatbot that answers "where is" questions with a link to the right module, and "who can help" questions with a real person to contact.

**Example questions**

- "Where is the company PTO policy?"
- "I had a problem with my payroll, who can I ask?"
- "Who is the design manager for this project?"
- "Who is responsible for BIM engineering?"

**Requirements**

1. "Where is" answers return a one-line summary plus a link to the approved module section.
2. "Who can help" answers return a contact card: name, title, email, working hours, and whether they are in today.
3. If the primary contact is out of office, the card also shows the backup contact.
4. A "Contact them" button opens a pre-drafted email the employee can edit and send.
5. The AI looks people up through tool calls on the directory tables; names and emails are never generated.
6. When no confident match exists, the assistant routes to the firm's default contact (office manager or HR).
7. For personal matters like payroll, the assistant routes without asking for details in chat.
8. Questions the assistant couldn't answer are logged for the admin.

**Acceptance criteria**

- Every contact card matches a real directory row exactly.
- Project-role questions return the person assigned to that role on that project.
- Unmatched questions never return a guessed person.

## AI principles and guardrails

Every AI output is grounded in the firm's own material, traceable to a source, and approved by a human before employees see it.

- **Enhance, never invent:** the AI may restructure and rewrite, never add facts or policies.
- **Trace everything:** each module passage and quiz question links to its source section.
- **Flag, don't fix:** problems go to the admin as issues, not silent AI edits.
- **Humans approve:** modules and the question bank need admin approval.
- **Structured lookups for people:** contacts come from database rows, not generated text.
- **Privacy:** each firm's data is stored separately and is not used to train models; personal HR matters are routed, not discussed.

## Technical approach

A React frontend talks to a Python FastAPI backend, which stores everything in Supabase and calls an LLM for enhancement, grading, and chat.

| Layer | Choice |
| --- | --- |
| Frontend | React + Vite, Tailwind CSS, shadcn/ui, react-diff-viewer |
| Backend | Python, FastAPI |
| Database, auth, storage | Supabase (Postgres) |
| AI | Claude API (or sponsor-provided model), with tool calling |
| Document parsing | PyMuPDF (PDF), python-docx (DOCX) |
| Hosting | Vercel (frontend), Render or Railway (backend) |

**Data model** (full SQL in the repo): firms, profiles, manuals, source sections, modules, module passages, issues, module progress, quiz questions, quiz attempts, quiz answers, people, responsibilities, projects, project roles, chat logs.

**No vector database for the MVP.** A demo firm's manual and module index fit in the model's context. Embeddings are the plan for large firms.

## Demo, metrics, and roadmap

**3-minute demo script**

1. Admin uploads a messy sample manual; the side-by-side view shows enhanced modules and flagged broken links.
2. Admin approves a module and marks it Day 1 and critical.
3. Intern logs in, sees "Hello {name}" and progress, and completes a module.
4. Intern asks "I had a problem with my payroll, who can help?" and gets a contact card.
5. Intern takes the final check, misses the Revit scenario, and gets a link back to the BIM module.
6. Admin dashboard shows progress and the most-failed question.

**Success metrics (pilot)**

- Time for a new hire to finish onboarding.
- Questions to senior staff in the first month.
- Share of assistant questions answered without a fallback.
- Model-corruption or file-handling incidents by new hires.

**Roadmap**

- ADP / Paycor and live calendar integration.
- Slack and intranet ingestion.
- Mentor/mentee matching.
- Revit plugin that opens firm guidance inside Revit.
- Multi-firm accounts and embeddings search for large firms.

**Open questions**

- [ ] Which three or four modules will we fully write for the demo?
- [ ] Who writes the sample manual and fake directory data?
- [ ] Which LLM do sponsor credits cover?
