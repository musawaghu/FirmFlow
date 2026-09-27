import * as React from "react"
import { Input as InputPrimitive } from "@base-ui/react/input"
import { cn } from "cn"

function Input({ className, type, ...props }: React.ComponentProps<"input">) {
  return (
    <InputPrimitive
      type={type}
      data-slot="input"
      className={cn(
        "h-10 w-full min-w-0 border-[2px] border-[var(--color-black)] bg-[var(--color-white)] px-3 py-2 text-base text-[var(--color-black)] transition-colors outline-none file:inline-flex file:h-6 file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-[var(--color-black)] placeholder:text-[var(--color-black)]/60 focus-visible:border-[var(--color-primary)] focus-visible:ring-2 focus-visible:ring-[var(--color-primary)]/50 disabled:pointer-events-none disabled:cursor-not-allowed disabled:bg-[var(--color-offwhite)] disabled:opacity-50 aria-invalid:border-[var(--color-primary)] aria-invalid:ring-2 aria-invalid:ring-[var(--color-primary)]/20 md:text-sm",
        className
      )}
      {...props}
    />
  )
}

export { Input }
