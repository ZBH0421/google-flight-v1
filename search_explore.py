"""
Explore cheapest destinations from any airport.

CLI usage:
    python3 search_explore.py [ORIGIN] [START_DATE] [END_DATE]

Importable:
    from search_explore import search, REGIONS, get_region
"""
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

sys.path.insert(0, "/Users/ph/dash_git_pre/fli")

from explore_fr24 import get_destinations   # FR24 primary; falls back to Wikipedia
from fli.models import (
    Airport,
    DateSearchFilters,
    FlightSearchFilters,
    FlightSegment,
    MaxStops,
    PassengerInfo,
    SeatType,
    TripType,
)
from fli.search.dates import SearchDates
from fli.search.flights import SearchFlights

ORIGIN      = sys.argv[1] if len(sys.argv) > 1 else "TPE"
START_DATE  = sys.argv[2] if len(sys.argv) > 2 else "2026-06-01"
END_DATE    = sys.argv[3] if len(sys.argv) > 3 else "2026-06-30"
TOP_N       = 20   # how many results per region
SLEEP_SEC   = 1.2  # polite delay between Google Flights calls

REGIONS: dict[str, set[str]] = {
    "亞洲": {
        "MNL","CEB","CRK",                                    # Philippines
        "ICN","GMP","PUS","CJU","TAE","CJJ","MWX",            # Korea
        "NRT","HND","KIX","NGO","CTS","FUK","OKA","SDJ",     # Japan main
        "AOJ","AKJ","AXT","FKS","HKD","HIJ","HNA","IBR",     # Japan regional
        "KCZ","KIJ","KKJ","KMI","KMJ","KMQ","KOJ","MYJ",
        "OIT","OKJ","TAK","TOY","YGJ","HSG","UKB",
        "HKG","MFM","TSA","KHH",                              # HK/Macau/TW
        "SIN","KUL","PEN","BKI","KCH","JHB",                 # Malaysia/Singapore
        "BKK","DMK","CNX","HKT",                              # Thailand
        "SGN","HAN","DAD","PQC","VDH",                        # Vietnam
        "CGK","DPS","SUB","MDC",                              # Indonesia
        "RGN","PNH","VTE","BWN",                              # Myanmar/Cambodia/Laos/Brunei
        "DEL","BOM","CCU","MAA","HYD","BLR","AMD","GOI",     # India
        "CMB","MLE","KTM","DAC",                              # SL/Maldives/Nepal/BD
        "ISB","KHI","LHE",                                    # Pakistan
        "PEK","PKX","PVG","SHA","CAN","SZX","TFU","CTU",     # China major
        "CKG","KMG","WUH","HGH","XMN","TAO","NKG","TSN",    # China secondary
        "HRB","SHE","DLC","CGO","XIY","URC","HAK","SYX",
        "CSX","TNA","NNG","KWE","FOC","KHN","HFE","TYN",
        "LHW","NGB",
        "GUM","SPN","ROR","ISG","SHI","MMY",                  # Pacific islands
        "ALA","TAS","ASB","GYD","BAH","KWI","MCT",            # Central Asia / Gulf
        "DXB","DWC","AUH","DOH","RUH","JED","AMM","BEY","TLV","IKA","SHJ",
    },
    "大洋洲": {
        "SYD","MEL","BNE","PER","AKL","CHC",
    },
    "歐洲": {
        "LHR","LGW","CDG","ORY","AMS","FRA","MUC","ZRH","GVA",
        "VIE","FCO","LIN","MXP","MAD","BCN","LIS","ATH","IST",
        "BRU","CPH","ARN","HEL","OSL","PRG","WAW","BUD","OTP",
        "LYS","NCE","MRS","TLS","CGN","DUS","HAM","BER","VCE",
        "NAP","BHX","MAN","EDI","GLA","DUB","LUX","LGG","BOD",
    },
    "美洲": {
        "LAX","SFO","SEA","YVR","ANC",                        # West Coast / Canada W
        "JFK","BOS","IAD","MIA","ORD","ATL","DFW","IAH",     # East / Central / South
        "PHX","LAS","DEN","SAN","PDX","SLC","ONT",
        "DTW","MSP","CVG","IND","MEM","SDF","LCK","EDF",
        "YYZ","YUL","YYC",                                    # Canada East
        "MEX","GRU","BOG","LIM",                              # Latin America
    },
    "中東 / 非洲": {
        "JNB","NBO","CMN","CAI","ADD",
    },
}


