"""Preserve project artifacts, pinned rubrics, reviewer grants and feedback."""

from alembic import op
import sqlalchemy as sa

revision = "d842bc315f20"
down_revision = "c731ab204e19"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "project_submissions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", sa.String(100), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("parent_id", sa.Integer(), sa.ForeignKey("project_submissions.id"), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("rubric_snapshot", sa.JSON(), nullable=False),
        sa.Column("artifact", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("user_id", "project_id", "revision"),
        sa.CheckConstraint("status IN ('draft', 'submitted')", name="ck_submission_status"),
        sa.CheckConstraint("revision > 0", name="ck_submission_revision"),
    )
    op.create_index("ix_project_submissions_user_id", "project_submissions", ["user_id"])
    op.create_table(
        "project_review_assignments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "submission_id",
            sa.Integer(),
            sa.ForeignKey("project_submissions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("submission_id", "email"),
    )
    op.create_index(
        "ix_project_review_assignments_submission_id", "project_review_assignments", ["submission_id"]
    )
    op.create_index("ix_project_review_assignments_email", "project_review_assignments", ["email"])
    op.create_table(
        "project_feedback",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "submission_id",
            sa.Integer(),
            sa.ForeignKey("project_submissions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("reviewer_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("ratings", sa.JSON(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("next_steps", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("submission_id", "reviewer_id"),
        sa.CheckConstraint("kind IN ('self', 'human')", name="ck_project_feedback_kind"),
    )
    op.create_index("ix_project_feedback_submission_id", "project_feedback", ["submission_id"])
    op.create_index("ix_project_feedback_reviewer_id", "project_feedback", ["reviewer_id"])


def downgrade():
    op.drop_table("project_feedback")
    op.drop_table("project_review_assignments")
    op.drop_table("project_submissions")
