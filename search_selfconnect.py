"""
Self-connect trip optimizer: TPE → IAH (stay ≥7d) → GVA (stay ≥7d) → TPE
Fetches each leg independently, then finds cheapest date combinations.
"""
import time
from datetime import datetime, timedelta
from itertools import product

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

DATES_BASE_URL = (
    "https://www.google.com/_/FlightsFrontendUi/data/travel.frontend.flights"
    ".FlightsFrontendService/GetCalendarGraph"
)

MIN_STAY = 7  # minimum days at each destination

# Each leg: (origin, dest, label, search_start, search_end)
LEGS = [
    (Airport.TPE, Airport.IAH, "TPE→IAH", "2026-06-01", "2026-06-14"),
    (Airport.IAH, Airport.GVA, "IAH→GVA", "2026-06-08", "2026-07-15"),
    (Airport.IAH, Airport.MXP, "IAH→MXP", "2026-06-08", "2026-07-15"),
    (Airport.GVA, Airport.TPE, "GVA→TPE", "2026-06-15", "2026-07-25"),
    (Airport.MXP, Airport.TPE, "MXP→TPE", "2026-06-15", "2026-07-25"),
]


def fetch_leg(origin, dest, start_date, end_date):
    """Return {date_str: price_twd} for a single leg."""
    search = SearchDates()
    filters = DateSearchFilters(
        trip_type=TripType.ONE_WAY,
        passenger_info=PassengerInfo(adults=1),
        flight_segments=[
            FlightSegment(
                departure_airport=[[origin, 0]],
                arrival_airport=[[dest, 0]],
                travel_date=start_date,
            )
        ],
        seat_type=SeatType.ECONOMY,
        stops=MaxStops.ANY,
        from_date=start_date,
        to_date=end_date,
    )
    results = search.search(filters)
    prices = {}
    for r in results:
        if r.date and r.price:
            prices[r.date[0].strftime("%Y-%m-%d")] = r.price
    return prices


def run():
    print("\nFetching prices for each leg (TWD, any stopover allowed)...\n")

    leg_data = []
    for origin, dest, label, start, end in LEGS:
        print(f"  {label}  ({start} ~ {end})...", end="", flush=True)
        prices = fetch_leg(origin, dest, start, end)
        leg_data.append((label, prices))
        print(f" {len(prices)} dates found")
        time.sleep(1.5)

    tpe_iah = leg_data[0][1]
    iah_gva = leg_data[1][1]
    iah_mxp = leg_data[2][1]
    gva_tpe = leg_data[3][1]
    mxp_tpe = leg_data[4][1]

    # Build leg2 and leg3 options: {date: (price, airport_label)}
    leg2_options = {d: (p, "GVA") for d, p in iah_gva.items()}
    for d, p in iah_mxp.items():
        if d not in leg2_options or p < leg2_options[d][0]:
            leg2_options[d] = (p, "MXP")

    leg3_gva = {d: (p, "GVA") for d, p in gva_tpe.items()}
    leg3_mxp = {d: (p, "MXP") for d, p in mxp_tpe.items()}

    print(f"\nFinding cheapest combinations (min {MIN_STAY} days at each stop)...\n")

    combos = []
    for d1_str, p1 in tpe_iah.items():
        d1 = datetime.strptime(d1_str, "%Y-%m-%d")
        earliest_d2 = d1 + timedelta(days=MIN_STAY)

        for d2_str, (p2, ap2) in leg2_options.items():
            d2 = datetime.strptime(d2_str, "%Y-%m-%d")
            if d2 < earliest_d2:
                continue
            earliest_d3 = d2 + timedelta(days=MIN_STAY)

            # Try all leg3 options (GVA→TPE and MXP→TPE)
            for leg3_pool in [leg3_gva, leg3_mxp]:
                for d3_str, (p3, ap3) in leg3_pool.items():
                    d3 = datetime.strptime(d3_str, "%Y-%m-%d")
                    if d3 < earliest_d3:
                        continue
                    total = p1 + p2 + p3
                    stay_iah = (d2 - d1).days
                    stay_eu = (d3 - d2).days
                    combos.append((total, p1, p2, p3, d1_str, d2_str, d3_str,
                                   stay_iah, stay_eu, ap2, ap3))

    if not combos:
        print("No valid combinations found.")
        return

    combos.sort()

    day_abbr = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    def fmt(d_str):
        d = datetime.strptime(d_str, "%Y-%m-%d")
        return f"{d_str}({day_abbr[d.weekday()]})"

    print(f"{'='*100}")
    print(f"  Top 20 cheapest — TPE→IAH(≥7d)→GVA/MXP(≥7d)→TPE  (進出可不同機場)")
    print(f"{'='*100}")
    print(f"  {'#':<3} {'Total':>8} {'Leg1':>8} {'Leg2':>8} {'Leg3':>8}  "
          f"{'TPE→IAH':<18} {'IAH→EU':<22} {'EU→TPE':<22} {'StayTX':>6} {'StayEU':>6}")
    print(f"  {'─'*110}")

    for i, (total, p1, p2, p3, d1, d2, d3, s1, s2, ap2, ap3) in enumerate(combos[:20], 1):
        leg2_label = f"IAH→{ap2}"
        leg3_label = f"{ap3}→TPE"
        print(f"  {i:<3} {total:>8,.0f} {p1:>8,.0f} {p2:>8,.0f} {p3:>8,.0f}  "
              f"{fmt(d1):<18} {leg2_label} {fmt(d2):<18} {leg3_label} {fmt(d3):<18} {s1:>4}d {s2:>4}d")

    best = combos[0]
    total, p1, p2, p3, d1, d2, d3, s1, s2, ap2, ap3 = best
    print(f"\n  ★  Cheapest total: NT${total:,.0f}")
    print(f"     TPE → IAH  on {fmt(d1)}  NT${p1:,.0f}")
    print(f"     IAH → {ap2}  on {fmt(d2)}  NT${p2:,.0f}  (stay {s1}d in Texas)")
    print(f"     {ap3} → TPE  on {fmt(d3)}  NT${p3:,.0f}  (stay {s2}d in Europe)")
    print()


if __name__ == "__main__":
    run()
