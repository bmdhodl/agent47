import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/next-auth";
import { authenticateApiKey, isAuthSuccess } from "@/lib/api-auth";
import { getTeamForUser } from "@/lib/auth";
import sql from "@/lib/db";
import { randomBytes } from "crypto";

/** Resolve team ID from either Bearer key or session cookie */
async function resolveTeamId(
  request: Request,
): Promise<{ teamId: string } | NextResponse> {
  // Try Bearer token first
  const auth = request.headers.get("authorization");
  if (auth?.startsWith("Bearer ")) {
    const result = await authenticateApiKey(request);
    if (!isAuthSuccess(result)) return result;
    return { teamId: result.teamId };
  }

  // Fall back to session auth
  const session = await getServerSession(authOptions);
  if (!session?.user) {
    return NextResponse.json(
      { error: "Authentication required" },
      { status: 401 },
    );
  }

  const user = session.user as { id: string };
  const team = await getTeamForUser(user.id);
  return { teamId: team.id as string };
}

function generateSlug(): string {
  return randomBytes(4).toString("base64url").slice(0, 6);
}

export async function POST(
  request: Request,
  { params }: { params: { traceId: string } },
) {
  const auth = await resolveTeamId(request);
  if (auth instanceof NextResponse) return auth;

  const { traceId } = params;

  // Check if already shared
  const existing = await sql`
    SELECT slug FROM shared_traces
    WHERE team_id = ${auth.teamId} AND trace_id = ${traceId}
  `;

  if (existing.length > 0) {
    const origin = new URL(request.url).origin;
    return NextResponse.json({
      slug: existing[0].slug,
      url: `${origin}/share/${existing[0].slug}`,
    });
  }

  // Check trace exists for this team
  const traceCheck = await sql`
    SELECT 1 FROM events
    WHERE team_id = ${auth.teamId} AND trace_id = ${traceId}
    LIMIT 1
  `;

  if (traceCheck.length === 0) {
    return NextResponse.json({ error: "Trace not found" }, { status: 404 });
  }

  // Parse optional expiry
  let expiresAt: string | null = null;
  try {
    const body = await request.json();
    if (body?.expires_in_days) {
      const d = new Date();
      d.setDate(d.getDate() + Number(body.expires_in_days));
      expiresAt = d.toISOString();
    }
  } catch {
    // No body or invalid JSON — that's fine, no expiry
  }

  // Retry slug generation on collision (up to 3 attempts)
  const origin = new URL(request.url).origin;
  for (let attempt = 0; attempt < 3; attempt++) {
    const slug = generateSlug();
    try {
      await sql`
        INSERT INTO shared_traces (team_id, trace_id, slug, expires_at)
        VALUES (${auth.teamId}, ${traceId}, ${slug}, ${expiresAt})
      `;
      return NextResponse.json({ slug, url: `${origin}/share/${slug}` });
    } catch (err) {
      const msg = err instanceof Error ? err.message : "";
      if (msg.includes("unique") || msg.includes("duplicate")) continue;
      throw err;
    }
  }

  return NextResponse.json(
    { error: "Failed to generate unique share link. Try again." },
    { status: 500 },
  );
}

export async function DELETE(
  request: Request,
  { params }: { params: { traceId: string } },
) {
  const auth = await resolveTeamId(request);
  if (auth instanceof NextResponse) return auth;

  await sql`
    DELETE FROM shared_traces
    WHERE team_id = ${auth.teamId} AND trace_id = ${params.traceId}
  `;

  return NextResponse.json({ ok: true });
}
