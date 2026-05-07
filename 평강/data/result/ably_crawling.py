import asyncio
import base64
import json
import urllib.parse
import pandas as pd
from playwright.async_api import async_playwright

CATEGORY_URL    = "https://api.a-bly.com/api/v2/screens/CATEGORY_DEPARTMENT/"
SUB_CATEGORY_URL = "https://api.a-bly.com/api/v2/screens/SUB_CATEGORY_DEPARTMENT/"
TARGET_COUNT    = 10000
SUB_CAT_LIMIT   = 500   # 서브카테고리당 최대 고유 수집 건수
OUTPUT_FILE     = "ably_products.csv"

# 메인 카테고리별 초기 next_token
CATEGORIES = {
    "아우터":    "eyJsIjogIkRlcGFydG1lbnRDYXRlZ29yeVJlYWx0aW1lUmFua0dlbmVyYXRvciIsICJwIjogeyJkZXBhcnRtZW50X3R5cGUiOiAiQ0FURUdPUlkiLCAiY2F0ZWdvcnlfc25vIjogN30sICJkIjogIkNBVEVHT1JZIiwgInByZXZpb3VzX3NjcmVlbl9uYW1lIjogIkNMT1RISU5HX0NBVEVHT1JZX0RFUEFSVE1FTlQiLCAiY2F0ZWdvcnlfc25vIjogN30=",
    "상의":      "eyJsIjogIkRlcGFydG1lbnRDYXRlZ29yeVJlYWx0aW1lUmFua0dlbmVyYXRvciIsICJwIjogeyJkZXBhcnRtZW50X3R5cGUiOiAiQ0FURUdPUlkiLCAiY2F0ZWdvcnlfc25vIjogOH0sICJkIjogIkNBVEVHT1JZIiwgInByZXZpb3VzX3NjcmVlbl9uYW1lIjogIkNMT1RISU5HX0NBVEVHT1JZX0RFUEFSVE1FTlQiLCAiY2F0ZWdvcnlfc25vIjogOH0=",
    "팬츠":      "eyJsIjogIkRlcGFydG1lbnRDYXRlZ29yeVJlYWx0aW1lUmFua0dlbmVyYXRvciIsICJwIjogeyJkZXBhcnRtZW50X3R5cGUiOiAiQ0FURUdPUlkiLCAiY2F0ZWdvcnlfc25vIjogMTc0fSwgImQiOiAiQ0FURUdPUlkiLCAicHJldmlvdXNfc2NyZWVuX25hbWUiOiAiQ0xPVEhJTkdfQ0FURUdPUllfREVQQVJUTUVOVCIsICJjYXRlZ29yeV9zbm8iOiAxNzR9",
    "원피스/세트": "eyJsIjogIkRlcGFydG1lbnRDYXRlZ29yeVJlYWx0aW1lUmFua0dlbmVyYXRvciIsICJwIjogeyJkZXBhcnRtZW50X3R5cGUiOiAiQ0FURUdPUlkiLCAiY2F0ZWdvcnlfc25vIjogMTB9LCAiZCI6ICJDQVRFR09SWSIsICJwcmV2aW91c19zY3JlZW5fbmFtZSI6ICJDTE9USElOR19DQVRFR09SWV9ERVBBUlRNRU5UIiwgImNhdGVnb3J5X3NubyI6IDEwfQ==",
    "스커트":    "eyJsIjogIkRlcGFydG1lbnRDYXRlZ29yeVJlYWx0aW1lUmFua0dlbmVyYXRvciIsICJwIjogeyJkZXBhcnRtZW50X3R5cGUiOiAiQ0FURUdPUlkiLCAiY2F0ZWdvcnlfc25vIjogMjAzfSwgImQiOiAiQ0FURUdPUlkiLCAicHJldmlvdXNfc2NyZWVuX25hbWUiOiAiQ0xPVEhJTkdfQ0FURUdPUllfREVQQVJUTUVOVCIsICJjYXRlZ29yeV9zbm8iOiAyMDN9",
    "언더웨어":  "eyJsIjogIkRlcGFydG1lbnRDYXRlZ29yeVJlYWx0aW1lUmFua0dlbmVyYXRvciIsICJwIjogeyJkZXBhcnRtZW50X3R5cGUiOiAiQ0FURUdPUlkiLCAiY2F0ZWdvcnlfc25vIjogMTY5fSwgImQiOiAiQ0FURUdPUlkiLCAicHJldmlvdXNfc2NyZWVuX25hbWUiOiAiQ0xPVEhJTkdfQ0FURUdPUllfREVQQVJUTUVOVCIsICJjYXRlZ29yeV9zbm8iOiAxNjl9",
    "트레이닝":  "eyJsIjogIkRlcGFydG1lbnRDYXRlZ29yeVJlYWx0aW1lUmFua0dlbmVyYXRvciIsICJwIjogeyJkZXBhcnRtZW50X3R5cGUiOiAiQ0FURUdPUlkiLCAiY2F0ZWdvcnlfc25vIjogNTE3fSwgImQiOiAiQ0FURUdPUlkiLCAicHJldmlvdXNfc2NyZWVuX25hbWUiOiAiQ0xPVEhJTkdfQ0FURUdPUllfREVQQVJUTUVOVCIsICJjYXRlZ29yeV9zbm8iOiA1MTd9",
}

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
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


