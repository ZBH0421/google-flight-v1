"""Flight search CLI command."""

from typing import Annotated, Any

import typer

from fli.cli.enums import OutputFormat
from fli.cli.utils import (
    build_json_error_response,
    build_json_success_response,
    display_flight_results,
    emit_json,
    normalize_cli_date,
    normalize_cli_time_range,
    serialize_flight_result,
    validate_currency,
)
from fli.core import (
    build_flight_segments,
    parse_airlines,
    parse_cabin_class,
    parse_emissions,
    parse_max_stops,
    parse_sort_by,
    resolve_airport,
)
from fli.core.parsers import ParseError
from fli.models import (
    BagsFilter,
    FlightSearchFilters,
    LayoverRestrictions,
    PassengerInfo,
)
from fli.search import SearchFlights
from fli.search.multi_country import CountryResult, search_all_countries
from fli.vpn.countries import parse_countries_flag
from fli.vpn.tor_manager import TorNotRunningError


def _display_country_comparison(results: list[CountryResult]) -> None:
    """Print a Rich table comparing cheapest prices per country."""
    from rich import box
    from rich.table import Table

    from fli.cli.console import console

    table = Table(box=box.SIMPLE, show_header=True, header_style="bold")
    table.add_column("Country", style="cyan", min_width=14)
    table.add_column("Code", width=6)
    table.add_column("Cheapest", justify="right", style="green", min_width=10)
    table.add_column("Flights", justify="right", width=8)
    table.add_column("Status", width=10)

    for r in results:
        if not r.flights:
            error_msg = r.error or "no results"
            table.add_row(
                r.country_name, r.country_code, "-", "-", f"[red]{error_msg}[/red]"
            )
        else:
            cheapest = min(f.price for f in r.flights)
            table.add_row(
                r.country_name,
                r.country_code,
                f"${cheapest:.0f}",
                str(len(r.flights)),
                "[green]✓[/green]",
            )

    console.print(table)

    successful = [r for r in results if r.flights]
    if successful:
        best = min(successful, key=lambda r: min(f.price for f in r.flights))
        best_price = min(f.price for f in best.flights)
        console.print(
            f"\n[bold green]Cheapest: {best.country_name} ({best.country_code})"
            f"  ${best_price:.0f}[/bold green]"
        )


def _build_filters(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: str | None,
    departure_window: str | tuple[int, int] | None,
    airlines: list[str] | None,
    cabin_class: str,
    max_stops: str,
    sort_by: str,
    exclude_basic_economy: bool,
    layover: list[str] | None,
    emissions: str,
    checked_bags: int,
    carry_on: bool,
    all_results: bool,
) -> FlightSearchFilters:
    """Build FlightSearchFilters from CLI arguments.

    Raises:
        ParseError: On invalid airport, airline, or enum values.

    """
    departure_date = normalize_cli_date(departure_date)
    return_date = normalize_cli_date(return_date)
    departure_window = normalize_cli_time_range(departure_window)

    origin_airport = resolve_airport(origin)
    destination_airport = resolve_airport(destination)
    seat_type = parse_cabin_class(cabin_class)
    stops = parse_max_stops(max_stops)
    parsed_airlines = parse_airlines(airlines)
    sort = parse_sort_by(sort_by)
    emissions_filter = parse_emissions(emissions)

    time_restrictions = None
    if departure_window:
        from fli.models import TimeRestrictions

        time_restrictions = TimeRestrictions(
            earliest_departure=departure_window[0],
            latest_departure=departure_window[1],
        )

    segments, trip_type = build_flight_segments(
        origin=origin_airport,
        destination=destination_airport,
        departure_date=departure_date,
        return_date=return_date,
        time_restrictions=time_restrictions,
    )

    layover_restrictions = None
    if layover:
        layover_airports = [resolve_airport(code) for code in layover]
        layover_restrictions = LayoverRestrictions(airports=layover_airports)

    bags_filter = None
    if checked_bags > 0 or carry_on:
        bags_filter = BagsFilter(checked_bags=checked_bags, carry_on=carry_on)

    return FlightSearchFilters(
        trip_type=trip_type,
        passenger_info=PassengerInfo(adults=1),
        flight_segments=segments,
        stops=stops,
        seat_type=seat_type,
        airlines=parsed_airlines,
        sort_by=sort,
        exclude_basic_economy=exclude_basic_economy,
        layover_restrictions=layover_restrictions,
        emissions=emissions_filter,
        bags=bags_filter,
        show_all_results=all_results,
    )


