"use client"

import { use, useEffect, useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { useStore } from "@/lib/store"
import { AppHeader } from "@/components/app-header"
import { ModuleQuiz } from "@/components/module-quiz"
import { RevitSimulator } from "@/components/revit-simulator"
import { AjeraSimulator } from "@/components/ajera-simulator"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"

export default function ModulePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const { hydrated, currentUser, modules, getUserProgress, setModuleResult } = useStore()
  const router = useRouter()
  const [justCompleted, setJustCompleted] = useState(false)

  useEffect(() => {
    if (hydrated && !currentUser) router.replace("/")
  }, [hydrated, currentUser, router])

  if (!hydrated || !currentUser) return null

  const module = modules.find((m) => m.id === id)
  if (!module) {
    return (
      <div className="min-h-screen bg-[var(--color-bg)]">
        <AppHeader homeHref="/dashboard" />
        <main className="mx-auto max-w-3xl px-4 py-16 text-center sm:px-6">
          <h1 className="text-xl font-semibold text-[var(--color-black)]">Module not found</h1>
          <p className="mt-2 text-[var(--color-black)]/70">This module may have been removed.</p>
          <Button render={<Link href="/dashboard" />} className="mt-6">
            Back to dashboard
          </Button>
        </main>
      </div>
    )
  }

  const progress = getUserProgress(currentUser.id)
  const moduleProgress = progress.modules[module.id]

  return (
    <div className="min-h-screen bg-[var(--color-bg)]">
      <AppHeader homeHref="/dashboard" />

      <main className="mx-auto max-w-3xl px-4 py-8 sm:px-6">
        <Link
          href="/dashboard"
          className="text-sm font-medium text-[var(--color-black)]/70 transition-colors hover:text-[var(--color-black)]"
        >
          ← Back to dashboard
        </Link>

        <div className="mt-4 flex flex-wrap items-center gap-2">
          <Badge variant="secondary" className="font-normal">
            {module.category}
          </Badge>
          {module.day1 && <Badge className="bg-[var(--color-secondary)] text-[var(--color-black)]">Day 1</Badge>}
          <span className="text-sm text-[var(--color-black)]/70">{module.estimatedMinutes} min read</span>
        </div>

        <h1 className="mt-3 text-3xl font-bold text-[var(--color-black)] sm:text-4xl" style={{ fontFamily: 'var(--font-title)' }}>{module.title}</h1>
        <p className="mt-2 text-pretty leading-relaxed text-[var(--color-black)]/75">{module.summary}</p>

        {moduleProgress?.completed && (
          <div className="mt-4 flex items-center gap-2 border-[2px] border-[var(--color-primary)] bg-[var(--color-primary)]/10 px-4 py-3 text-sm text-[var(--color-black)]">
            <span className="flex h-5 w-5 items-center justify-center bg-[var(--color-primary)] text-[var(--color-white)]">
              <svg viewBox="0 0 24 24" className="h-3 w-3" fill="none" stroke="currentColor" strokeWidth={3} strokeLinecap="round" strokeLinejoin="round">
                <path d="M20 6 9 17l-5-5" />
              </svg>
            </span>
            Completed{moduleProgress.quizScore !== null && ` — quiz score ${moduleProgress.quizScore}%`}
          </div>
        )}

        {/* Sections */}
        <article className="mt-8 space-y-6">
          {module.sections.map((section) => (
            <Card key={section.id}>
              <CardContent className="py-5">
                <h2 className="font-semibold text-foreground">{section.heading}</h2>
                <p className="mt-2 leading-relaxed text-muted-foreground">{section.body}</p>
              </CardContent>
            </Card>
          ))}
        </article>

        {/* Interactive simulator */}
        {module.interactive === "revit-open" && (
          <div className="mt-8">
            <RevitSimulator />
          </div>
        )}
        {module.interactive === "ajera-timesheet" && (
          <div className="mt-8">
            <AjeraSimulator />
          </div>
        )}

        {/* Quiz */}
        <div className="mt-8">
          <ModuleQuiz
            key={module.id}
            questions={module.quiz}
            onComplete={(result) => {
              setModuleResult(currentUser.id, module.id, {
                completed: true,
                quizScore: result.score,
                wrongQuestionIds: result.wrongQuestionIds,
              })
              setJustCompleted(true)
            }}
          />
        </div>

        {justCompleted && (
          <div className="mt-6 flex flex-col items-start gap-3 rounded-lg border border-border bg-card p-5 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm text-foreground">
              Progress saved. Keep the momentum going.
            </p>
            <Button render={<Link href="/dashboard" />}>Back to dashboard</Button>
          </div>
        )}
      </main>
    </div>
  )
}
