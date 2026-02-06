"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Activity, Bell, BarChart3, Settings, type LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

const navItems: { href: string; label: string; icon: LucideIcon }[] = [
  { href: "/traces", label: "Traces", icon: Activity },
  { href: "/alerts", label: "Alerts", icon: Bell },
  { href: "/usage", label: "Usage", icon: BarChart3 },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex h-screen w-56 flex-col border-r bg-card">
      <div className="flex h-14 items-center border-b px-4">
        <Link href="/traces" className="font-semibold tracking-tight">
          AgentGuard
        </Link>
      </div>
      <nav className="flex-1 space-y-1 p-2">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors",
              pathname.startsWith(item.href)
                ? "bg-accent text-accent-foreground"
                : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
            )}
          >
            <item.icon className="h-4 w-4 opacity-50" />
            {item.label}
          </Link>
        ))}
      </nav>
      <div className="border-t p-2 text-xs text-muted-foreground px-4 py-3">
        agentguard47 v0.3.0
      </div>
    </aside>
  );
}
