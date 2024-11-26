# -*- coding: utf-8 -*-
"""
Created on Sun Nov 24 18:39:50 2024

@author: Francois
"""

from datetime import datetime
from typing import List, Optional


class Tournament:
    def __init__(self, date: datetime, name: str, uri: str, json_file: Optional[str] = None, force_redownload: bool = False):
        self.date = date
        self.name = name
        self.uri = uri
        self.json_file = json_file
        self.force_redownload = force_redownload

    def __str__(self):
        return f"{self.name}|{self.date.strftime('%Y-%m-%d')}"


class Standing:
    def __init__(self, rank: int, player: str, points: int, wins: int, losses: int, draws: int, omwp: float, gwp: float, ogwp: float):
        self.rank = rank
        self.player = player
        self.points = points
        self.wins = wins
        self.losses = losses
        self.draws = draws
        self.omwp = omwp
        self.gwp = gwp
        self.ogwp = ogwp

    def __str__(self):
        return f"#{self.rank} {self.player} {self.points} points"


class RoundItem:
    def __init__(self, player1: str, player2: str, result: str):
        self.player1 = player1
        self.player2 = player2
        self.result = result

    def __str__(self):
        return f"{self.player1} {self.result} {self.player2}"


class Round:
    def __init__(self, round_name: str, matches: List[RoundItem]):
        self.round_name = round_name
        self.matches = matches

    def __str__(self):
        return f"Round: {self.round_name}, {len(self.matches)} matches"


class DeckItem:
    def __init__(self, count: int, card_name: str):
        self.count = count
        self.card_name = card_name

    def __str__(self):
        return f"{self.count} {self.card_name}"


class Deck:
    def __init__(self, date: Optional[datetime], player: str, result: str, anchor_uri: str,
                 mainboard: List[DeckItem], sideboard: List[DeckItem]):
        self.date = date
        self.player = player
        self.result = result
        self.anchor_uri = anchor_uri
        self.mainboard = mainboard
        self.sideboard = sideboard

    def contains(self, *cards: str) -> bool:
        return all(any(item.card_name == c for item in self.mainboard) or 
                   any(item.card_name == c for item in self.sideboard) for c in cards)

    def __str__(self):
        total = sum(item.count for item in self.mainboard) + sum(item.count for item in self.sideboard)
        return f"{total} cards"


class CacheItem:
    def __init__(self, tournament: Tournament, decks: List[Deck], rounds: List[Round], standings: List[Standing]):
        self.tournament = tournament
        self.decks = decks
        self.rounds = rounds
        self.standings = standings

    def __str__(self):
        return f"{len(self.decks)} decks"
