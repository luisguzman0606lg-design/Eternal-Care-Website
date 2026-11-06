# LuLevels — Session & Liquidity Suite (Pine Script v6)

`LuLevels.pine` is a native TradingView overlay indicator. It plots the RTH open and opening gap, the first presented FVG, session liquidity, macro windows, NDOG/NWOG and a compact dashboard on the chart's real symbol and data, and it raises alerts. It shows context only: it has **no buy/sell rules and makes no performance claims**.

---

## 1. Reference verification status (read first)

| Item | Status |
|---|---|
| Reference page `fluxcharts.com/creator/gatietrades` | **Not inspected.** The build environment's network policy blocked the host. |
| Public descriptions of "GEMS Po3" | **None found.** A web search returned nothing relevant. |
| Screenshots / recordings | None supplied. |
| Official Pine v6 docs (`tradingview.com`) | **Not reachable from the build environment.** The code follows v6 semantics as known up to the author's training data. See §9. |

**So none of this indicator's behaviour is verified against the reference.** Every feature follows the written specification. Each formula below is an **implementation choice, documented so you can check or change it**. Nothing here reproduces or claims to match any proprietary or undisclosed logic, and no third-party branding is used.

---

## 2. Install

1. Open TradingView and go to **Pine Editor** → **New** → **Blank indicator**.
2. Replace the editor contents with `LuLevels.pine`, click **Save**, then **Add to chart**.
3. Use an **intraday** chart. On daily or higher charts the dashboard reports "Unsupported" and nothing is drawn.
4. Stocks: turn on **extended hours** (chart settings → Symbol → Session) if you want Asia, London, Pre-market or Overnight levels. Without it those sessions have no bars, and the dashboard says `No bars: …`.

---

## 3. Time model: four distinct "days"

| Concept | Source in the script | Used by |
|---|---|---|
| **Calendar day** (session timezone) | Day of month changes at 00:00 in `Session timezone` | Midnight open, custom open |
| **Exchange trading day** | The symbol's own daily bars (`timeframe.change("D")`, `request.security(…"D"…)`) | Prior-day H/L, exchange-day open, NDOG (default mode) |
| **RTH session** | `RTH session` input (default 09:30–16:00 ET) | RTH open, previous RTH close, opening gap, first FVG, previous-session H/L |
| **Futures overnight** | `Overnight (futures ETH)` input (default 18:00–09:30 ET, off by default) | Overnight H/L, kept separate from Asia, London and Pre-market |

The default timezone is `America/New_York`. DST is handled by TradingView's timezone database, so all times stay local wall-clock times. **The default times are a US equity-session preset.** For other markets, change the sessions and timezone.

| Default window | Time (ET) | Intended meaning |
|---|---|---|
| RTH | 09:30–16:00 | US equity regular hours |
| Asia | 20:00–00:00 | Common FX/ICT-style Asia window |
| London | 02:00–05:00 | Common London window |
| Pre-market | 04:00–09:30 | US equity pre-market |
| Overnight (off) | 18:00–09:30 | CME Globex overnight up to RTH |
| Macros | 08:50–09:10, 09:50–10:10, 10:50–11:10, 11:50–12:10, 13:10–13:40, 15:15–15:45 | Configurable; editable defaults |

---

## 4. Exact definitions

### 4.1 Session tracking (all sessions and macros)
- **Membership:** a chart bar belongs to a window if TradingView's `time(timeframe.period, session, tz)` is non-`na`. In practice, that means the bar opens inside the window.
- **Occurrence ID:** the timestamp of the window's start. Bars after midnight in a window that crosses midnight belong to the previous day's start. This keeps back-to-back days separate on charts with no out-of-session bars (for example, stocks with RTH data only).
- **Developing extremes:** the high and low update every tick while the window is open. They show as `AS H~` / `AS L~`, and the box edges follow them.
- **Completion:** the session completes on the close of the bar whose close time reaches the window end. As a fallback, it also completes on the first bar that no longer belongs to the occurrence, for example after an early close or a data gap. On completion, the high and low become **fixed liquidity levels**; they are never recalculated.
- **Resolution check ("exact"):** a window is supported only when (a) its first bar starts exactly at the window start, (b) the bar duration is no longer than the window, and (c) the window length is a whole multiple of the bar duration. If any of these fail, the window produces **no levels, gap or alerts**, and the dashboard's `Data` row lists it as `TF too coarse`. Example: RTH on a 1H CME chart (bars start at :00, not 09:30) is unsupported, while 30m works.

