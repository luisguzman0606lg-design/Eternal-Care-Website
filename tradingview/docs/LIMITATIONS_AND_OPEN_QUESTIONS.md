# LIMITATIONS_AND_OPEN_QUESTIONS

_Last updated: 2026-11-06 (after the Phase 1 audit, before any research)_

## 1. Access blockers (observed, not assumed)

| Resource | Needed for | What happened | What unblocks it |
|---|---|---|---|
| `www.youtube.com`, `youtube.com`, `i.ytimg.com` | Video pages, public captions/transcripts, playlists (Phase 2) | Session proxy **refused CONNECT (403, policy denial)** on 2026-11-06 | Add `www.youtube.com` (and `youtube.com`) to the environment's allowed hosts |
| YouTube Data API v3 (`www.googleapis.com`) | Metadata only: titles, dates, durations, playlists, descriptions | Host is reachable, but **no API key is configured** | A YouTube Data API key, saved as a network credential for `www.googleapis.com`. Note: the Data API cannot download captions of other people's videos, so transcripts still need YouTube access |
| `www.tradingview.com` | Official Pine v6 reference, compiling, replay testing | Host not resolvable in this session | Allow the host for the docs. Compiling and replay need **you** to paste the script into the Pine Editor and report errors or screenshots |
| `www.fluxcharts.com` | The original reference page | Host not resolvable | Allow the host, or supply screenshots |
| Gatie Trades channel | Phase 2 research | Web search returned **no result that identifies the channel** | The exact channel URL or `@handle`, so identity can be checked before collecting videos |
| Labeled chart examples | Precision/recall (Phase 7) | None exist | Your labeled examples: symbol, timeframe, timestamp, concept, and expected result |

**Research rules while blocked:**
- No transcript, timestamp or quote will be written unless it was retrieved from the source.
- Third-party transcript mirrors and summary sites that appear in search results will **not** be used as evidence of what ICT or Gatie said. They are unofficial and their accuracy cannot be checked. I could log them only as leads if you explicitly allow that.
- Full visual review of video content (chart drawings on screen) is not possible with caption-only access. Concepts that depend on what is drawn will be marked "needs screenshot/clip".

## 2. Open questions (methodology; to be answered from sources)

| # | Question | Affects |
|---|---|---|
| Q1 | Which close defines the RTH/opening gap for index futures in ICT usage (16:00, 16:14/16:15, or settlement)? The current code uses the last bar of the 09:30–16:00 window | C11–C14 |
| Q2 | Definition of the "first presented FVG": does the window start at 09:30 or 09:31? Is it limited to 09:30–10:00? Must all three candles be after the open? | C15 |
| Q3 | Are NDOG = 17:00 close → 18:00 open and NWOG = Friday 17:00 → Sunday 18:00 the ICT definitions for CME, and what applies to other markets? | C18 |
| Q4 | Kill zone and macro times: exact ICT times, and their DST handling | C1, C17 |
| Q5 | What counts as a liquidity sweep or raid: a same-bar close-back, a multi-bar reclaim, a displacement requirement, or a minimum penetration? | C8 (D6) |
| Q6 | Daily/weekly bias and "draw on liquidity": is there an operational rule, or is it discretionary? If discretionary, it will not be automated | new |
| Q7 | Swing-point definition (number of bars per side) and the BOS vs MSS distinction, with or without displacement | new |
| Q8 | Order block definition: last opposite candle before displacement? Is a body or a wick range used? What invalidates it? | new |
| Q9 | Where Gatie Trades' explanations differ from ICT's own definitions | all |

## 3. Technical open questions (Pine / TradingView; to be checked on the platform)

- T1: Does `request.security(syminfo.tickerid, "D")` follow the chart's ETH setting for stocks? (D8)
- T2: Does `timeframe.change("D")` on stocks with ETH roll over at the start of the pre-market or at 09:30? (D8)
- T3: Is `time()` session membership correct for `2000-0000` (end at midnight)?
- T4: Do all v6 constructs used compile (D1)?

## 4. Standing limitations

- This is an indicator, not a strategy. **No profitability or win-rate figures will be produced.** A separate strategy with explicit costs would be needed for backtests.
- Even after the fixes, "non-repainting" can be claimed only per signal path, and only for paths that pass replay tests on TradingView.
