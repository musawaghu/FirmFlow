// Solid, straight-edged icons in the spirit of Design.md section 7 (Flaticon "Straight", solid).
// They fill with currentColor, so they are black on light surfaces and white on black ones.
// Swap in the licensed Flaticon SVGs later by replacing the paths here.

const PATHS = {
  // Arrow leaving a door frame.
  logout: "M3 3h10v4h-2V5H5v14h6v-2h2v4H3zM16 7l5 5-5 5v-4H9v-2h7z",
  // Arrow entering a door frame.
  login: "M11 3h10v18H11v-4h2v2h6V5h-6v2h-2zM8 7l5 5-5 5v-4H2v-2h6z",
  check: "M9 16.2 4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4z",
  close: "M6.4 5 12 10.6 17.6 5 19 6.4 13.4 12 19 17.6 17.6 19 12 13.4 6.4 19 5 17.6 10.6 12 5 6.4z",
  // Open book.
  book: "M2 4h7a3 3 0 0 1 3 3v13a2 2 0 0 0-2-2H2zM22 4h-7a3 3 0 0 0-3 3v13a2 2 0 0 1 2-2h8z",
  home: "M12 3 2 11h3v10h5v-6h4v6h5V11h3z",
  chart: "M3 3h2v16h16v2H3zM7 12h3v5H7zM12 8h3v9h-3zM17 5h3v12h-3z",
  users: "M8 4a4 4 0 1 1 0 8 4 4 0 0 1 0-8zm8 1a3 3 0 1 1 0 6 3 3 0 0 1 0-6zM1 20c0-4 3-6 7-6s7 2 7 6zm15 0c0-2-.7-3.7-2-5 4.4-.6 9 1 9 5z",
  alert: "M12 2 1 21h22zm-1 7h2v6h-2zm0 8h2v2h-2z",
  lock: "M6 10V7a6 6 0 1 1 12 0v3h2v12H4V10zm2 0h8V7a4 4 0 1 0-8 0z",
  building: "M3 21V3h12v6h6v12h-8v-4h-2v4zm3-15v2h2V6zm4 0v2h2V6zM6 10v2h2v-2zm4 0v2h2v-2zm7 2v2h2v-2zm0 4v2h2v-2zM6 14v2h2v-2zm4 0v2h2v-2z",
  layers: "M12 2 1 8l11 6 11-6zM3.5 12.5 1 14l11 6 11-6-2.5-1.5L12 17.2z",
  edit: "M3 17.3V21h3.7L17.8 9.9l-3.7-3.7zM20.7 7 17 3.3l-2.1 2.1 3.7 3.7z",
  eyeOff: "M2 4.3 3.3 3 21 20.7 19.7 22l-3.1-3.1A11 11 0 0 1 12 20C6 20 2 12 2 12a19 19 0 0 1 4.4-5.3zM12 4c6 0 10 8 10 8a19 19 0 0 1-3 4.2l-3.3-3.3A4 4 0 0 0 11.1 8.3L8.5 5.7A10 10 0 0 1 12 4z",
  question: "M12 2a10 10 0 1 1 0 20 10 10 0 0 1 0-20zm-1 14v2h2v-2zm1-10a4 4 0 0 0-4 4h2a2 2 0 1 1 3 1.7c-1.2.7-2 1.6-2 3.3h2c0-.9.4-1.3 1-1.7A4 4 0 0 0 12 6z",
  star: "M12 2l3 7h7l-5.6 4.4L18.5 21 12 16.6 5.5 21l2.1-7.6L2 9h7z",
  arrowRight: "M4 11h12.2l-5.6-5.6L12 4l8 8-8 8-1.4-1.4 5.6-5.6H4z",
} as const;

export type IconName = keyof typeof PATHS;

export function Icon({ name, size = 18, label }: { name: IconName; size?: number; label?: string }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="currentColor"
      role={label ? "img" : undefined}
      aria-label={label}
      aria-hidden={label ? undefined : true}
      focusable="false"
      style={{ flexShrink: 0 }}
    >
      <path fillRule="evenodd" d={PATHS[name]} />
    </svg>
  );
}
