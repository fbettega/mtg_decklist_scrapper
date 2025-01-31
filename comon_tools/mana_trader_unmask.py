import json
import re
# import os
import sys
import math
from typing import List,Tuple,Dict, DefaultDict,Optional
from itertools import permutations,product,islice,chain, combinations
# import html
from models.base_model import *
from comon_tools.tools import *
# from collections import defaultdict
from multiprocessing import Pool, cpu_count
import numpy as np
import time
import copy
from collections import Counter




def chunked(iterable, size):
    """Divise une liste en sous-listes de taille `size`"""
    it = iter(iterable)
    return iter(lambda: list(islice(it, size)), [])

# generate permutation tree
class Assignation_TreeNode:
    """Représente un nœud dans l'arbre de permutations."""
    def __init__(self, level, current_mapping, used_players, remaining_masks):
        self.level = level  # Niveau actuel dans l'arbre
        self.current_mapping = current_mapping  # Association actuelle masques -> joueurs
        self.used_players = used_players  # Joueurs déjà utilisés
        self.remaining_masks = remaining_masks  # Masques restants à attribuer
        self.children = []  # Branches descendantes
        self.invalid_permutations = set()  # Permutations invalides déjà rencontrées à ce niveau

def is_valid_combination(player1, player2, p1_wins, p2_wins,standings_dict):
    """Vérifie si une combinaison de joueurs est valide selon leurs standings."""
    if not (isinstance(player1, str) and re.fullmatch(r'.\*{10}.', player1)):
        if (p1_wins > p2_wins and standings_dict[player1].wins == 0) or \
        (p1_wins < p2_wins and standings_dict[player1].losses == 0) or \
        (p1_wins > 0 and standings_dict[player1].gwp == 0) or \
        (standings_dict[player1].losses > 0 and standings_dict[player1].wins == 0 and 
            custom_round(standings_dict[player1].gwp, 2) == 0.33 and p1_wins != 1):
            return False
    if not (isinstance(player2, str) and re.fullmatch(r'.\*{10}.', player2)):
        if (p2_wins > p1_wins and standings_dict[player2].wins == 0) or \
        (p2_wins < p1_wins and standings_dict[player2].losses == 0) or \
        (p2_wins > 0 and standings_dict[player2].gwp == 0) or \
        (standings_dict[player2].losses > 0 and standings_dict[player2].wins == 0 and 
            custom_round(standings_dict[player2].gwp, 2) == 0.33 and p2_wins != 1):
            return False
    return True

def is_valid_partial_combination(current_mapping, masked_matches, standings_dict):
    """Vérifie si une configuration partielle est valide."""
    seen_players = set()
    local_mapping = copy.deepcopy(current_mapping) 
    for match in masked_matches:
        if match.player1 in current_mapping.keys() or match.player2 in current_mapping.keys() :
            if match.player1 in current_mapping.keys():
                player1 = local_mapping.get(match.player1)[0]
                local_mapping[match.player1] = local_mapping[match.player1][1:]
            else :
                player1 = match.player1
            # Assigner les joueurs réels aux masques pour player2
            if match.player2 in current_mapping.keys():
                player2 = local_mapping.get(match.player2)[0]
                local_mapping[match.player2] = local_mapping[match.player2][1:]
            else:
                player2 = match.player2

            if player1 in seen_players or player2 in seen_players:
                return False
            p1_wins, p2_wins, _ = map(int, match.result.split('-'))
            if not is_valid_combination(player1, player2, p1_wins, p2_wins, standings_dict):
                return False
            if  not (isinstance(player1, str) and re.fullmatch(r'.\*{10}.', player1)):
                seen_players.add(player1)
            if  not (isinstance(player2, str) and re.fullmatch(r'.\*{10}.', player2)):
                seen_players.add(player2)
    return True


