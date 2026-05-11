'use client'

/**
 * HireFlow AI — Recruiter Dashboard (`/`)
 *
 * Generated from FRONTEND_SPEC.md §2.
 *
 * Stack: Next.js 14 App Router · Tailwind CSS · shadcn/ui · lucide-react · TanStack Query
 * Design tokens: primary #1a56db, accent #6c2bd9, success #057a55, warning #c27803, danger #c81e1e
 *
 * Notes:
 *   - Uses mock data + a 700ms simulated load. Wire to TanStack Query hitting the
 *     three API endpoints in §2 (`/analytics/dashboard`, `/jobs`, `/personas/health`)
 *     in parallel via `useQueries`.
 *   - Sidebar/Topbar are inlined here for self-contained preview. In production,
 *     hoist them into `app/(dashboard)/layout.tsx` so they're shared across pages.
 *   - shadcn primitives (Button, Card, Badge, Table) are styled inline with their
 *     class patterns; swap to the actual imports once `npx shadcn-ui add` is run.
 */

import { useEffect, useMemo, useState } from 'react'
import {
  Home,
  Briefcase,
  BarChart3,
  Settings,
  Sparkles,
  ArrowUp,
  ArrowDown,
  AlertTriangle,
  Bell,
  Plus,
  ChevronRight,
  LogOut,
  Activity,
  CircleDot,
  ShieldAlert,
  ShieldCheck,
} from 'lucide-react'

// ─────────────────────────────────────────────────────────────────────────────
// Types (mirrors FRONTEND_SPEC.md "Data Types" section)
// ─────────────────────────────────────────────────────────────────────────────

type JobStatus =
  | 'draft'
  | 'extraction_complete'
  | 'approved'
  | 'posted'
  | 'collecting'
  | 'scoring'
  | 'shortlisted'
  | 'closed'

interface Job {
  id: string
  title: string
  status: JobStatus
  collection_email: string | null
  channel_status: Record<string, { status: string; post_url: string | null }>
  created_at: string
  posted_at: string | null
  bias_audit_passed?: boolean
}

interface JobPipelineRow extends Job {
  applications_count: number
  shortlisted_count: number
  last_activity_at: string
}

interface DashboardStats {
  total_applications: number
  shortlisted: number
  nps_positive_pct: number
  jobs_by_status: Record<string, number>
  // Trend deltas for the 7-day arrows. Real API should expose these; for the MVP
  // Phase 2 backlog: extend `/analytics/dashboard` with `trend_7d` block.
  trend_7d: {
    total_applications: number
    shortlisted: number
    nps_positive_pct: number
    active_jobs: number
  }
}

interface PersonaAccount {
  id: string
  persona_name: string
  linkedin_handle: string
  health_status: 'green' | 'yellow' | 'red'
  posts_today: number
  total_posts: number
  last_post_at: string | null
  last_health_check_at: string | null
}

interface AuditEvent {
  id: string
  event_type: string
  entity_type: string
  channel: string | null
  content_hash: string | null
  data: Record<string, unknown>
  created_at: string
}

// ─────────────────────────────────────────────────────────────────────────────
// Mock data (replace with TanStack Query results)
// ─────────────────────────────────────────────────────────────────────────────

const MOCK_STATS: DashboardStats = {
  total_applications: 342,
  shortlisted: 41,
  nps_positive_pct: 67,
  jobs_by_status: {
    draft: 1,
    approved: 1,
    posted: 1,
    collecting: 1,
    scoring: 1,
    shortlisted: 2,
    closed: 0,
  },
  trend_7d: {
    total_applications: 12,
    shortlisted: 4,
    nps_positive_pct: -3,
    active_jobs: 0,
  },
}

