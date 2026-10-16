"""NRT → IAH: all June dates × selected currencies, one table per currency."""
import time
from collections import defaultdict

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
END_DATE   = "2026-06-30"

DATES_BASE_URL = (
    "https://www.google.com/_/FlightsFrontendUi/data/travel.frontend.flights"
    ".FlightsFrontendService/GetCalendarGraph"
)

# (gl_code, currency_label, TWD_rate)
# Rates sourced from Bank of Taiwan + XE.com, 2026-05-14
CURRENCIES = [
    ("ZA", "ZAR", 1.869),
    ("TH", "THB", 0.9557),
    ("TW", "TWD", 1.0),
]


def fetch_all_dates(gl_code):
    patched_url = f"{DATES_BASE_URL}?gl={gl_code}&hl=en"
    search = SearchDates()
    SearchDates.BASE_URL = patched_url
    filters = DateSearchFilters(
        trip_type=TripType.ONE_WAY,
        passenger_info=PassengerInfo(adults=1),
        flight_segments=[
            FlightSegment(
                departure_airport=[[Airport.TPE, 0]],
                arrival_airport=[[Airport.LYS, 0]],
                travel_date=START_DATE,
            )
        ],
        seat_type=SeatType.ECONOMY,
        stops=MaxStops.ANY,
        from_date=START_DATE,
        to_date=END_DATE,
    )
    results = search.search(filters)
    SearchDates.BASE_URL = DATES_BASE_URL
    return results


def run():
    print(f"\nNRT → IAH  |  {START_DATE} ~ {END_DATE}\n")

    # date_str -> {gl_code: (raw_price, twd_price)}
    date_data = defaultdict(dict)
    currency_meta = {}  # gl_code -> (label, rate)

    for gl_code, curr_label, twd_rate in CURRENCIES:
        print(f"  Querying gl={gl_code} ({curr_label})...", end="", flush=True)
        try:
            results = fetch_all_dates(gl_code)
            currency_meta[gl_code] = (curr_label, twd_rate)
            count = 0
            for r in results:
                if r.date and r.price:
                    date_str = r.date[0].strftime("%Y-%m-%d")
                    twd = r.price * twd_rate
                    date_data[date_str][gl_code] = (r.price, twd)
                    count += 1
            print(f" {count} dates")
        except Exception as e:
            print(f" ERROR: {e}")
        time.sleep(1.3)

    if not date_data:
        print("No data retrieved.")
        return

    all_dates = sorted(date_data.keys())
    gl_codes = [g for g, _, _ in CURRENCIES if g in currency_meta]

    # Header
    print(f"\n{'─'*120}")
    header = f"  {'Date':<12}"
    for gl in gl_codes:
        label = currency_meta[gl][0]
        header += f" {label:>10}"
    header += f"  {'Cheapest':>10}  {'By'}"
    print(header)
    print(f"  {'':─<12}", end="")
    for gl in gl_codes:
        print(f" {'─'*10}", end="")
    print(f"  {'─'*10}  {'─'*4}")

    # Rows
    for date_str in all_dates:
        row_data = date_data[date_str]
        # find cheapest TWD across available currencies
        available = {gl: row_data[gl] for gl in gl_codes if gl in row_data}
        if not available:
            continue
        cheapest_gl = min(available, key=lambda g: available[g][1])
        cheapest_twd = available[cheapest_gl][1]
        cheapest_label = currency_meta[cheapest_gl][0]

        day_name = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
        from datetime import datetime
        dow = day_name[datetime.strptime(date_str, "%Y-%m-%d").weekday()]
        line = f"  {date_str} {dow}"
        for gl in gl_codes:
            if gl in available:
                raw, twd = available[gl]
                line += f" {twd:>10,.0f}"
            else:
                line += f" {'—':>10}"
        line += f"  {cheapest_twd:>10,.0f}  {cheapest_label}"
        print(line)

    print(f"{'─'*120}")

    # Summary: top 10 cheapest date+currency combos
    print(f"\n{'Top 10 cheapest date × currency combinations':}")
    print(f"  {'Rank':<5} {'Date':<12} {'Day':<4} {'gl':<4} {'Currency':<6} {'Raw':>12} {'≈ NT$':>10}")
    print(f"  {'─'*60}")
    combos = []
    for date_str, row_data in date_data.items():
        for gl, (raw, twd) in row_data.items():
            if gl in currency_meta:
                label, _ = currency_meta[gl]
                combos.append((twd, date_str, gl, label, raw))
    combos.sort()
    from datetime import datetime
    day_name = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    for i, (twd, date_str, gl, label, raw) in enumerate(combos[:10], 1):
        dow = day_name[datetime.strptime(date_str, "%Y-%m-%d").weekday()]
        print(f"  {i:<5} {date_str:<12} {dow:<4} {gl:<4} {label:<6} {raw:>12,.0f} {twd:>10,.0f}")


if __name__ == "__main__":
    run()
