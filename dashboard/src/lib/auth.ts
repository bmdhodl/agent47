import { redirect } from "next/navigation";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/next-auth";
import sql from "@/lib/db";

export async function getSessionOrRedirect() {
  const session = await getServerSession(authOptions);

  if (!session?.user) {
    redirect("/login");
  }

  return session.user as { id: string; email: string };
}

export async function getTeamForUser(userId: string) {
  const rows = await sql`
    SELECT * FROM teams WHERE owner_id = ${userId}
  `;

  if (rows.length === 0) {
    throw new Error("Team not found");
  }

  return rows[0];
}
