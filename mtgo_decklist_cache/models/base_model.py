# -*- coding: utf-8 -*-
"""
Created on Sun Nov 24 18:39:50 2024

@author: Francois
"""
from datetime import datetime
from typing import List, Optional



class Tournament:
    def __init__(self, date: Optional[datetime] = None, name: Optional[str] = None, uri:  Optional[str] = None, json_file: Optional[str] = None, force_redownload: bool = False):
        self.date = date
        self.name = name
        self.uri = uri
        self.json_file = json_file
        self.force_redownload = force_redownload

    def __str__(self):
        if self.date:
            return f"{self.name}|{self.date.strftime('%Y-%m-%d')}"
        else:
            return f"{self.name}|No date available"
        
    def to_dict(self):
        return {
            "Date": self.date.isoformat() if self.date else None,
            "Name": self.name,
            "Uri": self.uri,
        }


class Standing:
    def __init__(self, 
                 rank: Optional[int] = None, 
                 player: Optional[str] = None, 
                 points: Optional[int] = None, 
                 wins: Optional[int] = None, 
                 losses: Optional[int] = None, 
                 draws: Optional[int] = None, 
                 omwp: Optional[float] = None, 
                 gwp: Optional[float] = None, 
                 ogwp: Optional[float] = None):
        # Assign default values if None
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
        return (
            f"Standing(Rank={self.rank}, Player='{self.player}', Points={self.points}, "
            f"Wins={self.wins}, Losses={self.losses}, Draws={self.draws}, "
            f"OMWP={self.omwp:.2f}, GWP={self.gwp:.2f}, OGWP={self.ogwp:.2f})"
        )

    def __eq__(self, other):
        if not isinstance(other, Standing):
            return NotImplemented
        return (
            self.rank == other.rank and
            self.player == other.player and
            self.points == other.points and
            self.wins == other.wins and
            self.losses == other.losses and
            self.draws == other.draws and
            self.omwp == other.omwp and
            self.gwp == other.gwp and
            self.ogwp == other.ogwp
        )
    
    def to_dict(self):
        return {
            "Rank": self.rank,
            "Player": self.player,
            "Points": self.points,
            "Wins": self.wins,
            "Losses": self.losses,
            "Draws": self.draws,
            "OMWP": self.omwp,
            "GWP": self.gwp,
            "OGWP": self.ogwp,
        }


class RoundItem:
    def __init__(self, player1: str, player2: str, result: str):
        self.player1 = player1
        self.player2 = player2
        self.result = result

    def __str__(self):
        return f"{self.player1} {self.result} {self.player2}"
    def __eq__(self, other):
        if not isinstance(other, RoundItem):
            return False
        return (self.player1 == other.player1 and
                self.player2 == other.player2 and
                self.result == other.result)
    def to_dict(self):
        return {
            "Player1": self.player1,
            "Player2": self.player2,
            "Result": self.result,
        }

class Round:
    def __init__(self, round_name: str, matches: List[RoundItem]):
        self.round_name = round_name
        self.matches = matches

    def __str__(self):
        return f"Round: {self.round_name}, {len(self.matches)} matches"
    def __eq__(self, other):
        if not isinstance(other, Round):
            return False
        return (self.round_name == other.round_name and
                self.matches == other.matches)
    def to_dict(self):
        return {
            "RoundName": self.round_name,
            "Matches": [match.to_dict() for match in self.matches],
        }

class DeckItem:
    def __init__(self, count: int, card_name: str):
        self.count = count
        self.card_name = card_name
    def __str__(self):
        return f"count : {self.count}, card name : {self.card_name}"
    def __eq__(self, other):
        if isinstance(other, DeckItem):
            return self.count == other.count and self.card_name == other.card_name
        return False
    def to_dict(self):
        return {
            "Count": self.count,
            "CardName": self.card_name,
        }

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
                # Calculer le nombre total de cartes
        total_mainboard = sum(item.count for item in self.mainboard)
        total_sideboard = sum(item.count for item in self.sideboard)
        total = total_mainboard + total_sideboard
        
        # Créer une représentation sous forme de chaîne des cartes du mainboard et du sideboard
        mainboard_cards = ', '.join(f"{item.card_name} ({item.count})" for item in self.mainboard)
        sideboard_cards = ', '.join(f"{item.card_name} ({item.count})" for item in self.sideboard)
        
        # Afficher toutes les informations utiles
        return (f"Deck for {self.player} ({self.result}) - {self.date}\n"
                f"Total Cards: {total}\n"
                f"Mainboard: {mainboard_cards}\n"
                f"Sideboard: {sideboard_cards}\n"
                f"Anchor URI: {self.anchor_uri}")
    
    def __eq__(self, other):
        if not isinstance(other, Deck):
            return False
        return (self.date == other.date and
                self.player == other.player and
                self.result == other.result and
                self.anchor_uri == other.anchor_uri and
                self.mainboard == other.mainboard and
                self.sideboard == other.sideboard)
    
    def to_dict(self):
        return {
            # "Date": self.date.isoformat() if self.date else None,
            "Date": self.date.isoformat() if self.date else None,
            "Player": self.player,
            "Result": self.result,
            "AnchorUri": self.anchor_uri,
            "Mainboard": [item.to_dict() for item in self.mainboard],
            "Sideboard": [item.to_dict() for item in self.sideboard],
        }

class CacheItem:
    def __init__(self, tournament: Tournament, decks: List[Deck], rounds: List[Round], standings: List[Standing]):
        self.tournament = tournament
        self.decks = decks
        self.rounds = rounds
        self.standings = standings

    def __str__(self):
        return f"{len(self.decks)} decks"
    
    def to_dict(self):
        return {
            "Tournament": self.tournament.to_dict(),
            "Decks": [deck.to_dict() for deck in self.decks],
            "Rounds": [
            round_.to_dict() for round_ in self.rounds or [] if round_ is not None
        ],
            "Standings": [
                standing.to_dict() for standing in (self.standings or []) if standing is not None
        ],
        }


class RoundItem:
    def __init__(self, player1: str, player2: str, result: str):
        self.player1 = player1
        self.player2 = player2
        self.result = result
    def __eq__(self, other):
        return (self.player1 == other.player1 and
                self.player2 == other.player2 and
                self.result == other.result)
    def __str__(self):
        return f"player1 : {self.player1}, player2 : {self.player2}, result : {self.result}"
    def to_dict(self):
        return {
            "Player1": self.player1,
            "Player2": self.player2,
            "Result": self.result
        }

