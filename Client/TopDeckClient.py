
import os
import json
from datetime import datetime, timedelta, timezone
import requests
import time
from threading import Lock
import math 
from models.base_model import *
from models.Topdeck_model import *
from comon_tools.tools import *




class MissingApiKeyException(Exception):
    def __init__(self):
        super().__init__(f"Could not load API key from environment variable {TopDeckConstants.Settings.API_KEY_ENV_VAR}")


class TopdeckClient:
    def __init__(self):
        self._api_key = TopDeckConstants.Settings.get_api_key()
        self._call_timestamps = []  # Liste pour stocker les horodatages des appels
        self._lock = Lock()         # Verrou pour sécuriser les accès multi-threads
        if not self._api_key:
            raise MissingApiKeyException()

    def _response_to_json(self, response: requests.models.Response):
        """
        Gère la réponse HTTP : vérifie le code de statut et tente de désérialiser le JSON.
        :param response: Réponse HTTP à traiter.
        :return: Données JSON désérialisées.
        :raises ValueError: Si le code de statut n'est pas 200 ou si le décodage JSON échoue.
        """
        # Vérifiez le code HTTP
        if response.status_code != 200:
            raise ValueError(f"Erreur lors de la récupération des données : {response.status_code}, {response.text}")
        
        # Assurez-vous que la réponse est bien un JSON
        try:
            server_data = response.json()  # Désérialise automatiquement en liste ou dict
        except json.JSONDecodeError as e:
            raise ValueError(f"Erreur lors du décodage JSON : {e}, réponse : {response.text}")
        
        return server_data

    def get_tournament_list(self, request):
        """
        Récupère la liste des tournois.
        :param request: Requête de tournoi (TopdeckTournamentRequest).
        :return: Liste des tournois (TopdeckListTournament).
        """
        response = self._get_client().post(TopDeckConstants.Routes.TOURNAMENT_ROUTE, json=request.to_dict())
        server_data = self._response_to_json(response)
        return self._normalize_array_result(TopdeckListTournament, server_data)

    def get_tournament(self, tournament_id):
        """
        Récupère un tournoi par son ID.
        :param tournament_id: Identifiant du tournoi.
        :return: Détails du tournoi (TopdeckTournament).
        """
        response = self._get_client().get(TopDeckConstants.Routes.FULL_TOURNAMENT_ROUTE.replace("{TID}", tournament_id))
        server_data = self._response_to_json(response)
        return self._normalize_result(TopdeckTournament, server_data)

    def get_tournament_info(self, tournament_id):
        """
        Récupère les informations d'un tournoi.
        :param tournament_id: Identifiant du tournoi.
        :return: Informations du tournoi (TopdeckTournamentInfo).
        """
        response = self._get_client().get(TopDeckConstants.Routes.TOURNAMENT_INFO_ROUTE.replace("{TID}", tournament_id))
        server_data = self._response_to_json(response)
        return self._normalize_result(TopdeckTournamentInfo, server_data)

    def get_standings(self, tournament_id):
        """
        Récupère les classements d'un tournoi.
        :param tournament_id: Identifiant du tournoi.
        :return: Classements du tournoi (TopdeckStanding).
        """
        response = self._get_client().get(TopDeckConstants.Routes.STANDINGS_ROUTE.replace("{TID}", tournament_id))
        server_data = self._response_to_json(response)
        return self._normalize_array_result(TopdeckStanding, server_data)

    def get_rounds(self, tournament_id):
        """
        Récupère les rondes d'un tournoi.
        :param tournament_id: Identifiant du tournoi.
        :return: Rondes du tournoi (TopdeckRound).
        """
        response = self._get_client().get(TopDeckConstants.Routes.ROUNDS_ROUTE.replace("{TID}", tournament_id))
        # Vérifiez le code HTTP
        server_data = self._response_to_json(response)
        return self._normalize_array_result(TopdeckRound, server_data)

    def _get_client(self):
        """
        Crée un client HTTP pour effectuer les requêtes, en respectant une limite de 200 appels par minute.
        :return: Client HTTP configuré.
        """
        with self._lock:  # Protège l'accès à _call_timestamps
            current_time = time.time()
            one_minute_ago = current_time - 60

            # Filtrer les horodatages pour conserver seulement ceux de la dernière minute
            self._call_timestamps = [timestamp for timestamp in self._call_timestamps if timestamp > one_minute_ago]

            # Vérifier si on dépasse la limite de 200 appels
            if len(self._call_timestamps) >= 200:
                sleep_time = math.ceil(60 - (current_time - self._call_timestamps[0]))  # Temps restant jusqu'à la prochaine disponibilité arrondie a au moins une seconde
                print(f"Limite d'appels atteinte. Pause de {sleep_time:.2f} secondes...")
                time.sleep(sleep_time)

            # Ajouter l'horodatage de l'appel actuel
            self._call_timestamps.append(current_time)

        # Créer le client HTTP
        session = requests.Session()
        session.headers.update({
            "Authorization": self._api_key,
            "Content-Type": "application/json; charset=utf-8"
        })
        return session

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
        # Assurez-vous que json_data est une liste
        if not isinstance(json_data, list):
            raise ValueError("Les données JSON doivent être une liste.")
        results = [cls.from_json(item) for item in json_data]

        # a = results[0].standings[1]
        # a.deckSnapshot
        for result in results:
            result.normalize()
        return results
    