const MOCK_JOBS: JobPipelineRow[] = [
  {
    id: 'job_01HX1',
    title: 'Senior Backend Engineer',
    status: 'shortlisted',
    collection_email: 'apply-job_01HX1@hireflow.in',
    channel_status: { linkedin: { status: 'posted', post_url: 'https://linkedin.com/posts/...' } },
    created_at: '2026-04-22T09:00:00Z',
    posted_at: '2026-04-23T11:30:00Z',
    bias_audit_passed: true,
    applications_count: 87,
    shortlisted_count: 12,
    last_activity_at: '2026-05-09T07:42:00Z',
  },
  {
    id: 'job_01HX2',
    title: 'Product Designer (Bengaluru)',
    status: 'shortlisted',
    collection_email: 'apply-job_01HX2@hireflow.in',
    channel_status: { linkedin: { status: 'posted', post_url: 'https://linkedin.com/posts/...' } },
    created_at: '2026-04-18T08:00:00Z',
    posted_at: '2026-04-19T10:15:00Z',
    bias_audit_passed: false,
    applications_count: 64,
    shortlisted_count: 8,
    last_activity_at: '2026-05-09T06:11:00Z',
  },
  {
    id: 'job_01HX3',
    title: 'Data Engineer',
    status: 'scoring',
    collection_email: 'apply-job_01HX3@hireflow.in',
    channel_status: { linkedin: { status: 'posted', post_url: 'https://linkedin.com/posts/...' } },
    created_at: '2026-04-28T12:30:00Z',
    posted_at: '2026-04-29T09:00:00Z',
    bias_audit_passed: true,
    applications_count: 102,
    shortlisted_count: 0,
    last_activity_at: '2026-05-09T05:50:00Z',
  },
  {
    id: 'job_01HX4',
    title: 'DevOps Engineer (Remote)',
    status: 'collecting',
    collection_email: 'apply-job_01HX4@hireflow.in',
    channel_status: { linkedin: { status: 'posted', post_url: 'https://linkedin.com/posts/...' } },
    created_at: '2026-05-02T11:00:00Z',
    posted_at: '2026-05-03T08:30:00Z',
    bias_audit_passed: true,
    applications_count: 53,
    shortlisted_count: 0,
    last_activity_at: '2026-05-09T04:18:00Z',
  },
  {
    id: 'job_01HX5',
    title: 'Customer Success Manager',
    status: 'posted',
    collection_email: 'apply-job_01HX5@hireflow.in',
    channel_status: { linkedin: { status: 'posted', post_url: 'https://linkedin.com/posts/...' } },
    created_at: '2026-05-06T10:00:00Z',
    posted_at: '2026-05-07T13:00:00Z',
    bias_audit_passed: true,
    applications_count: 28,
    shortlisted_count: 0,
    last_activity_at: '2026-05-08T22:30:00Z',
  },
  {
    id: 'job_01HX6',
    title: 'Frontend Lead (TypeScript)',
    status: 'approved',
    collection_email: 'apply-job_01HX6@hireflow.in',
    channel_status: {},
    created_at: '2026-05-08T15:00:00Z',
    posted_at: null,
    bias_audit_passed: true,
    applications_count: 0,
    shortlisted_count: 0,
    last_activity_at: '2026-05-08T15:42:00Z',
  },
  {
    id: 'job_01HX7',
    title: 'QA Automation Engineer',
    status: 'draft',
    collection_email: null,
    channel_status: {},
    created_at: '2026-05-09T03:00:00Z',
    posted_at: null,
    bias_audit_passed: undefined,
    applications_count: 0,
    shortlisted_count: 0,
    last_activity_at: '2026-05-09T03:12:00Z',
  },
]

const MOCK_PERSONAS: PersonaAccount[] = [
  {
    id: 'persona_01',
    persona_name: 'Riya Iyer',
    linkedin_handle: 'riya-iyer-recruits',
    health_status: 'green',
    posts_today: 1,
    total_posts: 47,
    last_post_at: '2026-05-09T04:30:00Z',
    last_health_check_at: '2026-05-09T08:00:00Z',
  },
  {
    id: 'persona_02',
    persona_name: 'Riya Sharma',
    linkedin_handle: 'riya-sharma-talent',
    health_status: 'yellow',
    posts_today: 2,
    total_posts: 31,
    last_post_at: '2026-05-09T06:10:00Z',
    last_health_check_at: '2026-05-09T08:00:00Z',
  },
]

