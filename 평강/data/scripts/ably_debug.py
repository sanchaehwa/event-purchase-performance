import asyncio
import json
from playwright.async_api import async_playwright

BASE_URL = "https://api.a-bly.com/api/v2/screens/CLOTHING_CATEGORY_DEPARTMENT/"

async def debug():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"
        )

        page = await context.new_page()
        print("쿠키 획득 중...")
        await page.goto("https://m.a-bly.com", wait_until="networkidle")
        await asyncio.sleep(2)

        response = await context.request.get(
            BASE_URL,
            headers={
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
        )

        print(f"HTTP Status: {response.status}")
        data = await response.json()

        # 최상위 키 확인
        print("\n[최상위 키]")
        print(list(data.keys()))

        # components 구조 확인
        components = data.get("components", [])
        print(f"\n[components 개수]: {len(components)}")

        for i, comp in enumerate(components):
            print(f"\n--- component[{i}] ---")
            print(f"  keys: {list(comp.keys())}")
            print(f"  type: {comp.get('type')}")

            entity = comp.get("entity", {})
            if not entity:
                print("  entity: 없음")
                continue

            print(f"  entity.keys: {list(entity.keys()) if isinstance(entity, dict) else type(entity)}")

            if not isinstance(entity, dict):
                continue

            item_list = entity.get("item_list", [])
            if not item_list:
                continue
            print(f"  entity.item_list 개수: {len(item_list)}")
            first = item_list[0]
            if not isinstance(first, dict):
                continue
            print(f"  item_list[0] 키: {list(first.keys())}")

            # item 키 안으로 진입
            inner = first.get("item", first)
            if isinstance(inner, dict):
                print(f"  item 키: {list(inner.keys())}")
                # 상품 필드 탐색
                goods = inner.get("goods", inner)
                if isinstance(goods, dict):
                    print(f"    goods 키: {list(goods.keys())}")
                    print(f"    name: {goods.get('name')}")
                    print(f"    price: {goods.get('price')}")
                    print(f"    brand_name: {goods.get('brand_name')}")
                    print(f"    market: {goods.get('market')}")
                    print(f"    category_name: {goods.get('category_name')}")

        # 전체 JSON을 파일로도 저장
        with open("ably_debug_response.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("\n전체 응답 → ably_debug_response.json 저장 완료")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug())
