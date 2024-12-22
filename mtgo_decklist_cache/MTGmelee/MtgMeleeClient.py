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
import html
from dataclasses import dataclass
from models.base_model import *
from comon_tools.tools import CardNameNormalizer
# sys.path.append(os.path.abspath(os.path.dirname(__file__)))


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
        
        has_data = True
        offset = 0
        # debug
        round_id = round_ids[-1]

        while True:
        # has_data and (max_players is None or offset < max_players):
            has_data = False
            round_parameters = MtgMeleeConstants.ROUND_PAGE_PARAMETERS.replace("{start}", str(offset)).replace("{roundId}", round_id) 
            round_url = MtgMeleeConstants.ROUND_PAGE 
            response = MtgMeleeClient.get_client().post(round_url, data=round_parameters)
            # print("Réponse obtenue:", response.status_code)
            round_data = json.loads(response.text)

            if len(round_data['data']) == 0 and offset == 0:
                if len(round_ids) > 1:
                    round_ids = round_ids[:-1]
                    round_id = round_ids[-1]
                    has_data = True
                    continue
                else:
                    break

            for entry in round_data['data']:
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
                        uri=MtgMeleeConstants.format_url(MtgMeleeConstants.DECK_PAGE, deckId=deck_list_id)
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
            # print(offset)
            if not has_data or (max_players is not None and offset >= max_players):
                break
        return result

    def get_deck(self, uri, players, skip_round_data=False):
        deck_page_content = self.get_client().get(uri).text
        deck_soup = BeautifulSoup(deck_page_content, 'html.parser')

        copy_button = deck_soup.select_one("button.decklist-builder-copy-button.btn-sm.btn.btn-card.text-nowrap")
        
        card_list = copy_button['data-clipboard-text'].split("\r\n")

        player_url = deck_soup.select_one("span.decklist-card-title-author a")['href']
        player_raw = deck_soup.select_one("span.decklist-card-title-author a").text
        player_name = self.get_player_name(player_raw, player_url, players)

        format_div = deck_soup.select_one(".card-header.decklist-card-header").find_all("div")[1].find_all("div")[2]
        format = format_div.text.strip()

        main_board = []
        side_board = []
        inside_sideboard = inside_companion = False
        CardNameNormalizer.initialize()
        for card in card_list:
            if card in ['Deck', 'Companion', 'Sideboard','']:
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
            
            rounds_div = deck_soup.select_one("div#tournament-path-grid-item")
            if rounds_div:
                # rounds_div.select("div div div table tbody tr")
                for round_div in rounds_div.select("div > div > div > table > tbody > tr")[1:]: 
                    # le [:1] est un ajout perso a tester car le selecteur python prend le tableau supérieur qui n'est pas un round par exmple dans le code debug 
                    # # Javier Dominguez
                    # # Rank:	6
                    # # Record:	0-0-0
                    # # Points:	42

                    round = self.get_round(round_div, player_name, players)
                    if round:
                        rounds.append(round)

        return MtgMeleeDeckInfo(
            deck_uri=uri,
            player=player_name,
            format=format,
            mainboard=main_board,
            sideboard=side_board,
            rounds=rounds if rounds else None
        )

    def get_round(self, round_node, player_name, players):

        round_columns = round_node.find_all("td")
        if round_columns[0].text.strip() == "No results found":
            return None
        # round_name = self.normalize_spaces(html.unescape(round_columns[0].decode_contents()))

        # opponent_link = round_columns[1].find("a")
        # round_opponent_url = opponent_link["href"] if opponent_link else None
        # round_opponent_raw = opponent_link.decode_contents() if opponent_link else None
        # round_opponent = get_player_name(round_opponent_raw, round_opponent_url, players)



        round_name = self.normalize_spaces(round_columns[0].text.strip())
        a_tag = round_columns[1].find("a")
        round_opponent_url = a_tag.get("href", None) if a_tag else None
        round_opponent_raw = a_tag.decode_contents() if a_tag else None
        round_opponent = self.get_player_name(round_opponent_raw, round_opponent_url, players) if a_tag else None

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
        elif f"{player_name} forfeited" in round_result and f"{round_opponent} forfeited" in round_result:
            item = RoundItem(player1=player_name, player2=round_opponent, result="0-0-0")
        if item is None:
            raise ValueError(f"Cannot parse round data for player {player_name} and opponent {round_opponent}")

        if len(item.result.split("-")) == 2:
            item.result += "-0"

        return MtgMeleeRoundInfo(round_name=round_name, match=item)

    def get_player_name(self, player_name_raw, profile_url, players):
        player_id = profile_url.split("/")[-1]
        # p = players[0]
        # p.username
        if player_id:
            player_info = next((p for p in players if p.username == player_id), None)
            if player_info:
                return player_info.player_name
            elif player_name_raw:
                return self.normalize_spaces(player_name_raw)
        return "-"
    
    def get_tournaments(self, start_date, end_date):
        offset = 0
        limit = -1
        result = []

        while True:
            tournament_list_parameters = MtgMeleeConstants.TOURNAMENT_LIST_PARAMETERS.replace("{offset}", str(offset)).replace("{startDate}", start_date.strftime("%Y-%m-%d")).replace("{endDate}", end_date.strftime("%Y-%m-%d"))
            tournament_list_url = MtgMeleeConstants.TOURNAMENT_LIST_PAGE
            response = self.get_client().post(tournament_list_url, data=tournament_list_parameters)
            tournament_data = json.loads(response.text)

            limit = tournament_data['recordsTotal']
            for item in tournament_data['data']:
                offset += 1
                tournament = MtgMeleeTournamentInfo(
                    tournament_id=item['ID'],
                    date=datetime.strptime(item['StartDate'], "%Y-%m-%dT%H:%M:%S"), #"%Y-%m-%dT%H:%M:%S%z"
                    name=self.normalize_spaces(item['Name']),
                    organizer=self.normalize_spaces(item['OrganizationName']),
                    formats=[self.normalize_spaces(item['FormatDescription'])],
                    uri=MtgMeleeConstants.TOURNAMENT_PAGE.replace("{tournamentId}", str(item['ID'])),
                    decklists=item['Decklists']
                )
                result.append(tournament)
            if offset >= limit:
                break
        return result
    
    # def download_deck(self,player, players, tournament, current_position):
    #     deck_uri = None
    #     print(f"\r[MtgMelee] Downloading player {player.player_name} ({current_position})", end='', flush=True)
    #     if player.decks and len(player.decks) > 0:
    #         if tournament.deck_offset is None:
    #             # Ancien comportement pour compatibilité
    #             deck_uri = player.decks[-1].uri  # Dernier deck
    #         else:
    #             if len(player.decks) >= tournament.expected_decks:
    #                 deck_uri = player.decks[tournament.deck_offset].uri
    #             else:
    #                 if tournament.fix_behavior == "UseLast":  # Équivaut à MtgMeleeMissingDeckBehavior.UseLast
    #                     deck_uri = player.decks[-1].uri
    #                 elif tournament.fix_behavior == "UseFirst":  # Équivaut à MtgMeleeMissingDeckBehavior.UseFirst
    #                     deck_uri = player.decks[0].uri
    #     if deck_uri is not None:
    #         return MtgMeleeClient().get_deck(deck_uri, players)
    #     else:
    #         return None


    def get_tournament_details(self,  tournament: MtgMeleeTournament) -> 'CacheItem':

        client = MtgMeleeClient()
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
            tournament=tournament.name,
            decks=decks,
            standings=standings,
            rounds=rounds
        )




