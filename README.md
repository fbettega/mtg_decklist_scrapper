# MTG Tournament Fetcher

## Overview
This script fetches tournament data from various Magic: The Gathering platforms, including [MTGO](https://www.mtgo.com/decklists), [Melee](https://melee.gg/Decklists) and [Topdeck](https://topdeck.gg). It stores tournament data in a structured folder format for further analysis.

## Note 
- [Manatraders](https://www.manatraders.com/tournaments/2) is not fully functional in order to recover standings. The script tries to de-anonymize the masks that replace player names, but this is not always possible (data errors, very large numbers of players in a single mask, etc.).
## Requirements

### Dependencies
Ensure you have the required dependencies installed. You can generate a `requirements.txt` file using:
```sh
pipreqs --force --ignore .venv --mode no-pin
```
Then install the dependencies:
```sh
pip install -r requirements.txt
```

#### Loging information and token api
To enable the parsers, you need to provide your API keys or login credentials in the following files:
##### Topdeck API
- Add your **API key** to the following file: "Api_token_and_login/api_topdeck.txt"

#####  MTG Melee Login
- Add your **login credentials** to this file: "Api_token_and_login/melee_login.json"
Expected format:
```json
{
  "login": "your MTG Melee email",
  "mdp": "your MTG Melee password"
}
```

### Python Version
Make sure you are using Python 3.8 or later.

## Usage
The script is executed from the command line as follows:
```sh
python fetch_tournament.py <cache_folder> <start_date> <end_date> <source> <leagues>
```

### Arguments
- `<cache_folder>`: The path to store tournament data.
- `<start_date>`: Start date in `YYYY-MM-DD` format (default: 7 days ago).
- `<end_date>`: End date in `YYYY-MM-DD` format (default: today).
- `<source>`: Source type. Options:
  - `mtgo`
  - `melee`
  - `topdeck`
  - `manatrader`
  - `all` (fetch from all sources)
- `<leagues>`: Include leagues. Options:
  - `keepleague` (default)
  - `skipleagues`

### Examples
Fetch tournaments from MTG Melee between January 1, 2025, and February 28, 2025:
```sh
python fetch_tournament.py ./MTG_decklistcache/Tournaments 2025-01-01 2025-02-28 melee keepleague
```

Fetch all tournaments in 2024:
```sh
python fetch_tournament.py ./MTG_decklistcache/Tournaments 2024-01-01 2024-12-31 all keepleague
```

## Logging
The script logs its execution to `log_scraping.txt`. Errors and progress updates will be recorded there.

## Error Handling & Retry Mechanism
If an error occurs while fetching tournament data, the script will automatically retry up to five times before failing.

## File Storage Structure
Tournaments are stored in:
```
<cache_folder>/<source>/<year>/<month>/<day>/<tournament>.json
```
Example:
```
./MTG_decklistcache/Tournaments/MTGmelee/2025/01/15/tournament_12345.json
```

## Contact
For issues or feature requests, please open a GitHub issue.

