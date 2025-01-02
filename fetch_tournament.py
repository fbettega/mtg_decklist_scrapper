# -*- coding: utf-8 -*-
"""
Created on Sun Nov 24 18:54:58 2024

@author: Francois
"""
import os
import json
from datetime import datetime, timedelta, timezone
from typing import Optional
from dateutil import parser
import argparse
import sys
import re
import Client.MtgMeleeClient as MTGmelee
import Client.MTGOclient as MTGO
import Client.TopDeckClient as TopDeck


# python fetch_tournament.py ./MTG_decklistcache/Tournaments 2024-01-01 2024-12-31 all keepleague

# python fetch_tournament.py ./MTG_decklistcache/Tournaments 2024-11-01 2024-11-07 mtgo keepleague
# python fetch_tournament.py ./MTG_decklistcache/Tournaments 2024-01-01 2024-12-01 all keepleague
# python fetch_tournament.py ./MTG_decklistcache/Tournaments 2024-11-01 2024-11-07 topdeck keepleague

# python fetch_tournament.py ./MTG_decklistcache/Tournaments 2024-01-01 2024-12-31 topdeck keepleague

# python fetch_tournament.py ./MTG_decklistcache/Tournaments 2024-01-01 2024-12-31 melee keepleague
#fait
# python fetch_tournament.py ./MTG_decklistcache/Tournaments 2024-01-01 2024-01-31 all keepleague
# python fetch_tournament.py ./MTG_decklistcache/Tournaments 2024-02-01 2024-02-29 all keepleague

# python fetch_tournament.py ./MTG_decklistcache/Tournaments 2024-03-01 2024-03-31 all keepleague
# python fetch_tournament.py ./MTG_decklistcache/Tournaments 2024-04-01 2024-04-30 all keepleague
# python fetch_tournament.py ./MTG_decklistcache/Tournaments 2024-05-01 2024-05-31 all keepleague
# python fetch_tournament.py ./MTG_decklistcache/Tournaments 2024-06-01 2024-06-30 melee keepleague
# python fetch_tournament.py ./MTG_decklistcache/Tournaments 2024-07-01 2024-07-31 all keepleague
# python fetch_tournament.py ./MTG_decklistcache/Tournaments 2024-08-01 2024-08-31 all keepleague
# python fetch_tournament.py ./MTG_decklistcache/Tournaments 2024-09-01 2024-09-30 all keepleague
# python fetch_tournament.py ./MTG_decklistcache/Tournaments 2024-10-01 2024-10-31 all keepleague
# python fetch_tournament.py ./MTG_decklistcache/Tournaments 2024-11-01 2024-11-30 all keepleague
# python fetch_tournament.py ./MTG_decklistcache/Tournaments 2024-12-01 2024-12-31 all keepleague

# python fetch_tournament.py ./MTG_decklistcache/Tournaments 2024-11-01 2024-11-07 mtgo keepleague


# python fetch_tournament.py ./MTG_decklistcache/Tournaments 2024-12-01 2024-12-12 topdeck keepleague

# Configure logging to file and console
def configure_logging(log_file_path):
    class Logger:
        def __init__(self, log_file):
            self.terminal = sys.stdout
            self.log_file = open(log_file, "a", encoding="utf-8")

        def write(self, message):
            timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S] ")
            self.terminal.write(message)
            self.log_file.write(timestamp + message)
            self.log_file.flush()  # Ensure immediate writing to the file

        def flush(self):
            self.terminal.flush()
            self.log_file.flush()

    sys.stdout = Logger(log_file_path)
    sys.stderr = sys.stdout  # Redirect stderr to stdout for error logging

def sanitize_filename(filename):
    """
    Replace invalid characters in the filename with underscores.
    """
    return re.sub(r'[<>:"/\\|?*]', '', filename)

def clean_temp_files(cache_folder: str):
    """Delete all temporary files starting with 'Temp' and ending with '.tmp' in the cache folder."""
    for root, _, files in os.walk(cache_folder):
        for file in files:
            if file.startswith("Temp") and file.endswith(".tmp"):
                temp_file_path = os.path.join(root, file)
                try:
                    os.remove(temp_file_path)
                    print(f"Removed temporary file: {temp_file_path}")
                except Exception as e:
                    print(f"Error removing temporary file {temp_file_path}: {e}")