### 4.2 RTH open and opening gap
- **RTH open** = the `open` of the **first chart bar of the current RTH window**.
- **Previous RTH close** = the `close` of the **last chart bar inside the previous RTH window**. This is **never** the daily settlement or the daily bar's close.
- **Gap boundaries:** top = max(open, prev close), bottom = min(open, prev close).
- **CE (50%)** = bottom + 0.5 × size. **25% / 75%** are measured **from the bottom**.
- **Flat gap:** a size below `Treat gaps smaller than (ticks) as flat` (or exactly 0) is labelled *Flat*. Flat gaps fire no CE or fill events.
- **CE touch:** the first bar, from the opening bar onward, whose range contains the CE (`low ≤ CE ≤ high`).
- **Fill:** gap up → `low ≤ prev close`; gap down → `high ≥ prev close`.
- **Lifetime:** the gap stays live until the next RTH open, then becomes historical (grey, dotted).

### 4.3 First presented FVG
- **Detection timeframe:** always the **chart timeframe**. Above `Max detection timeframe` (default 15m), or when RTH is not "exact", the module reports **Unsupported**.
- **Bullish:** `low > high[2]`, zone = `high[2] … low`. **Bearish:** `high < low[2]`, zone = `high … low[2]`.
- **Confirmation:** evaluated only on a **closed** third candle (`barstate.isconfirmed`).
- **Candle rule:**
  - *All 3 candles inside RTH* (default): candle 1 is the RTH opening bar or later.
  - *Candle 1 may precede the open*: candles 2 and 3 are inside RTH.
- **Search window:** 0 = the whole RTH session. Otherwise the third candle must open within N minutes of the RTH open.
- **Minimum size:** set in ticks, % of price, or a multiple of ATR(14). The gap size must be ≥ the minimum.
- **Mitigation** (closed bars after confirmation; choose one): Touch (enters the zone), Midpoint (reaches CE), Full fill (wick through the far edge), or Full fill (close beyond the far edge). The dashboard also shows whether the zone has been *tested* or reached CE.
- **States:** Waiting for RTH → Searching… → Active / Mitigated, Expired (next RTH open) or None this session. Unsupported is shown instead when resolution does not allow detection.

### 4.4 Session liquidity
Levels come from completed Asia, London, Pre-market, Overnight and RTH (previous-session) windows, plus the **prior exchange trading day** high/low. The prior-day values come from `request.security(sym, "D", high[1]/low[1], lookahead_on)`, a non-repainting pattern. For CME futures that is the 18:00–17:00 ET Globex day.

Each level has one of three mutually exclusive outcomes, all evaluated after the level exists:

| Event | High level | Low level | Timing |
|---|---|---|---|
| **Touch** | `high ≥ level` | `low ≤ level` | bar close (or intrabar, if selected) |
| **Sweep** | `high ≥ level + N ticks` **and** `close < level` | `low ≤ level − N ticks` **and** `close > level` | bar close only |
| **Break** | `close > level` | `close < level` | bar close only |

`N` is the `Sweep: minimum penetration` input (default 1 tick). After a sweep or break, the level stops extending, turns grey and dotted, and is no longer tracked. A sweep also gets a small ✕ marker (Standard and Detailed presets). Untouched levels from retained sessions keep extending to the label rail.

### 4.5 Macro windows
There are six configurable windows. The box top and bottom follow the developing high and low live. **Macro range completed** fires on the close of the window's last bar. The alert carries the high, low, window start and window end.

### 4.6 NDOG / NWOG
- **NDOG** = the `close` of the last bar **before** the day rollover vs. the `open` of the first bar **after** it.
  - *Exchange trading day* (default): the rollover is the symbol's daily-bar boundary. CME index futures: 16:59 bar close → 18:00 bar open. Stocks with RTH data only: identical to the RTH opening gap.
  - *Custom day session*: the rollover is the first bar of the `Custom day session` input. Use this for stocks with extended hours, FX, or crypto when the exchange day isn't what you want.
