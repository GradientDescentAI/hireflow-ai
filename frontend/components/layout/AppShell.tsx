"use client";

import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";
import { getSession } from "@/lib/auth";
import { useEffect, useState } from "react";
import type { Session } from "@/lib/auth";

interface AppShellProps {
  children: React.ReactNode;
  breadcrumbs?: Array<{ label: string; href?: string }>;
  showNewJob?: boolean;
}

export function AppShell({ children, breadcrumbs, showNewJob }: AppShellProps) {
  const [session, setSession] = useState<Session | null>(null);

  useEffect(() => {
    setSession(getSession());
  }, []);

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar
        userName={session?.name ?? "Recruiter"}
        userEmail={session?.email ?? ""}
        isAdmin={session?.role === "admin" || session?.role === "super_admin"}
      />
      <div className="ml-sidebar-width flex flex-1 flex-col">
        <Topbar breadcrumbs={breadcrumbs} showNewJob={showNewJob} />
        <main className="flex-1 p-6">{children}</main>
      </div>
    </div>
  );
}
