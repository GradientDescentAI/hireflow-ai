"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { jobsApi } from "@/lib/api";

const LINKEDIN_DRAFT = `🤝 We're Hiring: Senior Frontend Developer | Acme Corp | Bengaluru (Remote-Optional)

Are you passionate about building fast, accessible, and beautiful user experiences at scale? Acme Corp is looking for a Senior Frontend Developer to join our growing product team.

🛠️ What You'll Do:
• Lead architecture decisions for our core web platform
• Build reusable component libraries used across 3 product lines
• Collaborate with design, backend, and product teams

✅ What We're Looking For:
• 5+ years of React / Next.js experience
• TypeScript proficiency
• State management expertise (Redux, Zustand, or Context)

💰 Compensation: ₹18–25 LPA | Equity available for senior roles

📨 To apply, email your CV to: apply-sfd@hireflow.in (Subject: APPLY-SFD-2026)

This opportunity is being shared by Riya, an AI recruiting assistant operating on behalf of Acme Corp. Riya is not a human recruiter. For questions, contact hr@acmecorp.in.`;

export default function DistributePage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const [channels, setChannels] = useState({ linkedin: true, telegram: false, naukri: false });
  const [postTime, setPostTime] = useState("09:00");

  const distributeMutation = useMutation({
    mutationFn: () =>
      jobsApi.distribute(params.id, {
        channels: Object.entries(channels).filter(([, v]) => v).map(([k]) => k),
        channel_config: { post_time_ist: postTime },
      }),
    onSuccess: () => router.push(`/jobs/${params.id}`),
  });

  const disclosurePresent = LINKEDIN_DRAFT.includes("AI recruiting assistant") || LINKEDIN_DRAFT.includes("not a human");

  return (
    <AppShell
      breadcrumbs={[{ label: "Jobs", href: "/jobs" }, { label: "Senior Frontend Developer", href: `/jobs/${params.id}` }, { label: "Distribution" }]}
    >
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-headline-lg text-on-surface">Distribution Setup</h1>
        <Button
          onClick={() => distributeMutation.mutate()}
          loading={distributeMutation.isPending}
          disabled={!Object.values(channels).some(Boolean)}
        >
          <span className="material-symbols-outlined text-[16px]">rocket_launch</span>
          Launch Channels
        </Button>
      </div>

      {/* Compliance banner */}
      <div className="mb-6 flex items-center gap-3 rounded-xl border border-success/30 bg-success/5 px-4 py-3">
        <span className="material-symbols-outlined text-success">verified_user</span>
        <div>
          <p className="text-label-xs font-semibold text-success">Compliance Requirements Met</p>
          <div className="flex gap-4 mt-1">
            <span className="flex items-center gap-1 text-label-xs text-on-surface-variant">
              <span className="material-symbols-outlined text-[12px] text-success">check_circle</span>
              AI Disclosure included
            </span>
            <span className="flex items-center gap-1 text-label-xs text-on-surface-variant">
              <span className="material-symbols-outlined text-[12px] text-success">check_circle</span>
              Salary disclosed (Karnataka)
            </span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* LinkedIn preview */}
        <div className="col-span-2">
          <div className="card space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="ch-linkedin"
                  checked={channels.linkedin}
                  onChange={(e) => setChannels((c) => ({ ...c, linkedin: e.target.checked }))}
                  className="rounded"
                />
                <label htmlFor="ch-linkedin" className="flex items-center gap-2 text-label-md font-semibold text-on-surface">
                  <span className="material-symbols-outlined text-[18px]">work</span>
                  LinkedIn
                </label>
              </div>
              <div className="flex items-center gap-2">
                {disclosurePresent ? (
                  <span className="flex items-center gap-1 rounded-full bg-success/10 px-2 py-0.5 text-label-xs text-success">
                    <span className="material-symbols-outlined text-[12px]">check_circle</span> AI disclosure present
                  </span>
                ) : (
                  <span className="flex items-center gap-1 rounded-full bg-danger/10 px-2 py-0.5 text-label-xs text-danger">
                    <span className="material-symbols-outlined text-[12px]">error</span> Missing disclosure
                  </span>
                )}
              </div>
            </div>

            <div className="rounded-xl border border-outline-variant bg-surface-container-low p-4">
              <div className="flex items-center gap-3 mb-3 pb-3 border-b border-outline-variant">
                <div className="h-10 w-10 rounded-full bg-accent-ai/10 flex items-center justify-center">
                  <span className="material-symbols-outlined text-accent-ai">psychology</span>
                </div>
                <div>
                  <p className="text-label-xs font-semibold text-on-surface">Riya (via Acme Corp)</p>
                  <p className="text-label-xs text-on-surface-variant">AI Recruiting Assistant</p>
                </div>
              </div>
              <pre className="text-body-sm text-on-surface whitespace-pre-wrap font-sans leading-relaxed">
                {LINKEDIN_DRAFT}
              </pre>
            </div>

            <div className="flex gap-3">
              <Button variant="outline" size="sm">
                <span className="material-symbols-outlined text-[14px]">edit</span>
                Edit Draft
              </Button>
            </div>
          </div>
        </div>

        {/* Channel config sidebar */}
        <div className="space-y-4">
          {/* Other channels */}
          <div className="card space-y-3">
            <h3 className="text-label-md font-semibold text-on-surface">Other Channels</h3>
            {[
              { id: "telegram", label: "Telegram", icon: "send", badge: "Beta" },
              { id: "naukri", label: "Naukri India", icon: "business_center", badge: "Beta" },
            ].map((ch) => (
              <div key={ch.id} className="flex items-center justify-between py-2 border-b border-outline-variant last:border-0">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-[16px] text-on-surface-variant">{ch.icon}</span>
                  <span className="text-body-sm text-on-surface">{ch.label}</span>
                  <span className="rounded-full bg-surface-container px-2 py-0.5 text-label-xs text-on-surface-variant">{ch.badge}</span>
                </div>
                <input
                  type="checkbox"
                  checked={channels[ch.id as keyof typeof channels]}
                  onChange={(e) => setChannels((c) => ({ ...c, [ch.id]: e.target.checked }))}
                  className="rounded"
                />
              </div>
            ))}
          </div>

          {/* Posting cadence */}
          <div className="card space-y-3">
            <h3 className="text-label-md font-semibold text-on-surface">Posting Cadence</h3>
            <div>
              <label className="label">Post Time (IST)</label>
              <input
                type="time"
                value={postTime}
                onChange={(e) => setPostTime(e.target.value)}
                className="input"
                min="09:00"
                max="19:00"
              />
            </div>
            <p className="text-label-xs text-on-surface-variant">
              Window: 09:00–19:00 IST. Min 90-min spacing between channels.
            </p>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
