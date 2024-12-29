# -*- coding: utf-8 -*-
"""
Created on Sun Nov 24 18:39:50 2024

@author: Francois
"""
import json
from typing import List, Optional


# class TopdeckListTournamentStanding:
#     def __init__(self, standing_id=None):
#         self.standing_id = standing_id

#     def normalize(self):
#         # Implémentez la logique de normalisation ici si nécessaire
#         pass

#     def __str__(self):
#         return f"TopdeckListTournamentStanding(standing_id={self.standing_id})"

#     def __eq__(self, other):
#         if not isinstance(other, TopdeckListTournamentStanding):
#             return False
#         return self.standing_id == other.standing_id

#     def to_dict(self):
#         return {"standing_id": self.standing_id}
class TopdeckListTournamentStanding:
    def __init__(self, name=None, wins=None, losses=None, draws=None, deck_snapshot=None):
        """
        Initialise les propriétés de la classe.
        :param name: Nom du joueur ou de l'équipe.
        :param wins: Nombre de victoires.
        :param losses: Nombre de défaites.
        :param draws: Nombre de matchs nuls.
        :param deck_snapshot: Instance de TopdeckListTournamentDeckSnapshot représentant le deck.
        """
        self.name = name
        self.wins = wins
        self.losses = losses
        self.draws = draws
        self.deck_snapshot = deck_snapshot

    def normalize(self):
        """
        Normalise l'objet :
        - Appelle `normalize` sur le deck_snapshot.
        - Définit deck_snapshot à None si son mainboard est None après normalisation.
        """
        if self.deck_snapshot is not None:
            self.deck_snapshot.normalize()
            if self.deck_snapshot.mainboard is None:
                self.deck_snapshot = None

    def __str__(self):
        """
        Retourne une représentation lisible de l'objet.
        """
        return (
            f"TopdeckListTournamentStanding(name={self.name}, "
            f"wins={self.wins}, losses={self.losses}, draws={self.draws}, "
            f"deck_snapshot={self.deck_snapshot})"
        )

    def __eq__(self, other):
        """
        Compare deux objets pour l'égalité.
        :param other: Autre objet à comparer.
        :return: True si les objets sont égaux, sinon False.
        """
        if not isinstance(other, TopdeckListTournamentStanding):
            return False
        return (
            self.name == other.name
            and self.wins == other.wins
            and self.losses == other.losses
            and self.draws == other.draws
            and self.deck_snapshot == other.deck_snapshot
        )

    def to_dict(self):
        """
        Convertit l'objet en dictionnaire.
        :return: Dictionnaire contenant les propriétés de la classe.
        """
        return {
            "name": self.name,
            "wins": self.wins,
            "losses": self.losses,
            "draws": self.draws,
            "deck_snapshot": self.deck_snapshot.to_dict() if self.deck_snapshot else None,
        }

    @staticmethod
    def from_dict(data):
        """
        Crée une instance de la classe à partir d'un dictionnaire.
        :param data: Dictionnaire contenant les données.
        :return: Instance de TopdeckListTournamentStanding.
        """
        from_snapshot = (
            TopdeckListTournamentDeckSnapshot.from_dict(data["deck_snapshot"])
            if data.get("deck_snapshot")
            else None
        )
        return TopdeckListTournamentStanding(
            name=data.get("name"),
            wins=data.get("wins"),
            losses=data.get("losses"),
            draws=data.get("draws"),
            deck_snapshot=from_snapshot,
        )
    

class TopdeckListTournament:
    def __init__(self, id=None, name=None, start_date=None, uri=None, standings=None):
        self.id = id
        self.name = name
        self.start_date = start_date
        self.uri = uri
        self.standings = standings if standings is not None else []

    def normalize(self):
        if self.id is not None:
            self.uri = Misc.TournamentPage.replace("{tournamentId}", self.id)
        for standing in self.standings:
            standing.normalize()

    def __str__(self):
        return (
            f"TopdeckListTournament("
            f"id={self.id}, name={self.name}, start_date={self.start_date}, "
            f"uri={self.uri}, standings=[{', '.join(str(s) for s in self.standings)}]"
            f")"
        )

    def __eq__(self, other):
        if not isinstance(other, TopdeckListTournament):
            return False
        return (
            self.id == other.id
            and self.name == other.name
            and self.start_date == other.start_date
            and self.uri == other.uri
            and self.standings == other.standings
        )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "start_date": self.start_date,
            "uri": self.uri,
            "standings": [standing.to_dict() for standing in self.standings],
        }

    @staticmethod
    def from_json(data):
        standings = data.get("standings", [])
        standings_objects = [TopdeckListTournamentStanding(**standing) for standing in standings]
        return TopdeckListTournament(
            id=data.get("TID"),
            name=data.get("tournamentName"),
            start_date=data.get("startDate"),
            standings=standings_objects,
        )
