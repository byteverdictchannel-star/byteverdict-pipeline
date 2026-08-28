# TB-002 Content + Auto-Post Pipeline

## Goal
Two persistent subagents forming a production + publish loop:
1. **Content Agent** — sources news, drafts clips + captions, exports platform-ready files to the ready-queue
2. **Posting Agent** — watches the ready-queue, **writes a description/caption**, verifies checklist, posts to available platforms, logs results

## What exists today
- 3 clips ready on Desktop (`clips-channel-TB002/`) — all with audio, logos blurred
- 3 clips in `test-batch/ready-to-post/` — masters ready for posting
- `ig_post.py` — IG Reels poster via Graph API (OAuth not fully wired; manual posting works)
- `youtube_post.py` — YouTube Shorts poster via Data API v3 (proven)
- `xurl` — X/Twitter CLI (installed, needs auth setup)
- `clip-log/` — empty, needs entries
- No TikTok posting tool yet

## Pipeline design

### Content Agent (cron: every 6 hours)
Trigger: sourcing + production. Uses clips-channel-production skill + web search + YouTube sourcing.

Steps:
1. Search for fresh news / trending clips (YouTube, web, RSS)
2. Tier sources (Tier 1/2/3/4 per clips-channel-production)
3. Surface candidates with provenance log
4. For each vetted candidate: draft overlay (headline + context + attribution), draft caption (humanized), flag sensitive-content concerns
5. **Handoff to Leo** for final clip decisions + sensitive-content screen
6. On Leo's go: cut + overlay + export → drop into `test-batch/ready-to-post/`
7. Log clip entry in `clip-log/`

### Posting Agent (cron: every 3 hours, plus immediate on-file-create)
Trigger: file appears in `test-batch/ready-to-post/`.

Steps:
1. Scan `ready-to-post/` for new items not yet posted
2. **Write a description/caption** for each clip — grounded in the clip content + source, humanized voice, engagement hook
3. Verify checklist: sensitive-content cleared, overlay accurate, exports ready, log complete
4. Post to available platforms:
   - YouTube Shorts → `youtube_post.py` (available now)
   - Instagram Reels → `ig_post.py` (available now, OAuth-dependent)
   - X/Twitter → `xurl` (needs auth setup)
   - TikTok → not available yet (manual)
5. Log posting result (platform, post ID, timestamp, response, caption used)
6. Flag failures for Leo

## Guardrails (from subagent-delegation.md)
- Content agent drafts; Leo decides final clips, overlays, sensitive-content clearance
- Posting agent writes descriptions but Leo reviews before first few posts
- Nothing posts without Leo's explicit approval for the first few batches
- No legal/compliance decisions delegated
- No spending, no destructive changes

## First step
Spin up the Content Agent as a cron job. Posting Agent follows once the ready-queue pattern is proven.
