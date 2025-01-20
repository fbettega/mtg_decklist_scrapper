import json
import re
# import os
import math
from typing import List,Tuple,Dict, DefaultDict,Optional
from itertools import permutations,product,islice
# import html
from models.base_model import *
from comon_tools.tools import *
# from collections import defaultdict
from multiprocessing import Pool, cpu_count
import numpy as np
import time
import copy




class TreeNode:
    def __init__(self, combination=None):
        self.combination = combination  # La configuration actuelle du round
        self.children = []  # Les enfants du nœud
        self.valid = True  # Indique si ce nœud est valide

    def add_child(self, child):
        self.children.append(child)

class FilteredNode:
    """Classe pour représenter un nœud filtré avec ses sous-nœuds valides."""
    def __init__(self, combination, children=None):
        self.combination = combination
        self.children = children if children else []

def traverse_tree(node, operation):
    """
    Applique une opération sur chaque nœud de l'arbre.
    
    Args:
        node (TreeNode): Le nœud racine à explorer.
        operation (function): Une fonction à appliquer sur chaque nœud.
    """
    operation(node)  # Appliquer l'opération au nœud actuel
    for child in node.children:
        traverse_tree(child, operation)  # Explorer les enfants récursivement

def count_nodes(node):
    """
    Compte le nombre de nœuds dans l'arbre.
    """
    count = 0

    def increment_count(n):
        nonlocal count
        count += 1

    traverse_tree(node, increment_count)
    return count        
def is_single_line_tree(node):
    """
    Vérifie si l'arbre est une simple ligne d'enfants (aucune branche).
    
    Args:
        node (TreeNode): Le nœud racine de l'arbre.
    
    Returns:
        bool: True si l'arbre est une ligne droite, False sinon.
    """
    current = node
    while current:
        if len(current.children) > 1:
            return False  # Plus d'un enfant, ce n'est pas une ligne droite
        if len(current.children) == 0:
            break  # Feuille atteinte
        current = current.children[0]  # Passer au seul enfant
    return True
    
def apply_tree_permutations(node, modified_rounds, masked_name):
    """
    Applique les permutations contenues dans un nœud de l'arbre sur les rounds modifiés.
    """
    if not node:
        print("not a node") 
        return  
    if node.combination is None:
        # Continuer avec les enfants du nœud courant
        for child in node.children:
            apply_tree_permutations(child, modified_rounds, masked_name)
        return

    # Appliquer les modifications du nœud courant
    for real_name, updated_matches in node.combination.items():  # Itère sur les paires clé-valeur
        for updated_match in updated_matches:  # Parcourt les RoundItem associés
            for modified_round in modified_rounds:
                for match in modified_round.matches:
                    if match.id == updated_match.id:  # Vérifier si l'ID correspond
                        # Appliquer les modifications au joueur correspondant
                        if match.player1 == masked_name:
                            match.player1 = real_name
                        elif match.player2 == masked_name:
                            match.player2 = real_name
    for child in node.children:
        apply_tree_permutations(child, modified_rounds, masked_name)
                    # Appliquer les permutations à partir de l'arbre racine
def process_combination(task):
    """
    Traite une combinaison spécifique dans le cadre de la parallélisation.

    Args:
        task (tuple): Contient les informations nécessaires pour traiter une combinaison. 
                      Format : (first_round_combination, remaining_rounds, validate_fn,
                                player_indices, standings_wins, standings_losses, 
                                standings_gwp, n_players)

    Returns:
        list: Une liste de permutations valides, ou None si aucune permutation n'est valide.
    """
    (
        first_round_combination,  # La configuration initiale du premier round
        remaining_rounds,         # Les rounds restants à traiter
        validate_fn,              # Fonction de validation des combinaisons
        player_indices,           # Mapping des joueurs aux indices
        standings_wins,           # Statistiques des victoires des joueurs
        standings_losses,         # Statistiques des défaites des joueurs
        standings_gwp,            # Pourcentage de victoire dans les jeux
        n_players                 # Nombre total de joueurs
    ) = task
    # Construire un arbre pour explorer les permutations valides des rounds restants
    root = TreeNode()  # Nœud racine de l'arbre


    build_tree(
        root,
        [[first_round_combination]] + remaining_rounds,
        validate_fn,
        player_indices,
        standings_wins,
        standings_losses,
        standings_gwp,
        n_players
    )

    # Extraire les permutations valides à partir de l'arbre
    # return extract_valid_permutations(root)
    return root