def Assignation_build_tree(masked_keys, valid_player, masked_matches, standings_dict):
    """Construit l'arbre des permutations."""
    root = Assignation_TreeNode(level=0, current_mapping={}, used_players=set(), remaining_masks=masked_keys)
    stack = [root]  # Pile pour explorer l'arbre
    valid_combinations = []

    while stack:
        node = stack.pop()
        # Si nous avons atteint une configuration complète, vérifier et l'ajouter si valide
        if not node.remaining_masks:
            if is_valid_partial_combination(node.current_mapping, masked_matches, standings_dict):
                valid_combinations.append(node.current_mapping)
            continue

        # Sélectionner le prochain masque à traiter
        current_mask = node.remaining_masks[0]
        remaining_masks = node.remaining_masks[1:]

        # Explorer toutes les permutations possibles pour le masque actuel
        for perm in permutations(valid_player[current_mask]):
            if any(player in node.used_players for player in perm):
                continue  # Éviter les conflits de joueurs déjà utilisés

            # Créer un nouveau nœud avec la configuration mise à jour
            new_mapping = node.current_mapping.copy()
            new_mapping[current_mask] = perm
            new_used_players = node.used_players.union(perm)

            child_node = Assignation_TreeNode(
                level=node.level + 1,
                current_mapping=new_mapping,
                used_players=new_used_players,
                remaining_masks=remaining_masks
            )
            node.children.append(child_node)
            stack.append(child_node)  # Ajouter le nœud à la pile pour exploration

    return valid_combinations

def player_assignment_process_combination(task):
    """
    Traite chaque permutation (pour le premier round) et génère toutes les combinaisons possibles pour les autres masques.
    """
    x, remaining_masks, masked_matches, standings_dict, valid_player = task
    # Préparer la structure d'entrée pour Assignation_build_tree
    # Construire les combinaisons pour les autres masques
    if not is_valid_partial_combination(x, masked_matches, standings_dict):
        return

    valid_combinations = Assignation_build_tree(remaining_masks, valid_player, masked_matches, standings_dict)
    # Ajouter la permutation du premier round dans les combinaisons
    all_combinations = []
    for comb in valid_combinations:
        new_comb = copy.deepcopy(comb)
        # Ajouter la permutation du premier round pour le masque actuel
        for key, value in x.items():  # Parcours de chaque clé-valeur dans x
            new_comb[key] = value
        all_combinations.append(new_comb)

    return all_combinations
#######################################################################################################################
# stat tree 

class TreeNode:
    def __init__(self, combination=None):
        self.combination = combination  # La configuration actuelle du round
        self.children = []  # Les enfants du nœud
        self.valid = True  # Indique si ce nœud est valide

    def add_child(self, child):
        self.children.append(child)
     
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

def all_subsets(bad_tuples_dict):
    subsets = []
    keys = list(bad_tuples_dict.keys())
    for n in range(1, len(keys) + 1):  # Taille des sous-ensembles de 1 à len(bad_tuples_dict)
        for subset_keys in combinations(keys, n):
            # Générer les produits cartésiens pour les clés sélectionnées
            for tuples_combination in product(*(bad_tuples_dict[key] for key in subset_keys)):
                # Créer un dictionnaire pour ce sous-ensemble
                subset = dict(zip(subset_keys, tuples_combination))
                subsets.append(subset)
    return subsets

# Fonction pour trouver toutes les combinaisons minimales de tuples par clé qui vident remaining_combinations
def find_minimal_combinations(bad_tuples_dict, remaining_combinations):
    minimal_combinations = []
    keys_list = list(bad_tuples_dict.keys())  # Liste des clés de bad_tuples_dict

    # Tester toutes les tailles de combinaison de clés (de 1 à tout)
    for n in range(1, len(keys_list) + 1):
        for keys_subset in combinations(keys_list, n):
            # Construire un dictionnaire des positions interdites par clé
            positions_to_exclude = defaultdict(lambda: defaultdict(set))
            for key in keys_subset:
                for pos, players in bad_tuples_dict[key].items():
                    positions_to_exclude[key][pos].update(players)

            # Appliquer le filtre
            filtered_combinations = [
                combination
                for combination in remaining_combinations
                if all(
                    not any(
                        key in positions_to_exclude and pos in positions_to_exclude[key] and player in positions_to_exclude[key][pos]
                        for pos, player in enumerate(players)
                    )
                    for key, players in combination.items()
                )
            ]

            # Si remaining_combinations est vide, on garde cette combinaison
            if not filtered_combinations:
                minimal_combinations.append(set(keys_subset))

        # Dès qu'on trouve des solutions pour une taille `n`, on arrête
        if minimal_combinations:
            break

    return minimal_combinations

