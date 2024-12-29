from enum import Enum
import os
import json
from datetime import datetime, timedelta
import requests

class TopDeckConstants:
    class Format(Enum):
        EDH = "EDH"
        PauperEDH = "Pauper EDH"
        Standard = "Standard"
        Pioneer = "Pioneer"
        Modern = "Modern"
        Legacy = "Legacy"
        Pauper = "Pauper"
        Vintage = "Vintage"
        Premodern = "Premodern"
        Limited = "Limited"
        Timeless = "Timeless"
        Historic = "Historic"
        Explorer = "Explorer"
        Oathbreaker = "Oathbreaker"
    class Game(Enum):
        MagicTheGathering = "Magic: The Gathering"
    class Misc:
        NO_DECKLISTS_TEXT = "No Decklist Available"
        DRAW_TEXT = "Draw"
        TOURNAMENT_PAGE = "https://topdeck.gg/event/{tournamentId}"
    class PlayerColumn(Enum):
        Name = "name"
        Decklist = "decklist"
        DeckSnapshot = "deckSnapshot"
        Commanders = "commanders"
        Wins = "wins"
        WinsSwiss = "winsSwiss"
        WinsBracket = "winsBracket"
        WinRate = "winRate"
        WinRateSwiss = "winRateSwiss"
        WinRateBracket = "winRateBracket"
        Draws = "draws"
        Losses = "losses"
        LossesSwiss = "lossesSwiss"
        LossesBracket = "lossesBracket"
        ID = "id"

    class Routes:
        ROOT_URL = "https://topdeck.gg/api"
        TOURNAMENT_ROUTE = f"{ROOT_URL}/v2/tournaments"
        STANDINGS_ROUTE = f"{ROOT_URL}/v2/tournaments/{{TID}}/standings"
        ROUNDS_ROUTE = f"{ROOT_URL}/v2/tournaments/{{TID}}/rounds"
        TOURNAMENT_INFO_ROUTE = f"{ROOT_URL}/v2/tournaments/{{TID}}/info"
        FULL_TOURNAMENT_ROUTE = f"{ROOT_URL}/v2/tournaments/{{TID}}"

    class Settings:
        API_KEY_FILE_PATH = "Client/api_topdeck.txt"
        @staticmethod
        def get_api_key():
            try:
                with open(TopDeckConstants.Settings.API_KEY_FILE_PATH, "r") as file:
                    api_key = file.read().strip()
                    if api_key:
                        return api_key
                    else:
                        raise ValueError("Le fichier API est vide.")
            except FileNotFoundError:
                raise FileNotFoundError(f"Le fichier {Settings.API_KEY_FILE_PATH} est introuvable.")
            except Exception as e:
                raise RuntimeError(f"Erreur lors de la récupération de l'API key : {e}")
        

class MissingApiKeyException(Exception):
    def __init__(self):
        super().__init__(f"Could not load API key from environment variable {Settings.API_KEY_ENV_VAR}")


class TopdeckClient:
    def __init__(self):
        self._api_key = os.getenv(Settings.API_KEY_ENV_VAR, "").strip()
        if not self._api_key:
            raise MissingApiKeyException()

    def get_tournament_list(self, request):
        """
        Récupère la liste des tournois.
        :param request: Requête de tournoi (TopdeckTournamentRequest).
        :return: Liste des tournois (TopdeckListTournament).
        """
        server_data = self._get_client().post(Routes.TOURNAMENT_ROUTE, json=request.to_dict())
        return self._normalize_array_result(TopdeckListTournament, server_data)

    def get_tournament(self, tournament_id):
        """
        Récupère un tournoi par son ID.
        :param tournament_id: Identifiant du tournoi.
        :return: Détails du tournoi (TopdeckTournament).
        """
        server_data = self._get_client().get(Routes.FULL_TOURNAMENT_ROUTE.replace("{TID}", tournament_id))
        return self._normalize_result(TopdeckTournament, server_data)

    def get_tournament_info(self, tournament_id):
        """
        Récupère les informations d'un tournoi.
        :param tournament_id: Identifiant du tournoi.
        :return: Informations du tournoi (TopdeckTournamentInfo).
        """
        server_data = self._get_client().get(Routes.TOURNAMENT_INFO_ROUTE.replace("{TID}", tournament_id))
        return self._normalize_result(TopdeckTournamentInfo, server_data)

    def get_standings(self, tournament_id):
        """
        Récupère les classements d'un tournoi.
        :param tournament_id: Identifiant du tournoi.
        :return: Classements du tournoi (TopdeckStanding).
        """
        server_data = self._get_client().get(Routes.STANDINGS_ROUTE.replace("{TID}", tournament_id))
        return self._normalize_array_result(TopdeckStanding, server_data)

    def get_rounds(self, tournament_id):
        """
        Récupère les rondes d'un tournoi.
        :param tournament_id: Identifiant du tournoi.
        :return: Rondes du tournoi (TopdeckRound).
        """
        server_data = self._get_client().get(Routes.ROUNDS_ROUTE.replace("{TID}", tournament_id))
        return self._normalize_array_result(TopdeckRound, server_data)

    def _get_client(self):
        """
        Crée un client HTTP pour effectuer les requêtes.
        :return: Client HTTP configuré.
        """
        headers = {
            "Authorization": self._api_key,
            "Content-Type": "application/json; charset=utf-8"
        }
        return requests.Session().headers.update(headers)

    def _normalize_result(self, cls, json_data):
        """
        Normalise et retourne un objet à partir de données JSON.
        :param cls: Classe cible pour la désérialisation.
        :param json_data: Données JSON à désérialiser.
        :return: Objet normalisé de type `cls`.
        """
        result = cls.from_json(json_data)
        result.normalize()
        return result

    def _normalize_array_result(self, cls, json_data):
        """
        Normalise et retourne un tableau d'objets à partir de données JSON.
        :param cls: Classe cible pour la désérialisation.
        :param json_data: Données JSON à désérialiser.
        :return: Liste d'objets normalisés de type `cls`.
        """
        results = [cls.from_json(item) for item in json_data]
        for result in results:
            result.normalize()
        return results
    
