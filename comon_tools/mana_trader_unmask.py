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
from multiprocessing import Pool, cpu_count,Manager
import numpy as np
import time
import copy
from collections import Counter



################################################
# root method for multi processing
############
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
         # modif a verif
            np.isclose((standings_dict[player1].gwp),0.33,atol=0.01) and p1_wins != 1):
            return False
    if not (isinstance(player2, str) and re.fullmatch(r'.\*{10}.', player2)):
        if (p2_wins > p1_wins and standings_dict[player2].wins == 0) or \
        (p2_wins < p1_wins and standings_dict[player2].losses == 0) or \
        (p2_wins > 0 and standings_dict[player2].gwp == 0) or \
        (standings_dict[player2].losses > 0 and standings_dict[player2].wins == 0 and 
         # modif a verif
            np.isclose((standings_dict[player2].gwp),0.33,atol=0.01) and p2_wins != 1):
            return False
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
###########



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
    
def apply_tree_permutations(node, modified_rounds, masked_name,iteration = 0):
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
    
    used_players = defaultdict(int)
    # match_combination = node.combination[masked_name]
    for match in modified_rounds[iteration].matches:
        # Remplacer player1 si c'est un nom masqué
        if match.player1 in node.combination:
            used_players[match.player1] += 1
            player1_real_names = node.combination[match.player1]
            match.player1 = player1_real_names[used_players[match.player1] -1]
        # Remplacer player2 si c'est un nom masqué
        if match.player2 in node.combination:
            used_players[match.player2] += 1
            player2_real_names = node.combination[match.player2]  # Correction ici
            match.player2 = player2_real_names[used_players[match.player2] -1]  # Utiliser player2_real_names

    for child in node.children:
        apply_tree_permutations(child, modified_rounds, masked_name, iteration + 1)
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
def combination_has_forbidden(combination, positions_to_exclude):
    """
    Renvoie True si pour au moins une clé présente dans positions_to_exclude, 
    la combinaison possède dans la position indiquée un joueur interdit.
    """
    # Pour chaque clé qui doit être exclue
    for key, pos_forbidden in positions_to_exclude.items():
        # Si la clé n'est pas dans la combinaison, on ne peut rien vérifier pour celle-ci
        if key not in combination:
            continue
        players = combination[key]
        # Pour chaque position et ensemble de joueurs interdits pour cette clé
        for pos, forbidden_players in pos_forbidden.items():
            # Si la position est dans le tuple et que le joueur à cette position est interdit
            if pos < len(players) and players[pos] in forbidden_players:
                return True
    return False

def find_minimal_combinations(bad_tuples_dict, remaining_combinations):
    minimal_combinations = []
    keys_list = list(bad_tuples_dict.keys())

    # Tester les combinaisons de clés par ordre croissant de taille
    for n in range(1, len(keys_list) + 1):
        for keys_subset in combinations(keys_list, n):
            # Construire le dictionnaire des positions interdites pour le sous-ensemble courant
            # positions_to_exclude aura la forme : { key: { pos: set(de joueurs) } }
            positions_to_exclude = {}
            for key in keys_subset:
                # On copie le dictionnaire pour éviter les appels multiples à defaultdict
                # (il s'agit d'une copie simple car les valeurs sont des ensembles)
                positions_to_exclude[key] = {}
                for pos, players in bad_tuples_dict[key].items():
                    positions_to_exclude[key][pos] = set(players)
            
            # Filtrer les combinaisons restantes : on ne garde que celles qui ne satisfont pas 
            # la contrainte (c'est-à-dire celles qui ont au moins un joueur différent)
            filtered_combinations = [
                combination
                for combination in remaining_combinations
                if not combination_has_forbidden(combination, positions_to_exclude)
            ]

            # Si plus aucune combinaison ne reste, le sous-ensemble courant est minimal
            if not filtered_combinations:
                # Pour chaque clé du sous-ensemble, rassembler l'ensemble des joueurs interdits
                players_for_keys = {}
                for key in keys_subset:
                    union_players = set()
                    for players in bad_tuples_dict[key].values():
                        union_players.update(players)
                    players_for_keys[key] = union_players

                minimal_combinations.append(players_for_keys)

        # Dès qu'on trouve une solution minimale (pour une taille donnée), on arrête la recherche
        if minimal_combinations:
            break

    return minimal_combinations

