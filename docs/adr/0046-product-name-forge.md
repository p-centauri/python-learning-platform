# ADR 0046: Product name "Forge — Backend & AI Engineering Academy"

Date: 2026-10-29

Status: Accepted

## Context

The product was called "Form — Engineering Academy" ("form." wordmark). The owner is presenting it on a public portfolio (https://portfolio.xosilov.com) next to two other apps and wanted a name that represents what it is: a Backend + Applied AI engineering academy where skill is built by practice and measured by evidence. Offered: Forge, Proofwork, DeepStack Academy. The owner chose **Forge** and a full rebrand, then decided to keep the address **eng.xosilov.com** (no new subdomain).

## Decision

Everything a person reads says Forge: page title "Forge — Backend & AI Engineering Academy", the "forge." wordmark with an anvil mark (lucide `Anvil`, already a dependency) and the caption "BACKEND & AI ACADEMY", the footer, the recovery-key file text, the Markdown evidence export heading ("# Forge — personal evidence"), the OpenAPI title ("Forge API"), the seeded curriculum-version title and the repository's README/AGENTS titles.

Infrastructure identifiers stay as they are: the Compose project and containers `engineering-academy-*`, the `eng-edge` network, `/srv/aiagent/academy`, the database name and volume, the `academy-recovery-` key prefix and `academy-recovery-key.txt` file name, the npm package name, and the GitHub repository `p-centauri/python-learning-platform`. Renaming them changes nothing a learner sees and risks volumes, recovery keys already saved by learners, proxy routes and links.

## Consequences

No schema, API contract or learner data changes. Old recovery keys keep working (same prefix). The seeded curriculum title changes in the database only the next time the seed runs (`db.merge` on the same version id). Historical documents keep the old name where they describe past work.