DAY_ABBR = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def get_region(code: str) -> str:
    for region, codes in REGIONS.items():
        if code in codes:
            return region
    return "其他"


def fetch_cheapest(
    origin_ap: Airport, dest_ap: Airport, start_date: str, end_date: str,
    seat_type: SeatType = SeatType.ECONOMY,
) -> tuple[float, str] | tuple[None, None]:
    s = SearchDates()
    filters = DateSearchFilters(
        trip_type=TripType.ONE_WAY,
        passenger_info=PassengerInfo(adults=1),
        flight_segments=[
            FlightSegment(
                departure_airport=[[origin_ap, 0]],
                arrival_airport=[[dest_ap, 0]],
                travel_date=start_date,
            )
        ],
        seat_type=seat_type,
        stops=MaxStops.ANY,
        from_date=start_date,
        to_date=end_date,
    )
    try:
        results = s.search(filters)
    except Exception:
        return None, None

    if not results:
        return None, None

    best = min(results, key=lambda r: r.price)
    date_str = best.date[0].strftime("%Y-%m-%d") if best.date else "?"
    return best.price, date_str


def fetch_stops(
    origin_ap: Airport, dest_ap: Airport, date_str: str
) -> list[str]:
    """Return list of intermediate airport IATA codes (empty = non-stop)."""
    s = SearchFlights()
    filters = FlightSearchFilters(
        trip_type=TripType.ONE_WAY,
        passenger_info=PassengerInfo(adults=1),
        flight_segments=[
            FlightSegment(
                departure_airport=[[origin_ap, 0]],
                arrival_airport=[[dest_ap, 0]],
                travel_date=date_str,
            )
        ],
        seat_type=SeatType.ECONOMY,
        stops=MaxStops.ANY,
    )
    try:
        results = [r for r in s.search(filters) if r.price > 0]
    except Exception:
        return []
    if not results:
        return []
    best = min(results, key=lambda r: r.price)
    # Intermediate stops = arrival airports of all legs except the last
    stops = []
    for leg in best.legs[:-1]:
        if leg.arrival_airport:
            stops.append(leg.arrival_airport.name)  # IATA code
    return stops


def _search_one(args: tuple) -> dict | None:
    """Worker: SearchDates for one destination. Runs in thread pool."""
    origin_ap, dest_ap, code, region, dest_name, start_date, end_date, seat_type = args
    try:
        price, date_str = fetch_cheapest(origin_ap, dest_ap, start_date, end_date, seat_type)
    except Exception:
        return None
    if not price or not date_str or date_str == "?":
        return None
    d = datetime.strptime(date_str, "%Y-%m-%d")
    return {
        "price":  int(price),
        "code":   code,
        "name":   dest_name,
        "date":   date_str,
        "dow":    DAY_ABBR[d.weekday()],
        "region": region,
        "stops":  None,   # None = not yet queried; [] = confirmed non-stop
    }


def _fetch_stops_worker(args: tuple) -> tuple[str, list[str]]:
    """Worker: SearchFlights for one destination's stop detail."""
    origin_ap, dest_ap, code, date_str = args
    return code, fetch_stops(origin_ap, dest_ap, date_str)


