import json
from datetime import datetime, timedelta
from fli.models import (
    Airport,
    FlightSearchFilters,
    FlightSegment,
    PassengerInfo,
    SeatType,
    TripType,
    MaxStops,
    SortBy
)
from fli.search import SearchFlights

def search_multi_city(dest_airport, date1, date2):
    filters = FlightSearchFilters(
        trip_type=TripType.MULTI_CITY,
        passenger_info=PassengerInfo(adults=1),
        flight_segments=[
            FlightSegment(
                departure_airport=[[Airport.TPE, 0]],
                arrival_airport=[[Airport.NRT, 0]],
                travel_date=date1,
            ),
            FlightSegment(
                departure_airport=[[Airport.NRT, 0]],
                arrival_airport=[[dest_airport, 0]],
                travel_date=date2,
            )
        ],
        seat_type=SeatType.ECONOMY,
        stops=MaxStops.ANY,
        sort_by=SortBy.CHEAPEST,
    )

    search = SearchFlights()
    try:
        results = search.search(filters)
        return results
    except Exception as e:
        print(f"Error searching {dest_airport}: {e}")
        return []

print("Searching Multi-City: TPE -> NRT (6/1), NRT -> IAH/DFW (6/5)")

for dest in [Airport.IAH, Airport.DFW]:
    print(f"\n--- Destination: {dest.name} ---")
    results = search_multi_city(dest, "2026-06-01", "2026-06-05")
    if results:
        # Show top 3 cheapest
        for i, flight in enumerate(results[:3], 1):
            print(f"Option {i}: NT${flight.price} (Duration: {flight.duration} min)")
            for leg in flight.legs:
                print(f"  {leg.airline.value} {leg.flight_number} | {leg.departure_airport.value} -> {leg.arrival_airport.value} ({leg.departure_datetime.strftime('%m-%d %H:%M')})")
    else:
        print("No flights found.")
