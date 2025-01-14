# -*- coding: utf-8 -*-
"""
Created on Sun Nov 24 18:10:12 2024

@author: Francois
"""
import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, timedelta, timezone
from collections import namedtuple
# import os
import sys
import csv
import math
from typing import List,Tuple,Dict, DefaultDict,Optional
from urllib.parse import urljoin
from itertools import permutations,product,islice
# import html
from dataclasses import dataclass
from models.base_model import *
from comon_tools.tools import *
from multiprocessing import Pool, cpu_count
import numpy as np
import time
import copy
from comon_tools.mana_trader_unmask import Manatrader_fix_hidden_duplicate_name, custom_round ,truncate,update_encounters,process_single_permutation,validate_permutation

# https://www.manatraders.com/tournaments/history
class MantraderClient:
    _tournament_list_url = "https://www.manatraders.com/tournaments/2"
    _tournament_root_url = "https://www.manatraders.com"

    def get_tournaments(self):
        tournaments = []

        response = requests.get(self._tournament_list_url)
        html_content = response.text

        soup = BeautifulSoup(html_content, 'html.parser')
        tournament_list_node = soup.find("select")

        if not tournament_list_node:
            return tournaments

        for option in tournament_list_node.find_all("option"):
            date_and_format = option.text.strip()
            url = option.get("value")

            date_and_format_segments = [segment.strip() for segment in date_and_format.split("|")]
            month_and_year = date_and_format_segments[0]
            format_type = date_and_format_segments[1].capitalize()

            tournament_date = datetime.strptime(f"01 {month_and_year}", "%d %B %Y")
            tournament_date = (tournament_date.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
            tournament_date = tournament_date.replace(tzinfo=timezone.utc)
            # Skip invitationals
            if tournament_date.month == 12:
                continue

            tournament_name = f"ManaTraders Series {format_type} {month_and_year}"
            tournament_uri = urljoin(self._tournament_root_url, f"{url}/")
            json_file = f"manatraders-series-{format_type.lower()}-{month_and_year.lower().replace(' ', '-')}-{tournament_date.strftime('%Y-%m-%d')}.json"

            tournaments.append(Tournament(name=tournament_name,date= tournament_date, uri=tournament_uri, json_file=json_file))
        return tournaments


    @staticmethod
    def parse_deck_uris(root_url):
        response = requests.get(root_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        result = {}
        tables = soup.find_all('table', class_='table-tournament-rankings')
        if len(tables) < 2:
            return result

        deck_table = tables[-2]
        for row in deck_table.select('tbody tr'):
            columns = row.find_all('td')
            if len(columns) < 6:
                continue

            player_name = columns[1].text.strip().lower()
            url_link = columns[5].find('a')
            if url_link:
                result[player_name] = url_link['href']

        return result


    def parse_decks(self,csv_url, standings, deck_uris):
        response = requests.get(csv_url)
        response.raise_for_status()  # Ensure the request was successful

        # Parse CSV content
        reader = csv.DictReader(response.text.splitlines())

        player_cards = defaultdict(list)
        for row in reader:
            player_name = row['Player_Name'].strip() if row['Player_Name'].strip() else row['Player_Username'].strip()
            player_cards[player_name].append(row)
            
        result = []
        for player, cards in player_cards.items():
            # Match player names with standings, if not found, use the player name directly
            player_name = next((s.player for s in standings if s.player.lower() == player.lower()), player)
            
            # Get the corresponding deck URI from the deck_uris dictionary
            deck_uri = deck_uris.get(player_name.lower())

            # Create the mainboard and sideboard lists as DeckItem instances
            mainboard = [
                DeckItem(count=int(card['Qty']), card_name=card['Card'])
                for card in cards if card['Sideboard'] == '0'  # '0' means mainboard
            ]
            sideboard = [
                DeckItem(count=int(card['Qty']), card_name=card['Card'])
                for card in cards if card['Sideboard'] == '1'  # '1' means sideboard
            ]

            result.append(
                Deck(
                    date=None,  # You can add date logic here if applicable
                    player=player_name,
                    result="",  # Add result if necessary
                    anchor_uri=deck_uri,
                    mainboard=mainboard,
                    sideboard=sideboard
                )
                )

        return result

    @staticmethod
    def parse_standings(standings_url):
        response = requests.get(standings_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        standings_table = soup.find('table', class_='table-tournament-rankings')
        if not standings_table:
            return []

        standings = []
        for row in standings_table.select('tbody tr'):
            columns = row.find_all('td')
            rank = int(columns[0].text.strip())
            player = columns[1].text.strip()
            points = int(columns[2].text.strip())
            omwp = float(columns[5].text.strip('%')) / 100
            gwp = float(columns[6].text.strip('%')) / 100
            ogwp = float(columns[7].text.strip('%')) / 100

            nb_game ,wins, losses = map(int, columns[3].text.strip().split('/'))


            standings.append(Standing(
                    rank=rank,
                    player=player,
                    points=points,
                    wins=wins,
                    losses=losses,
                    draws= nb_game - (wins + losses),  # Si nécessaire, ajustez ce champ
                    omwp=omwp,
                    gwp=gwp,
                    ogwp=ogwp
                ))


        return standings


    def parse_bracket(self,bracket_url,standings:Standing):
        response = requests.get(bracket_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        rounds = []
        round_items = []

        for bracket_node in soup.select('.tournament-brackets ul li'):
            players = [div.text for div in bracket_node.select('div:first-child')]
            wins = [int(div.text) if div.text.isdigit() else 0 for div in bracket_node.select('div:last-child')]
            if players[1].strip() == "-":
                continue
            if players[1].strip()== players[2].strip():
                continue
            if wins[0] > wins[2]:
                round_items.append(RoundItem(players[1], players[2], f"{wins[0]}-{wins[2]}-{wins[1]}"))
            else:
                round_items.append(RoundItem(players[2], players[1], f"{wins[2]}-{wins[0]}-{wins[1]}"))
        # ici rest a définir round name
        # You can define the round name here (this could be dynamic or based on your logic)
        if len(round_items) == 7:
            # No extra rounds
            rounds.append(Round("Quarterfinals", round_items[:4]))
            rounds.append(Round("Semifinals", round_items[4:6]))
            rounds.append(Round("Finals", round_items[6:]))
        else:
            rounds.append(Round("Quarterfinals", round_items[:4]))
            rounds.append(Round("Loser Semifinals", round_items[10:12]))
            rounds.append(Round("Semifinals", round_items[4:6]))
            rounds.append(Round("Match for 7th and 8th places", round_items[15:16]))
            rounds.append(Round("Match for 5th and 6th places", round_items[12:13]))
            rounds.append(Round("Match for 3rd and 4th places", round_items[9:10]))
            rounds.append(Round("Finals", round_items[6:7]))
        bracket_rounds = [r for r in rounds if len(r.matches) > 0]
        return bracket_rounds

    def resolve_player_name(self,masked_name, standings, matched_standings, unmatched_matches):
        if masked_name is None:
            return None

        # Extraire les premiers et derniers caractères
        first_char, last_char = masked_name[0], masked_name[-1]
        # Trouver les joueurs correspondants dans standings
        matching_players = [
            standing for standing in standings
            if standing.player[0] == first_char and standing.player[-1] == last_char
            ]

        if len(matching_players) == 1:
            matched_standings.add(matching_players[0].player)  # Marquer comme apparié
            return matching_players[0].player
        else:
            # Ajouter à la liste des noms masqués non appariés
            unmatched_matches.append(masked_name)
            return masked_name



    def parse_swiss(self,swiss_url, standings,bracket):
        # Récupérer les données des matchs
        response = requests.get(swiss_url)
        data = response.json()
        # Variables pour suivre les joueurs appariés et non appariés
        matched_standings = set()
        unmatched_matches = []
        rounds = []
        for round_name, matches in data.items():
            round_items = [
                RoundItem(
                    self.resolve_player_name(match["p1"], standings, matched_standings, unmatched_matches),
                    self.resolve_player_name(match["p2"], standings, matched_standings, unmatched_matches),
                    match["res"],
                    id=f"{round_name}.{i}" 
                )
                for i, match in enumerate(matches)
            ]
            rounds.append(Round(round_name, round_items))

        if unmatched_matches:
            rounds = Manatrader_fix_hidden_duplicate_name().Find_name_form_player_stats(rounds,standings,bracket)


        return rounds
    


class TournamentList:
    _csv_root = "https://www.manatraders.com/tournaments/download_csv_by_month_and_year?month={month}&year={year}"
    _swiss_root = "https://www.manatraders.com/tournaments/swiss_json_by_month_and_year?month={month}&year={year}"


    def get_tournament_details(self,tournament):
        client = MantraderClient()
        csv_url = self._csv_root.format(month=tournament.date.month, year=tournament.date.year)
        swiss_url = self._swiss_root.format(month=tournament.date.month, year=tournament.date.year)
        standings_url = f"{tournament.uri}swiss"
        bracket_url = f"{tournament.uri}finals"
        standings = client.parse_standings(standings_url)

        deck_uris = client.parse_deck_uris(tournament.uri)
        decks = client.parse_decks(csv_url, standings, deck_uris)
        bracket = client.parse_bracket(bracket_url,standings)
        swiss = client.parse_swiss(swiss_url,standings,bracket)
        if swiss is None:
            return None
        else:
            rounds = swiss + bracket
        decks = OrderNormalizer.reorder_decks(decks, standings, bracket,True)
        # ATTENTION tu dois penser a vérifier les bye dans les calcules
        return CacheItem(
            tournament=tournament,
            decks=decks,
            standings=standings,
            rounds=rounds
        )

    

    @classmethod
    def DL_tournaments(cls,start_date: datetime, end_date: datetime = None) -> List[dict]:
        client = MantraderClient()
        tournaments = client.get_tournaments()
        filtered_tournaments = [t for t in tournaments if t.date >= start_date]
        if end_date:
            filtered_tournaments = [t for t in filtered_tournaments if t.date <= end_date]
        return filtered_tournaments
    
@dataclass
class ManaTradersCsvRecord:
    count: int  # Correspond à la propriété Count
    card: str   # Correspond à la propriété Card
    sideboard: bool  # Correspond à la propriété Sideboard
    player: str  # Correspond à la propriété Player