def extract_products(data):
    products = []
    for component in data.get("components", []):
        comp_type = component.get("type", {})
        if not isinstance(comp_type, dict):
            continue
        if comp_type.get("item_list") not in ("TWO_COL_GOODS_LIST", "GOODS_CAROUSEL", "TWO_COL_CARD_LIST"):
            continue
        for entry in component.get("entity", {}).get("item_list", []):
            product = (entry.get("item_entity") or {}).get("item") or entry.get("item", {})
            if not isinstance(product, dict):
                continue

            name = product.get("name")
            brand = product.get("market_name")
            category = product.get("category_name")
            price = product.get("price")
            if not name or not brand or not category or not price:
                continue

            image = product.get("image")
            if isinstance(image, dict):
                image_url = image.get("url") or image.get("image_url")
            elif isinstance(image, str):
                image_url = image
            else:
                image_url = None

            products.append({
                "product_name": name.strip(),
                "brand": brand.strip(),
                "category": category,
                "sub_category": None,
                "price": int(str(price).replace(",", "").replace("원", "")),
                "discount_rate": product.get("discount_rate"),
                "rating": None,
                "review_count": None,
                "tags": None,
                "description": None,
                "image_url": image_url,
                "source": "에이블리",
                "source_url": f"https://m.a-bly.com/goods/{product.get('sno', '')}",
            })
    return products


def get_sub_categories(data):
    """CATEGORY_DEPARTMENT 응답에서 서브카테고리 목록 추출"""
    sub_cats = []
    for component in data.get("components", []):
        comp_type = component.get("type", {})
        if not isinstance(comp_type, dict):
            continue
        if comp_type.get("item_list") != "FIVE_COL_ICON_LIST":
            continue
        for entry in component.get("entity", {}).get("item_list", []):
            item = entry.get("item", {})
            name = item.get("name")
            deeplink = item.get("deeplink", "")
            if "SUB_CATEGORY_DEPARTMENT" in deeplink and "next_token=" in deeplink:
                token = deeplink.split("next_token=")[1].split("&")[0]
                token = urllib.parse.unquote(token)
                sub_cats.append((name, token))
    return sub_cats


async def crawl_pages(context, label, base_url, init_token, unique_results, seen_keys, limit):
    """공통 페이지네이션 크롤러"""
    next_token = init_token
    page_count = 0
    sub_count = 0
    seen_tokens = set()
    zero_streak = 0

    while sub_count < limit and len(unique_results) < TARGET_COUNT:
        if next_token in seen_tokens:
            print(f"  [{label}] 토큰 순환 감지 → 종료")
            break
        seen_tokens.add(next_token)

        url = f"{base_url}?next_token={urllib.parse.quote(next_token)}"
        try:
            response = await context.request.get(url, headers=HEADERS)
            if response.status != 200:
                print(f"  [{label}] 에러: {response.status}")
                break

            data = await response.json()
            products = extract_products(data)
            page_count += 1

            new_count = 0
            for p_item in products:
                key = (p_item["product_name"], p_item["brand"])
                if key not in seen_keys:
                    seen_keys.add(key)
                    unique_results.append(p_item)
                    new_count += 1
                    sub_count += 1

            zero_streak = 0 if new_count > 0 else zero_streak + 1
            print(f"  [{label}] {page_count}p | 신규: {new_count} | 서브누적: {sub_count} | 전체: {len(unique_results)}")

            if zero_streak >= 10:
                print(f"  [{label}] 신규 0건 10페이지 연속 → 종료")
                break
            if sub_count >= limit:
                print(f"  [{label}] 제한({limit}건) 도달 → 종료")
                break

            next_token = data.get("next_token")
            if not next_token:
                print(f"  [{label}] 마지막 페이지")
                break

            await asyncio.sleep(1.5)

        except Exception as e:
            print(f"  [{label}] 오류: {e}")
            break


