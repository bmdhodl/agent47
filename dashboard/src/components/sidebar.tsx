"use client";

import {
  useState,
  useEffect,
  createContext,
  useContext,
  type ReactNode,
} from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  Bell,
  BarChart3,
  DollarSign,
  Settings,
  HelpCircle,
  Menu,
  X,
  Shield,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems: { href: string; label: string; icon: LucideIcon }[] = [
  { href: "/traces", label: "Traces", icon: Activity },
  { href: "/alerts", label: "Alerts", icon: Bell },
  { href: "/costs", label: "Costs", icon: DollarSign },
  { href: "/usage", label: "Usage", icon: BarChart3 },
  { href: "/settings", label: "Settings", icon: Settings },
];

const secondaryItems: { href: string; label: string; icon: LucideIcon }[] = [
  { href: "/security", label: "Security", icon: Shield },
  { href: "/help", label: "Help", icon: HelpCircle },
];

const SidebarContext = createContext<{
  open: boolean;
  setOpen: (v: boolean) => void;
}>({ open: false, setOpen: () => {} });

export function SidebarProvider({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();

  // Close on route change
  useEffect(() => {
    setOpen(false);
  }, [pathname]);

  // Lock body scroll when open
  useEffect(() => {
    document.body.style.overflow = open ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  return (
    <SidebarContext.Provider value={{ open, setOpen }}>
      {children}
    </SidebarContext.Provider>
  );
}

export function MobileMenuButton() {
  const { setOpen } = useContext(SidebarContext);
  return (
    <button
      type="button"
      className="inline-flex items-center justify-center rounded-lg p-2 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground md:hidden"
      onClick={() => setOpen(true)}
      aria-label="Open menu"
    >
      <Menu className="h-5 w-5" />
    </button>
  );
}

function NavLink({
  href,
  label,
  icon: Icon,
  isActive,
}: {
  href: string;
  label: string;
  icon: LucideIcon;
  isActive: boolean;
}) {
  return (
    <Link
      href={href}
      className={cn(
        "group flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all",
        isActive
          ? "bg-[hsl(var(--sidebar-accent))] text-[hsl(var(--sidebar-accent-foreground))] shadow-sm"
          : "text-muted-foreground hover:bg-[hsl(var(--sidebar-accent))] hover:text-[hsl(var(--sidebar-accent-foreground))]",
      )}
    >
      <Icon
        className={cn(
          "h-4 w-4 shrink-0 transition-colors",
          isActive
            ? "text-foreground"
            : "text-muted-foreground/70 group-hover:text-foreground",
        )}
      />
      {label}
    </Link>
  );
}

function SidebarContent() {
  const pathname = usePathname();

  return (
    <>
      <div className="flex h-14 items-center gap-2.5 border-b border-[hsl(var(--sidebar-border))] px-4">
        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary">
          <Activity className="h-4 w-4 text-primary-foreground" />
        </div>
        <Link href="/traces" className="font-semibold tracking-tight">
          AgentGuard
        </Link>
      </div>

      <nav className="flex-1 space-y-6 overflow-y-auto p-3">
        <div className="space-y-1">
          <p className="mb-2 px-3 text-[11px] font-medium uppercase tracking-wider text-muted-foreground/70">
            Monitor
          </p>
          {navItems.map((item) => (
            <NavLink
              key={item.href}
              href={item.href}
              label={item.label}
              icon={item.icon}
              isActive={pathname.startsWith(item.href)}
            />
          ))}
        </div>

        <div className="space-y-1">
          <p className="mb-2 px-3 text-[11px] font-medium uppercase tracking-wider text-muted-foreground/70">
            Support
          </p>
          {secondaryItems.map((item) => (
            <NavLink
              key={item.href}
              href={item.href}
              label={item.label}
              icon={item.icon}
              isActive={pathname.startsWith(item.href)}
            />
          ))}
        </div>
      </nav>

      <div className="border-t border-[hsl(var(--sidebar-border))] px-4 py-3">
        <a
          href="https://github.com/bmdhodl/agent47"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 text-xs text-muted-foreground/70 transition-colors hover:text-muted-foreground"
        >
          <span className="inline-block h-1.5 w-1.5 rounded-full bg-green-500" />
          agentguard47 v0.5.0
        </a>
      </div>
    </>
  );
}

export function Sidebar() {
  const { open, setOpen } = useContext(SidebarContext);

  return (
    <>
      {/* Mobile drawer overlay */}
      {open && (
        <div
          className="fixed inset-0 z-40 bg-background/80 backdrop-blur-sm md:hidden"
          onClick={() => setOpen(false)}
        />
      )}

      {/* Mobile drawer */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex w-72 flex-col border-r bg-[hsl(var(--sidebar))] transition-sidebar md:hidden",
          open ? "translate-x-0 shadow-2xl" : "-translate-x-full",
        )}
      >
        <button
          type="button"
          className="absolute right-3 top-3.5 z-10 rounded-lg p-1.5 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
          onClick={() => setOpen(false)}
          aria-label="Close menu"
        >
          <X className="h-4 w-4" />
        </button>
        <SidebarContent />
      </aside>

      {/* Desktop sidebar */}
      <aside className="hidden md:flex h-screen w-60 shrink-0 flex-col border-r bg-[hsl(var(--sidebar))]">
        <SidebarContent />
      </aside>
    </>
  );
}
