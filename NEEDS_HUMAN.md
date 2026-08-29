# NEEDS_HUMAN — genuine external blockers (not fabricatable by the agent)

The agent does NOT fake progress on these; they are recorded here and surfaced in chat.
See also EXPLICIT HUMAN CHECKPOINTS in /home/ubuntu/rag_v10_goal.txt (real LLM keys, public
DNS/SSL, live webhook creds, live DB migrations, billing).

## Open blockers

### B1. `gh` CLI not installed — cannot open PRs or file GitHub issues
- `gh: command not found`. The new workflow (per user correction) requires `gh pr create` /
  `gh issue create` / `gh pr merge`. The agent can create feature branches, commit, and push
  (all verified — branch `feat/phase-c-clickable-citations` is live on origin), but CANNOT
  open/merge PRs or create issues without the CLI.
- **Human decision needed:** (a) install + authenticate `gh` here (agent can `apt-get install
  gh`; needs the human to run `gh auth login` / provide a token — agent must NEVER invent/store
  a GitHub token), (b) human opens the PR manually via the URL GitHub returns on push, or
  (c) accept branch+push only for now.
- PR URL for this branch: https://github.com/shubhsaxena2020/hermes-rag/pull/new/feat/phase-c-clickable-citations

### B2. Dirty working tree + master/origin divergence (key-tier changes bundled into this PR)
- `origin/master` and local `master` have diverged (origin/master = P1 #9 key-tier lineage, 34
  commits; local master had v10.5–v10.13 commits that were NEVER pushed). This PHASE C branch is
  based on `origin/master` so its PR merges cleanly.
- When this branch was checked out, the working tree already contained UNCOMMITTED key-tier
  changes left by the earlier P1 #9 session: `app/models.py` (+25 lines: KeyInfo.expires_at,
  KeyExpiryRequest, PublishableKeyRequest, SecretKeyRequest) and `tests/test_security_fixes.py`
  (+71 lines of key-expiry tests) and `BACKLOG.md`. These are NOT authored by this change.
- They were bundled into the PHASE C commit via `git add -A` so the security_fixes suite stays
  green (those tests require the key-tier models). This pollutes the PHASE C PR with unrelated
  work. **Recommended:** the human should split `app/models.py` + `tests/test_security_fixes.py`
  (+ BACKLOG.md) into their own dedicated "key-tier" PR, leaving the PHASE C PR to contain only
  the widget/backend citation+multi-turn+markdown + the two genuine bug fixes (TenantKey.expires_at
  column, tenants.set_key_expiry import).
- Note: v10.5–v10.13 feature work (job queue, dedup, file upload, catalog) lives only on separate
  unmerged feature branches — those too need PRs (blocked by B1).

## Resolved
- (none yet)
