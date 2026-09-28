"""Scrape the first 100 books (pages 1-5) from books.toscrape.com into books.csv.

Columns: title, price (float), rating (1-5 int), in_stock (true/false), url

Usage:
    pip install requests beautifulsoup4
    python scrape_books.py
"""

import csv
import re
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://books.toscrape.com/catalogue/page-{}.html"
PAGES = range(1, 6)  # pages 1-5, 20 books each = 100 books
OUTPUT = "books.csv"

RATING_WORDS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


def parse_price(text):
    """'£51.77' -> 51.77"""
    match = re.search(r"\d+(?:\.\d+)?", text)
    if not match:
        raise ValueError(f"Could not parse price from {text!r}")
    return float(match.group())


def parse_rating(tag):
    """<p class="star-rating Three"> -> 3"""
    for cls in tag.get("class", []):
        if cls in RATING_WORDS:
            return RATING_WORDS[cls]
    raise ValueError(f"Could not parse rating from classes {tag.get('class')}")


def parse_page(html, page_url):
    soup = BeautifulSoup(html, "html.parser")
    books = []
    for pod in soup.select("article.product_pod"):
        link = pod.select_one("h3 a")
        availability = pod.select_one("p.availability").get_text(strip=True)
        books.append({
            "title": link["title"],  # full title (link text is truncated)
            "price": parse_price(pod.select_one("p.price_color").get_text()),
            "rating": parse_rating(pod.select_one("p.star-rating")),
            "in_stock": "true" if "in stock" in availability.lower() else "false",
            "url": urljoin(page_url, link["href"]),
        })
    return books


def scrape():
    session = requests.Session()
    session.headers["User-Agent"] = "Mozilla/5.0 (books scraper)"
    all_books = []
    for page in PAGES:
        url = BASE_URL.format(page)
        resp = session.get(url, timeout=30)
        resp.raise_for_status()
        # Pass raw bytes so BeautifulSoup uses the page's UTF-8 meta charset
        # (requests would otherwise guess ISO-8859-1 and mangle '£').
        books = parse_page(resp.content, url)
        print(f"Page {page}: {len(books)} books")
        all_books.extend(books)
        time.sleep(0.5)  # be polite
    return all_books[:100]


def write_csv(books, path=OUTPUT):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["title", "price", "rating", "in_stock", "url"]
        )
        writer.writeheader()
        writer.writerows(books)


if __name__ == "__main__":
    books = scrape()
    write_csv(books)
    print(f"Saved {len(books)} books to {OUTPUT}")
