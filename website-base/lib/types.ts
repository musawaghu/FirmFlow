export type Role = "user" | "admin"

export interface User {
  id: string
  name: string
  email: string
  password: string
  role: Role
  title: string
  startDate: string
  mentorId: string | null
}

export interface QuizQuestion {
  id: string
  prompt: string
  options: string[]
  correctIndex: number
}

export interface ModuleSection {
  id: string
  heading: string
  body: string
}

export interface Module {
  id: string
  title: string
  category: string
  summary: string
  estimatedMinutes: number
  day1: boolean
  /** Optional interactive simulator rendered above the quiz, e.g. "revit-open" */
  interactive?: "revit-open"
  sections: ModuleSection[]
  quiz: QuizQuestion[]
}

export interface ChecklistItem {
  id: string
  label: string
  done: boolean
}

/** Per user, per module completion record */
export interface ModuleProgress {
  moduleId: string
  completed: boolean
  quizScore: number | null // 0..100
  wrongQuestionIds: string[]
}

export interface UserProgress {
  userId: string
  modules: Record<string, ModuleProgress>
  checklist: ChecklistItem[]
}
