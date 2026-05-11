import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    String, Text, Integer, Float, Boolean, DateTime,
    ForeignKey, Index, UniqueConstraint, event, DDL,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# ── Tenant ────────────────────────────────────────────────────────────────────

class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    status: Mapped[str] = mapped_column(String(50), default="active")
    plan: Mapped[str] = mapped_column(String(50), default="free")
    settings: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    recruiters: Mapped[List["Recruiter"]] = relationship(back_populates="tenant")
    jobs: Mapped[List["Job"]] = relationship(back_populates="tenant")


# ── Recruiter ─────────────────────────────────────────────────────────────────

class Recruiter(Base):
    __tablename__ = "recruiters"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # recruiter | hiring_manager | admin | super_admin
    role: Mapped[str] = mapped_column(String(50), default="recruiter")
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    mfa_secret: Mapped[Optional[str]] = mapped_column(String(255))
    notification_prefs: Mapped[dict] = mapped_column(JSONB, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    tenant: Mapped["Tenant"] = relationship(back_populates="recruiters")
    jobs: Mapped[List["Job"]] = relationship(back_populates="created_by_recruiter")

    __table_args__ = (
        UniqueConstraint("tenant_id", "email"),
        Index("ix_recruiters_tenant_email", "tenant_id", "email"),
    )


# ── Job (JobDescription) ──────────────────────────────────────────────────────

class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("recruiters.id"), nullable=False)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    department: Mapped[Optional[str]] = mapped_column(String(255))
    # {type: remote|hybrid|onsite, city, state, country: IN}
    location: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    # Intern|Fresher|IC1|IC2|IC3|IC4|Manager|Director
    seniority: Mapped[Optional[str]] = mapped_column(String(50))
    industry: Mapped[Optional[str]] = mapped_column(String(255))

    responsibilities: Mapped[list] = mapped_column(JSONB, default=list)
    must_haves: Mapped[list] = mapped_column(JSONB, default=list)       # [{criterion, weight}]
    nice_to_haves: Mapped[list] = mapped_column(JSONB, default=list)    # [{criterion, weight}]
    tech_stack: Mapped[list] = mapped_column(JSONB, default=list)

    salary_min: Mapped[Optional[int]] = mapped_column(Integer)
    salary_max: Mapped[Optional[int]] = mapped_column(Integer)
    salary_currency: Mapped[str] = mapped_column(String(10), default="INR")
    salary_disclosed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Default weights; recruiter-editable pre-distribution
    scoring_rubric: Mapped[dict] = mapped_column(JSONB, default=lambda: {
        "must_have": 0.40,
        "experience": 0.25,
        "skills": 0.20,
        "nice_to_have": 0.10,
        "trajectory": 0.05,
    })

    distribution_channels: Mapped[list] = mapped_column(JSONB, default=list)
    channel_config: Mapped[dict] = mapped_column(JSONB, default=dict)

    # draft → approved → posted → collecting → scoring → shortlisted → closed
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False)

    # Email intake
    collection_email: Mapped[Optional[str]] = mapped_column(String(255))
    collection_open_until: Mapped[Optional[datetime]] = mapped_column(DateTime)

    shortlist_size: Mapped[int] = mapped_column(Integer, default=10)

    # Raw input storage
    raw_jd_text: Mapped[Optional[str]] = mapped_column(Text)
    raw_jd_file_key: Mapped[Optional[str]] = mapped_column(String(500))   # S3 key

    # Bias language flags from JD intake agent
    bias_flags: Mapped[list] = mapped_column(JSONB, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    tenant: Mapped["Tenant"] = relationship(back_populates="jobs")
    created_by_recruiter: Mapped["Recruiter"] = relationship(back_populates="jobs")
    channel_posts: Mapped[List["ChannelPost"]] = relationship(back_populates="job")
    candidates: Mapped[List["Candidate"]] = relationship(back_populates="job")

    __table_args__ = (
        Index("ix_jobs_tenant_status", "tenant_id", "status"),
        Index("ix_jobs_tenant_created", "tenant_id", "created_at"),
    )


# ── ChannelPost ───────────────────────────────────────────────────────────────

class ChannelPost(Base):
    __tablename__ = "channel_posts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    # linkedin|whatsapp|telegram|naukri|indeed|internshala|college|referral
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    channel_target_id: Mapped[Optional[str]] = mapped_column(String(500))   # group ID / channel ID / email

    post_url: Mapped[Optional[str]] = mapped_column(String(1000))
    post_id: Mapped[Optional[str]] = mapped_column(String(255))             # platform-native ID

    posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    posted_by_persona: Mapped[Optional[str]] = mapped_column(String(100))   # riya | anjali

    content_hash: Mapped[Optional[str]] = mapped_column(String(64))         # sha256 of post body
    content_preview: Mapped[Optional[str]] = mapped_column(Text)            # first 500 chars

    disclosure_included: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # sent|delivered|failed|quarantined
    delivery_status: Mapped[str] = mapped_column(String(50), default="sent", nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)

    metrics: Mapped[dict] = mapped_column(JSONB, default=dict)              # {impressions, clicks, applications_attributed}
    screenshot_key: Mapped[Optional[str]] = mapped_column(String(500))      # S3 key

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    job: Mapped["Job"] = relationship(back_populates="channel_posts")

    __table_args__ = (
        Index("ix_channel_posts_job", "job_id"),
        Index("ix_channel_posts_channel_status", "channel", "delivery_status"),
    )


# ── Candidate (CandidateProfile) ─────────────────────────────────────────────

class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)

    source_channel: Mapped[Optional[str]] = mapped_column(String(50))
    source_post_url: Mapped[Optional[str]] = mapped_column(String(1000))
    applied_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # PII — kept here, stripped before any LLM call
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(500))
    portfolio_url: Mapped[Optional[str]] = mapped_column(String(500))

    # Structured profile from Parsing Agent
    experience: Mapped[list] = mapped_column(JSONB, default=list)
    education: Mapped[list] = mapped_column(JSONB, default=list)
    skills_hard: Mapped[list] = mapped_column(JSONB, default=list)
    skills_soft: Mapped[list] = mapped_column(JSONB, default=list)
    certifications: Mapped[list] = mapped_column(JSONB, default=list)
    languages: Mapped[list] = mapped_column(JSONB, default=list)

    cv_file_key: Mapped[Optional[str]] = mapped_column(String(500))         # S3 key
    cv_original_filename: Mapped[Optional[str]] = mapped_column(String(255))
    cover_letter_text: Mapped[Optional[str]] = mapped_column(Text)

    parse_confidence: Mapped[Optional[float]] = mapped_column(Float)
    parse_flagged: Mapped[bool] = mapped_column(Boolean, default=False)     # low-confidence flag
    pii_anonymised: Mapped[bool] = mapped_column(Boolean, default=False)

    # DPDP Act 2023 consent
    dpdp_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_ts: Mapped[Optional[datetime]] = mapped_column(DateTime)
    retention_until: Mapped[Optional[datetime]] = mapped_column(DateTime)
    opted_out: Mapped[bool] = mapped_column(Boolean, default=False)

    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False)

    # received|parsing|parsed|scored|shortlisted|approved|rejected|hold|withdrawn
    status: Mapped[str] = mapped_column(String(50), default="received", nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    job: Mapped["Job"] = relationship(back_populates="candidates")
    score: Mapped[Optional["CandidateScore"]] = relationship(back_populates="candidate", uselist=False)

    __table_args__ = (
        Index("ix_candidates_job", "job_id"),
        Index("ix_candidates_tenant_email", "tenant_id", "email"),
        UniqueConstraint("job_id", "email", name="uq_candidate_job_email"),
    )


# ── CandidateScore ────────────────────────────────────────────────────────────

class CandidateScore(Base):
    __tablename__ = "candidate_scores"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=False, unique=True)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    composite_score: Mapped[float] = mapped_column(Float, nullable=False)
    rank: Mapped[Optional[int]] = mapped_column(Integer)

    # {must_have, experience, skills, nice_to_have, trajectory}  — each 0-100
    dimension_scores: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    # [{criterion, met: bool, confidence: float}]
    criteria_met: Mapped[list] = mapped_column(JSONB, default=list)

    justification: Mapped[Optional[str]] = mapped_column(Text)             # 2-4 sentences
    strengths: Mapped[list] = mapped_column(JSONB, default=list)           # 3-5 bullets
    risks: Mapped[list] = mapped_column(JSONB, default=list)               # 1-3 bullets

    near_miss_flag: Mapped[bool] = mapped_column(Boolean, default=False)   # score≥70 but failing one must-have
    bias_audit_passed: Mapped[Optional[bool]] = mapped_column(Boolean)

    scored_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    model_version: Mapped[Optional[str]] = mapped_column(String(100))

    # Recruiter actions
    recruiter_status: Mapped[Optional[str]] = mapped_column(String(50))    # approved|rejected|hold
    recruiter_override_score: Mapped[Optional[float]] = mapped_column(Float)
    recruiter_override_reason: Mapped[Optional[str]] = mapped_column(Text)
    nps_thumb: Mapped[Optional[int]] = mapped_column(Integer)              # 1-5 per SL-003

    candidate: Mapped["Candidate"] = relationship(back_populates="score")

    __table_args__ = (
        Index("ix_scores_job_rank", "job_id", "rank"),
        Index("ix_scores_job_composite", "job_id", "composite_score"),
    )


