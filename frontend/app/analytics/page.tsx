"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { AppShell } from "@/components/layout/AppShell";
import { AiBadge } from "@/components/ui/Badge";
import { analyticsApi } from "@/lib/api";
import type { DashboardStats } from "@/lib/types";

const MOCK_STATS: DashboardStats = {
  total_applications: 1284,
  applications_trend: 12,
  avg_time_to_shortlist_days: 4.2,
  time_trend_days: -1.5,
  shortlist_acceptance_rate: 78,
  acceptance_trend: 5,
  composite_qoh_score: 82,
  active_jobs: 5,
  bias_flagged_jobs: 1,
};

const SCORE_BARS = [
  { range: "0–20", pct: 15, color: "bg-danger" },
  { range: "21–40", pct: 30, color: "bg-warning" },
  { range: "41–60", pct: 55, color: "bg-primary-fixed-dim" },
  { range: "61–80", pct: 85, color: "bg-primary" },
  { range: "81–100", pct: 40, color: "bg-success" },
];

const CHANNELS = [
  { name: "LinkedIn", icon: "work", iconBg: "bg-primary-fixed", iconColor: "text-primary", vol: 542, shortlisted: 128, rate: "23.6%", rateColor: "text-success" },
  { name: "Referrals", icon: "group", iconBg: "bg-success/20", iconColor: "text-success", vol: 112, shortlisted: 45, rate: "40.1%", rateColor: "text-success" },
  { name: "Job Boards", icon: "language", iconBg: "bg-secondary-fixed", iconColor: "text-secondary", vol: 489, shortlisted: 82, rate: "16.7%", rateColor: "text-warning" },
  { name: "WhatsApp", icon: "chat", iconBg: "bg-surface-variant", iconColor: "text-on-surface-variant", vol: 141, shortlisted: 12, rate: "8.5%", rateColor: "text-danger" },
];

const DONUT_SEGMENTS = [
  { label: "Male", pct: 45, color: "bg-primary-container", strokeColor: "#1a56db", offset: 0 },
  { label: "Female", pct: 35, color: "bg-secondary-container", strokeColor: "#894ff7", offset: -45 },
  { label: "Undisclosed", pct: 20, color: "bg-neutral-400", strokeColor: "#9ca3af", offset: -80 },
];

