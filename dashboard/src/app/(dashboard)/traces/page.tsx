import { getSessionOrRedirect, getTeamForUser } from "@/lib/auth";
import { getTraceList } from "@/lib/queries";
import { TraceTable } from "@/components/trace-table";

export default async function TracesPage() {
  const user = await getSessionOrRedirect();
  const team = await getTeamForUser(user.id);
  const traces = await getTraceList(team.id);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold tracking-tight">Traces</h1>
      <TraceTable traces={traces} />
    </div>
  );
}
