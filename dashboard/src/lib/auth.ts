import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";

export async function getSessionOrRedirect() {
  const supabase = createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  return user;
}

export async function getTeamForUser(userId: string) {
  const supabase = createClient();
  const { data, error } = await supabase
    .from("teams")
    .select("*")
    .eq("owner_id", userId)
    .single();

  if (error || !data) {
    throw new Error("Team not found");
  }

  return data;
}
