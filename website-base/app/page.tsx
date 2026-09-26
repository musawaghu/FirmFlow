"use client"

import { useState, type FormEvent } from "react"
import { useRouter } from "next/navigation"
import { useStore } from "@/lib/store"
import { Logo } from "@/components/logo"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent } from "@/components/ui/card"

export default function LoginPage() {
  const { login } = useStore()
  const router = useRouter()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState<string | null>(null)

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    const user = login(email, password)
    if (!user) {
      setError("Incorrect email or password. Try one of the demo accounts below.")
      return
    }
    router.push(user.role === "admin" ? "/admin" : "/dashboard")
  }

  function quickFill(demoEmail: string, demoPassword: string) {
    setEmail(demoEmail)
    setPassword(demoPassword)
  }

  return (
    <main className="flex min-h-screen flex-col lg:flex-row">
      {/* Brand / value panel */}
      <section className="relative flex flex-1 flex-col justify-between overflow-hidden bg-primary px-8 py-10 text-primary-foreground lg:px-14 lg:py-14">
        <Logo className="[&_span:last-child]:text-white [&_.bg-primary]:bg-white [&_.bg-primary]:text-primary" />
        <div className="max-w-md">
          <h1 className="text-balance text-3xl font-bold leading-tight lg:text-4xl">
            Onboarding for architects, made clear and trackable.
          </h1>
          <p className="mt-4 text-pretty text-sm leading-relaxed text-primary-foreground/85 lg:text-base">
            Structured modules, guided quizzes, and a personal checklist so every new team member
            knows exactly what matters on Day 1 and beyond.
          </p>
          <ul className="mt-6 space-y-2 text-sm text-primary-foreground/85">
            {["Multimodal, organized content", "Trackable progress", "Interactive support & mentors"].map((f) => (
              <li key={f} className="flex items-center gap-2">
                <span aria-hidden className="h-1.5 w-1.5 rounded-full bg-white" />
                {f}
              </li>
            ))}
          </ul>
        </div>
        <p className="text-xs text-primary-foreground/70">Internal knowledge platform</p>
      </section>

      {/* Login form */}
      <section className="flex flex-1 items-center justify-center bg-background px-6 py-12">
        <div className="w-full max-w-sm">
          <h2 className="text-2xl font-semibold text-foreground">Welcome back</h2>
          <p className="mt-1 text-sm text-muted-foreground">Sign in to continue your onboarding.</p>

          <form onSubmit={handleSubmit} className="mt-8 space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                placeholder="you@firmflow.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            {error && (
              <p role="alert" className="text-sm text-destructive">
                {error}
              </p>
            )}
            <Button type="submit" className="w-full">
              Sign in
            </Button>
          </form>

          <Card className="mt-8 border-dashed bg-muted/40">
            <CardContent className="space-y-3 py-4">
              <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Demo accounts
              </p>
              <button
                type="button"
                onClick={() => quickFill("ava@firmflow.com", "welcome")}
                className="flex w-full items-center justify-between rounded-md px-3 py-2 text-left text-sm transition-colors hover:bg-secondary"
              >
                <span>
                  <span className="font-medium text-foreground">New employee</span>
                  <span className="block text-xs text-muted-foreground">ava@firmflow.com</span>
                </span>
                <span className="text-xs text-muted-foreground">welcome</span>
              </button>
              <button
                type="button"
                onClick={() => quickFill("admin@firmflow.com", "admin123")}
                className="flex w-full items-center justify-between rounded-md px-3 py-2 text-left text-sm transition-colors hover:bg-secondary"
              >
                <span>
                  <span className="font-medium text-foreground">Admin</span>
                  <span className="block text-xs text-muted-foreground">admin@firmflow.com</span>
                </span>
                <span className="text-xs text-muted-foreground">admin123</span>
              </button>
            </CardContent>
          </Card>
        </div>
      </section>
    </main>
  )
}
