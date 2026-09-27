"use client"

import Link from "next/link"
import { useRouter } from "next/navigation"
import { useStore } from "@/lib/store"
import { Logo } from "@/components/logo"
import { ChatAssistant } from "@/components/chat-assistant"
import {
  Avatar,
  AvatarFallback,
} from "@/components/ui/avatar"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

function initials(name: string) {
  return name
    .split(" ")
    .map((p) => p[0])
    .slice(0, 2)
    .join("")
    .toUpperCase()
}

export function AppHeader({ homeHref }: { homeHref: string }) {
  const { currentUser, logout } = useStore()
  const router = useRouter()

  function handleLogout() {
    logout()
    router.push("/")
  }

  return (
    <header className="sticky top-0 z-20 border-b-[2px] border-[var(--color-black)] bg-[var(--color-black)] text-[var(--color-white)]">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
        <Link href={homeHref} className="transition-opacity hover:opacity-80">
          <Logo className="[&_span:last-child]:text-[var(--color-white)] [&_.bg-primary]:bg-[var(--color-white)] [&_.bg-primary]:text-[var(--color-black)]" />
        </Link>

        {currentUser && (
          <div className="flex items-center gap-2">
            <ChatAssistant />
            <DropdownMenu>
              <DropdownMenuTrigger className="flex items-center gap-2 border-[2px] border-[var(--color-white)] bg-[var(--color-black)] px-2 py-1 text-left outline-none transition-colors hover:bg-[var(--color-primary)] focus-visible:ring-2 focus-visible:ring-[var(--color-primary)]">
                <div className="hidden text-right sm:block">
                  <p className="text-sm font-medium leading-none text-[var(--color-white)]">{currentUser.name}</p>
                  <p className="text-xs capitalize text-[var(--color-white)]/75">{currentUser.role}</p>
                </div>
                <Avatar className="h-9 w-9 border-[2px] border-[var(--color-white)] bg-[var(--color-primary)]">
                  <AvatarFallback className="bg-[var(--color-primary)] text-[var(--color-white)] text-xs font-semibold">
                    {initials(currentUser.name)}
                  </AvatarFallback>
                </Avatar>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-52">
                <DropdownMenuGroup>
                  <DropdownMenuLabel>
                    <span className="block font-medium">{currentUser.name}</span>
                    <span className="block text-xs font-normal text-[var(--color-black)]/70">
                      {currentUser.email}
                    </span>
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={handleLogout}>Log out</DropdownMenuItem>
                </DropdownMenuGroup>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        )}
      </div>
    </header>
  )
}
