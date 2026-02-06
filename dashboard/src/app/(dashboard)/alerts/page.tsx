import { getSessionOrRedirect, getTeamForUser } from "@/lib/auth";
import { getAlerts } from "@/lib/queries";
import { Badge } from "@/components/ui/badge";

export default async function AlertsPage() {
  const user = await getSessionOrRedirect();
  const team = await getTeamForUser(user.id);
  const alerts = await getAlerts(team.id);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold tracking-tight">Alerts</h1>
      {alerts.length === 0 ? (
        <div className="rounded-md border p-12 text-center">
          <p className="text-muted-foreground">No alerts.</p>
          <p className="mt-2 text-sm text-muted-foreground">
            Loop detections, budget overruns, and errors will appear here.
          </p>
        </div>
      ) : (
        <div className="rounded-md border divide-y">
          {alerts.map((alert) => (
            <div key={alert.id} className="flex items-center gap-4 px-4 py-3">
              <div
                className={`h-2 w-2 rounded-full ${
                  alert.error ? "bg-red-400" : "bg-yellow-400"
                }`}
              />
              <div className="flex-1 min-w-0">
                <div className="font-mono text-sm">{alert.name}</div>
                {alert.error && (
                  <div className="text-xs text-red-400">
                    {alert.error.type}: {alert.error.message}
                  </div>
                )}
              </div>
              <Badge variant="secondary" className="text-xs">
                {alert.service}
              </Badge>
              <div className="text-xs text-muted-foreground shrink-0">
                {new Date(alert.created_at).toLocaleString()}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
