"use client"

import { useEffect, useMemo, useState } from "react"
import { WarehouseModel } from "@/components/warehouse-model"

type Mode = "guided" | "interactive"
type Screen = "home" | "dialog" | "loading" | "success"

interface RevitFile {
  id: string
  name: string
  type: string
  date: string
  size: string
  isCentral?: boolean
  isCorrect?: boolean
}

const FILES: RevitFile[] = [
  {
    id: "central",
    name: "Riverside-Tower_CENTRAL.rvt",
    type: "Autodesk Revit Central Model",
    date: "9/24/2026 4:12 PM",
    size: "412,880 KB",
    isCentral: true,
  },
  {
    id: "sow",
    name: "Riverside-Tower_SOW-Interiors.rvt",
    type: "Autodesk Revit Project",
    date: "9/25/2026 9:03 AM",
    size: "398,204 KB",
    isCorrect: true,
  },
  {
    id: "struct",
    name: "Riverside-Tower_Structural.rvt",
    type: "Autodesk Revit Project",
    date: "9/20/2026 2:41 PM",
    size: "221,540 KB",
  },
  {
    id: "backup",
    name: "Riverside-Tower_CENTRAL_backup.rvt",
    type: "Revit Backup File",
    date: "9/23/2026 6:30 PM",
    size: "410,110 KB",
    isCentral: true,
  },
]

type StepKey = "open" | "select" | "createLocal" | "confirm"

const STEP_TEXT: Record<StepKey, { title: string; body: string }> = {
  open: {
    title: "Step 1 — Open the model",
    body: "On the Revit Home screen, click Open under Models.",
  },
  select: {
    title: "Step 2 — Pick the scope-of-work model",
    body: "Select Riverside-Tower_SOW-Interiors.rvt. Do NOT open the _CENTRAL model.",
  },
  createLocal: {
    title: "Step 3 — Create New Local",
    body: "Tick the Create New Local checkbox so you get your own working copy.",
  },
  confirm: {
    title: "Step 4 — Open it",
    body: "Click Open to load your new local file.",
  },
}

interface RevitSimulatorProps {
  onComplete?: () => void
}

