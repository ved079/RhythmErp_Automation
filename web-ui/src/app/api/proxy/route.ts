import { NextRequest, NextResponse } from "next/server";

const API_BASE = process.env.API_PROXY_URL || "http://127.0.0.1:8000";

async function proxyRequest(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const path = searchParams.get("path") || "";
  if (!path) {
    return NextResponse.json({ error: "Missing ?path= parameter" }, { status: 400 });
  }

  const targetUrl = `${API_BASE}/api/${path}`;
  console.log(`[Proxy] ${req.method} ${targetUrl}`);

  try {
    const headers: Record<string, string> = {};
    const contentType = req.headers.get("content-type");
    if (contentType) headers["Content-Type"] = contentType;

    const body = req.method !== "GET" ? await req.text() : undefined;

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000);

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