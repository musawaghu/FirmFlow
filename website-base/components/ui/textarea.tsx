import * as React from "react"
import { cn } from "cn"

function Textarea({ className, ...props }: React.ComponentProps<"textarea">) {
  return (
    <textarea
      data-slot="textarea"
      className={cn(
        "flex field-sizing-content min-h-16 w-full border-[2px] border-[var(--color-black)] bg-[var(--color-white)] px-3 py-2 text-base text-[var(--color-black)] transition-colors outline-none placeholder:text-[var(--color-black)]/60 focus-visible:border-[var(--color-primary)] focus-visible:ring-2 focus-visible:ring-[var(--color-primary)]/50 disabled:cursor-not-allowed disabled:bg-[var(--color-offwhite)] disabled:opacity-50 aria-invalid:border-[var(--color-primary)] aria-invalid:ring-2 aria-invalid:ring-[var(--color-primary)]/20 md:text-sm",
        className
      )}
      {...props}
    />
  )
}

export { Textarea }
