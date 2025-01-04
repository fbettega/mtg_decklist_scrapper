def calculate_player_stats(self, rounds: List[Round], standings: List[Standing]):
    # Identifier les joueurs et leurs matchs
    player_matches = defaultdict(list)  # Map joueur -> liste des matchs
    for rnd in rounds:
        for match in rnd.matches:
            player_matches[match.player1].append(match)
            player_matches[match.player2].append(match)
    
    # Identifier les joueurs en double
    duplicate_players = {player for player, matches in player_matches.items() if len(matches) > len(rounds)}

    # Regrouper les joueurs dupliqués par leurs matchs (même ensemble de matchs)
    duplicate_groups = {}
    for player in duplicate_players:
        key = frozenset((match.player1, match.player2, match.result) for match in player_matches[player])  # Utiliser un ensemble immuable comme clé
        if key not in duplicate_groups:
            duplicate_groups[key] = []
        duplicate_groups[key].append(player)

    # Calculer les stats
    player_stats = {}
    for player, matches in player_matches.items():
        if player in duplicate_players:
            # Identifier les matchs spécifiques où le joueur est impliqué
            specific_matches = [
                match for match in matches if match.player1 == player or match.player2 == player
            ]

            # Générer les permutations uniquement pour ces matchs
            match_combinations = list(permutations(specific_matches))
            stats_per_combination = []
            for match_combo in match_combinations:
                # Créer une liste complète des matchs avec les permutations appliquées
                full_matches = matches.copy()
                for original, permuted in zip(specific_matches, match_combo):
                    full_matches[full_matches.index(original)] = permuted

                stats = self.calculate_stats_for_matches(full_matches, standings)
                stats_per_combination.append(stats)

            # Assigner les permutations calculées au joueur
            player_stats[player] = stats_per_combination
        else:
            # Calculer les stats normalement pour les joueurs non dupliqués
            player_stats[player] = self.calculate_stats_for_matches(matches, standings)

    return player_stats
#Test2
########################################################################################################
    # def calculate_player_stats(self,rounds: List[Round], standings: List[Standing]):
    #     # Identifier les joueurs et leurs matchs
    #     player_matches = defaultdict(list)  # Map joueur -> liste des matchs
    #     for rnd in rounds:
    #         for match in rnd.matches:
    #             player_matches[match.player1].append(match)
    #             player_matches[match.player2].append(match)
        
    #     # Identifier les joueurs en double
    #     duplicate_players = {player for player, matches in player_matches.items() if len(matches) > len(rounds)}

    #     # Regrouper les joueurs dupliqués par leurs matchs (même ensemble de matchs)
    #     duplicate_groups = {}
    #     for player in duplicate_players:
    #         key = frozenset((match.player1, match.player2, match.result) for match in player_matches[player])  # Utiliser un ensemble immuable comme clé
    #         if key not in duplicate_groups:
    #             duplicate_groups[key] = []
    #         duplicate_groups[key].append(player)

    #     # Calculer les stats
    #     player_stats = {}
    #     for player, matches in player_matches.items():
    #         if player in duplicate_players:
    #             # Générer les permutations uniquement pour les matchs du joueur
    #             match_combinations = list(permutations(matches))
    #             stats_per_combination = []
    #             for match_combo in match_combinations:
    #                 stats = self.calculate_stats_for_matches(match_combo, standings)
    #                 stats_per_combination.append(stats)

    #             # Assigner les permutations calculées à ce joueur
    #             player_stats[player] = stats_per_combination
    #         else:
    #             # Calculer les stats normalement pour les joueurs non dupliqués
    #             player_stats[player] = self.calculate_stats_for_matches(matches, standings)

    #     return player_stats



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
        for match in matches:
            p1_wins, p2_wins, draws = map(int, match.result.split('-'))

            # Identifier le joueur et son adversaire
            if match.player1 in stats:
                player = match.player1
                opponent = match.player2
                player_wins, player_losses = p1_wins, p2_wins
            elif match.player2 in stats:
                player = match.player2
                opponent = match.player1
                player_wins, player_losses = p2_wins, p1_wins
            else:
                continue

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
            stats["GWP"] = max(total_games_won / total_games_played, 0.33)

        # Calculer OMP (Opponents’ Match-Win Percentage)
        opponent_match_points = 0
        opponent_total_matches = 0
        for opponent in opponents:
            opponent_standing = next((s for s in standings if s.player == opponent), None)
            if opponent_standing:
                opponent_match_points += opponent_standing.points
                opponent_total_matches += 3 * len(matches)  # Nombre de rounds (approximé ici)

        if opponent_total_matches > 0:
            stats["OMP"] = max(opponent_match_points / opponent_total_matches, 0.33)

        # Calculer OGP (Opponents’ Game-Win Percentage)
        opponent_game_wins = 0
        opponent_game_total = 0
        for opponent in opponents:
            opponent_standing = next((s for s in standings if s.player == opponent), None)
            if opponent_standing:
                opponent_game_wins += opponent_standing.wins
                opponent_game_total += opponent_standing.wins + opponent_standing.losses + opponent_standing.draws

        if opponent_game_total > 0:
            stats["OGP"] = max(opponent_game_wins / opponent_game_total, 0.33)

        return stats
