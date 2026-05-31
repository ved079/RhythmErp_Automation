import { NextRequest, NextResponse } from 'next/server'
import ZAI from 'z-ai-web-dev-sdk'
import { validateSession } from '@/lib/session'

// Cached ZAI instance for reuse across requests
let zaiInstance: ZAI | null = null

async function getZAI(): Promise<ZAI> {
  if (!zaiInstance) {
    zaiInstance = await ZAI.create()
  }
  return zaiInstance
}

interface BugTriageRequest {
  testId: string
  testDescription: string
  error: string
  moduleName: string
  userName: string
}

export async function POST(req: NextRequest) {
  // C1: Auth check
  const user = await validateSession(req)
  if (!user) {
    return NextResponse.json({ error: 'Not authenticated' }, { status: 401 })
  }

  try {
    const body: BugTriageRequest = await req.json()
    const { testId, testDescription, error, moduleName, userName } = body

    // Validate required fields
    if (!testId || !testDescription || !error || !moduleName) {
      return NextResponse.json(
        { error: 'Missing required fields: testId, testDescription, error, moduleName' },
        { status: 400 }
      )
    }

    const zai = await getZAI()

    const systemPrompt =
      'You are a QA expert analyzing bug reports for RhythmERP automation. Classify the bug and provide actionable insights. Always respond with valid JSON only.'

    const userPrompt = `Analyze this bug:
Test: ${testId}
Description: ${testDescription}
Error: ${error}
Module: ${moduleName}

Respond with JSON: { priority: 'low'|'medium'|'high'|'critical', category: string, suggestedAssignee: string, rootCauseHypothesis: string, severity: string, impactAssessment: string, recommendedAction: string }`

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
      // Try to extract JSON from the response (handle markdown code blocks)
      const jsonMatch = responseText.match(/```(?:json)?\s*([\s\S]*?)```/)
      const jsonStr = jsonMatch ? jsonMatch[1].trim() : responseText.trim()
      analysis = JSON.parse(jsonStr)
    } catch {
      console.error('[BugTriage] Failed to parse AI response as JSON:', responseText)
      analysis = {
        priority: 'medium',
        category: 'unknown',
        suggestedAssignee: userName || 'Unassigned',
        rootCauseHypothesis: responseText,
        severity: 'medium',
        impactAssessment: 'Unable to assess automatically',
        recommendedAction: 'Manual review required',
      }
    }

    return NextResponse.json({ success: true, analysis })
  } catch (error) {
    console.error('[BugTriage] POST error:', error)
    return NextResponse.json(
      { error: 'Failed to analyze bug report' },
      { status: 500 }
    )
  }
}
