"""
Etihad approach: search Asia → AUH (leg1) + AUH → Texas (leg2, Etihad filter).
Combine as self-connect to find cheapest Asian origin.
"""
import time
from datetime import datetime, timedelta

from fli.models import (
    Airline,
    Airport,
    DateSearchFilters,
    FlightSegment,
    MaxStops,
    PassengerInfo,
    SeatType,
    TripType,
)
from fli.search.dates import SearchDates

START_DATE = "2026-06-01"
END_DATE   = "2026-06-30"

ASIAN_ORIGINS = [
    (Airport.TPE, "Taipei"),
    (Airport.HKG, "Hong Kong"),
    (Airport.NRT, "Tokyo NRT"),
    (Airport.KIX, "Osaka"),
    (Airport.ICN, "Seoul"),
    (Airport.BKK, "Bangkok"),
    (Airport.SIN, "Singapore"),
    (Airport.KUL, "Kuala Lumpur"),
    (Airport.MNL, "Manila"),
    (Airport.CGK, "Jakarta"),
    (Airport.DEL, "Delhi"),
    (Airport.BOM, "Mumbai"),
]

TEXAS_AIRPORTS = [
    (Airport.IAH, "Houston"),
    (Airport.DFW, "Dallas"),
]


def fetch(origin, dest, airlines=None):
    search = SearchDates()
    filters = DateSearchFilters(
        trip_type=TripType.ONE_WAY,
        passenger_info=PassengerInfo(adults=1),
        flight_segments=[
            FlightSegment(
                departure_airport=[[origin, 0]],
                arrival_airport=[[dest, 0]],
                travel_date=START_DATE,
            )
        ],
        seat_type=SeatType.ECONOMY,
        stops=MaxStops.ANY,
        from_date=START_DATE,
        to_date=END_DATE,
        airlines=airlines,
    )
    results = search.search(filters)
    if not results:
        return {}
    return {r.date[0].strftime("%Y-%m-%d"): r.price for r in results if r.date and r.price}


def run():
    day_abbr = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    # Step 1: AUH → Texas (Etihad only)
    print("Step 1: AUH → Texas (Etihad EY only)")
    auh_texas = {}
    for dest_ap, dest_label in TEXAS_AIRPORTS:
        print(f"  AUH → {dest_label} ...", end="", flush=True)
        prices = fetch(Airport.AUH, dest_ap, airlines=[Airline.EY])
        if prices:
            best_price = min(prices.values())
            best_date = min(prices, key=lambda d: prices[d])
            d = datetime.strptime(best_date, "%Y-%m-%d")
            print(f" {len(prices)} dates, cheapest NT${best_price:,.0f} on {best_date} ({day_abbr[d.weekday()]})")
        else:
            print(" no results")
        auh_texas[(dest_ap, dest_label)] = prices
        time.sleep(1.3)

    # Step 2: Asia → AUH (any airline)
    print("\nStep 2: Asia → AUH (any airline)")
    asia_auh = {}
    for origin_ap, origin_label in ASIAN_ORIGINS:
        print(f"  {origin_label:<16} → AUH ...", end="", flush=True)
        prices = fetch(origin_ap, Airport.AUH)
        if prices:
            best = min(prices.values())
            print(f" {len(prices)} dates, cheapest NT${best:,.0f}")
        else:
            print(" no results")
        asia_auh[(origin_ap, origin_label)] = prices
        time.sleep(1.3)

    # Step 3: Combine (min 0 days at AUH — same day connection or next day)
    print("\nStep 3: Finding cheapest combinations (0-1 day at AUH)...\n")

    combos = []
    for (dest_ap, dest_label), auh_prices in auh_texas.items():
        if not auh_prices:
            continue
        for (origin_ap, origin_label), asia_prices in asia_auh.items():
            if not asia_prices:
                continue
            for d1_str, p1 in asia_prices.items():
                d1 = datetime.strptime(d1_str, "%Y-%m-%d")
                for lag in range(0, 2):  # same day or +1 day at AUH
                    d2 = d1 + timedelta(days=lag)
                    d2_str = d2.strftime("%Y-%m-%d")
                    p2 = auh_prices.get(d2_str)
                    if p2 is None:
                        continue
                    total = p1 + p2
                    combos.append((total, p1, p2, origin_label, origin_ap.name,
                                   dest_label, d1_str, d2_str, lag))

    if not combos:
        print("No combinations found — Etihad may not serve Texas from AUH in June.")
        return

    combos.sort()

    print(f"{'='*80}")
    print(f"  Etihad via AUH — Asia → AUH → Texas (June)")
    print(f"{'='*80}")
    print(f"  {'#':<4} {'Total':>9} {'Asia→AUH':>9} {'AUH→TX':>9}  "
          f"{'From':<16} {'Depart':<13} {'AUH lag':>7}  {'To'}")
    print(f"  {'─'*75}")
    for i, (total, p1, p2, o_label, o_code, d_label, d1, d2, lag) in enumerate(combos[:20], 1):
        d1obj = datetime.strptime(d1, "%Y-%m-%d")
        print(f"  {i:<4} {total:>9,.0f} {p1:>9,.0f} {p2:>9,.0f}  "
              f"{o_label:<16} {d1} ({day_abbr[d1obj.weekday()]})  +{lag}d       {d_label}")

    best = combos[0]
    print(f"\n  ★  Cheapest: NT${best[0]:,.0f}")
    print(f"     {best[3]} ({best[4]}) → AUH  on {best[6]}  NT${best[1]:,.0f}")
    print(f"     AUH → {best[5]}  on {best[7]}  NT${best[2]:,.0f}  (+{best[8]}d at AUH)")


if __name__ == "__main__":
    run()
