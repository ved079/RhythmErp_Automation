// ─── Next.js Middleware ──────────────────────────────────────
// Centralized route protection — runs before every API request.
// Public routes (no auth required):
//   - /api/auth/login  (POST)
//   - /api/auth/seed   (POST)
//   - /api/route.ts    (health check)
// All other /api/* routes require a valid session cookie.

import { NextRequest, NextResponse } from 'next/server'

// Routes that don't require authentication
const PUBLIC_ROUTES = new Set([
  '/api/auth/login',
  '/api/auth/seed',
  '/api',
])

// Route prefixes that don't require authentication
const PUBLIC_PREFIXES = [
  '/api/auth/login',
  '/api/auth/seed',
]

function isPublicRoute(pathname: string): boolean {
  if (PUBLIC_ROUTES.has(pathname)) return true
  for (const prefix of PUBLIC_PREFIXES) {
    if (pathname.startsWith(prefix)) return true
  }
  return false
}

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl

  // Only protect /api/* routes
  if (!pathname.startsWith('/api/')) {
    return NextResponse.next()
  }

  // Allow public routes through
  if (isPublicRoute(pathname)) {
    return NextResponse.next()
  }

  // Check for session cookie
  const token = req.cookies.get('session_token')?.value

  if (!token) {
    return NextResponse.json(
      { error: 'Not authenticated' },
      { status: 401 }
    )
  }

  // Token exists — let the route handler do full validation
  // (middleware runs on the Edge runtime, can't access Prisma directly)
  return NextResponse.next()
}

export const config = {
  // Match all API routes
  matcher: ['/api/:path*'],
}
