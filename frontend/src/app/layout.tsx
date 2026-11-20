import type { Metadata } from 'next'
import './globals.css'
import { AuthProvider } from '@/components/auth/AuthProvider'

export const metadata: Metadata = {
  title: {
    default: 'Court Vision AI — AI-Powered Legal Case Preparation',
    template: '%s | Court Vision AI',
  },
  description:
    'Transform complex case files into structured case intelligence, evidence trails and trial-ready insights. Built for law students, junior advocates, and legal researchers.',
  keywords: ['legal AI', 'case preparation', 'law student', 'trial preparation', 'legal research', 'moot court'],
  authors: [{ name: 'Court Vision AI' }],
  openGraph: {
    title: 'Court Vision AI',
    description: 'Prepare Before You Enter the Courtroom.',
    type: 'website',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" data-scroll-behavior="smooth">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  )
}
