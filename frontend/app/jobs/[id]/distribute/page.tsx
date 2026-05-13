"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { AiBadge } from "@/components/ui/Badge";
import { jobsApi } from "@/lib/api";

function PostSkeleton() {
  return (
    <div className="space-y-2 animate-pulse">
      {[80, 60, 90, 55, 70, 85, 65, 75].map((w, i) => (
        <div key={i} className="h-3.5 rounded bg-surface-container-high" style={{ width: `${w}%` }} />
      ))}
    </div>
  );
}

export default function DistributePage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const [channels, setChannels] = useState({ linkedin: true, telegram: false, naukri: false });
  const [postTime, setPostTime] = useState("09:00");
  const [editedDraft, setEditedDraft] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);

  const {
    data: draftData,
    isLoading: draftLoading,
    isError: draftError,
    error: draftErrorObj,
  } = useQuery({
    queryKey: ["linkedin-draft", params.id],
    queryFn: () => jobsApi.linkedinDraft(params.id).then((r) => r.data),
    staleTime: 5 * 60 * 1000, // cache 5 min — LLM call is expensive
    retry: 1,
  });

  const postBody = editedDraft ?? draftData?.post_body ?? "";
  const charCount = postBody.length;
  const disclosurePresent =
    postBody.includes("AI recruiting assistant") || postBody.includes("not a human");

  const distributeMutation = useMutation({
    mutationFn: () =>
      jobsApi.distribute(params.id, {
        channels: Object.entries(channels).filter(([, v]) => v).map(([k]) => k),
        channel_config: { post_time_ist: postTime },
      }),
    onSuccess: () => router.push(`/jobs/${params.id}`),
  });

  return (
    <AppShell
      breadcrumbs={[
        { label: "Jobs", href: "/jobs" },
        { label: "Job Detail", href: `/jobs/${params.id}` },
        { label: "Distribution" },
      ]}
    >
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <h1 className="text-headline-lg text-on-surface">Distribution Setup</h1>
          <AiBadge label="Riya" />
        </div>
        <Button
          onClick={() => distributeMutation.mutate()}
          loading={distributeMutation.isPending}
          disabled={!Object.values(channels).some(Boolean) || draftLoading}
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
              <span className={`material-symbols-outlined text-[12px] ${disclosurePresent || draftLoading ? "text-success" : "text-warning"}`}>
                {disclosurePresent || draftLoading ? "check_circle" : "warning"}
              </span>
              AI Disclosure {draftLoading ? "checking…" : disclosurePresent ? "included" : "missing"}
            </span>
            <span className="flex items-center gap-1 text-label-xs text-on-surface-variant">
              <span className="material-symbols-outlined text-[12px] text-success">check_circle</span>
              Salary disclosed
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
              <div className="flex items-center gap-2 text-label-xs text-on-surface-variant">
                {!draftLoading && (
                  <span className={charCount > 3000 ? "text-danger" : ""}>
                    {charCount} / 3,000 chars
                  </span>
                )}
                {disclosurePresent && !draftLoading && (
                  <span className="flex items-center gap-1 rounded-full bg-success/10 px-2 py-0.5 text-success">
                    <span className="material-symbols-outlined text-[12px]">check_circle</span>
                    AI disclosure present
                  </span>
                )}
              </div>
            </div>

            {/* Post preview / editor */}
            <div className="rounded-xl border border-outline-variant bg-surface-container-low p-4">
              <div className="flex items-center gap-3 mb-3 pb-3 border-b border-outline-variant">
                <div className="h-10 w-10 rounded-full bg-accent-ai/10 flex items-center justify-center">
                  <span className="material-symbols-outlined text-accent-ai">psychology</span>
                </div>
                <div>
                  <p className="text-label-xs font-semibold text-on-surface">Riya (AI Recruiting Assistant)</p>
                  <p className="text-label-xs text-on-surface-variant">
                    {draftLoading ? "Generating post with Gemini…" : "Post preview"}
                  </p>
                </div>
              </div>

              {draftLoading && <PostSkeleton />}

              {draftError && !draftLoading && (
                <div className="rounded-lg border border-danger/20 bg-danger/5 p-3 text-label-xs text-danger">
                  <strong>Could not generate draft:</strong>{" "}
                  {(draftErrorObj as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
                    "Job must be in Approved status. Confirm the JD first."}
                </div>
              )}

              {!draftLoading && !draftError && (
                editing ? (
                  <textarea
                    className="input min-h-[320px] font-sans text-body-sm leading-relaxed"
                    value={postBody}
                    onChange={(e) => setEditedDraft(e.target.value)}
                  />
                ) : (
                  <pre className="text-body-sm text-on-surface whitespace-pre-wrap font-sans leading-relaxed">
                    {postBody}
                  </pre>
                )
              )}
            </div>

            {!draftLoading && !draftError && (
              <div className="flex gap-3">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setEditing(!editing);
                    if (editing && editedDraft === null) setEditedDraft(postBody);
                  }}
                >
                  <span className="material-symbols-outlined text-[14px]">
                    {editing ? "visibility" : "edit"}
                  </span>
                  {editing ? "Preview" : "Edit Draft"}
                </Button>
                {editedDraft !== null && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => { setEditedDraft(null); setEditing(false); }}
                  >
                    Reset to AI draft
                  </Button>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Channel config sidebar */}
        <div className="space-y-4">
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
              Window: 09:00–19:00 IST · Min 90-min spacing between channels.
            </p>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