- **NWOG** = the `close` of the last bar of the prior week vs. the `open` of the first bar of the new week, using the symbol's **weekly-bar** boundary. CME: Friday 16:59 close → Sunday 18:00 open. On 24/7 crypto this is usually flat.
- Both use the same CE, fill and flat rules as §4.2. The newest NDOG/NWOG is live; older ones are kept faded (`NDOGs kept`, `NWOGs kept`).

### 4.7 Dashboard
- **Opens:** RTH open, midnight (00:00 in the session timezone), exchange-day open, week open, and an optional custom HH:MM. Each shows `(close − open) / open` in %. A row shows **N/A** when the chart has no bar starting exactly at that time; no nearby bar is substituted.
- **DXY context:** this is a **custom price-relative-to-open interpretation**, not a reproduction of any third-party formula. It is evaluated on the DXY symbol's own bars at the chart timeframe:
  - Intraday: `Δ% = (DXY close − DXY open at 00:00 / 08:30 / 09:30) / that open × 100`
  - Daily: `Δ% = (DXY close − DXY exchange-day open) / that open × 100`
  - Up if Δ% > band, Down if Δ% < −band, otherwise Flat (default band ±0.05%). N/A if the symbol is unavailable or has no bar at the reference time.
- **Detailed preset:** adds the nearest untouched liquidity above and below price, the time left in RTH, and the live macro range.
- **Data row:** lists anything that cannot be computed accurately at this resolution or with this data.

---

## 5. Display presets

| | Minimal | Standard | Detailed |
|---|---|---|---|
| RTH open, prev close, gap CE | ✓ | ✓ | ✓ |
| Gap 25/75% | – | ✓ | ✓ |
| First FVG | ✓ | ✓ | ✓ |
| Liquidity levels | latest session only | + history | + history |
| Session boxes, macro boxes, NDOG/NWOG drawings | – | ✓ | ✓ |
| Sweep ✕ markers, developing `~` labels | – | ✓ | ✓ |
| Prices on labels, macro range text, NDOG/NWOG quarters | – | – | ✓ |
| Dashboard | session, macro, RTH-open, DXY | + all opens, FVG, gaps | + liquidity ↑/↓, RTH time left |

**Clutter control:** every active level is labelled in a single **label rail** to the right of the last bar. Labels closer than `Merge labels closer than (× ATR14)` are merged into one chip (for example `AS H · PDH`), and hovering a chip shows the full names and prices. Active items use solid lines in their module colour; historical items are grey and dotted, with faded fills. The theme follows the chart background automatically (Auto) or can be forced to Dark or Light.

---

## 6. Alerts

### 6.1 Events

| Event | Fires when | Timing | Dedupe key (`event_id`) |
|---|---|---|---|
| `FVG_CONFIRMED` | first qualifying FVG of the RTH session is confirmed | bar close | `FVG_CONFIRMED|symbol|FPFVG|confirm-bar time` |
| `LIQ_SWEEP` | §4.4 sweep | bar close | `LIQ_SWEEP|symbol|tag|level anchor time` |
| `LIQ_TOUCH` (off by default) | §4.4 touch | close, or intrabar | `LIQ_TOUCH|…` |
| `LIQ_BREAK` (off by default) | §4.4 break | bar close | `LIQ_BREAK|…` |
| `GAP_CE_TOUCH` | §4.2 CE touch (RTH gap; NDOG/NWOG optional) | close, or intrabar | `GAP_CE_TOUCH|symbol|OG/NDOG/NWOG|gap open time` |
| `GAP_FILL` | §4.2 fill | close, or intrabar | `GAP_FILL|…` |
| `MACRO_COMPLETE` | macro window's last bar closed | bar close | `MACRO_COMPLETE|symbol|M1…M6|window start` |

**No repeats:** each object (level, gap, FVG, macro occurrence) keeps a one-way flag, so an event can fire at most once. In intrabar mode, touch-type events use `alert.freq_once_per_bar`; the touch condition depends only on the bar's running high and low, so it stays true for the rest of the bar and the flag is committed at the close.

