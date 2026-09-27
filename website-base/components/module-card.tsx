import Link from "next/link"
import type { Module, ModuleProgress } from "@/lib/types"
import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import { cn } from "@/lib/utils"

export function ModuleCard({
  module,
  progress,
}: {
  module: Module
  progress: ModuleProgress | undefined
}) {
  const completed = progress?.completed
  return (
    <Link href={`/modules/${module.id}`} className="group block">
      <Card className="flex h-full flex-col gap-4 p-4 transition-colors hover:bg-[var(--color-offwhite)]">
        <div className="flex items-start justify-between gap-3">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="secondary" className="font-normal">
              {module.category}
            </Badge>
            {module.day1 && <Badge className="bg-[var(--color-secondary)] text-[var(--color-black)]">Day 1</Badge>}
          </div>
          <span
            className={cn(
              "flex h-6 items-center border-[2px] border-[var(--color-black)] px-2 text-[11px] font-semibold uppercase tracking-wide",
              completed
                ? "bg-[var(--color-primary)] text-[var(--color-white)]"
                : "bg-[var(--color-offwhite)] text-[var(--color-black)]",
            )}
          >
            {completed ? "Completed" : "Not started"}
          </span>
        </div>

        <div className="flex-1">
          <h3 className="text-lg font-semibold leading-snug text-[var(--color-black)] transition-colors group-hover:text-[var(--color-primary)]">
            {module.title}
          </h3>
          <p className="mt-2 text-sm leading-relaxed text-[var(--color-black)]/75">{module.summary}</p>
        </div>

        <div className="flex items-center justify-between gap-2 text-[11px] font-medium uppercase tracking-wide text-[var(--color-black)]/75">
          <span>{module.estimatedMinutes} min • {module.quiz.length} quiz questions</span>
          {completed && progress?.quizScore !== null && progress?.quizScore !== undefined && (
            <span className="font-semibold text-[var(--color-black)]">Quiz {progress.quizScore}%</span>
          )}
        </div>
      </Card>
    </Link>
  )
}
