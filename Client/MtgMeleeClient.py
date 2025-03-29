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
from models.Melee_model import *
from models.base_model import *
from comon_tools.tools import *
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
                nb_of_oppo = entry['OpponentCount']

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
                        decks=player_decks if player_decks else None,
                        nb_of_oppo = nb_of_oppo
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


        deck_text = deck_soup.select_one("pre#decklist-text")
        card_list = deck_text.text.split("\r\n")

        player_link_element = deck_soup.select_one("a.text-nowrap.text-muted")

        player_url = player_link_element['href']
        player_raw = player_link_element.select_one("span.text-nowrap").text.strip()

        player_name = self.get_player_name(player_raw, player_url, players)

        date_string = deck_soup.select_one('span[data-toggle="date"]')['data-value'].strip()

        date_tournament = datetime.strptime(date_string, "%m/%d/%Y %I:%M:%S %p")

        format_div = deck_soup.select_one(".d-flex.flex-row.gap-8px .text-nowrap:last-of-type")
        format = format_div.text.strip()

        main_board = []
        side_board = []
        inside_sideboard = inside_companion = inside_commander = False
        CardNameNormalizer.initialize()
        for card in card_list:
            if card in ['MainDeck', 'Companion', 'Sideboard','Commander','']:
                if card == 'Commander':
                    inside_commander = True
                else:
                    inside_companion = card == 'Companion'
                    inside_sideboard = card == 'Sideboard'         
                if(inside_commander):
                    inside_sideboard = True
                if(card == 'Deck' and inside_commander):
                    inside_sideboard = False
                    inside_commander = False
                    inside_companion = False
            else:
                if inside_companion and not inside_commander:
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
            # in order to match badaro test put date to none,
            # date=date = date_tournament, 
            date=None,
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
                    # formats=[self.normalize_spaces(item['FormatDescription'])],
                    formats=self.normalize_spaces(item['FormatDescription']),
                    uri=MtgMeleeConstants.TOURNAMENT_PAGE.replace("{tournamentId}", str(item['ID'])),
                    decklists=item['Decklists'],
                    statut = item['StatusDescription']
                )
                result.append(tournament)
            if offset >= limit:
                break
        return result
    


# Configuration settings
class MtgMeleeAnalyzerSettings:
    MinimumPlayers = 16
    MininumPercentageOfDecks = 0.5
    ValidFormats = ["Standard", "Modern", "Pioneer", "Legacy", "Vintage", "Pauper","Commander","Premodern"] #
    PlayersLoadedForAnalysis = 25
    DecksLoadedForAnalysis = 16
    BlacklistedTerms = ["Team "]

# class FormatDetector:
#     _vintage_cards = ["Black Lotus", "Mox Emerald", "Mox Jet", "Mox Sapphire", "Mox Ruby", "Mox Pearl"]
#     _legacy_cards = ["Tundra", "Underground Sea", "Badlands", "Taiga", "Savannah", "Scrubland", "Volcanic Island", "Bayou", "Plateau", "Tropical Island"]
#     _modern_cards = ["Flooded Strand", "Polluted Delta", "Bloodstained Mire", "Wooded Foothills", "Windswept Heath", "Marsh Flats", "Scalding Tarn", "Verdant Catacombs", "Arid Mesa", "Misty Rainforest"]
#     _pioneer_cards1 = ["Hallowed Fountain", "Watery Grave", "Blood Crypt", "Stomping Ground", "Temple Garden", "Godless Shrine", "Overgrown Tomb", "Breeding Pool", "Steam Vents", "Sacred Foundry"]
#     _pioneer_cards2 = ["Nykthos, Shrine to Nyx", "Savai Triome", "Indatha Triome", "Zagoth Triome", "Ketria Triome", "Raugrin Triome", "Spara's Headquarters", "Raffine's Tower", "Xander's Lounge", "Ziatora's Proving Ground", "Jetmir's Garden"]
#     _pauper_cards = ["Lightning Bolt", "Counterspell"]
#     # manque le premodern mais je sais pas comment le traiter
#     @staticmethod
#     def detect(decks: List[dict]) -> str:
#         if any(c.card_name in FormatDetector._vintage_cards for d in decks for c in d.mainboard):
#             return "Vintage"
#         if all(c.count == 1 for d in decks for c in d.mainboard + d.sideboard) and \
#         all(len(d.sideboard) <= 3 for d in decks) and \
#         all((len(d.mainboard) + len(d.sideboard) == 100 or 
#                 (len(d.mainboard) + len(d.sideboard) == 101 and len(d.sideboard) == 3)) for d in decks):
#             return "Commander"
#         if any(c.card_name in FormatDetector._legacy_cards for d in decks for c in d.mainboard):
#             return "Legacy"
#         if any(c.card_name in FormatDetector._modern_cards for d in decks for c in d.mainboard):
#             return "Modern"
#         if (any(c.card_name in FormatDetector._pioneer_cards1 for d in decks for c in d.mainboard) and
#             any(c.card_name in FormatDetector._pioneer_cards2 for d in decks for c in d.mainboard)):
#             return "Pioneer"
#         if any(c.card_name in FormatDetector._pauper_cards for d in decks for c in d.mainboard):
#             return "Pauper"
#         return "Standard"




