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

def custom_round(value, decimals=0):
    # multiplier = 10**decimalsr
    epsilon = 10 ** (-decimals -3)
    return round(value + epsilon, decimals)
# determinist per worker 
# Fonction globale qui peut être picklée
def determinist_worker(args):
    """Vérifie si la permutation est valide."""
    perm, player_indices, standings_wins, standings_losses, standings_gwp, n_players,dict_standings = args
    return No_tree_determinist_validate_permutation(perm, player_indices, standings_wins, standings_losses, standings_gwp, n_players,dict_standings)

def No_tree_determinist_validate_permutation(perm, player_indices, standings_wins, standings_losses,standings_gwp, n_players,dict_standings):
    """Valider une permutation donnée."""
    wins = np.zeros(n_players, dtype=int)
    losses = np.zeros(n_players, dtype=int)
    gwp_calculated = np.zeros(n_players, dtype=float)
    matchups = {player: [] for player in player_indices.keys()}
    # rounds_played = np.zeros(n_players, dtype=int)
    for round_data in perm:
        for player, round_items in round_data.items():
            player_idx = player_indices[player]
            for round_item in round_items:
                if round_item.player1 == player:
                    win, loss = round_item.scores[0]  # Scores de player1
                    if re.fullmatch(r'.\*{10}.', round_item.player2):
                        if round_item.player2 in matchups[player]:
                            return False
                    matchups[player].append(round_item.player2)
                elif round_item.player2 == player:
                    win, loss = round_item.scores[1]  # Scores de player2  
                    if re.fullmatch(r'.\*{10}.', round_item.player1):
                        if round_item.player1 in matchups[player]:
                            return False
                    matchups[player].append(round_item.player1)
                # Mettre à jour les statistiques du joueur
                wins[player_idx] += win
                losses[player_idx] += loss

                # Vérifier si les limites de wins/losses sont dépassées
                if wins[player_idx] > standings_wins[player_idx] or losses[player_idx] > standings_losses[player_idx]:
                    return False
    if not np.array_equal(wins, standings_wins) or not np.array_equal(losses, standings_losses):
        return False
        # rounds_played = np.zeros(n_players, dtype=int)
    Match_win = np.zeros(n_players, dtype=int)
    Match_losses = np.zeros(n_players, dtype=int)
    Match_draw = np.zeros(n_players, dtype=int)

    for round_data in perm:
        for player, round_items in round_data.items():
            player_idx = player_indices[player]
            for round_item in round_items:
                if round_item.player1 == player:
                    win, loss,draw  = map(int, round_item.result.split('-'))  # Scores de player1
                elif round_item.player2 == player:
                    loss ,win, draw  = map(int, round_item.result.split('-'))  # Scores de player2  
                Match_win[player_idx] += win + (draw/3)
                Match_losses[player_idx] += loss
                Match_draw[player_idx] += draw
        # Calcul du GWP et comparaison avec standings_gwp
    for i in range(n_players):
        total_games = Match_win[i] + Match_losses[i] + Match_draw[i]
        if total_games > 0:
            gwp_calculated[i] = Match_win[i] / total_games
        else:
            gwp_calculated[i] = 0.0
        # Comparaison avec tolérance
        if not np.isclose(gwp_calculated[i], standings_gwp[i], atol=0.001):
            return False
    for player , oponents in matchups.items():
        if all(not re.fullmatch(r'.\*{10}.',element) for element in oponents):   
            gwp_opo = 0
            mwp_opo = 0
            total_opo_opo = 0
            for oponent in oponents:
                total_opo_opo += 1
                gwp_opo_en_cours = dict_standings[oponent]["gwp"] 
                gwp_opo += gwp_opo_en_cours if gwp_opo_en_cours >= 0.33333 else 0.33
                match_win_rate_opo = dict_standings[oponent]["wins"] /(dict_standings[oponent]["wins"]  + dict_standings[oponent]["losses"])
                mwp_opo += match_win_rate_opo if match_win_rate_opo >= 0.33333 else 0.33
                
            if not np.isclose(dict_standings[player]["ogwp"], gwp_opo/total_opo_opo, atol=0.001):
                return False 
            if not np.isclose(dict_standings[player]["omwp"], mwp_opo/total_opo_opo, atol=0.001):
                return False 
    return True


