"use client"

import type { ChecklistItem } from "@/lib/types"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"

export function ChecklistCard({
  items,
  onToggle,
}: {
  items: ChecklistItem[]
  onToggle: (id: string) => void
}) {
  const done = items.filter((i) => i.done).length
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between text-base font-semibold">
          Day 1 checklist
          <span className="text-sm font-semibold text-[var(--color-black)]">
            {done}/{items.length}
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-1">
        {items.map((item) => (
          <label
            key={item.id}
            className="flex cursor-pointer items-start gap-3 py-2 transition-colors hover:bg-[var(--color-offwhite)]"
          >
            <Checkbox
              checked={item.done}
              onCheckedChange={() => onToggle(item.id)}
              className="mt-0.5"
            />
            <span
              className={
                item.done
                  ? "text-sm text-[var(--color-black)]/60 line-through"
                  : "text-sm text-[var(--color-black)]"
              }
            >
              {item.label}
            </span>
          </label>
        ))}
      </CardContent>
    </Card>
  )
}