class TopdeckListTournamentDeckSnapshot:
    def __init__(self, mainboard=None, sideboard=None):
        """
        Initialise les propriétés mainboard et sideboard.
        :param mainboard: Dictionnaire représentant le mainboard.
        :param sideboard: Dictionnaire représentant le sideboard.
        """
        self.mainboard = mainboard if mainboard is not None else {}
        self.sideboard = sideboard if sideboard is not None else {}

    def normalize(self):
        """
        Normalise les dictionnaires mainboard et sideboard :
        - Remplace un dictionnaire vide par None.
        """
        if self.mainboard is not None and len(self.mainboard) == 0:
            self.mainboard = None
        if self.sideboard is not None and len(self.sideboard) == 0:
            self.sideboard = None

    def __str__(self):
        """
        Retourne une représentation lisible de l'objet.
        """
        return f"TopdeckListTournamentDeckSnapshot(mainboard={self.mainboard}, sideboard={self.sideboard})"

    def __eq__(self, other):
        """
        Compare deux objets pour l'égalité.
        :param other: Autre objet à comparer.
        :return: True si les objets sont égaux, sinon False.
        """
        if not isinstance(other, TopdeckListTournamentDeckSnapshot):
            return False
        return self.mainboard == other.mainboard and self.sideboard == other.sideboard

    def to_dict(self):
        """
        Convertit l'objet en dictionnaire.
        :return: Dictionnaire contenant les propriétés mainboard et sideboard.
        """
        return {
            "mainboard": self.mainboard,
            "sideboard": self.sideboard,
        }

    @staticmethod
    def from_dict(data):
        """
        Crée un objet à partir d'un dictionnaire.
        :param data: Dictionnaire contenant les données.
        :return: Instance de TopdeckListTournamentDeckSnapshot.
        """
        return TopdeckListTournamentDeckSnapshot(
            mainboard=data.get("mainboard"),
            sideboard=data.get("sideboard"),
        )
    



class TopdeckRoundTablePlayer:
    def __init__(self, name=None):
        """
        Initialise les propriétés de la classe.
        :param name: Nom du joueur.
        """
        self.name = name

    def normalize(self):
        """
        Normalisation des joueurs.
        Cette méthode est vide ici, mais peut être étendue si nécessaire.
        """
        pass

    def __str__(self):
        """
        Retourne une représentation lisible du joueur.
        """
        return f"TopdeckRoundTablePlayer(name={self.name})"

    def __eq__(self, other):
        """
        Compare deux objets TopdeckRoundTablePlayer.
        :param other: Autre objet à comparer.
        :return: True si les objets sont égaux, sinon False.
        """
        if not isinstance(other, TopdeckRoundTablePlayer):
            return False
        return self.name == other.name

    def to_dict(self):
        """
        Convertit l'objet en dictionnaire.
        :return: Dictionnaire représentant l'objet.
        """
        return {"name": self.name}


