"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ScoreDonut } from "@/components/ui/ScoreDonut";
import { AiBadge } from "@/components/ui/Badge";
import { shareApi } from "@/lib/api";
import type { ShortlistEntry } from "@/lib/types";

// --- Mock data (mirrors shortlist page) ---
const MOCK_CANDIDATES: ShortlistEntry[] = [
  {
    score_id: "s1", candidate_id: "c1", name: "Arjun Mehta", rank: 1, composite_score: 92,
    dimension_scores: { must_have: 95, experience: 90, skills: 92, nice_to_have: 70, trajectory: 85 },
    justification: "Arjun is a standout candidate for the Senior Frontend role. He strongly indexes on your Must-Haves, demonstrating deep expertise in React performance optimization and micro-frontend architecture. His experience scaling at TechFlow directly mirrors the challenges Acme Corp is currently facing.",
    strengths: ["Exceptional React internals and rendering optimisation", "Proven track record mentoring junior developers", "Strong CI/CD understanding for frontend deployments"],
    risks: ["Less React Native experience than ideally desired", "Expected salary at top end of approved band"],
    near_miss_flag: false, recruiter_status: null, nps_thumb: null, source_channel: "linkedin",
  },
  {
    score_id: "s2", candidate_id: "c2", name: "Priya Iyer", rank: 2, composite_score: 88,
    dimension_scores: { must_have: 88, experience: 82, skills: 90, nice_to_have: 80, trajectory: 78 },
    justification: "Priya is a high-velocity shipper with excellent UI/UX sensibilities. Strong Vue and Nuxt background — primary gap is less Next.js depth.",
    strengths: ["Exceptional component design and UI/UX instincts", "High shipping velocity with good code quality", "Strong cross-functional collaboration skills"],
    risks: ["Less Next.js experience vs. primary stack", "No large-scale team leadership experience yet"],
    near_miss_flag: false, recruiter_status: null, nps_thumb: null, source_channel: "email",
  },
  {
    score_id: "s3", candidate_id: "c3", name: "Rohan Das", rank: 3, composite_score: 79,
    dimension_scores: { must_have: 72, experience: 88, skills: 75, nice_to_have: 60, trajectory: 70 },
    justification: "Rohan brings 8 years of deep React and WebGL experience but shows lower alignment on the required tech stack (heavy Redux vs preferred Zustand).",
    strengths: ["8 years deep React expertise", "WebGL and 3D rendering proficiency", "Strong architectural thinking"],
    risks: ["Redux-heavy background; migration friction expected", "Tech stack mismatch on state management preference"],
    near_miss_flag: true, recruiter_status: null, nps_thumb: null, source_channel: "linkedin",
  },
];

const OVERALL_SUMMARY = "This shortlist represents top-tier talent with strong backgrounds in modern frontend frameworks (React, Vue) and scalable architectures. The candidates demonstrated exceptional problem-solving skills, particularly in state management and performance optimization. All three are technically sound but offer different balances of leadership experience versus deep individual contributor expertise.";

const INTERVIEW_QUESTIONS = [
  {
    area: "Architecture & Scaling",
    question: '"Can you walk me through the hardest performance bottleneck you had to solve? How did you measure the impact?"',
  },
  {
    area: "Leadership Gap Probe",
    question: '"Tell me about a time you had to push back on a product requirement because it compromised frontend technical debt. How did you handle the conversation?"',
  },
];

function DimensionBar({ label, value }: { label: string; value: number }) {
  const color = value >= 80 ? "bg-success" : value >= 60 ? "bg-warning" : "bg-danger";
  return (
    <div className="flex items-center gap-4">
      <div className="w-24 text-label-xs font-medium text-on-surface-variant text-right shrink-0 capitalize">
        {label.replace("_", "-")}
      </div>
      <div className="flex-1 h-2 bg-outline-variant rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full`} style={{ width: `${value}%` }} />
      </div>
      <div className="w-8 text-label-xs font-semibold text-on-surface text-right">{value}</div>
    </div>
  );
}

