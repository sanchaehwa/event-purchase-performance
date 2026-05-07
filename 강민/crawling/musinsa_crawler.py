import argparse
import csv
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from datetime import date
from html import unescape
from html.parser import HTMLParser
from pathlib import Path


DEFAULT_USER_AGENT = "ChatGPT-User"
ROBOTS_URL = "https://www.musinsa.com/robots.txt"
NULL_TEXT = "None"
ROBOTS_CACHE = {}
FIELDS = [
    "product_name",
    "brand",
    "category",
    "sub_category",
    "price",
    "discount_rate",
    "rating",
    "review_count",
    "tags",
    "description",
    "image_url",
    "source",
    "source_url",
]


class ProductScriptParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self._capture = False
        self._script_type = ""
        self.scripts = []

    def handle_starttag(self, tag, attrs):
        if tag != "script":
            return
        attr_map = {name.lower(): value or "" for name, value in attrs}
        script_type = attr_map.get("type", "")
        script_id = attr_map.get("id", "")
        if script_type == "application/ld+json" or script_id in {"pdp-data", "__NEXT_DATA__"}:
            self._capture = True
            self._script_type = script_type or script_id

    def handle_data(self, data):
        if self._capture:
            self.scripts.append((self._script_type, data.strip()))

    def handle_endtag(self, tag):
        if tag == "script":
            self._capture = False
            self._script_type = ""


def can_fetch(url, user_agent):
    parser = ROBOTS_CACHE.get(user_agent)
    if parser is None:
        parser = urllib.robotparser.RobotFileParser()
        parser.set_url(ROBOTS_URL)
        try:
            parser.read()
        except urllib.error.URLError:
            return True
        ROBOTS_CACHE[user_agent] = parser
    return parser.can_fetch(user_agent, url)