def _search_flights_core(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: str | None = None,
    departure_window: str | tuple[int, int] | None = None,
    airlines: list[str] | None = None,
    cabin_class: str = "ECONOMY",
    max_stops: str = "ANY",
    sort_by: str = "CHEAPEST",
    exclude_basic_economy: bool = False,
    layover: list[str] | None = None,
    emissions: str = "ALL",
    checked_bags: int = 0,
    carry_on: bool = False,
    all_results: bool = True,
    output_format: OutputFormat = OutputFormat.TEXT,
    currency: str = "USD",
) -> None:
    """Core flight search functionality."""
    query: dict[str, Any] = {
        "origin": origin.upper(),
        "destination": destination.upper(),
        "departure_date": departure_date,
        "return_date": return_date,
        "departure_window": None,
        "airlines": [airline.upper() for airline in airlines] if airlines else None,
        "cabin_class": cabin_class.upper(),
        "max_stops": max_stops.upper(),
        "sort_by": sort_by.upper(),
    }

    try:
        departure_date = normalize_cli_date(departure_date)
        return_date = normalize_cli_date(return_date)
        departure_window = normalize_cli_time_range(departure_window)
        query["departure_date"] = departure_date
        query["return_date"] = return_date
        query["departure_window"] = (
            f"{departure_window[0]}-{departure_window[1]}" if departure_window else None
        )

        # Build filters using shared helper (avoids duplicating filter construction)
        filters = _build_filters(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
            departure_window=departure_window,
            airlines=airlines,
            cabin_class=cabin_class,
            max_stops=max_stops,
            sort_by=sort_by,
            exclude_basic_economy=exclude_basic_economy,
            layover=layover,
            emissions=emissions,
            checked_bags=checked_bags,
            carry_on=carry_on,
            all_results=all_results,
        )
        trip_type = filters.trip_type

        # Perform search
        search_client = SearchFlights()
        results = search_client.search(filters)

        if not results:
            if output_format == OutputFormat.JSON:
                emit_json(
                    build_json_success_response(
                        search_type="flights",
                        trip_type=trip_type,
                        query=query,
                        results_key="flights",
                        results=[],
                    )
                )
                return

            typer.echo("No flights found.")
            raise typer.Exit(1)

        if output_format == OutputFormat.JSON:
            emit_json(
                build_json_success_response(
                    search_type="flights",
                    trip_type=trip_type,
                    query=query,
                    results_key="flights",
                    results=[
                        serialize_flight_result(result, default_currency=currency)
                        for result in results
                    ],
                )
            )
            return

        display_flight_results(results, default_currency=currency)

    except ParseError as e:
        if output_format == OutputFormat.JSON:
            emit_json(
                build_json_error_response(
                    search_type="flights",
                    message=str(e),
                    query=query,
                )
            )
            raise typer.Exit(1) from e

        typer.echo(f"Error: {str(e)}")
        raise typer.Exit(1) from e
    except (AttributeError, ValueError) as e:
        if output_format == OutputFormat.JSON:
            emit_json(
                build_json_error_response(
                    search_type="flights",
                    message=str(e),
                    error_type="search_error",
                    query=query,
                )
            )
            raise typer.Exit(1) from e

        typer.echo(f"Error: {str(e)}")
        raise typer.Exit(1) from e


