import { NextResponse } from "next/server";
import { hash } from "bcryptjs";
import { randomUUID } from "crypto";
import sql from "@/lib/db";

export async function POST(request: Request) {
  const { email, password } = await request.json();

  if (!email || !password || password.length < 6) {
    return NextResponse.json(
      { error: "Email and password (min 6 chars) required" },
      { status: 400 },
    );
  }

  // Check if user exists
  const existing = await sql`
    SELECT id FROM users WHERE email = ${email}
  `;

  if (existing.length > 0) {
    return NextResponse.json(
      { error: "Account already exists" },
      { status: 409 },
    );
  }

  const userId = randomUUID();
  const passwordHash = await hash(password, 12);

  // Create user + team
  await sql`
    INSERT INTO users (id, email, password_hash)
    VALUES (${userId}, ${email}, ${passwordHash})
  `;

  await sql`
    INSERT INTO teams (owner_id, name)
    VALUES (${userId}, ${email.split("@")[0] + "'s team"})
  `;

  return NextResponse.json({ ok: true });
}
