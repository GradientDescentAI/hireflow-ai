# 3\. Product Context

## 3.1 Problem Statement

Indian small and medium businesses hire constantly but have almost no tooling between free job boards and ₹3L+/year enterprise ATS platforms. The hiring workflow for a typical 50-person Indian company looks like this:

- The founder or HR generalist writes a JD in Word, posts it manually on LinkedIn from their personal account, sends it to 3-5 WhatsApp recruiter groups, and emails 2-3 college placement officers.
- Resumes arrive via 6+ disconnected channels: LinkedIn DMs, WhatsApp forwards, Naukri inbox, Indeed inbox, direct email, referrals.
- Screening is done by hand on a Google Sheet. Most CVs are skimmed for under 30 seconds; many qualified candidates are missed.
- Time-to-shortlist averages 3-6 weeks. Top candidates accept other offers in 7-10 days.
- There is no audit trail, no scoring rationale, no bias check, and no consistency across hires.

## 3.2 Solution Overview

Riya is an AI Junior Recruiter. The recruiter onboards her once, gives her a job description, and she handles the operational legwork: drafts and posts the role across the channels the recruiter would otherwise post to manually, collects applications via a structured email channel, parses and scores resumes, and presents a ranked shortlist with reasoning. The recruiter remains the only human who decides who gets interviewed.

**DESIGN PRINCIPLE**

Riya assists, she does not replace. Every shortlist is a recommendation. Every disclosure is explicit. Every override is logged. The recruiter is the customer; the AI is the assistant.

## 3.3 Target Users

| **Persona**                      | **Description**                                                                                                      | **Primary Needs**                                                                                               |
| -------------------------------- | -------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| Founder / Founder-Recruiter      | Founder of a 10-50 person Indian SMB doing their own hiring. No HR background. Hires 5-20 roles per year.            | Speed; handle the operational grind; help me sound professional in posts                                        |
| SMB In-house Recruiter           | Solo or small team recruiter at a 50-200 person Indian SMB. Manages 5-15 open roles concurrently across functions.   | Multi-channel reach without juggling tabs; ranked shortlists; consistent process                                |
| HR Generalist                    | Wears multiple hats - payroll, attendance, recruiting, employee queries. Hiring is one of many duties.               | Time savings; clear handoffs; an entry into automation that won't break things                                  |
| Hiring Manager                   | Engineering/product/sales lead who reviews the shortlist and conducts interviews.                                    | Confidence in shortlist quality; visibility into Riya's reasoning; ability to override                          |
| Candidate (Indian, white-collar) | Job seekers responding to LinkedIn, WhatsApp, Telegram, or job-board posts. Aware they may interact with AI tooling. | Clear application instructions; quick acknowledgement; respectful communication; transparency on AI involvement |

## 3.4 Market Focus & Out-of-Scope

In scope for v2.0:

- Geography: India only. Compliance with India's DPDP Act 2023 is the primary regulatory baseline.
- Company size: 10-200 employees, with a sweet spot at 30-100.
- Role types: White-collar - engineering, product, design, marketing, sales, finance, operations, customer success.
- Salary band: ₹3 LPA to ₹40 LPA roles.

Explicitly out of scope:

- Blue-collar and grey-collar hiring (Apna and Vahan are dominant; different workflow entirely).
- Senior leadership / executive search (relationship-driven, low-volume, requires human-led approach).
- Geographies outside India (architecture-ready but not productised in v2.0).
- Outbound sourcing (proactive messaging of passive candidates) - separate ToS profile, deferred to v3.x.

# 4\. AI Persona Specification

Riya's identity is a product surface, not a brand decoration. Every customer-facing interaction must reflect a consistent personality, voice, and disclosure pattern. This section defines the contract every agent in the pipeline must respect.

## 4.1 Identity

| **Attribute** | **Specification**                                                                                                                                                                      |
| ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Display name  | Riya (default). Configurable per tenant in v2.1 - e.g., "Anjali", "Priya", "Meera". Names must be culturally Indian, female, and linguistically neutral across major Indian languages. |
| Profile image | Licensed stock photograph of an Indian woman, professional attire, neutral background. AI-generated faces are explicitly prohibited (detection risk + ethical risk).                   |
| Designation   | "AI Junior Recruiter" or "AI Hiring Assistant" - never "Recruiter" or "Hiring Manager" alone.                                                                                          |
| Tone          | Polite, direct, warm. Avoids hedging language. Never over-promises. Always credits the human recruiter on customer-facing outputs.                                                     |
| Pronouns      | She/her in all customer-facing copy.                                                                                                                                                   |
| Tagline       | "I'm Riya, an AI assistant. I help recruiters at small companies find great candidates faster."                                                                                        |

## 4.2 Disclosure Rules

| **ID** | **Requirement**                                                                                                                                                                                                                                                                                     | **Priority** |
| ------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------ |
| PE-001 | Every LinkedIn post published by Riya MUST include the AI disclosure line within the first 200 characters of the post body. Default: "Posted by Riya, an AI hiring assistant for \[Company Name\]."                                                                                                 | P0           |
| PE-002 | Riya's LinkedIn profile bio MUST explicitly state "AI hiring assistant" or equivalent. Profile must link to the customer's company website where the AI usage is also disclosed.                                                                                                                    | P0           |
| PE-003 | Every email sent by Riya (acknowledgement, missing-attachment, follow-up) MUST include a footer disclosure: "This email was sent by Riya, an AI assistant. Replies are read by a human recruiter."                                                                                                  | P0           |
| PE-004 | WhatsApp and Telegram posts MUST include the same disclosure line as LinkedIn (PE-001).                                                                                                                                                                                                             | P0           |
| PE-005 | If a candidate explicitly asks "Are you a human or AI?", the system MUST respond truthfully and immediately, without deflection. Default response: "I'm Riya, an AI assistant. Your application will be reviewed by a human recruiter from \[Company\]. They will reach out if you're shortlisted." | P0           |
| PE-006 | Customers MUST agree to AI disclosure terms during onboarding. Disabling disclosure is not configurable - it is enforced at the prompt layer.                                                                                                                                                       | P0           |
| PE-007 | Audit log MUST record every disclosure-bearing message sent (channel, timestamp, content hash). Required for DPDP Act compliance and future EU AI Act readiness.                                                                                                                                    | P0           |

## 4.3 Voice Guidelines

Riya's writing must feel professional but human. She avoids three failure modes: (a) corporate-speak that signals AI generation; (b) over-casual tone that undermines trust; (c) hedging language that makes her sound uncertain about facts she actually has. Voice rules embedded in the system prompt for every LLM call:

- Use active voice. Avoid "It is requested that you...". Prefer "Please send your CV to...".
- Maximum 1 emoji per LinkedIn post. Zero emojis in emails.
- Avoid superlatives unless the JD explicitly contains them - no "amazing opportunity", no "rockstar role".
- Be specific: include role title, location, and one concrete responsibility in the first 3 lines.
- Sign off LinkedIn posts with "- Riya, AI assistant for \[Company\]" not "- The Hiring Team".

## 4.4 Account Resilience Strategy

LinkedIn's User Agreement prohibits non-human accounts. Riya operates as a transparently-disclosed AI but the account is technically out of policy. The product must be designed assuming periodic account loss (every 6-12 months under cautious operation, sooner under aggressive use).

