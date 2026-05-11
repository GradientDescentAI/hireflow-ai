# HireFlow AI v2.0 — System Architecture

## 1. Three-Tier Structure

```
┌─────────────────────────────────────────────────────────────┐
│  PERSONA LAYER                                              │
│  Riya identity · voice rules · disclosure enforcement ·    │
│  account management · health monitoring · failover logic    │
└─────────────────────────────────────────────────────────────┘
              ↕  shared persona context
┌─────────────────────────────────────────────────────────────┐
│  MODULE LAYER                                               │
│  ┌────────────────────┐   ┌────────────────────┐           │
│  │  Hiring Core v2.0  │   │  HR Ops v3.0 (TBD) │           │
│  │  (this PRD)        │   │  (future plug-in)  │           │
│  └────────────────────┘   └────────────────────┘           │
└─────────────────────────────────────────────────────────────┘
              ↕  shared services APIs
┌─────────────────────────────────────────────────────────────┐
│  SHARED SERVICES                                            │
│  Orchestrator · LLM Abstraction · Audit Log · Secrets      │
│  Vault · Notification Service · Multi-tenant Data Store    │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Hiring Core Agent Pipeline (DAG)

```
Recruiter Input (JD text / .docx / .pdf / URL)
        │
        ▼
┌──────────────────┐
│  JD Intake Agent │  LLM extract → structured JSON → recruiter confirms → scoring rubric
└──────────────────┘
        │
        │  JobDescription schema (approved)
        ▼
┌─────────────────────────────┐
│  Distribution Orchestrator  │  LangGraph parent node; fans out to channel sub-agents in parallel
└─────────────────────────────┘
   │      │      │       │         │         │
   ▼      ▼      ▼       ▼         ▼         ▼
[LI]  [WA]   [TG]   [JobBoard]  [College]  [Referral]
  │      │      │       │         │         │
  └──────┴──────┴───────┴─────────┴─────────┘
        │  ChannelPost records → audit log
        │
        ▼
┌──────────────────────┐
│  Collection Agent    │  IMAP IDLE per role inbox → extract CV files + metadata
└──────────────────────┘
        │  raw CV files (S3) + CandidateProfile stubs
        ▼
┌──────────────────┐
│  Parsing Agent   │  PDF/DOCX → CandidateProfile JSON; PII anonymised before LLM call
└──────────────────┘
        │  structured profiles
        ▼
┌──────────────────┐
│  Scoring Agent   │  LLM T=0 · 5 dimensions · reproducible · per-criterion explanations
└──────────────────┘
        │  CandidateScore records
        ▼
┌────────────────────┐
│  Evaluation Agent  │  top-N shortlist · justifications · strengths · risks · bias audit
└────────────────────┘
        │  ranked shortlist
        ▼
┌──────────────────┐
│  Delivery Agent  │  email + WhatsApp notification · dashboard update · ATS push (GA)
└──────────────────┘
        │
        ▼
  Recruiter Dashboard (approve / reject / hold / NPS thumb)
