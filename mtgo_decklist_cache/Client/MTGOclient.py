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
from urllib.parse import urljoin
import os
import sys
from typing import List, Optional
import html
from dataclasses import dataclass
# from models.Melee_model import *
from models.base_model import *
from comon_tools.tools import *

##########################################################################################################################################################################
# TournamentList
class MTGOSettings:
    LIST_URL = "https://www.mtgo.com/decklists/{year}/{month}"
    ROOT_URL = "https://www.mtgo.com"
    LEAGUE_REDOWNLOAD_DAYS = 3
    @staticmethod
    def format_url(url, **params):
        return url.format(**params)



class TournamentList:  
    def increment_month(date: datetime) -> datetime:
        """Increment the month, rolling over to the next year if needed."""
        new_month = date.month + 1
        new_year = date.year
        if new_month > 12:  # If it's December, roll over to January
            new_month = 1
            new_year += 1
        return date.replace(year=new_year, month=new_month, day=1)

    def DL_tournaments(start_date: datetime, end_date: datetime = None) -> List[dict]:
        if end_date is None:
            end_date = datetime.now(timezone.utc)

        results = []
        current_date = start_date
        while current_date <= end_date:
            tournament_list_url = MTGOSettings.LIST_URL.format(
                year=current_date.year,
                month=f"{current_date.month:02}"
            )

            response = requests.get(tournament_list_url)
            if response.status_code != 200:
                current_date = TournamentList.increment_month(current_date)  # Increment to the next month
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
            tournament_nodes = soup.select("li.decklists-item")

            if not tournament_nodes:
                current_date   = TournamentList.increment_month(current_date)   # Increment by one month
                continue

            for tournament_node in tournament_nodes:
                title = tournament_node.select_one("a > div > h3").text.strip()
                url = tournament_node.select_one("a")["href"]
                date_string = tournament_node.select_one("a > time")["datetime"]

                parsed_date = datetime.fromisoformat(date_string).date()
                url = urljoin(MTGOSettings.ROOT_URL, url)

                uri = url

                results.append(Tournament(
                    name=title,
                    date=parsed_date,
                    uri=uri,
                    json_file=os.path.splitext(os.path.basename(uri))[0] + ".json",
                    force_redownload=("league" in title.lower() and
                                      (datetime.now(timezone.utc).date() - parsed_date).days < MTGOSettings.LEAGUE_REDOWNLOAD_DAYS)
                ))

            current_date  = TournamentList.increment_month(current_date)   # Move to the first day of the next month

        filtered_results = [t for t in results if start_date.date() <= t.date <= end_date.date()]
        return sorted(filtered_results, key=lambda t: t.date, reverse=True)

    def get_tournament_details(self,  tournament: Tournament) -> 'CacheItem':
        """
        Récupère les détails d'un tournoi en téléchargeant et analysant les données JSON intégrées dans la page HTML.
        :param tournament: Instance de Tournament.
        :return: Un dictionnaire contenant les détails du tournoi ou None si une erreur se produit.
        """
        response = requests.get(tournament.uri)
        if response.status_code != 200:
            return None
        html_content = response.text
        html_rows = [line.strip() for line in html_content.splitlines()]

        # Trouver la ligne contenant les données JSON
        data_row = next(
            (line for line in html_rows if line.startswith("window.MTGO.decklists.data = ")),
            None
        )
        if not data_row:
            return None
        # Extraire la partie JSON
        json_data = data_row[29:-1]  # Skip 29 caractères initiaux et retirer le dernier caractère (point-virgule)
        event_json = json.loads(json_data)
        # Vérification des erreurs dans les données JSON
        if "errorCode" in event_json and event_json["errorCode"] == "SERVER_ERROR":
            return None
        # Déterminer le type d'événement
        event_type = "tournament" if "starttime" in event_json else "league"
        # Traiter les données pour un tournoi
        winloss = TournamentLoader.parse_winloss(event_json) if event_type == "tournament" else None
        standings = TournamentLoader.parse_standing(event_json, winloss) if event_type == "tournament" else None
        bracket = TournamentLoader.parse_bracket(event_json) if event_type == "tournament" else None
        # Parser les decks
        decks = TournamentLoader.parse_decks(tournament, event_type, winloss, event_json)
        # Réorganiser les decks si nécessaire
        if standings:
            decks = OrderNormalizer.reorder_decks(decks, standings, bracket, bracket is not None)
        return CacheItem(
                tournament=tournament,
                decks=decks,
                rounds=bracket,
                standings=standings
                )

