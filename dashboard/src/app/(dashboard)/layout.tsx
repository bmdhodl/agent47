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
    <div className="flex h-screen">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="flex h-14 items-center justify-end border-b px-6">
          <UserNav email={user.email ?? ""} />
        </header>
        <main className="flex-1 overflow-y-auto p-6">{children}</main>
      </div>
    </div>
  );
}