def gather_stats_from_standings_tree(node, base_table, compute_stat_fun, masked_name, compare_standings, standings, player_result=None):
    base_table_update = copy.deepcopy(base_table)

    if player_result is None:
        player_result = {}

    # Mettre à jour les statistiques pour le nœud courant
    if node.combination is not None:
        for real_name, matches in node.combination.items():
            if real_name not in player_result:
                player_result[real_name] = {
                    "Match_wins": 0,
                    "Match_losses": 0,
                    "Game_wins": 0,
                    "Game_losses": 0,
                    "Game_draws": 0,
                    "matchups": set(),
                }
            for match in matches:
                p1_wins, p2_wins, draws = map(int, match.result.split('-'))

                # Identifier si le joueur traité est Player1 ou Player2
                if match.player1 == real_name or match.player2 == real_name:
                    is_player1 = (match.player1 == real_name)

                    # Détermine les scores et l'adversaire en fonction de la position
                    win, loss = match.scores[0] if is_player1 else match.scores[1]
                    opponent = match.player2 if is_player1 else match.player1
                    game_wins = p1_wins if is_player1 else p2_wins
                    game_losses = p2_wins if is_player1 else p1_wins

                    # Mise à jour des statistiques du joueur
                    player_result[real_name]["Match_wins"] += win
                    player_result[real_name]["Match_losses"] += loss
                    player_result[real_name]["Game_wins"] += game_wins
                    player_result[real_name]["Game_losses"] += game_losses
                    player_result[real_name]["Game_draws"] += draws

                    # Ajout de l'adversaire si pertinent
                    if opponent is not None and not re.fullmatch(r'.\*{10}.', opponent):
                        player_result[real_name]["matchups"].add(opponent)

    # Si le nœud est une feuille, calcule les standings et évalue les comparaisons
    if not node.children:
        tree_standings_res = compute_stat_fun(base_table_update, player_result, masked_name)
        standings_comparator_res = []

        for unsure_standings in tree_standings_res:
            real_standing_ite = next(
                (standing for standing in standings if standing.player == unsure_standings.player), None
            )
            res_comparator = compare_standings(real_standing_ite, unsure_standings, 3, 3, 3)
            # if not res_comparator:    
            #     if debug_print:
            #         print(f"Real : {real_standing_ite}" )  
            #         print(f"Calc : {unsure_standings}" )       
            #     return None  
            standings_comparator_res.append(res_comparator)

        # Vérifie si toutes les comparaisons sont `True`
        if all(standings_comparator_res):
            return FilteredNode(node.combination)  # Retourne le nœud filtré

        return None  # Nœud non valide

    # Parcourt les enfants et filtre les sous-arbres valides
    valid_children = []
    for child in node.children:
        filtered_child = gather_stats_from_standings_tree(
            child, base_table_update, compute_stat_fun, masked_name, compare_standings, standings, player_result
        )
        if filtered_child:
            valid_children.append(filtered_child)

    # Si ce nœud ou ses enfants sont valides, créer un nœud filtré
    if valid_children or node.combination is not None:
        return FilteredNode(node.combination, valid_children)

    return None  # Aucun nœud valide

 

def build_tree(node, remaining_rounds, validate_fn, player_indices, standings_wins, standings_losses, standings_gwp, n_players, history=None, iteration=0):
    if history is None:
        history = {
            "Match_wins": np.zeros(n_players, dtype=int),
            "Match_losses": np.zeros(n_players, dtype=int),
            "Game_wins": np.zeros(n_players, dtype=int),
            "Game_losses": np.zeros(n_players, dtype=int),
            "Game_draws": np.zeros(n_players, dtype=int),
            "matchups": {player: set() for player in player_indices.keys()}
        }

    if not remaining_rounds or not node.valid:
        return

    current_round = remaining_rounds[0]

    for match_combination in current_round:
        # Copier l'historique actuel pour ce chemin
        new_history = {
            "Match_wins": history["Match_wins"].copy(),
            "Match_losses": history["Match_losses"].copy(),
            "Game_wins": history["Game_wins"].copy(),
            "Game_losses": history["Game_losses"].copy(),
            "Game_draws": history["Game_draws"].copy(),
            "matchups": {player: matchups.copy() for player, matchups in history["matchups"].items()}
        }

        # Mettre à jour les statistiques pour la combinaison actuelle
        valid = validate_fn(match_combination, new_history, player_indices, standings_wins, standings_losses, standings_gwp)

        if valid:
            child_node = TreeNode(match_combination)
            child_node.valid = True
            node.add_child(child_node)

            # Appel récursif avec l'historique mis à jour
            build_tree(
                child_node,
                remaining_rounds[1:],
                validate_fn,
                player_indices,
                standings_wins,
                standings_losses,
                standings_gwp,
                n_players,
                new_history,
                iteration + 1
            )