def backward_remove_matching_combinations(remaining_combinations, dead_combination_backward):
    filtered_combinations = []

    for combination in remaining_combinations:
        combination_values = set(combination.values())  # Ensemble des tuples de la combinaison
        
        # Vérifier si combination contient tous les tuples d'un élément de dead_combination_backward
        to_remove = any(set(dead_tuple) <= combination_values for dead_tuple in dead_combination_backward)

        if not to_remove:
            filtered_combinations.append(combination)

    return filtered_combinations

def build_tree_init_history(player_indices, base_result_from_know_player, history=None):
    n_players = len(player_indices)

    history = {
        "Match_wins": np.zeros(n_players, dtype=int),
        "Match_losses": np.zeros(n_players, dtype=int),
        "Game_wins": np.zeros(n_players, dtype=int),
        "Game_losses": np.zeros(n_players, dtype=int),
        "Game_draws": np.zeros(n_players, dtype=int),
        "matchups": {player: [] for player in player_indices.keys()}
    }

    # Mise à jour de l'historique avec les informations de base_result_from_know_player
    for player, idx in player_indices.items():
        if player in base_result_from_know_player:
            player_data = base_result_from_know_player[player]
            history["Match_wins"][idx] = player_data['wins']
            history["Match_losses"][idx] = player_data['losses']
            history["Game_wins"][idx] = player_data['total_games_won']
            history["Game_losses"][idx] = player_data['total_games_played'] - player_data['total_games_won']
            history["Game_draws"][idx] = player_data['draws']
            history["matchups"][player].extend(player_data['opponents'])

    return history

