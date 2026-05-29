import { NextRequest, NextResponse } from 'next/server'
import ZAI from 'z-ai-web-dev-sdk'

// Cached ZAI instance for reuse across requests
let zaiInstance: ZAI | null = null

async function getZAI(): Promise<ZAI> {
  if (!zaiInstance) {
    zaiInstance = await ZAI.create()
  }
  return zaiInstance
}

interface FailedTest {
  id: string
  name: string
  error: string
  module: string
}

interface ModuleHistory {
  moduleId: string
  passRate: number
  recentTrend: string
}

interface TestSuggestionsRequest {
  failedTests: FailedTest[]
  moduleHistory: ModuleHistory[]
}

export async function POST(req: NextRequest) {
  try {
    const body: TestSuggestionsRequest = await req.json()
    const { failedTests, moduleHistory } = body

    // Validate required fields
    if (!failedTests || !Array.isArray(failedTests) || failedTests.length === 0) {
      return NextResponse.json(
        { error: 'Missing required field: failedTests (non-empty array)' },
        { status: 400 }
      )
    }

    if (!moduleHistory || !Array.isArray(moduleHistory)) {
      return NextResponse.json(
        { error: 'Missing required field: moduleHistory (array)' },
        { status: 400 }
      )
    }

    const zai = await getZAI()

    const systemPrompt =
      'You are a QA test strategist. Based on failure patterns, suggest additional tests and areas to investigate. Always respond with valid JSON only.'

    // Format failed tests summary
    const failedTestsSummary = failedTests
      .map((t) => `- ${t.id}: ${t.name} (Module: ${t.module}) — Error: ${t.error}`)
      .join('\n')

    // Format module history summary
    const moduleHistorySummary = moduleHistory
      .map((m) => `- ${m.moduleId}: Pass rate ${m.passRate}%, Trend: ${m.recentTrend}`)
      .join('\n')

    const userPrompt = `Recent failures:
${failedTestsSummary}

Module history:
${moduleHistorySummary}

Respond with JSON: { suggestedTests: Array<{name: string, reason: string, priority: string, module: string}>, riskAreas: Array<{area: string, reason: string, severity: string}>, overallAssessment: string }`

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
    let suggestions: Record<string, unknown>
    try {
      const jsonMatch = responseText.match(/```(?:json)?\s*([\s\S]*?)```/)
      const jsonStr = jsonMatch ? jsonMatch[1].trim() : responseText.trim()
      suggestions = JSON.parse(jsonStr)
    } catch {
      console.error('[TestSuggestions] Failed to parse AI response as JSON:', responseText)
      suggestions = {
        suggestedTests: [],
        riskAreas: [],
        overallAssessment: responseText,
      }
    }

    return NextResponse.json({ success: true, suggestions })
  } catch (error) {
    console.error('[TestSuggestions] POST error:', error)
    return NextResponse.json(
      { error: 'Failed to generate test suggestions' },
      { status: 500 }
    )
  }
}
