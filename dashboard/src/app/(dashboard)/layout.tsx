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
        <main className="flex-1 overflow-y-auto p-4 pb-20 md:p-6 md:pb-6">{children}</main>
      </div>
    </div>
  );
}