def backward_remove_matching_combinations(remaining_combinations, dead_combination_backward):
    """
    Filtre les combinaisons de remaining_combinations.
    Pour chaque combinaison, on vérifie pour chacune des entrées de dead_combination_backward
    (c'est-à-dire pour chaque (clé, joueur, position)) que, si la clé est présente dans la combinaison,
    alors le tuple associé à cette clé possède bien le joueur à la position indiquée.
    Si pour toutes les entrées la condition est remplie, la combinaison est considérée comme "à filtrer"
    et n'est pas ajoutée à la liste finale.
    """
    filtered_combinations = []
    
    for combination in remaining_combinations:
        # On part de l'hypothèse que la combinaison correspond à toutes les contraintes
        remove_this = True  
        for key, player, pos in dead_combination_backward:
            # Si la clé n'est pas dans la combinaison, ou si le tuple associé ne contient pas
            # le joueur à la position indiquée, alors la combinaison ne doit pas être filtrée.
            if key not in combination:
                remove_this = False
                break
            # Récupérer le tuple associé à la clé
            players_tuple = combination[key]
            # Vérifier que la position existe et que le joueur à cette position correspond
            if pos >= len(players_tuple) or players_tuple[pos] != player:
                remove_this = False
                break
        
        # On conserve la combinaison uniquement si remove_this est False
        if not remove_this:
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
            history["Game_losses"][idx] = player_data['total_games_played'] - (player_data['total_games_won'] + player_data['total_game_draw'])
            history["Game_draws"][idx] = player_data['total_game_draw']
            history["matchups"][player].extend(player_data['opponents'])

    return history

def build_tree(node, remaining_rounds,masked_name_matches, validate_fn,compute_stat_fun,compare_standings_fun, player_indices, standings_wins, standings_losses, standings_gwp,standings_omwp,
                standings_ogwp, base_result_from_know_player,standings,full_list_of_masked_player,Global_bad_tupple_history = defaultdict(list),
                dead_combination_backward = [], history=None, iteration=0,max_ite_reach = 0):
    if history is None:
        history = build_tree_init_history(player_indices, base_result_from_know_player, history)

    if not node.valid:
        return
    # Si le nœud est une feuille, calcule les standings et évalue les comparaisons

    if not remaining_rounds:
        tree_standings_res = compute_stat_fun(base_result_from_know_player, history,full_list_of_masked_player,player_indices)
        standings_comparator_res = []
        # ajouter ici un merge avec le base_result_from_know_player

        for unsure_standings in tree_standings_res:
            standings_ite_current = standings[unsure_standings.player ]
            res_comparator = compare_standings_fun(standings_ite_current, unsure_standings, 3, 3, 3)
            standings_comparator_res.append(res_comparator)
        #     if not res_comparator:
        #         print(f"real standings {standings_ite_current}")
        #         print(f"Calculate standings {unsure_standings}")
        # print("###########################################################################################")
        if all(standings_comparator_res):
            return [node]  # Retourne le nœud valide
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
        valid,problematic_player = validate_fn(new_masked_name_matches[iteration].matches, new_history, player_indices, standings_wins, standings_losses, standings_gwp,full_list_of_masked_player)

        if not valid:
            # Ajouter la permutation problématique pour la transmission horizontale
            for suspect_player in problematic_player:
                for masked_name, player_tuple in match_combination.items():
                    if suspect_player in player_tuple: 
                        remaining_combinations2 =  filter_other_node_combinations(remaining_combinations, masked_name, player_tuple)
                        # Trouver la position exacte de suspect_player
                        player_position = player_tuple.index(suspect_player)
                        Global_bad_tupple_history[suspect_player].append({
                            'tuple' : {suspect_player : player_position},
                            'history' : history["matchups"][suspect_player].copy()
                        })
                        # print(f"iteration : {iteration} remove {player_tuple} Remaining perm : {len(remaining_combinations)} : remove : {len(current_round) - len(remaining_combinations)}")
            continue  # Ignorez cette combinaison invalide
        
        if valid:
            # if iteration > max_ite_reach:
            #     max_ite_reach = copy.deepcopy(iteration)
            #     print(max_ite_reach)
            #     sys.stdout.flush()
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
                full_list_of_masked_player,
                Global_bad_tupple_history,
                dead_combination_backward,
                new_history,
                iteration + 1,
                max_ite_reach
            )

            if result is not None:
                valid_children.append(child_node)
    # Met à jour les enfants du nœud actuel avec les enfants valides
    node.children = valid_children
    return valid_children if valid_children else []


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


