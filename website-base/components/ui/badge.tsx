import { mergeProps } from "@base-ui/react/merge-props"
import { useRender } from "@base-ui/react/use-render"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "cn"

const badgeVariants = cva(
  "group/badge inline-flex h-6 w-fit shrink-0 items-center justify-center gap-1 overflow-hidden border-[2px] border-[var(--color-black)] px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide whitespace-nowrap transition-all duration-200 focus-visible:border-[var(--color-primary)] focus-visible:ring-[3px] focus-visible:ring-[var(--color-primary)]/50 has-data-[icon=inline-end]:pr-1.5 has-data-[icon=inline-start]:pl-1.5 aria-invalid:border-destructive aria-invalid:ring-destructive/20 [&>svg]:pointer-events-none [&>svg]:size-3!",
  {
    variants: {
      variant: {
        default: 'bg-[var(--color-primary)] text-[var(--color-white)] [a]:hover:bg-[var(--color-primary-hover)]',
        secondary:
          'bg-[var(--color-offwhite)] text-[var(--color-black)] [a]:hover:bg-[var(--color-offwhite)]',
        destructive:
          'bg-[var(--color-primary)] text-[var(--color-white)] focus-visible:ring-destructive/20 [a]:hover:bg-[var(--color-primary-hover)]',
        outline:
          'bg-[var(--color-white)] text-[var(--color-black)] [a]:hover:bg-[var(--color-offwhite)]',
        ghost:
          'border-transparent bg-transparent text-[var(--color-black)] hover:bg-[var(--color-offwhite)]',
        link: 'border-transparent bg-transparent p-0 text-[var(--color-primary)] underline-offset-4 hover:underline',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
)

function Badge({
  className,
  variant = "default",
  render,
  ...props
}: useRender.ComponentProps<"span"> & VariantProps<typeof badgeVariants>) {
  return useRender({
    defaultTagName: "span",
    props: mergeProps<"span">(
      {
        className: cn(badgeVariants({ variant }), className),
      },
      props
    ),
    render,
    state: {
      slot: "badge",
      variant,
    },
  })
}

export { Badge, badgeVariants }