function KpiCard({ label, value, trend, trendLabel, aiTag }: { label: string; value: string; trend?: "up" | "down" | "stable"; trendLabel?: string; aiTag?: boolean }) {
  const trendColor = trend === "up" ? "text-success bg-success/10" : trend === "down" ? "text-success bg-success/10" : "text-on-surface-variant bg-surface-container";
  const trendIcon = trend === "up" ? "arrow_upward" : trend === "down" ? "arrow_downward" : "horizontal_rule";
  return (
    <div className="card flex flex-col gap-2">
      <div className="flex justify-between items-start">
        <p className="text-body-sm text-on-surface-variant font-medium">{label}</p>
        {aiTag && <AiBadge label="Riya AI" />}
      </div>
      <div className="flex items-baseline gap-3">
        <p className="text-3xl font-bold text-on-surface tracking-tight">{value}</p>
        {trendLabel && (
          <div className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-label-xs ${trendColor}`}>
            <span className="material-symbols-outlined text-[14px]">{trendIcon}</span>
            {trendLabel}
          </div>
        )}
      </div>
    </div>
  );
}

export default function AnalyticsPage() {
  const [period, setPeriod] = useState("Last 30 Days");

  const { data: stats } = useQuery({
    queryKey: ["analytics"],
    queryFn: () => analyticsApi.dashboard().then((r) => r.data as DashboardStats),
    placeholderData: MOCK_STATS,
  });

  const s = stats ?? MOCK_STATS;

  return (
    <AppShell breadcrumbs={[{ label: "Dashboard", href: "/" }, { label: "Analytics" }]}>
      {/* Page header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-headline-lg text-on-surface">Recruiter Analytics</h1>
        <div className="flex items-center bg-surface-container-lowest border border-outline-variant rounded-lg p-1 shadow-sm">
          <button className="p-2 text-on-surface-variant hover:bg-surface-container-low rounded-md transition-colors">
            <span className="material-symbols-outlined text-[18px]">chevron_left</span>
          </button>
          <span className="text-body-sm font-medium px-4">{period}</span>
          <button className="p-2 text-on-surface-variant hover:bg-surface-container-low rounded-md transition-colors">
            <span className="material-symbols-outlined text-[18px]">chevron_right</span>
          </button>
          <div className="h-6 w-px bg-outline-variant mx-2" />
          <button className="flex items-center gap-2 px-3 py-1.5 text-body-sm font-medium text-on-surface-variant hover:bg-surface-container-low rounded-md transition-colors">
            <span className="material-symbols-outlined text-[18px]">calendar_today</span>
            Custom
          </button>
        </div>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        <KpiCard label="Total Applications" value="1,284" trend="up" trendLabel="12%" />
        <KpiCard label="Avg. Time-to-Shortlist" value="4.2 Days" trend="down" trendLabel="1.5 d" />
        <KpiCard label="Shortlist Acceptance Rate" value="78%" trend="up" trendLabel="5%" />
        <KpiCard label="Composite QoH Score" value="82/100" trend="stable" trendLabel="Stable" aiTag />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        {/* Area chart: Applications by Channel */}
        <div className="lg:col-span-2 card flex flex-col">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-headline-md text-on-surface">Applications by Channel</h3>
            <button className="text-on-surface-variant hover:text-on-surface">
              <span className="material-symbols-outlined">more_horiz</span>
            </button>
          </div>
          <div className="flex-1 relative min-h-[240px] w-full flex items-end pt-4 pb-8 border-b border-outline-variant">
            <svg className="w-full h-full absolute bottom-8 left-0" preserveAspectRatio="none" viewBox="0 0 100 100">
              <defs>
                <linearGradient id="area-blue" x1="0" x2="0" y1="0" y2="1">
                  <stop offset="0%" stopColor="#1a56db" stopOpacity="0.3" />
                  <stop offset="100%" stopColor="#1a56db" stopOpacity="0" />
                </linearGradient>
                <linearGradient id="area-purple" x1="0" x2="0" y1="0" y2="1">
                  <stop offset="0%" stopColor="#894ff7" stopOpacity="0.2" />
                  <stop offset="100%" stopColor="#894ff7" stopOpacity="0" />
                </linearGradient>
              </defs>
              <path d="M0,100 L0,60 C20,50 30,80 50,40 C70,0 80,40 100,20 L100,100 Z" fill="url(#area-purple)" />
              <path d="M0,60 C20,50 30,80 50,40 C70,0 80,40 100,20" fill="none" stroke="#894ff7" strokeWidth="2" vectorEffect="non-scaling-stroke" />
              <path d="M0,100 L0,80 C20,70 30,90 50,50 C70,10 80,60 100,30 L100,100 Z" fill="url(#area-blue)" />
              <path d="M0,80 C20,70 30,90 50,50 C70,10 80,60 100,30" fill="none" stroke="#1a56db" strokeWidth="2" vectorEffect="non-scaling-stroke" />
            </svg>
            {/* Grid lines */}
            <div className="absolute inset-0 flex flex-col justify-between pointer-events-none pb-8">
              {[0, 1, 2, 3].map((i) => <div key={i} className="w-full h-px bg-outline-variant" />)}
            </div>
          </div>
          <div className="flex justify-between w-full mt-2 text-label-xs text-on-surface-variant">
            <span>Week 1</span><span>Week 2</span><span>Week 3</span><span>Week 4</span>
          </div>
          <div className="flex justify-center gap-4 mt-6">
            {[
              { color: "bg-primary-container", label: "LinkedIn" },
              { color: "bg-secondary-container", label: "Job Boards" },
              { color: "bg-success", label: "Referrals" },
            ].map((l) => (
              <div key={l.label} className="flex items-center gap-2">
                <div className={`w-3 h-3 rounded-sm ${l.color}`} />
                <span className="text-body-sm text-on-surface-variant">{l.label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Bar chart: Score Distribution */}
        <div className="card flex flex-col">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-headline-md text-on-surface">Score Distribution</h3>
            <AiBadge label="Riya AI" />
          </div>
          <div className="flex-1 flex items-end justify-between gap-2 pt-4 pb-2" style={{ minHeight: 180 }}>
            {SCORE_BARS.map((bar) => (
              <div key={bar.range} className="flex flex-col items-center gap-2 flex-1">
                <div className="w-full bg-surface-container-high rounded-t-md h-40 flex items-end">
                  <div
                    className={`w-full ${bar.color} rounded-t-md transition-all`}
                    style={{ height: `${bar.pct}%` }}
                  />
                </div>
                <span className="text-label-xs text-on-surface-variant">{bar.range}</span>
              </div>
            ))}
          </div>
          <p className="text-label-xs text-on-surface-variant text-center mt-2">Volume per AI score bucket.</p>
        </div>
      </div>

      {/* Bottom section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Channel performance table */}
        <div className="lg:col-span-2 card p-0 overflow-hidden">
          <div className="px-6 py-4 border-b border-outline-variant flex justify-between items-center">
            <h3 className="text-headline-md text-on-surface">Top Performing Channels</h3>
            <button className="text-body-sm font-medium text-primary hover:underline">View All</button>
          </div>
          <table className="w-full text-left">
            <thead>
              <tr className="bg-surface-container-low text-on-surface-variant text-label-xs uppercase tracking-wider border-b border-outline-variant">
                <th className="px-6 py-4 font-medium">Channel</th>
                <th className="px-6 py-4 font-medium">Total Vol.</th>
                <th className="px-6 py-4 font-medium">Shortlisted</th>
                <th className="px-6 py-4 font-medium text-right">Conversion Rate</th>
              </tr>
            </thead>
            <tbody className="text-body-sm text-on-surface divide-y divide-outline-variant">
              {CHANNELS.map((ch) => (
                <tr key={ch.name} className="table-row-hover">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3 font-medium">
                      <div className={`w-8 h-8 rounded-full ${ch.iconBg} flex items-center justify-center ${ch.iconColor}`}>
                        <span className="material-symbols-outlined text-[16px]">{ch.icon}</span>
                      </div>
                      {ch.name}
                    </div>
                  </td>
                  <td className="px-6 py-4">{ch.vol}</td>
                  <td className="px-6 py-4">{ch.shortlisted}</td>
                  <td className={`px-6 py-4 text-right font-medium ${ch.rateColor}`}>{ch.rate}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Bias audit donut */}
        <div className="card flex flex-col">
          <div className="flex justify-between items-start mb-6">
            <div>
              <h3 className="text-headline-md text-on-surface">Bias Audit</h3>
              <p className="text-label-xs text-on-surface-variant">Recent Shortlists Demographic Parity</p>
            </div>
            <span className="material-symbols-outlined text-warning text-[24px]">shield_lock</span>
          </div>
          <div className="flex flex-col items-center gap-6 py-4 flex-1">
            {/* Donut */}
            <div className="relative w-32 h-32">
              <svg className="w-full h-full -rotate-90" viewBox="0 0 36 36">
                <path className="text-surface-container-high" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeWidth="6" />
                <path className="text-primary-container" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeDasharray="45, 100" strokeWidth="6" />
                <path className="text-secondary-container" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeDasharray="35, 100" strokeDashoffset="-45" strokeWidth="6" />
                <path style={{ color: "#9ca3af" }} d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeDasharray="20, 100" strokeDashoffset="-80" strokeWidth="6" />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center flex-col">
                <span className="text-headline-md font-bold text-on-surface">Fair</span>
                <span className="text-label-xs text-success">Status</span>
              </div>
            </div>
            <div className="w-full space-y-3">
              {DONUT_SEGMENTS.map((seg) => (
                <div key={seg.label} className="flex justify-between items-center text-body-sm">
                  <div className="flex items-center gap-2">
                    <div className={`w-3 h-3 rounded-sm ${seg.color}`} />
                    <span className="text-on-surface-variant">{seg.label}</span>
                  </div>
                  <span className="font-medium">{seg.pct}%</span>
                </div>
              ))}
            </div>
          </div>
          <div className="pt-4 border-t border-outline-variant">
            <div className="bg-warning/10 border border-warning/20 rounded-lg p-3 flex gap-3 items-start">
              <span className="material-symbols-outlined text-warning text-[20px] mt-0.5">info</span>
              <p className="text-label-xs text-on-surface-variant">AI scoring models show no significant statistical deviation across tracked demographic groups in the current period.</p>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
