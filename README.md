# IPL Player Data Dashboard

This project scrapes IPL player information from Cricbuzz, stores the fetched data in a CSV file, downloads player images, and displays the results in an Tableau workbook, grouped by IPL teams.

## Project Files

- `main.py` - Scrapes IPL team/player pages, extracts profile details and IPL batting/bowling stats, downloads player images, and writes the final dataset.
- `players.csv` - Generated player dataset used by the frontend.
- `player_images/` - Downloaded player images referenced by `players.csv`.
- `IPL Dashboard.twb` - Tableau workbook for exploring and visualizing the IPL player dataset.
- `~Book2__3340.twbr` - Tableau workbook recovery/backup file (can be ignored unless the main .twb file is corrupted).
- `requirements.txt` - Python dependencies required by the scraper.
- `prompt.txt` - Assignment prompt/context for player performance classification.

## Features

- Team-wise grouping for all IPL players.
- Local player image rendering from `player_images/`.
- Search across player name, team, role, batting style, and bowling style.
- Filters for team and player role.
- Sorting by impact score, runs, wickets, strike rate, economy, or name.
- Team summary metrics including total runs, wickets, top run scorer, and top wicket taker.

## Setup

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

## Generate Fresh Data

Run the scraper:

```bash
python main.py
```

This creates or updates:

- `players.csv`
- files inside `player_images/`

## Tableau Dashboard

To view the Tableau version of this project:

1. Open `IPL Dashboard.twb` in Tableau Desktop.
2. If prompted to locate the data source, point Tableau to `players.csv` in this project folder.
3. Refresh the data source after running `main.py` to load the latest scraped data.

## Data Columns

The CSV includes player identity, team, role, batting style, bowling style, IPL batting stats, IPL bowling stats, and the local image filename.

Important columns include:

- `name`
- `team`
- `role`
- `Batting Style`
- `Bowling Style`
- `bat_runs`
- `bat_average`
- `bat_sr`
- `bowl_wickets`
- `bowl_avg`
- `bowl_eco`
- `player_image_filename`

## Notes

- No build step is required.