def flights(
    origin: Annotated[str, typer.Argument(help="Departure airport IATA code (e.g., JFK)")],
    destination: Annotated[str, typer.Argument(help="Arrival airport IATA code (e.g., LHR)")],
    departure_date: Annotated[str, typer.Argument(help="Travel date (YYYY-MM-DD)")],
    return_date: Annotated[
        str | None,
        typer.Option(
            "--return",
            "-r",
            help="Return date (YYYY-MM-DD)",
        ),
    ] = None,
    departure_window: Annotated[
        str | None,
        typer.Option(
            "--time",
            "-t",
            help="Departure time window in 24h format (e.g., 6-20)",
        ),
    ] = None,
    airlines: Annotated[
        list[str] | None,
        typer.Option(
            "--airlines",
            "-a",
            help="List of airline IATA codes (e.g., BA KL)",
        ),
    ] = None,
    cabin_class: Annotated[
        str,
        typer.Option(
            "--class",
            "-c",
            help="Cabin class (ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST)",
        ),
    ] = "ECONOMY",
    max_stops: Annotated[
        str,
        typer.Option(
            "--stops",
            "-s",
            help="Maximum stops (ANY, 0 for non-stop, 1 for one stop, 2+ for two stops)",
        ),
    ] = "ANY",
    sort_by: Annotated[
        str,
        typer.Option(
            "--sort",
            "-o",
            help="Sort by: TOP_FLIGHTS, BEST, CHEAPEST, DEPARTURE_TIME,"
            " ARRIVAL_TIME, DURATION, EMISSIONS",
        ),
    ] = "CHEAPEST",
    exclude_basic_economy: Annotated[
        bool,
        typer.Option(
            "--exclude-basic",
            "-e",
            help="Exclude basic economy fares",
        ),
    ] = False,
    layover: Annotated[
        list[str] | None,
        typer.Option(
            "--layover",
            "-l",
            help="Restrict layover to these airports (e.g., -l ORD -l MDW)",
        ),
    ] = None,
    emissions: Annotated[
        str,
        typer.Option(
            "--emissions",
            help="Filter by emissions level (ALL, LESS)",
        ),
    ] = "ALL",
    checked_bags: Annotated[
        int,
        typer.Option(
            "--bags",
            "-b",
            help="Number of checked bags to include in price (0, 1, or 2)",
            min=0,
            max=2,
        ),
    ] = 0,
    carry_on: Annotated[
        bool,
        typer.Option(
            "--carry-on",
            help="Include carry-on bag fee in price",
        ),
    ] = False,
    all_results: Annotated[
        bool,
        typer.Option(
            "--all/--no-all",
            help="Show all available results (default) or only ~30 curated results",
        ),
    ] = True,
    output_format: Annotated[
        OutputFormat,
        typer.Option(
            "--format",
            help="Output format: text or json",
            case_sensitive=False,
        ),
    ] = OutputFormat.TEXT,
    currency: Annotated[
        str,
        typer.Option(
            "--currency",
            callback=validate_currency,
            help="Fallback currency code when not returned by Google (e.g., CAD, EUR).",
        ),
    ] = "USD",
    compare_countries: Annotated[
        bool,
        typer.Option(
            "--compare-countries",
            help="Search from multiple countries via Tor and compare prices",
        ),
    ] = False,
    countries: Annotated[
        str | None,
        typer.Option(
            "--countries",
            help="Comma-separated country codes to compare (e.g. IN,MX,TH). "
            "Defaults to built-in cheap-country list.",
        ),
    ] = None,
):
    """Search for flights on a specific date.

    Example:
        fli flights JFK LHR 2025-10-25 --time 6-20 --airlines BA KL --stops NON_STOP
        fli flights JFK LHR 2025-10-25 --format json
        fli flights JFK LHR 2025-10-25 --exclude-basic
        fli flights JFK LAX 2025-10-25 --bags 1 --carry-on
        fli flights JFK LAX 2025-10-25 --emissions LESS
        fli flights JFK LAX 2025-10-25 --all

    """
    if compare_countries:
        country_list = parse_countries_flag(countries) if countries else None
        try:
            filters = _build_filters(
                origin=origin,
                destination=destination,
                departure_date=departure_date,
                return_date=return_date,
                departure_window=departure_window,
                airlines=airlines,
                cabin_class=cabin_class,
                max_stops=max_stops,
                sort_by=sort_by,
                exclude_basic_economy=exclude_basic_economy,
                layover=layover,
                emissions=emissions,
                checked_bags=checked_bags,
                carry_on=carry_on,
                all_results=all_results,
            )
        except (ParseError, AttributeError, ValueError) as e:
            typer.echo(f"Error: {e}")
            raise typer.Exit(1) from e

        typer.echo("Comparing prices from countries via Tor (this may take 3-5 minutes)...\n")
        try:
            results = search_all_countries(filters, countries=country_list)
        except TorNotRunningError as e:
            typer.echo(str(e))
            raise typer.Exit(1) from e
        _display_country_comparison(results)
        return

    _search_flights_core(
        origin=origin,
        destination=destination,
        departure_date=departure_date,
        return_date=return_date,
        departure_window=departure_window,
        airlines=airlines,
        cabin_class=cabin_class,
        max_stops=max_stops,
        sort_by=sort_by,
        exclude_basic_economy=exclude_basic_economy,
        layover=layover,
        emissions=emissions,
        checked_bags=checked_bags,
        carry_on=carry_on,
        all_results=all_results,
        output_format=output_format,
        currency=currency,
    )
