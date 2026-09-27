import { Analytics } from '@vercel/analytics/next'
import type { Metadata, Viewport } from 'next'
import './globals.css'
import { Providers } from './providers'

export const metadata: Metadata = {
  title: 'FIRM FLOW — Architect Onboarding',
  description:
    'FIRM FLOW is a guided onboarding platform that helps new architects learn company tools and workflows with structured modules, quizzes, and progress tracking.',
  generator: 'v0.app',
  icons: {
    icon: [{ url: '/icon-32x32.png', sizes: '32x32', type: 'image/png' }],
    apple: '/apple-icon.png',
  },
}

export const viewport: Viewport = {
  colorScheme: 'light',
  themeColor: '#f85a3e',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className="light">
      <body className="antialiased">
        <Providers>{children}</Providers>
        {process.env.NODE_ENV === 'production' && <Analytics />}
      </body>
    </html>
  )
}
