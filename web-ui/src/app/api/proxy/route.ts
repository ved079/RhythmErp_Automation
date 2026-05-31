import { NextRequest, NextResponse } from "next/server";
import { validateSession } from "@/lib/session";

const API_BASE = process.env.API_PROXY_URL || "http://127.0.0.1:8000";

// C4: No hardcoded fallback — must be set via environment variable
const PROXY_API_KEY = process.env.PROXY_API_KEY || ""
// C4: Warn if PROXY_API_KEY is not set — required for production
if (!process.env.PROXY_API_KEY && process.env.NODE_ENV === 'production') {
  console.error('[SECURITY] PROXY_API_KEY is not set! Proxy authentication is disabled.')
}

// ─── Backend health cache ────────────────────────────────
// Avoid hammering the Python backend when it's down.
let backendAlive = true;
let backendCheckedAt = 0;
const BACKEND_CHECK_TTL = 30_000; // 30 seconds

async function isBackendRunning(): Promise<boolean> {
  if (Date.now() - backendCheckedAt < BACKEND_CHECK_TTL) {
    return backendAlive;
  }

  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 3000);
    const res = await fetch(`${API_BASE}/api/health`, {
      signal: controller.signal,
      cache: "no-store",
    });
    clearTimeout(timeout);
    backendAlive = res.ok;
  } catch {
    backendAlive = false;
  }
  backendCheckedAt = Date.now();
  return backendAlive;
}

async function proxyRequest(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const path = searchParams.get("path") || "";
  if (!path) {
    return NextResponse.json({ error: "Missing ?path= parameter" }, { status: 400 });
  }

  const targetUrl = `${API_BASE}/api/${path}`;

  // Validate user session for all requests except health
  const isHealthCheck = path === "health";
  const user = isHealthCheck ? null : await validateSession(req);

  if (!isHealthCheck && !user) {
    return NextResponse.json({ error: "Not authenticated" }, { status: 401 });
  }

  // Quick-reject if backend is down (skip for SSE streams)
  const isStreamPath = path.startsWith("runs/start");
  if (!isHealthCheck && !isStreamPath) {
    const alive = await isBackendRunning();
    if (!alive) {
      return NextResponse.json(
        {
          error: "Automation engine is not running",
          detail: "The FastAPI backend is not reachable. Please start it and try again.",
          targetUrl,
        },
        { status: 502 }
      );
    }
  }

  try {
    const headers: Record<string, string> = {};

    const contentType = req.headers.get("content-type");
    if (contentType) headers["Content-Type"] = contentType;

    headers["X-Proxy-API-Key"] = PROXY_API_KEY;

    if (user) {
      headers["X-User-Id"] = user.id;
      headers["X-User-Email"] = user.email;
      headers["X-User-Role"] = user.role;
    }

    const body = req.method !== "GET" && req.method !== "HEAD" ? await req.text() : undefined;

    // Shorter timeout for regular calls (10s), long for streams (10min)
    const isStreamRequest = isStreamPath || path.startsWith("screenshot");
    const timeoutMs = isStreamRequest ? 600_000 : 10_000;

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), timeoutMs);

    const res = await fetch(targetUrl, {
      method: req.method,
      headers,
      body,
      signal: controller.signal,
      cache: "no-store",
    });
    clearTimeout(timeout);

    const ct = res.headers.get("content-type") || "";
    if (ct.includes("text/event-stream")) {
      return new NextResponse(res.body, {
        status: res.status,
        headers: {
          "Content-Type": "text/event-stream",
          "Cache-Control": "no-cache",
          Connection: "keep-alive",
        },
      });
    }

    // Backend responded — mark as alive
    backendAlive = true;
    backendCheckedAt = Date.now();

    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (err: unknown) {
    let message = "Unknown error";
    if (err instanceof Error) {
      message = err.message;
      if (err.name === "AbortError") {
        message = isStreamPath ? "Request timed out (10 min limit)" : "Request timed out (10s limit)";
      } else if ("cause" in err && err.cause) {
        message += ` | cause: ${JSON.stringify(err.cause)}`;
      }
    }
    console.error(`[Proxy] Failed to fetch ${targetUrl}:`, message);

    const isConnectionRefused = message.includes("ECONNREFUSED") || message.includes("fetch failed");
    if (isConnectionRefused) {
      backendAlive = false;
      backendCheckedAt = Date.now();
      return NextResponse.json(
        {
          error: "Automation engine is not running",
          detail: "The FastAPI backend is not reachable. Please start it and try again.",
          targetUrl,
        },
        { status: 502 }
      );
    }

    return NextResponse.json(
      { error: message, targetUrl },
      { status: 502 }
    );
  }
}

export async function GET(req: NextRequest) {
  return proxyRequest(req);
}

export async function POST(req: NextRequest) {
  return proxyRequest(req);
}

export async function PUT(req: NextRequest) {
  return proxyRequest(req);
}

export async function DELETE(req: NextRequest) {
  return proxyRequest(req);
}