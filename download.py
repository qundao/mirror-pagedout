import argparse
import logging
import re
import time
from pathlib import Path

import feedparser
import requests

README_FILE = "README.md"
RSS_URL = "https://pagedout.institute/rss.xml"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"
}


def parse_rss(save_dir):
    logging.info("Read rss")
    d = feedparser.parse(RSS_URL)
    entries = d["entries"]
    logging.info(f"Rss feeds = {len(entries)}")
    if len(entries) == 0:
        logging.warning("No entries")
        return

    if not Path(save_dir).exists():
        Path(save_dir).mkdir(parents=True)

    data = []
    for entry in entries:
        title = entry["title"]
        link = entry["link"]
        # summary = entry['summary']
        published = entry["published"]
        if pub_date := re.findall(r"(\w+, \d+ \w+ \d{4}) \d+:\d+:\d+ \+\d+", published):
            pub_date = pub_date[0]
        else:
            pub_date = published

        logging.info(f"Process = {title}, {pub_date}")
        data.append(f"*{pub_date}*, {title} [link]({link})")
        if download_pdf(link, save_dir):
            time.sleep(5)

    update_readme(data)


def download_pdf(link, save_dir, chunk_size=1024):
    file = link.split("/")[-1]
    if not file.endswith(".pdf"):
        logging.info("Ignore non-pdf file")
        return False

    save_file = Path(save_dir, file)
    if save_file.exists():
        logging.info("Ignore existed file")
        return False

    try:
        res = requests.get(link, headers=HEADERS, stream=True)
        res.raise_for_status()
        with open(save_file, "wb") as f:
            for chunk in res.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
        logging.info(f"Save {file}")
    except requests.exceptions.RequestException as e:
        logging.warning(f"Error: {e}")
    return True


def update_readme(data):
    logging.info(f"Update {README_FILE}")
    with open(README_FILE, "r", encoding="utf-8") as f:
        text = f.read()

    new_content = "\n- ".join([""] + data).strip()
    text = re.sub(
        r"(<!-- list-start -->\n).*(<!-- list-end -->)",
        rf"\1{new_content}\n\2",
        text,
        flags=re.DOTALL | re.MULTILINE,
    )
    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(text)


if __name__ == "__main__":
    fmt = "%(asctime)s %(filename)s %(levelname)s %(message)s"
    logging.basicConfig(level=logging.INFO, format=fmt)

    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--out", type=str, default="pdf")
    args = parser.parse_args()

    parse_rss(args.out)