class MtgMeleeAnalyzer:
    def get_scraper_tournaments(self, tournament: MtgMeleeTournamentInfo) -> Optional[List[MtgMeleeTournament]]:
        is_pro_tour = (
            tournament.organizer == "Wizards of the Coast" and
            ("Pro Tour" in tournament.name or "World Championship" in tournament.name) and
            "Qualifier" not in tournament.name
        )
        # Skips tournaments with blacklisted terms
        if any(term.lower() in tournament.name.lower() for term in MtgMeleeAnalyzerSettings.BlacklistedTerms):
            return None

        # Skips tournaments with weird formats
        if not is_pro_tour and any(f not in MtgMeleeAnalyzerSettings.ValidFormats for f in tournament.formats):
            return None
        # skip not ended tournament 'In Progress'
        if tournament.statut != 'Ended' and (tournament.date.replace(tzinfo=timezone.utc) - datetime.now(timezone.utc)) < timedelta(days=5):
            return None
        
        client = MtgMeleeClient()
        players = client.get_players(tournament.uri, MtgMeleeAnalyzerSettings.PlayersLoadedForAnalysis)
        # Skips empty tournaments
        if not players:
            return None
        # Not commander multi tournament
        if any(f == 'Commander' for f in tournament.formats):
            for player in players:
                if player.nb_of_oppo >  (player.standing.wins + player.standing.losses + player.standing.draws):
                    return None
                

        

        #     #         if re.search(r'\d+(-\d+){3,}', round_result):
        #     # return "commander multi"
            
        #     deck_uris = [
        #         p.decks[0].uri for p in players if p.decks and len(p.decks) > 0
        #     ][:MtgMeleeAnalyzerSettings.DecksLoadedForAnalysis]
        #     decks = [MtgMeleeClient().get_deck(uri, players, False) for uri in deck_uris]



        # not in badaro code
        # Skips small tournaments
        # if tournament.decklists < MtgMeleeAnalyzerSettings.MinimumPlayers:
        #     return None
        # Skips small tournaments
        # if len(players) < MtgMeleeAnalyzerSettings.MinimumPlayers:
        #     return None


        # # Skips "mostly empty" tournaments
        # total_players = len(players)
        # players_with_decks = sum(1 for p in players if p.decks)
        # if players_with_decks < total_players * MtgMeleeAnalyzerSettings.MininumPercentageOfDecks:
        #     return None

        max_decks_per_player = max((len(p.decks) for p in players if p.decks), default=0)

        if is_pro_tour:
            return [self.generate_pro_tour_tournament(tournament, players)]
        else:
            if max_decks_per_player == 1:
                return [self.generate_single_format_tournament(tournament)]
            else:
                result = []
                for i in range(max_decks_per_player):
                    result.append(self.generate_multi_format_tournament(tournament, players, i, max_decks_per_player))
                return result

    def generate_single_format_tournament(self, tournament: MtgMeleeTournamentInfo) -> MtgMeleeTournament:
        ### Complètement inutile car deja filtré dans (# Skips tournaments with weird formats) et prend enormement de temps
        # , players: List[MtgMeleePlayerInfo]
        # if any(tournament.formats[0] not in MtgMeleeAnalyzerSettings.ValidFormats):   
        #     deck_uris = [p.decks[0].uri for p in players if p.decks and len(p.decks) > 0][:MtgMeleeAnalyzerSettings.DecksLoadedForAnalysis]
        #     decks = [MtgMeleeClient().get_deck(uri, players, True) for uri in deck_uris]
        #     format_detected = FormatDetector.detect(decks)
        # else:
        format_detected = tournament.formats[0]


        return MtgMeleeTournament(
            uri=tournament.uri,
            date=tournament.date,
            name=tournament.name,
            formats=format_detected,
            json_file=self.generate_file_name(tournament, format_detected, -1)
        )

    def generate_multi_format_tournament(self, tournament: MtgMeleeTournamentInfo, players: List[MtgMeleePlayerInfo], offset: int, expected_decks: int) -> MtgMeleeTournament:
        deck_uris = [
            p.decks[offset].uri for p in players if p.decks and len(p.decks) > offset
        ][:MtgMeleeAnalyzerSettings.DecksLoadedForAnalysis]

        decks = [MtgMeleeClient().get_deck(uri, players, True) for uri in deck_uris]
        formats = {deck.format for deck in decks}  # Ensemble des formats uniques

        if len(formats) > 1:
            raise ValueError(f"multiple formats need fix : {formats}")
        # format_detected = FormatDetector.detect(decks)
        return MtgMeleeTournament(
            uri=tournament.uri,
            date=tournament.date,
            name=tournament.name,
            formats=formats.pop(),
            json_file=FilenameGenerator.generate_file_name(
                tournament_id=tournament.uri.split("/")[-1],
                name=tournament.name,
                date=tournament.date,
                format=formats.pop(),
                valid_formats=MtgMeleeAnalyzerSettings.ValidFormats,
                offset=offset
            ),
            deck_offset=offset,
            expected_decks=expected_decks,
            fix_behavior="Skip"
        )

    def generate_pro_tour_tournament(self, tournament: MtgMeleeTournamentInfo, players: List[MtgMeleePlayerInfo]) -> MtgMeleeTournament:
        deck_uris = [p.decks[-1].uri for p in players if p.decks]
        decks = [MtgMeleeClient().get_deck(uri, players, True) for uri in deck_uris]

        formats = {deck.format for deck in decks}  

        if len(formats) > 1:
            raise ValueError(f"multiple formats need fix  : {formats}")
            
        format_detected = FormatDetector.detect(decks)
        return MtgMeleeTournament(
            uri=tournament.uri,
            date=tournament.date,
            name=tournament.name,
            formats=formats.pop(),
            json_file=self.generate_file_name(tournament, format_detected, -1),
            deck_offset=0,
            expected_decks=3,
            fix_behavior="UseFirst",
            excluded_rounds=["Round 1", "Round 2", "Round 3", "Round 9", "Round 10", "Round 11"]
        )

    def generate_file_name(self, tournament: MtgMeleeTournamentInfo, format: str, offset: int) -> str:
        name = tournament.name
        if format.lower() not in name.lower():
            name += f" ({format})"

        for other_format in MtgMeleeAnalyzerSettings.ValidFormats:
            if other_format.lower() != format.lower() and other_format.lower() in name.lower():
                name = name.replace(other_format, other_format[:3], 1)

        if offset >= 0:
            name += f" (Seat {offset + 1})"

        return f"{SlugGenerator.generate_slug(name.strip())}-{tournament.uri.split('/')[-1]}-{tournament.date.strftime('%Y-%m-%d')}.json"


class TournamentList:
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
            client = MtgMeleeClient()
            tournaments = client.get_tournaments(start_date, current_end_date)
            analyzer = MtgMeleeAnalyzer()
            for tournament in tournaments:
                melee_tournaments = analyzer.get_scraper_tournaments(tournament)
                if melee_tournaments:
                    result.extend(melee_tournaments)
            start_date = current_end_date
        print("\r[MtgMelee] Download finished".ljust(80))
        return result