# Update folder function
def update_folder(cache_root_folder: str, source, source_name:str,start_date: datetime, end_date: Optional[datetime]):
    
    cache_folder = os.path.join(cache_root_folder, source_name)  # Provider is the class name
    # Clean up any leftover temp files
    clean_temp_files(cache_folder)
    print(f"Downloading tournament list for {source_name}")
    tournaments = source.TournamentList.DL_tournaments(start_date, end_date)
    tournaments.sort(key=lambda t: t.date)
    
    for tournament in tournaments:
        target_folder = os.path.join(cache_folder, str(tournament.date.year), f"{tournament.date.month:02d}", f"{tournament.date.day:02d}")

        os.makedirs(target_folder, exist_ok=True)
        
        sanitize_json_file = sanitize_filename(tournament.json_file)
        target_file = os.path.join(target_folder, sanitize_json_file)
        # if os.path.exists(target_file) and not tournament.force_redownload:
        if os.path.exists(target_file):
            continue
        print(f"- Downloading tournament {sanitize_json_file}")
        details = run_with_retry(lambda: source.TournamentList().get_tournament_details(tournament), 3)
        if not details:
            print(f"-- Tournament has no data, skipping")
            if not os.listdir(target_folder):  # If folder is empty, remove it
                os.rmdir(target_folder)
            continue
        if not details.decks:
            print(f"-- Tournament has no decks, skipping")
            if not os.listdir(target_folder):
                os.rmdir(target_folder)
            continue
        if all(len(deck.mainboard) == 0 for deck in details.decks):
            print(f"-- Tournament has only empty decks, skipping")
            if not os.listdir(target_folder):
                os.rmdir(target_folder)
            continue
        temp_file = os.path.join(cache_folder, f"Temp{sanitize_json_file}.tmp")  # Temp file in cache_folder
        temp_file = sanitize_filename(temp_file)
        with open(temp_file, 'w', encoding="utf-8") as f:
                json.dump(details.to_dict(), f, ensure_ascii=False, indent=2)
        os.replace(temp_file, target_file) 

# Retry function
def run_with_retry(action, max_attempts: int):
    retry_count = 1
    while True:
        try:
            return action()
        except Exception as ex:
            if retry_count < max_attempts:
                print(f"-- Error '{str(ex).strip('.')}' during call, retrying ({retry_count + 1}/{max_attempts})")
                retry_count += 1
            else:
                raise

# Main function equivalent
def main():
    configure_logging("log_scraping.txt")  # Log file nam
    # Configure argparse
    arg_parser = argparse.ArgumentParser(
        description="MTGO Decklist Cache Updater"
    )
    arg_parser.add_argument(
        "cache_folder",
        type=str,
        help="Path to the cache folder."
    )
    arg_parser.add_argument(
        "start_date",
        type=str,
        nargs="?",
        help="Start date in YYYY-MM-DD format. Defaults to 7 days ago.",
        default=(datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
    )
    arg_parser.add_argument(
        "end_date",
        type=str,
        nargs="?",
        help="End date in YYYY-MM-DD format. Defaults to today.",
        default=datetime.now().strftime("%Y-%m-%d"),
    )
    arg_parser.add_argument(
        "source",
        type=str,
        nargs="?",
        help="Source type: 'mtgo', 'melee', 'topdeck', or 'all'. Defaults to 'all'.",
        default="all",
    )
    arg_parser.add_argument(
        "leagues",
        type=str,
        nargs="?",
        help="Include leagues? Use 'keepleague' or 'skipleagues'. Defaults to 'keepleague'.",
        default="keepleague",
    )
    args = arg_parser.parse_args()

    # Convert arguments to variables
    cache_folder = os.path.abspath(args.cache_folder)
    start_date = parser.parse(args.start_date).astimezone(timezone.utc)
    end_date = parser.parse(args.end_date).astimezone(timezone.utc)
    use_mtgo = args.source.lower() in ["mtgo", "all"]
    use_mtg_melee = args.source.lower() in ["melee", "all"]
    use_topdeck = args.source.lower() in ["topdeck", "all"]
    include_leagues = args.leagues.lower() != "skipleagues"

    print(f"Cache folder: {cache_folder}")
    print(f"Start date: {start_date}")
    print(f"End date: {end_date}")
    print(f"Using MTGO: {use_mtgo}")
    print(f"Using MTG Melee: {use_mtg_melee}")
    print(f"Using Topdeck: {use_topdeck}")
    print(f"Including Leagues: {include_leagues}")

    # Update folders based on source
    if use_mtgo:
        print("Updating MTGO...")
        update_folder(cache_folder, MTGO, "MTGO", start_date, end_date)

    if use_mtg_melee:
        print("Updating MTG Melee...")
        update_folder(cache_folder, MTGmelee, "MTGmelee", start_date, end_date)

    if use_topdeck:
        print("Updating Topdeck...")
        update_folder(cache_folder, TopDeck, "Topdeck", start_date, end_date)

if __name__ == "__main__":
    main()