```

---

## 3. Directory Structure

```
hireflow/
├── apps/
│   ├── api/                        # FastAPI — REST endpoints + webhook emitter
│   ├── dashboard/                  # Next.js 14 — recruiter UI
│   └── worker/                     # Agent worker process (LangGraph runtime)
│
├── packages/
│   ├── persona/                    # Riya: identity config, voice rules, disclosure
│   │   ├── identity.py             # Name, tone, pronouns, tagline constants
│   │   ├── disclosure.py           # PE-001 to PE-007 enforcement helpers
│   │   ├── voice.py                # System prompt builder for every LLM call
│   │   └── account_manager.py     # LinkedIn health check, failover logic
│   │
│   ├── agents/
│   │   ├── jd_intake/
│   │   │   ├── agent.py            # LangGraph node
│   │   │   ├── extractor.py        # LLM → JobDescription JSON
│   │   │   ├── rubric.py           # Scoring weight calculator
│   │   │   └── prompts/            # Versioned prompt templates
│   │   │
│   │   ├── distribution/
│   │   │   ├── orchestrator.py     # Parallel fan-out, status aggregation
│   │   │   ├── linkedin/
│   │   │   │   ├── agent.py
│   │   │   │   ├── browser.py      # Playwright session, proxy, anti-detection
│   │   │   │   ├── post_builder.py # 8-section template + disclosure
│   │   │   │   └── health.py       # Account health monitor
│   │   │   ├── whatsapp/
│   │   │   │   ├── agent.py
│   │   │   │   ├── path_a.py       # Playwright / WhatsApp Web
│   │   │   │   └── path_b.py       # Gupshup/Wati Business API
│   │   │   ├── telegram/
│   │   │   │   └── agent.py        # python-telegram-bot
│   │   │   ├── job_boards/
│   │   │   │   ├── naukri.py       # Playwright automation
│   │   │   │   └── indeed.py       # Publisher API
│   │   │   ├── colleges/
│   │   │   │   ├── agent.py
│   │   │   │   ├── db.py           # 500+ placement contact store
│   │   │   │   └── email_builder.py
│   │   │   └── referral/
│   │   │       └── agent.py
│   │   │
│   │   ├── collection/
│   │   │   ├── agent.py            # LangGraph node
│   │   │   ├── imap_listener.py    # IMAP IDLE + fallback polling
│   │   │   ├── extractor.py        # Subject routing, attachment extraction
│   │   │   ├── dedup.py
│   │   │   └── acknowledger.py     # SendGrid ack emails with disclosure
│   │   │
│   │   ├── parsing/
│   │   │   ├── agent.py
│   │   │   ├── pdf_parser.py       # pdfplumber + OCR fallback (pytesseract)
│   │   │   ├── docx_parser.py      # python-docx
│   │   │   ├── llm_extractor.py    # Structured output → CandidateProfile
│   │   │   └── anonymiser.py       # PII strip before LLM call
│   │   │
│   │   ├── scoring/
│   │   │   ├── agent.py
│   │   │   ├── scorer.py           # 5-dimension LLM scoring, T=0
│   │   │   ├── vector_similarity.py # pgvector experience match
│   │   │   └── bias_audit.py       # Demographic distribution check
│   │   │
│   │   ├── evaluation/
│   │   │   ├── agent.py
│   │   │   └── shortlist_builder.py # top-N · justifications · strengths/risks
│   │   │
│   │   └── delivery/
│   │       ├── agent.py
│   │       ├── email_sender.py     # SendGrid shortlist notification
│   │       └── dashboard_pusher.py # WebSocket push to UI
│   │
│   ├── llm/
│   │   ├── client.py               # Provider abstraction (OpenAI / Anthropic)
│   │   ├── router.py               # Stage → model selection (mini vs full)
│   │   ├── prompt_registry.py      # Version-controlled prompt store
│   │   └── pii_guard.py            # Strip PII before any external LLM call
│   │
│   ├── audit/
│   │   ├── logger.py               # Immutable append-only writer
│   │   └── models.py               # AuditEvent schema
│   │
│   ├── vault/
│   │   └── client.py               # HashiCorp Vault / AWS SM abstraction
│   │
│   └── db/
│       ├── models.py               # SQLAlchemy ORM models
│       ├── schemas.py              # Pydantic request/response schemas
│       └── migrations/             # Alembic migrations
│
├── infra/
│   ├── docker-compose.yml          # MVP local + staging
│   ├── Dockerfile.api
│   ├── Dockerfile.worker
│   └── terraform/                  # AWS Mumbai (ap-south-1) — GA
│
└── tests/
    ├── unit/
    ├── integration/
    └── fixtures/
        ├── cvs/                    # 500-CV Indian test set
        └── jds/                    # Sample JDs
```

---

## 4. Data Flow & Schemas

### 4.1 Core Schemas (versioned JSON contracts)

| Schema | Key Fields | Owner Agent |
|---|---|---|
| `JobDescription` | id, tenant_id, title, location, seniority, must_haves, nice_to_haves, scoring_rubric, distribution_channels, status | JD Intake |
| `ChannelPost` | id, jd_id, channel, post_url, posted_at, disclosure_included, delivery_status, metrics | Distribution |
| `CandidateProfile` | id, jd_id, source_channel, contact, experience, education, skills, parse_confidence, pii_anonymised, consent | Parsing |
| `CandidateScore` | id, candidate_id, composite_score, dimension_scores, criteria_met, justification, strengths, risks, bias_audit_passed | Scoring |

### 4.2 Message Bus Topics (Redis Streams — MVP)

```
hireflow.jd.approved          → Distribution Orchestrator
hireflow.channel.{channel}.posted → Audit + Dashboard
hireflow.application.received  → Parsing Agent
hireflow.cv.parsed             → Scoring Agent
hireflow.scoring.complete      → Evaluation Agent
hireflow.shortlist.ready       → Delivery Agent + Webhook
hireflow.persona.alert         → Ops notification
hireflow.agent.error           → Dead-letter + alerting
```

---

## 5. Infrastructure (MVP → GA)

| Component | MVP (Month 1-3) | GA (Month 7-9) |
|---|---|---|
| Compute | Docker Compose on single VPS (India region) | ECS Fargate / K8s (ap-south-1) |
| Orchestrator | LangGraph (in-process) | LangGraph + Temporal for durable workflows |
| Database | PostgreSQL 16 + pgvector (single node) | RDS Multi-AZ (ap-south-1) |
| Queue | Redis 7 (single node) | ElastiCache Redis cluster |
| Object Store | MinIO (local) | AWS S3 (ap-south-1) |
| Email inbound | IMAP IDLE on Gmail-hosted domain | Same + Gmail API push |
| Email outbound | SendGrid | SendGrid (India IP pool) |
| Secrets | .env + manual rotation | HashiCorp Vault / AWS Secrets Manager |
| Browser | Playwright + residential proxy | Same — headless on dedicated EC2 |
| Monitoring | Structlog + basic dashboards | OpenTelemetry → Grafana |
| Vector DB | pgvector | pgvector (MVP), Pinecone (v2.1) |

---

## 6. Security Architecture

```
Recruiter (browser)
    │  HTTPS / TLS 1.3
    ▼
