"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { AiBadge } from "@/components/ui/Badge";
import { ScoreDonut } from "@/components/ui/ScoreDonut";
import { jobsApi, shortlistApi } from "@/lib/api";
import { scoreColor } from "@/lib/utils";
import type { ShortlistEntry } from "@/lib/types";

const MOCK_SHORTLIST: ShortlistEntry[] = [
  { score_id: "s1", candidate_id: "c1", name: "Arjun Mehta", rank: 1, composite_score: 92, dimension_scores: { must_have: 95, experience: 90, skills: 92, nice_to_have: 70, trajectory: 85 }, justification: "Arjun is a standout candidate. He strongly indexes on Must-Haves, demonstrating deep expertise in React performance optimization and micro-frontend architecture. His experience scaling a product team directly mirrors the challenges ahead.", strengths: ["Exceptional React internals and rendering optimisation", "Proven track record mentoring junior developers", "Strong CI/CD understanding for frontend deployments"], risks: ["Less React Native experience than ideally desired", "Expected salary at top end of approved band"], near_miss_flag: false, recruiter_status: null, nps_thumb: null, source_channel: "linkedin" },
  { score_id: "s2", candidate_id: "c2", name: "Priya Iyer", rank: 2, composite_score: 88, dimension_scores: { must_have: 88, experience: 82, skills: 90, nice_to_have: 80, trajectory: 78 }, justification: "Priya is a high-velocity shipper with excellent UI/UX sensibilities. Strong Vue and Nuxt background — primary gap is less Next.js depth.", strengths: ["Exceptional component design and UI/UX instincts", "High shipping velocity with good code quality", "Strong cross-functional collaboration skills"], risks: ["Less Next.js experience vs. primary stack", "No large-scale team leadership experience yet"], near_miss_flag: false, recruiter_status: "approved", nps_thumb: true, source_channel: "email" },
  { score_id: "s3", candidate_id: "c3", name: "Rohan Das", rank: 3, composite_score: 79, dimension_scores: { must_have: 72, experience: 88, skills: 75, nice_to_have: 60, trajectory: 70 }, justification: "Rohan brings 8 years of deep React and WebGL experience but shows lower alignment on the required tech stack (heavy Redux vs preferred Zustand).", strengths: ["8 years deep React expertise", "WebGL and 3D rendering proficiency", "Strong architectural thinking"], risks: ["Redux-heavy background; migration friction expected", "Tech stack mismatch on state management preference"], near_miss_flag: true, recruiter_status: null, nps_thumb: null, source_channel: "linkedin" },
];

function DimensionBar({ label, value }: { label: string; value: number }) {
  const color = value >= 80 ? "bg-success" : value >= 60 ? "bg-warning" : "bg-danger";
  return (
    <div className="flex items-center gap-3">
      <span className="w-24 text-label-xs text-on-surface-variant text-right shrink-0 capitalize">{label.replace("_", "-")}</span>
      <div className="flex-1 h-2 rounded-full bg-surface-container-high overflow-hidden">
        <div className={`h-full rounded-full ${color} transition-all`} style={{ width: `${value}%` }} />
      </div>
      <span className="w-8 text-label-xs font-semibold text-on-surface text-right">{value}</span>
    </div>
  );
}

