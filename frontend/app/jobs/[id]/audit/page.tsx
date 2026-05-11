"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { jobsApi } from "@/lib/api";
import { relativeTime } from "@/lib/utils";
import type { AuditEvent } from "@/lib/types";

const MOCK_EVENTS: AuditEvent[] = [
  {
    id: "EVT-9901A",
    event_type: "posting",
    actor: "Riya AI",
    actor_type: "ai",
    description: "Post Published to LinkedIn",
    detail: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    entity: "Job Post (JP-1042)",
    created_at: new Date(Date.now() - 120000).toISOString(),
  },
  {
    id: "EVT-9900B",
    event_type: "override",
    actor: "Sarah Jenkins (Recruiter)",
    actor_type: "human",
    description: "AI Score Overridden Manually",
    detail: 'Candidate lacks specific framework experience required by the hiring manager, despite strong general JS skills noted by AI. Adjusted score from 85 to 65 to reflect immediate project needs.',
    entity: "Candidate (C-4091)",
    created_at: new Date(Date.now() - 900000).toISOString(),
  },
  {
    id: "EVT-9899C",
    event_type: "scoring",
    actor: "Riya AI",
    actor_type: "ai",
    description: "Candidate Batch Scored",
    detail: "28 candidates scored. Average composite: 71.4. 3 candidates flagged as near-miss.",
    entity: "Shortlist (SL-2026-SFD)",
    created_at: new Date(Date.now() - 3600000 * 2).toISOString(),
  },
  {
    id: "EVT-9898D",
    event_type: "disclosure",
    actor: "Riya AI",
    actor_type: "ai",
    description: "AI Disclosure Validated",
    detail: "SHA-256: a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",
    entity: "Job Post (JP-1042)",
    created_at: new Date(Date.now() - 3600000 * 4).toISOString(),
  },
  {
    id: "EVT-9897E",
    event_type: "posting",
    actor: "Sarah Jenkins (Recruiter)",
    actor_type: "human",
    description: "Job Approved for Distribution",
    detail: "Recruiter confirmed JD. Karnataka salary disclosure verified. Status: approved.",
    entity: "Job (JD-SFD-2026)",
    created_at: new Date(Date.now() - 3600000 * 6).toISOString(),
  },
];

const EVENT_FILTERS = ["All Events", "Disclosure", "Posting", "Scoring", "Override"] as const;
type EventFilter = (typeof EVENT_FILTERS)[number];

function eventTypeStyle(type: string) {
  switch (type) {
    case "posting":
      return { bg: "bg-primary/10", text: "text-primary", dot: "bg-primary/10 border-primary/20", icon: "check_circle", iconColor: "text-primary" };
    case "override":
      return { bg: "bg-warning/10", text: "text-warning", dot: "bg-warning/10 border-warning/20", icon: "edit_note", iconColor: "text-warning" };
    case "scoring":
      return { bg: "bg-accent-ai/10", text: "text-accent-ai", dot: "bg-accent-ai/10 border-accent-ai/20", icon: "auto_awesome", iconColor: "text-accent-ai" };
    case "disclosure":
      return { bg: "bg-success/10", text: "text-success", dot: "bg-success/10 border-success/20", icon: "verified_user", iconColor: "text-success" };
    default:
      return { bg: "bg-surface-container", text: "text-on-surface-variant", dot: "bg-surface-container border-outline-variant", icon: "info", iconColor: "text-on-surface-variant" };
  }
}

