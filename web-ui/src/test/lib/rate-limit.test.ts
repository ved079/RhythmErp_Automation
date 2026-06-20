import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { checkRateLimit, getClientIp } from '@/lib/rate-limit'

beforeEach(() => {
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
})

describe('checkRateLimit', () => {
  it('allows the first request', () => {
    const result = checkRateLimit('127.0.0.1', 'login')
    expect(result.limited).toBe(false)
  })

  it('allows requests under the limit', () => {
    for (let i = 0; i < 10; i++) {
      const result = checkRateLimit('192.168.1.1', 'api')
      expect(result.limited).toBe(false)
    }
  })

  it('blocks requests over the limit', () => {
    for (let i = 0; i < 10; i++) {
      checkRateLimit('10.0.0.1', 'login')
    }
    const blocked = checkRateLimit('10.0.0.1', 'login')
    expect(blocked.limited).toBe(true)
    expect(blocked.retryAfterMs).toBeGreaterThan(0)
  })

  it('does not affect other IPs for the same endpoint', () => {
    for (let i = 0; i < 10; i++) {
      checkRateLimit('10.0.0.3', 'login')
    }
    const other = checkRateLimit('10.0.0.4', 'login')
    expect(other.limited).toBe(false)
  })

  it('does not affect the same IP for a different endpoint', () => {
    for (let i = 0; i < 10; i++) {
      checkRateLimit('10.0.0.8', 'login')
    }
    const different = checkRateLimit('10.0.0.8', 'forgot-password')
    expect(different.limited).toBe(false)
  })

  it('resets the window after the time period', () => {
    const options = { windowMs: 60_000, maxRequests: 3 }
    for (let i = 0; i < 3; i++) {
      checkRateLimit('10.0.0.5', 'login', options)
    }
    expect(checkRateLimit('10.0.0.5', 'login', options).limited).toBe(true)

    vi.advanceTimersByTime(60_001)
    expect(checkRateLimit('10.0.0.5', 'login', options).limited).toBe(false)
  })

  it('respects custom maxRequests', () => {
    const options = { maxRequests: 1 }
    const ip = '10.0.0.6'
    expect(checkRateLimit(ip, 'login', options).limited).toBe(false)
    expect(checkRateLimit(ip, 'login', options).limited).toBe(true)
  })

  it('respects custom windowMs', () => {
    const options = { windowMs: 10_000, maxRequests: 1 }
    const ip = '10.0.0.7'
    expect(checkRateLimit(ip, 'login', options).limited).toBe(false)
    expect(checkRateLimit(ip, 'login', options).limited).toBe(true)
    vi.advanceTimersByTime(10_001)
    expect(checkRateLimit(ip, 'login', options).limited).toBe(false)
  })
})

describe('getClientIp', () => {
  const mockRequest = (headers: Record<string, string>): Request =>
    ({ headers: { get: (name: string) => headers[name] ?? null } }) as unknown as Request

  it('extracts IP from x-forwarded-for', () => {
    const req = mockRequest({ 'x-forwarded-for': '203.0.113.1, 10.0.0.1' })
    expect(getClientIp(req)).toBe('203.0.113.1')
  })

  it('extracts IP from x-real-ip when x-forwarded-for is absent', () => {
    const req = mockRequest({ 'x-real-ip': '198.51.100.1' })
    expect(getClientIp(req)).toBe('198.51.100.1')
  })

  it('falls back to "unknown" when no headers are present', () => {
    const req = mockRequest({})
    expect(getClientIp(req)).toBe('unknown')
  })
})