export default function SharePage({ params }: { params: { token: string } }) {
  const [selected, setSelected] = useState<ShortlistEntry>(MOCK_CANDIDATES[0]);

  const { data } = useQuery({
    queryKey: ["share", params.token],
    queryFn: () => shareApi.get(params.token).then((r) => r.data as { candidates: ShortlistEntry[]; job_title: string; company: string; expires_at: string }),
    placeholderData: { candidates: MOCK_CANDIDATES, job_title: "Senior Frontend Developer", company: "Acme Corp", expires_at: "2026-10-30" },
  });

  const candidates = data?.candidates ?? MOCK_CANDIDATES;
  const jobTitle = data?.job_title ?? "Senior Frontend Developer";
  const company = data?.company ?? "Acme Corp";
  const expiresAt = data?.expires_at ?? "Oct 30, 2026";

  return (
    <div className="bg-neutral-50 font-sans text-on-surface min-h-screen flex flex-col">
      {/* Minimal public header */}
      <header className="bg-surface-container-lowest border-b border-outline-variant px-6 py-4 flex items-center justify-between sticky top-0 z-10 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-primary flex items-center justify-center text-on-primary">
            <span className="material-symbols-outlined text-[20px]">work</span>
          </div>
          <h1 className="text-headline-md text-on-surface">HireFlow</h1>
        </div>
        <div className="flex items-center gap-4">
          <div className="bg-warning/10 text-warning px-3 py-1 rounded-full text-label-xs flex items-center gap-1 border border-warning/20">
            <span className="material-symbols-outlined text-[14px]">schedule</span>
            Expires {expiresAt}
          </div>
          <button className="flex items-center gap-2 bg-surface-container-lowest border border-outline-variant text-on-surface-variant px-4 py-2 rounded-lg text-body-sm font-medium hover:bg-surface-container transition-colors">
            <span className="material-symbols-outlined text-[18px]">download</span>
            Download Report
          </button>
        </div>
      </header>

      <main className="flex-1 max-w-[1280px] w-full mx-auto p-6 md:p-8 space-y-8">
        {/* Page header */}
        <section className="space-y-4">
          <div>
            <h2 className="text-headline-lg text-on-surface">Shortlist for {jobTitle}</h2>
            <p className="text-on-surface-variant text-body-sm mt-1">
              {company} • {candidates.length} Candidates Recommended
            </p>
          </div>

          {/* Riya summary */}
          <div className="bg-accent-ai/5 border border-accent-ai/20 rounded-xl p-5 shadow-sm relative overflow-hidden">
            <div className="absolute top-0 left-0 w-1 h-full bg-accent-ai" />
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-full bg-accent-ai/10 flex items-center justify-center shrink-0">
                <span className="material-symbols-outlined text-accent-ai">auto_awesome</span>
              </div>
              <div className="space-y-2">
                <h3 className="font-semibold text-on-surface text-body-sm flex items-center gap-2">
                  Overall Pool Quality
                  <AiBadge label="Powered by Riya AI" />
                </h3>
                <p className="text-on-surface-variant text-body-sm leading-relaxed">{OVERALL_SUMMARY}</p>
              </div>
            </div>
          </div>
        </section>

        {/* Split layout */}
        <div className="flex flex-col lg:flex-row gap-6">
          {/* Left: Candidate list */}
          <div className="w-full lg:w-[40%] space-y-4">
            <h3 className="text-headline-md text-on-surface px-1">Ranked Candidates</h3>
            {candidates.map((c) => {
              const isSelected = selected.score_id === c.score_id;
              return (
                <button
                  key={c.score_id}
                  onClick={() => setSelected(c)}
                  className={`w-full text-left rounded-xl p-4 shadow-sm cursor-pointer relative overflow-hidden transition-all ${
                    isSelected
                      ? "bg-surface-container-lowest border-2 border-primary/20"
                      : "bg-surface-container-lowest border border-outline-variant hover:border-outline"
                  }`}
                >
                  {isSelected && <div className="absolute top-0 left-0 w-1 h-full bg-primary" />}
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`font-bold px-2 py-0.5 rounded text-label-xs ${
                          isSelected ? "bg-primary/10 text-primary" : "bg-surface-container text-on-surface-variant border border-outline-variant"
                        }`}>
                          #{c.rank} Rank
                        </span>
                        <h4 className="font-semibold text-on-surface text-body-sm">{c.name}</h4>
                      </div>
                      {c.near_miss_flag && (
                        <span className="text-label-xs text-warning">⚡ Near miss</span>
                      )}
                    </div>
                    <ScoreDonut score={c.composite_score} size={48} />
                  </div>
                  <div className="bg-surface-container-low rounded p-2 text-label-xs text-on-surface-variant border border-outline-variant">
                    <span className="font-medium text-on-surface">Strength:</span>{" "}
                    {c.strengths[0]}
                  </div>
                </button>
              );
            })}
          </div>

          {/* Right: Detail panel */}
          <div className="w-full lg:w-[60%] flex flex-col gap-6">
            <div className="bg-surface-container-lowest border border-outline-variant rounded-xl shadow-sm overflow-hidden">
              {/* Detail header */}
              <div className="p-6 border-b border-outline-variant bg-surface-container-low flex justify-between items-start">
                <div>
                  <h2 className="text-headline-lg text-on-surface">{selected.name}</h2>
                  <p className="text-on-surface-variant mt-1 text-body-sm">Senior Frontend Developer</p>
                  <div className="flex gap-2 mt-3">
                    <span className="inline-flex items-center gap-1 bg-success/10 text-success px-2 py-1 rounded text-label-xs font-medium border border-success/20">
                      <span className="material-symbols-outlined text-[14px]">check_circle</span>
                      Ready to Hire
                    </span>
                  </div>
                </div>
                <div className="text-center">
                  <ScoreDonut score={selected.composite_score} size={64} />
                  <p className="text-label-xs text-on-surface-variant mt-1">Match Score</p>
                </div>
              </div>

              <div className="p-6 space-y-6">
                {/* AI Justification */}
                <div className="bg-accent-ai/5 border border-accent-ai/20 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="material-symbols-outlined text-[16px] text-accent-ai">auto_awesome</span>
                    <span className="text-label-xs font-bold text-accent-ai uppercase tracking-wider">Riya's Assessment</span>
                  </div>
                  <p className="text-body-sm text-on-surface-variant leading-relaxed">{selected.justification}</p>
                </div>

                {/* Dimension breakdown */}
                <div>
                  <h3 className="text-body-sm font-semibold text-on-surface mb-4 border-b border-outline-variant pb-2">
                    Dimension Breakdown
                  </h3>
                  <div className="space-y-4">
                    {Object.entries(selected.dimension_scores).map(([dim, val]) => (
                      <DimensionBar key={dim} label={dim} value={val} />
                    ))}
                  </div>
                </div>

                {/* Strengths + Risks */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="border border-outline-variant rounded-lg p-4 bg-surface-container-low">
                    <h4 className="text-label-xs font-bold text-success uppercase tracking-wide mb-2 flex items-center gap-1">
                      <span className="material-symbols-outlined text-[16px]">thumb_up</span> Key Strengths
                    </h4>
                    <ul className="text-body-sm text-on-surface-variant space-y-2">
                      {selected.strengths.map((s, i) => (
                        <li key={i} className="flex gap-2">
                          <span className="text-success mt-0.5">•</span> {s}
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div className="border border-outline-variant rounded-lg p-4 bg-surface-container-low">
                    <h4 className="text-label-xs font-bold text-warning uppercase tracking-wide mb-2 flex items-center gap-1">
                      <span className="material-symbols-outlined text-[16px]">warning</span> Potential Risks
                    </h4>
                    <ul className="text-body-sm text-on-surface-variant space-y-2">
                      {selected.risks.map((r, i) => (
                        <li key={i} className="flex gap-2">
                          <span className="text-warning mt-0.5">•</span> {r}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            </div>

            {/* Interview questions */}
            <div className="bg-surface-container-lowest border border-outline-variant rounded-xl shadow-sm p-6">
              <div className="flex items-center gap-2 mb-4 pb-2 border-b border-outline-variant">
                <span className="material-symbols-outlined text-accent-ai">psychology</span>
                <h3 className="text-headline-md text-on-surface">Riya's Interview Suggestions</h3>
              </div>
              <p className="text-body-sm text-on-surface-variant mb-4">
                Based on this candidate's profile and your required competencies, focus on these areas:
              </p>
              <ul className="space-y-4">
                {INTERVIEW_QUESTIONS.map((q, i) => (
                  <li key={i} className="bg-surface-container-low p-3 rounded border border-outline-variant flex gap-3">
                    <div className="text-accent-ai font-bold text-body-sm">{i + 1}.</div>
                    <div>
                      <p className="text-body-sm font-medium text-on-surface">{q.area}</p>
                      <p className="text-label-xs text-on-surface-variant mt-1 italic">{q.question}</p>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        {/* Public footer */}
        <footer className="border-t border-outline-variant pt-6 text-center text-label-xs text-on-surface-variant space-y-1">
          <p>
            This shortlist was prepared by <strong>Riya</strong>, an AI recruiting assistant operating on behalf of {company}.{" "}
            <strong>Riya is not a human recruiter.</strong>
          </p>
          <p>For questions, contact your Acme Corp HR representative. This link expires on {expiresAt}.</p>
        </footer>
      </main>
    </div>
  );
}
