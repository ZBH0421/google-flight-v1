"""Show detailed flight info for TPE→PHX (6/5) and PHX→IAH (6/6)."""
from fli.models import (
    Airport,
    FlightSearchFilters,
    FlightSegment,
    MaxStops,
    PassengerInfo,
    SeatType,
    SortBy,
    TripType,
)
from fli.search.flights import SearchFlights


def show(filters, label):
    results = SearchFlights().search(filters)
    if not results:
        print(f"  No results for {label}")
        return
    print(f"\n{'='*70}")
    print(f"  {label}  —  Top results")
    print(f"{'='*70}")
    for i, flight in enumerate(results[:5], 1):
        duration_h, duration_m = divmod(flight.duration, 60)
        stops_label = "Non-stop" if flight.stops == 0 else f"{flight.stops} stop(s)"
        print(f"\n  #{i}  NT${flight.price:,.0f}  |  {duration_h}h{duration_m:02d}m  |  {stops_label}")
        for leg in flight.legs:
            dep = leg.departure_datetime.strftime("%m/%d %H:%M")
            arr = leg.arrival_datetime.strftime("%m/%d %H:%M")
            leg_h, leg_m = divmod(leg.duration, 60)
            print(f"       {leg.airline.value} {leg.flight_number:<8}  "
                  f"{leg.departure_airport.value} {dep} → "
                  f"{leg.arrival_airport.value} {arr}  ({leg_h}h{leg_m:02d}m)")


# Leg 1: TPE → LAS on 2026-06-05
leg1 = FlightSearchFilters(
    trip_type=TripType.ONE_WAY,
    passenger_info=PassengerInfo(adults=1),
    flight_segments=[
        FlightSegment(
            departure_airport=[[Airport.TPE, 0]],
            arrival_airport=[[Airport.LAS, 0]],
            travel_date="2026-06-05",
        )
    ],
    seat_type=SeatType.ECONOMY,
    stops=MaxStops.ANY,
    sort_by=SortBy.CHEAPEST,
)

# Leg 2: LAS → AUS on 2026-06-06
leg2 = FlightSearchFilters(
    trip_type=TripType.ONE_WAY,
    passenger_info=PassengerInfo(adults=1),
    flight_segments=[
        FlightSegment(
            departure_airport=[[Airport.LAS, 0]],
            arrival_airport=[[Airport.AUS, 0]],
            travel_date="2026-06-06",
        )
    ],
    seat_type=SeatType.ECONOMY,
    stops=MaxStops.ANY,
    sort_by=SortBy.CHEAPEST,
)

show(leg1, "TPE → LAS  |  2026-06-05 (Fri)")
show(leg2, "LAS → AUS  |  2026-06-06 (Sat)")
