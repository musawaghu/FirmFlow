import { cn } from "@/lib/utils"

type LogoProps = {
  className?: string
  /** "dark" places the mark on a light tile so its navy stroke stays visible on black backgrounds. */
  variant?: "light" | "dark"
  size?: "md" | "lg"
}

export function Logo({ className, variant = "light", size = "md" }: LogoProps) {
  const lg = size === "lg"
  return (
    <div className={cn("flex items-center", lg ? "gap-3" : "gap-2", className)}>
      <span
        aria-hidden
        className={cn(
          "flex items-center justify-center border-[2px] bg-[var(--color-white)]",
          variant === "dark" ? "border-[var(--color-white)]" : "border-[var(--color-black)]",
          lg ? "h-14 w-14" : "h-9 w-9",
        )}
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/logo.png" alt="" className={cn("w-auto object-contain", lg ? "h-10" : "h-6")} />
      </span>
      <span
        className={cn(
          "font-bold tracking-tight",
          variant === "dark" ? "text-[var(--color-white)]" : "text-[var(--color-black)]",
          lg ? "text-3xl" : "text-lg",
        )}
      >
        FIRM<span className="text-[var(--color-primary)]">FLOW</span>
      </span>
    </div>
  )
}
