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
import sys
import csv
from typing import List,Tuple,Dict, DefaultDict,Optional
from urllib.parse import urljoin
from itertools import permutations,product
import copy
import numpy as np
from multiprocessing import Pool, cpu_count
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

def validate_permutation(perm, dict_standings, player_indices, standings_wins, standings_losses, n_players):
    """Valider une permutation donnée."""
    wins = np.zeros(n_players, dtype=int)
    losses = np.zeros(n_players, dtype=int)
    rounds_played = np.zeros(n_players, dtype=int)

    for round_data in perm:
        for player, round_items in round_data.items():
            player_idx = player_indices[player]
            for round_item in round_items:
                p1_wins, p2_wins, _ = map(int, round_item.result.split('-'))
                rounds_played[player_idx] += 1

                if round_item.player1 == player:
                    wins[player_idx] += int(p1_wins > p2_wins)
                    losses[player_idx] += int(p1_wins < p2_wins)
                elif round_item.player2 == player:
                    wins[player_idx] += int(p2_wins > p1_wins)
                    losses[player_idx] += int(p2_wins < p1_wins)

    # Validation vectorisée
    if np.any(wins > standings_wins) or np.any(losses > standings_losses):
        return False
    if np.any(rounds_played > (standings_wins + standings_losses)):
        return False
    return True


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



    def parse_swiss(self,swiss_url, standings,bracket):
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

        if unmatched_matches:
            rounds = Manatrader_fix_hidden_duplicate_name().Find_name_form_player_stats(rounds,standings,bracket)


        return rounds
    


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
        swiss = client.parse_swiss(swiss_url,standings,bracket)

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



class Manatrader_fix_hidden_duplicate_name: 

    def calculate_stats_for_matches(self, player: str, matches: List[RoundItem], standings: List[Standing]):
        # Initialiser les stats
        points = 0
        wins = 0
        losses = 0
        draws = 0
        total_games_played = 0
        total_games_won = 0
        opponents = set()

        # Variables auxiliaires pour GWP et OGP
        player_names = {standing.player for standing in standings}

        # Parcourir les matchs
        for match in matches:
            p1_wins, p2_wins, draws_ = map(int, match.result.split('-'))

            # Identifier l'adversaire
            if match.player1 == player:
                opponent = match.player2
                player_wins, player_losses = p1_wins, p2_wins
            elif match.player2 == player:
                opponent = match.player1
                player_wins, player_losses = p2_wins, p1_wins
            else:
                continue  # Ignorer les matchs où le joueur n'est pas impliqué

            # Calculer les victoires, défaites et égalités
        # Mise à jour des statistiques
            # total_matches += 1
            if player_wins > player_losses:
                wins += 1
            elif player_wins < player_losses:
                losses += 1
            else:
                draws += 1

            

            # Ajouter aux jeux joués et gagnés
            total_games_played += player_wins + player_losses + draws
            total_games_won += player_wins

            # Ajouter l'adversaire à la liste
            opponents.add(opponent)
        # Ajouter aux points (3 pour chaque victoire, 1 pour chaque égalité)
        points += 3 * wins + draws
        # Calculer GWP (Game-Win Percentage)
        gwp = total_games_won / total_games_played if total_games_played > 0 else 0.33

        # Calculer OMP (Opponents’ Match-Win Percentage)
        opponent_match_points = 0
        opponent_total_matches = 0
        for opponent in opponents:
            opponent_standing = next((s for s in standings if s.player == opponent), None)
            if opponent_standing:
                opponent_match_points += opponent_standing.points
                opponent_total_matches += 3 * len(matches)  # Nombre de rounds (approximé ici)

        omwp = opponent_match_points / opponent_total_matches if opponent_total_matches > 0 else 0.33

        # Calculer OGP (Opponents’ Game-Win Percentage)
        opponent_game_wins = 0
        opponent_game_total = 0
        for opponent in opponents:
            opponent_standing = next((s for s in standings if s.player == opponent), None)
            if opponent_standing:
                opponent_game_wins += opponent_standing.wins
                opponent_game_total += opponent_standing.wins + opponent_standing.losses + opponent_standing.draws

        ogwp = opponent_game_wins / opponent_game_total if opponent_game_total > 0 else 0.33
        
        # Calculer le rang du joueur en fonction des points
        standings_with_updated_points = sorted(
            standings + [Standing(player=player, points=points)],
            key=lambda s: s.points,
            reverse=True,
        )
        rank = next(
            (i + 1 for i, s in enumerate(standings_with_updated_points) if s.player == player),
            None,
        )
        # Créer et retourner l'objet Standing avec les valeurs calculées
        return Standing(
            rank=rank,  # Le classement est optionnel ici
            player=player,
            points=points,
            wins=wins,
            losses=losses,
            draws=draws,
            omwp=omwp,
            gwp=gwp,
            ogwp=ogwp
        )
    
    def calculate_recalculated_stats(self,assignments_per_masked: Dict[str, List[Tuple[DefaultDict[str, List[RoundItem]]]]], standings: List[Standing]) -> Dict[str, List[Dict[str, Dict]]]:
