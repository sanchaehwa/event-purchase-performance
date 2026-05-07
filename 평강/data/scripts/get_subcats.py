import json, base64

with open("ably_debug2_response.json", encoding="utf-8") as f:
    d = json.load(f)

for comp in d["components"]:
    t = comp.get("type", {})
    if isinstance(t, dict) and t.get("item_list") == "FIVE_COL_ICON_LIST":
        for entry in comp["entity"]["item_list"]:
            item = entry["item"]
            dl = item.get("deeplink", "")
            if "next_token=" in dl:
                token = dl.split("next_token=")[1].split("&")[0]
                import urllib.parse
                token = urllib.parse.unquote(token)
                decoded = json.loads(base64.urlsafe_b64decode(token + "=="))
                sno = decoded.get("category_sno")
                print(f"{item['name']}: category_sno={sno}, token={token[:60]}...")