###########################################################################################################################################
# TournamentList

class TournamentList:
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
            columns=[TopDeckConstants.PlayerColumn.Name.value, TopDeckConstants.PlayerColumn.Wins.value, TopDeckConstants.PlayerColumn.Losses.value, TopDeckConstants.PlayerColumn.Draws.value, TopDeckConstants.PlayerColumn.DeckSnapshot.value]
        ))[0]  

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
                points=standing.points,
                wins=list_standing.wins if list_standing else 0,
                losses=list_standing.losses if list_standing else 0,
                draws=list_standing.draws if list_standing else 0,
                gwp=standing.game_win_rate,
                omwp=standing.opponent_win_rate,
                ogwp=standing.opponent_game_win_rate
            ))

        decks = []
        CardNameNormalizer.initialize()
        for standing in tournament_data.standings:
            list_standing = next((s for s in tournament_data_from_list.standings if s.name == standing.name), None)

            if list_standing and list_standing.deckSnapshot and list_standing.deckSnapshot.mainboard:
                player_result = f"{standing.standing}th Place" if standing.standing > 3 else f"{standing.standing}st Place"  # or nd, rd depending on the rank
                
                mainboard = [DeckItem(count=value, card_name=CardNameNormalizer.normalize(key)) for key, value in list_standing.deckSnapshot.mainboard.items()] if list_standing.deckSnapshot.mainboard else []
                sideboard = [DeckItem(count=value, card_name=CardNameNormalizer.normalize(key)) for key, value in list_standing.deckSnapshot.sideboard.items()] if list_standing.deckSnapshot.sideboard else []
                decks.append(Deck(
                    player=standing.name,
                    date=tournament.date,
                    result=player_result,
                    anchor_uri=standing.decklist,
                    mainboard=mainboard,
                    sideboard=sideboard
                ))
        return CacheItem(tournament=tournament, standings=standings, rounds=rounds, decks=decks)

    def DL_tournaments(start_date: datetime, end_date: datetime = None) -> List[dict]:
        if start_date < datetime(2020, 1, 1, tzinfo=timezone.utc):
            return []  # Si la date de départ est avant le 1er janvier 2020, retourner une liste vide.
        if end_date is None:
            end_date = datetime.now(timezone.utc) + timedelta(days=1)
        valid_formats = [TopDeckConstants.Format.Standard.value,
                        TopDeckConstants.Format.Pioneer.value,
                        TopDeckConstants.Format.Modern.value,
                        TopDeckConstants.Format.Legacy.value,
                        TopDeckConstants.Format.Vintage.value,
                        TopDeckConstants.Format.Pauper.value,
                        TopDeckConstants.Format.DuelCommander.value,
                        TopDeckConstants.Format.Premodern.value
                        ]
        client = TopdeckClient()
        result = []
        while start_date < end_date:
            current_end_date = start_date + timedelta(days=7)
            print(f"\r[Topdeck] Downloading tournaments from {start_date.strftime('%Y-%m-%d')} to {current_end_date.strftime('%Y-%m-%d')}", end='')

            for format in valid_formats:
                tournaments = client.get_tournament_list(TopdeckTournamentRequest(
                    start= start_date.timestamp(),
                    end= current_end_date.timestamp(),
                    game= TopDeckConstants.Game.MagicTheGathering,
                    format=format
                ))

                for tournament in tournaments:
                    date = datetime.fromtimestamp(tournament.start_date, tz=timezone.utc)
                    result.append(Tournament(
                        name=tournament.name,
                        date=date,
                        formats=format,
                        uri=f"https://topdeck.gg/event/{tournament.id}",
                        json_file=FilenameGenerator.generate_file_name(
                            tournament.id, tournament.name, date, format, [f for f in valid_formats], -1
                        )
                    ))

            start_date = start_date + timedelta(days=7)
        print("\r[Topdeck] Download finished")
        return result