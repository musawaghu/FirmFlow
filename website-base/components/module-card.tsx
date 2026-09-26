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
      <Card className="flex h-full flex-col gap-3 p-5 transition-all hover:border-primary/50 hover:shadow-md">
        <div className="flex items-start justify-between gap-3">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="secondary" className="font-normal">
              {module.category}
            </Badge>
            {module.day1 && (
              <Badge className="bg-accent text-accent-foreground">Day 1</Badge>
            )}
          </div>
          <span
            className={cn(
              "flex h-6 items-center rounded-full px-2 text-xs font-medium",
              completed
                ? "bg-primary/10 text-primary"
                : "bg-muted text-muted-foreground",
            )}
          >
            {completed ? "Completed" : "Not started"}
          </span>
        </div>

        <div className="flex-1">
          <h3 className="font-semibold leading-snug text-foreground transition-colors group-hover:text-primary">
            {module.title}
          </h3>
          <p className="mt-1 text-sm leading-relaxed text-muted-foreground">{module.summary}</p>
        </div>

        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>{module.estimatedMinutes} min · {module.quiz.length} quiz questions</span>
          {completed && progress?.quizScore !== null && progress?.quizScore !== undefined && (
            <span className="font-medium text-foreground">Quiz {progress.quizScore}%</span>
          )}
        </div>
      </Card>
    </Link>
  )
}
