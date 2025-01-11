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
from collections import namedtuple
# import os
import sys
import csv
import math
from typing import List,Tuple,Dict, DefaultDict,Optional
from urllib.parse import urljoin
from itertools import permutations,product,islice
# import html
from dataclasses import dataclass
from models.base_model import *
from comon_tools.tools import *
from multiprocessing import Pool, cpu_count
import numpy as np
import time
import copy


def truncate(number, decimals=4):
    factor = 10.0 ** decimals
    return math.floor(number * factor) / factor


def validate_permutation(perm, player_indices, standings_wins, standings_losses,standings_gwp, n_players):
    """Valider une permutation donnée."""
    wins = np.zeros(n_players, dtype=int)
    losses = np.zeros(n_players, dtype=int)
    gwp_calculated = np.zeros(n_players, dtype=float)
    # rounds_played = np.zeros(n_players, dtype=int)
    for round_data in perm:
        for player, round_items in round_data.items():
            player_idx = player_indices[player]
            for round_item in round_items:
                if round_item.player1 == player:
                    win, loss = round_item.scores[0]  # Scores de player1
                elif round_item.player2 == player:
                    win, loss = round_item.scores[1]  # Scores de player2  
                wins[player_idx] += win
                losses[player_idx] += loss
                if wins[player_idx] > standings_wins[player_idx] or losses[player_idx] > standings_losses[player_idx]:
                    return False
    if not np.array_equal(wins, standings_wins) or not np.array_equal(losses, standings_losses):
        return False
        # rounds_played = np.zeros(n_players, dtype=int)
    Match_win = np.zeros(n_players, dtype=int)
    Match_losses = np.zeros(n_players, dtype=int)
    for round_data in perm:
        for player, round_items in round_data.items():
            player_idx = player_indices[player]
            for round_item in round_items:
                if round_item.player1 == player:
                    win, loss,_  = map(int, round_item.result.split('-'))  # Scores de player1
                elif round_item.player2 == player:
                   loss ,win, _  = map(int, round_item.result.split('-'))  # Scores de player2  
                Match_win[player_idx] += win
                Match_losses[player_idx] += loss
        # Calcul du GWP et comparaison avec standings_gwp
    for i in range(n_players):
        total_games = Match_win[i] + Match_losses[i]
        if total_games > 0:
            gwp_calculated[i] = truncate(Match_win[i] / total_games)
        else:
            gwp_calculated[i] = 0.0
        # Comparaison avec tolérance
        if not np.isclose(round(gwp_calculated[i], 3), round(standings_gwp[i],3), atol=0.001):
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
                    match["res"],
                    id=f"{round_name}.{i}" 
                )
                for i, match in enumerate(matches)
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
        # ATTENTION tu dois penser a vérifier les bye dans les calcules
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
    def calculate_stats_for_matches(self, player: str, matches: List[RoundItem],rounds ,standings: List[Standing]):
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
        gwp = truncate(total_games_won / total_games_played) if total_games_played > 0 else 0

        # Calculer OGP (Opponents’ Game-Win Percentage)

        total_ogp = 0
        total_opponents = 0
        stop_compute_ogwp = False
        for opponent in opponents:
        # Ignorer les adversaires qui correspondent à la regexp
            if re.fullmatch(r'.\*{10}.', opponent):
                stop_compute_ogwp = True
                break
            # Récupérer les matchs de l'adversaire
            opponent_matches = [
                match for rnd in rounds
                for match in rnd.matches
                if match.player1 == opponent or match.player2 == opponent
            ]

            opponent_games_won = 0
            opponent_games_played = 0

            for match in opponent_matches:
                p1_wins, p2_wins, draws_ = map(int, match.result.split('-'))

                if match.player1 == opponent:
                    opponent_games_won += p1_wins
                    opponent_games_played += p1_wins + p2_wins + draws_
                elif match.player2 == opponent:
                    opponent_games_won += p2_wins
                    opponent_games_played += p1_wins + p2_wins + draws_

            # Calculer le pourcentage de victoires de l'adversaire (GWP pour l'adversaire)
            if opponent_games_played > 0:
                opponent_gwp = opponent_games_won / opponent_games_played  # GWP pour l'adversaire
                total_ogp += opponent_gwp
                total_opponents += 1

        # Moyenne des GWP des adversaires (OGP)
        if stop_compute_ogwp:
            ogwp = None
        else :
            ogwp = truncate(total_ogp / total_opponents) if total_opponents > 0 else None

        # Calculer OMWP (Opponents' Match-Win Percentage)
        opponent_match_wins = 0
        opponent_match_total = 0
        for opponent in opponents:
            if re.fullmatch(r'.\*{10}.', opponent):
                omwp = None
                break
            opponent_standing = next((s for s in standings if s.player == opponent), None)
            if opponent_standing:
                opponent_match_wins += opponent_standing.wins
                opponent_match_total += opponent_standing.wins + opponent_standing.losses + opponent_standing.draws

        omwp = opponent_match_wins / opponent_match_total if opponent_match_total > 0 else None
        
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
        # Analyser les résultats des matchs pour mettre à jour les victoires et défaites des joueurs
            # Étendre les joueurs pour correspondre au nombre de matchs
        match_round = int(round_name.replace('Round ', ''))
        valid_player = [player for player in actual_players if player_match_count[player] >= match_round]
        for perm in permutations(valid_player, len(matches)):
            replaced_matches = defaultdict(list)
            for (role, match), player in zip(matches, perm):
            # Si un joueur a plus de matchs que le round actuel lui permet, la permutation est invalide
                # print(f"Permutation invalide pour {player} au round {match_round}. Nombre de matchs restants: {player_match_count[player]}")
                p1_wins, p2_wins, _ = map(int, match.result.split('-'))
                if (role == 'player1'  and (
                    (p1_wins > p2_wins and standings_dict[player].wins == 0) or 
                    (p1_wins < p2_wins and standings_dict[player].losses == 0) or 
                    (p1_wins > 0 and standings_dict[player].gwp == 0) or
                    (standings_dict[player].losses > 0 and standings_dict[player].wins == 0 and round(standings_dict[player].gwp, 2) == 0.33 and p1_wins != 1) 
                    )):
                    break
                elif (role == 'player2' and (
                    (p1_wins < p2_wins and standings_dict[player].wins == 0) or 
                    (p1_wins > p2_wins and standings_dict[player].losses == 0) or 
                    (p2_wins > 0 and standings_dict[player].gwp == 0) or 
                    (standings_dict[player].losses > 0 and standings_dict[player].wins == 0 and round(standings_dict[player].gwp, 2) == 0.33 and p2_wins != 1)
                    )):
                    break      
                else:
                    new_match = RoundItem(
                        player1=match.player1 if role != 'player1' else player,
                        player2=match.player2 if role != 'player2' else player,
                        result=match.result,
                        id=match.id
                    )
                    replaced_matches[player].append(new_match)
            if len(replaced_matches) == len(valid_player):
                round_combinations.append(replaced_matches)
        return round_combinations

    def organize_matches_by_round(self, matches_info):
        """Organiser les matchs par round."""
        matches_by_round = defaultdict(list)
        for role, round_name, match in matches_info:
            matches_by_round[round_name].append((role, match))
        return matches_by_round


    def generate_assignments(self, masked_matches, masked_to_actual, standings):
        """Optimiser la génération des assignments avec multiprocessing."""
        dict_standings = self.standings_to_dict(standings)
        assignments_per_masked = {}
        for masked, matches_info in masked_matches.items():
            actual_players = masked_to_actual[masked]
            matches_by_round = self.organize_matches_by_round(matches_info)
            # Préparer les données
            player_indices = {player: idx for idx, player in enumerate(actual_players)}
            n_players = len(actual_players)
            standings_wins = np.array([dict_standings[player]["wins"] for player in actual_players])
            standings_losses = np.array([dict_standings[player]["losses"] for player in actual_players])
            standings_gwp = np.array([dict_standings[player]['gwp'] for player in actual_players]) 
            # Fonction génératrice pour les combinaisons de rounds
            def generate_valid_combinations():
                for round_name, matches in matches_by_round.items():
                    round_combinations = self.generate_round_combinations(matches, actual_players, standings, round_name)
                    if round_combinations:  # Vérifie si des combinaisons existent pour ce round
                        yield round_combinations

            def clean_round_combinations(round_combinations):
                seen = set()  # Pour garder trace des dictionnaires déjà vus
                cleaned_round_data = []
                for round_item in round_combinations:
                    # Convertir le defaultdict en un tuple des éléments
                    item_tuple = tuple((key, tuple(value)) for key, value in round_item.items())
                    if item_tuple not in seen:
                        seen.add(item_tuple)  # Marquer ce dict comme vu
                        cleaned_round_data.append(round_item)  # Ajouter le dict à la liste nettoyée
                return cleaned_round_data

            # Générer le générateur de combinaisons valides pour chaque round
            valid_combinations = generate_valid_combinations()
            # Nettoyage des données des combinaisons générées
            cleaned_combinations = []
            for round_combinations in valid_combinations:
                cleaned_round_data = clean_round_combinations(round_combinations)
                cleaned_combinations.append(cleaned_round_data)


            permutations_lazy_permutations = product(*cleaned_combinations)                          
            total_permutations = 1
            for comb in cleaned_combinations:
                    total_permutations *= len(comb)
            start_time = time.time()  # Démarre le timer
            # if masked == '_**********_':
            #     print("stop")
            if total_permutations < 1000: 
                # dict_standings remove des arguments
                assignments_per_masked[masked] = list((perm for perm in permutations_lazy_permutations if validate_permutation(perm,  player_indices, standings_wins, standings_losses, standings_gwp, n_players)))

            else:
                print(f"Total permutations for parralelisation : {total_permutations}") 
                # Taille dynamique du chunk en fonction du total des permutations
                chunk_size = min(10000, max(1000, total_permutations // (10 * cpu_count())))
                valid_assignments = []
                with Pool(cpu_count()) as pool:
                    while True:
                        # Créer un lot de permutations
                        chunk = list(islice(permutations_lazy_permutations, chunk_size))
                        if not chunk:
                            break
                        # Préparer les arguments pour chaque permutation dans le chunk
                                # Validation des permutations en parallèle
                        # dict_standings remove des arguments
                        results = pool.starmap(validate_permutation, [
                            (perm, player_indices, standings_wins, standings_losses,standings_gwp, n_players)
                            for perm in chunk
                        ])
                        # print("Permutation généré assignation") 
                        # Ajouter les permutations valides
                        valid_assignments.extend(perm for perm, is_valid in zip(chunk, results) if is_valid)
                assignments_per_masked[masked] = valid_assignments
        end_time = time.time()  # Fin du timer
        print(f"Temps total d'exécution : {end_time - start_time:.2f} secondes")
        return assignments_per_masked

# # Calculer le nombre d'objets pouvant être stockés
# num_objects = ram_in_bytes // object_size
# print(f"Nombre d'objets que vous pouvez stocker : {num_objects}")

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
                [RoundItem(match.player1, match.player2, match.result,match.id) for match in rnd.matches]
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
# #################################################################################################################        
#         # on regarde les bye 
#         print(standings[63])
#         for r in rounds:
#             for m in r.matches:
#                 if m.player1 == "ZYX_Jerry" or m.player2 == "ZYX_Jerry":
#                     print(m)
# #################################################################################################################            
#         for r in rounds:
#             for m in r.matches:
#                 if m.player1 == "jamalxvi" or m.player2 == "jamalxvi":
#                     print(m)
#         print(standings[75])
#         GWP_a = []
#         win_a = []
#         tot_a = []
#         test_212 = []
#         for s in standings:
#             if s.player in ["SKK","ZYX_Jerry","MrPippin","Veraquios","knighthunter01","Tw33Ty","friskifraska","citizenofnerdvana"]:
#                 test_212.append(s.points)
#                 GWP_a.append(s.gwp)
#                 win_a.append(s.wins)
#                 tot_a.append(s.wins + s.losses)
#                 print(s)
# #################################################################################################################
#         for r in rounds:
#             for m in r.matches:
#                 if m.player1 == "SKK" or m.player2 == "SKK":
#                     print(m)
        
#         print(standings[144])
#         GWP_a = []
#         win_a = []
#         tot_a = []
#         test_212 = []
#         for s in standings:
#             if s.player in ["jamalxvi","rastaf","fj_rodman"]:
#                 test_212.append(s.points)
#                 GWP_a.append(s.gwp)
#                 win_a.append(s.wins)
#                 tot_a.append(s.wins + s.losses)
#                 print(s) 
#         matches = [
#             match for rnd in rounds 
#             for match in rnd.matches 
#             if match.player1 == "SKK" or match.player2 == "SKK"
#         ]         
#         print(self.calculate_stats_for_matches("SKK", matches,rounds ,standings))
# #################################################################################################################
#         print(standings[75]) 
#         matches = [
#             match for rnd in rounds 
#             for match in rnd.matches 
#             if match.player1 == "jamalxvi" or match.player2 == "jamalxvi"
#         ]
#         print(self.calculate_stats_for_matches("jamalxvi", matches,rounds ,standings))
#         print(standings[21]) 
#         matches = [
#             match for rnd in rounds 
#             for match in rnd.matches 
#             if match.player1 == "rastaf" or match.player2 == "rastaf"
#         ]
#         print(self.calculate_stats_for_matches("rastaf", matches,rounds ,standings))
#         print(standings[158])
#         matches = [
#             match for rnd in rounds 
#             for match in rnd.matches 
#             if match.player1 == "fj_rodman" or match.player2 == "fj_rodman"
#         ]
#         for r in rounds:
#             for m in r.matches:
#                 if m.player1 == "fj_rodman" or m.player2 == "fj_rodman":
#                     print(m)
#         print(self.calculate_stats_for_matches("fj_rodman", matches,rounds ,standings))
# #################################################################################################################
        GWP_a = []
        win_a = []
        tot_a = []
        test_212 = []
        for s in standings:
            if s.player in ["graciasportanto","Ekeross","SKK"]:
                test_212.append(s.points)
                GWP_a.append(s.gwp)
                win_a.append(s.wins)
                tot_a.append(s.wins + s.losses)
                print(s) 
        print(standings[127]) 
        matches = [
            match for rnd in rounds 
            for match in rnd.matches 
            if match.player1 == "graciasportanto" or match.player2 == "graciasportanto"
        ]
        print(self.calculate_stats_for_matches("graciasportanto", matches,rounds ,standings))
        print(standings[33]) 
        matches = [
            match for rnd in rounds 
            for match in rnd.matches 
            if match.player1 == "Ekeross" or match.player2 == "Ekeross"
        ]
        print(self.calculate_stats_for_matches("Ekeross", matches,rounds ,standings))
        print(standings[144]) 
        matches = [
            match for rnd in rounds 
            for match in rnd.matches 
            if match.player1 == "SKK" or match.player2 == "SKK"
        ]
        print(self.calculate_stats_for_matches("SKK", matches,rounds ,standings))

        for r in rounds:
            for m in r.matches:
                if m.player1 == "Ekeross" or m.player2 == "Ekeross":
                    print(m)
# # #################################################################################################################

        matching_permutation = {}
        for masked_name in duplicated_masked_names:
            print(f"Traitement pour le nom masqué : {masked_name}")
            # if masked_name == 'M**********s': 
            # "K**********v"
            # if masked_name == "K**********v" :#  "s**********o"" 'N**********s' "_**********_"
            masked_matches = self.collect_matches_for_duplicated_masked_names(
                {masked_name}, rounds
            )
            # Étape 3
            assignments_per_masked = self.generate_assignments(
                masked_matches, masked_to_actual, standings
            )
            print(sum(len(v) for v in assignments_per_masked.values()))
            # temp refactoring remove after
            matching_permutation[masked_name] = assignments_per_masked

            # # Étape 4
            # real_standings_by_player = {
            #     standing.player: standing for standing in standings
            # }
            
            # recalculated_stats = self.calculate_recalculated_stats(
            #     assignments_per_masked, standings
            # )
            # # del assignments_per_masked
            # # Étape 5
            # matching_permutation_iteration = self.find_best_combinations(
            #     recalculated_stats, real_standings_by_player
            # )
            # # Stocker les résultats
            # matching_permutation[masked_name] = matching_permutation_iteration

        Determinist_permutation,remaining_matching_perm = self.generate_tournaments_with_unique_permutations(rounds, matching_permutation)
            # round 0 round item 53 devrait etre remplacé
        a = self.process_permutations_with_recalculation(Determinist_permutation, remaining_matching_perm,standings)


        # Étape 6 : Identifier les permutations uniques
        unique_matching_perm = {}
        for masked_name, match_permutation_res in matching_permutation.items():
            if len(match_permutation_res) == 1:  # Cas d'un seul élément
                unique_matching_perm[masked_name] = match_permutation_res
            elif  match_permutation_res:
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

    def process_permutations_with_recalculation(
        self,
        rounds: List[Round], 
        matching_permutation: Dict[str, Dict[str, List[List[Dict[str, List[RoundItem]]]]]], 
        standings: List[Standing]):
        """Traiter les permutations avec recalcul des statistiques."""
        
        # Créer une copie modifiable des rounds
        modified_rounds = [
            Round(
                rnd.round_name,
                [RoundItem(match.player1, match.player2, match.result,match.id) for match in rnd.matches]
            )
            for rnd in rounds
        ]
        
        initial_lengths = [(rnd.round_name, len(rnd.matches)) for rnd in rounds]

        # Parcours des masques et traitement des permutations
        for masked_name, permutations in sorted(matching_permutation.items(), key=lambda x: len(x[1])):
            # if masked_name == 'M**********s':#'M**********3' 'M**********s'
            valide_perm = []
            for permuted_names, round_permutations in permutations.items():
                if len(round_permutations) <5 :
                    Temp_tournament_stats = []
                    permutation_tested_tournament = []
                    for round_combination in round_permutations:  # Une permutation complète de tous les rounds
                        # Créer une copie temporaire de modified_rounds pour cette permutation
                        temp_rounds = [
                            Round(
                                rnd.round_name,
                                [RoundItem(match.player1, match.player2, match.result,match.id) for match in rnd.matches]
                            )
                            for rnd in modified_rounds
                        ]
                        players_to_recalculate = set()  # Suivre les joueurs pour recalculer les stats
                        # Parcourir tous les rounds dans cette permutation complète
                        for round_index, round_dict in enumerate(round_combination):
                            if round_index >= len(temp_rounds):
                                break  # Éviter les erreurs si round_combination dépasse les rounds disponibles
                            temp_round = temp_rounds[round_index]

                            for real_name, updated_matches in round_dict.items():
                                for updated_match in updated_matches:
                                    for match in temp_round.matches:
                                        # Appliquer les modifications si le masque et l'autre joueur correspondent
                                        if match.player1 == masked_name and match.id == updated_match.id:
                                            match.player1 = real_name
                                            if not re.fullmatch(r'.\*{10}.', match.player2):
                                                players_to_recalculate.update([real_name, match.player2])
                                        elif match.player2 == masked_name and match.id == updated_match.id:
                                            match.player2 = real_name
                                            if not re.fullmatch(r'.\*{10}.', match.player1):
                                                players_to_recalculate.update([real_name, match.player1])
                        permutation_tested_tournament.append(temp_rounds)
                        permutation_stats = []

                        # Vérifier si les joueurs concernés n'affrontent plus de masques
                        for player in players_to_recalculate:
                            matches = [
                                match for rnd in temp_rounds 
                                for match in rnd.matches 
                                if match.player1 == player or match.player2 == player
                            ]
                            if not any(masked_name in (match.player1, match.player2) for match in matches):
                                # Recalculer les statistiques du joueur
                                permutation_stats.append(self.calculate_stats_for_matches(player, matches,temp_rounds ,standings))
                        standings_comparator_res = []
                        for unsure_standings in  permutation_stats:
                            # Rechercher le joueur correspondant dans les standings recalculés
                            real_standing_ite = next(
                                (standing for standing in standings if standing.player == unsure_standings.player), None
                            )      

                            res_comparator = self.compare_standings(real_standing_ite, unsure_standings, 3,3,3)
                            if not res_comparator:
                                print(f"Rea : {real_standing_ite}")
                                print(f"cal : {unsure_standings}") 
                            standings_comparator_res.append(res_comparator)

                        valide_perm.append(all(standings_comparator_res))
                        Temp_tournament_stats.append(permutation_stats)
                print(masked_name)
                print(valide_perm)
                if  valide_perm.count(True) == 1:
                    print(masked_name)
    


        # Après les modifications, vérifier qu'aucun nouveau match n'a été ajouté
        final_lengths = [(rnd.round_name, len(rnd.matches)) for rnd in modified_rounds]
        for initial, final in zip(initial_lengths, final_lengths):
            if initial != final:
                raise ValueError(f"Round {initial[0]} a changé de nombre de matchs : {initial[1]} -> {final[1]}")

        return modified_rounds   

    def generate_tournaments_with_unique_permutations(self,rounds, matching_permutation):
        """
        Génère une liste de tournois en remplaçant les noms masqués par des permutations uniques.

        Args:
            rounds (List[Round]): Liste des rounds originaux avec des noms masqués.
            matching_permutation (dict): Dictionnaire contenant les masques et leurs permutations uniques.

        Returns:
            List[List[Round]]: Liste de tournois (chaque tournoi est une liste de rounds avec des noms non masqués).
        """
        # Liste des tournois générés
        modified_rounds = [
            Round(
                rnd.round_name,
                [RoundItem(match.player1, match.player2, match.result,match.id) for match in rnd.matches]
            )
            for rnd in rounds
        ]

        initial_lengths = [(rnd.round_name, len(rnd.matches)) for rnd in rounds]
        # Copie des permutations restantes
        remaining_permutations = matching_permutation.copy()
        # Parcours des masques et application des permutations uniques
        for masked_name, permutations in matching_permutation.items():
            permuted_names, round_data = next(iter(permutations.items()))
            if len(round_data) == 1:
                # Parcourir chaque round concerné dans round_data
                for round_index, round_combinations in enumerate(round_data):
                    if round_index >= len(modified_rounds):
                        break  # Éviter les erreurs si round_data dépasse les rounds disponibles

                    modified_round = modified_rounds[round_index]

                    for round_dict in round_combinations:
                        for real_name, updated_matches in round_dict.items():
                            for updated_match in updated_matches:
                                # Appliquer les modifications si le masque et l'autre joueur correspondent
                                for match in modified_round.matches:
                                    if match.player1 == masked_name and match.id == updated_match.id:
                                        match.player1 = real_name
                                    elif match.player2 == masked_name and match.id == updated_match.id:
                                        match.player2 = real_name
                # Supprimer le masque traité des permutations restantes
                del remaining_permutations[masked_name]


        # Après les modifications, vérifier qu'aucun nouveau match n'a été ajouté
        final_lengths = [(rnd.round_name, len(rnd.matches)) for rnd in modified_rounds]
        # Vérification que les longueurs des rounds sont restées identiques
        for initial, final in zip(initial_lengths, final_lengths):
            if initial != final:
                raise ValueError(f"Round {initial[0]} a changé de nombre de matchs : {initial[1]} -> {final[1]}")

        return modified_rounds, remaining_permutations

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
                    # print(f"Real Standing for {player}: {real_standing} ")
                    # print(f"Calc Standing for {player}: {recalculated_standing} ")
                    # if is_matching and masked_name == '_**********_':
                    #     # print(f"Real Standing for {player}: {real_standing} ")
                    #     print(f"Recalculated Standing for {player}: {recalculated_standing}")
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


    def compare_standings(self,real_standing, recalculated_standing,  compare_gwp=None, compare_omwp=None, compare_ogwp=None):
        """Compare deux standings et retourne True s'ils sont identiques, sinon False."""
        matches = (
            real_standing.rank == recalculated_standing.rank and
            real_standing.points == recalculated_standing.points and
            real_standing.wins == recalculated_standing.wins and
            real_standing.losses == recalculated_standing.losses 
        )

        # Comparaison optionnelle des pourcentages uniquement s'ils ne sont pas None
        if compare_gwp and real_standing.gwp is not None and recalculated_standing.gwp is not None:
            matches = matches and (round(real_standing.gwp, compare_gwp) == round(recalculated_standing.gwp, compare_gwp))
        if compare_omwp and real_standing.omwp is not None and recalculated_standing.omwp is not None:
            matches = matches and (round(real_standing.omwp, compare_omwp) == round(recalculated_standing.omwp, compare_omwp))
        if compare_ogwp and real_standing.ogwp is not None and recalculated_standing.ogwp is not None:
            matches = matches and (round(real_standing.ogwp, compare_ogwp) == round(recalculated_standing.ogwp, compare_ogwp))  

        return matches