# ── PersonaAccount ────────────────────────────────────────────────────────────

class PersonaAccount(Base):
    __tablename__ = "persona_accounts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    persona_name: Mapped[str] = mapped_column(String(100), nullable=False)  # riya | anjali
    platform: Mapped[str] = mapped_column(String(50), nullable=False)       # linkedin | whatsapp
    region: Mapped[str] = mapped_column(String(100), default="india")

    # Key under which credentials are stored in the secrets vault
    vault_secret_key: Mapped[str] = mapped_column(String(500), nullable=False)

    is_primary: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)

    # green | yellow | red
    health_status: Mapped[str] = mapped_column(String(20), default="green")
    posts_today: Mapped[int] = mapped_column(Integer, default=0)
    posts_today_reset_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_health_check_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_ban_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    account_aged_since: Mapped[Optional[datetime]] = mapped_column(DateTime)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_persona_accounts_platform_region", "platform", "region"),
        Index("ix_persona_accounts_active", "platform", "is_active", "is_banned"),
    )


# ── CollegeContact ────────────────────────────────────────────────────────────

class CollegeContact(Base):
    __tablename__ = "college_contacts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    institution_name: Mapped[str] = mapped_column(String(500), nullable=False)
    placement_officer_name: Mapped[Optional[str]] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50))

    tier: Mapped[str] = mapped_column(String(10), nullable=False)           # T1 | T2 | T3
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    city: Mapped[Optional[str]] = mapped_column(String(100))
    lat: Mapped[Optional[float]] = mapped_column(Float)
    lng: Mapped[Optional[float]] = mapped_column(Float)

    courses_offered: Mapped[list] = mapped_column(JSONB, default=list)
    is_partner: Mapped[bool] = mapped_column(Boolean, default=False)

    unsubscribed: Mapped[bool] = mapped_column(Boolean, default=False)
    unsubscribed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    open_rate: Mapped[Optional[float]] = mapped_column(Float)
    click_rate: Mapped[Optional[float]] = mapped_column(Float)
    last_emailed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_college_tier_state", "tier", "state"),
        Index("ix_college_partner", "is_partner"),
    )


