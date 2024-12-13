# -*- coding: utf-8 -*-
"""
Created on Sun Nov 24 18:23:21 2024

@author: Francois
"""
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from typing import List, Optional

class MtgMeleeTournament:
    def __init__(self, id: Optional[int], uri: str, date: datetime, organizer: str, name: str, decklists: Optional[int], formats: Optional[List[str]]):
        self.id = id
        self.uri = uri
        self.date = date
        self.organizer = organizer
        self.name = name
        self.decklists = decklists
        self.formats = formats

class TournamentList:
    @staticmethod
    def get_tournaments(start_date: datetime, end_date: Optional[datetime] = None) -> List[MtgMeleeTournament]:
        if start_date < datetime(2020, 1, 1, 0, 0, 0, tzinfo=None):
            return []
        
        if end_date is None:
            end_date = datetime.utcnow() + timedelta(days=1)

        result = []
        current_start_date = start_date
        
        while current_start_date < end_date:
            current_end_date = current_start_date + timedelta(days=7)
            
            print(f"\r[MtgMelee] Downloading tournaments from {current_start_date.strftime('%Y-%m-%d')} to {current_end_date.strftime('%Y-%m-%d')}".ljust(80))

            tournaments = MtgMeleeClient().get_tournaments(current_start_date, current_end_date)

            for tournament in tournaments:
                melee_tournaments = MtgMeleeAnalyzer().get_scraper_tournaments(tournament)
                if melee_tournaments is not None:
                    result.extend(melee_tournaments)

            current_start_date = current_start_date + timedelta(days=7)

        print("\r[MtgMelee] Download finished".ljust(80))

        return result

# Usage example
# start_date = datetime(2023, 1, 1)
# tournaments = TournamentList.get_tournaments(start_date)

# for tournament in tournaments:
#     print(f"Tournament: {tournament.name}, Date: {tournament.date}")

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
    @staticmethod
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

    @staticmethod
    def get_deck(player: MtgMeleePlayerInfo, players: List[MtgMeleePlayerInfo], tournament: dict, current_position: int) -> Optional[MtgMeleeDeckInfo]:
        print(f"[MtgMelee] Downloading player {player.player_name} ({current_position})")

        deck_uri = None
        if player.decks:
            if 'deck_offset' not in tournament:
                deck_uri = player.decks[-1].deck_uri  # Use the last deck for compatibility
            else:
                if len(player.decks) >= tournament['expected_decks']:
                    deck_uri = player.decks[tournament['deck_offset']].deck_uri
                else:
                    # Implement missing behavior (similar to the C# version)
                    if tournament['fix_behavior'] == 'UseLast':
                        deck_uri = player.decks[-1].deck_uri
                    elif tournament['fix_behavior'] == 'UseFirst':
                        deck_uri = player.decks[0].deck_uri
        
        if deck_uri:
            return TournamentLoader.get_deck_info(deck_uri)
        return None

    @staticmethod
    def get_deck_info(deck_uri: str) -> MtgMeleeDeckInfo:
        # Fetch deck info from the deck_uri using an API or other methods
        # For now, returning dummy data
        return MtgMeleeDeckInfo(deck_uri, ['Card1', 'Card2'], ['SideboardCard1'])

    @staticmethod
    def get_players(tournament_uri: str) -> List[MtgMeleePlayerInfo]:
        # Fetch players from the API
        # Dummy data
        return [
            MtgMeleePlayerInfo('Player1', [MtgMeleeDeckInfo('uri1', ['CardA'], ['SideA'])], {'rank': 1}),
            MtgMeleePlayerInfo('Player2', [MtgMeleeDeckInfo('uri2', ['CardB'], ['SideB'])], {'rank': 2})
        ]

# Usage
tournament_info = {
    'uri': 'http://example.com/tournament',
    'name': 'Tournament 1',
    'excluded_rounds': ['Round 1'],
    'expected_decks': 8,
    'deck_offset': 0,
    'fix_behavior': 'UseFirst'
}

cache_item = TournamentLoader.get_tournament_details(tournament_info)