def build_tree(node, remaining_rounds,masked_name_matches, validate_fn,compute_stat_fun,compare_standings_fun, player_indices, standings_wins, standings_losses, standings_gwp,standings_omwp,
                standings_ogwp, base_result_from_know_player,standings,Global_bad_tupple_history = defaultdict(list),dead_combination_backward = set(), history=None, iteration=0):
    if history is None:
        history = build_tree_init_history(player_indices, base_result_from_know_player, history)

    if not node.valid:
        return

    # Si le nœud est une feuille, calcule les standings et évalue les comparaisons
    if not remaining_rounds:
        tree_standings_res = compute_stat_fun(base_result_from_know_player, history)
        standings_comparator_res = []
        # ajouter ici un merge avec le base_result_from_know_player
        for unsure_standings in tree_standings_res:
            res_comparator = compare_standings_fun(standings, unsure_standings, 3, 3, 3)
            standings_comparator_res.append(res_comparator)
        if all(standings_comparator_res):
            return node  # Retourne le nœud valide
        else:
            return None  # Feuille invalide

    current_round = remaining_rounds[0]
    valid_children = []
    remaining_combinations = current_round[:] 

    # Construire un dictionnaire stockant les positions interdites pour chaque joueur
    bad_tuples_dict = defaultdict(lambda: defaultdict(set))

    for player, bad_tuples in Global_bad_tupple_history.items():
        for bad_data in bad_tuples:
            if history["matchups"][player] == bad_data["history"]:
                for bad_player,pos in bad_data["tuple"].items():  # Lire la position et le joueur
                    if bad_player == player:  # Vérifier si c'est bien le joueur concerné
                        player_mask = f"{bad_player[0]}{'*' * 10}{bad_player[-1]}"
                        bad_tuples_dict[player_mask][pos].add(player)

    # Filtrer les combinaisons où un joueur est à une position interdite
    remaining_combinations = [
        combination
        for combination in remaining_combinations
        if all(
            not any(
                key in bad_tuples_dict and pos in bad_tuples_dict[key] and player in bad_tuples_dict[key][pos]
                for pos, player in enumerate(players)
            )
            for key, players in combination.items()
        )
    ]
    # print(f"Initial filter using other_tree iteration : {iteration} {bad_tuples_dict} Remaining perm : {len(remaining_combinations)} remove {len(current_round) - len(remaining_combinations)}")

    if len(remaining_combinations) == 0:
        # # Trouver les combinaisons qui vident `remaining_combinations`
        test_reaming_combination = current_round[:] 
        dead_key_list = find_minimal_combinations(bad_tuples_dict, test_reaming_combination)
        if len(dead_key_list) > 1:
            print("debug3")
        for keys in dead_key_list:
            temp_combination_set = set()
            for key in keys:
                bad_tuples_dict[key]
                temp_combination_set.add(node.combination[key])
            if iteration == 1:
                print("debug")
            dead_combination_backward.add(frozenset(temp_combination_set))

    while remaining_combinations:
        match_combination = remaining_combinations.pop(0)  #
        # Copier l'historique actuel pour ce chemin
        new_history = {
            "Match_wins": history["Match_wins"].copy(),
            "Match_losses": history["Match_losses"].copy(),
            "Game_wins": history["Game_wins"].copy(),
            "Game_losses": history["Game_losses"].copy(),
            "Game_draws": history["Game_draws"].copy(),
            "matchups": {player: matchups.copy() for player, matchups in history["matchups"].items()}
        }

        new_masked_name_matches = copy.deepcopy(masked_name_matches)
        used_players = defaultdict(int)
        for match in new_masked_name_matches[iteration].matches:
            # Remplacer player1 si c'est un nom masqué
            if match.player1 in match_combination:
                used_players[match.player1] += 1
                player1_real_names = match_combination[match.player1]
                match.player1 = player1_real_names[used_players[match.player1] -1]
            # Remplacer player2 si c'est un nom masqué
            if match.player2 in match_combination:
                used_players[match.player2] += 1
                player2_real_names = match_combination[match.player2]  # Correction ici
                match.player2 = player2_real_names[used_players[match.player2] -1]  # Utiliser player2_real_names

        # Mettre à jour les statistiques pour la combinaison actuelle
        valid,problematic_player = validate_fn(new_masked_name_matches[iteration].matches, new_history, player_indices, standings_wins, standings_losses, standings_gwp,iteration,standings,base_result_from_know_player)

        if not valid:
            # Ajouter la permutation problématique pour la transmission horizontale
            for suspect_player in problematic_player:
                for masked_name, player_tuple in match_combination.items():
                    if suspect_player in player_tuple: 
                        remaining_combinations =  filter_other_node_combinations(remaining_combinations, masked_name, player_tuple)
                        # Trouver la position exacte de suspect_player
                        player_position = player_tuple.index(suspect_player)
                        Global_bad_tupple_history[suspect_player].append({
                            'tuple' : {suspect_player : player_position},
                            'history' : history["matchups"][suspect_player].copy()
                        })
                        # print(f"iteration : {iteration} remove {player_tuple} Remaining perm : {len(remaining_combinations)} : remove : {len(current_round) - len(remaining_combinations)}")
            if iteration == 0:
                for suspect_player in problematic_player:
                    for masked_name, player_tuple in match_combination.items():
                        print(f"iteration : {iteration} test on ite 0 remove {player_tuple} Remaining perm : {len(remaining_combinations)} : remove : {len(current_round) - len(remaining_combinations)}")
                        sys.stdout.flush()
            continue  # Ignorez cette combinaison invalide
        
        if valid:
            if iteration > 4:
                print(iteration)
            child_node = TreeNode(match_combination)
            child_node.valid = True
            node.add_child(child_node)
            previous_dead_combination_backward = copy.deepcopy(dead_combination_backward)
            # Appel récursif avec l'historique mis à jour
            result = build_tree(
                child_node,
                remaining_rounds[1:],
                new_masked_name_matches,
                validate_fn,
                compute_stat_fun,
                compare_standings_fun,
                player_indices,
                standings_wins,
                standings_losses,
                standings_gwp,
                standings_omwp,
                standings_ogwp,
                base_result_from_know_player,
                standings,
                Global_bad_tupple_history,
                dead_combination_backward,
                new_history,
                iteration + 1
            )
            if result is None and dead_combination_backward != previous_dead_combination_backward: 
                len_before_filter =  len(remaining_combinations)  
                if iteration == 0:
                    print("degug")      
                    remaining_combinations2 = backward_remove_matching_combinations(remaining_combinations, dead_combination_backward) 
                    print(f"iteration : {iteration} Backward remove {dead_combination_backward} Remaining perm : {len(remaining_combinations2)}/{len(current_round)} : remove : {len_before_filter - len(remaining_combinations2)}")          
                
                remaining_combinations = backward_remove_matching_combinations(remaining_combinations, dead_combination_backward) 
                print(f"iteration : {iteration} Backward remove {dead_combination_backward} Remaining perm : {len(remaining_combinations)}/{len(current_round)} : remove : {len_before_filter - len(remaining_combinations)}") 
                sys.stdout.flush()
                # needed to reset after clearing this level 
                dead_combination_backward = set()
                previous_dead_combination_backward = set()
            if len(remaining_combinations) == 0 and iteration == 0:
                print("problem")

            if result is not None:
                valid_children.append(child_node)
    # Met à jour les enfants du nœud actuel avec les enfants valides
    node.children = valid_children

    # Si le nœud a au moins un enfant valide, retourne-le ; sinon, retourne None
    if valid_children and valid:
        return node
    else:
        return None

