import type { APIRoute } from "astro";

export const prerender = false;

const GATEWAY_URL = process.env.GATEWAY_URL ?? "http://localhost:8080";

// Forward /api/* to the Python gateway so the browser never talks gRPC or CORS.
export const ALL: APIRoute = async ({ request, params }) => {
  try {
    const upstream = await fetch(`${GATEWAY_URL}/api/${params.path}`, {
      method: request.method,
      headers: { "Content-Type": "application/json" },
      body: request.method === "GET" ? undefined : await request.text(),
    });
    return new Response(await upstream.text(), {
      status: upstream.status,
      headers: { "Content-Type": "application/json" },
    });
  } catch {
    return Response.json({ success: false, error: "gateway unreachable" }, { status: 502 });
  }
};
