"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { AppShell } from "@/components/layout/AppShell";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Button } from "@/components/ui/Button";
import { AiBadge } from "@/components/ui/Badge";
import { jobsApi } from "@/lib/api";
import type { Job } from "@/lib/types";

const MOCK_JOB: Job = {
  id: "1",
  title: "Senior Frontend Developer",
  status: "extraction_complete",
  collection_email: null,
  channel_status: {},
  created_at: new Date(Date.now() - 86400000 * 2).toISOString(),
  posted_at: null,
  location: { city: "Bangalore", state: "Karnataka", remote: false },
  salary_min: 1800000,
  salary_max: 2500000,
  must_haves: [
    { criterion: "5+ years React / Next.js experience", weight: 2 },
    { criterion: "TypeScript proficiency", weight: 2 },
    { criterion: "State management (Redux, Zustand, or Context)", weight: 1 },
  ],
  nice_to_haves: [
    { criterion: "Experience with micro-frontend architecture" },
    { criterion: "React Native exposure" },
  ],
  tech_stack: ["React", "TypeScript", "Next.js", "Tailwind CSS", "GraphQL"],
  responsibilities: [
    "Lead frontend architecture decisions",
    "Mentor junior engineers",
    "Work closely with design team on component library",
  ],
  bias_flags: ["young and energetic — may discourage older applicants"],
  karnataka_salary_warning: false,
  scoring_rubric: { must_have: 40, experience: 25, skills: 20, nice_to_have: 10, trajectory: 5 },
  shortlist_justification: undefined,
};

const TABS = ["Overview", "JD Review", "Distribution", "Applications", "Shortlist", "Audit"] as const;
type Tab = (typeof TABS)[number];

