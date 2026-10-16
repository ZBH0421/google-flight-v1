"""
Qatar Airways (QR) and Emirates (EK): Asia → Texas, full June.
Finds cheapest Asian origin + Texas destination per airline.
"""
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
]

AIRLINES = [
    (Airline.QR, "Qatar Airways", "DOH"),
    (Airline.EK, "Emirates",      "DXB"),
]


def fetch(origin, dest, airline):
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
        airlines=[airline],
    )
    results = search.search(filters)
    if not results:
        return None, None
    best = min(results, key=lambda r: r.price)
    date_str = best.date[0].strftime("%Y-%m-%d") if best.date else "?"
    return best.price, date_str


def run():
    day_abbr = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    all_results = {}  # airline_name -> [(price, origin, dest, date, dow)]

    for airline_code, airline_name, hub in AIRLINES:
        print(f"\n{'='*65}")
        print(f"  {airline_name} (via {hub}) — Asia → Texas")
        print(f"{'='*65}")
        results = []

        for origin_ap, origin_label in ASIAN_ORIGINS:
            for dest_ap, dest_label in TEXAS_AIRPORTS:
                print(f"  {origin_label:<16} → {dest_label:<14} ...", end="", flush=True)
                try:
                    price, date = fetch(origin_ap, dest_ap, airline_code)
                    if price:
                        d = datetime.strptime(date, "%Y-%m-%d")
                        dow = day_abbr[d.weekday()]
                        print(f" NT${price:,.0f}  [{date} {dow}]")
                        results.append((price, origin_ap.name, origin_label,
                                        dest_ap.name, dest_label, date, dow))
                    else:
                        print(" —")
                except Exception as e:
                    print(f" ERROR: {e}")
                time.sleep(1.3)

        all_results[airline_name] = sorted(results)

    # Summary
    for airline_name, results in all_results.items():
        if not results:
            print(f"\n  {airline_name}: No results found.")
            continue

        print(f"\n{'='*68}")
        print(f"  {airline_name} — Ranked cheapest (Asia → Texas, June)")
        print(f"{'='*68}")
        print(f"  {'#':<4} {'From':<16} {'To':<14} {'NT$':>9}  {'Best Date'}")
        print(f"  {'─'*62}")
        for i, (price, o_code, o_label, d_code, d_label, date, dow) in enumerate(results, 1):
            print(f"  {i:<4} {o_label:<16} {d_label:<14} {price:>9,.0f}  {date} ({dow})")

        best = results[0]
        print(f"\n  ★  {airline_name} cheapest: {best[2]} → {best[4]}  NT${best[0]:,.0f}  on {best[5]} ({best[6]})")

        # Hub stopover hotel note
        hub = "Doha" if "Qatar" in airline_name else "Dubai"
        program = "Qatar Stopover" if "Qatar" in airline_name else "Emirates Stopover"
        print(f"  ℹ  Free hotel in {hub} via {program} programme (book on airline website)")


if __name__ == "__main__":
    run()
