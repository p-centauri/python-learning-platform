# Academy UI/UX review and implementation

Started 2026-10-16 at the user's request. Product: a study workspace for an experienced developer learning backend and applied AI engineering. The primary job is to find the right next task, understand a lesson, practise, and revisit evidence. This is an application, not a marketing landing page.

## Review findings

- Observed the hosted login at a narrow viewport: the introduction occupies most of the first screen and pushes form actions below it.
- The main sidebar has fourteen destinations in one undifferentiated list. Its drawer starts only below 700px, leaving limited learning space on tablets.
- Learning path, practice and knowledge map render all 195 lessons without local topic/track filters. The learning path exposes every module at once.
- Body, metadata, controls and notes commonly use 9–14px text. Several icon controls are smaller than comfortable touch targets.
- Lesson notes sit after the entire article on mobile. There is no direct study action strip for notes/practice and the sticky context can exceed short screens.
- Dashboard introduces multiple competing prompts plus decorative slogans. The next-lesson footer hardcodes two exercises instead of using its API count.
- Search can retain old results while a different query is pending. Native dialog semantics already provide a useful keyboard foundation.
- Existing strengths to preserve: real account-owned evidence, planned curriculum labels, light/dark themes, server-side grading, private active answers, accessible dialog/focus handling and actual saved notes/drafts.

## Design direction

Visual thesis: a focused engineering notebook, with generous reading space, precise typography and Form's established forest-green identity.

Content plan: overview leads to the next study action; curriculum presents searchable tracks; lessons present readable material with nearby study tools; assessments keep their focused workspace and honest evidence labels.

Interaction thesis: clear hover/focus/pressed states, responsive navigation with predictable dismissal, quick topic filtering, reachable notes and practice, and useful loading/saved feedback. Motion is brief and functional, with reduced-motion support.

Palette: ink `#182a25`, secondary text `#52665f`, canvas `#f6f8f7`, white surface `#ffffff`, forest action `#17634b`, pale green `#e8f2ed`. Dark equivalents must retain measured text/control contrast. Typography uses self-hosted DM Sans for interface/headings and the existing monospace stack for code. Spacing follows 4/8px steps; section separation carries hierarchy rather than boxing every element.

The first Pro Max education query returned children's typography and claymorphism, which do not fit this audience. A narrower developer/productivity query returned flat, typography-led app guidance. Use its relevant keyboard, responsive and accessibility guidance; choose the actual palette/type for this academy. Do not persist or apply the children's recommendation or marketing-page structure.

Plan review: retain the recognizable green brand, remove decorative slogans and excess uppercase labels, use real curriculum and learner state, and give each surface a primary task. Do not introduce streak targets, fabricated completion, learner-code execution or decorative controls.

## Verification and release

Implementation, browser evidence, accessibility checks and release outcome will be recorded here and in STATUS/PROGRESS after verification. Preview uses a separate database and ports 3001/8001; original local learning state is preserved.

## Implemented and locally verified

- Preserved Form's forest-green identity with readable self-hosted DM Sans, consistent light/dark tokens, larger controls and short border/press feedback. Foreground/background theme changes are immediate to avoid transient low contrast. No font requests go to Google in the browser.
- The first-time overview leads with the actual next lesson, with plan setup as a secondary action and evidence totals below. Removed decorative slogans and replaced hardcoded exercise counts with API data.
- Grouped all fourteen destinations. The sidebar scrolls separately from its visible account controls; the accessible drawer applies through 960px, with a five-item mobile dock and safe-area spacing. Focused assessments retain their distraction-free shell.
- Added topic/track filters to learning, practice and map, plus reading-status filtering and track disclosure in the learning path. Search covers all lessons; practice/map show 24 at a time with an actual Show more action. Planned tracks remain explicit and reading counts do not imply mastery.
- Added reachable lesson overview/practice/notes/bookmark controls, readable prose/code, keyboard-scrollable code/table regions, appropriately offset anchors and mobile note placement. Existing explicit saves and persistence remain intact; dirty notes show a state indicator and a close/reload warning.
- Brought the authentication form first on mobile, improved labels/password help and added password visibility. Search clears old results while the next query is pending. All changes use the existing React/Next.js/Lucide stack; the only added asset is the licensed local font.

Local checks:

