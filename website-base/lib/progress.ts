import type { Module, UserProgress } from "./types"

export function completedCount(progress: UserProgress, modules: Module[]): number {
  return modules.filter((m) => progress.modules[m.id]?.completed).length
}

export function completionPercent(progress: UserProgress, modules: Module[]): number {
  if (modules.length === 0) return 0
  return Math.round((completedCount(progress, modules) / modules.length) * 100)
}

export function averageQuizScore(progress: UserProgress): number | null {
  const scores = Object.values(progress.modules)
    .map((m) => m.quizScore)
    .filter((s): s is number => s !== null)
  if (scores.length === 0) return null
  return Math.round(scores.reduce((a, b) => a + b, 0) / scores.length)
}
