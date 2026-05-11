"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { AiBadge } from "@/components/ui/Badge";
import { jobsApi } from "@/lib/api";

type InputMode = "text" | "url";

export default function NewJobPage() {
  const router = useRouter();
  const [mode, setMode] = useState<InputMode>("text");
  const [text, setText] = useState("");
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const canSubmit = mode === "text" ? text.trim().length >= 100 : url.trim().length > 8;

  const handleSubmit = async () => {
    setError("");
    setLoading(true);
    try {
      const res = await jobsApi.create({
        raw_jd_text: mode === "text" ? text : undefined,
        raw_jd_url: mode === "url" ? url : undefined,
      });
      const jobId = (res.data as { job_id: string }).job_id;
      router.push(`/jobs/${jobId}`);
    } catch {
      setError("Failed to create job. Please try again.");
      setLoading(false);
    }
  };

  return (
    <AppShell
      breadcrumbs={[{ label: "Dashboard", href: "/" }, { label: "Jobs", href: "/jobs" }, { label: "New Job" }]}
      showNewJob={false}
    >
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-headline-lg text-on-surface">Create a New Job</h1>
          <p className="text-body-sm text-on-surface-variant mt-1">
            Start by providing the source content for Riya to extract structured details.
          </p>
        </div>

        <div className="card">
          {/* Mode toggle */}
          <div className="flex rounded-lg border border-outline-variant p-1 mb-6 bg-surface-container w-fit">
            {(["text", "url"] as InputMode[]).map((m) => (
              <button
                key={m}
                onClick={() => setMode(m)}
                className={`px-4 py-1.5 rounded text-label-xs font-medium transition-colors ${
                  mode === m
                    ? "bg-surface-container-lowest text-on-surface shadow-sm"
                    : "text-on-surface-variant hover:text-on-surface"
                }`}
              >
                {m === "text" ? "Paste Description" : "Enter URL"}
              </button>
            ))}
          </div>

          {/* Input area */}
          {mode === "text" ? (
            <div className="mb-6">
              <label className="label">Job Description</label>
              <textarea
                className="input min-h-[280px] resize-y font-mono text-xs"
                placeholder="Paste the full job description here...&#10;&#10;Include: title, responsibilities, requirements, salary (required for Karnataka), location."
                value={text}
                onChange={(e) => setText(e.target.value)}
              />
              <p className="mt-1.5 text-label-xs text-on-surface-variant">
                {text.length} characters{text.length < 100 && text.length > 0 && " — minimum 100 required"}
              </p>
            </div>
          ) : (
            <div className="mb-6">
              <label className="label">Job Posting URL</label>
              <input
                type="url"
                className="input"
                placeholder="https://www.linkedin.com/jobs/view/..."
                value={url}
                onChange={(e) => setUrl(e.target.value)}
              />
              <p className="mt-1.5 text-label-xs text-on-surface-variant">
                LinkedIn, Naukri, or company careers page URLs are supported.
              </p>
            </div>
          )}

          {error && (
            <div className="mb-4 flex items-center gap-2 rounded-lg bg-danger/10 border border-danger/20 px-3 py-2.5 text-body-sm text-danger">
              <span className="material-symbols-outlined text-[16px]">error</span>
              {error}
            </div>
          )}

          {/* Submit */}
          <Button
            onClick={handleSubmit}
            disabled={!canSubmit}
            loading={loading}
            className="w-full justify-center"
          >
            <AiBadge label="" />
            Extract with Riya →
          </Button>

          <p className="mt-3 text-center text-label-xs text-on-surface-variant">
            Riya will extract structured fields. You'll review and edit everything before posting.
          </p>
        </div>

        {/* Info cards */}
        <div className="mt-6 grid grid-cols-3 gap-4">
          {[
            { icon: "auto_awesome", title: "AI Extraction", desc: "Title, requirements, tech stack, salary — all structured automatically" },
            { icon: "shield", title: "Bias Check", desc: "Riya flags age-coded or gendered language and suggests alternatives" },
            { icon: "gavel", title: "Compliance", desc: "Karnataka salary disclosure requirement enforced before posting" },
          ].map((item) => (
            <div key={item.title} className="rounded-xl border border-outline-variant p-4 bg-surface-container-lowest">
              <span className="material-symbols-outlined text-accent-ai text-[20px]">{item.icon}</span>
              <p className="text-label-xs font-semibold text-on-surface mt-2">{item.title}</p>
              <p className="text-label-xs text-on-surface-variant mt-1">{item.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </AppShell>
  );
}
