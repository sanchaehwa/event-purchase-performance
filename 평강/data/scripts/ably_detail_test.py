import asyncio
import json
from playwright.async_api import async_playwright

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

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=HEADERS["User-Agent"]
        )

        page = await context.new_page()
        await page.goto("https://m.a-bly.com", wait_until="networkidle")
        await asyncio.sleep(2)

        url = "https://api.a-bly.com/api/v2/goods/66912259/"
        response = await context.request.get(url, headers=HEADERS)
        print(f"Status: {response.status}")

        if response.status == 200:
            data = await response.json()
            print("최상위 키:", list(data.keys()))
            with open("ably_detail_response.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("전체 응답 → ably_detail_response.json 저장")

            # 선택 컬럼 확인
            print("\n[선택 컬럼 확인]")
            goods = data.get("goods", data)
            print("rating:", goods.get("review_average") or goods.get("rating") or goods.get("review_score"))
            print("review_count:", goods.get("review_count"))
            print("tags:", goods.get("tags") or goods.get("hashtags"))
            print("description:", str(goods.get("description") or goods.get("content", ""))[:100])
            print("sub_category:", goods.get("sub_category_name") or goods.get("sub_category"))
        else:
            text = await response.text()
            print("응답 내용:", text[:200])

        await browser.close()

if __name__ == "__main__":
    asyncio.run(test())
