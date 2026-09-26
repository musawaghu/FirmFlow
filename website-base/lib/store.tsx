"use client"

import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react"
import type { Module, User, UserProgress, ModuleProgress } from "./types"
import {
  users as seedUsers,
  modules as seedModules,
  defaultChecklist,
} from "./mock-data"

const STORAGE_KEY = "firmflow-state-v1"
const SESSION_KEY = "firmflow-session-v1"

interface PersistedState {
  users: User[]
  modules: Module[]
  progress: Record<string, UserProgress>
}

function freshProgress(userId: string): UserProgress {
  return {
    userId,
    modules: {},
    checklist: defaultChecklist.map((c) => ({ ...c })),
  }
}

function seedState(): PersistedState {
  const progress: Record<string, UserProgress> = {}
  for (const u of seedUsers) {
    progress[u.id] = freshProgress(u.id)
  }
  // Give one user some sample progress so the admin view has data.
  progress["u-3"] = {
    userId: "u-3",
    checklist: defaultChecklist.map((c, i) => ({ ...c, done: i < 4 })),
    modules: {
      "m-day1": { moduleId: "m-day1", completed: true, quizScore: 100, wrongQuestionIds: [] },
      "m-bim": { moduleId: "m-bim", completed: true, quizScore: 50, wrongQuestionIds: ["q2"] },
      "m-qaqc": { moduleId: "m-qaqc", completed: false, quizScore: null, wrongQuestionIds: [] },
    },
  }
  return { users: seedUsers, modules: seedModules, progress }
}

interface StoreValue {
  hydrated: boolean
  currentUser: User | null
  users: User[]
  modules: Module[]
  progress: Record<string, UserProgress>
  login: (email: string, password: string) => User | null
  logout: () => void
  // progress actions
  getUserProgress: (userId: string) => UserProgress
  setModuleResult: (
    userId: string,
    moduleId: string,
    result: Omit<ModuleProgress, "moduleId">,
  ) => void
  toggleChecklistItem: (userId: string, itemId: string) => void
  // admin module CRUD
  saveModule: (mod: Module) => void
  deleteModule: (moduleId: string) => void
}

const StoreContext = createContext<StoreValue | null>(null)

export function StoreProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<PersistedState>(() => seedState())
  const [currentUserId, setCurrentUserId] = useState<string | null>(null)
  const [hydrated, setHydrated] = useState(false)

  // Load persisted state on mount (client only)
  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      if (raw) {
        const persisted = JSON.parse(raw) as PersistedState
        // Merge in any seed modules/users added after this state was saved,
        // so new onboarding content appears without wiping saved progress.
        const moduleIds = new Set(persisted.modules.map((m) => m.id))
        const mergedModules = [
          ...persisted.modules,
          ...seedModules.filter((m) => !moduleIds.has(m.id)),
        ]
        const userIds = new Set(persisted.users.map((u) => u.id))
        const mergedUsers = [
          ...persisted.users,
          ...seedUsers.filter((u) => !userIds.has(u.id)),
        ]
        setState({ ...persisted, modules: mergedModules, users: mergedUsers })
      }
      const session = localStorage.getItem(SESSION_KEY)
      if (session) setCurrentUserId(session)
    } catch {
      // ignore corrupt storage
    }
    setHydrated(true)
  }, [])

  useEffect(() => {
    if (!hydrated) return
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
  }, [state, hydrated])

  useEffect(() => {
    if (!hydrated) return
    if (currentUserId) localStorage.setItem(SESSION_KEY, currentUserId)
    else localStorage.removeItem(SESSION_KEY)
  }, [currentUserId, hydrated])

  const value = useMemo<StoreValue>(() => {
    const currentUser = state.users.find((u) => u.id === currentUserId) ?? null

    const getUserProgress = (userId: string): UserProgress =>
      state.progress[userId] ?? freshProgress(userId)

    return {
      hydrated,
      currentUser,
      users: state.users,
      modules: state.modules,
      progress: state.progress,
      login: (email, password) => {
        const found = state.users.find(
          (u) => u.email.toLowerCase() === email.trim().toLowerCase() && u.password === password,
        )
        if (found) {
          setState((s) => {
            if (s.progress[found.id]) return s
            return { ...s, progress: { ...s.progress, [found.id]: freshProgress(found.id) } }
          })
          setCurrentUserId(found.id)
          return found
        }
        return null
      },
      logout: () => setCurrentUserId(null),
      getUserProgress,
      setModuleResult: (userId, moduleId, result) => {
        setState((s) => {
          const existing = s.progress[userId] ?? freshProgress(userId)
          return {
            ...s,
            progress: {
              ...s.progress,
              [userId]: {
                ...existing,
                modules: {
                  ...existing.modules,
                  [moduleId]: { moduleId, ...result },
                },
              },
            },
          }
        })
      },
      toggleChecklistItem: (userId, itemId) => {
        setState((s) => {
          const existing = s.progress[userId] ?? freshProgress(userId)
          return {
            ...s,
            progress: {
              ...s.progress,
              [userId]: {
                ...existing,
                checklist: existing.checklist.map((c) =>
                  c.id === itemId ? { ...c, done: !c.done } : c,
                ),
              },
            },
          }
        })
      },
      saveModule: (mod) => {
        setState((s) => {
          const exists = s.modules.some((m) => m.id === mod.id)
          return {
            ...s,
            modules: exists
              ? s.modules.map((m) => (m.id === mod.id ? mod : m))
              : [...s.modules, mod],
          }
        })
      },
      deleteModule: (moduleId) => {
        setState((s) => ({
          ...s,
          modules: s.modules.filter((m) => m.id !== moduleId),
        }))
      },
    }
  }, [state, currentUserId, hydrated])

  return <StoreContext.Provider value={value}>{children}</StoreContext.Provider>
}

export function useStore() {
  const ctx = useContext(StoreContext)
  if (!ctx) throw new Error("useStore must be used within StoreProvider")
  return ctx
}