export default function AuditPage({ params }: { params: { id: string } }) {
  const [filter, setFilter] = useState<EventFilter>("All Events");
  const [search, setSearch] = useState("");

  const { data: events } = useQuery({
    queryKey: ["audit", params.id],
    queryFn: () => jobsApi.audit(params.id).then((r) => r.data as AuditEvent[]),
    placeholderData: MOCK_EVENTS,
  });

  const list = events ?? MOCK_EVENTS;

  const filtered = list.filter((e) => {
    const matchesFilter = filter === "All Events" || e.event_type === filter.toLowerCase();
    const matchesSearch =
      search.trim() === "" ||
      e.description.toLowerCase().includes(search.toLowerCase()) ||
      e.id.toLowerCase().includes(search.toLowerCase()) ||
      e.entity.toLowerCase().includes(search.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  return (
    <AppShell
      breadcrumbs={[
        { label: "Jobs", href: "/jobs" },
        { label: "Senior Frontend Developer", href: `/jobs/${params.id}` },
        { label: "Audit Trail" },
      ]}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-headline-lg text-on-surface">System Events Log</h1>
          <p className="text-body-sm text-on-surface-variant mt-1">
            A verifiable, chronological record of all AI agent actions, system states, and manual recruiter overrides.
          </p>
        </div>
        <Button variant="outline" size="sm">
          <span className="material-symbols-outlined text-[14px]">download</span>
          Export CSV
        </Button>
      </div>

      {/* Search + Filter bar */}
      <div className="card p-4 flex flex-col sm:flex-row gap-4 items-center justify-between mb-6">
        <div className="flex-1 w-full relative">
          <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-[18px]">search</span>
          <input
            className="w-full pl-10 pr-4 py-2 bg-surface-container-low border border-outline-variant focus:border-primary rounded-lg text-body-sm text-on-surface placeholder:text-on-surface-variant outline-none transition-colors"
            placeholder="Search events by ID, entity, or keyword..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {EVENT_FILTERS.map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1.5 rounded-md text-label-xs font-medium transition-colors border ${
                filter === f
                  ? "bg-surface-container-highest text-on-surface border-transparent"
                  : "bg-surface-container-lowest text-on-surface-variant border-outline-variant hover:text-on-surface"
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* Audit timeline */}
      <div className="card relative pt-4 pb-6 px-6">
        {/* Vertical line */}
        <div className="absolute left-[2.5rem] top-8 bottom-8 w-px bg-outline-variant z-0" />

        <div className="space-y-8 relative z-10">
          {filtered.length === 0 ? (
            <p className="text-body-sm text-on-surface-variant text-center py-12">No events match the current filters.</p>
          ) : (
            filtered.map((event) => {
              const style = eventTypeStyle(event.event_type);
              return (
                <div key={event.id} className="flex gap-6">
                  {/* Timeline node */}
                  <div className={`w-8 h-8 rounded-full border flex items-center justify-center shrink-0 mt-1 relative z-10 ${style.dot}`}>
                    <span className={`material-symbols-outlined text-[16px] ${style.iconColor}`}>{style.icon}</span>
                  </div>

                  {/* Event content */}
                  <div className="flex-1 space-y-3">
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${style.bg} ${style.text}`}>
                            {event.event_type}
                          </span>
                          <span className="text-label-xs font-medium text-on-surface">{event.description}</span>
                        </div>
                        <div className="flex items-center gap-3 text-label-xs text-on-surface-variant flex-wrap">
                          <span className="flex items-center gap-1">
                            <span className="material-symbols-outlined text-[14px]">schedule</span>
                            {relativeTime(event.created_at)}
                          </span>
                          <span>•</span>
                          {event.actor_type === "ai" ? (
                            <span className="flex items-center gap-1 font-medium text-accent-ai bg-accent-ai/10 px-1.5 py-0.5 rounded">
                              <span className="material-symbols-outlined text-[12px]">auto_awesome</span>
                              {event.actor}
                            </span>
                          ) : (
                            <span className="flex items-center gap-1 font-medium text-on-surface-variant">
                              <span className="material-symbols-outlined text-[14px]">person</span>
                              {event.actor}
                            </span>
                          )}
                          <span>•</span>
                          <span>Entity: {event.entity}</span>
                        </div>
                      </div>
                      <span className="text-[10px] text-on-surface-variant font-mono shrink-0">{event.id}</span>
                    </div>

                    {/* Detail block */}
                    {event.event_type === "posting" || event.event_type === "disclosure" ? (
                      <div className="bg-surface-container-low border border-outline-variant rounded-lg p-3">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-label-xs font-semibold text-on-surface flex items-center gap-1">
                            <span className="material-symbols-outlined text-[14px] text-primary">verified_user</span>
                            Content Verification Hash (SHA-256)
                          </span>
                          <button className="text-on-surface-variant hover:text-on-surface transition-colors">
                            <span className="material-symbols-outlined text-[16px]">content_copy</span>
                          </button>
                        </div>
                        <div className="font-mono text-label-xs text-on-surface-variant bg-surface-container-lowest border border-outline-variant p-2 rounded truncate">
                          {event.detail}
                        </div>
                      </div>
                    ) : (
                      <div className={`rounded-lg p-3 text-body-sm text-on-surface border ${
                        event.event_type === "override"
                          ? "bg-warning/5 border-warning/20"
                          : "bg-surface-container-low border-outline-variant"
                      }`}>
                        {event.event_type === "override" && (
                          <span className="font-semibold text-warning text-label-xs block mb-1">Justification Provided:</span>
                        )}
                        {event.detail}
                      </div>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </AppShell>
  );
}
