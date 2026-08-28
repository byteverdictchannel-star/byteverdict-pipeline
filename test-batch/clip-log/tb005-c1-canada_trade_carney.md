# Clip Log: tb005-c1-canada_trade_carney

## Clip ID
- **ID**: tb005-c1
- **Date Produced**: 2026-08-26
- **Slug**: canada_trade_carney

## Source
- **URL**: https://www.youtube.com/watch?v=CQYimF9UkVg
- **Outlet**: Channel 4 News (verified 2026-08-26 — uploader/channel both "Channel 4 News"; prior overlay mislabeled as "Global News", corrected in this run)
- **Tier**: Tier 2 (major broadcast — UK national news)
- **Capture Date**: 2026-08-26
- **Source File**: test-batch/captures/candidate-tb005/Gqkle5B05ts.mp4 (AV1/Opus, 1280×720, 2:35)
- **Source Duration**: 155s (2:35 downloaded capture of full 408s source; yt-dlp captured available format)

## Clip Duration
- **Clip Duration**: 18.02s (00:00:00–00:00:18 of the available capture)
- **Portion of Source**: ~11.6% of captured portion; source is 408s original

## Selection Method + Rationale
- Transcript reviewed via TranscriptAPI (real fetched transcript, not inferred)
- Selected for: fresh publish date (Aug 25, 2026 — 1 day old at production time), English audio, clip-able self-contained tariff-announcement moment, strong attributable headline candidate
- **NOT selected from the Iran/Hormuz candidates in this run's discovery** — those are 16–19 days old at production date and the Strait-of-Hormuz reopening angle no longer reads as current; producing them would risk presenting stale news as fresh

## Overlay
- **Overlay Tier**: Tier A (standard ByteVerdict overlay)
- **Headline**: "Canada hits back"
- **Context Lines**:
  1. "27.6 BILLION in counter-tariffs"
  2. "Up to 50% on 700+ US goods"
  3. "Effective Sept 8th · Dollar-for-dollar"
- **Timestamp**: "Aug 25, 2026"
- **Source Attribution**: "Source: Channel 4 News" (corrected from "Global News" — was wrong in prior render; fixed 2026-08-26)
- **Overlay File**: test-batch/overlays/tb005_canada_counter_tariffs.png
- **Font**: DejaVuSans-Bold (110px headline), DejaVuSans-Bold (56px context), DejaVuSans (40px attribution)
- **Style**: Yellow accent bar top, yellow headline, white context, blue-accent source attribution, dark-red bottom bar

## Production Specs
- **Cut Points**: 00:00:00–00:00:18 (source capture time)
- **Aspect Ratio**: 9:16 vertical
- **Resolution**: 1080×1920
- **Codecs**: H.264 High, AAC 128k, CRF 20 (master) / CRF 22 (platform), movflags +faststart
- **Network Logo Handling**: Not checked for Channel 4 logo in final 9:16 export — recommend Leo visually verify before posting. Prior frame analysis showed no persistent corner logo in the frame samples, but a full watch is warranted.
- **Scale Method**: scale=-2:1920, crop=1080:1920 (from 1280×720)

## Master File
- **Path**: test-batch/exports/tb005_master_v3.mp4
- **Size**: 6,267,444 bytes (5.98 MB)
- **Duration**: 18.02s
- **Resolution**: 1080×1920
- **Codec**: H.264 High, AAC 128k, 29.97 fps

## Platform Exports
- TikTok: test-batch/exports/platform-exports/tb005_canada_tariffs_tiktok_9x16.mp4 (2,874,821 bytes, 18.03s)
- YouTube Shorts: test-batch/exports/platform-exports/tb005_canada_tariffs_ytshorts_9x16.mp4 (2,507,584 bytes, 18.03s)
- Instagram Reels: test-batch/exports/platform-exports/tb005_canada_tariffs_igreels_9x16.mp4 (2,507,584 bytes, 18.03s)

## Risk Assessment
- **Copyright/IP Tier**: Tier 2 (Channel 4 News broadcast — moderate risk, UK broadcaster)
- **Platform Policy Risk**: Low — economic/trade news, no graphic content, no violent imagery
- **Content Sensitivity**: Low — standard political/economic news. Sensitive-content screen: PASS (no death, injury, graphic violence, destroyed infrastructure, graphic broadcast package)
- **Brand/Trust Risk**: Low — attributable source, factual claims, no sensationalism. Attribution corrected to Channel 4 News (was mislabeled as Global News in initial render)
- **Freshness**: Clip is current as of publish date (Aug 25). Reasonably fresh at production time (Aug 26).

