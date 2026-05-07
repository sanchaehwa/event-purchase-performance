import asyncio
import json
import urllib.parse
from playwright.async_api import async_playwright

INIT_TOKEN = "eyJsIjogIkRlcGFydG1lbnRDYXRlZ29yeVJlYWx0aW1lUmFua0dlbmVyYXRvciIsICJwIjogeyJkZXBhcnRtZW50X3R5cGUiOiAiQ0FURUdPUlkiLCAiY2F0ZWdvcnlfc25vIjogN30sICJkIjogIkNBVEVHT1JZIiwgInByZXZpb3VzX3NjcmVlbl9uYW1lIjogIkNMT1RISU5HX0NBVEVHT1JZX0RFUEFSVE1FTlQiLCAiY2F0ZWdvcnlfc25vIjogN30="
URL = f"https://api.a-bly.com/api/v2/screens/CATEGORY_DEPARTMENT/?next_token={urllib.parse.quote(INIT_TOKEN)}"

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Origin": "https://m.a-bly.com",
    "Referer": "https://m.a-bly.com/",
    "sec-ch-ua": '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
    "x-anonymous-token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhbm9ueW1vdXNfaWQiOiIxMDQ1MTA4MDY0IiwiaWF0IjoxNzc3NjA4MTkyfQ.toKoKuz7rBu71qbg0RaBQhF8PZbcHH4ugBQHWstklS4",
    "x-app-version": "0.1.0",
    "x-device-id": "60db17fa-a366-4c82-961f-7116522c665f",
    "x-device-type": "PCWeb",
    "x-web-type": "Web",
}

async def debug():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=HEADERS["User-Agent"])
        page = await context.new_page()
        await page.goto("https://m.a-bly.com", wait_until="networkidle")
        await asyncio.sleep(2)

        def print_components(data, label):
            components = data.get("components", [])
            print(f"\n=== {label} | components 개수: {len(components)} ===")
            for i, comp in enumerate(components):
                t = comp.get("type", {})
                entity = comp.get("entity", {})
                item_list = entity.get("item_list", []) if isinstance(entity, dict) else []
                print(f"  [{i}] type.item_list={t.get('item_list') if isinstance(t, dict) else t} | item_list 개수={len(item_list)}")
                if item_list:
                    first = item_list[0].get("item", {})
                    print(f"       item 키: {list(first.keys()) if isinstance(first, dict) else first}")
            return data.get("next_token")

        # 1페이지
        response = await context.request.get(URL, headers=HEADERS)
        print(f"Status: {response.status}")
        data = await response.json()
        with open("ably_debug2_response.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        next_token = print_components(data, "1페이지")
        print(f"next_token: {next_token[:60] if next_token else None}...")

        # 2페이지
        if next_token:
            import urllib.parse as up
            url2 = f"https://api.a-bly.com/api/v2/screens/CATEGORY_DEPARTMENT/?next_token={up.quote(next_token)}"
            response2 = await context.request.get(url2, headers=HEADERS)
            data2 = await response2.json()
            with open("ably_debug2_page2.json", "w", encoding="utf-8") as f:
                json.dump(data2, f, ensure_ascii=False, indent=2)
            print_components(data2, "2페이지")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug())