class TopdeckRoundTable:
    def __init__(self, name=None, players=None, winner=None):
        """
        Initialise les propriétés de la table de tournoi.
        :param name: Nom de la table.
        :param players: Liste des joueurs de la table.
        :param winner: Nom du gagnant.
        """
        self.name = name
        self.players = players if players is not None else []
        self.winner = winner

    def normalize(self):
        """
        Normalisation de la table de tournoi :
        Normalise chaque joueur de la table.
        """
        for player in self.players:
            player.normalize()

    def __str__(self):
        """
        Retourne une représentation lisible de la table.
        """
        return f"TopdeckRoundTable(name={self.name}, players={self.players}, winner={self.winner})"

    def __eq__(self, other):
        """
        Compare deux objets TopdeckRoundTable.
        :param other: Autre objet à comparer.
        :return: True si les objets sont égaux, sinon False.
        """
        if not isinstance(other, TopdeckRoundTable):
            return False
        return self.name == other.name and self.players == other.players and self.winner == other.winner

    def to_dict(self):
        """
        Convertit l'objet en dictionnaire.
        :return: Dictionnaire représentant l'objet.
        """
        return {
            "name": self.name,
            "players": [player.to_dict() for player in self.players],
            "winner": self.winner
        }


class TopdeckStanding:
    def __init__(self, standing=None, name=None, decklist=None, points=None, opponent_win_rate=None, game_win_rate=None, opponent_game_win_rate=None):
        """
        Initialise les propriétés du classement.
        :param standing: Position du joueur.
        :param name: Nom du joueur.
        :param decklist: URL du decklist.
        :param points: Nombre de points du joueur.
        :param opponent_win_rate: Taux de victoire contre les adversaires.
        :param game_win_rate: Taux de victoire dans les parties.
        :param opponent_game_win_rate: Taux de victoire contre les adversaires dans les parties.
        """
        self.standing = standing
        self.name = name
        self.decklist = decklist
        self.points = points
        self.opponent_win_rate = opponent_win_rate
        self.game_win_rate = game_win_rate
        self.opponent_game_win_rate = opponent_game_win_rate

    def normalize(self):
        """
        Normalisation de l'objet :
        Si le decklist est vide ou mal formé, il est mis à None.
        """
        if not self.decklist or self.decklist == "NoDecklistsText" or not self._is_valid_uri(self.decklist):
            self.decklist = None

    def _is_valid_uri(self, uri):
        """
        Vérifie si une chaîne est une URL valide.
        :param uri: URL à vérifier.
        :return: True si l'URL est valide, sinon False.
        """
        from urllib.parse import urlparse
        result = urlparse(uri)
        return all([result.scheme, result.netloc])

    def __str__(self):
        """
        Retourne une représentation lisible du classement.
        """
        return (
            f"TopdeckStanding(standing={self.standing}, name={self.name}, "
            f"decklist={self.decklist}, points={self.points}, "
            f"opponent_win_rate={self.opponent_win_rate}, "
            f"game_win_rate={self.game_win_rate}, opponent_game_win_rate={self.opponent_game_win_rate})"
        )

    def __eq__(self, other):
        """
        Compare deux objets TopdeckStanding.
        :param other: Autre objet à comparer.
        :return: True si les objets sont égaux, sinon False.
        """
        if not isinstance(other, TopdeckStanding):
            return False
        return (
            self.standing == other.standing
            and self.name == other.name
            and self.decklist == other.decklist
            and self.points == other.points
            and self.opponent_win_rate == other.opponent_win_rate
            and self.game_win_rate == other.game_win_rate
            and self.opponent_game_win_rate == other.opponent_game_win_rate
        )

    def to_dict(self):
        """
        Convertit l'objet en dictionnaire.
        :return: Dictionnaire représentant l'objet.
        """
        return {
            "standing": self.standing,
            "name": self.name,
            "decklist": self.decklist,
            "points": self.points,
            "opponent_win_rate": self.opponent_win_rate,
            "game_win_rate": self.game_win_rate,
            "opponent_game_win_rate": self.opponent_game_win_rate,
        }



class NormalizableObject:
    def normalize(self):
        pass


