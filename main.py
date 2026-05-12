"""IPL player scraper using requests + BeautifulSoup.

This script:
1. Reads all IPL team player pages.
2. Fetches player profile basic details.
3. Extracts IPL batting and bowling stats.
4. Exports one row per player with the required assignment columns.
"""

import re
from pathlib import Path

import re
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup


BASE_URL = "https://www.cricbuzz.com"

IPL_TEAMS = [
    ("chennai_super_kings", 58),
    ("delhi_capitals", 61),
    ("gujarat_titans", 971),
    ("kolkata_knight_riders", 63),
    ("lucknow_super_giants", 966),
    ("mumbai_indians", 62),
    ("punjab_kings", 65),
    ("rajasthan_royals", 64),
    ("royal_challengers_bengaluru", 59),
    ("sunrisers_hyderabad", 255),
]

OUTPUT_COLUMNS = [
    "name",
    "role",
    "Batting Style",
    "Bowling Style",
    "team",
    "bat_matches",
    "bat_innings",
    "bat_runs",
    "bat_balls",
    "bat_highest",
    "bat_average",
    "bat_sr",
    "bat_not_out",
    "bat_fours",
    "bat_sixes",
    "bat_ducks",
    "bat_50s",
    "bat_100s",
    "bat_200s",
    "bat_300s",
    "bat_400s",
    "bowl_matches",
    "bowl_innings",
    "bowl_balls",
    "bowl_runs",
    "bowl_maidens",
    "bowl_wickets",
    "bowl_avg",
    "bowl_eco",
    "bowl_sr",
    "bowl_bbi",
    "bowl_bbm",
    "bowl_4w",
    "bowl_5w",
    "bowl_10w",
    "player_image_filename",
]

TEXT_COLUMNS = ["name", "role", "Batting Style", "Bowling Style", "team", "player_image_filename"]

BATTING_LABEL_MAP = {
    "matches": "bat_matches",
    "match": "bat_matches",
    "mat": "bat_matches",
    "innings": "bat_innings",
    "inns": "bat_innings",
    "runs": "bat_runs",
    "balls": "bat_balls",
    "ball": "bat_balls",
    "highest": "bat_highest",
    "hs": "bat_highest",
    "average": "bat_average",
    "avg": "bat_average",
    "sr": "bat_sr",
    "strike rate": "bat_sr",
    "strike_rate": "bat_sr",
    "not out": "bat_not_out",
    "not_out": "bat_not_out",
    "fours": "bat_fours",
    "4s": "bat_fours",
    "sixes": "bat_sixes",
    "6s": "bat_sixes",
    "ducks": "bat_ducks",
    "50": "bat_50s",
    "50s": "bat_50s",
    "100": "bat_100s",
    "100s": "bat_100s",
    "200": "bat_200s",
    "200s": "bat_200s",
    "300": "bat_300s",
    "300s": "bat_300s",
    "400": "bat_400s",
    "400s": "bat_400s",
}

BOWLING_LABEL_MAP = {
    "matches": "bowl_matches",
    "match": "bowl_matches",
    "mat": "bowl_matches",
    "innings": "bowl_innings",
    "inns": "bowl_innings",
    "balls": "bowl_balls",
    "ball": "bowl_balls",
    "runs": "bowl_runs",
    "maidens": "bowl_maidens",
    "mdns": "bowl_maidens",
    "wickets": "bowl_wickets",
    "wkts": "bowl_wickets",
    "average": "bowl_avg",
    "avg": "bowl_avg",
    "eco": "bowl_eco",
    "economy": "bowl_eco",
    "sr": "bowl_sr",
    "strike rate": "bowl_sr",
    "strike_rate": "bowl_sr",
    "best innings": "bowl_bbi",
    "best_innings": "bowl_bbi",
    "bbi": "bowl_bbi",
    "best match": "bowl_bbm",
    "best_match": "bowl_bbm",
    "bbm": "bowl_bbm",
    "4 wickets": "bowl_4w",
    "4w": "bowl_4w",
    "5 wickets": "bowl_5w",
    "5w": "bowl_5w",
    "10 wickets": "bowl_10w",
    "10w": "bowl_10w",
}


