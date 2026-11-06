# CODEBASE_AUDIT — LuLevels v1.0.0 (baseline)

**Audit date:** 2026-11-06 · **Baseline:** `tradingview/baseline/LuLevels_v1.0.0.pine` (SHA-256 `fc6fdedd…0de0a9`, identical to `LuLevels.pine` at commit `fdec02d`)

## 0. Method and limits

| Method | Done | Notes |
|---|---|---|
| Line-by-line manual review of all source and docs | ✓ | Every file in the repo listed in §1 |
| Structural parse with `pynescript` (open-source Pine parser, v5 grammar) | ✓ | Parses; this does **not** check v6 type and qualifier rules |
| Python reference checks of suspect algorithms (`tests/audit_checks.py`) | ✓ | 2 defects confirmed (D2, D3) |
| Compile in the TradingView Pine Editor | ✗ | `www.tradingview.com` is blocked by this session's network policy |
| Check against the official Pine v6 reference manual | ✗ | Same block |
| Replay or real-time testing on TradingView | ✗ | Same block |
| Check concepts against ICT / Gatie Trades sources | ✗ | YouTube is blocked; see `LIMITATIONS_AND_OPEN_QUESTIONS.md` |

**So every finding marked "reasoned" below is a code-reading conclusion, not an observed runtime result.**

## 1. Inventory

| Item | Content |
|---|---|
| Source files | `LuLevels.pine` (1,124 lines, Pine v6, `indicator(overlay=true)`); no libraries or imports |
| Docs | `README.md` (definitions, alert setup, data notes) |
| Config | Inputs only (≈85 inputs in 10 groups); no external config |
| External data | 2 × `request.security`: prior trading-day H/L (`:675`) and DXY context (`:685`) |
| Alerts | 7 `alert()` event types via `f_fire` (`:247`), plus 7 `alertcondition`s (`:1118-1124`) |
| Drawings | lines, boxes, labels (500 each declared); 1 table (`:967`) |
| Tests before this audit | **None** |
| Strategy / backtest | None (indicator only) |
| Other repo content | `index.html` (unrelated website) |

## 2. Implemented concepts and exact detection logic

| # | Concept | Logic as implemented (file:line) | When it is evaluated |
|---|---|---|---|
| C1 | Session membership | `not na(time(timeframe.period, sess + ":1234567", tz))` (`:647-658`) | every bar |
| C2 | Session occurrence | ID = wall-clock start timestamp; bars after midnight map to the previous day via `base − 86 400 000` (`f_anchor :203`) | every bar |
| C3 | Developing session high/low | running max/min of `high`/`low` while active (`step :371`) | every tick (live) |
| C4 | Session completion | close of the bar with `time_close ≥ endTs`, or fallback on the first bar not in the occurrence (`:404`, `:375`) | closed bar |
| C5 | Resolution guard ("exact") | first bar starts at the window start, `tf ≤ window`, and `window % tf == 0` (`:391`) | at session start |
| C6 | Session liquidity levels | completed H/L → `Level` objects (`f_spawnLevels :445`); line drawn **from the extreme bar** (`:449`) | at completion |
| C7 | Touch | high: `high ≥ level`; low: `low ≤ level` (`:467`) | close (or every tick in intrabar mode) |
| C8 | Sweep | high: `high ≥ level + N·tick AND close < level` (`:474`); mirrored for lows | closed bar, same bar only |
| C9 | Break | high: `close > level` (`:475`) | closed bar |
| C10 | Prior trading-day H/L | `request.security(tickerid, "D", [high[1], low[1], time[1]], lookahead_on)` (`:675`) | new daily bar |
| C11 | RTH open / previous RTH close | open of the first RTH bar; close of the last RTH bar of the previous occurrence (`:747`, `finish :356`) | RTH start |
| C12 | Opening gap, CE, quarters | top/bottom = max/min(open, previous close); CE = 50%; quarters from the bottom (`f_gapNew :497`) | RTH start |
| C13 | Flat gap | `rng == 0 or rng < gapMinTicks·mintick` (`:501`) | creation |
| C14 | Gap CE touch / fill | `low ≤ CE ≤ high`; fill: gap up `low ≤ pc`, gap down `high ≥ pc` (`:570`, `:577`) | close / intrabar |
| C15 | First presented FVG | bull `low > high[2]`, bear `high < low[2]`, size ≥ minimum (`:689-690`); candle rule (`:779`); window (`:780`); box from `time[2]` (`:786`) | closed bar |
| C16 | FVG mitigation | Touch / CE / full wick / full close (`:768`) | closed bar after confirmation |
| C17 | Macro windows | same session engine; box follows live H/L; completion alert (`f_macroProc :843`) | live / closed bar |
| C18 | NDOG / NWOG | `close[1]` vs `open` at `timeframe.change("D")` (or custom session) / `timeframe.change("W")` (`:811`, `:816`) | rollover bar |
| C19 | Opens (dashboard) | open of the bar starting exactly at HH:MM in tz (`f_openAt :209`); exchange-day and week opens on rollover | every bar |
| C20 | DXY context | same-TF `request.security` of DXY; `(close − ref open)/ref open`, neutral band (`:678-685`, `f_bias :981`) | last bar |
| C21 | Label rail | merges labels within ATR × fraction, placed at the group mean (`:937`) | last bar |
| C22 | Alert dedupe | one-way flags per object, plus `freq_once_per_bar(_close)` (`:247`) | per event |

