# Forge (Backend & AI Engineering Academy) — session guide

Before changing this project, read `docs/STATUS.md`, `docs/ROADMAP.md`, and the latest entry in `docs/PROGRESS.md`. Read the relevant architecture/assessment/security documents before changing those domains.

## Product contract
- The original requirements are preserved in `docs/PROJECT_BRIEF.md`.
- Build an academy for an experienced JavaScript/Vue/PostgreSQL developer becoming a Backend + Applied AI engineer.
- Use Next.js/TypeScript and a Python/FastAPI/SQLAlchemy modular monolith. PostgreSQL is the deployment database.
- Keep educational content outside React. Never equate reading completion with mastery.
- No dead controls, invented progress, placeholder lessons, or answers exposed in active exams.
- Clearly label planned curriculum and distinguish objective grading from human/self assessment.
- Never execute learner code inside the API process. A future runner needs isolation and resource limits.

## Session closeout (required)
1. Run checks appropriate to the changes; record commands and outcomes.
2. Update `docs/STATUS.md` with what works, limitations, and the exact next action.
3. Append a dated entry to `docs/PROGRESS.md` with changes, tests, and unresolved issues.
4. Update checkboxes in `docs/ROADMAP.md`; never mark unverified work complete.
5. Record consequential decisions in `docs/adr/`.

Do not erase previous progress entries. These files are the durable handoff across sessions.
