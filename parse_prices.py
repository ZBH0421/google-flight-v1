import json

files = ["dfw_biz.json", "iah_eco.json", "iah_biz.json"]
for f in files:
    try:
        with open(f, "r") as fp:
            data = json.load(fp)
            # data could be a dictionary or a list
            if isinstance(data, dict):
                data = data.get("dates", [])
            elif isinstance(data, list):
                # Filter out booleans or non-dicts
                data = [x for x in data if isinstance(x, dict) and "price" in x]

            # Sort by price
            sorted_data = sorted(data, key=lambda x: x["price"])
            print(f"\n--- {f} ---")
            for d in sorted_data[:5]:
                print(f"{d['departure_date']}: NT${d['price']}")
    except Exception as e:
        print(f"Failed to process {f}: {e}")
