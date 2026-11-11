"""Illustrative preview of LuLevels' chart layout (NOT TradingView output).

Builds SYNTHETIC 5-minute bars, applies simplified Python ports of the
indicator's rules (sessions, completed levels, touch/sweep/break, RTH gap,
first presented FVG, NDOG, macros, label-rail merging) and draws them with
LuLevels' dark-theme palette. Prices are made up; this shows design and
layout only and proves nothing about the Pine script's runtime behaviour.

Run: python3 -I tradingview/preview/render_preview.py <out.png>
"""
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch

TZ = ZoneInfo("America/New_York")
TICK = 0.25
rng = np.random.default_rng(7)

C = dict(bg="#131722", grid="#1E2433", txt="#E2E8F0", mut="#94A3B8",
         bull="#22D3EE", bear="#FB7185", neu="#94A3B8", liq="#60A5FA",
         acc="#38BDF8", mac="#818CF8", key="#E2E8F0", hist="#94A3B8",
         up="#26A69A", dn="#EF5350", panel="#0B1220", frame="#1E293B")


def rt(x):
    return round(x / TICK) * TICK


# ── 1. synthetic CME-style bars (17:00–18:00 maintenance break removed) ──────
anchors = [
    ("2026-11-09 18:00", 5840), ("2026-11-10 02:00", 5834), ("2026-11-10 09:30", 5846),
    ("2026-11-10 12:00", 5867), ("2026-11-10 14:30", 5858), ("2026-11-10 15:55", 5852),
    ("2026-11-10 16:55", 5850),
    ("2026-11-10 18:00", 5853.5), ("2026-11-10 20:30", 5856), ("2026-11-10 22:00", 5849.5),
    ("2026-11-10 23:55", 5853), ("2026-11-11 02:30", 5849), ("2026-11-11 04:30", 5860),
    ("2026-11-11 07:00", 5855), ("2026-11-11 08:40", 5863.5), ("2026-11-11 09:25", 5853),
    ("2026-11-11 09:30", 5861), ("2026-11-11 09:45", 5857), ("2026-11-11 10:05", 5863),
    ("2026-11-11 10:25", 5864), ("2026-11-11 10:45", 5858.5), ("2026-11-11 11:00", 5860.5),
]
anch = [(datetime.strptime(t, "%Y-%m-%d %H:%M").replace(tzinfo=TZ), p) for t, p in anchors]

times = []
t = anch[0][0]
end = anch[-1][0]
while t <= end:
    if not (t.hour == 17):          # CME daily break
        times.append(t)
    t += timedelta(minutes=5)

ats = np.array([a[0].timestamp() for a in anch])
aps = np.array([a[1] for a in anch])
target = np.interp([x.timestamp() for x in times], ats, aps)

O, H, L, Cl = [], [], [], []
prev = target[0]
for i, tg in enumerate(target):
    o = rt(prev)
    if times[i].strftime("%H:%M") in ("18:00", "09:30") and i > 0:
        o = rt(target[i])            # session opens gap to the anchor
    c = rt(tg + rng.normal(0, 0.9))
    h = rt(max(o, c) + abs(rng.normal(0, 0.8)))
    l = rt(min(o, c) - abs(rng.normal(0, 0.8)))
    O.append(o); H.append(h); L.append(l); Cl.append(c)
    prev = c
O, H, L, Cl = map(np.array, (O, H, L, Cl))
idx = {x.strftime("%m-%d %H:%M"): i for i, x in enumerate(times)}


def mins(x):
    return x.hour * 60 + x.minute


def in_win(x, a, b):  # a,b minutes of day; b may be 0 (=24:00) or wrap
    m = mins(x)
    return (a <= m < b) if a < b else (m >= a or m < b)