def clean_text(text):
    return re.sub(r"\s+", " ", str(text).strip().lower())


def to_kebab_case(text):
    return re.sub(r"[^a-zA-Z0-9]+", "-", str(text).strip().lower()).strip("-")


def normalize_best_figure(value):
    value = str(value or "").strip().replace(" ", "")
    if re.fullmatch(r"\d+/\d+", value):
        wickets, runs = value.split("/", maxsplit=1)
        return f"{int(wickets)}/{int(runs)}"
    return "-/-"


def get_player_name(soup):
    h1 = soup.find("h1")
    if h1:
        return h1.get_text(strip=True)
    if soup.title and soup.title.string:
        return soup.title.string.split(" Profile")[0].strip()
    return "unknown_player"


def pick_stats_table(tables, required_labels):
    required = {clean_text(label) for label in required_labels}
    for table in tables:
        labels = set()
        for row in table.find_all("tr"):
            cells = row.find_all(["th", "td"])
            if cells:
                labels.add(clean_text(cells[0].get_text(" ", strip=True)))
        if required.issubset(labels):
            return table
    return None


def extract_profile_info(soup):
    values = {"role": "", "batting style": "", "bowling style": ""}

    for container in soup.find_all("div"):
        children = container.find_all("div", recursive=False)
        if len(children) >= 2:
            label = clean_text(children[0].get_text(" ", strip=True)).rstrip(":")
            value = children[1].get_text(" ", strip=True)
            if label in values and value and not values[label]:
                values[label] = value

    for row in soup.find_all("tr"):
        cells = row.find_all(["th", "td"])
        if len(cells) >= 2:
            label = clean_text(cells[0].get_text(" ", strip=True)).rstrip(":")
            value = cells[1].get_text(" ", strip=True)
            if label in values and value:
                values[label] = value

    for tag in soup.find_all(["div", "span", "p", "li"]):
        text_value = tag.get_text(" ", strip=True)
        lower_text = clean_text(text_value)
        for label in values:
            prefix = f"{label} "
            if lower_text.startswith(prefix) and not values[label]:
                values[label] = text_value[len(prefix) :].strip()

    page_text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))
    if not values["role"]:
        match = re.search(r"\bRole\s+(.+?)\s+Batting\s+Style\b", page_text, flags=re.IGNORECASE)
        if match:
            values["role"] = match.group(1).strip()
    if not values["batting style"]:
        match = re.search(r"\bBatting\s+Style\s+(.+?)\s+Bowling\s+Style\b", page_text, flags=re.IGNORECASE)
        if match:
            values["batting style"] = match.group(1).strip()
    if not values["bowling style"]:
        match = re.search(
            r"\bBowling\s+Style\s+(.+?)(?:\s+ICC\s+Rankings\b|\s+Career\s+Information\b|\s+Teams\b)",
            page_text,
            flags=re.IGNORECASE,
        )
        if match:
            values["bowling style"] = match.group(1).strip()

    return values["role"], values["batting style"], values["bowling style"]


def extract_stats_for_format(table, label_map, target_format="ipl"):
    stats = {col: "" for col in label_map.values()}
    if table is None:
        return stats

    rows = table.find_all("tr")
    if not rows:
        return stats

    headers = [clean_text(cell.get_text(" ", strip=True)) for cell in rows[0].find_all(["th", "td"])]
    if len(headers) < 2:
        return stats

    try:
        format_index = headers.index(target_format)
    except ValueError:
        return stats

    for row in rows[1:]:
        cells = [cell.get_text(" ", strip=True) for cell in row.find_all(["th", "td"])]
        if not cells or format_index >= len(cells):
            continue
        key = label_map.get(clean_text(cells[0]))
        if key:
            stats[key] = cells[format_index]
    return stats