| **ID** | **Requirement**                                                                                                                                                                                                        | **Priority** |
| ------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------ |
| AR-001 | System MUST cap Riya's LinkedIn posting frequency at 4 posts per day (configurable, default 3). Posts MUST be spaced minimum 90 minutes apart.                                                                         | P0           |
| AR-002 | System MUST NOT perform automated engagement - no auto-likes, auto-comments, auto-connection-requests, or auto-DMs.                                                                                                    | P0           |
| AR-003 | Riya's session MUST log in from a single residential India IP per account. Mobile and desktop sessions for the same account are not permitted simultaneously.                                                          | P0           |
| AR-004 | System MUST maintain a backup persona pool - minimum 2 ready-to-activate Riya accounts per region (e.g., North India "Riya", South India "Anjali"). Profiles aged minimum 30 days before activation.                   | P1           |
| AR-005 | On primary account ban or restriction, system MUST automatically failover to the backup persona within 4 hours, notify all affected customers, and migrate active role posts to the new account.                       | P1           |
| AR-006 | System MUST monitor LinkedIn account health daily - login success, post visibility, engagement metrics. Anomalies (sudden 0-impression post, login challenge, profile restriction) escalate to operator within 1 hour. | P0           |
| AR-007 | Customer contracts MUST include a Distribution Channel Disclosure clause acknowledging that LinkedIn is a third-party platform with its own terms, and channel access cannot be guaranteed indefinitely.               | P0           |

# 5\. Goals & Success Metrics

## 5.1 Product Goals

| **Goal**                                                                            | **Rationale**                                                                                                       |
| ----------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| Reduce time-to-shortlist to under 7 days                                            | Indian SMB baseline is 3-6 weeks. 7-day cycle keeps SMBs competitive against larger employers offering same talent. |
| Achieve over 70% recruiter shortlist acceptance rate                                | Adoption signal: if recruiters override more than 30% of Riya's recommendations, the scoring is not trusted.        |
| Ship explainable evaluations on 100% of shortlists                                  | Every candidate card carries justification, strengths, and risks. Differentiator vs. keyword-match competitors.     |
| Maintain account resilience: under 2 LinkedIn account losses per year per region    | Account ban is operational risk, not catastrophic, but must be bounded.                                             |
| Achieve over 4.0 / 5.0 CSAT among paying SMB customers within 90 days of activation | Sub-4.0 triggers product review; SMB market is unforgiving on bad UX.                                               |
| Reach unit economics positive at 200 paying customers                               | Path to sustainable indie-bootstrap business; informs feature investment cap.                                       |

## 5.2 Quality of Hire (QoH) KPI Framework

Quality of hire is the metric customers actually care about, but it lags by 6-12 months. The framework below splits QoH into four signals at different time horizons. All four are instrumented in-product.

| **Tier**                     | **Metric**                     | **Definition**                                                                                                                              | **Target**                 | **Cadence** |
| ---------------------------- | ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------- | ----------- |
| Tier 1 - Immediate           | Shortlist NPS                  | Per-candidate thumbs (1-5) from recruiter at shortlist review. Single click in UI. Tracked as % of "4 or 5" responses per role.             | \>70% positive             | Daily       |
| Tier 2 - Short-term          | Interview-to-Offer Rate        | Of Riya-shortlisted candidates who reach interview, % who receive an offer. Compared to recruiter's baseline (self-reported at onboarding). | ≥ recruiter baseline + 10% | Weekly      |
| Tier 3 - Long-term           | 90-Day Retention + Manager NPS | Two-question survey to hiring manager at day 90: (a) Is the hire still employed? (b) Would you hire from Riya's shortlist again? (1-5)      | \>85% retained, >4.0 NPS   | Quarterly   |
| Tier 4 - Compensation signal | Top-Candidate Accept Rate      | Of offers extended to Riya-shortlisted candidates, % accepted. High accept rate indicates good candidate-role fit.                          | \>50% accept rate          | Per offer   |

Composite QoH Score (rolled up to dashboard):

QoH = 0.20 × NPS_norm + 0.30 × Conversion_norm + 0.40 × Retention_norm + 0.10 × Accept_norm

All inputs normalised 0-100. Composite reported per role and per customer. Public on dashboard from day 1 of beta.

## 5.3 Operational KPIs

| **Metric**                                            | **Baseline** | **Target (6m)**             | **Owner**   |
| ----------------------------------------------------- | ------------ | --------------------------- | ----------- |
| Time-to-shortlist (days)                              | 21-42 days   | < 7 days                    | Product     |
| Shortlist NPS                                         | -            | \>70%                       | Product     |
| Resume-to-shortlist processing time                   | Manual       | < 2 minutes per CV          | Engineering |
| LinkedIn post success rate                            | -            | \>95%                       | Engineering |
| Application channel diversity (avg channels per role) | 1-2          | ≥ 4                         | Product     |
| System uptime                                         | -            | 99.5% SLA (SMB-appropriate) | Engineering |
| Cost per shortlist generated                          | -            | < ₹150                      | Engineering |
| Account ban incidents per region                      | -            | < 2 per year                | Operations  |
| Customer CSAT                                         | -            | \>4.0 / 5.0                 | Product     |
| Net Revenue Retention                                 | -            | \>110%                      | Founder     |

# 6\. System Architecture

HireFlow AI v2.0 is structured as a modular agent pipeline. The Hiring Core (this PRD) is one of multiple planned modules; HR Operations (planned v3.0) plugs into the same orchestrator and shared services layer. Each agent is independently deployable and communicates through a central message bus.

## 6.1 Modular Architecture Overview

Three architectural tiers:

- Persona Layer: Riya identity, voice, disclosure, and account management. Shared across all modules.
- Module Layer: Hiring Core (v2.0) and HR Ops (v3.0). New modules attach without changes to the persona layer.
- Shared Services: orchestrator, LLM abstraction, audit log, secrets vault, notification service, multi-tenant data store. All modules consume from this layer.

## 6.2 Hiring Core Agent Pipeline

| **Agent**                 | **Input**                                | **Output**                                              | **Key Technologies**                                                       |
| ------------------------- | ---------------------------------------- | ------------------------------------------------------- | -------------------------------------------------------------------------- |
| JD Intake Agent           | Raw JD (text / .docx / .pdf / URL)       | Structured JD schema (JSON)                             | LLM extraction + recruiter confirmation UI                                 |
| Distribution Orchestrator | Structured JD + channel config           | Channel-specific post artifacts + posting confirmations | Coordinates 6 channel sub-agents in parallel                               |
| LinkedIn Channel Agent    | JD + Riya account credentials            | Post URL + post ID + screenshot                         | Playwright (headless Chromium), residential proxy, anti-detection patterns |
| WhatsApp Group Agent      | JD + group whitelist                     | Posted message IDs per group                            | WhatsApp Web automation OR official Business API (Gupshup/Wati)            |
| Telegram Channel Agent    | JD + channel whitelist                   | Posted message IDs                                      | Telegram Bot API (legitimate, no ToS risk)                                 |
| Job Board Agent           | JD + tenant credentials                  | Listing URLs (Naukri, Indeed, Internshala)              | Per-board API where available, browser automation fallback                 |
| College Outreach Agent    | JD + college contact database            | Email send confirmations                                | SendGrid + tracked bulk email                                              |
| Referral Network Agent    | JD + past-candidate pool from CRM        | Outbound message confirmations                          | Email + SMS (MSG91) personalised outreach                                  |
| Collection Agent          | Dedicated inbox per role                 | Raw CV files + sender metadata                          | IMAP IDLE / Gmail API push                                                 |
| Parsing Agent             | Raw CVs (PDF / DOCX / DOC)               | Structured candidate profiles                           | PDF/DOCX parsers + LLM extraction with structured output                   |
| Scoring Agent             | JD schema + candidate profiles           | Scored & ranked candidate list                          | LLM scoring (deterministic) + vector similarity                            |
| Evaluation Agent          | Scored list + JD context                 | Shortlist with justifications, strengths, risks         | LLM with JSON-schema-constrained output                                    |
| Delivery Agent            | Shortlist + recruiter notification prefs | Email / WhatsApp / dashboard delivery                   | SendGrid + WhatsApp Business API                                           |

