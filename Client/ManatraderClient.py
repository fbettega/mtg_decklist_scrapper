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
import csv
from typing import List,Tuple,Dict, Optional
from urllib.parse import urljoin
from itertools import permutations,product
import copy
# import html
from dataclasses import dataclass
from models.base_model import *
from comon_tools.tools import *
# from models.Melee_model import *

# import requests
# import json
# from bs4 import BeautifulSoup
# from datetime import datetime
# from csv import DictReader
# from io import StringIO
# from collections import defaultdict

# https://www.manatraders.com/tournaments/history
class MantraderClient:
    _tournament_list_url = "https://www.manatraders.com/tournaments/2"
    _tournament_root_url = "https://www.manatraders.com"

    def get_tournaments(self):
        tournaments = []

        response = requests.get(self._tournament_list_url)
        html_content = response.text

        soup = BeautifulSoup(html_content, 'html.parser')
        tournament_list_node = soup.find("select")

        if not tournament_list_node:
            return tournaments

        for option in tournament_list_node.find_all("option"):
            date_and_format = option.text.strip()
            url = option.get("value")

            date_and_format_segments = [segment.strip() for segment in date_and_format.split("|")]
            month_and_year = date_and_format_segments[0]
            format_type = date_and_format_segments[1].capitalize()

            tournament_date = datetime.strptime(f"01 {month_and_year}", "%d %B %Y")
            tournament_date = (tournament_date.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)

            # Skip invitationals
            if tournament_date.month == 12:
                continue

            tournament_name = f"ManaTraders Series {format_type} {month_and_year}"
            tournament_uri = urljoin(self._tournament_root_url, f"{url}/")
            json_file = f"manatraders-series-{format_type.lower()}-{month_and_year.lower().replace(' ', '-')}-{tournament_date.strftime('%Y-%m-%d')}.json"

            tournaments.append(Tournament(tournament_name, tournament_date, tournament_uri, json_file))
        return tournaments


    @staticmethod
    def parse_deck_uris(root_url):
        response = requests.get(root_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        result = {}
        tables = soup.find_all('table', class_='table-tournament-rankings')
        if len(tables) < 2:
            return result

        deck_table = tables[-2]
        for row in deck_table.select('tbody tr'):
            columns = row.find_all('td')
            if len(columns) < 6:
                continue

            player_name = columns[1].text.strip().lower()
            url_link = columns[5].find('a')
            if url_link:
                result[player_name] = url_link['href']

        return result


    def parse_decks(self,csv_url, standings, deck_uris):
        response = requests.get(csv_url)
        response.raise_for_status()  # Ensure the request was successful

        # Parse CSV content
        reader = csv.DictReader(response.text.splitlines())

        player_cards = defaultdict(list)
        for row in reader:
            player_name = row['Player_Name'].strip() if row['Player_Name'].strip() else row['Player_Username'].strip()
            player_cards[player_name].append(row)
            
        result = []
        for player, cards in player_cards.items():
            # Match player names with standings, if not found, use the player name directly
            player_name = next((s.player for s in standings if s.player.lower() == player.lower()), player)
            
            # Get the corresponding deck URI from the deck_uris dictionary
            deck_uri = deck_uris.get(player_name.lower())

            # Create the mainboard and sideboard lists as DeckItem instances
            mainboard = [
                DeckItem(count=int(card['Qty']), card_name=card['Card'])
                for card in cards if card['Sideboard'] == '0'  # '0' means mainboard
            ]
            sideboard = [
                DeckItem(count=int(card['Qty']), card_name=card['Card'])
                for card in cards if card['Sideboard'] == '1'  # '1' means sideboard
            ]

            result.append(
                Deck(
                    date=None,  # You can add date logic here if applicable
                    player=player_name,
                    result="",  # Add result if necessary
                    anchor_uri=deck_uri,
                    mainboard=mainboard,
                    sideboard=sideboard
                )
                )

        return result

    @staticmethod
    def parse_standings(standings_url):
        response = requests.get(standings_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        standings_table = soup.find('table', class_='table-tournament-rankings')
        if not standings_table:
            return []

        standings = []
        for row in standings_table.select('tbody tr'):
            columns = row.find_all('td')
            rank = int(columns[0].text.strip())
            player = columns[1].text.strip()
            points = int(columns[2].text.strip())
            omwp = float(columns[5].text.strip('%')) / 100
            gwp = float(columns[6].text.strip('%')) / 100
            ogwp = float(columns[7].text.strip('%')) / 100

            nb_game ,wins, losses = map(int, columns[3].text.strip().split('/'))


            standings.append(Standing(
                    rank=rank,
                    player=player,
                    points=points,
                    wins=wins,
                    losses=losses,
                    draws= nb_game - (wins + losses),  # Si nécessaire, ajustez ce champ
                    omwp=omwp,
                    gwp=gwp,
                    ogwp=ogwp
                ))


        return standings


    def parse_bracket(self,bracket_url,standings:Standing):
        response = requests.get(bracket_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        rounds = []
        round_items = []

        for bracket_node in soup.select('.tournament-brackets ul li'):
            players = [div.text for div in bracket_node.select('div:first-child')]
            wins = [int(div.text) if div.text.isdigit() else 0 for div in bracket_node.select('div:last-child')]
            if players[1].strip() == "-":
                continue
            if players[1].strip()== players[2].strip():
                continue
            if wins[0] > wins[2]:
                round_items.append(RoundItem(players[1], players[2], f"{wins[0]}-{wins[2]}-{wins[1]}"))
            else:
                round_items.append(RoundItem(players[2], players[1], f"{wins[2]}-{wins[0]}-{wins[1]}"))
        # ici rest a définir round name
        # You can define the round name here (this could be dynamic or based on your logic)
        if len(round_items) == 7:
            # No extra rounds
            rounds.append(Round("Quarterfinals", round_items[:4]))
            rounds.append(Round("Semifinals", round_items[4:6]))
            rounds.append(Round("Finals", round_items[6:]))
        else:
            rounds.append(Round("Quarterfinals", round_items[:4]))
            rounds.append(Round("Loser Semifinals", round_items[10:12]))
            rounds.append(Round("Semifinals", round_items[4:6]))
            rounds.append(Round("Match for 7th and 8th places", round_items[15:16]))
            rounds.append(Round("Match for 5th and 6th places", round_items[12:13]))
            rounds.append(Round("Match for 3rd and 4th places", round_items[9:10]))
            rounds.append(Round("Finals", round_items[6:7]))
        bracket_rounds = [r for r in rounds if len(r.matches) > 0]
        return bracket_rounds

    def resolve_player_name(self,masked_name, standings, matched_standings, unmatched_matches):
        if masked_name is None:
            return None

        # Extraire les premiers et derniers caractères
        first_char, last_char = masked_name[0], masked_name[-1]
        # Trouver les joueurs correspondants dans standings
        matching_players = [
            standing for standing in standings
            if standing.player[0] == first_char and standing.player[-1] == last_char
            ]

        if len(matching_players) == 1:
            matched_standings.add(matching_players[0].player)  # Marquer comme apparié
            return matching_players[0].player
        else:
            # Ajouter à la liste des noms masqués non appariés
            unmatched_matches.append(masked_name)
            return masked_name



    def parse_swiss(self,swiss_url, standings):
        # Récupérer les données des matchs
        response = requests.get(swiss_url)
        data = response.json()
        # Variables pour suivre les joueurs appariés et non appariés
        matched_standings = set()
        unmatched_matches = []
        rounds = []
        for round_name, matches in data.items():
            round_items = [
                RoundItem(
                    self.resolve_player_name(match["p1"], standings, matched_standings, unmatched_matches),
                    self.resolve_player_name(match["p2"], standings, matched_standings, unmatched_matches),
                    match["res"]
                )
                for match in matches
            ]
            rounds.append(Round(round_name, round_items))


        test = self.calculate_player_stats(rounds,standings)
        # Identifier les joueurs non appariés dans standings
        unmatched_standings = [
            standing.player for standing in standings if standing.player not in matched_standings
        ]
        unmatched_standings = [
            standing for standing in standings if standing.player not in matched_standings
        ]
        return rounds
    
#test1
#########################################################################################################

    def calculate_stats_for_matches(self,matches: List[RoundItem], standings: List[Standing]):
        # Initialiser les stats
        stats = {
            "Rank": None,
            "Points": 0,
            "Wins": 0,
            "Losses": 0,
            "Draws": 0,
            "OMP": 0.0,
            "GWP": 0.0,
            "OGP": 0.0,
        }
        # Variables auxiliaires pour GWP et OGP
        total_games_played = 0
        total_games_won = 0
        opponents = set()

        # Parcourir les matchs
        player_names = {standing.player for standing in standings}

        # Parcourir les matchs
        for match in matches:
            p1_wins, p2_wins, draws = map(int, match.result.split('-'))

            # Identifier le joueur et son adversaire
            if match.player1 in player_names:
                player = match.player1
                opponent = match.player2
                player_wins, player_losses = p1_wins, p2_wins
            elif match.player2 in player_names:
                player = match.player2
                opponent = match.player1
                player_wins, player_losses = p2_wins, p1_wins
            else:
                continue  # Ignorer les matchs dont les joueurs ne sont pas dans standings

            # Calculer les victoires, défaites et égalités
            stats["Wins"] += player_wins
            stats["Losses"] += player_losses
            stats["Draws"] += draws

            # Ajouter aux points (3 pour chaque victoire, 1 pour chaque égalité)
            stats["Points"] += 3 * player_wins + draws

            # Ajouter aux jeux joués et gagnés
            total_games_played += player_wins + player_losses + draws
            total_games_won += player_wins

            # Ajouter l'adversaire à la liste
            opponents.add(opponent)

        # Calculer GWP (Game-Win Percentage)
        if total_games_played > 0:
            stats["GWP"] = total_games_won / total_games_played

        # Calculer OMP (Opponents’ Match-Win Percentage)
        opponent_match_points = 0
        opponent_total_matches = 0
        for opponent in opponents:
            opponent_standing = next((s for s in standings if s.player == opponent), None)
            if opponent_standing:
                opponent_match_points += opponent_standing.points
                opponent_total_matches += 3 * len(matches)  # Nombre de rounds (approximé ici)

        if opponent_total_matches > 0:
            stats["OMP"] = opponent_match_points / opponent_total_matches

        # Calculer OGP (Opponents’ Game-Win Percentage)
        opponent_game_wins = 0
        opponent_game_total = 0
        for opponent in opponents:
            opponent_standing = next((s for s in standings if s.player == opponent), None)
            if opponent_standing:
                opponent_game_wins += opponent_standing.wins
                opponent_game_total += opponent_standing.wins + opponent_standing.losses + opponent_standing.draws

        if opponent_game_total > 0:
            stats["OGP"] = opponent_game_wins / opponent_game_total

        # Calculer le rang du joueur en fonction des points
        standings_with_updated_points = sorted(
            standings + [Standing(player=player, points=stats["Points"])],
            key=lambda s: s.points,
            reverse=True,
        )
        stats["Rank"] = next(
            (i + 1 for i, s in enumerate(standings_with_updated_points) if s.player == player),
            None,
        )
        return stats
    

    def calculate_player_stats(self, rounds: List[Round], standings: List[Standing]) -> Tuple[Dict[str, List[Dict]], List[str], List[str]]: 
            # Étape 1 : Mapper les noms masqués aux joueurs réels
            masked_to_actual = defaultdict(list)
            for standing in standings:
                if standing.player:
                    masked_name = f"{standing.player[0]}{'*' * 10}{standing.player[-1]}"
                    masked_to_actual[masked_name].append(standing.player)
            # Étape 3 : Identifier les joueurs dupliqués (nom masqué avec plusieurs joueurs réels)
            duplicated_masked_names = {masked for masked, actuals in masked_to_actual.items() if len(actuals) > 1}
            
            # Étape 4 : Collecter les matchs impliquant des noms masqués dupliqués
            masked_matches = defaultdict(list)  # masked_name -> list of (role, round_name, match)
            for masked in duplicated_masked_names:
                for rnd in rounds:
                    for match in rnd.matches:
                        if match.player1 == masked:
                            masked_matches[masked].append(('player1', rnd.round_name, match))
                        if match.player2 == masked:
                            masked_matches[masked].append(('player2', rnd.round_name, match))

            # Étape 5 : Générer toutes les combinaisons possibles d'assignations pour chaque joueur dupliqué
            assignments_per_masked = {}
            for masked, matches_info in masked_matches.items():
                actual_players = masked_to_actual[masked]
                per_round_assignments = []  # Contient les combinaisons possibles par round
                # Organiser les matchs par round
                matches_by_round = defaultdict(list)
                for role, round_name, match in matches_info:
                    matches_by_round[round_name].append((role, match))

                # Générer les permutations pour chaque round
                for round_name, matches in matches_by_round.items():
                    round_combinations = []
                    for match_info in matches:
                        role, match = match_info

                        # Créer toutes les permutations en remplaçant le joueur masqué
                        for player in actual_players:
                            # Copier le match pour éviter d'écraser les données originales
                            new_match = RoundItem(
                                player1=match.player1 if role != 'player1' else player,
                                player2=match.player2 if role != 'player2' else player,
                                result=match.result,
                            )
                            round_combinations.append(new_match)
                    # Ajouter les combinaisons de ce round aux résultats globaux
                    per_round_assignments.append(round_combinations)
                # Générer toutes les combinaisons possibles entre les rounds
                assignments_per_masked[masked] = list(product(*per_round_assignments))

            recalculated_stats = {}
            for masked_name, match_combinations in assignments_per_masked.items():
                player_stats_for_combinations = []

                for combination in match_combinations:
                    # Chaque combination est une liste de RoundItem correspondant aux 9 rounds.
                    all_matches = list(combination)  # Extraire directement les RoundItem de la combinaison.

                    # Recalculer les statistiques pour ces matchs
                    stats = self.calculate_stats_for_matches(all_matches, standings)

                    # Ajouter les statistiques recalculées aux résultats
                    player_stats_for_combinations.append(stats)

                # Stocker les statistiques recalculées pour ce joueur masqué
                recalculated_stats[masked_name] = player_stats_for_combinations




class TournamentList:
    _csv_root = "https://www.manatraders.com/tournaments/download_csv_by_month_and_year?month={month}&year={year}"
    _swiss_root = "https://www.manatraders.com/tournaments/swiss_json_by_month_and_year?month={month}&year={year}"


    def get_tournament_details(self,tournament):
        client = MantraderClient()
        csv_url = self._csv_root.format(month=tournament.date.month, year=tournament.date.year)
        swiss_url = self._swiss_root.format(month=tournament.date.month, year=tournament.date.year)
        standings_url = f"{tournament.uri}swiss"
        bracket_url = f"{tournament.uri}finals"
        standings = client.parse_standings(standings_url)

        deck_uris = client.parse_deck_uris(tournament.uri)
        decks = client.parse_decks(csv_url, standings, deck_uris)
        bracket = client.parse_bracket(bracket_url,standings)
        swiss = client.parse_swiss(swiss_url,standings)

        rounds = swiss + bracket
        decks = OrderNormalizer.reorder_decks(decks, standings, bracket,True)
# for r in bracket:
#     for m in r.matches:
#         print(m)
# for d in decks:
#     print(d)
# for s in standings:
#         print(s)

        return CacheItem(
            tournament=tournament,
            decks=decks,
            standings=standings,
            rounds=rounds
        )

    


    def DL_tournaments(start_date: datetime, end_date: datetime = None) -> List[dict]:
        tournaments = MantraderClient.get_tournaments()
        filtered_tournaments = [t for t in tournaments if t.date >= start_date]
        if end_date:
            filtered_tournaments = [t for t in filtered_tournaments if t.date <= end_date]
        return filtered_tournaments
    
@dataclass
class ManaTradersCsvRecord:
    count: int  # Correspond à la propriété Count
    card: str   # Correspond à la propriété Card
    sideboard: bool  # Correspond à la propriété Sideboard
    player: str  # Correspond à la propriété Player