API Gateway (JWT + RBAC)
    │
    ├── Rate limit: 1,000 req/min per tenant
    ├── CORS locked to dashboard domain
    └── Request-ID header on every response

Data stores:
    PostgreSQL    → AES-256 at rest (RDS encryption or LUKS)
    S3/MinIO CVs  → AES-256 at rest, per-tenant prefix isolation
    Redis         → TLS in transit, no PII in cache

PII flow:
    Raw CV (S3)
        │ Parsing Agent reads
        │ Anonymiser strips name/photo/gender/age signals
        ▼
    Anonymised text → LLM API (no PII leaves system)
    Structured profile (with PII) → PostgreSQL encrypted store only

Secrets:
    LinkedIn creds / email passwords / API keys → Vault
    Never in environment variables beyond local dev
    Never in logs

Audit log:
    Append-only PostgreSQL table (WORM semantics via trigger)
    Every disclosure-bearing message: channel, timestamp, content hash
    Every score, override, agent error
    7-year retention
```

---

## 7. LinkedIn Account Resilience

```
Normal operation:
  Riya account → residential India IP → max 3 posts/day
                                       → 90-min spacing
                                       → 09:00-19:00 IST window
                                       → NO engagement automation

Health monitor (daily cron):
  ├── Login success check
  ├── Post impression trend (sudden 0 → flag)
  ├── Profile restriction scan
  └── Anomaly → operator alert within 1 hour

On restriction / CAPTCHA:
  └── Freeze account → failover to backup persona within 4 hours
                    → migrate active posts to backup account
                    → notify affected customers

Backup pool:
  Minimum 2 aged accounts (>30 days) ready per region
```

---

## 8. LLM Routing

| Pipeline Stage | Model | Reason |
|---|---|---|
| JD extraction | GPT-4o-mini | Structured output, low cost |
| Post draft (LinkedIn/WA/TG) | GPT-4o-mini | Template-guided, cheap |
| CV parsing extraction | GPT-4o-mini | High volume, structured output |
| Candidate scoring | GPT-4o | Reasoning quality matters |
| Shortlist justifications | Claude Sonnet (Pro tier) / GPT-4o | Explainability quality |
| Bias audit | GPT-4o | Sensitive — better reasoning |

Rules:
- Temperature = 0 for scoring (reproducibility — SC-001)
- All prompts version-controlled in `prompt_registry`
- PII stripped before every external call (`pii_guard.py`)
- Model version pinned per tenant for scoring consistency

---

## 9. Multi-Tenant Isolation

```
tenant_id is a required column on every data table.
Row-level security enforced at PostgreSQL level.
S3 objects namespaced: /{tenant_id}/{role_id}/...
Redis keys prefixed: {tenant_id}:{domain}:...
Agent workers receive tenant context at job start; never cross tenant boundaries.
Automated isolation tests run on every release (scalability requirement).
```

---

## 10. API Surface

REST JSON over HTTPS. Bearer JWT. Rate-limit 1,000 req/min per tenant.

**Core endpoints:**
```
POST   /api/v1/jobs                          Create job (trigger JD Intake)
GET    /api/v1/jobs/{id}                     Job state + channel status
POST   /api/v1/jobs/{id}/distribute          Trigger Distribution Orchestrator
GET    /api/v1/jobs/{id}/posts               All ChannelPost records
GET    /api/v1/jobs/{id}/applications        Applications (filterable)
POST   /api/v1/jobs/{id}/score               Trigger Scoring (async)
GET    /api/v1/jobs/{id}/shortlist           Ranked shortlist + scores
PATCH  /api/v1/shortlist/{score_id}          Approve/reject/hold + NPS
GET    /api/v1/jobs/{id}/audit               Full audit trail
GET    /api/v1/personas/health               LinkedIn/WA account health (ops)
GET    /api/v1/analytics/dashboard           Portfolio metrics
```

**Webhook events:** `job.distributed`, `channel.post.failed`, `application.received`,
`scoring.complete`, `shortlist.ready`, `bias_audit.flagged`,
`persona.account.warning`, `persona.account.banned`, `agent.error`
