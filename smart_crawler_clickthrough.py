import json
import time
from urllib.parse import urlparse, urljoin

from playwright.sync_api import sync_playwright

visited_urls = set()
results = []

def is_same_domain(base, target):
    return urlparse(base).netloc == urlparse(target).netloc

def normalize_url(url):
    return url.split("#")[0].rstrip("/")

def crawl_site(playwright, start_url):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    to_visit = [start_url]

    while to_visit:
        current_url = normalize_url(to_visit.pop(0))
        if current_url in visited_urls:
            continue

        try:
            print(f"[+] Visiting: {current_url}")
            page.goto(current_url, timeout=100000, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)
            # page.wait_for_selector("#app", timeout=5000)

            # Save rendered HTML
            html = page.content()
            results.append({
                "url": current_url,
                "html": html
            })
            visited_urls.add(current_url)

            # Extract all visible <a> links
            anchors = page.eval_on_selector_all(
                "a[href]", "els => els.map(a => a.href)"
            )

            for link in anchors:
                norm_link = normalize_url(link)
                if is_same_domain(start_url, norm_link) and norm_link not in visited_urls and norm_link not in to_visit:
                    to_visit.append(norm_link)

            time.sleep(1)  # Polite delay

        except Exception as e:
            print(f"[!] Error visiting {current_url}: {e}")
            continue

    browser.close()

if __name__ == "__main__":
    start_url = input("Enter website URL (e.g., https://www.betpawa.com): ").strip()

    with sync_playwright() as playwright:
        crawl_site(playwright, start_url)

    with open("crawled_pages.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n[✔] Done. Crawled {len(results)} pages. Saved to 'crawled_pages.json'")