def window_bars(day_start, a, b):
    """Indices of bars in the occurrence that starts on day_start at minute a."""
    start = day_start.replace(hour=a // 60, minute=a % 60)
    dur = ((b - a) % 1440) or 1440
    stop = start + timedelta(minutes=dur)
    return [i for i, x in enumerate(times) if start <= x < stop]


# engineered events, so the preview shows each state at least once
asia = window_bars(datetime(2026, 11, 10, tzinfo=TZ), 20 * 60, 0)
asia_lo = L[asia].min()
i = idx["11-11 02:35"]                      # London sweeps Asia low, closes back
L[i] = asia_lo - 1.25; O[i] = asia_lo + 0.5; Cl[i] = asia_lo + 1.25; H[i] = max(H[i], Cl[i] + 0.5)
pm = window_bars(datetime(2026, 11, 11, tzinfo=TZ), 4 * 60, 9 * 60 + 30)
pm_hi = H[pm].max()
for k, (o, h, l, c) in {"09:50": (5857.5, 5858.5, 5856.75, 5858.25),
                        "09:55": (5858.25, 5862.75, 5858.0, 5862.5),
                        "10:00": (5862.5, 5863.5, 5860.25, 5863.25)}.items():
    j = idx["11-11 " + k]; O[j], H[j], L[j], Cl[j] = o, h, l, c
j = idx["11-11 10:25"]                      # RTH sweeps pre-market high, closes back
O[j] = pm_hi - 0.75; H[j] = pm_hi + 1.5; Cl[j] = pm_hi - 1.0; L[j] = min(L[j], Cl[j] - 0.5)
N = len(times)
atr = np.mean(H[-14:] - L[-14:])

# ── 2. simplified ports of the indicator logic ──────────────────────────────
def sess(day, a, b, name, tag, col):
    bars = window_bars(day, a, b)
    hi_i = bars[int(np.argmax(H[bars]))]; lo_i = bars[int(np.argmin(L[bars]))]
    return dict(name=name, tag=tag, col=col, bars=bars, hi=H[hi_i], lo=L[lo_i],
                hi_i=hi_i, lo_i=lo_i, done_i=bars[-1])

S_prev_rth = sess(datetime(2026, 11, 10, tzinfo=TZ), 570, 960, "RTH", "RTH", C["bull"])
S_asia = sess(datetime(2026, 11, 10, tzinfo=TZ), 1200, 0, "Asia", "AS", C["mac"])
S_lon = sess(datetime(2026, 11, 11, tzinfo=TZ), 120, 300, "London", "LO", C["liq"])
S_pm = sess(datetime(2026, 11, 11, tzinfo=TZ), 240, 570, "Pre-market", "PM", C["acc"])
rth_now = window_bars(datetime(2026, 11, 11, tzinfo=TZ), 570, 960)

pd_bars = [i for i, x in enumerate(times) if x < datetime(2026, 11, 10, 17, tzinfo=TZ)]
levels = []
for s in (S_prev_rth, S_asia, S_lon, S_pm):
    levels.append(dict(tag=s["tag"] + " H", price=s["hi"], hi=True, t0=s["hi_i"], tc=s["done_i"], col=s["col"]))
    levels.append(dict(tag=s["tag"] + " L", price=s["lo"], hi=False, t0=s["lo_i"], tc=s["done_i"], col=s["col"]))
nd_i = idx["11-10 18:00"]
levels.append(dict(tag="PDH", price=H[pd_bars].max(), hi=True, t0=nd_i, tc=nd_i - 1, col=C["key"]))
levels.append(dict(tag="PDL", price=L[pd_bars].min(), hi=False, t0=nd_i, tc=nd_i - 1, col=C["key"]))
for lv in levels:                            # touch / sweep / break on closed bars
    lv["end"] = None; lv["state"] = "live"
    for i in range(lv["tc"] + 1, N):
        p = lv["price"]
        sw = (H[i] >= p + TICK and Cl[i] < p) if lv["hi"] else (L[i] <= p - TICK and Cl[i] > p)
        br = Cl[i] > p if lv["hi"] else Cl[i] < p
        if sw or br:
            lv["end"] = i; lv["state"] = "swept" if sw else "broken"; break

og_i = idx["11-11 09:30"]
pc = Cl[S_prev_rth["done_i"]]; op = O[og_i]
g_top, g_bot = max(pc, op), min(pc, op); g_mid = (g_top + g_bot) / 2
g_ce = any(L[i] <= g_mid <= H[i] for i in range(og_i, N))
g_fill = any((L[i] <= pc) if op > pc else (H[i] >= pc) for i in range(og_i, N))
nd_pc, nd_op = Cl[nd_i - 1], O[nd_i]
nd_top, nd_bot = max(nd_pc, nd_op), min(nd_pc, nd_op)

fvg = None
for i in range(og_i + 2, N):                 # all 3 candles inside RTH, min 2 ticks
    if L[i] - H[i - 2] >= 2 * TICK:
        fvg = dict(bull=True, top=L[i], bot=H[i - 2], t0=i - 2, tc=i); break
    if L[i - 2] - H[i] >= 2 * TICK:
        fvg = dict(bull=False, top=L[i - 2], bot=H[i], t0=i - 2, tc=i); break
if fvg:
    fvg["mid"] = (fvg["top"] + fvg["bot"]) / 2
    fvg["state"] = "Active"
    for i in range(fvg["tc"] + 1, N):
        if (Cl[i] < fvg["bot"]) if fvg["bull"] else (Cl[i] > fvg["top"]):
            fvg["state"] = "Mitigated"; fvg["end"] = i; break

macros = []
for a, b in ((530, 550), (590, 610), (650, 670)):
    bars = window_bars(datetime(2026, 11, 11, tzinfo=TZ), a, b)
    if bars:
        macros.append(dict(a=a, b=b, bars=bars, hi=H[bars].max(), lo=L[bars].min(),
                           live=bars[-1] == N - 1 and mins(times[-1]) < b - 5))

# ── 3. draw ─────────────────────────────────────────────────────────────────
v0 = idx["11-10 16:30"]
RAIL = N + 6
fig, ax = plt.subplots(figsize=(16, 9), dpi=110)
fig.patch.set_facecolor(C["bg"]); ax.set_facecolor(C["bg"])
for s in ax.spines.values():
    s.set_visible(False)
ax.grid(color=C["grid"], lw=0.6); ax.tick_params(colors=C["mut"], labelsize=8)

def box(x0, x1, y0, y1, col, fa, ea, ls="-", lw=0.8, label=None):
    ax.add_patch(Rectangle((x0 - 0.5, y0), x1 - x0 + 1, y1 - y0, facecolor=col, alpha=fa,
                           edgecolor=col, lw=lw, ls=ls, zorder=1))
    if ea:
        ax.add_patch(Rectangle((x0 - 0.5, y0), x1 - x0 + 1, y1 - y0, fill=False,
                               edgecolor=col, alpha=ea, lw=lw, ls=ls, zorder=1))
    if label:
        ax.text(x0, y1 - 0.25, label, color=col, alpha=0.85, fontsize=7, va="top", zorder=2)

for s in (S_asia, S_lon, S_pm):              # completed session boxes (faded)
    box(s["bars"][0], s["bars"][-1], s["lo"], s["hi"], s["col"], 0.06, 0.35, "--", label=s["name"])
for m in macros:
    lbl = f"{m['a']//60:02d}:{m['a']%60:02d}–{m['b']//60:02d}:{m['b']%60:02d}"
    x1 = m["bars"][0] + (m["b"] - m["a"]) // 5 - 1
    box(m["bars"][0], x1, m["lo"], m["hi"], C["mac"], 0.12 if m["live"] else 0.07,
        0.6 if m["live"] else 0.3, "--", label=lbl)

# NDOG zone + CE
box(nd_i, RAIL, nd_bot, nd_top, C["acc"], 0.06, 0)
ax.plot([nd_i, RAIL], [(nd_top + nd_bot) / 2] * 2, color=C["acc"], lw=1, ls="--", zorder=2)

# RTH opening gap
gcol = C["bull"] if op > pc else C["bear"]
box(og_i, RAIL, g_bot, g_top, gcol, 0.12, 0)
ax.plot([og_i, RAIL], [g_mid] * 2, color=gcol, lw=1.2, ls="-" if g_ce else "--", zorder=3)
for q in (g_bot + (g_top - g_bot) * 0.25, g_bot + (g_top - g_bot) * 0.75):
    ax.plot([og_i, RAIL], [q] * 2, color=gcol, lw=0.8, ls=":", alpha=0.6, zorder=3)
ax.plot([og_i, RAIL], [op] * 2, color=gcol, lw=1.2, zorder=3)
ax.plot([og_i, RAIL], [pc] * 2, color=C["neu"], lw=1.2, zorder=3)

if fvg:                                      # first presented FVG
    fc = C["bull"] if fvg["bull"] else C["bear"]
    x1 = fvg.get("end", RAIL)
    box(fvg["t0"], x1, fvg["bot"], fvg["top"], fc, 0.22 if fvg["state"] == "Active" else 0.08, 0.6)
    ax.plot([fvg["t0"], x1], [fvg["mid"]] * 2, color=fc, lw=0.9, ls=":", zorder=3)

for lv in levels:                            # liquidity levels
    if lv["t0"] < v0 and lv["end"] is not None and lv["end"] < v0:
        continue
    if lv["end"] is None:
        ax.plot([max(lv["t0"], v0), RAIL], [lv["price"]] * 2, color=lv["col"], lw=1.3, zorder=3)
    else:
        ax.plot([max(lv["t0"], v0), lv["end"]], [lv["price"]] * 2, color=C["hist"], lw=1, ls=":", alpha=0.7, zorder=3)
        if lv["state"] == "swept":
            ax.scatter([lv["end"]], [lv["price"]], marker="x", s=36, color=lv["col"], zorder=6, lw=1.6)

for i in range(v0, N):                       # candles
    col = C["up"] if Cl[i] >= O[i] else C["dn"]
    ax.plot([i, i], [L[i], H[i]], color=col, lw=0.8, zorder=4)
    ax.add_patch(Rectangle((i - 0.35, min(O[i], Cl[i])), 0.7, max(abs(Cl[i] - O[i]), TICK * 0.4),
                           color=col, zorder=5))

# label rail: merge labels closer than 0.20 × ATR, place at group mean
rail = [(lv["price"], lv["tag"], lv["col"]) for lv in levels if lv["end"] is None]
rail += [(op, "RTH O", gcol), (pc, "PC", C["neu"]), (g_mid, "OG CE", gcol),
         (g_bot + (g_top - g_bot) * 0.25, "OG 25%", gcol), (g_bot + (g_top - g_bot) * 0.75, "OG 75%", gcol),
         ((nd_top + nd_bot) / 2, "NDOG CE", C["acc"])]
if fvg and fvg["state"] == "Active":
    rail.append((fvg["mid"], "FPFVG", C["bull"] if fvg["bull"] else C["bear"]))
rail.sort()
groups, thr = [], 0.20 * atr
for p, t, c in rail:
    if groups and p - groups[-1]["first"] <= thr:
        groups[-1]["ps"].append(p); groups[-1]["ts"].append(t)
    else:
        groups.append(dict(first=p, ps=[p], ts=[t], col=c))
for g in groups:
    y = float(np.mean(g["ps"]))
    ax.text(RAIL + 0.6, y, " · ".join(g["ts"]), color=g["col"], fontsize=7.5, va="center", zorder=7,
            bbox=dict(boxstyle="round,pad=0.25", fc=g["col"], ec="none", alpha=0.0))
    ax.add_patch(FancyBboxPatch((RAIL + 0.3, y - 0.32), 1.6 * len(" · ".join(g["ts"])) * 0.62, 0.64,
                                boxstyle="round,pad=0.05", fc=g["col"], ec="none", alpha=0.16, zorder=6))

# dashboard (Standard preset)
rth_open = O[og_i]; px = Cl[-1]
mid_open = O[idx["11-11 00:00"]]; day_open = O[nd_i]
def rel(ref):
    p = (px - ref) / ref * 100
    return (("▲ +" if px >= ref else "▼ ") + f"{p:.2f}%"), (C["bull"] if px > ref else C["bear"] if px < ref else C["neu"])
fv_txt = (("Bull · " if fvg["bull"] else "Bear · ") + fvg["state"]) if fvg else "None this session"
rows = [("Session", "RTH", C["bull"]),
        ("Macro", "10:50–11:10 · live", C["mac"]),
        ("vs RTH open", *rel(rth_open)),
        ("vs 00:00 open", *rel(mid_open)),
        ("vs exch-day open", *rel(day_open)),
        ("FPFVG", fv_txt, (C["bull"] if fvg and fvg["bull"] else C["bear"]) if fvg and fvg["state"] == "Active" else C["mut"]),
        ("RTH gap", f"{'Up' if op > pc else 'Down'} {g_top - g_bot:.2f} · CE {'✓' if g_ce else '–'} · Fill {'✓' if g_fill else '–'}", gcol),
        ("NDOG", f"{'Up' if nd_op > nd_pc else 'Down'} {nd_top - nd_bot:.2f}", C["acc"]),
        ("DXY vs 00:00", "N/A (no DXY data in mock)", C["mut"]),
        ("DXY vs day open", "N/A (no DXY data in mock)", C["mut"])]
x0, y0, rh, w = 0.755, 0.965, 0.034, 0.235
ax.add_patch(FancyBboxPatch((x0, y0 - rh * (len(rows) + 1) - 0.01), w, rh * (len(rows) + 1) + 0.012,
                            boxstyle="round,pad=0.004", transform=ax.transAxes, fc=C["panel"],
                            ec=C["frame"], lw=1, alpha=0.95, zorder=8))
ax.text(x0 + 0.008, y0 - rh * 0.55, "LuLevels", color=C["bull"], fontsize=9, weight="bold", transform=ax.transAxes, zorder=9, va="center")
ax.text(x0 + w - 0.008, y0 - rh * 0.55, "v1.0.0 · 5m", color=C["mut"], fontsize=8, transform=ax.transAxes, zorder=9, va="center", ha="right")
for k, (a, b, c) in enumerate(rows, start=1):
    y = y0 - rh * (k + 0.55)
    ax.text(x0 + 0.008, y, a, color=C["mut"], fontsize=8, transform=ax.transAxes, zorder=9, va="center")
    ax.text(x0 + w - 0.008, y, b, color=c, fontsize=8, transform=ax.transAxes, zorder=9, va="center", ha="right")

# axes / ticks / watermark
ticks = [i for i in range(v0, N) if times[i].minute == 0 and times[i].hour % 2 == 0]
ax.set_xticks(ticks); ax.set_xticklabels([times[i].strftime("%a %H:%M") for i in ticks], rotation=0)
ax.set_xlim(v0 - 1, RAIL + 14)
vis = slice(v0, N)
y_lo = min(L[vis].min(), g_bot) - 3
y_hi = max(H[vis].max(), g_top) + 2
ax.set_ylim(y_lo, y_lo + (y_hi - y_lo) / 0.52)  # headroom for the dashboard
ax.yaxis.tick_right()
ax.text(0.01, 0.985, "ES1! · 5 · CME (synthetic)", color=C["txt"], fontsize=10, transform=ax.transAxes, va="top")
ax.text(0.01, 0.955, "LuLevels — Session & Liquidity Suite · Standard preset · Dark", color=C["mut"], fontsize=8, transform=ax.transAxes, va="top")
fig.text(0.5, 0.015, "ILLUSTRATIVE MOCKUP — synthetic prices drawn in Python with LuLevels' rules and colours. "
         "Not TradingView output; the Pine script itself has not been compiled yet.",
         ha="center", color=C["bear"], fontsize=9)
plt.subplots_adjust(left=0.01, right=0.955, top=0.99, bottom=0.07)
fig.savefig(sys.argv[1], facecolor=C["bg"])

print("levels:", [(l["tag"], l["price"], l["state"]) for l in levels])
print("gap:", pc, op, "CE", g_ce, "fill", g_fill, "| NDOG", nd_pc, nd_op)
print("fvg:", fvg)
print("macros:", [(m["a"], m["hi"], m["lo"], m["live"]) for m in macros])
