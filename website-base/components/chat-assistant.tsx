"use client"

import { useEffect, useRef, useState, type FormEvent } from "react"
import Link from "next/link"
import { Bot, ExternalLink, LoaderCircle, MessageCircle, Send, UserRound, X } from "lucide-react"
import { useStore } from "@/lib/store"

type Contact = {
  person_id: string
  name: string
  title: string
  department: string
  email: string
  phone_ext: string | null
  working_hours: string
  is_in_today: boolean
  out_of_office_until: string | null
  reason: string
  mailto: string
  backup: Contact | null
}

type ChatLink = {
  module_id: string
  module_title: string
  passage_id: string
  passage_heading: string | null
}

type ChatResponse = {
  intent: string
  answer: string
  links: ChatLink[]
  contacts: Contact[]
  used_fallback: boolean
}

type ChatMessage = {
  role: "assistant" | "user"
  text: string
  result?: ChatResponse
}

const starterMessage: ChatMessage = {
  role: "assistant",
  text: "Hi! I’m your FIRM FLOW assistant. Ask me where to find a policy or who can help with something at the firm.",
}

function findAccessToken(): string | null {
  try {
    for (const storage of [localStorage, sessionStorage]) {
      for (let index = 0; index < storage.length; index += 1) {
        const key = storage.key(index)
        if (!key?.startsWith("sb-") || !key.endsWith("-auth-token")) continue
        const value = storage.getItem(key)
        if (!value) continue
        const session = JSON.parse(value) as { access_token?: unknown; currentSession?: { access_token?: unknown } }
        const token = session.access_token ?? session.currentSession?.access_token
        if (typeof token === "string" && token.length > 0) return token
      }
    }
  } catch {
    // Ignore malformed or inaccessible browser storage; the request will show a useful auth error.
  }
  return null
}

function ContactCard({ contact }: { contact: Contact }) {
  return (
    <div className="border-[2px] border-[var(--color-black)] bg-[var(--color-white)] p-3 text-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-semibold">{contact.name}</p>
          <p className="text-xs text-[var(--color-black)]/70">{contact.title}{contact.department ? ` · ${contact.department}` : ""}</p>
        </div>
        <span className={`shrink-0 border px-2 py-1 text-[10px] font-semibold uppercase ${contact.is_in_today ? "border-green-800 bg-green-100 text-green-900" : "border-[var(--color-black)]/40 bg-[var(--color-offwhite)] text-[var(--color-black)]/70"}`}>
          {contact.is_in_today ? "In today" : "Out today"}
        </span>
      </div>
      <p className="mt-2 text-xs leading-relaxed text-[var(--color-black)]/75">{contact.reason}</p>
      <p className="mt-1 text-xs text-[var(--color-black)]/70">Hours: {contact.working_hours}{contact.phone_ext ? ` · Ext. ${contact.phone_ext}` : ""}</p>
      {contact.out_of_office_until && <p className="mt-1 text-xs text-[var(--color-black)]/70">Back {contact.out_of_office_until}</p>}
      <a className="mt-3 inline-flex items-center gap-1 border-[2px] border-[var(--color-black)] bg-[var(--color-primary)] px-3 py-2 text-xs font-semibold text-white transition-colors hover:bg-[var(--color-primary-hover)]" href={contact.mailto}>
        Email {contact.name.split(" ")[0]} <ExternalLink className="h-3 w-3" aria-hidden="true" />
      </a>
      {contact.backup && (
        <div className="mt-3 border-t border-[var(--color-black)]/20 pt-3">
          <p className="mb-2 text-[10px] font-semibold uppercase tracking-wide text-[var(--color-black)]/60">Backup contact</p>
          <ContactCard contact={{ ...contact.backup, backup: null }} />
        </div>
      )}
    </div>
  )
}

