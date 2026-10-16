"""Search HKG -> GVA / MXP for June using multiple gl= country currencies."""
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

# All currencies to test: (gl_code, currency_label, TWD_rate)
# Rates sourced from Bank of Taiwan + XE.com, 2026-05-14
CURRENCIES = [
    # Asia
    ("TW", "TWD", 1.0),
    ("HK", "HKD", 3.988),
    ("JP", "JPY", 0.1969),
    ("KR", "KRW", 0.02116),
    ("SG", "SGD", 24.62),
    ("CN", "CNY", 4.614),
    ("TH", "THB", 0.9557),
    ("MY", "MYR", 8.021),
    ("IN", "INR", 0.3294),
    ("ID", "IDR", 0.001801),
    ("PH", "PHP", 0.5133),
    ("VN", "VND", 0.001198),
    ("AU", "AUD", 22.625),
    ("NZ", "NZD", 18.53),
    # Europe
    ("HU", "HUF", 0.10321),
    ("NO", "NOK", 3.44),
    ("SE", "SEK", 3.32),
    ("DK", "DKK", 4.941),
    ("PL", "PLN", 8.692),
    ("CZ", "CZK", 1.5175),
    ("CH", "CHF", 40.08),
    ("GB", "GBP", 42.285),
    ("DE", "EUR", 36.605),
    ("TR", "TRY", 0.694),
    ("RO", "RON", 7.32),
    ("BG", "BGN", 18.72),
    # Others
    ("US", "USD", 31.43),
    ("CA", "CAD", 22.8),
    ("MX", "MXN", 1.834),
    ("BR", "BRL", 6.423),
    ("ZA", "ZAR", 1.869),
    ("EG", "EGP", 0.5957),
    ("SA", "SAR", 8.406),
    ("AE", "AED", 8.584),
]

ROUTES = [
    (Airport.NRT, Airport.IAH, "NRT→IAH"),
    (Airport.HND, Airport.IAH, "HND→IAH"),
]

START_DATE = "2026-06-01"
END_DATE   = "2026-06-15"

DATES_BASE_URL = (
    "https://www.google.com/_/FlightsFrontendUi/data/travel.frontend.flights"
    ".FlightsFrontendService/GetCalendarGraph"
)


def search_route_currency(origin, dest, gl_code):
    patched_url = f"{DATES_BASE_URL}?gl={gl_code}&hl=en"
    search = SearchDates()
    SearchDates.BASE_URL = patched_url  # monkey-patch

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
    )
    results = search.search(filters)
    SearchDates.BASE_URL = DATES_BASE_URL  # restore
    return results


def run():
    print(f"\nHKG → GVA / MXP  |  {START_DATE} ~ {END_DATE}  |  {len(CURRENCIES)} currencies\n")

    all_results = {}  # route -> list of (gl, label, twd_rate, best_date, raw_price, twd_price)

    for origin, dest, route_label in ROUTES:
        all_results[route_label] = []
        print(f"=== {route_label} ===")
        for gl_code, curr_label, twd_rate in CURRENCIES:
            try:
                results = search_route_currency(origin, dest, gl_code)
                if results:
                    best = min(results, key=lambda r: r.price)
                    twd = best.price * twd_rate
                    date_str = best.date[0].strftime("%m/%d") if best.date else "?"
                    all_results[route_label].append(
                        (gl_code, curr_label, twd_rate, date_str, best.price, twd)
                    )
                    print(f"  gl={gl_code} ({curr_label:>4}): {curr_label} {best.price:>10,.0f}  ≈ NT${twd:>8,.0f}  [{date_str}]")
                else:
                    print(f"  gl={gl_code} ({curr_label:>4}): no results")
                    all_results[route_label].append((gl_code, curr_label, twd_rate, "-", None, None))
            except Exception as e:
                print(f"  gl={gl_code} ({curr_label:>4}): ERROR - {e}")
                all_results[route_label].append((gl_code, curr_label, twd_rate, "-", None, None))
            time.sleep(1.3)
        print()

    # Summary tables
    for route_label, rows in all_results.items():
        valid = [(gl, cl, tr, dt, rp, twd) for gl, cl, tr, dt, rp, twd in rows if twd is not None]
        if not valid:
            continue
        valid.sort(key=lambda x: x[5])
        print(f"\n{'='*60}")
        print(f"  {route_label} — Ranked by TWD equivalent")
        print(f"{'='*60}")
        print(f"  {'Rank':<5} {'gl':<4} {'Currency':<6} {'Raw Price':>14} {'≈ NT$':>10} {'Best Date'}")
        print(f"  {'-'*55}")
        for i, (gl, cl, tr, dt, rp, twd) in enumerate(valid, 1):
            print(f"  {i:<5} {gl:<4} {cl:<6} {rp:>14,.0f} {twd:>10,.0f} {dt}")
        cheapest = valid[0]
        priciest = valid[-1]
        spread = (priciest[5] - cheapest[5]) / cheapest[5] * 100
        print(f"\n  Cheapest: gl={cheapest[0]} ({cheapest[1]})  NT${cheapest[5]:,.0f}")
        print(f"  Priciest: gl={priciest[0]} ({priciest[1]})  NT${priciest[5]:,.0f}")
        print(f"  Spread:   {spread:.1f}%")


if __name__ == "__main__":
    run()
