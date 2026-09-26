import { cn } from "@/lib/utils"

export function Logo({ className }: { className?: string }) {
  return (
    <div className={cn("flex items-center gap-2", className)}>
      <span
        aria-hidden
        className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-foreground"
      >
        <svg viewBox="0 0 24 24" fill="none" className="h-5 w-5" stroke="currentColor" strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round">
          <path d="M3 21V5l9-3 9 3v16" />
          <path d="M3 21h18" />
          <path d="M9 21v-6h6v6" />
        </svg>
      </span>
      <span className="text-lg font-bold tracking-tight text-foreground">
        FIRM<span className="text-primary">FLOW</span>
      </span>
    </div>
  )
}
