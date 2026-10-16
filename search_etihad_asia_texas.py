"""Find cheapest Etihad Airways flights from Asian cities to Texas in June."""
import time
from datetime import datetime

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
    (Airport.IAH, "Houston IAH"),
    (Airport.DFW, "Dallas DFW"),
    (Airport.AUS, "Austin AUS"),
]


def fetch(origin, dest):
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
        airlines=[Airline.EY],
    )
    results = search.search(filters)
    if not results:
        return None, None
    best = min(results, key=lambda r: r.price)
    date_str = best.date[0].strftime("%Y-%m-%d") if best.date else "?"
    return best.price, date_str


def run():
    day_abbr = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    print(f"\nEtihad Airways (EY) — Asia → Texas  |  {START_DATE} ~ {END_DATE}\n")

    results = []
    for origin_ap, origin_label in ASIAN_ORIGINS:
        for dest_ap, dest_label in TEXAS_AIRPORTS:
            label = f"{origin_ap.name}→{dest_ap.name}"
            print(f"  {origin_label:<16} → {dest_label:<14} ...", end="", flush=True)
            try:
                price, date = fetch(origin_ap, dest_ap)
                if price:
                    d = datetime.strptime(date, "%Y-%m-%d")
                    dow = day_abbr[d.weekday()]
                    print(f" NT${price:,.0f}  [{date} {dow}]")
                    results.append((price, origin_ap.name, origin_label, dest_ap.name, dest_label, date, dow))
                else:
                    print(" no results")
            except Exception as e:
                print(f" ERROR: {e}")
            time.sleep(1.3)

    if not results:
        print("\nNo Etihad results found.")
        return

    results.sort()

    print(f"\n{'='*72}")
    print(f"  Etihad Airways — Asia → Texas  (June, ranked by price)")
    print(f"{'='*72}")
    print(f"  {'#':<4} {'From':<16} {'To':<14} {'NT$':>9}  {'Best Date'}")
    print(f"  {'─'*65}")
    for i, (price, o_code, o_label, d_code, d_label, date, dow) in enumerate(results, 1):
        print(f"  {i:<4} {o_label:<16} {d_label:<14} {price:>9,.0f}  {date} ({dow})")

    best = results[0]
    print(f"\n  ★  Cheapest: {best[2]} → {best[4]}  NT${best[0]:,.0f}  on {best[5]} ({best[6]})")

    # Best per Texas city
    print(f"\n  Best per Texas destination:")
    for _, dest_label in TEXAS_AIRPORTS:
        subset = [r for r in results if r[4] == dest_label]
        if subset:
            b = subset[0]
            print(f"    {b[4]}: NT${b[0]:,.0f}  from {b[2]}  on {b[5]} ({b[6]})")

    # Best per Asian origin
    print(f"\n  Best per Asian city:")
    seen = set()
    for r in results:
        if r[2] not in seen:
            seen.add(r[2])
            print(f"    {r[2]:<16}: NT${r[0]:,.0f}  → {r[4]}  on {r[5]} ({r[6]})")


if __name__ == "__main__":
    run()
