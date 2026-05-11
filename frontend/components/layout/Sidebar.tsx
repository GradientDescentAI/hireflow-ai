"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

interface NavItem {
  label: string;
  href: string;
  icon: string;
  adminOnly?: boolean;
}

const NAV_ITEMS: NavItem[] = [
  { label: "Dashboard", href: "/", icon: "dashboard" },
  { label: "Jobs", href: "/jobs", icon: "work" },
  { label: "Analytics", href: "/analytics", icon: "bar_chart" },
];

const BOTTOM_NAV: NavItem[] = [
  { label: "Persona Health", href: "/settings/personas", icon: "manage_accounts", adminOnly: true },
];

interface SidebarProps {
  personaStatus?: "green" | "yellow" | "red";
  userName?: string;
  userEmail?: string;
  isAdmin?: boolean;
}

export function Sidebar({ personaStatus = "green", userName = "Recruiter", userEmail = "", isAdmin }: SidebarProps) {
  const pathname = usePathname();

  const statusDot = {
    green: "bg-success",
    yellow: "bg-warning",
    red: "bg-danger",
  }[personaStatus];

  const statusLabel = {
    green: "Riya: Healthy",
    yellow: "Riya: Warning",
    red: "Riya: Action Needed",
  }[personaStatus];

  return (
    <aside className="fixed left-0 top-0 flex h-screen w-sidebar-width flex-col border-r border-outline-variant bg-surface-container-lowest">
      {/* Logo */}
      <div className="flex h-16 items-center gap-2 px-4 border-b border-outline-variant">
        <span className="material-symbols-outlined text-primary text-2xl">psychology</span>
        <div>
          <p className="text-label-md font-semibold text-on-surface leading-none">HireFlow AI</p>
          <p className="text-label-xs text-on-surface-variant">Riya</p>
        </div>
      </div>

      {/* Persona status pill */}
      <div className="px-4 py-3 border-b border-outline-variant">
        <div className="flex items-center gap-2 rounded-lg bg-surface-container px-3 py-2">
          <span className={cn("h-2 w-2 rounded-full", statusDot, personaStatus === "green" && "animate-pulse")} />
          <span className="text-label-xs text-on-surface-variant">{statusLabel}</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
        {NAV_ITEMS.map((item) => {
          const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-body-sm transition-colors",
                active
                  ? "bg-primary/10 text-primary font-medium"
                  : "text-on-surface-variant hover:bg-surface-container hover:text-on-surface"
              )}
            >
              <span className="material-symbols-outlined text-[20px]">{item.icon}</span>
              {item.label}
            </Link>
          );
        })}

        {/* Admin section */}
        {isAdmin && (
          <>
            <div className="pt-3 pb-1">
              <p className="px-3 text-label-xs font-medium text-on-surface-variant uppercase tracking-wider">Admin</p>
            </div>
            {BOTTOM_NAV.map((item) => {
              const active = pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2 text-body-sm transition-colors",
                    active
                      ? "bg-primary/10 text-primary font-medium"
                      : "text-on-surface-variant hover:bg-surface-container hover:text-on-surface"
                  )}
                >
                  <span className="material-symbols-outlined text-[20px]">{item.icon}</span>
                  {item.label}
                </Link>
              );
            })}
          </>
        )}
      </nav>

      {/* User profile */}
      <div className="border-t border-outline-variant px-4 py-3">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-primary text-label-md font-semibold">
            {userName.charAt(0).toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-label-xs font-medium text-on-surface truncate">{userName}</p>
            <p className="text-label-xs text-on-surface-variant truncate">{userEmail}</p>
          </div>
          <Link href="/login" className="text-on-surface-variant hover:text-on-surface">
            <span className="material-symbols-outlined text-[18px]">logout</span>
          </Link>
        </div>
      </div>
    </aside>
  );
}
