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
import os
import sys
from typing import List, Optional

# sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from models.mtg_melee_models import (
    MtgMeleePlayerInfo,
    MtgMeleePlayerDeck,
    MtgMeleeDeckInfo,
    MtgMeleeTournamentInfo,
    MtgMeleeRoundInfo
)
from models.base_model import (
    Standing,
    DeckItem,
    RoundItem
)

from constant.MtgMeleeconstant import MtgMeleeConstants

class MtgMeleeClient:
    @staticmethod
    def get_client():
        session = requests.Session()
        session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0',
        'Content-Type': 'application/x-www-form-urlencoded'
    })
        return session

    @staticmethod
    def normalize_spaces(data):
        return re.sub(r'\s+', ' ', data).strip()

    def get_players(self, uri, max_players=None):
        
        result = []
        # je ne suis pas sur de bien comprendre pourquoi utilisé self ici sachant qu'on appel une méthode static
        # page_content = self.get_client().get(uri).text
        page_content = MtgMeleeClient.get_client().get(uri).text
        soup = BeautifulSoup(page_content, 'html.parser')

        round_nodes = soup.select('button.btn.btn-gray.round-selector[data-is-completed="True"]')

        if not round_nodes:
            return None

        round_ids = [node['data-id'] for node in round_nodes]
        
        for round_id in round_ids:
            has_data = True
            offset = 0
            # debug
            # round_id = round_ids[-1]

            round_parameters = MtgMeleeConstants.ROUND_PAGE_PARAMETERS.replace("{start}", str(offset)).replace("{roundId}", round_id) 
            round_url = MtgMeleeConstants.ROUND_PAGE 
            response = MtgMeleeClient.get_client().post(round_url, data=round_parameters)
            print("Réponse obtenue:", response.status_code)
            round_data = json.loads(response.text)
 

            # print(len(round_data['data']))
            while has_data and (max_players is None or offset < max_players):
                if len(round_data['data']) == 0 and offset == 0:
                    if len(round_ids) > 1:
                        round_ids = round_ids[:-1]
                        round_id = round_ids[-1]
                        has_data = True
                        continue
                    else:
                        break

                for entry in round_data['data']:
                    print("Entrée trouvée:", entry)
                    # entry = round_data['data'][1]
                    has_data = True
                    player_name = entry['Team']['Players'][0]['DisplayName']
                    if not player_name:
                        continue

                    player_name = self.normalize_spaces(player_name)
                    user_name = entry['Team']['Players'][0]['Username']
                    player_points = entry['Points']
                    omwp = entry['OpponentMatchWinPercentage']
                    gwp = entry['TeamGameWinPercentage']
                    ogwp = entry['OpponentGameWinPercentage']
                    player_position = entry['Rank']
                    wins = entry['MatchWins']
                    losses = entry['MatchLosses']
                    draws = entry['MatchDraws']

                    standing = Standing(
                        player=player_name,
                        rank=player_position,
                        points=player_points,
                        omwp=omwp,
                        gwp=gwp,
                        ogwp=ogwp,
                        wins=wins,
                        losses=losses,
                        draws=draws
                    )

                    player_decks = []
                    for decklist in entry['Decklists']:
                        deck_list_id = decklist['DecklistId']
                        if not deck_list_id:
                            continue
                        decklist_format = decklist['Format']
                        player_decks.append(MtgMeleePlayerDeck(
                            deck_id=deck_list_id,
                            format=decklist_format,
                            uri=f"{MtgMeleeConstants.DECK_PAGE}/{deck_list_id}"
                        ))

                    result.append(
                        MtgMeleePlayerInfo( 
                            username=user_name,
                            player_name=player_name,
                            result=f"{wins}-{losses}-{draws}",
                            standing=standing,
                            decks=player_decks if player_decks else None
                    )
                    )

                offset += 25
        return result

    def get_deck(self, uri, players, skip_round_data=False):
        deck_page_content = self.get_client().get(uri).text
        deck_soup = BeautifulSoup(deck_page_content, 'html.parser')

        copy_button = deck_soup.select_one("button.decklist-builder-copy-button.btn-sm.btn.btn-card.text-nowrap")
        
        card_list = copy_button['data-clipboard-text'].split("\r\n")

        player_url = deck_soup.select_one("span.decklist-card-title-author a")['href']
        player_raw = deck_soup.select_one("span.decklist-card-title-author a").text
        player_name = self.get_player_name(player_raw, player_url, players)

        format_div = deck_soup.select_one(".card-header.decklist-card-header")
        format = format_div.text.strip()

        main_board = []
        side_board = []
        inside_sideboard = inside_companion = False
        for card in card_list:
            if card in ['Deck', 'Companion', 'Sideboard']:
                inside_companion = card == 'Companion'
                inside_sideboard = card == 'Sideboard'
            else:
                if inside_companion:
                    continue
                count, name = card.split(" ", 1)
                count = int(count)
                name = CardNameNormalizer.normalize(name)

                if inside_sideboard:
                    side_board.append(DeckItem(card_name=name, count=count))
                else:
                    main_board.append(DeckItem(card_name=name, count=count))

        rounds = []
        if not skip_round_data:
            rounds_div = deck_soup.select_one("#tournament-path-grid-item")
            if rounds_div:
                for round_div in rounds_div.select("div div div table tbody tr"):
                    round = self.get_round(round_div, player_name, players)
                    if round:
                        rounds.append(round)

        return MtgMeleeDeckInfo(
            deck_uri=uri,
            format=format,
            mainboard=main_board,
            sideboard=side_board,
            rounds=rounds if rounds else None
        )

    def get_round(self, round_node, player_name, players):
        round_columns = round_node.find_all("td")
        if round_columns[0].text.strip() == "No results found":
            return None

        round_name = self.normalize_spaces(round_columns[0].text.strip())
        round_opponent_url = round_columns[1].find("a")['href']
        round_opponent_raw = round_columns[1].find("a").text
        round_opponent = self.get_player_name(round_opponent_raw, round_opponent_url, players)

        round_result = self.normalize_spaces(round_columns[3].text.strip())
        item = None
        if round_result.startswith(f"{player_name} won"):
            item = RoundItem(player1=player_name, player2=round_opponent, result=round_result.split(" ")[-1])
        elif round_result.startswith(f"{round_opponent} won"):
            item = RoundItem(player1=round_opponent, player2=player_name, result=round_result.split(" ")[-1])
        elif "Draw" in round_result:
            item = RoundItem(player1=player_name, player2=round_opponent, result=round_result.split(" ")[0])
        elif "bye" in round_result or "was awarded a bye" in round_result:
            item = RoundItem(player1=player_name, player2="-", result="2-0-0")
        elif round_result.startswith("won "):
            item = RoundItem(player1="-", player2=player_name, result="2-0-0")
        elif round_result.startswith(f"{player_name} forfeited"):
            item = RoundItem(player1=player_name, player2=round_opponent, result="0-2-0")
        elif round_result.startswith("Not reported") or "[FORMAT EXCEPTION]" in round_result:
            item = RoundItem(player1=player_name, player2=round_opponent, result="0-0-0")

        if item is None:
            raise ValueError(f"Cannot parse round data for player {player_name} and opponent {round_opponent}")

        if len(item.result.split("-")) == 2:
            item.result += "-0"

        return MtgMeleeRoundInfo(round_name=round_name, match=item)

    def get_player_name(self, player_name_raw, profile_url, players):
        player_id = profile_url.split("/")[-1]
        if player_id:
            player_info = next((p for p in players if p.user_name == player_id), None)
            if player_info:
                return player_info.player_name
            elif player_name_raw:
                return self.normalize_spaces(player_name_raw)
        return "-"
    
    def get_tournaments(self, start_date, end_date):
        offset = 0
        limit = -1
        result = []
        while offset < limit:
            tournament_list_parameters = MtgMeleeConstants.TOURNAMENT_LIST_PARAMETERS.replace("{offset}", str(offset)).replace("{startDate}", start_date.strftime("%Y-%m-%d")).replace("{endDate}", end_date.strftime("%Y-%m-%d"))
            tournament_list_url = MtgMeleeConstants.TOURNAMENT_LIST_PAGE

            response = self.get_client().post(tournament_list_url, data=tournament_list_parameters)
            tournament_data = json.loads(response.text)

            limit = tournament_data['recordsTotal']
            for item in tournament_data['data']:
                offset += 1
                tournament = MtgMeleeTournamentInfo(
                    id=item['ID'],
                    date=datetime.strptime(item['StartDate'], "%Y-%m-%dT%H:%M:%S%z"),
                    name=self.normalize_spaces(item['Name']),
                    organizer=self.normalize_spaces(item['OrganizationName']),
                    formats=[self.normalize_spaces(item['FormatDescription'])],
                    uri=MtgMeleeConstants.TOURNAMENT_PAGE.replace("{tournamentId}", str(item['ID'])),
                    decklists=item['Decklists']
                )
                result.append(tournament)

        return result
    

