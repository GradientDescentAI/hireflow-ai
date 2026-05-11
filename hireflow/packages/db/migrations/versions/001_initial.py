"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-05-09
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension (safe if already exists)
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # ── tenants ──────────────────────────────────────────────────────────────
    op.create_table(
        "tenants",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("domain", sa.String(255), unique=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("plan", sa.String(50), nullable=False, server_default="free"),
        sa.Column("settings", JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # ── recruiters ────────────────────────────────────────────────────────────
    op.create_table(
        "recruiters",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), nullable=False, server_default="recruiter"),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("mfa_enabled", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("mfa_secret", sa.String(255)),
        sa.Column("notification_prefs", JSONB, nullable=False, server_default="{}"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_unique_constraint("uq_recruiters_tenant_email", "recruiters", ["tenant_id", "email"])
    op.create_index("ix_recruiters_tenant_email", "recruiters", ["tenant_id", "email"])

    # ── jobs ──────────────────────────────────────────────────────────────────
    op.create_table(
        "jobs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("recruiters.id"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("department", sa.String(255)),
        sa.Column("location", JSONB, nullable=False, server_default="{}"),
        sa.Column("seniority", sa.String(50)),
        sa.Column("industry", sa.String(255)),
        sa.Column("responsibilities", JSONB, nullable=False, server_default="[]"),
        sa.Column("must_haves", JSONB, nullable=False, server_default="[]"),
        sa.Column("nice_to_haves", JSONB, nullable=False, server_default="[]"),
        sa.Column("tech_stack", JSONB, nullable=False, server_default="[]"),
        sa.Column("salary_min", sa.Integer),
        sa.Column("salary_max", sa.Integer),
        sa.Column("salary_currency", sa.String(10), nullable=False, server_default="INR"),
        sa.Column("salary_disclosed", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("scoring_rubric", JSONB, nullable=False, server_default='{"must_have":0.40,"experience":0.25,"skills":0.20,"nice_to_have":0.10,"trajectory":0.05}'),
        sa.Column("distribution_channels", JSONB, nullable=False, server_default="[]"),
        sa.Column("channel_config", JSONB, nullable=False, server_default="{}"),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("collection_email", sa.String(255)),
        sa.Column("collection_open_until", sa.DateTime),
        sa.Column("shortlist_size", sa.Integer, nullable=False, server_default="10"),
        sa.Column("raw_jd_text", sa.Text),
        sa.Column("raw_jd_file_key", sa.String(500)),
        sa.Column("bias_flags", JSONB, nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("posted_at", sa.DateTime),
        sa.Column("closed_at", sa.DateTime),
    )
    op.create_index("ix_jobs_tenant_status", "jobs", ["tenant_id", "status"])
    op.create_index("ix_jobs_tenant_created", "jobs", ["tenant_id", "created_at"])

    # ── channel_posts ─────────────────────────────────────────────────────────
    op.create_table(
        "channel_posts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", UUID(as_uuid=True), sa.ForeignKey("jobs.id"), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("channel", sa.String(50), nullable=False),
        sa.Column("channel_target_id", sa.String(500)),
        sa.Column("post_url", sa.String(1000)),
        sa.Column("post_id", sa.String(255)),
        sa.Column("posted_at", sa.DateTime),
        sa.Column("posted_by_persona", sa.String(100)),
        sa.Column("content_hash", sa.String(64)),
        sa.Column("content_preview", sa.Text),
        sa.Column("disclosure_included", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("delivery_status", sa.String(50), nullable=False, server_default="sent"),
        sa.Column("error_message", sa.Text),
        sa.Column("retry_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("metrics", JSONB, nullable=False, server_default="{}"),
        sa.Column("screenshot_key", sa.String(500)),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_channel_posts_job", "channel_posts", ["job_id"])
    op.create_index("ix_channel_posts_channel_status", "channel_posts", ["channel", "delivery_status"])

    # ── candidates ────────────────────────────────────────────────────────────
    op.create_table(
        "candidates",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", UUID(as_uuid=True), sa.ForeignKey("jobs.id"), nullable=False),
        sa.Column("source_channel", sa.String(50)),
        sa.Column("source_post_url", sa.String(1000)),
        sa.Column("applied_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255)),
        sa.Column("phone", sa.String(50)),
        sa.Column("linkedin_url", sa.String(500)),
        sa.Column("portfolio_url", sa.String(500)),
        sa.Column("experience", JSONB, nullable=False, server_default="[]"),
        sa.Column("education", JSONB, nullable=False, server_default="[]"),
        sa.Column("skills_hard", JSONB, nullable=False, server_default="[]"),
        sa.Column("skills_soft", JSONB, nullable=False, server_default="[]"),
        sa.Column("certifications", JSONB, nullable=False, server_default="[]"),
        sa.Column("languages", JSONB, nullable=False, server_default="[]"),
        sa.Column("cv_file_key", sa.String(500)),
        sa.Column("cv_original_filename", sa.String(255)),
        sa.Column("cover_letter_text", sa.Text),
        sa.Column("parse_confidence", sa.Float),
        sa.Column("parse_flagged", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("pii_anonymised", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("dpdp_consent", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("consent_ts", sa.DateTime),
        sa.Column("retention_until", sa.DateTime),
        sa.Column("opted_out", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_duplicate", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("status", sa.String(50), nullable=False, server_default="received"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_candidates_job", "candidates", ["job_id"])
    op.create_index("ix_candidates_tenant_email", "candidates", ["tenant_id", "email"])
    op.create_unique_constraint("uq_candidate_job_email", "candidates", ["job_id", "email"])

    # ── candidate_scores ──────────────────────────────────────────────────────
    op.create_table(
        "candidate_scores",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("candidate_id", UUID(as_uuid=True), sa.ForeignKey("candidates.id"), nullable=False, unique=True),
        sa.Column("job_id", UUID(as_uuid=True), sa.ForeignKey("jobs.id"), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("composite_score", sa.Float, nullable=False),
        sa.Column("rank", sa.Integer),
        sa.Column("dimension_scores", JSONB, nullable=False, server_default="{}"),
        sa.Column("criteria_met", JSONB, nullable=False, server_default="[]"),
        sa.Column("justification", sa.Text),
        sa.Column("strengths", JSONB, nullable=False, server_default="[]"),
        sa.Column("risks", JSONB, nullable=False, server_default="[]"),
        sa.Column("near_miss_flag", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("bias_audit_passed", sa.Boolean),
        sa.Column("scored_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("model_version", sa.String(100)),
        sa.Column("recruiter_status", sa.String(50)),
        sa.Column("recruiter_override_score", sa.Float),
        sa.Column("recruiter_override_reason", sa.Text),
        sa.Column("nps_thumb", sa.Integer),
    )
    op.create_index("ix_scores_job_rank", "candidate_scores", ["job_id", "rank"])
    op.create_index("ix_scores_job_composite", "candidate_scores", ["job_id", "composite_score"])

    # ── persona_accounts ──────────────────────────────────────────────────────
    op.create_table(
        "persona_accounts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("persona_name", sa.String(100), nullable=False),
        sa.Column("platform", sa.String(50), nullable=False),
        sa.Column("region", sa.String(100), nullable=False, server_default="india"),
        sa.Column("vault_secret_key", sa.String(500), nullable=False),
        sa.Column("is_primary", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_banned", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("health_status", sa.String(20), nullable=False, server_default="green"),
        sa.Column("posts_today", sa.Integer, nullable=False, server_default="0"),
        sa.Column("posts_today_reset_at", sa.DateTime),
        sa.Column("last_health_check_at", sa.DateTime),
        sa.Column("last_ban_at", sa.DateTime),
        sa.Column("account_aged_since", sa.DateTime),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_persona_accounts_platform_region", "persona_accounts", ["platform", "region"])
    op.create_index("ix_persona_accounts_active", "persona_accounts", ["platform", "is_active", "is_banned"])

    # ── college_contacts ──────────────────────────────────────────────────────
    op.create_table(
        "college_contacts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("institution_name", sa.String(500), nullable=False),
        sa.Column("placement_officer_name", sa.String(255)),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("phone", sa.String(50)),
        sa.Column("tier", sa.String(10), nullable=False),
        sa.Column("state", sa.String(100), nullable=False),
        sa.Column("city", sa.String(100)),
        sa.Column("lat", sa.Float),
        sa.Column("lng", sa.Float),
        sa.Column("courses_offered", JSONB, nullable=False, server_default="[]"),
        sa.Column("is_partner", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("unsubscribed", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("unsubscribed_at", sa.DateTime),
        sa.Column("open_rate", sa.Float),
        sa.Column("click_rate", sa.Float),
        sa.Column("last_emailed_at", sa.DateTime),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_college_tier_state", "college_contacts", ["tier", "state"])

    # ── whatsapp_groups ───────────────────────────────────────────────────────
    op.create_table(
        "whatsapp_groups",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("group_id", sa.String(255), nullable=False),
        sa.Column("group_name", sa.String(500)),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("last_posted_at", sa.DateTime),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_unique_constraint("uq_whatsapp_groups_tenant_group", "whatsapp_groups", ["tenant_id", "group_id"])
    op.create_index("ix_whatsapp_groups_tenant", "whatsapp_groups", ["tenant_id"])

    # ── audit_events (immutable) ──────────────────────────────────────────────
    op.create_table(
        "audit_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True)),
        sa.Column("user_id", UUID(as_uuid=True)),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(100)),
        sa.Column("entity_id", UUID(as_uuid=True)),
        sa.Column("channel", sa.String(50)),
        sa.Column("content_hash", sa.String(64)),
        sa.Column("data", JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_audit_events_tenant_created", "audit_events", ["tenant_id", "created_at"])
    op.create_index("ix_audit_events_entity", "audit_events", ["entity_type", "entity_id"])
    op.create_index("ix_audit_events_type", "audit_events", ["event_type"])

    # WORM trigger on audit_events
    op.execute("""
        CREATE OR REPLACE FUNCTION audit_events_worm()
        RETURNS TRIGGER LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'audit_events is append-only — UPDATE and DELETE are prohibited';
        END;
        $$;

        CREATE TRIGGER trg_audit_events_worm
        BEFORE UPDATE OR DELETE ON audit_events
        FOR EACH ROW EXECUTE FUNCTION audit_events_worm();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_audit_events_worm ON audit_events")
    op.execute("DROP FUNCTION IF EXISTS audit_events_worm()")
    for tbl in [
        "audit_events", "whatsapp_groups", "college_contacts",
        "persona_accounts", "candidate_scores", "candidates",
        "channel_posts", "jobs", "recruiters", "tenants",
    ]:
        op.drop_table(tbl)
