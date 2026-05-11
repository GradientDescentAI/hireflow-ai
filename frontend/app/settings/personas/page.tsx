"use client";

import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { personasApi } from "@/lib/api";
import type { PersonaAccount } from "@/lib/types";

const MOCK_PERSONAS: PersonaAccount[] = [
  {
    id: "p1",
    name: "Riya - North India",
    handle: "@riya_recruits",
    status: "healthy",
    posts_today: 42,
    posts_limit: 50,
    last_post_at: new Date(Date.now() - 900000).toISOString(),
    linkedin_status: "connected",
    whatsapp_status: "active",
    api_status: "stable",
  },
  {
    id: "p2",
    name: "Anjali - South India",
    handle: "@anjali_south",
    status: "warning",
    posts_today: 48,
    posts_limit: 50,
    last_post_at: new Date(Date.now() - 1800000).toISOString(),
    linkedin_status: "rate_limited",
    whatsapp_status: "active",
    api_status: "stable",
  },
];

const MOCK_EVENTS = [
  {
    id: "e1",
    color: "bg-warning",
    time: "10:42 AM Today",
    title: "LinkedIn Rate Limit Warning",
    desc: "Persona @anjali_south has reached 96% of daily connection request limits. Recommend throttling.",
  },
  {
    id: "e2",
    color: "bg-primary",
    time: "08:15 AM Today",
    title: "Routine Rotation Completed",
    desc: "Credentials successfully rotated for @riya_recruits. Systems nominal.",
  },
  {
    id: "e3",
    color: "bg-danger",
    time: "Yesterday, 4:30 PM",
    title: "WhatsApp Session Disconnect",
    desc: "Temporary drop in WhatsApp API connectivity for @vikram_west. Auto-recovered after 5 mins.",
  },
];

const MOCK_KPIS = [
  { label: "Active Personas", value: "12" },
  { label: "Total Posts Today", value: "342" },
  { label: "Avg Health Score", value: "94%", valueColor: "text-success" },
  { label: "Pending Failovers", value: "1", valueColor: "text-warning" },
];

function StatusDot({ status }: { status: string }) {
  if (status === "connected" || status === "active" || status === "stable")
    return <span className="text-success font-medium">{status.charAt(0).toUpperCase() + status.slice(1)}</span>;
  if (status === "rate_limited")
    return (
      <span className="text-warning font-medium flex items-center gap-1">
        <span className="material-symbols-outlined text-[14px]">error</span> Rate Limited
      </span>
    );
  return <span className="text-on-surface-variant">{status}</span>;
}

function PersonaCard({ persona }: { persona: PersonaAccount }) {
  const isWarning = persona.status === "warning";
  const postPct = Math.round((persona.posts_today / persona.posts_limit) * 100);

  return (
    <div className={`bg-surface-container-lowest border rounded-xl p-6 shadow-sm flex flex-col gap-6 ${
      isWarning ? "border-warning/30 ring-1 ring-warning/20" : "border-outline-variant"
    }`}>
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex gap-4 items-center">
          <div className={`w-16 h-16 rounded-full flex items-center justify-center text-2xl font-bold border-2 border-surface-container-lowest shadow-sm ${
            isWarning ? "bg-warning/10 text-warning" : "bg-primary/10 text-primary"
          }`}>
            {persona.name.charAt(0)}
          </div>
          <div>
            <h4 className="text-on-surface text-lg font-bold">{persona.name}</h4>
            <p className="text-on-surface-variant text-body-sm">{persona.handle}</p>
          </div>
        </div>
        {isWarning ? (
          <div className="bg-warning/10 text-warning px-3 py-1 rounded-full text-label-xs flex items-center gap-1 border border-warning/20">
            <span className="material-symbols-outlined text-[14px]">warning</span>
            Action Required
          </div>
        ) : (
          <div className="bg-success/10 text-success px-3 py-1 rounded-full text-label-xs flex items-center gap-1 border border-success/20">
            <span className="material-symbols-outlined text-[14px]">check_circle</span>
            Healthy
          </div>
        )}
      </div>

      {/* Metrics */}
      <div className={`grid grid-cols-1 md:grid-cols-2 gap-6 p-4 rounded-lg border ${
        isWarning ? "bg-warning/5 border-warning/20" : "bg-surface-container-low border-outline-variant"
      }`}>
        {/* Engagement */}
        <div className="flex flex-col gap-3">
          <p className="text-label-xs text-on-surface-variant uppercase tracking-wider">Engagement Metrics</p>
          <div>
            <div className="flex justify-between text-body-sm mb-1">
              <span className="text-on-surface">Posts Today</span>
              <span className="text-on-surface font-medium">{persona.posts_today} / {persona.posts_limit}</span>
            </div>
            <div className="w-full bg-outline-variant rounded-full h-1.5">
              <div
                className={`h-1.5 rounded-full ${isWarning ? "bg-warning" : "bg-primary"}`}
                style={{ width: `${postPct}%` }}
              />
            </div>
          </div>
          <p className={`text-label-xs ${isWarning ? "text-warning" : "text-on-surface-variant"}`}>
            {isWarning ? "Approaching rate limit" : `Last post: ~15 mins ago`}
          </p>
        </div>

        {/* System status */}
        <div className="flex flex-col gap-2">
          <p className="text-label-xs text-on-surface-variant uppercase tracking-wider">System Status</p>
          <ul className="flex flex-col gap-2 text-body-sm">
            <li className="flex items-center justify-between">
              <span className="flex items-center gap-2 text-on-surface">
                <span className="material-symbols-outlined text-[16px] text-on-surface-variant">work</span> LinkedIn
              </span>
              <StatusDot status={persona.linkedin_status} />
            </li>
            <li className="flex items-center justify-between">
              <span className="flex items-center gap-2 text-on-surface">
                <span className="material-symbols-outlined text-[16px] text-on-surface-variant">chat</span> WhatsApp
              </span>
              <StatusDot status={persona.whatsapp_status} />
            </li>
            {persona.api_status && (
              <li className="flex items-center justify-between">
                <span className="flex items-center gap-2 text-on-surface">
                  <span className="material-symbols-outlined text-[16px] text-on-surface-variant">api</span> API Connectivity
                </span>
                <StatusDot status={persona.api_status} />
              </li>
            )}
          </ul>
        </div>
      </div>

      {/* Actions */}
      <div className="flex flex-wrap gap-3 pt-2 border-t border-outline-variant">
        <Button size="sm">Run Health Check</Button>
        <Button variant="outline" size="sm">
          {isWarning ? "Acknowledge Alert" : "Rotate Credentials"}
        </Button>
        <Button variant="danger" size="sm" className="ml-auto">
          Initiate Failover
        </Button>
      </div>
    </div>
  );
}

