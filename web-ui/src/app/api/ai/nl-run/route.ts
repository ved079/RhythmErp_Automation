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

interface AvailableTest {
  id: string
  name: string
  module: string
}

interface NlRunRequest {
  command: string
  availableModules: string[]
  availableTests: AvailableTest[]
}

export async function POST(req: NextRequest) {
  try {
    const body: NlRunRequest = await req.json()
    const { command, availableModules, availableTests } = body

    // Validate required fields
    if (!command || typeof command !== 'string') {
      return NextResponse.json(
        { error: 'Missing required field: command (string)' },
        { status: 400 }
      )
    }

    if (!availableModules || !Array.isArray(availableModules)) {
      return NextResponse.json(
        { error: 'Missing required field: availableModules (array of strings)' },
        { status: 400 }
      )
    }

    if (!availableTests || !Array.isArray(availableTests)) {
      return NextResponse.json(
        { error: 'Missing required field: availableTests (array of {id, name, module})' },
        { status: 400 }
      )
    }

    const zai = await getZAI()

    const systemPrompt =
      'You are a test execution assistant for RhythmERP automation. Interpret the user\'s natural language command and determine which tests to run. Always respond with valid JSON only.'

    // Format available tests list
    const availableTestsList = availableTests
      .map((t) => `${t.id}: ${t.name} (Module: ${t.module})`)
      .join('\n')

    const userPrompt = `User says: "${command}"

Available modules: ${availableModules.join(', ')}
Available tests:
${availableTestsList}

Respond with JSON: { understood: boolean, modules: string[], testIds: string[], runType: "all"|"priority"|"selected", priority?: "smoke"|"regression"|"sanity", explanation: string }`

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
    let interpretation: Record<string, unknown>
    try {
      const jsonMatch = responseText.match(/```(?:json)?\s*([\s\S]*?)```/)
      const jsonStr = jsonMatch ? jsonMatch[1].trim() : responseText.trim()
      interpretation = JSON.parse(jsonStr)
    } catch {
      console.error('[NlRun] Failed to parse AI response as JSON:', responseText)
      interpretation = {
        understood: false,
        modules: [],
        testIds: [],
        runType: 'selected',
        explanation: responseText,
      }
    }

    return NextResponse.json({ success: true, interpretation })
  } catch (error) {
    console.error('[NlRun] POST error:', error)
    return NextResponse.json(
      { error: 'Failed to interpret natural language command' },
      { status: 500 }
    )
  }
}
