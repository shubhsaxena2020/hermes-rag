# NEEDS_HUMAN — genuine external blockers (not fabricatable by the agent)

This file tracks items that require a human operator. The agent does NOT fake progress on
these; they are recorded here and surfaced in chat. See also the EXPLICIT HUMAN CHECKPOINTS
in /home/ubuntu/rag_v10_goal.txt (real LLM keys, public DNS/SSL, live webhook creds, live DB
migrations, billing).

## Open blockers

### B1. `gh` CLI not installed — cannot open PRs or file GitHub issues (2026-08-29)
- **What's blocked:** The new workflow (per user correction) requires opening real PRs
  (`gh pr create`) and filing real issues (`gh issue create`) for each chunk of work. `gh`
  is not present in this environment (`gh: command not found`), so the agent can create
  feature branches, commit, and push (all verified working — branch `feat/phase-c-widget-polish`
  is live on origin), but CANNOT open/merge PRs or create issues.
- **What the agent did instead:** Branch + commit + push completed for PHASE C widget-polish.
  GitHub returned the PR URL: https://github.com/shubhsaxena2020/hermes-rag/pull/new/feat/phase-c-widget-polish
- **Human decision needed (pick one):**
  1. Install + authenticate `gh` here (agent can `apt-get install gh` then needs the human to
     run `gh auth login` / provide a token — agent must NOT invent or store a GitHub token), OR
  2. Human opens the PR manually via the URL above and files issues manually, OR
  3. Accept branch+push only (no PR mechanism) for now.
- **Why not auto-fixed:** Authenticating `gh` needs a real GitHub credential (human checkpoint);
  the agent must never invent/guess a token. Installing software is also a heavier action best
  confirmed with the human.

## Resolved
- (none yet)
