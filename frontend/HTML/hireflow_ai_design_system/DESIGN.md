---
name: HireFlow AI Design System
colors:
  surface: '#faf8ff'
  surface-dim: '#d9d9e4'
  surface-bright: '#faf8ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f3f3fe'
  surface-container: '#ededf8'
  surface-container-high: '#e7e7f3'
  surface-container-highest: '#e2e1ed'
  on-surface: '#191b23'
  on-surface-variant: '#434654'
  inverse-surface: '#2e3039'
  inverse-on-surface: '#f0f0fb'
  outline: '#737686'
  outline-variant: '#c3c5d7'
  surface-tint: '#1353d8'
  primary: '#003fb1'
  on-primary: '#ffffff'
  primary-container: '#1a56db'
  on-primary-container: '#d4dcff'
  inverse-primary: '#b5c4ff'
  secondary: '#6f30dc'
  on-secondary: '#ffffff'
  secondary-container: '#894ff7'
  on-secondary-container: '#fffbff'
  tertiary: '#852b00'
  on-tertiary: '#ffffff'
  tertiary-container: '#ad3b00'
  on-tertiary-container: '#ffd4c5'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dbe1ff'
  primary-fixed-dim: '#b5c4ff'
  on-primary-fixed: '#00174d'
  on-primary-fixed-variant: '#003dab'
  secondary-fixed: '#eaddff'
  secondary-fixed-dim: '#d2bcff'
  on-secondary-fixed: '#25005a'
  on-secondary-fixed-variant: '#5900c7'
  tertiary-fixed: '#ffdbcf'
  tertiary-fixed-dim: '#ffb59a'
  on-tertiary-fixed: '#380d00'
  on-tertiary-fixed-variant: '#802a00'
  background: '#faf8ff'
  on-background: '#191b23'
  surface-variant: '#e2e1ed'
  success: '#057a55'
  warning: '#c27803'
  danger: '#c81e1e'
  neutral-50: '#f9fafb'
  neutral-200: '#e5e7eb'
  neutral-700: '#374151'
  neutral-900: '#111928'
  accent-ai: '#6c2bd9'
typography:
  headline-lg:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-md:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 28px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-muted:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
  label-xs:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  sidebar-width: 240px
  sidebar-collapsed: 64px
  max-content-width: 80rem
  container-padding: 1.5rem
  card-padding: 1.5rem
  gutter: 1rem
---

# HireFlow AI — Frontend Specification
## For use with Claude.ai Artifacts (React component generation + live preview)

---

## How to use this file