### 6.2 JSON format (`Message format = JSON`)
```json
{"script":"LuLevels","version":"1.0.0","symbol":"CME_MINI:ES1!","timeframe":"1",
 "event":"LIQ_SWEEP","detail":"Asia high","level":5862.25,
 "bar_time":1730903400000,"event_id":"LIQ_SWEEP|CME_MINI:ES1!|AS_H|1730851200000"}
```
`bar_time` is the UTC epoch in ms of the triggering bar's **open**. Some events add fields: `fvg_top`, `fvg_bottom`, `direction`, `gap_top`, `gap_bottom`, `high`, `low`, `window_start`, `window_end`.

### 6.3 Creating the running alert
1. Add the indicator, then choose the settings and alert toggles you want.
2. Open **Alerts** (⏰) → **Create alert**. Set **Condition** to `LuLevels…` → **Any alert() function call**.
3. Leave **Message** empty; the script supplies the text or JSON. Optionally set a webhook URL under **Notifications**.
4. Alternatively, pick one of the named `alertcondition` entries (for example *LuLevels · Liquidity sweep*). These carry a plain message, not JSON, and ignore the alert toggles. Use **Once per bar close**, or **Once per bar** if you use intrabar timing.

**When to recreate alerts:** an alert stores a snapshot of the script version **and** its inputs when you create it. Any later change to the script code, a new saved version, or any input change in the chart does **not** reach existing alerts. Delete and recreate the alert after updating the script or changing settings, including sessions, timezone, presets, and alert toggles or format.

---

## 7. Data, feeds and real-time behaviour
- All values come from the chart's actual symbol at the chart timeframe. DXY and the prior-day levels come from `request.security`.
- **Whether data is real-time, delayed or end-of-day depends on the exchange and your TradingView data subscriptions.** For example, CME futures and many stock exchanges are delayed without the matching real-time package. DXY availability and latency depend on the feed you select (`TVC:DXY`, `ICEUS:DX1!`, …). The script cannot detect delay. Check the symbol's status in the chart legend.
- Stocks: whether pre-market and overnight bars exist depends on the chart's extended-hours setting and on the feed.
- Developing visuals (session/macro boxes, developing highs and lows, the rail, the dashboard) update on every real-time tick. Event confirmations and alerts default to closed bars. FVG, sweep, break and macro events are always closed-bar.
- After a page reload, historical bars are recalculated from confirmed data, so closed-bar events don't repaint.

---

## 8. Known limits
- Pine keeps at most 500 lines, 500 boxes and 500 labels per script; older drawings are recycled. Lower `Historical sessions kept` on 1m charts with deep history.
- Bars that straddle a window boundary make that window unsupported (§4.1); no approximate values are shown instead.
- `time()` treats a bar as in-session based on its open time. Exotic chart types (Renko, Range, etc.) are not supported.
- Half-day sessions complete through the fallback rule (on the next bar), so the previous RTH close is still the last real RTH bar.

---

## 9. Verification status and test checklist
- **Checked in this environment:** the script parses cleanly with the open-source `pynescript` Pine parser (structure, indentation, expressions).
- **Not yet checked:** compilation in the TradingView Pine Editor, and the v6 reference pages for each built-in. Neither host was reachable here. On first compile, confirm in particular:
  - `alert()` calls inside user functions
  - `input.session` with an overnight value (`2000-0000`)
  - `timeframe.change`
  - `request.security(…, ignore_invalid_symbol = true)` returning a tuple
  - `str.tostring(x, "#.##########")` producing plain numbers for JSON

Suggested manual checks on the chart:
1. ES1! 1m, RTH-only view: the opening-gap prev close matches the 15:59 bar close (not the settlement).
2. A stock (for example SPY) 5m with extended hours off: the Data row reports `No bars: AS · LO · PM`, and the gap still works.
3. 1H futures chart: RTH, FVG and macros report `TF too coarse`; London and Asia still produce levels.
4. Replay mode: watch a sweep alert appear once at bar close and not again on later bars.
5. DST weeks (March/November): 09:30 ET levels stay at 09:30 local.