def validate_permutation(match_combination, history, player_indices, standings_wins, standings_losses, standings_gwp,full_list_of_masked_player):
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
        if not re.fullmatch(r'.\*{10}.', round_item.player1) :
            modified_players.add(round_item.player1)
        if not re.fullmatch(r'.\*{10}.', round_item.player2) :
            modified_players.add(round_item.player2)

        # Itérer sur les deux joueurs de chaque match
        for player, opponent, win, loss, M_win, M_loss, M_draw in players:
            # Vérifier que le joueur n'est pas None et valider les résultats
            if  player in full_list_of_masked_player:
                if player is not None :
                    if opponent in matchups[player]:
                        return False,(player,opponent)
                    if not re.fullmatch(r'.\*{10}.', opponent):
                        matchups[player].extend([opponent])
                        matchups[opponent].extend([player])
                    # Mettre à jour les statistiques
                    player_idx = player_indices[player]
                    Match_wins[player_idx] += win
                    Match_losses[player_idx] += loss
                    Game_wins[player_idx] += M_win
                    Game_losses[player_idx] += M_loss
                    Game_draws[player_idx] += M_draw

                    # Valider les limites de wins et losses
                    if Match_wins[player_idx] > standings_wins[player_idx] or Match_losses[player_idx] > standings_losses[player_idx]:
                        # print(base_result_from_know_player[player])
                        return False,(player,opponent)
            else :
                continue

    # Validation finale du GWP uniquement pour les joueurs modifiés
    for player in modified_players:
        player_idx = player_indices[player]
        if Match_wins[player_idx] == standings_wins[player_idx] and Match_losses[player_idx] == standings_losses[player_idx] and ((standings_wins[player_idx] + standings_losses[player_idx]) ==  len(matchups[player])):
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
        standings,
        full_list_of_masked_player
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
        standings,
        full_list_of_masked_player
    )

    # Extraire les permutations valides à partir de l'arbre

    return root