class CardNameNormalizer:
    def normalize(card_name):
        return card_name.strip()

class TournamentList:
    def get_tournaments(start_date: datetime, end_date: datetime = None) -> List[dict]:
        """Récupérer les tournois entre les dates start_date et end_date."""
        if start_date < datetime(2020, 1, 1):
            return []  # Si la date de départ est avant le 1er janvier 2020, retourner une liste vide.
        
        if end_date is None:
            end_date = datetime.utcnow()

        result = []

        while start_date < end_date:
            current_end_date = start_date + timedelta(days=7)
            print(f"\r[MtgMelee] Downloading tournaments from {start_date.strftime('%Y-%m-%d')} to {current_end_date.strftime('%Y-%m-%d')}", end="")

            # Créer une instance du client et récupérer les tournois
            client = MtgMeleeClient()
            tournaments = client.get_tournaments(start_date, current_end_date)

            # Analyser les tournois récupérés
            analyzer = MtgMeleeAnalyzer()
            for tournament in tournaments:
                melee_tournaments = analyzer.get_scraper_tournaments(tournament)
                if melee_tournaments:
                    result.extend(melee_tournaments)

            # Passer à la semaine suivante
            start_date = current_end_date

        print("\r[MtgMelee] Download finished".ljust(80))
        return result
    
