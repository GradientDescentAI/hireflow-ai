// ── Shared TypeScript interfaces ──────────────────────────────────────────────
// Mirrors backend Pydantic models and API response shapes.

export type JobStatus =
  | "draft"
  | "extraction_complete"
  | "approved"
  | "posted"
  | "collecting"
  | "scoring"
  | "shortlisted"
  | "closed";

export interface Job {
  id: string;
  title: string;
  status: JobStatus;
  collection_email: string | null;
  channel_status: Record<string, { status: string; post_url: string | null }>;
  created_at: string;
  posted_at: string | null;
  // Extended fields (GET /jobs/:id)
  must_haves?: Array<{ criterion: string; weight: number }>;
  nice_to_haves?: Array<{ criterion: string }>;
  responsibilities?: string[];
  tech_stack?: string[];
  salary_min?: number;
  salary_max?: number;
  location?: { city: string; state: string; remote: boolean };
  bias_flags?: string[];
  karnataka_salary_warning?: boolean;
  scoring_rubric?: Record<string, number>;
  shortlist_justification?: ShortlistJustification;
}

export interface ApplicationSummary {
  id: string;
  name: string;
  email: string;
  source_channel: string;
  status: "received" | "parsed" | "parse_failed" | "scored";
  applied_at: string;
  parse_confidence: number | null;
  parse_flagged: boolean;
}

export interface ShortlistEntry {
  score_id: string;
  candidate_id: string;
  name: string | null;
  rank: number;
  composite_score: number;
  dimension_scores: {
    must_have: number;
    experience: number;
    skills: number;
    nice_to_have: number;
    trajectory: number;
  };
  justification: string;
  strengths: string[];
  risks: string[];
  near_miss_flag: boolean;
  recruiter_status: "pending" | "approved" | "rejected" | "hold" | null;
  nps_thumb: boolean | null;
  source_channel: string | null;
}

export interface ShortlistJustification {
  shortlist_summary: string;
  top_candidate_notes: Array<{
    rank: number;
    headline: string;
    fit_reasons: string[];
    watch_points: string[];
  }>;
  panel_interview_questions: string[];
  diversity_note: string;
  recommended_interview_format: string;
}

export interface AuditEvent {
  id: string;
  event_type: string;
  actor: string;
  actor_type: "ai" | "human";
  description: string;
  detail: string;
  entity: string;
  created_at: string;
}

export interface DashboardStats {
  total_applications: number;
  applications_trend?: number;
  avg_time_to_shortlist_days?: number;
  time_trend_days?: number;
  shortlist_acceptance_rate?: number;
  acceptance_trend?: number;
  composite_qoh_score?: number;
  active_jobs?: number;
  bias_flagged_jobs?: number;
  // Legacy fields (dashboard widget)
  shortlisted?: number;
  nps_positive_pct?: number;
  jobs_by_status?: Record<string, number>;
}

export interface PersonaAccount {
  id: string;
  name: string;
  handle: string;
  status: "healthy" | "warning" | "error";
  posts_today: number;
  posts_limit: number;
  last_post_at: string | null;
  linkedin_status: string;
  whatsapp_status: string;
  api_status?: string;
}

export interface User {
  recruiter_id: string;
  tenant_id: string;
  role: "recruiter" | "hiring_manager" | "admin" | "super_admin";
  name: string;
  email: string;
  access_token: string;
}
