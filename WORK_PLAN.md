# HireFlow AI v2.0 — Implementation Work Plan

## Phase 0 — Foundation (Week 1-2)

**Goal:** Skeleton runs. Database up. Agents can talk to each other.

| Task | Description | Priority |
|---|---|---|
| Repo scaffold | `hireflow/` monorepo, `apps/` + `packages/` layout, Docker Compose | P0 |
| DB schema + migrations | All core tables: tenants, jobs, candidates, scores, channel_posts, audit_log | P0 |
| LLM abstraction layer | `packages/llm/`: client, router, prompt_registry, pii_guard | P0 |
| Secrets vault client | `packages/vault/client.py` wrapping env-based config (MVP) → Vault (GA) | P0 |
| Audit logger | Append-only writer, AuditEvent schema, WORM trigger on PostgreSQL | P0 |
| Redis Streams bus | Topic constants, publisher/consumer helpers | P0 |
| LangGraph worker shell | `apps/worker/` — empty graph, node registration, checkpoint store | P0 |
| FastAPI skeleton | `apps/api/` — auth middleware (JWT), tenant context, health endpoint | P0 |
| Persona constants | `packages/persona/identity.py`, `disclosure.py`, `voice.py` | P0 |

**Exit criteria:** `docker compose up` → API returns 200, worker connects to DB and Redis.

---

## Phase 1 — MVP Core Pipeline (Week 3-8)

### 1A: JD Intake Agent (Week 3)

| Task | Key decisions |
|---|---|
| File ingestion (text / PDF / DOCX / URL) | Use `pdfplumber` for PDF, `python-docx` for DOCX, `httpx` + html2text for URL |
| LLM extraction → JobDescription JSON | Structured output mode (response_format); prompt in `prompt_registry` |
| Bias language detector | LLM side-call; flag gendered/age-coded terms; suggest alternatives (JD-006) |
| Scoring rubric generator | Default weights from schema; recruiter-editable before distribution |
| Confirmation UI contract | API returns draft JD; frontend renders inline-edit form; `PATCH /api/v1/jobs/{id}` saves edits; POST `/distribute` only available post-confirm |
| Karnataka salary enforcement | State detection on location field → block distribute if salary missing (JD-007) |

### 1B: Persona + LinkedIn Agent (Week 4-5)

| Task | Key decisions |
|---|---|
| LinkedIn Playwright session | Single residential India proxy per account; session token in vault; IMAP IDLE checks before each action |
| Anti-detection patterns | Randomise typing delays, scroll behaviour, viewport; human-like timing |
| Post builder (8-section template) | Disclosure within first 200 chars enforced in code, not just prompt (PE-001) |
| Recruiter approval gate | API: `POST /api/v1/jobs/{id}/distribution/linkedin/draft` → returns preview; `POST /approve` triggers post; no auto-post path exists |
| MFA / CAPTCHA handler | Playwright detects challenge → pause → alert operator via webhook; resume on operator ack |
| Post cadence enforcer | Redis counter per Riya account per day; 90-min spacing via scheduled queue |
| Health monitor | Daily cron: login check, impression trend, restriction scan; anomaly → webhook |
| Audit on every post | `ChannelPost` record + screenshot stored in S3 + audit log entry |

### 1C: Application Collection Agent (Week 5-6)

| Task | Key decisions |
|---|---|
| Inbox provisioning | On `job.distributed` event: create `apply-{role_id}@hireflow.in` alias via email provider API |
| IMAP IDLE listener | Per-role listener; fallback 5-min polling; reconnect on disconnect |
| Subject routing | Case-insensitive partial match on `APPLY-{ROLE_ID}`; non-match → quarantine table |
| Attachment extraction | PDF/DOCX only; max 10MB; max 3; store at `/{tenant_id}/{role_id}/{email}/{ts}/cv.{ext}` |
| Deduplication | Hash (sender_email + role_id) → flag duplicates; retain original |
| Acknowledgement email | SendGrid; 5-min SLA; role title + reference + AI disclosure footer (PE-003) |
| Missing-attachment handler | Trigger resubmission request email if no valid attachment found (AC-008) |

### 1D: Parsing Agent (Week 6)

| Task | Key decisions |
|---|---|
| PDF parser | `pdfplumber` → text; `pytesseract` OCR fallback for scanned CVs |
| DOCX parser | `python-docx`; preserve structure |
| PII anonymiser | Strip name, photo, phone, email from text before LLM call; keep in DB, never in prompt |
| LLM structured extraction | → `CandidateProfile` JSON; structured output mode |
| Confidence scoring | Per-field confidence; composite < 0.6 → flag for recruiter review (RP-004) |
| Indian CV test set | 500-CV fixture set in `tests/fixtures/cvs/`; accuracy CI gate > 90% |