###########################################################################################################################################
# updater

class TopdeckSource:
    def __init__(self):
        self.provider = "topdeck.gg"
        self.client = TopdeckClient()

    def get_tournament_details(self, tournament):
        tournament_id = tournament.uri.split("/")[-1]

        tournament_data = self.client.get_tournament(tournament_id)
        tournament_data_from_list = self.client.get_tournament_list(TopdeckTournamentRequest(
            start=tournament_data.data.start_date,
            end=tournament_data.data.start_date + 1,
            game=tournament_data.data.game,
            format=tournament_data.data.format,
            columns=[PlayerColumn.Name, PlayerColumn.Wins, PlayerColumn.Losses, PlayerColumn.Draws, PlayerColumn.DeckSnapshot]
        ))[0]  # Assuming the tournament name matches

        rounds = []
        for round in tournament_data.rounds:
            round_items = []
            for table in round.tables:
                if table.winner == "Draw" or len(table.players) == 1:
                    if len(table.players) == 1:
                        # Byes
                        round_items.append(RoundItem(player1=table.players[0].name, player2="", result="0-0-1"))
                    else:
                        round_items.append(RoundItem(player1=table.players[0].name, player2=table.players[1].name, result="0-0-1"))
                else:
                    winner = table.winner
                    if winner == table.players[0].name:
                        round_items.append(RoundItem(player1=table.players[0].name, player2=table.players[1].name, result="1-0-0"))
                    elif winner == table.players[1].name:
                        round_items.append(RoundItem(player1=table.players[1].name, player2=table.players[0].name, result="1-0-0"))
            rounds.append(Round(round_name=round.name, matches=round_items))

        standings = []
        for standing in tournament_data.standings:
            list_standing = next((s for s in tournament_data_from_list.standings if s.name == standing.name), None)

            standings.append(Standing(
                player=standing.name,
                rank=standing.standing,
                wins=list_standing.wins,
                losses=list_standing.losses,
                draws=list_standing.draws,
                gwp=standing.game_win_rate,
                omwp=standing.opponent_win_rate,
                ogwp=standing.opponent_game_win_rate
            ))

        decks = []
        for standing in tournament_data.standings:
            list_standing = next((s for s in tournament_data_from_list.standings if s.name == standing.name), None)

            if list_standing.deck_snapshot and list_standing.deck_snapshot.mainboard:
                player_result = f"{standing.standing}th Place" if standing.standing > 3 else f"{standing.standing}st Place"  # or nd, rd depending on the rank

                mainboard = [DeckItem(count=card['value'], card_name=card['key']) for card in list_standing.deck_snapshot.mainboard]
                sideboard = [DeckItem(count=card['value'], card_name=card['key']) for card in list_standing.deck_snapshot.sideboard] if list_standing.deck_snapshot.sideboard else []

                decks.append(Deck(
                    player=standing.name,
                    date=tournament.date,
                    result=player_result,
                    anchor_uri=standing.decklist,
                    mainboard=mainboard,
                    sideboard=sideboard
                ))

        return CacheItem(tournament=tournament, standings=standings, rounds=rounds, decks=decks)

    def get_tournaments(self, start_date, end_date=None):
        if start_date < datetime(2020, 1, 1):
            return []
        if not end_date:
            end_date = datetime.utcnow() + timedelta(days=1)

        valid_formats = [Format.Standard, Format.Pioneer, Format.Modern, Format.Legacy, Format.Vintage, Format.Pauper]
        result = []

        while start_date < end_date:
            current_end_date = start_date + timedelta(days=7)
            print(f"\r[Topdeck] Downloading tournaments from {start_date.strftime('%Y-%m-%d')} to {current_end_date.strftime('%Y-%m-%d')}", end='')

            for format in valid_formats:
                tournaments = self.client.get_tournament_list(TopdeckTournamentRequest(
                    start=start_date.timestamp(),
                    end=current_end_date.timestamp(),
                    game=Game.MagicTheGathering,
                    format=format
                ))

                for tournament in tournaments:
                    date = datetime.utcfromtimestamp(tournament.start_date)
                    result.append(Tournament(
                        name=tournament.name,
                        date=date,
                        uri=f"https://topdeck.gg/event/{tournament.id}",
                        json_file=FilenameGenerator.generate_file_name(
                            tournament.id, tournament.name, date, format.name, [f.name for f in valid_formats], -1
                        )
                    ))

            start_date = start_date + timedelta(days=7)

        print("\r[Topdeck] Download finished")
        return result