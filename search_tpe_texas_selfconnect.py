"""
Self-connect: TPE → [LAX/SFO/SEA] (stay 1-2d) → [IAH/DFW/AUS]
Finds cheapest combinations for early June departures.
"""
import time
from datetime import datetime, timedelta

from fli.models import (
    Airport,
    DateSearchFilters,
    FlightSegment,
    MaxStops,
    PassengerInfo,
    SeatType,
    TripType,
)
from fli.search.dates import SearchDates

MIN_STAY = 1
MAX_STAY = 2

STOPOVERS = [Airport.PHX, Airport.LAS]
TEXAS     = [Airport.IAH, Airport.DFW, Airport.AUS]

LEG1_START = "2026-06-01"
LEG1_END   = "2026-06-10"
LEG2_START = "2026-06-02"
LEG2_END   = "2026-06-14"


def fetch(origin, dest, start, end):
    search = SearchDates()
    filters = DateSearchFilters(
        trip_type=TripType.ONE_WAY,
        passenger_info=PassengerInfo(adults=1),
        flight_segments=[
            FlightSegment(
                departure_airport=[[origin, 0]],
                arrival_airport=[[dest, 0]],
                travel_date=start,
            )
        ],
        seat_type=SeatType.ECONOMY,
        stops=MaxStops.ANY,
        from_date=start,
        to_date=end,
    )
    results = search.search(filters)
    return {r.date[0].strftime("%Y-%m-%d"): r.price for r in results if r.date and r.price}


def run():
    # --- Fetch leg 1: TPE → each stopover ---
    leg1 = {}  # (stopover) -> {date: price}
    print("Leg 1  TPE → West Coast:")
    for ap in STOPOVERS:
        print(f"  TPE→{ap.name} ...", end="", flush=True)
        leg1[ap] = fetch(Airport.TPE, ap, LEG1_START, LEG1_END)
        print(f" {len(leg1[ap])} dates")
        time.sleep(1.3)

    # --- Fetch leg 2: each stopover → each Texas city ---
    leg2 = {}  # (stopover, texas) -> {date: price}
    print("\nLeg 2  West Coast → Texas:")
    for ap in STOPOVERS:
        for tx in TEXAS:
            key = (ap, tx)
            print(f"  {ap.name}→{tx.name} ...", end="", flush=True)
            leg2[key] = fetch(ap, tx, LEG2_START, LEG2_END)
            print(f" {len(leg2[key])} dates")
            time.sleep(1.3)

    # --- Combine ---
    print(f"\nCombining (stopover {MIN_STAY}–{MAX_STAY} days)...\n")

    day_abbr = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    def fmt(d_str):
        d = datetime.strptime(d_str, "%Y-%m-%d")
        return f"{d_str}({day_abbr[d.weekday()]})"

    combos = []
    for stop in STOPOVERS:
        for tx in TEXAS:
            for d1_str, p1 in leg1[stop].items():
                d1 = datetime.strptime(d1_str, "%Y-%m-%d")
                for days in range(MIN_STAY, MAX_STAY + 1):
                    d2 = d1 + timedelta(days=days)
                    d2_str = d2.strftime("%Y-%m-%d")
                    p2 = leg2[(stop, tx)].get(d2_str)
                    if p2 is None:
                        continue
                    total = p1 + p2
                    combos.append((total, p1, p2, d1_str, d2_str, stop.name, tx.name, days))

    if not combos:
        print("No combinations found.")
        return

    combos.sort()

    print(f"{'='*95}")
    print(f"  Top 20 cheapest  —  TPE → Stopover ({MIN_STAY}-{MAX_STAY}d) → Texas")
    print(f"{'='*95}")
    print(f"  {'#':<3} {'Total':>8} {'TPE→Stop':>9} {'Stop→TX':>8}  "
          f"{'Depart TPE':<20} {'Stop':<5} {'Stay':>4} {'Fly to TX':<20} {'Dest'}")
    print(f"  {'─'*90}")

    for i, (total, p1, p2, d1, d2, stop, tx, days) in enumerate(combos[:20], 1):
        print(f"  {i:<3} {total:>8,.0f} {p1:>9,.0f} {p2:>8,.0f}  "
              f"{fmt(d1):<20} {stop:<5} {days:>3}d  {fmt(d2):<20} {tx}")

    print(f"\n  ★  Cheapest: NT${combos[0][0]:,.0f}")
    t, p1, p2, d1, d2, stop, tx, days = combos[0]
    print(f"     TPE → {stop}  on {fmt(d1)}  NT${p1:,.0f}")
    print(f"     Stay {days} day(s) at {stop}")
    print(f"     {stop} → {tx}  on {fmt(d2)}  NT${p2:,.0f}")
    print()

    # --- Summary by destination ---
    print(f"  Best per Texas destination:")
    for tx in [ap.name for ap in TEXAS]:
        best = min((c for c in combos if c[6] == tx), key=lambda x: x[0], default=None)
        if best:
            t, p1, p2, d1, d2, stop, _, days = best
            print(f"    {tx}: NT${t:,.0f}  via {stop}  ({fmt(d1)} +{days}d → {fmt(d2)})")

    # --- Summary by stopover ---
    print(f"\n  Best per stopover city:")
    for stop in [ap.name for ap in STOPOVERS]:
        best = min((c for c in combos if c[5] == stop), key=lambda x: x[0], default=None)
        if best:
            t, p1, p2, d1, d2, _, tx, days = best
            print(f"    {stop}: NT${t:,.0f}  → {tx}  ({fmt(d1)} +{days}d → {fmt(d2)})")


if __name__ == "__main__":
    run()
