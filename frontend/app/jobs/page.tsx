"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { AppShell } from "@/components/layout/AppShell";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Button } from "@/components/ui/Button";
import { jobsApi } from "@/lib/api";
import { relativeTime } from "@/lib/utils";
import type { Job, JobStatus } from "@/lib/types";

const MOCK_JOBS: Job[] = [
  { id: "1", title: "Senior Frontend Developer", status: "shortlisted", collection_email: "apply-sfd@hireflow.in", channel_status: { linkedin: { status: "delivered", post_url: "#" } }, created_at: new Date(Date.now() - 86400000 * 14).toISOString(), posted_at: new Date(Date.now() - 86400000 * 13).toISOString() },
  { id: "2", title: "Product Manager", status: "scoring", collection_email: "apply-pm@hireflow.in", channel_status: { linkedin: { status: "delivered", post_url: "#" } }, created_at: new Date(Date.now() - 86400000 * 10).toISOString(), posted_at: new Date(Date.now() - 86400000 * 9).toISOString() },
  { id: "3", title: "UX Designer", status: "collecting", collection_email: "apply-ux@hireflow.in", channel_status: { linkedin: { status: "delivered", post_url: "#" } }, created_at: new Date(Date.now() - 86400000 * 7).toISOString(), posted_at: new Date(Date.now() - 86400000 * 6).toISOString() },
  { id: "4", title: "Data Scientist", status: "posted", collection_email: "apply-ds@hireflow.in", channel_status: { linkedin: { status: "delivered", post_url: "#" } }, created_at: new Date(Date.now() - 86400000 * 5).toISOString(), posted_at: new Date(Date.now() - 86400000 * 4).toISOString() },
  { id: "5", title: "Backend Engineer", status: "approved", collection_email: null, channel_status: {}, created_at: new Date(Date.now() - 86400000 * 2).toISOString(), posted_at: null },
  { id: "6", title: "DevOps Lead", status: "draft", collection_email: null, channel_status: {}, created_at: new Date(Date.now() - 86400000 * 1).toISOString(), posted_at: null },
];

const FILTERS: { label: string; value: string }[] = [
  { label: "All", value: "all" },
  { label: "Active", value: "active" },
  { label: "Shortlisted", value: "shortlisted" },
  { label: "Closed", value: "closed" },
  { label: "Draft", value: "draft" },
];

const ACTIVE_STATUSES: JobStatus[] = ["approved", "posted", "collecting", "scoring"];

export default function JobsPage() {
  const [filter, setFilter] = useState("all");
  const { data: jobs } = useQuery({
    queryKey: ["jobs"],
    queryFn: () => jobsApi.list().then((r) => r.data as Job[]),
    placeholderData: MOCK_JOBS,
  });

  const filtered = (jobs ?? MOCK_JOBS).filter((j) => {
    if (filter === "all") return true;
    if (filter === "active") return ACTIVE_STATUSES.includes(j.status as JobStatus);
    return j.status === filter;
  });

  return (
    <AppShell breadcrumbs={[{ label: "Dashboard", href: "/" }, { label: "Jobs" }]}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-headline-lg text-on-surface">Jobs</h1>
          <p className="text-body-sm text-on-surface-variant mt-1">
            Manage your active and past job postings
          </p>
        </div>
        <Link href="/jobs/new">
          <Button>
            <span className="material-symbols-outlined text-[16px]">add</span>
            New Job
          </Button>
        </Link>
      </div>

      {/* Filter pills */}
      <div className="flex items-center gap-2 mb-6">
        {FILTERS.map((f) => (
          <button
            key={f.value}
            onClick={() => setFilter(f.value)}
            className={`px-4 py-1.5 rounded-full text-label-xs font-medium transition-colors ${
              filter === f.value
                ? "bg-primary text-on-primary"
                : "bg-surface-container text-on-surface-variant hover:bg-surface-container-high"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Table */}
      {filtered.length === 0 ? (
        <div className="card flex flex-col items-center justify-center py-16 text-center">
          <span className="material-symbols-outlined text-[48px] text-outline mb-3">work_off</span>
          <p className="text-headline-sm text-on-surface">No jobs found</p>
          <p className="text-body-sm text-on-surface-variant mt-1">
            {filter === "all" ? "Post your first role to get started." : `No jobs with status "${filter}".`}
          </p>
          <Link href="/jobs/new" className="mt-4">
            <Button>Create job</Button>
          </Link>
        </div>
      ) : (
        <div className="card p-0 overflow-hidden">
          <table className="w-full text-left">
            <thead>
              <tr className="bg-surface-container-low text-on-surface-variant text-label-xs uppercase tracking-wider border-b border-outline-variant">
                <th className="px-6 py-3 font-medium">Title</th>
                <th className="px-6 py-3 font-medium">Status</th>
                <th className="px-6 py-3 font-medium">Channels</th>
                <th className="px-6 py-3 font-medium">Created</th>
                <th className="px-6 py-3 font-medium">Posted</th>
                <th className="px-6 py-3 font-medium"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-outline-variant">
              {filtered.map((job) => (
                <tr key={job.id} className="table-row-hover">
                  <td className="px-6 py-4">
                    <p className="text-body-sm font-medium text-on-surface">{job.title}</p>
                    {job.collection_email && (
                      <p className="text-label-xs text-on-surface-variant mt-0.5">{job.collection_email}</p>
                    )}
                  </td>
                  <td className="px-6 py-4"><StatusBadge status={job.status} /></td>
                  <td className="px-6 py-4">
                    {Object.keys(job.channel_status).length > 0 ? (
                      <div className="flex gap-1">
                        {Object.keys(job.channel_status).map((ch) => (
                          <span key={ch} className="inline-flex items-center gap-1 rounded-full bg-surface-container px-2 py-0.5 text-label-xs text-on-surface-variant">
                            <span className="material-symbols-outlined text-[12px]">check_circle</span>
                            {ch}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <span className="text-label-xs text-on-surface-variant">—</span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-body-sm text-on-surface-variant">{relativeTime(job.created_at)}</td>
                  <td className="px-6 py-4 text-body-sm text-on-surface-variant">
                    {job.posted_at ? relativeTime(job.posted_at) : "—"}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2 justify-end">
                      <Link
                        href={`/jobs/${job.id}`}
                        className="text-label-xs font-medium text-primary hover:underline"
                      >
                        View →
                      </Link>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </AppShell>
  );
}