# ── WhatsAppGroup ─────────────────────────────────────────────────────────────

class WhatsAppGroup(Base):
    __tablename__ = "whatsapp_groups"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    group_id: Mapped[str] = mapped_column(String(255), nullable=False)
    group_name: Mapped[Optional[str]] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("tenant_id", "group_id"),
        Index("ix_whatsapp_groups_tenant", "tenant_id"),
    )


# ── AuditEvent (immutable — WORM semantics enforced via DB trigger) ───────────

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    # e.g. channel_post.created | candidate.received | score.overridden | disclosure.sent
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[Optional[str]] = mapped_column(String(100))     # job|candidate|channel_post|score|persona_account
    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    channel: Mapped[Optional[str]] = mapped_column(String(50))

    # sha256 of disclosure-bearing message body (PE-007)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64))

    data: Mapped[dict] = mapped_column(JSONB, default=dict)

    # No default=func.now() — we set this explicitly so tests can control time
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    __table_args__ = (
        Index("ix_audit_events_tenant_created", "tenant_id", "created_at"),
        Index("ix_audit_events_entity", "entity_type", "entity_id"),
        Index("ix_audit_events_type", "event_type"),
    )


# ── WORM trigger: prevent UPDATE/DELETE on audit_events ──────────────────────

_audit_worm_trigger = DDL("""
CREATE OR REPLACE FUNCTION audit_events_worm()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'audit_events is append-only — UPDATE and DELETE are prohibited';
END;
$$;

DROP TRIGGER IF EXISTS trg_audit_events_worm ON audit_events;
CREATE TRIGGER trg_audit_events_worm
BEFORE UPDATE OR DELETE ON audit_events
FOR EACH ROW EXECUTE FUNCTION audit_events_worm();
""")

event.listen(AuditEvent.__table__, "after_create", _audit_worm_trigger)