#test1
#########################################################################################################
    def get_opponents(self, player: str, rounds: List[Round]) -> List[str]:
        """Retourne la liste des adversaires d'un joueur dans tous les rounds."""
        opponents = set()
        for rnd in rounds:
            for match in rnd.matches:
                if match.player1 == player:
                    opponents.add(match.player2)
                elif match.player2 == player:
                    opponents.add(match.player1)
        return list(opponents)

    def calculate_player_stats(self, rounds: List[Round], standings: List[Standing]) -> Tuple[Dict[str, List[Dict]], List[str], List[str]]: 
            # Étape 1 : Mapper les noms masqués aux joueurs réels
            masked_to_actual = defaultdict(list)
            for standing in standings:
                if standing.player:
                    masked_name = f"{standing.player[0]}{'*' * 10}{standing.player[-1]}"
                    masked_to_actual[masked_name].append(standing.player)
            
            # Étape 2 : Collecter les matchs par joueur
            player_matches = defaultdict(list)
            for rnd in rounds:
                for match in rnd.matches:
                    player_matches[match.player1].append(match)
                    player_matches[match.player2].append(match)
            
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
                num_matches = len(matches_info)
                # Générer toutes les assignations possibles (produit cartésien avec répétition)
                assignments = list(product(actual_players, repeat=num_matches))
                assignments_per_masked[masked] = assignments
            
            # Étape 6 : Générer toutes les combinaisons d'assignations entre les joueurs dupliqués
            if assignments_per_masked:
                all_masked_names = list(assignments_per_masked.keys())
                all_assignments_combinations = list(product(*(assignments_per_masked[masked] for masked in all_masked_names)))
            else:
                all_masked_names = []
                all_assignments_combinations = [()]
            
            # Étape 7 : Appliquer chaque combinaison d'assignations et calculer les stats
            player_stats = defaultdict(list)
            for assignment_combo in all_assignments_combinations:
                # Créer une copie des rounds pour appliquer les assignations
                new_rounds = copy.deepcopy(rounds)
                
                # Appliquer chaque assignation
                for i, masked in enumerate(all_masked_names):
                    assigned_players = assignment_combo[i]
                    for j, (role, round_name, match) in enumerate(masked_matches[masked]):
                        # Trouver le round correspondant
                        for rnd in new_rounds:
                            if rnd.round_name == round_name:
                                for m in rnd.matches:
                                    if m == match:
                                        if role == 'player1':
                                            m.player1 = assigned_players[j]
                                        elif role == 'player2':
                                            m.player2 = assigned_players[j]
                
                # Calculer les stats pour cette assignation
                stats = self.calculate_stats_for_matches(new_rounds, standings)
                
                # Assignation des stats aux joueurs
                for player, stat in stats.items():
                    player_stats[player].append(stat)
            
            # Étape 8 : Identifier les joueurs non appariés dans les standings
            players_in_stats = set(player_stats.keys())
            unmatched_standings = [s.player for s in standings if s.player not in players_in_stats]
            
            # Étape 9 : Identifier les matchs non appariés (si nécessaire)
            # Dans ce contexte, tous les matchs devraient être appariés via les assignations
            unmatched_matches = []
            
            return player_stats, unmatched_standings, unmatched_matches