- `npm run typecheck`, `npm run build` and Prettier checks for all changed frontend/test files pass.
- Existing learning/checkpoint/diagnostic/three-level Python suites: **7 passed (1.0m)**.
- Combined everyday/plan/learning/responsive run: **11 passed, one long browser sweep interrupted (2.5m)**. The interrupted test was subsequently completed successfully. Together the runs verify **17 distinct browser journeys**, not seventeen in one run.
- Dedicated final everyday accessibility sweep: **1 passed (1.3m), 60 checks, zero violations or page overflow**. Initial checks exposed keyboard access to overflow code and transient dark-theme contrast; both were corrected. Earlier concurrent runs collided in their shared trace directory; final runs use a dedicated output folder or execute separately. No failed run is represented as successful.
- New responsive suite verifies filters and incremental loading, actual note persistence, authentication, tablet drawer/quick navigation, **25 additional light/dark axe observations** across 320/390/820/1440px, 844×390 landscape and reduced motion. All observed checks pass. These finite observations are not universal accessibility certification or testing on physical iOS/Android devices.
- Original local academy.db bytes and all earlier PROGRESS bytes remain unchanged. Preview uses a separate SQLite file under `.local/ui-ux-20261016/` on 3001/8001. No API/domain/schema/educational content changes were required.

Decision: [ADR 0044](adr/0044-responsive-study-workspace.md). Detailed private logs and reports are in `.local/ui-ux-20261016/`. Hosted release verification follows below once completed.

## Completed hosted release and final acceptance

The redesign is live at **https://academy.45-141-22-101.sslip.io**. Verified fifteen frontend source hashes and deployed only the academy web service. Final image: `sha256:ea5cc4ec3011b00ff4495715fa96441fe2c233c65399dfd5e1ffcfca07156178`. All other ten academy/carwash containers retain their IDs/start times/restart counters. API/database remain healthy; no migration, proxy change or restart of another service was needed. The previous image is retained as `engineering-academy-web:before-ui-ux-20261016`, with source backups and release manifests under server-private `.local/ui-ux-20261016/`.

Final authenticated checks used the **local compiled standalone production build and separate test database**: `E2E_BASE_URL=http://127.0.0.1:3002 npx playwright test tests/responsive-design.spec.ts tests/learning.spec.ts ...` — **six passed (26.7s)**. This includes actual note persistence, reading state, scenario/diagnostic flows, incremental topic lists, phone/tablet navigation, 25 clean light/dark scans, landscape and reduced motion. The existing checkpoint/failure-preservation suite was also rerun after code-scroll changes: **two passed (14.3s)**. Local `next start` emitted the standalone configuration warning, so verification used the documented `.next/standalone/server.js` with its copied build assets instead.

Automatic approval review rejected the proposed temporary production account, notes and assessment fixture because the trusted UI request did not specifically authorize production-data testing and cleanup. The action was not executed or bypassed. No account was created on the server for this release's tests. A safer live test blocks all API mutations and checks public pages/assets: **one passed (10.2s)**, with login at 390/1440px and recovery at 320px, three clean axe scans, health 200, preserved security headers, zero console errors and zero external Google font requests. Authenticated live flows were not exercised in this release; the isolated standalone checks are separate evidence.

Visually inspected screenshots:

- [Live mobile login](screenshots/ui-ux-hosted-login-390.png) and [live desktop login](screenshots/ui-ux-hosted-login-1440.png).
- [Production-build mobile overview with isolated test data](screenshots/ui-ux-overview-390.png) and [desktop overview](screenshots/ui-ux-overview-1440.png).
- [Mobile lesson](screenshots/ui-ux-lesson-390.png), [curriculum](screenshots/ui-ux-curriculum-390.png) and [dark assessment catalog](screenshots/ui-ux-assessments-dark-390.png).

All temporary local preview processes were stopped after verification. Ports 3000/3001/3002/8000/8001/9000/3100 are closed, original local academy.db bytes match the saved fingerprint, and historical PROGRESS bytes are preserved. The server stays running. Hosted code execution remains subject to the previously recorded separate-worker boundary; the UI redesign does not change it.

Exact next action: use the hosted academy and wait for the user's next request. Independent learner research, physical-device/assistive-technology testing and broader curriculum/worker work remain separate tasks.

Reproducible commands (from `apps/web`, using an isolated preview database):

```sh
npm run typecheck
npm run build
E2E_BASE_URL=http://127.0.0.1:3001 npx playwright test tests/interactive-lessons.spec.ts tests/learning.spec.ts tests/python-assessments.spec.ts --workers=1 --reporter=line
E2E_BASE_URL=http://127.0.0.1:3001 npx playwright test tests/everyday.spec.ts --grep 'major learning routes' --workers=1 --trace off --output ../../.local/ui-ux-20261016/accessibility-clean-results --reporter=line
E2E_BASE_URL=http://127.0.0.1:3002 npx playwright test tests/responsive-design.spec.ts tests/learning.spec.ts --workers=1 --output ../../.local/ui-ux-20261016/production-results --reporter=line
```

The isolated preview is stopped at handoff. Do not point these account-creating journeys at production without explicit authorization for their data/cleanup scope. The live read-only helper is retained privately in `.local/ui-ux-20261016/hosted-readonly.spec.ts` and blocks all API mutations.
