# -*- coding: utf-8 -*-
"""
Created on Sun Nov 24 18:39:50 2024

@author: Francois
"""
import json
from typing import List, Optional
from datetime import datetime



class TopdeckListTournamentStanding:
    def __init__(
        self, 
        id: Optional[str] = None,
        name: Optional[str] = None,
        decklist: Optional[str] = None,
        wins: Optional[int] = None,
        losses: Optional[int] = None,
        draws: Optional[int] = None,
        deckSnapshot: Optional['TopdeckListTournamentDeckSnapshot'] = None
    ):
        """
        Initialise les propriétés de la classe.
        :param id: Identifiant unique.
        :param name: Nom du joueur ou de l'équipe.
        :param decklist: Identifiant ou URL du deck utilisé.
        :param wins: Nombre de victoires.
        :param losses: Nombre de défaites.
        :param draws: Nombre de matchs nuls.
        :param deckSnapshot: Instance de TopdeckListTournamentDeckSnapshot représentant le deck.
        """
        self.id = id
        self.name = name
        self.decklist = decklist
        self.wins = wins
        self.losses = losses
        self.draws = draws
        self.deckSnapshot = deckSnapshot

    def normalize(self) -> None:
        """
        Normalise l'objet :
        - Appelle `normalize` sur le deckSnapshot.
        - Définit deckSnapshot à None si son mainboard est None après normalisation.
        """
        if self.deckSnapshot is not None:
            self.deckSnapshot.normalize()
            if self.deckSnapshot.mainboard is None:
                self.deckSnapshot = None

    def __str__(self) -> str:
        """
        Retourne une représentation lisible de l'objet.
        """
        return (
            f"TopdeckListTournamentStanding(id={self.id}, name={self.name}, "
            f"decklist={self.decklist}, wins={self.wins}, losses={self.losses}, "
            f"draws={self.draws}, deckSnapshot={self.deckSnapshot})"
        )

    def __eq__(self, other: object) -> bool:
        """
        Compare deux objets pour l'égalité.
        :param other: Autre objet à comparer.
        :return: True si les objets sont égaux, sinon False.
        """
        if not isinstance(other, TopdeckListTournamentStanding):
            return False
        return (
            self.id == other.id
            and self.name == other.name
            and self.decklist == other.decklist
            and self.wins == other.wins
            and self.losses == other.losses
            and self.draws == other.draws
            and self.deckSnapshot == other.deckSnapshot
        )

    def to_dict(self) -> dict:
        """
        Convertit l'objet en dictionnaire.
        :return: Dictionnaire contenant les propriétés de la classe.
        """
        return {
            "id": self.id,
            "name": self.name,
            "decklist": self.decklist,
            "wins": self.wins,
            "losses": self.losses,
            "draws": self.draws,
            "deckSnapshot": self.deckSnapshot.to_dict() if self.deckSnapshot else None,
        }

    @classmethod
    def from_json(cls, data) -> 'TopdeckListTournamentStanding':
        """
        Crée une instance de la classe à partir d'un dictionnaire.
        :param data: Dictionnaire contenant les données.
        :return: Instance de TopdeckListTournamentStanding.
        """
        from_snapshot = (
            TopdeckListTournamentDeckSnapshot.from_dict(data["deckSnapshot"])
            if data.get("deckSnapshot")
            else None
        )
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            decklist=data.get("decklist"),
            wins=data.get("wins"),
            losses=data.get("losses"),
            draws=data.get("draws"),
            deckSnapshot=from_snapshot,
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

    @classmethod
    def from_json(cls, data):
        standings = data.get("standings", [])
        standings_objects = [TopdeckListTournamentStanding(**standing) for standing in standings]
        return cls(
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
    def __init__(self, name=None, players:Optional[List[TopdeckRoundTablePlayer]]=None, winner=None):
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

    @classmethod
    def from_json(cls, data):
        """
        Crée une instance de TopdeckRoundTable à partir d'une structure JSON.
        :param data: Dictionnaire représentant une table.
        :return: Instance de TopdeckRoundTable.
        """
        name = f"Table {data.get('table')}"
        players = [TopdeckRoundTablePlayer(player.get("name")) for player in data.get("players", [])]
        winner = data.get("winner")
        return cls(name=name, players=players, winner=winner)

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

class TopdeckRound:
    def __init__(self, name=None, tables: Optional[List[TopdeckRoundTable]]=None):
        """
        Initialise les propriétés de la ronde du tournoi.
        :param name: Nom de la ronde.
        :param tables: Liste des tables du tournoi.
        """
        self.name = name
        self.tables = tables if tables is not None else []

    def normalize(self):
        """
        Normalise la ronde de tournoi en normalisant chaque table.
        """
        for table in self.tables:
            table.normalize()

    @classmethod
    def from_json(cls, data):
        """
        Crée une instance de TopdeckRound à partir d'une structure JSON.
        :param data: Dictionnaire représentant une ronde de tournoi.
        :return: Instance de TopdeckRound.
        """
        name = str(data.get("round"))
        tables = [TopdeckRoundTable.from_json(table) for table in data.get("tables", [])]
        return cls(name=name, tables=tables)

    def __str__(self):
        return f"TopdeckRound(name={self.name}, tables={self.tables})"

    def to_dict(self):
        """
        Convertit l'objet en dictionnaire.
        :return: Dictionnaire représentant l'objet.
        """
        return {
            "name": self.name,
            "tables": [table.to_dict() for table in self.tables]
        }

class TopdeckStanding:
    def __init__(self, 
                 standing: Optional[int] = None, 
                 name: Optional[str] = None, 
                 decklist: Optional[str] = None, 
                 points: Optional[int] = None, 
                 opponent_win_rate: Optional[float] = None, 
                 game_win_rate: Optional[float] = None, 
                 opponent_game_win_rate: Optional[float] = None):
        """
        Initialise les propriétés du classement.
        :param standing: Position du joueur (int).
        :param name: Nom du joueur (str).
        :param decklist: URL du decklist (str).
        :param points: Nombre de points du joueur (int).
        :param opponent_win_rate: Taux de victoire contre les adversaires (float).
        :param game_win_rate: Taux de victoire dans les parties (float).
        :param opponent_game_win_rate: Taux de victoire contre les adversaires dans les parties (float).
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

    @classmethod
    def from_json(cls, data) -> 'TopdeckStanding':
        """
        Crée une instance de TopdeckStanding à partir d'une structure JSON.
        :param data: Dictionnaire représentant un classement.
        :return: Instance de TopdeckStanding.
        """
        standing = data.get('standing')
        name = data.get('name')
        decklist = data.get('decklist')
        points = data.get('points')
        opponent_win_rate = data.get('opponentWinRate')
        game_win_rate = data.get('gameWinRate')
        opponent_game_win_rate = data.get('opponentGameWinRate')

        return cls(
            standing=standing,
            name=name,
            decklist=decklist,
            points=points,
            opponent_win_rate=opponent_win_rate,
            game_win_rate=game_win_rate,
            opponent_game_win_rate=opponent_game_win_rate
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
    def __init__(
        self, 
        name: Optional[str] = None, 
        game: Optional[str] = None, 
        format: Optional[str] = None, 
        start_date: Optional[int] =None
    ):
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
    @classmethod
    def from_json(cls, data) -> 'TopdeckTournamentInfo':
        """
        Crée une instance de TopdeckTournamentInfo à partir d'une structure JSON.
        :param data: Dictionnaire représentant les informations d'un tournoi.
        :return: Instance de TopdeckTournamentInfo.
        """
        name = data.get('name')
        game = data.get('game')
        format = data.get('format')
        start_date = data.get('startDate')
        return cls(
            name=name,
            game=game,
            format=format,
            start_date=start_date
        )
    
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
    def __init__(
        self, 
        game: Optional[str] = None, 
        format: Optional[str] = None, 
        start: Optional[int] = None, 
        end: Optional[int] = None, 
        last: Optional[int] = None, 
        columns: Optional[List[str]] = None
    ):
        """
        Initialise la requête de tournoi.
        :param game: Jeu associé à la requête.
        :param format: Format du tournoi.
        :param start: Date de début en timestamp Unix.
        :param end: Date de fin en timestamp Unix.
        :param last: Nombre de tournois à récupérer.
        :param columns: Liste des colonnes à inclure dans la réponse.
        """
        self.game = game
        self.format = format
        self.start = start
        self.end = end
        self.last = last
        self.columns = columns if columns is not None else []

    def to_json(self) -> str:
        """
        Convertit l'objet en JSON.
        :return: Représentation JSON de l'objet.
        """
        return json.dumps(self.to_dict(), ensure_ascii=False)

    def __str__(self) -> str:
        """
        Retourne une représentation lisible de la requête.
        """
        return (
            f"TopdeckTournamentRequest("
            f"game={self.game}, format={self.format}, start={self.start}, "
            f"end={self.end}, last={self.last}, columns={self.columns})"
        )

    def __eq__(self, other: object) -> bool:
        """
        Compare deux objets TopdeckTournamentRequest.
        :param other: Autre objet à comparer.
        :return: True si les objets sont égaux, sinon False.
        """
        if not isinstance(other, TopdeckTournamentRequest):
            return False
        return (
            self.game == other.game 
            and self.format == other.format 
            and self.start == other.start 
            and self.end == other.end 
            and self.last == other.last 
            and self.columns == other.columns
        )

    def to_dict(self) -> dict:
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
            "columns": self.columns
        }