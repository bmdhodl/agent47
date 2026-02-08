import { NextResponse } from "next/server";
import sql from "@/lib/db";
import { hashApiKey } from "@/lib/api-key";
import { rateLimit, getClientIp } from "@/lib/rate-limit";

export interface ApiAuthResult {
  teamId: string;
  apiKeyId: string;
}

/**
 * Authenticate a request using a Bearer ag_ API key.
 * Returns { teamId, apiKeyId } on success or a NextResponse error.
 */
export async function authenticateApiKey(
  request: Request,
): Promise<ApiAuthResult | NextResponse> {
  // Rate limit: 60 reads per minute per IP
  const ip = getClientIp(request);
  const rl = rateLimit(`api-read:${ip}`, 60, 60_000);
  if (!rl.ok) {
    return NextResponse.json(
      { error: "Too many requests" },
      { status: 429 },
    );
  }

  // Extract Bearer token
  const auth = request.headers.get("authorization");
  if (!auth?.startsWith("Bearer ")) {
    return NextResponse.json(
      { error: "Missing or invalid Authorization header" },
      { status: 401 },
    );
  }

  const rawKey = auth.slice(7);
  const keyHash = hashApiKey(rawKey);

  // Look up API key
  const keyRows = await sql`
    SELECT id, team_id FROM api_keys
    WHERE key_hash = ${keyHash} AND revoked_at IS NULL
  `;

  if (keyRows.length === 0) {
    return NextResponse.json(
      { error: "Invalid or revoked API key" },
      { status: 401 },
    );
  }

  return {
    teamId: keyRows[0].team_id as string,
    apiKeyId: keyRows[0].id as string,
  };
}

/** Type guard: true if auth succeeded */
export function isAuthSuccess(
  result: ApiAuthResult | NextResponse,
): result is ApiAuthResult {
  return !(result instanceof NextResponse);
}