export default function PersonasPage() {
  const { data: personas } = useQuery({
    queryKey: ["personas"],
    queryFn: () => personasApi.health().then((r) => r.data as PersonaAccount[]),
    placeholderData: MOCK_PERSONAS,
    refetchInterval: 30000,
  });

  const list = personas ?? MOCK_PERSONAS;

  return (
    <AppShell breadcrumbs={[{ label: "Dashboard", href: "/" }, { label: "Settings" }, { label: "Persona Health" }]}>
      {/* Header */}
      <div className="flex flex-wrap justify-between items-end gap-4 border-b border-outline-variant pb-6 mb-8">
        <div className="flex flex-col gap-1">
          <h1 className="text-headline-lg text-on-surface">Persona Health</h1>
          <div className="flex items-center gap-2">
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-success opacity-75" />
              <span className="relative inline-flex rounded-full h-3 w-3 bg-success" />
            </span>
            <p className="text-on-surface-variant text-body-sm font-medium">System Status: Online</p>
          </div>
        </div>
        <Button variant="outline" size="sm">
          <span className="material-symbols-outlined text-[18px]">refresh</span>
          Refresh Data
        </Button>
      </div>

      {/* KPI Summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {MOCK_KPIS.map((kpi) => (
          <div key={kpi.label} className="card flex flex-col gap-2">
            <p className="text-on-surface-variant text-body-sm font-medium">{kpi.label}</p>
            <p className={`text-3xl font-bold ${kpi.valueColor ?? "text-on-surface"}`}>{kpi.value}</p>
          </div>
        ))}
      </div>

      {/* Main grid */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-8">
        {/* Persona cards */}
        <div className="xl:col-span-8 flex flex-col gap-6">
          <h3 className="text-headline-md font-semibold text-on-surface">Persona Accounts</h3>
          {list.map((p) => <PersonaCard key={p.id} persona={p} />)}
        </div>

        {/* Health events timeline */}
        <div className="xl:col-span-4">
          <div className="card sticky top-20">
            <div className="flex items-center gap-2 mb-6 border-b border-outline-variant pb-4">
              <span className="material-symbols-outlined text-on-surface-variant">history</span>
              <h3 className="text-headline-md font-semibold text-on-surface">Recent Health Events</h3>
            </div>
            <div className="relative border-l-2 border-outline-variant ml-3 space-y-6">
              {MOCK_EVENTS.map((evt) => (
                <div key={evt.id} className="relative pl-6">
                  <div className={`absolute -left-[9px] top-1 h-4 w-4 rounded-full border-2 border-surface-container-lowest ${evt.color}`} />
                  <p className="text-label-xs text-on-surface-variant mb-1">{evt.time}</p>
                  <p className="text-body-sm text-on-surface font-medium">{evt.title}</p>
                  <p className="text-label-xs text-on-surface-variant mt-1">{evt.desc}</p>
                </div>
              ))}
            </div>
            <button className="w-full mt-8 border border-outline-variant text-on-surface-variant py-2 rounded-lg text-label-xs font-medium hover:bg-surface-container transition-colors">
              View Full Logs
            </button>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
