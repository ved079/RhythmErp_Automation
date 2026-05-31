import { NextRequest, NextResponse } from 'next/server'
import ZAI from 'z-ai-web-dev-sdk'
import { validateSession } from '@/lib/session'
import { checkRateLimit, getClientIp } from '@/lib/rate-limit'

// Cached ZAI instance for reuse across requests
let zaiInstance: ZAI | null = null

async function getZAI(): Promise<ZAI> {
  if (!zaiInstance) {
    zaiInstance = await ZAI.create()
  }
  return zaiInstance
}

interface RecentRun {
  date: string
  status: string
  duration: number
}

interface FailureAnalysisRequest {
  testId: string
  testName: string
  error: string
  moduleName: string
  stackTrace?: string
  recentRuns: RecentRun[]
}

export async function POST(req: NextRequest) {
  // C1: Auth check
  const user = await validateSession(req)
  if (!user) {
    return NextResponse.json({ error: 'Not authenticated' }, { status: 401 })
  }

  // C3: Rate limiting — 5 AI requests per minute per IP
  const clientIp = getClientIp(req)
  const rateCheck = checkRateLimit(clientIp, 'ai-failure-analysis', { maxRequests: 5, windowMs: 60_000 })
  if (rateCheck.limited) {
    return NextResponse.json(
      { error: 'Too many requests. Please try again later.' },
      {
        status: 429,
        headers: { 'Retry-After': String(Math.ceil((rateCheck.retryAfterMs || 60_000) / 1000)) }
      }
    )
  }

  try {
    const body: FailureAnalysisRequest = await req.json()
    const { testId, testName, error, moduleName, stackTrace, recentRuns } = body

    // Validate required fields
    if (!testId || !testName || !error || !moduleName) {
      return NextResponse.json(
        { error: 'Missing required fields: testId, testName, error, moduleName' },
        { status: 400 }
      )
    }

    const zai = await getZAI()

    const systemPrompt =
      'You are a senior QA engineer performing root cause analysis on test failures. Provide detailed analysis with actionable recommendations. Always respond with valid JSON only.'

    // Format stack trace section
    const stackTraceSection = stackTrace
      ? `Stack trace: ${stackTrace}`
      : 'Stack trace: Not provided'

    // Format recent run history
    const recentRunsSummary =
      recentRuns && Array.isArray(recentRuns) && recentRuns.length > 0
        ? recentRuns
            .map((r) => `${r.date}: ${r.status} (duration: ${r.duration}ms)`)
            .join('\n')
        : 'No recent run history available'

    const userPrompt = `Analyze this failure:
Test: ${testId} - ${testName}
Module: ${moduleName}
Error: ${error}
${stackTraceSection}
Recent run history:
${recentRunsSummary}

Respond with JSON: { rootCause: string, likelyCause: string, fixSuggestion: string, preventionTip: string, relatedTests: string[], severityAssessment: string, timeToFixEstimate: string }`

    const completion = await zai.chat.completions.create({
      messages: [
        { role: 'assistant', content: systemPrompt },
        { role: 'user', content: userPrompt },
      ],
      thinking: { type: 'disabled' },
    })

    const responseText = completion.choices[0]?.message?.content

    if (!responseText) {
      return NextResponse.json(
        { error: 'AI returned an empty response' },
        { status: 502 }
      )
    }

    // Parse JSON from AI response with fallback
    let analysis: Record<string, unknown>
    try {
      const jsonMatch = responseText.match(/```(?:json)?\s*([\s\S]*?)```/)
      const jsonStr = jsonMatch ? jsonMatch[1].trim() : responseText.trim()
      analysis = JSON.parse(jsonStr)
    } catch {
      console.error('[FailureAnalysis] Failed to parse AI response as JSON:', responseText)
      analysis = {
        rootCause: responseText,
        likelyCause: 'Unable to determine automatically',
        fixSuggestion: 'Manual investigation required',
        preventionTip: 'Add more monitoring and logging',
        relatedTests: [],
        severityAssessment: 'medium',
        timeToFixEstimate: 'Unknown',
      }
    }

    return NextResponse.json({ success: true, analysis })
  } catch (error) {
    console.error('[FailureAnalysis] POST error:', error)
    return NextResponse.json(
      { error: 'Failed to analyze test failure' },
      { status: 500 }
    )
  }
}