const MOCK_AUDIT_EVENTS: AuditEvent[] = [
  {
    id: 'evt_01',
    event_type: 'SHORTLIST_PUBLISHED',
    entity_type: 'job',
    channel: null,
    content_hash: 'a4f9c2…',
    data: { job_id: 'job_01HX1', candidates: 12 },
    created_at: '2026-05-09T07:42:00Z',
  },
  {
    id: 'evt_02',
    event_type: 'BIAS_AUDIT_FAILED',
    entity_type: 'job',
    channel: null,
    content_hash: '7c1b8e…',
    data: { job_id: 'job_01HX2', dimension: 'gender', delta_pp: -28 },
    created_at: '2026-05-09T06:11:00Z',
  },
  {
    id: 'evt_03',
    event_type: 'SCORE_OVERRIDE',
    entity_type: 'shortlist_entry',
    channel: null,
    content_hash: '2d6a91…',
    data: { score_id: 'sc_88', from: 72, to: 81, reason: 'Recruiter context' },
    created_at: '2026-05-09T05:55:00Z',
  },
  {
    id: 'evt_04',
    event_type: 'POST_PUBLISHED',
    entity_type: 'job',
    channel: 'linkedin',
    content_hash: 'b3e7f4…',
    data: { job_id: 'job_01HX5', persona_id: 'persona_01' },
    created_at: '2026-05-08T13:00:00Z',
  },
  {
    id: 'evt_05',
    event_type: 'JD_EXTRACTED',
    entity_type: 'job',
    channel: null,
    content_hash: null,
    data: { job_id: 'job_01HX7' },
    created_at: '2026-05-09T03:12:00Z',
  },
]

// ─────────────────────────────────────────────────────────────────────────────
// Utilities
// ─────────────────────────────────────────────────────────────────────────────

function relTime(iso: string, now = Date.now()): string {
  const diff = (now - new Date(iso).getTime()) / 1000
  if (diff < 60) return 'just now'
  if (diff < 3600) return `${Math.round(diff / 60)}m ago`
  if (diff < 86400) return `${Math.round(diff / 3600)}h ago`
  return `${Math.round(diff / 86400)}d ago`
}

function formatEventLabel(t: string): string {
  return t
    .toLowerCase()
    .split('_')
    .map((w) => w[0].toUpperCase() + w.slice(1))
    .join(' ')
}

// ─────────────────────────────────────────────────────────────────────────────
// Sidebar
// ─────────────────────────────────────────────────────────────────────────────

