"use client"

import { useEffect, useMemo } from "react"
import { useRouter } from "next/navigation"
import { useStore } from "@/lib/store"
import { mentors } from "@/lib/mock-data"
import { AppHeader } from "@/components/app-header"
import { ModuleCard } from "@/components/module-card"
import { ChecklistCard } from "@/components/checklist-card"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { completedCount, completionPercent, averageQuizScore } from "@/lib/progress"

export default function DashboardPage() {
  const { hydrated, currentUser, modules, getUserProgress, toggleChecklistItem } = useStore()
  const router = useRouter()

  useEffect(() => {
    if (!hydrated) return
    if (!currentUser) router.replace("/")
    else if (currentUser.role === "admin") router.replace("/admin")
  }, [hydrated, currentUser, router])

  const progress = currentUser ? getUserProgress(currentUser.id) : null

  const stats = useMemo(() => {
    if (!progress) return null
    return {
      done: completedCount(progress, modules),
      total: modules.length,
      percent: completionPercent(progress, modules),
      avgScore: averageQuizScore(progress),
    }
  }, [progress, modules])

  if (!currentUser || !progress || !stats) return null

  const firstName = currentUser.name.split(" ")[0]
  const mentor = mentors.find((m) => m.id === currentUser.mentorId) ?? null
  const day1Modules = modules.filter((m) => m.day1)
  const otherModules = modules.filter((m) => !m.day1)

  return (
    <div className="min-h-screen bg-[var(--color-bg)]">
      <AppHeader homeHref="/dashboard" />

      <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
        <div className="flex flex-col gap-1">
          <p className="text-sm font-medium uppercase tracking-[0.12em] text-[var(--color-black)]/70">Welcome back,</p>
          <h1 className="text-3xl font-bold text-[var(--color-black)] sm:text-4xl" style={{ fontFamily: 'var(--font-title)' }}>
            {firstName} — {currentUser.title}
          </h1>
        </div>

        <div className="mt-6 grid gap-4 sm:grid-cols-3">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold uppercase tracking-[0.08em] text-[var(--color-black)]/70">
                Overall progress
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-end justify-between gap-3">
                <span className="text-3xl font-bold text-[var(--color-black)]">{stats.percent}%</span>
                <span className="text-sm text-[var(--color-black)]/70">
                  {stats.done}/{stats.total} modules
                </span>
              </div>
              <Progress value={stats.percent} className="mt-3" />
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold uppercase tracking-[0.08em] text-[var(--color-black)]/70">
                Average quiz score
              </CardTitle>
            </CardHeader>
            <CardContent>
              <span className="text-3xl font-bold text-[var(--color-black)]">
                {stats.avgScore === null ? "—" : `${stats.avgScore}%`}
              </span>
              <p className="mt-3 text-sm text-[var(--color-black)]/70">
                {stats.avgScore === null
                  ? "Complete a module quiz to see your score."
                  : "Across completed module quizzes."}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold uppercase tracking-[0.08em] text-[var(--color-black)]/70">
                Your mentor
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-3">
                <Avatar className="h-11 w-11 border-[var(--color-black)] bg-[var(--color-offwhite)]">
                  <AvatarFallback className="bg-[var(--color-primary)] text-[var(--color-white)] font-semibold">
                    {mentor ? mentor.name.split(" ").map((p) => p[0]).join("") : "?"}
                  </AvatarFallback>
                </Avatar>
                <div>
                  <p className="font-medium text-[var(--color-black)]">{mentor?.name ?? "To be assigned"}</p>
                  <p className="text-sm text-[var(--color-black)]/70">
                    {mentor ? mentor.title : "Check back soon"}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="mt-8 grid gap-8 lg:grid-cols-[1fr_320px]">
          <div className="space-y-8">
            {day1Modules.length > 0 && (
              <section>
                <div className="flex items-center gap-2">
                  <h2 className="text-xl font-semibold text-[var(--color-black)]">Start here</h2>
                  <Badge className="bg-[var(--color-secondary)] text-[var(--color-black)]">Day 1</Badge>
                </div>
                <div className="mt-4 grid gap-4 sm:grid-cols-2">
                  {day1Modules.map((m) => (
                    <ModuleCard key={m.id} module={m} progress={progress.modules[m.id]} />
                  ))}
                </div>
              </section>
            )}

            <section>
              <h2 className="text-xl font-semibold text-[var(--color-black)]">All modules</h2>
              <div className="mt-4 grid gap-4 sm:grid-cols-2">
                {otherModules.map((m) => (
                  <ModuleCard key={m.id} module={m} progress={progress.modules[m.id]} />
                ))}
              </div>
            </section>
          </div>

          <aside className="lg:sticky lg:top-24 lg:self-start">
            <ChecklistCard
              items={progress.checklist}
              onToggle={(id) => toggleChecklistItem(currentUser.id, id)}
            />
          </aside>
        </div>
      </main>
    </div>
  )
}
