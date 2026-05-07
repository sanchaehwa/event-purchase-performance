import asyncio
import json
import urllib.parse
from playwright.async_api import async_playwright

TOKEN = "eyJsIjogIkRlcGFydG1lbnRDYXRlZ29yeVJlYWx0aW1lUmFua0dlbmVyYXRvciIsICJwIjogeyJkZXBhcnRtZW50X3R5cGUiOiAiQ0FURUdPUlkiLCAiY2F0ZWdvcnlfc25vIjogMjk2fSwgImQiOiAiQ0FURUdPUlkiLCAicHJldmlvdXNfc2NyZWVuX25hbWUiOiAiQ0FURUdPUllfREVQQVJUTUVOVCIsICJjYXRlZ29yeV9zbm8iOiAyOTZ9"
URL = f"https://api.a-bly.com/api/v2/screens/SUB_CATEGORY_DEPARTMENT/?next_token={urllib.parse.quote(TOKEN)}&filter_sub_category_sno=497"

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

        response = await context.request.get(URL, headers=HEADERS)
        print(f"Status: {response.status}")
        data = await response.json()

        with open("ably_debug3_response.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"title: {data.get('title')}")
        print(f"next_token: {'있음' if data.get('next_token') else '없음'}")
        components = data.get("components", [])
        print(f"components: {len(components)}개")
        for i, comp in enumerate(components):
            t = comp.get("type", {})
            entity = comp.get("entity", {})
            item_list = entity.get("item_list", []) if isinstance(entity, dict) else []
            print(f"  [{i}] {t.get('item_list') if isinstance(t, dict) else t} | {len(item_list)}건", end="")
            if item_list:
                first = item_list[0]
                item = (first.get("item_entity") or {}).get("item") or first.get("item", {})
                if isinstance(item, dict) and item.get("name"):
                    print(f" | 샘플: {item.get('name')[:30]}", end="")
            print()

        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug())
