import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
    title: 'Hexabot | Institutional Trading Desk',
    description: 'Production-ready quantitative trading infrastructure.',
}

export default function RootLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <html lang="en">
            <head>
                <link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&family=Geist+Mono:wght@400;500&display=swap" rel="stylesheet" />
                <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' rx='25' fill='%232DD4BF'/><path d='M30 25V75M70 25V75M30 50H70' stroke='%23040405' stroke-width='12' stroke-linecap='round' stroke-linejoin='round'/></svg>" />
            </head>
            <body>{children}</body>
        </html>
    )
}