## 3. Repainting, lookahead and knowledge-time review (reasoned)

| Path | Data | Lookahead / future leakage | Repaint on history vs real-time | Verdict |
|---|---|---|---|---|
| Session H/L (developing) | chart bars | none | updates intrabar **by design**, labelled `~` | OK, provisional state is labelled |
| Session H/L (completed) | chart bars | none | fixed at completion | OK, but see **D5** (drawn from an earlier bar) |
| Sweep / break / FVG / macro events | chart bars | none; `barstate.isconfirmed` gate | none expected | OK (not TV-verified) |
| Touch / gap CE / fill (intrabar mode) | chart bars | none | the alert fires intrabar; the visual can flicker until close (rollback) | OK by design; **undocumented** (D10) |
| Prior-day H/L | `"D"` with `[1]` + `lookahead_on` | none (standard non-repainting idiom) | none | OK; session-type ambiguity for stocks (**D8**) |
| DXY context | other symbol, same TF, `lookahead_off` | none | developing on the real-time bar; dashboard only | OK; staleness not shown (**D11**) |
| `timeframe.change("D"/"W")` | chart | none | none | OK; daily boundary on stocks with ETH unverified (**D8**) |

No `lookahead_on` without `[1]`, no negative offsets, no `ta.pivothigh`/`pivotlow` (so no pivot-confirmation delay to mis-plot), and no `barmerge.gaps_on`.

## 4. Defects and risks (ranked)

