"use client"

import { useEffect, useRef, useState } from "react"
import type { Module, ModuleSection, QuizQuestion } from "@/lib/types"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Checkbox } from "@/components/ui/checkbox"
import { Separator } from "@/components/ui/separator"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"

function readUploadTitle(fileName: string) {
  return fileName
    .replace(/\.[^/.]+$/, "")
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    || "Imported module"
}

function normalizeText(value: string) {
  return value.replace(/\r\n/g, "\n").trim()
}

const MD_HEADING = /^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$/
const MD_RULE = /^\s{0,3}([-*_])(\s*\1){2,}\s*$/
const MD_FENCE = /^\s{0,3}(```|~~~)/

// Section bodies are displayed as plain text, so drop inline markdown syntax.
function stripInlineMarkdown(line: string) {
  return line
    .replace(/!\[([^\]]*)\]\([^)]*\)/g, "$1")
    .replace(/\[([^\]]+)\]\(([^)\s]+)[^)]*\)/g, (_, label: string, url: string) => (label === url ? url : `${label} (${url})`))
    .replace(/`([^`]+)`/g, "$1")
    .replace(/(\*\*|__)(?=\S)([\s\S]*?\S)\1/g, "$2")
    .replace(/(^|[^\w*])\*(?=\S)([^*]*?\S)\*(?!\w)/g, "$1$2")
    .replace(/(^|[^\w])_(?=\S)([^_]*?\S)_(?!\w)/g, "$1$2")
    .replace(/~~(?=\S)([\s\S]*?\S)~~/g, "$1")
}

const MD_TABLE_ROW = /^\s*\|.*\|\s*$/
const MD_TABLE_DIVIDER = /^\s*\|?(\s*:?-+:?\s*\|)+\s*(:?-+:?\s*)?$/

function tableCells(row: string) {
  return row.trim().replace(/^\||\|$/g, "").split("|").map((cell) => stripInlineMarkdown(cell.trim()))
}

// A pipe table becomes one bullet per row, each cell labelled with its column header.
function tableToText(rows: string[]) {
  const hasHeader = rows.length > 1 && MD_TABLE_DIVIDER.test(rows[1])
  const headers = hasHeader ? tableCells(rows[0]) : []
  return (hasHeader ? rows.slice(2) : rows)
    .filter((row) => !MD_TABLE_DIVIDER.test(row))
    .map((row) => "• " + tableCells(row)
      .map((cell, i) => (headers[i] ? `${headers[i]}: ${cell}` : cell))
      .filter(Boolean)
      .join(" · "))
}

function cleanMarkdownBody(lines: string[]) {
  const out: string[] = []
  let inFence = false
  for (let i = 0; i < lines.length; i++) {
    const raw = lines[i]
    if (MD_FENCE.test(raw)) {
      inFence = !inFence
      continue
    }
    if (inFence) {
      out.push(raw)
      continue
    }
    if (MD_TABLE_ROW.test(raw)) {
      const rows: string[] = []
      while (i < lines.length && MD_TABLE_ROW.test(lines[i])) rows.push(lines[i++])
      i--
      out.push(...tableToText(rows))
      continue
    }
    if (MD_RULE.test(raw)) continue
    const line = raw
      .replace(/^\s{0,3}>\s?/, "")
      .replace(/^(\s*)[-*+]\s+(\[[ xX]\]\s+)?/, "$1• ")
      .replace(/^(\s*\d+[.)]\s+)\[[ xX]\]\s+/, "$1")
    out.push(stripInlineMarkdown(line))
  }
  return out.join("\n").replace(/\n{3,}/g, "\n\n").trim()
}

function parseMarkdown(text: string): { title: string | null; sections: ModuleSection[] } {
  // YAML front matter ("---" ... "---") at the top is metadata, not content.
  const lines = normalizeText(text).replace(/^---\n[\s\S]*?\n---(\n|$)/, "").split("\n")
  const sections: ModuleSection[] = []
  const h1s: string[] = []
  let heading = "Overview"
  let body: string[] = []
  let inFence = false
  const flush = () => {
    const cleaned = cleanMarkdownBody(body)
    if (cleaned) sections.push({ id: `s-${Date.now()}-${sections.length}`, heading, body: cleaned })
    body = []
  }
  for (const line of lines) {
    if (MD_FENCE.test(line)) inFence = !inFence
    const match = inFence ? null : MD_HEADING.exec(line)
    if (match) {
      flush()
      heading = stripInlineMarkdown(match[2]) || "Overview"
      if (match[1] === "#") h1s.push(heading)
    } else {
      body.push(line)
    }
  }
  flush()
  return { title: h1s.length === 1 ? h1s[0] : null, sections }
}