#######################################################################################################################
# update stat tree
def update_and_validate_tree(node, updated_rounds, validate_fn, compute_stat_fun, compare_standings_fun, 
                            player_indices, standings_wins, standings_losses, standings_gwp, standings_omwp, 
                            standings_ogwp, base_result_from_know_player, standings, full_list_of_masked_player, history = None,
                            iteration=0):
    """
    Met à jour l'arbre avec les nouvelles données de rounds et vérifie sa validité.
    Supprime les branches invalides et tente de reconstruire si nécessaire.
    """

    if not node:
        return None  # Si le nœud est vide, on l’ignore
    # Si le nœud est le premier et n'a pas de combinaison, on met à jour ses enfants directement
    if node.combination is None:
        new_children = []
        for child in node.children:
            updated_child = update_and_validate_tree(child,
                updated_rounds, validate_fn, compute_stat_fun,
                compare_standings_fun, player_indices, standings_wins,
                standings_losses, standings_gwp, standings_omwp, standings_ogwp,
                base_result_from_know_player, standings, full_list_of_masked_player, history,iteration)
            if updated_child:
                new_children.append(updated_child)

        node.children = new_children  # Mise à jour des enfants
        return node if new_children else None  # Supprime l’arbre s'il devient vide

    if history is None:
        history = build_tree_init_history(player_indices, base_result_from_know_player, history)
    # Mise à jour des informations de l'arbre avec les nouveaux rounds
    new_masked_name_matches = copy.deepcopy(updated_rounds)
    if iteration >= len(new_masked_name_matches):
        print(f"Attention : iteration {iteration} dépasse la taille de new_masked_name_matches ({len(new_masked_name_matches)})")
    # Appliquer les nouvelles permutations sur ce nœud
    new_history = {
        "Match_wins": history["Match_wins"].copy(),
        "Match_losses": history["Match_losses"].copy(),
        "Game_wins": history["Game_wins"].copy(),
        "Game_losses": history["Game_losses"].copy(),
        "Game_draws": history["Game_draws"].copy(),
        "matchups": {player: matchups.copy() for player, matchups in history["matchups"].items()}
    }
    used_players = defaultdict(int)
    for match in new_masked_name_matches[iteration].matches:
        if match.player1 in node.combination:
            used_players[match.player1] += 1
            player1_real_names = node.combination[match.player1]
            match.player1 = player1_real_names[used_players[match.player1] - 1]
        
        if match.player2 in node.combination:
            used_players[match.player2] += 1
            player2_real_names = node.combination[match.player2]
            match.player2 = player2_real_names[used_players[match.player2] - 1]

    # Valider la mise à jour
    valid, problematic_players = validate_fn(new_masked_name_matches[iteration].matches, new_history, 
                                             player_indices, standings_wins, standings_losses, standings_gwp, 
                                             full_list_of_masked_player)
    
    if not valid:
        print(f"Nœud invalide après mise à jour, suppression de {node.combination}")
        return None  # Ce nœud est devenu invalide, on le supprime

    # Mettre à jour récursivement les enfants du nœud
    new_children = []
    for child in node.children:
        updated_child = update_and_validate_tree(
            child, updated_rounds, validate_fn, compute_stat_fun,
            compare_standings_fun, player_indices, standings_wins,
            standings_losses, standings_gwp, standings_omwp, standings_ogwp,
            base_result_from_know_player, standings, full_list_of_masked_player,new_history,
            iteration + 1)
        
        if updated_child:
            new_children.append(updated_child)

    node.children = new_children  # Mettre à jour les enfants du nœud
    if not new_children:
    # Vérification de la feuille avec les standings        
        computed_standings = compute_stat_fun(base_result_from_know_player, history,full_list_of_masked_player,player_indices)
        standings_comparator_res = []
        for unsure_standings in computed_standings:
            standings_ite_current = standings[unsure_standings.player ]
            res_comparator = compare_standings_fun(standings_ite_current, unsure_standings, 3, 3, 3)
            standings_comparator_res.append(res_comparator)
        if all(standings_comparator_res):
            return [node]  # Retourne le nœud valide
        else:
            return None  # Feuille invalide
    # print(f"🌿 Feuille valide : {node.combination}")

    # return node 



###########
# generate combination of player per_round 
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
################################################

