import { Button as ButtonPrimitive } from '@base-ui/react/button'
import { cva, type VariantProps } from 'class-variance-authority'

import { cn } from '@/lib/utils'

const buttonVariants = cva(
  "group/button inline-flex shrink-0 items-center justify-center border-[2px] border-[var(--color-black)] bg-clip-padding text-sm font-semibold whitespace-nowrap transition-all duration-200 outline-none select-none focus-visible:border-[var(--color-primary)] focus-visible:ring-2 focus-visible:ring-[var(--color-primary)]/50 disabled:pointer-events-none disabled:opacity-50 aria-invalid:border-destructive aria-invalid:ring-2 aria-invalid:ring-destructive/20 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
  {
    variants: {
      variant: {
        default: 'bg-[var(--color-primary)] text-[var(--color-white)] hover:bg-[var(--color-primary-hover)] hover:rounded-[var(--radius-hover)]',
        outline:
          'bg-[var(--color-white)] text-[var(--color-black)] hover:bg-[var(--color-offwhite)] hover:rounded-[var(--radius-hover)]',
        secondary:
          'bg-[var(--color-secondary)] text-[var(--color-black)] hover:bg-[var(--color-secondary-hover)] hover:rounded-[var(--radius-hover)]',
        ghost:
          'border-transparent bg-transparent text-[var(--color-black)] hover:bg-[var(--color-offwhite)] hover:rounded-[var(--radius-hover)]',
        destructive:
          'bg-[var(--color-primary)] text-[var(--color-white)] hover:bg-[var(--color-primary-hover)] hover:rounded-[var(--radius-hover)] focus-visible:border-[var(--color-primary-hover)] focus-visible:ring-[var(--color-primary)]/20',
        link: 'border-transparent bg-transparent p-0 text-[var(--color-primary)] underline-offset-4 hover:underline',
      },
      size: {
        default:
          'h-10 gap-1.5 px-3 has-data-[icon=inline-end]:pr-2 has-data-[icon=inline-start]:pl-2',
        xs: "h-7 gap-1 px-2 text-xs has-data-[icon=inline-end]:pr-1.5 has-data-[icon=inline-start]:pl-1.5 [&_svg:not([class*='size-'])]:size-3",
        sm: "h-8 gap-1 px-2.5 text-[0.8rem] has-data-[icon=inline-end]:pr-1.5 has-data-[icon=inline-start]:pl-1.5 [&_svg:not([class*='size-'])]:size-3.5",
        lg: 'h-11 gap-1.5 px-4 has-data-[icon=inline-end]:pr-3 has-data-[icon=inline-start]:pl-3',
        icon: 'size-8',
        'icon-xs': "size-6 [&_svg:not([class*='size-'])]:size-3",
        'icon-sm': "size-7 [&_svg:not([class*='size-'])]:size-3.5",
        'icon-lg': 'size-9',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  },
)

function Button({
  className,
  variant = 'default',
  size = 'default',
  ...props
}: ButtonPrimitive.Props & VariantProps<typeof buttonVariants>) {
  return (
    <ButtonPrimitive
      data-slot="button"
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  )
}

export { Button, buttonVariants }