1. Open [claude.ai](https://claude.ai) in a browser (Sonnet or Opus model).
2. Start a new conversation. Paste this entire file as your first message, then say:
   > "I'm building this product. Generate the [Page Name] page as a React component
   > using Next.js 14 App Router, Tailwind CSS, and shadcn/ui. Use the API contracts
   > and data types defined in this spec. Show a realistic preview with mock data."
3. Claude will render a live preview in the Artifacts panel on the right.
4. Iterate on the design in that conversation, then copy the final code into the repo.
5. Do one page per conversation to keep context clean.

---

## Tech Stack

| Layer | Choice | Reason |
|---|---|---|
| Framework | Next.js 14 (App Router) | SSR for shortlist share links; RSC for dashboard data |
| Styling | Tailwind CSS v3 | Fast, consistent, no CSS files to manage |
| Component library | shadcn/ui (Radix primitives) | Accessible, customisable, copy-paste model |
| Charts | Recharts | Lightweight, Tailwind-friendly |
| State / data fetching | TanStack Query v5 | Cache, loading states, refetch on focus |
| Auth | next-auth v5 (JWT strategy) | Wraps the existing FastAPI JWT; no Prisma needed |
| Forms | React Hook Form + Zod | Schema-driven validation |
| Icons | lucide-react | Included with shadcn/ui |
| HTTP client | axios (with interceptor for Bearer token) | |
| Deployment | Vercel (frontend) + existing Docker stack (API) | |
| i18n | next-intl (English only for MVP; Hindi stub) | |

---

## Design System

### Colours (Tailwind config)
```js
// tailwind.config.js — extend colors:
primary:   { DEFAULT: '#1a56db', hover: '#1648c2' }   // blue — primary actions
success:   { DEFAULT: '#057a55' }                       // green — shortlisted / passed
warning:   { DEFAULT: '#c27803' }                       // amber — flagged / near miss
danger:    { DEFAULT: '#c81e1e' }                       // red — rejected / banned account
neutral:   { 50: '#f9fafb', 900: '#111928' }            // greys
accent:    { DEFAULT: '#6c2bd9' }                       // purple — AI / Riya badge
```

### Typography
- Font: Inter (Google Fonts)
- Headings: `font-semibold`
- Body: `text-sm text-neutral-700`
- Muted: `text-xs text-neutral-500`

### Layout
- Sidebar navigation (240px fixed, collapsible to icon rail on mobile)
- Main content: `max-w-7xl mx-auto px-6 py-8`
- Cards: `rounded-xl border border-neutral-200 bg-white shadow-sm p-6`

### Riya AI badge (used wherever AI generated content appears)
```jsx
<span className="inline-flex items-center gap-1 rounded-full bg-accent/10 px-2 py-0.5 text-xs font-medium text-accent">
  <SparklesIcon className="h-3 w-3" /> AI
</span>
```

---

## API Base URL

```
NEXT_PUBLIC_API_URL=https://api.hireflow.in   // production
// dev: http://localhost:8000
```

All requests include `Authorization: Bearer <jwt>` header.
Interceptor handles 401 → redirect to /login.

---

## Data Types (TypeScript interfaces)

```ts
// Job
interface Job {
  id: string
  title: string
  status: 'draft' | 'extraction_complete' | 'approved' | 'posted' | 'collecting' | 'scoring' | 'shortlisted' | 'closed'
  collection_email: string | null
  channel_status: Record<string, { status: string; post_url: string | null }>
  created_at: string
  posted_at: string | null
  // Extended (GET /jobs/:id only)
  must_haves?: Array<{ criterion: string; weight: number }>
  nice_to_haves?: Array<{ criterion: string }>
  responsibilities?: string[]
  tech_stack?: string[]
  salary_min?: number
  salary_max?: number
  location?: { city: string; state: string; remote: boolean }
  bias_flags?: string[]
  karnataka_salary_warning?: boolean
  scoring_rubric?: Record<string, number>
  shortlist_justification?: ShortlistJustification
}

// Candidate (in applications list)
interface ApplicationSummary {
  id: string
  name: string
  email: string
  source_channel: string
  status: 'received' | 'parsed' | 'parse_failed' | 'scored'
  applied_at: string
  parse_confidence: number | null
  parse_flagged: boolean
}

// Score (in shortlist)
interface ShortlistEntry {
  score_id: string
  candidate_id: string
  name: string | null
  rank: number
  composite_score: number   // 0–100
  dimension_scores: {
    must_have: number
    experience: number
    skills: number
    nice_to_have: number
    trajectory: number
  }
  justification: string
  strengths: string[]
  risks: string[]
  near_miss_flag: boolean
  recruiter_status: 'pending' | 'approved' | 'rejected' | 'hold' | null
  nps_thumb: boolean | null
  source_channel: string | null
}

// Shortlist justification doc (stored on Job)
interface ShortlistJustification {
  shortlist_summary: string
  top_candidate_notes: Array<{
    rank: number
    headline: string
    fit_reasons: string[]
    watch_points: string[]
  }>
  panel_interview_questions: string[]
  diversity_note: string
  recommended_interview_format: string
}

// Audit event
interface AuditEvent {
  id: string
  event_type: string
  entity_type: string
  channel: string | null
  content_hash: string | null
  data: Record<string, unknown>
  created_at: string
}

// Analytics
interface DashboardStats {
  total_applications: number
  shortlisted: number
  nps_positive_pct: number
  jobs_by_status: Record<string, number>
}

// Persona health
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
```

---

## Pages & Routes

| Route | Page | Auth required | Notes |
|---|---|---|---|
| `/login` | Login | No | |
| `/` | Dashboard | Yes | Redirect from root |
| `/jobs` | Jobs list | Yes | |
| `/jobs/new` | Create job | Yes | |
| `/jobs/[id]` | Job detail / JD review | Yes | Tabbed layout |
| `/jobs/[id]/distribute` | Distribution setup | Yes | Requires status=approved |
| `/jobs/[id]/applications` | Applications list | Yes | |
| `/jobs/[id]/shortlist` | Shortlist review | Yes | |
| `/jobs/[id]/audit` | Audit trail | Yes | |
| `/analytics` | Analytics dashboard | Yes | |
| `/settings/personas` | Persona health | Yes (admin) | |
| `/share/[token]` | Public shortlist view | No | Read-only, time-limited JWT |

---

## Page Specifications

---

### 1. `/login` — Login Page

**Layout:** Centered card, 400px wide, full-height background with subtle gradient.

**Elements:**
- HireFlow logo + "Riya" wordmark top-center
- Tagline: "AI-powered hiring for Indian SMBs"
- Email input
- Password input
- "Sign in" button (primary)
- Error state: inline red alert below button

**API:**
```
POST /api/v1/auth/login
Body: { email, password }
Response: { access_token, recruiter_id, tenant_id, role, name }
```

**Behaviour:**
- On success: store JWT in httpOnly cookie via next-auth, redirect to `/`
- On 401: "Invalid email or password"
- No self-sign-up link (invite-only MVP)

---

### 2. `/` — Recruiter Dashboard

**Layout:** Sidebar + main content.

**Sidebar navigation items:**
- Dashboard (home icon)
- Jobs (briefcase icon)
- Analytics (bar-chart icon)
- Settings / Personas (settings icon, admin only)
- Separator + "Riya AI" badge with green/red dot (persona health summary)

**Main content — 3 sections:**

**Section A: KPI strip (4 cards in a row)**
```
Total Applications | Shortlisted | NPS Positive | Active Jobs
      342          |     41      |    67%       |     5
```
Each card: large number, label, 7-day trend arrow (↑↓).

**Section B: Active jobs pipeline (table)**
Columns: Job title | Status badge | Applications | Shortlisted | Last activity | Actions
Status badges: colour-coded pill (draft=grey, approved=blue, posted=indigo,
collecting=cyan, scoring=amber, shortlisted=green, closed=neutral).
Actions: "View" link → `/jobs/[id]`

**Section C: System alerts (right sidebar, 240px)**
- Persona health status (green/yellow/red dot + "Riya: Healthy" or "Action needed")
- Bias audit alerts: if any job has `bias_audit_passed=false`, show warning card
- Recent audit events (last 5, compact list)

**API calls (parallel on mount):**
```
GET /api/v1/analytics/dashboard   → DashboardStats
GET /api/v1/jobs                  → Job[]  (list, all statuses)
GET /api/v1/personas/health       → PersonaAccount[]
```

---

### 3. `/jobs` — Jobs List

**Layout:** Page header with "New Job" button (top right) + filterable table.

**Filters (horizontal pill bar):** All | Draft | Active | Shortlisted | Closed

**Table columns:** Title | Status | Applications | Posted channels | Created | Actions
**Row actions:** View | Re-score (if shortlisted) | Close

**Empty state:** Illustration + "Post your first role" CTA → `/jobs/new`

**API:**
```
GET /api/v1/jobs   → Job[]
```

---

### 4. `/jobs/new` — Create Job

**Layout:** Centred form, max-w-2xl.

**Step 1 of 2 — Paste JD:**
- Radio toggle: "Paste text" | "Enter URL"
- If text: large textarea (min 200 chars, placeholder: "Paste the full job description…")
- If URL: URL input (validated)
- "Extract with AI →" button (primary)
- Below button: small text "Riya will extract structured fields. You'll review before posting."

**Step 2 of 2 — Review (shows after extraction completes):**
- Loading state: spinner with "Riya is reading your JD…" (poll GET /jobs/:id every 2s until status=extraction_complete)
- On complete: redirect to `/jobs/[id]` (JD review tab)

**Bias flag alert (if bias_flags non-empty):**
```
⚠️  Riya detected potentially biased language:
• "young and energetic" — may discourage older applicants
• "recent graduate preferred" — age-coded
[Suggested alternatives below each flag]
```

**Karnataka salary alert (if karnataka_salary_warning=true):**
```
⚠️  Karnataka law requires salary disclosure for this role.
Please add salary range before distributing.
```

**API:**
```
POST /api/v1/jobs
Body: { raw_jd_text } or { raw_jd_url }
Response: { job_id, status }
```

---

### 5. `/jobs/[id]` — Job Detail (Tabbed)

**Tabs:** Overview | JD Review | Distribution | Applications | Shortlist | Audit

**Tab: Overview**
- Job title (editable inline), status badge
- KPI row: Applications, Shortlisted, Channels posted, Days active
- Channel status cards: LinkedIn (green/amber/red dot + post URL link), others as stubs
- Collection email box: `apply-{role_id}@hireflow.in` with copy button

**Tab: JD Review**
- Structured fields rendered from extracted JSON, all editable:
  - Title, Location, Remote toggle
  - Salary Min / Max (with Karnataka warning banner if applicable)
  - Must-haves (tag list, add/remove)
  - Nice-to-haves (tag list)
  - Tech stack (tag chips)
  - Responsibilities (numbered list, editable)
  - Scoring rubric (5 sliders, locked to sum=100)
- Bias flags section (collapsible, amber background)
- Bottom action bar:
  - "Save changes" (PATCH /jobs/:id)
  - "Confirm & Approve →" button (POST /jobs/:id/confirm) — only enabled if no Karnataka violation

**Tab: Distribution** (only shown when status=approved or later)
- Channel checklist: ☑ LinkedIn, ☐ Telegram (beta), ☐ Naukri (beta)
- LinkedIn preview card:
  - Shows the draft post text (call POST .../linkedin/draft first — stub for now)
  - "Approve & Post" button → POST /jobs/:id/distribute
  - Disclosure badge indicator: "✓ AI disclosure present" (green) or "✗ Missing" (red)
- After posting: post URL link + thumbnail of screenshot stored in S3

**Tab: Applications**
(see `/jobs/[id]/applications` page spec — same content, embedded in tab)

**Tab: Shortlist**
(see `/jobs/[id]/shortlist` page spec — same content, embedded in tab)

**Tab: Audit**
(see `/jobs/[id]/audit` page spec — same content, embedded in tab)

**API:**
```
GET  /api/v1/jobs/:id                 → Job (full)
POST /api/v1/jobs/:id/confirm         → { status: 'approved' }
POST /api/v1/jobs/:id/distribute      Body: { channels, channel_config }
PATCH /api/v1/jobs/:id               Body: partial Job fields
```

---

### 6. `/jobs/[id]/applications` — Applications List

**Layout:** Filter bar + data table.

**Filter bar:** Channel (All | LinkedIn | Email | WhatsApp) | Status (All | Received | Parsed | Flagged | Failed)

**Table columns:**
- Name | Email | Channel (icon badge) | Applied | Status (pill) | Confidence | Actions

**Confidence column:**
- ≥ 0.8: green dot "High"
- 0.6–0.79: amber dot "Medium"
- < 0.6: red dot "Low — review" (links to flag)

**Row actions:** View CV (presigned S3 URL in new tab)

**Bulk action bar (appears when rows selected):**
"Trigger scoring for selected" → POST /jobs/:id/score (scoped to selection — future phase)

**Empty state:** "No applications yet. Share the collection email with candidates."

**API:**
```
GET /api/v1/jobs/:id/applications?channel=&status=   → ApplicationSummary[]
```

---

### 7. `/jobs/[id]/shortlist` — Shortlist Review

This is the most important page. Design it with care.

**Layout:** Two-panel on desktop (list left 40%, detail right 60%). Single column on mobile.

**Left panel — ranked list:**
- Each row: Rank badge (#1, #2…) | Composite score donut (small, colour-coded) | Strengths snippet | Near-miss flag (amber ⚡ if true) | Recruiter status badge
- Clicking a row loads detail in right panel
- Sort controls: By Score (default) | By Must-Have | By Experience

**Right panel — candidate detail:**

*Score header:*
- Composite score: large number with colour ring (green ≥80, amber 60-79, red <60)
- Source channel badge
- Near-miss flag callout (if true): "Near miss — scored ≥70 but missed a must-have requirement"

*AI Riya badge* above justification text

*Justification:* Multi-sentence paragraph from LLM output

*Dimension breakdown (horizontal bar chart):*
```
Must-Have    ████████░░  82 / 100
Experience   ██████░░░░  61 / 100
Skills       ███████░░░  71 / 100
Nice-to-have █████░░░░░  54 / 100
Trajectory   ████░░░░░░  43 / 100
```

*Criteria met table:*
| Criterion | Met? | Confidence |
| 5+ yrs Python | ✅ Yes | High |
| AWS certified | ❌ No | — |

*Strengths (green bullets) + Risks (amber bullets)*

*Recruiter actions (sticky bottom bar):*
```
[👍 Approve]  [⏸ Hold]  [👎 Reject]    [⭐ Thumb up / down NPS]
```
- After status set: badge updates, next candidate auto-selected
- Override score: expandable "Override score" section → score slider + required reason text

*Shortlist justification doc (collapsible, at top of right panel):*
Shown once, covers the whole shortlist — summary, interview questions, diversity note.

**Export bar (top right):**
- "Export PDF" | "Export CSV" | "Copy share link" (generates time-limited read-only URL)

**Bias audit banner (if failed):**
```
⚠️  Bias audit flagged: female candidates are under-represented
in this shortlist vs. the applicant pool (−28 pp). Review with care.
```

**API:**
```
GET  /api/v1/jobs/:id/shortlist                         → ShortlistEntry[]
PATCH /api/v1/shortlist/:score_id
  Body: { recruiter_status, nps_thumb, override_score?, override_reason? }
```

---

### 8. `/jobs/[id]/audit` — Audit Trail

**Layout:** Timeline list, newest first.

**Each event:**
- Event type label (colour-coded: blue=info, green=success, amber=warning, red=error)
- Timestamp (relative + absolute on hover)
- Entity type + ID
- Data payload (collapsible JSON viewer — use `react-json-view` or simple pre block)
- Content hash (if disclosure-bearing event): short truncated hash with copy button

**Filter:** Event type multi-select

**API:**
```
GET /api/v1/jobs/:id/audit   → AuditEvent[]
```

---

### 9. `/analytics` — Analytics Dashboard

**KPI cards row:** Total applications (all time) | Shortlist rate | Avg NPS | Active jobs

**Charts (Recharts):**

1. **Applications over time** (AreaChart, 30-day rolling) — stacked by channel
2. **Score distribution** (BarChart) — histogram of composite_score across all candidates
3. **Channel attribution** (PieChart) — LinkedIn vs Email vs Other
4. **Shortlist NPS over time** (LineChart) — thumbs up % by week

**API:**
```
GET /api/v1/analytics/dashboard   → DashboardStats
```
(Charts use the same endpoint for MVP; break out per-chart endpoints in Phase 2)

---

### 10. `/settings/personas` — Persona Health (Admin only)

**Layout:** Card per persona account.

**Card content:**
- Persona name + LinkedIn handle
- Health status: large coloured dot + label (Healthy / Warning / Banned)
- Posts today / daily limit (3)
- Last post timestamp
- Last health check timestamp
- "Run health check" button → POST /api/v1/personas/:id/check (stub for now)

**Warning state (yellow):** amber border, "Account showing signs of reduced reach. Monitor closely."
**Banned state (red):** red border, "Account restricted. Failover to backup persona initiated."

**API:**
```
GET /api/v1/personas/health   → PersonaAccount[]
```

---

### 11. `/share/[token]` — Public Shortlist View (no login)

**Purpose:** Hiring manager receives link via email (time-limited JWT), can view shortlist without creating an account.

**Layout:** Clean, minimal — no sidebar. HireFlow logo + "Powered by Riya AI" footer.

**Content:**
- Job title + company name
- Shortlist table: Rank | Score | Strengths | Risks (name hidden)
- Justification document (read-only)
- Interview questions panel
- "This view expires on [date]" notice
- Bias audit status badge

**No actions** — read-only. Recruiter must log in to approve/reject.

**API:**
```
GET /api/v1/share/:token   → { job: Job (partial), shortlist: ShortlistEntry[] (anonymised) }
```
(This endpoint is not yet built — add to Phase 1 backlog)

---

## Navigation / Layout Component

```
Sidebar:
  [HireFlow logo]
  [Riya AI status dot — green/yellow/red]
  ──────────────
  Dashboard        /
  Jobs             /jobs
  Analytics        /analytics
  ──────────────
  Personas         /settings/personas  (admin only)
  ──────────────
  [User avatar]
  [Name + role]
  [Sign out]
```

Topbar (inside main content):
- Breadcrumb navigation
- Notification bell (future — show bias audit alerts)
- "New Job" shortcut button

---

## Key UX Rules

1. **Always show the Riya AI badge** next to any AI-generated text (JD extraction, justification, post draft). Never let users mistake AI output for human-written content.
2. **Recruiter is always in control.** No action (post, score, shortlist) happens without an explicit button click. Loading states show what Riya is doing, not what "the system" is doing.
3. **Bias audit is always visible.** Never hide the bias audit result. Show it on the shortlist page even when it passes.
4. **Disclosure is verifiable.** On the Distribution tab, show a green "✓ AI disclosure present in post" or red "✗ Missing" badge — never let a recruiter approve a post without seeing this.
5. **Karnataka salary warning is a blocker.** The "Confirm & Approve" button is disabled (with tooltip) until salary range is filled in if the job is in Karnataka.
6. **Empty states are actionable.** Every empty state has a clear next-step CTA, not just "No data".
7. **Mobile-first for the shortlist page.** Hiring managers often review shortlists on phones. The shortlist right panel should be a bottom sheet on mobile.

---

## Component Generation Order (recommended for Claude.ai sessions)

Generate in this order — each builds on the previous:

1. Design system tokens + layout shell (sidebar + topbar) — ask Claude to make this reusable
2. Dashboard page (uses KPI cards + job table + alert sidebar)
3. Jobs list page
4. Create job page (2-step form with bias flag UI)
5. JD Review tab (editable structured fields + rubric sliders)
6. Applications list
7. Shortlist page (most complex — two-panel, score charts, action bar)
8. Audit trail timeline
9. Analytics page (charts)
10. Persona health page
11. Login page
12. Public share page

---

## Claude.ai Prompt Template (copy-paste for each page)

```
Context: I'm building HireFlow AI, an AI hiring agent for Indian SMBs.
Tech stack: Next.js 14 App Router, Tailwind CSS, shadcn/ui, Recharts, TanStack Query.
Design system: Inter font, primary #1a56db, accent #6c2bd9, success #057a55,
warning #c27803, danger #c81e1e. Cards: rounded-xl border shadow-sm.

[Paste the relevant page spec section from this document]

Generate the complete React component with:
- Realistic mock data (use plausible Indian names, roles, companies)
- All states shown: loading skeleton, data loaded, empty state
- Responsive (mobile + desktop)
- shadcn/ui components where applicable (Button, Card, Badge, Table, Tabs, etc.)
- TypeScript types matching the interfaces in the spec
- No external API calls — use the mock data directly

Show the full component code in the artifact.
```

---

## Deployment Plan

### Frontend (Vercel)
```
# Install Vercel CLI
npm i -g vercel

# From hireflow-frontend/ directory
vercel deploy --prod

# Environment variables to set in Vercel dashboard:
NEXT_PUBLIC_API_URL=https://api.hireflow.in
NEXTAUTH_SECRET=<random 32-char string>
NEXTAUTH_URL=https://app.hireflow.in
```

### API (existing Docker stack)
- Add Caddy or nginx reverse proxy in front of FastAPI
- Set `CORS_ORIGINS=https://app.hireflow.in` in `.env`
- `make up` on the production server

### Secure share link (to implement)
```python
# In apps/api/routers/jobs.py — add:
GET /api/v1/share/{token}
# token = jose.jwt.encode({"job_id": ..., "exp": now+72h}, SHARE_SECRET)
# Returns partial job + anonymised shortlist, no auth header required
```

---

## Testing Plan (Phase 1 exit criteria)

### Unit tests (pytest)
| Module | Tests |
|---|---|
| `pii_guard.py` | Email, phone, DOB, gender marker patterns; `assert_clean()` raises on PII |
| `disclosure.py` | `validate_linkedin_post_disclosure()` returns False on missing disclosure; `assert_` raises |
| `rubric.py` | Weights sum to 1.0; `apply_rubric()` matches expected composite; `validate_rubric()` catches bad input |
| `bias_audit.py` | `infer_gender()` correct for male/female/unknown; `run_bias_audit()` flags >20pp disparity; passes with <5 candidates |
| `scorer.py` | `_normalise()` sets near_miss_flag correctly; composite recalculated from rubric |
| `extractor.py` (JD) | `requires_salary_disclosure()` returns True for Karnataka; False for Maharashtra |

### Integration tests (pytest + TestClient)
| Endpoint | Test |
|---|---|
| `POST /jobs` | Returns 202 + job_id; job in DB with status=draft |
| `POST /jobs/:id/confirm` | Transitions draft→approved; returns 400 if already approved |
| `POST /jobs/:id/distribute` | Returns 400 if not approved; publishes to bus if approved |
| `POST /jobs/:id/score` | Returns 202; job status updated to scoring |
| `PATCH /shortlist/:id` | Override requires reason; logs SCORE_OVERRIDE event |
| `GET /health` | DB + Redis both checked; returns 200 |

### End-to-end smoke test (manual)
```
1. POST /jobs (paste a real JD) → verify extraction_complete
2. POST /jobs/:id/confirm → status=approved
3. POST /jobs/:id/distribute (channels=["linkedin"]) → status=posted
4. Manually trigger parse for a test CV via POST /jobs/:id/score
5. GET /jobs/:id/shortlist → verify scores returned
6. PATCH /shortlist/:id (recruiter_status=approved) → verify audit event
7. GET /jobs/:id/audit → verify complete trail
```

### CV parsing accuracy test
```python
# tests/unit/test_parsing_accuracy.py
# Load 500 CVs from tests/fixtures/cvs/
# Run extract_profile() on each
# Compare against ground-truth JSON in tests/fixtures/cvs/ground_truth/
# Assert: field_accuracy > 0.90 across experience, education, skills_hard
# Assert: no PII leaks (assert_clean on all LLM inputs)
```

---

*Last updated: 2026-05-09*
*Status: Ready for frontend generation + Phase 1 testing*