def filter_other_node_combinations(remaining_combinations, masked_name, player_tuple):
    """
    Supprime les éléments de remaining_combinations contenant exactement 
    (masked_name, player_tuple).
    
    Args:
        remaining_combinations (list): Liste de dictionnaires de type match_combination.
        masked_name (str): Le nom masqué à vérifier.
        player_tuple (tuple): Le tuple de joueurs à vérifier.
    
    Returns:
        list: Liste filtrée de remaining_combinations.
    """
    return [
        combination
        for combination in remaining_combinations
        if not (masked_name in combination and combination[masked_name] == player_tuple)
    ]


def custom_round(value, decimals=0):
    # multiplier = 10**decimals
    epsilon = 10 ** (-decimals -3)
    return round(value + epsilon, decimals)


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


def validate_permutation(match_combination, history, player_indices, standings_wins, standings_losses, standings_gwp,ite,standings,base_result_from_know_player):
    """
    Valider une permutation partielle dans le cadre de la construction de l'arbre.
    """

    Match_wins = history["Match_wins"]
    Match_losses = history["Match_losses"]
    Game_wins = history["Game_wins"]
    Game_losses = history["Game_losses"]
    Game_draws = history["Game_draws"]
    matchups = history["matchups"]
    modified_players = set()  # Suivi des joueurs dont les statistiques ont été modifiées

    for round_item in match_combination:
        # Traiter à la fois player1 et player2 sans conditions if/elif
        results_match = list(map(int, round_item.result.split('-')))
        players = [(round_item.player1, round_item.player2, *round_item.scores[0], *results_match),
                    (round_item.player2, round_item.player1, *round_item.scores[1],results_match[1], results_match[0], results_match[2])]
        
        if round_item.player1 in modified_players or round_item.player2 in modified_players:
            print("problem") 
        modified_players.add(round_item.player1)
        modified_players.add(round_item.player2)

        # Itérer sur les deux joueurs de chaque match
        for player, opponent, win, loss, M_win, M_loss, M_draw in players:
            # Vérifier que le joueur n'est pas None et valider les résultats
            if player is not None:
                if opponent in matchups[player]:
                    # if ite > 1:                    
                    # print("opo")
                    return False,(player,opponent)
                if not re.fullmatch(r'.\*{10}.', opponent):
                    matchups[player].extend([opponent])

                # Mettre à jour les statistiques
                player_idx = player_indices[player]
                Match_wins[player_idx] += win
                Match_losses[player_idx] += loss
                Game_wins[player_idx] += M_win
                Game_losses[player_idx] += M_loss
                Game_draws[player_idx] += M_draw

                # Valider les limites de wins et losses
                if Match_wins[player_idx] > standings_wins[player_idx] or Match_losses[player_idx] > standings_losses[player_idx]:
                    # if ite >0:
                    #     # print(base_result_from_know_player[player])
                    #     print("win or loose")
                    return False,(player,opponent)
                
    # Validation finale du GWP uniquement pour les joueurs modifiés
    for player in modified_players:
        player_idx = player_indices[player]
        if Match_wins[player_idx] == standings_wins[player_idx] and Match_losses[player_idx] == standings_losses[player_idx]:
            # Lorsque les résultats sont complets pour un joueur, le GWP peut être validé
            total_games = Game_wins[player_idx] + Game_losses[player_idx] + Game_draws[player_idx]
            if total_games > 0:
                gwp_calculated = (Game_wins[player_idx] + (Game_draws[player_idx] / 3)) / total_games
                if not np.isclose(gwp_calculated, standings_gwp[player_idx], atol=0.001):
                    # if ite > 0:
                    #     print("debug")
                    return False,(player,list(matchups[player])[-1])
                
    return True, "ok"


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
        masked_name_matches,
        validate_fn,
        compute_stat_fun,
        compare_standings_fun,
        player_indices,
        standings_wins, 
        standings_losses, 
        standings_gwp,
        standings_omwp,
        standings_ogwp, 
        base_result_of_named_player,
        standings
    ) = task
    # Construire un arbre pour explorer les permutations valides des rounds restants
    root = TreeNode()  # Nœud racine de l'arbre


    build_tree(
        root,
        [first_round_combination] + remaining_rounds, 
        masked_name_matches,
        validate_fn,
        compute_stat_fun,
        compare_standings_fun,
        player_indices,
        standings_wins, 
        standings_losses, 
        standings_gwp,
        standings_omwp,
        standings_ogwp, 
        base_result_of_named_player,
        standings
    )

    # Extraire les permutations valides à partir de l'arbre

    return root


