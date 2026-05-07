import argparse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path


DEFAULT_SITEMAPS = [
    f"https://www.musinsa.com/static/sitemap/sitemap-goods-{index}.xml"
    for index in range(1, 31)
]
DEFAULT_USER_AGENT = "ChatGPT-User"
NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def fetch_text(url, user_agent, timeout):
    request = urllib.request.Request(url, headers={"User-Agent": user_agent})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def collect_product_urls(sitemap_urls, limit, user_agent, timeout):
    urls = []
    seen = set()
    for sitemap_url in sitemap_urls:
        root = ET.fromstring(fetch_text(sitemap_url, user_agent, timeout))
        for loc in root.findall(".//sm:loc", NS):
            url = (loc.text or "").strip()
            if "/products/" in url and url not in seen:
                urls.append(url)
                seen.add(url)
            if len(urls) >= limit:
                break
        if len(urls) >= limit:
            break
    return urls


def main():
    parser = argparse.ArgumentParser(description="Collect Musinsa product URLs from sitemap.")
    parser.add_argument("--sitemap", action="append", help="Sitemap URL. Can be passed multiple times.")
    parser.add_argument("--limit", type=int, default=10000)
    parser.add_argument("--output", default=str(Path(__file__).resolve().parents[1] / "data/raw/musinsa_product_urls.txt"))
    parser.add_argument("--user-agent", default=DEFAULT_USER_AGENT)
    parser.add_argument("--timeout", type=int, default=20)
    args = parser.parse_args()

    urls = collect_product_urls(args.sitemap or DEFAULT_SITEMAPS, args.limit, args.user_agent, args.timeout)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(urls) + "\n", encoding="utf-8")
    print(f"Saved {len(urls)} URLs to {output_path}")


if __name__ == "__main__":
    main()
