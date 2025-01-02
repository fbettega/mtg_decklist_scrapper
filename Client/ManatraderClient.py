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
# import os
# import sys
from typing import List, Optional
# import html
from dataclasses import dataclass
from models.base_model import *
from comon_tools.tools import *
# from models.Melee_model import *

# import requests
# import json
# from bs4 import BeautifulSoup
# from datetime import datetime
# from csv import DictReader
# from io import StringIO
# from collections import defaultdict

class TournamentLoader:
    _csv_root = "https://www.manatraders.com/tournaments/download_csv_by_month_and_year?month={month}&year={year}"
    _swiss_root = "https://www.manatraders.com/tournaments/swiss_json_by_month_and_year?month={month}&year={year}"

    @staticmethod
    def get_tournament_details(tournament):
        csv_url = TournamentLoader._csv_root.format(month=tournament['date'].month, year=tournament['date'].year)
        swiss_url = TournamentLoader._swiss_root.format(month=tournament['date'].month, year=tournament['date'].year)
        standings_url = f"{tournament['uri']}swiss"
        bracket_url = f"{tournament['uri']}finals"

        standings = TournamentLoader.parse_standings(standings_url)
        deck_uris = TournamentLoader.parse_deck_uris(tournament['uri'])
        decks = TournamentLoader.parse_decks(csv_url, standings, deck_uris)
        bracket = TournamentLoader.parse_bracket(bracket_url)
        swiss = TournamentLoader.parse_swiss(swiss_url)

        rounds = swiss + bracket
        decks = TournamentLoader.reorder_decks(decks, standings, bracket)

        return {
            "tournament": tournament,
            "decks": decks,
            "standings": standings,
            "rounds": rounds
        }

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

    @staticmethod
    def parse_decks(csv_url, standings, deck_uris):
        response = requests.get(csv_url)
        csv_data = StringIO(response.text)
        reader = DictReader(csv_data)

        player_cards = defaultdict(list)
        for row in reader:
            player_cards[row['Player'].strip()].append(row)

        result = []
        for player, cards in player_cards.items():
            player_name = next((s['player'] for s in standings if s['player'].lower() == player.lower()), player)
            deck_uri = deck_uris.get(player_name.lower())

            mainboard = [
                {"count": int(card['Count']), "card_name": card['Card']}
                for card in cards if not card['Sideboard']
            ]
            sideboard = [
                {"count": int(card['Count']), "card_name": card['Card']}
                for card in cards if card['Sideboard']
            ]

            result.append({
                "player": player_name,
                "anchor_uri": deck_uri,
                "mainboard": mainboard,
                "sideboard": sideboard
            })

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

            wins, losses, _ = map(int, columns[3].text.strip().split('/'))

            standings.append({
                "rank": rank,
                "player": player,
                "points": points,
                "omwp": omwp,
                "gwp": gwp,
                "ogwp": ogwp,
                "wins": wins,
                "losses": losses
            })

        return standings

    @staticmethod
    def parse_bracket(bracket_url):
        response = requests.get(bracket_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        brackets = []
        for bracket_node in soup.select('.tournament-brackets ul li'):
            players = [div.text for div in bracket_node.select('div:first-child')]
            wins = [int(div.text) if div.text.isdigit() else 0 for div in bracket_node.select('div:last-child')]

            if players[0] == "-":
                continue

            if wins[0] > wins[1]:
                brackets.append({"player1": players[0], "player2": players[1], "result": f"{wins[0]}-{wins[1]}-0"})
            else:
                brackets.append({"player1": players[1], "player2": players[0], "result": f"{wins[1]}-{wins[0]}-0"})

        return brackets

    @staticmethod
    def parse_swiss(swiss_url):
        response = requests.get(swiss_url)
        data = response.json()

        rounds = []
        for round_name, matches in data.items():
            round_items = [
                {"player1": match["p1"], "player2": match["p2"], "result": match["res"]}
                for match in matches
            ]
            rounds.append({"round_name": round_name, "matches": round_items})

        return rounds

    @staticmethod
    def reorder_decks(decks, standings, bracket):
        # Placeholder for custom sorting logic
        return decks


class TournamentList:
    _tournament_list_url = "https://www.manatraders.com/tournaments/2"
    _tournament_root_url = "https://www.manatraders.com"

    @staticmethod
    def get_tournaments():
        tournaments = []

        response = requests.get(TournamentList._tournament_list_url)
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

            # Skip invitationals
            if tournament_date.month == 12:
                continue

            tournament_name = f"ManaTraders Series {format_type} {month_and_year}"
            tournament_uri = urljoin(TournamentList._tournament_root_url, f"{url}/")
            json_file = f"manatraders-series-{format_type.lower()}-{month_and_year.lower().replace(' ', '-')}-{tournament_date.strftime('%Y-%m-%d')}.json"

            tournaments.append(Tournament(tournament_name, tournament_date, tournament_uri, json_file))

        return tournaments


class ManaTradersSource:
    def __init__(self):
        self.provider = "manatraders.com"

    def get_tournament_details(self, tournament):
        # Placeholder for fetching tournament details
        return None

    def get_tournaments(self, start_date, end_date=None):
        tournaments = TournamentList.get_tournaments()
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