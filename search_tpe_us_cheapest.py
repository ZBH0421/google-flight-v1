"""Find cheapest US city to fly to from TPE in early June."""
import time
from datetime import datetime

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

START_DATE = "2026-06-01"
END_DATE   = "2026-06-10"

US_AIRPORTS = [
    # West Coast
    (Airport.LAX, "Los Angeles"),
    (Airport.SFO, "San Francisco"),
    (Airport.SEA, "Seattle"),
    (Airport.LAS, "Las Vegas"),
    (Airport.SAN, "San Diego"),
    (Airport.PDX, "Portland"),
    # Hawaii
    (Airport.HNL, "Honolulu"),
    # Mountain / Southwest
    (Airport.DEN, "Denver"),
    (Airport.PHX, "Phoenix"),
    # Texas
    (Airport.IAH, "Houston"),
    (Airport.DFW, "Dallas"),
    (Airport.AUS, "Austin"),
    # Midwest
    (Airport.ORD, "Chicago"),
    (Airport.MSP, "Minneapolis"),
    (Airport.DTW, "Detroit"),
    # Southeast
    (Airport.ATL, "Atlanta"),
    (Airport.MIA, "Miami"),
    (Airport.MCO, "Orlando"),
    # Northeast
    (Airport.JFK, "New York JFK"),
    (Airport.EWR, "New York EWR"),
    (Airport.BOS, "Boston"),
    (Airport.IAD, "Washington DC"),
]


def fetch(dest, label):
    search = SearchDates()
    filters = DateSearchFilters(
        trip_type=TripType.ONE_WAY,
        passenger_info=PassengerInfo(adults=1),
        flight_segments=[
            FlightSegment(
                departure_airport=[[Airport.TPE, 0]],
                arrival_airport=[[dest, 0]],
                travel_date=START_DATE,
            )
        ],
        seat_type=SeatType.ECONOMY,
        stops=MaxStops.ANY,
        from_date=START_DATE,
        to_date=END_DATE,
    )
    results = search.search(filters)
    if not results:
        return None, None
    best = min(results, key=lambda r: r.price)
    date_str = best.date[0].strftime("%Y-%m-%d") if best.date else "?"
    return best.price, date_str


def run():
    day_abbr = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    print(f"\nTPE → US cities  |  {START_DATE} ~ {END_DATE}\n")
    results = []

    for ap, label in US_AIRPORTS:
        print(f"  {ap.name:<5} {label:<20} ...", end="", flush=True)
        try:
            price, date = fetch(ap, label)
            if price:
                d = datetime.strptime(date, "%Y-%m-%d")
                dow = day_abbr[d.weekday()]
                print(f" NT${price:,.0f}  [{date} {dow}]")
                results.append((price, ap.name, label, date, dow))
            else:
                print(" no results")
        except Exception as e:
            print(f" ERROR: {e}")
        time.sleep(1.3)

    if not results:
        print("No results.")
        return

    results.sort()

    print(f"\n{'='*65}")
    print(f"  TPE → US  —  Ranked by cheapest fare (Jun 1-10)")
    print(f"{'='*65}")
    print(f"  {'Rank':<5} {'Code':<6} {'City':<22} {'NT$':>9}  {'Best Date'}")
    print(f"  {'─'*60}")
    for i, (price, code, label, date, dow) in enumerate(results, 1):
        print(f"  {i:<5} {code:<6} {label:<22} {price:>9,.0f}  {date} ({dow})")

    best = results[0]
    print(f"\n  ★  Cheapest: {best[2]} ({best[1]})  NT${best[0]:,.0f}  on {best[3]} ({best[4]})")


if __name__ == "__main__":
    run()