class TopdeckTournamentInfo(NormalizableObject):
    def __init__(self, name=None, game=None, format=None, start_date=None):
        """
        Initialise les propriétés de l'information du tournoi.
        :param name: Nom du tournoi.
        :param game: Jeu associé au tournoi.
        :param format: Format du tournoi.
        :param start_date: Date de début du tournoi.
        """
        self.name = name
        self.game = game
        self.format = format
        self.start_date = start_date

    def normalize(self):
        """
        Normalisation de l'information du tournoi. 
        Ici, aucune action spécifique n'est nécessaire.
        """
        pass

    def __str__(self):
        """
        Retourne une représentation lisible de l'information du tournoi.
        """
        return f"TopdeckTournamentInfo(name={self.name}, game={self.game}, format={self.format}, start_date={self.start_date})"

    def __eq__(self, other):
        """
        Compare deux objets TopdeckTournamentInfo.
        :param other: Autre objet à comparer.
        :return: True si les objets sont égaux, sinon False.
        """
        if not isinstance(other, TopdeckTournamentInfo):
            return False
        return self.name == other.name and self.game == other.game and self.format == other.format and self.start_date == other.start_date

    def to_dict(self):
        """
        Convertit l'objet en dictionnaire.
        :return: Dictionnaire représentant l'objet.
        """
        return {
            "name": self.name,
            "game": self.game,
            "format": self.format,
            "start_date": self.start_date
        }


class TopdeckTournament(NormalizableObject):
    def __init__(self, data: Optional[TopdeckTournamentInfo] = None, standings: Optional[List['TopdeckStanding']] = None, rounds: Optional[List['TopdeckRound']] = None):
        """
        Initialise les propriétés du tournoi.
        :param data: Informations sur le tournoi.
        :param standings: Liste des classements.
        :param rounds: Liste des rondes.
        """
        self.data = data
        self.standings = standings if standings is not None else []
        self.rounds = rounds if rounds is not None else []

    def normalize(self):
        """
        Normalisation du tournoi.
        """
        if self.data:
            self.data.normalize()
        for standing in self.standings:
            standing.normalize()
        for round_ in self.rounds:
            round_.normalize()

    def __str__(self):
        """
        Retourne une représentation lisible du tournoi.
        """
        return f"TopdeckTournament(data={self.data}, standings={self.standings}, rounds={self.rounds})"

    def __eq__(self, other):
        """
        Compare deux objets TopdeckTournament.
        :param other: Autre objet à comparer.
        :return: True si les objets sont égaux, sinon False.
        """
        if not isinstance(other, TopdeckTournament):
            return False
        return self.data == other.data and self.standings == other.standings and self.rounds == other.rounds

    def to_dict(self):
        """
        Convertit l'objet en dictionnaire.
        :return: Dictionnaire représentant l'objet.
        """
        return {
            "data": self.data.to_dict() if self.data else None,
            "standings": [standing.to_dict() for standing in self.standings],
            "rounds": [round_.to_dict() for round_ in self.rounds]
        }


class TopdeckTournamentRequest:
    def __init__(self, game=None, format=None, start=None, end=None, last=None, columns=None):
        """
        Initialise la requête de tournoi.
        :param game: Jeu associé à la requête.
        :param format: Format du tournoi.
        :param start: Date de début.
        :param end: Date de fin.
        :param last: Nombre de tournois à récupérer.
        :param columns: Colonnes à inclure dans la réponse.
        """
        self.game = game
        self.format = format
        self.start = start
        self.end = end
        self.last = last
        self.columns = columns if columns is not None else []

    def to_json(self):
        """
        Convertit l'objet en JSON.
        :return: Représentation JSON de l'objet.
        """
        return json.dumps(self, default=lambda o: o.__dict__, ensure_ascii=False)

    def __str__(self):
        """
        Retourne une représentation lisible de la requête.
        """
        return f"TopdeckTournamentRequest(game={self.game}, format={self.format}, start={self.start}, end={self.end}, last={self.last}, columns={self.columns})"

    def __eq__(self, other):
        """
        Compare deux objets TopdeckTournamentRequest.
        :param other: Autre objet à comparer.
        :return: True si les objets sont égaux, sinon False.
        """
        if not isinstance(other, TopdeckTournamentRequest):
            return False
        return self.game == other.game and self.format == other.format and self.start == other.start and self.end == other.end and self.last == other.last and self.columns == other.columns

    def to_dict(self):
        """
        Convertit l'objet en dictionnaire.
        :return: Dictionnaire représentant l'objet.
        """
        return {
            "game": self.game,
            "format": self.format,
            "start": self.start,
            "end": self.end,
            "last": self.last,
            "columns": [column.to_dict() for column in self.columns] if self.columns else None
        }
