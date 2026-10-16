"""Dash frontend for flight explore tool."""
import sys
sys.path.insert(0, "/Users/ph/dash_git_pre/fli")

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, dash_table, dcc, html

from explore_labels import label
from fli.models import Airport, SeatType
from search_explore import REGIONS, search

# ── Airport options (any airport in the fli Airport enum) ────────────────────

def _airport_label(iata: str) -> str:
    try:
        name = Airport[iata].value
        name = name.replace(" International Airport", "").replace(" Airport", "")
        return f"{iata}  {name}"
    except KeyError:
        return iata

# Major hub airports shown in dropdown (can be freely extended)
_HUB_IATAS = [
    # Taiwan
    "TPE","TSA","KHH",
    # Japan
    "NRT","HND","KIX","NGO","CTS","FUK","OKA",
    # Korea
    "ICN","GMP","PUS",
    # SE Asia
    "HKG","MFM","SIN","KUL","BKK","DMK","MNL","CGK","DPS","SGN","HAN",
    # China
    "PEK","PVG","CAN","SZX",
    # Middle East
    "DXB","DOH","AUH",
    # India
    "DEL","BOM",
    # Europe
    "LHR","CDG","AMS","FRA","MUC","IST",
    # USA
    "IAH","DFW","LAX","SFO","JFK","ORD",
    # Australia
    "SYD","MEL",
]

AIRPORT_OPTIONS = sorted(
    [{"label": _airport_label(k), "value": k}
     for k in _HUB_IATAS if k in Airport.__members__],
    key=lambda x: x["value"],
)

REGION_OPTIONS = list(REGIONS.keys()) + ["其他"]

# ── App ───────────────────────────────────────────────────────────────────────

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    title="Flight Explorer",
)

# ── Layout ────────────────────────────────────────────────────────────────────

controls = dbc.Card(
    dbc.CardBody([
        dbc.Row([
            dbc.Col([
                dbc.Label("出發機場"),
                dcc.Dropdown(
                    id="origin",
                    options=AIRPORT_OPTIONS,
                    value="TPE",
                    clearable=False,
                    style={"color": "#000"},
                ),
            ], md=3),
            dbc.Col([
                dbc.Label("出發日期（起）"),
                dbc.Input(id="start-date", type="date", value="2026-07-01"),
            ], md=2),
            dbc.Col([
                dbc.Label("出發日期（迄）"),
                dbc.Input(id="end-date", type="date", value="2026-07-31"),
            ], md=2),
            dbc.Col([
                dbc.Label("艙等"),
                dcc.Dropdown(
                    id="cabin",
                    options=[
                        {"label": "經濟艙", "value": "ECONOMY"},
                        {"label": "商務艙", "value": "BUSINESS"},
                    ],
                    value="ECONOMY",
                    clearable=False,
                    style={"color": "#000"},
                ),
            ], md=2),
            dbc.Col([
                dbc.Label(" "),  # spacer
                dbc.Button(
                    "🔍 開始搜尋", id="search-btn", color="primary",
                    className="w-100",
                ),
            ], md=3),
        ], className="g-3"),
        html.Hr(),
        dbc.Row([
            dbc.Col([
                dbc.Label("地區篩選"),
                dbc.Checklist(
                    id="regions",
                    options=[{"label": r, "value": r} for r in REGION_OPTIONS],
                    value=REGION_OPTIONS,
                    inline=True,
                ),
            ]),
        ]),
    ]),
    className="mb-3",
)

app.layout = dbc.Container([
    html.H3("✈ Flight Explorer", className="my-3"),
    controls,
    dcc.Loading(
        id="loading",
        type="circle",
        children=html.Div(id="results"),
        fullscreen=False,
        overlay_style={"visibility": "visible", "opacity": 0.5},
    ),
    html.Div(id="status", className="text-muted mt-2 small"),
], fluid=True)

# ── Table builder ─────────────────────────────────────────────────────────────

TABLE_COLS = [
    {"name": "#",          "id": "rank"},
    {"name": "IATA",       "id": "code"},
    {"name": "國家",       "id": "country"},
    {"name": "城市",       "id": "city"},
    {"name": "NT$",        "id": "price_fmt"},
    {"name": "最便宜日期", "id": "date_fmt"},
    {"name": "轉機",       "id": "stops_fmt"},
]