async def crawl():
    # 기존 CSV 로드
    try:
        existing_df = pd.read_csv(OUTPUT_FILE, encoding="utf-8-sig")
        existing_results = existing_df.to_dict("records")
        print(f"기존 데이터 로드: {len(existing_results)}건")
    except FileNotFoundError:
        existing_results = []
        print("기존 파일 없음, 새로 시작")

    seen_keys = {(r["product_name"], r["brand"]) for r in existing_results}
    unique_results = list(existing_results)
    print(f"추가 수집 목표: {TARGET_COUNT - len(unique_results)}건 (고유 기준)")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=HEADERS["User-Agent"])

        page = await context.new_page()
        print("쿠키 획득 중...")
        await page.goto("https://m.a-bly.com", wait_until="networkidle")
        await asyncio.sleep(2)

        # 1단계: 메인 카테고리 → 서브카테고리 크롤링
        for cat_name, cat_token in CATEGORIES.items():
            if len(unique_results) >= TARGET_COUNT:
                break

            print(f"\n{'='*50}")
            print(f"[{cat_name}] 서브카테고리 탐색 중...")

            # 메인 카테고리 첫 페이지로 서브카테고리 목록 조회
            try:
                resp = await context.request.get(
                    f"{CATEGORY_URL}?next_token={urllib.parse.quote(cat_token)}",
                    headers=HEADERS
                )
                cat_data = await resp.json()
                sub_cats = get_sub_categories(cat_data)
            except Exception as e:
                print(f"  서브카테고리 조회 실패: {e}")
                sub_cats = []

            if sub_cats:
                print(f"  서브카테고리 {len(sub_cats)}개: {[s[0] for s in sub_cats]}")
                for sub_name, sub_token in sub_cats:
                    if len(unique_results) >= TARGET_COUNT:
                        break
                    print(f"\n  [{cat_name} > {sub_name}] 크롤링 시작")
                    await crawl_pages(
                        context,
                        f"{cat_name}>{sub_name}",
                        SUB_CATEGORY_URL,
                        sub_token,
                        unique_results,
                        seen_keys,
                        SUB_CAT_LIMIT,
                    )
            else:
                # 서브카테고리 없으면 메인 카테고리 직접 크롤링
                print(f"  서브카테고리 없음 → 메인 카테고리 직접 크롤링")
                await crawl_pages(
                    context,
                    cat_name,
                    CATEGORY_URL,
                    cat_token,
                    unique_results,
                    seen_keys,
                    2000,
                )

        print(f"\n[1단계 완료] 고유 수집: {len(unique_results)}건")

        # 2단계: 선택 컬럼 상세 API 수집
        print(f"\n[2단계] 상세 정보 수집 시작...")
        semaphore = asyncio.Semaphore(5)

        async def fetch_detail(item, idx):
            sno = item["source_url"].split("/")[-1]
            url = f"https://api.a-bly.com/api/v2/goods/{sno}/"
            async with semaphore:
                try:
                    resp = await context.request.get(url, headers=HEADERS)
                    if resp.status == 200:
                        d = await resp.json()
                        goods = d.get("goods", {})
                        review = d.get("review", {})
                        hash_tags = goods.get("hash_tags") or []
                        item["tags"] = ",".join(hash_tags) if hash_tags else None
                        item["review_count"] = review.get("count")
                        item["rating"] = review.get("positive_percent")
                except Exception:
                    pass
            if (idx + 1) % 200 == 0:
                print(f"  상세 수집: {idx + 1}/{len(unique_results)}건")

        await asyncio.gather(*[fetch_detail(item, i) for i, item in enumerate(unique_results)])
        print(f"[2단계 완료]")

        await browser.close()

    df = pd.DataFrame(unique_results).head(TARGET_COUNT)
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print(f"\n완료: {len(df)}건 저장 → {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(crawl())