def fetch_html(url, user_agent, timeout):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def as_list(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def normalize_int(value):
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    digits = re.sub(r"[^0-9]", "", str(value))
    return int(digits) if digits else None


def normalize_float(value):
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    cleaned = re.sub(r"[^0-9.]", "", str(value))
    return float(cleaned) if cleaned else None


def normalize_image(value):
    image = as_list(value)[0] if as_list(value) else ""
    if isinstance(image, dict):
        image = image.get("imageUrl") or image.get("url") or ""
    if isinstance(image, str) and image.startswith("//"):
        return f"https:{image}"
    if isinstance(image, str) and image.startswith("/"):
        return f"https://image.msscdn.net{image}"
    return image or None


def category_parts(value):
    if isinstance(value, dict):
        category = value.get("categoryDepth1Name") or value.get("categoryDepth1Title") or ""
        sub_category = value.get("categoryDepth2Name") or value.get("categoryDepth2Title") or ""
        return category or None, sub_category or None
    if isinstance(value, str) and ">" in value:
        parts = [part.strip() for part in value.split(">")]
        return parts[0] or None, parts[1] if len(parts) > 1 and parts[1] else None
    return value or None, None


def extract_assignment_json(script_body, variable_name):
    marker = f"{variable_name} = "
    start = script_body.find(marker)
    if start < 0:
        return None
    brace_start = script_body.find("{", start + len(marker))
    if brace_start < 0:
        return None

    depth = 0
    in_string = False
    escape = False
    for index in range(brace_start, len(script_body)):
        char = script_body[index]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return json.loads(script_body[brace_start : index + 1])
    return None


def product_from_mss_state(state, source_url):
    if state.get("isOutOfStock"):
        return {"_skip_reason": "sold_out", "source_url": source_url}
    price = state.get("goodsPrice") if isinstance(state.get("goodsPrice"), dict) else {}
    brand_info = state.get("brandInfo") if isinstance(state.get("brandInfo"), dict) else {}
    category, sub_category = category_parts(state.get("category") or state.get("baseCategoryFullPath"))
    review = state.get("goodsReview") if isinstance(state.get("goodsReview"), dict) else {}
    labels = state.get("labels") if isinstance(state.get("labels"), list) else []
    seo = state.get("seo") if isinstance(state.get("seo"), dict) else {}
    return {
        "product_name": state.get("goodsNm") or state.get("name") or None,
        "brand": brand_info.get("brandName") or state.get("brand") or None,
        "category": category,
        "sub_category": sub_category,
        "price": normalize_int(price.get("salePrice") or price.get("couponPrice") or price.get("normalPrice")),
        "discount_rate": normalize_float(price.get("discountRate") or price.get("totalDiscount")),
        "rating": normalize_float(review.get("satisfactionScore")),
        "review_count": normalize_int(review.get("totalCount")),
        "tags": "|".join(label.get("name", "") for label in labels if isinstance(label, dict) and label.get("name")) or None,
        "description": seo.get("metaDescription") or seo.get("faceBookMetaDescription") or None,
        "image_url": normalize_image(state.get("thumbnailImageUrl") or state.get("goodsImages")),
        "source": "musinsa",
        "source_url": source_url,
    }


def product_from_json_ld(data, source_url):
    for item in as_list(data):
        if not isinstance(item, dict):
            continue
        if item.get("@graph"):
            product = product_from_json_ld(item["@graph"], source_url)
            if product:
                return product
        item_types = item.get("@type") if isinstance(item.get("@type"), list) else [item.get("@type")]
        if "Product" not in item_types:
            continue
        offers = item.get("offers") if isinstance(item.get("offers"), dict) else {}
        brand = item.get("brand") if isinstance(item.get("brand"), dict) else {}
        aggregate = item.get("aggregateRating") if isinstance(item.get("aggregateRating"), dict) else {}
        category, sub_category = category_parts(item.get("category") or "")
        return {
            "product_name": item.get("name") or None,
            "brand": brand.get("name") or item.get("brand") or None,
            "category": category,
            "sub_category": sub_category,
            "price": normalize_int(offers.get("price")),
            "discount_rate": None,
            "rating": normalize_float(aggregate.get("ratingValue")),
            "review_count": normalize_int(aggregate.get("reviewCount")),
            "tags": None,
            "description": item.get("description") or None,
            "image_url": normalize_image(item.get("image")),
            "source": "musinsa",
            "source_url": source_url,
        }
    return None


def parse_product(html, source_url):
    parser = ProductScriptParser()
    parser.feed(html)
    fallback = None
    for script_type, body in parser.scripts:
        if not body:
            continue
        try:
            if script_type == "pdp-data":
                state = extract_assignment_json(body, "window.__MSS__.product.state")
                if state:
                    return product_from_mss_state(state, source_url)
            data = json.loads(unescape(body))
            product = product_from_json_ld(data, source_url)
            if product:
                fallback = product
        except json.JSONDecodeError:
            continue
    return fallback


def read_urls(args):
    urls = list(args.url or [])
    if args.url_file:
        urls.extend(
            line.strip()
            for line in Path(args.url_file).read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        )
    return urls


def read_existing_products(output_path):
    path = Path(output_path)
    if not path.exists():
        return [], set()
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    seen_urls = {row.get("source_url", "") for row in rows if row.get("source_url")}
    return rows, seen_urls


def read_existing_lines(path):
    file_path = Path(path)
    if not file_path.exists():
        return []
    return [
        line.strip()
        for line in file_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_csv(rows, output_path, fields):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(
            {
                field: NULL_TEXT if row.get(field) is None else row.get(field, NULL_TEXT)
                for field in fields
            }
            for row in rows
        )


def write_lines(lines, output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def write_report(report_path, stats, output_path, log_dir):
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        "\n".join(
            [
                "# Musinsa Crawling Result",
                "",
                f"- Run date: {date.today().isoformat()}",
                "- Target count standard: 10000 products per member",
                f"- Target URLs: {stats['total']}",
                f"- Success products: {stats['success']}",
                f"- Sold out skipped: {stats['sold_out']}",
                f"- Parse failed: {stats['parse_failed']}",
                f"- HTTP 429: {stats['rate_limited']}",
                f"- Other failed: {stats['failed']}",
                "- Output CSV: `data/raw/musinsa_products_raw.csv`",
                "- Failed URL log: `data/logs/failed_urls.txt`",
                "- Rate limit log: `data/logs/rate_limited_urls.txt`",
                "- Parse failed log: `data/logs/parse_failed_urls.txt`",
                "- Sold out log: `data/logs/sold_out_urls.txt`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def main():
    parser = argparse.ArgumentParser(description="Crawl Musinsa product pages into CSV.")
    parser.add_argument("--url", action="append")
    parser.add_argument("--url-file", default=str(Path(__file__).resolve().parents[1] / "data/raw/musinsa_product_urls.txt"))
    parser.add_argument("--output", default=str(Path(__file__).resolve().parents[1] / "data/raw/musinsa_products_raw.csv"))
    parser.add_argument("--log-dir", default=str(Path(__file__).resolve().parents[1] / "data/logs"))
    parser.add_argument("--report", default=str(Path(__file__).resolve().parents[1] / "data/reports/crawling_result.md"))
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--retry-delay", type=float, default=5.0)
    parser.add_argument("--retries", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--target-count", type=int, default=10000)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--checkpoint-every", type=int, default=100)
    parser.add_argument("--max-requests", type=int)
    parser.add_argument("--user-agent", default=DEFAULT_USER_AGENT)
    parser.add_argument("--ignore-robots", action="store_true")
    args = parser.parse_args()

    urls = read_urls(args)
    if not urls:
        print("No URLs provided.", file=sys.stderr)
        return 2

    rows, seen_urls = read_existing_products(args.output) if args.resume else ([], set())
    log_dir = Path(args.log_dir)
    failed_urls = read_existing_lines(log_dir / "failed_urls.txt") if args.resume else []
    rate_limited_urls = read_existing_lines(log_dir / "rate_limited_urls.txt") if args.resume else []
    parse_failed_urls = read_existing_lines(log_dir / "parse_failed_urls.txt") if args.resume else []
    sold_out_urls = read_existing_lines(log_dir / "sold_out_urls.txt") if args.resume else []
    skipped_urls = set(seen_urls)
    skipped_urls.update(line.split("\t", 1)[0] for line in failed_urls)
    skipped_urls.update(rate_limited_urls)
    skipped_urls.update(parse_failed_urls)
    skipped_urls.update(sold_out_urls)
    stats = {"total": len(urls), "success": 0, "sold_out": 0, "parse_failed": 0, "rate_limited": 0, "failed": 0}

    processed_requests = 0
    for index, url in enumerate(urls, start=1):
        if len(rows) >= args.target_count:
            break
        if args.max_requests is not None and processed_requests >= args.max_requests:
            break
        if url in skipped_urls:
            continue
        processed_requests += 1
        parsed = urllib.parse.urlparse(url)
        if parsed.netloc and not parsed.netloc.endswith("musinsa.com"):
            failed_urls.append(f"{url}\tnon-musinsa-url")
            stats["failed"] += 1
            continue
        if not args.ignore_robots and not can_fetch(url, args.user_agent):
            failed_urls.append(f"{url}\tblocked-by-robots")
            stats["failed"] += 1
            continue

        html = None
        last_error = ""
        for attempt in range(args.retries + 1):
            try:
                html = fetch_html(url, args.user_agent, args.timeout)
                break
            except urllib.error.HTTPError as error:
                last_error = f"HTTP {error.code}"
                if error.code == 429:
                    if attempt < args.retries:
                        time.sleep(args.retry_delay)
                    continue
                break
            except urllib.error.URLError as error:
                last_error = str(error)
                break

        if html is None:
            if "429" in last_error:
                rate_limited_urls.append(url)
                stats["rate_limited"] += 1
            else:
                failed_urls.append(f"{url}\t{last_error}")
                stats["failed"] += 1
            print(f"[{index}/{len(urls)}] failed {url}: {last_error}")
        else:
            product = parse_product(html, url)
            if product and product.get("_skip_reason") == "sold_out":
                sold_out_urls.append(url)
                stats["sold_out"] += 1
                print(f"[{index}/{len(urls)}] sold out {url}")
            elif product and product.get("product_name") and product.get("brand") and product.get("category") and product.get("price") is not None and product.get("source_url"):
                rows.append({field: product.get(field) for field in FIELDS})
                seen_urls.add(url)
                skipped_urls.add(url)
                stats["success"] += 1
                print(f"[{index}/{len(urls)}] success {url}")
            else:
                parse_failed_urls.append(url)
                stats["parse_failed"] += 1
                print(f"[{index}/{len(urls)}] parse failed {url}")
        if index < len(urls):
            time.sleep(args.delay)
        if args.checkpoint_every > 0 and processed_requests % args.checkpoint_every == 0:
            write_csv(rows, Path(args.output), FIELDS)
            write_lines(failed_urls, log_dir / "failed_urls.txt")
            write_lines(rate_limited_urls, log_dir / "rate_limited_urls.txt")
            write_lines(parse_failed_urls, log_dir / "parse_failed_urls.txt")
            write_lines(sold_out_urls, log_dir / "sold_out_urls.txt")

    write_csv(rows, Path(args.output), FIELDS)
    write_lines(failed_urls, log_dir / "failed_urls.txt")
    write_lines(rate_limited_urls, log_dir / "rate_limited_urls.txt")
    write_lines(parse_failed_urls, log_dir / "parse_failed_urls.txt")
    write_lines(sold_out_urls, log_dir / "sold_out_urls.txt")
    write_report(Path(args.report), stats, Path(args.output), log_dir)
    print(f"Saved {len(rows)} products to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