TABLE_STYLE = dict(
    style_table={"overflowX": "auto"},
    style_cell={
        "backgroundColor": "#2b2b2b",
        "color": "#f8f9fa",
        "border": "1px solid #444",
        "padding": "6px 12px",
        "fontFamily": "monospace",
    },
    style_header={
        "backgroundColor": "#1a1a2e",
        "fontWeight": "bold",
        "color": "#adb5bd",
        "border": "1px solid #555",
    },
    style_data_conditional=[
        {"if": {"row_index": "odd"}, "backgroundColor": "#333"},
        {"if": {"column_id": "price_fmt"}, "color": "#7fff7f", "fontWeight": "bold"},
        {"if": {"column_id": "code"}, "color": "#ffd700"},
        {"if": {"filter_query": '{stops_fmt} = "直飛"', "column_id": "stops_fmt"},
         "color": "#00bfff", "fontWeight": "bold"},
    ],
    page_size=50,
)


def make_table(table_id: str, rows: list[dict]) -> dash_table.DataTable:
    table_rows = []
    for i, r in enumerate(rows, 1):
        stops = r.get("stops")   # None = not queried, [] = confirmed non-stop
        if stops is None:
            stops_fmt = "—"
        elif len(stops) == 0:
            stops_fmt = "直飛"
        else:
            parts = [label(s)[1] or s for s in stops]
            stops_fmt = " → ".join(parts)
        country, city = label(r["code"])
        table_rows.append({
            "rank":      i,
            "code":      r["code"],
            "country":   country,
            "city":      city if city != r["code"] else r["name"],
            "price_fmt": f"NT${r['price']:,}",
            "date_fmt":  f"{r['date']} {r['dow']}",
            "stops_fmt": stops_fmt,
        })
    return dash_table.DataTable(
        id=table_id,
        columns=TABLE_COLS,
        data=table_rows,
        **TABLE_STYLE,
    )


def make_section(region: str, rows: list[dict]) -> list:
    cheapest = f"NT${rows[0]['price']:,}" if rows else "—"
    header = dbc.Row([
        dbc.Col(html.H5(f"▶ {region}", className="mb-0"), width="auto"),
        dbc.Col(
            dbc.Badge(f"最低 {cheapest}", color="success", className="ms-2"),
            width="auto", className="d-flex align-items-center",
        ),
        dbc.Col(
            dbc.Badge(f"{len(rows)} 條航線", color="secondary", className="ms-1"),
            width="auto", className="d-flex align-items-center",
        ),
    ], className="align-items-center mb-2")
    _ID_MAP = {"亞洲":"asia","大洋洲":"oceania","歐洲":"europe","美洲":"americas","中東 / 非洲":"mideast","其他":"other"}
    table_id = "table-" + _ID_MAP.get(region, region[:6])
    return [header, make_table(table_id, rows), html.Hr()]

# ── Callback ──────────────────────────────────────────────────────────────────

@app.callback(
    Output("results", "children"),
    Output("status", "children"),
    Input("search-btn", "n_clicks"),
    State("origin", "value"),
    State("start-date", "value"),
    State("end-date", "value"),
    State("regions", "value"),
    State("cabin", "value"),
    prevent_initial_call=True,
)
def run_search(n_clicks, origin, start_date, end_date, selected_regions, cabin):
    if not origin or not start_date or not end_date:
        return html.Div("請填寫所有欄位。", className="text-warning"), ""

    # Trim date strings (DatePickerRange sometimes returns with time component)
    start_date = str(start_date)[:10]
    end_date   = str(end_date)[:10]

    # [] means user deselected all → return empty; None means no filter
    region_filter = selected_regions if selected_regions else []
    if region_filter == REGION_OPTIONS:   # all selected = same as no filter
        region_filter = None

    seat = SeatType[cabin] if cabin in SeatType.__members__ else SeatType.ECONOMY

    if region_filter == []:
        return html.Div("請至少選擇一個地區。", className="text-warning"), ""

    results = search(origin, start_date, end_date,
                     regions=region_filter,
                     seat_type=seat,
                     include_stops=True)

    if not results:
        return html.Div("查無結果。", className="text-warning"), ""

    # Group by region (preserve REGION_OPTIONS order)
    grouped: dict[str, list] = {r: [] for r in REGION_OPTIONS}
    for r in results:
        grouped.setdefault(r["region"], []).append(r)

    sections = []
    for region in REGION_OPTIONS:
        rows = grouped.get(region, [])
        if rows:
            sections.extend(make_section(region, rows))

    status = f"共找到 {len(results)} 條有價格的航線 ({origin} → ???，{start_date} ~ {end_date})"
    return sections, status


if __name__ == "__main__":
    app.run(debug=True, port=8052)
