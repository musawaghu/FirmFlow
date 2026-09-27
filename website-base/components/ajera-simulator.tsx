"use client"

import { useEffect, useMemo, useState } from "react"

type Mode = "guided" | "interactive"
type Screen = "home" | "loading" | "success"
type StepKey = "meeting" | "selectProject" | "logHours" | "submit"

interface ProjectRow {
  id: string
  code: string
  name: string
  phase: string
  isAssigned?: boolean
}

const PROJECTS: ProjectRow[] = [
  { id: "p-riverside", code: "24-118", name: "Riverside Tower", phase: "CD — Interiors", isAssigned: true },
  { id: "p-oakview", code: "23-092", name: "Oakview Medical Center", phase: "CA" },
  { id: "p-greenline", code: "24-041", name: "Greenline Transit Hub", phase: "SD" },
  { id: "p-overhead", code: "OH-100", name: "Studio / Overhead", phase: "General" },
]

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
const TODAY_INDEX = 3
const TODAY_LABEL = "Thu, Sep 24"

const STEP_TEXT: Record<StepKey, { title: string; body: string }> = {
  meeting: {
    title: "Step 1 — Log your meeting time",
    body: "Under Today's Entries, enter 0.5 in the hours box for Studio Meeting and add a short note about it.",
  },
  selectProject: {
    title: "Step 2 — Find your project in the timeline",
    body: "Scroll to the timeline below and click the row for the project you're assigned to (it's highlighted).",
  },
  logHours: {
    title: "Step 3 — Log your project hours",
    body: `Enter the hours you worked today in the ${DAYS[TODAY_INDEX]} column for that project.`,
  },
  submit: {
    title: "Step 4 — Submit the day",
    body: "Click Submit in the top-left of the toolbar to submit today's timesheet.",
  },
}

interface AjeraSimulatorProps {
  onComplete?: () => void
}

