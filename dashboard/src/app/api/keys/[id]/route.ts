import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/next-auth";
import sql from "@/lib/db";

export async function DELETE(
  _request: Request,
  { params }: { params: { id: string } },
) {
  const session = await getServerSession(authOptions);
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const userId = (session.user as { id: string }).id;

  // Verify user owns the key's team
  const keys = await sql`
    SELECT ak.id FROM api_keys ak
    JOIN teams t ON t.id = ak.team_id
    WHERE ak.id = ${params.id} AND t.owner_id = ${userId}
  `;

  if (keys.length === 0) {
    return NextResponse.json({ error: "Not found" }, { status: 404 });
  }

  await sql`
    UPDATE api_keys SET revoked_at = NOW()
    WHERE id = ${params.id}
  `;

  return NextResponse.json({ ok: true });
}