def extract_valid_permutations(node, current_path=None):
    """
    Récupère toutes les permutations valides depuis l'arbre.
    """
    if current_path is None:
        current_path = []
    
    if not node.children:  # Feuille de l'arbre
        return [current_path + [node.combination]] if node.combination else [current_path]

    results = []
    for child in node.children:
        results.extend(extract_valid_permutations(child, current_path + [node.combination] if node.combination else current_path))
    return results


def custom_round(value, decimals=0):
    # multiplier = 10**decimals
    epsilon = 10 ** (-decimals -3)
    return round(value + epsilon, decimals)

def truncate(number, decimals=4):
    factor = 10.0 ** decimals
    return math.floor(number * factor) / factor

def update_encounters(encounters, player1, player2):
    """
    Met à jour le dictionnaire des affrontements. Retourne False si la règle est violée.
    """
    if player1 > player2:  # Assurez l'ordre pour éviter les doublons
        player1, player2 = player2, player1

    if player1 not in encounters:
        encounters[player1] = set()

    if player2 in encounters[player1]:  # Affrontement déjà existant
        return False

    # Enregistrer l'affrontement
    encounters[player1].add(player2)
    return True


# Méthode globale pour multiprocessing
def process_single_permutation(args):
    round_combination, masked_name, modified_rounds, standings, calculate_stats_for_matches, compare_standings,debug_print = args
    temp_rounds = [
        Round(
            rnd.round_name,
            [RoundItem(match.player1, match.player2, match.result, match.id) for match in rnd.matches]
        )
        for rnd in modified_rounds
    ]
    players_to_recalculate = set()
    # Dictionnaire pour suivre les affrontements
    player_encounters = {}
    for round_index, round_dict in enumerate(round_combination):
        temp_round = temp_rounds[round_index]
        for real_name, updated_matches in round_dict.items():
            for updated_match in updated_matches:
                for match in temp_round.matches:
                    if match.player1 == masked_name and match.id == updated_match.id:
                        match.player1 = real_name
                        if match.player2 is not None and not re.fullmatch(r'.\*{10}.', match.player2):
                            players_to_recalculate.update([real_name, match.player2])
                            if not update_encounters(player_encounters, real_name, match.player2):
                                if debug_print:
                                    print(f"{masked_name} : P1 : {match.player1} / P2 {match.player2} Player already encounter" )
                                return None
                    elif match.player2 == masked_name and match.id == updated_match.id:
                        match.player2 = real_name
                        if match.player1 is not None and not re.fullmatch(r'.\*{10}.', match.player1):
                            players_to_recalculate.update([real_name, match.player1])
                            if not update_encounters(player_encounters, real_name, match.player1):
                                if debug_print:
                                    print(f"{masked_name} : P1 : {match.player1} / P2 {match.player2} Player already encounter" )
                                return None

    permutation_stats = []
    for player in players_to_recalculate:
        matches = [
            match for rnd in temp_rounds
            for match in rnd.matches
            if match.player1 == player or match.player2 == player
        ]
        if not any(masked_name in (match.player1, match.player2) for match in matches):
            permutation_stats.append(calculate_stats_for_matches(player, matches, temp_rounds, standings))

    standings_comparator_res = []
    for unsure_standings in permutation_stats:
        real_standing_ite = next(
            (standing for standing in standings if standing.player == unsure_standings.player), None
        )
        res_comparator = compare_standings(real_standing_ite, unsure_standings, 3, 3, 3)
        if not res_comparator:    
            if debug_print:
                print(f"Real : {real_standing_ite}" )  
                print(f"Calc : {unsure_standings}" )       
            return None
        standings_comparator_res.append(res_comparator)

    if all(standings_comparator_res):
        return round_combination
    print(f"{masked_name} : Bug" )
    return None


