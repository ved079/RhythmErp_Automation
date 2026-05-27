import { NextRequest, NextResponse } from "next/server";
import { db } from "@/lib/db";

const API_BASE = process.env.API_PROXY_URL || "http://127.0.0.1:8000";

// Shared secret for proxy-to-FastAPI communication
const PROXY_API_KEY = process.env.PROXY_API_KEY || "rhythmerp-proxy-key-change-in-production";

/**
 * Validate the session cookie from the incoming request.
 * Returns the user object if valid, null otherwise.
 */
async function validateSession(req: NextRequest): Promise<{ id: string; email: string; name: string; role: string } | null> {
  const token = req.cookies.get("session_token")?.value;
  if (!token) return null;

  try {
    const session = await db.session.findUnique({
      where: { token },
      include: { user: true },
    });

    if (!session || !session.user || session.expiresAt < new Date()) {
      return null;
    }

    return {
      id: session.user.id,
      email: session.user.email,
      name: session.user.name,
      role: session.user.role,
    };
  } catch {
    return null;
  }
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
      if ("cause" in err && err.cause) {
        message += ` | cause: ${JSON.stringify(err.cause)}`;
      }
    }
    console.error(`[Proxy] Failed to fetch ${targetUrl}:`, message);
    return NextResponse.json(
      { error: message, targetUrl, hint: "Is FastAPI running on 127.0.0.1:8000?" },
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