class MtgMeleeTournament:
    def __init__(self, id: Optional[int], uri: str, date: datetime, organizer: str, name: str, decklists: Optional[int], formats: Optional[List[str]]):
        self.id = id
        self.uri = uri
        self.date = date
        self.organizer = organizer
        self.name = name
        self.decklists = decklists
        self.formats = formats
class RoundItem:
    def __init__(self, player1: str, player2: str, result: str):
        self.player1 = player1
        self.player2 = player2
        self.result = result

class Round:
    def __init__(self, round_name: str, matches: List[RoundItem]):
        self.round_name = round_name
        self.matches = matches

class MtgMeleeDeckInfo:
    def __init__(self, deck_uri: str, mainboard: List[str], sideboard: List[str], rounds: Optional[List[Round]] = None):
        self.deck_uri = deck_uri
        self.mainboard = mainboard
        self.sideboard = sideboard
        self.rounds = rounds or []

class MtgMeleePlayerInfo:
    def __init__(self, player_name: str, decks: Optional[List[MtgMeleeDeckInfo]] = None, standing: Optional[dict] = None):
        self.player_name = player_name
        self.decks = decks or []
        self.standing = standing or {}

class CacheItem:
    def __init__(self, tournament: str, decks: List[MtgMeleeDeckInfo], standings: List[dict], rounds: List[Round]):
        self.tournament = tournament
        self.decks = decks
        self.standings = standings
        self.rounds = rounds

class TournamentLoader:
    def get_tournament_details(tournament: dict) -> CacheItem:
        players = TournamentLoader.get_players(tournament['uri'])
        
        decks = []
        standings = []
        consolidated_rounds = {}

        current_position = 1
        for player in players:
            standings.append(player.standing)
            player_position = player.standing.get('rank', 0)
            player_result = f"{player_position}th Place" if player_position > 3 else f"{player_position}st Place"  # Simplified result naming

            deck = TournamentLoader.get_deck(player, players, tournament, current_position)
            if deck:
                decks.append(MtgMeleeDeckInfo(
                    deck_uri=deck.deck_uri,
                    mainboard=deck.mainboard,
                    sideboard=deck.sideboard,
                    rounds=deck.rounds
                ))

            # Consolidating rounds
            if deck and deck.rounds:
                for deck_round in deck.rounds:
                    if 'excluded_rounds' in tournament and deck_round.round_name in tournament['excluded_rounds']:
                        continue

                    if deck_round.round_name not in consolidated_rounds:
                        consolidated_rounds[deck_round.round_name] = {}

                    round_item_key = f"{deck_round.round_name}_{deck_round.matches[0].player1}_{deck_round.matches[0].player2}"
                    if round_item_key not in consolidated_rounds[deck_round.round_name]:
                        consolidated_rounds[deck_round.round_name][round_item_key] = deck_round.matches[0]

        print("[MtgMelee] Downloading finished")
        
        rounds = [Round(round_name, list(matches.values())) for round_name, matches in consolidated_rounds.items()]
        
        return CacheItem(
            tournament=tournament['name'],
            decks=decks,
            standings=standings,
            rounds=rounds
        )

