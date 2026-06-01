// ─── In-Memory Rate Limiter ──────────────────────────────────
// Tracks request counts per IP per endpoint window.
// Uses a sliding-window approach with periodic cleanup.
// No external dependencies required — works in Next.js Edge + Node.

interface RateLimitEntry {
  count: number
  resetAt: number
}

// Map<key (ip:endpoint), entry>
const rateLimitStore = new Map<string, RateLimitEntry>()

// Cleanup old entries every 60 seconds
let lastCleanup = Date.now()
const CLEANUP_INTERVAL = 60_000

function cleanupStore() {
  const now = Date.now()
  if (now - lastCleanup < CLEANUP_INTERVAL) return
  lastCleanup = now
  for (const [key, entry] of rateLimitStore) {
    if (now > entry.resetAt) {
      rateLimitStore.delete(key)
    }
  }
}

export interface RateLimitOptions {
  /** Time window in milliseconds (default: 60_000 = 1 minute) */
  windowMs?: number
  /** Max requests per window per IP (default: 10) */
  maxRequests?: number
}

/**
 * Check if a request should be rate-limited.
 * Returns { limited: true } if the request exceeds the limit,
 * or { limited: false } if it's allowed.
 *
 * @param ip - The client IP address
 * @param endpoint - A label for the endpoint (e.g. 'login', 'forgot-password')
 * @param options - Window size and max requests
 */
export function checkRateLimit(
  ip: string,
  endpoint: string,
  options: RateLimitOptions = {}
): { limited: boolean; retryAfterMs?: number } {
  cleanupStore()

  const windowMs = options.windowMs ?? 60_000
  const maxRequests = options.maxRequests ?? 10
  const now = Date.now()
  const key = `${ip}:${endpoint}`

  const entry = rateLimitStore.get(key)

  if (!entry || now > entry.resetAt) {
    // New window
    rateLimitStore.set(key, { count: 1, resetAt: now + windowMs })
    return { limited: false }
  }

  entry.count++

  if (entry.count > maxRequests) {
    const retryAfterMs = entry.resetAt - now
    return { limited: true, retryAfterMs }
  }

  return { limited: false }
}

/**
 * Extract client IP from a Next.js request.
 * Checks common proxy headers first, falls back to 'unknown'.
 */
export function getClientIp(request: Request): string {
  const forwarded = request.headers.get('x-forwarded-for')
  if (forwarded) {
    // x-forwarded-for may contain multiple IPs; first is the client
    return forwarded.split(',')[0].trim()
  }
  const realIp = request.headers.get('x-real-ip')
  if (realIp) return realIp.trim()
  return 'unknown'
}