# j'en suis ici il y a au moins 2 problème adapté calculate_stats_for_matches pour qu'il prenne l'ensemble des match d'un joueurs et lui passer l'ensemble des matchs
    # Dictionnaire pour stocker les statistiques recalculées
        recalculated_stats = {}
        # Accès rapide aux standings réels par joueur
        real_standings_by_player = {standing.player: standing for standing in standings}

        # Parcourir les joueurs masqués et leurs combinaisons
        for masked_name, match_combinations in assignments_per_masked.items():
            player_stats_for_combinations = []  # Liste pour stocker les stats de chaque combinaison

            # Parcourir chaque combinaison de matchs
            for combination in match_combinations:
                # Regrouper tous les matchs (RoundItems) pour chaque joueur dans cette combinaison
                aggregated_matches = defaultdict(list)

                for player_dict in combination:
                    for player, matches in player_dict.items():
                        # Ajouter les matchs de ce dictionnaire au groupe de ce joueur
                        aggregated_matches[player].extend(matches)

                # Calculer les statistiques pour chaque joueur avec tous leurs matchs agrégés
                stats_for_combination = {}
                for player, matches in aggregated_matches.items():
                    # Vérifier si le joueur existe dans les standings
                    player_standing = real_standings_by_player.get(player)
                    if player_standing:
                        # Passer tous les matchs agrégés pour ce joueur
                        stats = self.calculate_stats_for_matches(player, matches, standings)
                        stats_for_combination[player] = stats

                # Ajouter les statistiques pour cette combinaison
                player_stats_for_combinations.append(stats_for_combination)

            # Stocker les statistiques recalculées pour ce joueur masqué
            recalculated_stats[masked_name] = player_stats_for_combinations
        return recalculated_stats

    def collect_matches_for_duplicated_masked_names(self, duplicated_masked_names,rounds):
        """Étape 4 : Collecter les matchs impliquant des noms masqués dupliqués."""
        masked_matches = defaultdict(list)
        for masked in duplicated_masked_names:
            for rnd in rounds:
                for match in rnd.matches:
                    if match.player1 == masked:
                        masked_matches[masked].append(('player1', rnd.round_name, match))
                    if match.player2 == masked:
                        masked_matches[masked].append(('player2', rnd.round_name, match))
        return masked_matches



    def map_masked_to_actual(self, standings: List[Standing], rounds: List[Round]):
        """Étape 1 : Mapper les noms masqués aux joueurs réels, en considérant uniquement les joueurs des rounds au format spécifique."""
        masked_to_actual = defaultdict(list)

            # Définir un pattern regex pour les noms au format valide
        masked_pattern = re.compile(r'^.\*{10}.$')

        # Collecter les joueurs des rounds qui ont un format valide (premier caractère, 10 *, dernier caractère)
        valid_masked_players = set()
        for rnd in rounds:
            for match in rnd.matches:
                for player in [match.player1, match.player2]:
                    if player and masked_pattern.match(player):
                        valid_masked_players.add(player)

        # Mapper uniquement les joueurs valides des standings
        for standing in standings:
            if standing.player:
                masked_name = f"{standing.player[0]}{'*' * 10}{standing.player[-1]}"
                if masked_name in valid_masked_players:
                    masked_to_actual[masked_name].append(standing.player)

        return masked_to_actual


    def generate_round_combinations(self, matches, actual_players, standings,round_name):
        """Générer les permutations pour chaque round en tenant compte du nombre de matchs du joueur."""
        round_combinations = []
        # Calculer le nombre total de matchs pour chaque joueur
        # Convertir standings en un dictionnaire, où la clé est le nom du joueur
        standings_dict = {standing.player: standing for standing in standings}

        # Calculer le nombre total de matchs pour chaque joueur
        player_match_count = {player: standings_dict[player].wins + standings_dict[player].losses for player in actual_players}
        player_wins = {player: standings_dict[player].wins for player in actual_players}
        player_losses = {player: standings_dict[player].losses for player in actual_players}
        # Analyser les résultats des matchs pour mettre à jour les victoires et défaites des joueurs
            # Étendre les joueurs pour correspondre au nombre de matchs

        for perm in permutations(actual_players, len(matches)):
            replaced_matches = defaultdict(list)
            # valid_combination = True
            # temp_player_wins = {player: 0 for player in actual_players}
            # temp_player_losses = {player: 0 for player in actual_players}
            # match_round = int(round_name.replace('Round ', ''))
            for (role, match), player in zip(matches, perm):
                # Si un joueur a plus de matchs que le round actuel lui permet, la permutation est invalide
                # if player_match_count[player] < match_round:
                #     # print(f"Permutation invalide pour {player} au round {match_round}. Nombre de matchs restants: {player_match_count[player]}")
                #     valid_combination = False
                #     break
                new_match = RoundItem(
                    player1=match.player1 if role != 'player1' else player,
                    player2=match.player2 if role != 'player2' else player,
                    result=match.result,
                )
                replaced_matches[player].append(new_match)
            round_combinations.append(replaced_matches)
            # if valid_combination:
            #     round_combinations.append(replaced_matches)

        return round_combinations

    def organize_matches_by_round(self, matches_info):
        """Organiser les matchs par round."""
        matches_by_round = defaultdict(list)
        for role, round_name, match in matches_info:
            matches_by_round[round_name].append((role, match))
        return matches_by_round

    # def generate_assignments(self, masked_matches, masked_to_actual,standings):
    #     """Étape 5 : Générer toutes les combinaisons possibles d'assignations pour chaque joueur dupliqué."""
    #     def custom_rule(perm,standings):             
    #         # Parcours de chaque niveau dans perm
    #         player_stats = defaultdict(lambda: {"rounds_played": 0, "wins": 0, "losses": 0})
    #         # Parcours des données de perm
    #         for round_data in perm:
    #             for player, round_items in round_data.items():
    #                 for round_item in round_items:
    #                     p1_wins, p2_wins, _ = map(int, round_item.result.split('-'))
    #                     player_stats[player]["rounds_played"] += 1

    #                     # Validation des rounds joués
    #                     max_rounds = standings[player]["wins"] + standings[player]["losses"]
    #                     if player_stats[player]["rounds_played"] > max_rounds:
    #                         return False

    #                     # Mise à jour des victoires et défaites
    #                     if round_item.player1 == player:
    #                         player_stats[player]["wins"] += int(p1_wins > p2_wins)
    #                         player_stats[player]["losses"] += int(p1_wins < p2_wins)
    #                     elif round_item.player2 == player:
    #                         player_stats[player]["wins"] += int(p2_wins > p1_wins)
    #                         player_stats[player]["losses"] += int(p2_wins < p1_wins)

    #                     # Validation des statistiques
    #                     if (player_stats[player]["wins"] > standings[player]["wins"] or
    #                         player_stats[player]["losses"] > standings[player]["losses"]):
    #                         return False

    #         return True
        
    #     assignments_per_masked = {}
    #     dict_standings = self.standings_to_dict(standings)
    #     for masked, matches_info in masked_matches.items():
    #         if masked == '_**********_':
    #             actual_players = masked_to_actual[masked]
    #             per_round_assignments = []
    #             matches_by_round = self.organize_matches_by_round(matches_info)
    #             for round_name, matches in matches_by_round.items():
    #                 round_combinations = self.generate_round_combinations(matches, actual_players,standings,round_name)
    #                 per_round_assignments.append(round_combinations)
    #                 # Générer toutes les combinaisons possibles entre les rounds
    #             per_round_assignments_non_empty = [item for item in per_round_assignments if item]
    #             # assignments_per_masked[masked] = list(product(*per_round_assignments_non_empty))
    #             assignments_per_masked[masked] = list((perm for perm in product(*per_round_assignments_non_empty) if custom_rule(perm,dict_standings)))

    #     return assignments_per_masked

    def generate_assignments(self, masked_matches, masked_to_actual, standings):
        """Optimiser la génération des assignments avec multiprocessing."""
        dict_standings = self.standings_to_dict(standings)
        assignments_per_masked = {}



        for masked, matches_info in masked_matches.items():
        # if masked == '_**********_':
            actual_players = masked_to_actual[masked]
            matches_by_round = self.organize_matches_by_round(matches_info)

            # Préparer les données
            player_indices = {player: idx for idx, player in enumerate(actual_players)}
            n_players = len(actual_players)
            standings_wins = np.array([dict_standings[player]["wins"] for player in actual_players])
            standings_losses = np.array([dict_standings[player]["losses"] for player in actual_players])

            # Fonction génératrice pour les combinaisons de rounds
            def generate_valid_combinations():
                for round_name, matches in matches_by_round.items():
                    round_combinations = self.generate_round_combinations(matches, actual_players, standings, round_name)
                    if round_combinations:
                        yield round_combinations

            # Créer un générateur pour les permutations
            permutations = product(*generate_valid_combinations())

            # Diviser les permutations en lots pour multiprocessing
            def chunked_iterable(iterable, chunk_size):
                """Diviser un itérable en morceaux de taille chunk_size."""
                chunk = []
                for item in iterable:
                    chunk.append(item)
                    if len(chunk) == chunk_size:
                        yield chunk
                        chunk = []
                if chunk:
                    yield chunk

            # Valider les permutations en parallèle
            chunk_size = 100000  # Ajustez la taille des lots selon la mémoire disponible
            valid_assignments = []

            with Pool(cpu_count()) as pool:
                for chunk in chunked_iterable(permutations, chunk_size):
                    results = pool.starmap(
                        validate_permutation,
                        [(perm, dict_standings, player_indices, standings_wins, standings_losses, n_players) for perm in chunk]
                    )
                    valid_assignments.extend([chunk[i] for i, is_valid in enumerate(results) if is_valid])

            assignments_per_masked[masked] = valid_assignments

        return assignments_per_masked

    def standings_to_dict(self,standings: List[Standing]) -> Dict[str, Dict]:
        standings_dict = {}
        for standing in standings:
            if standing.player:  # Vérifie que le joueur est défini
                standings_dict[standing.player] = {
                    "rank": standing.rank,
                    "points": standing.points,
                    "wins": standing.wins,
                    "losses": standing.losses,
                    "draws": standing.draws,
                    "omwp": standing.omwp,
                    "gwp": standing.gwp,
                    "ogwp": standing.ogwp,
                }
        return standings_dict