export function AjeraSimulator({ onComplete }: AjeraSimulatorProps) {
  const [mode, setMode] = useState<Mode>("guided")
  const [screen, setScreen] = useState<Screen>("home")
  const [meetingHours, setMeetingHours] = useState("")
  const [meetingNote, setMeetingNote] = useState("")
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null)
  const [projectHours, setProjectHours] = useState<Record<string, string>>({})
  const [feedback, setFeedback] = useState<{ tone: "error" | "info"; msg: string } | null>(null)

  const selectedProject = PROJECTS.find((p) => p.id === selectedProjectId) ?? null
  const meetingLogged = meetingHours.trim().length > 0 && Number(meetingHours) > 0 && meetingNote.trim().length > 0
  const currentProjectHoursStr = selectedProjectId ? (projectHours[selectedProjectId] ?? "") : ""
  const projectLogged = !!selectedProjectId && Number(currentProjectHoursStr) > 0

  const currentStep: StepKey = useMemo(() => {
    if (!meetingLogged) return "meeting"
    if (!selectedProjectId) return "selectProject"
    if (!projectLogged) return "logHours"
    return "submit"
  }, [meetingLogged, selectedProjectId, projectLogged])

  useEffect(() => {
    if (screen === "loading") {
      const t = setTimeout(() => setScreen("success"), 1400)
      return () => clearTimeout(t)
    }
  }, [screen])

  useEffect(() => {
    if (screen === "success") onComplete?.()
  }, [screen, onComplete])

  const guided = mode === "guided"
  const ring = (step: StepKey) =>
    guided && currentStep === step && screen === "home"
      ? "ring-2 ring-offset-2 ring-offset-white ring-[#e8792c] animate-pulse"
      : ""

  function reset() {
    setScreen("home")
    setMeetingHours("")
    setMeetingNote("")
    setSelectedProjectId(null)
    setProjectHours({})
    setFeedback(null)
  }

  function handleSelectProject(project: ProjectRow) {
    setSelectedProjectId(project.id)
    if (project.isAssigned) {
      setFeedback({
        tone: "info",
        msg: `Good — ${project.name} is your assigned project. Now enter your hours in the ${DAYS[TODAY_INDEX]} column.`,
      })
    } else {
      setFeedback({
        tone: "error",
        msg: `${project.name} isn't your assigned project. Look for the highlighted row instead.`,
      })
    }
  }

  function handleHoursChange(projectId: string, value: string) {
    setProjectHours((prev) => ({ ...prev, [projectId]: value }))
  }

  function handleSubmit() {
    if (!meetingLogged) {
      setFeedback({
        tone: "error",
        msg: "Log your meeting time first — enter hours (e.g. 0.5) and a short note under Today's Entries.",
      })
      return
    }
    if (!selectedProjectId) {
      setFeedback({ tone: "error", msg: "Select your assigned project in the timeline before submitting." })
      return
    }
    if (!selectedProject?.isAssigned) {
      setFeedback({ tone: "error", msg: "That row isn't your assigned project. Choose the highlighted project instead." })
      return
    }
    if (!projectLogged) {
      setFeedback({
        tone: "error",
        msg: `Enter your hours for ${selectedProject.name} in the ${DAYS[TODAY_INDEX]} column.`,
      })
      return
    }
    setFeedback(null)
    setScreen("loading")
  }

  const totalToday = (Number(meetingHours) || 0) + (Number(currentProjectHoursStr) || 0)

  return (
    <section className="rounded-xl border border-border bg-card p-4 sm:p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="font-semibold text-foreground">Interactive: log &amp; submit your daily timesheet</h2>
          <p className="text-sm text-muted-foreground">
            Practice logging your hours inside a simulated Ajera Time &amp; Expense screen.
          </p>
        </div>
        <div className="inline-flex rounded-lg border border-border bg-muted p-0.5 text-sm">
          <button
            type="button"
            onClick={() => {
              setMode("guided")
              reset()
            }}
            className={`rounded-md px-3 py-1.5 font-medium transition-colors ${
              mode === "guided" ? "bg-card text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"
            }`}
          >
            Guided walkthrough
          </button>
          <button
            type="button"
            onClick={() => {
              setMode("interactive")
              reset()
            }}
            className={`rounded-md px-3 py-1.5 font-medium transition-colors ${
              mode === "interactive"
                ? "bg-card text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            Interactive practice
          </button>
        </div>
      </div>

      {/* Instruction banner */}
      {screen === "home" && (
        <div className="mt-4 flex items-start gap-3 rounded-lg border border-primary/30 bg-primary/5 px-4 py-3">
          <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-foreground">
            {currentStep === "meeting" ? "1" : currentStep === "selectProject" ? "2" : currentStep === "logHours" ? "3" : "4"}
          </span>
          <div>
            <p className="text-sm font-semibold text-foreground">{STEP_TEXT[currentStep].title}</p>
            <p className="text-sm text-muted-foreground">{STEP_TEXT[currentStep].body}</p>
          </div>
        </div>
      )}

      {/* Feedback toast */}
      {feedback && screen === "home" && (
        <div
          className={`mt-3 rounded-lg px-4 py-2.5 text-sm ${
            feedback.tone === "error"
              ? "border border-destructive/30 bg-destructive/10 text-destructive"
              : "border border-primary/30 bg-primary/5 text-foreground"
          }`}
        >
          {feedback.msg}
        </div>
      )}

      {/* Simulated Ajera window */}
      <div className="mt-4 overflow-hidden rounded-lg border border-[#0f2a44] shadow-sm">
        {screen === "home" && (
          <div className="bg-white">
            {/* title bar */}
            <div className="flex flex-wrap items-center justify-between gap-2 bg-[#0f2a44] px-3 py-2 text-white">
              <div className="flex items-center gap-2 text-[13px] font-semibold">
                <AjeraMark />
                Ajera — Time &amp; Expense
              </div>
              <span className="text-[11px] text-white/70">Week of Sep 21 – Sep 27, 2026</span>
            </div>

            {/* toolbar — Submit button top-left */}
            <div className="flex flex-wrap items-center gap-2 border-b border-[#e0e0e0] bg-[#f4f6f8] px-3 py-2">
              <div className={`rounded ${ring("submit")}`}>
                <button
                  type="button"
                  onClick={handleSubmit}
                  className="rounded border border-[#c96419] bg-[#e8792c] px-4 py-1.5 text-[12px] font-semibold text-white transition-colors hover:bg-[#d96c22]"
                >
                  Submit
                </button>
              </div>
              <button
                type="button"
                onClick={() => setFeedback({ tone: "info", msg: "Draft saved locally (demo only)." })}
                className="rounded border border-[#c8c8c8] bg-white px-3 py-1.5 text-[12px] text-[#333] transition-colors hover:bg-[#ececec]"
              >
                Save Draft
              </button>
              <span className="ml-auto text-[11px] text-[#556]">
                Total logged today: <strong className="text-[#1a1a1a]">{totalToday.toFixed(2)} hrs</strong>
              </span>
            </div>

            {/* today's entries — meeting logging */}
            <div className="border-b border-[#e0e0e0] px-3 py-3">
              <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-[#667]">
                Today&apos;s Entries — {TODAY_LABEL}
              </p>
              <div
                className={`grid grid-cols-1 gap-2 rounded border border-[#dfe3e6] bg-[#fafbfc] p-3 sm:grid-cols-[1fr_90px_1.4fr] sm:items-center ${ring(
                  "meeting",
                )}`}
              >
                <div className="flex items-center gap-2 text-[12px] text-[#333]">
                  <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded bg-[#0f2a44] text-[9px] font-bold text-white">
                    OH
                  </span>
                  Studio Meeting (Overhead)
                </div>
                <input
                  value={meetingHours}
                  onChange={(e) => setMeetingHours(e.target.value)}
                  placeholder="0.5"
                  inputMode="decimal"
                  aria-label="Meeting hours"
                  className="rounded border border-[#c8c8c8] px-2 py-1 text-[12px] text-[#1a1a1a] focus:border-[#0696d7] focus:outline-none"
                />
                <input
                  value={meetingNote}
                  onChange={(e) => setMeetingNote(e.target.value)}
                  placeholder="Note, e.g. Monday studio meeting"
                  aria-label="Meeting note"
                  className="rounded border border-[#c8c8c8] px-2 py-1 text-[12px] text-[#1a1a1a] focus:border-[#0696d7] focus:outline-none"
                />
              </div>
            </div>

            {/* timeline / weekly grid */}
            <div className="px-3 py-3">
              <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-[#667]">
                Timeline — your projects
              </p>
              <div className={`overflow-x-auto rounded border border-[#dfe3e6] ${ring("selectProject")}`}>
                <table className="w-full min-w-[560px] border-collapse text-[12px]">
                  <thead>
                    <tr className="bg-[#eef1f4] text-[#556]">
                      <th className="px-2 py-1.5 text-left font-semibold">Project / Phase</th>
                      {DAYS.map((d, i) => (
                        <th
                          key={d}
                          className={`px-2 py-1.5 text-center font-semibold ${
                            i === TODAY_INDEX ? "bg-[#dcecf8] text-[#0f2a44]" : ""
                          }`}
                        >
                          {d}
                          {i === TODAY_INDEX ? " •" : ""}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {PROJECTS.map((p) => {
                      const isSel = selectedProjectId === p.id
                      const highlight =
                        guided && currentStep === "selectProject" && p.isAssigned && !isSel
                          ? "ring-2 ring-inset ring-[#e8792c] animate-pulse"
                          : ""
                      return (
                        <tr
                          key={p.id}
                          onClick={() => handleSelectProject(p)}
                          className={`cursor-pointer border-t border-[#eceff1] transition-colors ${
                            isSel ? "bg-[#fdeee1]" : "hover:bg-[#f7f9fa]"
                          } ${highlight}`}
                        >
                          <td className="px-2 py-1.5">
                            <div className="font-medium text-[#1a1a1a]">
                              {p.code} — {p.name}
                            </div>
                            <div className="text-[10px] text-[#8a94a0]">
                              {p.phase}
                              {p.isAssigned ? " · Assigned to you" : ""}
                            </div>
                          </td>
                          {DAYS.map((d, i) => (
                            <td
                              key={d}
                              className={`px-1 py-1.5 text-center ${i === TODAY_INDEX ? "bg-[#f5faff]" : ""}`}
                            >
                              {i === TODAY_INDEX && isSel ? (
                                <input
                                  value={projectHours[p.id] ?? ""}
                                  onChange={(e) => handleHoursChange(p.id, e.target.value)}
                                  onClick={(e) => e.stopPropagation()}
                                  placeholder="0"
                                  inputMode="decimal"
                                  aria-label={`Hours for ${p.name} on ${d}`}
                                  className={`w-12 rounded border border-[#c8c8c8] px-1 py-0.5 text-center text-[12px] focus:border-[#0696d7] focus:outline-none ${ring(
                                    "logHours",
                                  )}`}
                                />
                              ) : i === TODAY_INDEX ? (
                                <span className="text-[#c3cbd2]">—</span>
                              ) : (
                                <span className="text-[#c3cbd2]">·</span>
                              )}
                            </td>
                          ))}
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* LOADING */}
        {screen === "loading" && (
          <div className="flex min-h-[360px] flex-col items-center justify-center bg-[#e9edf0]/95">
            <div className="h-9 w-9 animate-spin rounded-full border-4 border-[#cdd6dc] border-t-[#e8792c]" />
            <p className="mt-4 text-[13px] font-medium text-[#4a5259]">Submitting timesheet…</p>
            <p className="mt-1 text-[12px] text-[#8a9299]">{TODAY_LABEL} · 2 entries</p>
          </div>
        )}

        {/* SUCCESS */}
        {screen === "success" && (
          <div className="flex min-h-[360px] flex-col items-center bg-[#e9edf0] p-6 text-center">
            <span className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-[#2e9e5b] text-white">
              <CheckIcon />
            </span>
            <p className="mt-4 text-[15px] font-semibold text-[#2b2b2b]">Timesheet submitted for {TODAY_LABEL}</p>
            <p className="mt-1 max-w-sm text-[13px] text-[#5a6169]">
              You logged your meeting time, entered hours against your assigned project, and submitted the day —
              exactly right.
            </p>

            <div className="mt-5 w-full max-w-md rounded-lg border border-[#d7dde2] bg-white text-left">
              <div className="flex items-center justify-between border-b border-[#eceff1] px-4 py-2 text-[11px] font-semibold uppercase tracking-wide text-[#8a9299]">
                <span>Entry</span>
                <span>Hours</span>
              </div>
              <div className="flex items-center justify-between px-4 py-2.5 text-[13px] text-[#333]">
                <div>
                  <p className="font-medium">Studio Meeting (Overhead)</p>
                  <p className="text-[12px] text-[#8a9299]">{meetingNote}</p>
                </div>
                <span className="font-semibold">{Number(meetingHours).toFixed(2)}</span>
              </div>
              <div className="flex items-center justify-between border-t border-[#eceff1] px-4 py-2.5 text-[13px] text-[#333]">
                <div>
                  <p className="font-medium">{selectedProject?.name}</p>
                  <p className="text-[12px] text-[#8a9299]">{selectedProject?.phase}</p>
                </div>
                <span className="font-semibold">{Number(currentProjectHoursStr).toFixed(2)}</span>
              </div>
              <div className="flex items-center justify-between border-t border-[#eceff1] bg-[#fafbfc] px-4 py-2.5 text-[13px] font-semibold text-[#1a1a1a]">
                <span>Total</span>
                <span>{totalToday.toFixed(2)} hrs</span>
              </div>
            </div>

            <button
              type="button"
              onClick={reset}
              className="mt-5 shrink-0 rounded-md border border-[#c0c0c0] bg-white px-4 py-2 text-[13px] font-medium text-[#333] transition-colors hover:bg-[#f2f2f2]"
            >
              Log another day
            </button>
          </div>
        )}
      </div>
    </section>
  )
}

function AjeraMark() {
  return (
    <span className="flex h-4 w-4 shrink-0 items-center justify-center rounded-[3px] bg-[#e8792c] text-[9px] font-black text-white">
      A
    </span>
  )
}

function CheckIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-7 w-7" fill="none" stroke="currentColor" strokeWidth={3} strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 6 9 17l-5-5" />
    </svg>
  )
}
