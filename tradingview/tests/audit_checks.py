"""Audit checks for LuLevels v1.0.0 (baseline).

Re-implements two small pieces of the Pine logic in Python (IEEE-754 doubles,
IANA time zones via zoneinfo) to test suspected defects deterministically.
These are reference checks of the ALGORITHM, not of TradingView's runtime.
Run:  python3 -I tradingview/tests/audit_checks.py
"""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/New_York")
DAY_MS = 86_400_000


def ms(dt):
    return int(dt.timestamp() * 1000)


def local(t_ms):
    return datetime.fromtimestamp(t_ms / 1000, tz=timezone.utc).astimezone(TZ)


def pine_timestamp(y, mo, d, h, mi):
    # Pine timestamp(tz, y, m, d, h, mi): wall-clock time in tz -> UTC ms
    return ms(datetime(y, mo, d, h, mi, tzinfo=TZ))


def min_of_day(t_ms):
    lt = local(t_ms)
    return lt.hour * 60 + lt.minute


def anchor_v1(t_ms, start_min):
    """Exact port of f_anchor() in LuLevels v1.0.0."""
    lt = local(t_ms)
    base = pine_timestamp(lt.year, lt.month, lt.day, start_min // 60, start_min % 60)
    return base if min_of_day(t_ms) >= start_min else base - DAY_MS


def anchor_fixed(t_ms, start_min):
    """Proposed fix: take the previous CALENDAR date, then build wall-clock start."""
    lt = local(t_ms)
    if min_of_day(t_ms) >= start_min:
        return pine_timestamp(lt.year, lt.month, lt.day, start_min // 60, start_min % 60)
    day_start = pine_timestamp(lt.year, lt.month, lt.day, 0, 0)
    prev = local(day_start - 3_600_000)  # 1h before local midnight is always the previous date
    return pine_timestamp(prev.year, prev.month, prev.day, start_min // 60, start_min % 60)


def session_ids(fn, start_local, hours, start_min):
    t0 = ms(start_local)
    return [(local(t0 + i * 3_600_000).strftime("%a %H:%M %Z"), fn(t0 + i * 3_600_000, start_min)) for i in range(hours)]


def check_dst_anchor():
    results = []
    # 24/7 market, overnight session 18:00-09:30 ET, across both 2026 US DST changes.
    for label, start in [("spring-forward 2026-03-08", datetime(2026, 3, 7, 18, 0, tzinfo=TZ)),
                         ("fall-back 2026-11-01", datetime(2026, 10, 31, 18, 0, tzinfo=TZ))]:
        for name, fn in [("v1.0.0", anchor_v1), ("fixed", anchor_fixed)]:
            ids = session_ids(fn, start, 15, 18 * 60)  # bars 18:00 .. 08:00 (one occurrence)
            distinct = len({i for _, i in ids})
            results.append((label, name, distinct))
    return results


def check_tick_rounding():
    cases = []
    # (description, price_a, price_b, mintick): one-tick gaps
    for desc, a, b, tick in [("EURUSD 1 tick", 1.08345, 1.08344, 0.00001),
                             ("USDJPY 1 tick", 151.235, 151.234, 0.001),
                             ("ES 1 tick", 5850.25, 5850.00, 0.25),
                             ("NQ 1 tick", 20512.75, 20512.50, 0.25),
                             ("CL 1 tick", 71.43, 71.42, 0.01),
                             ("BTC 1 tick", 68123.45, 68123.44, 0.01)]:
        rng = a - b
        v1_flat = rng == 0 or rng < 1 * tick          # v1.0.0: gapMinTicks = 1
        fixed_flat = round(rng / tick) < 1             # proposed: integer tick count
        cases.append((desc, repr(rng), v1_flat, fixed_flat))
    return cases


if __name__ == "__main__":
    print("== Session-occurrence ID across DST (distinct IDs per single occurrence; 1 is correct)")
    ok = True
    for label, name, distinct in check_dst_anchor():
        print(f"  {label:<26} {name:<7} distinct_ids={distinct}")
        if name == "fixed" and distinct != 1:
            ok = False
    print("\n== One-tick gaps classified as 'flat' with gapMinTicks=1 (False is correct)")
    for desc, rng, v1_flat, fixed_flat in check_tick_rounding():
        print(f"  {desc:<14} range={rng:<24} v1_flat={v1_flat!s:<5} fixed_flat={fixed_flat}")
        if fixed_flat:
            ok = False
    print("\nproposed fixes pass:", ok)