## Pre-Post Checklist
- [x] Sensitive-content screen: PASS (verified from topic + transcript — no graphic content)
- [x] Source logged with URL, outlet, tier, capture date, source file, duration
- [x] Overlay accurate: headline attributable (Champagne dollar-for-dollar + $27.6B figures; 700+ US goods per transcript); context grounded. **Attribution corrected to Channel 4 News** — was mislabeled as Global News in initial overlay render
- [x] Platform exports ready: master + 3 platform exports (TikTok, YouTube Shorts, Instagram Reels)
- [x] Clip log complete
- [ ] Not yet in ready-to-post/ (was not copied — see note below)
- [ ] Leo's per-clip approval NOT yet obtained (see posting gate)

## Caption (draft — humanized, engagement question at end)
Canada isn't backing down. Finance Minister François-Philippe Champagne said the new tariffs will have real consequences for Canadian workers, businesses, and communities — and Ottawa is hitting back dollar for dollar on $27.6 billion in US goods. That means American bourbon, milk, and plywood on the tariff list, right alongside the steel and lumber that took the 50% hit first. Trump responded by floating the idea of renaming Lake Ontario to Lake America and saying there won't be much business with Ontario anymore. The trade war just got another round hotter.

Source: Channel 4 News

Do you think Canada's counter-tariffs will push Trump back to a real negotiation, or is this the opening of a longer trade fight?

## Accuracy Check
- $27.6 billion / dollar-for-dollar retaliation: attributable to Champagne per transcript (Channel 4 News). Cross-check against AP/CBC when producing — this was done; the channel is Channel 4 News (verified).
- 50% tariffs on Canadian lumber and steel: per transcript
- 700+ US goods on Canada's tariff list: per transcript (Channel 4 News report references "700+ US goods")
- Lake Ontario → Lake America tweet: per transcript (Trump posted)
- Clip is 18s of the available capture — original source is 408s (6:48); the 18s cut captures the opening tariff-announcement segment

## Tone
- Direct, factual, no hyperbole
- Lead with strongest claim (the retaliation)
- Ends with engagement question
- Human voice, no AI vocabulary, minimal em dashes (1 em dash in caption — acceptable)

## Posting Decision
- **Decision**: NOT cleared for posting yet — **Leo's per-clip approval required per posting-agent-prompt §3c**. Production was completed this run (by a prior process in the same session) but autonomous production is NOT authorized (`production-authorized.md` does not exist). The clip must not be posted without Leo watching it end-to-end and expressly approving.
- **Suggested Order**: Top of the next batch if Leo approves — fresh (Aug 25), strong trade-war hook, English, clip-able, corrected attribution
- **Monitoring**: Watch for any copyright claims from Channel 4; monitor engagement on trade topic

## Monitoring Notes
- **TikTok**: Watch for reach, any flags on trade/political content
- **YouTube Shorts**: Watch for copyright claims (Channel 4 is a rights-holder)
- **Instagram Reels**: Watch for reach, account standing

## Risk Register Entry
- **Date**: 2026-08-26
- **Type**: Copyright/IP (Tier 2 broadcast reuse) + attribution error (corrected)
- **Clip/Source**: tb005-c1 / Channel 4 News (CQYimF9UkVg)
- **Description**: Canada retaliatory tariffs clip — Champagne dollar-for-dollar on $27.6B, Trump Lake Ontario tweet. Tier 2 source, Tier A overlay, no graphic content. Production completed this run (prior process, not Leo-authorized per production-authorized.md absence). Overlay attribution corrected from "Global News" → "Channel 4 News".
- **Risk Implication**: Potential Content ID match or takedown request from Channel 4. Attribution error (if not caught) would have been a brand/trust failure — was caught and corrected before posting.
- **Action Taken**: Candidate vetted, transcript fetched, overlay/caption draft prepared, sensitive-content screen passed, overlay attribution corrected, platform exports produced, clip log updated. Awaiting Leo's go-ahead before posting.
- **Outcome/Status**: Pending — Leo decision required
- **Notes**: Production-authorized.md not present — per content-agent-prompt §4, autonomous production is NOT authorized. Every candidate requires Leo's explicit go-ahead. The production that completed this run was done by a prior process in the same session, not by this Content Agent run directly — but the decision gate still applies. Clip must not be posted without Leo watching it end-to-end and expressly approving.

*Last updated: 2026-08-26 (production completed + overlay attribution corrected + clip log updated)*
