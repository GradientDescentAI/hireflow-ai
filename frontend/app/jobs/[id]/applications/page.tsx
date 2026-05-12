"use client";

import { useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { jobsApi } from "@/lib/api";
import { relativeTime } from "@/lib/utils";
import type { ApplicationSummary } from "@/lib/types";

const MOCK_APPS: ApplicationSummary[] = [
  { id: "1", name: "Rahul Sharma", email: "rahul.sharma@gmail.com", source_channel: "linkedin", status: "parsed", applied_at: new Date(Date.now() - 3600000 * 2).toISOString(), parse_confidence: 0.92, parse_flagged: false },
  { id: "2", name: "Priya Patel", email: "priya.patel@outlook.com", source_channel: "email", status: "scored", applied_at: new Date(Date.now() - 3600000 * 5).toISOString(), parse_confidence: 0.88, parse_flagged: false },
  { id: "3", name: "Amit Kumar", email: "amit.kumar@yahoo.com", source_channel: "linkedin", status: "parsed", applied_at: new Date(Date.now() - 3600000 * 8).toISOString(), parse_confidence: 0.54, parse_flagged: true },
  { id: "4", name: "Sneha Reddy", email: "sneha.reddy@gmail.com", source_channel: "email", status: "received", applied_at: new Date(Date.now() - 3600000 * 10).toISOString(), parse_confidence: null, parse_flagged: false },
  { id: "5", name: "Vikram Singh", email: "vikram.s@hotmail.com", source_channel: "whatsapp", status: "parse_failed", applied_at: new Date(Date.now() - 3600000 * 14).toISOString(), parse_confidence: 0.21, parse_flagged: true },
];

const CHANNEL_OPTIONS = ["All", "linkedin", "email", "whatsapp"];
const STATUS_OPTIONS = ["All", "received", "parsed", "scored", "parse_failed"];

// ── Upload CV modal ────────────────────────────────────────────────────────────

function UploadCVModal({
  jobId,
  onClose,
}: {
  jobId: string;
  onClose: () => void;
}) {
  const qc = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [fileName, setFileName] = useState("");
  const [error, setError] = useState("");

  const mutation = useMutation({
    mutationFn: (fd: FormData) => jobsApi.uploadCV(jobId, fd),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["applications", jobId] });
      onClose();
    },
    onError: (err: unknown) => {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Upload failed. Check storage configuration.";
      setError(msg);
    },
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    const file = fileRef.current?.files?.[0];
    if (!file) { setError("Select a CV file"); return; }
    if (!email) { setError("Candidate email is required"); return; }

    const fd = new FormData();
    fd.append("file", file);
    fd.append("email", email);
    fd.append("name", name);
    fd.append("source_channel", "direct");
    mutation.mutate(fd);
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-2xl border border-outline-variant bg-surface-container-lowest shadow-2xl">
        <div className="flex items-center justify-between border-b border-outline-variant px-6 py-4">
          <h2 className="text-headline-sm text-on-surface">Upload CV</h2>
          <button onClick={onClose} className="rounded p-1 hover:bg-surface-container text-on-surface-variant">
            <span className="material-symbols-outlined text-[20px]">close</span>
          </button>
        </div>
        <form onSubmit={handleSubmit} className="px-6 py-5 space-y-4">
          {/* File picker */}
          <div>
            <label className="label">CV File (PDF, DOC, DOCX — max 10 MB)</label>
            <div
              className="mt-1 flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed border-outline-variant bg-surface-container px-4 py-8 hover:border-primary hover:bg-primary/5 transition-colors"
              onClick={() => fileRef.current?.click()}
            >
              <span className="material-symbols-outlined text-[36px] text-on-surface-variant">upload_file</span>
              {fileName ? (
                <p className="text-label-xs font-medium text-primary">{fileName}</p>
              ) : (
                <p className="text-label-xs text-on-surface-variant">Click to browse or drag & drop</p>
              )}
            </div>
            <input
              ref={fileRef}
              type="file"
              accept=".pdf,.doc,.docx"
              className="hidden"
              onChange={(e) => setFileName(e.target.files?.[0]?.name ?? "")}
            />
          </div>

          {/* Email */}
          <div>
            <label className="label">Candidate Email *</label>
            <input
              type="email"
              className="input"
              placeholder="candidate@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          {/* Name */}
          <div>
            <label className="label">Candidate Name (optional)</label>
            <input
              type="text"
              className="input"
              placeholder="Full name"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>

          {error && (
            <p className="rounded-lg border border-danger/30 bg-danger/5 px-3 py-2 text-label-xs text-danger">
              {error}
            </p>
          )}

          <div className="flex justify-end gap-2 pt-1">
            <Button type="button" variant="outline" size="sm" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" size="sm" loading={mutation.isPending}>
              <span className="material-symbols-outlined text-[14px]">upload</span>
              Upload & Queue
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ── Confidence pill ────────────────────────────────────────────────────────────

function ConfidencePill({ confidence, flagged }: { confidence: number | null; flagged: boolean }) {
  if (confidence === null) return <span className="text-on-surface-variant text-label-xs">—</span>;
  if (confidence >= 0.8) return <span className="inline-flex items-center gap-1 text-label-xs text-success"><span className="h-1.5 w-1.5 rounded-full bg-success" />High</span>;
  if (confidence >= 0.6) return <span className="inline-flex items-center gap-1 text-label-xs text-warning"><span className="h-1.5 w-1.5 rounded-full bg-warning" />Medium</span>;
  return <span className="inline-flex items-center gap-1 text-label-xs text-danger"><span className="h-1.5 w-1.5 rounded-full bg-danger" />{flagged ? "Low — review" : "Low"}</span>;
}

export default function ApplicationsPage({ params }: { params: { id: string } }) {
  const [channel, setChannel] = useState("All");
  const [status, setStatus] = useState("All");
  const [uploadOpen, setUploadOpen] = useState(false);

  const { data: apps } = useQuery({
    queryKey: ["applications", params.id, channel, status],
    queryFn: () =>
      jobsApi.applications(params.id, {
        channel: channel === "All" ? undefined : channel,
        status: status === "All" ? undefined : status,
      }).then((r) => r.data as ApplicationSummary[]),
    placeholderData: MOCK_APPS,
  });

  const filtered = (apps ?? MOCK_APPS).filter(
    (a) =>
      (channel === "All" || a.source_channel === channel) &&
      (status === "All" || a.status === status)
  );

  return (
    <AppShell
      breadcrumbs={[
        { label: "Jobs", href: "/jobs" },
        { label: "Senior Frontend Developer", href: `/jobs/${params.id}` },
        { label: "Applications" },
      ]}
    >
      {uploadOpen && (
        <UploadCVModal jobId={params.id} onClose={() => setUploadOpen(false)} />
      )}

      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-headline-lg text-on-surface">Applications</h1>
          <p className="text-body-sm text-on-surface-variant mt-1">
            {filtered.length} application{filtered.length !== 1 ? "s" : ""} received
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => setUploadOpen(true)}>
            <span className="material-symbols-outlined text-[14px]">upload_file</span>
            Upload CV
          </Button>
          <Button variant="secondary" size="sm">
            <span className="material-symbols-outlined text-[14px]">auto_awesome</span>
            Trigger Scoring
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3 mb-6">
        <div className="flex items-center gap-2">
          <span className="text-label-xs text-on-surface-variant">Channel:</span>
          <div className="flex rounded-lg border border-outline-variant overflow-hidden">
            {CHANNEL_OPTIONS.map((c) => (
              <button
                key={c}
                onClick={() => setChannel(c)}
                className={`px-3 py-1.5 text-label-xs font-medium transition-colors border-r border-outline-variant last:border-0 ${channel === c ? "bg-primary text-on-primary" : "bg-surface-container-lowest text-on-surface-variant hover:bg-surface-container"}`}
              >
                {c}
              </button>
            ))}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-label-xs text-on-surface-variant">Status:</span>
          <div className="flex rounded-lg border border-outline-variant overflow-hidden">
            {STATUS_OPTIONS.map((s) => (
              <button
                key={s}
                onClick={() => setStatus(s)}
                className={`px-3 py-1.5 text-label-xs font-medium transition-colors border-r border-outline-variant last:border-0 ${status === s ? "bg-primary text-on-primary" : "bg-surface-container-lowest text-on-surface-variant hover:bg-surface-container"}`}
              >
                {s === "parse_failed" ? "Failed" : s.charAt(0).toUpperCase() + s.slice(1)}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="card p-0 overflow-hidden">
        <table className="w-full text-left">
          <thead>
            <tr className="bg-surface-container-low text-on-surface-variant text-label-xs uppercase tracking-wider border-b border-outline-variant">
              <th className="px-6 py-3 font-medium">Candidate</th>
              <th className="px-6 py-3 font-medium">Source</th>
              <th className="px-6 py-3 font-medium">Applied</th>
              <th className="px-6 py-3 font-medium">Status</th>
              <th className="px-6 py-3 font-medium">Confidence</th>
              <th className="px-6 py-3 font-medium"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-outline-variant">
            {filtered.length === 0 ? (
              <tr><td colSpan={6} className="px-6 py-12 text-center text-body-sm text-on-surface-variant">No applications match the current filters.</td></tr>
            ) : (
              filtered.map((app) => (
                <tr key={app.id} className="table-row-hover">
                  <td className="px-6 py-4">
                    <p className="text-body-sm font-medium text-on-surface">{app.name}</p>
                    <p className="text-label-xs text-on-surface-variant">{app.email}</p>
                  </td>
                  <td className="px-6 py-4">
                    <span className="inline-flex items-center gap-1.5 text-label-xs text-on-surface-variant">
                      <span className="material-symbols-outlined text-[14px]">
                        {app.source_channel === "linkedin" ? "work" : app.source_channel === "email" ? "email" : "chat"}
                      </span>
                      {app.source_channel}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-body-sm text-on-surface-variant">{relativeTime(app.applied_at)}</td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-label-xs font-medium ${
                      app.status === "scored" ? "bg-success/10 text-success" :
                      app.status === "parsed" ? "bg-primary/10 text-primary" :
                      app.status === "parse_failed" ? "bg-danger/10 text-danger" :
                      "bg-surface-container text-on-surface-variant"
                    }`}>
                      {app.status.replace("_", " ")}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <ConfidencePill confidence={app.parse_confidence} flagged={app.parse_flagged} />
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button className="text-label-xs font-medium text-primary hover:underline">View CV</button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
        <div className="px-6 py-3 border-t border-outline-variant flex items-center justify-between text-label-xs text-on-surface-variant">
          <span>Showing {filtered.length} results</span>
          <div className="flex items-center gap-2">
            <button className="rounded px-2 py-1 hover:bg-surface-container disabled:opacity-40" disabled>← Previous</button>
            <button className="rounded px-2 py-1 hover:bg-surface-container">Next →</button>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
