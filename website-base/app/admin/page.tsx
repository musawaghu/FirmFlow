"use client"

import { useEffect, useMemo, useState } from "react"
import { useRouter } from "next/navigation"
import { useStore } from "@/lib/store"
import { mentors } from "@/lib/mock-data"
import type { Module } from "@/lib/types"
import { AppHeader } from "@/components/app-header"
import { ModuleEditor } from "@/components/admin/module-editor"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { completedCount, completionPercent } from "@/lib/progress"

export default function AdminPage() {
  const {
    hydrated,
    currentUser,
    users,
    modules,
    progress,
    getUserProgress,
    saveModule,
    deleteModule,
  } = useStore()
  const router = useRouter()

  const [editorOpen, setEditorOpen] = useState(false)
  const [editing, setEditing] = useState<Module | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<Module | null>(null)

  useEffect(() => {
    if (!hydrated) return
    if (!currentUser) router.replace("/")
    else if (currentUser.role !== "admin") router.replace("/dashboard")
  }, [hydrated, currentUser, router])

  const employees = useMemo(() => users.filter((u) => u.role === "user"), [users])

  // Aggregate quiz insights: which questions are most missed.
  const insights = useMemo(() => {
    const missCount: Record<string, number> = {}
    let totalCompletions = 0
    let scoreSum = 0
    let scoreN = 0

    for (const u of employees) {
      const p = progress[u.id]
      if (!p) continue
      for (const mp of Object.values(p.modules)) {
        if (mp.completed) totalCompletions++
        if (mp.quizScore !== null) {
          scoreSum += mp.quizScore
          scoreN++
        }
        for (const qid of mp.wrongQuestionIds) {
          missCount[`${mp.moduleId}::${qid}`] = (missCount[`${mp.moduleId}::${qid}`] ?? 0) + 1
        }
      }
    }

    const missed = Object.entries(missCount)
      .map(([key, count]) => {
        const [moduleId, qid] = key.split("::")
        const mod = modules.find((m) => m.id === moduleId)
        const q = mod?.quiz.find((qq) => qq.id === qid)
        return { moduleTitle: mod?.title ?? "Removed module", prompt: q?.prompt ?? qid, count }
      })
      .sort((a, b) => b.count - a.count)

    return {
      missed,
      totalCompletions,
      avgScore: scoreN ? Math.round(scoreSum / scoreN) : null,
    }
  }, [employees, progress, modules])

  if (!currentUser || currentUser.role !== "admin") return null

  return (
    <div className="min-h-screen bg-[var(--color-bg)]">
      <AppHeader homeHref="/admin" />

      <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
        <div className="flex flex-col gap-1">
          <p className="text-sm font-semibold uppercase tracking-[0.12em] text-[var(--color-black)]/70">Admin</p>
          <h1 className="text-3xl font-bold text-[var(--color-black)] sm:text-4xl" style={{ fontFamily: 'var(--font-title)' }}>Onboarding control</h1>
        </div>

        <div className="mt-6 grid gap-4 sm:grid-cols-4">
          <StatCard label="Employees" value={String(employees.length)} />
          <StatCard label="Modules" value={String(modules.length)} />
          <StatCard label="Module completions" value={String(insights.totalCompletions)} />
          <StatCard
            label="Avg quiz score"
            value={insights.avgScore === null ? "—" : `${insights.avgScore}%`}
          />
        </div>

        <Tabs defaultValue="modules" className="mt-8">
          <TabsList>
            <TabsTrigger value="modules">Modules</TabsTrigger>
            <TabsTrigger value="people">People</TabsTrigger>
            <TabsTrigger value="insights">Quiz insights</TabsTrigger>
          </TabsList>

          {/* MODULES */}
          <TabsContent value="modules" className="mt-6">
            <div className="flex items-center justify-between gap-3">
              <h2 className="text-lg font-semibold text-[var(--color-black)]">Training modules</h2>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  onClick={() => {
                    setEditing(null)
                    setEditorOpen(true)
                  }}
                >
                  Upload modules
                </Button>
                <Button
                  onClick={() => {
                    setEditing(null)
                    setEditorOpen(true)
                  }}
                >
                  New module
                </Button>
              </div>
            </div>

            <div className="mt-4 grid gap-3">
              {modules.map((m) => (
                <Card key={m.id}>
                  <CardContent className="flex flex-col gap-3 py-4 sm:flex-row sm:items-center sm:justify-between">
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="font-semibold text-[var(--color-black)]">{m.title}</h3>
                        <Badge variant="secondary" className="font-normal">
                          {m.category}
                        </Badge>
                        {m.day1 && <Badge className="bg-[var(--color-secondary)] text-[var(--color-black)]">Day 1</Badge>}
                      </div>
                      <p className="mt-1 text-sm text-[var(--color-black)]/70">{m.summary}</p>
                      <p className="mt-1 text-xs text-[var(--color-black)]/70">
                        {m.sections.length} sections · {m.quiz.length} questions · {m.estimatedMinutes} min
                      </p>
                    </div>
                    <div className="flex shrink-0 gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setEditing(m)
                          setEditorOpen(true)
                        }}
                      >
                        Edit
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-destructive hover:text-destructive"
                        onClick={() => setDeleteTarget(m)}
                      >
                        Delete
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          {/* PEOPLE */}
          <TabsContent value="people" className="mt-6">
            <h2 className="text-lg font-semibold text-foreground">Employee progress</h2>
            <div className="mt-4 grid gap-3">
              {employees.map((u) => {
                const p = getUserProgress(u.id)
                const percent = completionPercent(p, modules)
                const done = completedCount(p, modules)
                const mentor = mentors.find((mm) => mm.id === u.mentorId)
                return (
                  <Card key={u.id}>
                    <CardContent className="flex flex-col gap-4 py-4 sm:flex-row sm:items-center">
                      <div className="flex items-center gap-3 sm:w-64">
                        <Avatar className="h-10 w-10">
                          <AvatarFallback className="bg-primary/10 text-primary font-semibold">
                            {u.name.split(" ").map((n) => n[0]).join("")}
                          </AvatarFallback>
                        </Avatar>
                        <div className="min-w-0">
                          <p className="truncate font-medium text-foreground">{u.name}</p>
                          <p className="truncate text-sm text-muted-foreground">{u.title}</p>
                        </div>
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">
                            {done}/{modules.length} modules
                          </span>
                          <span className="font-medium text-foreground">{percent}%</span>
                        </div>
                        <Progress value={percent} className="mt-2" />
                      </div>
                      <div className="text-sm text-muted-foreground sm:w-40 sm:text-right">
                        Mentor:{" "}
                        <span className="text-foreground">{mentor?.name ?? "Unassigned"}</span>
                      </div>
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          </TabsContent>

          {/* INSIGHTS */}
          <TabsContent value="insights" className="mt-6">
            <h2 className="text-lg font-semibold text-foreground">Most-missed quiz questions</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Questions employees get wrong most often — good candidates to clarify in training.
            </p>
            <Card className="mt-4">
              <CardContent className="py-2">
                {insights.missed.length === 0 ? (
                  <p className="py-6 text-center text-sm text-muted-foreground">
                    No incorrect answers recorded yet.
                  </p>
                ) : (
                  <ul className="divide-y divide-border">
                    {insights.missed.map((item, i) => (
                      <li key={i} className="flex items-start justify-between gap-4 py-3">
                        <div className="min-w-0">
                          <p className="text-sm font-medium text-foreground">{item.prompt}</p>
                          <p className="text-xs text-muted-foreground">{item.moduleTitle}</p>
                        </div>
                        <Badge variant="secondary" className="shrink-0">
                          {item.count} {item.count === 1 ? "miss" : "misses"}
                        </Badge>
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>

      <ModuleEditor
        open={editorOpen}
        onOpenChange={setEditorOpen}
        module={editing}
        onSave={saveModule}
      />

      <Dialog open={!!deleteTarget} onOpenChange={(o) => !o && setDeleteTarget(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete module?</DialogTitle>
            <DialogDescription>
              {deleteTarget
                ? `"${deleteTarget.title}" will be removed for all employees. This cannot be undone.`
                : ""}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteTarget(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => {
                if (deleteTarget) deleteModule(deleteTarget.id)
                setDeleteTarget(null)
              }}
            >
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle>
      </CardHeader>
      <CardContent>
        <span className="text-3xl font-bold text-foreground">{value}</span>
      </CardContent>
    </Card>
  )
}
