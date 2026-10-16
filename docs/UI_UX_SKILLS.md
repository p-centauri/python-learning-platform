# Installed UI/UX skills

Verified on 2026-10-16. The user requested these three design skills. They are installed globally for Codex on this Mac in `/Users/xasilov/.codex/skills`. Their discovery and use were observed in the subsequent UI/UX redesign turn. They are development tools; the hosted academy does not need these files installed on its server.

| Skill | Source and pinned revision | Use |
| --- | --- | --- |
| `ui-ux-pro-max` | [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/tree/56ea9cf174ed86786187daa9de0e6247cb0747e4/.claude/skills/ui-ux-pro-max), `56ea9cf174ed86786187daa9de0e6247cb0747e4` | Searchable UX, accessibility, typography, palette and framework guidance, including Next.js. |
| `frontend-design` | [Anthropic Frontend Design](https://github.com/anthropics/skills/tree/dbd4588f9e1033efb41dad4bef2f7947c8993d44/skills/frontend-design), `dbd4588f9e1033efb41dad4bef2f7947c8993d44` | Visual direction, typography, layout, interface copy and critique. |
| `frontend-skill` | [OpenAI Frontend Skill](https://github.com/openai/skills/tree/30444aed500c00c85294d12074f6e3ee794f808a/skills/.curated/frontend-skill), `30444aed500c00c85294d12074f6e3ee794f808a` | Restrained composition, app hierarchy, imagery and motion. Historical official version, not a current curated offering. |

OpenAI's [frontend article](https://developers.openai.com/blog/designing-delightful-frontends-with-gpt-5-4) identifies the original Frontend Skill. The official repository history records its removal in commit `11c643813b4645ca9f25d49ca180697732e0141a` on 2026-04-23. This installation uses that commit's parent, preserving the published skill rather than substituting a community copy.

## Installation and compatibility

Used the built-in skill-installer's `install-skill-from-github.py` with explicit `--repo`, `--ref`, `--path`, and `--dest /Users/xasilov/.codex/skills`. Inspected temporary copies before installing. No third-party npm installer was executed and no new Python dependency was needed.

Pro Max's upstream skill contains Claude-specific command examples. Adapted its eleven script examples to `python3 /Users/xasilov/.codex/skills/ui-ux-pro-max/scripts/search.py`, and included the repository's MIT `LICENSE`. Its scripts, data and references are unchanged. Anthropic's two files and OpenAI's three files match their reviewed upstream copies exactly; their licenses are preserved.

Installed entry points:

- `/Users/xasilov/.codex/skills/ui-ux-pro-max/SKILL.md`
- `/Users/xasilov/.codex/skills/frontend-design/SKILL.md`
- `/Users/xasilov/.codex/skills/frontend-skill/SKILL.md`

Invoke a skill in a future request using `$ui-ux-pro-max`, `$frontend-design`, or `$frontend-skill`. Select the guidance appropriate to the task; project requirements, accessibility and the academy's educational contract take precedence over aesthetic defaults. Installing a skill does not authorize a redesign or deployment.

## Verification

- Verified all three skill names/descriptions, entry points, bundled files and absence of symlinks: 74 Pro Max files, two Anthropic files and three OpenAI files.
- Compared every staged upstream file with its installed counterpart. The only changed upstream file is Pro Max's `SKILL.md`, containing the documented command adaptation.
- Parsed all five Pro Max top-level Python scripts successfully. Static inspection of these scripts found local CSV/JSON processing and optional explicit design-system persistence; their imports do not include a network client or subprocess launcher.
- Ran the installed search from `/tmp` with Python bytecode writes disabled: `"keyboard focus modal" --domain ux --json` returned three results; `"suspense streaming bundle" --stack nextjs --json` returned three results; `"education learning platform" --design-system --json` returned a populated design system with no persistence requested.
- No academy application code, learner data, runtime configuration or server services changed. Application tests were not rerun for this tooling/documentation-only task. Discovery in the subsequent Codex turn is confirmed; the UI/UX review uses all three skills.

The next user turn activated all three skills for the requested academy UI/UX redesign; see UI_UX_REVIEW.md and ADR 0044.
