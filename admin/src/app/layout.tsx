import type { Metadata } from 'next'
import './globals.css'
import ClientLayout from './ClientLayout'

export const metadata: Metadata = {
  title: 'FaceGuard Admin — Sécurité Industrielle',
  description: 'Plateforme d\'administration FaceGuard — Surveillance comportementale industrielle',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr" className="dark">
      <body>
        <ClientLayout>{children}</ClientLayout>
      </body>
    </html>
  )
}
