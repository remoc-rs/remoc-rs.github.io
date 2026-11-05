#!/usr/bin/env python3
"""Submit the published sitemap to IndexNow."""

import argparse
import json
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlsplit


HOST = "remoc.rs"
SITE = f"https://{HOST}"
KEY = "feca9b2c077e4f8484876b8d9e3d8e41"
KEY_URL = f"{SITE}/{KEY}.txt"
SITEMAP_URL = f"{SITE}/sitemap.xml"
ENDPOINT = "https://api.indexnow.org/indexnow"


def fetch(url):
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read()


def sitemap_urls(data):
    root = ET.fromstring(data)
    if root.tag != "{http://www.sitemaps.org/schemas/sitemap/0.9}urlset":
        raise ValueError("The published sitemap is not a sitemap URL set")
    urls = []
    for element in root.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url/{http://www.sitemaps.org/schemas/sitemap/0.9}loc"):
        url = (element.text or "").strip()
        parts = urlsplit(url)
        if parts.scheme != "https" or parts.netloc != HOST or parts.fragment:
            raise ValueError(f"Invalid sitemap URL for {HOST}: {url!r}")
        if url in urls:
            raise ValueError(f"Duplicate sitemap URL: {url}")
        urls.append(url)
    if not urls or len(urls) > 10_000:
        raise ValueError("The sitemap must contain between 1 and 10,000 URLs")
    return urls


def submit(urls):
    payload = json.dumps({"host": HOST, "key": KEY, "keyLocation": KEY_URL, "urlList": urls}).encode()
    request = urllib.request.Request(
        ENDPOINT, data=payload, headers={"Content-Type": "application/json; charset=utf-8"}
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        if response.status not in (200, 202):
            raise ValueError(f"IndexNow returned unexpected HTTP status {response.status}")
        return response.status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="Print published sitemap URLs without submitting")
    args = parser.parse_args()

    try:
        urls = sitemap_urls(fetch(SITEMAP_URL))
        if args.list:
            print("\n".join(urls))
            return 0

        key_file = Path(__file__).resolve().parent.parent / f"{KEY}.txt"
        if key_file.read_text(encoding="utf-8").strip() != KEY:
            raise ValueError(f"Local IndexNow key in {key_file} does not match")
        if fetch(KEY_URL).decode("utf-8").strip() != KEY:
            raise ValueError(f"Published IndexNow key at {KEY_URL} does not match")
        status = submit(urls)
        print(f"IndexNow returned HTTP {status} for {len(urls)} URLs.")
        if status == 202:
            print("The URLs were received; key validation is pending.")
        else:
            print("The URLs were received; indexing is not guaranteed.")
        return 0
    except (OSError, UnicodeError, ET.ParseError, ValueError, urllib.error.URLError) as exc:
        print(f"IndexNow: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
