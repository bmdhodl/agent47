import { getSessionOrRedirect } from "@/lib/auth";
import { Sidebar } from "@/components/sidebar";
import { UserNav } from "@/components/user-nav";

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const user = await getSessionOrRedirect();

  return (
    <div className="flex h-screen flex-col md:flex-row">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="flex h-14 shrink-0 items-center justify-between border-b px-4 md:justify-end md:px-6">
          <span className="font-semibold tracking-tight md:hidden">AgentGuard</span>
          <UserNav email={user.email ?? ""} />
        </header>
        <main className="flex flex-1 flex-col overflow-y-auto p-4 pb-20 md:p-6 md:pb-6">
          <div className="flex-1">{children}</div>
          <footer className="mt-auto border-t pt-3 pb-1 text-xs text-muted-foreground md:mt-12">
            <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
              <a href="/security" className="hover:underline">Security</a>
              <a href="/help" className="hover:underline">Help</a>
              <a href="https://github.com/bmdhodl/agent47" target="_blank" rel="noopener noreferrer" className="hover:underline">GitHub</a>
              <span className="ml-auto">agentguard47 v0.4.0</span>
            </div>
          </footer>
        </main>
      </div>
    </div>
  );
}