# Génération avec filtrage via la méthode personnalisée filtered_permutations = (perm for perm in product(*per_round_assignments_non_empty) if custom_rule(perm))


    def create_modified_rounds(self,rounds, unique_matching_perm, assignments_per_masked):
        """
        Crée de nouveaux objets Round avec les modifications apportées par les permutations sélectionnées.

        Args:
            rounds (List[Round]): Liste des rounds d'origine.
            unique_matching_perm (dict): Contient les joueurs masqués et leurs indices de permutation sélectionnés.
            assignments_per_masked (dict): Contient les permutations possibles pour chaque joueur masqué.

        Returns:
            List[Round]: Nouvelle liste d'objets Round avec les modifications appliquées.
        """
        # Créer une copie des rounds pour les modifications
        modified_rounds = [
            Round(
                rnd.round_name,
                [RoundItem(match.player1, match.player2, match.result) for match in rnd.matches]
            )
            for rnd in rounds
        ]
        # Avant de modifier les matchs, vérifier que la longueur des rounds et des matchs est correcte
        initial_lengths = [(rnd.round_name, len(rnd.matches)) for rnd in rounds]
        for masked_name, selected_index in unique_matching_perm.items():
            # Récupérer la permutation sélectionnée
            if isinstance(selected_index, list):  # Si c'est une liste, utiliser l'index 0
                selected_permutation = assignments_per_masked[masked_name][selected_index[0]]
            else:  # Si c'est un entier, on peut directement l'utiliser
                selected_permutation = assignments_per_masked[masked_name][selected_index]           
            # Parcourir les combinaisons par round dans la permutation sélectionnée
            for round_index, round_combinations in enumerate(selected_permutation):
                modified_round = modified_rounds[round_index]  # Le round à modifier
                for player, updated_matches in round_combinations.items():
                    for updated_match in updated_matches:
                        # Mettre à jour les matchs dans le round correspondant
                        for match in modified_round.matches:
                            if match.player1 == masked_name:
                                match.player1 = updated_match.player1
                            if match.player2 == masked_name:
                                match.player2 = updated_match.player2
        # Après les modifications, vérifier qu'aucun nouveau match n'a été ajouté
        final_lengths = [(rnd.round_name, len(rnd.matches)) for rnd in modified_rounds]

        # Vérification que les longueurs des rounds sont restées identiques
        for initial, final in zip(initial_lengths, final_lengths):
            if initial != final:
                raise ValueError(f"Round {initial[0]} a changé de nombre de matchs : {initial[1]} -> {final[1]}")


        return modified_rounds



    # Fonction ou méthode principale
    def Find_name_form_player_stats(self, rounds: List[Round], standings: List[Standing],bracket: List[Round]) -> List[Round]: 
        # Initialiser les rounds pour les mises à jour successives
        masked_to_actual = self.map_masked_to_actual(standings,rounds)
        # Étape 1 : Identifier les noms masqués dupliqués
        duplicated_masked_names = {
            masked for masked, actuals in masked_to_actual.items() if len(actuals) > 1
        }

        # Étape 2 : Collecter les matchs pour les noms masqués dupliqués
        masked_matches = self.collect_matches_for_duplicated_masked_names(
            duplicated_masked_names, rounds
        )

        # Étape 3 : Générer les combinaisons possibles d'assignations
        assignments_per_masked = self.generate_assignments(
            masked_matches, masked_to_actual, standings
        )

        # Étape 4 : Calculer et comparer les statistiques recalculées
        real_standings_by_player = {
            standing.player: standing for standing in standings
        }
        recalculated_stats = self.calculate_recalculated_stats(
            assignments_per_masked, standings
        )

        # Étape 5 : Trouver les meilleures combinaisons
        matching_permutation = self.find_best_combinations(
            recalculated_stats, real_standings_by_player
        )

        # Étape 6 : Identifier les permutations uniques
        unique_matching_perm = {}
        for masked_name, match_permutation_res in matching_permutation.items():
            if match_permutation_res:
                unique_matching_perm[masked_name] = match_permutation_res[0]
            else:
                # Si aucune permutation, ajouter une valeur par défaut ou ignorer
                unique_matching_perm[masked_name] = "No Match"  # Exemple
        # Étape 7 : Créer de nouveaux rounds mis à jour
        updated_rounds = self.create_modified_rounds(
            updated_rounds, unique_matching_perm, assignments_per_masked
        )



        # Retourner les rounds mis à jour
        return updated_rounds



    def find_best_combinations(self, recalculated_stats, real_standings_by_player):
        matching_combinations = {}
        for masked_name, player_combinations in recalculated_stats.items():
            matching_combinations[masked_name] = []
            closest_combination = None
            min_gwp_difference = float('inf')
            min_ogwp_difference = float('inf')

            for combination_index, combination in enumerate(player_combinations):
                is_matching = True
                ogwp_differences = []
                gwp_differences = []  # Liste pour stocker les différences de gwp
                comparison_details = []

                for player, recalculated_standing in combination.items():
                    real_standing = real_standings_by_player.get(player)
                    if is_matching and masked_name == '_**********_':
                        # print(f"Real Standing for {player}: {real_standing} ")
                        print(f"Recalculated Standing for {player}: {recalculated_standing}")
                    if not real_standing or not self.compare_standings(real_standing, recalculated_standing):
                        is_matching = False
                        break

                    # Calculer la différence de gwp pour ce joueur
                    if real_standing.gwp is not None and recalculated_standing.gwp is not None:
                        gwp_differences.append(abs(real_standing.gwp - recalculated_standing.gwp))

                    # Calculer la différence de ogwp pour ce joueur
                    if real_standing.ogwp is not None and recalculated_standing.ogwp is not None:
                        ogwp_differences.append(abs(real_standing.ogwp - recalculated_standing.ogwp))

                    # Collecter les détails pour le débogage
                    comparison_details.append((player, real_standing, recalculated_standing))
                # Si la combinaison correspond aux critères principaux
                if is_matching:
                    # Calculer la moyenne des différences de gwp et ogwp pour la combinaison
                    avg_gwp_diff = sum(gwp_differences) / len(gwp_differences) if gwp_differences else float('inf')
                    avg_ogwp_diff = sum(ogwp_differences) / len(ogwp_differences) if ogwp_differences else float('inf')

                    # Comparer et sélectionner la meilleure combinaison en fonction des critères
                    if avg_gwp_diff < min_gwp_difference:
                        min_gwp_difference = avg_gwp_diff
                        min_ogwp_difference = avg_ogwp_diff
                        closest_combination = [combination_index]
                    elif avg_gwp_diff == min_gwp_difference and avg_ogwp_diff < min_ogwp_difference:
                        min_ogwp_difference = avg_ogwp_diff
                        closest_combination = [combination_index]
                    elif avg_gwp_diff == min_gwp_difference and avg_ogwp_diff == min_ogwp_difference:
                        closest_combination.append(combination_index)  # Ajouter l'indice si égalité

            # Si plusieurs permutations sont trouvées pour le joueur masqué, on sélectionne la meilleure
            if closest_combination:
                matching_combinations[masked_name] = closest_combination

        return matching_combinations




        return matching_combinations

    def compare_standings(self,real_standing, recalculated_standing, compare_ogwp=False):
        """Compare deux standings et retourne True s'ils sont identiques, sinon False."""
        def float_equals(a, b, precision=2):
            """Compare deux floats avec une précision donnée (par défaut 3 chiffres après la virgule)."""
            if a is None or b is None:
                return False  # Considérer None comme non égal à toute autre valeur
            return round(a, precision) == round(b, precision)
        # Comparaison stricte sur certains critères
        matches = (
            real_standing.rank == recalculated_standing.rank and
            real_standing.points == recalculated_standing.points and
            real_standing.wins == recalculated_standing.wins and
            real_standing.losses == recalculated_standing.losses 
        )
        # Comparaison optionnelle de `ogwp`
        if compare_ogwp:
            matches = matches and float_equals(real_standing.ogwp, recalculated_standing.ogwp)

        return matches