class Manatrader_fix_hidden_duplicate_name: 

          


    def organize_matches_by_round(self, matches_info):
        """Organiser les matchs par round."""
        matches_by_round = defaultdict(list)
        for role, round_name, match in matches_info:
            matches_by_round[round_name].append((role, match))
        return matches_by_round


    




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
###############################################################################################
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
            if len(permutations) == 1:
                print(f"Permutation unique attribué : {masked_name}")
                for round_combinations in permutations:
                    for round_dict in round_combinations:  # Itère sur chaque defaultdict
                        for real_name, updated_matches in round_dict.items():  # Itère sur les paires clé-valeur
                            for updated_match in updated_matches:  # Itère sur les RoundItem associés
                                # Appliquer les modifications si le masque et l'autre joueur correspondent
                                for modified_round in modified_rounds:
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

        return modified_rounds,remaining_permutations
    
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
    
    def assign_determinist_permutation_player_to_match(self,rounds,masked_to_actual,standings):
        matching_permutation = {}
        # ICI  RESTE A MODIFIER LE COMPORTEMENT DE DETERMINISTE PERMUTATION POUR UPDATE LES MATCHES A CHAQUE TOUR DE BOUCLE OU BOUCLE WHILE
        # ET RE PARALELISER CAR LONG
        temp_rounds = copy.deepcopy(rounds)
        # Identifier l'adversaire
        start_time = time.time()
        i = 0
        masked_names = list(masked_to_actual.keys())  # Faire une copie pour éviter les erreurs d'indexation
        while i < len(masked_names):  # Pas besoin de `<=`, sinon IndexError
            masked_name = masked_names[i]
            print(i)
            print(masked_name)
            masked_matches = self.collect_matches_for_duplicated_masked_names(
                {masked_name}, temp_rounds
            )
            assignments_per_masked = self.No_tree_determinist_generate_assignments(
                masked_matches, masked_to_actual, standings
            )

            if assignments_per_masked[masked_name]:
                for key, value in assignments_per_masked.items():
                    matching_permutation[key] = value
                    temp_rounds, matching_permutation = self.generate_tournaments_with_unique_permutations(
                        temp_rounds, matching_permutation
                    )

                # Si une itération déterministe existe, supprimer `masked_name`
                if masked_name in masked_to_actual:
                    del masked_to_actual[masked_name]
                    masked_names.remove(masked_name)  # Mise à jour de la liste copiée
                    continue  # Ne pas incrémenter `i` pour éviter de sauter un élément
            i += 1

        end_time = time.time()
        print(f"Temps total d'exécution pour determinist les perm: {end_time - start_time:.2f} secondes")
        return matching_permutation.keys(),Determinist_permutation
    
    def No_tree_determinist_generate_assignments(self, masked_matches, masked_to_actual, standings):
        """Optimiser la génération des assignments avec multiprocessing."""
        ### method for detrminist perm validation
        def parallel_validate_permutations(chunk, player_indices, standings_wins, standings_losses, standings_gwp, n_players):
            """Fonction de validation utilisée en parallèle."""
            return [
                perm for perm in chunk if No_tree_determinist_validate_permutation(
                    perm, player_indices, standings_wins, standings_losses, standings_gwp, n_players,dict_standings
                )
            ]

        def No_tree_determinist_generate_round_combinations(matches, actual_players, standings,round_name):
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

        def No_tree_determinist_clean_round_combinations(round_combinations):
            seen = set()  # Pour garder trace des dictionnaires déjà vus
            cleaned_round_data = []
            for round_item in round_combinations:
                # Convertir le defaultdict en un tuple des éléments
                item_tuple = tuple((key, tuple(value)) for key, value in round_item.items())
                if item_tuple not in seen:
                    seen.add(item_tuple)  # Marquer ce dict comme vu
                    cleaned_round_data.append(round_item)  # Ajouter le dict à la liste nettoyée
            return cleaned_round_data
                                                    

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
                    round_combinations = No_tree_determinist_generate_round_combinations(matches, actual_players, standings, round_name)
                    if round_combinations:  # Vérifie si des combinaisons existent pour ce round
                        yield round_combinations

            # Générer le générateur de combinaisons valides pour chaque round
            valid_combinations = generate_valid_combinations()

            # Nettoyage des données des combinaisons générées
            cleaned_combinations = [No_tree_determinist_clean_round_combinations(round_combinations) for round_combinations in valid_combinations]

            # Calcul du nombre total de permutations
            total_permutations = 1
            for comb in cleaned_combinations:
                total_permutations *= len(comb)

            # Génération paresseuse des permutations
            permutations_lazy_permutations = product(*cleaned_combinations)

            # Si le nombre de permutations est petit, on traite en séquentiel
            if total_permutations < 1000:
                valid_perms = [
                    perm for perm in permutations_lazy_permutations
                    if No_tree_determinist_validate_permutation(perm, player_indices, standings_wins, standings_losses, standings_gwp, n_players,dict_standings)
                ]
                if len(valid_perms) > 1:
                    assignments_per_masked[masked] = None
                else:
                    assignments_per_masked[masked] = valid_perms

            # Si le nombre de permutations est raisonnable, on utilise le multiprocessing
            elif total_permutations < 1_000_000_000:
                start_time = time.time()
                print(f"Total permutations for parallelization: {total_permutations}")

                # Taille dynamique du chunk
                chunk_size = min(10_000, max(1_000, total_permutations // (10 * cpu_count())))

                manager = Manager()
                valid_perms = manager.list()  # Stockage partagé sécurisé pour éviter des conflits d'accès



                with Pool(cpu_count()) as pool:
                    it = pool.imap_unordered(determinist_worker, 
                        [(perm, player_indices, standings_wins, standings_losses, standings_gwp, n_players,dict_standings) for perm in permutations_lazy_permutations],
                        chunksize=chunk_size
                    )

                    for is_valid in it:
                        if is_valid:
                            valid_perms.append(is_valid)
                        if len(valid_perms) > 1:
                            pool.terminate()  # Arrête immédiatement les processus
                            break

                assignments_per_masked[masked] = None if len(valid_perms) > 1 else list(valid_perms)

                end_time = time.time()
                print(f"Total execution time: {end_time - start_time:.2f} seconds")

            # Si trop de permutations, on stoppe
            else:
                print(f"Total permutations too large, STOP: {total_permutations}")
                assignments_per_masked[masked] = None
        return assignments_per_masked






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