export function RevitSimulator({ onComplete }: RevitSimulatorProps) {
  const [mode, setMode] = useState<Mode>("guided")
  const [screen, setScreen] = useState<Screen>("home")
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [createLocal, setCreateLocal] = useState(false)
  const [detach, setDetach] = useState(false)
  const [audit, setAudit] = useState(false)
  const [feedback, setFeedback] = useState<{ tone: "error" | "info"; msg: string } | null>(null)

  const selected = FILES.find((f) => f.id === selectedId) ?? null

  const currentStep: StepKey = useMemo(() => {
    if (screen === "home") return "open"
    if (!selected || !selected.isCorrect) return "select"
    if (!createLocal) return "createLocal"
    return "confirm"
  }, [screen, selected, createLocal])

  useEffect(() => {
    if (screen === "loading") {
      const t = setTimeout(() => setScreen("success"), 1600)
      return () => clearTimeout(t)
    }
  }, [screen])

  useEffect(() => {
    if (screen === "success") onComplete?.()
  }, [screen, onComplete])

  const guided = mode === "guided"
  const ring = (step: StepKey) =>
    guided && currentStep === step && screen !== "loading" && screen !== "success"
      ? "ring-2 ring-offset-2 ring-offset-[#f0f0f0] ring-[#0696d7] animate-pulse"
      : ""

  function reset() {
    setScreen("home")
    setSelectedId(null)
    setCreateLocal(false)
    setDetach(false)
    setAudit(false)
    setFeedback(null)
  }

  function handleSelect(file: RevitFile) {
    setSelectedId(file.id)
    if (file.isCentral) {
      setFeedback({
        tone: "error",
        msg: "That is the central model. Never open central directly — choose the scope-of-work model instead.",
      })
    } else if (file.isCorrect) {
      setFeedback({ tone: "info", msg: "Good — that is the scope-of-work model. Now enable Create New Local." })
    } else {
      setFeedback({ tone: "error", msg: "That is not your scope of work. Open Riverside-Tower_SOW-Interiors.rvt." })
    }
  }

  function handleOpen() {
    if (!selected) {
      setFeedback({ tone: "error", msg: "Select a file first." })
      return
    }
    if (selected.isCentral) {
      setFeedback({
        tone: "error",
        msg: "Stop — this is the central model. Cancel and open the scope-of-work model so you never edit central directly.",
      })
      return
    }
    if (!selected.isCorrect) {
      setFeedback({ tone: "error", msg: "Wrong model. Open Riverside-Tower_SOW-Interiors.rvt." })
      return
    }
    if (!createLocal) {
      setFeedback({
        tone: "error",
        msg: "Enable Create New Local first, or you would work directly against central.",
      })
      return
    }
    setFeedback(null)
    setScreen("loading")
  }

  return (
    <section className="rounded-xl border border-border bg-card p-4 sm:p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="font-semibold text-foreground">Interactive: open the model correctly</h2>
          <p className="text-sm text-muted-foreground">
            Practice the exact steps inside a simulated Revit 2024 interface.
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
      {screen !== "success" && (
        <div className="mt-4 flex items-start gap-3 rounded-lg border border-primary/30 bg-primary/5 px-4 py-3">
          <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-foreground">
            {currentStep === "open" ? "1" : currentStep === "select" ? "2" : currentStep === "createLocal" ? "3" : "4"}
          </span>
          <div>
            <p className="text-sm font-semibold text-foreground">{STEP_TEXT[currentStep].title}</p>
            <p className="text-sm text-muted-foreground">{STEP_TEXT[currentStep].body}</p>
          </div>
        </div>
      )}

      {/* Feedback toast */}
      {feedback && screen !== "success" && (
        <div
          className={`mt-3 rounded-lg px-4 py-2.5 text-sm ${
            feedback.tone === "error"
              ? "border border-destructive/30 bg-destructive/10 text-destructive"
              : "border border-primary/30 bg-primary/10 text-foreground"
          }`}
          role="status"
        >
          {feedback.msg}
        </div>
      )}

      {/* Revit window */}
      <div className="mt-4 overflow-hidden rounded-lg border border-[#c8c8c8] bg-[#f0f0f0] shadow-lg">
        {/* Title bar */}
        <div className="flex items-center justify-between bg-[#2b2b2b] px-3 py-2 text-[13px] text-white">
          <div className="flex items-center gap-2">
            <span className="flex h-5 w-5 items-center justify-center rounded-sm bg-[#0696d7] text-[11px] font-black">
              R
            </span>
            <span className="font-medium">Autodesk Revit 2024 — Riverside Tower</span>
          </div>
          <div className="flex items-center gap-3 text-[#bdbdbd]">
            <span className="hidden sm:inline">— ▢</span>
            <span className="text-white">✕</span>
          </div>
        </div>

        <div className="relative">
          {/* HOME SCREEN */}
          <div className="min-h-[360px] bg-[#e9edf0] text-[#333]">
            <div className="grid grid-cols-1 sm:grid-cols-[220px_1fr]">
              {/* Left rail */}
              <div className="border-b border-[#d3d8dc] bg-[#f7f9fa] p-4 sm:border-b-0 sm:border-r">
                <p className="text-[11px] font-bold uppercase tracking-wide text-[#8a9299]">Models</p>
                <button
                  type="button"
                  onClick={() => {
                    if (screen === "home") {
                      setScreen("dialog")
                      setFeedback(null)
                    }
                  }}
                  className={`mt-2 flex w-full items-center gap-2 rounded-md px-3 py-2 text-left text-[14px] font-medium text-[#0696d7] transition-colors hover:bg-[#e2eef5] ${ring(
                    "open",
                  )}`}
                >
                  <FolderIcon />
                  Open...
                </button>
                <button
                  type="button"
                  className="mt-1 flex w-full items-center gap-2 rounded-md px-3 py-2 text-left text-[14px] text-[#5a6169] hover:bg-[#eceff1]"
                >
                  <PlusIcon />
                  New...
                </button>

                <p className="mt-5 text-[11px] font-bold uppercase tracking-wide text-[#8a9299]">Families</p>
                <button
                  type="button"
                  className="mt-2 flex w-full items-center gap-2 rounded-md px-3 py-2 text-left text-[14px] text-[#5a6169] hover:bg-[#eceff1]"
                >
                  <FolderIcon />
                  Open...
                </button>
              </div>

              {/* Recent */}
              <div className="p-5">
                <p className="text-[13px] font-semibold text-[#5a6169]">Recent Models</p>
                <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3">
                  {["Maple Civic Center", "Harbor Point Lab", "Riverside Tower"].map((n) => (
                    <div
                      key={n}
                      className="overflow-hidden rounded-md border border-[#d3d8dc] bg-white opacity-70"
                    >
                      <div className="flex h-16 items-center justify-center bg-gradient-to-br from-[#dbe4ea] to-[#c3d0d9] text-[#9aa6ae]">
                        <BuildingIcon />
                      </div>
                      <p className="truncate px-2 py-1.5 text-[11px] text-[#5a6169]">{n}</p>
                    </div>
                  ))}
                </div>
                <p className="mt-4 text-[12px] text-[#9aa6ae]">
                  Tip: open your project through the Open dialog so you can enable Create New Local.
                </p>
              </div>
            </div>
          </div>

          {/* OPEN DIALOG */}
          {screen === "dialog" && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/30 p-3">
              <div className="w-full max-w-2xl overflow-hidden rounded-md border border-[#8a8a8a] bg-[#f0f0f0] shadow-2xl">
                {/* dialog title */}
                <div className="flex items-center justify-between border-b border-[#d0d0d0] bg-[#fafafa] px-3 py-2 text-[13px] font-medium text-[#333]">
                  <span>Open</span>
                  <button
                    type="button"
                    onClick={reset}
                    className="flex h-5 w-5 items-center justify-center rounded-sm text-[#666] hover:bg-[#e0e0e0]"
                    aria-label="Close dialog"
                  >
                    ✕
                  </button>
                </div>

                {/* path bar */}
                <div className="flex items-center gap-2 border-b border-[#e0e0e0] bg-white px-3 py-2 text-[12px] text-[#555]">
                  <span className="text-[#9aa6ae]">Look in:</span>
                  <span className="rounded border border-[#d8d8d8] bg-[#f7f7f7] px-2 py-0.5">
                    N:\Projects\Riverside-Tower\BIM
                  </span>
                </div>

                {/* file list header */}
                <div className="grid grid-cols-[1fr_140px_90px] gap-2 border-b border-[#e6e6e6] bg-[#f7f7f7] px-3 py-1.5 text-[11px] font-semibold text-[#888]">
                  <span>Name</span>
                  <span className="hidden sm:block">Date modified</span>
                  <span className="hidden sm:block">Type</span>
                </div>

                {/* file rows */}
                <div className="max-h-[220px] overflow-y-auto bg-white">
                  {FILES.map((file) => {
                    const isSel = selectedId === file.id
                    const highlight =
                      guided && currentStep === "select" && file.isCorrect && !isSel
                        ? "ring-2 ring-inset ring-[#0696d7] animate-pulse"
                        : ""
                    return (
                      <button
                        type="button"
                        key={file.id}
                        onClick={() => handleSelect(file)}
                        onDoubleClick={() => {
                          handleSelect(file)
                          handleOpen()
                        }}
                        className={`grid w-full grid-cols-[1fr_140px_90px] items-center gap-2 px-3 py-1.5 text-left text-[12px] transition-colors ${
                          isSel ? "bg-[#cce4f5] text-[#1a1a1a]" : "text-[#333] hover:bg-[#eef5fb]"
                        } ${highlight}`}
                      >
                        <span className="flex items-center gap-2 truncate">
                          <RvtIcon central={file.isCentral} />
                          <span className="truncate font-medium">{file.name}</span>
                        </span>
                        <span className="hidden truncate text-[#777] sm:block">{file.date}</span>
                        <span className="hidden truncate text-[#777] sm:block">
                          {file.isCentral ? "Central" : "Project"}
                        </span>
                      </button>
                    )
                  })}
                </div>

                {/* filename + type */}
                <div className="space-y-2 border-t border-[#e0e0e0] bg-[#fafafa] px-3 py-3">
                  <div className="flex items-center gap-2 text-[12px]">
                    <span className="w-16 text-[#666]">File name:</span>
                    <span className="flex-1 truncate rounded border border-[#c8c8c8] bg-white px-2 py-1 text-[#1a1a1a]">
                      {selected ? selected.name : ""}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-[12px]">
                    <span className="w-16 text-[#666]">Files of type:</span>
                    <span className="flex-1 rounded border border-[#c8c8c8] bg-white px-2 py-1 text-[#1a1a1a]">
                      Revit Files (*.rvt)
                    </span>
                  </div>

                  {/* worksharing checkboxes */}
                  <div className="flex flex-wrap items-center gap-x-5 gap-y-2 pt-1">
                    <RvtCheckbox label="Audit" checked={audit} onChange={setAudit} />
                    <RvtCheckbox label="Detach from Central" checked={detach} onChange={setDetach} />
                    <div className={`rounded ${ring("createLocal")}`}>
                      <RvtCheckbox
                        label="Create New Local"
                        checked={createLocal}
                        emphasize
                        onChange={(v) => {
                          setCreateLocal(v)
                          if (v && selected?.isCorrect)
                            setFeedback({ tone: "info", msg: "Create New Local is on. Now click Open." })
                        }}
                      />
                    </div>
                  </div>
                </div>

                {/* buttons */}
                <div className="flex justify-end gap-2 border-t border-[#e0e0e0] bg-[#f0f0f0] px-3 py-3">
                  <button
                    type="button"
                    onClick={handleOpen}
                    className={`rounded border border-[#0d7fb5] bg-[#0696d7] px-5 py-1.5 text-[13px] font-medium text-white transition-colors hover:bg-[#0d84bf] ${ring(
                      "confirm",
                    )}`}
                  >
                    Open
                  </button>
                  <button
                    type="button"
                    onClick={reset}
                    className="rounded border border-[#c0c0c0] bg-[#f7f7f7] px-5 py-1.5 text-[13px] text-[#333] transition-colors hover:bg-[#ececec]"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* LOADING */}
          {screen === "loading" && (
            <div className="absolute inset-0 flex flex-col items-center justify-center bg-[#e9edf0]/95">
              <div className="h-9 w-9 animate-spin rounded-full border-4 border-[#cdd6dc] border-t-[#0696d7]" />
              <p className="mt-4 text-[13px] font-medium text-[#4a5259]">Creating new local file…</p>
              <p className="mt-1 text-[12px] text-[#8a9299]">Riverside-Tower_SOW-Interiors_yourname.rvt</p>
            </div>
          )}

          {/* SUCCESS */}
          {screen === "success" && (
            <div className="flex min-h-[360px] flex-col items-center bg-[#e9edf0] p-6 text-center">
              <span className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-[#2e9e5b] text-white">
                <CheckIcon />
              </span>
              <p className="mt-4 text-[15px] font-semibold text-[#2b2b2b]">Local file opened correctly</p>
              <p className="mt-1 max-w-sm text-[13px] text-[#5a6169]">
                You opened the scope-of-work model as a new local copy. Your edits stay local until you synchronize
                with central — exactly right.
              </p>

              {/* 3D preview of the model the user will see once it loads */}
              <div className="mt-5 w-full max-w-xl">
                <div className="mb-2 flex items-center justify-between">
                  <p className="text-[12px] font-semibold uppercase tracking-wide text-[#8a9299]">
                    This is the model you&apos;ll see
                  </p>
                  <span className="text-[11px] text-[#9aa6ae]">Drag to orbit</span>
                </div>
                <WarehouseModel />
                <p className="mt-2 text-[12px] text-[#5a6169]">
                  Riverside-Tower_SOW-Interiors — distribution warehouse (scope of work)
                </p>
              </div>

              <button
                type="button"
                onClick={reset}
                className="mt-5 shrink-0 rounded-md border border-[#c0c0c0] bg-white px-4 py-2 text-[13px] font-medium text-[#333] transition-colors hover:bg-[#f2f2f2]"
              >
                Try again
              </button>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}

function RvtCheckbox({
  label,
  checked,
  onChange,
  emphasize,
}: {
  label: string
  checked: boolean
  onChange: (v: boolean) => void
  emphasize?: boolean
}) {
  return (
    <button
      type="button"
      role="checkbox"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className="flex cursor-pointer items-center gap-2 text-[12px] text-[#333]"
    >
      <span
        className={`flex h-4 w-4 items-center justify-center rounded-sm border ${
          checked ? "border-[#0696d7] bg-[#0696d7] text-white" : "border-[#9aa6ae] bg-white"
        }`}
      >
        {checked && (
          <svg viewBox="0 0 24 24" className="h-3 w-3" fill="none" stroke="currentColor" strokeWidth={4}>
            <path d="M20 6 9 17l-5-5" />
          </svg>
        )}
      </span>
      <span className={emphasize ? "font-semibold" : ""}>{label}</span>
    </button>
  )
}

function RvtIcon({ central }: { central?: boolean }) {
  return (
    <span
      className={`flex h-4 w-4 shrink-0 items-center justify-center rounded-[3px] text-[9px] font-black text-white ${
        central ? "bg-[#c0392b]" : "bg-[#0696d7]"
      }`}
    >
      R
    </span>
  )
}

function FolderIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth={2}>
      <path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
    </svg>
  )
}

function PlusIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth={2}>
      <path d="M12 5v14M5 12h14" />
    </svg>
  )
}

function BuildingIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-7 w-7" fill="none" stroke="currentColor" strokeWidth={1.5}>
      <path d="M3 21h18M6 21V5a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v16M14 21V9h4a1 1 0 0 1 1 1v11M9 8h2M9 12h2M9 16h2" />
    </svg>
  )
}

function CheckIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-7 w-7" fill="none" stroke="currentColor" strokeWidth={3} strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 6 9 17l-5-5" />
    </svg>
  )
}
