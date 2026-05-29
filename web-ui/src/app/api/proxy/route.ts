import { NextRequest, NextResponse } from "next/server";
import { validateSession } from "@/lib/session";

const API_BASE = process.env.API_PROXY_URL || "http://127.0.0.1:8000";

// Shared secret for proxy-to-FastAPI communication
const PROXY_API_KEY = process.env.PROXY_API_KEY || "rhythmerp-proxy-key-change-in-production";

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

  try {
    const headers: Record<string, string> = {};

    // Forward content type
    const contentType = req.headers.get("content-type");
    if (contentType) headers["Content-Type"] = contentType;

    // Send proxy API key for FastAPI to verify this is a trusted proxy request
    headers["X-Proxy-API-Key"] = PROXY_API_KEY;

    // Send user info headers so FastAPI can log who made the request
    if (user) {
      headers["X-User-Id"] = user.id;
      headers["X-User-Email"] = user.email;
      headers["X-User-Role"] = user.role;
    }

    const body = req.method !== "GET" && req.method !== "HEAD" ? await req.text() : undefined;

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 600000); // 10 min timeout for long test runs

    const res = await fetch(targetUrl, {
      method: req.method,
      headers,
      body,
      signal: controller.signal,
      cache: "no-store",
    });
    clearTimeout(timeout);

    // If SSE stream, forward it directly
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

    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (err: unknown) {
    let message = "Unknown error";
    if (err instanceof Error) {
      message = err.message;
      if (err.name === "AbortError") {
        message = "Request timed out (10 min limit)";
      } else if ("cause" in err && err.cause) {
        message += ` | cause: ${JSON.stringify(err.cause)}`;
      }
    }
    console.error(`[Proxy] Failed to fetch ${targetUrl}:`, message);

    // Provide a helpful error for when FastAPI is not running
    const isConnectionRefused = message.includes("ECONNREFUSED") || message.includes("fetch failed");
    if (isConnectionRefused) {
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