export default function ShortlistPage({ params }: { params: { id: string } }) {
  const [selected, setSelected] = useState<ShortlistEntry>(MOCK_SHORTLIST[0]);
  const [overrideOpen, setOverrideOpen] = useState(false);
  const [overrideReason, setOverrideReason] = useState("");
  const qc = useQueryClient();

  const { data: entries } = useQuery({
    queryKey: ["shortlist", params.id],
    queryFn: () => jobsApi.shortlist(params.id).then((r) => r.data as ShortlistEntry[]),
    placeholderData: MOCK_SHORTLIST,
  });

  const statusMutation = useMutation({
    mutationFn: (payload: { scoreId: string; recruiter_status: "approved" | "rejected" | "hold" }) =>
      shortlistApi.update(payload.scoreId, { recruiter_status: payload.recruiter_status }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["shortlist", params.id] }),
  });

  const npsMutation = useMutation({
    mutationFn: (payload: { scoreId: string; nps_thumb: boolean }) =>
      shortlistApi.update(payload.scoreId, { nps_thumb: payload.nps_thumb }),
  });

  const list = entries ?? MOCK_SHORTLIST;
  const biasAuditFailed = false; // would come from job data

  return (
    <AppShell
      breadcrumbs={[
        { label: "Jobs", href: "/jobs" },
        { label: "Senior Frontend Developer", href: `/jobs/${params.id}` },
        { label: "Shortlist" },
      ]}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <h1 className="text-headline-lg text-on-surface">Shortlist Review</h1>
          <AiBadge label="AI Generated" />
          <span className="text-label-xs text-on-surface-variant">{list.length} candidates</span>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm">
            <span className="material-symbols-outlined text-[14px]">download</span>
            Export CSV
          </Button>
          <Button variant="outline" size="sm">
            <span className="material-symbols-outlined text-[14px]">share</span>
            Share Link
          </Button>
        </div>
      </div>

      {/* Bias audit banner */}
      {biasAuditFailed && (
        <div className="mb-4 flex items-start gap-3 rounded-xl border border-warning/30 bg-warning/5 px-4 py-3">
          <span className="material-symbols-outlined text-warning mt-0.5">shield</span>
          <p className="text-label-xs text-on-surface-variant">
            <strong className="text-warning">Bias audit flagged:</strong> female candidates are under-represented in this shortlist vs. the applicant pool (−28 pp). Review with additional care.
          </p>
        </div>
      )}

      {/* Two-panel layout */}
      <div className="flex gap-4 h-[calc(100vh-280px)]">
        {/* Left panel — ranked list */}
        <div className="w-80 shrink-0 overflow-y-auto space-y-2">
          {list.map((entry) => (
            <button
              key={entry.score_id}
              onClick={() => setSelected(entry)}
              className={`w-full text-left rounded-xl border p-4 transition-all ${
                selected.score_id === entry.score_id
                  ? "border-primary/40 bg-primary/5 shadow-sm"
                  : "border-outline-variant bg-surface-container-lowest hover:border-outline"
              }`}
            >
              <div className="flex items-start justify-between mb-2">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`text-label-xs font-bold px-1.5 py-0.5 rounded ${selected.score_id === entry.score_id ? "bg-primary text-on-primary" : "bg-surface-container text-on-surface-variant"}`}>
                      #{entry.rank}
                    </span>
                    {entry.near_miss_flag && (
                      <span className="text-label-xs text-warning">⚡ Near miss</span>
                    )}
                  </div>
                  <p className="text-label-xs font-semibold text-on-surface">{entry.name ?? `Candidate #${entry.rank}`}</p>
                  <p className="text-label-xs text-on-surface-variant mt-0.5 line-clamp-1">
                    {entry.strengths[0] ?? "—"}
                  </p>
                </div>
                <ScoreDonut score={entry.composite_score} size={44} />
              </div>
              {entry.recruiter_status && (
                <span className={`text-label-xs font-medium rounded-full px-2 py-0.5 ${
                  entry.recruiter_status === "approved" ? "bg-success/10 text-success" :
                  entry.recruiter_status === "rejected" ? "bg-danger/10 text-danger" :
                  "bg-warning/10 text-warning"
                }`}>
                  {entry.recruiter_status}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Right panel — candidate detail */}
        <div className="flex-1 overflow-y-auto rounded-xl border border-outline-variant bg-surface-container-lowest pb-20">
          {/* Score header */}
          <div className="flex items-start justify-between p-6 border-b border-outline-variant bg-surface-container-low">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <h2 className="text-headline-md text-on-surface">{selected.name ?? `Candidate #${selected.rank}`}</h2>
                <span className="text-label-xs text-on-surface-variant">• {selected.source_channel}</span>
              </div>
              {selected.near_miss_flag && (
                <div className="flex items-center gap-2 rounded-lg bg-warning/10 border border-warning/20 px-3 py-2 text-label-xs text-warning mt-2">
                  <span className="material-symbols-outlined text-[14px]">warning</span>
                  Near miss — scored ≥70 but missed a must-have requirement
                </div>
              )}
            </div>
            <div className="text-center">
              <ScoreDonut score={selected.composite_score} size={64} />
              <p className="text-label-xs text-on-surface-variant mt-1">Composite</p>
            </div>
          </div>

          <div className="p-6 space-y-6">
            {/* AI Justification */}
            <div className="rounded-xl border border-accent-ai/20 bg-accent-ai/5 p-4">
              <div className="flex items-center gap-2 mb-2">
                <AiBadge label="Riya's Justification" />
              </div>
              <p className="text-body-sm text-on-surface leading-relaxed">{selected.justification}</p>
            </div>

            {/* Dimension breakdown */}
            <div>
              <h3 className="text-label-md font-semibold text-on-surface mb-3">Dimension Breakdown</h3>
              <div className="space-y-3">
                {Object.entries(selected.dimension_scores).map(([dim, val]) => (
                  <DimensionBar key={dim} label={dim} value={val} />
                ))}
              </div>
            </div>

            {/* Strengths + Risks */}
            <div className="grid grid-cols-2 gap-4">
              <div className="rounded-xl border border-success/20 bg-success/5 p-4">
                <h4 className="text-label-xs font-bold text-success uppercase tracking-wide mb-2 flex items-center gap-1">
                  <span className="material-symbols-outlined text-[14px]">thumb_up</span> Strengths
                </h4>
                <ul className="space-y-2">
                  {selected.strengths.map((s, i) => (
                    <li key={i} className="text-label-xs text-on-surface-variant flex gap-2">
                      <span className="text-success mt-0.5">•</span> {s}
                    </li>
                  ))}
                </ul>
              </div>
              <div className="rounded-xl border border-warning/20 bg-warning/5 p-4">
                <h4 className="text-label-xs font-bold text-warning uppercase tracking-wide mb-2 flex items-center gap-1">
                  <span className="material-symbols-outlined text-[14px]">warning</span> Risks
                </h4>
                <ul className="space-y-2">
                  {selected.risks.map((r, i) => (
                    <li key={i} className="text-label-xs text-on-surface-variant flex gap-2">
                      <span className="text-warning mt-0.5">•</span> {r}
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Override score */}
            <div>
              <button
                onClick={() => setOverrideOpen(!overrideOpen)}
                className="text-label-xs text-primary hover:underline flex items-center gap-1"
              >
                <span className="material-symbols-outlined text-[14px]">edit</span>
                {overrideOpen ? "Close" : "Override score"}
              </button>
              {overrideOpen && (
                <div className="mt-3 rounded-lg border border-outline-variant p-4 space-y-3">
                  <div>
                    <label className="label">Override Reason (required)</label>
                    <textarea
                      className="input min-h-[80px]"
                      placeholder="Explain why you're overriding the AI score..."
                      value={overrideReason}
                      onChange={(e) => setOverrideReason(e.target.value)}
                    />
                  </div>
                  <Button size="sm" disabled={!overrideReason.trim()}>Apply Override</Button>
                </div>
              )}
            </div>
          </div>

          {/* Sticky action bar */}
          <div className="sticky bottom-0 flex items-center justify-between border-t border-outline-variant bg-surface-container-lowest px-6 py-4">
            <div className="flex items-center gap-2">
              <span className="text-label-xs text-on-surface-variant">NPS:</span>
              <button
                onClick={() => npsMutation.mutate({ scoreId: selected.score_id, nps_thumb: true })}
                className={`p-2 rounded-lg border transition-colors ${selected.nps_thumb === true ? "bg-success/10 border-success/30 text-success" : "border-outline-variant text-on-surface-variant hover:bg-surface-container"}`}
              >
                <span className="material-symbols-outlined text-[18px]">thumb_up</span>
              </button>
              <button
                onClick={() => npsMutation.mutate({ scoreId: selected.score_id, nps_thumb: false })}
                className={`p-2 rounded-lg border transition-colors ${selected.nps_thumb === false ? "bg-danger/10 border-danger/30 text-danger" : "border-outline-variant text-on-surface-variant hover:bg-surface-container"}`}
              >
                <span className="material-symbols-outlined text-[18px]">thumb_down</span>
              </button>
            </div>
            <div className="flex gap-2">
              <Button variant="danger" size="sm" onClick={() => statusMutation.mutate({ scoreId: selected.score_id, recruiter_status: "rejected" })}>
                Reject
              </Button>
              <Button variant="secondary" size="sm" onClick={() => statusMutation.mutate({ scoreId: selected.score_id, recruiter_status: "hold" })}>
                Hold
              </Button>
              <Button size="sm" onClick={() => statusMutation.mutate({ scoreId: selected.score_id, recruiter_status: "approved" })}>
                <span className="material-symbols-outlined text-[14px]">check_circle</span>
                Approve
              </Button>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