def validate_permutation(match_combination, history, player_indices, standings_wins, standings_losses, standings_gwp):
    """
    Valider une permutation partielle dans le cadre de la construction de l'arbre.
    """

    Match_wins = history["Match_wins"]
    Match_losses = history["Match_losses"]
    Game_wins = history["Game_wins"]
    Game_losses = history["Game_losses"]
    Game_draws = history["Game_draws"] 
    matchups = history["matchups"]

    for player, round_items in match_combination.items():
        for round_item in round_items:
            if round_item.player1 == player:
                opponent = round_item.player2
                win, loss = round_item.scores[0]
                M_win, M_loss,M_draw  = map(int, round_item.result.split('-'))  # Scores de player1
            elif round_item.player2 == player:
                opponent = round_item.player1
                win, loss = round_item.scores[1]
                M_loss,M_win,M_draw  = map(int, round_item.result.split('-'))  # Scores de player2
            else:
                continue

            if opponent is not None:
                if opponent in matchups[player]:
                    return False
                if not re.fullmatch(r'.\*{10}.', opponent):
                    matchups[player].add(opponent)
                    # matchups[opponent].add(player)

            # Mettre à jour les statistiques
            player_idx = player_indices[player]
            Match_wins[player_idx] += win
            Match_losses[player_idx] += loss

            Game_wins[player_idx] += M_win
            Game_losses[player_idx] += M_loss
            Game_draws[player_idx] += M_draw

            # Valider les limites de wins et losses
            if Match_wins[player_idx] > standings_wins[player_idx] or Match_losses[player_idx] > standings_losses[player_idx]:
                return False

    # Validation finale du GWP si wins et losses sont complets
    for player, player_idx in player_indices.items():
        if Match_wins[player_idx] == standings_wins[player_idx] and Match_losses[player_idx] == standings_losses[player_idx]:
            # Lorsque les résultats sont complets pour un joueur, le GWP peut être validé
            total_games = Game_wins[player_idx] + Game_losses[player_idx] + Game_draws[player_idx]
            if total_games > 0:
                gwp_calculated = (Game_wins[player_idx] + (Game_draws[player_idx]/3)) / total_games
                if not np.isclose(gwp_calculated, standings_gwp[player_idx], atol=0.001):
                    return False

    return True



