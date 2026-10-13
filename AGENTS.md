# AGENTS.md: magicmountain.pro

Shared instructions for any AI assistant or IDE working in this repo. `CLAUDE.md` imports this file, so edit here only.

This is the public repo for the Magic Mountain website, a static site built with Python (standard library only) and deployed to GitHub Pages. Pushing to `main` deploys it.

**Before working, read `../magic-mountain-design/docs/website-setup.md`** (a private sibling repo). It has the architecture, setup, copy rules and the launch to-do list. If that folder isn't available, ask Dan before changing copy or content.

## Ground rules
- Standard library only: no pip dependencies, no JS framework. Build with `python3 src/build.py`.
- Copy lives in `src/content.py` as (English, Hungarian) pairs. Change both.
- Hike content comes from Notion at build time; don't hard-code hikes.
- This repo is public. Never commit secrets or private business details (bank details, internal notes, personal data).
