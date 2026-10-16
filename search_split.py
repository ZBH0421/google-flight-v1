import json
from datetime import datetime, timedelta
from fli.models import (
    Airport,
    DateSearchFilters,
    FlightSegment,
    PassengerInfo,
    SeatType,
    TripType,
    MaxStops
)
from fli.search import SearchDates

def get_exchange_rate(from_curr, to_curr="TWD"):
    if from_curr == to_curr:
        return 1.0
    rates = {
        "USD": 32.5,
        "JPY": 0.21,
        "EUR": 35.0,
        "HKD": 4.15,
        "SGD": 24.0,
        "KRW": 0.024,
        "GBP": 40.5
    }
    return rates.get(from_curr, 1.0)

def search_cheapest_dates(origin, dest, start_date, end_date):
    search = SearchDates()
    try:
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
            to_date=end_date
        )
        results = search.search(filters)
        if not results:
            print(f"No results for {origin.name} -> {dest.name}")
            return
        sorted_dates = sorted(results, key=lambda x: x.price)
        print(f"\n--- {origin.name} -> {dest.name} ---")
        for d in sorted_dates[:5]:
            rate = get_exchange_rate(d.currency, "TWD")
            twd_price = d.price * rate
            print(f"{d.date[0].strftime('%Y-%m-%d')}: {d.currency} {d.price:,.0f} (約 NT$ {twd_price:,.0f})")
    except Exception as e:
        print(f"Error for {origin.name} -> {dest.name}: {e}")

search_cheapest_dates(Airport.TPE, Airport.NRT, "2026-06-01", "2026-06-10")
search_cheapest_dates(Airport.NRT, Airport.DFW, "2026-06-03", "2026-06-15")
search_cheapest_dates(Airport.NRT, Airport.IAH, "2026-06-03", "2026-06-15")