def search(
    origin: str,
    start_date: str,
    end_date: str,
    regions: list[str] | None = None,
    seat_type: SeatType = SeatType.ECONOMY,
    include_stops: bool = True,
    stops_top_n: int = 20,
    max_workers: int = 8,
    stops_workers: int = 5,
    progress_cb=None,
) -> list[dict]:
    """
    Phase 1 — parallel SearchDates (max_workers threads).
    Phase 2 — parallel SearchFlights for the top stops_top_n cheapest (stops_workers threads).
    progress_cb(done, total) called after each Phase 1 future completes.
    """
    dest_codes = get_destinations(origin, verbose=False)
    try:
        origin_ap = Airport[origin.upper()]
    except KeyError:
        return []

    # Build task list (filter by region up front)
    tasks = []
    for code in sorted(dest_codes):
        try:
            dest_ap = Airport[code]
        except KeyError:
            continue
        region = get_region(code)
        if regions and region not in regions:
            continue
        dest_name = dest_ap.value.replace(" Airport", "").replace(" International", "")
        tasks.append((origin_ap, dest_ap, code, region, dest_name, start_date, end_date, seat_type))

    # ── Phase 1: parallel SearchDates ────────────────────────────────────────
    results: list[dict] = []
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        future_to_code = {pool.submit(_search_one, t): t[2] for t in tasks}
        done = 0
        for future in as_completed(future_to_code):
            done += 1
            if progress_cb:
                progress_cb(done, len(tasks))
            result = future.result()
            if result:
                results.append(result)

    results.sort(key=lambda r: r["price"])

    # ── Phase 2: parallel SearchFlights for top-N only ───────────────────────
    if include_stops:
        top = results[:stops_top_n]
        stop_tasks = []
        for r in top:
            try:
                dest_ap = Airport[r["code"]]
            except KeyError:
                continue
            stop_tasks.append((origin_ap, dest_ap, r["code"], r["date"]))

        code_to_stops: dict[str, list[str]] = {}
        with ThreadPoolExecutor(max_workers=stops_workers) as pool:
            for future in as_completed(pool.submit(_fetch_stops_worker, t) for t in stop_tasks):
                try:
                    code, stops = future.result()
                    code_to_stops[code] = stops
                except Exception:
                    pass

        for r in top:
            r["stops"] = code_to_stops.get(r["code"], [])

    return results


def run():
    print(f"\nExplore: {ORIGIN} → ???   {START_DATE} ~ {END_DATE}\n")
    print("Fetching destinations from Wikipedia...", flush=True)

    try:
        dest_codes = get_destinations(ORIGIN, verbose=True)
    except ValueError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    total = len(dest_codes)
    print(f"  Searching {total} destinations...\n")
    origin_ap = Airport[ORIGIN.upper()]
    results_raw, not_found = [], []

    for i, code in enumerate(sorted(dest_codes), 1):
        try:
            dest_ap = Airport[code]
        except KeyError:
            not_found.append(code)
            continue

        dest_name = dest_ap.value.replace(" Airport", "").replace(" International", "")
        print(f"  [{i:3}/{total}] {code}  {dest_name:<35} ...", end="", flush=True)

        price, date_str = fetch_cheapest(origin_ap, dest_ap, START_DATE, END_DATE)
        if price and date_str:
            d = datetime.strptime(date_str, "%Y-%m-%d")
            dow = DAY_ABBR[d.weekday()]
            print(f" NT${price:>8,.0f}  [{date_str} {dow}]")
            results_raw.append((price, code, dest_name, date_str, dow))
        else:
            print(" —")
        time.sleep(SLEEP_SEC)

    results = sorted(results_raw)

    print(f"\n{'═'*72}")
    print(f"  {ORIGIN} 最便宜目的地  {START_DATE} ~ {END_DATE}  （全部排名）")
    print(f"{'═'*72}")
    print(f"  {'#':<4} {'IATA':<5} {'地區':<10} {'目的地':<30} {'NT$':>9}  {'日期'}")
    print(f"  {'─'*66}")
    for rank, (price, code, name, date_str, dow) in enumerate(results[:TOP_N], 1):
        print(f"  {rank:<4} {code:<5} {get_region(code):<10} {name:<30} {price:>9,.0f}  {date_str} ({dow})")

    region_results: dict[str, list] = {r: [] for r in REGIONS}
    region_results["其他"] = []
    for item in results:
        region_results[get_region(item[1])].append(item)

    for region, items in region_results.items():
        if not items:
            continue
        print(f"\n{'─'*72}")
        print(f"  ▶ {region}")
        print(f"{'─'*72}")
        print(f"  {'#':<4} {'IATA':<5} {'目的地':<35} {'NT$':>9}  {'日期'}")
        for rank, (price, code, name, date_str, dow) in enumerate(items[:TOP_N], 1):
            print(f"  {rank:<4} {code:<5} {name:<35} {price:>9,.0f}  {date_str} ({dow})")

    if not_found:
        print(f"\n  (略過 — Airport enum 不支援: {', '.join(not_found)})")
    print(f"\n  共 {len(results)} 條航線有價格，{len(not_found)} 條略過")


if __name__ == "__main__":
    run()
