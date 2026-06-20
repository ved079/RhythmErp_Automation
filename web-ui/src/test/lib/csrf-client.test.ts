import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { getCsrfToken, csrfHeaders, withCsrf } from '@/lib/csrf-client'

const TOKEN = 'test-csrf-token-123'

beforeEach(() => {
  document.cookie = `csrf_token=${TOKEN}; path=/`
})

afterEach(() => {
  document.cookie = 'csrf_token=; path=/; max-age=0'
})

describe('getCsrfToken', () => {
  it('returns the token from the cookie', () => {
    expect(getCsrfToken()).toBe(TOKEN)
  })

  it('returns empty string when no cookie is set', () => {
    document.cookie = 'csrf_token=; path=/; max-age=0'
    expect(getCsrfToken()).toBe('')
  })
})

describe('csrfHeaders', () => {
  it('includes X-CSRF-Token when token is present', () => {
    const headers = csrfHeaders()
    expect(headers['X-CSRF-Token']).toBe(TOKEN)
  })

  it('preserves existing headers', () => {
    const headers = csrfHeaders({ 'Content-Type': 'application/json' })
    expect(headers['Content-Type']).toBe('application/json')
    expect(headers['X-CSRF-Token']).toBe(TOKEN)
  })

  it('overwrites X-CSRF-Token if already present', () => {
    const headers = csrfHeaders({ 'X-CSRF-Token': 'old' })
    expect(headers['X-CSRF-Token']).toBe(TOKEN)
  })

  it('returns empty object when no token and no existing headers', () => {
    document.cookie = 'csrf_token=; path=/; max-age=0'
    expect(csrfHeaders()).toEqual({})
  })
})

describe('withCsrf', () => {
  it('adds X-CSRF-Token header to fetch options', () => {
    const options = withCsrf({ method: 'POST' })
    const headers = options.headers as Headers
    expect(headers.get('X-CSRF-Token')).toBe(TOKEN)
    expect(options.method).toBe('POST')
  })

  it('preserves existing headers when adding CSRF token', () => {
    const options = withCsrf({
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    })
    const headers = options.headers as Headers
    expect(headers.get('Content-Type')).toBe('application/json')
    expect(headers.get('X-CSRF-Token')).toBe(TOKEN)
  })

  it('works with no existing options', () => {
    const options = withCsrf()
    const headers = options.headers as Headers
    expect(headers.get('X-CSRF-Token')).toBe(TOKEN)
  })

  it('returns options unchanged when no token is present', () => {
    document.cookie = 'csrf_token=; path=/; max-age=0'
    const options = withCsrf({ method: 'GET' })
    expect(options).toEqual({ method: 'GET' })
    expect((options.headers as Headers)?.get?.('X-CSRF-Token')).toBeUndefined()
  })
})