| ID | Severity | Status | Finding | Location | Proposed correction |
|---|---|---|---|---|---|
| D1 | **High** | open | The script has **never been compiled** in TradingView; v6 semantics are unverified (`alert()` inside functions, `input.session` with `2000-0000`, tuple + `ignore_invalid_symbol`, `str.tostring` patterns) | whole file | User compiles it, or allows `tradingview.com` access |
| D2 | Medium | **confirmed** (`audit_checks.py`) | A session crossing midnight is split into **2 occurrences** on DST-change weekends: `base − 86 400 000` is not "same wall-clock time yesterday" across a 23h/25h day. Affects 24/7 markets (crypto) and the custom-day NDOG mode; CME and stocks are closed at those hours | `f_anchor :203` | Build the start from the previous **calendar date** (local midnight − 1h → y/m/d → `timestamp(tz, …)`). Fix verified in Python: 1 occurrence |
| D3 | Medium | **confirmed** (`audit_checks.py`) | Float comparisons in price units misclassify **exact one-tick** distances (a BTC 1-tick gap gives 0.0099999…, so it is "flat"). The same pattern exists for sweep penetration and FVG minimum size | `:501`, `:474`, `:688-690` | Compare whole tick counts: `math.round(diff / syminfo.mintick)` |
| D4 | Medium | reasoned | `endTs = sid + duration` ignores DST inside the occurrence, so normal completion is skipped and the fallback completes one bar late (24/7 markets only) | `:385` | `endTs = timestamp(tz, end date, eh, em)` |
| D5 | Medium | reasoned | **Knowledge-time presentation:** a completed session level is drawn from the bar that made the extreme, so on history it looks known before the session ended. Alerts carry the event bar time but not formation vs confirmation times | `:449`, `:786`, `f_json :240` | Draw a faint pre-confirmation segment and the solid level from completion. Add `formed_time` and `confirmed_time` to the JSON |
| D6 | Medium | methodology, **unsourced** | Sweep = same-bar close-back only. Multi-bar reclaims, displacement and "run on stops" are not modelled. Whether this matches ICT or Gatie needs sources | `:474` | Decide after research (Phase 3); possible option "reclaim within N bars" |
| D7 | Low | reasoned | A bar that pierces then closes **exactly at** the level is neither a sweep nor a break, so the level stays live. Undocumented | `:474-475` | Document it, or make close-at-level count as reclaim (sourced choice) |
| D8 | Medium | unverified | For stocks with ETH on: whether `request.security(tickerid,"D")` and `timeframe.change("D")` use RTH or extended daily bars | `:675`, `:660` | Verify on TradingView; if needed, derive PDH/PDL from the RTH session tracker instead |
| D9 | Low | reasoned | "vs RTH open" keeps showing the **previous** day's RTH open from 16:00 until the next 09:30, unlabelled | dashboard | Label it "prev RTH O" outside RTH, or show N/A |
| D10 | Low | by design | Intrabar touch visuals can flicker within the real-time bar | `f_procGaps`, `f_procLevels` | Document it, or draw intrabar visuals only after confirmation |
| D11 | Low | reasoned | DXY values can be stale on chart bars where DXY has no bar (`gaps_off` forward-fills); no staleness flag | `:685` | Return the DXY `time` and show "stale" when it lags |
| D12 | Low | reasoned | Both `alert()` and `alertcondition` alerts can be created for the same event, giving duplicate notifications **if the user creates both** | `:1118+` | Document it (already partly in README) |
| D13 | Info | unverified | Times treated as ICT conventions are **unsourced**: Asia 20:00–00:00, London 02:00–05:00, macro times, NDOG 17:00→18:00, NWOG Fri→Sun, opening-gap close (16:00 vs other conventions), first-presented-FVG window | inputs | Validate in Phase 4 against the knowledge base |
| D14 | Info | reasoned | `alert()` JSON `detail` strings are not escaped. Safe today (fixed strings), fragile if names become user-editable | `f_json :240` | Escape `"` and `\` |

Performance (reasoned): each bar runs 12 `time()` calls and loops over ≤ ~48 levels; drawing totals stay far below 500 at default retention. No issue expected; unmeasured.

## 5. Missing tests

There were no tests in the project before this audit. Still missing:

1. Positive and negative fixtures for every concept (C3–C22).
2. Session boundaries, including half-days, missing bars, and DST weeks in March and November (US and EU dates differ).
3. Resolution guard across 1s/1m/3m/5m/15m/30m/1h/4h on CME, stocks with and without ETH, FX and crypto.
4. Real-time vs history: replay-mode check that each closed-bar event fires once and at the same bar as on history.
5. Alert dedupe across reloads; check that the JSON is valid.
6. Drawing-limit stress test (1m, maximum retention, long history).
7. Compile check in the Pine Editor (D1).

## 6. Concepts in the mission that are NOT implemented

Market structure (swings, BOS, MSS), displacement, equal highs/lows (relative equal liquidity), order blocks, breakers, mitigation and rejection blocks, inverse FVG, BPR, premium/discount and equilibrium, OTE / Fibonacci dealing ranges, SMT divergence, Silver Bullet and 2022-model windows, Judas swing, higher-timeframe Power-of-Three candles, daily/weekly bias and draw on liquidity, and NY AM/PM kill zones. The midnight open exists only as a dashboard value, not as a level on the chart.

None of these will be added until the knowledge base gives an operational definition (see `IMPLEMENTATION_PLAN.md`).
