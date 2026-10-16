# ADR 0044: Responsive, task-focused study workspace

Date: 2026-10-16

Status: Accepted

## Context

The user requested a frontend review and a responsive, interactive redesign after installing UI/UX Pro Max, Anthropic Frontend Design and the historical OpenAI Frontend Skill. The academy has 195 lessons and fourteen navigation destinations. Its original layout required extensive browsing, used small interface text and placed an introduction before the mobile authentication form. Educational evidence and active assessment secrecy must remain intact.

## Decision

Keep the established Form identity and implement a presentation-only redesign in the existing Next.js application. Self-host the licensed DM Sans variable font through next/font/local. Shared semantic colors, spacing, readable type and controls live in workspace.css after the existing feature styles; both themes remain supported. Retain feature CSS rather than mixing a framework migration into this request.

Group navigation into study, practice/evidence, and library/account. Use the existing focus-trapped drawer through tablet widths, with four mobile destination links and a More control. Keep profile controls visible while navigation scrolls. Focused assessments retain their separate workspace without the mobile dock.

Filter the existing curriculum response on the client by topic/track and, in the learning path, reading status. Native track disclosures reduce visual overload. Practice/map initially render 24 matching topics and expose an explicit Show more control; filtering always searches the full collection. Every count and reading label derives from API data. Planned tracks remain labeled, and reading completion remains separate from mastery.

Give lessons a sticky study toolbar for overview/practice/notes/bookmark, readable prose/code, keyboard-scrollable code/table regions, and reachable mobile notes. Notes retain explicit server saves and expose unsaved state. A browser close/reload warning protects dirty notes; this does not promise automatic draft recovery or interception of every client-side route change.

Authentication places the form first on small screens, retains password-manager/paste support, and adds an accessible password visibility toggle. Search clears outdated results while a new request is pending. No curriculum, assessment definitions, API authorization, schema, learner-code execution or third-party analytics change.

## Verification and deployment

Real Chrome journeys cover learning/notes/checkpoints, all Python assessment levels, plans, account recovery and navigation. New tests exercise topic/status filters, incremental topic lists, tablet/mobile navigation, study tools, password visibility, landscape and reduced motion. Keyboard access to overflow code and explicit filter labels were corrected during testing. A broad accessibility sweep exposed transient low contrast during theme color transitions; text/background switch immediately while border/shadow feedback remains available.

Deploy only the web service after build and browser checks, retaining the prior image and source for rollback. API, database, migrations and carwash containers must retain identity/start time. Detailed outcomes and finite accessibility coverage belong in UI_UX_REVIEW, STATUS and PROGRESS; automated checks do not establish universal accessibility or usability certification.

## Consequences

The academy keeps one frontend stack and its existing data contracts. Large collections become easier to search without an additional endpoint or dependency. More complete historical/URL-preserved filtering, independent assistive-technology research and a separately isolated hosted code worker remain future work. The installed design skills guide choices; their generic aesthetic defaults do not override this product's learning contract.