class Manatrader_fix_hidden_duplicate_name: 
    def calculate_stats_for_matches(self, base_table_res,permutation_res_table,masked_name):
        # Initialiser les stats

        opponent_names = set()
        for data in permutation_res_table.values():
                opponent_names.update(data['matchups']) 

        update_player_standings = []
        for player, data in permutation_res_table.items():
                computable_ogp_omwp = True
                number_of_opponent = 0
                total_omp = 0
                total_ogp = 0
                for opo in data['matchups']:
                    if re.fullmatch(r'.\*{10}.', opo):  
                       computable_ogp_omwp = False
                       break
                    if opo :
                        opponent_gwp = base_table_res[opo]["total_games_won"] / base_table_res[opo]["total_games_played"]  # GWP pour l'adversaire
                        total_ogp += opponent_gwp if opponent_gwp >= 0.3333 else 0.33
                        number_of_opponent += 1
                        # OMWP 
                        opponent_match_winrate = base_table_res[opo]["wins"] / (base_table_res[opo]["wins"] + base_table_res[opo]["losses"]) 
                        total_omp += opponent_match_winrate if opponent_match_winrate >= 0.3333 else 0.33
                
                update_player_standings.append(
                        Standing(
                        rank=None,
                        player=player,
                        points = (data['Match_wins']*3),
                        wins=data['Match_wins'],
                        losses=data['Match_losses'],
                        draws=0,
                        omwp= total_omp/number_of_opponent if computable_ogp_omwp else None,
                        gwp=(data['Game_wins'] + (data['Game_draws']/3))/(data['Game_wins'] + data['Game_draws'] +data['Game_losses']),
                        ogwp=total_ogp/number_of_opponent if computable_ogp_omwp else None
                        )
                        )

        for oponent_name in opponent_names:
            if oponent_name:
                masked_opponents = {name for name in base_table_res[oponent_name]['opponents'] if re.fullmatch(r'.\*{10}.', name)}
                if len(masked_opponents) == 1 and masked_name in masked_opponents:
                    player_omwp =0
                    number_of_player = 0
                    player_ogwp = 0
                    for player, data in permutation_res_table.items():
                        if oponent_name in data['matchups']:
                            number_of_player += 1
                            ogwp_ite = (data['Game_wins'] + (data['Game_draws']/3))/(data['Game_wins'] + data['Game_draws'] +data['Game_losses'])
                            omw_ite = data['Match_wins']/(data['Match_wins'] + data['Game_losses'])
                            player_omwp += omw_ite if omw_ite >= 0.3333 else 0.33
                            player_ogwp +=  ogwp_ite if ogwp_ite >= 0.3333 else 0.33
                    update_player_standings.append(
                    Standing(
                    rank=None,
                    player=oponent_name,
                    points = (base_table_res[oponent_name]['wins']*3),
                    wins=base_table_res[oponent_name]['wins'],
                    losses=base_table_res[oponent_name]['losses'],
                    draws=base_table_res[oponent_name]['draws'],

                    omwp= (base_table_res[oponent_name]['notmasked_opponent_result']['numerator_omwp'] + player_omwp)/(base_table_res[oponent_name]['notmasked_opponent_result']['total_opponents']+number_of_player),

                    gwp=base_table_res[oponent_name]['total_games_won']/base_table_res[oponent_name]['total_games_played'],

                    ogwp=(base_table_res[oponent_name]['notmasked_opponent_result']['numerator_ogwp'] + player_ogwp)/(base_table_res[oponent_name]['notmasked_opponent_result']['total_opponents']+number_of_player)
                    )
                    )


        return update_player_standings





            
    def From_player_to_result_dict_matches(self, player: str,rounds ,standings: List[Standing]):
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
        for round in rounds:
            for match in round.matches:
                p1_wins, p2_wins, draws = map(int, match.result.split('-'))
                # Identifier l'adversaire
                if match.player1 == player:
                    opponent = match.player2
                    player_wins, player_losses ,player_draw= p1_wins, p2_wins,draws
                elif match.player2 == player:
                    opponent = match.player1
                    player_wins, player_losses ,player_draw = p2_wins, p1_wins,draws
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
                total_games_played += player_wins + player_losses + player_draw
                total_games_won += player_wins + (player_draw/3)

                # Ajouter l'adversaire à la liste
                opponents.add(opponent)
        # Ajouter aux points (3 pour chaque victoire, 1 pour chaque égalité)
        points += 3 * wins + draws

        total_ogp = 0
        total_opponents = 0

        total_omp = 0
        for opponent in opponents:
        # Ignorer les adversaires qui correspondent à la regexp
            if opponent is None:
                continue
            elif re.fullmatch(r'.\*{10}.', opponent):
                continue
            # Récupérer les matchs de l'adversaire
            opponent_matches = [
                match for rnd in rounds
                for match in rnd.matches
                if match.player1 == opponent or match.player2 == opponent
            ]

            opponent_match_won = 0
            opponent_match_total_number = 0

            opponent_games_won = 0
            opponent_games_played = 0

            for match in opponent_matches:
                p1_wins, p2_wins, draws = map(int, match.result.split('-'))
                # verifier les bye
                if match.player1 == opponent:
                    opponent_games_won += (p1_wins + (draws/3))
                    opponent_games_played += p1_wins + p2_wins 
                    opponent_match_won += 1 if p1_wins > p2_wins else 0
                    opponent_match_total_number += 1
                elif match.player2 == opponent:
                    opponent_games_won += (p2_wins + (draws/3))
                    opponent_games_played += p1_wins + p2_wins 
                    opponent_match_won += 1 if p1_wins < p2_wins else 0
                    opponent_match_total_number += 1
                 
            # Calculer le pourcentage de victoires de l'adversaire (GWP pour l'adversaire)
            if opponent_games_played > 0:
                # OGWP
                opponent_gwp = opponent_games_won / opponent_games_played  # GWP pour l'adversaire
                total_ogp += opponent_gwp if opponent_gwp >= 0.3333 else 0.33
                total_opponents += 1
                # OMWP 
                opponent_match_winrate = opponent_match_won/opponent_match_total_number 
                total_omp += opponent_match_winrate if opponent_match_winrate >= 0.3333 else 0.33

        return {
        'wins' : wins,
        'losses' : losses,
        'draws' : draws,
        'total_games_played' : total_games_played,
        'total_games_won' : total_games_won,
        'opponents' : opponents,
        'notmasked_opponent_result' :{
           'numerator_ogwp': total_ogp if total_opponents > 0 else None ,
           'numerator_omwp':total_omp if total_opponents > 0 else None,
           'total_opponents' :total_opponents
        }
        }      


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
                    (standings_dict[player].losses > 0 and standings_dict[player].wins == 0 and custom_round(standings_dict[player].gwp, 2) == 0.33 and p1_wins != 1) 
                    )):
                    break
                elif (role == 'player2' and (
                    (p1_wins < p2_wins and standings_dict[player].wins == 0) or 
                    (p1_wins > p2_wins and standings_dict[player].losses == 0) or 
                    (p2_wins > 0 and standings_dict[player].gwp == 0) or 
                    (standings_dict[player].losses > 0 and standings_dict[player].wins == 0 and custom_round(standings_dict[player].gwp, 2) == 0.33 and p2_wins != 1)
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

    def clean_round_combinations(self,round_combinations):
        seen = set()  # Pour garder trace des dictionnaires déjà vus
        cleaned_round_data = []
        for round_item in round_combinations:
            # Convertir le defaultdict en un tuple des éléments
            item_tuple = tuple((key, tuple(value)) for key, value in round_item.items())
            if item_tuple not in seen:
                seen.add(item_tuple)  # Marquer ce dict comme vu
                cleaned_round_data.append(round_item)  # Ajouter le dict à la liste nettoyée
        return cleaned_round_data

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
            standings_gwp = np.array([dict_standings[player]["gwp"] for player in actual_players])

            # Générer les combinaisons nettoyées
            valid_combinations = [
                self.clean_round_combinations(self.generate_round_combinations(matches, actual_players, standings, round_name))
                for round_name, matches in matches_by_round.items()
            ]
                       
            total_permutations = 1
            for comb in valid_combinations:
                    total_permutations *= len(comb)
            
            if total_permutations < 1000:
                # Construire l'arbre des permutations
                root = TreeNode()
                build_tree(
                    root,
                    valid_combinations,  # Liste des rounds avec leurs combinaisons valides
                    validate_permutation,
                    player_indices,
                    standings_wins,
                    standings_losses,
                    standings_gwp,
                    n_players
                )

                # Extraire les permutations valides
                # valid_permutations = extract_valid_permutations(root)
                valid_permutations = [root]
                if valid_permutations:
                    assignments_per_masked[masked] = valid_permutations
                else :
                    assignments_per_masked[masked] = None
            elif total_permutations < 5000000000:
                # Parallélisation
                print(f"Utilisation de la parallélisation. : {total_permutations}")
                start_time = time.time()

                # Préparer les arguments pour la parallélisation
                first_round_xs = valid_combinations[0]  # Objets X du premier round
                remaining_rounds = valid_combinations[1:]  # Rounds restants
                tasks = [
                    (
                        x,
                        remaining_rounds,
                        validate_permutation,
                        player_indices,
                        standings_wins,
                        standings_losses,
                        standings_gwp,
                        n_players,
                    )
                    for x in first_round_xs
                ]

                # Diviser les tâches pour chaque round dans valid_combinations
                with Pool(cpu_count()) as pool:
                    results = pool.map(process_combination, tasks)

                # Fusionner les résultats valides
                # valid_permutations = [perm for result in results if result for perm in result]
                valid_permutations = results

                assignments_per_masked[masked] = valid_permutations if valid_permutations else None
                end_time = time.time()
                print(f"Temps total d'exécution pour {masked}: {end_time - start_time:.2f} secondes")
            else: 
                print(f"{masked} Permutations trop nombreuses (>1 milliard), assignation à None.")
                assignments_per_masked[masked] = None

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
        matching_permutation = {}
        for masked_name in duplicated_masked_names:
            print(f"Traitement pour le nom masqué : {masked_name}")
            masked_matches = self.collect_matches_for_duplicated_masked_names(
                {masked_name}, rounds
            )
                    
            # Étape 3
            assignments_per_masked = self.generate_assignments(
                masked_matches, masked_to_actual, standings
            )
            if assignments_per_masked is None:
                return None
            total_len = 0
            for trees in assignments_per_masked.values():
                for tree in trees:
                   total_len += count_nodes(tree)
            print(total_len)
            # temp refactoring remove after
            for key, value in assignments_per_masked.items():
                    matching_permutation[key] = value  # Créer une nouvelle clé si elle n'existe pas


        Determinist_permutation,remaining_matching_perm = self.generate_tournaments_with_unique_permutations(rounds, matching_permutation)
        previous_output = None
        current_output = (None, None)
        # Utilisation des valeurs actuelles pour la première itération
        local_deterministic_permutations = copy.deepcopy(Determinist_permutation)
        local_remaining_permutations = copy.deepcopy(remaining_matching_perm)
        while current_output != previous_output and local_remaining_permutations:
            # Mettre à jour l'entrée précédente avec la sortie actuelle
            previous_output = current_output
            
            # Appeler la méthode avec les entrées
            not_determinist_permutations, remaining_perm_not_determinist = self.process_permutations_with_recalculation(
                local_deterministic_permutations, 
                local_remaining_permutations, 
                standings #, True        
            )
            # Mettre à jour les entrées pour la prochaine itération
            local_deterministic_permutations =  copy.deepcopy(not_determinist_permutations)
            local_remaining_permutations = copy.deepcopy(remaining_perm_not_determinist)
            # Mettre à jour la sortie actuelle
            current_output = (not_determinist_permutations, remaining_perm_not_determinist)


        not_determinist_permutations, remaining_perm_not_determinist = self.process_permutations_with_recalculation(
            local_deterministic_permutations, 
            local_remaining_permutations, 
            standings , 
            True        
        )

        for rounds  in not_determinist_permutations :
            for match in rounds.matches: 
                if (match.player1 is not None and re.fullmatch(r'.\*{10}.', match.player1)) or (match.player2 is not None and re.fullmatch(r'.\*{10}.', match.player2)):
                    print(rounds)
                    print(match)
                    print(f"Masked Name present : {rounds}")
                    return None
    # Retourner les rounds mis à jour
        return not_determinist_permutations

    def process_permutations_with_recalculation(
        self,
        rounds: List[Round], 
        matching_permutation: Dict[str, Dict[str, List[List[Dict[str, List[RoundItem]]]]]], 
        standings: List[Standing],
        debug_print = False
        ):
        """Traiter les permutations avec recalcul des statistiques."""
        if debug_print:
            print("debug")
        modified_rounds = [
            Round(
                rnd.round_name,
                [RoundItem(match.player1, match.player2, match.result, match.id) for match in rnd.matches]
            )
            for rnd in rounds
        ]
        filterd_perm = {}
        initial_lengths = [(rnd.round_name, len(rnd.matches)) for rnd in rounds]

        player_with_real_name = set()
            # Identifier l'adversaire
        for round in modified_rounds:
            for match in round.matches:
                if match.player1 and not re.fullmatch(r'.\*{10}.', match.player1):
                        player_with_real_name.add(match.player1)
                if match.player2 and not re.fullmatch(r'.\*{10}.', match.player2):
                        player_with_real_name.add(match.player2)

        base_result_of_named_player = {}
        for ite_player in player_with_real_name:
           base_result_of_named_player[ite_player] = self.From_player_to_result_dict_matches(ite_player, modified_rounds ,standings)
        
        # def print_tree(node, depth=0):
        #     """Affiche récursivement l'arbre filtré."""
        #     if node:
        #         print("  " * depth + f"Combination: {node.combination}")
        #         for child in node.children:
        #             print_tree(child, depth + 1)

        # Commentaire a reprendre ici
        for masked_name, permutations in sorted(
                matching_permutation.items(), 
                key=lambda x: len(x[1])  # Trier par la longueur de la liste de defaultdict
            ):
            if len(permutations) == 1:
                Tree_with_correct_standings = [gather_stats_from_standings_tree(permutations[0],base_result_of_named_player,self.calculate_stats_for_matches,masked_name,self.compare_standings,standings)]
            else:
                # ajouter parrallelle ici
                continue

            if Tree_with_correct_standings and len(Tree_with_correct_standings) == 1:  # Cas où il y a une seule permutation (arbre)
                root_tree = Tree_with_correct_standings[0]  # Récupérer l'arbre unique
                if is_single_line_tree(root_tree):
                    print(f"Permutation unique attribuée : {masked_name}")
                    apply_tree_permutations(root_tree, modified_rounds,masked_name)
                    # A réfléchir propobablement méthode a def 
                    player_with_real_name = set()
                    # Identifier l'adversaire
                    for round in modified_rounds:
                        for match in round.matches:
                            if match.player1 and not re.fullmatch(r'.\*{10}.', match.player1):
                                    player_with_real_name.add(match.player1)
                            if match.player2 and not re.fullmatch(r'.\*{10}.', match.player2):
                                    player_with_real_name.add(match.player2)

                    base_result_of_named_player = {}
                    for ite_player in player_with_real_name:
                        base_result_of_named_player[ite_player] = self.From_player_to_result_dict_matches(ite_player, modified_rounds ,standings)
                    # Supprimer le masque traité des permutations restantes
                else:
                    filterd_perm[masked_name] = Tree_with_correct_standings

            else :
                filterd_perm[masked_name] = Tree_with_correct_standings


        final_lengths = [(rnd.round_name, len(rnd.matches)) for rnd in modified_rounds]
        for initial, final in zip(initial_lengths, final_lengths):
            if initial != final:
                raise ValueError(f"Round {initial[0]} a changé de nombre de matchs : {initial[1]} -> {final[1]}")
        print("fin de l'évaluation")
        return modified_rounds,filterd_perm

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

        # Longueurs initiales des rounds
        initial_lengths = [(rnd.round_name, len(rnd.matches)) for rnd in rounds]

        # Copie des permutations restantes
        remaining_permutations = matching_permutation.copy()

        # Parcours des masques et application des permutations uniques
        for masked_name, trees in matching_permutation.items():
            if len(trees) == 1:  # Cas où il y a une seule permutation (arbre)
                root_tree = trees[0]  # Récupérer l'arbre unique
                if is_single_line_tree(root_tree):
                    print(f"Permutation unique attribuée : {masked_name}")
                    apply_tree_permutations(root_tree, modified_rounds,masked_name)
                    # Supprimer le masque traité des permutations restantes
                    del remaining_permutations[masked_name]


        # Après les modifications, vérifier qu'aucun nouveau match n'a été ajouté
        final_lengths = [(rnd.round_name, len(rnd.matches)) for rnd in modified_rounds]
        # Vérification que les longueurs des rounds sont restées identiques
        for initial, final in zip(initial_lengths, final_lengths):
            if initial != final:
                raise ValueError(f"Round {initial[0]} a changé de nombre de matchs : {initial[1]} -> {final[1]}")

        return modified_rounds, remaining_permutations


    def compare_standings(self,real_standing, recalculated_standing,  compare_gwp=None, compare_omwp=None, compare_ogwp=None, tolerance=1e-3):
        """Compare deux standings et retourne True s'ils sont identiques, sinon False."""
        matches = (
            # real_standing.rank == recalculated_standing.rank and
            real_standing.points == recalculated_standing.points and
            real_standing.wins == recalculated_standing.wins and
            real_standing.losses == recalculated_standing.losses 
        )
        # Fonction pour comparer avec tolérance
        def are_close(val1, val2, tol):
            return abs(val1 - val2) <= tol

        # Comparaison optionnelle des pourcentages
        if compare_gwp and real_standing.gwp is not None and recalculated_standing.gwp is not None:
                        matches = matches and are_close(
                real_standing.gwp, 
                recalculated_standing.gwp, 
                tolerance
            )
        if compare_omwp and real_standing.omwp is not None and recalculated_standing.omwp is not None:

            matches = matches and are_close(
                real_standing.omwp, 
                recalculated_standing.omwp, 
                tolerance
            )
        if compare_ogwp and real_standing.ogwp is not None and recalculated_standing.ogwp is not None:
            matches = matches and are_close(
                real_standing.omwp, 
                recalculated_standing.omwp, 
                tolerance
            )

        return matches

    def update_modified_rounds_with_valid_permutation(self,modified_rounds, valide_perm,masked_name):
        for valid_permutation_tuple in valide_perm:
            for valid_permutation in valid_permutation_tuple: 
            # 'valid_permutation_tuple' est un tuple contenant un defaultdict
                for player, updated_rounds in valid_permutation.items():
                    for updated_match in updated_rounds:  # updated_round est un RoundItem, pas une liste
                        # Trouver le round et le match correspondant dans modified_rounds
                        for rnd in modified_rounds:
                            for match in rnd.matches:
                                if match.id == updated_match.id:  # Si l'ID du match correspond
                                    if match.player1 == masked_name:
                                        match.player1 = updated_match.player1
                                    # Appliquer les modifications du RoundItem dans modified_rounds
                                    if match.player2 == masked_name:
                                        match.player2 = updated_match.player2                          
        return modified_rounds  



