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
import MTGmelee.MtgMeleeClient as MTGmelee

# Update folder function
def update_folder(cache_root_folder: str, source, start_date: datetime, end_date: Optional[datetime]):
    cache_folder = os.path.join(cache_root_folder, source.__class__.__name__)  # Provider is the class name
    print(f"Downloading tournament list for {source.__class__.__name__}")
    tournaments = source.TournamentList.get_tournaments(start_date, end_date)
    tournaments.sort(key=lambda t: t.date)
    
    for tournament in tournaments:
        target_folder = os.path.join(cache_folder, str(tournament.date.year), f"{tournament.date.month:02d}", f"{tournament.date.day:02d}")
        os.makedirs(target_folder, exist_ok=True)
        
        target_file = os.path.join(target_folder, tournament.json_file)
        if os.path.exists(target_file) and not tournament.force_redownload:
            continue

        print(f"- Downloading tournament {tournament.json_file}")
        
        details = run_with_retry(lambda: source.get_tournament_details(tournament), 3)
        if not details:
            print(f"-- Tournament has no data, skipping")
            if not os.listdir(target_folder):  # If folder is empty, remove it
                os.rmdir(target_folder)
            continue
        if not details.get('decks'):
            print(f"-- Tournament has no decks, skipping")
            if not os.listdir(target_folder):
                os.rmdir(target_folder)
            continue
        if all(len(deck['mainboard']) == 0 for deck in details['decks']):
            print(f"-- Tournament has only empty decks, skipping")
            if not os.listdir(target_folder):
                os.rmdir(target_folder)
            continue

        with open(target_file, 'w') as f:
            json.dump(details, f, indent=4)

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
    args = ["./cache_folder", "2024-11-01", "2024-11-24", "all", "keepleague"]
    
    if len(args) < 1:
        print("Usage: MTGODecklistCache.Updater.App CACHE_FOLDER [START_DATE] [END_DATE] [SOURCE]")
        return

    cache_folder = os.path.abspath(args[0])
    
    start_date = (datetime.now() - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
    if len(args) > 1:
        start_date = parser.parse(args[1]).astimezone(timezone.utc)

    end_date = None
    if len(args) > 2:
        end_date = parser.parse(args[2]).astimezone(timezone.utc)

    use_mtgo = len(args) < 4 or args[3].lower() in ["mtgo", "all"]
    use_mtg_melee = len(args) < 4 or args[3].lower() in ["melee", "all"]
    use_topdeck = len(args) < 4 or args[3].lower() in ["topdeck", "all"]

    include_leagues = len(args) < 5 or args[4].lower() != "skipleagues"

    # if use_mtgo:
        # You would need to replace this with the actual implementation of MtgoSource
        # update_folder(cache_folder, ITournamentSource(), start_date, end_date)
    
    if use_mtg_melee:
        # You would need to replace this with the actual implementation of MtgMeleeSource
        update_folder(cache_folder, MTGmelee, start_date, end_date)
    
    # if use_topdeck:
        # You would need to replace this with the actual implementation of TopdeckSource
        # update_folder(cache_folder, ITournamentSource(), start_date, end_date)

if __name__ == "__main__":
    main()
    



