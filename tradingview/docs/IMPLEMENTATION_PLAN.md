# IMPLEMENTATION_PLAN (draft — awaiting approval)

The plan has stages. Each stage ends with verification, and nothing in a research-gated stage starts without knowledge-base evidence.

## Stage 0 — Baseline and audit ✅
- Baseline preserved: `baseline/LuLevels_v1.0.0.pine` (hash recorded in `CODEBASE_AUDIT.md`).
- `CODEBASE_AUDIT.md`, `LIMITATIONS_AND_OPEN_QUESTIONS.md`, and `tests/audit_checks.py` (2 confirmed defects).

## Stage 1 — Engineering fixes (no methodology change; can start now)
| Step | Change | Verification |
|---|---|---|
| 1.1 | Fix D2 (DST occurrence split) and D4 (DST end time) | Python reference fixtures for US and EU DST weeks |
| 1.2 | Fix D3: tick-integer comparisons for flat gap, sweep penetration and FVG minimum | Fixtures with BTC/EURUSD/ES tick sizes |
| 1.3 | Fix D5: knowledge-time drawing (faint until confirmed) and `formed_time`/`confirmed_time` in the JSON | Python check of the event log; you check visually |
| 1.4 | Fix D9, D11, D14; document D7, D10, D12 | Code review |
| 1.5 | **Python reference implementation** of the existing modules (sessions, gaps, FVG, levels, events) over OHLCV fixtures, plus a deterministic test suite (positive/negative, edge cases, DST, half-days, missing bars) | `TEST_RESULTS.md` with real outputs |
| 1.6 | **Compile gate (needs you):** paste into the Pine Editor and report errors; run the replay checklist | Your report |

## Stage 2 — Research acquisition (blocked until access is granted)
1. Confirm channel identity: ICT (`@InnerCircleTrader`, to be confirmed on youtube.com) and Gatie Trades (needs your URL).
2. `VIDEO_RESEARCH_INDEX.csv`: full metadata inventory with `yt-dlp --skip-download` (title, URL, date, playlist, duration, caption availability).
3. Transcript collection for videos with public captions only; the status of every video recorded; nothing invented.
4. Priority order: ICT 2022 Mentorship → market structure, liquidity, FVG, OB, PD-array videos → time/price and kill zones → Silver Bullet and models → Gatie explanations of the same topics.

## Stage 3 — Knowledge base
- `ICT_GATIE_KNOWLEDGE_BASE.md`: each concept with an operational definition, conditions, confirmation, invalidation, context, and a quote with URL and timestamp, plus a confidence rating.
- `SOURCE_CONFLICTS.md`: ICT vs Gatie differences, kept as separate versions.
- Each rule is classified as *directly supported*, *interpretation*, *implementation assumption*, or *unverified*.

## Stage 4 — Validate existing concepts
- `CONCEPT_VALIDATION_MATRIX.csv`: C1–C22 × sources → accurate / incomplete / ambiguous / incorrect, with the proposed correction and its references.
- Apply only the corrections that have evidence. Add modes (ICT Strict / Gatie / Hybrid) **only** where the sources specify behaviour.

## Stage 5 — New modules (each gated on knowledge-base evidence and Pine feasibility)
Planned order, chosen by dependency:
1. Swings with explicit confirmation delay (plotted at the confirmation bar, with the pivot time recorded separately)
2. BOS/MSS
3. Displacement
4. Equal highs/lows
5. IFVG/BPR
6. Order blocks and breakers
7. Premium/discount and OTE on a defined dealing range
8. Kill zones and Silver Bullet windows
9. SMT (correlated symbol via `request.security`, same timeframe, confirmed bars only)
10. HTF PO3 candles

Setup scoring will be built only if the sources define qualifying criteria. Otherwise the indicator stays contextual.

## Stage 6 — Validation and UX
- Replay tests, multi-instrument checks, and drawing-limit stress tests.
- Precision/recall only against your independently labelled examples, with sample sizes reported.
- `TEST_RESULTS.md`, `CHANGELOG.md`, updated README.

## Decisions needed from you
1. Network access to YouTube, and optionally a YouTube Data API key.
2. The Gatie Trades channel URL or handle.
3. Whether to start Stage 1 (engineering fixes plus the Python test harness) **now**, while research access is pending.
4. Whether you can run TradingView compile and replay checks and send me the results or screenshots.
5. (Optional) Labelled chart examples for precision/recall.
