from datetime import datetime, timezone
from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    name: Mapped[str] = mapped_column(String(80))
    password_hash: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class LoginSession(Base):
    __tablename__ = "sessions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class AccountRecoveryKey(Base):
    __tablename__ = "account_recovery_keys"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    token_hash: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class LearningPreferences(Base):
    __tablename__ = "learning_preferences"
    __table_args__ = (
        CheckConstraint("weekly_hours BETWEEN 1 AND 20", name="ck_plan_hours"),
        CheckConstraint("goal IN ('python', 'backend', 'applied-ai', 'backend-ai')", name="ck_plan_goal"),
        CheckConstraint("starting_mode IN ('recommended', 'from-start')", name="ck_plan_start"),
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    goal: Mapped[str] = mapped_column(String(20))
    weekly_hours: Mapped[int] = mapped_column(Integer)
    starting_mode: Mapped[str] = mapped_column(String(20))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class CurriculumVersion(Base):
    __tablename__ = "curriculum_versions"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    title: Mapped[str] = mapped_column(String(120))


class Track(Base):
    __tablename__ = "tracks"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    version_id: Mapped[str] = mapped_column(ForeignKey("curriculum_versions.id"))
    title: Mapped[str] = mapped_column(String(150))
    description: Mapped[str] = mapped_column(Text)
    position: Mapped[int] = mapped_column(Integer)


class Module(Base):
    __tablename__ = "modules"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    track_id: Mapped[str] = mapped_column(ForeignKey("tracks.id"), index=True)
    title: Mapped[str] = mapped_column(String(150))
    position: Mapped[int] = mapped_column(Integer)


class Lesson(Base):
    __tablename__ = "lessons"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    module_id: Mapped[str] = mapped_column(ForeignKey("modules.id"), index=True)
    title: Mapped[str] = mapped_column(String(150))
    skill: Mapped[str] = mapped_column(String(80))
    minutes: Mapped[int] = mapped_column(Integer)
    content_path: Mapped[str] = mapped_column(String(200))


class LessonProgress(Base):
    __tablename__ = "lesson_progress"
    __table_args__ = (UniqueConstraint("user_id", "lesson_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    lesson_id: Mapped[str] = mapped_column(ForeignKey("lessons.id"))
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ExerciseState(Base):
    __tablename__ = "exercise_states"
    __table_args__ = (UniqueConstraint("user_id", "exercise_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    exercise_id: Mapped[str] = mapped_column(String(100))
    hints_used: Mapped[int] = mapped_column(Integer, default=0)
    revealed: Mapped[bool] = mapped_column(Boolean, default=False)


class ExerciseAttempt(Base):
    __tablename__ = "exercise_attempts"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    lesson_id: Mapped[str] = mapped_column(ForeignKey("lessons.id"))
    exercise_id: Mapped[str] = mapped_column(String(100), index=True)
    answer: Mapped[int] = mapped_column(Integer)
    score: Mapped[int] = mapped_column(Integer)
    hints_used: Mapped[int] = mapped_column(Integer)
    revealed: Mapped[bool] = mapped_column(Boolean)
    is_review: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ReviewItem(Base):
    __tablename__ = "review_items"
    __table_args__ = (UniqueConstraint("user_id", "exercise_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    exercise_id: Mapped[str] = mapped_column(String(100))
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    interval_days: Mapped[int] = mapped_column(Integer, default=1)
    repetitions: Mapped[int] = mapped_column(Integer, default=0)


class Note(Base):
    __tablename__ = "notes"
    __table_args__ = (UniqueConstraint("user_id", "lesson_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    lesson_id: Mapped[str] = mapped_column(ForeignKey("lessons.id"))
    body: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Bookmark(Base):
    __tablename__ = "bookmarks"
    __table_args__ = (UniqueConstraint("user_id", "lesson_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    lesson_id: Mapped[str] = mapped_column(ForeignKey("lessons.id"))


class ExamAttempt(Base):
    __tablename__ = "exam_attempts"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    exam_id: Mapped[str] = mapped_column(String(100))
    definition_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    answers: Mapped[dict] = mapped_column(JSON, default=dict)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    workspace: Mapped[dict] = mapped_column(JSON, default=dict)


class ExamRun(Base):
    __tablename__ = "exam_runs"
    __table_args__ = (UniqueConstraint("user_id", "request_key"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    attempt_id: Mapped[int] = mapped_column(ForeignKey("exam_attempts.id"), index=True)
    request_key: Mapped[str] = mapped_column(String(36))
    code: Mapped[str] = mapped_column(Text)
    definition_snapshot: Mapped[dict] = mapped_column(JSON)
    result: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class ProjectProgress(Base):
    __tablename__ = "project_progress"
    __table_args__ = (UniqueConstraint("user_id", "project_id", "task_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    project_id: Mapped[str] = mapped_column(String(100))
    task_id: Mapped[str] = mapped_column(String(100))
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ProjectSubmission(Base):
    __tablename__ = "project_submissions"
    __table_args__ = (
        UniqueConstraint("user_id", "project_id", "revision"),
        CheckConstraint("status IN ('draft', 'submitted')", name="ck_submission_status"),
        CheckConstraint("revision > 0", name="ck_submission_revision"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    project_id: Mapped[str] = mapped_column(String(100))
    revision: Mapped[int] = mapped_column(Integer)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("project_submissions.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    rubric_snapshot: Mapped[dict] = mapped_column(JSON)
    artifact: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ProjectReviewAssignment(Base):
    __tablename__ = "project_review_assignments"
    __table_args__ = (UniqueConstraint("submission_id", "email"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    submission_id: Mapped[int] = mapped_column(
        ForeignKey("project_submissions.id", ondelete="CASCADE"), index=True
    )
    email: Mapped[str] = mapped_column(String(254), index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ProjectFeedback(Base):
    __tablename__ = "project_feedback"
    __table_args__ = (
        UniqueConstraint("submission_id", "reviewer_id"),
        CheckConstraint("kind IN ('self', 'human')", name="ck_project_feedback_kind"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    submission_id: Mapped[int] = mapped_column(
        ForeignKey("project_submissions.id", ondelete="CASCADE"), index=True
    )
    reviewer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    kind: Mapped[str] = mapped_column(String(20))
    ratings: Mapped[dict] = mapped_column(JSON)
    summary: Mapped[str] = mapped_column(Text)
    next_steps: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class CodingDraft(Base):
    __tablename__ = "coding_drafts"
    __table_args__ = (UniqueConstraint("user_id", "exercise_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    exercise_id: Mapped[str] = mapped_column(String(100))
    code: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class CodingAttempt(Base):
    __tablename__ = "coding_attempts"
    __table_args__ = (UniqueConstraint("user_id", "request_key"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    exercise_id: Mapped[str] = mapped_column(String(100))
    request_key: Mapped[str] = mapped_column(String(36))
    code: Mapped[str] = mapped_column(Text)
    definition_snapshot: Mapped[dict] = mapped_column(JSON)
    result: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class RecallSession(Base):
    __tablename__ = "recall_sessions"
    __table_args__ = (
        UniqueConstraint("user_id", "active_key"),
        CheckConstraint("status IN ('active', 'submitted', 'abandoned')", name="ck_recall_status"),
        CheckConstraint("mode IN ('practice', 'delayed')", name="ck_recall_mode"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    concept_id: Mapped[str] = mapped_column(String(100), index=True)
    active_key: Mapped[str | None] = mapped_column(String(100), nullable=True)
    question_id: Mapped[str] = mapped_column(String(150))
    status: Mapped[str] = mapped_column(String(20), default="active")
    mode: Mapped[str] = mapped_column(String(20))
    definition_snapshot: Mapped[dict] = mapped_column(JSON)
    answer: Mapped[str] = mapped_column(String(120), default="")
    used_help: Mapped[bool] = mapped_column(Boolean, default=False)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class LessonCheckpointAttempt(Base):
    __tablename__ = "lesson_checkpoint_attempts"
    __table_args__ = (UniqueConstraint("user_id", "request_key"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    lesson_id: Mapped[str] = mapped_column(String(100), index=True)
    checkpoint_id: Mapped[str] = mapped_column(String(150))
    request_key: Mapped[str] = mapped_column(String(36))
    answer: Mapped[int] = mapped_column(Integer)
    definition_snapshot: Mapped[dict] = mapped_column(JSON)
    result: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