## 6.3 Infrastructure Components

| **Component**      | **Specification**                                                                                                                                                                                      |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Orchestrator       | Stateful workflow engine (LangGraph for v2.0 MVP; Temporal at scale). Manages agent DAG, retries, and per-job state. Module-agnostic - same orchestrator runs Hiring and HR Ops modules.               |
| LLM Backend        | Primary: GPT-4o-mini for cost-sensitive operations (parsing, post drafts); GPT-4o or Claude Sonnet for scoring and justification. All prompts version-controlled. Model choice per stage configurable. |
| Browser Automation | Playwright (headless Chromium). Used by LinkedIn Channel Agent and (optionally) WhatsApp Web Agent. Residential India proxy. Session tokens stored in vault, rotated on health-check failure.          |
| Email Service      | Inbound: IMAP IDLE on dedicated apply-{role_id}@{tenant_domain} address. Outbound: SendGrid (acknowledgements, college outreach, recruiter notifications).                                             |
| WhatsApp Service   | Two paths: (a) WhatsApp Web automation via Playwright for SMB tier; (b) WhatsApp Business API via Gupshup/Wati for paid tier (higher reliability, no ToS risk).                                        |
| Telegram Service   | Telegram Bot API (official, legitimate). Bot posts to channels where it is added as admin.                                                                                                             |
| SMS Service        | MSG91 (India-native). Used for candidate acknowledgements and referral outreach.                                                                                                                       |
| Message Bus        | v2.0 MVP: Redis Streams. v2.1 scale: Apache Kafka. Topics per agent stage.                                                                                                                             |
| Data Store         | PostgreSQL (structured records). Redis (queue/session). S3-compatible (MinIO for self-host, AWS S3 for cloud) for raw CV files.                                                                        |
| Vector DB          | v2.0 MVP: Postgres pgvector. v2.1: Pinecone or Weaviate.                                                                                                                                               |
| Secrets Vault      | HashiCorp Vault (self-host) or AWS Secrets Manager. Stores LinkedIn credentials, email passwords, API keys. Auto-rotation. All access audited.                                                         |
| API Gateway        | REST + GraphQL. OAuth 2.0 / JWT. Rate-limit per tenant. CORS locked.                                                                                                                                   |
| Audit Logger       | Immutable append-only log of every agent action, scoring decision, disclosure event, override, and account-health event. PostgreSQL with WORM-table semantics.                                         |

# 7\. Functional Requirements

Each module below corresponds to an agent in the pipeline. Requirements are tagged with priority: P0 = MVP launch blocker, P1 = required for GA (v2.0), P2 = post-launch (v2.1+).

## 7.1 Module 1 - JD Intake & Parsing

| **ID** | **Requirement**                                                                                                                                                                                                                                         | **Priority** |
| ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------ |
| JD-001 | System MUST accept JD input as plain text (paste), .docx, .pdf, or URL pointing to a live job posting.                                                                                                                                                  | P0           |
| JD-002 | System MUST extract: Job Title, Department, Location (remote/hybrid/on-site, City), Seniority, Responsibilities, Must-Have Qualifications, Nice-to-Have Qualifications, Salary Range (in INR), Tech Stack / Tools, Industry. Output as structured JSON. | P0           |
| JD-003 | System MUST prompt the recruiter to confirm extracted fields. Inline edits supported. Confirmation is mandatory before distribution.                                                                                                                    | P0           |
| JD-004 | System MUST generate a weighted scoring rubric: must-haves weighted 2x vs nice-to-haves. Recruiter can adjust weights pre-distribution.                                                                                                                 | P0           |
| JD-005 | System MUST support JDs in English and Hinglish (mixed Hindi-English). Pure Hindi deferred to v2.1.                                                                                                                                                     | P0           |
| JD-006 | System SHOULD flag biased language (gendered terms, age-coded language like "young dynamic team") and suggest neutral alternatives.                                                                                                                     | P1           |
| JD-007 | System MUST enforce salary range disclosure for any role posted in Karnataka (state law) and recommend disclosure for all other Indian states.                                                                                                          | P1           |

## 7.2 Module 2 - Multi-Channel Distribution

Distribution is the single most differentiating capability of HireFlow AI v2.0. Indian SMBs hire across 6+ channels - Riya unifies them. Each channel sub-agent operates independently and reports posting status to the Distribution Orchestrator.

**DESIGN DECISION**

Manual copy-paste is explicitly rejected. The product credibility depends on Riya executing posts autonomously. Channels where automation is infeasible are excluded from MVP scope rather than degraded to copy-paste.

### 7.2.1 LinkedIn Channel Agent

