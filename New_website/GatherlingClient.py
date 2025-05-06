# -*- coding: utf-8 -*-
"""
Created on Sun Nov 24 18:10:12 2024

@author: Francois
"""
# https://gatherling.com/
# https://github.com/PennyDreadfulMTG/gatherling
# https://github.com/Badaro/MTGODecklistCache.Tools/blob/gatherling/MTGODecklistCache.Updater.Gatherling/GatherlingSource.cs
# tO do :
# - fetch tournament data
# - fetch player data
# - fetch deck data
# - fetch round data
# - fetch match data



import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, timedelta, timezone
import os
import time
# import sys
from typing import List, Optional
# import html
from dataclasses import dataclass
# from models.Melee_model import *
from models.base_model import *
from comon_tools.tools import *


class GatherlingClient:
    @staticmethod
    def get_client():
        session = requests.Session()
        session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0',
        'Content-Type': 'application/x-www-form-urlencoded'
                })
        return session
    def get_tournaments(self, start_date, end_date):
        url = "https://gatherling.com/eventreport.php?mode=Filter+Events"
        response = self.get_client().get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        tournaments = []

        rows = soup.select("table tr")
        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 2:
                continue

            try:
                link_tag = cols[0].find('a')
                if not link_tag or 'href' not in link_tag.attrs:
                    continue  # Not a tournament row

                name = link_tag.text.strip()
                link = link_tag['href']
                full_link = "https://gatherling.com/" + link

                # Try to extract date from the event name (heuristic)
                date = None
                for token in name.split():
                    try:
                        date = datetime.strptime(token, "%m.%d").replace(year=datetime.now().year, tzinfo=timezone.utc)
                        break
                    except ValueError:
                        continue

                if not date:
                    continue  # Can't parse date, skip

                if not (start_date <= date <= end_date):
                    continue

                # Since the structure is unclear, best-effort extraction:
                host = cols[1].text.strip() if len(cols) > 1 else "Unknown"

                tournaments.append(Tournament(name, date.strftime("%Y-%m-%d"), host, full_link))

            except Exception as e:
                print(f"Error parsing row: {e}")
                continue

        return tournaments


class TournamentList:
    def get_tournament_details(self,  tournament) -> 'CacheItem':
        client = GatherlingClient()
        players = client.get_players(tournament.uri)
        
        decks = []
        standings = []
        consolidated_rounds = {}
        current_position = 1
        # player = players[0]
        # uri = tournament.uri
        for player in players:
            standings.append(player.standing)
            player_position = player.standing.rank
            player_result = f"{player_position}th Place" if player_position > 3 else f"{player_position}st Place"  # Simplified result naming

            if len(player.decks) > 0:
                deck_uri = player.decks[-1].uri
                deck = MtgMeleeClient().get_deck(deck_uri, players)
            else: 
                deck = None
            if deck is not None:
                decks.append(
                    MtgMeleeDeckInfo(
                    # in order to match badaro test put date to none,
                    # date=tournament.date, 
                    date=None,
                    deck_uri=deck.deck_uri,
                    player=player.player_name,
                    format= deck.format,
                    mainboard=deck.mainboard,
                    sideboard=deck.sideboard,
                    result =player_result,
                    rounds=deck.rounds
                )
                )

            # Consolidating rounds
            if deck is not None and deck.rounds:
                deck_round = deck.rounds[0]
                for deck_round in deck.rounds:
                    if tournament.excluded_rounds is not None and deck_round.round_name in tournament.excluded_rounds:
                        continue

                    if deck_round.round_name not in consolidated_rounds:
                        consolidated_rounds[deck_round.round_name] = {}

                    round_item_key = f"{deck_round.round_name}_{deck_round.match.player1}_{deck_round.match.player2}"
                    if round_item_key not in consolidated_rounds[deck_round.round_name]:
                        consolidated_rounds[deck_round.round_name][round_item_key] = deck_round.match        
        rounds = [Round(round_name, list(matches.values())) for round_name, matches in consolidated_rounds.items()]
        
        return CacheItem(
            tournament=tournament,
            decks=decks,
            standings=standings,
            rounds=rounds
        )

    @classmethod
    def DL_tournaments(cls,start_date: datetime, end_date: datetime = None) -> List[dict]:
        """Récupérer les tournois entre les dates start_date et end_date."""
        if start_date < datetime(2020, 1, 1, tzinfo=timezone.utc):
            return []  # Si la date de départ est avant le 1er janvier 2020, retourner une liste vide.
        if end_date is None:
            end_date = datetime.now(timezone.utc)
        result = []
        while start_date < end_date:
            current_end_date = start_date + timedelta(days=7)
            print(f"\r[MtgMelee] Downloading tournaments from {start_date.strftime('%Y-%m-%d')} to {current_end_date.strftime('%Y-%m-%d')}", end="")
            # Créer une instance du client et récupérer les tournois
            client = GatherlingClient()
            tournaments = client.get_tournaments(start_date, current_end_date)
            # analyzer = MtgMeleeAnalyzer()
            for tournament in tournaments:
                melee_tournaments = analyzer.get_scraper_tournaments(tournament)
                if melee_tournaments:
                    result.extend(melee_tournaments)
            start_date = current_end_date
        print("\r[MtgMelee] Download finished".ljust(80))
        return result