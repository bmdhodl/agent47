import { NextResponse } from "next/server";
import { hash } from "bcryptjs";
import { randomUUID } from "crypto";
import sql from "@/lib/db";
import { rateLimit, getClientIp } from "@/lib/rate-limit";

export async function POST(request: Request) {
  // Rate limit: 5 signups per hour per IP
  const ip = getClientIp(request);
  const rl = rateLimit(`signup:${ip}`, 5, 3600_000);
  if (!rl.ok) {
    return NextResponse.json({ error: "Too many requests" }, { status: 429 });
  }

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