class Manatrader_fix_hidden_duplicate_name: 
    def calculate_stats_for_matches(self, base_table_res,permutation_res_table):
        # Initialiser les stats
        opponent_names = set()
        for data in permutation_res_table.values():
                opponent_names.update(x for x in data['matchups'] if x is not None)

        update_player_standings = []
        for player, data in permutation_res_table.items():
                computable_ogp_omwp = True
                number_of_opponent = 0
                total_omp = 0
                total_ogp = 0
                if len(permutation_res_table[player]['matchups']) == 0:
                    computable_ogp_omwp = False
                else:
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
            masked_opponents = {name for name in base_table_res[oponent_name]['opponents'] if name and re.fullmatch(r'.\*{10}.', name)}
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


                opponent_data = base_table_res.get(oponent_name, {})
                notmasked_result = opponent_data.get('notmasked_opponent_result', {})

                # Gestion de total_opponents avec valeur par défaut 0
                opoponent_numbers_base = notmasked_result.get('total_opponents', 0) or 0
                opoponent_numbers = opoponent_numbers_base + number_of_player

                # Gestion des valeurs manquantes pour éviter les erreurs
                numerator_omwp = notmasked_result.get('numerator_omwp', 0) or 0
                numerator_ogwp = notmasked_result.get('numerator_ogwp', 0) or 0
                total_games_won = opponent_data.get('total_games_won', 0) or 0
                total_games_played = opponent_data.get('total_games_played', 1) or 1  # Éviter la division par zéro

                update_player_standings.append(
                    Standing(
                        rank=None,
                        player=oponent_name,
                        points=(opponent_data.get('wins', 0) * 3),
                        wins=opponent_data.get('wins', 0),
                        losses=opponent_data.get('losses', 0),
                        draws=opponent_data.get('draws', 0),
                        omwp=(numerator_omwp + player_omwp) / opoponent_numbers,
                        gwp=total_games_won / total_games_played,
                        ogwp=(numerator_ogwp + player_ogwp) / opoponent_numbers
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


    def generate_round_combinations(self, round_obj: Round, actual_players, standings):
        """Générer les permutations pour un round donné en tenant compte du nombre de matchs du joueur."""
        # Préparation des données
        round_combinations = []
        standings_dict = {standing.player: standing for standing in standings}
        player_match_count = {player: standings_dict[player].wins + standings_dict[player].losses for player in standings_dict}
        match_round = int(round_obj.round_name.replace('Round ', ''))     
        # Filtrage des joueurs valides
        valid_player = defaultdict(list)
        number_of_filterd_player = 0
        for masked, possible_players in actual_players.items():
            filtered_players = [
                player for player in possible_players
                if player_match_count.get(player, 0) >= match_round
            ]
            if filtered_players:  # Ajouter seulement si la liste n'est pas vide
                number_of_filterd_player += 1
                valid_player[masked] = filtered_players

        # Identifier les matchs avec des noms masqués
        masked_matches = [
            match for match in round_obj.matches
            if match.player1 in valid_player or match.player2 in valid_player
        ]
        masked_keys = list(valid_player.keys())
        # Générer les combinaisons
        largest_mask = max(
            [key for key, value in valid_player.items() if len(value) > 5],
            key=lambda key: len(valid_player[key]),
            default=None
            )
        first_round_xs = list(permutations(valid_player.get(largest_mask, [])))  # Objets X du premier round
        remaining_mask = [mask for mask in valid_player.keys() if mask != largest_mask]  # Rounds restants
        if len(first_round_xs) > 1:
            tasks = [
                (
                    {largest_mask: x},
                    remaining_mask,
                    masked_matches,
                    standings_dict,
                    valid_player
                )
                for x in first_round_xs  # Distribuer les permutations du premier round en tâches
            ]
            # Étape 3 : Diviser les tâches pour chaque round et paralléliser leur traitement
            with Pool(cpu_count()) as pool:
                multiproc_res = pool.map(player_assignment_process_combination, tasks)
                permutation_assignment = list(chain.from_iterable(filter(None, multiproc_res)))

        else :
              permutation_assignment =  Assignation_build_tree(remaining_mask, valid_player, masked_matches, standings_dict)

        seen = set()
        for perm in permutation_assignment:
            # Convertir le dictionnaire en une version immuable (tuple des items triés)
            perm_tuple = tuple(sorted(perm.items()))
            if perm_tuple in seen:
                print("Il y a des doublons dans permutation_assignment.")
            seen.add(perm_tuple)


        return permutation_assignment


    def organize_matches_by_round(self, matches_info):
        """Organiser les matchs par round."""
        matches_by_round = defaultdict(list)
        for role, round_name, match in matches_info:
            matches_by_round[round_name].append((role, match))
        return matches_by_round

    def generate_assignments(self,  rounds: list[Round], masked_to_actual, standings):
        """Optimiser la génération des assignments avec multiprocessing."""
        assignments_per_masked = {}
        dict_standings = self.standings_to_dict(standings)
        assignments_per_round = []
        start_time = time.time()
        for round_obj in rounds:
            print(round_obj.round_name)
            # if round_obj.round_name == "Round 5":
            valid_combinations = self.generate_round_combinations(round_obj, masked_to_actual, standings)
            assignments_per_round.append( valid_combinations)
        end_time = time.time()
        print(f"Temps total d'exécution pour genérer les perm: {end_time - start_time:.2f} secondes")
        return assignments_per_round
    
    def find_real_tournament_from_permutation(self,assignments_per_masked,masked_to_actual, rounds, standings):
        # Préparer les données
        # Identifier les matchs avec des noms masqués
        full_name_matches = [
            Round(
                round_obj.round_name,
                [
                    match for match in round_obj.matches
                        if not (
                            (isinstance(match.player1, str) and re.fullmatch(r'.\*{10}.', match.player1)) or
                            (isinstance(match.player2, str) and re.fullmatch(r'.\*{10}.', match.player2))
                        )
                ]
            )
            for round_obj in rounds
        ]

        masked_name_matches = [
            Round(
                round_obj.round_name,
                [
                    match for match in round_obj.matches
                        if (
                            (isinstance(match.player1, str) and re.fullmatch(r'.\*{10}.', match.player1)) or
                            (isinstance(match.player2, str) and re.fullmatch(r'.\*{10}.', match.player2))
                        )
                ]
            )
            for round_obj in rounds
        ]
        # dict_standings = self.standings_to_dict(standings)
        # for round_obj in full_name_matches:
        #     print(f"Round: {round_obj.round_name}")
        #     for match in round_obj.matches:
        #         print(f"Match: {match.player1} vs {match.player2}")
        player_with_real_name = set()
            # Identifier l'adversaire
        for round in full_name_matches:
            for match in round.matches:
                if match.player1 and not re.fullmatch(r'.\*{10}.', match.player1):
                        player_with_real_name.add(match.player1)
                if match.player2 and not re.fullmatch(r'.\*{10}.', match.player2):
                        player_with_real_name.add(match.player2)

        base_result_of_named_player = {}
        for ite_player in player_with_real_name:
           base_result_of_named_player[ite_player] = self.From_player_to_result_dict_matches(ite_player, full_name_matches ,standings)


        player_indices = {standing.player: idx for idx, standing in enumerate(standings)}
        n_players = len(standings)
        # Créer les numpy arrays en extrayant les attributs des instances Standing
        # Créer les numpy arrays en extrayant les attributs des instances Standing
        standings_wins = np.array([standing.wins for standing in standings])
        standings_losses = np.array([standing.losses for standing in standings])
        standings_gwp = np.array([standing.gwp for standing in standings])
        standings_omwp = np.array([standing.omwp for standing in standings])
        standings_ogwp = np.array([standing.ogwp for standing in standings])

        # Parallélisation
        start_time = time.time()
        # Préparer les arguments pour la parallélisation
        # first_round_xs = assignments_per_masked[0]  # Objets X du premier round
        # remaining_rounds = assignments_per_masked[1:]  # Rounds restants
        # chunk_size = 100  # Ajuste selon la taille souhaitée
        # first_round_chunks = list(chunked(first_round_xs, chunk_size))
        # tasks = [
        #     (
        #         chunk,
        #         remaining_rounds,
        #         masked_name_matches,
        #         validate_permutation,
        #         self.calculate_stats_for_matches,
        #         self.compare_standings,
        #         player_indices,
        #         standings_wins, 
        #         standings_losses, 
        #         standings_gwp,
        #         standings_omwp,
        #         standings_ogwp, 
        #         base_result_of_named_player,
        #         standings
        #     )
        #     for chunk in first_round_chunks
        # ]
        # # Diviser les tâches pour chaque round dans valid_combinations
        # with Pool(cpu_count()) as pool:
        #     results = pool.map(process_combination, tasks)

        # Fusionner les résultats valides
        # valid_permutations = [perm for result in results if result for perm in result]
        # Préparer les arguments pour la parallélisation
        root = TreeNode()  # Nœud racine de l'arbre
        build_tree(
            root,
            assignments_per_masked, 
            masked_name_matches,
            validate_permutation,
            self.calculate_stats_for_matches,
            self.compare_standings,
            player_indices,
            standings_wins, 
            standings_losses, 
            standings_gwp,
            standings_omwp,
            standings_ogwp, 
            base_result_of_named_player,
            standings
        )

        # Fusionner les résultats valides
        # valid_permutations = [perm for result in results if result for perm in result]

        end_time = time.time()
        print(f"Temps total traitement des arbres: {end_time - start_time:.2f} secondes")
        return root


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
        # on repete tout ici pour tout faire en une fois 
        matching_permutation = {}
        assignments_per_masked = self.generate_assignments(
            rounds, masked_to_actual, standings
        )
        
        print("ok")
        resulting_tree =  self.find_real_tournament_from_permutation(
            assignments_per_masked,masked_to_actual, rounds, standings
        )

        print(f"Traitement pour le nom masqué :")



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