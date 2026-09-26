"use client"

import { useEffect, useState } from "react"
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

  useEffect(() => {
    if (open) setDraft(module ? structuredClone(module) : emptyModule())
  }, [open, module])

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

          {/* Sections */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-foreground">Content sections</h3>
              <Button type="button" variant="outline" size="sm" onClick={addSection}>
                Add section
              </Button>
            </div>
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
