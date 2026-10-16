import json
import urllib.request

def get_exchange_rate(from_curr, to_curr="TWD"):
    if from_curr == to_curr:
        return 1.0
    # Hardcoded fallback rates just in case
    rates = {
        "USD": 32.5,
        "JPY": 0.21,
        "EUR": 35.0,
        "HKD": 4.15,
        "SGD": 24.0,
        "KRW": 0.024,
        "PHP": 0.55,
        "IDR": 0.002,
        "GBP": 40.5
    }
    return rates.get(from_curr, 1.0) # fallback to 1 if unknown

files = {"TPE -> NRT": "tpe_nrt.json", "NRT -> IAH": "nrt_iah.json", "NRT -> DFW": "nrt_dfw.json"}

for route, f in files.items():
    try:
        with open(f, "r") as fp:
            data = json.load(fp)
            dates = data.get("dates", [])

            # Sort by price
            sorted_data = sorted([d for d in dates if d.get("price")], key=lambda x: x["price"])
            print(f"\n--- {route} ---")
            for d in sorted_data[:5]:
                price = d["price"]
                curr = d["currency"]

                if curr != "TWD":
                    rate = get_exchange_rate(curr, "TWD")
                    converted = price * rate
                    print(f"{d['departure_date']}: {curr} {price:,.2f} (約 NT$ {converted:,.0f})")
                else:
                    print(f"{d['departure_date']}: NT$ {price:,.0f}")
    except Exception as e:
        print(f"Failed to process {f}: {e}")