function makeSectionsFromText(text: string, fallbackTitle: string): ModuleSection[] {
  const normalized = normalizeText(text)
  if (!normalized) return [{ id: `s-${Date.now()}`, heading: "Overview", body: "" }]

  if (normalized.split("\n").some((line) => MD_HEADING.test(line))) {
    const { sections } = parseMarkdown(normalized)
    if (sections.length > 0) return sections
  }

  const blocks = normalized
    .split(/\n\s*\n+/)
    .map((block) => block.trim())
    .filter(Boolean)

  const sections: ModuleSection[] = []
  for (const block of blocks) {
    const match = block.match(/^(?:#+\s*)?(.*?)(?:\n|$)([\s\S]*)$/)
    if (!match) {
      sections.push({ id: `s-${Date.now()}-${sections.length}`, heading: "Overview", body: block })
      continue
    }
    const heading = match[1].trim() || "Overview"
    const body = match[2].trim() || block.replace(/^.*?\n/, "").trim()
    if (body) {
      sections.push({ id: `s-${Date.now()}-${sections.length}`, heading, body })
    }
  }

  if (sections.length === 0) {
    return [{ id: `s-${Date.now()}`, heading: "Overview", body: normalized }]
  }

  return sections.slice(0, 4).map((section, index) => ({
    ...section,
    id: `${section.id}-${index}`,
    heading: section.heading || "Overview",
    body: section.body || `${fallbackTitle} content`,
  }))
}

function makeQuizFromText(text: string, title: string): QuizQuestion[] {
  const normalized = normalizeText(text)
  if (!normalized) {
    return [{ id: `q-${Date.now()}`, prompt: `What is the main purpose of ${title}?`, options: ["To explain the process", "To skip the task", "To create a new policy", "To ignore the workflow"], correctIndex: 0 }]
  }

  const sentences = normalized
    .split(/[.!?]+\s+/)
    .map((sentence) => sentence.trim())
    .filter((sentence) => sentence.length > 20)

  const asks = sentences.slice(0, 3)
  if (asks.length === 0) {
    return [{ id: `q-${Date.now()}`, prompt: `What should a user understand from ${title}?`, options: ["The key workflow", "Nothing at all", "A random tool", "The browser title"], correctIndex: 0 }]
  }

  return asks.map((sentence, index) => ({
    id: `q-${Date.now()}-${index}`,
    prompt: `Which statement best reflects this training content: "${sentence.slice(0, 90)}${sentence.length > 90 ? "..." : ""}"?`,
    options: [
      sentence.slice(0, 55) || "Key workflow guidance",
      "This training is unrelated to the operational task.",
      "The workflow should be skipped by default.",
      "Users should only read the filename and ignore the content.",
    ],
    correctIndex: 0,
  }))
}

function buildModuleFromUpload(file: File): Module {
  const title = readUploadTitle(file.name)

  return {
    id: `m-${Date.now()}`,
    title,
    category: "Imported",
    summary: `Imported from ${file.name}. Review and refine the generated sections before saving.`,
    estimatedMinutes: 10,
    day1: false,
    sections: [{ id: `s-${Date.now()}`, heading: "Overview", body: `Imported content from ${file.name}.` }],
    quiz: [{ id: `q-${Date.now()}`, prompt: `What is the purpose of ${title}?`, options: ["To review the imported onboarding material", "To remove the module", "To delete the quiz", "To change the file name"], correctIndex: 0 }],
  }
}

function emptyModule(): Module {
  return {
    id: `m-${Date.now()}`,
    title: "",
    category: "General",
    summary: "",
    estimatedMinutes: 10,
    day1: false,
    sections: [{ id: `s-${Date.now()}`, heading: "", body: "" }],
    quiz: [
      {
        id: `q-${Date.now()}`,
        prompt: "",
        options: ["", "", "", ""],
        correctIndex: 0,
      },
    ],
  }
}

export function ModuleEditor({
  open,
  onOpenChange,
  module,
  onSave,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  module: Module | null
  onSave: (module: Module) => void
}) {
  const [draft, setDraft] = useState<Module>(emptyModule())
  const [uploadStatus, setUploadStatus] = useState<string | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement | null>(null)

  useEffect(() => {
    if (open) setDraft(module ? structuredClone(module) : emptyModule())
  }, [open, module])

  async function handleUpload(file: File | null) {
    if (!file) return

    const fileName = file.name
    const title = readUploadTitle(fileName)
    const lowerName = fileName.toLowerCase()

    try {
      setIsUploading(true)

      if (lowerName.endsWith(".pdf") || lowerName.endsWith(".docx")) {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
        const formData = new FormData()
        formData.append("file", file)
        formData.append("title", title)

        setUploadStatus(`Sending ${fileName} to the backend AI parser…`)

        const response = await fetch(`${apiUrl}/api/manuals`, {
          method: "POST",
          body: formData,
        })

        if (!response.ok) {
          const detail = await response.text().catch(() => "")
          throw new Error(detail || `The backend rejected ${fileName}.`)
        }

        const payload = await response.json().catch(() => null)
        setDraft((current) => ({
          ...current,
          title: payload?.title ?? title,
          category: current.category || "Imported",
          summary: `Queued for AI processing from ${fileName}. Review the generated module once the backend finishes condensing it.`,
          estimatedMinutes: current.estimatedMinutes || 10,
          sections: current.sections.length ? current.sections : [{ id: `s-${Date.now()}`, heading: "Overview", body: `This manual has been queued for AI condensation from ${fileName}.` }],
          quiz: current.quiz.length ? current.quiz : [{ id: `q-${Date.now()}`, prompt: `What should a learner retain from ${payload?.title ?? title}?`, options: ["The key workflow steps", "No relevant details", "Only the file name", "A blank answer"], correctIndex: 0 }],
        }))

        setUploadStatus(`Queued ${fileName} with the backend AI pipeline. Review the generated module after processing finishes.`)
        return
      }

      setUploadStatus("Reading your uploaded module…")

      const raw = await file.text()
      const normalized = normalizeText(raw)

      if (!normalized) {
        throw new Error("The selected file is empty. Please choose a file with module content.")
      }

      let parsed: Partial<Module> = {
        title,
        category: "Imported",
        summary: `Imported from ${fileName}. Review and tune this draft before saving.`,
        sections: [{ id: `s-${Date.now()}`, heading: "Overview", body: `Imported content from ${fileName}.` }],
        quiz: [{ id: `q-${Date.now()}`, prompt: `What are the key takeaways from ${title}?`, options: ["The main workflow steps", "No relevant guidance", "Only the file name", "A blank answer"], correctIndex: 0 }],
      }

      try {
        const asJson = JSON.parse(normalized)
        if (Array.isArray(asJson) && asJson.length > 0) {
          const first = asJson[0]
          if (first && typeof first === "object") {
            parsed = {
              title: typeof first.title === "string" ? first.title : title,
              category: typeof first.category === "string" ? first.category : "Imported",
              summary: typeof first.summary === "string" ? first.summary : `Imported from ${fileName}.`,
              estimatedMinutes: typeof first.estimatedMinutes === "number" ? first.estimatedMinutes : 10,
              day1: Boolean(first.day1),
              sections: Array.isArray(first.sections) && first.sections.length > 0 ? first.sections.map((section: any, index: number) => ({
                id: section.id ?? `s-${Date.now()}-${index}`,
                heading: section.heading ?? `Section ${index + 1}`,
                body: section.body ?? "",
              })) : [{ id: `s-${Date.now()}`, heading: "Overview", body: `Imported content from ${fileName}.` }],
              quiz: Array.isArray(first.quiz) && first.quiz.length > 0 ? first.quiz.map((question: any, index: number) => ({
                id: question.id ?? `q-${Date.now()}-${index}`,
                prompt: question.prompt ?? `Question ${index + 1}`,
                options: Array.isArray(question.options) && question.options.length > 0 ? question.options.slice(0, 4) : ["Option A", "Option B", "Option C", "Option D"],
                correctIndex: typeof question.correctIndex === "number" ? question.correctIndex : 0,
              })) : [{ id: `q-${Date.now()}`, prompt: `What are the key takeaways from ${title}?`, options: ["The main workflow steps", "No relevant guidance", "Only the file name", "A blank answer"], correctIndex: 0 }],
            }
          }
        }
      } catch {
        const sections = makeSectionsFromText(normalized, title)
        const plainText = sections.map((section) => section.body).join("\n\n")
        const quiz = makeQuizFromText(plainText, title)
        const markdownTitle = lowerName.endsWith(".md") || lowerName.endsWith(".markdown") ? parseMarkdown(normalized).title : null
        parsed = {
          title: markdownTitle || title,
          category: "Imported",
          summary: plainText.split(/\n\s*\n+/)[0]?.slice(0, 180) || `Imported from ${fileName}.`,
          estimatedMinutes: 10,
          day1: false,
          sections,
          quiz,
        }
      }

      setDraft((current) => ({
        ...current,
        ...parsed,
        id: current.id,
        title: parsed.title ?? current.title,
        category: parsed.category ?? current.category,
        summary: parsed.summary ?? current.summary,
        estimatedMinutes: parsed.estimatedMinutes ?? current.estimatedMinutes,
        day1: parsed.day1 ?? current.day1,
        sections: parsed.sections ?? current.sections,
        quiz: parsed.quiz ?? current.quiz,
      }))
      setUploadStatus(`Imported ${parsed.title ?? title} from ${fileName}. Review and save when ready.`)
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unable to import that file."
      setUploadStatus(message)
    } finally {
      setIsUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ""
    }
  }

  function update<K extends keyof Module>(key: K, value: Module[K]) {
    setDraft((d) => ({ ...d, [key]: value }))
  }

  function updateSection(index: number, patch: Partial<ModuleSection>) {
    setDraft((d) => ({
      ...d,
      sections: d.sections.map((s, i) => (i === index ? { ...s, ...patch } : s)),
    }))
  }

  function addSection() {
    setDraft((d) => ({
      ...d,
      sections: [...d.sections, { id: `s-${Date.now()}`, heading: "", body: "" }],
    }))
  }

  function removeSection(index: number) {
    setDraft((d) => ({ ...d, sections: d.sections.filter((_, i) => i !== index) }))
  }

  function updateQuestion(index: number, patch: Partial<QuizQuestion>) {
    setDraft((d) => ({
      ...d,
      quiz: d.quiz.map((q, i) => (i === index ? { ...q, ...patch } : q)),
    }))
  }

  function updateOption(qIndex: number, oIndex: number, value: string) {
    setDraft((d) => ({
      ...d,
      quiz: d.quiz.map((q, i) =>
        i === qIndex
          ? { ...q, options: q.options.map((o, oi) => (oi === oIndex ? value : o)) }
          : q,
      ),
    }))
  }

  function addQuestion() {
    setDraft((d) => ({
      ...d,
      quiz: [
        ...d.quiz,
        { id: `q-${Date.now()}`, prompt: "", options: ["", "", "", ""], correctIndex: 0 },
      ],
    }))
  }

  function removeQuestion(index: number) {
    setDraft((d) => ({ ...d, quiz: d.quiz.filter((_, i) => i !== index) }))
  }

  const valid =
    draft.title.trim() &&
    draft.summary.trim() &&
    draft.sections.every((s) => s.heading.trim() && s.body.trim()) &&
    draft.quiz.every((q) => q.prompt.trim() && q.options.every((o) => o.trim()))

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <input
        ref={fileInputRef}
        type="file"
        accept=".txt,.md,.json,.pdf,.docx"
        className="hidden"
        onChange={(event) => {
          const file = event.target.files?.[0] ?? null
          void handleUpload(file)
        }}
      />

      <DialogContent className="max-h-[90vh] max-w-2xl overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{module ? "Edit module" : "New module"}</DialogTitle>
          <DialogDescription>
            Modules appear in the employee dashboard immediately after saving.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-5">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2 sm:col-span-2">
              <Label htmlFor="title">Title</Label>
              <Input
                id="title"
                value={draft.title}
                onChange={(e) => update("title", e.target.value)}
                placeholder="e.g. Ajera Accounting & Timesheets"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="category">Category</Label>
              <Input
                id="category"
                value={draft.category}
                onChange={(e) => update("category", e.target.value)}
                placeholder="Finance"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="minutes">Estimated minutes</Label>
              <Input
                id="minutes"
                type="number"
                min={1}
                value={draft.estimatedMinutes}
                onChange={(e) => update("estimatedMinutes", Number(e.target.value) || 0)}
              />
            </div>
            <div className="space-y-2 sm:col-span-2">
              <Label htmlFor="summary">Summary</Label>
              <Textarea
                id="summary"
                value={draft.summary}
                onChange={(e) => update("summary", e.target.value)}
                placeholder="One or two sentences describing the module."
                rows={2}
              />
            </div>
            <label className="flex items-center gap-2 text-sm sm:col-span-2">
              <Checkbox
                checked={draft.day1}
                onCheckedChange={(v) => update("day1", Boolean(v))}
              />
              Mark as a Day 1 module
            </label>
          </div>

          <Separator />

          <div className="space-y-2">
            <div className="flex items-center justify-between gap-2">
              <h3 className="font-semibold text-foreground">Content sections</h3>
              <div className="flex items-center gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={isUploading}
                  onClick={() => fileInputRef.current?.click()}
                >
                  {isUploading ? "Reading…" : "Upload module"}
                </Button>
                <Button type="button" variant="outline" size="sm" onClick={addSection}>
                  Add section
                </Button>
              </div>
            </div>
            {uploadStatus && (
              <p className="text-xs text-muted-foreground" role="status">
                {uploadStatus}
              </p>
            )}
          </div>

          {/* Sections */}
          <div className="space-y-3">
            {draft.sections.map((section, i) => (
              <div key={section.id} className="space-y-2 rounded-lg border border-border p-3">
                <div className="flex items-center gap-2">
                  <Input
                    value={section.heading}
                    onChange={(e) => updateSection(i, { heading: e.target.value })}
                    placeholder="Section heading"
                  />
                  {draft.sections.length > 1 && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => removeSection(i)}
                    >
                      Remove
                    </Button>
                  )}
                </div>
                <Textarea
                  value={section.body}
                  onChange={(e) => updateSection(i, { body: e.target.value })}
                  placeholder="Section content"
                  rows={3}
                />
              </div>
            ))}
          </div>

          <Separator />

          {/* Quiz */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-foreground">Quiz questions</h3>
              <Button type="button" variant="outline" size="sm" onClick={addQuestion}>
                Add question
              </Button>
            </div>
            {draft.quiz.map((q, qi) => (
              <div key={q.id} className="space-y-3 rounded-lg border border-border p-3">
                <div className="flex items-center gap-2">
                  <Input
                    value={q.prompt}
                    onChange={(e) => updateQuestion(qi, { prompt: e.target.value })}
                    placeholder={`Question ${qi + 1}`}
                  />
                  {draft.quiz.length > 1 && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => removeQuestion(qi)}
                    >
                      Remove
                    </Button>
                  )}
                </div>
                <div className="grid gap-2">
                  <p className="text-xs text-muted-foreground">
                    Select the radio to mark the correct answer.
                  </p>
                  {q.options.map((option, oi) => (
                    <div key={oi} className="flex items-center gap-2">
                      <input
                        type="radio"
                        name={`correct-${q.id}`}
                        checked={q.correctIndex === oi}
                        onChange={() => updateQuestion(qi, { correctIndex: oi })}
                        className="h-4 w-4 accent-[var(--primary)]"
                        aria-label={`Mark option ${oi + 1} correct`}
                      />
                      <Input
                        value={option}
                        onChange={(e) => updateOption(qi, oi, e.target.value)}
                        placeholder={`Option ${String.fromCharCode(65 + oi)}`}
                      />
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            disabled={!valid}
            onClick={() => {
              onSave(draft)
              onOpenChange(false)
            }}
          >
            Save module
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
