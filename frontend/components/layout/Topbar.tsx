"use client";

import Link from "next/link";
import { Button } from "@/components/ui/Button";

interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface TopbarProps {
  breadcrumbs?: BreadcrumbItem[];
  showNewJob?: boolean;
}

export function Topbar({ breadcrumbs = [], showNewJob = true }: TopbarProps) {
  return (
    <header className="sticky top-0 z-10 flex h-16 items-center justify-between border-b border-outline-variant bg-surface-container-lowest px-6">
      {/* Breadcrumbs */}
      <nav className="flex items-center gap-2 text-body-sm">
        {breadcrumbs.map((crumb, i) => (
          <span key={i} className="flex items-center gap-2">
            {i > 0 && (
              <span className="material-symbols-outlined text-[16px] text-on-surface-variant">
                chevron_right
              </span>
            )}
            {crumb.href ? (
              <Link href={crumb.href} className="text-on-surface-variant hover:text-on-surface transition-colors">
                {crumb.label}
              </Link>
            ) : (
              <span className="font-medium text-on-surface">{crumb.label}</span>
            )}
          </span>
        ))}
      </nav>

      {/* Actions */}
      <div className="flex items-center gap-3">
        <button className="relative text-on-surface-variant hover:text-on-surface">
          <span className="material-symbols-outlined text-[22px]">notifications</span>
          <span className="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full bg-danger" />
        </button>
        {showNewJob && (
          <Link href="/jobs/new">
            <Button size="sm">
              <span className="material-symbols-outlined text-[16px]">add</span>
              New Job
            </Button>
          </Link>
        )}
      </div>
    </header>
  );
}
