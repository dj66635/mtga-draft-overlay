import os
import shutil
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import time

BASE = "https://www.mtggoldfish.com"
META_URL = BASE + "/metagame/standard/full"
TOP_X = 30  # number of top archetypes to download


# Archive old decks
def archive_old_decks():
    os.makedirs("_old", exist_ok=True)
    for f in os.listdir("."):
        if f.endswith(".dck"):
            shutil.move(f, os.path.join("_old", f))


def get_top_archetypes():
    r = requests.get(META_URL)
    soup = BeautifulSoup(r.text, "html.parser")
    links = []

    for a in soup.select(".archetype-tile-title a"):
        url = BASE + a["href"].split("#")[0]
        if url not in links:
            links.append(url)
        if len(links) >= TOP_X:
            break

    return links


def get_archetype_name(deck_page_url):
    r = requests.get(deck_page_url)
    soup = BeautifulSoup(r.text, "html.parser")

    h1 = soup.find("h1")
    if not h1:
        return "deck"

    # remove <span> inside h1 (author)
    for span in h1.find_all("span"):
        span.extract()

    name = h1.get_text(strip=True)
    return name


def get_download_link(deck_page_url):
    r = requests.get(deck_page_url)
    soup = BeautifulSoup(r.text, "html.parser")

    # select the download button link
    link = soup.select_one("a.deck-tools-btn[href*='/deck/download/']")

    if not link:
        return None

    return BASE + link["href"]


def download_deck(download_url):
    r = requests.get(download_url)
    return r.text

def sanitized(name):
    return re.sub(r"[^a-zA-Z0-9_-]", "_", name)


def process_deck(deck_text, deck_name):
    deck_text = deck_text.replace("\r\n", "\n")
    deck_text = re.sub(r'\n{2,}', '\n\nSideboard\n\n', deck_text)
    deck_text = f"Name {deck_name}\n\n{deck_text}"

    lines = deck_text.split("\n")
    new_lines = []

    for line in lines:
        # if "Superior Spider-Man" in line:
        #    line = line.replace("Superior Spider-Man", "Kavaero, Mind-Bitten")

        if "/" in line:
            line = line.replace("/", " // ")

        new_lines.append(line)
    
    return "\n".join(new_lines)


def save_deck(deck_text, deck_name):
    date = datetime.now().strftime("%y%m%d")
    filename = f"{date}_{sanitized(deck_name)}.dck"

    # prepend Name line and Sideboard label
    final_deck = process_deck(deck_text, deck_name)

    with open(filename, "w", encoding="utf-8") as f:
        f.write(final_deck)

    print("Saved:", filename)


# -------------------------------
# Main
# -------------------------------
def main():
    archive_old_decks()

    archetypes = get_top_archetypes()
    for archetype in archetypes:
        print("Processing archetype:", archetype)

        deck_name = get_archetype_name(archetype)
        download_url = get_download_link(archetype)
        if not download_url:
            print("  No deck found.")
            continue

        deck_text = download_deck(download_url)
        save_deck(deck_text, deck_name)

        time.sleep(1)  # polite delay


if __name__ == "__main__":
    main()