export function ChatAssistant() {
  const { modules } = useStore()
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([starterMessage])
  const [question, setQuestion] = useState("")
  const [error, setError] = useState("")
  const [sending, setSending] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" })
  }, [messages, sending, open])

  useEffect(() => {
    if (open) inputRef.current?.focus()
  }, [open])

  async function sendQuestion(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const trimmedQuestion = question.trim()
    if (!trimmedQuestion || sending) return

    setMessages((current) => [...current, { role: "user", text: trimmedQuestion }])
    setQuestion("")
    setError("")
    setSending(true)

    try {
      const token = findAccessToken()
      if (!token) {
        throw new Error("Chat needs an active Supabase sign-in. The current demo login does not create a backend session; sign in with your firm's connected account and try again.")
      }

      const apiBase = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "")
      const response = await fetch(`${apiBase}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ question: trimmedQuestion }),
      })

      if (!response.ok) {
        if (response.status === 401) throw new Error("Your sign-in session has expired. Sign in again to use the assistant.")
        if (response.status === 403) throw new Error("Your account does not have a FIRM FLOW profile yet. Please contact your administrator.")
        const payload = await response.json().catch(() => null) as { detail?: string } | null
        throw new Error(payload?.detail || `The assistant couldn't answer right now (HTTP ${response.status}). Please try again.`)
      }

      const result = await response.json() as ChatResponse
      setMessages((current) => [...current, { role: "assistant", text: result.answer, result }])
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Something went wrong. Please try again.")
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-label={open ? "Close assistant" : "Open assistant"}
        aria-expanded={open}
        className="relative flex h-10 items-center gap-2 border-[2px] border-[var(--color-white)] bg-[var(--color-black)] px-3 text-sm font-semibold text-[var(--color-white)] transition-colors hover:bg-[var(--color-primary)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-primary)]"
      >
        <MessageCircle className="h-4 w-4" aria-hidden="true" />
        <span className="hidden sm:inline">Ask assistant</span>
      </button>

      {open && (
        <section
          aria-label="FIRM FLOW assistant chat"
          className="fixed inset-x-3 bottom-3 z-50 flex h-[min(680px,calc(100dvh-1.5rem))] flex-col border-[2px] border-[var(--color-black)] bg-[var(--color-white)] text-[var(--color-black)] shadow-[8px_8px_0_var(--color-black)] sm:inset-x-auto sm:bottom-5 sm:right-5 sm:w-[min(420px,calc(100vw-2.5rem))]"
        >
          <div className="flex items-center justify-between border-b-[2px] border-[var(--color-black)] bg-[var(--color-black)] px-4 py-3 text-[var(--color-white)]">
            <div className="flex items-center gap-3">
              <span className="flex h-9 w-9 items-center justify-center border-[2px] border-[var(--color-white)] bg-[var(--color-primary)]">
                <Bot className="h-5 w-5" aria-hidden="true" />
              </span>
              <div>
                <h2 className="text-sm font-semibold">FIRM FLOW assistant</h2>
                <p className="text-xs text-white/70">Policies, procedures & people</p>
              </div>
            </div>
            <button type="button" onClick={() => setOpen(false)} aria-label="Close assistant" className="p-2 transition-colors hover:bg-white/15 focus-visible:outline-2 focus-visible:outline-white">
              <X className="h-5 w-5" aria-hidden="true" />
            </button>
          </div>

          <div className="flex-1 space-y-4 overflow-y-auto bg-[var(--color-offwhite)] p-4" aria-live="polite">
            {messages.map((message, index) => (
              <div key={`${index}-${message.role}`} className={`flex items-start gap-2 ${message.role === "user" ? "flex-row-reverse" : ""}`}>
                <span className={`mt-1 flex h-7 w-7 shrink-0 items-center justify-center border-[2px] border-[var(--color-black)] ${message.role === "user" ? "bg-[var(--color-primary)] text-white" : "bg-[var(--color-white)]"}`}>
                  {message.role === "user" ? <UserRound className="h-4 w-4" aria-hidden="true" /> : <Bot className="h-4 w-4" aria-hidden="true" />}
                </span>
                <div className={`min-w-0 max-w-[86%] space-y-3 ${message.role === "user" ? "text-right" : ""}`}>
                  <p
                    style={{ borderRadius: message.role === "user" ? "0 14px 0 0" : "14px 0 0 0" }}
                    className={`inline-block border-[2px] border-[var(--color-black)] px-3 py-2 text-left text-sm leading-relaxed ${message.role === "user" ? "bg-[var(--color-primary)] text-white" : "bg-[var(--color-white)]"}`}
                  >
                    {message.text}
                  </p>
                  {message.result?.used_fallback && (
                    <p className="text-left text-xs font-medium text-[var(--color-black)]/65">I couldn’t find a confident match, so this answer may be limited.</p>
                  )}
                  {!!message.result?.links.length && (
                    <div className="space-y-2 text-left">
                      <p className="text-[10px] font-bold uppercase tracking-wider text-[var(--color-black)]/60">Related onboarding</p>
                      {message.result.links.map((source) => {
                        const content = (
                          <>
                            <span className="block font-semibold">{source.module_title}</span>
                            {source.passage_heading && <span className="mt-1 block text-[var(--color-black)]/70">{source.passage_heading}</span>}
                          </>
                        )
                        return modules.some((module) => module.id === source.module_id) ? (
                          <Link key={source.passage_id} href={`/modules/${encodeURIComponent(source.module_id)}`} onClick={() => setOpen(false)} className="block border-[2px] border-[var(--color-black)] bg-[var(--color-white)] p-3 text-xs transition-colors hover:bg-[var(--color-primary)]/10">
                            {content}
                          </Link>
                        ) : (
                          <div key={source.passage_id} className="border-[2px] border-[var(--color-black)] bg-[var(--color-white)] p-3 text-xs">
                            {content}
                          </div>
                        )
                      })}
                    </div>
                  )}
                  {!!message.result?.contacts.length && (
                    <div className="space-y-2 text-left">
                      <p className="text-[10px] font-bold uppercase tracking-wider text-[var(--color-black)]/60">People who can help</p>
                      {message.result.contacts.map((contact) => <ContactCard key={contact.person_id} contact={contact} />)}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {messages.length === 1 && (
              <div className="ml-9 flex flex-wrap gap-2">
                {["Where can I find the PTO policy?", "Who can help with Revit?"].map((prompt) => (
                  <button key={prompt} type="button" onClick={() => setQuestion(prompt)} className="border border-[var(--color-black)]/35 bg-[var(--color-white)] px-2 py-1.5 text-left text-xs transition-colors hover:border-[var(--color-black)] hover:bg-[var(--color-primary)]/10">
                    {prompt}
                  </button>
                ))}
              </div>
            )}
            {sending && (
              <div className="ml-9 flex items-center gap-2 border-[2px] border-[var(--color-black)] bg-[var(--color-white)] px-3 py-2 text-xs" role="status">
                <LoaderCircle className="h-4 w-4 animate-spin" aria-hidden="true" /> Looking through firm resources…
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {error && <p role="alert" className="border-t-[2px] border-[var(--color-black)] bg-[var(--color-primary)]/10 px-4 py-3 text-xs leading-relaxed">{error}</p>}

          <form onSubmit={sendQuestion} className="border-t-[2px] border-[var(--color-black)] bg-[var(--color-white)] p-3">
            <label htmlFor="assistant-question" className="sr-only">Ask a question</label>
            <div className="flex items-end gap-2">
              <textarea
                id="assistant-question"
                ref={inputRef}
                value={question}
                onChange={(event) => setQuestion(event.target.value.slice(0, 500))}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && !event.shiftKey) {
                    event.preventDefault()
                    event.currentTarget.form?.requestSubmit()
                  }
                }}
                placeholder="Ask about a policy or person…"
                rows={2}
                maxLength={500}
                disabled={sending}
                className="min-h-11 flex-1 resize-none border-[2px] border-[var(--color-black)] bg-[var(--color-white)] px-3 py-2 text-sm outline-none placeholder:text-[var(--color-black)]/50 focus-visible:ring-2 focus-visible:ring-[var(--color-primary)] disabled:opacity-60"
              />
              <button type="submit" aria-label="Send question" disabled={!question.trim() || sending} className="flex h-11 w-11 shrink-0 items-center justify-center border-[2px] border-[var(--color-black)] bg-[var(--color-primary)] text-white transition-colors hover:bg-[var(--color-primary-hover)] disabled:cursor-not-allowed disabled:opacity-45">
                {sending ? <LoaderCircle className="h-4 w-4 animate-spin" aria-hidden="true" /> : <Send className="h-4 w-4" aria-hidden="true" />}
              </button>
            </div>
            <p className="mt-1 text-right text-[10px] text-[var(--color-black)]/55">{question.length}/500 · Enter to send</p>
          </form>
        </section>
      )}
    </div>
  )
}