function Sidebar({ overallHealth, isAdmin }: { overallHealth: 'green' | 'yellow' | 'red'; isAdmin: boolean }) {
  const dotClass =
    overallHealth === 'green' ? 'bg-success' : overallHealth === 'yellow' ? 'bg-warning' : 'bg-danger'
  const healthLabel =
    overallHealth === 'green' ? 'Healthy' : overallHealth === 'yellow' ? 'Action needed' : 'Account issue'

  const navItems = [
    { icon: Home, label: 'Dashboard', href: '/', active: true },
    { icon: Briefcase, label: 'Jobs', href: '/jobs', active: false },
    { icon: BarChart3, label: 'Analytics', href: '/analytics', active: false },
  ]

  return (
    <aside className="hidden md:flex md:w-60 md:flex-col fixed inset-y-0 z-20 border-r border-neutral-200 bg-white">
      <div className="px-5 py-5 border-b border-neutral-200">
        <div className="flex items-center gap-2.5">
          <div className="h-9 w-9 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center shrink-0">
            <Sparkles className="h-4 w-4 text-white" />
          </div>
          <div className="min-w-0">
            <div className="font-semibold text-neutral-900 leading-tight">HireFlow</div>
            <div className="flex items-center gap-1 text-xs text-neutral-500 mt-0.5">
              <span className={`h-1.5 w-1.5 rounded-full ${dotClass}`} />
              <span className="truncate">Riya AI · {healthLabel}</span>
            </div>
          </div>
        </div>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-0.5">
        {navItems.map((item) => (
          <a
            key={item.href}
            href={item.href}
            className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              item.active
                ? 'bg-primary/10 text-primary'
                : 'text-neutral-700 hover:bg-neutral-50 hover:text-neutral-900'
            }`}
          >
            <item.icon className="h-4 w-4" />
            {item.label}
          </a>
        ))}

        {isAdmin && (
          <div className="pt-4 mt-4 border-t border-neutral-200 space-y-0.5">
            <a
              href="/settings/personas"
              className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-neutral-700 hover:bg-neutral-50 hover:text-neutral-900"
            >
              <Settings className="h-4 w-4" />
              Personas
            </a>
          </div>
        )}
      </nav>

      <div className="px-3 py-3 border-t border-neutral-200">
        <div className="flex items-center gap-3 px-2">
          <div className="h-8 w-8 rounded-full bg-gradient-to-br from-neutral-300 to-neutral-400 flex items-center justify-center text-xs font-semibold text-white shrink-0">
            T
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-sm font-medium text-neutral-900 truncate">Tamilinpan</div>
            <div className="text-xs text-neutral-500">Recruiter</div>
          </div>
          <button
            type="button"
            aria-label="Sign out"
            className="text-neutral-400 hover:text-neutral-700 p-1 rounded"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </div>
    </aside>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Topbar
// ─────────────────────────────────────────────────────────────────────────────

function Topbar({ alertCount }: { alertCount: number }) {
  return (
    <div className="sticky top-0 z-10 flex items-center justify-between bg-white/90 backdrop-blur border-b border-neutral-200 px-6 py-3">
      <nav aria-label="Breadcrumb" className="text-sm text-neutral-500">
        <span className="text-neutral-900 font-medium">Dashboard</span>
      </nav>
      <div className="flex items-center gap-2">
        <button
          type="button"
          aria-label={`Notifications${alertCount ? `, ${alertCount} unread` : ''}`}
          className="relative p-2 text-neutral-500 hover:text-neutral-700 rounded-lg hover:bg-neutral-100 transition-colors"
        >
          <Bell className="h-4 w-4" />
          {alertCount > 0 && (
            <span className="absolute top-1 right-1 h-2 w-2 bg-danger rounded-full ring-2 ring-white" />
          )}
        </button>
        <a
          href="/jobs/new"
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary hover:bg-primary-hover text-white text-sm font-medium transition-colors"
        >
          <Plus className="h-4 w-4" />
          New Job
        </a>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// KPI card
// ─────────────────────────────────────────────────────────────────────────────

interface KpiCardProps {
  label: string
  value: number
  delta: number
  suffix?: string
}

function KpiCard({ label, value, delta, suffix = '' }: KpiCardProps) {
  const isUp = delta > 0
  const isDown = delta < 0
  const trendClass = isUp ? 'text-success' : isDown ? 'text-danger' : 'text-neutral-400'
  const TrendIcon = isUp ? ArrowUp : isDown ? ArrowDown : CircleDot

  return (
    <div className="rounded-xl border border-neutral-200 bg-white shadow-sm p-5">
      <div className="text-xs font-medium text-neutral-500 uppercase tracking-wider">{label}</div>
      <div className="mt-2 flex items-baseline gap-2">
        <span className="text-3xl font-semibold text-neutral-900 tabular-nums">
          {value}
          {suffix}
        </span>
        <span className={`inline-flex items-center text-xs font-medium ${trendClass}`}>
          <TrendIcon className="h-3 w-3 mr-0.5" />
          {Math.abs(delta)}
          {suffix}
        </span>
      </div>
      <div className="mt-1 text-xs text-neutral-500">vs. previous 7 days</div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Status badge (job pipeline status)
// ─────────────────────────────────────────────────────────────────────────────

const STATUS_STYLE: Record<JobStatus, { label: string; cls: string }> = {
  draft: { label: 'Draft', cls: 'bg-neutral-100 text-neutral-700' },
  extraction_complete: { label: 'Review', cls: 'bg-blue-50 text-blue-700' },
  approved: { label: 'Approved', cls: 'bg-blue-50 text-blue-700' },
  posted: { label: 'Posted', cls: 'bg-indigo-50 text-indigo-700' },
  collecting: { label: 'Collecting', cls: 'bg-cyan-50 text-cyan-700' },
  scoring: { label: 'Scoring', cls: 'bg-amber-50 text-amber-700' },
  shortlisted: { label: 'Shortlisted', cls: 'bg-emerald-50 text-emerald-700' },
  closed: { label: 'Closed', cls: 'bg-neutral-100 text-neutral-500' },
}

function StatusBadge({ status }: { status: JobStatus }) {
  const cfg = STATUS_STYLE[status]
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${cfg.cls}`}>
      {cfg.label}
    </span>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Active jobs pipeline table
// ─────────────────────────────────────────────────────────────────────────────

function JobsPipeline({ jobs }: { jobs: JobPipelineRow[] }) {
  if (jobs.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-neutral-300 bg-white p-12 text-center">
        <Briefcase className="h-10 w-10 text-neutral-300 mx-auto" aria-hidden />
        <h3 className="mt-3 text-sm font-medium text-neutral-900">No jobs yet</h3>
        <p className="mt-1 text-sm text-neutral-500">
          Post your first role to start collecting applications.
        </p>
        <a
          href="/jobs/new"
          className="mt-4 inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-primary hover:bg-primary-hover text-white text-sm font-medium"
        >
          <Plus className="h-4 w-4" /> Create job
        </a>
      </div>
    )
  }

  return (
    <section
      aria-labelledby="pipeline-heading"
      className="rounded-xl border border-neutral-200 bg-white shadow-sm overflow-hidden"
    >
      <header className="px-6 py-4 border-b border-neutral-200 flex items-center justify-between">
        <div>
          <h2 id="pipeline-heading" className="text-base font-semibold text-neutral-900">
            Active jobs pipeline
          </h2>
          <p className="text-xs text-neutral-500 mt-0.5">{jobs.length} jobs across all stages</p>
        </div>
        <a href="/jobs" className="text-sm text-primary font-medium hover:underline inline-flex items-center">
          View all <ChevronRight className="h-3.5 w-3.5 ml-0.5" />
        </a>
      </header>

      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead className="bg-neutral-50">
            <tr>
              <th scope="col" className="px-6 py-3 text-xs font-medium text-neutral-500 uppercase tracking-wider">
                Job
              </th>
              <th scope="col" className="px-6 py-3 text-xs font-medium text-neutral-500 uppercase tracking-wider">
                Status
              </th>
              <th scope="col" className="px-6 py-3 text-xs font-medium text-neutral-500 uppercase tracking-wider tabular-nums">
                Apps
              </th>
              <th scope="col" className="px-6 py-3 text-xs font-medium text-neutral-500 uppercase tracking-wider tabular-nums">
                Shortlisted
              </th>
              <th scope="col" className="px-6 py-3 text-xs font-medium text-neutral-500 uppercase tracking-wider">
                Last activity
              </th>
              <th scope="col" className="px-6 py-3" aria-label="Row actions" />
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-200">
            {jobs.map((job) => (
              <tr key={job.id} className="hover:bg-neutral-50 transition-colors">
                <td className="px-6 py-3.5">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-neutral-900">{job.title}</span>
                    {job.bias_audit_passed === false && (
                      <span title="Bias audit flagged">
                        <ShieldAlert className="h-3.5 w-3.5 text-warning" aria-label="Bias audit flagged" />
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-neutral-500 mt-0.5">
                    Created {new Date(job.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}
                  </div>
                </td>
                <td className="px-6 py-3.5">
                  <StatusBadge status={job.status} />
                </td>
                <td className="px-6 py-3.5 text-sm text-neutral-700 tabular-nums">{job.applications_count}</td>
                <td className="px-6 py-3.5 text-sm text-neutral-700 tabular-nums">
                  {job.shortlisted_count > 0 ? (
                    <span className="font-medium text-success">{job.shortlisted_count}</span>
                  ) : (
                    <span className="text-neutral-400">—</span>
                  )}
                </td>
                <td className="px-6 py-3.5 text-sm text-neutral-500" title={new Date(job.last_activity_at).toLocaleString()}>
                  {relTime(job.last_activity_at)}
                </td>
                <td className="px-6 py-3.5 text-right">
                  <a
                    href={`/jobs/${job.id}`}
                    className="text-sm text-primary font-medium hover:underline"
                  >
                    View
                  </a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// System alerts panel (right rail)
// ─────────────────────────────────────────────────────────────────────────────

interface SystemAlertsProps {
  personas: PersonaAccount[]
  biasFlaggedJobs: JobPipelineRow[]
  events: AuditEvent[]
}

function SystemAlerts({ personas, biasFlaggedJobs, events }: SystemAlertsProps) {
  const overall: 'green' | 'yellow' | 'red' = personas.some((p) => p.health_status === 'red')
    ? 'red'
    : personas.some((p) => p.health_status === 'yellow')
      ? 'yellow'
      : 'green'

  const overallCfg = {
    green: {
      label: 'Riya: Healthy',
      sub: 'All persona accounts in good standing',
      cls: 'bg-success/5 border-success/20 text-success',
      Icon: ShieldCheck,
    },
    yellow: {
      label: 'Riya: Action needed',
      sub: `${personas.filter((p) => p.health_status === 'yellow').length} persona showing reduced reach`,
      cls: 'bg-warning/5 border-warning/30 text-warning',
      Icon: AlertTriangle,
    },
    red: {
      label: 'Riya: Account issue',
      sub: 'A persona account is restricted — failover initiated',
      cls: 'bg-danger/5 border-danger/30 text-danger',
      Icon: ShieldAlert,
    },
  }[overall]

  const recent = events.slice(0, 5)

  return (
    <aside aria-label="System alerts" className="space-y-4">
      {/* Persona health summary */}
      <section
        aria-labelledby="persona-health-heading"
        className={`rounded-xl border ${overallCfg.cls} p-4`}
      >
        <div className="flex items-start gap-3">
          <overallCfg.Icon className="h-5 w-5 mt-0.5 shrink-0" aria-hidden />
          <div className="min-w-0 flex-1">
            <h3 id="persona-health-heading" className="text-sm font-semibold">
              {overallCfg.label}
            </h3>
            <p className="mt-0.5 text-xs opacity-90">{overallCfg.sub}</p>
            <ul className="mt-3 space-y-1.5">
              {personas.map((p) => (
                <li key={p.id} className="flex items-center justify-between text-xs">
                  <span className="flex items-center gap-1.5 text-neutral-700">
                    <span
                      className={`h-1.5 w-1.5 rounded-full ${
                        p.health_status === 'green'
                          ? 'bg-success'
                          : p.health_status === 'yellow'
                            ? 'bg-warning'
                            : 'bg-danger'
                      }`}
                    />
                    {p.persona_name}
                  </span>
                  <span className="text-neutral-500 tabular-nums">
                    {p.posts_today}/3 today
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      {/* Bias audit alerts */}
      {biasFlaggedJobs.length > 0 && (
        <section
          aria-labelledby="bias-heading"
          className="rounded-xl border border-warning/30 bg-warning/5 p-4"
        >
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 mt-0.5 text-warning shrink-0" aria-hidden />
            <div className="min-w-0 flex-1">
              <h3 id="bias-heading" className="text-sm font-semibold text-warning">
                Bias audit flagged
              </h3>
              <p className="mt-0.5 text-xs text-neutral-700">
                {biasFlaggedJobs.length} job{biasFlaggedJobs.length === 1 ? '' : 's'} with under-represented groups
                in the shortlist.
              </p>
              <ul className="mt-3 space-y-1.5">
                {biasFlaggedJobs.map((job) => (
                  <li key={job.id} className="text-xs">
                    <a
                      href={`/jobs/${job.id}/shortlist`}
                      className="font-medium text-neutral-900 hover:text-primary hover:underline"
                    >
                      {job.title}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </section>
      )}

      {/* Recent audit events */}
      <section
        aria-labelledby="audit-heading"
        className="rounded-xl border border-neutral-200 bg-white shadow-sm p-4"
      >
        <header className="flex items-center justify-between">
          <h3 id="audit-heading" className="text-sm font-semibold text-neutral-900 inline-flex items-center gap-1.5">
            <Activity className="h-4 w-4 text-neutral-500" />
            Recent activity
          </h3>
        </header>
        {recent.length === 0 ? (
          <p className="mt-3 text-xs text-neutral-500">No events yet.</p>
        ) : (
          <ol className="mt-3 space-y-3">
            {recent.map((evt) => {
              const isWarn = evt.event_type.includes('FAILED') || evt.event_type.includes('OVERRIDE')
              return (
                <li key={evt.id} className="flex gap-2.5">
                  <span
                    className={`mt-1.5 h-1.5 w-1.5 rounded-full shrink-0 ${
                      isWarn ? 'bg-warning' : 'bg-primary'
                    }`}
                  />
                  <div className="min-w-0 flex-1">
                    <div className="text-xs font-medium text-neutral-900">{formatEventLabel(evt.event_type)}</div>
                    <div className="text-xs text-neutral-500" title={new Date(evt.created_at).toLocaleString()}>
                      {relTime(evt.created_at)}
                      {evt.channel ? ` · ${evt.channel}` : ''}
                    </div>
                  </div>
                </li>
              )
            })}
          </ol>
        )}
      </section>
    </aside>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Loading skeleton
// ─────────────────────────────────────────────────────────────────────────────

function DashboardSkeleton() {
  return (
    <div className="grid grid-cols-1 xl:grid-cols-[1fr_300px] gap-6 animate-pulse" aria-hidden>
      <div className="space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="h-28 rounded-xl bg-neutral-100" />
          ))}
        </div>
        <div className="h-96 rounded-xl bg-neutral-100" />
      </div>
      <div className="space-y-4">
        <div className="h-32 rounded-xl bg-neutral-100" />
        <div className="h-48 rounded-xl bg-neutral-100" />
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Main page
// ─────────────────────────────────────────────────────────────────────────────

export default function DashboardPage() {
  // In production: replace with TanStack Query.
  //   const { data: stats }    = useQuery({ queryKey: ['stats'],    queryFn: () => api.get('/analytics/dashboard') })
  //   const { data: jobs }     = useQuery({ queryKey: ['jobs'],     queryFn: () => api.get('/jobs') })
  //   const { data: personas } = useQuery({ queryKey: ['personas'], queryFn: () => api.get('/personas/health') })
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [jobs, setJobs] = useState<JobPipelineRow[]>([])
  const [personas, setPersonas] = useState<PersonaAccount[]>([])
  const [events, setEvents] = useState<AuditEvent[]>([])

  useEffect(() => {
    const t = setTimeout(() => {
      setStats(MOCK_STATS)
      setJobs(MOCK_JOBS)
      setPersonas(MOCK_PERSONAS)
      setEvents(MOCK_AUDIT_EVENTS)
      setLoading(false)
    }, 700)
    return () => clearTimeout(t)
  }, [])

  const overallHealth = useMemo<'green' | 'yellow' | 'red'>(() => {
    if (personas.some((p) => p.health_status === 'red')) return 'red'
    if (personas.some((p) => p.health_status === 'yellow')) return 'yellow'
    return 'green'
  }, [personas])

  const activeJobsCount = useMemo(
    () => jobs.filter((j) => !['draft', 'closed'].includes(j.status)).length,
    [jobs],
  )

  const biasFlaggedJobs = useMemo(() => jobs.filter((j) => j.bias_audit_passed === false), [jobs])

  const alertCount = (overallHealth !== 'green' ? 1 : 0) + (biasFlaggedJobs.length > 0 ? 1 : 0)

  return (
    <div className="min-h-screen bg-neutral-50 font-sans antialiased">
      <Sidebar overallHealth={overallHealth} isAdmin />
      <div className="md:pl-60">
        <Topbar alertCount={alertCount} />
        <main className="px-6 py-6 max-w-7xl mx-auto">
          <header className="mb-6">
            <h1 className="text-2xl font-semibold text-neutral-900">Welcome back, Tamilinpan</h1>
            <p className="text-sm text-neutral-500 mt-1">
              Here's what's happening across your hiring pipeline.
            </p>
          </header>

          {loading || !stats ? (
            <DashboardSkeleton />
          ) : (
            <div className="grid grid-cols-1 xl:grid-cols-[1fr_300px] gap-6">
              <div className="space-y-6 min-w-0">
                {/* Section A: KPI strip */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                  <KpiCard
                    label="Total Applications"
                    value={stats.total_applications}
                    delta={stats.trend_7d.total_applications}
                  />
                  <KpiCard
                    label="Shortlisted"
                    value={stats.shortlisted}
                    delta={stats.trend_7d.shortlisted}
                  />
                  <KpiCard
                    label="NPS Positive"
                    value={stats.nps_positive_pct}
                    delta={stats.trend_7d.nps_positive_pct}
                    suffix="%"
                  />
                  <KpiCard
                    label="Active Jobs"
                    value={activeJobsCount}
                    delta={stats.trend_7d.active_jobs}
                  />
                </div>

                {/* Section B: Active jobs pipeline */}
                <JobsPipeline jobs={jobs} />
              </div>

              {/* Section C: System alerts (right rail) */}
              <SystemAlerts
                personas={personas}
                biasFlaggedJobs={biasFlaggedJobs}
                events={events}
              />
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