Riya posts from her own dedicated LinkedIn account (not the recruiter's). The account is positioned as an AI hiring assistant working with the customer company. Posts are short, punchy, hashtagged for organic reach.

| **Section**       | **Specification**                                                                                                                                                                                                                                                                                                                                                              |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------ |
| Account ownership | One Riya persona account per region (default: pan-India "Riya"; future: "Anjali" for South India). Owned and operated by HireFlow AI, used across all customers.                                                                                                                                                                                                               |
| Profile content   | Bio: "AI hiring assistant for Indian SMBs. I post roles from companies I work with. Apply to listed email - replies read by the company's recruiter." Profile photo: licensed stock. Cover: branded HireFlow visual.                                                                                                                                                           |
| Post structure    | (1) Disclosure line: "Posted by Riya for \[Company\]" (≤200 char from start); (2) Role hook (2 lines); (3) Role title + location/work mode in bold; (4) 3 responsibilities; (5) 3 must-haves; (6) CTA: "Email apply-\[ROLE_ID\]@hireflow.in with subject APPLY-\[ROLE_ID\]"; (7) 5-8 hashtags; (8) Sign-off: "- Riya, AI assistant for \[Company\]". Total ≤ 3,000 characters. |
| Posting cadence   | Per Riya account: max 4 posts per day (default 3), minimum 90 minutes apart. Posting window 09:00-19:00 IST. Mid-week (Tue-Thu) prioritised.                                                                                                                                                                                                                                   |
| Approval gate     | Recruiter MUST review and click "Approve & Post" before publication. No auto-posting permitted (RD-005 from v1.0 retained).                                                                                                                                                                                                                                                    |
| **ID**            | **Requirement**                                                                                                                                                                                                                                                                                                                                                                | **Priority** |
| LI-001            | System MUST authenticate to LinkedIn via Riya's account credentials retrieved from secrets vault. Credentials never logged.                                                                                                                                                                                                                                                    | P0           |
| LI-002            | System MUST generate the LinkedIn post body via LLM following the 8-section template above. AI disclosure (PE-001) MUST appear within first 200 characters.                                                                                                                                                                                                                    | P0           |
| LI-003            | System MUST present full draft to recruiter for review and explicit "Approve & Post" click before publication.                                                                                                                                                                                                                                                                 | P0           |
| LI-004            | System MUST handle MFA challenges: detect, pause automation, alert operator (not recruiter - Riya account is operated by HireFlow AI), resume after manual MFA.                                                                                                                                                                                                                | P0           |
| LI-005            | System MUST handle CAPTCHA / security challenges: detect, freeze the Riya account, failover to backup account (AR-005), alert operator.                                                                                                                                                                                                                                        | P0           |
| LI-006            | System MUST capture post URL, timestamp, post ID, and confirmation screenshot to audit log.                                                                                                                                                                                                                                                                                    | P0           |
| LI-007            | System MUST enforce posting cadence (max 4/day, 90-min spacing). Excess posts queued for next day.                                                                                                                                                                                                                                                                             | P0           |
| LI-008            | System MUST monitor Riya account daily for restriction signals: login challenge frequency, post impression drop, profile flag warnings. Anomalies escalate to operator within 1 hour (AR-006).                                                                                                                                                                                 | P0           |
| LI-009            | System MUST NOT perform any automated engagement - no likes, comments, connection requests, DMs, profile views (AR-002).                                                                                                                                                                                                                                                       | P0           |
| LI-010            | Recruiter dashboard MUST display Riya's LinkedIn account health status (green / yellow / red) per region.                                                                                                                                                                                                                                                                      | P1           |

### 7.2.2 WhatsApp Group Channel Agent

WhatsApp groups are the largest hidden hiring channel in India. Indian recruiters cross-post to 5-20 groups per role, manually. Riya automates this via two paths depending on customer tier and group access.

| **Section**                               | **Specification**                                                                                                                                                                              |
| ----------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------ |
| Path A - WhatsApp Web (MVP tier)          | Customer logs into WhatsApp Web via QR-scan once during onboarding. Session persisted server-side (encrypted). Riya posts to a customer-defined whitelist of groups via Playwright automation. |
| Path B - WhatsApp Business API (Pro tier) | Customer connects via Gupshup or Wati. Higher reliability, ToS-compliant, supports message templates and delivery receipts. Cost: ~₹0.50/message - bundled into Pro pricing.                   |
| Group whitelist                           | Customer maintains a list of groups Riya may post to. Default empty - explicit opt-in per group. System MUST never auto-discover or auto-add groups.                                           |
| Post format                               | Shorter than LinkedIn - max 1,500 characters. Same 8-section template, abbreviated. Disclosure line mandatory (PE-004). CTA points to same email channel.                                      |
| Cadence                                   | Max 5 groups per role per day. 30-second spacing between posts. Cool-down: 7 days before reposting same role to same group.                                                                    |
| **ID**                                    | **Requirement**                                                                                                                                                                                | **Priority** |
| WA-001                                    | System MUST onboard customer's WhatsApp account via QR-scan (Path A) or API connection (Path B). Customer choice.                                                                              | P0           |
| WA-002                                    | System MUST maintain per-customer group whitelist. Auto-discovery prohibited.                                                                                                                  | P0           |
| WA-003                                    | System MUST generate WhatsApp post copy via LLM with disclosure (PE-004) and route to whitelisted groups via Playwright (Path A) or API (Path B).                                              | P0           |
| WA-004                                    | System MUST enforce 30-second inter-post spacing and 7-day repost cool-down per group.                                                                                                         | P0           |
| WA-005                                    | System MUST detect and gracefully handle: WhatsApp Web session expiry, group removal, message-failed errors. Failed posts retry with exponential backoff (3 attempts), then alert recruiter.   | P0           |
| WA-006                                    | System MUST log every post attempt: target group ID, status, timestamp, message hash. PII-free logs (no phone numbers stored beyond what's required for delivery).                             | P0           |
| WA-007                                    | System SHOULD support inbound query handling: when a candidate replies in-group asking how to apply, Riya can DM them the application link (Pro tier only).                                    | P2           |

### 7.2.3 Telegram Channel Agent

Telegram has an official Bot API - fully ToS-legitimate, zero account-ban risk. Indian job channels on Telegram have 10K-500K subscribers each. The bot must be added as channel admin by the channel owner.

| **ID** | **Requirement**                                                                                                                                                                                                       | **Priority** |
| ------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------ |
| TG-001 | System MUST provide a HireFlow Telegram bot. Customers (or partner channel owners) add the bot to their channels as admin.                                                                                            | P0           |
| TG-002 | System MUST post via Bot API to all channels where the bot has post permissions and that the customer has whitelisted.                                                                                                | P0           |
| TG-003 | Posts MUST follow the same 8-section template (≤ 4,000 char Telegram limit). Disclosure mandatory (PE-004).                                                                                                           | P0           |
| TG-004 | System SHOULD support partnered Telegram channels - HireFlow negotiates bot-admin access to popular channels (e.g., "Bangalore Tech Jobs", "India PM Roles") and offers customers shared distribution as a value-add. | P1           |
| TG-005 | System MUST track delivery receipts and view counts via Bot API (where channel permissions allow).                                                                                                                    | P1           |

### 7.2.4 Job Board Channel Agent

Indian job boards remain the primary candidate-discovery surface for white-collar roles. Riya distributes to free or paid tiers depending on customer subscription.

| **Job Board**                    | **Integration Path**                                                                                                                                                                     | **Priority** |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------ |
| Naukri.com                       | Free job posting via account automation (Playwright). Paid Naukri RMS API for customers with existing subscriptions.                                                                     | P0           |
| Indeed India                     | Free posting via Indeed API (free tier) for organic listings. Sponsored posting via paid API for Pro tier.                                                                               | P0           |
| Internshala                      | API integration for entry-level and intern roles. Highly relevant for SMBs hiring freshers.                                                                                              | P1           |
| Hirect                           | Chat-based hiring app. API integration for verified employers. P1 due to integration cost vs. SMB volume.                                                                                | P1           |
| Foundit (formerly Monster India) | Browser automation for free posting tier.                                                                                                                                                | P2           |
| **ID**                           | **Requirement**                                                                                                                                                                          | **Priority** |
| JB-001                           | System MUST support Naukri free posting via account automation. Customer's Naukri account credentials stored in vault. Disclosure (PE-001 equivalent for job boards) appears in JD body. | P0           |
| JB-002                           | System MUST support Indeed India free posting via Indeed Publisher API (officially supported, no ToS risk).                                                                              | P0           |
| JB-003                           | System MUST format JD to each board's character limits and field structures automatically - no manual reformatting.                                                                      | P0           |
| JB-004                           | System MUST capture posting URL and listing ID per board for audit and analytics.                                                                                                        | P0           |
| JB-005                           | All board postings MUST direct candidates to the same email collection channel (apply-\[ROLE_ID\]@hireflow.in) - single intake, multiple sources.                                        | P0           |
| JB-006                           | System SHOULD support sponsored posting upgrades - recruiter can convert a free posting to paid sponsored from the dashboard.                                                            | P2           |

### 7.2.5 College Placement Network Agent

Most SMBs ignore college placement cells because outreach is manual and time-consuming. Automated bulk outreach to 200+ placement officers per role is a uniquely valuable feature for Indian SMBs hiring freshers.

| **ID** | **Requirement**                                                                                                                                                                                                                               | **Priority** |
| ------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------ |
| CP-001 | System MUST maintain a curated database of college placement contacts: institution name, placement officer name, email, phone, tier (T1/T2/T3), state, courses offered.                                                                       | P0           |
| CP-002 | System MUST include minimum 500 colleges across India at MVP launch - covering IITs, NITs, IIITs, top private engineering, top B-schools, top design institutes.                                                                              | P0           |
| CP-003 | Recruiter MUST be able to filter outreach: by tier, state, course, distance from office. Default: all colleges within 500 km offering matching course.                                                                                        | P0           |
| CP-004 | System MUST send personalised outreach emails: {Officer_Name} salutation, role summary, salary range, CTA to forward to relevant students. Disclosure (PE-003) mandatory in footer.                                                           | P0           |
| CP-005 | System MUST track open rate, click rate, and reply rate per email. Aggregated per college for tier scoring over time.                                                                                                                         | P0           |
| CP-006 | System MUST honour unsubscribe requests within 24 hours. Suppressed list maintained globally, not per customer.                                                                                                                               | P0           |
| CP-007 | System SHOULD support placement-cell partnership flag - colleges that have explicitly agreed to receive HireFlow notifications get priority and higher cadence; cold outreach to unpartnered colleges capped at 1 email per 30 days per role. | P1           |
| CP-008 | System SHOULD support placement-event signaling: colleges advertising upcoming placement weeks are flagged on dashboard so recruiters can time submissions.                                                                                   | P2           |

### 7.2.6 Referral Network Agent

Past candidates who interviewed but were not hired are an under-used hiring asset for SMBs. Riya re-engages them for new relevant roles, and asks for referrals into their network. This requires a candidate database - built up over time as the SMB uses HireFlow.

| **ID** | **Requirement**                                                                                                                                                                                    | **Priority** |
| ------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------ |
| RN-001 | System MUST maintain a per-customer candidate database: every applicant from every role, with profile, score, status (interviewed / rejected / hired / withdrawn), tags.                           | P0           |
| RN-002 | On a new role, system MUST identify candidates from past pools whose profile matches the new JD with score ≥ 70. Surface these to recruiter as "Past candidate matches" before posting externally. | P0           |
| RN-003 | Recruiter MUST be able to one-click send re-engagement emails: "We have a new role that matches your profile - interested?" Disclosure (PE-003) and DPDP-compliant unsubscribe link mandatory.     | P0           |
| RN-004 | System MUST send referral-request emails to past candidates: "Know someone who'd be a fit for \[Role\]? Forward this - \[referral link\]." Referrals tracked back to source candidate.             | P1           |
| RN-005 | System MUST honour past candidates' opt-out preferences. Default: candidates who applied in the last 12 months are eligible for re-engagement; older requires explicit opt-in.                     | P0           |
| RN-006 | Referral conversions tracked in analytics - per-customer cost-per-hire metric should reflect that referred hires often have lower cost-per-hire than channel-acquired.                             | P2           |

## 7.3 Module 3 - Application Collection

All channels point to a single intake: a dedicated email address per role. The structured subject line APPLY-\[ROLE_ID\] is the routing key. Email-as-intake is intentionally simple - works on every channel, no third-party API integration required, ToS-clean.

| **Parameter**            | **Specification**                                                                                                                                                                  |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------ |
| Inbound address format   | apply-{role_id}@hireflow.in (shared domain for MVP). Per-tenant subdomain (apply-{role_id}@{tenant}.hireflow.in) deferred to v2.1.                                                 |
| Required subject         | APPLY-{ROLE_ID} - e.g., APPLY-ACME-PM-2026-12. Case-insensitive partial match accepted.                                                                                            |
| Accepted attachments     | PDF, DOCX, DOC. Max 10MB per attachment. Max 3 attachments per email.                                                                                                              |
| Polling                  | IMAP IDLE for near-real-time. Fallback: 5-min polling.                                                                                                                             |
| Invalid subject handling | Quarantine - not discard. Recruiter can re-assign or dismiss from dashboard.                                                                                                       |
| Acknowledgement          | Auto-reply within 5 minutes of valid receipt. Includes role title, reference number, expected timeline, AI disclosure (PE-003).                                                    |
| **ID**                   | **Requirement**                                                                                                                                                                    | **Priority** |
| AC-001                   | System MUST provision unique inbox address on role publication. Auto-decommission on role closure.                                                                                 | P0           |
| AC-002                   | Collection Agent MUST poll via IMAP IDLE (or Gmail API push for Gmail-hosted tenants).                                                                                             | P0           |
| AC-003                   | Agent MUST filter by subject pattern; matched emails proceed to attachment extraction. Non-matched emails quarantined.                                                             | P0           |
| AC-004                   | Agent MUST extract CV attachments and store in encrypted object store at /{tenant_id}/{role_id}/{candidate_email}/{timestamp}/cv.{ext}.                                            | P0           |
| AC-005                   | Agent MUST extract metadata: sender email, sender name, received timestamp, attachment names, body text (cover letter), source channel tag inferred from email signature/referrer. | P0           |
| AC-006                   | System MUST deduplicate: same sender + same role = duplicate flag. Original retained; later submissions queued for recruiter approval.                                             | P0           |
| AC-007                   | System MUST send acknowledgement email within 5 min of valid receipt. Template per tenant. Disclosure (PE-003) mandatory.                                                          | P0           |
| AC-008                   | Missing-attachment emails MUST trigger a polite resubmission request with instructions.                                                                                            | P1           |
| AC-009                   | Live application counter on dashboard, refreshed every 5 minutes.                                                                                                                  | P1           |
| AC-010                   | Manual "Trigger Collection Now" button for force-poll.                                                                                                                             | P1           |
| AC-011                   | Audit log every email event: received, matched, quarantined, extracted, duplicate-flagged, acknowledged.                                                                           | P0           |
| AC-012                   | Configurable collection window (open/close dates). Auto-respond after close.                                                                                                       | P1           |

## 7.4 Module 4 - Resume Parsing

| **ID** | **Requirement**                                                                                                                                                                                                                                                                         | **Priority** |
| ------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------ |
| RP-001 | System MUST parse PDF (text + scanned/OCR), DOCX, DOC, HTML, and .txt CVs.                                                                                                                                                                                                              | P0           |
| RP-002 | System MUST extract: contact details, work experience (company, title, dates, description), education (institution, degree, dates), hard skills, soft skills (LLM-inferred), certifications, languages, URLs (LinkedIn, GitHub, portfolio). Output as structured CandidateProfile JSON. | P0           |
| RP-003 | Parsing MUST achieve >90% field extraction accuracy on Indian-format CVs (validated against curated test set of 500 CVs sampled from real Indian SMB applicants).                                                                                                                       | P0           |
| RP-004 | Low-confidence parses (<0.6) flagged for recruiter review.                                                                                                                                                                                                                              | P0           |
| RP-005 | PII restricted to encrypted candidate data store. No PII transmitted to external LLM APIs without anonymisation.                                                                                                                                                                        | P0           |
| RP-006 | Anonymised parsing mode (strip name, photo, gender markers, age signals) configurable per tenant.                                                                                                                                                                                       | P1           |
| RP-007 | Parsing SHOULD complete in <5 seconds per CV at p99.                                                                                                                                                                                                                                    | P1           |

## 7.5 Module 5 - AI Candidate Scoring

Composite score (0-100) derived from five dimensions:

| **Dimension**                    | **Default Weight**                                                                                                                                                                                                                                                 | **Description**                                                             |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------- |
| Must-have qualification match    | 40%                                                                                                                                                                                                                                                                | Binary + partial match against must-have criteria from JD.                  |
| Experience relevance             | 25%                                                                                                                                                                                                                                                                | Semantic similarity between candidate's past roles and JD responsibilities. |
| Skills alignment                 | 20%                                                                                                                                                                                                                                                                | Hard skill exact match + soft skill LLM inference.                          |
| Nice-to-have qualification match | 10%                                                                                                                                                                                                                                                                | Bonus for non-mandatory criteria.                                           |
| Career trajectory signal         | 5%                                                                                                                                                                                                                                                                 | Positive signal for upward progression in the relevant domain.              |
| **ID**                           | **Requirement**                                                                                                                                                                                                                                                    | **Priority**                                                                |
| SC-001                           | Scoring MUST be reproducible - same input always yields same output. LLM temperature = 0; model version pinned per tenant.                                                                                                                                         | P0                                                                          |
| SC-002                           | Every score MUST produce a structured explanation: criteria met, criteria not met, confidence per dimension.                                                                                                                                                       | P0                                                                          |
| SC-003                           | Scoring MUST run with anonymised profile when tenant has enabled anonymised mode (RP-006).                                                                                                                                                                         | P0                                                                          |
| SC-004                           | Recruiter MUST be able to override any score with a documented reason. Overrides logged.                                                                                                                                                                           | P0                                                                          |
| SC-005                           | Scoring of 200 applications MUST complete in under 5 minutes.                                                                                                                                                                                                      | P1                                                                          |
| SC-006                           | Scoring weights configurable per role within bounds set by HR Ops admin.                                                                                                                                                                                           | P1                                                                          |
| SC-007                           | "Skills gap" flag for near-miss candidates: score ≥70 but failing one must-have. Surfaced for sourcing decisions.                                                                                                                                                  | P2                                                                          |
| SC-008                           | Bias audit MUST be run on every shortlist comparing demographic distribution of shortlisted vs. applicant pool. Where demographic data unavailable, name-inferred gender (only) used with explicit recruiter consent. India-specific name → gender model required. | P1                                                                          |

## 7.6 Module 6 - Shortlist Generation & Delivery

| **ID** | **Requirement**                                                                                                                                                                                                    | **Priority** |
| ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------ |
| SL-001 | System MUST generate top-N shortlist. Default N = 10. Range 3-25 (SMB-appropriate; smaller than v1.0).                                                                                                             | P0           |
| SL-002 | Each candidate card MUST include: composite score, rank, dimension breakdown, fit justification (2-4 sentences), strengths (3-5 bullets), risks/gaps (1-3 bullets), original CV download link, source channel tag. | P0           |
| SL-003 | Shortlist UI MUST support: sort by dimension, filter by score range, expand/collapse cards, side-by-side comparison of two candidates, single-click thumbs (Tier 1 NPS capture).                                   | P0           |
| SL-004 | Recruiter MUST be able to: Approve, Reject (with reason), Hold. All actions logged.                                                                                                                                | P0           |
| SL-005 | Export: PDF report (formatted), CSV (raw data), WhatsApp share (formatted message with top 3 + link to full shortlist).                                                                                            | P0           |
| SL-006 | Notification: email + WhatsApp (configurable) when shortlist ready.                                                                                                                                                | P1           |
| SL-007 | Shortlist sharing via secure read-only link to hiring manager (no login required, time-limited).                                                                                                                   | P1           |
| SL-008 | Pipeline insights summary per role: applications per channel, score distribution histogram, time-to-shortlist.                                                                                                     | P2           |
| SL-009 | ATS push (Greenhouse, Lever, Keka - Keka prioritised for India market).                                                                                                                                            | P1           |

## 7.7 Module 7 - Recruiter Dashboard

| **ID** | **Requirement**                                                                                                                                    | **Priority** |
| ------ | -------------------------------------------------------------------------------------------------------------------------------------------------- | ------------ |
| DB-001 | Show all active roles with: status (draft/posted/collecting/scoring/shortlisted/closed), application count by channel, time elapsed since posting. | P0           |
| DB-002 | System alerts: posting failures per channel, parsing errors, low application volume, account health warnings (Riya LinkedIn status).               | P0           |
| DB-003 | Audit trail view per role - every agent action with timestamps and disclosures.                                                                    | P0           |
| DB-004 | Channel performance panel: applications per channel, conversion rate per channel, cost per applicant per channel.                                  | P1           |
| DB-005 | QoH dashboard: rolling Tier 1-4 metrics with composite QoH score per role and per customer.                                                        | P1           |
| DB-006 | Cross-role analytics: avg time-to-shortlist, top channels, AI acceptance rate, override patterns.                                                  | P2           |
| DB-007 | Bias audit panel: shortlist vs. applicant pool demographic distribution where data is available.                                                   | P2           |

# 8\. Non-Functional Requirements

## 8.1 Performance

| **Requirement**                                           | **Target**    | **Measurement**              |
| --------------------------------------------------------- | ------------- | ---------------------------- |
| JD parsing latency                                        | < 10 seconds  | p99, end-to-end              |
| Resume parsing throughput                                 | \> 50 CVs/min | Sustained load               |
| Scoring latency per candidate                             | < 5 seconds   | p99                          |
| Full pipeline (post → shortlist) for 200-application pool | < 30 minutes  | p95                          |
| UI page load                                              | < 3 seconds   | p95 on Indian 4G connections |
| API response                                              | < 800ms       | p99 on all endpoints         |

## 8.2 Security & Compliance

| **Area**                 | **Requirement**                                                                                                                                |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| Data encryption          | AES-256 at rest. TLS 1.3+ in transit.                                                                                                          |
| Authentication           | OAuth 2.0 + OIDC. MFA mandatory for recruiter and admin accounts.                                                                              |
| Authorisation            | RBAC: Recruiter / Hiring Manager / Admin / Super Admin (multi-tenant).                                                                         |
| DPDP Act 2023 (India)    | Primary regulatory baseline. Consent capture at candidate application; right-to-deletion within 30 days; data localisation (servers in India). |
| GDPR readiness           | Architecture supports GDPR controls; not enforced unless EU customers added.                                                                   |
| EU AI Act readiness      | Audit log, human oversight, and bias-audit infrastructure built from day 1 - enables future EU expansion without re-platforming.               |
| AI disclosure compliance | Persona disclosure (PE-001 to PE-007) is enforced at the prompt and template layer; not bypassable by configuration.                           |
| PII handling             | PII isolated in encrypted store. PII stripped from prompts before LLM calls in production.                                                     |
| Audit logging            | Immutable, append-only. 7-year retention. Includes every disclosure-bearing message and every override.                                        |
| Penetration testing      | Third-party pen test before paid GA. Annual thereafter.                                                                                        |

## 8.3 Reliability & Availability

MVP target: 99.5% uptime (~3.5 days/year downtime tolerance). GA target: 99.9% uptime.

- All agents idempotent - retrying a failed step never duplicates outputs.
- Pipeline resumes from last successful checkpoint; no full re-run on failure.
- Backups: daily full, hourly incremental. PITR within 1 hour.
- Single-region (Mumbai / Bangalore) for MVP. Multi-region DR for GA. RTO < 4 hours, RPO < 1 hour.

## 8.4 Scalability

- MVP target: 500 concurrent active roles across all tenants.
- GA target: 5,000 concurrent active roles. 100,000 CV processing jobs/month.
- Strict multi-tenant data isolation - verified via automated tests on every release.

# 9\. Core Data Models

Canonical JSON schemas flowing through the agent pipeline. Schemas are versioned contracts - any breaking change requires migration.

## 9.1 JobDescription Schema

{ "id": "jd_uuid", "tenant_id": "tenant_uuid", "title": "string", "department": "string", "location": { "type": "remote|hybrid|onsite", "city": "string", "state": "string", "country": "IN" }, "seniority": "Intern|Fresher|IC1|IC2|IC3|IC4|Manager|Director", "responsibilities": \["string"\], "must_haves": \[{ "criterion": "string", "weight": 2 }\], "nice_to_haves": \[{ "criterion": "string", "weight": 1 }\], "tech_stack": \["string"\], "salary_range": { "min": 0, "max": 0, "currency": "INR" }, "scoring_rubric": { "must_have": 0.40, "experience": 0.25, "skills": 0.20, "nice_to_have": 0.10, "trajectory": 0.05 }, "distribution_channels": \["linkedin", "whatsapp", "telegram", "naukri", "indeed", "internshala", "colleges", "referral_network"\], "channel_config": { "linkedin": { "enabled": true }, "whatsapp": { "groups": \["uuid"\] }, "colleges": { "tier_filter": \["T1","T2"\] } }, "created_by": "recruiter_uuid", "status": "draft|approved|posted|collecting|scoring|shortlisted|closed"}

## 9.2 CandidateProfile Schema

{ "id": "candidate_uuid", "tenant_id": "tenant_uuid", "jd_id": "jd_uuid", "source_channel": "linkedin|whatsapp|telegram|naukri|indeed|internshala|college|referral|direct", "source_post_url": "string", "applied_at": "ISO8601", "contact": { "email": "string", "phone": "string", "linkedin_url": "string", "portfolio_url": "string" }, "experience": \[{ "company": "string", "title": "string", "start": "YYYY-MM", "end": "YYYY-MM|present", "description": "string" }\], "education": \[{ "institution": "string", "degree": "string", "field": "string", "year": 2020 }\], "skills": { "hard": \["string"\], "soft": \["string"\] }, "certifications": \["string"\], "languages": \["string"\], "parse_confidence": 0.0, "pii_anonymised": true, "consent": { "dpdp_consent": true, "consent_ts": "ISO8601", "retention_until": "ISO8601" }}

## 9.3 CandidateScore Schema

{ "id": "score_uuid", "candidate_id": "candidate_uuid", "jd_id": "jd_uuid", "composite_score": 0, "rank": 1, "dimension_scores": { "must_have": 0, "experience": 0, "skills": 0, "nice_to_have": 0, "trajectory": 0 }, "criteria_met": \[{ "criterion": "string", "met": true, "confidence": 0.0 }\], "justification": "string (2-4 sentences)", "strengths": \["string"\], "risks": \["string"\], "near_miss_flag": false, "bias_audit_passed": true, "scored_at": "ISO8601", "model_version": "string", "recruiter_override": null}

## 9.4 ChannelPost Schema (NEW in v2.0)

{ "id": "post_uuid", "jd_id": "jd_uuid", "channel": "linkedin|whatsapp|telegram|naukri|indeed|internshala|college|referral", "channel_target_id": "string (group ID, channel ID, college email, etc.)", "post_url": "string", "post_id": "string (platform-native)", "posted_at": "ISO8601", "posted_by_persona": "riya|anjali|...", "content_hash": "sha256", "disclosure_included": true, "delivery_status": "sent|delivered|failed|quarantined", "metrics": { "impressions": 0, "clicks": 0, "applications_attributed": 0 }}

# 10\. API Requirements

RESTful JSON over HTTPS. Bearer JWT auth. Rate-limit 1,000 req/min per tenant. Every response includes a request-id header for tracing.

## 10.1 Core Endpoints

| **Method** | **Endpoint**                       | **Description**                                                                                |
| ---------- | ---------------------------------- | ---------------------------------------------------------------------------------------------- |
| POST       | /api/v1/jobs                       | Create job from JD. Triggers JD Intake Agent.                                                  |
| GET        | /api/v1/jobs/{job_id}              | Get full job state including channel posting status.                                           |
| POST       | /api/v1/jobs/{job_id}/distribute   | Trigger Distribution Orchestrator. Body: channels enabled + per-channel config.                |
| GET        | /api/v1/jobs/{job_id}/posts        | List all ChannelPost records for the job.                                                      |
| GET        | /api/v1/jobs/{job_id}/applications | List applications. Filterable by channel, status, score.                                       |
| POST       | /api/v1/jobs/{job_id}/score        | Trigger Scoring Agent. Async.                                                                  |
| GET        | /api/v1/jobs/{job_id}/shortlist    | Retrieve shortlist with full CandidateScore objects.                                           |
| PATCH      | /api/v1/shortlist/{score_id}       | Update candidate status (approved/rejected/hold) with optional NPS thumbs and override reason. |
| GET        | /api/v1/jobs/{job_id}/audit        | Full audit trail for job.                                                                      |
| GET        | /api/v1/jobs/{job_id}/qoh          | QoH metrics for the job (Tier 1-4 + composite).                                                |
| GET        | /api/v1/personas/health            | LinkedIn/WhatsApp account health per region (operator endpoint).                               |
| GET        | /api/v1/analytics/dashboard        | Aggregated metrics for recruiter portfolio.                                                    |

## 10.2 Webhook Events

| **Event**               | **Trigger**                                                                    |
| ----------------------- | ------------------------------------------------------------------------------ |
| job.distributed         | Distribution Orchestrator finished - at least one channel posted successfully. |
| channel.post.failed     | Specific channel failed. Includes channel and error context.                   |
| application.received    | New application ingested and parsed.                                           |
| scoring.complete        | Scoring Agent finished.                                                        |
| shortlist.ready         | Shortlist generated and ready for review.                                      |
| bias_audit.flagged      | Bias audit detected disparity > threshold.                                     |
| persona.account.warning | Riya account showed restriction signals (LinkedIn or WhatsApp).                |
| persona.account.banned  | Riya account banned. Failover initiated.                                       |
| agent.error             | Unrecoverable agent error.                                                     |

# 11\. Third-Party Integrations

| **Integration**                       | **Purpose**                                | **Scope**  | **Notes / Constraints**                                                                                             |
| ------------------------------------- | ------------------------------------------ | ---------- | ------------------------------------------------------------------------------------------------------------------- |
| LinkedIn (Playwright)                 | Outbound - Riya account posting            | P0 - MVP   | ToS grey area. Operated as transparently disclosed AI persona. Account resilience plan (AR-001 to AR-007) required. |
| WhatsApp Web (Playwright)             | Outbound - group posting (SMB tier)        | P0 - MVP   | ToS sensitive. Customer-side group whitelist; no auto-discovery. Per-customer session in vault.                     |
| WhatsApp Business API (Gupshup/Wati)  | Outbound - Pro tier                        | P1 - GA    | Officially supported, per-message cost ~₹0.50. Required for high-volume customers.                                  |
| Telegram Bot API                      | Outbound - channel posting                 | P0 - MVP   | Officially supported. Zero ToS risk.                                                                                |
| Naukri.com                            | Outbound - job board posting               | P0 - MVP   | Free tier via account automation; paid via API for subscribed customers.                                            |
| Indeed India Publisher API            | Outbound - job board posting               | P0 - MVP   | Officially supported. Free organic listings; paid sponsored.                                                        |
| Internshala API                       | Outbound - entry-level/intern roles        | P1 - GA    | Officially supported. Critical for fresher hiring.                                                                  |
| IMAP / Gmail API                      | Inbound - application collection           | P0 - MVP   | TLS 1.3+. IDLE preferred for reliability.                                                                           |
| SendGrid                              | Outbound - transactional email             | P0 - MVP   | Acknowledgements, college outreach, recruiter notifications. India IP pool.                                         |
| MSG91                                 | Outbound - SMS (India)                     | P1 - GA    | Candidate acknowledgements, referral outreach. India-native delivery.                                               |
| OpenAI GPT-4o / GPT-4o-mini           | LLM inference                              | P0 - MVP   | Post drafting, parsing, scoring. PII stripped before API call.                                                      |
| Anthropic Claude Sonnet               | LLM inference (fallback + premium scoring) | P1 - GA    | Same PII rules apply.                                                                                               |
| HashiCorp Vault / AWS Secrets Manager | Secrets management                         | P0 - MVP   | All credentials encrypted; auto-rotation; access audited.                                                           |
| Keka HRMS                             | Bi-directional - Indian HR platform        | P1 - GA    | Push approved shortlist; future bundling for HR Ops module.                                                         |
| Greenhouse / Lever ATS                | Bi-directional - international ATS         | P2 - v2.1+ | For Indian SMBs using these. Lower priority than Keka.                                                              |
| MSG91 / Wati WhatsApp                 | Outbound - recruiter notifications         | P1 - GA    | WhatsApp push to recruiter when shortlist ready.                                                                    |

# 12\. Release Plan

## 12.1 Phased Rollout

| **Phase**          | **Timeline** | **Scope**                                                                                                                                                            | **Exit Criteria**                                                                                                                         |
| ------------------ | ------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| MVP (Closed Pilot) | Month 1-3    | Riya persona setup; LinkedIn auto-posting (1 Riya account); JD intake + parsing; email collection; scoring; shortlist UI. 5 design-partner SMBs in Bangalore.        | 10 roles posted end-to-end. Shortlist NPS > 60% positive. LinkedIn account stable for 90 days.                                            |
| Beta (Open Beta)   | Month 4-6    | Add WhatsApp + Telegram + Naukri + Indeed channels. College outreach DB (500 colleges). Referral Network. Backup Riya account ready. Free tier offered.              | 30 paying customers. Shortlist NPS > 70%. Multi-channel attribution functioning. Account resilience tested via deliberate failover drill. |
| GA v2.0            | Month 7-9    | All P0/P1 requirements. Pricing tiers live. Internshala + Hirect channels. WhatsApp Business API for Pro tier. Keka ATS integration. India data residency confirmed. | 100 paying customers. CSAT > 4.0. NPS > 30. Pen test passed.                                                                              |
| v2.1               | Month 10-12  | Multi-persona regional accounts (Anjali - South India). Anonymised parsing. ATS integrations (Greenhouse/Lever). Configurable scoring weights.                       | 200 paying customers. NRR > 110%. QoH framework Tier 3 data starts arriving.                                                              |
| v3.0 (HR Ops)      | Month 13-18  | HR Operations module: onboarding, leave, attendance, performance reviews. Hiring + HR Ops bundle pricing.                                                            | 30% of Hiring customers attach HR Ops. Bundle ARPU > 2x standalone.                                                                       |

## 12.2 MVP Scope (Months 1-3)

Brutally minimal. Build the boring version. Ship to 5 design-partner SMBs.

Included in MVP:

- JD paste / upload + LLM extraction + recruiter confirmation.
- Riya persona: 1 LinkedIn account, complete profile, account-health monitoring.
- LinkedIn auto-posting via Playwright with explicit recruiter approval gate. Non-negotiable: no copy-paste fallback.
- Single email collection inbox per role + IMAP polling + acknowledgement emails.
- Resume parsing (PDF + DOCX) + scoring + shortlist UI.
- Shortlist NPS thumbs (Tier 1 QoH capture).
- Audit log of every disclosure-bearing action.

Excluded from MVP (deferred to Beta or later):

- WhatsApp / Telegram / job board / college / referral channels.
- Multi-tenant RBAC (single-tenant per design partner in MVP).
- Bias audit panel.
- ATS integrations.
- Anonymised parsing mode.
- Multi-region DR.
- Vector DB (use postgres LIKE / full-text for MVP scoring).

## 12.3 GA Launch Readiness Checklist

- All P0 functional requirements implemented and QA-signed.
- Pen test completed; no critical/high findings outstanding.
- DPDP Act compliance review by Indian legal counsel.
- AI persona disclosure terms reviewed and accepted by all design-partner customers.
- Bias audit run on 1,000 synthetic Indian-context candidate profiles - pass rate 100%.
- Parsing accuracy validated on 500-CV Indian test set - > 90%.
- Load test: 200 CVs scored in < 5 minutes.
- LinkedIn account resilience drill completed - primary → backup failover < 4 hours.
- WhatsApp Web session recovery tested across 30-day session expiry.
- College outreach database verified - 500 colleges, deliverable email rate > 90%.
- Beta customer CSAT > 4.0.
- Runbook complete for every agent failure mode including persona-account ban.

# 13\. Risks & Open Questions

## 13.1 Risk Register

| **Risk**                                                                                   | **Likelihood** | **Impact** | **Mitigation**                                                                                                                                                                                                                                                        |
| ------------------------------------------------------------------------------------------ | -------------- | ---------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Riya LinkedIn account banned for ToS violation                                             | Medium-High    | Medium     | Account-resilience strategy (AR-001 to AR-007). Backup persona pool. Cap 4 posts/day. No automated engagement. Customer contracts include channel-disclosure clause. Plan for periodic loss every 6-12 months as acceptable operational cost, not catastrophic event. |
| WhatsApp Web automation flagged / number banned                                            | Medium         | Medium     | Customer's own number is used (not shared). Per-customer session isolation. Path B (WhatsApp Business API) as Pro-tier alternative removes risk entirely.                                                                                                             |
| Indian SMB unwillingness to pay > 3 month free trial                                       | High           | High       | Time-bound free tier (max 14 days). Bundling path with HR Ops as second product reduces churn. Annual prepay discount to reduce monthly-decision friction.                                                                                                            |
| LLM cost per shortlist exceeds ₹150 target                                                 | Medium         | Medium     | Tiered model selection (GPT-4o-mini for cheap stages, GPT-4o for scoring). Aggressive caching of repeated parses. Customer-tier-based model assignment (Pro gets Claude Sonnet).                                                                                      |
| Resume parsing accuracy < 90% on Indian-format CVs                                         | Medium         | High       | Train on India-specific test set including: chronological CVs, functional CVs, photo-included CVs, multi-language CVs. LLM-based extraction is more robust than rules-based. Manual flagging for low-confidence parses.                                               |
| DPDP Act enforcement targets AI hiring tools                                               | Low            | High       | Build consent capture, retention controls, and audit log from day 1. India-resident data store. Annual compliance review.                                                                                                                                             |
| Candidate experience friction: "email-with-subject-line" CTA underperforms one-click apply | High           | Medium     | Acceptable for SMB segment where candidate volume is bounded. Mitigate via prominent CTA in posts. Future: WhatsApp-bot apply flow as v2.1 enhancement.                                                                                                               |
| Recruiters distrust AI shortlist quality                                                   | Medium         | High       | Explainability is core to product (SC-002). Recruiter override is one-click. Tier 1 NPS feedback loop tunes model. "Augment not replace" messaging consistent.                                                                                                        |
| Multiple competitors enter SMB India space                                                 | High           | Medium     | Distribution moat: multi-channel ingest is hard to replicate (especially college DB and WhatsApp groups). Speed-to-market matters; ship MVP in 90 days.                                                                                                               |
| Founder bandwidth: indie-bootstrap with day-job                                            | High           | High       | Phased plan respects part-time bandwidth. MVP scoped for 3 months of evening/weekend work. Design partners co-investing time. No fundraise required for MVP.                                                                                                          |