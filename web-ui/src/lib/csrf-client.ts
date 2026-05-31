// ─── Client-side CSRF Helper ─────────────────────────────────
// C6: Provides utilities for reading the CSRF token from the cookie
// and including it in fetch request headers.
// Used by all pages that make state-changing API requests.

/**
 * Get CSRF token from the csrf_token cookie (set by middleware).
 */
export function getCsrfToken(): string {
  if (typeof document === 'undefined') return ''
  const match = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]*)/)
  return match ? decodeURIComponent(match[1]) : ''
}

/**
 * Create headers object with CSRF token included.
 * Merges with any existing headers.
 */
export function csrfHeaders(existing?: Record<string, string>): Record<string, string> {
  const token = getCsrfToken()
  return {
    ...existing,
    ...(token ? { 'X-CSRF-Token': token } : {}),
  }
}

/**
 * Enhance a fetch options object with the CSRF token header.
 */
export function withCsrf(options: RequestInit = {}): RequestInit {
  const token = getCsrfToken()
  if (!token) return options

  const headers = new Headers(options.headers || {})
  headers.set('X-CSRF-Token', token)

  return { ...options, headers }
}