class Manatrader_fix_hidden_duplicate_name: 
    ###################################################################################################################    
    # Fonction ou méthode principale
    def Find_name_form_player_stats(self, rounds: List[Round], standings: List[Standing],bracket: List[Round]) -> List[Round]: 
        # Initialiser les rounds pour les mises à jour successives
        masked_to_actual = self.map_masked_to_actual(standings,rounds)
        # Étape 1 : Identifier les noms masqués dupliqués
        duplicated_masked_names = {
            masked for masked, actuals in masked_to_actual.items() if len(actuals) > 1
        }
        # étape 2 on crée des arbres par masked name et on tente de les assigner cette fonction doit etre récursive jusqu'a pas de changement ou tout les masked name attribué
        unmasked_rounds,remaining_mask_after_step2 = self.handle_mask_by_mask(rounds, masked_to_actual,standings)

        print("stop here ")
        # étape 2.1 créer un arbre par masked name ne conserver que les branches valides basé sur les stats du joueurs 
        # on utilise c'est arbres pour :
        #   validation des ogwp omwp ainsi que pour les adversaire concerné
        # on boucle jusqu'a ce que ça ne boude plus

        # étape 3 on crée les permutations globale et on fini le boulot.



        mask_to_remove,round_with_deterministic_round = self.assign_determinist_permutation_player_to_match(rounds, masked_to_actual,standings)

        for determinist_mask in mask_to_remove:
            del masked_to_actual[determinist_mask]

        
        # 2 chose a faire ici faire une methode qui vire les permut deterministe 
        # et peut etre auto assigner les permutations quand un joueur devient seul dans sa perm
        # on repete tout ici pour tout faire en une fois 
        matching_permutation = {}
        assignments_per_masked = self.generate_assignments(
            round_with_deterministic_round, masked_to_actual, standings
        )
        
        round_number = 0
        for permutation_per_round in assignments_per_masked:
            round_number += 1
            print(f"Round : {round_number} number of perm :{len(permutation_per_round)}")

        print("ok")
        resulting_tree =  self.find_real_tournament_from_permutation(
            assignments_per_masked,masked_to_actual, round_with_deterministic_round, standings
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
    
    def generate_assignments(self,  rounds: list[Round], masked_to_actual, standings):
        """Optimiser la génération des assignments avec multiprocessing."""
        assignments_per_masked = {}
        dict_standings = self.standings_to_dict(standings)
        assignments_per_round = []
        start_time = time.time()
        for round_obj in rounds:
            # print(round_obj.round_name)
            # if round_obj.round_name == "Round 5":
            valid_combinations = self.generate_round_combinations(round_obj, masked_to_actual, standings)
            assignments_per_round.append( valid_combinations)
        end_time = time.time()
        print(f"Temps total d'exécution pour genérer les perm: {end_time - start_time:.2f} secondes")
        return assignments_per_round



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
    
    def find_real_tournament_from_permutation(self,assignments_per_masked,masked_to_actual, rounds, standings,partial_assignment = False):
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

        player_with_real_name = set()
            # Identifier l'adversaire
        for round in rounds:
            for match in round.matches:
                if match.player1 and not re.fullmatch(r'.\*{10}.', match.player1):
                        player_with_real_name.add(match.player1)
                if match.player2 and not re.fullmatch(r'.\*{10}.', match.player2):
                        player_with_real_name.add(match.player2)

        base_result_of_named_player = {}
        for ite_player in player_with_real_name:
           base_result_of_named_player[ite_player] = self.From_player_to_result_dict_matches(ite_player, rounds ,standings,True)

        full_list_of_masked_player = set()
        for mask,player_list in masked_to_actual.items():
            for player in player_list:
                full_list_of_masked_player.add(player)
            
        player_indices = {standing.player: idx for idx, standing in enumerate(standings)}
        n_players = len(standings)
        # Créer les numpy arrays en extrayant les attributs des instances Standing
        # Créer les numpy arrays en extrayant les attributs des instances Standing
        standings_wins = np.array([standing.wins for standing in standings])
        standings_losses = np.array([standing.losses for standing in standings])
        standings_gwp = np.array([standing.gwp for standing in standings])
        standings_omwp = np.array([standing.omwp for standing in standings])
        standings_ogwp = np.array([standing.ogwp for standing in standings])

        dict_standings = self.standings_to_dict(standings)
        # Parallélisation
        start_time = time.time()
        # Préparer les arguments pour la parallélisation
        print(mask)
        total_perm_count = 1
        for round_perm in assignments_per_masked:
            total_perm_count *= len(round_perm)
        print(total_perm_count)
        if len(assignments_per_masked[0]) < 5:
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
                dict_standings,
                full_list_of_masked_player
            )
            valid_permutations = root
            if len(valid_permutations.children) > 0:
                print("tree ok")
        else:
            first_round_xs = assignments_per_masked[0]  # Objets X du premier round
            remaining_rounds = assignments_per_masked[1:]  # Rounds restants
            chunk_size =  int(len(first_round_xs)/5)
            # chunk_size =  int(len(first_round_xs)/50)#1000  # Ajuste selon la taille souhaitée
            first_round_chunks = list(chunked(first_round_xs, chunk_size))
            tasks = [
                (
                    chunk,
                    remaining_rounds,
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
                    dict_standings,
                    full_list_of_masked_player
                )
                for chunk in first_round_chunks
            ]
            # Diviser les tâches pour chaque round dans valid_combinations
            with Pool(cpu_count()) as pool:
                results = pool.map(process_combination, tasks)
            # Fusionner les résultats valides
            valid_permutations = results
            if len(valid_permutations) > 1:
                print("tree ok")
            elif len(results) == 1 and len(valid_permutations[0].children) > 0:
                print("tree ok")
        end_time = time.time()
        print(f"Temps total traitement des arbres: {end_time - start_time:.2f} secondes")
        return valid_permutations
    

    def handle_mask_by_mask(self,rounds, masked_to_actual,standings):
        Assignement_per_mask_result = {}
        tree_result = {}
        for mask ,actual_player in masked_to_actual.items():
            Assignement_per_mask_result[mask] = self.generate_assignments( rounds, {mask: actual_player}, standings)
            tree_result[mask] = self.find_real_tournament_from_permutation(Assignement_per_mask_result[mask],{mask: actual_player}, rounds, standings,True)

        modified_rounds = copy.deepcopy(rounds)
        # 1 les arbres sont crée reste a vérifier les arbres unique puis update les rounds
        it = 0
        while True:
            print(it)
            keys_to_delete = []
            for mask,tree in tree_result.items():
                if isinstance(tree, list) and len(tree) == 1:
                    tree = tree[0]  # Extraire l'élément unique de la liste
                if isinstance(tree, TreeNode) and is_single_line_tree(tree):
                    apply_tree_permutations(tree, modified_rounds, mask)
                    # debug_test temp 
                    debug_masked_name_matches = [
                        match for round_obj in modified_rounds for match in round_obj.matches
                        if (isinstance(match.player1, str) and mask == match.player1) or
                        (isinstance(match.player2, str) and mask == match.player2)
                    ]
                    if debug_masked_name_matches:
                        print("Il reste des noms masqués :", debug_masked_name_matches)
                    else:
                        print("Unique perm : ", mask)
                        keys_to_delete.append(mask)
                # Si plus rien à supprimer, on sort de la boucle
            if not keys_to_delete:
                break
            for key in keys_to_delete:
                del tree_result[key]
                del masked_to_actual[key]

            
            # 2 Une fois les rounds update il faut une fonction qui update les arbres avec les nouveau rounds et coupes les arbres invalides
            for mask, tree in tree_result.items():
                # bug 's**********o' vide 
                if mask == 's**********o':
                    print("debug")
                start_time = time.time()
                tree_result[mask] = self.update_tree_after_round_assignation(tree,{mask: masked_to_actual[mask]}, rounds, standings)
                end_time = time.time()
                print(f"Update round {mask}: {end_time - start_time:.2f} secondes")
            it += 1

        return resulting_rounds ,remaining_mask
    
    def update_tree_after_round_assignation(self,tree, masked_to_actual,rounds, standings):
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

        player_with_real_name = set()
            # Identifier l'adversaire
        for round in rounds:
            for match in round.matches:
                if match.player1 and not re.fullmatch(r'.\*{10}.', match.player1):
                        player_with_real_name.add(match.player1)
                if match.player2 and not re.fullmatch(r'.\*{10}.', match.player2):
                        player_with_real_name.add(match.player2)

        base_result_of_named_player = {}
        for ite_player in player_with_real_name:
           base_result_of_named_player[ite_player] = self.From_player_to_result_dict_matches(ite_player, rounds ,standings,True)

        full_list_of_masked_player = set()
        for mask,player_list in masked_to_actual.items():
            for player in player_list:
                full_list_of_masked_player.add(player)
            
        player_indices = {standing.player: idx for idx, standing in enumerate(standings)}
        n_players = len(standings)
        # Créer les numpy arrays en extrayant les attributs des instances Standing
        # Créer les numpy arrays en extrayant les attributs des instances Standing
        standings_wins = np.array([standing.wins for standing in standings])
        standings_losses = np.array([standing.losses for standing in standings])
        standings_gwp = np.array([standing.gwp for standing in standings])
        standings_omwp = np.array([standing.omwp for standing in standings])
        standings_ogwp = np.array([standing.ogwp for standing in standings])

        dict_standings = self.standings_to_dict(standings)
        full_list_of_masked_player = set()
        for mask,player_list in masked_to_actual.items():
            for player in player_list:
                full_list_of_masked_player.add(player)
        tree_result = {}
        if isinstance(tree, list):
            with Pool(processes=cpu_count()) as pool:
                tree = pool.starmap(
                    update_and_validate_tree, 
                    [(t, masked_name_matches, validate_permutation, 
                    self.calculate_stats_for_matches, self.compare_standings,
                    player_indices, standings_wins, standings_losses, standings_gwp, 
                    standings_omwp, standings_ogwp, base_result_of_named_player, 
                    dict_standings, full_list_of_masked_player) for t in tree]
                )
            
            # Filtrer les arbres invalides
            tree_result[mask] = [t for t in tree if t is not None]
        else:
            tree_result[mask] = update_and_validate_tree(tree,
                                                        masked_name_matches,
                                                        validate_permutation,
                                                        self.calculate_stats_for_matches,
                                                        self.compare_standings,
                                                        player_indices, standings_wins, 
                                                        standings_losses, standings_gwp, standings_omwp, standings_ogwp, 
                                                        base_result_of_named_player, dict_standings,
                                                        full_list_of_masked_player
                                                        )

        # Supprime les entrées vides
        tree_result = {mask: tree for mask, tree in tree_result.items() if tree}
        return tree_result
    


    def From_player_to_result_dict_matches(self, player: str,rounds ,standings: List[Standing],masked_player_tolerate = False):
        # Initialiser les stats
        points = 0
        wins = 0
        losses = 0
        draws = 0
        total_games_played = 0
        total_games_won = 0
        total_game_draw = 0
        opponents = set()

        # Parcourir les matchs
        for round in rounds:
            for match in round.matches:
                p1_wins, p2_wins, draws = map(int, match.result.split('-'))
                opponent = None
                # Identifier l'adversaire
                if match.player1 == player:
                    if match.player2 and not re.fullmatch(r'.\*{10}.', match.player2) and masked_player_tolerate:
                        opponent = match.player2
                    player_wins, player_losses ,player_draw= p1_wins, p2_wins,draws
                elif match.player2 == player:
                    if match.player1 and not re.fullmatch(r'.\*{10}.', match.player1) and masked_player_tolerate:
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
                total_games_won += player_wins 
                total_game_draw += player_draw
                # Ajouter l'adversaire à la liste
                if opponent:
                    opponents.add(opponent)
        # Ajouter aux points (3 pour chaque victoire, 1 pour chaque égalité)
        points += 3 * wins + draws

        return {
        'wins' : wins,
        'losses' : losses,
        'draws' : draws,
        'total_games_played' : total_games_played,
        'total_games_won' : total_games_won,
        'total_game_draw' : total_game_draw,
        'opponents' : opponents
        }      


    def calculate_stats_for_matches(self, base_table_res,permutation_res_table,full_list_of_masked_player,player_indices):  
        Match_wins = copy.deepcopy(permutation_res_table["Match_wins"])
        Match_losses = copy.deepcopy(permutation_res_table["Match_losses"])
        Game_wins = copy.deepcopy(permutation_res_table["Game_wins"])
        Game_losses = copy.deepcopy(permutation_res_table["Game_losses"])
        Game_draws = copy.deepcopy(permutation_res_table["Game_draws"])
        matchups = copy.deepcopy(permutation_res_table["matchups"])
        update_player_standings = []

        for player in player_indices:
            if len(matchups[player]) > 0:
                player_idx = player_indices[player]
                computable_ogp_omwp = True
                number_of_opponent = 0
                total_omp = 0
                total_ogp = 0
                if len(matchups[player]) > (Match_wins[player_idx] + Match_losses[player_idx]):
                    print("plus d'opo que de partie ...")
                elif len(matchups[player]) != (Match_wins[player_idx] + Match_losses[player_idx]):
                    computable_ogp_omwp = False
                else:
                    for opo in matchups[player]:
                        if re.fullmatch(r'.\*{10}.', opo):  
                            computable_ogp_omwp = False
                            break
                        if opo :
                            opo_idx = player_indices[opo]
                            opponent_gwp = (Game_wins[opo_idx] +(Game_draws[opo_idx]/3)) / (Game_wins[opo_idx] +Game_draws[opo_idx] + Game_losses[opo_idx])  # GWP pour l'adversaire
                            total_ogp += opponent_gwp if opponent_gwp >= 0.3333 else 0.33
                            number_of_opponent += 1
                            # OMWP 
                            opponent_match_winrate = Match_wins[opo_idx] / (Match_wins[opo_idx] + Match_losses[opo_idx])
                            total_omp += opponent_match_winrate if opponent_match_winrate >= 0.3333 else 0.33
                update_player_standings.append(
                        Standing(
                        rank=None,
                        player=player,
                        points = (Match_wins[player_idx]*3),
                        wins=Match_wins[player_idx],
                        losses=Match_losses[player_idx],
                        draws=0,
                        omwp= total_omp/number_of_opponent if computable_ogp_omwp else None,
                        gwp=(Game_wins[player_idx] +(Game_draws[player_idx]/3)) / (Game_wins[player_idx] +Game_draws[player_idx] + Game_losses[player_idx]),
                        ogwp=total_ogp/number_of_opponent if computable_ogp_omwp else None
                        )
                        )
        return update_player_standings

    def compare_standings(self,real_standing, recalculated_standing,  compare_gwp=None, compare_omwp=None, compare_ogwp=None, tolerance=1e-3):
        """Compare deux standings et retourne True s'ils sont identiques, sinon False."""
        matches = (
            # real_standing["rank"] == recalculated_standing.rank and
            real_standing["points"] == recalculated_standing.points and
            real_standing["wins"] == recalculated_standing.wins and
            real_standing["losses"] == recalculated_standing.losses
        )

        # Fonction pour comparer avec tolérance
        def are_close(val1, val2, tol):
            return abs(val1 - val2) <= tol

        # Comparaison optionnelle des pourcentages
        if compare_gwp and real_standing.get("gwp") is not None and recalculated_standing.gwp is not None:
            matches = matches and are_close(
                real_standing["gwp"], 
                recalculated_standing.gwp, 
                tolerance
            )

        if compare_omwp and real_standing.get("omwp") is not None and recalculated_standing.omwp is not None:
            matches = matches and are_close(
                real_standing["omwp"], 
                recalculated_standing.omwp, 
                tolerance
            )

        if compare_ogwp and real_standing.get("ogwp") is not None and recalculated_standing.ogwp is not None:
            matches = matches and are_close(
                real_standing["ogwp"], 
                recalculated_standing.ogwp, 
                tolerance
            )

        return matches
