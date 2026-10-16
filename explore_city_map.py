"""City/airport string → IATA code mapping for Wikipedia destination parsing."""
import unicodedata


def _normalize(s: str) -> str:
    """Lowercase + strip combining accent chars only (ō→o, ü→u), keep en-dash etc."""
    nfd = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")

# Wikipedia uses city names with optional airport disambiguation via en-dash (–).
# Keys are lowercase. Covers all common routes on major Asian hub airports.
CITY_TO_IATA = {
    # Taiwan
    "taipei": "TPE", "taipei–taoyuan": "TPE", "taipei–songshan": "TSA",
    "kaohsiung": "KHH", "taichung": "RMQ",

    # Japan
    "tokyo": "NRT", "tokyo–narita": "NRT", "narita": "NRT",
    "tokyo–haneda": "HND", "haneda": "HND",
    "osaka": "KIX", "osaka–kansai": "KIX", "osaka–itami": "ITM",
    "nagoya": "NGO", "nagoya–centrair": "NGO",
    "sapporo": "CTS", "sapporo–new chitose": "CTS", "sapporo–chitose": "CTS",
    "new chitose": "CTS",
    "fukuoka": "FUK", "naha": "OKA", "okinawa": "OKA", "ishigaki": "ISG",
    "hiroshima": "HIJ", "sendai": "SDJ", "akita": "AXT",
    "aomori": "AOJ", "asahikawa": "AKJ", "hakodate": "HKD",
    "takamatsu": "TAK", "kagoshima": "KOJ", "miyazaki": "KMI",
    "kumamoto": "KMJ", "oita": "OIT", "nagasaki": "NGS",
    "miyako": "MMY",

    # Korea
    "seoul": "ICN", "seoul–incheon": "ICN", "incheon": "ICN",
    "seoul–gimpo": "GMP", "gimpo": "GMP",
    "busan": "PUS", "gimhae": "PUS",
    "jeju": "CJU", "daegu": "TAE",

    # Hong Kong / Macau
    "hong kong": "HKG", "macau": "MFM",

    # Southeast Asia
    "singapore": "SIN", "singapore–changi": "SIN",
    "kuala lumpur": "KUL", "kuala lumpur–international": "KUL",
    "kuala lumpur–subang": "SZB", "penang": "PEN",
    "kota kinabalu": "BKI", "kuching": "KCH", "johor bahru": "JHB",
    "bangkok": "BKK", "bangkok–suvarnabhumi": "BKK",
    "bangkok–don mueang": "DMK",
    "chiang mai": "CNX", "phuket": "HKT",
    "manila": "MNL", "cebu": "CEB", "clark": "CRK",
    "jakarta": "CGK", "jakarta–soekarno–hatta": "CGK",
    "jakarta–soekarno-hatta": "CGK",
    "bali": "DPS", "denpasar": "DPS", "surabaya": "SUB",
    "ho chi minh city": "SGN", "ho chi minh": "SGN",
    "hanoi": "HAN", "da nang": "DAD",
    "phnom penh": "PNH", "siem reap": "REP",
    "vientiane": "VTE", "yangon": "RGN",
    "bandar seri begawan": "BWN",

    # China
    "beijing": "PEK", "beijing–capital": "PEK", "beijing–daxing": "PKX",
    "shanghai": "PVG", "shanghai–pudong": "PVG", "shanghai–hongqiao": "SHA",
    "guangzhou": "CAN", "shenzhen": "SZX",
    "chengdu": "TFU", "chengdu–tianfu": "TFU", "chengdu–shuangliu": "CTU",
    "chongqing": "CKG", "kunming": "KMG", "wuhan": "WUH",
    "hangzhou": "HGH", "xiamen": "XMN", "qingdao": "TAO",
    "nanjing": "NKG", "tianjin": "TSN", "harbin": "HRB",
    "shenyang": "SHE", "dalian": "DLC", "zhengzhou": "CGO",
    "xi'an": "XIY", "urumqi": "URC", "haikou": "HAK", "sanya": "SYX",
    "changsha": "CSX", "jinan": "TNA", "nanning": "NNG",
    "guiyang": "KWE", "fuzhou": "FOC", "nanchang": "KHN",
    "hefei": "HFE", "taiyuan": "TYN", "lanzhou": "LHW",

    # South Asia
    "delhi": "DEL", "new delhi": "DEL",
    "mumbai": "BOM", "kolkata": "CCU", "chennai": "MAA",
    "hyderabad": "HYD", "bangalore": "BLR", "bangalore–kempegowda": "BLR",
    "ahmedabad": "AMD", "goa": "GOI",
    "islamabad": "ISB", "karachi": "KHI", "lahore": "LHE",
    "kathmandu": "KTM", "dhaka": "DAC",
    "colombo": "CMB", "male": "MLE", "maldives": "MLE",

    # Middle East
    "dubai": "DXB", "dubai–international": "DXB",
    "dubai–al maktoum": "DWC",
    "abu dhabi": "AUH", "doha": "DOH", "muscat": "MCT",
    "riyadh": "RUH", "jeddah": "JED",
    "kuwait": "KWI", "kuwait city": "KWI",
    "bahrain": "BAH", "amman": "AMM", "beirut": "BEY",
    "tel aviv": "TLV", "tehran": "IKA",

    # Central Asia
    "almaty": "ALA", "tashkent": "TAS", "ashgabat": "ASB", "baku": "GYD",

    # Pacific
    "guam": "GUM", "saipan": "SPN",
    "honolulu": "HNL", "hawaii": "HNL",

    # North America
    "los angeles": "LAX", "san francisco": "SFO", "seattle": "SEA",
    "vancouver": "YVR", "anchorage": "ANC",
    "anchorage- ted stevens": "ANC", "anchorage–ted stevens": "ANC",
    "anchorage–elmendorf": "EDF",
    "new york": "JFK", "new york–john f. kennedy": "JFK",
    "new york–jfk": "JFK",
    "chicago": "ORD", "chicago–o'hare": "ORD",
    "dallas": "DFW", "dallas/fort worth": "DFW",
    "houston": "IAH", "houston–intercontinental": "IAH",
    "miami": "MIA",
    "boston": "BOS", "washington": "IAD", "washington–dulles": "IAD",
    "atlanta": "ATL", "detroit": "DTW",
    "minneapolis": "MSP", "phoenix": "PHX", "phoenix–sky harbor": "PHX",
    "las vegas": "LAS", "denver": "DEN",
    "toronto": "YYZ", "toronto–pearson": "YYZ",
    "montreal": "YUL", "calgary": "YYC",
    "mexico city": "MEX",
    "memphis": "MEM", "indianapolis": "IND", "louisville": "SDF",

    # South America
    "são paulo": "GRU", "sao paulo": "GRU",
    "bogotá": "BOG", "bogota": "BOG", "lima": "LIM",

    # Europe
    "london": "LHR", "london–heathrow": "LHR", "london–gatwick": "LGW",
    "paris": "CDG", "paris–charles de gaulle": "CDG", "paris–orly": "ORY",
    "amsterdam": "AMS", "frankfurt": "FRA", "munich": "MUC",
    "zurich": "ZRH", "zürich": "ZRH", "geneva": "GVA",
    "vienna": "VIE", "rome": "FCO", "rome–fiumicino": "FCO",
    "milan": "MXP", "milan–malpensa": "MXP", "milan–linate": "LIN",
    "madrid": "MAD", "barcelona": "BCN", "lisbon": "LIS",
    "istanbul": "IST", "athens": "ATH",
    "brussels": "BRU", "copenhagen": "CPH",
    "stockholm": "ARN", "helsinki": "HEL", "oslo": "OSL",
    "prague": "PRG", "warsaw": "WAW", "budapest": "BUD",
    "bucharest": "OTP", "lyon": "LYS", "nice": "NCE",
    "marseille": "MRS", "toulouse": "TLS",
    "cologne": "CGN", "cologne/bonn": "CGN",
    "düsseldorf": "DUS", "dusseldorf": "DUS",
    "hamburg": "HAM", "berlin": "BER",
    "venice": "VCE", "naples": "NAP",
    "birmingham": "BHX", "manchester": "MAN",
    "edinburgh": "EDI", "glasgow": "GLA", "dublin": "DUB",
    "luxembourg": "LUX",

    # Africa / Oceania
    "johannesburg": "JNB", "nairobi": "NBO",
    "casablanca": "CMN", "cairo": "CAI", "addis ababa": "ADD",
    "sydney": "SYD", "melbourne": "MEL", "brisbane": "BNE",
    "perth": "PER", "auckland": "AKL", "christchurch": "CHC",

    # US secondary
    "cincinnati": "CVG", "columbus": "CMH", "columbus–rickenbacker": "LCK",
    "portland": "PDX", "salt lake city": "SLC", "san diego": "SAN",
    "nashville": "BNA", "charlotte": "CLT", "philadelphia": "PHL",
    "ontario": "ONT", "seattle/tacoma": "SEA",

    # China secondary
    "ningbo": "NGB",

    # Middle East secondary
    "sharjah": "SHJ",

    # Vietnam secondary
    "phu quoc": "PQC",

    # Japan secondary
    "cheongju": "CJJ", "kitakyushu": "KKJ", "kobe": "UKB",
    "komatsu": "KMQ", "matsuyama": "MYJ", "ibaraki": "IBR",
    "hanamaki": "HNA", "fukushima": "FKS",
    "kochi": "KCZ", "kochi": "KCZ",
    "niigata": "KIJ", "okayama": "OKJ", "saga": "HSG",
    "toyama": "TOY", "yonago": "YGJ", "shimojishima": "SHI",
    "oita": "OIT",

    # Korea secondary
    "muan": "MWX",

    # Pacific
    "koror": "ROR", "palau": "ROR",

    # Southeast Asia secondary
    "manado": "MDC", "nha trang": "NHA", "dong hoi": "VDH",

    # Belgium / misc
    "liège": "LGG", "leige": "LGG",

    # ── Extended global coverage (non-TPE origins) ────────────────────────────
    # Scandinavia / Northern Europe
    "aalborg": "AAL", "ålesund": "AES", "alta": "ALF", "arvidsjaur": "AJR",
    "bergen": "BGO", "billund": "BLL", "bodø": "BOO", "gothenburg": "GOT",
    "inverness": "INV", "ivalo": "IVL", "kristiansand": "KRS",
    "newcastle": "NCL", "norwich": "NWI", "oulu": "OUL", "rovaniemi": "RVN",
    "shannon": "SNN", "tromsø": "TOS", "turku": "TKU",

    # UK / Ireland
    "aberdeen": "ABZ", "asheville": "AVL", "belfast": "BFS",
    "belfast–city": "BFS", "belfast–international": "BFS",
    "bristol": "BRS", "cardiff": "CWL", "cork": "ORK",
    "east midlands": "EMA", "exeter": "EXT", "guernsey": "GCI",
    "isle of man": "IOM", "jersey": "JER", "leeds bradford": "LBA",

    # Western Europe
    "alghero": "AHO", "alicante": "ALC", "antalya": "AYT",
    "asturias": "OVD", "bari": "BRI", "bastia": "BIA", "biarritz": "BIQ",
    "bilbao": "BIO", "bologna": "BLQ", "bordeaux": "BOD", "bremen": "BRE",
    "brindisi": "BDS", "brno": "BRQ", "cagliari": "CAG", "catania": "CTA",
    "chania": "CHQ", "cluj-napoca": "CLJ", "cork": "ORK", "craiova": "CRA",
    "dalaman": "DLM", "debrecen": "DEB", "dortmund": "DTM", "dresden": "DRS",
    "dubrovnik": "DBV", "faro": "FAO", "fuerteventura": "FUE",
    "genoa": "GOA", "gibraltar": "GIB", "girona": "GRO", "gothenburg": "GOT",
    "gran canaria": "LPA", "graz": "GRZ", "hannover": "HAJ",
    "ibiza": "IBZ", "innsbruck": "INN", "la palma": "SPC",
    "lamezia terme": "SUF", "lanzarote": "ACE", "linz": "LNZ",
    "malaga": "AGP", "málaga": "AGP", "menorca": "MAH",
    "montpellier": "MPL", "nuremberg": "NUE", "olbia": "OLB",
    "palermo": "PMO", "palma de mallorca": "PMI", "paphos": "PFO",
    "pisa": "PSA", "podgorica": "TGD", "poznań": "POZ", "pristina": "PRN",
    "rhodes": "RHO", "riga": "RIX", "salzburg": "SZG", "santorini": "JTR",
    "sarajevo": "SJJ", "shannon": "SNN", "skopje": "SKP", "sofia": "SOF",
    "split": "SPU", "strasbourg": "SXB", "stuttgart": "STR",
    "tallinn": "TLL", "thessaloniki": "SKG", "tirana": "TIA",
    "tivat": "TIV", "trieste": "TRS", "varna": "VAR", "verona": "VRN",
    "vilnius": "VNO", "valencia": "VLC", "valletta": "MLA",
    "zagreb": "ZAG", "bratislava": "BTS", "katowice": "KTW",
    "wroclaw": "WRO", "lublin": "LUZ",

    # Eastern Europe / Russia
    "astrakhan": "ASF", "chita": "HTA", "chișinău": "RMO",
    "dnipro": "DNK", "dushanbe": "DYU", "ekaterinburg": "SVX",
    "irkutsk": "IKT", "iași": "IAS", "kazan": "KZN",
    "khabarovsk": "KHV", "krasnodar": "KRR", "minsk": "MSQ",
    "moscow–domodedovo": "DME", "moscow–sheremetyevo": "SVO",
    "moscow–vnukovo": "VKO", "nizhny novgorod": "GOJ",
    "oradea": "OMR", "reykjavik": "RKV", "reykjavík": "RKV",
    "reykjavík–keflavík": "KEF", "sochi": "AER", "tallinn": "TLL",
    "tbilisi": "TBS", "vladivostok": "VVO", "volgograd": "VOG",
    "yerevan": "EVN", "zagreb": "ZAG",

    # Middle East / Central Asia
    "al najaf": "NJF", "andizhan": "AZN", "aden": "ADE",
    "aktau": "SCO", "atyrau": "GUW", "baghdad": "BGW",
    "bandar abbas": "BND", "bukhara": "BHK", "busher": "BUZ",
    "bushehr": "BUZ", "erbil": "EBL", "fujairah": "FJR",
    "ganja": "GNJ", "hatay": "HTY", "kabul": "KBL", "kashgar": "KHG",
    "kaunas": "KUN", "larnaca": "LCA", "mashhad": "MHD",
    "multan": "MUX", "nakhchivan": "NAJ", "navoi": "NVI",
    "ras al khaimah": "RKT", "salalah": "SLL", "samarkand": "SKD",
    "sharm el sheikh": "SSH", "sharm el-sheikh": "SSH",
    "sulaymaniyah": "ISU", "tabriz": "TBZ", "tabuk": "TUU",
    "trabzon": "TZX",

    # Africa
    "abuja": "ABV", "accra": "ACC", "asmara": "ASM",
    "antananarivo": "TNR", "assiut": "ATZ", "banjul": "BJL",
    "bosaso": "BSA", "conakry": "CKY", "cotonou": "COO",
    "dakar": "DKR", "djibouti": "JIB", "douala": "DLA",
    "entebbe": "EBB", "gaborone": "GBE", "harare": "HRE",
    "hurghada": "HRG", "juba": "JUB", "kano": "KAN",
    "kilimanjaro": "JRO", "kigali": "KGL", "kinshasa": "FIH",
    "lagos": "LOS", "libreville": "LBV", "lomé": "LFW",
    "luanda": "LAD", "lubumbashi": "FBM", "lusaka": "LUN",
    "luxor": "LXR", "malabo": "SSG", "maputo": "MPM",
    "marsa alam": "RMF", "mogadishu": "MGQ", "mombasa": "MBA",
    "monrovia": "ROB", "n'djamena": "NDJ", "nairobi": "NBO",
    "nouakchott": "NKC", "olbia": "OLB", "oran": "ORA",
    "ouagadougou": "OUA", "port harcourt": "PHC",
    "windhoek": "WDH", "windhoek–hosea kutako": "WDH",
    "yaoundé": "YAO", "zanzibar": "ZNZ",

    # South / Latin America
    "barranquilla": "BAQ", "bogota": "BOG", "bogotá": "BOG",
    "florianopolis": "FLN", "guadalajara": "GDL",
    "guatemala city": "GUA", "havana": "HAV", "joinville": "JOI",
    "medellin": "MDE", "montevideo": "MVD",
    "panama city–tocumen": "PTY", "paramaribo": "PBM",
    "punta cana": "PUJ", "quebec city": "YQB", "quito": "UIO",
    "recife": "REC", "rio de janeiro": "GIG",
    "rio de janeiro–galeão": "GIG", "santiago": "SCL",
    "tobago": "TAB",

    # North America
    "albany": "ALB", "ancona": "AOI", "aspen": "ASE",
    "austin": "AUS", "baltimore": "BWI", "bangor": "BGR",
    "belize city": "BZE", "buffalo": "BUF", "cancún": "CUN",
    "cleveland": "CLE", "colorado springs": "COS",
    "corpus christi": "CRP", "des moines": "DSM",
    "durango": "DRO", "el paso": "ELP", "edmonton": "YEG",
    "fort lauderdale": "FLL", "fresno": "FAT", "jacksonville": "JAX",
    "kansas city": "MCI", "loreto": "LTO",
    "myrtle beach": "MYR", "norfolk": "ORF", "orlando": "MCO",
    "pensacola": "PNS", "raleigh/durham": "RDU",
    "roanoke": "ROA", "sacramento": "SMF", "san antonio": "SAT",
    "sarasota": "SRQ", "savannah": "SAV", "spokane": "GEG",
    "st. john's": "YYT", "tampa": "TPA", "tucson": "TUS",
    "tulsa": "TUL", "winnipeg": "YWG",

    # South / Southeast Asia
    "ajmer": "KQH", "amritsar": "ATQ", "aurangabad": "IXU",
    "avalon": "AVV", "bagdogra": "IXB", "balikpapan": "BPN",
    "banda aceh": "BTJ", "bandung": "BDO", "bandung–kertajati": "KJT",
    "bangui": "BGF", "banjarmasin": "BDJ", "barbados": "BGI",
    "batam": "BTH", "belgaum": "IXG", "bengaluru": "BLR",
    "bhopal": "BHO", "cairns": "CNS", "calicut": "CCJ",
    "canberra": "CBR", "cape town": "CPT", "chandigarh": "IXC",
    "chiang rai": "CEI", "cochin": "COK", "coimbatore": "CJB",
    "darwin": "DRW", "davao": "DVO", "dehradun": "DED",
    "dibrugarh": "DIB", "dili": "DIL", "general santos": "GES",
    "gold coast": "OOL", "guilin": "KWL", "guwahati": "GAU",
    "hat yai": "HDY", "iloilo": "ILO", "imphal": "IMF",
    "jaipur": "JAI", "jammu": "IXJ", "jodhpur": "JDH",
    "juba": "JUB", "kahului": "OGG", "kalibo": "KLO",
    "kannur": "CNN", "karachi": "KHI", "khon kaen": "KKC",
    "kinmen": "KNH", "krabi": "KBV", "kuantan": "KUA",
    "labuan": "LBU", "langkawi": "LGK", "laoag": "LAO",
    "madurai": "IXM", "malacca": "MKZ", "mandalay": "MDL",
    "miri": "MYY", "nagpur": "NAG", "nadi": "NAN",
    "nassau": "NAS", "padang": "PDG", "palembang": "PLM",
    "paro": "PBH", "port moresby": "POM", "pune": "PNQ",
    "raipur": "RPR", "sandakan": "SDK", "seychelles": "SEZ",
    "surabaya": "SUB", "tainan": "TNN", "taitung": "TTT",
    "udon thani": "UTH", "ulaanbaatar": "ULN",
    "varanasi": "VNS", "zamboanga": "ZAM",
    "yogyakarta–international": "YIA",

    # Japan extended
    "amakusa": "AXJ", "fukue": "FUJ", "hualien": "HUN",
    "kushiro": "KUH", "matsumoto": "MMJ", "memanbetsu": "MMB",
    "tokushima": "TKS",

    # Korea extended
    "gwangju": "KWJ", "ulsan": "USN", "yeosu": "RSU",

    # China extended
    "aksu": "AKU", "ankang": "AKA", "anqing": "AQG",
    "anyang": "AYN", "baotou": "BAV", "beihai": "BHY",
    "bengbu": "BFU", "changde": "CGD", "changzhi": "CIH",
    "changzhou": "CZX", "chifeng": "CIF", "dali": "DLU",
    "dandong": "DDG", "datong": "DAT", "dunhuang": "DNH",
    "enshi": "ENH", "ganzhou": "KOW", "guangyuan": "GYS",
    "guilin": "KWL", "hami": "HMI", "handan": "HDG",
    "hanzhong": "HZG", "hengyang": "HNY", "hohhot": "HET",
    "hotan": "HTN", "jiamusi": "JMU", "jiayuguan": "JGN",
    "jingdezhen": "JDZ", "jinzhou": "JNZ", "lianyungang": "LYG",
    "lijiang": "LJG", "luoyang": "LYA", "luzhou": "LZO",
    "nanchong": "NAO", "nantong": "NTG", "tongliao": "TGO",
    "xilinhot": "XIL", "yamagata": "GAJ", "yichang": "YIH",
    "yinchuan": "INC", "zhangjiajie": "DYG", "zhuhai": "ZUH",

    # Middle East misc
    "algiers": "ALG", "ankara": "ESB", "erbil": "EBL",
    "faisalabad": "LYP", "gassim": "ELQ", "gaziantep": "GZT",
    "gazipasa": "GZP", "gazipaşa": "GZP",
    "hurghada": "HRG", "pyongyang": "FNJ",
    "quetta": "UET", "rabat": "RBA", "santiago de compostela": "SCQ",
    "vilnius": "VNO",
}


# Pre-normalize all dict keys so lookup always works on NFD-stripped ASCII
_NORMALIZED = {_normalize(k): v for k, v in CITY_TO_IATA.items()}


def lookup(city_str: str) -> str | None:
    """Return IATA code for a Wikipedia destination string, or None."""
    key = _normalize(city_str.strip())
    if key in _NORMALIZED:
        return _NORMALIZED[key]
    # Try disambiguated parts after '–' (en-dash)
    if "–" in key:
        parts = [p.strip() for p in key.split("–")]
        for part in reversed(parts):
            if part in _NORMALIZED:
                return _NORMALIZED[part]
        if parts[0] in _NORMALIZED:
            return _NORMALIZED[parts[0]]
    return None