### 1E: Scoring Agent (Week 7)

| Task | Key decisions |
|---|---|
| 5-dimension scorer | Must-have (40%), Experience (25%), Skills (20%), Nice-to-have (10%), Trajectory (5%) |
| Reproducibility | Temperature=0; model version pinned per tenant; same input → same output (SC-001) |
| Experience relevance | pgvector cosine similarity between candidate experience embeddings and JD responsibilities |
| Criteria-level explanations | Per must-have: met/not-met + confidence; output in `criteria_met` array (SC-002) |
| Bias audit | Name-inferred gender distribution check on shortlist vs. applicant pool; flag if disparity > threshold (SC-008) |
| Recruiter override | `PATCH /api/v1/shortlist/{score_id}` with `override_reason`; logged to audit |
| Throughput target | 200 CVs in < 5 minutes → async batch job; progress pushed via WebSocket |

### 1F: Evaluation + Delivery + Dashboard (Week 8)

| Task | Key decisions |
|---|---|
| Shortlist builder | top-N (default 10); justification (2-4 sentences); strengths (3-5 bullets); risks (1-3 bullets) |
| Shortlist UI | Sort by dimension; filter by score; side-by-side comparison; thumbs NPS; approve/reject/hold |
| Export | PDF (formatted), CSV (raw), WhatsApp share message |
| Secure share link | Time-limited read-only JWT → hiring manager view (no login required) (SL-007) |
| Delivery notifications | SendGrid email + (placeholder) WhatsApp on shortlist ready |
| Recruiter dashboard | Active roles list; status pipeline; system alerts; audit trail view |

---

## Phase 2 — Beta Channels (Month 4-6)

Order of addition:

1. **Telegram Agent** — official Bot API, zero ToS risk, quick win
2. **Naukri Agent** — Playwright automation (highest Indian SMB reach)
3. **Indeed Agent** — Publisher API (officially supported)
4. **WhatsApp Group Agent (Path A)** — Playwright + per-customer session
5. **College Outreach Agent** — 500+ placement contact DB, SendGrid bulk
6. **Referral Network Agent** — past-candidate re-engagement

Additional Beta work:
- Multi-tenant RBAC (Recruiter / Hiring Manager / Admin)
- Backup Riya account pool + failover drill
- Anonymised parsing mode (RP-006)
- Application channel attribution dashboard (DB-004)
- Live application counter (AC-009)

---

## Phase 3 — GA (Month 7-9)

All P0 + P1 requirements. Key additions:

- WhatsApp Business API (Gupshup/Wati) — Pro tier Path B
- MSG91 SMS integration
- Keka HRMS ATS push
- Internshala + Hirect job board agents
- QoH dashboard (Tier 1-4 composite)
- India data residency confirmation (all infra in ap-south-1)
- Third-party pen test
- DPDP Act compliance sign-off

---

## Phase 4 — v2.1 (Month 10-12)

- Multi-persona regional accounts (Anjali — South India)
- Configurable scoring weights per role
- Greenhouse / Lever ATS integrations
- pgvector → Pinecone migration path
- WhatsApp-bot apply flow (replace email CTA)
- Pure Hindi JD support

---

## Non-Negotiables (apply to every sprint)

- **No copy-paste fallback.** If automation fails, the channel is skipped and the recruiter is notified. Degraded manual path is never built.
- **Disclosure is not configurable.** PE-001 to PE-007 enforced in code, not prompt alone.
- **PII never reaches LLM APIs.** `pii_guard.py` is called at the package boundary; tests assert it.
- **All agent actions are idempotent.** Retrying a failed node never duplicates an output.
- **Audit log is append-only.** No UPDATE or DELETE ever touches the audit table.
- **Recruiter is always in the loop.** LinkedIn posts require explicit "Approve & Post" click. Scoring requires recruiter shortlist review. System recommends; human decides.

---

## MVP Definition of Done (Month 3 exit criteria)

- [ ] 10 roles posted end-to-end (JD → LinkedIn post → email collection → shortlist)
- [ ] Shortlist NPS > 60% positive (Tier 1 QoH)
- [ ] LinkedIn account stable for 90 consecutive days
- [ ] Parsing accuracy > 90% on 500-CV Indian test set
- [ ] 200 CVs scored in < 5 minutes
- [ ] Every posted role has disclosure in first 200 chars of LinkedIn body
- [ ] Audit log captures every disclosure-bearing message
- [ ] 5 design-partner SMBs actively using the product
