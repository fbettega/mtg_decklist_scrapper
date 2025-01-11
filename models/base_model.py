# -*- coding: utf-8 -*-
"""
Created on Sun Nov 24 18:39:50 2024

@author: Francois
"""
from datetime import datetime
from typing import List, Optional
import decimal
class Tournament:
    def __init__(self, date: Optional[datetime] = None, name: Optional[str] = None, uri:  Optional[str] = None,formats: Optional[List[str]] = None, json_file: Optional[str] = None, force_redownload: bool = False):
        self.date = date
        self.name = name
        self.uri = uri
        self.formats = formats
        self.json_file = json_file
        self.force_redownload = force_redownload

    def __str__(self):
        if self.date:
            return f"{self.name}|{self.date.strftime('%Y-%m-%d')}"
        else:
            return f"{self.name}|No date available"
    def __eq__(self, other):
        """
        Compare deux objets Tournament pour l'égalité.
        :param other: Autre objet à comparer.
        :return: True si les objets sont égaux, sinon False.
        """
        if not isinstance(other, Tournament):
            return False
        return (
            self.date == other.date
            and self.name == other.name
            and self.uri == other.uri
            and self.formats == other.formats
            and self.json_file == other.json_file
            and self.force_redownload == other.force_redownload
        )
        
    def to_dict(self):
        return {
            "Date": self.date.isoformat() if self.date else None,
            "Name": self.name,
            "Uri": self.uri,
            "Formats": self.formats,
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
                # OMP - Opponents’ Match-Win Percentage. A player’s match-win percentage is that player’s accumulated match points divided by X times the number of rounds in which he or she competed, or 0.33, whichever is greater.
                 gwp: Optional[float] = None, 
                # pour manatrader les bye compte
                # GWP - Game-Win Percentage. Similar to the match-win percentage, a player’s game-win percentage is the total number of game points he or she earned divided by X times the number of games played.
                 ogwp: Optional[float] = None):
                # Vérifier par calcules si on des ogwp est inférieurs a 0.33 il est remplacé par exactement 0.33
                #OGP - Opponents’ Game-Win Percentage. Similar to opponents’ match-win percentage, a player’s opponents’ game-win percentage is simply the average game-win percentage of all of that player’s opponents. And, as with opponents’ match-win percentage, each opponent has a minimum game-win percentage of 0.33.
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
            f"OMWP={'{:.4f}'.format(self.omwp) if self.omwp is not None else 'None'}, "
            f"GWP={'{:.4f}'.format(self.gwp) if self.gwp is not None else 'None'}, "
            f"OGWP={'{:.4f}'.format(self.ogwp) if self.ogwp is not None else 'None'})"
        )

    def get_significant_digits(self, value: float) -> int:
        """Calcule le nombre de chiffres significatifs d'un nombre flottant."""
        if value is None:
            return 0
        d = decimal.Decimal(str(value))
        # Exclure les parties non significatives après la virgule
        return max(d.as_tuple().exponent, -d.as_tuple().exponent)  # Nombre de chiffres après la virgule

    def __eq__(self, other):
        if not isinstance(other, Standing):
            return NotImplemented
        
        def float_equals(a, b):
            # Calculer le nombre de chiffres significatifs de chaque nombre
            digits_a = self.get_significant_digits(a)
            digits_b = self.get_significant_digits(b)
            # La tolérance est donnée par le plus petit nombre de chiffres significatifs entre les deux valeurs
            tolerance = 10 ** -min(digits_a, digits_b)
            return abs(a - b) <= tolerance

        return (
            self.rank == other.rank and
            self.player == other.player and
            self.points == other.points and
            self.wins == other.wins and
            self.losses == other.losses and
            self.draws == other.draws and
            float_equals(self.omwp, other.omwp) and
            float_equals(self.gwp, other.gwp) and
            float_equals(self.ogwp, other.ogwp)
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
    def __hash__(self):
        return hash((self.player1, self.player2, self.result))
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
    def __init__(self, player1: str, player2: str, result: str,id:Optional[str]=None):
        self.player1 = player1
        self.player2 = player2
        self.result = result
        p1_wins, p2_wins, _ = map(int, result.split('-'))  
        self.id = id
        # Pré-calculer les résultats sous forme de tuples (wins, losses)
        self.scores = [
            (int(p1_wins > p2_wins), int(p1_wins < p2_wins)),  # Résultat pour player1
            (int(p2_wins > p1_wins), int(p2_wins < p1_wins))   # Résultat pour player2
        ]

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
    def __hash__(self):
        return hash((self.player1, self.player2, self.result))