##########################################################################################################################################################################
# TournamentLoader
class TournamentLoader:
    def parse_event_date(event_date_str):
    # Essayer le format "%Y-%m-%d %H:%M:%S.%f"
        try:
            return datetime.strptime(event_date_str, "%Y-%m-%d %H:%M:%S.%f")
        # Si ça échoue, essayer le format "%Y-%m-%d"
        except ValueError:
            return datetime.strptime(event_date_str, "%Y-%m-%d")

    def parse_winloss(event_json):
        """
        Parse les données de victoires/défaites pour chaque joueur à partir du JSON.
        :param event_json: Dictionnaire des données JSON de l'événement.
        :return: Un dictionnaire des résultats de victoires/défaites par joueur ou None si aucune donnée n'est trouvée.
        """
        if "winloss" not in event_json:
            return None

        player_winloss = {}
        for winloss in event_json["winloss"]:
            player_id = winloss["loginid"]
            wins = winloss["wins"]
            losses = winloss["losses"]
            player_winloss[player_id] = f"{wins}-{losses}"

        return player_winloss if player_winloss else None
    
    def parse_decks(tournament, event_type, winloss, event_json):
        """
        Analyse les decks d'un tournoi à partir des données JSON.
        
        :param tournament: Instance de Tournament.
        :param event_type: Type d'événement ('league' ou 'tournament').
        :param winloss: Dictionnaire des résultats (victoires/défaites) des joueurs.
        :param event_json: Données JSON de l'événement.
        :return: Liste de Decks ou None si aucune donnée n'est disponible.
        """
        # Déterminer la date de l'événement
        event_date_str = event_json.get("publish_date") if event_type == "league" else event_json.get("starttime")
        # Convertir cette chaîne en un objet datetime sans fuseau horaire
        event_date_naive = TournamentLoader.parse_event_date(event_date_str)
        event_date = event_date_naive.replace(tzinfo=timezone.utc)

        # Ajouter un fuseau horaire UTC à l'objet datetime
        # Vérifier si les données de decklists existent
        if "decklists" not in event_json:
            return None

        added_players = set()
        decks = []
        rank = 1

        # deck = event_json["decklists"][0]

        for deck in event_json["decklists"]:
            mainboard = []
            sideboard = []
            player = deck.get("player")
            player_id = deck.get("loginid")

            # Traiter le mainboard
            for card in deck.get("main_deck", []):
                name = card["card_attributes"]["card_name"]
                quantity = int(card["qty"]) 
                name = CardNameNormalizer.normalize(name)
                mainboard.append(DeckItem(count=quantity, card_name=name))

            # Traiter le sideboard
            for card in deck.get("sideboard_deck", []):
                name = card["card_attributes"]["card_name"]
                quantity = int(card["qty"]) 
                name = CardNameNormalizer.normalize(name)
                sideboard.append(DeckItem(count=quantity, card_name=name))

            # Déterminer le résultat du joueur
            result = ""
            if event_type == "league":
                # Résultats pour une league
                wins = deck.get("wins", {}).get("wins", "0")
                result = {
                    "5": "5-0",
                    "4": "4-1",
                    "3": "3-2",
                    "2": "2-4",
                    "1": "1-4",
                    "0": "0-5"
                }.get(wins, "")
            else:
                if winloss:
                    # Résultats pour un Prelim
                    result = winloss.get(player_id, "")
                else:
                    # Résultats pour un Challenge
                    if rank == 1:
                        result = "1st Place"
                    elif rank == 2:
                        result = "2nd Place"
                    elif rank == 3:
                        result = "3rd Place"
                    else:
                        result = f"{rank}th Place"
                    rank += 1

            # Normaliser et ajouter le deck

            deck_ite = DeckNormalizer.normalize(Deck(
                        date=event_date,
                        player=player,
                        result=result,
                        anchor_uri=f"{tournament.uri}#deck_{player}",
                        mainboard=mainboard,
                        sideboard=sideboard
                    ))
            decks.append(deck_ite)
            added_players.add(player)
        return decks if decks else None
    
    def parse_standing(json_data, winloss):
        """
        Analyse les standings d'un tournoi.

        :param json_data: Données JSON de l'événement.
        :param winloss: Dictionnaire des victoires/défaites des joueurs.
        :return: Liste de standings triés ou None.
        """
        if "standings" not in json_data:
            return None

        standings = []

        for standing in json_data["standings"]:
            player: str = standing["login_name"]
            player_id: int = int(standing["loginid"])  # Conversion en entier
            points: int = int(standing["score"])  # Conversion en entier
            rank: int = int(standing["rank"])  # Conversion en entier
            gwp: float = float(standing["gamewinpercentage"])  # Conversion en flottant
            ogwp: float = float(standing["opponentgamewinpercentage"])  # Conversion en flottant
            omwp: float = float(standing["opponentmatchwinpercentage"]) 

            wins = 0
            losses = 0
            if player_id in winloss:
                win_loss = winloss[player_id].split("-")
                wins = int(win_loss[0])
                losses = int(win_loss[1])

            standings.append(Standing(
                rank=rank,
                player=player,
                points=points,
                wins=wins,
                losses=losses,
                draws=0,  # Si nécessaire, ajustez ce champ
                omwp=omwp,
                gwp=gwp,
                ogwp=ogwp
            ))
        # Tri des standings par le rank
        return sorted(standings, key=lambda s: s.rank) if standings else None
    
    def parse_bracket(json_data):
        """
        Analyse les brackets d'un tournoi.

        :param json_data: Données JSON de l'événement.
        :return: Liste des rounds triés ou None.
        """
        if "brackets" not in json_data:
            return Noned
        # brackets = []
        rounds = []       
        for bracket in json_data["brackets"]:
            matches = []

            for match in bracket["matches"]:
                player1 = match["players"][0]["player"]
                player2 = match["players"][1]["player"]
                player1_wins = match["players"][0]["wins"]
                player2_wins = match["players"][1]["wins"]
                reverse_order = match["players"][1]["winner"]

                if reverse_order:
                    matches.append(RoundItem(
                            player1=player2,
                            player2=player1,
                            result=f"{player2_wins}-{player1_wins}-0"
                        ))
                else:
                    matches.append(RoundItem(
                        player1=player1,
                        player2=player2,
                        result=f"{player1_wins}-{player2_wins}-0"
                    ))

            round_name = "Quarterfinals"
            if len(matches) == 2:
                round_name = "Semifinals"
            if len(matches) == 1:
                round_name = "Finals"

            rounds.append(
                Round(
                    round_name=round_name,
                    matches=matches
                    ))

        valid_brackets = [r for r in rounds if r.round_name in {"Quarterfinals", "Semifinals", "Finals"}]
        return valid_brackets if valid_brackets else None