def extract_primary_image_url(soup, profile_url):
    player_slug = profile_url.rstrip("/").split("/")[-1].lower()
    player_slug_text = player_slug.replace("-", " ")

    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src") or img.get("data-lazy")
        alt = (img.get("alt") or "").lower()
        if not src:
            continue
        full_src = urljoin(BASE_URL, src)
        lower_src = full_src.lower()
        if player_slug in lower_src or player_slug in alt or player_slug_text in alt:
            return full_src

    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src") or img.get("data-lazy")
        if src:
            full_src = urljoin(BASE_URL, src)
            if "/i1/" in full_src.lower():
                return full_src

    og = soup.find("meta", attrs={"property": "og:image"})
    if og and og.get("content"):
        return urljoin(BASE_URL, og["content"])
    return ""


def download_player_image(image_url, team_name, player_name, session):
    if not image_url:
        return ""
    images_dir = Path("player_images")
    images_dir.mkdir(exist_ok=True)
    filename = f"{to_kebab_case(team_name)}__{to_kebab_case(player_name)}.jpg"
    file_path = images_dir / filename
    try:
        response = session.get(image_url, timeout=30)
        response.raise_for_status()
        file_path.write_bytes(response.content)
        return filename
    except Exception:
        return ""


def finalize_row(row):
    for column in OUTPUT_COLUMNS:
        row.setdefault(column, "")

    for column in TEXT_COLUMNS:
        value = str(row.get(column, "")).strip()
        row[column] = value if value else "N/A"

    for column in OUTPUT_COLUMNS:
        if column in TEXT_COLUMNS:
            continue
        value = str(row.get(column, "")).strip()
        row[column] = value if value else "0"

    row["bowl_bbi"] = normalize_best_figure(row.get("bowl_bbi"))
    row["bowl_bbm"] = normalize_best_figure(row.get("bowl_bbm"))
    return row


def collect_all_ipl_player_profiles(session):
    seen = set()
    players = []

    for team_slug, team_id in IPL_TEAMS:
        url = f"{BASE_URL}/cricket-team/{team_slug.replace('_', '-')}/{team_id}/players"
        try:
            soup = BeautifulSoup(session.get(url, timeout=30).text, "html.parser")
        except Exception:
            continue

        found = 0
        for link in soup.find_all("a"):
            href = link.get("href")
            if not href or "/profiles/" not in href:
                continue
            found += 1
            profile_url = urljoin(BASE_URL, href)
            key = (team_slug, profile_url)
            if key in seen:
                continue
            seen.add(key)
            players.append({"team_name": team_slug.replace("_", " ").title(), "profile_url": profile_url})

        if found == 0:
            print(f"Warning: no player profiles found for {team_slug} at {url}")

    return players


def scrape_player(entry, session):
    team_name = entry["team_name"]
    profile_url = entry["profile_url"]
    row = {"team": team_name}

    try:
        soup = BeautifulSoup(session.get(profile_url, timeout=30).text, "html.parser")
        tables = soup.find_all("table")
        row["name"] = get_player_name(soup)

        role, bat_style, bowl_style = extract_profile_info(soup)
        row["role"] = role
        row["Batting Style"] = bat_style
        row["Bowling Style"] = bowl_style

        image_url = extract_primary_image_url(soup, profile_url)
        row["player_image_filename"] = download_player_image(image_url, team_name, row["name"], session)

        batting_table = pick_stats_table(tables, ["matches", "innings", "runs", "sr"])
        bowling_table = pick_stats_table(tables, ["wickets", "avg", "eco"])
        row.update(extract_stats_for_format(batting_table, BATTING_LABEL_MAP))
        row.update(extract_stats_for_format(bowling_table, BOWLING_LABEL_MAP))
    except Exception:
        row["name"] = "unknown_player"

    return finalize_row(row)


def save_output(rows):
    df = pd.DataFrame(rows, columns=OUTPUT_COLUMNS).fillna("")
    df.to_csv("players.csv", index=False)
    print(f"Saved {len(df)} players to players.csv")


def main():
    session = requests.Session()
    entries = collect_all_ipl_player_profiles(session)
    print(f"Collected player profiles: {len(entries)}")
    rows = [scrape_player(entry, session) for entry in entries]
    save_output(rows)


if __name__ == "__main__":
    main()