export default function JobDetailPage({ params }: { params: { id: string } }) {
  const [tab, setTab] = useState<Tab>("JD Review");
  const [rubric, setRubric] = useState(MOCK_JOB.scoring_rubric ?? {});
  const qc = useQueryClient();

  const { data: job } = useQuery({
    queryKey: ["job", params.id],
    queryFn: () => jobsApi.get(params.id).then((r) => r.data as Job),
    placeholderData: MOCK_JOB,
    // Poll until the JD is extracted so the recruiter doesn't have to refresh
    refetchInterval: (query) => {
      const s = query.state.data?.status;
      return s === "draft" || s === undefined ? 3000 : false;
    },
  });

  const confirmMutation = useMutation({
    mutationFn: () => jobsApi.confirm(params.id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["job", params.id] }),
  });

  const j = job ?? MOCK_JOB;
  const runicTotal = Object.values(rubric).reduce((a, b) => a + b, 0);
  const canApprove = !j.karnataka_salary_warning && (j.salary_min ?? 0) > 0 && (j.salary_max ?? 0) > 0;

  return (
    <AppShell
      breadcrumbs={[{ label: "Dashboard", href: "/" }, { label: "Jobs", href: "/jobs" }, { label: j.title }]}
    >
      {/* Page header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <h1 className="text-headline-lg text-on-surface">{j.title}</h1>
          <StatusBadge status={j.status} />
          <AiBadge label="AI Extracted" />
        </div>
        {j.collection_email && (
          <div className="flex items-center gap-2 rounded-lg border border-outline-variant bg-surface-container px-3 py-2 text-label-xs text-on-surface-variant">
            <span className="material-symbols-outlined text-[14px]">email</span>
            {j.collection_email}
            <button className="hover:text-on-surface">
              <span className="material-symbols-outlined text-[14px]">content_copy</span>
            </button>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-outline-variant mb-6">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2.5 text-label-xs font-medium border-b-2 transition-colors ${
              tab === t
                ? "border-primary text-primary"
                : "border-transparent text-on-surface-variant hover:text-on-surface"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {tab === "Overview" && (
        <div className="grid grid-cols-3 gap-4">
          {[
            { label: "Status", value: j.status },
            { label: "Location", value: j.location ? `${j.location.city}, ${j.location.state}` : "—" },
            { label: "Remote", value: j.location?.remote ? "Yes" : "No" },
          ].map((item) => (
            <div key={item.label} className="card">
              <p className="text-label-xs text-on-surface-variant">{item.label}</p>
              <p className="text-body-sm font-medium text-on-surface mt-1">{item.value}</p>
            </div>
          ))}
        </div>
      )}

      {tab === "JD Review" && (
        <div className="flex gap-6">
          {/* Left — editable fields */}
          <div className="flex-1 space-y-6">
            {/* Bias flags */}
            {(j.bias_flags ?? []).length > 0 && (
              <div className="flex items-start gap-3 rounded-xl border border-warning/30 bg-warning/5 p-4">
                <span className="material-symbols-outlined text-warning mt-0.5">warning</span>
                <div>
                  <p className="text-label-xs font-semibold text-warning">Bias Language Detected</p>
                  <ul className="mt-2 space-y-1">
                    {j.bias_flags!.map((flag, i) => (
                      <li key={i} className="text-label-xs text-on-surface-variant">• {flag}</li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            {/* Karnataka salary warning */}
            {j.karnataka_salary_warning && (
              <div className="flex items-start gap-3 rounded-xl border border-danger/30 bg-danger/5 p-4">
                <span className="material-symbols-outlined text-danger mt-0.5">gavel</span>
                <p className="text-label-xs text-danger">
                  Karnataka law requires salary disclosure for this role. Add a salary range before distributing.
                </p>
              </div>
            )}

            {/* Job details */}
            <div className="card space-y-4">
              <h3 className="text-headline-sm text-on-surface">Job Details</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Job Title</label>
                  <input defaultValue={j.title} className="input" />
                </div>
                <div>
                  <label className="label">Location</label>
                  <input defaultValue={j.location ? `${j.location.city}, ${j.location.state}` : ""} className={`input ${j.location?.state?.toLowerCase() === "karnataka" ? "border-warning bg-warning/5" : ""}`} />
                </div>
                <div>
                  <label className="label">Salary Min (₹)</label>
                  <input type="number" defaultValue={j.salary_min} className="input" />
                </div>
                <div>
                  <label className="label">Salary Max (₹)</label>
                  <input type="number" defaultValue={j.salary_max} className="input" />
                </div>
              </div>

              <div className="flex items-center gap-2">
                <input type="checkbox" id="remote" defaultChecked={j.location?.remote} className="rounded" />
                <label htmlFor="remote" className="text-body-sm text-on-surface">Remote optional</label>
              </div>
            </div>

            {/* Must-haves */}
            <div className="card space-y-3">
              <h3 className="text-headline-sm text-on-surface">Must-Haves</h3>
              {(j.must_haves ?? []).map((mh, i) => (
                <div key={i} className="flex items-center justify-between rounded-lg border border-outline-variant px-3 py-2.5 bg-surface-container-low">
                  <span className="text-body-sm text-on-surface">{mh.criterion}</span>
                  <span className="text-label-xs text-on-surface-variant">weight {mh.weight}×</span>
                </div>
              ))}
            </div>

            {/* Tech stack */}
            <div className="card space-y-3">
              <h3 className="text-headline-sm text-on-surface">Tech Stack</h3>
              <div className="flex flex-wrap gap-2">
                {(j.tech_stack ?? []).map((t) => (
                  <span key={t} className="inline-flex items-center gap-1.5 rounded-full bg-primary/10 px-3 py-1 text-label-xs font-medium text-primary">
                    {t}
                    <button><span className="material-symbols-outlined text-[12px]">close</span></button>
                  </span>
                ))}
                <button className="inline-flex items-center gap-1 rounded-full border border-dashed border-outline-variant px-3 py-1 text-label-xs text-on-surface-variant hover:border-primary hover:text-primary">
                  <span className="material-symbols-outlined text-[12px]">add</span> Add
                </button>
              </div>
            </div>
          </div>

          {/* Right — scoring rubric */}
          <div className="w-72 shrink-0">
            <div className="card sticky top-20 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-headline-sm text-on-surface">Scoring Rubric</h3>
                <span className={`text-label-xs font-medium ${runicTotal === 100 ? "text-success" : "text-warning"}`}>
                  {runicTotal}%
                </span>
              </div>
              {Object.entries(rubric).map(([dim, weight]) => (
                <div key={dim}>
                  <div className="flex justify-between text-label-xs text-on-surface-variant mb-1">
                    <span className="capitalize">{dim.replace("_", " ")}</span>
                    <span>{weight}%</span>
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={60}
                    step={5}
                    value={weight}
                    onChange={(e) => setRubric((r) => ({ ...r, [dim]: +e.target.value }))}
                    className="w-full accent-primary"
                  />
                </div>
              ))}
              <p className="text-label-xs text-on-surface-variant">Weights must sum to 100%.</p>
            </div>
          </div>
        </div>
      )}

      {tab === "Distribution" && (
        <div className="max-w-xl">
          <p className="text-body-sm text-on-surface-variant mb-4">
            Ready to distribute this job posting to your selected channels.
          </p>
          <Link href={`/jobs/${params.id}/distribute`}>
            <Button disabled={j.status !== "approved"}>
              Set up Distribution →
            </Button>
          </Link>
          {j.status !== "approved" && (
            <p className="text-label-xs text-on-surface-variant mt-2">Confirm the JD first to enable distribution.</p>
          )}
        </div>
      )}

      {tab === "Applications" && (
        <div>
          <Link href={`/jobs/${params.id}/applications`} className="text-primary text-body-sm hover:underline">
            View all applications →
          </Link>
        </div>
      )}

      {tab === "Shortlist" && (
        <div>
          <Link href={`/jobs/${params.id}/shortlist`} className="text-primary text-body-sm hover:underline">
            View shortlist →
          </Link>
        </div>
      )}

      {tab === "Audit" && (
        <div>
          <Link href={`/jobs/${params.id}/audit`} className="text-primary text-body-sm hover:underline">
            View audit trail →
          </Link>
        </div>
      )}

      {/* Bottom action bar — JD Review tab */}
      {tab === "JD Review" && j.status === "extraction_complete" && (
        <div className="fixed bottom-0 left-sidebar-width right-0 bg-surface-container-lowest border-t border-outline-variant px-6 py-4 flex items-center justify-between">
          <Button variant="outline">Save changes</Button>
          <Button
            onClick={() => confirmMutation.mutate()}
            loading={confirmMutation.isPending}
            disabled={!canApprove}
          >
            Confirm & Approve →
          </Button>
        </div>
      )}
    </AppShell>
  );
}
